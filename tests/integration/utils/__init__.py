"""Utilities for integration tests."""

import asyncio
import hashlib
import random
import re
import shutil
import socket
import tempfile
import time
from pathlib import Path
from typing import Dict, Tuple, List, Optional

import httpx
from python_on_whales import DockerClient

from .progress import TestProgressReporter, ContainerWaitReporter, get_test_reporter
from .progress import progress_context as progress_context


def find_free_port(max_retries: int = 10) -> int:
    """Find a free port with retry logic for test isolation."""
    for attempt in range(max_retries):
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                s.bind(("127.0.0.1", 0))  # Bind to localhost explicitly
                s.listen(1)
                port = s.getsockname()[1]

            # Port was successfully allocated and socket is now closed
            # Reduced delay for faster tests while maintaining isolation
            time.sleep(random.uniform(0.02, 0.05))
            return port

        except OSError:
            if attempt < max_retries - 1:
                time.sleep(random.uniform(0.1, 0.3))
                continue
            raise
    raise RuntimeError(f"Could not find free port after {max_retries} attempts")


def allocate_test_ports(max_retries: int = 5) -> Dict[str, int]:
    """Allocate unique ports for a test instance with collision avoidance."""
    for attempt in range(max_retries):
        try:
            # Allocate all ports at once to check for conflicts
            ports = {
                "validation_port": find_free_port(),
                "validation_haproxy_port": find_free_port(),
                "validation_health_port": find_free_port(),
                "production_port": find_free_port(),
                "http_port": find_free_port(),
                "health_port": find_free_port(),
            }

            # Verify no duplicate ports were allocated
            port_values = list(ports.values())
            if len(port_values) == len(set(port_values)):
                return ports
            else:
                # Duplicate ports detected, try again
                if attempt < max_retries - 1:
                    time.sleep(random.uniform(0.2, 0.8))
                    continue
                raise RuntimeError("Duplicate ports allocated")

        except Exception as e:
            if attempt < max_retries - 1:
                time.sleep(random.uniform(0.5, 1.5))
                continue
            raise RuntimeError(
                f"Failed to allocate ports after {max_retries} attempts: {e}"
            )

    # This should never be reached but added for mypy completeness
    raise RuntimeError("Failed to allocate ports: no attempts made")


def generate_project_name(test_name: str) -> str:
    """Generate unique Docker Compose project name."""
    # Sanitize test name to be Docker-friendly (alphanumeric and underscores only)
    safe_name = re.sub(r"[^a-zA-Z0-9]", "", test_name)[:20]
    # Use hash instead of UUID for deterministic but unique names
    test_hash = hashlib.md5(test_name.encode()).hexdigest()[:8]
    return f"test_{safe_name}_{test_hash}"


def generate_compose_file(
    ports: Dict[str, int], template_path: Path, use_prebuilt_images: bool = False
) -> str:
    """Generate docker-compose.yml with dynamic ports and optionally pre-built images."""
    with open(template_path, "r") as f:
        template = f.read()

    # Replace port placeholders
    content = template.replace("{{VALIDATION_PORT}}", str(ports["validation_port"]))
    content = content.replace(
        "{{VALIDATION_HAPROXY_PORT}}", str(ports["validation_haproxy_port"])
    )
    content = content.replace(
        "{{VALIDATION_HEALTH_PORT}}", str(ports["validation_health_port"])
    )
    content = content.replace("{{PRODUCTION_PORT}}", str(ports["production_port"]))
    content = content.replace("{{HTTP_PORT}}", str(ports["http_port"]))
    content = content.replace("{{HEALTH_PORT}}", str(ports["health_port"]))

    # If using pre-built images, replace build contexts with image references
    if use_prebuilt_images:
        # Replace HAProxy build section with image reference
        content = re.sub(
            r"validation-haproxy: &haproxy\s*build:\s*context: haproxy\s*dockerfile: Dockerfile",
            "validation-haproxy: &haproxy\n    image: test-haproxy:integration",
            content,
            flags=re.MULTILINE | re.DOTALL,
        )

        # Replace Dataplane build section with image reference
        content = re.sub(
            r"validation-dataplane-api: &dataplane\s*build:\s*context: dataplane\s*dockerfile: Dockerfile",
            "validation-dataplane-api: &dataplane\n    image: test-dataplane:integration",
            content,
            flags=re.MULTILINE | re.DOTALL,
        )

    return content


