"""
Integration tests for HAProxy protocol-specific configurations.

This test module verifies that protocol-specific HAProxy configurations
like TCP mode, HTTP features, SSL/TLS termination, and HTTP/2 support
can be deployed successfully via the dataplane API config synchronizer.
"""

import pytest

from .conftest import assert_config_sync_success, assert_config_contains_pattern


@pytest.mark.integration
@pytest.mark.asyncio
async def test_tcp_mode_simple(
    docker_compose_dataplane,
    config_synchronizer,
    haproxy_context_factory,
):
    """Test simple TCP mode configuration."""
    ports, compose_manager = docker_compose_dataplane

    tcp_config = """
global
    stats socket /etc/haproxy/haproxy-master.sock mode 600 level admin

defaults
    mode tcp
    timeout connect 5000ms
    timeout client 50000ms
    timeout server 50000ms

frontend mysql_front
    bind *:3306
    default_backend mysql_servers

backend mysql_servers
    balance roundrobin
    server db1 127.0.0.1:3306 check
"""

    context = haproxy_context_factory(config_content=tcp_config)
    result = await config_synchronizer.sync_configuration(context)
    assert_config_sync_success(result)

    await assert_config_contains_pattern(
        compose_manager, r"mode\s+tcp", "TCP mode configuration"
    )
    await assert_config_contains_pattern(
        compose_manager, r"bind\s+\*:3306", "MySQL port binding"
    )


@pytest.mark.integration
@pytest.mark.asyncio
async def test_http_mode_with_compression(
    docker_compose_dataplane,
    config_synchronizer,
    haproxy_context_factory,
):
    """Test HTTP mode with compression enabled."""
    ports, compose_manager = docker_compose_dataplane

    compression_config = """
global
    stats socket /etc/haproxy/haproxy-master.sock mode 600 level admin

defaults
    mode http
    timeout connect 5000ms
    timeout client 50000ms
    timeout server 50000ms

frontend main
    bind *:80
    compression algo gzip
    compression type text/html text/css application/javascript
    default_backend servers

frontend status
    bind *:8404
    http-request return status 200 content-type text/plain string "OK" if { path /healthz }

backend servers
    server web1 127.0.0.1:8080 check
"""

    context = haproxy_context_factory(config_content=compression_config)
    result = await config_synchronizer.sync_configuration(context)
    assert_config_sync_success(result)

    await assert_config_contains_pattern(
        compose_manager, r"compression\s+algo\s+gzip", "compression algorithm"
    )
    await assert_config_contains_pattern(
        compose_manager, r"compression\s+type.*text/html", "compression types"
    )


@pytest.mark.integration
@pytest.mark.asyncio
async def test_ssl_termination_basic(
    docker_compose_dataplane,
    config_synchronizer,
    haproxy_context_factory,
):
    """Test basic SSL termination configuration."""
    from .ssl_certs import generate_ssl_certificate

    ports, compose_manager = docker_compose_dataplane

    # Generate SSL certificate for testing
    ssl_cert = generate_ssl_certificate(common_name="localhost")

    ssl_config = """
global
    stats socket /etc/haproxy/haproxy-master.sock mode 600 level admin

defaults
    mode http
    timeout connect 5000ms
    timeout client 50000ms
    timeout server 50000ms

frontend https_front
    bind *:443 ssl crt /etc/haproxy/ssl/server.pem
    default_backend servers

frontend status
    bind *:8404
    http-request return status 200 content-type text/plain string "OK" if { path /healthz }

backend servers
    server web1 127.0.0.1:8080 check
"""

    # Create context with SSL certificate
    context = haproxy_context_factory(
        config_content=ssl_config, cert_files={"server.pem": ssl_cert.combined_pem}
    )
    result = await config_synchronizer.sync_configuration(context)
    assert_config_sync_success(result)

    await assert_config_contains_pattern(
        compose_manager, r"bind.*:443.*ssl", "SSL binding on port 443"
    )


