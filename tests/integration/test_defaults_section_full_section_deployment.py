"""
Integration tests for defaults section full_section=True deployment.

This test module verifies that defaults section directives are correctly deployed
using full_section=True parameter. These tests expose the current issue where
'log global' directive in defaults section is missing from deployed configuration
due to the lack of full_section=True parameter.

Test Coverage:
1. Defaults section 'log global' directive deployment
2. Defaults section timeout directives deployment
3. Complete defaults section consistency validation

These tests use real Docker containers to validate defaults section deployment
through DataPlane API with full_section=True requirement.
"""

import asyncio

import pytest


async def get_deployed_haproxy_config(dataplane_client) -> str:
    """
    Retrieve the actual deployed HAProxy configuration from a running instance.

    Uses the DataPlane API to fetch the current HAProxy configuration that's
    actually running, not what we think we deployed.
    """
    response = await dataplane_client.get("/v3/services/haproxy/configuration/raw")
    response.raise_for_status()
    return response.text


def parse_defaults_section(config_content: str) -> list[str]:
    """
    Parse HAProxy configuration to extract defaults section lines.

    Returns a list of configuration lines from the defaults section.
    """
    lines = []
    in_defaults = False

    for line in config_content.split("\n"):
        line = line.strip()
        if not line or line.startswith("#"):
            continue

        if line.startswith("defaults"):
            in_defaults = True
            continue
        elif line.startswith(("global", "frontend", "backend", "userlist", "peers")):
            in_defaults = False
        elif in_defaults:
            lines.append(line)

    return lines


@pytest.mark.integration
@pytest.mark.asyncio
async def test_defaults_section_log_global_deployment(
    docker_compose_dataplane,
    config_synchronizer,
    haproxy_context_factory,
    production_dataplane_client_raw,
):
    """
    Test that 'log global' directive in defaults section is correctly deployed.

    This test specifically validates the issue where defaults section directives
    are missing from deployed configuration due to lack of full_section=True.
    This test WILL FAIL until full_section=True is implemented for defaults operations.
    """
    ports, compose_manager = docker_compose_dataplane

    # Config with 'log global' in defaults section (the problematic directive)
    config_with_log_global = """
global
    log stdout len 4096 local0 info
    stats socket /etc/haproxy/haproxy-master.sock mode 600 level admin

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
    context = haproxy_context_factory(config_content=config_with_log_global)
    await config_synchronizer.sync_configuration(context)

    # Give the deployment a moment to complete
    await asyncio.sleep(2)

    # Retrieve the actual deployed configuration
    deployed_config = await get_deployed_haproxy_config(production_dataplane_client_raw)

    # Parse the deployed defaults section
    defaults_lines = parse_defaults_section(deployed_config)

    # CRITICAL ASSERTION: This will fail until full_section=True is implemented
    assert any("log global" in line for line in defaults_lines), (
        f"Missing 'log global' directive in deployed defaults section. "
        f"Deployed defaults lines: {defaults_lines}. "
        f"This indicates full_section=True is not being used for defaults operations."
    )

    # Additional specific checks for other defaults directives
    assert any("mode http" in line for line in defaults_lines), (
        "Missing 'mode http' directive in deployed defaults section"
    )
    assert any("option httplog" in line for line in defaults_lines), (
        "Missing 'option httplog' directive in deployed defaults section"
    )
    assert any("timeout connect 5s" in line for line in defaults_lines), (
        "Missing 'timeout connect 5s' directive in deployed defaults section"
    )


@pytest.mark.integration
@pytest.mark.asyncio
async def test_defaults_section_timeout_directives_deployment(
    docker_compose_dataplane,
    config_synchronizer,
    haproxy_context_factory,
    production_dataplane_client_raw,
):
    """
    Test that timeout directives in defaults section are correctly deployed.

    This verifies that all defaults section directives are deployed when
    full_section=True is used, not just the 'log global' directive.
    """
    ports, compose_manager = docker_compose_dataplane

    # Config focusing on timeout directives in defaults section
    config_with_timeouts = """
global
    stats socket /etc/haproxy/haproxy-master.sock mode 600 level admin

defaults
    mode http
    timeout connect 2000ms
    timeout client 30000ms
    timeout server 30000ms
    timeout check 1000ms
    retries 3
    option redispatch

frontend main
    bind *:80
    default_backend servers

backend servers
    balance roundrobin
