"""
Structured logging functionality (backward compatibility module).

This module re-exports all functionality from the haproxy_template_ic.core.logging
module to maintain backward compatibility with existing code.

The actual implementation has been moved to the core package for better organization.
"""

# Re-export everything from the core.logging module
from haproxy_template_ic.core.logging import (
    _extract_context_from_parameters,
    _get_function_signature,
    add_emoji_prefix,
    autolog,
    observe,
    setup_structured_logging,
)

__all__ = [
    "setup_structured_logging",
    "autolog",
    "observe",
    "add_emoji_prefix",
    "_extract_context_from_parameters",  # Private function for tests
    "_get_function_signature",  # Private function for tests
]
