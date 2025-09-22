"""
Test utilities for HAProxy Template IC end-to-end tests.

This package provides utilities for:
- Telepresence connection management
- Local operator execution
- Test helpers and assertions
"""

# Import main utilities from consolidated modules
from .helpers import (
    assert_config_change,
    assert_config_structure,
    assert_log_line,
    assert_no_handler_failures,
    assert_no_reload_loop,
    assert_operator_health,
    count_log_occurrences,
    # Assertions
    verify_config_contains,
    # Operator helpers
    wait_for_operator_ready,
    wait_for_watch_streams_ready,
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
    "assert_no_handler_failures",
    "assert_no_reload_loop",
    "assert_operator_health",
    # Assertions
    "verify_config_contains",
    "assert_config_structure",
]
