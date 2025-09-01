"""
Exception classes for HAProxy Dataplane API operations.

Defines custom exceptions for handling dataplane API errors,
validation failures, and deployment issues.
"""

from typing import Optional

__all__ = [
    "DataplaneAPIError",
    "ValidationError",
]


class DataplaneAPIError(Exception):
    """Base exception for Dataplane API errors.

    Attributes:
        endpoint: The dataplane endpoint URL where the error occurred
        operation: The operation that failed (e.g., 'validate', 'deploy', 'get_version')
        original_error: The original exception that caused this error, if any
    """

    def __init__(
        self,
        message: str,
        endpoint: Optional[str] = None,
        operation: Optional[str] = None,
        original_error: Optional[Exception] = None,
    ):
        super().__init__(message)
        self.endpoint = endpoint
        self.operation = operation
        self.original_error = original_error

    def __str__(self) -> str:
        """Return detailed error message with context."""
        base_message = super().__str__()
        context_parts = []

        if self.operation:
            context_parts.append(f"operation={self.operation}")
        if self.endpoint:
            context_parts.append(f"endpoint={self.endpoint}")

        if context_parts:
            return f"{base_message} [{', '.join(context_parts)}]"
        return base_message


class ValidationError(DataplaneAPIError):
    """Raised when HAProxy configuration validation fails.

    Attributes:
        config_size: Size of the configuration that failed validation
        validation_details: Detailed error message from HAProxy validation
        error_line: Line number where the error occurred (if extracted)
        config_content: Full configuration content that failed validation
        error_context: Configuration lines around the error (if available)
    """

    def __init__(
        self,
        message: str,
        endpoint: Optional[str] = None,
        config_size: Optional[int] = None,
        validation_details: Optional[str] = None,
        error_line: Optional[int] = None,
        config_content: Optional[str] = None,
        error_context: Optional[str] = None,
        original_error: Optional[Exception] = None,
    ):
        super().__init__(
            message,
            endpoint=endpoint,
            operation="validate",
            original_error=original_error,
        )
        self.config_size = config_size
        self.validation_details = validation_details
        self.error_line = error_line
        self.config_content = config_content
        self.error_context = error_context

    def __str__(self) -> str:
        """Return detailed validation error message with context."""
        base_message = super().__str__()
        detail_parts = []

        if self.config_size:
            detail_parts.append(f"config_size={self.config_size}")
        if self.validation_details:
            detail_parts.append(f"details={self.validation_details}")

        if detail_parts:
            result = f"{base_message} [{', '.join(detail_parts)}]"
        else:
            result = base_message

        # Add error context if available
        if self.error_context:
            result += f"\n\nConfiguration context around error:\n{self.error_context}"

        return result
