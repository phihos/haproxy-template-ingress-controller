"""
Tests for core HAProxy Template IC operator functionality.

This module contains tests that verify the basic operation of the
HAProxy Template IC operator, including initialization, startup,
and basic state management.
"""

import pytest
import yaml

from tests.e2e.utils import (
    assert_no_handler_failures,
    assert_operator_health,
    wait_for_operator_ready,
    wait_for_watch_streams_ready,
)


@pytest.mark.acceptance
def test_basic_init(operator, configmap, config_dict, collect_coverage):
    """Test that the operator initializes successfully and handles configmap events.

    This test verifies:
    1. The operator starts and initializes configuration
    2. The operator process remains healthy
    3. No critical errors occur during initialization
    4. ConfigMap event handlers work without signature errors
    """
    wait_for_operator_ready(operator)
    wait_for_watch_streams_ready(operator)

    # Verify operator is healthy and running
    assert_operator_health(operator)

    # Check logs for successful initialization
    logs = operator.get_logs()
    # Verify configuration was loaded successfully
    assert "✅ Configuration and credentials loaded successfully." in logs
    # Verify metrics server started
    assert "📊 Metrics server started on port" in logs

    # Trigger a configmap change to test handler signature compatibility
    # This should trigger the handle_configmap_change handler
    configmap.patch({"data": {"config": yaml.dump(config_dict, Dumper=yaml.CDumper)}})

    # Monitor for handler failures for 5 seconds
    # This will catch kopf signature mismatches like unexpected keyword arguments
    assert_no_handler_failures(operator, timeout=5)
