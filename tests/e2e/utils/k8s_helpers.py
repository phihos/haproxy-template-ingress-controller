"""
Kubernetes interaction utilities for HAProxy Template IC tests.

This module provides comprehensive utilities for interacting with Kubernetes
resources, pods, and the management socket during end-to-end tests. It includes
automatic log collection, formatted output, and debugging capabilities.

Key Features:
    - Management socket communication with retry logic
    - Pod log retrieval with container-specific filtering
    - Automatic log printing on test failures
    - Configurable log limits and redaction
    - Error handling and recovery patterns

Environment Configuration:
    PYTEST_POD_LOG_TAIL_LINES: Default number of log lines to retrieve (default: varies by function)
    PYTEST_MAX_LOG_LINES_PER_CONTAINER: Hard limit per container (default: 1000)
    PYTEST_DISABLE_POD_LOG_PRINTING: Set to 'true' to disable automatic log printing
    PYTEST_POD_LOG_REDACT_SECRETS: Set to 'true' to enable secret redaction

Usage Patterns:
    # Basic management socket interaction
    response = send_socket_command(pod, "dump all")
    if response and "indices" in response:
        print(f"Active resources: {len(response['indices'])}")

    # Log collection for debugging
    logs = get_pod_logs(pod, ["haproxy", "dataplane"], tail_lines=100)
    for container, content in logs.items():
        if "ERROR" in content:
            print(f"Errors in {container}")

    # Automatic failure debugging (typically in pytest hooks)
    if test_failed:
        print_pod_logs_on_failure(pod, test_name)

Troubleshooting:
    Common Issues:
    - "Empty response from management socket":
      → Check pod readiness and socket availability
      → Verify socat is installed in the container
      → Ensure management socket is listening

    - "Error retrieving logs from container":
      → Verify container names are correct
      → Check pod and container status
      → Ensure pod is not in terminating state

    - Memory issues with large logs:
      → Reduce PYTEST_MAX_LOG_LINES_PER_CONTAINER
      → Use smaller tail_lines values
      → Enable log truncation warnings

    Performance Tips:
    - Use specific container_names instead of retrieving all containers
    - Set appropriate tail_lines based on expected log volume
    - Enable redaction in CI environments to prevent sensitive data exposure
    - Consider disabling log printing in automated environments
"""

import json
import logging
import os
import re
import shlex
import time
from typing import Any, Dict, List, Optional

import pytest

# Module-level logger for better performance
logger = logging.getLogger(__name__)

# Pre-compiled regex patterns for sensitive information detection (for performance)
_REDACTION_PATTERNS = [
    # Common credential patterns
    re.compile(r'(password["\s]*[:=]["\s]*)([^"\s\n]+)', re.IGNORECASE),
    re.compile(r'(passwd["\s]*[:=]["\s]*)([^"\s\n]+)', re.IGNORECASE),
    re.compile(r'(token["\s]*[:=]["\s]*)([^"\s\n]+)', re.IGNORECASE),
    re.compile(r'(secret["\s]*[:=]["\s]*)([^"\s\n]+)', re.IGNORECASE),
    re.compile(r'(key["\s]*[:=]["\s]*)([^"\s\n]+)', re.IGNORECASE),
    re.compile(r'(api_key["\s]*[:=]["\s]*)([^"\s\n]+)', re.IGNORECASE),
    # HTTP Authorization headers
    re.compile(r"(authorization:\s*)(bearer\s+[^\s\n]+)", re.IGNORECASE),
    re.compile(r"(authorization:\s*)(basic\s+[^\s\n]+)", re.IGNORECASE),
    # Base64 encoded content (likely sensitive if longer than 20 chars)
    re.compile(r'(["\s]|^)([A-Za-z0-9+/]{20,}={0,2})(["\s]|$)'),
    # JWT tokens (starts with ey)
    re.compile(r'([\s"\'])?(eyJ[A-Za-z0-9+/=.-]+)([\s"\'])?'),
    # Common environment variable patterns
    re.compile(r"(export\s+\w*(?:PASS|TOKEN|KEY|SECRET)\w*=)([^\s\n]+)", re.IGNORECASE),
    # URLs with credentials
    re.compile(r"(https?://)[^:\s]+:[^@\s]+@([^\s]+)"),
    # Connection strings
    re.compile(r"(password=)[^;\s]+", re.IGNORECASE),
    # Private keys
    re.compile(
        r"-----BEGIN [A-Z ]+PRIVATE KEY-----.*?-----END [A-Z ]+PRIVATE KEY-----",
        re.DOTALL | re.IGNORECASE,
    ),
]

