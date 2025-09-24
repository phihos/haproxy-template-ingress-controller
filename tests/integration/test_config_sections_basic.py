"""
Integration tests for basic HAProxy configuration sections.

This test module verifies that basic HAProxy configuration sections
can be deployed successfully via the dataplane API config synchronizer.
Each test focuses on a single configuration feature to isolate bugs.
"""

import pytest

from .conftest import assert_config_sync_success, assert_config_contains_pattern


@pytest.mark.integration
@pytest.mark.asyncio
async def test_global_daemon_mode(
    docker_compose_dataplane,
    config_synchronizer,
    haproxy_context_factory,
):
    """Test global section with daemon mode."""
    ports, compose_manager = docker_compose_dataplane

    daemon_config = """
global
    daemon
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
    server web1 127.0.0.1:8080 check
"""

    context = haproxy_context_factory(config_content=daemon_config)
    result = await config_synchronizer.sync_configuration(context)
    assert_config_sync_success(result)

    await assert_config_contains_pattern(
        compose_manager, r"\s*daemon\s*", "daemon mode in global section"
    )


@pytest.mark.integration
@pytest.mark.asyncio
async def test_defaults_tcp_mode(
    docker_compose_dataplane,
    config_synchronizer,
    haproxy_context_factory,
):
    """Test defaults section with TCP mode."""
    ports, compose_manager = docker_compose_dataplane

    tcp_defaults_config = """
global
    stats socket /etc/haproxy/haproxy-master.sock mode 600 level admin

defaults
    mode tcp
    timeout connect 5000ms
    timeout client 50000ms
    timeout server 50000ms

frontend main
    bind *:3306
    default_backend mysql_servers

backend mysql_servers
    server db1 127.0.0.1:3306 check
"""

    context = haproxy_context_factory(config_content=tcp_defaults_config)
    result = await config_synchronizer.sync_configuration(context)
    assert_config_sync_success(result)

    await assert_config_contains_pattern(
        compose_manager, r"mode\s+tcp", "TCP mode in defaults"
    )


@pytest.mark.integration
@pytest.mark.asyncio
async def test_backend_leastconn_algorithm(
    docker_compose_dataplane,
    config_synchronizer,
    haproxy_context_factory,
):
    """Test backend with leastconn balance algorithm."""
    ports, compose_manager = docker_compose_dataplane

    leastconn_config = """
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
    balance leastconn
    server web1 127.0.0.1:8080 check
"""

    context = haproxy_context_factory(config_content=leastconn_config)
    result = await config_synchronizer.sync_configuration(context)
    assert_config_sync_success(result)

    await assert_config_contains_pattern(
        compose_manager, r"balance\s+leastconn", "leastconn balance algorithm"
    )


@pytest.mark.integration
@pytest.mark.asyncio
async def test_backend_first_algorithm(
    docker_compose_dataplane,
    config_synchronizer,
    haproxy_context_factory,
):
    """Test backend with first balance algorithm."""
    ports, compose_manager = docker_compose_dataplane

    first_config = """
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
    balance first
    server web1 127.0.0.1:8080 check
    server web2 127.0.0.1:8081 check
"""

    context = haproxy_context_factory(config_content=first_config)
    result = await config_synchronizer.sync_configuration(context)
    assert_config_sync_success(result)

    await assert_config_contains_pattern(
        compose_manager, r"balance\s+first", "first balance algorithm"
    )


@pytest.mark.integration
@pytest.mark.asyncio
async def test_server_weight_parameter(
    docker_compose_dataplane,
    config_synchronizer,
    haproxy_context_factory,
):
    """Test server with weight parameter."""
    ports, compose_manager = docker_compose_dataplane

    weight_config = """
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
    server web1 127.0.0.1:8080 check weight 5
"""

    context = haproxy_context_factory(config_content=weight_config)
    result = await config_synchronizer.sync_configuration(context)
    assert_config_sync_success(result)

    await assert_config_contains_pattern(
        compose_manager,
        r"server\s+web1\s+127\.0\.0\.1:8080\s+check\s+weight\s+5",
        "server weight parameter",
    )


