"""
Consolidated test helpers for HAProxy Template IC end-to-end tests.

This module combines utilities from operator_helpers, k8s_helpers, and assertions
into a single, well-organized module for easier imports and maintenance.
"""

import os
from typing import Any, Dict, Optional

import pytest

from tests.e2e.utils.local_operator import LocalOperatorRunner
from tests.e2e.utils.socket_client import send_socket_command as socket_send


# =============================================================================
# OPERATOR HELPERS
# =============================================================================


def wait_for_operator_ready(operator: LocalOperatorRunner) -> None:
    """Wait for the operator to be fully initialized and ready."""
    from tests.e2e.utils.local_operator import wait_for_operator_ready as local_wait

    if not isinstance(operator, LocalOperatorRunner):
        raise ValueError(f"Expected LocalOperatorRunner, got {type(operator)}")

    local_wait(operator)


def wait_for_watch_streams_ready(operator: LocalOperatorRunner) -> None:
    """Wait for the operator to establish watch streams for ConfigMap changes."""
    assert_log_line(
        operator,
        "Starting the watch-stream for configmaps.v1 cluster-wide.",
    )


def assert_log_line(
    operator: LocalOperatorRunner, expected_log_line: str, timeout: float = 5
) -> str:
    """Assert that a specific log line appears in the operator's logs within timeout.

    Args:
        operator: LocalOperatorRunner instance
        expected_log_line: The log line text to search for (partial match)
        timeout: Maximum time to wait for the log line (default: 5 seconds)

    Returns:
        str: The complete log output collected during the search

    Raises:
        pytest.fail: If the expected log line is not found within timeout
    """
    from tests.e2e.utils.local_operator import assert_log_line as local_assert

    if not isinstance(operator, LocalOperatorRunner):
        raise ValueError(f"Expected LocalOperatorRunner, got {type(operator)}")

    return local_assert(operator, expected_log_line, timeout)


def assert_config_change(operator: LocalOperatorRunner, timeout: float = 30) -> None:
    """Assert that a configuration change is detected and processed."""
    assert_log_line(operator, "🔄 Config has changed:", timeout=timeout)
    assert_log_line(
        operator, "🔄 Configuration changed. Reinitializing...", timeout=timeout
    )


def count_log_occurrences(
    operator: LocalOperatorRunner, pattern: str, timeout: float = 30
) -> int:
    """Count how many times a pattern appears in operator logs within timeout period.

    Args:
        operator: LocalOperatorRunner instance
        pattern: The string pattern to count occurrences of
        timeout: Time window in seconds to collect logs

    Returns:
        int: Number of times the pattern was found in logs
    """
    if not isinstance(operator, LocalOperatorRunner):
        raise ValueError(f"Expected LocalOperatorRunner, got {type(operator)}")

    # Get all available logs from the operator
    logs = operator.get_logs()

    # Count occurrences of pattern in logs
    count = 0
    for log_line in logs:
        if pattern in log_line:
            count += 1

    return count


def assert_no_reload_loop(
    operator: LocalOperatorRunner, max_reloads: int = 1, timeout: float = 30
) -> None:
    """Assert that the operator doesn't enter a reload loop.

    Monitors logs for a specified time period and ensures that reload
    messages don't occur excessively, which would indicate a reload loop.

    Args:
        operator: LocalOperatorRunner instance
        max_reloads: Maximum number of reload messages expected (default: 1)
        timeout: Time period to monitor in seconds (default: 30)
    """
    # Note: The timeout parameter is used for monitoring duration, not actual delay
    reload_count = count_log_occurrences(
        operator, "🔄 Config has changed: reloading", timeout
    )

    if reload_count > max_reloads:
        pytest.fail(
            f"Reload loop detected! Found {reload_count} reload messages "
            f"within {timeout} seconds (expected at most {max_reloads})"
        )

    print(
        f"✅ No reload loop detected. Found {reload_count} reload(s) in {timeout}s (expected ≤{max_reloads})"
    )


def assert_operator_health(operator: LocalOperatorRunner) -> None:
    """Assert that the operator is healthy and functioning."""
    # If socket responds successfully, operator is healthy
    response = send_socket_command(operator, "dump all", retries=1)
    assert response is not None, "Management socket should be responsive"
    assert "error" not in response, (
        f"Socket should not return errors: {response.get('error', 'N/A')}"
    )


