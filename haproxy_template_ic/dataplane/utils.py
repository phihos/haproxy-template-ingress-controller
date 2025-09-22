"""
Utility functions for HAProxy Dataplane API operations.

Contains helper functions for URL normalization, error parsing,
configuration context extraction, and other common operations.
"""

import asyncio
import functools
import logging
import re
import traceback
from typing import Any, Callable, TYPE_CHECKING
from urllib.parse import urlparse, urlunparse

import httpx
from haproxy_dataplane_v3 import errors

from haproxy_template_ic.metrics import get_metrics_collector
from haproxy_template_ic.tracing import (
    record_span_event,
    set_span_error,
)

if TYPE_CHECKING:
    from .types import DataplaneAPIError


__all__ = [
    "normalize_dataplane_url",
    "extract_hostname_from_url",
    "parse_haproxy_error_line",
    "extract_config_context",
    "parse_validation_error_details",
    "handle_dataplane_errors",
    "natural_sort_key",
    "extract_exception_origin",
]

logger = logging.getLogger(__name__)


def extract_exception_origin(exc: Exception) -> str:
    """Extract detailed origin information from an exception.

    Returns a formatted string with filename, line number, and function name
    where the exception occurred, along with the full traceback.

    Args:
        exc: The exception to analyze

    Returns:
        Formatted string with exception origin details
    """
    try:
        tb = exc.__traceback__
        if tb is None:
            return "Origin: No traceback available"

        # Extract the last frame (where the actual error occurred)
        tb_lines = traceback.extract_tb(tb)
        if not tb_lines:
            return "Origin: No traceback frames available"

        # Get the innermost frame (actual error location)
        last_frame = tb_lines[-1]
        origin_info = (
            f"Origin: {last_frame.filename}:{last_frame.lineno} in {last_frame.name}()"
        )

        # Get full traceback for debugging
        full_traceback = "".join(traceback.format_tb(tb)).strip()

        return f"{origin_info}\nCall Stack:\n{full_traceback}"
    except Exception as extract_error:
        return f"Origin: Error extracting traceback: {extract_error}"


def natural_sort_key(name: str) -> tuple:
    """Extract numeric parts for natural sorting of names like SRV_1, SRV_10.

    This function splits a string into alternating text and numeric parts,
    converting numeric parts to integers for proper numerical sorting.

    Examples:
        SRV_1 -> ('SRV_', 1, '')
        SRV_10 -> ('SRV_', 10, '')
        SRV_2 -> ('SRV_', 2, '')

    This ensures SRV_1, SRV_2, ..., SRV_9, SRV_10 instead of SRV_1, SRV_10, SRV_2, ...
    """
    parts = re.split(r"(\d+)", name)
    return tuple(int(part) if part.isdigit() else part for part in parts)


def normalize_dataplane_url(base_url: str) -> str:
    """Normalize a Dataplane API URL to ensure it ends with /v3.

    This utility function handles various URL formats and ensures consistent
    API endpoint formatting for the HAProxy Dataplane API v3. It properly
    preserves query parameters and fragments while adding /v3 to the path.

    Args:
        base_url: The base URL in any of these formats:
            - "http://localhost:5555" -> "http://localhost:5555/v3"
            - "http://localhost:5555/" -> "http://localhost:5555/v3"
            - "http://localhost:5555/v3" -> "http://localhost:5555/v3" (unchanged)
            - "http://localhost:5555?timeout=30" -> "http://localhost:5555/v3?timeout=30"
            - "https://haproxy.example.com:5555/api" -> "https://haproxy.example.com:5555/api/v3"

    Returns:
        Normalized URL ending with /v3, preserving query parameters and fragments

    Example:
        >>> normalize_dataplane_url("http://localhost:5555")
        'http://localhost:5555/v3'
        >>> normalize_dataplane_url("http://localhost:5555?timeout=30")
        'http://localhost:5555/v3?timeout=30'
        >>> normalize_dataplane_url("https://api.example.com/haproxy/")
        'https://api.example.com/haproxy/v3'
    """
    try:
        parsed = urlparse(base_url)
    except ValueError:
        # If URL parsing fails, append /v3 to the raw URL as fallback
        if not base_url.endswith("/v3"):
            return f"{base_url.rstrip('/')}/v3"
        return base_url

    # Handle path normalization
    path = parsed.path.rstrip("/")
    if not path.endswith("/v3"):
        path = f"{path}/v3"

    # Reconstruct the URL with normalized path
    try:
        result = urlunparse(
            (
                parsed.scheme,
                parsed.netloc,
                path,
                parsed.params,
                parsed.query,
                parsed.fragment,
            )
        )
        return str(result) if isinstance(result, bytes) else result
    except ValueError:
        # If reconstruction fails, use simple string concatenation
        if not base_url.endswith("/v3"):
            return f"{base_url.rstrip('/')}/v3"
        return base_url


