"""Utilities for integration tests."""

import asyncio
import hashlib
import os
import random
import re
import shutil
import socket
import tempfile
import time
from pathlib import Path
from typing import Dict, Tuple, List, Optional

import filelock
import httpx
from python_on_whales import DockerClient


def format_troubleshooting_info(
    compose_file: Path,
    ports: Dict[str, int],
    failed_services: List[str],
    container_logs: Dict[str, str],
) -> str:
    """Format troubleshooting information for failed tests."""
    lines = [
        "\n" + "=" * 80,
        "🚨 INTEGRATION TEST FAILURE - TROUBLESHOOTING INFO",
        "=" * 80,
        "",
        f"📄 Docker Compose File: {compose_file}",
        "",
        "🔌 Port Allocations:",
    ]

    for name, port in ports.items():
        lines.append(f"  - {name}: {port}")

    if failed_services:
        lines.extend(
            [
                "",
                "❌ Failed Services:",
            ]
        )
        for service in failed_services:
            lines.append(f"  - {service}")

    lines.extend(
        [
            "",
            "🛠️  Debugging Commands:",
            f"  docker compose -f {compose_file} ps",
            f"  docker compose -f {compose_file} logs",
            f"  docker compose -f {compose_file} down -v",
            "",
            "🔍 Manual Service Testing:",
        ]
    )

    for name, port in ports.items():
        if "dataplane" in name or "api" in name:
            lines.append(f"  curl -u admin:adminpass http://localhost:{port}/v3/info")
        elif "health" in name:
            lines.append(f"  curl http://localhost:{port}/healthz")

    if container_logs:
        lines.extend(
            [
                "",
                "📜 Container Logs:",
                "",
            ]
        )
        for service, logs in container_logs.items():
            lines.append(f"--- {service} ---")

            # Give more space for dataplane API containers (they contain important error details)
            if "dataplane-api" in service:
                # Show last 2000 characters for dataplane API containers
                if len(logs) > 2000:
                    log_lines = logs.split("\n")
                    if len(log_lines) > 50:
                        # Show last 50 lines which is usually more useful than truncating characters
                        truncated_logs = "\n".join(log_lines[-50:])
                        lines.append("... (showing last 50 lines) ...")
                        lines.append(truncated_logs)
                    else:
                        lines.append(logs[-2000:])
                        lines.append("... (truncated to last 2000 characters)")
                else:
                    lines.append(logs)
            else:
                # Other containers get the original 1000 character limit
                lines.append(logs[:1000] + ("..." if len(logs) > 1000 else ""))

            lines.append("")  # Empty line after each service

    lines.extend(["=" * 80, ""])

    return "\n".join(lines)


def find_free_port(used_ports: set, max_retries: int = 10) -> int:
    """Find a free port with collision checking against used ports set."""
    for attempt in range(max_retries):
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                s.bind(("127.0.0.1", 0))  # Bind to localhost explicitly
                s.listen(1)
                port = s.getsockname()[1]

            # Check if port is already used by another worker
            if port not in used_ports:
                return port

        except OSError:
            pass

        # Port was taken or socket error occurred, try again
        if attempt < max_retries - 1:
            time.sleep(random.uniform(0.05, 0.15))
            continue

    raise RuntimeError(f"Could not find free port after {max_retries} attempts")


def get_worker_id() -> str:
    """Get pytest-xdist worker ID or 'master' for non-xdist runs."""
    return os.environ.get("PYTEST_XDIST_WORKER", "master")