# Corresponding replacement patterns (same order as compiled patterns)
_REPLACEMENT_PATTERNS = [
    r"\1***REDACTED***",  # password patterns
    r"\1***REDACTED***",  # passwd patterns
    r"\1***REDACTED***",  # token patterns
    r"\1***REDACTED***",  # secret patterns
    r"\1***REDACTED***",  # key patterns
    r"\1***REDACTED***",  # api_key patterns
    r"\1Bearer ***REDACTED***",  # authorization bearer
    r"\1Basic ***REDACTED***",  # authorization basic
    r"\1***REDACTED***\3",  # base64 content
    r"\1***REDACTED***\3",  # JWT tokens
    r"\1***REDACTED***",  # environment variables
    r"\1***REDACTED***@\2",  # URLs with credentials
    r"\1***REDACTED***",  # connection strings
    "-----BEGIN PRIVATE KEY-----\n***REDACTED***\n-----END PRIVATE KEY-----",  # private keys
]

# Constants for timeouts and limits
DEFAULT_SOCKET_RETRIES = 3
DEFAULT_SOCKET_RETRY_DELAY = 2
MAX_RETRIES_LIMIT = 10
MAX_ERROR_MESSAGE_LENGTH = 100
DEFAULT_POD_LOG_TAIL_LINES = 100
DEFAULT_MAX_LOG_LINES_PER_CONTAINER = 1000
MAX_VALIDATION_VALUE = 100000
MAX_TAIL_LINES_LIMIT = 50000
MAX_LOG_CONTENT_SIZE = 1_000_000
MAX_TEST_NAME_LENGTH = 100


# Input validation functions
def _validate_positive_int(
    value: str, default: int, name: str, min_value: int = 1
) -> int:
    """Validate that an environment variable is a positive integer.

    Args:
        value: String value to validate
        default: Default value to use if validation fails
        name: Name of the environment variable for logging
        min_value: Minimum allowed value (default: 1)

    Returns:
        Validated integer value or default
    """
    try:
        parsed = int(value)
        if parsed < min_value:
            logger.warning(f"{name} must be >= {min_value}, using default: {default}")
            return default
        if parsed > MAX_VALIDATION_VALUE:  # Reasonable upper limit
            logger.warning(f"{name} too large ({parsed}), using default: {default}")
            return default
        return parsed
    except (ValueError, TypeError):
        logger.warning(f"Invalid {name} value '{value}', using default: {default}")
        return default


# Cache environment variables to avoid repeated parsing with validation
_ENV_CACHE = {
    "pod_log_tail_lines": _validate_positive_int(
        os.environ.get("PYTEST_POD_LOG_TAIL_LINES", str(DEFAULT_POD_LOG_TAIL_LINES)),
        DEFAULT_POD_LOG_TAIL_LINES,
        "PYTEST_POD_LOG_TAIL_LINES",
        min_value=0,  # 0 allowed for "all logs"
    ),
    "max_log_lines_per_container": _validate_positive_int(
        os.environ.get(
            "PYTEST_MAX_LOG_LINES_PER_CONTAINER",
            str(DEFAULT_MAX_LOG_LINES_PER_CONTAINER),
        ),
        DEFAULT_MAX_LOG_LINES_PER_CONTAINER,
        "PYTEST_MAX_LOG_LINES_PER_CONTAINER",
    ),
    "disable_pod_log_printing": os.environ.get(
        "PYTEST_DISABLE_POD_LOG_PRINTING", ""
    ).lower()
    == "true",
    "redact_secrets": os.environ.get("PYTEST_POD_LOG_REDACT_SECRETS", "").lower()
    == "true",
}


