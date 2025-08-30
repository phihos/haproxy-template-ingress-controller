"""
HAProxy Dataplane API integration for template synchronization.

This module provides functionality to:
1. Discover HAProxy pods using pod selectors
2. Validate configurations via validation sidecars
3. Deploy configurations to production HAProxy instances
4. Synchronize state across all HAProxy instances

Uses the complete generated HAProxy Dataplane API v3 client for all operations.
"""

import asyncio
import base64
import io
import logging
import re
import time
from dataclasses import dataclass
from datetime import UTC, datetime
from enum import Enum
from typing import TYPE_CHECKING, Any, Dict, List, Optional, Tuple
from urllib.parse import urlparse, urlunparse

import httpx
import xxhash

if TYPE_CHECKING:
    from haproxy_template_ic.config_models import IndexedResourceCollection
    from haproxy_template_ic.credentials import Credentials

# HAProxy Dataplane API v3 client
from haproxy_dataplane_v3 import AuthenticatedClient, errors

# Main configuration APIs
from haproxy_dataplane_v3.api.acl import (
    create_acl_backend,
    create_acl_frontend,
    delete_acl_backend,
    delete_acl_frontend,
    get_all_acl_backend,
    get_all_acl_frontend,
    replace_acl_backend,
    replace_acl_frontend,
)
from haproxy_dataplane_v3.api.backend import (
    create_backend,
    delete_backend,
    get_backends,
    replace_backend,
)
from haproxy_dataplane_v3.api.backend_switching_rule import (
    create_backend_switching_rule,
    delete_backend_switching_rule,
    get_backend_switching_rules,
    replace_backend_switching_rule,
)

# Core section APIs
from haproxy_dataplane_v3.api.bind import (
    create_bind_frontend,
    delete_bind_frontend,
    get_all_bind_frontend,
    replace_bind_frontend,
)
from haproxy_dataplane_v3.api.cache import (
    get_caches,
)
from haproxy_dataplane_v3.api.configuration import (
    get_configuration_version,
    get_ha_proxy_configuration,
)
from haproxy_dataplane_v3.api.defaults import (
    get_defaults_sections,
    replace_defaults_section,
)
from haproxy_dataplane_v3.api.fcgi_app import (
    get_fcgi_apps,
)
from haproxy_dataplane_v3.api.filter_ import (
    create_filter_backend,
    create_filter_frontend,
    delete_filter_backend,
    delete_filter_frontend,
    get_all_filter_backend,
    get_all_filter_frontend,
    replace_filter_backend,
    replace_filter_frontend,
)
from haproxy_dataplane_v3.api.frontend import (
    create_frontend,
    delete_frontend,
    get_frontends,
    replace_frontend,
)
from haproxy_dataplane_v3.api.global_ import get_global, replace_global
from haproxy_dataplane_v3.api.http_after_response_rule import (
    get_all_http_after_response_rule_backend,
    get_all_http_after_response_rule_frontend,
)
from haproxy_dataplane_v3.api.http_check import (
    get_all_http_check_backend,
)
from haproxy_dataplane_v3.api.http_error_rule import (
    get_all_http_error_rule_backend,
    get_all_http_error_rule_frontend,
)
from haproxy_dataplane_v3.api.http_errors import (
    get_http_errors_sections,
)
from haproxy_dataplane_v3.api.http_request_rule import (
    create_http_request_rule_backend,
    create_http_request_rule_frontend,
    delete_http_request_rule_backend,
    delete_http_request_rule_frontend,
    get_all_http_request_rule_backend,
    get_all_http_request_rule_frontend,
    replace_http_request_rule_backend,
    replace_http_request_rule_frontend,
)
from haproxy_dataplane_v3.api.http_response_rule import (
    create_http_response_rule_backend,
    create_http_response_rule_frontend,
    delete_http_response_rule_backend,
    delete_http_response_rule_frontend,
    get_all_http_response_rule_backend,
    get_all_http_response_rule_frontend,
    replace_http_response_rule_backend,
    replace_http_response_rule_frontend,
)
from haproxy_dataplane_v3.api.information import get_info

# Advanced section APIs
from haproxy_dataplane_v3.api.log_forward import (
    get_log_forwards,
)
from haproxy_dataplane_v3.api.log_target import (
    create_log_target_backend,
    create_log_target_frontend,
    delete_log_target_backend,
    delete_log_target_frontend,
    get_all_log_target_backend,
    get_all_log_target_frontend,
    get_all_log_target_global,
    replace_log_target_backend,
    replace_log_target_frontend,
)
from haproxy_dataplane_v3.api.mailers import (
    get_mailers_sections,
)
from haproxy_dataplane_v3.api.peer import (
    get_peer_sections,
)
from haproxy_dataplane_v3.api.process_manager import (
    get_programs,
)
from haproxy_dataplane_v3.api.quic_initial_rule import (
    get_all_quic_initial_rule_frontend,
)
from haproxy_dataplane_v3.api.resolver import (
    get_resolvers,
)
from haproxy_dataplane_v3.api.ring import (
    get_rings,
)
from haproxy_dataplane_v3.api.server import (
    create_server_backend,
    delete_server_backend,
    get_all_server_backend,
    replace_server_backend,
)
from haproxy_dataplane_v3.api.server_switching_rule import (
    create_server_switching_rule,
    delete_server_switching_rule,
    get_server_switching_rules,
    replace_server_switching_rule,
)
from haproxy_dataplane_v3.api.stick_rule import (
    create_stick_rule,
    delete_stick_rule,
    get_stick_rules,
    replace_stick_rule,
)
from haproxy_dataplane_v3.api.storage import (
    create_storage_general_file,
    create_storage_map_file,
    create_storage_ssl_certificate,
    delete_storage_general_file,
    delete_storage_map,
    delete_storage_ssl_certificate,
    get_all_storage_general_files,
    get_all_storage_map_files,
    get_all_storage_ssl_certificates,
    get_one_storage_general_file,
    get_one_storage_map,
    get_one_storage_ssl_certificate,
    replace_storage_general_file,
    replace_storage_map_file,
    replace_storage_ssl_certificate,
)
from haproxy_dataplane_v3.api.tcp_check import (
    get_all_tcp_check_backend,
)
from haproxy_dataplane_v3.api.tcp_request_rule import (
    create_tcp_request_rule_backend,
    create_tcp_request_rule_frontend,
    delete_tcp_request_rule_backend,
    delete_tcp_request_rule_frontend,
    get_all_tcp_request_rule_backend,
    get_all_tcp_request_rule_frontend,
    replace_tcp_request_rule_backend,
    replace_tcp_request_rule_frontend,
)
from haproxy_dataplane_v3.api.tcp_response_rule import (
    create_tcp_response_rule_backend,
    delete_tcp_response_rule_backend,
    get_all_tcp_response_rule_backend,
    replace_tcp_response_rule_backend,
)
from haproxy_dataplane_v3.api.transactions import (
    commit_transaction,
    delete_transaction,
    start_transaction,
)
from haproxy_dataplane_v3.api.userlist import (
    create_userlist,
    delete_userlist,
    get_userlists,
)
from haproxy_dataplane_v3.models.create_storage_general_file_body import (
    CreateStorageGeneralFileBody,
)
from haproxy_dataplane_v3.models.create_storage_map_file_body import (
    CreateStorageMapFileBody,
)
from haproxy_dataplane_v3.models.create_storage_ssl_certificate_body import (
    CreateStorageSSLCertificateBody,
)
from haproxy_dataplane_v3.models.replace_storage_general_file_body import (
    ReplaceStorageGeneralFileBody,
)
from haproxy_dataplane_v3.types import File
from tenacity import (
    AsyncRetrying,
    retry_if_exception,
    stop_after_attempt,
    wait_exponential_jitter,
)

from haproxy_template_ic.config_models import HAProxyConfigContext
from haproxy_template_ic.constants import (
    DEFAULT_API_TIMEOUT,
    DEFAULT_DATAPLANE_PASSWORD,
    DEFAULT_DATAPLANE_PORT,
    DEFAULT_DATAPLANE_USERNAME,
    INITIAL_RETRY_WAIT_SECONDS,
    MAX_RETRY_WAIT_SECONDS,
)
from haproxy_template_ic.metrics import get_metrics_collector
from haproxy_template_ic.tracing import (
    add_span_attributes,
    record_span_event,
    set_span_error,
    trace_dataplane_operation,
)

logger = logging.getLogger(__name__)


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
        import functools

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


# Constants for configuration comparison performance
MAX_CONFIG_COMPARISON_CHANGES = 10  # Stop comparison after finding this many changes


class ConfigChangeType(Enum):
    """Types of configuration changes that can be applied."""

    CREATE = "create"
    UPDATE = "update"
    DELETE = "delete"


class ConfigSectionType(Enum):
    """Types of configuration sections supported for structured updates."""

    BACKEND = "backend"
    FRONTEND = "frontend"
    DEFAULTS = "defaults"
    GLOBAL = "global"
    USERLIST = "userlist"
    CACHE = "cache"
    MAILERS = "mailers"
    RESOLVER = "resolver"
    PEER = "peer"
    FCGI_APP = "fcgi_app"
    HTTP_ERRORS = "http_errors"
    RING = "ring"
    LOG_FORWARD = "log_forward"
    PROGRAM = "program"


class ConfigElementType(Enum):
    """Types of nested configuration elements within sections."""

    # Backend-specific elements
    SERVER = "server"
    SERVER_SWITCHING_RULE = "server_switching_rule"
    STICK_RULE = "stick_rule"

    # Frontend-specific elements
    BIND = "bind"
    BACKEND_SWITCHING_RULE = "backend_switching_rule"

    # Common elements for frontends, backends, defaults
    ACL = "acl"
    HTTP_REQUEST_RULE = "http_request_rule"
    HTTP_RESPONSE_RULE = "http_response_rule"
    TCP_REQUEST_RULE = "tcp_request_rule"
    TCP_RESPONSE_RULE = "tcp_response_rule"
    FILTER = "filter"
    LOG_TARGET = "log_target"

    # Defaults-specific elements
    ERROR_FILE = "error_file"


@dataclass
class ConfigChange:
    """Represents a specific configuration change to be applied via dataplane API.

    This class encapsulates all information needed to apply a granular configuration
    change using the HAProxy Dataplane API's structured endpoints instead of the
    raw configuration endpoint.

    Attributes:
        change_type: The type of change (CREATE, UPDATE, DELETE)
        section_type: The type of configuration section being changed
        section_name: The name/identifier of the specific section
        new_config: The new configuration object (None for DELETE operations)
        old_config: The old configuration object (None for CREATE operations)
        section_index: For indexed sections like defaults, the section index (optional)
        element_type: For nested elements within sections (optional)
        element_index: For ordered elements like rules, the element index (optional)
        element_id: For named elements within sections (optional)
    """

    change_type: ConfigChangeType
    section_type: ConfigSectionType
    section_name: str
    new_config: Optional[Any] = None
    old_config: Optional[Any] = None
    section_index: Optional[int] = None
    element_type: Optional[ConfigElementType] = None
    element_index: Optional[int] = None
    element_id: Optional[str] = None

    def __str__(self) -> str:
        """Return a human-readable description of the change."""
        base_description = f"{self.section_type.value} {self.section_name}"

        if self.element_type:
            # This is a nested element change
            element_id = (
                self.element_id or f"[{self.element_index}]"
                if self.element_index is not None
                else ""
            )
            element_description = f"{self.element_type.value} {element_id}".strip()
            base_description = f"{base_description}/{element_description}"

        if self.change_type == ConfigChangeType.CREATE:
            return f"create {base_description}"
        elif self.change_type == ConfigChangeType.DELETE:
            return f"remove {base_description}"
        else:  # UPDATE
            return f"modify {base_description}"

    @classmethod
    def create_section_change(
        cls,
        change_type: ConfigChangeType,
        section_type: ConfigSectionType,
        section_name: str,
        new_config: Optional[Any] = None,
        old_config: Optional[Any] = None,
        section_index: Optional[int] = None,
    ) -> "ConfigChange":
        """Factory method for creating section-level configuration changes."""
        return cls(
            change_type=change_type,
            section_type=section_type,
            section_name=section_name,
            new_config=new_config,
            old_config=old_config,
            section_index=section_index,
        )

    @classmethod
    def create_element_change(
        cls,
        change_type: ConfigChangeType,
        section_type: ConfigSectionType,
        section_name: str,
        element_type: ConfigElementType,
        new_config: Optional[Any] = None,
        old_config: Optional[Any] = None,
        element_id: Optional[str] = None,
        element_index: Optional[int] = None,
    ) -> "ConfigChange":
        """Factory method for creating element-level configuration changes."""
        return cls(
            change_type=change_type,
            section_type=section_type,
            section_name=section_name,
            element_type=element_type,
            new_config=new_config,
            old_config=old_config,
            element_id=element_id,
            element_index=element_index,
        )


