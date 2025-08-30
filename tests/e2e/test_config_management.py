"""
Tests for configuration management functionality.

This module contains tests that verify the HAProxy Template IC operator's
ability to watch ConfigMaps, detect changes, reload configurations,
and apply new settings correctly.
"""

import pytest
import time
import yaml

from tests.e2e.utils import (
    wait_for_operator_ready,
    wait_for_watch_streams_ready,
    send_socket_command,
    assert_config_structure,
    assert_config_change,
    assert_log_line,
    verify_config_contains,
    assert_no_reload_loop,
)


@pytest.mark.acceptance
def test_config_reload(operator, configmap, config_dict, collect_coverage):
    """Test that configuration changes are detected and applied.

    This test verifies:
    1. The controller watches for ConfigMap changes
    2. Configuration changes are detected
    3. The operator reloads with new configuration
    4. The new configuration is accessible via management socket
    """
    # Wait for initial setup and verify initial configuration
    wait_for_operator_ready(operator)
    wait_for_watch_streams_ready(operator)

    initial_response = send_socket_command(operator, "dump all")
    assert_config_structure(initial_response["config"])

    # Change configuration
    config_dict["pod_selector"] = {"match_labels": {"baz": "bar"}}
    configmap.patch({"data": {"config": yaml.dump(config_dict, Dumper=yaml.CDumper)}})

    # Verify change detection and reload process
    assert_config_change(operator)
    assert_log_line(operator, "Stop-flag is raised. Operator is stopping.")
    assert_log_line(operator, "🔄 Configuration changed. Reinitializing...", timeout=10)

    # Wait for operator to be ready again after reload
    wait_for_operator_ready(operator)

    # Verify new configuration is applied
    updated_response = send_socket_command(operator, "dump all")
    expected_new_config = {"pod_selector": {"match_labels": {"baz": "bar"}}}
    verify_config_contains(updated_response["config"], expected_new_config)


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

    initial_response = send_socket_command(operator, "dump all")
    assert_config_structure(initial_response["config"])

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

    # Verify operator is still healthy and configuration is unchanged
    final_response = send_socket_command(operator, "dump all")
    verify_config_contains(final_response["config"], initial_response["config"])

    print(
        "✅ Regression test passed: No reload loop detected for repeated ConfigMap events"
    )