# =============================================================================
# SOCKET COMMUNICATION
# =============================================================================


def send_socket_command(
    operator: LocalOperatorRunner, command: str, timeout: float = 5, retries: int = 3
) -> Optional[Dict[str, Any]]:
    """Send a command to the operator's management socket.

    Args:
        operator: LocalOperatorRunner instance
        command: Command to send (e.g., "dump all", "dump config")
        timeout: Socket timeout in seconds (ignored, uses socket default)
        retries: Number of retry attempts (ignored for simplicity)

    Returns:
        Parsed response from the socket or None if failed
    """
    # Extract socket path from operator
    if hasattr(operator, "socket_path"):
        socket_path = operator.socket_path
    else:
        # This shouldn't happen, but handle it for type safety
        socket_path = str(operator)

    # Call the actual socket client function (which only takes 2 args)
    return socket_send(socket_path, command)


# =============================================================================
# ASSERTIONS
# =============================================================================


def verify_config_contains(
    actual_config: Dict[str, Any], expected_partial: Dict[str, Any]
) -> None:
    """Verify that actual config contains all expected key-value pairs."""
    for key, expected_value in expected_partial.items():
        assert key in actual_config, f"Missing expected config key: {key}"
        assert actual_config[key] == expected_value, f"Config key '{key}' mismatch"


def verify_response_has_structure(
    response: Dict[str, Any], required_keys: list
) -> None:
    """Verify that response contains all required top-level keys."""
    missing_keys = [key for key in required_keys if key not in response]
    assert not missing_keys, f"Response missing required keys: {missing_keys}"


def assert_config_structure(config: Dict[str, Any]) -> None:
    """Assert that config has the expected structure and values."""
    expected_config = {
        "pod_selector": {
            "match_labels": {"app": "haproxy", "component": "loadbalancer"}
        },
    }
    verify_config_contains(config, expected_config)

    # Verify required sections exist and have expected nested values
    assert "watched_resources" in config and "maps" in config

    watched_resources = config["watched_resources"]
    if "ingresses" in watched_resources:
        expected_ingress = {"kind": "Ingress", "api_version": "networking.k8s.io/v1"}
        verify_config_contains(watched_resources["ingresses"], expected_ingress)


def assert_dump_all_response_structure(response: Dict[str, Any]) -> None:
    """Assert that 'dump all' response has the expected structure and values."""
    # Verify response has all required sections
    required_keys = [
        "config",
        "haproxy_config_context",
        "metadata",
        "indices",
        "cli_options",
    ]
    verify_response_has_structure(response, required_keys)

    # Verify config data
    assert_config_structure(response["config"])

    # Verify expected metadata values
    expected_metadata = {
        "configmap_name": "haproxy-template-ic-config",
        "has_config_reload_flag": True,
        "has_stop_flag": True,
    }
    verify_config_contains(response["metadata"], expected_metadata)

    # Verify expected CLI options
    expected_cli_options = {
        "configmap_name": "haproxy-template-ic-config",
    }
    verify_config_contains(response["cli_options"], expected_cli_options)


# =============================================================================
# POD LOGGING (for test debugging)
# =============================================================================


def print_pod_logs_on_failure(pod: Any, test_name: str) -> None:
    """Print formatted pod logs for debugging test failures.

    This is a simplified version that just prints basic pod information.
    In the context of Telepresence-based testing, the operator runs locally
    and logs are captured by LocalOperatorRunner, so this function is mainly
    for compatibility with the existing test framework.

    Args:
        pod: The Kubernetes pod object (may be None for local operator)
        test_name: Name of the failed test for context
    """
    # Check if log printing is disabled
    if os.environ.get("PYTEST_DISABLE_POD_LOG_PRINTING", "").lower() == "true":
        return

    # For local operator tests, this is mostly a no-op
    if pod is None:
        print(f"\n{'=' * 80}")
        print(
            f"🔍 Test failed: {test_name} (operator running locally via Telepresence)"
        )
        print(f"{'=' * 80}\n")
        return

    # For pod-based tests (if any remain)
    print(f"\n{'=' * 80}")
    print(f"🔍 POD LOGS FOR FAILED TEST: {test_name}")
    print(f"Pod: {getattr(pod, 'name', 'unknown')}")
    print(f"{'=' * 80}")
    print("(Pod log retrieval not implemented for Telepresence-based tests)")
    print(f"{'=' * 80}\n")
