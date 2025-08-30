"""
Test utilities for HAProxy Template IC end-to-end tests.

This package provides utilities for:
- Telepresence connection management
- Local operator execution
- Test helpers and assertions
- Management socket communication
"""

# Import main utilities from consolidated modules
from .helpers import (
    # Operator helpers
    wait_for_operator_ready,
    wait_for_watch_streams_ready,
    assert_log_line,
    assert_config_change,
    count_log_occurrences,
    assert_no_reload_loop,
    assert_operator_health,
    # Socket communication
    send_socket_command,
    # Assertions
    verify_config_contains,
    verify_response_has_structure,
    assert_config_structure,
    assert_dump_all_response_structure,
)

from .local_operator import LocalOperatorRunner
from .telepresence import TelepresenceConnection

__all__ = [
    # Classes
    "LocalOperatorRunner",
    "TelepresenceConnection",
    # Operator helpers
    "wait_for_operator_ready",
    "wait_for_watch_streams_ready",
    "assert_log_line",
    "assert_config_change",
    "count_log_occurrences",
    "assert_no_reload_loop",
    "assert_operator_health",
    # Socket communication
    "send_socket_command",
    # Assertions
    "verify_config_contains",
    "verify_response_has_structure",
    "assert_config_structure",
    "assert_dump_all_response_structure",
]
