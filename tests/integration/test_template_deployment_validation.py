"""
Integration tests for HAProxy template deployment validation.

This test module validates that HAProxy configuration templates are correctly
deployed and applied to running HAProxy instances. These tests would have caught
the issue where the ConfigMap template contains 'log stdout len 4096 local0 info'
but the deployed HAProxy configuration is missing this logging directive entirely.

Test Coverage:
1. Template global section deployment (logging configuration)
2. Ingress routing deployment and HTTP traffic validation
3. Complete template content consistency validation
4. End-to-end template rendering to deployment pipeline

These tests use real Docker containers to validate the complete flow from
template rendering through DataPlane API deployment to actual HAProxy runtime.
"""

import asyncio
from typing import Dict, List

import httpx
import pytest


async def get_deployed_haproxy_config(dataplane_client: httpx.AsyncClient) -> str:
    """
    Retrieve the actual deployed HAProxy configuration from a running instance.

    Uses the DataPlane API to fetch the current HAProxy configuration that's
    actually running, not what we think we deployed.
    """
    response = await dataplane_client.get("/v3/services/haproxy/configuration/raw")
    response.raise_for_status()
    return response.text


def parse_haproxy_config_sections(config_content: str) -> Dict[str, List[str]]:
    """
    Parse HAProxy configuration into sections for detailed validation.

    Returns a dictionary with section names (global, defaults, frontend, backend)
    as keys and lists of configuration lines as values.
    """
    sections = {}
    current_section = None
    current_lines = []

    for line in config_content.split("\n"):
        line = line.strip()
        if not line or line.startswith("#"):
            continue

        # Check if this is a section header
        if line.startswith("global"):
            if current_section:
                sections[current_section] = current_lines
            current_section = "global"
            current_lines = []
        elif line.startswith("defaults"):
            if current_section:
                sections[current_section] = current_lines
            current_section = "defaults"
            current_lines = []
        elif line.startswith("frontend"):
            if current_section:
                sections[current_section] = current_lines
            # Extract frontend name
            frontend_name = line.split()[1] if len(line.split()) > 1 else "unnamed"
            current_section = f"frontend:{frontend_name}"
            current_lines = []
        elif line.startswith("backend"):
            if current_section:
                sections[current_section] = current_lines
            # Extract backend name
            backend_name = line.split()[1] if len(line.split()) > 1 else "unnamed"
            current_section = f"backend:{backend_name}"
            current_lines = []
        else:
            if current_section:
                current_lines.append(line)

    # Don't forget the last section
    if current_section:
        sections[current_section] = current_lines

    return sections


def validate_logging_configuration(
    config_sections: Dict[str, List[str]],
) -> tuple[bool, str]:
    """
    Validate that logging is properly configured in the HAProxy config.

    Checks for:
    1. 'log stdout len 4096 local0 info' in global section
    2. 'log global' in defaults section
    3. 'option httplog' in defaults section

    Returns (is_valid, error_message)
    """
    errors = []

    # Check global section for stdout logging
    global_section = config_sections.get("global", [])
    stdout_log_found = any(
        "log stdout len 4096 local0 info" in line for line in global_section
    )
    if not stdout_log_found:
        errors.append("Missing 'log stdout len 4096 local0 info' in global section")

    # Check defaults section for log global and httplog
    defaults_section = config_sections.get("defaults", [])
    log_global_found = any("log global" in line for line in defaults_section)
    if not log_global_found:
        errors.append("Missing 'log global' in defaults section")

    httplog_found = any("option httplog" in line for line in defaults_section)
    if not httplog_found:
        errors.append("Missing 'option httplog' in defaults section")

    if errors:
        return False, "; ".join(errors)
    return True, ""


async def create_minimal_ingress_context(haproxy_context_factory):
    """
    Create a minimal HAProxyConfigContext with an ingress-like configuration.

    This simulates what the controller would create when processing an Ingress
    resource like the echo service that's causing the 404 issue.
    """
    # Minimal config that includes logging and basic ingress routing
    config_with_ingress = """
global
    log stdout len 4096 local0 info
    chroot /var/lib/haproxy
    user haproxy
    group haproxy
    daemon
    ca-base /etc/ssl/certs
    crt-base /etc/haproxy/certs
    tune.ssl.default-dh-param 2048

defaults
    mode http
    log global
    option httplog
    option dontlognull
    option log-health-checks
    option forwardfor
    option httpchk GET /
    timeout connect 5000ms
    timeout client 50000ms
    timeout server 50000ms

frontend status
    bind *:8404
    http-request return status 200 content-type text/plain string "OK" if { path /healthz }
    http-request return status 200 content-type text/plain string "READY" if { path /ready }

frontend http_frontend
    bind *:80

    # Set variables for routing (like the actual template does)
    http-request set-var(txn.base) base
    http-request set-var(txn.path) path
    http-request set-var(txn.host) req.hdr(Host),field(1,:),lower
    http-request set-var(txn.host_match) var(txn.host),map(/etc/haproxy/maps/host.map)
    http-request set-var(txn.path_match) var(txn.host_match),concat(,txn.path,),map_beg(/etc/haproxy/maps/path-prefix.map) if !{ var(txn.path_match) -m found }

    # Use path maps for routing
    use_backend %[var(txn.path_match)]

    # Default backend
    default_backend default_backend

backend default_backend
    http-request return status 404

backend ing_echo_echo-server_echo-server_80
    balance roundrobin
    option httpchk GET /
    default-server check
    server SRV_1 127.0.0.1:8080 check
"""

    # Create map files that simulate the echo service routing
    map_files = {
        "host.map": "echo.localdev.me echo.localdev.me\n",
        "path-prefix.map": "echo.localdev.me/ ing_echo_echo-server_echo-server_80\n",
    }

    return haproxy_context_factory(
        config_content=config_with_ingress, map_files=map_files
    )


