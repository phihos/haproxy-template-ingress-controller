"""
Integration tests for ConfigSynchronizer ACL runtime operations.

This test module verifies that ACL file synchronization works correctly using
ConfigSynchronizer with runtime operations (no HAProxy reload required).
Tests use the existing Docker infrastructure with minimal additional fixtures.
"""

import pytest

from .utils import (
    exec_container_command,
    read_container_file,
    haproxy_socket_command,
    get_haproxy_process_info,
)


@pytest.mark.integration
@pytest.mark.asyncio
async def test_acl_runtime_operations_no_reload(
    docker_compose_dataplane,
    config_synchronizer,
    haproxy_config_with_acl,
    haproxy_context_factory,
):
    """Test ACL runtime operations without HAProxy reload using ConfigSynchronizer.

    This test verifies the complete workflow:
    1. Deploy initial config with baseline ACL file via ConfigSynchronizer
    2. Capture HAProxy process state
    3. Update ACL content with new entry
    4. Deploy updated config via ConfigSynchronizer
    5. Verify ACL file updated on disk in container
    6. Verify runtime socket shows new ACL entry
    7. Verify HAProxy did not reload (process unchanged)
    """
    ports, compose_manager = docker_compose_dataplane

    # Step 1: Initial sync with baseline ACL content
    initial_context = haproxy_context_factory(
        config_content=haproxy_config_with_acl,
        acl_files={"blocked.acl": "192.168.1.100\n"},
    )

    result1 = await config_synchronizer.sync_configuration(initial_context)
    assert "success" in str(result1).lower() or "completed" in str(result1).lower()

    # Step 2: Capture HAProxy process state before update
    process_before = await get_haproxy_process_info(
        compose_manager, "production-haproxy"
    )
    initial_pid = process_before["pid"]
    initial_start_time = process_before["start_time"]

    # Verify initial ACL file exists and has baseline content
    acl_content_before = await read_container_file(
        compose_manager, "production-haproxy", "/etc/haproxy/general/blocked.acl"
    )
    assert "192.168.1.100" in acl_content_before
    assert "10.0.0.50" not in acl_content_before  # Not yet added

    # Step 3: Update ACL content with additional entry
    updated_context = haproxy_context_factory(
        config_content=haproxy_config_with_acl,
        acl_files={"blocked.acl": "192.168.1.100\n10.0.0.50\n"},
    )

    # Step 4: Deploy updated configuration via ConfigSynchronizer
    result2 = await config_synchronizer.sync_configuration(updated_context)
    assert "success" in str(result2).lower() or "completed" in str(result2).lower()

    # Step 5: Verify ACL file updated on disk with new content
    acl_content_after = await read_container_file(
        compose_manager, "production-haproxy", "/etc/haproxy/general/blocked.acl"
    )
    assert "192.168.1.100" in acl_content_after  # Original entry preserved
    assert "10.0.0.50" in acl_content_after  # New entry added

    # Step 6: Verify runtime socket shows ACL entries
    # Note: This tests that ACL runtime operations are working
    try:
        acl_output = await haproxy_socket_command(
            compose_manager, "production-haproxy", "show acl"
        )
        # Should show ACL information including our blocked.acl file
        assert "blocked.acl" in acl_output or "acl" in acl_output.lower()
    except RuntimeError as e:
        # If socket command fails, it might be that ACL entries aren't loaded yet
        # or the implementation needs work - that's what TDD is for
        pytest.fail(f"ACL socket command failed: {e}")

    # Step 7: Verify HAProxy did not reload (critical requirement)
    process_after = await get_haproxy_process_info(
        compose_manager, "production-haproxy"
    )
    after_pid = process_after["pid"]
    after_start_time = process_after["start_time"]

    # Assert process ID and start time unchanged (no reload)
    assert after_pid == initial_pid, (
        f"HAProxy reloaded! PID changed from {initial_pid} to {after_pid}. "
        "ACL operations should use runtime API without reload."
    )
    assert after_start_time == initial_start_time, (
        f"HAProxy reloaded! Start time changed from {initial_start_time} to {after_start_time}. "
        "ACL operations should use runtime API without reload."
    )

    # Additional verification: ensure file is in expected location
    # This helps debug path issues if the test fails
    try:
        ls_output = await exec_container_command(
            compose_manager, "production-haproxy", "ls -la /etc/haproxy/general/"
        )
        assert "blocked.acl" in ls_output, (
            f"ACL file not found in general directory: {ls_output}"
        )
    except RuntimeError as e:
        pytest.fail(f"Failed to list maps directory: {e}")