def send_socket_command(
    pod: Any, command: str, retries: int = DEFAULT_SOCKET_RETRIES
) -> Optional[Dict[str, Any]]:
    """Send a command to the management socket using socat and return the response.

    Args:
        pod: The Kubernetes pod object containing the management socket
        command: Socket command to send (e.g., "dump all", "dump config")
        retries: Number of retry attempts on failure (default: 3)

    Returns:
        dict: Parsed JSON response from the management socket, or None on failure

    Raises:
        pytest.fail: If all retry attempts fail
        ValueError: If input parameters are invalid

    Example:
        >>> response = send_socket_command(pod, "dump all")
        >>> if response and "indices" in response:
        ...     print(f"Found {len(response['indices'])} resource indices")

    Note:
        Requires socat to be available in the pod. Uses automatic retry with
        exponential backoff on failures.
    """
    # Input validation
    if pod is None:
        raise ValueError("Pod cannot be None")

    if not command or not isinstance(command, str):
        raise ValueError("Command must be a non-empty string")

    if not isinstance(retries, int) or retries < 1:
        logger.warning(
            f"Invalid retries value {retries}, using default: {DEFAULT_SOCKET_RETRIES}"
        )
        retries = DEFAULT_SOCKET_RETRIES

    if retries > MAX_RETRIES_LIMIT:  # Reasonable upper limit
        logger.warning(
            f"Retries too high ({retries}), limiting to: {MAX_RETRIES_LIMIT}"
        )
        retries = MAX_RETRIES_LIMIT

    for attempt in range(retries):
        try:
            # Check if socat is available first
            pod.exec(["which", "socat"])

            # Use echo to pipe command to socat (properly escaped for security)
            escaped_command = shlex.quote(command)
            cmd = f"echo {escaped_command} | socat - UNIX-CONNECT:/run/haproxy-template-ic/management.sock"
            result = pod.exec(["sh", "-c", cmd])

            # Parse the response
            response_text = result.stdout.decode("utf-8").strip()
            if not response_text:
                raise ValueError("Empty response from management socket")
            return json.loads(response_text)
        except Exception as e:
            if attempt < retries - 1:
                time.sleep(DEFAULT_SOCKET_RETRY_DELAY)  # Wait before retry
                continue
            pytest.fail(
                f"Failed to communicate with management socket after {retries} attempts: {e}"
            )
    return None


