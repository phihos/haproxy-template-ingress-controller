"""
Integration test fixtures for HAProxy Template IC.

This module provides fixtures for integration tests that use real Docker containers
to test interactions with HAProxy and Dataplane API.
"""

import asyncio
import logging
import os
import threading
from pathlib import Path
from typing import Dict, Optional, Tuple

import httpx
import pytest
import pytest_asyncio
from pydantic import SecretStr
from pytest import CollectReport, StashKey

# Import for shared session fixtures
from pytest_shared_session_scope import (
    SetupToken,
    shared_session_scope_pickle,
)
from python_on_whales import DockerClient

from haproxy_template_ic.credentials import DataplaneAuth
from haproxy_template_ic.dataplane import (
    DataplaneClient,
    DataplaneEndpoint,
)
from haproxy_template_ic.metrics import MetricsCollector

# HAProxyInstance removed in simplification - using direct URLs now
from .utils import (
    DockerComposeManager,
    allocate_test_ports,
    read_config_file,
    wait_for_dataplane_api,
)

# Store test results for --keep-containers on-failure
phase_report_key = StashKey[Dict[str, CollectReport]]()


def pytest_addoption(parser):
    """Add pytest command line options for integration tests."""
    parser.addoption(
        "--keep-containers",
        action="store",
        default="",
        choices=["", "always", "on-failure"],
        help="Keep Docker containers after testing. Options: always, on-failure (default: remove)",
    )
    parser.addoption(
        "--show-container-logs",
        action="store_true",
        default=False,
        help="Show container logs during test execution (useful with -s)",
    )
    parser.addoption(
        "--verbose-docker",
        action="store_true",
        default=False,
        help="Show detailed Docker operations and debugging information",
    )


@pytest.hookimpl(wrapper=True, tryfirst=True)
def pytest_runtest_makereport(item, call):
    """Store test results for each phase to support --keep-containers on-failure."""
    rep = yield
    item.stash.setdefault(phase_report_key, {})[rep.when] = rep
    return rep


@pytest_asyncio.fixture
async def docker_compose_dataplane(
    request, docker_resource_semaphore, shared_docker_images
):
    """
    Fixture that provides a docker-compose setup with HAProxy and Dataplane API.

    Supports --keep-containers option:
    - "" (default): Always remove containers
    - "always": Never remove containers
    - "on-failure": Keep containers only if test failed

    Returns a tuple of (ports, compose_manager) where ports is a dict with:
    - validation_port: Port for validation Dataplane API
    - validation_haproxy_port: Port for validation HAProxy HTTP
    - validation_health_port: Port for validation HAProxy health endpoint
    - production_port: Port for production Dataplane API
    - http_port: Port for production HAProxy HTTP
    - health_port: Port for production HAProxy health endpoint
    """
    # Get test name for progress reporting
    test_name = request.node.name if hasattr(request.node, "name") else "unknown"

    # Acquire semaphore to limit concurrent Docker operations
    docker_resource_semaphore.acquire()
    try:
        # Allocate unique ports for this test
        ports = allocate_test_ports()

        # Create compose manager with test name and shared images
        compose_manager = DockerComposeManager(
            ports, test_name=test_name, shared_images=shared_docker_images
        )

        # Start containers
        try:
            await compose_manager.__aenter__()
            yield ports, compose_manager
        finally:
            # Determine if we should keep containers
            keep_containers = request.config.getoption("--keep-containers")

            if keep_containers == "always":
                print("\n🔒 Keeping containers as requested (--keep-containers=always)")
                print(f"📄 Compose file: {compose_manager.compose_file}")
                print(
                    f"🧹 To manually clean up: docker compose -f {compose_manager.compose_file} down -v"
                )
            elif keep_containers == "on-failure":
                # Check if test failed
                report = request.node.stash.get(phase_report_key, {})
                test_failed = ("setup" in report and report["setup"].failed) or (
                    "call" in report and report["call"].failed
                )

                if test_failed:
                    print(
                        "\n🔒 Keeping containers due to test failure (--keep-containers=on-failure)"
                    )
                    print(f"📄 Compose file: {compose_manager.compose_file}")
                    print(
                        f"🧹 To manually clean up: docker compose -f {compose_manager.compose_file} down -v"
                    )
                else:
                    # Test passed, clean up
                    await compose_manager.__aexit__(None, None, None)
            else:
                # Default: always clean up
                await compose_manager.__aexit__(None, None, None)
    finally:
        # Always release the semaphore
        docker_resource_semaphore.release()


