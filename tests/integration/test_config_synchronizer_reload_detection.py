"""
TDD Integration tests for ConfigSynchronizer reload detection.

This test module uses Test-Driven Development to verify that HAProxy reload detection
works correctly through ConfigSynchronizer operations. Tests are written first to fail,
then reload detection implementation is added to make them pass.

Tests verify:
1. New backend deployment triggers reload detection
2. Identical config deployment avoids reload
3. Server changes use runtime API (no reload)
4. Frontend changes trigger reload detection
5. Transaction commit reload detection works
"""

import asyncio

import pytest

from .conftest import assert_config_sync_success


@pytest.mark.integration
@pytest.mark.asyncio
async def test_new_backend_triggers_reload(
    docker_compose_dataplane, config_synchronizer, haproxy_context_factory
):
    """Test that deploying a config with a new backend triggers reload detection.

    This test follows TDD:
    1. Deploy initial config without backend
    2. Deploy config with new backend
    3. Verify reload_info.reload_triggered == True
    4. Verify reload_info.reload_id is not None
    5. Verify INFO log message about reload
    """
    ports, compose_manager = docker_compose_dataplane

    # Step 1: Deploy initial config without backend
    initial_config = """
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

backend servers
    balance roundrobin
"""

    initial_context = haproxy_context_factory(config_content=initial_config)
    await config_synchronizer.sync_configuration(initial_context)

    # Step 2: Deploy config with new backend
    config_with_new_backend = """
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

backend servers
    balance roundrobin
    server web1 192.168.1.100:8080 check

backend api_servers
    balance roundrobin
    server api1 192.168.1.200:3000 check
"""

    new_backend_context = haproxy_context_factory(
        config_content=config_with_new_backend
    )
    result = await config_synchronizer.sync_configuration(new_backend_context)

    # Step 3: TDD Assertions - These WILL FAIL until reload detection is implemented
    assert hasattr(result, "reload_info"), "Result should have reload_info attribute"
    assert hasattr(result.reload_info, "reload_triggered"), (
        "ReloadInfo should have reload_triggered property"
    )
    assert hasattr(result.reload_info, "reload_id"), (
        "ReloadInfo should have reload_id attribute"
    )

    # Adding new backend should trigger reload
    assert result.reload_info.reload_triggered, (
        "Adding new backend should trigger reload"
    )
    assert result.reload_info.reload_id is not None, (
        "Reload ID should be present when reload triggered"
    )
    assert isinstance(result.reload_info.reload_id, str), "Reload ID should be string"
    assert len(result.reload_info.reload_id) > 0, "Reload ID should not be empty"


@pytest.mark.integration
@pytest.mark.asyncio
async def test_identical_config_no_reload(
    docker_compose_dataplane, config_synchronizer, haproxy_context_factory
):
    """Test that deploying identical config twice does not trigger reload on second deployment.

    This verifies that reload detection correctly identifies when no reload is needed.
    """
    ports, compose_manager = docker_compose_dataplane

    # Same config for both deployments
    test_config = """
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

backend servers
    balance roundrobin
    server web1 192.168.1.100:8080 check
"""

    # First deployment
    context1 = haproxy_context_factory(config_content=test_config)
    result1 = await config_synchronizer.sync_configuration(context1)
    assert_config_sync_success(result1)

    # Second deployment with identical config
    context2 = haproxy_context_factory(config_content=test_config)
    result2 = await config_synchronizer.sync_configuration(context2)

    # TDD Assertions - Will fail until reload detection is implemented
    assert hasattr(result2, "reload_info"), "Result should have reload_info attribute"

    # Second deployment should not trigger reload (config unchanged)
    assert not result2.reload_info.reload_triggered, (
        "Identical config should not trigger reload"
    )
    assert result2.reload_info.reload_id is None, (
        "Reload ID should be None when no reload triggered"
    )


@pytest.mark.integration
@pytest.mark.asyncio
async def test_server_weight_changes_no_reload(
    docker_compose_dataplane, config_synchronizer, haproxy_context_factory
):
    """Test that server weight changes use runtime API (no reload).

    This verifies that runtime-compatible server modifications (like weight changes)
    use HAProxy's runtime API instead of triggering full reloads.
    """
    ports, compose_manager = docker_compose_dataplane

    # Initial config with one server (no weight specified)
    initial_config = """
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

backend servers
    balance roundrobin
    server web1 192.168.1.100:8080 check
    """

    # Deploy initial config
    initial_context = haproxy_context_factory(config_content=initial_config)
    result = await config_synchronizer.sync_configuration(initial_context)
    assert_config_sync_success(result)

    await asyncio.sleep(10)

    # Config with modified server weight (same IP, runtime-compatible change)
    modified_config = """
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

backend servers
    balance roundrobin
    server web1 192.168.1.100:8080 check weight 150
    """

    # Deploy modified config
    modified_context = haproxy_context_factory(config_content=modified_config)
    result = await config_synchronizer.sync_configuration(modified_context)

    # TDD Assertions - Runtime-compatible changes should not trigger reload
    assert hasattr(result, "reload_info"), "Result should have reload_info attribute"

    # Weight changes should use runtime API (no reload)
    assert not result.reload_info.reload_triggered, (
        "Server weight changes should use runtime API without reload"
    )
    assert result.reload_info.reload_id is None, (
        "Reload ID should be None for runtime-only changes"
    )


