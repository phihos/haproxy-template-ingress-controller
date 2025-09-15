"""
Tests for core HAProxy Template IC operator functionality.

This module contains tests that verify the basic operation of the
HAProxy Template IC operator, including initialization, startup,
and basic state management.
"""

import pytest

from tests.e2e.utils import (
    assert_operator_health,
    wait_for_operator_ready,
)


@pytest.mark.acceptance
def test_basic_init(operator, collect_coverage):
    """Test that the operator initializes successfully.

    This test verifies:
    1. The operator starts and initializes configuration
    2. The operator process remains healthy
    3. No critical errors occur during initialization
    """
    wait_for_operator_ready(operator)

    # Verify operator is healthy and running
    assert_operator_health(operator)

    # Check logs for successful initialization
    logs = operator.get_logs()
    # Verify configuration was loaded successfully
    assert "✅ Configuration and credentials loaded successfully." in logs
    # Verify metrics server started
    assert "📊 Metrics server started on port" in logs
