"""
Operator-specific utilities for HAProxy Template IC tests.

This module contains utilities for interacting with the HAProxy Template IC
operator, including log monitoring, state checking, and operator lifecycle
management during end-to-end tests.
"""

import time

import pytest


def assert_log_line(pod, expected_log_line, timeout=5):
    """Assert that a specific log line appears in the pod's logs within timeout.

    Args:
        pod: The Kubernetes pod object to monitor logs from
        expected_log_line: The log line text to search for (partial match)
        timeout: Maximum time to wait for the log line (default: 5 seconds)
                Note: For config change operations, consider using longer timeouts (10-15s)
                as these can be slower in parallel test environments.

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
        # Stream logs with timeout and retry on network errors
        max_retries = 3
        for retry in range(max_retries):
            try:
                for log_line in pod.logs(
                    follow=True, timeout=timeout, container="haproxy-template-ic"
                ):
                    lines_checked += 1
                    line_text = str(log_line).strip()
                    collected_logs.append(line_text)

                    # Check if we found the expected log line
                    if expected_log_line in line_text:
                        elapsed_time = time.time() - start_time
                        print(
                            f"✅ Found expected log line after {elapsed_time:.2f}s and {lines_checked} lines"
                        )
                        return "\\n".join(collected_logs)

                    # Check timeout periodically to avoid hanging
                    elapsed_time = time.time() - start_time
                    if elapsed_time > timeout:
                        break
                break  # If we get here, log stream ended normally
            except (ConnectionError, TimeoutError, Exception) as e:
                print(f"⚠️ Log reading attempt {retry + 1} failed: {e}")
                if retry == max_retries - 1:
                    raise
                time.sleep(1)  # Brief pause before retry

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
    return None


def _log_search_failure(
    expected_log_line, collected_logs, lines_checked, elapsed_time, timeout, error=None
):
    """Helper function to provide detailed failure information for log line searches."""
    full_log_text = (
        "\\n".join(collected_logs) if collected_logs else "(no logs collected)"
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

    pytest.fail("\\n".join(failure_message))


def wait_for_operator_ready(pod):
    """Wait for the operator to be fully initialized and ready."""
    assert_log_line(pod, "✅ Configuration loaded successfully.")
    assert_log_line(
        pod,
        "🔌 Management socket server listening on /run/haproxy-template-ic/management.sock",
    )


def wait_for_watch_streams_ready(pod):
    """Wait for the operator to establish watch streams for ConfigMap changes."""
    assert_log_line(
        pod,
        "Starting the watch-stream for configmaps.v1 cluster-wide.",
    )


def assert_config_change(pod, timeout=30):
    """Assert that a configuration change is detected and processed."""
    assert_log_line(pod, "🔄 Config has changed:", timeout=timeout)
    assert_log_line(pod, "✅ Configuration loaded successfully.", timeout=timeout)


def count_log_occurrences(pod, pattern, timeout=30):
    """Count how many times a pattern appears in pod logs within timeout period.

    Args:
        pod: The Kubernetes pod to read logs from
        pattern: The string pattern to count occurrences of
        timeout: Time window in seconds to collect logs

    Returns:
        int: Number of times the pattern was found in logs
    """
    import time

    collected_logs = []
    start_time = time.time()

    try:
        # Stream logs for the specified timeout period
        for log_line in pod.logs(
            follow=True, timeout=timeout, container="haproxy-template-ic"
        ):
            line_text = str(log_line).strip()
            collected_logs.append(line_text)

            # Check if we've exceeded the timeout
            elapsed_time = time.time() - start_time
            if elapsed_time >= timeout:
                break

    except (ConnectionError, TimeoutError, Exception):
        # Log stream ended or error occurred, continue with what we have
        pass

    # Count occurrences of pattern in all collected logs
    count = 0
    for log_line in collected_logs:
        if pattern in log_line:
            count += 1

    return count


def assert_no_reload_loop(pod, max_reloads=1, timeout=30):
    """Assert that the operator doesn't enter a reload loop.

    Monitors logs for a specified time period and ensures that reload
    messages don't occur excessively, which would indicate a reload loop.

    Args:
        pod: The Kubernetes pod to monitor
        max_reloads: Maximum number of reload messages expected (default: 1)
        timeout: Time period to monitor in seconds (default: 30)
    """
    reload_count = count_log_occurrences(
        pod, "🔄 Config has changed: reloading", timeout
    )

    if reload_count > max_reloads:
        pytest.fail(
            f"Reload loop detected! Found {reload_count} reload messages "
            f"within {timeout} seconds (expected at most {max_reloads})"
        )

    print(
        f"✅ No reload loop detected. Found {reload_count} reload(s) in {timeout}s (expected ≤{max_reloads})"
    )


def assert_operator_health(pod):
    """Assert that the operator is healthy and functioning."""
    assert_log_line(pod, "Serving health status at http://0.0.0.0:8080/healthz")
    assert_log_line(pod, "Starting the watch-stream for configmaps.v1 cluster-wide")