def extract_hostname_from_url(url: str) -> str | None:
    """Extract hostname from a URL.

    Args:
        url: The URL to parse

    Returns:
        Hostname/IP address from the URL, or None if parsing fails

    Example:
        >>> extract_hostname_from_url("http://192.168.1.10:5555/v3")
        '192.168.1.10'
    """
    try:
        parsed = urlparse(url)
        return parsed.hostname
    except ValueError:
        return None


def parse_haproxy_error_line(error_message: str) -> int | None:
    """Extract line number from HAProxy validation error messages.

    HAProxy errors often contain line numbers in formats like:
    - "config parsing [/tmp/file:54]"
    - "line 42:"
    - "[line 123]"

    Args:
        error_message: The error message from HAProxy validation

    Returns:
        Line number if found, None otherwise
    """
    # Pattern to match various HAProxy error formats with line numbers
    patterns = [
        r"config parsing \[.*?:(\d+)\]",  # [/tmp/file:54]
        r"line (\d+):",  # line 42:
        r"\[line (\d+)\]",  # [line 123]
        r"at line (\d+)",  # at line 123
        r":(\d+)\]",  # generic :number]
    ]

    for pattern in patterns:
        match = re.search(pattern, error_message, re.IGNORECASE)
        if match:
            try:
                return int(match.group(1))
            except (ValueError, IndexError):
                continue

    return None


def extract_config_context(
    config_content: str, error_line: int, context_lines: int = 3
) -> str:
    """Extract configuration lines around an error for better debugging.

    Args:
        config_content: Full HAProxy configuration content
        error_line: Line number where error occurred (1-based)
        context_lines: Number of lines to show before and after error line

    Returns:
        Formatted string showing the error line with context
    """
    if not config_content:
        return "No configuration content available"

    lines = config_content.splitlines()
    total_lines = len(lines)

    # Convert to 0-based indexing
    error_idx = error_line - 1

    if error_idx < 0 or error_idx >= total_lines:
        return (
            f"Error line {error_line} is out of range (config has {total_lines} lines)"
        )

    # Calculate context range
    start_idx = max(0, error_idx - context_lines)
    end_idx = min(total_lines - 1, error_idx + context_lines)

    # Format the context with line numbers
    context_parts = []
    for i in range(start_idx, end_idx + 1):
        line_num = i + 1
        line_content = lines[i].rstrip()  # Remove trailing whitespace

        # Mark the error line with >
        if i == error_idx:
            context_parts.append(f"> {line_num:3}: {line_content}")
        else:
            context_parts.append(f"  {line_num:3}: {line_content}")

    return "\n".join(context_parts)


def parse_validation_error_details(
    error_response: str, config_content: str | None = None
) -> tuple[str | None, int | None, str | None]:
    """Parse HAProxy validation error response to extract structured details.

    Args:
        error_response: Raw error response from HAProxy validation
        config_content: Optional configuration content for context extraction

    Returns:
        Tuple of (validation_details, error_line, error_context)
    """
    if not error_response:
        return None, None, None

    # Extract error line number
    error_line = parse_haproxy_error_line(error_response)

    # Extract error context if we have line number and config content
    error_context = None
    if error_line and config_content:
        error_context = extract_config_context(config_content, error_line)

    # Clean up validation details (remove redundant information)
    validation_details = error_response.strip()

    return validation_details, error_line, error_context


