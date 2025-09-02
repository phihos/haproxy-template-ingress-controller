"""
Type aliases and validation patterns for HAProxy Template IC.

This module contains all type aliases using Pydantic's StringConstraints
for validation, providing better maintainability and standardized error messages.
"""

from typing import Annotated
from pydantic.types import StringConstraints

# Type Aliases for Common Validation Patterns

# Non-empty string validation
NonEmptyStr = Annotated[str, StringConstraints(min_length=1)]

# Non-empty strict string for template validation (prevents Template objects)
NonEmptyStrictStr = Annotated[str, StringConstraints(min_length=1, strict=True)]

# Absolute path validation (deprecated - use storage_*_dir fields instead)
AbsolutePath = Annotated[str, StringConstraints(pattern="^/")]

# Filename validation (secure against path traversal and filesystem issues)
Filename = Annotated[
    str,
    StringConstraints(
        min_length=1,
        max_length=255,  # Common filesystem limit
        # Whitelist approach: Only allow safe characters
        # - Must start with alphanumeric character
        # - Can contain alphanumeric, dots, hyphens, underscores
        # - No encoded sequences, path separators, or special characters
        pattern=r"^[a-zA-Z0-9][a-zA-Z0-9._-]*$",
    ),
]

# Kubernetes kind validation (PascalCase starting with uppercase)
KubernetesKind = Annotated[
    str, StringConstraints(min_length=1, pattern="^[A-Z][a-zA-Z0-9]*$")
]

# API version validation (supports both 'v1' and 'group/version' formats)
ApiVersion = Annotated[
    str,
    StringConstraints(
        min_length=1, pattern="^([a-z0-9.-]+/)?v[0-9]+([a-z][a-z0-9]*)?$"
    ),
]

# Template snippet name (no spaces or newlines)
SnippetName = Annotated[str, StringConstraints(min_length=1, pattern="^[^\\s\\n]+$")]

__all__ = [
    "NonEmptyStr",
    "NonEmptyStrictStr",
    "AbsolutePath",
    "Filename",
    "KubernetesKind",
    "ApiVersion",
    "SnippetName",
]