async def assert_dataplane_api_ready(
    base_url: str, auth: tuple[str, str], compose_manager: DockerComposeManager
):
    # Verify service is ready (additional check if needed)
    ready = await wait_for_dataplane_api(
        base_url,
        auth,
        timeout=30,
        service_name="Production Dataplane API (client fixture)",
    )
    assert ready, "Production Dataplane API not ready for client fixture"


@pytest_asyncio.fixture
async def production_dataplane_client_raw(docker_compose_dataplane):
    """Dataplane API client for production instance."""
    ports, compose_manager = docker_compose_dataplane

    base_url = f"http://localhost:{ports['production_port']}"
    auth = ("admin", "adminpass")

    await assert_dataplane_api_ready(base_url, auth, compose_manager)

    async with httpx.AsyncClient(base_url=base_url, auth=auth, timeout=30.0) as client:
        yield client


@pytest_asyncio.fixture
async def validation_dataplane_client_raw(docker_compose_dataplane):
    """Validation Dataplane API client (raw httpx)."""
    ports, compose_manager = docker_compose_dataplane

    base_url = f"http://localhost:{ports['validation_port']}"
    auth = ("admin", "adminpass")

    await assert_dataplane_api_ready(base_url, auth, compose_manager)

    async with httpx.AsyncClient(base_url=base_url, auth=auth, timeout=30.0) as client:
        yield client


@pytest_asyncio.fixture
async def validation_dataplane_client(docker_compose_dataplane):
    """Ready-to-use DataplaneClient instance for validation integration tests."""
    ports, compose_manager = docker_compose_dataplane

    base_url = f"http://localhost:{ports['validation_port']}"
    # Check readiness with base URL (without /v3)
    await assert_dataplane_api_ready(base_url, ("admin", "adminpass"), compose_manager)

    # Add /v3 for the actual client
    if not base_url.endswith("/v3"):
        base_url += "/v3"

    auth = DataplaneAuth(username="admin", password=SecretStr("adminpass"))
    endpoint = DataplaneEndpoint(url=base_url, dataplane_auth=auth)
    metrics = MetricsCollector()
    client = DataplaneClient(endpoint, metrics)

    yield client


@pytest_asyncio.fixture
async def production_dataplane_client(docker_compose_dataplane):
    """Ready-to-use DataplaneClient instance for integration tests."""
    ports, compose_manager = docker_compose_dataplane

    base_url = f"http://localhost:{ports['production_port']}"
    # Check readiness with base URL (without /v3)
    await assert_dataplane_api_ready(base_url, ("admin", "adminpass"), compose_manager)

    # Add /v3 for the actual client
    if not base_url.endswith("/v3"):
        base_url += "/v3"

    auth = DataplaneAuth(username="admin", password=SecretStr("adminpass"))
    endpoint = DataplaneEndpoint(url=base_url, dataplane_auth=auth)
    metrics = MetricsCollector()
    client = DataplaneClient(endpoint, metrics)

    yield client


@pytest_asyncio.fixture
async def mock_haproxy_urls(docker_compose_dataplane) -> Tuple[str, str]:
    """
    HAProxy dataplane URLs pointing to Docker containers.

    Returns (validation_url, production_url) that can be used
    with ConfigSynchronizer tests.
    """
    ports, _ = docker_compose_dataplane

    validation_url = f"http://localhost:{ports['validation_port']}"
    production_url = f"http://localhost:{ports['production_port']}"

    return validation_url, production_url