@pytest.mark.integration
@pytest.mark.asyncio
async def test_http2_enable(
    docker_compose_dataplane,
    config_synchronizer,
    haproxy_context_factory,
):
    """Test HTTP/2 protocol support."""
    ports, compose_manager = docker_compose_dataplane

    http2_config = """
global
    stats socket /etc/haproxy/haproxy-master.sock mode 600 level admin

defaults
    mode http
    timeout connect 5000ms
    timeout client 50000ms
    timeout server 50000ms

frontend http_front
    bind *:80
    http-request add-header X-Forwarded-Proto http
    default_backend servers

frontend status
    bind *:8404
    http-request return status 200 content-type text/plain string "OK" if { path /healthz }

backend servers
    server web1 127.0.0.1:8080 check
"""

    context = haproxy_context_factory(config_content=http2_config)
    result = await config_synchronizer.sync_configuration(context)
    assert_config_sync_success(result)

    await assert_config_contains_pattern(
        compose_manager,
        r"http-request\s+add-header\s+X-Forwarded-Proto\s+http",
        "HTTP header addition",
    )


@pytest.mark.integration
@pytest.mark.asyncio
async def test_websocket_upgrade(
    docker_compose_dataplane,
    config_synchronizer,
    haproxy_context_factory,
):
    """Test WebSocket upgrade handling."""
    ports, compose_manager = docker_compose_dataplane

    websocket_config = """
global
    stats socket /etc/haproxy/haproxy-master.sock mode 600 level admin

defaults
    mode http
    timeout connect 5000ms
    timeout client 50000ms
    timeout server 50000ms
    timeout tunnel 3600s

frontend main
    bind *:80
    acl is_websocket hdr(Upgrade) -i websocket
    use_backend websocket_servers if is_websocket
    default_backend servers

frontend status
    bind *:8404
    http-request return status 200 content-type text/plain string "OK" if { path /healthz }

backend websocket_servers
    server ws1 127.0.0.1:8080 check

backend servers
    server web1 127.0.0.1:8080 check
"""

    context = haproxy_context_factory(config_content=websocket_config)
    result = await config_synchronizer.sync_configuration(context)
    assert_config_sync_success(result)

    await assert_config_contains_pattern(
        compose_manager,
        r"acl\s+is_websocket\s+hdr\(Upgrade\)\s+-i\s+websocket",
        "WebSocket ACL",
    )
    await assert_config_contains_pattern(
        compose_manager, r"timeout\s+tunnel\s+(3600s|1h)", "tunnel timeout"
    )


@pytest.mark.integration
@pytest.mark.asyncio
async def test_grpc_protocol(
    docker_compose_dataplane,
    config_synchronizer,
    haproxy_context_factory,
):
    """Test gRPC protocol configuration."""
    from .ssl_certs import generate_ssl_certificate

    ports, compose_manager = docker_compose_dataplane

    # Generate SSL certificate for gRPC testing
    ssl_cert = generate_ssl_certificate(common_name="localhost")

    grpc_config = """
global
    stats socket /etc/haproxy/haproxy-master.sock mode 600 level admin

defaults
    mode http
    timeout connect 5000ms
    timeout client 50000ms
    timeout server 50000ms

frontend grpc_front
    bind *:443 ssl crt /etc/haproxy/ssl/grpc.pem alpn h2
    acl is_grpc hdr(content-type) -i application/grpc
    use_backend grpc_servers if is_grpc
    default_backend servers

frontend status
    bind *:8404
    http-request return status 200 content-type text/plain string "OK" if { path /healthz }

backend grpc_servers
    server grpc1 127.0.0.1:50051 check proto h2

backend servers
    server web1 127.0.0.1:8080 check
"""

    # Create context with SSL certificate
    context = haproxy_context_factory(
        config_content=grpc_config, cert_files={"grpc.pem": ssl_cert.combined_pem}
    )
    result = await config_synchronizer.sync_configuration(context)
    assert_config_sync_success(result)

    await assert_config_contains_pattern(
        compose_manager,
        r"acl\s+is_grpc\s+hdr\(content-type\)\s+-i\s+application/grpc",
        "gRPC content type ACL",
    )
    await assert_config_contains_pattern(
        compose_manager, r"server\s+grpc1.*proto\s+h2", "gRPC server with h2 protocol"
    )