def _to_dict_safe(obj: Any) -> dict[str, Any] | Any:
    """Safely convert an object to dictionary, handling serialization errors gracefully."""
    try:
        return obj.to_dict() if hasattr(obj, "to_dict") else obj
    except Exception as e:
        logger.debug(f"Failed to serialize object: {e}")
        return {
            "__serialization_error__": str(e),
            "__type__": type(obj).__name__,
        }


def _check_early_exit_condition(changes: list[str], max_changes: int) -> bool:
    """Check if early exit condition is met for comparison operations.

    Args:
        changes: List of changes detected so far
        max_changes: Maximum number of changes before early exit

    Returns:
        True if early exit should be triggered
    """
    if len(changes) >= max_changes:
        changes.append(f"... and more (stopped after {max_changes} changes)")
        return True
    return False


def _log_fetch_error(resource_type: str, identifier: str, error: Exception) -> None:
    """Log a debug message for resource fetch failures.

    Args:
        resource_type: Type of resource being fetched (e.g., "map", "certificate")
        identifier: Resource identifier (name, ID, etc.)
        error: The exception that occurred
    """
    logger.debug(f"Could not fetch {resource_type} {identifier}: {error}")


def _handle_exception(
    exception: Exception, op_name: str, metrics, endpoint: str
) -> "DataplaneAPIError":
    """Handle exceptions consistently for dataplane operations.

    Args:
        exception: The caught exception
        op_name: Operation name for context
        metrics: Metrics collector instance
        endpoint: Dataplane endpoint for context

    Returns:
        DataplaneAPIError with proper context and chaining
    """
    from .types import DataplaneAPIError, ValidationError

    if isinstance(exception, (ValidationError, DataplaneAPIError)):
        # Re-raise these without wrapping
        raise exception

    metrics.record_dataplane_api_request(op_name, "error")
    record_span_event(f"{op_name}_failed", {"error": str(exception)})

    if isinstance(exception, errors.UnexpectedStatus):
        set_span_error(exception, f"Dataplane API error in {op_name}")
        raise DataplaneAPIError(
            f"API error in {op_name}: {exception}",
            endpoint=endpoint,
            operation=op_name,
            original_error=exception,
        ) from exception
    elif isinstance(
        exception, (ConnectionError, TimeoutError, OSError, httpx.RequestError)
    ):
        set_span_error(exception, f"Network error in {op_name}")
        raise DataplaneAPIError(
            f"Network error in {op_name}: {exception}",
            endpoint=endpoint,
            operation=op_name,
            original_error=exception,
        ) from exception
    else:
        set_span_error(exception, f"Unexpected error in {op_name}")
        raise DataplaneAPIError(
            f"Unexpected error in {op_name}: {exception}",
            endpoint=endpoint,
            operation=op_name,
            original_error=exception,
        ) from exception


def handle_dataplane_errors(
    operation_name: str | None = None,
) -> Callable[[Callable], Callable]:
    """Decorator to standardize error handling for dataplane operations.

    Automatically wraps exceptions in DataplaneAPIError with consistent context,
    records metrics and tracing events, and preserves error chaining.

    Args:
        operation_name: Name of the operation for error context. If None, uses function name.
    """

    def decorator(func):
        @functools.wraps(func)
        def wrapper(self, *args, **kwargs):
            op_name = operation_name or func.__name__
            metrics = get_metrics_collector()
            endpoint = getattr(self, "endpoint", getattr(self, "base_url", "unknown"))

            try:
                result = func(self, *args, **kwargs)
                # Handle async results properly
                if asyncio.iscoroutine(result):

                    async def async_handler():
                        try:
                            return await result
                        except Exception as e:
                            _handle_exception(e, op_name, metrics, endpoint)

                    return async_handler()
                return result
            except Exception as e:
                _handle_exception(e, op_name, metrics, endpoint)

        return wrapper

    return decorator
