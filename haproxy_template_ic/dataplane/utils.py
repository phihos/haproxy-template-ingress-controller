"""
Utility functions for HAProxy Dataplane API operations.

Contains helper functions for URL normalization, error parsing,
configuration context extraction, and other common operations.
"""

import asyncio
import functools
import logging
import re
from typing import Any, List, Optional
from urllib.parse import urlparse, urlunparse

import httpx
from haproxy_dataplane_v3 import errors
from haproxy_dataplane_v3.api.configuration import get_configuration_version

from .errors import DataplaneAPIError, ValidationError

__all__ = [
    "normalize_dataplane_url",
    "parse_haproxy_error_line", 
    "extract_config_context",
    "parse_validation_error_details",
    "handle_dataplane_errors",
    "_get_configuration_version",
    "_fetch_with_metrics",
    "MAX_CONFIG_COMPARISON_CHANGES",
]

logger = logging.getLogger(__name__)

# Constants for configuration comparison performance
MAX_CONFIG_COMPARISON_CHANGES = 10  # Stop comparison after finding this many changes


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
        return urlunparse(
            (
                parsed.scheme,
                parsed.netloc,
                path,
                parsed.params,
                parsed.query,
                parsed.fragment,
            )
        )
    except ValueError:
        # If reconstruction fails, use simple string concatenation
        if not base_url.endswith("/v3"):
            return f"{base_url.rstrip('/')}/v3"
        return base_url


def parse_haproxy_error_line(error_message: str) -> Optional[int]:
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
    error_response: str, config_content: Optional[str] = None
) -> tuple[Optional[str], Optional[int], Optional[str]]:
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


def _to_dict_safe(obj: Any) -> Any:
    """Safely convert an object to dictionary, handling serialization errors gracefully."""
    try:
        return obj.to_dict() if hasattr(obj, "to_dict") else obj
    except Exception as e:
        logger.debug(f"Failed to serialize object: {e}")
        return {
            "__serialization_error__": str(e),
            "__type__": type(obj).__name__,
        }


def _check_early_exit_condition(changes: List[str], max_changes: int) -> bool:
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


async def _get_configuration_version(client: Any) -> Optional[int]:
    """Get the current HAProxy configuration version.

    Args:
        client: The dataplane API client

    Returns:
        Configuration version number or None if failed to fetch
    """
    try:
        return await get_configuration_version.asyncio(client=client)
    except Exception:
        # Silently return None for version fetch failures
        return None


async def _fetch_with_metrics(
    operation_name: str,
    fetch_func,
    client: Any,
    metrics,
    default_value: Optional[Any] = None,
) -> Any:
    """Fetch configuration data with metrics timing.

    Args:
        operation_name: Name for metrics tracking
        fetch_func: Async function to call for fetching data
        client: Dataplane API client
        metrics: Metrics collector instance
        default_value: Value to return if fetch_func returns None/empty

    Returns:
        Result from fetch_func or default_value if result is falsy
    """
    with metrics.time_dataplane_api_operation(operation_name):
        return await fetch_func(client=client) or default_value


def handle_dataplane_errors(operation_name: Optional[str] = None):
    """Decorator to standardize error handling for dataplane operations.

    Automatically wraps exceptions in DataplaneAPIError with consistent context,
    records metrics and tracing events, and preserves error chaining.

    Args:
        operation_name: Name of the operation for error context. If None, uses function name.
    """

    def decorator(func):
        from haproxy_template_ic.metrics import get_metrics_collector
        from haproxy_template_ic.tracing import (
            record_span_event,
            set_span_error,
        )

        @functools.wraps(func)
        async def async_wrapper(self, *args, **kwargs):
            op_name = operation_name or func.__name__
            metrics = get_metrics_collector()

            try:
                return await func(self, *args, **kwargs)
            except ValidationError:
                # Re-raise ValidationError without wrapping
                raise
            except DataplaneAPIError:
                # Re-raise DataplaneAPIError without wrapping
                raise
            except errors.UnexpectedStatus as e:
                metrics.record_dataplane_api_request(op_name, "error")
                record_span_event(f"{op_name}_failed", {"error": str(e)})
                set_span_error(e, f"Dataplane API error in {op_name}")
                raise DataplaneAPIError(
                    f"API error in {op_name}: {e}",
                    endpoint=getattr(self, "base_url", "unknown"),
                    operation=op_name,
                    original_error=e,
                ) from e
            except (ConnectionError, TimeoutError, OSError, httpx.RequestError) as e:
                metrics.record_dataplane_api_request(op_name, "error")
                record_span_event(f"{op_name}_failed", {"error": str(e)})
                set_span_error(e, f"Network error in {op_name}")
                raise DataplaneAPIError(
                    f"Network error in {op_name}: {e}",
                    endpoint=getattr(self, "base_url", "unknown"),
                    operation=op_name,
                    original_error=e,
                ) from e
            except Exception as e:
                metrics.record_dataplane_api_request(op_name, "error")
                record_span_event(f"{op_name}_failed", {"error": str(e)})
                set_span_error(e, f"Unexpected error in {op_name}")
                raise DataplaneAPIError(
                    f"Unexpected error in {op_name}: {e}",
                    endpoint=getattr(self, "base_url", "unknown"),
                    operation=op_name,
                    original_error=e,
                ) from e

        @functools.wraps(func)
        def sync_wrapper(self, *args, **kwargs):
            op_name = operation_name or func.__name__
            metrics = get_metrics_collector()

            try:
                return func(self, *args, **kwargs)
            except ValidationError:
                # Re-raise ValidationError without wrapping
                raise
            except DataplaneAPIError:
                # Re-raise DataplaneAPIError without wrapping
                raise
            except errors.UnexpectedStatus as e:
                metrics.record_dataplane_api_request(op_name, "error")
                record_span_event(f"{op_name}_failed", {"error": str(e)})
                set_span_error(e, f"Dataplane API error in {op_name}")
                raise DataplaneAPIError(
                    f"API error in {op_name}: {e}",
                    endpoint=getattr(self, "base_url", "unknown"),
                    operation=op_name,
                    original_error=e,
                ) from e
            except (ConnectionError, TimeoutError, OSError, httpx.RequestError) as e:
                metrics.record_dataplane_api_request(op_name, "error")
                record_span_event(f"{op_name}_failed", {"error": str(e)})
                set_span_error(e, f"Network error in {op_name}")
                raise DataplaneAPIError(
                    f"Network error in {op_name}: {e}",
                    endpoint=getattr(self, "base_url", "unknown"),
                    operation=op_name,
                    original_error=e,
                ) from e
            except Exception as e:
                metrics.record_dataplane_api_request(op_name, "error")
                record_span_event(f"{op_name}_failed", {"error": str(e)})
                set_span_error(e, f"Unexpected error in {op_name}")
                raise DataplaneAPIError(
                    f"Unexpected error in {op_name}: {e}",
                    endpoint=getattr(self, "base_url", "unknown"),
                    operation=op_name,
                    original_error=e,
                ) from e

        # Return the appropriate wrapper based on whether the function is async
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper

    return decorator