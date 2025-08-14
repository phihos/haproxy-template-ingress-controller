"""
Acceptance tests for HAProxy Template IC.

These tests verify the operator's behavior in a real Kubernetes environment
using a kind cluster. They test integration between components and validate
end-to-end functionality.
"""

import json
import time

import pytest
import yaml

# =============================================================================
# Test Utilities
# =============================================================================


def assert_log_line(pod, expected_log_line, timeout=5):
    """Assert that a specific log line appears in the pod's logs within timeout.

    Args:
        pod: The Kubernetes pod object to monitor logs from
        expected_log_line: The log line text to search for (partial match)
        timeout: Maximum time to wait for the log line (default: 5 seconds)

    Returns:
        str: The complete log output collected during the search

    Raises:
        pytest.fail: If the expected log line is not found within timeout
    """
    if not expected_log_line.strip():
        pytest.fail("Expected log line cannot be empty")

    collected_logs = []
    lines_checked = 0
    start_time = time.time()

    try:
        # Stream logs with timeout
        for log_line in pod.logs(follow=True, timeout=timeout):
            lines_checked += 1
            line_text = str(log_line).strip()
            collected_logs.append(line_text)

            # Check if we found the expected log line
            if expected_log_line in line_text:
                elapsed_time = time.time() - start_time
                print(
                    f"✅ Found expected log line after {elapsed_time:.2f}s and {lines_checked} lines"
                )
                return "\n".join(collected_logs)

            # Check timeout periodically to avoid hanging
            elapsed_time = time.time() - start_time
            if elapsed_time > timeout:
                break

    except Exception as e:
        elapsed_time = time.time() - start_time
        _log_search_failure(
            expected_log_line=expected_log_line,
            collected_logs=collected_logs,
            lines_checked=lines_checked,
            elapsed_time=elapsed_time,
            timeout=timeout,
            error=str(e),
        )

    # If we reach here, the log line was not found
    elapsed_time = time.time() - start_time
    _log_search_failure(
        expected_log_line=expected_log_line,
        collected_logs=collected_logs,
        lines_checked=lines_checked,
        elapsed_time=elapsed_time,
        timeout=timeout,
    )


def _log_search_failure(
    expected_log_line, collected_logs, lines_checked, elapsed_time, timeout, error=None
):
    """Helper function to provide detailed failure information for log line searches."""
    full_log_text = (
        "\n".join(collected_logs) if collected_logs else "(no logs collected)"
    )

    failure_message = [
        f"❌ Expected log line not found: '{expected_log_line}'",
        "",
        "Search details:",
        f"  • Timeout: {timeout}s",
        f"  • Elapsed time: {elapsed_time:.2f}s",
        f"  • Lines checked: {lines_checked}",
    ]

    if error:
        failure_message.extend([f"  • Error occurred: {error}", ""])

    failure_message.extend(
        [
            "",
            f"Complete log output ({len(collected_logs)} lines):",
            f"{'=' * 80}",
            full_log_text,
            f"{'=' * 80}",
        ]
    )

    # Add recent lines for easier debugging
    if collected_logs:
        recent_lines = (
            collected_logs[-10:] if len(collected_logs) > 10 else collected_logs
        )
        failure_message.extend(
            [
                "",
                f"Last {len(recent_lines)} lines:",
                f"{'-' * 40}",
            ]
        )
        for i, line in enumerate(recent_lines, 1):
            failure_message.append(f"{i:2d}: {line}")
        failure_message.append(f"{'-' * 40}")

    pytest.fail("\n".join(failure_message))


def send_socket_command(pod, command):
    """Send a command to the management socket using socat and return the response."""
    try:
        # Use echo to pipe command to socat
        cmd = f'echo "{command}" | socat - UNIX-CONNECT:/run/haproxy-template-ic/management.sock'
        result = pod.exec(["sh", "-c", cmd])

        # Parse the response
        response_text = result.stdout.decode("utf-8")
        return json.loads(response_text)
    except Exception as e:
        pytest.fail(f"Failed to communicate with management socket: {e}")


def wait_for_operator_ready(pod):
    """Wait for the operator to be fully initialized and ready."""
    assert_log_line(pod, "✅ Configuration loaded successfully.")
    assert_log_line(
        pod,
        "🔌 Management socket server listening on /run/haproxy-template-ic/management.sock",
    )