def compute_content_hash(content: str) -> str:
    """Compute xxHash64 of content for fast change detection.

    Uses xxHash64 for its excellent performance (5GB/s+) and sufficient
    collision resistance for non-cryptographic change detection.

    Args:
        content: The text content to hash

    Returns:
        Hash string in format "xxh64:<hex_hash>"
    """
    return f"xxh64:{xxhash.xxh64(content.encode('utf-8')).hexdigest()}"


def extract_hash_from_description(description: Optional[str]) -> Optional[str]:
    """Extract content hash from description field if present.

    Args:
        description: Description field that may contain a hash

    Returns:
        The hash string if found (e.g., "xxh64:abc123..."), None otherwise
    """
    if not description or not isinstance(description, str):
        return None

    # Check if description starts with a known hash format
    if description.startswith(("xxh64:", "sha256:", "md5:")):
        # Return just the hash part (before any additional description)
        return description.split(" ", 1)[0]

    return None


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
    error_message: str, config_content: str
) -> Tuple[Optional[int], Optional[str]]:
    """Parse HAProxy validation error to extract line number and context.

    Args:
        error_message: The validation error message from dataplane API
        config_content: Full configuration content that was validated

    Returns:
        Tuple of (error_line_number, error_context) where either can be None
    """
    error_line = parse_haproxy_error_line(error_message)
    error_context = None

    if error_line and config_content:
        try:
            error_context = extract_config_context(config_content, error_line)
        except Exception as e:
            logger.debug(f"Failed to extract error context for line {error_line}: {e}")
            error_context = f"Error extracting context for line {error_line}: {e}"

    return error_line, error_context


# Classes removed for simplification - using simple URLs and dicts instead


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


class DeploymentHistory:
    """Simple deployment tracking per endpoint with thread-safe operations."""

    def __init__(self) -> None:
        self._history: Dict[str, Dict[str, Any]] = {}

    def record(
        self, endpoint: str, version: str, success: bool, error: Optional[str] = None
    ) -> None:
        """Record a deployment attempt."""
        # Keep current version only if this deployment succeeded
        current_version = (
            self._history.get(endpoint, {}).get("version") if not success else version
        )

        self._history[endpoint] = {
            "version": current_version,  # What's actually running
            "timestamp": datetime.now(UTC).isoformat(),
            "success": success,
            "last_attempt": version,  # What was attempted
            "error": error,
        }

    def to_dict(self) -> Dict[str, Any]:
        """Get deployment history as dict."""
        return {"deployment_history": self._history}


def get_production_urls_from_index(
    indexed_pods: "IndexedResourceCollection",
) -> List[str]:
    """Extract dataplane URLs from indexed HAProxy pods."""

    urls = []

    # IndexedResourceCollection has already converted all Kopf objects to regular dicts
    # We can iterate through all resources directly
    for pod_dict in indexed_pods.values():
        # Extract pod status information
        status = pod_dict.get("status", {})
        phase = status.get("phase") if isinstance(status, dict) else None
        pod_ip = status.get("podIP") if isinstance(status, dict) else None

        logger.debug(f"🔍 Pod phase: {phase}, IP: {pod_ip}")

        if phase == "Running" and pod_ip:
            metadata = pod_dict.get("metadata", {})
            annotations = (
                metadata.get("annotations", {}) if isinstance(metadata, dict) else {}
            )
            port = (
                annotations.get(
                    "haproxy-template-ic/dataplane-port", str(DEFAULT_DATAPLANE_PORT)
                )
                if isinstance(annotations, dict)
                else str(DEFAULT_DATAPLANE_PORT)
            )
            url = f"http://{pod_ip}:{port}"
            urls.append(url)
            logger.debug(f"🔍 Found production URL: {url}")

    logger.debug(f"🔍 Found {len(urls)} production URLs: {urls}")
    return urls


# Element handler registry for structured nested element deployment
_ELEMENT_HANDLERS = {
    ConfigElementType.SERVER: {
        "sections": {ConfigSectionType.BACKEND},
        "api": (create_server_backend, replace_server_backend, delete_server_backend),
        "id_type": "name",
    },
    ConfigElementType.BIND: {
        "sections": {ConfigSectionType.FRONTEND},
        "api": (create_bind_frontend, replace_bind_frontend, delete_bind_frontend),
        "id_type": "name",
    },
    ConfigElementType.HTTP_REQUEST_RULE: {
        "api_map": {
            ConfigSectionType.BACKEND: (
                create_http_request_rule_backend,
                replace_http_request_rule_backend,
                delete_http_request_rule_backend,
            ),
            ConfigSectionType.FRONTEND: (
                create_http_request_rule_frontend,
                replace_http_request_rule_frontend,
                delete_http_request_rule_frontend,
            ),
        },
        "id_type": "index",
    },
    ConfigElementType.ACL: {
        "api_map": {
            ConfigSectionType.BACKEND: (
                create_acl_backend,
                replace_acl_backend,
                delete_acl_backend,
            ),
            ConfigSectionType.FRONTEND: (
                create_acl_frontend,
                replace_acl_frontend,
                delete_acl_frontend,
            ),
        },
        "id_type": "index",
    },
    ConfigElementType.BACKEND_SWITCHING_RULE: {
        "sections": {ConfigSectionType.FRONTEND},
        "api": (
            create_backend_switching_rule,
            replace_backend_switching_rule,
            delete_backend_switching_rule,
        ),
        "id_type": "index",
    },
    ConfigElementType.HTTP_RESPONSE_RULE: {
        "api_map": {
            ConfigSectionType.BACKEND: (
                create_http_response_rule_backend,
                replace_http_response_rule_backend,
                delete_http_response_rule_backend,
            ),
            ConfigSectionType.FRONTEND: (
                create_http_response_rule_frontend,
                replace_http_response_rule_frontend,
                delete_http_response_rule_frontend,
            ),
        },
        "id_type": "index",
    },
    ConfigElementType.FILTER: {
        "api_map": {
            ConfigSectionType.BACKEND: (
                create_filter_backend,
                replace_filter_backend,
                delete_filter_backend,
            ),
            ConfigSectionType.FRONTEND: (
                create_filter_frontend,
                replace_filter_frontend,
                delete_filter_frontend,
            ),
        },
        "id_type": "index",
    },
    ConfigElementType.TCP_REQUEST_RULE: {
        "api_map": {
            ConfigSectionType.BACKEND: (
                create_tcp_request_rule_backend,
                replace_tcp_request_rule_backend,
                delete_tcp_request_rule_backend,
            ),
            ConfigSectionType.FRONTEND: (
                create_tcp_request_rule_frontend,
                replace_tcp_request_rule_frontend,
                delete_tcp_request_rule_frontend,
            ),
        },
        "id_type": "index",
    },
    ConfigElementType.STICK_RULE: {
        "sections": {ConfigSectionType.BACKEND},
        "api": (create_stick_rule, replace_stick_rule, delete_stick_rule),
        "id_type": "index",
    },
    ConfigElementType.SERVER_SWITCHING_RULE: {
        "sections": {ConfigSectionType.BACKEND},
        "api": (
            create_server_switching_rule,
            replace_server_switching_rule,
            delete_server_switching_rule,
        ),
        "id_type": "index",
    },
    ConfigElementType.TCP_RESPONSE_RULE: {
        "api_map": {
            ConfigSectionType.BACKEND: (
                create_tcp_response_rule_backend,
                replace_tcp_response_rule_backend,
                delete_tcp_response_rule_backend,
            ),
        },
        "id_type": "index",
    },
    ConfigElementType.LOG_TARGET: {
        "api_map": {
            ConfigSectionType.BACKEND: (
                create_log_target_backend,
                replace_log_target_backend,
                delete_log_target_backend,
            ),
            ConfigSectionType.FRONTEND: (
                create_log_target_frontend,
                replace_log_target_frontend,
                delete_log_target_frontend,
            ),
        },
        "id_type": "index",
    },
}


# Section handler registry for structured top-level section deployment
_SECTION_HANDLERS = {
    ConfigSectionType.BACKEND: {
        "create": create_backend.asyncio,
        "update": replace_backend.asyncio,
        "delete": delete_backend.asyncio,
        "id_field": "name",
        "supports_create": True,
        "supports_update": True,
        "supports_delete": True,
    },
    ConfigSectionType.FRONTEND: {
        "create": create_frontend.asyncio,
        "update": replace_frontend.asyncio,
        "delete": delete_frontend.asyncio,
        "id_field": "name",
        "supports_create": True,
        "supports_update": True,
        "supports_delete": True,
    },
    ConfigSectionType.DEFAULTS: {
        "update": replace_defaults_section.asyncio,
        "id_field": "name",
        "supports_create": False,
        "supports_update": True,
        "supports_delete": False,
        "full_section": True,  # Use full_section=True for defaults
    },
    ConfigSectionType.GLOBAL: {
        "update": replace_global.asyncio,
        "id_field": None,  # Global section doesn't have a name
        "supports_create": True,  # CREATE is treated as UPDATE
        "supports_update": True,
        "supports_delete": False,
    },
    ConfigSectionType.USERLIST: {
        "create": create_userlist.asyncio,
        "delete": delete_userlist.asyncio,
        "id_field": "name",
        "supports_create": True,
        "supports_update": True,  # UPDATE handled as DELETE+CREATE
        "supports_delete": True,
        "update_strategy": "delete_create",  # No replace endpoint
    },
}


# Section elements registry - defines which nested elements each section type supports
_SECTION_ELEMENTS = {
    ConfigSectionType.BACKEND: [
        ("servers", ConfigElementType.SERVER, True),  # Named elements
        (
            "server_switching_rules",
            ConfigElementType.SERVER_SWITCHING_RULE,
            False,
        ),  # Ordered
        ("stick_rules", ConfigElementType.STICK_RULE, False),  # Ordered
        ("http_request_rules", ConfigElementType.HTTP_REQUEST_RULE, False),  # Ordered
        ("http_response_rules", ConfigElementType.HTTP_RESPONSE_RULE, False),  # Ordered
        ("tcp_request_rules", ConfigElementType.TCP_REQUEST_RULE, False),  # Ordered
        ("tcp_response_rules", ConfigElementType.TCP_RESPONSE_RULE, False),  # Ordered
        ("acls", ConfigElementType.ACL, True),  # Named
        ("filters", ConfigElementType.FILTER, False),  # Ordered
        ("log_targets", ConfigElementType.LOG_TARGET, False),  # Ordered
    ],
    ConfigSectionType.FRONTEND: [
        ("binds", ConfigElementType.BIND, True),  # Named elements
        (
            "backend_switching_rules",
            ConfigElementType.BACKEND_SWITCHING_RULE,
            False,
        ),  # Ordered
        ("http_request_rules", ConfigElementType.HTTP_REQUEST_RULE, False),  # Ordered
        ("http_response_rules", ConfigElementType.HTTP_RESPONSE_RULE, False),  # Ordered
        ("tcp_request_rules", ConfigElementType.TCP_REQUEST_RULE, False),  # Ordered
        # NOTE: TCP response rules are not supported for frontends
        ("acls", ConfigElementType.ACL, True),  # Named
        ("filters", ConfigElementType.FILTER, False),  # Ordered
        ("log_targets", ConfigElementType.LOG_TARGET, False),  # Ordered
    ],
    # Note: ConfigSectionType.DEFAULTS is not included here because the HAProxy
    # Dataplane API v3 doesn't support nested element endpoints for defaults
    # sections (returns HTTP 501 Not Implemented). Defaults are handled as
    # atomic units using full_section=true.
}


