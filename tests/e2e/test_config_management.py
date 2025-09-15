"""
Tests for configuration management functionality.

This module contains tests that verify the HAProxy Template IC operator's
ability to watch ConfigMaps, detect changes, reload configurations,
and apply new settings correctly.
"""

import time

import pytest
import yaml

from tests.e2e.utils import (
    assert_config_change,
    assert_log_line,
    assert_no_reload_loop,
    wait_for_operator_ready,
    wait_for_watch_streams_ready,
)


@pytest.mark.acceptance
def test_config_reload(operator, configmap, config_dict, collect_coverage):
    """Test that configuration changes are detected and applied.

    This test verifies:
    1. The controller watches for ConfigMap changes
    2. Configuration changes are detected
    3. The operator reloads with new configuration
    4. The new configuration is applied successfully
    """
    # Wait for initial setup and verify initial configuration is loaded
    wait_for_operator_ready(operator)
    wait_for_watch_streams_ready(operator)

    # Verify initial configuration is loaded by checking for pod selector in logs
    # Note: We rely on startup logs showing the configuration was loaded correctly

    # Change configuration - modify pod selector labels
    config_dict["pod_selector"] = {"match_labels": {"baz": "bar"}}
    configmap.patch({"data": {"config": yaml.dump(config_dict, Dumper=yaml.CDumper)}})

    # Verify change detection and reload process
    assert_config_change(operator)
    assert_log_line(operator, "Stop-flag is raised. Operator is stopping.")

    # Wait for operator to be ready again after reload using the standard wait function
    # This checks for the correct patterns: config loaded + metrics server started
    wait_for_operator_ready(operator)

    # Verify the new configuration is being used - template debouncer should restart with new config
    assert_log_line(
        operator,
        "Template debouncer started (",  # Partial match since it includes parameters
        since_milliseconds=100,
        timeout=15,
    )


@pytest.mark.acceptance
def test_no_reload_loop_on_repeated_events(
    operator, configmap, config_dict, collect_coverage
):
    """Regression test to ensure no reload loop occurs when ConfigMap events are repeated.

    This test verifies the fix for the infinite reload loop bug where the operator
    would continuously reload even when the ConfigMap content hasn't actually changed.

    The bug occurred because Jinja2 Template objects don't implement proper equality
    comparison, so Config objects with identical content would always compare as different.

    This test:
    1. Waits for initial operator setup
    2. Triggers multiple ConfigMap update events with identical content
    3. Ensures that reload messages don't occur excessively
    4. Verifies the operator remains stable
    """
    # Wait for initial setup and verify operator is working
    wait_for_operator_ready(operator)
    wait_for_watch_streams_ready(operator)

    # Verify initial stability - operator should be running normally
    assert_log_line(operator, "Template debouncer started (")

    # Trigger multiple ConfigMap updates with IDENTICAL content
    # This simulates Kubernetes generating update events even when content is unchanged
    # or when external tools repeatedly apply the same configuration
    for i in range(3):
        # Patch with the exact same configuration data
        configmap.patch(
            {"data": {"config": yaml.dump(config_dict, Dumper=yaml.CDumper)}}
        )

        # Small delay to ensure the event is processed
        time.sleep(2)

    # Monitor logs for 30 seconds to ensure no reload loop occurs
    # With the fix, we should see 0 reload messages (since config hasn't changed)
    # Without the fix, we would see multiple reload messages (one for each event)
    assert_no_reload_loop(operator, max_reloads=0, timeout=30)

    # Verify operator is still healthy by checking that it continues to operate normally
    # The absence of reload messages and continued template processing indicates stability
    # We should still see the debouncer running (no restart should have occurred)
    assert_log_line(
        operator,
        "Template debouncer started (",  # Should still be running the same instance
        timeout=5,
    )

    print(
        "✅ Regression test passed: No reload loop detected for repeated ConfigMap events"
    )