def assert_config_structure(config):
    """Assert that config has the expected structure and values."""
    assert config["pod_selector"] == {"match_labels": {"foo": "bar"}}
    assert "watch_resources" in config
    assert "maps" in config
    assert "ingresses" in config["watch_resources"]
    assert config["watch_resources"]["ingresses"]["kind"] == "Ingress"
    assert config["watch_resources"]["ingresses"]["group"] == "networking.k8s.io"


def assert_operator_health(pod):
    """Assert that the operator is healthy and functioning."""
    assert_log_line(pod, "Serving health status at http://0.0.0.0:8080/healthz")
    assert_log_line(pod, "Starting the watch-stream for configmaps.v1 cluster-wide")


# =============================================================================
# Acceptance Tests
# =============================================================================


@pytest.mark.slow
def test_basic_init(ingress_controller, collect_coverage):
    """Test that the operator initializes successfully.

    This test verifies:
    1. The operator starts and initializes configuration
    2. The management socket becomes available
    3. Basic state can be queried via the socket
    """
    # Wait for operator to be ready
    wait_for_operator_ready(ingress_controller)

    # Verify we can query the operator state
    response = send_socket_command(ingress_controller, "dump all")

    # Basic assertions about the state
    assert "config" in response
    assert "metadata" in response
    assert response["metadata"]["configmap_name"] == "haproxy-template-ic-config"

    # Verify config is loaded correctly
    assert_config_structure(response["config"])


@pytest.mark.slow
def test_config_reload(ingress_controller, configmap, config_dict, collect_coverage):
    """Test that configuration changes are detected and applied.

    This test verifies:
    1. The controller watches for ConfigMap changes
    2. Configuration changes are detected
    3. The operator reloads with new configuration
    4. The new configuration is accessible via management socket
    """
    # Wait for initial setup
    wait_for_operator_ready(ingress_controller)
    assert_log_line(
        ingress_controller,
        "Starting the watch-stream for configmaps.v1 cluster-wide.",
    )

    # Verify initial configuration via socket
    initial_response = send_socket_command(ingress_controller, "dump all")
    assert_config_structure(initial_response["config"])

    # Change configuration
    config_dict["pod_selector"] = {"match_labels": {"baz": "bar"}}
    configmap.patch({"data": {"config": yaml.dump(config_dict, Dumper=yaml.CDumper)}})

    # Verify change detection and reload
    assert_log_line(ingress_controller, "🔄 Config has changed:")
    assert_log_line(ingress_controller, "Stop-flag is raised. Operator is stopping.")
    assert_log_line(
        ingress_controller, "🔄 Configuration changed. Reinitializing...", timeout=10
    )
    assert_log_line(ingress_controller, "✅ Configuration loaded successfully.")

    # Verify new configuration is applied via socket
    updated_response = send_socket_command(ingress_controller, "dump all")
    assert updated_response["config"]["pod_selector"] == {
        "match_labels": {"baz": "bar"}
    }


@pytest.mark.slow
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
    _assert_dump_all_command(ingress_controller)

    # Test individual dump commands
    _test_dump_indices_command(ingress_controller)
    _test_dump_config_command(ingress_controller)

    # Test error handling
    _test_error_handling(ingress_controller)

    # Verify operator health
    assert_operator_health(ingress_controller)


def _assert_dump_all_command(pod):
    """Assert that 'dump all' response has expected structure and content."""
    response = send_socket_command(pod, "dump all")

    # Verify response structure
    assert "config" in response
    assert "haproxy_config_context" in response
    assert "metadata" in response
    assert "indices" in response
    assert "cli_options" in response

    # Verify config data
    assert_config_structure(response["config"])

    # Verify metadata
    assert response["metadata"]["configmap_name"] == "haproxy-template-ic-config"
    assert response["metadata"]["has_config_reload_flag"] is True
    assert response["metadata"]["has_stop_flag"] is True

    # Verify CLI options
    assert response["cli_options"]["configmap_name"] == "haproxy-template-ic-config"
    assert (
        response["cli_options"]["socket_path"]
        == "/run/haproxy-template-ic/management.sock"
    )


def _test_dump_indices_command(pod):
    """Test the 'dump indices' command."""
    response = send_socket_command(pod, "dump indices")
    assert "indices" in response
    assert isinstance(response["indices"], dict)


def _test_dump_config_command(pod):
    """Test the 'dump config' command."""
    response = send_socket_command(pod, "dump config")
    assert "haproxy_config_context" in response
    assert "rendered_maps" in response["haproxy_config_context"]
    assert isinstance(response["haproxy_config_context"]["rendered_maps"], dict)


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
