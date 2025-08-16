"""
Tests for core HAProxy Template IC operator functionality.

This module contains tests that verify the basic operation of the
HAProxy Template IC operator, including initialization, startup,
and basic state management.
"""

import pytest

from tests.e2e.utils import (
    wait_for_operator_ready,
    send_socket_command,
    verify_response_has_structure,
    verify_config_contains,
    assert_config_structure,
)


@pytest.mark.acceptance
def test_basic_init(ingress_controller, collect_coverage):
    """Test that the operator initializes successfully.

    This test verifies:
    1. The operator starts and initializes configuration
    2. The management socket becomes available
    3. Basic state can be queried via the socket
    """
    wait_for_operator_ready(ingress_controller)

    # Verify we can query the operator state and config is loaded correctly
    response = send_socket_command(ingress_controller, "dump all")
    verify_response_has_structure(response, ["config", "metadata"])

    expected_metadata = {"configmap_name": "haproxy-template-ic-config"}
    verify_config_contains(response["metadata"], expected_metadata)
    assert_config_structure(response["config"])
