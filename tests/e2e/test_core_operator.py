"""
Tests for core HAProxy Template IC operator functionality.

This module contains tests that verify the basic operation of the
HAProxy Template IC operator, including initialization, startup,
and basic state management.
"""

import pytest

from tests.e2e.utils import (
    wait_for_operator_ready,
)


@pytest.mark.acceptance
def test_basic_init(operator, management_socket, collect_coverage):
    """Test that the operator initializes successfully.

    This test verifies:
    1. The operator starts and initializes configuration
    2. The management socket becomes available
    3. Basic state can be queried via the socket
    """
    wait_for_operator_ready(operator)

    application_state = management_socket.application_state()

    # Verify configmap name is in CLI options
    expected_configmap_name = "haproxy-template-ic-config"
    assert (
        application_state.runtime.cli_options.configmap_name == expected_configmap_name
    )
