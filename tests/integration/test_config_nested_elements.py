"""
Integration tests for HAProxy configuration nested elements.

This test module verifies that nested configuration elements like
HTTP rules, ACL definitions, stick tables, and error handling
can be deployed successfully via the dataplane API config synchronizer.
"""

import pytest

from .conftest import assert_config_sync_success, assert_config_contains_pattern


@pytest.mark.integration
@pytest.mark.asyncio
async def test_http_request_rule_deny(
    docker_compose_dataplane,
    config_synchronizer,
    haproxy_context_factory,
):
    """Test HTTP request rule with deny action."""
    ports, compose_manager = docker_compose_dataplane

    deny_rule_config = """
global
    stats socket /etc/haproxy/haproxy-master.sock mode 600 level admin

defaults
    mode http
    timeout connect 5000ms
    timeout client 50000ms
    timeout server 50000ms

frontend main
    bind *:80
    http-request deny if { src 192.168.1.100 }
    default_backend servers

frontend status
    bind *:8404
    http-request return status 200 content-type text/plain string "OK" if { path /healthz }

backend servers
    server web1 127.0.0.1:8080 check
"""

    context = haproxy_context_factory(config_content=deny_rule_config)
    result = await config_synchronizer.sync_configuration(context)
    assert_config_sync_success(result)

    await assert_config_contains_pattern(
        compose_manager,
        r"http-request\s+deny\s+if\s+\{\s*src\s+192\.168\.1\.100\s*\}",
        "HTTP request deny rule",
    )


@pytest.mark.integration
@pytest.mark.asyncio
async def test_http_response_rule_header(
    docker_compose_dataplane,
    config_synchronizer,
    haproxy_context_factory,
):
    """Test HTTP response rule with header addition."""
    ports, compose_manager = docker_compose_dataplane

    header_rule_config = """
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
    http-response set-header X-Backend-Server %s
    server web1 127.0.0.1:8080 check
"""

    context = haproxy_context_factory(config_content=header_rule_config)
    result = await config_synchronizer.sync_configuration(context)
    assert_config_sync_success(result)

    await assert_config_contains_pattern(
        compose_manager,
        r"http-response\s+set-header\s+X-Backend-Server\s+%s",
        "HTTP response header rule",
    )


@pytest.mark.integration
@pytest.mark.asyncio
async def test_acl_host_header(
    docker_compose_dataplane,
    config_synchronizer,
    haproxy_context_factory,
):
    """Test ACL based on host header."""
    ports, compose_manager = docker_compose_dataplane

    host_acl_config = """
global
    stats socket /etc/haproxy/haproxy-master.sock mode 600 level admin

defaults
    mode http
    timeout connect 5000ms
    timeout client 50000ms
    timeout server 50000ms

frontend main
    bind *:80
    acl is_admin hdr(host) -i admin.example.com
    use_backend admin_servers if is_admin
    default_backend servers

frontend status
    bind *:8404
    http-request return status 200 content-type text/plain string "OK" if { path /healthz }

backend admin_servers
    server admin1 127.0.0.1:8001 check

backend servers
    server web1 127.0.0.1:8080 check
"""

    context = haproxy_context_factory(config_content=host_acl_config)
    result = await config_synchronizer.sync_configuration(context)
    assert_config_sync_success(result)

    await assert_config_contains_pattern(
        compose_manager,
        r"acl\s+is_admin\s+hdr\(host\)\s+-i\s+admin\.example\.com",
        "host header ACL",
    )


@pytest.mark.integration
@pytest.mark.asyncio
async def test_acl_method_based(
    docker_compose_dataplane,
    config_synchronizer,
    haproxy_context_factory,
):
    """Test ACL based on HTTP method."""
    ports, compose_manager = docker_compose_dataplane

    method_acl_config = """
global
    stats socket /etc/haproxy/haproxy-master.sock mode 600 level admin

defaults
    mode http
    timeout connect 5000ms
    timeout client 50000ms
    timeout server 50000ms

frontend main
    bind *:80
    acl is_post method POST
    use_backend post_servers if is_post
    default_backend servers

frontend status
    bind *:8404
    http-request return status 200 content-type text/plain string "OK" if { path /healthz }

backend post_servers
    server post1 127.0.0.1:8001 check

backend servers
    server web1 127.0.0.1:8080 check
"""

    context = haproxy_context_factory(config_content=method_acl_config)
    result = await config_synchronizer.sync_configuration(context)
    assert_config_sync_success(result)

    await assert_config_contains_pattern(
        compose_manager, r"acl\s+is_post\s+method\s+POST", "method-based ACL"
    )