def allocate_test_ports(max_retries: int = 10) -> Dict[str, int]:
    """
    Allocate unique ports for a test instance with file-based coordination.

    Uses file locking to coordinate port allocation between pytest-xdist workers,
    preventing race conditions and port conflicts.
    """
    worker_id = get_worker_id()
    lock_file = Path(tempfile.gettempdir()) / "integration_test_ports.lock"
    port_registry_file = Path(tempfile.gettempdir()) / "integration_test_ports.txt"

    for attempt in range(max_retries):
        try:
            # Use file lock to coordinate between workers
            with filelock.FileLock(str(lock_file), timeout=30):
                # Read currently used ports from registry
                used_ports = set()
                if port_registry_file.exists():
                    try:
                        content = port_registry_file.read_text().strip()
                        if content:
                            used_ports = set(
                                int(p) for p in content.split("\n") if p.strip()
                            )
                    except (ValueError, OSError):
                        # Corrupted file, start fresh
                        pass

                # Allocate all ports needed for this test
                port_names = [
                    "validation_port",
                    "validation_haproxy_port",
                    "validation_health_port",
                    "production_port",
                    "http_port",
                    "health_port",
                ]

                allocated_ports = {}
                for port_name in port_names:
                    port = find_free_port(used_ports, max_retries=20)
                    allocated_ports[port_name] = port
                    used_ports.add(port)

                # Verify no duplicates in our allocation
                port_values = list(allocated_ports.values())
                if len(port_values) != len(set(port_values)):
                    raise RuntimeError("Duplicate ports in allocation")

                # Write allocated ports to registry
                all_ports = (
                    used_ports if port_registry_file.exists() else set(port_values)
                )
                all_ports.update(port_values)
                port_registry_file.write_text(
                    "\n".join(str(p) for p in sorted(all_ports))
                )

                return allocated_ports

        except (filelock.Timeout, RuntimeError) as e:
            if attempt < max_retries - 1:
                # Add jitter and worker-specific delay to reduce contention
                base_delay = 0.5 + (hash(worker_id) % 100) / 1000  # 0.5-0.6s base
                jitter = random.uniform(0.2, 0.8)
                time.sleep(base_delay + jitter)
                continue
            raise RuntimeError(
                f"Failed to allocate ports after {max_retries} attempts: {e}"
            )

    # This should never be reached but added for mypy completeness
    raise RuntimeError("Failed to allocate ports: no attempts made")


def release_test_ports(ports: Dict[str, int]) -> None:
    """
    Release ports from the global registry when test is complete.

    Uses file locking to coordinate removal between pytest-xdist workers.
    """
    if not ports:
        return

    lock_file = Path(tempfile.gettempdir()) / "integration_test_ports.lock"
    port_registry_file = Path(tempfile.gettempdir()) / "integration_test_ports.txt"

    try:
        with filelock.FileLock(str(lock_file), timeout=10):
            if not port_registry_file.exists():
                return

            # Read current registry
            try:
                content = port_registry_file.read_text().strip()
                if not content:
                    return
                used_ports = set(int(p) for p in content.split("\n") if p.strip())
            except (ValueError, OSError):
                return

            # Remove our ports from the registry
            port_values = set(ports.values())
            remaining_ports = used_ports - port_values

            # Write back the remaining ports
            if remaining_ports:
                port_registry_file.write_text(
                    "\n".join(str(p) for p in sorted(remaining_ports))
                )
            else:
                # No ports left, remove the file
                port_registry_file.unlink(missing_ok=True)

    except (filelock.Timeout, OSError):
        # Port cleanup is best-effort, don't fail tests for it
        pass


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
    service_name: str = "service",
) -> bool:
    """Wait for a service to become available."""
    start_time = time.time()

    while time.time() - start_time < timeout:
        try:
            async with httpx.AsyncClient(timeout=3.0) as client:
                response = await client.get(url)
                if response.status_code < 500:  # Accept any non-server-error response
                    return True
        except (httpx.RequestError, httpx.HTTPStatusError):
            pass

        await asyncio.sleep(interval)

    return False