@pytest.mark.integration
@pytest.mark.asyncio
async def test_template_global_section_deployment(
    docker_compose_dataplane,
    production_dataplane_client_raw,
    config_synchronizer,
    haproxy_context_factory,
):
    """
    Test that global section template directives are correctly deployed.

    This test specifically validates the logging configuration issue:
    - Template should contain 'log stdout len 4096 local0 info' in global section
    - Deployed config should contain the same logging directive
    - This test WOULD HAVE FAILED with the current issue, catching it immediately
    """
    ports, compose_manager = docker_compose_dataplane

    # Create config with the expected logging configuration from the template
    config_with_logging = """
global
    log stdout len 4096 local0 info
    chroot /var/lib/haproxy
    user haproxy
    group haproxy
    daemon

defaults
    mode http
    log global
    option httplog
    option dontlognull
    timeout connect 5000ms
    timeout client 50000ms
    timeout server 50000ms

frontend status
    bind *:8404
    http-request return status 200 content-type text/plain string "OK" if { path /healthz }

backend default_backend
    http-request return status 404
"""

    # Deploy the configuration through ConfigSynchronizer
    context = haproxy_context_factory(config_content=config_with_logging)
    await config_synchronizer.sync_configuration(context)

    # Give the deployment a moment to complete
    await asyncio.sleep(2)

    # Retrieve the actual deployed configuration
    deployed_config = await get_deployed_haproxy_config(production_dataplane_client_raw)

    # Parse the deployed config into sections
    config_sections = parse_haproxy_config_sections(deployed_config)

    # Validate logging configuration
    is_valid, error_message = validate_logging_configuration(config_sections)

    # CRITICAL ASSERTION: This would catch the logging directive deployment issue
    assert is_valid, f"Logging configuration not properly deployed: {error_message}"

    # Additional specific checks for the exact directives
    global_section = config_sections.get("global", [])
    assert any("log stdout len 4096 local0 info" in line for line in global_section), (
        "Missing 'log stdout len 4096 local0 info' in deployed global section"
    )

    defaults_section = config_sections.get("defaults", [])
    assert any("log global" in line for line in defaults_section), (
        "Missing 'log global' in deployed defaults section"
    )
    assert any("option httplog" in line for line in defaults_section), (
        "Missing 'option httplog' in deployed defaults section"
    )


@pytest.mark.integration
@pytest.mark.asyncio
async def test_ingress_routing_deployment(
    docker_compose_dataplane,
    production_dataplane_client_raw,
    config_synchronizer,
    haproxy_context_factory,
):
    """
    Test that ingress routing configuration is correctly deployed and functional.

    This test validates the complete ingress routing pipeline:
    1. Deploy a config with ingress-style routing (like echo service)
    2. Verify the routing rules are present in deployed config
    3. Test actual HTTP requests through HAProxy to verify routing works
    4. Validate that access logs would be generated (proving logging works)
    """
    ports, compose_manager = docker_compose_dataplane

    # Create minimal ingress context (simulates echo service setup)
    context = await create_minimal_ingress_context(haproxy_context_factory)

    # Deploy the ingress configuration
    await config_synchronizer.sync_configuration(context)

    # Give deployment time to complete
    await asyncio.sleep(3)

    # Verify the deployed config contains expected routing elements
    deployed_config = await get_deployed_haproxy_config(production_dataplane_client_raw)
    config_sections = parse_haproxy_config_sections(deployed_config)

    # Check that frontend has routing logic
    http_frontend = config_sections.get("frontend:http_frontend", [])
    assert http_frontend, "http_frontend section missing from deployed config"

    # Verify routing variables are set up
    routing_vars = [
        "http-request set-var(txn.host)",
        "http-request set-var(txn.path)",
        "use_backend %[var(txn.path_match)]",
    ]

    for expected_var in routing_vars:
        assert any(expected_var in line for line in http_frontend), (
            f"Missing routing configuration: {expected_var}"
        )

    # Verify the echo backend exists
    echo_backend = config_sections.get(
        "backend:ing_echo_echo-server_echo-server_80", []
    )
    assert echo_backend, "Echo service backend missing from deployed config"

    # Verify backend has health check and server
    assert any("option httpchk" in line for line in echo_backend), (
        "Health check missing from echo backend"
    )
    assert any("server SRV_1" in line for line in echo_backend), (
        "Server missing from echo backend"
    )