@pytest.fixture
def haproxy_configs() -> Dict[str, str]:
    """Load HAProxy configuration fixtures."""
    return {
        "valid": read_config_file("haproxy-valid.cfg"),
        "invalid": read_config_file("haproxy-invalid.cfg"),
        "with_health": read_config_file("haproxy-with-health.cfg"),
    }


@pytest.fixture
def haproxy_config_with_acl() -> str:
    """HAProxy configuration with ACL file reference for ConfigSynchronizer testing."""
    return """
global
    stats socket /etc/haproxy/haproxy-master.sock mode 600 level admin

defaults
    mode http
    timeout connect 5000ms
    timeout client 50000ms
    timeout server 50000ms

frontend main
    bind *:80
    # Reference ACL file from general storage directory
    acl blocked_ips src -f /etc/haproxy/general/blocked.acl
    http-request deny if blocked_ips
    default_backend servers

frontend status
    bind *:8404
    http-request return status 200 content-type text/plain string "OK" if { path /healthz }

backend servers
    balance roundrobin
    server web1 192.168.1.100:8080 check
"""


@pytest.fixture
def haproxy_config_clean() -> str:
    """HAProxy configuration without ACL file references for testing."""
    return """
global
    stats socket /etc/haproxy/haproxy-master.sock mode 600 level admin

defaults
    mode http
    timeout connect 5000ms
    timeout client 50000ms
    timeout server 50000ms

frontend main
    bind *:80
    default_backend servers

frontend status
    bind *:8404
    http-request return status 200 content-type text/plain string "OK" if { path /healthz }

backend servers
    balance roundrobin
    server web1 192.168.1.100:8080 check
"""


@pytest_asyncio.fixture
async def config_synchronizer(mock_haproxy_urls):
    """ConfigSynchronizer using existing URL infrastructure for integration testing.

    This fixture creates a ConfigSynchronizer with validation and production endpoints
    using the existing mock_haproxy_urls fixture, leveraging the established Docker
    container infrastructure.
    """
    from haproxy_template_ic.dataplane.synchronizer import ConfigSynchronizer
    from haproxy_template_ic.dataplane.endpoint import (
        DataplaneEndpoint,
        DataplaneEndpointSet,
    )
    from haproxy_template_ic.credentials import DataplaneAuth
    from pydantic import SecretStr

    validation_url, production_url = mock_haproxy_urls

    # Create auth objects
    auth = DataplaneAuth(username="admin", password=SecretStr("adminpass"))

    # Create endpoints with /v3 suffix for API
    validation_endpoint = DataplaneEndpoint(
        url=f"{validation_url}/v3", dataplane_auth=auth
    )
    production_endpoint = DataplaneEndpoint(
        url=f"{production_url}/v3", dataplane_auth=auth
    )

    # Create endpoint set
    endpoint_set = DataplaneEndpointSet(
        validation=validation_endpoint, production=[production_endpoint]
    )

    # Create and return ConfigSynchronizer
    metrics = MetricsCollector()
    synchronizer = ConfigSynchronizer(endpoint_set, metrics)

    yield synchronizer