"""

    # Deploy the configuration
    context = haproxy_context_factory(config_content=config_with_timeouts)
    await config_synchronizer.sync_configuration(context)

    # Wait for deployment
    await asyncio.sleep(2)

    # Get deployed config and parse defaults section
    deployed_config = await get_deployed_haproxy_config(production_dataplane_client_raw)
    defaults_lines = parse_defaults_section(deployed_config)

    # Verify all timeout directives are present in deployed config
    expected_directives = [
        "timeout connect 2s",
        "timeout client 30s",
        "timeout server 30s",
        "timeout check 1s",
        "retries 3",
        "option redispatch",
    ]

    for directive in expected_directives:
        assert any(directive in line for line in defaults_lines), (
            f"Missing '{directive}' directive in deployed defaults section. "
            f"Deployed defaults: {defaults_lines}"
        )


@pytest.mark.integration
@pytest.mark.asyncio
async def test_defaults_section_complete_consistency(
    docker_compose_dataplane,
    config_synchronizer,
    haproxy_context_factory,
    production_dataplane_client_raw,
):
    """
    Test that the entire defaults section is deployed consistently.

    This is a comprehensive test that validates defaults section deployment
    contains all expected directives when full_section=True is properly implemented.
    """
    ports, compose_manager = docker_compose_dataplane

    # Comprehensive defaults configuration
    comprehensive_config = """
global
    log stdout len 4096 local0 info
    stats socket /etc/haproxy/haproxy-master.sock mode 600 level admin

defaults
    mode http
    log global
    option httplog
    option dontlognull
    option log-health-checks
    option forwardfor
    option httpchk GET /health
    timeout connect 5000ms
    timeout client 50000ms
    timeout server 50000ms
    timeout check 2000ms
    retries 3
    option redispatch
    maxconn 3000
    balance roundrobin

frontend status
    bind *:8404
    http-request return status 200 content-type text/plain string "OK" if { path /healthz }

backend default_backend
    http-request return status 404
"""

    # Deploy comprehensive configuration
    context = haproxy_context_factory(config_content=comprehensive_config)
    await config_synchronizer.sync_configuration(context)

    # Wait for deployment
    await asyncio.sleep(2)

    # Get deployed configuration
    deployed_config = await get_deployed_haproxy_config(production_dataplane_client_raw)
    defaults_lines = parse_defaults_section(deployed_config)

    # Verify all expected defaults directives are present
    expected_directives = [
        "mode http",
        "log global",  # This is the key directive that fails without full_section=True
        "option httplog",
        "option dontlognull",
        "option log-health-checks",
        "option forwardfor",
        "option httpchk GET /health",
        "timeout connect 5s",
        "timeout client 50s",
        "timeout server 50s",
        "timeout check 2s",
        "retries 3",
        "option redispatch",
        "maxconn 3000",
        "balance roundrobin",
    ]

    missing_directives = []
    for directive in expected_directives:
        if not any(directive in line for line in defaults_lines):
            missing_directives.append(directive)

    assert not missing_directives, (
        f"Missing directives in deployed defaults section: {missing_directives}. "
        f"Deployed defaults lines: {defaults_lines}. "
        f"This indicates full_section=True is not working properly for defaults operations."
    )


@pytest.mark.integration
@pytest.mark.asyncio
async def test_defaults_section_regression_log_global(
    docker_compose_dataplane,
    config_synchronizer,
    haproxy_context_factory,
    production_dataplane_client_raw,
):
    """
    Regression test specifically for the 'log global' directive deployment issue.

    This test directly validates the exact issue that was discovered:
    - Defaults section contains 'log global' in template
    - Deployed HAProxy config was missing this directive
    - This test ensures the issue doesn't regress after fix
    """
    ports, compose_manager = docker_compose_dataplane

    # Minimal config focusing specifically on the log global issue
    minimal_config_with_log_global = """
global
    log stdout len 4096 local0 info
    stats socket /etc/haproxy/haproxy-master.sock mode 600 level admin

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
    context = haproxy_context_factory(config_content=minimal_config_with_log_global)
    await config_synchronizer.sync_configuration(context)

    # Wait for deployment
    await asyncio.sleep(1)

    # Get the raw deployed configuration text
    deployed_config = await get_deployed_haproxy_config(production_dataplane_client_raw)

    # REGRESSION TEST: Exact string matching for the log global directive in defaults
    assert "log global" in deployed_config, (
        "REGRESSION: 'log global' directive not found in deployed config. "
        "This is the exact issue that caused missing access logs!"
    )

    # Also verify it's specifically in the defaults section
    defaults_lines = parse_defaults_section(deployed_config)
    assert any("log global" in line for line in defaults_lines), (
        f"'log global' found in config but not in defaults section. "
        f"Defaults section: {defaults_lines}"
    )

    # Print config for debugging if test fails (this output helps troubleshooting)
    if not any("log global" in line for line in defaults_lines):
        print(f"\nDEPLOYED CONFIG DEBUG:\n{deployed_config}")
        print(f"\nDEFAULTS SECTION LINES: {defaults_lines}")