# Element fetch API registry - maps element attribute names to their fetch functions
_ELEMENT_FETCH_APIS = {
    ConfigSectionType.BACKEND: {
        "servers": get_all_server_backend.asyncio,
        "server_switching_rules": get_server_switching_rules.asyncio,
        "http_request_rules": get_all_http_request_rule_backend.asyncio,
        "http_response_rules": get_all_http_response_rule_backend.asyncio,
        "http_after_response_rules": get_all_http_after_response_rule_backend.asyncio,
        "http_error_rules": get_all_http_error_rule_backend.asyncio,
        "http_checks": get_all_http_check_backend.asyncio,
        "tcp_checks": get_all_tcp_check_backend.asyncio,
        "acls": get_all_acl_backend.asyncio,
        "filters": get_all_filter_backend.asyncio,
        "tcp_request_rules": get_all_tcp_request_rule_backend.asyncio,
        "tcp_response_rules": get_all_tcp_response_rule_backend.asyncio,
        "log_targets": get_all_log_target_backend.asyncio,
        "stick_rules": get_stick_rules.asyncio,
    },
    ConfigSectionType.FRONTEND: {
        "binds": get_all_bind_frontend.asyncio,
        "backend_switching_rules": get_backend_switching_rules.asyncio,
        "http_request_rules": get_all_http_request_rule_frontend.asyncio,
        "http_response_rules": get_all_http_response_rule_frontend.asyncio,
        "http_after_response_rules": get_all_http_after_response_rule_frontend.asyncio,
        "http_error_rules": get_all_http_error_rule_frontend.asyncio,
        "acls": get_all_acl_frontend.asyncio,
        "filters": get_all_filter_frontend.asyncio,
        "tcp_request_rules": get_all_tcp_request_rule_frontend.asyncio,
        "tcp_response_rules": None,  # Not supported for frontends
        "log_targets": get_all_log_target_frontend.asyncio,
        "quic_initial_rules": get_all_quic_initial_rule_frontend.asyncio,
    },
    ConfigSectionType.GLOBAL: {
        "log_targets": get_all_log_target_global.asyncio,
    },
}


# Storage resource sync registry for unified resource management
_STORAGE_SYNC_CONFIGS = {
    "maps": {
        "get_all_func": get_all_storage_map_files.asyncio,
        "get_one_func": get_one_storage_map.asyncio,
        "create_func": create_storage_map_file.asyncio,
        "delete_func": delete_storage_map.asyncio,
        "replace_func": replace_storage_map_file.asyncio,
        "create_body_class": CreateStorageMapFileBody,
        "mime_type": "text/plain",
    },
    "certificates": {
        "get_all_func": get_all_storage_ssl_certificates.asyncio,
        "get_one_func": get_one_storage_ssl_certificate.asyncio,
        "create_func": create_storage_ssl_certificate.asyncio,
        "delete_func": delete_storage_ssl_certificate.asyncio,
        "replace_func": replace_storage_ssl_certificate.asyncio,
        "create_body_class": CreateStorageSSLCertificateBody,
        "mime_type": "application/x-pem-file",
    },
}