@pytest.fixture
def haproxy_context_factory():
    """Factory for creating HAProxyConfigContext objects for testing.

    This factory provides a convenient way to create HAProxyConfigContext instances
    with various configurations and content types for ConfigSynchronizer testing.
    """
    from haproxy_template_ic.models.context import HAProxyConfigContext, RenderedConfig

    def _create_context(
        config_content: str,
        acl_files: Optional[Dict[str, str]] = None,
        map_files: Optional[Dict[str, str]] = None,
        cert_files: Optional[Dict[str, str]] = None,
        other_files: Optional[Dict[str, str]] = None,
    ) -> HAProxyConfigContext:
        """Create HAProxyConfigContext with specified content.

        Args:
            config_content: Main HAProxy configuration content
            acl_files: Dictionary of ACL filename -> content
            map_files: Dictionary of map filename -> content
            cert_files: Dictionary of certificate filename -> content
            other_files: Dictionary of other filename -> content

        Returns:
            HAProxyConfigContext with rendered content
        """
        from haproxy_template_ic.models.templates import RenderedContent, ContentType
        from haproxy_template_ic.models.context import TemplateContext

        # Create main config
        rendered_config = RenderedConfig(content=config_content)

        # Create rendered content list for all additional files
        rendered_content = []

        if acl_files:
            rendered_content.extend(
                [
                    RenderedContent(
                        filename=filename, content=content, content_type=ContentType.ACL
                    )
                    for filename, content in acl_files.items()
                ]
            )

        if map_files:
            rendered_content.extend(
                [
                    RenderedContent(
                        filename=filename, content=content, content_type=ContentType.MAP
                    )
                    for filename, content in map_files.items()
                ]
            )

        if cert_files:
            rendered_content.extend(
                [
                    RenderedContent(
                        filename=filename,
                        content=content,
                        content_type=ContentType.CERTIFICATE,
                    )
                    for filename, content in cert_files.items()
                ]
            )

        if other_files:
            rendered_content.extend(
                [
                    RenderedContent(
                        filename=filename,
                        content=content,
                        content_type=ContentType.FILE,
                    )
                    for filename, content in other_files.items()
                ]
            )

        # Create minimal template context (empty resources)
        template_context = TemplateContext()

        return HAProxyConfigContext(
            template_context=template_context,
            rendered_config=rendered_config,
            rendered_content=rendered_content,
        )

    return _create_context


def assert_config_sync_success(result, allow_failures: bool = False):
    """Assert ConfigSynchronizer result indicates successful deployment.

    Args:
        result: ConfigSynchronizerResult from sync_configuration()
        allow_failures: If True, allows failed deployments (for negative tests)
    """
    if not allow_failures:
        assert result.failed == 0, (
            f"Deployment failed for {result.failed} endpoints: {result.errors}"
        )
        assert result.errors == [], (
            f"DataplaneAPIErrors occurred during deployment: {result.errors}"
        )


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
def docker_resource_semaphore():
    """Limit concurrent Docker operations to prevent resource exhaustion."""

    # Allow max 6 concurrent Docker operations to reduce port contention
    semaphore = threading.Semaphore(6)
    return semaphore


@pytest.fixture(scope="session")
def docker_client():
    """Provide a Docker client for container operations."""
    return DockerClient()


@pytest.fixture(scope="session")
def docker_cleanup_session(docker_client):
    """Clean up Docker resources at session start to improve performance."""
    try:
        # Remove containers from previous integration test runs
        containers = docker_client.container.list(
            all=True, filters={"label": "com.docker.compose.project~=test_"}
        )
        for container in containers:
            try:
                docker_client.container.remove(container.name, force=True)
            except Exception:
                pass

        # Remove old test images (keep only current session images)
        images = docker_client.image.list(filters={"dangling": True})
        for image in images:
            if any("test" in str(tag) for tag in image.tags):
                try:
                    docker_client.image.remove(image.id, force=True)
                except Exception:
                    pass

        # Prune unused volumes
        docker_client.volume.prune()

    except Exception as e:
        # Don't fail tests if cleanup fails
        print(f"Warning: Docker cleanup failed: {e}")

    yield

    # No cleanup needed on exit - let Docker handle it