@pytest.mark.integration
@pytest.mark.asyncio
async def test_stick_table_basic(
    docker_compose_dataplane,
    config_synchronizer,
    haproxy_context_factory,
):
    """Test basic stick table configuration."""
    ports, compose_manager = docker_compose_dataplane

    stick_table_config = """
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
    stick-table type ip size 100k expire 30m
    stick on src
    server web1 127.0.0.1:8080 check
    server web2 127.0.0.1:8081 check
"""

    context = haproxy_context_factory(config_content=stick_table_config)
    result = await config_synchronizer.sync_configuration(context)
    assert_config_sync_success(result)

    await assert_config_contains_pattern(
        compose_manager,
        r"stick-table\s+type\s+ip\s+size\s+100k\s+expire\s+30m",
        "stick table definition",
    )
    await assert_config_contains_pattern(
        compose_manager, r"stick\s+on\s+src", "stick on source"
    )


@pytest.mark.integration
@pytest.mark.asyncio
async def test_redirect_rule(
    docker_compose_dataplane,
    config_synchronizer,
    haproxy_context_factory,
):
    """Test HTTP redirect rule."""
    ports, compose_manager = docker_compose_dataplane

    redirect_config = """
global
    stats socket /etc/haproxy/haproxy-master.sock mode 600 level admin

defaults
    mode http
    timeout connect 5000ms
    timeout client 50000ms
    timeout server 50000ms

frontend main
    bind *:80
    http-request redirect scheme https if !{ ssl_fc }
    default_backend servers

frontend status
    bind *:8404
    http-request return status 200 content-type text/plain string "OK" if { path /healthz }

backend servers
    server web1 127.0.0.1:8080 check
"""

    context = haproxy_context_factory(config_content=redirect_config)
    result = await config_synchronizer.sync_configuration(context)
    assert_config_sync_success(result)

    await assert_config_contains_pattern(
        compose_manager,
        r"http-request\s+redirect\s+scheme\s+https\s+if\s+!\{\s*ssl_fc\s*\}",
        "HTTPS redirect rule",
    )


@pytest.mark.integration
@pytest.mark.asyncio
async def test_server_track_option(
    docker_compose_dataplane,
    config_synchronizer,
    haproxy_context_factory,
):
    """Test server track option for health check sharing."""
    ports, compose_manager = docker_compose_dataplane

    track_config = """
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
    server web1 127.0.0.1:8080 check
    server web1-ssl 127.0.0.1:8443 track servers/web1
"""

    context = haproxy_context_factory(config_content=track_config)
    result = await config_synchronizer.sync_configuration(context)
    assert_config_sync_success(result)

    await assert_config_contains_pattern(
        compose_manager,
        r"server\s+web1-ssl\s+127\.0\.0\.1:8443\s+track\s+servers/web1",
        "server track option",
    )


@pytest.mark.integration
@pytest.mark.asyncio
async def test_capture_request_header(
    docker_compose_dataplane,
    config_synchronizer,
    haproxy_context_factory,
):
    """Test capture request header configuration."""
    ports, compose_manager = docker_compose_dataplane

    capture_config = """
global
    stats socket /etc/haproxy/haproxy-master.sock mode 600 level admin

defaults
    mode http
    timeout connect 5000ms
    timeout client 50000ms
    timeout server 50000ms

frontend main
    bind *:80
    declare capture request len 64
    declare capture request len 128
    default_backend servers

frontend status
    bind *:8404
    http-request return status 200 content-type text/plain string "OK" if { path /healthz }

backend servers
    http-request capture req.hdr(Host) id 0
    http-request capture req.hdr(User-Agent) id 1
    server web1 127.0.0.1:8080 check
"""

    context = haproxy_context_factory(config_content=capture_config)
    result = await config_synchronizer.sync_configuration(context)
    assert_config_sync_success(result)

    await assert_config_contains_pattern(
        compose_manager,
        r"declare\s+capture\s+request\s+len\s+64",
        "declare capture request len 64",
    )
    await assert_config_contains_pattern(
        compose_manager,
        r"declare\s+capture\s+request\s+len\s+128",
        "declare capture request len 128",
    )
    await assert_config_contains_pattern(
        compose_manager,
        r"http-request\s+capture\s+req\.hdr\(Host\)\s+id\s+0",
        "http-request capture Host header",
    )
    await assert_config_contains_pattern(
        compose_manager,
        r"http-request\s+capture\s+req\.hdr\(User-Agent\)\s+id\s+1",
        "http-request capture User-Agent header",
    )