class DataplaneClient:
    """Wrapper around the generated HAProxy Dataplane API v3 client.

    This client provides a simplified interface for common Dataplane API operations
    including configuration validation and deployment. All operations raise
    structured exceptions with detailed context information.

    Example:
        Basic usage with error handling:

        >>> client = DataplaneClient("http://localhost:5555", auth=("admin", "password"))
        >>> try:
        ...     await client.validate_configuration(config_text)
        ...     version = await client.deploy_configuration(config_text)
        ... except ValidationError as e:
        ...     print(f"Config validation failed: {e}")
        ...     print(f"Config size: {e.config_size}, Details: {e.validation_details}")
        ... except DataplaneAPIError as e:
        ...     print(f"API error: {e}")
        ...     print(f"Endpoint: {e.endpoint}, Operation: {e.operation}")

    Raises:
        DataplaneAPIError: For general API communication errors
        ValidationError: For HAProxy configuration validation failures
    """

    def __init__(
        self,
        base_url: str,
        timeout: float = DEFAULT_API_TIMEOUT,
        auth: tuple[str, str] = (
            DEFAULT_DATAPLANE_USERNAME,
            DEFAULT_DATAPLANE_PASSWORD,
        ),
    ):
        """
        Initialize the client.

        Args:
            base_url: The base URL of the Dataplane API (with or without /v3)
            timeout: Request timeout in seconds
            auth: Tuple of (username, password) for basic auth
        """
        # Normalize the base URL to ensure it ends with /v3
        self.base_url = normalize_dataplane_url(base_url)
        self.timeout = timeout
        self.auth = auth

        # Defer client creation until first use
        self._client = None

    def _get_client(self) -> Any:
        """Lazy initialization of AuthenticatedClient object."""
        if self._client is None:
            logger.debug(f"Creating dataplane client for {self.base_url}")
            # Create basic auth token from username and password
            auth_string = f"{self.auth[0]}:{self.auth[1]}"
            auth_token = base64.b64encode(auth_string.encode()).decode("ascii")
            self._client = AuthenticatedClient(
                base_url=self.base_url,
                token=auth_token,
                prefix="Basic",
                timeout=httpx.Timeout(self.timeout),
            )
        return self._client

    @handle_dataplane_errors()
    async def get_version(self) -> Dict[str, Any]:
        """Get HAProxy version information using the generated client."""
        client = self._get_client()
        info_response = await get_info.asyncio(client=client)

        # Convert the generated model to dict format expected by existing code
        result = {}
        if hasattr(info_response, "haproxy") and info_response.haproxy:
            result.update(info_response.haproxy.to_dict())
        if hasattr(info_response, "api") and info_response.api:
            result.update(info_response.api.to_dict())
        if hasattr(info_response, "system") and info_response.system:
            result.update(info_response.system.to_dict())

        return result

    async def validate_configuration(self, config_content: str) -> None:
        """Validate HAProxy configuration without applying it.

        Uses direct httpx calls since openapi-python-client doesn't support
        text/plain content type for configuration endpoints.

        Raises:
            ValidationError: If configuration validation fails
            DataplaneAPIError: If API communication fails
        """
        with trace_dataplane_operation("validate", self.base_url):
            add_span_attributes(
                config_size=len(config_content), dataplane_url=self.base_url
            )

            metrics = get_metrics_collector()

            with metrics.time_dataplane_api_operation("validate"):
                try:
                    # Ensure config ends with newline to avoid HAProxy truncation errors
                    config_data = config_content.rstrip() + "\n"

                    # Use httpx directly for text/plain content
                    async with httpx.AsyncClient(timeout=self.timeout) as client:
                        response = await client.post(
                            f"{self.base_url}/services/haproxy/configuration/raw",
                            content=config_data,
                            headers={"Content-Type": "text/plain"},
                            params={"only_validate": "true", "skip_version": "true"},
                            auth=(self.auth[0], self.auth[1]),
                        )

                        if response.status_code >= 400:
                            validation_details = response.text
                            record_span_event(
                                "validation_failed", {"error": "validation_failed"}
                            )
                            set_span_error(
                                Exception(validation_details),
                                "Configuration validation failed",
                            )

                            # Extract error line and context for better debugging
                            error_line, error_context = parse_validation_error_details(
                                validation_details, config_data
                            )

                            raise ValidationError(
                                f"Configuration validation failed: {response.status_code} {validation_details}",
                                endpoint=self.base_url,
                                config_size=len(config_content),
                                validation_details=validation_details,
                                error_line=error_line,
                                config_content=config_data,
                                error_context=error_context,
                            )

                        record_span_event("validation_successful")

                except ValidationError:
                    # Re-raise ValidationError without wrapping
                    raise
                except httpx.RequestError as e:
                    # Handle network-related exceptions
                    record_span_event("validation_failed", {"error": str(e)})
                    set_span_error(e, "Configuration validation failed")
                    raise DataplaneAPIError(
                        f"Network error during validation: {e}",
                        endpoint=self.base_url,
                        operation="validate",
                        original_error=e,
                    ) from e
                except Exception as e:
                    # Handle all other unexpected exceptions
                    record_span_event("validation_failed", {"error": str(e)})
                    set_span_error(e, "Configuration validation failed")
                    raise DataplaneAPIError(
                        f"Configuration validation failed: {e}",
                        endpoint=self.base_url,
                        operation="validate",
                        original_error=e,
                    ) from e

    async def deploy_configuration(self, config_content: str) -> str:
        """Deploy HAProxy configuration.

        Uses direct httpx calls since openapi-python-client doesn't support
        text/plain content type for configuration endpoints.

        This method includes retry logic for transient failures (network issues,
        temporary dataplane unavailability), but excludes validation errors
        from retries since retrying won't fix config errors.
        """
        with trace_dataplane_operation("deploy", self.base_url):
            add_span_attributes(
                config_size=len(config_content), dataplane_url=self.base_url
            )

            metrics = get_metrics_collector()

            async def deployment_operation():
                with metrics.time_dataplane_api_operation("deploy"):
                    async with httpx.AsyncClient(timeout=self.timeout) as client:
                        # Get current configuration version first
                        version_response = await client.get(
                            f"{self.base_url}/services/haproxy/configuration/version",
                            auth=(self.auth[0], self.auth[1]),
                        )
                        if version_response.status_code >= 400:
                            raise DataplaneAPIError(
                                f"Failed to get configuration version: {version_response.text}"
                            )

                        current_version = version_response.json()

                        # Deploy configuration with reload using httpx
                        # Ensure config ends with newline to avoid HAProxy truncation errors
                        config_data = config_content.rstrip() + "\n"

                        deploy_response = await client.post(
                            f"{self.base_url}/services/haproxy/configuration/raw",
                            content=config_data,
                            headers={"Content-Type": "text/plain"},
                            params={
                                "version": str(current_version),
                            },
                            auth=(self.auth[0], self.auth[1]),
                        )

                        if deploy_response.status_code >= 400:
                            error_details = deploy_response.text
                            # Parse error details to extract line number and context
                            error_line, error_context = parse_validation_error_details(
                                error_details, config_data
                            )

                            # Create enhanced error with config context
                            error_msg = f"Configuration deployment failed: {deploy_response.status_code} {error_details}"
                            if error_context:
                                error_msg += f"\n\nConfiguration context around error:\n{error_context}"

                            raise DataplaneAPIError(error_msg)

                        # Get the new configuration version
                        new_version_response = await client.get(
                            f"{self.base_url}/services/haproxy/configuration/version",
                            auth=(self.auth[0], self.auth[1]),
                        )
                        if new_version_response.status_code >= 400:
                            raise DataplaneAPIError(
                                f"Failed to get new configuration version: {new_version_response.text}"
                            )

                        new_version = new_version_response.json()
                        return str(new_version)

            try:
                # Simple retry with tenacity
                async for attempt in AsyncRetrying(
                    stop=stop_after_attempt(5),
                    wait=wait_exponential_jitter(
                        initial=INITIAL_RETRY_WAIT_SECONDS, max=MAX_RETRY_WAIT_SECONDS
                    ),
                    retry=retry_if_exception(
                        lambda e: (
                            isinstance(e, httpx.RequestError)  # Network errors only
                            or (
                                isinstance(e, DataplaneAPIError)
                                and not isinstance(e, ValidationError)
                                and "400" not in str(e)  # Don't retry validation errors
                            )
                        )
                    ),
                ):
                    with attempt:
                        version = await deployment_operation()
                        add_span_attributes(config_version=version)
                        record_span_event("deployment_successful", {"version": version})
                        return version

                # This should never be reached, but satisfies mypy
                raise DataplaneAPIError(
                    "Retry loop completed without success or failure"
                )
            except Exception as e:
                record_span_event("deployment_failed", {"error": str(e)})
                set_span_error(e, "Configuration deployment failed")
                raise DataplaneAPIError(
                    f"Configuration deployment failed: {e}",
                    endpoint=self.base_url,
                    operation="deploy",
                    original_error=e,
                ) from e

    def _extract_storage_content(self, storage_item: Optional[Any]) -> Optional[str]:
        """Extract content from HAProxy storage API response.

        Args:
            storage_item: Response from get_one_storage_* API calls

        Returns:
            Decoded content string or None if extraction fails
        """
        if not storage_item or not hasattr(storage_item, "payload"):
            return None
        try:
            content = storage_item.payload.read()
            if hasattr(storage_item.payload, "seek"):
                storage_item.payload.seek(0)
            return content.decode("utf-8")
        except Exception:
            return None

    @handle_dataplane_errors()
    async def _sync_storage_resources(
        self,
        resource_type: str,
        new_resources: Dict[str, str],
        get_all_func,
        get_one_func,
        create_func,
        delete_func,
        create_body_class,
        mime_type: str = "text/plain",
        replace_func=None,
    ) -> None:
        """Generic method to sync storage resources with content comparison.

        Args:
            resource_type: Type of resource ("map", "certificate", or "file")
            new_resources: Dict of resource name to content
            get_all_func: Async function to get all existing resources
            get_one_func: Async function to get a single resource
            create_func: Async function to create a resource
            delete_func: Async function to delete a resource
            create_body_class: Class to create request body
            mime_type: MIME type for the resource
            replace_func: Optional async function to replace resource content
        """
        metrics = get_metrics_collector()
        operation = f"sync_{resource_type}s"

        with metrics.time_dataplane_api_operation(operation):
            client = self._get_client()

            # Get existing resources
            existing = await get_all_func(client=client)
            existing_dict = {
                f.storage_name: f for f in (existing or []) if f.storage_name
            }

            target_names = set(new_resources.keys())
            existing_names = set(existing_dict.keys())

            created_count = 0
            updated_count = 0
            skipped_count = 0

            # Create new resources
            for name in target_names - existing_names:
                body = create_body_class(
                    file_upload=File(
                        payload=io.BytesIO(new_resources[name].encode("utf-8")),
                        file_name=name,
                        mime_type=mime_type,
                    )
                )
                body["description"] = compute_content_hash(new_resources[name])
                await create_func(client=client, body=body)
                created_count += 1
                logger.debug(f"Created {resource_type} {name}")

            # Update or skip existing resources
            for name in target_names & existing_names:
                new_content = new_resources[name]

                # Check if content changed
                try:
                    existing_resource = await get_one_func(client=client, name=name)
                    existing_content = self._extract_storage_content(existing_resource)

                    if existing_content == new_content:
                        skipped_count += 1
                        logger.debug(f"Skipped {resource_type} {name} (unchanged)")
                        continue
                except Exception as e:
                    _log_fetch_error(resource_type, name, e)

                # Content changed - use replace if available, otherwise delete+create
                if replace_func:
                    # Use generated replace function for maps/certificates
                    # The generated functions expect: client, name, body (string content)
                    await replace_func(client=client, name=name, body=new_content)
                else:
                    # Fallback to delete+create (shouldn't happen with proper replace_func)
                    await delete_func(client=client, name=name)
                    body = create_body_class(
                        file_upload=File(
                            payload=io.BytesIO(new_content.encode("utf-8")),
                            file_name=name,
                            mime_type=mime_type,
                        )
                    )
                    body["description"] = compute_content_hash(new_content)
                    await create_func(client=client, body=body)

                updated_count += 1
                logger.debug(f"Updated {resource_type} {name}")

            # Delete obsolete resources
            for name in existing_names - target_names:
                await delete_func(client=client, name=name)
                logger.debug(f"Deleted {resource_type} {name}")

            # Log summary - only use INFO if something changed
            if created_count or updated_count:
                logger.info(
                    f"{resource_type.capitalize()}s: "
                    f"{created_count} created, {updated_count} updated, {skipped_count} unchanged"
                )
            elif skipped_count:
                logger.debug(
                    f"{resource_type.capitalize()}s: "
                    f"{created_count} created, {updated_count} updated, {skipped_count} unchanged"
                )

            metrics.record_dataplane_api_request(operation, "success")

    async def sync_maps(self, maps: Dict[str, str]) -> None:
        """Synchronize HAProxy map files to storage."""
        config = _STORAGE_SYNC_CONFIGS["maps"]
        await self._sync_storage_resources(
            resource_type="map", new_resources=maps, **config
        )

    async def sync_certificates(self, certificates: Dict[str, str]) -> None:
        """Synchronize SSL certificates to storage."""
        config = _STORAGE_SYNC_CONFIGS["certificates"]
        await self._sync_storage_resources(
            resource_type="certificate", new_resources=certificates, **config
        )

    @handle_dataplane_errors()
    async def sync_files(self, files: Dict[str, str]) -> None:
        """Synchronize general-purpose files to HAProxy storage.

        Note: Files use replace instead of delete+create for updates.
        """
        metrics = get_metrics_collector()
        operation = "sync_files"

        with metrics.time_dataplane_api_operation(operation):
            client = self._get_client()

            # Get existing resources
            existing = await get_all_storage_general_files.asyncio(client=client)
            existing_dict = {
                f.storage_name: f for f in (existing or []) if f.storage_name
            }

            target_names = set(files.keys())
            existing_names = set(existing_dict.keys())

            created_count = 0
            updated_count = 0
            skipped_count = 0

            # Create new files
            for name in target_names - existing_names:
                body = CreateStorageGeneralFileBody(
                    file_upload=File(
                        payload=io.BytesIO(files[name].encode("utf-8")),
                        file_name=name,
                        mime_type="text/plain",
                    )
                )
                body["description"] = compute_content_hash(files[name])
                await create_storage_general_file.asyncio(client=client, body=body)
                created_count += 1
                logger.debug(f"Created file {name}")

            # Update or skip existing files
            for name in target_names & existing_names:
                new_content = files[name]

                # Check if content changed
                try:
                    existing_file = await get_one_storage_general_file.asyncio(
                        client=client, name=name
                    )
                    existing_content = self._extract_storage_content(existing_file)

                    if existing_content == new_content:
                        skipped_count += 1
                        logger.debug(f"Skipped file {name} (unchanged)")
                        continue
                except Exception as e:
                    _log_fetch_error("file", name, e)

                # Content changed - use replace for files
                body = ReplaceStorageGeneralFileBody(
                    file_upload=File(
                        payload=io.BytesIO(new_content.encode("utf-8")),
                        file_name=name,
                        mime_type="text/plain",
                    )
                )
                body["description"] = compute_content_hash(new_content)
                await replace_storage_general_file.asyncio(
                    client=client, name=name, body=body
                )
                updated_count += 1
                logger.debug(f"Updated file {name}")

            # Delete obsolete files
            for name in existing_names - target_names:
                await delete_storage_general_file.asyncio(client=client, name=name)
                logger.debug(f"Deleted file {name}")

            # Log summary - only use INFO if something changed
            if created_count or updated_count:
                logger.info(
                    f"Files: "
                    f"{created_count} created, {updated_count} updated, {skipped_count} unchanged"
                )
            elif skipped_count:
                logger.debug(
                    f"Files: "
                    f"{created_count} created, {updated_count} updated, {skipped_count} unchanged"
                )

            metrics.record_dataplane_api_request(operation, "success")

    async def get_current_configuration(self) -> Optional[str]:
        """Get current raw HAProxy configuration.

        Returns:
            Current HAProxy configuration as string, or None if not available
        """
        try:
            client = self._get_client()
            config = await get_ha_proxy_configuration.asyncio(client=client)
            return config
        except Exception as e:
            _log_fetch_error("configuration", "current", e)
            return None

    async def deploy_configuration_conditionally(
        self, config_content: str, force: bool = False
    ) -> str:
        """Deploy HAProxy configuration only if it differs from current config.

        This method compares the new configuration with the current one and only
        deploys if they differ or if force=True. This helps minimize unnecessary
        HAProxy reloads.

        Args:
            config_content: New configuration to deploy
            force: If True, deploy even if configs are identical

        Returns:
            Configuration version after deployment

        Raises:
            ValidationError: If configuration validation fails
            DataplaneAPIError: If deployment fails
        """

        with trace_dataplane_operation("deploy_conditional", self.base_url):
            add_span_attributes(
                config_size=len(config_content),
                dataplane_url=self.base_url,
                force_deployment=force,
            )

            # Get current configuration for comparison
            current_config = None
            if not force:
                current_config = await self.get_current_configuration()

            # Normalize both configs for comparison (remove extra whitespace, etc.)
            def normalize_config(config: str) -> str:
                if not config:
                    return ""
                # Remove trailing whitespace from each line and normalize line endings
                lines = [line.rstrip() for line in config.splitlines()]
                # Remove empty lines at the end
                while lines and not lines[-1]:
                    lines.pop()
                return "\n".join(lines) + "\n" if lines else ""

            new_config_normalized = normalize_config(config_content)
            current_config_normalized = (
                normalize_config(current_config) if current_config else ""
            )

            # Skip deployment if configs are identical
            if not force and new_config_normalized == current_config_normalized:
                logger.info(
                    f"⏭️  Configuration unchanged, skipping deployment to {self.base_url}"
                )
                add_span_attributes(deployment_skipped=True)
                record_span_event("deployment_skipped", {"reason": "config_unchanged"})

                # Get current version
                try:
                    client = self._get_client()
                    version_response = await _get_configuration_version(client)
                    return str(version_response) if version_response else "unknown"
                except Exception:
                    return "unknown"

            # Deploy the configuration (it's different or forced)
            logger.info(
                f"📤 Deploying configuration to {self.base_url} (changed: {current_config is not None})"
            )
            add_span_attributes(
                deployment_skipped=False, config_changed=current_config is not None
            )
            return await self.deploy_configuration(new_config_normalized)

    async def deploy_structured_configuration(self, changes: List[ConfigChange]) -> str:
        """Deploy HAProxy configuration changes using granular dataplane API endpoints.

        This method applies a list of ConfigChange objects using HAProxy's structured
        API endpoints within a transaction, which minimizes reloads by only changing
        what's actually different.

        Args:
            changes: List of ConfigChange objects to apply

        Returns:
            Configuration version after deployment

        Raises:
            DataplaneAPIError: If deployment fails
        """
        if not changes:
            logger.debug("⏭️  No changes to deploy")
            return "unchanged"

        with trace_dataplane_operation("deploy_structured", self.base_url):
            add_span_attributes(
                dataplane_url=self.base_url,
                changes_count=len(changes),
                change_types=[str(c.change_type.value) for c in changes],
            )

            metrics = get_metrics_collector()
            client = self._get_client()

            # Start a transaction to batch all changes atomically
            try:
                # Get current configuration version for transaction consistency
                current_version = await _get_configuration_version(client)
                if current_version is None:
                    raise DataplaneAPIError(
                        "Failed to get current configuration version for transaction",
                        endpoint=self.base_url,
                        operation="get_configuration_version",
                    )

                # Start transaction with version
                with metrics.time_dataplane_api_operation("start_transaction"):
                    transaction = await start_transaction.asyncio(
                        client=client, version=current_version
                    )
                    transaction_id = transaction.id if transaction else None

                logger.debug(
                    f"📦 Started transaction {transaction_id} for {len(changes)} changes"
                )

                try:
                    # Apply all changes within the transaction
                    for i, change in enumerate(changes):
                        logger.debug(
                            f"📝 Applying change {i + 1}/{len(changes)}: {change}"
                        )
                        await self._apply_config_change(
                            client, change, transaction_id or ""
                        )

                    # Commit the transaction
                    with metrics.time_dataplane_api_operation("commit_transaction"):
                        await commit_transaction.asyncio(
                            client=client, id=transaction_id
                        )

                    logger.info(
                        f"✅ Successfully deployed {len(changes)} structured changes in transaction {transaction_id}"
                    )

                    # Get the new configuration version
                    version_response = await _get_configuration_version(client)
                    new_version = (
                        str(version_response) if version_response else "unknown"
                    )

                    record_span_event(
                        "structured_deployment_successful",
                        {
                            "transaction_id": transaction_id,
                            "changes_count": len(changes),
                            "version": new_version,
                        },
                    )

                    return new_version

                except Exception as apply_error:
                    # Rollback transaction on failure
                    try:
                        logger.warning(
                            f"⚠️  Rolling back transaction {transaction_id} due to error: {apply_error}"
                        )
                        await delete_transaction.asyncio(
                            client=client, id=transaction_id
                        )
                    except Exception as rollback_error:
                        logger.error(
                            f"❌ Failed to rollback transaction {transaction_id}: {rollback_error}"
                        )

                    record_span_event(
                        "structured_deployment_failed",
                        {"transaction_id": transaction_id, "error": str(apply_error)},
                    )
                    set_span_error(apply_error, "Structured deployment failed")

                    raise DataplaneAPIError(
                        f"Structured deployment failed in transaction {transaction_id}: {apply_error}",
                        endpoint=self.base_url,
                        operation="deploy_structured",
                        original_error=apply_error,
                    ) from apply_error

            except Exception as transaction_error:
                record_span_event(
                    "transaction_start_failed", {"error": str(transaction_error)}
                )
                set_span_error(transaction_error, "Failed to start transaction")

                raise DataplaneAPIError(
                    f"Failed to start transaction for structured deployment: {transaction_error}",
                    endpoint=self.base_url,
                    operation="deploy_structured",
                    original_error=transaction_error,
                ) from transaction_error

    async def _apply_nested_element_change(
        self, client: Any, change: ConfigChange, transaction_id: str
    ) -> None:
        """Apply a nested element change using the appropriate dataplane API endpoint.

        Args:
            client: The authenticated dataplane API client
            change: The nested element change to apply
            transaction_id: The transaction ID to use for the change
        """
        element_type = change.element_type
        section_type = change.section_type
        section_name = change.section_name

        try:
            # Look up handler configuration from registry
            if element_type is None:
                logger.warning(
                    "⚠️  Element type is None - skipping nested element change"
                )
                return

            handler_config = _ELEMENT_HANDLERS.get(element_type)
            if not handler_config:
                logger.warning(
                    f"⚠️  Unsupported nested element type for structured deployment: {element_type}"
                )
                return

            id_type = handler_config["id_type"]

            # Handle both registry formats: api_map (multiple sections) vs sections + api (single section type)
            if "api_map" in handler_config:
                # Multiple sections format
                api_map = dict(handler_config["api_map"])
                if section_type not in api_map:
                    logger.debug(
                        f"Element type {element_type} not supported for section type {section_type}"
                    )
                    return
                api_tuple = api_map[section_type]
                if not isinstance(api_tuple, (list, tuple)) or len(api_tuple) != 3:
                    logger.error(
                        f"Invalid API tuple for {element_type.value}/{section_type.value}"
                    )
                    return
                create_fn, replace_fn, delete_fn = (
                    api_tuple[0],
                    api_tuple[1],
                    api_tuple[2],
                )
            elif "sections" in handler_config and "api" in handler_config:
                # Single section type format
                if section_type not in handler_config["sections"]:
                    logger.debug(
                        f"Element type {element_type} not supported for section type {section_type}"
                    )
                    return
                create_fn, replace_fn, delete_fn = handler_config["api"]
            else:
                logger.error(
                    f"Invalid handler configuration for element type {element_type}"
                )
                return

            # Prepare common parameters
            base_params = {
                "client": client,
                "parent_name": section_name,
                "transaction_id": transaction_id,
            }

            # Execute the appropriate operation
            if change.change_type == ConfigChangeType.CREATE:
                clean_config = self._get_clean_config_object(change.new_config)
                params = {**base_params, "body": clean_config}
                if id_type == "index":
                    params["index"] = change.element_index
                await create_fn.asyncio(**params)

            elif change.change_type == ConfigChangeType.UPDATE:
                clean_config = self._get_clean_config_object(change.new_config)
                params = {**base_params, "body": clean_config}
                if id_type == "index":
                    params["index"] = change.element_index
                else:  # name
                    params["name"] = change.element_id
                await replace_fn.asyncio(**params)

            elif change.change_type == ConfigChangeType.DELETE:
                params = base_params.copy()
                if id_type == "index":
                    params["index"] = change.element_index
                else:  # name
                    params["name"] = change.element_id
                await delete_fn.asyncio(**params)

        except Exception as e:
            raise DataplaneAPIError(
                f"Failed to apply nested element change {change}: {e}",
                endpoint=self.base_url,
                operation=f"apply_{change.change_type.value}_{element_type.value if element_type else 'unknown'}",
                original_error=e,
            ) from e

    def _get_clean_config_object(self, config_obj: Any) -> Any:
        """Remove dynamically added attributes from config objects.

        This method ensures that only original model attributes are present
        when passing objects to the API, avoiding JSON serialization errors
        with dynamically added nested elements.

        Args:
            config_obj: The config object that may have extra attributes

        Returns:
            A clean config object suitable for API calls
        """
        if config_obj is None:
            return None

        # If it's a model object with to_dict/from_dict methods, use them
        # to create a clean copy with only the original schema attributes
        if hasattr(config_obj, "to_dict") and hasattr(config_obj, "from_dict"):
            try:
                # Get the clean dictionary representation (only original attributes)
                clean_dict = config_obj.to_dict()
                # Recreate the object from the dictionary
                return config_obj.__class__.from_dict(clean_dict)
            except Exception as e:
                logger.debug(
                    f"Failed to clean config object {type(config_obj).__name__}: {e}"
                )
                return config_obj

        # For non-model objects, return as-is
        return config_obj

    async def _apply_config_change(
        self, client: Any, change: ConfigChange, transaction_id: str
    ) -> None:
        """Apply a single configuration change using the appropriate dataplane API endpoint.

        Args:
            client: The authenticated dataplane API client
            change: The configuration change to apply
            transaction_id: The transaction ID to use for the change
        """
        try:
            # Handle nested element changes
            if change.element_type:
                await self._apply_nested_element_change(client, change, transaction_id)
                return

            # Handle top-level section changes using registry
            handler_config = _SECTION_HANDLERS.get(change.section_type)
            if not handler_config:
                logger.warning(
                    f"⚠️  Unsupported section type for structured deployment: {change.section_type}"
                )
                return

            # Prepare base parameters
            base_params = {
                "client": client,
                "transaction_id": transaction_id,
            }

            # Handle different change types
            if change.change_type == ConfigChangeType.CREATE:
                if not handler_config.get("supports_create", False):
                    if change.section_type == ConfigSectionType.GLOBAL:
                        # Global CREATE is treated as UPDATE
                        change.change_type = ConfigChangeType.UPDATE
                    else:
                        logger.debug(
                            f"Section type {change.section_type} doesn't support CREATE"
                        )
                        return

                if (
                    change.change_type == ConfigChangeType.CREATE
                ):  # Still CREATE after potential conversion
                    clean_config = self._get_clean_config_object(change.new_config)
                    params = {**base_params, "body": clean_config}
                    await handler_config["create"](**params)
                else:
                    # Fall through to UPDATE handling for converted GLOBAL operations
                    pass

            if change.change_type == ConfigChangeType.UPDATE:
                if not handler_config.get("supports_update", False):
                    logger.debug(
                        f"Section type {change.section_type} doesn't support UPDATE"
                    )
                    return

                # Handle different update strategies
                if handler_config.get("update_strategy") == "delete_create":
                    # Userlist: delete then create
                    if handler_config.get("supports_delete", False):
                        params = {**base_params}
                        if handler_config["id_field"]:
                            params[handler_config["id_field"]] = change.section_name
                        await handler_config["delete"](**params)

                    clean_config = self._get_clean_config_object(change.new_config)
                    params = {**base_params, "body": clean_config}
                    await handler_config["create"](**params)
                else:
                    # Standard update
                    clean_config = self._get_clean_config_object(change.new_config)
                    params = {**base_params, "body": clean_config}
                    if handler_config["id_field"]:
                        params[handler_config["id_field"]] = change.section_name
                    if handler_config.get("full_section"):
                        params["full_section"] = True
                    await handler_config["update"](**params)

            elif change.change_type == ConfigChangeType.DELETE:
                if not handler_config.get("supports_delete", False):
                    logger.debug(
                        f"Section type {change.section_type} doesn't support DELETE"
                    )
                    return

                params = {**base_params}
                if handler_config["id_field"]:
                    params[handler_config["id_field"]] = change.section_name
                await handler_config["delete"](**params)

        except Exception as e:
            raise DataplaneAPIError(
                f"Failed to apply {change}: {e}",
                endpoint=self.base_url,
                operation=f"apply_{change.change_type.value}_{change.section_type.value}",
                original_error=e,
            ) from e

    async def fetch_structured_configuration(self) -> Dict[str, Any]:
        """Fetch complete structured configuration components from this HAProxy instance.

        This method fetches both top-level configuration sections and all their detailed
        nested configurations using specialized endpoints, ensuring complete configuration
        comparison and deployment.

        Returns:
            Dictionary containing:
            - backends: List of backend configurations with nested details
            - frontends: List of frontend configurations with nested details
            - defaults: List of defaults sections with nested details
            - global: Global configuration section with nested details
            - userlists: List of userlist sections
            - caches: List of cache sections
            - mailers: List of mailers sections
            - resolvers: List of resolvers sections
            - peers: List of peer sections
            - fcgi_apps: List of fcgi-app sections with nested details
            - http_errors: List of http-errors sections
            - rings: List of ring sections
            - log_forwards: List of log-forward sections
            - programs: List of program sections

        Raises:
            DataplaneAPIError: If fetching configuration fails
        """
        metrics = get_metrics_collector()

        with metrics.time_dataplane_api_operation("fetch_structured"):
            client = self._get_client()

            try:
                # Fetch all top-level components with timing using helper
                backends = await _fetch_with_metrics(
                    "fetch_backends", get_backends.asyncio, client, metrics, []
                )
                frontends = await _fetch_with_metrics(
                    "fetch_frontends", get_frontends.asyncio, client, metrics, []
                )
                defaults = await _fetch_with_metrics(
                    "fetch_defaults", get_defaults_sections.asyncio, client, metrics, []
                )
                global_config = await _fetch_with_metrics(
                    "fetch_global", get_global.asyncio, client, metrics
                )
                userlists = await _fetch_with_metrics(
                    "fetch_userlists", get_userlists.asyncio, client, metrics, []
                )
                caches = await _fetch_with_metrics(
                    "fetch_caches", get_caches.asyncio, client, metrics, []
                )
                mailers = await _fetch_with_metrics(
                    "fetch_mailers", get_mailers_sections.asyncio, client, metrics, []
                )
                resolvers = await _fetch_with_metrics(
                    "fetch_resolvers", get_resolvers.asyncio, client, metrics, []
                )
                peers = await _fetch_with_metrics(
                    "fetch_peers", get_peer_sections.asyncio, client, metrics, []
                )
                fcgi_apps = await _fetch_with_metrics(
                    "fetch_fcgi_apps", get_fcgi_apps.asyncio, client, metrics, []
                )
                http_errors = await _fetch_with_metrics(
                    "fetch_http_errors",
                    get_http_errors_sections.asyncio,
                    client,
                    metrics,
                    [],
                )
                rings = await _fetch_with_metrics(
                    "fetch_rings", get_rings.asyncio, client, metrics, []
                )
                log_forwards = await _fetch_with_metrics(
                    "fetch_log_forwards", get_log_forwards.asyncio, client, metrics, []
                )
                programs = await _fetch_with_metrics(
                    "fetch_programs", get_programs.asyncio, client, metrics, []
                )

                # Create storage for nested elements to avoid modifying frozen models
                nested_elements: Dict[str, Dict[str, Dict[str, Any]]] = {
                    "backends": {},
                    "frontends": {},
                    "defaults": {},
                    "global": {},
                }

                # Now fetch detailed configurations for each section using registry-based approach
                section_configs = [
                    (ConfigSectionType.BACKEND, backends, "backends"),
                    (ConfigSectionType.FRONTEND, frontends, "frontends"),
                ]

                for section_type, sections, section_key in section_configs:
                    fetch_apis = _ELEMENT_FETCH_APIS.get(section_type, {})

                    for section in sections:
                        if hasattr(section, "name") and section.name:
                            section_name = section.name
                            nested_elements[section_key][section_name] = {}

                            try:
                                # Fetch all element types for this section
                                for attr_name, fetch_func in fetch_apis.items():
                                    if fetch_func is None:
                                        # Handle unsupported operations (like tcp_response_rules for frontends)
                                        nested_elements[section_key][section_name][
                                            attr_name
                                        ] = []
                                    else:
                                        nested_elements[section_key][section_name][
                                            attr_name
                                        ] = (
                                            await fetch_func(
                                                client=client, parent_name=section_name
                                            )
                                            or []
                                        )
                            except Exception as e:
                                logger.debug(
                                    f"Failed to fetch details for {section_type.value} {section_name}: {e}"
                                )
                                # Continue with other sections even if one fails

                # Skip nested element fetching for defaults sections
                # HAProxy Dataplane API v3 limitation: nested element endpoints for defaults sections
                # return HTTP 501 Not Implemented. Instead, defaults are handled as atomic units
                # using full_section=true in deployment operations.
                # The main defaults configuration already includes all nested elements.

                # Fetch nested elements for global configuration
                if global_config:
                    nested_elements["global"] = {}
                    global_fetch_apis = _ELEMENT_FETCH_APIS.get(
                        ConfigSectionType.GLOBAL, {}
                    )

                    try:
                        for attr_name, fetch_func in global_fetch_apis.items():
                            result = await fetch_func(client=client) or []
                            if isinstance(result, list):
                                nested_elements["global"][attr_name] = {}
                                for idx, item in enumerate(result):
                                    nested_elements["global"][attr_name][str(idx)] = (
                                        item
                                    )
                            else:
                                nested_elements["global"][attr_name] = {}
                    except Exception as e:
                        logger.debug(f"Failed to fetch global configuration: {e}")

                # Skip fcgi_apps nested elements for now - they have minimal nested configuration
                # and are not commonly used in most HAProxy setups

                # Record successful fetch
                metrics.record_dataplane_api_request("fetch_structured", "success")

                # Record component counts
                add_span_attributes(
                    backends_count=len(backends),
                    frontends_count=len(frontends),
                    defaults_count=len(defaults),
                    has_global=global_config is not None,
                    userlists_count=len(userlists),
                    caches_count=len(caches),
                    mailers_count=len(mailers),
                    resolvers_count=len(resolvers),
                    peers_count=len(peers),
                    fcgi_apps_count=len(fcgi_apps),
                    http_errors_count=len(http_errors),
                    rings_count=len(rings),
                    log_forwards_count=len(log_forwards),
                    programs_count=len(programs),
                )

                return {
                    "backends": backends,
                    "frontends": frontends,
                    "defaults": defaults,
                    "global": global_config,
                    "userlists": userlists,
                    "caches": caches,
                    "mailers": mailers,
                    "resolvers": resolvers,
                    "peers": peers,
                    "fcgi_apps": fcgi_apps,
                    "http_errors": http_errors,
                    "rings": rings,
                    "log_forwards": log_forwards,
                    "programs": programs,
                    "nested_elements": nested_elements,
                }
            except Exception as e:
                metrics.record_dataplane_api_request("fetch_structured", "error")
                _log_fetch_error("structured configuration", "all", e)
                raise DataplaneAPIError(
                    f"Failed to fetch structured configuration: {e}",
                    endpoint=self.base_url,
                    operation="fetch_structured",
                    original_error=e,
                ) from e