async def wait_for_service(
    url: str,
    timeout: int = 10,
    interval: float = 0.2,
    reporter: Optional[TestProgressReporter] = None,
    service_name: str = "service",
) -> bool:
    """Wait for a service to become available with progress reporting."""
    if reporter is None:
        reporter = get_test_reporter()

    start_time = time.time()
    wait_reporter = ContainerWaitReporter(reporter)
    attempt = 0
    max_attempts = int(timeout / interval)

    while time.time() - start_time < timeout:
        attempt += 1
        wait_reporter.update(service_name, url, attempt, max_attempts)

        try:
            async with httpx.AsyncClient(timeout=3.0) as client:
                response = await client.get(url)
                if response.status_code < 500:  # Accept any non-server-error response
                    wait_reporter.success(service_name, url)
                    return True
                else:
                    reporter.debug(
                        f"Service {service_name} returned status {response.status_code}"
                    )
        except (httpx.RequestError, httpx.HTTPStatusError) as e:
            reporter.debug(f"Service {service_name} connection failed: {e}")

        await asyncio.sleep(interval)

    wait_reporter.failure(service_name, url, f"Timeout after {timeout}s")
    return False


async def wait_for_dataplane_api(
    base_url: str,
    auth: Tuple[str, str] = ("admin", "adminpass"),
    timeout: int = 10,
    reporter: Optional[TestProgressReporter] = None,
    service_name: str = "Dataplane API",
) -> bool:
    """Wait for Dataplane API to become ready with progress reporting."""
    if reporter is None:
        reporter = get_test_reporter()

    start_time = time.time()
    wait_reporter = ContainerWaitReporter(reporter)
    attempt = 0
    interval = 0.2  # Faster polling
    max_attempts = int(timeout / interval)
    api_url = f"{base_url}/v3/info"

    while time.time() - start_time < timeout:
        attempt += 1
        wait_reporter.update(service_name, api_url, attempt, max_attempts)

        try:
            async with httpx.AsyncClient(timeout=3.0, auth=auth) as client:
                response = await client.get(api_url)
                if response.status_code == 200:
                    wait_reporter.success(service_name, api_url)
                    return True
                else:
                    reporter.debug(
                        f"Dataplane API returned status {response.status_code}"
                    )
        except (httpx.RequestError, httpx.HTTPStatusError) as e:
            reporter.debug(f"Dataplane API connection failed: {e}")

        await asyncio.sleep(interval)

    wait_reporter.failure(service_name, api_url, f"Timeout after {timeout}s")
    return False


def read_config_file(filename: str) -> str:
    """Read HAProxy config file from fixtures."""
    fixtures_dir = Path(__file__).parent.parent / "fixtures" / "dataplane"
    config_path = fixtures_dir / filename

    with open(config_path, "r") as f:
        return f.read()


def get_container_logs(
    docker: DockerClient,
    service_name: str,
    reporter: Optional[TestProgressReporter] = None,
) -> str:
    """Get logs from a docker-compose service for debugging."""
    if reporter is None:
        reporter = get_test_reporter()

    try:
        reporter.debug(f"Fetching logs for service {service_name}")
        logs = docker.compose.logs(services=[service_name])
        if logs.strip():
            reporter.container_logs(service_name, logs)
        return logs
    except Exception as e:
        error_msg = f"Failed to get logs: {e}"
        reporter.warning(f"Could not fetch logs for {service_name}: {e}")
        return error_msg