@pytest.mark.integration
@pytest.mark.asyncio
async def test_log_format_custom(
    docker_compose_dataplane,
    config_synchronizer,
    haproxy_context_factory,
):
    """Test custom log format configuration."""
    ports, compose_manager = docker_compose_dataplane

    log_format_config = """
global
    stats socket /etc/haproxy/haproxy-master.sock mode 600 level admin

defaults
    mode http
    timeout connect 5000ms
    timeout client 50000ms
    timeout server 50000ms
    log-format "%ci:%cp [%t] %ft %b/%s %Tq/%Tw/%Tc/%Tr/%Ta %ST %B %CC %CS %tsc %ac/%fc/%bc/%sc/%rc %sq/%bq %hr %hs %{+Q}r"

frontend main
    bind *:80
    default_backend servers

frontend status
    bind *:8404
    http-request return status 200 content-type text/plain string "OK" if { path /healthz }

backend servers
    server web1 127.0.0.1:8080 check
"""

    context = haproxy_context_factory(config_content=log_format_config)
    result = await config_synchronizer.sync_configuration(context)
    assert_config_sync_success(result)

    await assert_config_contains_pattern(
        compose_manager, r"log-format\s+\"%ci:%cp", "custom log format"
    )


@pytest.mark.integration
@pytest.mark.asyncio
async def test_rate_limiting_basic(
    docker_compose_dataplane,
    config_synchronizer,
    haproxy_context_factory,
):
    """Test basic rate limiting with stick table."""
    ports, compose_manager = docker_compose_dataplane

    rate_limit_config = """
global
    stats socket /etc/haproxy/haproxy-master.sock mode 600 level admin

defaults
    mode http
    timeout connect 5000ms
    timeout client 50000ms
    timeout server 50000ms

frontend main
    bind *:80
    stick-table type ip size 100k expire 30s store http_req_rate(10s)
    http-request track-sc0 src
    http-request deny if { sc_http_req_rate(0) gt 20 }
    default_backend servers

frontend status
    bind *:8404
    http-request return status 200 content-type text/plain string "OK" if { path /healthz }

backend servers
    server web1 127.0.0.1:8080 check
"""

    context = haproxy_context_factory(config_content=rate_limit_config)
    result = await config_synchronizer.sync_configuration(context)
    assert_config_sync_success(result)

    await assert_config_contains_pattern(
        compose_manager,
        r"stick-table\s+type\s+ip.*store\s+http_req_rate\(10s\)",
        "rate limiting stick table",
    )
    await assert_config_contains_pattern(
        compose_manager, r"http-request\s+track-sc0\s+src", "request tracking"
    )
    await assert_config_contains_pattern(
        compose_manager,
        r"http-request\s+deny\s+if\s+\{\s*sc_http_req_rate\(0\)\s+gt\s+20\s*\}",
        "rate limit deny rule",
    )


@pytest.mark.integration
@pytest.mark.asyncio
async def test_declare_capture_request_header(
    docker_compose_dataplane,
    config_synchronizer,
    haproxy_context_factory,
):
    """Test declare capture with http-request capture configuration."""
    ports, compose_manager = docker_compose_dataplane

    declare_capture_config = """
global
    stats socket /etc/haproxy/haproxy-master.sock mode 600 level admin

defaults
    mode http
    timeout connect 5000ms
    timeout client 50000ms
    timeout server 50000ms

frontend main
    bind *:80
    declare capture request len 64
    declare capture request len 128
    default_backend servers

frontend status
    bind *:8404
    http-request return status 200 content-type text/plain string "OK" if { path /healthz }

backend servers
    server web1 127.0.0.1:8080 check
"""

    context = haproxy_context_factory(config_content=declare_capture_config)
    result = await config_synchronizer.sync_configuration(context)
    assert_config_sync_success(result)

    await assert_config_contains_pattern(
        compose_manager,
        r"declare\s+capture\s+request\s+len\s+64",
        "declare capture request 64",
    )
    await assert_config_contains_pattern(
        compose_manager,
        r"declare\s+capture\s+request\s+len\s+128",
        "declare capture request 128",
    )


