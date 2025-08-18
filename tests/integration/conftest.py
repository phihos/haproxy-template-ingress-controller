"""
Integration test fixtures for HAProxy Template IC.

This module provides fixtures for integration tests that use real Docker containers
to test interactions with HAProxy and Dataplane API.
"""

import asyncio
from typing import Dict, Tuple
from unittest.mock import Mock

import httpx
import pytest
import pytest_asyncio
from pytest import CollectReport, StashKey

from haproxy_template_ic.dataplane import HAProxyInstance

from .utils import (
    DockerComposeManager,
    allocate_test_ports,
    read_config_file,
    wait_for_dataplane_api,
)

# Import for shared session fixtures
from pytest_shared_session_scope import (
    SetupToken,
    shared_session_scope_pickle,
)
from python_on_whales import DockerClient
from pathlib import Path


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


@pytest_asyncio.fixture
async def validation_dataplane_client(docker_compose_dataplane):
    """Dataplane API client for validation sidecar."""
    ports, _ = docker_compose_dataplane

    base_url = f"http://localhost:{ports['validation_port']}"
    auth = ("admin", "adminpass")

    async with httpx.AsyncClient(base_url=base_url, auth=auth, timeout=30.0) as client:
        yield client


@pytest_asyncio.fixture
async def production_dataplane_client(docker_compose_dataplane):
    """Dataplane API client for production instance."""
    ports, compose_manager = docker_compose_dataplane

    base_url = f"http://localhost:{ports['production_port']}"
    auth = ("admin", "adminpass")

    # Verify service is ready (additional check if needed)
    ready = await wait_for_dataplane_api(
        base_url,
        auth,
        timeout=30,
        reporter=compose_manager.reporter,
        service_name="Production Dataplane API (client fixture)",
    )
    assert ready, "Production Dataplane API not ready for client fixture"

    async with httpx.AsyncClient(base_url=base_url, auth=auth, timeout=30.0) as client:
        yield client


@pytest_asyncio.fixture
async def mock_haproxy_instances(
    docker_compose_dataplane,
) -> Tuple[HAProxyInstance, HAProxyInstance]:
    """
    Mock HAProxy instances pointing to Docker containers.

    Returns validation and production instances that can be used
    with ConfigSynchronizer tests.
    """
    ports, _ = docker_compose_dataplane

    # Mock validation instance
    validation_pod = Mock()
    validation_pod.namespace = "test"
    validation_pod.name = "validation-haproxy"

    validation_instance = HAProxyInstance(
        pod=validation_pod,
        dataplane_url=f"http://localhost:{ports['validation_port']}/v3",
        is_validation_sidecar=True,
    )

    # Mock production instance
    production_pod = Mock()
    production_pod.namespace = "test"
    production_pod.name = "production-haproxy"

    production_instance = HAProxyInstance(
        pod=production_pod,
        dataplane_url=f"http://localhost:{ports['production_port']}/v3",
        is_validation_sidecar=False,
    )

    return validation_instance, production_instance


@pytest.fixture
def haproxy_configs() -> Dict[str, str]:
    """Load HAProxy configuration fixtures."""
    return {
        "valid": read_config_file("haproxy-valid.cfg"),
        "invalid": read_config_file("haproxy-invalid.cfg"),
        "with_health": read_config_file("haproxy-with-health.cfg"),
    }


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
def docker_resource_semaphore():
    """Limit concurrent Docker operations to prevent resource exhaustion."""
    import threading

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

        # Build Docker images
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
    import os
    import logging

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