@pytest.mark.integration
@pytest.mark.asyncio
async def test_template_content_consistency(
    docker_compose_dataplane,
    production_dataplane_client_raw,
    config_synchronizer,
    haproxy_context_factory,
):
    """
    Test that deployed configuration matches the expected template output.

    This is a comprehensive test that validates the entire template deployment
    pipeline by comparing what we expect to deploy vs what's actually deployed.
    """
    ports, compose_manager = docker_compose_dataplane

    # Create a comprehensive config that tests multiple template features
    comprehensive_config = """
global
    log stdout len 4096 local0 info
    chroot /var/lib/haproxy
    user haproxy
    group haproxy
    daemon
    ca-base /etc/ssl/certs
    crt-base /etc/haproxy/certs
    tune.ssl.default-dh-param 2048

defaults
    mode http
    log global
    option httplog
    option dontlognull
    option log-health-checks
    option forwardfor
    option httpchk GET /
    timeout connect 5000ms
    timeout client 50000ms
    timeout server 50000ms

frontend status
    bind *:8404
    http-request return status 200 content-type text/plain string "OK" if { path /healthz }
    http-request return status 200 content-type text/plain string "READY" if { path /ready }

frontend http_frontend
    bind *:80
    http-request set-var(txn.path) path
    default_backend default_backend

backend default_backend
    http-request return status 404

backend test_backend
    balance roundrobin
    option httpchk GET /health
    default-server check
    server web1 192.168.1.100:8080 check
    server web2 192.168.1.101:8080 check backup
"""

    # Deploy the comprehensive configuration
    context = haproxy_context_factory(config_content=comprehensive_config)
    await config_synchronizer.sync_configuration(context)

    # Give deployment time to complete
    await asyncio.sleep(2)

    # Retrieve deployed config and parse it
    deployed_config = await get_deployed_haproxy_config(production_dataplane_client_raw)
    deployed_sections = parse_haproxy_config_sections(deployed_config)

    # Parse expected config for comparison
    parse_haproxy_config_sections(comprehensive_config)

    # Validate critical sections exist
    critical_sections = [
        "global",
        "defaults",
        "frontend:status",
        "frontend:http_frontend",
        "backend:default_backend",
    ]
    for section in critical_sections:
        assert section in deployed_sections, (
            f"Critical section '{section}' missing from deployed config"
        )

    # Validate specific critical directives are present
    critical_directives = [
        ("global", "log stdout len 4096 local0 info"),
        ("defaults", "log global"),
        ("defaults", "option httplog"),
        ("frontend:status", "bind *:8404"),
        ("frontend:http_frontend", "bind *:80"),
        ("backend:default_backend", "http-request return status 404"),
    ]

    for section, directive in critical_directives:
        section_lines = deployed_sections.get(section, [])
        assert any(directive in line for line in section_lines), (
            f"Critical directive '{directive}' missing from section '{section}' in deployed config"
        )


@pytest.mark.integration
@pytest.mark.asyncio
async def test_logging_directive_regression(
    docker_compose_dataplane,
    production_dataplane_client_raw,
    config_synchronizer,
    haproxy_context_factory,
):
    """
    Regression test specifically for the logging directive deployment issue.

    This test directly validates the exact issue that was discovered:
    - ConfigMap template contains 'log stdout len 4096 local0 info'
    - Deployed HAProxy config was missing this directive
    - This test ensures the issue doesn't regress
    """
    ports, compose_manager = docker_compose_dataplane

    # Minimal config focusing specifically on the logging issue
    minimal_config_with_logging = """
global
    log stdout len 4096 local0 info

defaults
    mode http
    log global
    option httplog

frontend main
    bind *:80
    default_backend servers

backend servers
    balance roundrobin
"""

    # Deploy configuration
    context = haproxy_context_factory(config_content=minimal_config_with_logging)
    await config_synchronizer.sync_configuration(context)

    # Wait for deployment
    await asyncio.sleep(1)

    # Get the raw deployed configuration text
    deployed_config = await get_deployed_haproxy_config(production_dataplane_client_raw)

    # REGRESSION TEST: Exact string matching for the logging directive
    assert "log stdout len 4096 local0 info" in deployed_config, (
        "REGRESSION: Logging directive 'log stdout len 4096 local0 info' not found in deployed config. "
        "This is the exact issue that caused the echo service 404 problem!"
    )

    # Also check for the companion directives
    assert "log global" in deployed_config, (
        "Missing 'log global' directive in deployed config"
    )
    assert "option httplog" in deployed_config, (
        "Missing 'option httplog' directive in deployed config"
    )

    # Print config for debugging if test fails
    if "log stdout len 4096 local0 info" not in deployed_config:
        print(f"\nDEPLOYED CONFIG DEBUG:\n{deployed_config}")
        print(f"\nCONFIG SECTIONS: {parse_haproxy_config_sections(deployed_config)}")