@shared_session_scope_pickle()
def shared_docker_images(request, docker_client, docker_cleanup_session):
    """
    Build Docker images once per test session, shared across pytest-xdist workers.

    This fixture ensures that HAProxy and Dataplane API images are built only once
    at the start of the test session, even when running with pytest-xdist parallel
    execution. The built images are cached and reused across all test workers.

    This fixture is only activated for tests that explicitly request it or tests
    marked with 'integration' marker.
    """
    images = yield
    if images is SetupToken.FIRST:
        print("\n🐳 Building shared Docker images for integration tests...")

        # Get paths to Dockerfiles
        fixtures_dir = Path(__file__).parent / "fixtures" / "dataplane"

        # Build Docker images with buildx if available
        use_buildx = (
            os.environ.get("DOCKER_BUILDKIT") == "1" or os.environ.get("CI") == "true"
        )

        if use_buildx:
            print("📦 Building HAProxy image with Buildx...")
            try:
                # Configure cache based on environment
                if os.environ.get("GITHUB_ACTIONS") == "true":
                    docker_client.buildx.build(
                        context_path=str(fixtures_dir / "haproxy"),
                        tags=["test-haproxy:integration"],
                        cache_from="type=gha,scope=haproxy-test",
                        cache_to="type=gha,mode=max,scope=haproxy-test",
                        load=True,
                    )
                else:
                    docker_client.buildx.build(
                        context_path=str(fixtures_dir / "haproxy"),
                        tags=["test-haproxy:integration"],
                        cache_from="type=local,src=/tmp/haproxy-test-cache",
                        cache_to="type=local,dest=/tmp/haproxy-test-cache",
                        load=True,
                    )
            except Exception as e:
                print(f"⚠️  Buildx failed, using standard build: {e}")
                docker_client.build(
                    context_path=str(fixtures_dir / "haproxy"),
                    tags=["test-haproxy:integration"],
                )

            print("📦 Building Dataplane API image with Buildx...")
            try:
                # Configure cache based on environment
                if os.environ.get("GITHUB_ACTIONS") == "true":
                    docker_client.buildx.build(
                        context_path=str(fixtures_dir / "dataplane"),
                        tags=["test-dataplane:integration"],
                        cache_from="type=gha,scope=dataplane-test",
                        cache_to="type=gha,mode=max,scope=dataplane-test",
                        load=True,
                    )
                else:
                    docker_client.buildx.build(
                        context_path=str(fixtures_dir / "dataplane"),
                        tags=["test-dataplane:integration"],
                        cache_from="type=local,src=/tmp/dataplane-test-cache",
                        cache_to="type=local,dest=/tmp/dataplane-test-cache",
                        load=True,
                    )
            except Exception as e:
                print(f"⚠️  Buildx failed, using standard build: {e}")
                docker_client.build(
                    context_path=str(fixtures_dir / "dataplane"),
                    tags=["test-dataplane:integration"],
                )
        else:
            print("📦 Building HAProxy image...")
            docker_client.build(
                context_path=str(fixtures_dir / "haproxy"),
                tags=["test-haproxy:integration"],
            )

            print("📦 Building Dataplane API image...")
            docker_client.build(
                context_path=str(fixtures_dir / "dataplane"),
                tags=["test-dataplane:integration"],
            )

        images = {
            "haproxy": "test-haproxy:integration",
            "dataplane": "test-dataplane:integration",
        }
        print(f"✅ Docker images built successfully: {list(images.values())}")

    yield images


def pytest_configure(config):
    """Configure pytest for integration tests."""
    config.addinivalue_line(
        "markers",
        "integration: marks tests as integration tests using real external dependencies",
    )
    # Make config available globally for progress reporting
    pytest.current_config = config

    # Configure logging for pytest-xdist compatibility

    worker_id = os.environ.get("PYTEST_XDIST_WORKER")
    if worker_id is not None:
        # Running with pytest-xdist - configure logging to show progress
        # Unfortunately, due to pytest-xdist architecture, real-time output isn't possible
        # Our logging will appear in captured logs after test completion
        logging.basicConfig(
            level=logging.WARNING,
            format="%(message)s",
            force=True,  # Override any existing configuration
        )
