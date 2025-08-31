# Core utilities package
# This package contains general-purpose utilities not specific to Kubernetes:
# structured logging, common helpers, etc.

from .logging import (
    setup_structured_logging,
    autolog,
    observe,
    add_emoji_prefix,
    _extract_context_from_parameters,
    _get_function_signature,
)

__all__ = [
    # Structured logging
    "setup_structured_logging",
    "autolog",
    "observe",
    "add_emoji_prefix",
    "_extract_context_from_parameters",  # Private function for tests
    "_get_function_signature",  # Private function for tests
]