class ConfigSynchronizer:
    """Simple configuration synchronizer for HAProxy instances."""

    def __init__(
        self,
        production_urls: List[str],
        validation_url: str,
        credentials: "Credentials",
        deployment_history: Optional[DeploymentHistory] = None,
    ):
        self.production_urls = production_urls
        self.validation_url = validation_url
        self.credentials = credentials
        self.deployment_history = deployment_history or DeploymentHistory()

        # Initialize client references (will be created lazily)
        self._validation_client: Optional[DataplaneClient] = None
        self._production_clients: Dict[str, DataplaneClient] = {}

    def _get_validation_client(self) -> DataplaneClient:
        """Get validation client, creating it if needed (lazy initialization)."""
        if self._validation_client is None:
            self._validation_client = DataplaneClient(
                self.validation_url,
                auth=(
                    self.credentials.validation.username,
                    self.credentials.validation.password.get_secret_value(),
                ),
            )
        return self._validation_client

    def _prepare_sync_content(
        self, config_context: HAProxyConfigContext
    ) -> Tuple[Dict[str, str], Dict[str, str], Dict[str, str]]:
        """Prepare content for synchronization."""
        return (
            {rc.filename: rc.content for rc in config_context.rendered_maps},
            {rc.filename: rc.content for rc in config_context.rendered_certificates},
            {rc.filename: rc.content for rc in config_context.rendered_files},
        )

    def _update_production_clients(self, new_urls: List[str]) -> None:
        """Update production clients based on current URLs.

        This method handles dynamic HAProxy pod lifecycle by:
        - Creating clients for newly discovered URLs
        - Removing clients for URLs that are no longer present
        - Preserving existing clients for stable URLs to maintain connection pooling

        Args:
            new_urls: Current list of production HAProxy URLs
        """
        # Remove clients for URLs that are no longer present
        removed_urls = set(self._production_clients.keys()) - set(new_urls)
        for url in removed_urls:
            # Simply remove the client - the underlying httpx client will be cleaned up
            # when the DataplaneClient is garbage collected
            del self._production_clients[url]
            logger.debug(f"Removed cached client for {url}")

        # Create clients for new URLs
        new_urls_set = set(new_urls)
        existing_urls = set(self._production_clients.keys())
        newly_added_urls = new_urls_set - existing_urls

        for url in newly_added_urls:
            self._production_clients[url] = DataplaneClient(
                url,
                auth=(
                    self.credentials.dataplane.username,
                    self.credentials.dataplane.password.get_secret_value(),
                ),
            )
            logger.debug(f"Created cached client for {url}")

        # Update the production URLs list
        self.production_urls = new_urls

    def add_production_url(self, url: str) -> None:
        """Add a single production URL and create its client.

        Args:
            url: The production HAProxy dataplane URL to add
        """
        if url not in self._production_clients:
            self._production_clients[url] = DataplaneClient(
                url,
                auth=(
                    self.credentials.dataplane.username,
                    self.credentials.dataplane.password.get_secret_value(),
                ),
            )
            logger.debug(f"➕ Added production client for {url}")

            # Update the URLs list
            if url not in self.production_urls:
                self.production_urls.append(url)

    def remove_production_url(self, url: str) -> None:
        """Remove a single production URL and cleanup its client.

        Args:
            url: The production HAProxy dataplane URL to remove
        """
        if url in self._production_clients:
            # Remove the client
            del self._production_clients[url]
            logger.debug(f"➖ Removed production client for {url}")

            # Update the URLs list
            if url in self.production_urls:
                self.production_urls.remove(url)

    async def _sync_content_to_client(
        self,
        client: DataplaneClient,
        maps: Dict[str, str],
        certificates: Dict[str, str],
        files: Dict[str, str],
        url: str,
    ) -> None:
        """Sync all content types to a single client."""
        if maps:
            logger.debug(f"Syncing {len(maps)} maps to {url}")
            await client.sync_maps(maps)

        if certificates:
            logger.debug(f"Syncing {len(certificates)} certificates to {url}")
            await client.sync_certificates(certificates)

        if files:
            logger.debug(f"Syncing {len(files)} files to {url}")
            await client.sync_files(files)

    async def _validate_configuration(self, config: str) -> None:
        """Validate configuration using the validation instance."""
        logger.debug(f"Validating configuration at {self.validation_url}")
        try:
            validation_client = self._get_validation_client()
            await validation_client.validate_configuration(config)
        except Exception as e:
            raise ValidationError(f"Configuration validation failed: {e}") from e

    def _compare_nested_elements(
        self,
        current_nested: Dict[str, Any],
        new_nested: Dict[str, Any],
        section_type: ConfigSectionType,
        section_name: str,
        changes: List[ConfigChange],
    ) -> None:
        """Compare all nested elements within a section.

        This method compares nested configuration elements like servers, ACLs,
        HTTP request rules, etc. within backends, frontends, and defaults sections.

        Args:
            current_nested: Current nested elements for this section
            new_nested: New nested elements for this section
            section_type: Type of the parent section
            section_name: Name of the parent section
            changes: List to append detected changes to
        """
        # Get element mappings from registry
        elements_to_compare = _SECTION_ELEMENTS.get(section_type, [])

        # Compare each type of nested element
        for attr_name, element_type, is_named in elements_to_compare:
            # Get nested element lists from the nested storage
            current_items = current_nested.get(attr_name, []) or []
            new_items = new_nested.get(attr_name, []) or []

            # Ensure we have lists
            if not isinstance(current_items, list):
                current_items = []
            if not isinstance(new_items, list):
                new_items = []

            self._compare_element_list(
                current_items,
                new_items,
                element_type,
                section_type,
                section_name,
                changes,
                is_named,
            )

    def _compare_element_list(
        self,
        current_items: List[Any],
        new_items: List[Any],
        element_type: ConfigElementType,
        section_type: ConfigSectionType,
        section_name: str,
        changes: List[ConfigChange],
        is_named: bool,
    ) -> None:
        """Compare element lists using either named or ordered strategy.

        Args:
            current_items: Current list of elements
            new_items: New list of elements
            element_type: Type of the nested element
            section_type: Type of the parent section
            section_name: Name of the parent section
            changes: List to append detected changes to
            is_named: If True, use named comparison; if False, use ordered comparison
        """
        if is_named:
            self._compare_by_name(
                current_items,
                new_items,
                element_type,
                section_type,
                section_name,
                changes,
            )
        else:
            self._compare_by_order(
                current_items,
                new_items,
                element_type,
                section_type,
                section_name,
                changes,
            )

    def _compare_by_name(
        self,
        current_items: List[Any],
        new_items: List[Any],
        element_type: ConfigElementType,
        section_type: ConfigSectionType,
        section_name: str,
        changes: List[ConfigChange],
    ) -> None:
        """Compare named nested elements like servers or ACLs."""
        # Build dictionaries by name for efficient comparison
        current_dict = {}
        for item in current_items:
            if hasattr(item, "name") and item.name:
                current_dict[item.name] = item
            elif hasattr(item, "id") and item.id:
                current_dict[item.id] = item

        new_dict = {}
        for item in new_items:
            if hasattr(item, "name") and item.name:
                new_dict[item.name] = item
            elif hasattr(item, "id") and item.id:
                new_dict[item.id] = item

        current_names = set(current_dict.keys())
        new_names = set(new_dict.keys())

        # Deletions
        for name in current_names - new_names:
            changes.append(
                ConfigChange.create_element_change(
                    change_type=ConfigChangeType.DELETE,
                    section_type=section_type,
                    section_name=section_name,
                    element_type=element_type,
                    element_id=name,
                    old_config=current_dict[name],
                )
            )

        # Additions
        for name in new_names - current_names:
            changes.append(
                ConfigChange.create_element_change(
                    change_type=ConfigChangeType.CREATE,
                    section_type=section_type,
                    section_name=section_name,
                    element_type=element_type,
                    element_id=name,
                    new_config=new_dict[name],
                )
            )

        # Modifications
        for name in current_names & new_names:
            if _to_dict_safe(current_dict[name]) != _to_dict_safe(new_dict[name]):
                changes.append(
                    ConfigChange.create_element_change(
                        change_type=ConfigChangeType.UPDATE,
                        section_type=section_type,
                        section_name=section_name,
                        element_type=element_type,
                        element_id=name,
                        old_config=current_dict[name],
                        new_config=new_dict[name],
                    )
                )

    def _compare_by_order(
        self,
        current_items: List[Any],
        new_items: List[Any],
        element_type: ConfigElementType,
        section_type: ConfigSectionType,
        section_name: str,
        changes: List[ConfigChange],
    ) -> None:
        """Compare ordered nested elements like HTTP request rules."""
        # Compare lists element by element
        max_len = max(len(current_items), len(new_items))

        for i in range(max_len):
            if i < len(current_items) and i < len(new_items):
                # Both exist - check for modifications
                if _to_dict_safe(current_items[i]) != _to_dict_safe(new_items[i]):
                    changes.append(
                        ConfigChange(
                            change_type=ConfigChangeType.UPDATE,
                            section_type=section_type,
                            section_name=section_name,
                            element_type=element_type,
                            element_index=i,
                            old_config=current_items[i],
                            new_config=new_items[i],
                        )
                    )
            elif i < len(new_items):
                # New element added
                changes.append(
                    ConfigChange(
                        change_type=ConfigChangeType.CREATE,
                        section_type=section_type,
                        section_name=section_name,
                        element_type=element_type,
                        element_index=i,
                        new_config=new_items[i],
                    )
                )
            else:
                # Element removed (current has more elements than new)
                changes.append(
                    ConfigChange(
                        change_type=ConfigChangeType.DELETE,
                        section_type=section_type,
                        section_name=section_name,
                        element_type=element_type,
                        element_index=i,
                        old_config=current_items[i],
                    )
                )

    def _analyze_config_changes(
        self, current: Dict[str, Any], new: Dict[str, Any]
    ) -> List[ConfigChange]:
        """Analyze two structured configurations and return list of actionable changes.

        This method compares HAProxy configuration sections and returns a list of
        ConfigChange objects that can be applied using granular dataplane API endpoints.

        Args:
            current: Current structured configuration
            new: New structured configuration

        Returns:
            List of ConfigChange objects representing the required changes
        """
        changes: List[ConfigChange] = []

        # Compare backends
        current_backends = {
            b.name: b for b in current.get("backends", []) if hasattr(b, "name")
        }
        new_backends = {
            b.name: b for b in new.get("backends", []) if hasattr(b, "name")
        }

        current_names = set(current_backends.keys())
        new_names = set(new_backends.keys())

        # Backend deletions
        for name in current_names - new_names:
            changes.append(
                ConfigChange(
                    change_type=ConfigChangeType.DELETE,
                    section_type=ConfigSectionType.BACKEND,
                    section_name=name,
                    old_config=current_backends[name],
                )
            )

        # Backend additions
        for name in new_names - current_names:
            changes.append(
                ConfigChange(
                    change_type=ConfigChangeType.CREATE,
                    section_type=ConfigSectionType.BACKEND,
                    section_name=name,
                    new_config=new_backends[name],
                )
            )

        # Backend modifications
        for name in current_names & new_names:
            if _to_dict_safe(current_backends[name]) != _to_dict_safe(
                new_backends[name]
            ):
                changes.append(
                    ConfigChange(
                        change_type=ConfigChangeType.UPDATE,
                        section_type=ConfigSectionType.BACKEND,
                        section_name=name,
                        new_config=new_backends[name],
                        old_config=current_backends[name],
                    )
                )

            # Compare nested elements within existing backends
            current_nested = (
                current.get("nested_elements", {}).get("backends", {}).get(name, {})
            )
            new_nested = (
                new.get("nested_elements", {}).get("backends", {}).get(name, {})
            )
            self._compare_nested_elements(
                current_nested, new_nested, ConfigSectionType.BACKEND, name, changes
            )

        # Compare frontends
        current_frontends = {
            f.name: f for f in current.get("frontends", []) if hasattr(f, "name")
        }
        new_frontends = {
            f.name: f for f in new.get("frontends", []) if hasattr(f, "name")
        }

        current_names = set(current_frontends.keys())
        new_names = set(new_frontends.keys())

        # Frontend deletions
        for name in current_names - new_names:
            changes.append(
                ConfigChange(
                    change_type=ConfigChangeType.DELETE,
                    section_type=ConfigSectionType.FRONTEND,
                    section_name=name,
                    old_config=current_frontends[name],
                )
            )

        # Frontend additions
        for name in new_names - current_names:
            changes.append(
                ConfigChange(
                    change_type=ConfigChangeType.CREATE,
                    section_type=ConfigSectionType.FRONTEND,
                    section_name=name,
                    new_config=new_frontends[name],
                )
            )

        # Frontend modifications
        for name in current_names & new_names:
            if _to_dict_safe(current_frontends[name]) != _to_dict_safe(
                new_frontends[name]
            ):
                changes.append(
                    ConfigChange(
                        change_type=ConfigChangeType.UPDATE,
                        section_type=ConfigSectionType.FRONTEND,
                        section_name=name,
                        new_config=new_frontends[name],
                        old_config=current_frontends[name],
                    )
                )

            # Compare nested elements within existing frontends
            current_nested = (
                current.get("nested_elements", {}).get("frontends", {}).get(name, {})
            )
            new_nested = (
                new.get("nested_elements", {}).get("frontends", {}).get(name, {})
            )
            self._compare_nested_elements(
                current_nested, new_nested, ConfigSectionType.FRONTEND, name, changes
            )

        # Compare defaults sections
        current_defaults = current.get("defaults", [])
        new_defaults = new.get("defaults", [])

        # For defaults sections, we compare by name (if available) or fallback to index
        for i, new_def in enumerate(new_defaults):
            if i < len(current_defaults):
                # Use the name from the new defaults object if available, otherwise fallback to index-based name
                section_name = getattr(new_def, "name", None) or f"defaults-{i}"

                # Existing defaults section - check if it needs updating
                if _to_dict_safe(current_defaults[i]) != _to_dict_safe(new_def):
                    changes.append(
                        ConfigChange(
                            change_type=ConfigChangeType.UPDATE,
                            section_type=ConfigSectionType.DEFAULTS,
                            section_name=section_name,
                            new_config=new_def,
                            old_config=current_defaults[i],
                        )
                    )

                # Skip nested element comparison for defaults sections
                # HAProxy Dataplane API v3 limitation: defaults sections don't support nested
                # element endpoints (they return HTTP 501). Defaults are handled as atomic units
                # and any changes trigger a full section update using full_section=true.

        # Compare global section
        current_global = current.get("global")
        new_global = new.get("global")

        if current_global and new_global:
            if _to_dict_safe(current_global) != _to_dict_safe(new_global):
                changes.append(
                    ConfigChange(
                        change_type=ConfigChangeType.UPDATE,
                        section_type=ConfigSectionType.GLOBAL,
                        section_name="global",
                        new_config=new_global,
                        old_config=current_global,
                    )
                )
        elif new_global and not current_global:
            changes.append(
                ConfigChange(
                    change_type=ConfigChangeType.CREATE,
                    section_type=ConfigSectionType.GLOBAL,
                    section_name="global",
                    new_config=new_global,
                )
            )
        elif current_global and not new_global:
            changes.append(
                ConfigChange(
                    change_type=ConfigChangeType.DELETE,
                    section_type=ConfigSectionType.GLOBAL,
                    section_name="global",
                    old_config=current_global,
                )
            )

        # Helper function for named sections
        def analyze_named_sections(section_key: str, section_type: ConfigSectionType):
            """Analyze named configuration sections for changes."""
            current_sections = {
                s.name: s
                for s in current.get(section_key, [])
                if hasattr(s, "name") and s.name
            }
            new_sections = {
                s.name: s
                for s in new.get(section_key, [])
                if hasattr(s, "name") and s.name
            }

            current_names = set(current_sections.keys())
            new_names = set(new_sections.keys())

            # Deletions
            for name in current_names - new_names:
                changes.append(
                    ConfigChange(
                        change_type=ConfigChangeType.DELETE,
                        section_type=section_type,
                        section_name=name,
                        old_config=current_sections[name],
                    )
                )

            # Additions
            for name in new_names - current_names:
                changes.append(
                    ConfigChange(
                        change_type=ConfigChangeType.CREATE,
                        section_type=section_type,
                        section_name=name,
                        new_config=new_sections[name],
                    )
                )

            # Modifications
            for name in current_names & new_names:
                if _to_dict_safe(current_sections[name]) != _to_dict_safe(
                    new_sections[name]
                ):
                    changes.append(
                        ConfigChange(
                            change_type=ConfigChangeType.UPDATE,
                            section_type=section_type,
                            section_name=name,
                            new_config=new_sections[name],
                            old_config=current_sections[name],
                        )
                    )

        # Analyze all named sections
        analyze_named_sections("userlists", ConfigSectionType.USERLIST)
        analyze_named_sections("caches", ConfigSectionType.CACHE)
        analyze_named_sections("mailers", ConfigSectionType.MAILERS)
        analyze_named_sections("resolvers", ConfigSectionType.RESOLVER)
        analyze_named_sections("peers", ConfigSectionType.PEER)
        analyze_named_sections("fcgi_apps", ConfigSectionType.FCGI_APP)
        analyze_named_sections("http_errors", ConfigSectionType.HTTP_ERRORS)
        analyze_named_sections("rings", ConfigSectionType.RING)
        analyze_named_sections("log_forwards", ConfigSectionType.LOG_FORWARD)
        analyze_named_sections("programs", ConfigSectionType.PROGRAM)

        return changes

    def _compare_structured_configs(
        self, current: Dict[str, Any], new: Dict[str, Any]
    ) -> List[str]:
        """Compare two structured configurations and return list of changes.

        This method performs an optimized comparison of HAProxy configuration sections
        including backends, frontends, defaults, global, and all other sections.

        Performance considerations:
        - For large configurations (>100 backends/frontends), this method may consume
          significant memory as it loads all configuration sections into memory
        - Early exit after MAX_CONFIG_COMPARISON_CHANGES changes to avoid expensive
          deep comparisons when many changes are detected
        - Uses xxHash-based serialization with defensive error handling

        Args:
            current: Current structured configuration
            new: New structured configuration

        Returns:
            List of change descriptions, empty if configs are identical
        """
        start_time = time.time()
        changes: List[str] = []
        max_changes_before_exit = MAX_CONFIG_COMPARISON_CHANGES

        # Compare backends - optimized with dict comprehensions
        current_backends = {
            b.name: _to_dict_safe(b)
            for b in current.get("backends", [])
            if hasattr(b, "name")
        }
        new_backends = {
            b.name: _to_dict_safe(b)
            for b in new.get("backends", [])
            if hasattr(b, "name")
        }

        # Find changes in backends efficiently
        current_names = set(current_backends.keys())
        new_names = set(new_backends.keys())

        changes.extend(f"remove backend {name}" for name in current_names - new_names)
        if _check_early_exit_condition(changes, max_changes_before_exit):
            return changes

        changes.extend(f"add backend {name}" for name in new_names - current_names)
        if _check_early_exit_condition(changes, max_changes_before_exit):
            return changes

        changes.extend(
            f"modify backend {name}"
            for name in current_names & new_names
            if current_backends[name] != new_backends[name]
        )
        if _check_early_exit_condition(changes, max_changes_before_exit):
            return changes

        # Compare frontends - same optimization
        current_frontends = {
            f.name: _to_dict_safe(f)
            for f in current.get("frontends", [])
            if hasattr(f, "name")
        }
        new_frontends = {
            f.name: _to_dict_safe(f)
            for f in new.get("frontends", [])
            if hasattr(f, "name")
        }

        current_names = set(current_frontends.keys())
        new_names = set(new_frontends.keys())

        changes.extend(f"remove frontend {name}" for name in current_names - new_names)
        if _check_early_exit_condition(changes, max_changes_before_exit):
            return changes

        changes.extend(f"add frontend {name}" for name in new_names - current_names)
        if _check_early_exit_condition(changes, max_changes_before_exit):
            return changes

        changes.extend(
            f"modify frontend {name}"
            for name in current_names & new_names
            if current_frontends[name] != new_frontends[name]
        )
        if _check_early_exit_condition(changes, max_changes_before_exit):
            return changes

        # Compare defaults sections
        current_defaults = [_to_dict_safe(d) for d in current.get("defaults", [])]
        new_defaults = [_to_dict_safe(d) for d in new.get("defaults", [])]

        if len(current_defaults) != len(new_defaults):
            changes.append(
                f"defaults count changed from {len(current_defaults)} to {len(new_defaults)}"
            )
        else:
            changes.extend(
                f"modify defaults section {i}"
                for i, (curr, new_def) in enumerate(zip(current_defaults, new_defaults))
                if curr != new_def
            )

        # Helper function to compare named sections (similar to backends/frontends)
        def compare_named_sections(section_name: str) -> bool:
            """Compare named configuration sections and return True if early exit needed."""
            nonlocal changes
            try:
                current_sections = {
                    s.name: _to_dict_safe(s)
                    for s in current.get(section_name, [])
                    if hasattr(s, "name") and s.name
                }
                new_sections = {
                    s.name: _to_dict_safe(s)
                    for s in new.get(section_name, [])
                    if hasattr(s, "name") and s.name
                }

                current_names = set(current_sections.keys())
                new_names = set(new_sections.keys())

                changes.extend(
                    f"remove {section_name[:-1]} {name}"
                    for name in current_names - new_names
                )
                if _check_early_exit_condition(changes, max_changes_before_exit):
                    return True

                changes.extend(
                    f"add {section_name[:-1]} {name}"
                    for name in new_names - current_names
                )
                if _check_early_exit_condition(changes, max_changes_before_exit):
                    return True

                changes.extend(
                    f"modify {section_name[:-1]} {name}"
                    for name in current_names & new_names
                    if current_sections[name] != new_sections[name]
                )
                return _check_early_exit_condition(changes, max_changes_before_exit)
            except Exception as e:
                logger.debug(f"Error comparing {section_name}: {type(e).__name__}: {e}")
                changes.append(f"error comparing {section_name}: {type(e).__name__}")
                return _check_early_exit_condition(changes, max_changes_before_exit)

        # Helper function to compare list sections (similar to defaults)
        def compare_list_sections(section_name: str) -> bool:
            """Compare list configuration sections and return True if early exit needed."""
            nonlocal changes
            try:
                current_list = [_to_dict_safe(s) for s in current.get(section_name, [])]
                new_list = [_to_dict_safe(s) for s in new.get(section_name, [])]

                if len(current_list) != len(new_list):
                    changes.append(
                        f"{section_name} count changed from {len(current_list)} to {len(new_list)}"
                    )
                    return _check_early_exit_condition(changes, max_changes_before_exit)
                else:
                    changes.extend(
                        f"modify {section_name} section {i}"
                        for i, (curr, new_item) in enumerate(
                            zip(current_list, new_list)
                        )
                        if curr != new_item
                    )
                    return _check_early_exit_condition(changes, max_changes_before_exit)
            except Exception as e:
                logger.debug(f"Error comparing {section_name}: {type(e).__name__}: {e}")
                changes.append(f"error comparing {section_name}: {type(e).__name__}")
                return _check_early_exit_condition(changes, max_changes_before_exit)

        # Compare all named sections
        if compare_named_sections("userlists"):
            return changes

        if compare_named_sections("caches"):
            return changes

        if compare_named_sections("mailers"):
            return changes

        if compare_named_sections("resolvers"):
            return changes

        if compare_named_sections("peers"):
            return changes

        if compare_named_sections("fcgi_apps"):
            return changes

        if compare_named_sections("http_errors"):
            return changes

        if compare_named_sections("rings"):
            return changes

        if compare_named_sections("log_forwards"):
            return changes

        if compare_named_sections("programs"):
            return changes

        # Compare global section
        current_global = _to_dict_safe(current.get("global"))
        new_global = _to_dict_safe(new.get("global"))

        if current_global and new_global:
            if current_global != new_global:
                changes.append("modify global")
        elif new_global and not current_global:
            changes.append("add global")
        elif current_global and not new_global:
            changes.append("remove global")

        # Log comparison performance
        elapsed = time.time() - start_time
        logger.debug(
            f"⏱️ Structured config comparison took {elapsed:.3f}s, found {len(changes)} changes"
        )

        # Record metrics
        metrics = get_metrics_collector()
        if hasattr(metrics, "record_custom_metric"):
            metrics.record_custom_metric("structured_comparison_time", elapsed)
            metrics.record_custom_metric("structured_changes_count", len(changes))

        return changes

    async def _deploy_to_single_instance(
        self,
        url: str,
        config: str,
        maps_to_sync: Dict[str, str],
        certificates_to_sync: Dict[str, str],
        files_to_sync: Dict[str, str],
        validation_structured: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Deploy to a single production instance with structured comparison.

        Returns:
            Dict with keys: method, version
        """
        client = self._production_clients[url]

        # Sync auxiliary content first (maps, certs, files)
        await self._sync_content_to_client(
            client, maps_to_sync, certificates_to_sync, files_to_sync, url
        )

        # Fetch current structured config from production instance
        try:
            production_structured = await client.fetch_structured_configuration()

            # Analyze structured configurations to get actionable changes
            config_changes = self._analyze_config_changes(
                production_structured, validation_structured
            )

            if not config_changes:
                # No changes needed - skip deployment
                logger.debug(f"⏭️  No structural changes for {url}, skipping deployment")
                return {"method": "skipped", "version": "unchanged"}
            else:
                # Changes detected - use structured deployment
                change_descriptions = [str(change) for change in config_changes]
                logger.debug(
                    f"📝 {len(config_changes)} changes detected for {url}: {', '.join(change_descriptions[:5])}"
                )

                try:
                    version = await client.deploy_structured_configuration(
                        config_changes
                    )
                    return {"method": "structured", "version": version}
                except DataplaneAPIError as structured_error:
                    # If structured deployment fails, fall back to raw deployment
                    logger.warning(
                        f"⚠️  Structured deployment failed for {url}, falling back to raw: {structured_error}"
                    )

                    # Record structured deployment failure metrics
                    metrics = get_metrics_collector()
                    metrics.increment_dataplane_fallback("structured_to_raw")

                    version = await client.deploy_configuration(config)
                    return {"method": "raw_fallback", "version": version}

        except Exception as fetch_error:
            # Fallback to conditional deployment if structured comparison fails
            logger.warning(
                f"⚠️  Structured comparison failed for {url}, falling back to conditional: {fetch_error}"
            )

            # Record fallback metrics
            metrics = get_metrics_collector()
            metrics.increment_dataplane_fallback("structured_to_conditional")

            try:
                version = await client.deploy_configuration_conditionally(config)
                return {"method": "conditional", "version": version}
            except Exception as conditional_error:
                # Final fallback to regular deployment
                logger.warning(
                    f"⚠️  Conditional deployment also failed for {url}, using regular deployment: {conditional_error}"
                )

                # Record double fallback metrics
                metrics.increment_dataplane_fallback("conditional_to_regular")

                version = await client.deploy_configuration(config)
                return {"method": "fallback", "version": version}

    def _handle_deployment_error(
        self, url: str, error: Exception, config: str, results: Dict[str, Any]
    ) -> None:
        """Handle deployment error with enhanced logging."""
        self.deployment_history.record(url, "unknown", False, str(error))
        results["failed"] += 1
        results["errors"].append(f"{url}: {error}")

        error_msg = f"❌ Failed to deploy to {url}: {error}"
        if isinstance(
            error, DataplaneAPIError
        ) and "Configuration context around error:" in str(error):
            logger.error(error_msg)
        else:
            try:
                error_line, error_context = parse_validation_error_details(
                    str(error), config
                )
                if error_context:
                    error_msg += (
                        f"\n\nConfiguration context around error:\n{error_context}"
                    )
            except Exception as parse_error:
                # Broad exception catch is necessary here because parse_validation_error_details
                # calls extract_config_context which performs string operations on user-provided
                # configuration content that may contain unexpected characters or formats that
                # could raise various exceptions (UnicodeError, IndexError, etc.). We must ensure
                # that error parsing failure doesn't mask the original deployment error.
                logger.debug(
                    f"Could not parse validation error details: {type(parse_error).__name__}: {parse_error}"
                )
            logger.error(error_msg)

    async def sync_configuration(
        self, config_context: HAProxyConfigContext
    ) -> Dict[str, Any]:
        """Synchronize configuration to all endpoints with validation-first deployment.

        This method implements an improved approach that minimizes HAProxy reloads:
        1. Sync maps/certs/files to validation instance and validate config
        2. Deploy to production instances only if configuration changed
        3. Use structured deployment with automatic fallbacks to avoid unnecessary reloads

        Args:
            config_context: The rendered configuration context
        """
        if not config_context.rendered_config:
            raise DataplaneAPIError("No rendered HAProxy configuration available")

        config = config_context.rendered_config.content
        maps_to_sync, certificates_to_sync, files_to_sync = self._prepare_sync_content(
            config_context
        )

        # Update production clients to handle dynamic URL changes
        self._update_production_clients(self.production_urls)

        # Step 1: Sync content to validation instance and validate
        logger.debug("🔍 Validating configuration and syncing auxiliary content")
        validation_client = self._get_validation_client()
        await self._sync_content_to_client(
            validation_client,
            maps_to_sync,
            certificates_to_sync,
            files_to_sync,
            "validation instance",
        )
        await self._validate_configuration(config)

        # Step 2: Deploy config to validation instance and fetch structured components
        logger.debug(
            "📤 Deploying config to validation instance for structured comparison"
        )
        await validation_client.deploy_configuration(config)

        # Fetch structured config from validation instance
        logger.debug("🔍 Fetching structured configuration from validation instance")
        validation_structured = await validation_client.fetch_structured_configuration()

        # Step 3: Deploy to production instances using structured comparison
        results: Dict[str, Any] = {
            "successful": 0,
            "failed": 0,
            "skipped": 0,
            "errors": [],
        }

        logger.debug(
            f"🚀 Deploying to {len(self.production_urls)} production instances"
        )

        # Create deployment tasks for parallel execution
        deployment_tasks = []
        for url in self.production_urls:
            task = self._deploy_to_single_instance(
                url,
                config,
                maps_to_sync,
                certificates_to_sync,
                files_to_sync,
                validation_structured,
            )
            deployment_tasks.append(task)

        # Execute all deployments in parallel
        deployment_results = await asyncio.gather(
            *deployment_tasks, return_exceptions=True
        )

        # Process results
        for url, result in zip(self.production_urls, deployment_results):
            if isinstance(result, Exception):
                # Task failed with exception
                self._handle_deployment_error(url, result, config, results)
            elif isinstance(result, dict):
                # Successful result
                if result["method"] == "skipped":
                    results["skipped"] += 1
                else:
                    results["successful"] += 1

                    method_emojis = {
                        "structured": "🏗️",
                        "conditional": "✅",
                        "raw_fallback": "🔄",
                        "fallback": "🔄",
                    }
                    method_emoji = method_emojis.get(result["method"], "✅")
                    logger.info(
                        f"{method_emoji} Deployed to {url} ({result['method']}), version: {result['version']}"
                    )

                self.deployment_history.record(url, result["version"], True)
            else:
                # Unexpected result type
                error_msg = f"Unexpected result type from deployment: {type(result)}"
                self._handle_deployment_error(
                    url, Exception(error_msg), config, results
                )

        # Enhanced logging with skip information
        total_instances = len(self.production_urls)
        if results["successful"] > 0:
            # Log at INFO when we actually deployed something
            logger.info(
                f"🎯 Sync complete: {results['successful']} deployed, "
                f"{results['skipped']} skipped (unchanged), "
                f"{results['failed']} failed out of {total_instances} instances"
            )
        elif results["failed"] > 0:
            # Log at INFO when there were failures (important to know)
            logger.info(
                f"Sync complete: {results['successful']} successful, {results['failed']} failed"
            )
        else:
            # Log at DEBUG when nothing changed (all skipped)
            logger.debug(
                f"🎯 Sync complete: {results['successful']} deployed, "
                f"{results['skipped']} skipped (unchanged), "
                f"{results['failed']} failed out of {total_instances} instances"
            )

        return results
