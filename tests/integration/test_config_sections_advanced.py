"""
Integration tests for advanced HAProxy configuration sections.

This test module verifies that advanced HAProxy configuration sections
like peers, resolvers, cache, and ring can be deployed successfully
via the dataplane API config synchronizer.
"""

import pytest

from .conftest import assert_config_sync_success, assert_config_contains_pattern


@pytest.mark.integration
@pytest.mark.asyncio
async def test_peers_section_basic(
    docker_compose_dataplane,
    config_synchronizer,
    haproxy_context_factory,
):
    """Test basic peers section for synchronization."""
    ports, compose_manager = docker_compose_dataplane

    peers_config = """
global
    stats socket /etc/haproxy/haproxy-master.sock mode 600 level admin

defaults
    mode http
    timeout connect 5000ms
    timeout client 50000ms
    timeout server 50000ms

peers mypeers
    peer local 127.0.0.1:1024
    peer remote 127.0.0.1:1025

frontend main
    bind *:80
    default_backend servers

frontend status
    bind *:8404
    http-request return status 200 content-type text/plain string "OK" if { path /healthz }

backend servers
    server web1 127.0.0.1:8080 check
"""

    context = haproxy_context_factory(config_content=peers_config)
    result = await config_synchronizer.sync_configuration(context)
    assert_config_sync_success(result)

    await assert_config_contains_pattern(
        compose_manager, r"peers\s+mypeers", "peers section definition"
    )
    await assert_config_contains_pattern(
        compose_manager, r"peer\s+local\s+127\.0\.0\.1:1024", "local peer definition"
    )


@pytest.mark.integration
@pytest.mark.asyncio
async def test_resolvers_section_basic(
    docker_compose_dataplane,
    config_synchronizer,
    haproxy_context_factory,
):
    """Test basic resolvers section for DNS resolution."""
    ports, compose_manager = docker_compose_dataplane

    resolvers_config = """
global
    stats socket /etc/haproxy/haproxy-master.sock mode 600 level admin

defaults
    mode http
    timeout connect 5000ms
    timeout client 50000ms
    timeout server 50000ms

resolvers mydns
    nameserver dns1 8.8.8.8:53
    timeout resolve 1s
    timeout retry 1s

frontend main
    bind *:80
    default_backend servers

frontend status
    bind *:8404
    http-request return status 200 content-type text/plain string "OK" if { path /healthz }

backend servers
    server web1 127.0.0.1:8080 check
"""

    context = haproxy_context_factory(config_content=resolvers_config)
    result = await config_synchronizer.sync_configuration(context)
    assert_config_sync_success(result)

    await assert_config_contains_pattern(
        compose_manager, r"resolvers\s+mydns", "resolvers section definition"
    )
    await assert_config_contains_pattern(
        compose_manager, r"nameserver\s+dns1\s+8\.8\.8\.8:53", "nameserver definition"
    )


@pytest.mark.integration
@pytest.mark.asyncio
async def test_cache_section_basic(
    docker_compose_dataplane,
    config_synchronizer,
    haproxy_context_factory,
):
    """Test basic cache section for HTTP caching."""
    ports, compose_manager = docker_compose_dataplane

    cache_config = """
global
    stats socket /etc/haproxy/haproxy-master.sock mode 600 level admin

defaults
    mode http
    timeout connect 5000ms
    timeout client 50000ms
    timeout server 50000ms

cache mycache
    total-max-size 64
    max-age 3600

frontend main
    bind *:80
    default_backend servers

frontend status
    bind *:8404
    http-request return status 200 content-type text/plain string "OK" if { path /healthz }

backend servers
    http-request cache-use mycache
    http-response cache-store mycache
    server web1 127.0.0.1:8080 check
"""

    context = haproxy_context_factory(config_content=cache_config)
    result = await config_synchronizer.sync_configuration(context)
    assert_config_sync_success(result)

    await assert_config_contains_pattern(
        compose_manager, r"cache\s+mycache", "cache section definition"
    )
    await assert_config_contains_pattern(
        compose_manager, r"total-max-size\s+64", "cache total-max-size"
    )


@pytest.mark.integration
@pytest.mark.asyncio
async def test_ring_section_basic(
    docker_compose_dataplane,
    config_synchronizer,
    haproxy_context_factory,
):
    """Test basic ring section for log ring buffers."""
    ports, compose_manager = docker_compose_dataplane

    ring_config = """
global
    stats socket /etc/haproxy/haproxy-master.sock mode 600 level admin

defaults
    mode http
    timeout connect 5000ms
    timeout client 50000ms
    timeout server 50000ms

ring myring
    description "Application logs"
    format raw
    size 32764

frontend main
    bind *:80
    default_backend servers

frontend status
    bind *:8404
    http-request return status 200 content-type text/plain string "OK" if { path /healthz }

backend servers
    server web1 127.0.0.1:8080 check
"""

    context = haproxy_context_factory(config_content=ring_config)
    result = await config_synchronizer.sync_configuration(context)
    assert_config_sync_success(result)

    await assert_config_contains_pattern(
        compose_manager, r"ring\s+myring", "ring section definition"
    )
    await assert_config_contains_pattern(
        compose_manager, r"description\s+\"Application logs\"", "ring description"
    )