class DockerComposeManager:
    """Context manager for docker-compose with automatic cleanup and progress reporting."""

    def __init__(
        self,
        ports: Dict[str, int],
        test_name: str = "unknown",
        shared_images: Optional[Dict[str, str]] = None,
    ):
        self.ports = ports
        self.test_name = test_name
        self.project_name = generate_project_name(test_name)
        self.compose_file = None
        self.temp_dir = None
        self.docker = None  # Will be initialized with compose file
        self.reporter = get_test_reporter()
        self.failed_services: List[str] = []
        self.container_logs: Dict[str, str] = {}
        self.shared_images = shared_images or {}
        self.use_prebuilt_images = bool(shared_images)

    async def __aenter__(self):
        """Set up Docker compose environment with progress reporting."""
        self.reporter.phase("SETUP", "Initializing Docker environment")

        # Report port allocations
        self.reporter.port_allocation(self.ports)

        # Create temporary directory for docker-compose.yml
        self.reporter.docker_operation("Creating temporary directory")
        self.temp_dir = tempfile.mkdtemp()

        # Get fixture directory
        fixtures_dir = Path(__file__).parent.parent / "fixtures" / "dataplane"
        temp_path = Path(self.temp_dir)

        # Copy Docker build files to temp directory only if not using pre-built images
        if not self.use_prebuilt_images:
            self.reporter.docker_operation("Copying Docker build context")
            for dir_name in ["dataplane", "haproxy"]:
                self.reporter.debug(f"Copying {dir_name} directory")
                shutil.copytree(fixtures_dir / dir_name, temp_path / dir_name)
        else:
            self.reporter.docker_operation("Using pre-built Docker images")

        # Generate docker-compose.yml
        self.reporter.docker_operation("Generating docker-compose.yml")
        template_path = fixtures_dir / "docker-compose-template.yml"
        compose_content = generate_compose_file(
            self.ports, template_path, self.use_prebuilt_images
        )

        self.compose_file = temp_path / "docker-compose.yml"
        with open(self.compose_file, "w") as f:
            f.write(compose_content)

        self.reporter.compose_file(self.compose_file)

        # Initialize Docker client with compose file and project name
        self.reporter.docker_operation("Initializing Docker client")
        self.docker = DockerClient(
            compose_files=[str(self.compose_file)],
            compose_project_name=self.project_name,
        )

        # Build and start containers with retry logic
        self.reporter.docker_operation("Building and starting containers")
        max_retries = 5  # Increased from 3 to 5
        template_path = fixtures_dir / "docker-compose-template.yml"

        for attempt in range(max_retries):
            try:
                # Clean up any orphaned containers first
                try:
                    self.docker.compose.down(volumes=True, remove_orphans=True)
                    # Small delay to ensure cleanup completes
                    await asyncio.sleep(random.uniform(0.5, 1.0))
                except Exception:
                    pass  # Ignore if nothing to clean

                # Start containers (skip build if using pre-built images)
                if self.use_prebuilt_images:
                    self.docker.compose.up(detach=True, remove_orphans=True)
                else:
                    self.docker.compose.up(detach=True, build=True, remove_orphans=True)
                break

            except Exception as e:
                error_msg = str(e).lower()
                if (
                    "port is already allocated" in error_msg
                    or "bind" in error_msg
                    and "failed" in error_msg
                    or "external connectivity" in error_msg
                ) and attempt < max_retries - 1:
                    self.reporter.warning(
                        f"Port conflict detected (attempt {attempt + 1}/{max_retries}), retrying with new ports..."
                    )

                    # Re-allocate ports and regenerate compose file
                    # Wait longer before retrying to reduce contention
                    delay = (2**attempt) + random.uniform(1.0, 3.0)
                    await asyncio.sleep(delay)

                    # Re-allocate ports with higher retry count for aggressive scenarios
                    self.ports = allocate_test_ports(max_retries=8)
                    self.reporter.port_allocation(self.ports)

                    compose_content = generate_compose_file(
                        self.ports, template_path, self.use_prebuilt_images
                    )
                    with open(self.compose_file, "w") as f:
                        f.write(compose_content)

                    # Recreate Docker client with new compose file
                    self.docker = DockerClient(
                        compose_files=[str(self.compose_file)],
                        compose_project_name=self.project_name,
                    )

                    continue

                # If it's not a port conflict or we've exhausted retries, re-raise
                self.reporter.error(f"Failed to start containers: {e}")
                raise

        # Wait for services to be ready
        self.reporter.phase("HEALTH_CHECK", "Waiting for services to become ready")

        # Wait for services to be ready
        validation_ready = await wait_for_dataplane_api(
            f"http://localhost:{self.ports['validation_port']}",
            auth=("admin", "adminpass"),
            timeout=10,
            reporter=self.reporter,
            service_name="Validation Dataplane API",
        )

        production_ready = await wait_for_dataplane_api(
            f"http://localhost:{self.ports['production_port']}",
            auth=("admin", "adminpass"),
            timeout=10,
            reporter=self.reporter,
            service_name="Production Dataplane API",
        )

        all_ready = validation_ready and production_ready

        if not all_ready:
            failed_services = []
            # Check which services failed
            if not validation_ready:
                failed_services.append("Validation Dataplane API")
                self.failed_services.append("Validation Dataplane API")
            if not production_ready:
                failed_services.append("Production Dataplane API")
                self.failed_services.append("Production Dataplane API")
        else:
            failed_services = []

        # Collect logs if any service failed
        if failed_services:
            self.reporter.phase("DIAGNOSIS", "Collecting diagnostic information")

            # Collect container logs
            service_containers = [
                "validation-dataplane-api",
                "production-dataplane-api",
                "validation-haproxy",
                "production-haproxy",
            ]

            for container in service_containers:
                try:
                    logs = get_container_logs(self.docker, container, self.reporter)
                    self.container_logs[container] = logs
                except Exception as e:
                    self.reporter.warning(f"Could not get logs for {container}: {e}")
                    self.container_logs[container] = f"Failed to get logs: {e}"

            # Format troubleshooting information
            from .progress import format_troubleshooting_info

            troubleshooting_info = format_troubleshooting_info(
                self.compose_file, self.ports, failed_services, self.container_logs
            )

            self.reporter.error("Some services failed to start")
            print(troubleshooting_info)

            raise RuntimeError(
                f"Services failed to start: {', '.join(failed_services)}\n"
                f"See troubleshooting information above for details."
            )

        self.reporter.phase("READY", f"All services ready for test: {self.test_name}")
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Clean up Docker environment with progress reporting."""
        self.reporter.phase("TEARDOWN", "Cleaning up Docker environment")

        # Stop and remove containers with retry logic
        if self.docker and self.compose_file:
            max_cleanup_retries = 2
            for attempt in range(max_cleanup_retries):
                try:
                    self.reporter.docker_operation("Stopping containers")
                    self.docker.compose.down(volumes=True, remove_orphans=True)
                    break
                except Exception as e:
                    if attempt < max_cleanup_retries - 1:
                        self.reporter.warning(
                            f"Cleanup attempt {attempt + 1} failed, retrying: {e}"
                        )
                        await asyncio.sleep(1.0)
                        continue
                    else:
                        self.reporter.warning(
                            f"Error during container cleanup after {max_cleanup_retries} attempts: {e}"
                        )

        # Clean up temporary directory
        if self.temp_dir:
            try:
                self.reporter.docker_operation("Removing temporary files")
                shutil.rmtree(self.temp_dir)
            except Exception as e:
                self.reporter.warning(f"Error during temp directory cleanup: {e}")

        if exc_type is not None:
            self.reporter.error(f"Test failed with {exc_type.__name__}: {exc_val}")
        else:
            self.reporter.debug("Docker environment cleaned up successfully")