@pytest.mark.integration
@pytest.mark.asyncio
async def test_declare_capture_response_header(
    docker_compose_dataplane,
    config_synchronizer,
    haproxy_context_factory,
):
    """Test declare capture with http-response capture configuration."""
    ports, compose_manager = docker_compose_dataplane

    declare_capture_response_config = """
global
    stats socket /etc/haproxy/haproxy-master.sock mode 600 level admin

defaults
    mode http
    timeout connect 5000ms
    timeout client 50000ms
    timeout server 50000ms

frontend main
    bind *:80
    declare capture response len 64
    declare capture response len 128
    default_backend servers

frontend status
    bind *:8404
    http-request return status 200 content-type text/plain string "OK" if { path /healthz }

backend servers
    http-response capture res.hdr(Content-Type) id 0
    http-response capture res.hdr(Server) id 1
    server web1 127.0.0.1:8080 check
"""

    context = haproxy_context_factory(config_content=declare_capture_response_config)
    result = await config_synchronizer.sync_configuration(context)
    assert_config_sync_success(result)

    await assert_config_contains_pattern(
        compose_manager,
        r"declare\s+capture\s+response\s+len\s+64",
        "declare capture response 64",
    )
    await assert_config_contains_pattern(
        compose_manager,
        r"declare\s+capture\s+response\s+len\s+128",
        "declare capture response 128",
    )
    await assert_config_contains_pattern(
        compose_manager,
        r"http-response\s+capture\s+res\.hdr\(Content-Type\)\s+id\s+0",
        "http-response capture Content-Type",
    )
    await assert_config_contains_pattern(
        compose_manager,
        r"http-response\s+capture\s+res\.hdr\(Server\)\s+id\s+1",
        "http-response capture Server",
    )


@pytest.mark.integration
@pytest.mark.asyncio
async def test_server_template_basic(
    docker_compose_dataplane,
    config_synchronizer,
    haproxy_context_factory,
):
    """Test basic server template configuration."""
    ports, compose_manager = docker_compose_dataplane

    server_template_config = """
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
    server-template srv 1-3 google.com:80 check weight 100
"""

    context = haproxy_context_factory(config_content=server_template_config)
    result = await config_synchronizer.sync_configuration(context)
    assert_config_sync_success(result)

    await assert_config_contains_pattern(
        compose_manager,
        r"server-template\s+srv\s+1-3\s+google\.com:80\s+check\s+weight\s+100",
        "server template configuration",
    )


@pytest.mark.integration
@pytest.mark.asyncio
async def test_http_check_backend(
    docker_compose_dataplane,
    config_synchronizer,
    haproxy_context_factory,
):
    """Test HTTP check configuration in backend."""
    ports, compose_manager = docker_compose_dataplane

    http_check_config = """
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
    option httpchk GET /health HTTP/1.1
    http-check send hdr Host www.example.com
    server web1 127.0.0.1:8080 check
"""

    context = haproxy_context_factory(config_content=http_check_config)
    result = await config_synchronizer.sync_configuration(context)
    assert_config_sync_success(result)

    await assert_config_contains_pattern(
        compose_manager, r"option\s+httpchk\s+GET\s+/health", "HTTP check option"
    )
    await assert_config_contains_pattern(
        compose_manager,
        r"http-check\s+send\s+hdr\s+Host\s+www\.example\.com",
        "HTTP check send header",
    )


@pytest.mark.integration
@pytest.mark.asyncio
async def test_tcp_check_backend(
    docker_compose_dataplane,
    config_synchronizer,
    haproxy_context_factory,
):
    """Test TCP check configuration in backend."""
    ports, compose_manager = docker_compose_dataplane

    tcp_check_config = """
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
    option tcp-check
    tcp-check connect port 8080
    tcp-check send PING\\r\\n
    tcp-check expect string PONG
    server web1 127.0.0.1:8080 check
"""

    context = haproxy_context_factory(config_content=tcp_check_config)
    result = await config_synchronizer.sync_configuration(context)
    assert_config_sync_success(result)

    await assert_config_contains_pattern(
        compose_manager, r"option\s+tcp-check", "TCP check option"
    )
    await assert_config_contains_pattern(
        compose_manager, r"tcp-check\s+connect\s+port\s+8080", "TCP check connect"
    )
    await assert_config_contains_pattern(
        compose_manager, r"tcp-check\s+send\s+PING", "TCP check send"
    )
    await assert_config_contains_pattern(
        compose_manager, r"tcp-check\s+expect\s+string\s+PONG", "TCP check expect"
    )