@pytest.mark.integration
@pytest.mark.asyncio
async def test_server_changes_no_reload(
    docker_compose_dataplane, config_synchronizer, haproxy_context_factory
):
    """Test that server changes within existing backend use runtime API (no reload).

    This verifies that server modifications use HAProxy's runtime API instead of
    triggering full reloads when possible.
    """
    ports, compose_manager = docker_compose_dataplane

    # Initial config with one server
    initial_config = """
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

backend servers
    balance roundrobin
    server web1 192.168.1.100:8080 check
    """

    # Deploy initial config
    initial_context = haproxy_context_factory(config_content=initial_config)
    result = await config_synchronizer.sync_configuration(initial_context)
    assert_config_sync_success(result)

    # Config with modified server (different IP)
    modified_config = """
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

backend servers
    balance roundrobin
    server web1 192.168.1.101:8080 check weight 150
    """

    # Deploy modified config
    modified_context = haproxy_context_factory(config_content=modified_config)
    result = await config_synchronizer.sync_configuration(modified_context)

    # TDD Assertions - Will fail until runtime API detection is implemented
    assert hasattr(result, "reload_info"), "Result should have reload_info attribute"

    # Server changes should use runtime API (no reload)
    assert not result.reload_info.reload_triggered, (
        "Server changes should use runtime API without reload"
    )
    assert result.reload_info.reload_id is None, (
        "Reload ID should be None for runtime-only changes"
    )


@pytest.mark.integration
@pytest.mark.asyncio
async def test_frontend_changes_trigger_reload(
    docker_compose_dataplane, config_synchronizer, haproxy_context_factory
):
    """Test that frontend changes trigger reload detection.

    Frontend configuration changes typically require HAProxy reload.
    """
    ports, compose_manager = docker_compose_dataplane

    # Initial config with one frontend
    initial_config = """
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

backend servers
    balance roundrobin
    server web1 192.168.1.100:8080 check
    """

    # Deploy initial config
    initial_context = haproxy_context_factory(config_content=initial_config)
    result = await config_synchronizer.sync_configuration(initial_context)
    assert_config_sync_success(result)

    # Config with additional frontend
    config_with_new_frontend = """
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

frontend api
    bind *:8080
    default_backend servers

backend servers
    balance roundrobin
    server web1 192.168.1.100:8080 check
    """

    # Deploy config with new frontend
    new_frontend_context = haproxy_context_factory(
        config_content=config_with_new_frontend
    )
    result = await config_synchronizer.sync_configuration(new_frontend_context)

    # TDD Assertions - Will fail until reload detection is implemented
    assert hasattr(result, "reload_info"), "Result should have reload_info attribute"

    # Adding new frontend should trigger reload
    assert result.reload_info.reload_triggered, (
        "Adding new frontend should trigger reload"
    )
    assert result.reload_info.reload_id is not None, (
        "Reload ID should be present when reload triggered"
    )


@pytest.mark.integration
@pytest.mark.asyncio
async def test_transaction_commit_reload_detection(
    docker_compose_dataplane, config_synchronizer, haproxy_context_factory
):
    """Test that transaction-based deployments properly detect reloads.

    This verifies reload detection works for structured/transaction-based deployments.
    """
    ports, compose_manager = docker_compose_dataplane

    # Config that should trigger transaction-based deployment with reload
    config_with_multiple_changes = """
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

frontend ssl_frontend
    bind *:443
    default_backend servers

backend servers
    balance roundrobin
    server web1 192.168.1.100:8080 check
    server web2 192.168.1.101:8080 check

backend cache_servers
    balance roundrobin
    server cache1 192.168.1.200:6379 check
    """

    # Deploy complex config that requires transaction
    context = haproxy_context_factory(config_content=config_with_multiple_changes)
    result = await config_synchronizer.sync_configuration(context)

    # TDD Assertions - Will fail until transaction reload detection is implemented
    assert hasattr(result, "reload_info"), "Result should have reload_info attribute"

    # Complex changes should trigger reload via transaction
    assert result.reload_info.reload_triggered, (
        "Multiple structural changes should trigger reload"
    )
    assert result.reload_info.reload_id is not None, (
        "Transaction commit should provide reload ID"
    )


@pytest.mark.integration
@pytest.mark.asyncio
async def test_reload_logging_behavior(
    docker_compose_dataplane, config_synchronizer, haproxy_context_factory, caplog
):
    """Test that reload detection triggers appropriate INFO-level logging.

    This verifies that reload events are properly logged with endpoint context.
    """
    import logging

    # Set up logging capture
    caplog.set_level(logging.INFO)

    ports, compose_manager = docker_compose_dataplane

    # Config change that should trigger reload
    config_with_backend = """
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

backend servers
    balance roundrobin
    server web1 192.168.1.100:8080 check

backend new_backend
    balance roundrobin
    server new1 192.168.1.200:9000 check
    """

    # Deploy config that should trigger reload
    context = haproxy_context_factory(config_content=config_with_backend)
    result = await config_synchronizer.sync_configuration(context)

    # TDD Assertions - Will fail until logging is implemented
    assert hasattr(result, "reload_info"), "Result should have reload_info attribute"

    if result.reload_info.reload_triggered:
        # Check that INFO-level log message was generated for reload
        # Look for specific reload notification logs, not HTTP request logs
        reload_logs = [
            record
            for record in caplog.records
            if record.levelname == "INFO"
            and "reload triggered" in record.message.lower()
            and "haproxy_template_ic.dataplane.synchronizer" in record.name
        ]
        assert len(reload_logs) > 0, "Reload should trigger INFO-level log message"

        # Verify log contains reload ID and endpoint information
        reload_log = reload_logs[0]
        assert result.reload_info.reload_id in reload_log.message, (
            "Log should contain reload ID"
        )
        assert "http://" in reload_log.message, "Log should contain endpoint URL"