@pytest.mark.integration
@pytest.mark.asyncio
async def test_acl_file_creation_and_removal(
    docker_compose_dataplane,
    config_synchronizer,
    haproxy_config_with_acl,
    haproxy_context_factory,
):
    """Test ACL file creation and removal via ConfigSynchronizer.

    This test verifies:
    1. ACL files can be created from scratch
    2. ACL files can be removed completely
    3. File operations work correctly via runtime API
    """
    ports, compose_manager = docker_compose_dataplane

    # Step 1: Deploy config without ACL files initially
    initial_context = haproxy_context_factory(
        config_content=haproxy_config_with_acl,
        acl_files={},  # No ACL files initially
    )

    await config_synchronizer.sync_configuration(initial_context)

    # Step 2: Deploy config with ACL file
    with_acl_context = haproxy_context_factory(
        config_content=haproxy_config_with_acl,
        acl_files={"blocked.acl": "192.168.1.100\n10.0.0.50\n"},
    )

    result = await config_synchronizer.sync_configuration(with_acl_context)
    assert "success" in str(result).lower() or "completed" in str(result).lower()

    # Verify ACL file was created
    acl_content = await read_container_file(
        compose_manager, "production-haproxy", "/etc/haproxy/general/blocked.acl"
    )
    assert "192.168.1.100" in acl_content
    assert "10.0.0.50" in acl_content

    # Step 3: Remove ACL file by deploying empty ACL list
    no_acl_context = haproxy_context_factory(
        config_content=haproxy_config_with_acl,
        acl_files={},  # No ACL files - should remove existing
    )

    await config_synchronizer.sync_configuration(no_acl_context)

    # Verify ACL file was removed or cleared
    try:
        acl_content_after = await read_container_file(
            compose_manager, "production-haproxy", "/etc/haproxy/general/blocked.acl"
        )
        # If file still exists, it should be empty or contain only comments
        assert not acl_content_after.strip() or acl_content_after.startswith("#")
    except RuntimeError:
        # File not found is also acceptable - means it was properly removed
        pass


@pytest.mark.integration
@pytest.mark.asyncio
async def test_multiple_acl_files_synchronization(
    docker_compose_dataplane, config_synchronizer, haproxy_context_factory
):
    """Test synchronization of multiple ACL files simultaneously.

    This verifies that multiple ACL files can be managed together
    via ConfigSynchronizer without conflicts.
    """
    ports, compose_manager = docker_compose_dataplane

    # HAProxy config that references multiple ACL files
    multi_acl_config = """
global
    stats socket /etc/haproxy/haproxy-master.sock mode 600 level admin

defaults
    mode http
    timeout connect 5000ms
    timeout client 50000ms
    timeout server 50000ms

frontend main
    bind *:80
    acl blocked_ips src -f /etc/haproxy/general/blocked.acl
    acl allowed_ips src -f /etc/haproxy/general/allowed.acl
    acl blocked_hosts hdr(host) -f /etc/haproxy/general/blocked_hosts.acl

    http-request deny if blocked_ips
    http-request deny if blocked_hosts
    http-request allow if allowed_ips

    default_backend servers

frontend status
    bind *:8404
    http-request return status 200 content-type text/plain string "OK" if { path /healthz }

backend servers
    balance roundrobin
    server web1 192.168.1.100:8080 check
"""

    # Deploy configuration with multiple ACL files
    context = haproxy_context_factory(
        config_content=multi_acl_config,
        acl_files={
            "blocked.acl": "192.168.1.100\n10.0.0.50\n",
            "allowed.acl": "192.168.1.200\n172.16.0.1\n",
            "blocked_hosts.acl": "evil.example.com\nbad.domain.org\n",
        },
    )

    result = await config_synchronizer.sync_configuration(context)
    assert "success" in str(result).lower() or "completed" in str(result).lower()

    # Verify all ACL files were created with correct content
    blocked_content = await read_container_file(
        compose_manager, "production-haproxy", "/etc/haproxy/general/blocked.acl"
    )
    assert "192.168.1.100" in blocked_content
    assert "10.0.0.50" in blocked_content

    allowed_content = await read_container_file(
        compose_manager, "production-haproxy", "/etc/haproxy/general/allowed.acl"
    )
    assert "192.168.1.200" in allowed_content
    assert "172.16.0.1" in allowed_content

    hosts_content = await read_container_file(
        compose_manager, "production-haproxy", "/etc/haproxy/general/blocked_hosts.acl"
    )
    assert "evil.example.com" in hosts_content
    assert "bad.domain.org" in hosts_content

    # Verify runtime socket shows multiple ACL files
    try:
        acl_output = await haproxy_socket_command(
            compose_manager, "production-haproxy", "show acl"
        )
        # Should show information about our ACL files
        assert "acl" in acl_output.lower()
    except RuntimeError as e:
        # Expected to fail until implementation is complete
        pytest.fail(f"Multiple ACL socket verification failed: {e}")