@pytest.mark.integration
@pytest.mark.asyncio
async def test_global_worker_processes(
    docker_compose_dataplane,
    config_synchronizer,
    haproxy_context_factory,
):
    """Test global section with nbproc/nbthread settings."""
    ports, compose_manager = docker_compose_dataplane

    worker_config = """
global
    daemon
    nbthread 2
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

    context = haproxy_context_factory(config_content=worker_config)
    result = await config_synchronizer.sync_configuration(context)
    assert_config_sync_success(result)

    await assert_config_contains_pattern(
        compose_manager, r"nbthread\s+2", "nbthread configuration"
    )


@pytest.mark.integration
@pytest.mark.asyncio
async def test_defaults_option_httplog(
    docker_compose_dataplane,
    config_synchronizer,
    haproxy_context_factory,
):
    """Test defaults section with option httplog."""
    ports, compose_manager = docker_compose_dataplane

    httplog_config = """
global
    stats socket /etc/haproxy/haproxy-master.sock mode 600 level admin

defaults
    mode http
    option httplog
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

    context = haproxy_context_factory(config_content=httplog_config)
    result = await config_synchronizer.sync_configuration(context)
    assert_config_sync_success(result)

    await assert_config_contains_pattern(
        compose_manager, r"option\s+httplog", "option httplog"
    )


@pytest.mark.integration
@pytest.mark.asyncio
async def test_backend_option_httpchk(
    docker_compose_dataplane,
    config_synchronizer,
    haproxy_context_factory,
):
    """Test backend with option httpchk for health checks."""
    ports, compose_manager = docker_compose_dataplane

    httpchk_config = """
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
    option httpchk GET /health
    server web1 127.0.0.1:8080 check
"""

    context = haproxy_context_factory(config_content=httpchk_config)
    result = await config_synchronizer.sync_configuration(context)
    assert_config_sync_success(result)

    await assert_config_contains_pattern(
        compose_manager, r"option\s+httpchk\s+GET\s+/health", "option httpchk"
    )


@pytest.mark.integration
@pytest.mark.asyncio
async def test_mailers_section_basic(
    docker_compose_dataplane,
    config_synchronizer,
    haproxy_context_factory,
):
    """Test basic mailers section for email notifications."""
    ports, compose_manager = docker_compose_dataplane

    mailers_config = """
global
    stats socket /etc/haproxy/haproxy-master.sock mode 600 level admin

defaults
    mode http
    timeout connect 5000ms
    timeout client 50000ms
    timeout server 50000ms

mailers mymailers
    mailer smtp1 192.168.1.100:25
    timeout mail 20s

frontend main
    bind *:80
    default_backend servers

frontend status
    bind *:8404
    http-request return status 200 content-type text/plain string "OK" if { path /healthz }

backend servers
    server web1 127.0.0.1:8080 check
"""

    context = haproxy_context_factory(config_content=mailers_config)
    result = await config_synchronizer.sync_configuration(context)
    assert_config_sync_success(result)

    await assert_config_contains_pattern(
        compose_manager, r"mailers\s+mymailers", "mailers section definition"
    )
    await assert_config_contains_pattern(
        compose_manager, r"mailer\s+smtp1\s+192\.168\.1\.100:25", "mailer definition"
    )


@pytest.mark.integration
@pytest.mark.asyncio
async def test_errorfile_configuration(
    docker_compose_dataplane,
    config_synchronizer,
    haproxy_context_factory,
):
    """Test errorfile configuration in defaults section."""
    ports, compose_manager = docker_compose_dataplane

    errorfile_config = """
global
    stats socket /etc/haproxy/haproxy-master.sock mode 600 level admin

defaults
    mode http
    timeout connect 5000ms
    timeout client 50000ms
    timeout server 50000ms
    errorfile 503 /etc/haproxy/errors/503.http

frontend main
    bind *:80
    default_backend servers

frontend status
    bind *:8404
    http-request return status 200 content-type text/plain string "OK" if { path /healthz }

backend servers
    server web1 127.0.0.1:8080 check
"""

    context = haproxy_context_factory(config_content=errorfile_config)
    result = await config_synchronizer.sync_configuration(context)
    assert_config_sync_success(result)

    await assert_config_contains_pattern(
        compose_manager,
        r"errorfile\s+503\s+/etc/haproxy/errors/503\.http",
        "errorfile configuration",
    )
