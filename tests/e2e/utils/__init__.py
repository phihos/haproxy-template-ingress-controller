"""
E2E test utilities for HAProxy Template IC.

This package provides shared utilities for end-to-end testing including
assertion helpers, Kubernetes interaction utilities, and operator-specific
test helpers.
"""

# Import commonly used utilities for convenience
from .assertions import (
    verify_config_contains,
    verify_response_has_structure,
    assert_config_structure,
    assert_dump_all_response_structure,
)

from .k8s_helpers import (
    send_socket_command,
)

from .operator_helpers import (
    assert_log_line,
    wait_for_operator_ready,
    wait_for_watch_streams_ready,
    assert_config_change,
    assert_operator_health,
    count_log_occurrences,
    assert_no_reload_loop,
)

__all__ = [
    # Assertions
    "verify_config_contains",
    "verify_response_has_structure",
    "assert_config_structure",
    "assert_dump_all_response_structure",
    # K8s helpers
    "send_socket_command",
    # Operator helpers
    "assert_log_line",
    "wait_for_operator_ready",
    "wait_for_watch_streams_ready",
    "assert_config_change",
    "assert_operator_health",
    "count_log_occurrences",
    "assert_no_reload_loop",
]
