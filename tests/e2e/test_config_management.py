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
def test_config_reload(
    operator, management_socket, configmap, config_dict, collect_coverage
):
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

    initial_application_state = management_socket.application_state()
    assert (
        initial_application_state.configuration.config.pod_selector.match_labels
        == config_dict["pod_selector"]["match_labels"]
    )

    # Change configuration
    config_dict["pod_selector"] = {"match_labels": {"baz": "bar"}}
    configmap.patch({"data": {"config": yaml.dump(config_dict, Dumper=yaml.CDumper)}})

    # Verify change detection and reload process
    assert_config_change(operator)
    assert_log_line(operator, "Stop-flag is raised. Operator is stopping.")

    # Wait for operator to be ready again after reload
    assert_log_line(
        operator,
        "✅ Configuration and credentials loaded successfully.",
        since_milliseconds=100,
    )
    assert_log_line(
        operator, "🔌 Management socket server listening on", since_milliseconds=100
    )

    # Verify new configuration is applied
    updated_application_state = management_socket.application_state()
    assert updated_application_state.configuration.config.pod_selector.match_labels == {
        "baz": "bar"
    }


@pytest.mark.acceptance
def test_no_reload_loop_on_repeated_events(
    operator, management_socket, configmap, config_dict, collect_coverage
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

    initial_application_state = management_socket.application_state()

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
    updated_application_state = management_socket.application_state()
    # Compare the config objects directly
    assert (
        initial_application_state.configuration.config
        == updated_application_state.configuration.config
    )

    print(
        "✅ Regression test passed: No reload loop detected for repeated ConfigMap events"
    )