async def wait_for_dataplane_api(
    base_url: str,
    auth: Tuple[str, str] = ("admin", "adminpass"),
    timeout: int = 10,
    service_name: str = "Dataplane API",
) -> bool:
    """Wait for Dataplane API to become ready."""
    start_time = time.time()
    interval = 0.2  # Faster polling
    api_url = f"{base_url}/v3/info"

    while time.time() - start_time < timeout:
        try:
            async with httpx.AsyncClient(timeout=3.0, auth=auth) as client:
                response = await client.get(api_url)
                if response.status_code == 200:
                    return True
        except (httpx.RequestError, httpx.HTTPStatusError):
            pass

        await asyncio.sleep(interval)

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
) -> str:
    """Get logs from a docker-compose service for debugging."""
    try:
        logs = docker.compose.logs(services=[service_name])
        return logs
    except Exception as e:
        return f"Failed to get logs: {e}"


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
        self.docker: DockerClient | None = None  # Will be initialized with compose file
        self.failed_services: List[str] = []
        self.container_logs: Dict[str, str] = {}
        self.shared_images = shared_images or {}
        self.use_prebuilt_images = bool(shared_images)

    async def __aenter__(self):
        """Set up Docker compose environment."""
        # Create temporary directory for docker-compose.yml
        self.temp_dir = tempfile.mkdtemp()

        # Get fixture directory
        fixtures_dir = Path(__file__).parent.parent / "fixtures" / "dataplane"
        temp_path = Path(self.temp_dir)

        # Copy Docker build files to temp directory only if not using pre-built images
        if not self.use_prebuilt_images:
            for dir_name in ["dataplane", "haproxy"]:
                shutil.copytree(fixtures_dir / dir_name, temp_path / dir_name)

        # Generate docker-compose.yml
        template_path = fixtures_dir / "docker-compose-template.yml"
        compose_content = generate_compose_file(
            self.ports, template_path, self.use_prebuilt_images
        )

        self.compose_file = temp_path / "docker-compose.yml"
        with open(self.compose_file, "w") as f:
            f.write(compose_content)

        # Initialize Docker client with compose file and project name
        self.docker = DockerClient(
            compose_files=[str(self.compose_file)],
            compose_project_name=self.project_name,
        )

        # Build and start containers with retry logic
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
                    # Re-allocate ports and regenerate compose file
                    # Wait longer before retrying to reduce contention
                    delay = (2**attempt) + random.uniform(1.0, 3.0)
                    await asyncio.sleep(delay)

                    # Re-allocate ports with higher retry count for aggressive scenarios
                    self.ports = allocate_test_ports(max_retries=8)

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
                raise

        # Wait for services to be ready
        validation_ready = await wait_for_dataplane_api(
            f"http://localhost:{self.ports['validation_port']}",
            auth=("admin", "adminpass"),
            timeout=10,
            service_name="Validation Dataplane API",
        )

        production_ready = await wait_for_dataplane_api(
            f"http://localhost:{self.ports['production_port']}",
            auth=("admin", "adminpass"),
            timeout=10,
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
            # Collect container logs
            service_containers = [
                "validation-dataplane-api",
                "production-dataplane-api",
                "validation-haproxy",
                "production-haproxy",
            ]

            for container in service_containers:
                try:
                    assert self.docker is not None, (
                        "DockerComposeManager not initialized"
                    )
                    logs = get_container_logs(self.docker, container)
                    self.container_logs[container] = logs
                except Exception as e:
                    self.container_logs[container] = f"Failed to get logs: {e}"

            # Format troubleshooting information
            troubleshooting_info = format_troubleshooting_info(
                self.compose_file, self.ports, failed_services, self.container_logs
            )

            print(troubleshooting_info)

            raise RuntimeError(
                f"Services failed to start: {', '.join(failed_services)}\n"
                f"See troubleshooting information above for details."
            )

        return self

    def collect_logs_on_failure(
        self, container_names: Optional[List[str]] = None
    ) -> Dict[str, str]:
        """Collect container logs for debugging failed tests.

        Args:
            container_names: List of container names to collect logs from.
                           If None, collects from all known containers.

        Returns:
            Dictionary mapping container names to their log content.
        """
        if container_names is None:
            # Default to dataplane API containers for debugging
            container_names = [
                "validation-dataplane-api",
                "production-dataplane-api",
                "validation-haproxy",
                "production-haproxy",
            ]

        container_logs = {}

        for container in container_names:
            try:
                assert self.docker is not None, "DockerComposeManager not initialized"
                logs = get_container_logs(self.docker, container)
                if logs and logs.strip():
                    container_logs[container] = logs
                else:
                    container_logs[container] = f"No logs available for {container}"
            except Exception as e:
                container_logs[container] = f"Failed to get logs: {e}"

        return container_logs

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Clean up Docker environment."""
        # Stop and remove containers with retry logic
        if self.docker and self.compose_file:
            max_cleanup_retries = 2
            for attempt in range(max_cleanup_retries):
                try:
                    self.docker.compose.down(volumes=True, remove_orphans=True)
                    break
                except Exception:
                    if attempt < max_cleanup_retries - 1:
                        await asyncio.sleep(1.0)
                        continue

        # Clean up temporary directory
        if self.temp_dir:
            try:
                shutil.rmtree(self.temp_dir)
            except Exception:
                pass

        # Release allocated ports from global registry
        try:
            release_test_ports(self.ports)
        except Exception:
            pass


# Container interaction utilities for integration tests
async def exec_container_command(
    compose_manager: DockerComposeManager, service_name: str, command: str
) -> str:
    """Execute command in Docker container using existing DockerComposeManager.

    Args:
        compose_manager: DockerComposeManager instance from docker_compose_dataplane fixture
        service_name: Name of the Docker Compose service (e.g., "production-haproxy")
        command: Command to execute in the container

    Returns:
        Command output as string

    Raises:
        RuntimeError: If command execution fails
    """
    try:
        # Use the existing docker client from DockerComposeManager
        assert compose_manager.docker is not None, (
            "DockerComposeManager not initialized"
        )
        result = compose_manager.docker.container.execute(
            container=f"{compose_manager.project_name}-{service_name}-1",
            command=command.split() if isinstance(command, str) else command,
        )
        return str(result)
    except Exception as e:
        raise RuntimeError(
            f"Failed to execute command '{command}' in {service_name}: {e}"
        ) from e


async def read_container_file(
    compose_manager: DockerComposeManager, service_name: str, file_path: str
) -> str:
    """Read file content from Docker container filesystem.

    Args:
        compose_manager: DockerComposeManager instance from docker_compose_dataplane fixture
        service_name: Name of the Docker Compose service (e.g., "production-haproxy")
        file_path: Path to file inside the container

    Returns:
        File content as string

    Raises:
        RuntimeError: If file reading fails
    """
    try:
        # Use cat command to read file content
        content = await exec_container_command(
            compose_manager, service_name, f"cat {file_path}"
        )
        return content
    except Exception as e:
        raise RuntimeError(
            f"Failed to read file '{file_path}' from {service_name}: {e}"
        ) from e


async def haproxy_socket_command(
    compose_manager: DockerComposeManager, service_name: str, socket_cmd: str
) -> str:
    """Send command to HAProxy stats socket via socat.

    Args:
        compose_manager: DockerComposeManager instance from docker_compose_dataplane fixture
        service_name: Name of the Docker Compose service (e.g., "production-haproxy")
        socket_cmd: HAProxy socket command (e.g., "show acl", "show map")

    Returns:
        Socket command output as string

    Raises:
        RuntimeError: If socket command fails
    """
    try:
        # Use socat to send command to HAProxy stats socket
        full_command = f'echo "{socket_cmd}" | socat - /etc/haproxy/haproxy-master.sock'
        result = await exec_container_command(
            compose_manager, service_name, full_command
        )
        return result
    except Exception as e:
        raise RuntimeError(
            f"Failed to execute socket command '{socket_cmd}' on {service_name}: {e}"
        ) from e


async def get_haproxy_process_info(
    compose_manager: DockerComposeManager, service_name: str
) -> Dict[str, str]:
    """Get HAProxy process information for reload detection.

    Args:
        compose_manager: DockerComposeManager instance from docker_compose_dataplane fixture
        service_name: Name of the Docker Compose service (e.g., "production-haproxy")

    Returns:
        Dictionary with process information (pid, start_time, etc.)

    Raises:
        RuntimeError: If process info retrieval fails
    """
    try:
        # Get HAProxy process info using ps command (BusyBox compatible)
        ps_output = await exec_container_command(
            compose_manager, service_name, "ps | grep haproxy"
        )

        # Parse ps output to extract process info
        lines = ps_output.strip().split("\n")
        # Filter out the grep command itself
        haproxy_lines = [line for line in lines if line and "grep haproxy" not in line]
        if not haproxy_lines:
            raise RuntimeError("No HAProxy process found")

        # Extract key process information
        # BusyBox ps format: PID USER TIME COMMAND
        fields = haproxy_lines[0].split()
        if len(fields) < 4:
            raise RuntimeError(f"Unexpected ps output format: {ps_output}")

        return {
            "pid": fields[0],
            "start_time": fields[2],  # TIME field in BusyBox ps
            "command": " ".join(fields[3:]),
            "full_output": ps_output,
        }
    except Exception as e:
        raise RuntimeError(
            f"Failed to get process info from {service_name}: {e}"
        ) from e
