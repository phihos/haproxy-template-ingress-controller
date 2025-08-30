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
def test_management_socket(operator, collect_coverage):
    """Test comprehensive management socket functionality.

    This test verifies:
    1. The management socket becomes available
    2. All socket commands work correctly
    3. Response data has expected structure and content
    4. Error handling works for invalid commands
    5. The operator remains healthy during socket operations
    """
    # Wait for operator to be ready
    wait_for_operator_ready(operator)

    # Test 'dump all' command with comprehensive validation
    _test_dump_all_command(operator)

    # Test individual dump commands
    _test_dump_indices_command(operator)
    _test_dump_config_command(operator)

    # Test error handling
    _test_error_handling(operator)

    # Verify operator health
    assert_operator_health(operator)


def _test_dump_all_command(operator):
    """Assert that 'dump all' response has expected structure and content."""
    response = send_socket_command(operator, "dump all")
    assert_dump_all_response_structure(response)


def _test_dump_indices_command(operator):
    """Test the 'dump indices' command."""
    response = send_socket_command(operator, "dump indices")
    assert "indices" in response


def _test_dump_config_command(operator):
    """Test the 'dump config' command."""
    response = send_socket_command(operator, "dump config")
    # Verify nested structure exists
    assert "haproxy_config_context" in response
    assert "rendered_maps" in response["haproxy_config_context"]


def _test_error_handling(operator):
    """Test error handling for invalid socket commands."""
    # Test invalid command
    response = send_socket_command(operator, "invalid command")
    assert "error" in response
    assert "Unknown command" in response["error"]

    # Test empty command
    response = send_socket_command(operator, "")
    assert "error" in response
    assert "Empty command" in response["error"]