@pytest.mark.integration
@pytest.mark.asyncio
async def test_proxy_protocol_v1(
    docker_compose_dataplane,
    config_synchronizer,
    haproxy_context_factory,
):
    """Test PROXY protocol v1 support."""
    ports, compose_manager = docker_compose_dataplane

    proxy_protocol_config = """
global
    stats socket /etc/haproxy/haproxy-master.sock mode 600 level admin

defaults
    mode http
    timeout connect 5000ms
    timeout client 50000ms
    timeout server 50000ms

frontend main
    bind *:80 accept-proxy
    default_backend servers

frontend status
    bind *:8404
    http-request return status 200 content-type text/plain string "OK" if { path /healthz }

backend servers
    server web1 127.0.0.1:8080 check send-proxy
"""

    context = haproxy_context_factory(config_content=proxy_protocol_config)
    result = await config_synchronizer.sync_configuration(context)
    assert_config_sync_success(result)

    await assert_config_contains_pattern(
        compose_manager, r"bind.*:80.*accept-proxy", "accept PROXY protocol"
    )
    await assert_config_contains_pattern(
        compose_manager, r"server\s+web1.*send-proxy", "send PROXY protocol"
    )


@pytest.mark.integration
@pytest.mark.asyncio
async def test_tcp_splicing(
    docker_compose_dataplane,
    config_synchronizer,
    haproxy_context_factory,
):
    """Test TCP splicing optimization."""
    ports, compose_manager = docker_compose_dataplane

    splicing_config = """
global
    stats socket /etc/haproxy/haproxy-master.sock mode 600 level admin

defaults
    mode tcp
    timeout connect 5000ms
    timeout client 50000ms
    timeout server 50000ms
    option splice-auto

frontend tcp_front
    bind *:3306
    default_backend tcp_servers

backend tcp_servers
    server tcp1 127.0.0.1:3306 check
"""

    context = haproxy_context_factory(config_content=splicing_config)
    result = await config_synchronizer.sync_configuration(context)
    assert_config_sync_success(result)

    await assert_config_contains_pattern(
        compose_manager, r"option\s+splice-auto", "TCP splicing option"
    )


@pytest.mark.integration
@pytest.mark.asyncio
async def test_health_check_variants(
    docker_compose_dataplane,
    config_synchronizer,
    haproxy_context_factory,
):
    """Test different health check configurations."""
    ports, compose_manager = docker_compose_dataplane

    health_check_config = """
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
    option httpchk GET /healthz
    http-check expect status 200
    server web1 127.0.0.1:8080 check inter 5s fall 3 rise 2
"""

    context = haproxy_context_factory(config_content=health_check_config)
    result = await config_synchronizer.sync_configuration(context)
    assert_config_sync_success(result)

    await assert_config_contains_pattern(
        compose_manager, r"option\s+httpchk\s+GET\s+/healthz", "HTTP health check"
    )
    await assert_config_contains_pattern(
        compose_manager,
        r"http-check\s+expect\s+status\s+200",
        "health check expectation",
    )
    await assert_config_contains_pattern(
        compose_manager,
        r"server\s+web1.*check.*inter\s+5s",
        "health check timing",
    )


@pytest.mark.integration
@pytest.mark.asyncio
async def test_connection_limiting(
    docker_compose_dataplane,
    config_synchronizer,
    haproxy_context_factory,
):
    """Test connection limiting configuration."""
    ports, compose_manager = docker_compose_dataplane

    conn_limit_config = """
global
    stats socket /etc/haproxy/haproxy-master.sock mode 600 level admin
    maxconn 4096

defaults
    mode http
    timeout connect 5000ms
    timeout client 50000ms
    timeout server 50000ms

frontend main
    bind *:80
    maxconn 2048
    default_backend servers

frontend status
    bind *:8404
    http-request return status 200 content-type text/plain string "OK" if { path /healthz }

backend servers
    server web1 127.0.0.1:8080 check maxconn 512
"""

    context = haproxy_context_factory(config_content=conn_limit_config)
    result = await config_synchronizer.sync_configuration(context)
    assert_config_sync_success(result)

    await assert_config_contains_pattern(
        compose_manager, r"global\s*\n[\s\S]*?maxconn\s+4096", "global maxconn"
    )
    await assert_config_contains_pattern(
        compose_manager,
        r"frontend\s+main\s*\n[\s\S]*?maxconn\s+2048",
        "frontend maxconn",
    )
    await assert_config_contains_pattern(
        compose_manager, r"server\s+web1.*maxconn\s+512", "server maxconn"
    )