def get_pod_logs(
    pod: Any,
    container_names: Optional[List[str]] = None,
    tail_lines: Optional[int] = DEFAULT_POD_LOG_TAIL_LINES,
) -> Dict[str, str]:
    """Get logs from a pod, optionally from specific containers.

    Args:
        pod: The Kubernetes pod object to get logs from
        container_names: List of container names to get logs from. If None, gets logs from all containers.
        tail_lines: Number of lines to tail from the end of logs (default: 100, 0 for all logs)

    Returns:
        dict[str, str]: Dictionary mapping container names to their log content

    Environment Variables:
        PYTEST_POD_LOG_TAIL_LINES: Override default tail_lines (default: 100)
        PYTEST_MAX_LOG_LINES_PER_CONTAINER: Hard limit per container (default: 1000)

    Examples:
        >>> # Get logs from all containers with default settings
        >>> logs = get_pod_logs(pod)
        >>> for container, content in logs.items():
        ...     print(f"Container {container}: {len(content.splitlines())} lines")

        >>> # Get logs from specific containers with custom tail
        >>> logs = get_pod_logs(pod, ["haproxy", "dataplane"], tail_lines=50)
        >>> haproxy_logs = logs.get("haproxy", "No logs found")

        >>> # Get all logs (no tail limit)
        >>> all_logs = get_pod_logs(pod, tail_lines=0)

    Error Handling:
        Returns error messages in the dictionary for containers that fail:
        >>> logs = get_pod_logs(None)  # Invalid pod example
        >>> if "error" in logs:
        ...     print(f"Failed to get logs: {logs['error']}")

    Performance Notes:
        - Respects PYTEST_MAX_LOG_LINES_PER_CONTAINER to prevent memory issues
        - Automatically truncates logs if they exceed the limit
        - Use tail_lines=0 cautiously with large log volumes
    """
    # Input validation
    if pod is None:
        return {"error": "Pod object is None"}

    if not hasattr(pod, "spec") or not hasattr(pod, "logs"):
        return {"error": "Invalid pod object - missing spec or logs method"}

    # Validate tail_lines parameter
    if tail_lines is None or not isinstance(tail_lines, int):
        tail_lines = DEFAULT_POD_LOG_TAIL_LINES
    elif tail_lines < 0:
        tail_lines = 0  # 0 means all logs
    elif tail_lines > MAX_TAIL_LINES_LIMIT:  # Reasonable upper limit
        tail_lines = MAX_TAIL_LINES_LIMIT

    # Validate container_names parameter
    if container_names is not None and not isinstance(container_names, list):
        return {"error": "container_names must be a list or None"}  # type: ignore[unreachable]
    if container_names is not None and not all(
        isinstance(name, str) and name.strip() for name in container_names
    ):
        return {"error": "All container names must be non-empty strings"}

    # Get max log lines from cached environment variable or use default
    max_tail_lines = _ENV_CACHE.get("pod_log_tail_lines", tail_lines)
    actual_tail_lines = (
        min(max_tail_lines, tail_lines) if tail_lines > 0 else max_tail_lines
    )

    if container_names is None:
        try:
            # Get all container names from the pod
            if hasattr(pod.spec, "__getitem__"):
                containers = pod.spec["containers"]
            else:
                containers = (
                    pod.spec.containers if hasattr(pod.spec, "containers") else []
                )

            if isinstance(containers, list):
                container_names = []
                for c in containers:
                    if isinstance(c, dict):
                        name = c.get("name")
                    else:
                        name = getattr(c, "name", None)
                    if name is not None:
                        container_names.append(str(name))
            else:
                container_names = []

        except (AttributeError, KeyError, TypeError) as e:
            return {"error": f"Could not extract container names from pod: {e}"}

    logs = {}
    for container_name in container_names:
        try:
            # Get logs from the specific container
            log_lines = []
            log_count = 0
            max_logs = _ENV_CACHE.get("max_log_lines_per_container", 1000)

            for log_line in pod.logs(
                container=container_name,
                tail_lines=actual_tail_lines if actual_tail_lines > 0 else None,
            ):
                if log_count >= max_logs:
                    log_lines.append(f"... [truncated after {max_logs} lines] ...")
                    break
                log_lines.append(str(log_line).strip())
                log_count += 1

            logs[container_name] = "\n".join(log_lines)
        except (OSError, AttributeError, ValueError) as e:
            # Sanitize error message to avoid exposing sensitive details
            sanitized_error = str(e)[
                :MAX_ERROR_MESSAGE_LENGTH
            ]  # Limit error message length
            if (
                "password" in sanitized_error.lower()
                or "token" in sanitized_error.lower()
            ):
                sanitized_error = "Authentication or permission error"
            logs[container_name] = (
                f"Error retrieving logs from container '{container_name}': {sanitized_error}"
            )

    return logs