@pytest.mark.integration
@pytest.mark.asyncio
async def test_server_backup_parameter(
    docker_compose_dataplane,
    config_synchronizer,
    haproxy_context_factory,
):
    """Test server with backup parameter."""
    ports, compose_manager = docker_compose_dataplane

    backup_config = """
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
    server web1 127.0.0.1:8080 check
    server backup1 127.0.0.1:8081 check backup
"""

    context = haproxy_context_factory(config_content=backup_config)
    result = await config_synchronizer.sync_configuration(context)
    assert_config_sync_success(result)

    await assert_config_contains_pattern(
        compose_manager,
        r"server\s+backup1.*127\.0\.0\.1:8081.*backup",
        "server backup parameter",
    )


@pytest.mark.integration
@pytest.mark.asyncio
async def test_frontend_multiple_bind_addresses(
    docker_compose_dataplane,
    config_synchronizer,
    haproxy_context_factory,
):
    """Test frontend with multiple bind addresses."""
    ports, compose_manager = docker_compose_dataplane

    multi_bind_config = """
global
    stats socket /etc/haproxy/haproxy-master.sock mode 600 level admin

defaults
    mode http
    timeout connect 5000ms
    timeout client 50000ms
    timeout server 50000ms

frontend main
    bind *:80
    bind *:8080
    default_backend servers

frontend status
    bind *:8404
    http-request return status 200 content-type text/plain string "OK" if { path /healthz }

backend servers
    server web1 127.0.0.1:8001 check
"""

    context = haproxy_context_factory(config_content=multi_bind_config)
    result = await config_synchronizer.sync_configuration(context)
    assert_config_sync_success(result)

    await assert_config_contains_pattern(
        compose_manager, r"bind\s+\*:80", "first bind address"
    )
    await assert_config_contains_pattern(
        compose_manager, r"bind\s+\*:8080", "second bind address"
    )


@pytest.mark.integration
@pytest.mark.asyncio
async def test_simple_acl_definition(
    docker_compose_dataplane,
    config_synchronizer,
    haproxy_context_factory,
):
    """Test frontend with simple ACL definition."""
    ports, compose_manager = docker_compose_dataplane

    simple_acl_config = """
global
    stats socket /etc/haproxy/haproxy-master.sock mode 600 level admin

defaults
    mode http
    timeout connect 5000ms
    timeout client 50000ms
    timeout server 50000ms

frontend main
    bind *:80
    acl is_api path_beg /api
    use_backend api_servers if is_api
    default_backend web_servers

frontend status
    bind *:8404
    http-request return status 200 content-type text/plain string "OK" if { path /healthz }

backend api_servers
    server api1 127.0.0.1:8001 check

backend web_servers
    server web1 127.0.0.1:8002 check
"""

    context = haproxy_context_factory(config_content=simple_acl_config)
    result = await config_synchronizer.sync_configuration(context)
    assert_config_sync_success(result)

    await assert_config_contains_pattern(
        compose_manager, r"acl\s+is_api\s+path_beg\s+/api", "ACL definition"
    )
    await assert_config_contains_pattern(
        compose_manager, r"use_backend\s+api_servers\s+if\s+is_api", "ACL usage"
    )


@pytest.mark.integration
@pytest.mark.asyncio
async def test_timeout_variations(
    docker_compose_dataplane,
    config_synchronizer,
    haproxy_context_factory,
):
    """Test different timeout configurations in defaults."""
    ports, compose_manager = docker_compose_dataplane

    timeout_config = """
global
    stats socket /etc/haproxy/haproxy-master.sock mode 600 level admin

defaults
    mode http
    timeout connect 10s
    timeout client 1m
    timeout server 30s
    timeout http-request 10s

frontend main
    bind *:80
    default_backend servers

frontend status
    bind *:8404
    http-request return status 200 content-type text/plain string "OK" if { path /healthz }

backend servers
    server web1 127.0.0.1:8080 check
"""

    context = haproxy_context_factory(config_content=timeout_config)
    result = await config_synchronizer.sync_configuration(context)
    assert_config_sync_success(result)

    await assert_config_contains_pattern(
        compose_manager, r"timeout\s+connect\s+10s", "connect timeout"
    )
    await assert_config_contains_pattern(
        compose_manager, r"timeout\s+client\s+1m", "client timeout"
    )
    await assert_config_contains_pattern(
        compose_manager, r"timeout\s+server\s+30s", "server timeout"
    )
    await assert_config_contains_pattern(
        compose_manager, r"timeout\s+http-request\s+10s", "http-request timeout"
    )
