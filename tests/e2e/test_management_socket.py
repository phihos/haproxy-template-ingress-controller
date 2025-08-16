"""
Tests for management socket functionality.

This module contains tests that verify the HAProxy Template IC operator's
management socket operations, including all socket commands, response
validation, and error handling.
"""

import pytest

from tests.e2e.utils import (
    wait_for_operator_ready,
    send_socket_command,
    assert_dump_all_response_structure,
    assert_operator_health,
)


@pytest.mark.acceptance
def test_management_socket(ingress_controller, collect_coverage):
    """Test comprehensive management socket functionality.

    This test verifies:
    1. The management socket becomes available
    2. All socket commands work correctly
    3. Response data has expected structure and content
    4. Error handling works for invalid commands
    5. The operator remains healthy during socket operations
    """
    # Wait for operator to be ready
    wait_for_operator_ready(ingress_controller)

    # Test 'dump all' command with comprehensive validation
    _test_dump_all_command(ingress_controller)

    # Test individual dump commands
    _test_dump_indices_command(ingress_controller)
    _test_dump_config_command(ingress_controller)

    # Test error handling
    _test_error_handling(ingress_controller)

    # Verify operator health
    assert_operator_health(ingress_controller)


def _test_dump_all_command(pod):
    """Assert that 'dump all' response has expected structure and content."""
    response = send_socket_command(pod, "dump all")
    assert_dump_all_response_structure(response)


def _test_dump_indices_command(pod):
    """Test the 'dump indices' command."""
    response = send_socket_command(pod, "dump indices")
    assert "indices" in response


def _test_dump_config_command(pod):
    """Test the 'dump config' command."""
    response = send_socket_command(pod, "dump config")
    # Verify nested structure exists
    assert "haproxy_config_context" in response
    assert "rendered_maps" in response["haproxy_config_context"]


def _test_error_handling(pod):
    """Test error handling for invalid socket commands."""
    # Test invalid command
    response = send_socket_command(pod, "invalid command")
    assert "error" in response
    assert "Unknown command" in response["error"]

    # Test empty command
    response = send_socket_command(pod, "")
    assert "error" in response
    assert "Empty command" in response["error"]