def print_pod_logs_on_failure(pod: Any, test_name: str) -> None:
    """Print formatted pod logs for debugging test failures.

    This function provides comprehensive log output for failed tests, including
    automatic container discovery, formatted output, and optional secret redaction.

    Args:
        pod: The Kubernetes pod object to get logs from
        test_name: Name of the failed test for context

    Environment Variables:
        PYTEST_POD_LOG_TAIL_LINES: Maximum lines to retrieve per container (default: 200)
        PYTEST_MAX_LOG_LINES_PER_CONTAINER: Hard limit on log lines (default: 1000)
        PYTEST_DISABLE_POD_LOG_PRINTING: Set to 'true' to disable log printing
        PYTEST_POD_LOG_REDACT_SECRETS: Set to 'true' to enable basic secret redaction

    Examples:
        >>> # Basic usage in pytest teardown
        >>> def pytest_runtest_teardown(item, nextitem):
        ...     if item.rep_call.failed:
        ...         print_pod_logs_on_failure(pod, item.name)

        >>> # Manual debugging with custom settings
        >>> import os
        >>> os.environ['PYTEST_POD_LOG_TAIL_LINES'] = '500'
        >>> os.environ['PYTEST_POD_LOG_REDACT_SECRETS'] = 'true'
        >>> print_pod_logs_on_failure(pod, "debug_session")

    Output Format:
        ================================================================================
        🔍 POD LOGS FOR FAILED TEST: test_name
        ================================================================================

        📋 Container: container_name
        ------------------------------------------------------------
        [container log content]
        ------------------------------------------------------------

    Troubleshooting:
        - If no logs appear: Check pod status and container readiness
        - If logs are truncated: Increase PYTEST_POD_LOG_TAIL_LINES
        - If memory issues: Decrease PYTEST_MAX_LOG_LINES_PER_CONTAINER
        - To disable in CI: Set PYTEST_DISABLE_POD_LOG_PRINTING=true
    """
    # Check if log printing is disabled
    if _ENV_CACHE.get("disable_pod_log_printing", False):
        return

    # Input validation
    if pod is None:
        print("❌ Cannot print logs: Pod object is None")
        return

    if not test_name or not isinstance(test_name, str):
        test_name = "unknown_test"
    elif len(test_name) > MAX_TEST_NAME_LENGTH:  # Prevent extremely long test names
        test_name = test_name[:MAX_TEST_NAME_LENGTH] + "..."

    logger.info(f"Printing pod logs for failed test: {test_name}")

    print(f"\n{'=' * 80}")
    print(f"🔍 POD LOGS FOR FAILED TEST: {test_name}")
    print(f"{'=' * 80}")

    try:
        # Get configurable tail lines from cached environment
        tail_lines = _ENV_CACHE.get("pod_log_tail_lines", 200)
        container_logs = get_pod_logs(pod, tail_lines=tail_lines)

        # Check for errors in log retrieval
        if len(container_logs) == 1 and "error" in container_logs:
            print(f"❌ {container_logs['error']}")
            return

        redact_secrets = _ENV_CACHE.get("redact_secrets", False)

        for container_name, logs in container_logs.items():
            print(f"\n📋 Container: {container_name}")
            print(f"{'-' * 60}")

            if logs.strip():
                processed_logs = (
                    _redact_sensitive_info(logs) if redact_secrets else logs
                )
                print(processed_logs)
            else:
                print("(No logs available)")

            print(f"{'-' * 60}")

    except (OSError, AttributeError, ValueError) as e:
        logger.error(f"Error retrieving pod logs for test {test_name}: {e}")
        print(f"❌ Error retrieving pod logs: {e}")

    print(f"{'=' * 80}")
    print("🔍 END POD LOGS")
    print(f"{'=' * 80}\n")


def _redact_sensitive_info(log_content: Any) -> str:
    """Basic redaction of potentially sensitive information in logs.

    This function applies regex patterns to identify and redact common sensitive
    information patterns in log output, helping prevent accidental exposure of
    credentials or tokens during debugging.

    Args:
        log_content: Raw log content to process

    Returns:
        Log content with sensitive patterns replaced by '***REDACTED***'

    Redacted Patterns:
        - password=value or password: value
        - token=value or token: value
        - secret=value or secret: value
        - key=value or key: value
        - Authorization: Bearer token

    Examples:
        >>> content = "password=secret123 token: abc123"
        >>> redacted = _redact_sensitive_info(content)
        >>> print(redacted)
        password=***REDACTED*** token: ***REDACTED***

        >>> auth_log = "Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJSUzI1NiJ9"
        >>> redacted = _redact_sensitive_info(auth_log)
        >>> print(redacted)
        Authorization: Bearer ***REDACTED***

    Note:
        This is basic pattern matching and may not catch all sensitive data.
        Consider more sophisticated redaction for production log analysis.
        Patterns are case-insensitive to catch variations in log formatting.
    """
    # Input validation
    if not isinstance(log_content, str):
        return str(log_content) if log_content is not None else ""

    if len(log_content) > MAX_LOG_CONTENT_SIZE:  # 1MB limit for safety
        log_content = (
            log_content[:MAX_LOG_CONTENT_SIZE]
            + "\n... [truncated for redaction processing] ..."
        )

    # Use pre-compiled patterns for better performance
    redacted_content = log_content
    for pattern, replacement in zip(_REDACTION_PATTERNS, _REPLACEMENT_PATTERNS):
        redacted_content = pattern.sub(replacement, redacted_content)

    return redacted_content
