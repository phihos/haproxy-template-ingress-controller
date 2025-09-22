"""
Adapter module for HAProxy Dataplane API operations.

This module serves as the single point of contact between the dataplane package
and the generated haproxy_dataplane_v3 client. It provides:

- Centralized API access control (only this module imports from generated client)
- Automatic retry logic for 409 (Conflict) responses with exponential backoff
- Uniform error handling and response parsing across all API operations
- Generic APIResponse[T] interface with reload information
- Clean separation between Response objects (internal) and APIResponse objects (external)

All dataplane modules should import from this adapter instead of directly
from haproxy_dataplane_v3.api.* modules.
"""

import asyncio
import base64
import functools
import json
import logging
from dataclasses import dataclass
from typing import (
    TYPE_CHECKING,
    Any,
    Awaitable,
    Callable,
    Generic,
    ParamSpec,
    Protocol,
    TypeVar,
    Union,
    cast,
)
from typing_extensions import TypeGuard

import httpx
from haproxy_dataplane_v3 import AuthenticatedClient, Client
from haproxy_dataplane_v3.api.acl import (
    create_acl_backend as _create_acl_backend,
    create_acl_frontend as _create_acl_frontend,
    delete_acl_backend as _delete_acl_backend,
    delete_acl_frontend as _delete_acl_frontend,
    get_all_acl_backend as _get_all_acl_backend,
    get_all_acl_frontend as _get_all_acl_frontend,
    replace_acl_backend as _replace_acl_backend,
    replace_acl_frontend as _replace_acl_frontend,
)

from haproxy_dataplane_v3.api.acl_runtime import (
    add_payload_runtime_acl as _add_payload_runtime_acl,
    delete_services_haproxy_runtime_acls_parent_name_entries_id as _delete_services_haproxy_runtime_acls_parent_name_entries_id,
    get_services_haproxy_runtime_acls_parent_name_entries_id as _get_services_haproxy_runtime_acls_parent_name_entries_id,
    post_services_haproxy_runtime_acls_parent_name_entries as _post_services_haproxy_runtime_acls_parent_name_entries,
)

from haproxy_dataplane_v3.api.backend import (
    create_backend as _create_backend,
    delete_backend as _delete_backend,
    get_backends as _get_backends,
    replace_backend as _replace_backend,
)
from haproxy_dataplane_v3.api.backend_switching_rule import (
    get_backend_switching_rules as _get_all_backend_switching_rules,
    create_backend_switching_rule as _create_backend_switching_rule,
    delete_backend_switching_rule as _delete_backend_switching_rule,
    replace_backend_switching_rule as _replace_backend_switching_rule,
)

from haproxy_dataplane_v3.api.bind import (
    create_bind_frontend as _create_bind_frontend,
    delete_bind_frontend as _delete_bind_frontend,
    get_all_bind_frontend as _get_all_bind_frontend,
    replace_bind_frontend as _replace_bind_frontend,
)
from haproxy_dataplane_v3.api.cache import (
    create_cache as _create_cache,
    delete_cache as _delete_cache,
    get_caches as _get_caches,
    replace_cache as _replace_cache,
)

from haproxy_dataplane_v3.api.configuration import (
    get_configuration_version as _get_configuration_version,
    get_ha_proxy_configuration as _get_ha_proxy_configuration,
    post_ha_proxy_configuration as _post_ha_proxy_configuration,
)
from haproxy_dataplane_v3.api.defaults import (
    add_defaults_section as _add_defaults_section,
    create_defaults_section as _create_defaults_section,
    delete_defaults_section as _delete_defaults_section,
    get_defaults_section as _get_defaults_section,
    get_defaults_sections as _get_defaults_sections,
    replace_defaults_section as _replace_defaults_section,
)
from haproxy_dataplane_v3.api.fcgi_app import (
    create_fcgi_app as _create_fcgi_app,
    delete_fcgi_app as _delete_fcgi_app,
    get_fcgi_apps as _get_fcgi_apps,
    replace_fcgi_app as _replace_fcgi_app,
)
from haproxy_dataplane_v3.api.filter_ import (
    create_filter_backend as _create_filter_backend,
    create_filter_frontend as _create_filter_frontend,
    delete_filter_backend as _delete_filter_backend,
    delete_filter_frontend as _delete_filter_frontend,
    get_all_filter_backend as _get_all_filter_backend,
    get_all_filter_frontend as _get_all_filter_frontend,
    replace_filter_backend as _replace_filter_backend,
    replace_filter_frontend as _replace_filter_frontend,
)
from haproxy_dataplane_v3.api.frontend import (
    create_frontend as _create_frontend,
    delete_frontend as _delete_frontend,
    get_frontends as _get_frontends,
    replace_frontend as _replace_frontend,
)
from haproxy_dataplane_v3.api.global_ import (
    get_global as _get_global,
    replace_global as _replace_global,
)
from haproxy_dataplane_v3.api.http_errors import (
    create_http_errors_section as _create_http_errors_section,
    delete_http_errors_section as _delete_http_errors_section,
    get_http_errors_sections as _get_http_errors_sections,
    replace_http_errors_section as _replace_http_errors_section,
)
from haproxy_dataplane_v3.api.http_request_rule import (
    create_http_request_rule_backend as _create_http_request_rule_backend,
    create_http_request_rule_frontend as _create_http_request_rule_frontend,
    delete_http_request_rule_backend as _delete_http_request_rule_backend,
    delete_http_request_rule_frontend as _delete_http_request_rule_frontend,
    get_all_http_request_rule_backend as _get_all_http_request_rule_backend,
    get_all_http_request_rule_frontend as _get_all_http_request_rule_frontend,
    replace_http_request_rule_backend as _replace_http_request_rule_backend,
    replace_http_request_rule_frontend as _replace_http_request_rule_frontend,
)
from haproxy_dataplane_v3.api.http_response_rule import (
    create_http_response_rule_backend as _create_http_response_rule_backend,
    create_http_response_rule_frontend as _create_http_response_rule_frontend,
    delete_http_response_rule_backend as _delete_http_response_rule_backend,
    delete_http_response_rule_frontend as _delete_http_response_rule_frontend,
    get_all_http_response_rule_backend as _get_all_http_response_rule_backend,
    get_all_http_response_rule_frontend as _get_all_http_response_rule_frontend,
    replace_http_response_rule_backend as _replace_http_response_rule_backend,
    replace_http_response_rule_frontend as _replace_http_response_rule_frontend,
)

from haproxy_dataplane_v3.api.information import (
    get_haproxy_process_info as _get_haproxy_process_info,
    get_info as _get_info,
)
from haproxy_dataplane_v3.api.log_forward import (
    create_log_forward as _create_log_forward,
    delete_log_forward as _delete_log_forward,
    get_log_forwards as _get_log_forwards,
    replace_log_forward as _replace_log_forward,
)
from haproxy_dataplane_v3.api.log_target import (
    create_log_target_backend as _create_log_target_backend,
    create_log_target_defaults as _create_log_target_defaults,
    create_log_target_frontend as _create_log_target_frontend,
    create_log_target_global as _create_log_target_global,
    create_log_target_log_forward as _create_log_target_log_forward,
    create_log_target_peer as _create_log_target_peer,
    delete_log_target_backend as _delete_log_target_backend,
    delete_log_target_defaults as _delete_log_target_defaults,
    delete_log_target_frontend as _delete_log_target_frontend,
    delete_log_target_global as _delete_log_target_global,
    delete_log_target_log_forward as _delete_log_target_log_forward,
    delete_log_target_peer as _delete_log_target_peer,
    get_all_log_target_backend as _get_all_log_target_backend,
    get_all_log_target_defaults as _get_all_log_target_defaults,
    get_all_log_target_frontend as _get_all_log_target_frontend,
    get_all_log_target_global as _get_all_log_target_global,
    get_all_log_target_log_forward as _get_all_log_target_log_forward,
    get_all_log_target_peer as _get_all_log_target_peer,
    replace_log_target_backend as _replace_log_target_backend,
    replace_log_target_defaults as _replace_log_target_defaults,
    replace_log_target_frontend as _replace_log_target_frontend,
    replace_log_target_global as _replace_log_target_global,
    replace_log_target_log_forward as _replace_log_target_log_forward,
    replace_log_target_peer as _replace_log_target_peer,
)
from haproxy_dataplane_v3.api.mailers import (
    create_mailers_section as _create_mailers_section,
    delete_mailers_section as _delete_mailers_section,
    edit_mailers_section as _edit_mailers_section,
    get_mailers_sections as _get_mailers_sections,
)

from haproxy_dataplane_v3.api.maps import (
    add_map_entry as _add_map_entry,
    delete_runtime_map_entry as _delete_runtime_map_entry,
    get_runtime_map_entry as _get_runtime_map_entry,
    replace_runtime_map_entry as _replace_runtime_map_entry,
)
from haproxy_dataplane_v3.api.peer import (
    create_peer as _create_peer,
    delete_peer as _delete_peer,
    get_peer_sections as _get_peer_sections,
)
from haproxy_dataplane_v3.api.process_manager import (
    create_program as _create_program,
    delete_program as _delete_program,
    get_programs as _get_programs,
    replace_program as _replace_program,
)
from haproxy_dataplane_v3.api.resolver import (
    create_resolver as _create_resolver,
    delete_resolver as _delete_resolver,
    get_resolvers as _get_resolvers,
    replace_resolver as _replace_resolver,
)
from haproxy_dataplane_v3.api.ring import (
    create_ring as _create_ring,
    delete_ring as _delete_ring,
    get_rings as _get_rings,
    replace_ring as _replace_ring,
)

from haproxy_dataplane_v3.api.server import (
    add_runtime_server as _add_runtime_server,
    create_server_backend as _create_server_backend,
    delete_runtime_server as _delete_runtime_server,
    delete_server_backend as _delete_server_backend,
    get_all_runtime_server as _get_all_runtime_server,
    get_all_server_backend as _get_all_server_backend,
    replace_runtime_server as _replace_runtime_server,
    replace_server_backend as _replace_server_backend,
)

from haproxy_dataplane_v3.api.storage import (
    create_storage_general_file as _create_storage_general_file,
    create_storage_map_file as _create_storage_map_file,
    create_storage_ssl_certificate as _create_storage_ssl_certificate,
    delete_storage_general_file as _delete_storage_general_file,
    delete_storage_map as _delete_storage_map,
    delete_storage_ssl_certificate as _delete_storage_ssl_certificate,
    get_all_storage_general_files as _get_all_storage_general_files,
    get_all_storage_map_files as _get_all_storage_map_files,
    get_all_storage_ssl_certificates as _get_all_storage_ssl_certificates,
    get_one_storage_general_file as _get_one_storage_general_file,
    get_one_storage_map as _get_one_storage_map,
    get_one_storage_ssl_certificate as _get_one_storage_ssl_certificate,
    replace_storage_general_file as _replace_storage_general_file,
    replace_storage_map_file as _replace_storage_map_file,
    replace_storage_ssl_certificate as _replace_storage_ssl_certificate,
)

from haproxy_dataplane_v3.api.transactions import (
    commit_transaction as _commit_transaction,
    delete_transaction as _delete_transaction,
    start_transaction as _start_transaction,
)
from haproxy_dataplane_v3.api.userlist import (
    create_userlist as _create_userlist,
    delete_userlist as _delete_userlist,
    get_userlists as _get_userlists,
)
from haproxy_dataplane_v3.models import (
    ACLLines,
    # Configuration section models
    Backend,
    BackendSwitchingRule,
    Bind,
    Cache,
    # Storage models
    CreateStorageGeneralFileBody,
    CreateStorageMapFileBody,
    CreateStorageSSLCertificateBody,
    Defaults,
    Error,
    FcgiApp,
    Filter,
    Frontend,
    GeneralUseFile,
    Global,
    HAProxyInformation,
    HttpErrorsSection,
    HTTPRequestRule,
    HTTPResponseRule,
    # Information models
    Information,
    LogForward,
    LogTarget,
    MailersSection,
    MapFile,
    OneACLFileEntry,
    OneMapEntry,
    PeerSection,
    Program,
    ReplaceRuntimeMapEntryBody,
    ReplaceStorageGeneralFileBody,
    Resolver,
    Ring,
    RuntimeAddServer,
    RuntimeServer,
    # Nested element models
    Server,
    Userlist,
)
from haproxy_dataplane_v3.models import (
    SSLFile,
    SSLFile1,
)
from haproxy_dataplane_v3.types import UNSET, File, Response, Unset

from haproxy_template_ic.constants import DEFAULT_API_TIMEOUT
from haproxy_template_ic.metrics import get_metrics_collector
from haproxy_template_ic.tracing import record_span_event

from .types import DataplaneAPIError, ValidationError

if TYPE_CHECKING:
    from .endpoint import DataplaneEndpoint


# Protocol for types that are not Error - helps MyPy understand Error | T -> T
class NotError(Protocol):
    """Protocol for types that are not Error - enables Union type extraction."""

    pass


# Type variables for generic support
T = TypeVar("T", bound=NotError)  # Constrain T to non-Error types
P = ParamSpec("P")


def is_not_error(value: Error | T) -> TypeGuard[T]:
    """TypeGuard to help MyPy understand Error | T → T transformation."""
    return not isinstance(value, Error)


logger = logging.getLogger(__name__)


@dataclass
class ReloadInfo:
    """Information about HAProxy reload detection.

    Captures reload status from HAProxy Dataplane API operations.
    Any operation that returns HTTP 202 status code triggers a reload.
    """

    reload_id: str | None = None

    @property
    def reload_triggered(self) -> bool:
        """True when reload_id is not None, indicating a reload was triggered."""
        return self.reload_id is not None

    @classmethod
    def from_response(cls, response: Response) -> "ReloadInfo":
        """Extract reload information from HAProxy Dataplane API response.

        HAProxy operations that trigger reloads return HTTP 202 status code
        and include a 'Reload-ID' header with the reload identifier.

        Args:
            response: Response object from haproxy_dataplane_v3 with status_code and headers

        Returns:
            ReloadInfo instance with reload_id if reload was triggered
        """
        reload_id = None

        if response.status_code == 202:
            for header_name in ["Reload-ID", "reload-id", "RELOAD-ID", "reload_id"]:
                reload_id = response.headers.get(header_name)
                if reload_id:
                    break

        return cls(reload_id=reload_id)

    @classmethod
    def combine(cls, *reload_infos: "ReloadInfo") -> "ReloadInfo":
        """Combine multiple ReloadInfo instances using 'any reload wins' logic.

        If any of the provided ReloadInfo instances indicates a reload was triggered,
        the combined result will show reload_triggered=True. The first non-None
        reload_id will be preserved.

        Args:
            *reload_infos: Variable number of ReloadInfo instances to combine

        Returns:
            Combined ReloadInfo instance

        Examples:
            >>> r1 = ReloadInfo()  # No reload
            >>> r2 = ReloadInfo(reload_id="abc123")  # Reload triggered
            >>> combined = ReloadInfo.combine(r1, r2)
            >>> combined.reload_triggered
            True
            >>> combined.reload_id
            'abc123'
        """
        # Find the first reload_id from any ReloadInfo that triggered a reload
        combined_reload_id = None
        for reload_info in reload_infos:
            if reload_info.reload_triggered:
                combined_reload_id = reload_info.reload_id
                break

        return cls(reload_id=combined_reload_id)


@dataclass
class APIResponse(Generic[T]):
    """Unified response container with parsed content and reload information.

    This class provides a consistent interface for all adapter API functions,
    containing both the parsed response data and reload information extracted
    from the HTTP response.

    Type Parameters:
        T: The type of the parsed response content
    """

    content: T
    reload_info: ReloadInfo


logger = logging.getLogger(__name__)


async def _refresh_version_for_retry(kwargs: dict) -> None:
    """Refresh the version parameter for retry attempts on 409 conflicts.

    Args:
        kwargs: Function keyword arguments to update
    """
    # Safety check: only refresh if both endpoint and version are present
    if "endpoint" in kwargs and "version" in kwargs:
        try:
            endpoint = kwargs["endpoint"]
            version_response = await get_configuration_version(endpoint=endpoint)
            new_version = version_response.content
            old_version = kwargs["version"]

            kwargs["version"] = new_version
            logger.debug(
                f"🔄 Refreshed version from {old_version} to {new_version} for retry"
            )

        except Exception as e:
            logger.warning(f"Failed to refresh version for retry: {e}")
            # Continue with original version if refresh fails
    else:
        logger.debug(
            "Skipping version refresh - endpoint or version parameter not found"
        )


def retry_on(
    status: list[int], max_attempts: int = 3, base_delay: float = 1.0
) -> Callable[
    [Callable[P, Awaitable[Response[T] | Error]]],
    Callable[P, Awaitable[Response[T] | Error]],
]:
    """Decorator to retry API operations on specific HTTP status codes.

    Implements exponential backoff and may return Error after exhausted retries.
    The final response (success or failure) is passed to the next decorator in the chain.

    Args:
        status: List of HTTP status codes to retry on (e.g., [409])
        max_attempts: Maximum number of retry attempts (default: 3)
        base_delay: Base delay in seconds for exponential backoff (default: 1.0)
    """

    def decorator(
        func: Callable[P, Awaitable[Response[T] | Error]],
    ) -> Callable[P, Awaitable[Response[T] | Error]]:
        @functools.wraps(func)
        async def wrapper(*args: P.args, **kwargs: P.kwargs) -> Response[T] | Error:
            metrics = get_metrics_collector()
            operation_name = getattr(func, "__name__", "unknown")

            for attempt in range(max_attempts):
                try:
                    response = await func(*args, **kwargs)

                    # Check if retry is needed for Response objects
                    if (
                        hasattr(response, "status_code")
                        and response.status_code in status
                    ):
                        if attempt < max_attempts - 1:  # Not the last attempt
                            # Handle 409 conflicts by refreshing version unconditionally
                            if response.status_code == 409:
                                await _refresh_version_for_retry(kwargs)
                                logger.debug(
                                    f"⚠️ Retrying {operation_name} with fresh version due to 409 conflict, "
                                    f"attempt {attempt + 1}/{max_attempts}"
                                )
                            else:
                                delay = base_delay * (2**attempt)  # Exponential backoff
                                logger.debug(
                                    f"⚠️ Retrying {operation_name} due to status {response.status_code}, "
                                    f"attempt {attempt + 1}/{max_attempts}, waiting {delay}s"
                                )
                                await asyncio.sleep(delay)

                            metrics.record_dataplane_api_request(
                                f"{operation_name}_retry", "attempt"
                            )
                            record_span_event(
                                f"{operation_name}_retry",
                                {
                                    "attempt": attempt + 1,
                                    "status_code": response.status_code,
                                    "delay": 0
                                    if response.status_code == 409
                                    else base_delay * (2**attempt),
                                },
                            )

                            continue

                    # Success or final attempt - return response (Response[T] or Error)
                    if attempt > 0:
                        metrics.record_dataplane_api_request(
                            f"{operation_name}_retry", "success"
                        )
                        record_span_event(
                            f"{operation_name}_retry_success",
                            {
                                "final_attempt": attempt + 1,
                                "total_attempts": max_attempts,
                            },
                        )

                    return response

                except Exception as e:
                    # For unexpected exceptions, re-raise on final attempt
                    if attempt == max_attempts - 1:  # Last attempt
                        raise

                    delay = base_delay * (2**attempt)
                    logger.warning(
                        f"Exception in {operation_name}, attempt {attempt + 1}/{max_attempts}: {e}, "
                        f"waiting {delay}s"
                    )
                    await asyncio.sleep(delay)

            # This should never be reached due to the loop logic above
            raise RuntimeError(f"Unexpected end of retry loop in {operation_name}")

        return wrapper

    return decorator


def handle_dataplane_error(
    operation_type: str = "dataplane",
) -> Callable[
    [Callable[P, Awaitable[Response[Error | T]]]],
    Callable[P, Awaitable[Response[T]]],
]:
    """Decorator to handle dataplane API responses uniformly.

    Takes Response[Error | T] from retry decorator, extracts T from the Union,
    and returns guaranteed Response[T] object (converts Error to raised exception).

    Args:
        operation_type: Type of operation for specialized error handling
                       ("dataplane" for general operations, "configuration" for config operations)
    """

    def decorator(
        func: Callable[P, Awaitable[Response[Error | T]]],
    ) -> Callable[P, Awaitable[Response[T]]]:
        @functools.wraps(func)
        async def wrapper(*args: P.args, **kwargs: P.kwargs) -> Response[T]:
            try:
                # Get Response[Error | T] from the decorated function
                result: Response[Error | T] = await func(*args, **kwargs)

                # Extract endpoint for error reporting
                # For adapter functions, there's no endpoint available since they're pure functions
                # Error reporting will be less specific but functional
                endpoint = "adapter_function"

                # Check if the parsed content is an Error object
                if isinstance(result.parsed, Error):
                    error_obj = result.parsed
                    error_msg = f"{getattr(func, '__name__', 'unknown')} failed"
                    if hasattr(error_obj, "message") and error_obj.message:
                        error_msg += f": {error_obj.message}"
                    if hasattr(error_obj, "code") and error_obj.code:
                        error_msg += f" (HTTP {error_obj.code})"

                    logger.warning(
                        f"Dataplane API error in {getattr(func, '__name__', 'unknown')}: "
                        f"code={getattr(error_obj, 'code', 'unknown')}, "
                        f"message={getattr(error_obj, 'message', 'unknown')}"
                    )

                    raise DataplaneAPIError(
                        error_msg,
                        endpoint=endpoint,
                        operation=getattr(func, "__name__", "unknown"),
                        original_error=None,
                    )

                # At this point, we know result.parsed is T (not Error)
                # We need to create a Response[T] from Response[Error | T]
                # Since response attributes other than parsed remain the same
                if not is_not_error(result.parsed):
                    raise RuntimeError("Error should have been handled above")

                typed_response: Response[T] = Response(
                    status_code=result.status_code,
                    content=result.content,
                    headers=result.headers,
                    parsed=cast(T, result.parsed),  # Type cast after TypeGuard check
                )

                # Apply additional error checking for Response objects based on operation type
                if operation_type == "configuration":
                    # For configuration operations, pass config content if available
                    config_content = kwargs.get("body") if "body" in kwargs else None
                    if config_content is not None and not isinstance(
                        config_content, str
                    ):
                        config_content = str(config_content)
                    check_configuration_response(
                        typed_response,
                        getattr(func, "__name__", "unknown"),
                        endpoint,
                        config_content,
                    )
                    # If check_configuration_response didn't raise, return the original response
                    checked_response = typed_response
                else:
                    # For general dataplane operations
                    checked_response = check_dataplane_response(
                        typed_response, getattr(func, "__name__", "unknown"), endpoint
                    )

                # Return the full Response object (not parsed) for to_api_response decorator
                return checked_response

            except Exception:
                # Let existing error handling in utils.py handle the exception chain
                raise

        return wrapper

    return decorator


def to_api_response() -> Callable[
    [Callable[P, Awaitable[Response[T]]]], Callable[P, Awaitable[APIResponse[T]]]
]:
    """Converts guaranteed Response[T] to APIResponse[T] with reload info.

    This is the outermost decorator that provides the final clean interface,
    converting Response objects to APIResponse objects with embedded reload information.
    """

    def decorator(
        func: Callable[P, Awaitable[Response[T]]],
    ) -> Callable[P, Awaitable[APIResponse[T]]]:
        @functools.wraps(func)
        async def wrapper(*args: P.args, **kwargs: P.kwargs) -> APIResponse[T]:
            response: Response[T] = await func(
                *args, **kwargs
            )  # Guaranteed Response[T]

            # Handle case where parsed content might be None (common for DELETE operations)
            if response.parsed is None:
                # For DELETE operations and other operations that return empty responses,
                # we'll use None as the content since the operation succeeded
                parsed_content = None
            else:
                parsed_content = response.parsed

            return APIResponse(
                content=cast(T, parsed_content),
                reload_info=ReloadInfo.from_response(response),
            )

        return wrapper

    return decorator


def inject_client_for_endpoint():
    """Decorator to inject AuthenticatedClient for a given DataplaneEndpoint.

    This decorator transforms functions that expect a 'client' parameter to accept
    an 'endpoint' parameter instead. The client is created on-the-fly for each call.

    The calling signature changes from:
        func(client: AuthenticatedClient, **kwargs) -> T
    to:
        func(endpoint: DataplaneEndpoint, **kwargs) -> T

    But the decorated function still expects client internally.
    """

    def decorator(func):
        @functools.wraps(func)
        async def wrapper(endpoint: "DataplaneEndpoint", *args: Any, **kwargs: Any):
            auth = (
                endpoint.dataplane_auth.username,
                endpoint.dataplane_auth.password.get_secret_value(),
            )
            auth_string = f"{auth[0]}:{auth[1]}"
            auth_token = base64.b64encode(auth_string.encode()).decode("ascii")

            client = AuthenticatedClient(
                base_url=endpoint.url,  # type: ignore[call-arg]
                token=auth_token,
                prefix="Basic",
                timeout=httpx.Timeout(DEFAULT_API_TIMEOUT),  # type: ignore[call-arg]
            )

            return await func(client=client, *args, **kwargs)

        return wrapper

    return decorator


def with_metrics(operation_name: str):
    """Decorator to add metrics timing to API functions.

    This decorator wraps functions with metrics.time_dataplane_api_operation() context
    to track operation timing. It serves as a replacement for the fetch_with_metrics utility.

    Args:
        operation_name: Name of the operation for metrics tracking

    Returns:
        Decorator that adds metrics timing to the wrapped function
    """

    def decorator(func):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            metrics = get_metrics_collector()
            with metrics.time_dataplane_api_operation(operation_name):
                return await func(*args, **kwargs)

        return wrapper

    return decorator


def api_function(
    retry_status: list[int] | None = None,
    retry_max_attempts: int = 3,
    retry_base_delay: float = 1.0,
    operation_type: str = "dataplane",
    operation_name: str | None = None,
) -> Callable[
    [Callable[P, Awaitable[Response[Error | T]]]],
    Callable[P, Awaitable[APIResponse[T]]],
]:
    """Combined decorator for API functions with endpoint injection and full pipeline.

    This decorator combines all necessary decorators for adapter API functions:
    1. inject_client_for_endpoint - converts endpoint parameter to client
    2. retry_on - retries on specified HTTP status codes
    3. handle_dataplane_error - converts errors to exceptions
    4. to_api_response - wraps result in APIResponse with reload info
    5. with_metrics - adds metrics timing (if operation_name provided)

    Args:
        retry_status: List of HTTP status codes to retry on (default: [409])
        retry_max_attempts: Maximum number of retry attempts (default: 3)
        retry_base_delay: Base delay in seconds for exponential backoff (default: 1.0)
        operation_type: Type of operation for specialized error handling (default: "dataplane")
        operation_name: Operation name for metrics tracking (optional)

    Returns:
        Decorator that transforms raw API functions into endpoint-based APIResponse functions
    """
    if retry_status is None:
        retry_status = [409]

    def decorator(
        func: Callable[..., Awaitable[Response[Error | T]]],
    ) -> Callable[..., Awaitable[APIResponse[T]]]:
        # Apply decorators in reverse order (innermost to outermost)
        # Note: intermediate steps use Any to handle signature transformations
        decorated_func: Any = func
        decorated_func = inject_client_for_endpoint()(decorated_func)
        decorated_func = retry_on(
            status=retry_status,
            max_attempts=retry_max_attempts,
            base_delay=retry_base_delay,
        )(decorated_func)
        decorated_func = handle_dataplane_error(operation_type=operation_type)(
            decorated_func
        )
        decorated_func = to_api_response()(decorated_func)

        # Apply metrics timing if operation_name is provided
        if operation_name:
            decorated_func = with_metrics(operation_name)(decorated_func)

        return decorated_func

    return decorator


# Factory functions removed - all APIs now use explicit wrapper functions for proper IDE support


# ===== Storage API Functions =====
# Explicit wrapper functions for proper IDE support


@api_function()
async def create_storage_general_file(
    *,
    client: AuthenticatedClient | Client,
    body: CreateStorageGeneralFileBody,
) -> Response[Error | GeneralUseFile]:
    return await _create_storage_general_file.asyncio_detailed(
        client=client,
        body=body,
    )


@api_function()
async def create_storage_map_file(
    *,
    client: AuthenticatedClient | Client,
    body: CreateStorageMapFileBody,
) -> Response[Error | MapFile]:
    return await _create_storage_map_file.asyncio_detailed(
        client=client,
        body=body,
    )


@api_function()
async def create_storage_ssl_certificate(
    *,
    client: AuthenticatedClient | Client,
    body: CreateStorageSSLCertificateBody,
    skip_reload: Unset | bool = False,
    force_reload: Unset | bool = False,
) -> Response[Error | SSLFile1]:
    return await _create_storage_ssl_certificate.asyncio_detailed(  # type: ignore[return-value]
        client=client,
        body=body,
        skip_reload=skip_reload,
        force_reload=force_reload,
    )


@api_function()
async def delete_storage_general_file(
    name: str,
    *,
    client: AuthenticatedClient | Client,
) -> Response[Any | Error]:
    return await _delete_storage_general_file.asyncio_detailed(
        name=name,
        client=client,
    )


@api_function()
async def delete_storage_map(
    name: str,
    *,
    client: AuthenticatedClient | Client,
    force_reload: Unset | bool = False,
) -> Response[Any | Error]:
    return await _delete_storage_map.asyncio_detailed(
        name=name,
        client=client,
    )


@api_function()
async def delete_storage_ssl_certificate(
    name: str,
    *,
    client: AuthenticatedClient | Client,
    force_reload: Unset | bool = False,
) -> Response[Error | None]:
    return await _delete_storage_ssl_certificate.asyncio_detailed(
        name=name,
        client=client,
        force_reload=force_reload,
    )


@api_function()
async def get_all_storage_general_files(
    *,
    client: AuthenticatedClient | Client,
) -> Response[Error | list["GeneralUseFile"]]:
    return await _get_all_storage_general_files.asyncio_detailed(
        client=client,
    )


@api_function()
async def get_all_storage_map_files(
    *,
    client: AuthenticatedClient | Client,
) -> Response[Error | list["MapFile"]]:
    return await _get_all_storage_map_files.asyncio_detailed(
        client=client,
    )


@api_function()
async def get_all_storage_ssl_certificates(
    *,
    client: AuthenticatedClient | Client,
) -> Response[Error | list["SSLFile1"]]:
    return await _get_all_storage_ssl_certificates.asyncio_detailed(  # type: ignore[return-value]
        client=client,
    )


@api_function()
async def get_one_storage_general_file(
    name: str,
    *,
    client: AuthenticatedClient | Client,
) -> Response[Error | File]:
    return await _get_one_storage_general_file.asyncio_detailed(
        name=name,
        client=client,
    )


@api_function()
async def get_one_storage_map(
    name: str,
    *,
    client: AuthenticatedClient | Client,
) -> Response[Error | File]:
    return await _get_one_storage_map.asyncio_detailed(
        name=name,
        client=client,
    )


@api_function()
async def get_one_storage_ssl_certificate(
    name: str,
    *,
    client: AuthenticatedClient | Client,
) -> Response[Error | SSLFile]:
    return await _get_one_storage_ssl_certificate.asyncio_detailed(
        name=name,
        client=client,
    )


@api_function()
async def replace_storage_general_file(
    name: str,
    *,
    client: AuthenticatedClient | Client,
    body: ReplaceStorageGeneralFileBody,
    skip_reload: Unset | bool = False,
    force_reload: Unset | bool = False,
) -> Response[Any | Error]:
    return await _replace_storage_general_file.asyncio_detailed(
        name=name,
        client=client,
        body=body,
        skip_reload=skip_reload,
        force_reload=force_reload,
    )


@api_function()
async def replace_storage_map_file(
    name: str,
    *,
    client: AuthenticatedClient | Client,
    body: str,
    skip_reload: Unset | bool = False,
    force_reload: Unset | bool = False,
) -> Response[Any | Error]:
    return await _replace_storage_map_file.asyncio_detailed(
        name=name,
        client=client,
        body=body,
        skip_reload=skip_reload,
        force_reload=force_reload,
    )


@api_function()
async def replace_storage_ssl_certificate(
    name: str,
    *,
    client: AuthenticatedClient | Client,
    body: str,
    skip_reload: Unset | bool = False,
    force_reload: Unset | bool = False,
) -> Response[Error | SSLFile1]:
    return await _replace_storage_ssl_certificate.asyncio_detailed(  # type: ignore[return-value]
        name=name,
        client=client,
        body=body,
        skip_reload=skip_reload,
        force_reload=force_reload,
    )


@api_function(operation_type="configuration")
async def get_configuration_version(
    *,
    client: AuthenticatedClient | Client,
    transaction_id: Unset | str = UNSET,
) -> Response[Error | int]:
    return await _get_configuration_version.asyncio_detailed(
        client=client,
        transaction_id=transaction_id,
    )


@api_function(operation_type="configuration")
async def get_ha_proxy_configuration(
    *,
    client: AuthenticatedClient | Client,
    transaction_id: Unset | str = UNSET,
    version: Unset | int = UNSET,
) -> Response[str]:
    return await _get_ha_proxy_configuration.asyncio_detailed(
        client=client,
        transaction_id=transaction_id,
        version=version,
    )


@api_function(operation_type="configuration")
async def post_haproxy_configuration(
    *,
    client: AuthenticatedClient | Client,
    body: str,
    skip_version: Unset | bool = False,
    skip_reload: Unset | bool = False,
    only_validate: Unset | bool = False,
    version: Unset | int = UNSET,
    force_reload: Unset | bool = False,
    x_runtime_actions: Unset | str = UNSET,
) -> Response[str]:
    return await _post_ha_proxy_configuration.asyncio_detailed(
        client=client,
        body=body,
        skip_version=skip_version,
        skip_reload=skip_reload,
        only_validate=only_validate,
        version=version,
        force_reload=force_reload,
        x_runtime_actions=x_runtime_actions,
    )


# ===== Transaction and Information API Functions =====
# Explicit wrapper functions for proper IDE support


@api_function()
async def commit_transaction(
    id: str,
    *,
    client: AuthenticatedClient | Client,
    force_reload: Unset | bool = False,
) -> Response[Error | Any]:
    return await _commit_transaction.asyncio_detailed(
        id=id,
        client=client,
        force_reload=force_reload,
    )


@api_function()
async def delete_transaction(
    id: str,
    *,
    client: AuthenticatedClient | Client,
) -> Response[Error | None]:
    return await _delete_transaction.asyncio_detailed(
        id=id,
        client=client,
    )


@api_function()
async def start_transaction(
    *,
    client: AuthenticatedClient | Client,
    version: Unset | int = UNSET,
) -> Response[Error | Any]:
    return await _start_transaction.asyncio_detailed(
        client=client,
        version=version,  # type: ignore[arg-type]
    )


@api_function()
async def get_info(
    *,
    client: AuthenticatedClient | Client,
) -> Response[Error | Information]:
    return await _get_info.asyncio_detailed(
        client=client,
    )


@api_function()
async def get_haproxy_process_info(
    *,
    client: AuthenticatedClient | Client,
) -> Response[Error | HAProxyInformation]:
    return await _get_haproxy_process_info.asyncio_detailed(
        client=client,
    )


# Runtime API functions
_RUNTIME_API_FUNCTIONS = {
    "add_payload_runtime_acl": _add_payload_runtime_acl,
    "delete_runtime_acl_file_entry": _delete_services_haproxy_runtime_acls_parent_name_entries_id,
    "get_runtime_acl_file_entry": _get_services_haproxy_runtime_acls_parent_name_entries_id,
    "post_runtime_acl_entry": _post_services_haproxy_runtime_acls_parent_name_entries,
    "add_map_entry": _add_map_entry,
    "delete_runtime_map_entry": _delete_runtime_map_entry,
    "get_runtime_map_entry": _get_runtime_map_entry,
    "replace_runtime_map_entry": _replace_runtime_map_entry,
    "add_runtime_server": _add_runtime_server,
    "delete_runtime_server": _delete_runtime_server,
    "get_runtime_servers": _get_all_runtime_server,
    "replace_runtime_server": _replace_runtime_server,
}


# Runtime API functions (explicit wrappers for IDE support)
@api_function()
async def add_payload_runtime_acl(
    parent_name: str,
    *,
    client: AuthenticatedClient | Client,
    body: list[OneACLFileEntry],
) -> Response[Error | list[OneACLFileEntry]]:
    return await _add_payload_runtime_acl.asyncio_detailed(
        parent_name=parent_name,
        client=client,
        body=body,
    )


@api_function()
async def delete_runtime_acl_file_entry(
    parent_name: str,
    id: str,
    *,
    client: AuthenticatedClient | Client,
) -> Response[Any | Error]:
    return await _delete_services_haproxy_runtime_acls_parent_name_entries_id.asyncio_detailed(
        parent_name=parent_name,
        id=id,
        client=client,
    )


@api_function()
async def get_runtime_acl_file_entry(
    parent_name: str,
    id: str,
    *,
    client: AuthenticatedClient | Client,
) -> Response[Error | OneACLFileEntry]:
    return await _get_services_haproxy_runtime_acls_parent_name_entries_id.asyncio_detailed(
        parent_name=parent_name,
        id=id,
        client=client,
    )


@api_function()
async def post_runtime_acl_entry(
    parent_name: str,
    *,
    client: AuthenticatedClient | Client,
    body: OneACLFileEntry,
) -> Response[Error | OneACLFileEntry]:
    return (
        await _post_services_haproxy_runtime_acls_parent_name_entries.asyncio_detailed(
            parent_name=parent_name,
            client=client,
            body=body,
        )
    )


@api_function()
async def add_map_entry(
    parent_name: str,
    *,
    client: AuthenticatedClient | Client,
    body: OneMapEntry,
    force_sync: Unset | bool = False,
) -> Response[Error | OneMapEntry]:
    return await _add_map_entry.asyncio_detailed(
        parent_name=parent_name,
        client=client,
        body=body,
        force_sync=force_sync,
    )


@api_function()
async def delete_runtime_map_entry(
    parent_name: str,
    id: str,
    *,
    client: AuthenticatedClient | Client,
    force_sync: Unset | bool = False,
) -> Response[Any | Error]:
    return await _delete_runtime_map_entry.asyncio_detailed(
        parent_name=parent_name,
        id=id,
        client=client,
        force_sync=force_sync,
    )


@api_function()
async def get_runtime_map_entry(
    parent_name: str,
    id: str,
    *,
    client: AuthenticatedClient | Client,
) -> Response[Error | OneMapEntry]:
    return await _get_runtime_map_entry.asyncio_detailed(
        parent_name=parent_name,
        id=id,
        client=client,
    )


@api_function()
async def replace_runtime_map_entry(
    parent_name: str,
    id: str,
    *,
    client: AuthenticatedClient | Client,
    body: ReplaceRuntimeMapEntryBody,
    force_sync: Unset | bool = False,
) -> Response[Error | OneMapEntry]:
    return await _replace_runtime_map_entry.asyncio_detailed(
        parent_name=parent_name,
        id=id,
        client=client,
        body=body,
        force_sync=force_sync,
    )


@api_function()
async def add_runtime_server(
    parent_name: str,
    *,
    client: AuthenticatedClient | Client,
    body: RuntimeAddServer,
) -> Response[Error | RuntimeAddServer]:
    return await _add_runtime_server.asyncio_detailed(
        parent_name=parent_name,
        client=client,
        body=body,
    )


@api_function()
async def delete_runtime_server(
    parent_name: str,
    name: str,
    *,
    client: AuthenticatedClient | Client,
) -> Response[Any | Error]:
    return await _delete_runtime_server.asyncio_detailed(
        parent_name=parent_name,
        name=name,
        client=client,
    )


@api_function()
async def get_runtime_servers(
    parent_name: str,
    *,
    client: AuthenticatedClient | Client,
) -> Response[Error | list[RuntimeServer]]:
    return await _get_all_runtime_server.asyncio_detailed(
        parent_name=parent_name,
        client=client,
    )


@api_function()
async def replace_runtime_server(
    parent_name: str,
    name: str,
    *,
    client: AuthenticatedClient | Client,
    body: RuntimeServer,
) -> Response[Error | RuntimeServer]:
    return await _replace_runtime_server.asyncio_detailed(
        parent_name=parent_name,
        name=name,
        client=client,
        body=body,
    )


# Server API functions


@api_function()
async def get_all_server_backend(
    parent_name: str,
    *,
    client: AuthenticatedClient | Client,
    transaction_id: Unset | str = UNSET,
) -> Response[Error | list[Server]]:
    return await _get_all_server_backend.asyncio_detailed(
        parent_name=parent_name,
        client=client,
        transaction_id=transaction_id,
    )


@api_function()
async def create_server_backend(
    parent_name: str,
    *,
    client: AuthenticatedClient | Client,
    body: Server,
    transaction_id: Unset | str = UNSET,
    version: Unset | int = UNSET,
    force_reload: Unset | bool = False,
) -> Response[Error | Server]:
    return await _create_server_backend.asyncio_detailed(
        parent_name=parent_name,
        client=client,
        body=body,
        transaction_id=transaction_id,
        version=version,
        force_reload=force_reload,
    )


@api_function()
async def delete_server_backend(
    parent_name: str,
    name: str,
    *,
    client: AuthenticatedClient | Client,
    transaction_id: Unset | str = UNSET,
    version: Unset | int = UNSET,
    force_reload: Unset | bool = False,
) -> Response[Any | Error]:
    return await _delete_server_backend.asyncio_detailed(
        parent_name=parent_name,
        name=name,
        client=client,
        transaction_id=transaction_id,
        version=version,
        force_reload=force_reload,
    )


@api_function()
async def replace_server_backend(
    parent_name: str,
    name: str,
    *,
    client: AuthenticatedClient | Client,
    body: Server,
    transaction_id: Unset | str = UNSET,
    version: Unset | int = UNSET,
    force_reload: Unset | bool = False,
) -> Response[Error | Server]:
    return await _replace_server_backend.asyncio_detailed(
        parent_name=parent_name,
        name=name,
        client=client,
        body=body,
        transaction_id=transaction_id,
        version=version,
        force_reload=force_reload,
    )


# ACL API functions


@api_function()
async def get_all_acl_backend(
    parent_name: str,
    *,
    client: AuthenticatedClient | Client,
    acl_name: Unset | str = UNSET,
    transaction_id: Unset | str = UNSET,
) -> Response[Error | list[ACLLines]]:
    return await _get_all_acl_backend.asyncio_detailed(
        parent_name=parent_name,
        client=client,
        acl_name=acl_name,
        transaction_id=transaction_id,
    )


@api_function()
async def create_acl_backend(
    parent_name: str,
    index: int,
    *,
    client: AuthenticatedClient | Client,
    body: ACLLines,
    transaction_id: Unset | str = UNSET,
    version: Unset | int = UNSET,
    force_reload: Unset | bool = False,
) -> Response[ACLLines | Error]:
    return await _create_acl_backend.asyncio_detailed(
        parent_name=parent_name,
        index=index,
        client=client,
        body=body,
        transaction_id=transaction_id,
        version=version,
        force_reload=force_reload,
    )


@api_function()
async def delete_acl_backend(
    parent_name: str,
    index: int,
    *,
    client: AuthenticatedClient | Client,
    transaction_id: Unset | str = UNSET,
    version: Unset | int = UNSET,
    force_reload: Unset | bool = False,
) -> Response[Any | Error]:
    return await _delete_acl_backend.asyncio_detailed(
        parent_name=parent_name,
        index=index,
        client=client,
        transaction_id=transaction_id,
        version=version,
        force_reload=force_reload,
    )


@api_function()
async def replace_acl_backend(
    parent_name: str,
    index: int,
    *,
    client: AuthenticatedClient | Client,
    body: ACLLines,
    transaction_id: Unset | str = UNSET,
    version: Unset | int = UNSET,
    force_reload: Unset | bool = False,
) -> Response[ACLLines | Error]:
    return await _replace_acl_backend.asyncio_detailed(
        parent_name=parent_name,
        index=index,
        client=client,
        body=body,
        transaction_id=transaction_id,
        version=version,
        force_reload=force_reload,
    )


@api_function()
async def get_all_acl_frontend(
    parent_name: str,
    *,
    client: AuthenticatedClient | Client,
    acl_name: Unset | str = UNSET,
    transaction_id: Unset | str = UNSET,
) -> Response[Error | list[ACLLines]]:
    return await _get_all_acl_frontend.asyncio_detailed(
        parent_name=parent_name,
        client=client,
        acl_name=acl_name,
        transaction_id=transaction_id,
    )


@api_function()
async def create_acl_frontend(
    parent_name: str,
    index: int,
    *,
    client: AuthenticatedClient | Client,
    body: ACLLines,
    transaction_id: Unset | str = UNSET,
    version: Unset | int = UNSET,
    force_reload: Unset | bool = False,
) -> Response[ACLLines | Error]:
    return await _create_acl_frontend.asyncio_detailed(
        parent_name=parent_name,
        index=index,
        client=client,
        body=body,
        transaction_id=transaction_id,
        version=version,
        force_reload=force_reload,
    )


@api_function()
async def delete_acl_frontend(
    parent_name: str,
    index: int,
    *,
    client: AuthenticatedClient | Client,
    transaction_id: Unset | str = UNSET,
    version: Unset | int = UNSET,
    force_reload: Unset | bool = False,
) -> Response[Any | Error]:
    return await _delete_acl_frontend.asyncio_detailed(
        parent_name=parent_name,
        index=index,
        client=client,
        transaction_id=transaction_id,
        version=version,
        force_reload=force_reload,
    )


@api_function()
async def replace_acl_frontend(
    parent_name: str,
    index: int,
    *,
    client: AuthenticatedClient | Client,
    body: ACLLines,
    transaction_id: Unset | str = UNSET,
    version: Unset | int = UNSET,
    force_reload: Unset | bool = False,
) -> Response[ACLLines | Error]:
    return await _replace_acl_frontend.asyncio_detailed(
        parent_name=parent_name,
        index=index,
        client=client,
        body=body,
        transaction_id=transaction_id,
        version=version,
        force_reload=force_reload,
    )


# Backend Switching Rule API functions


@api_function()
async def get_all_backend_switching_rule_frontend(
    parent_name: str,
    *,
    client: AuthenticatedClient | Client,
    transaction_id: Unset | str = UNSET,
) -> Response[Error | list[BackendSwitchingRule]]:
    return await _get_all_backend_switching_rules.asyncio_detailed(
        parent_name=parent_name,
        client=client,
        transaction_id=transaction_id,
    )


@api_function()
async def create_backend_switching_rule_frontend(
    parent_name: str,
    index: int,
    *,
    client: AuthenticatedClient | Client,
    body: BackendSwitchingRule,
    transaction_id: Unset | str = UNSET,
    version: Unset | int = UNSET,
    force_reload: Unset | bool = False,
) -> Response[BackendSwitchingRule | Error]:
    return await _create_backend_switching_rule.asyncio_detailed(
        parent_name=parent_name,
        index=index,
        client=client,
        body=body,
        transaction_id=transaction_id,
        version=version,
        force_reload=force_reload,
    )


@api_function()
async def replace_backend_switching_rule_frontend(
    parent_name: str,
    index: int,
    *,
    client: AuthenticatedClient | Client,
    body: BackendSwitchingRule,
    transaction_id: Unset | str = UNSET,
    version: Unset | int = UNSET,
    force_reload: Unset | bool = False,
) -> Response[BackendSwitchingRule | Error]:
    return await _replace_backend_switching_rule.asyncio_detailed(
        parent_name=parent_name,
        index=index,
        client=client,
        body=body,
        transaction_id=transaction_id,
        version=version,
        force_reload=force_reload,
    )


@api_function()
async def delete_backend_switching_rule_frontend(
    parent_name: str,
    index: int,
    *,
    client: AuthenticatedClient | Client,
    transaction_id: Unset | str = UNSET,
    version: Unset | int = UNSET,
    force_reload: Unset | bool = False,
) -> Response[Any | Error]:
    return await _delete_backend_switching_rule.asyncio_detailed(
        parent_name=parent_name,
        index=index,
        client=client,
        transaction_id=transaction_id,
        version=version,
        force_reload=force_reload,
    )


# Bind API functions


@api_function()
async def get_all_bind_frontend(
    parent_name: str,
    *,
    client: AuthenticatedClient | Client,
    transaction_id: Unset | str = UNSET,
) -> Response[Error | list[Bind]]:
    return await _get_all_bind_frontend.asyncio_detailed(
        parent_name=parent_name,
        client=client,
        transaction_id=transaction_id,
    )


@api_function()
async def create_bind_frontend(
    parent_name: str,
    *,
    client: AuthenticatedClient | Client,
    body: Bind,
    transaction_id: Unset | str = UNSET,
    version: Unset | int = UNSET,
    force_reload: Unset | bool = False,
) -> Response[Bind | Error]:
    return await _create_bind_frontend.asyncio_detailed(
        parent_name=parent_name,
        client=client,
        body=body,
        transaction_id=transaction_id,
        version=version,
        force_reload=force_reload,
    )


@api_function()
async def delete_bind_frontend(
    parent_name: str,
    name: str,
    *,
    client: AuthenticatedClient | Client,
    transaction_id: Unset | str = UNSET,
    version: Unset | int = UNSET,
    force_reload: Unset | bool = False,
) -> Response[Any | Error]:
    return await _delete_bind_frontend.asyncio_detailed(
        parent_name=parent_name,
        name=name,
        client=client,
        transaction_id=transaction_id,
        version=version,
        force_reload=force_reload,
    )


@api_function()
async def replace_bind_frontend(
    parent_name: str,
    name: str,
    *,
    client: AuthenticatedClient | Client,
    body: Bind,
    transaction_id: Unset | str = UNSET,
    version: Unset | int = UNSET,
    force_reload: Unset | bool = False,
) -> Response[Bind | Error]:
    return await _replace_bind_frontend.asyncio_detailed(
        parent_name=parent_name,
        name=name,
        client=client,
        body=body,
        transaction_id=transaction_id,
        version=version,
        force_reload=force_reload,
    )


# HTTP Request Rule API functions


@api_function()
async def get_all_http_request_rule_frontend(
    parent_name: str,
    *,
    client: AuthenticatedClient | Client,
    transaction_id: Unset | str = UNSET,
) -> Response[Error | list[HTTPRequestRule]]:
    return await _get_all_http_request_rule_frontend.asyncio_detailed(
        parent_name=parent_name, client=client, transaction_id=transaction_id
    )


@api_function()
async def create_http_request_rule_frontend(
    parent_name: str,
    index: int,
    *,
    client: AuthenticatedClient | Client,
    body: HTTPRequestRule,
    transaction_id: Unset | str = UNSET,
    version: Unset | int = UNSET,
    force_reload: Unset | bool = False,
) -> Response[Error | HTTPRequestRule]:
    return await _create_http_request_rule_frontend.asyncio_detailed(
        parent_name=parent_name,
        index=index,
        client=client,
        body=body,
        transaction_id=transaction_id,
        version=version,
        force_reload=force_reload,
    )


@api_function()
async def delete_http_request_rule_frontend(
    parent_name: str,
    index: int,
    *,
    client: AuthenticatedClient | Client,
    transaction_id: Unset | str = UNSET,
    version: Unset | int = UNSET,
    force_reload: Unset | bool = False,
) -> Response[Any | Error]:
    return await _delete_http_request_rule_frontend.asyncio_detailed(
        parent_name=parent_name,
        index=index,
        client=client,
        transaction_id=transaction_id,
        version=version,
        force_reload=force_reload,
    )


@api_function()
async def replace_http_request_rule_frontend(
    parent_name: str,
    index: int,
    *,
    client: AuthenticatedClient | Client,
    body: HTTPRequestRule,
    transaction_id: Unset | str = UNSET,
    version: Unset | int = UNSET,
    force_reload: Unset | bool = False,
) -> Response[HTTPRequestRule | Error]:
    return await _replace_http_request_rule_frontend.asyncio_detailed(
        parent_name=parent_name,
        index=index,
        client=client,
        body=body,
        transaction_id=transaction_id,
        version=version,
        force_reload=force_reload,
    )


@api_function()
async def get_all_http_request_rule_backend(
    parent_name: str,
    *,
    client: AuthenticatedClient | Client,
    transaction_id: Unset | str = UNSET,
) -> Response[Error | list[HTTPRequestRule]]:
    return await _get_all_http_request_rule_backend.asyncio_detailed(
        parent_name=parent_name, client=client, transaction_id=transaction_id
    )


@api_function()
async def create_http_request_rule_backend(
    parent_name: str,
    index: int,
    *,
    client: AuthenticatedClient | Client,
    body: HTTPRequestRule,
    transaction_id: Unset | str = UNSET,
    version: Unset | int = UNSET,
    force_reload: Unset | bool = False,
) -> Response[Error | HTTPRequestRule]:
    return await _create_http_request_rule_backend.asyncio_detailed(
        parent_name=parent_name,
        index=index,
        client=client,
        body=body,
        transaction_id=transaction_id,
        version=version,
        force_reload=force_reload,
    )


@api_function()
async def delete_http_request_rule_backend(
    parent_name: str,
    index: int,
    *,
    client: AuthenticatedClient | Client,
    transaction_id: Unset | str = UNSET,
    version: Unset | int = UNSET,
    force_reload: Unset | bool = False,
) -> Response[Any | Error]:
    return await _delete_http_request_rule_backend.asyncio_detailed(
        parent_name=parent_name,
        index=index,
        client=client,
        transaction_id=transaction_id,
        version=version,
        force_reload=force_reload,
    )


@api_function()
async def replace_http_request_rule_backend(
    parent_name: str,
    index: int,
    *,
    client: AuthenticatedClient | Client,
    body: HTTPRequestRule,
    transaction_id: Unset | str = UNSET,
    version: Unset | int = UNSET,
    force_reload: Unset | bool = False,
) -> Response[HTTPRequestRule | Error]:
    return await _replace_http_request_rule_backend.asyncio_detailed(
        parent_name=parent_name,
        index=index,
        client=client,
        body=body,
        transaction_id=transaction_id,
        version=version,
        force_reload=force_reload,
    )


# HTTP Response Rule API functions


@api_function()
async def get_all_http_response_rule_frontend(
    parent_name: str,
    *,
    client: AuthenticatedClient | Client,
    transaction_id: Unset | str = UNSET,
) -> Response[Error | list[HTTPResponseRule]]:
    return await _get_all_http_response_rule_frontend.asyncio_detailed(
        parent_name=parent_name, client=client, transaction_id=transaction_id
    )


@api_function()
async def create_http_response_rule_frontend(
    parent_name: str,
    index: int,
    *,
    client: AuthenticatedClient | Client,
    body: HTTPResponseRule,
    transaction_id: Unset | str = UNSET,
    version: Unset | int = UNSET,
    force_reload: Unset | bool = False,
) -> Response[Error | HTTPResponseRule]:
    return await _create_http_response_rule_frontend.asyncio_detailed(
        parent_name=parent_name,
        index=index,
        client=client,
        body=body,
        transaction_id=transaction_id,
        version=version,
        force_reload=force_reload,
    )


@api_function()
async def delete_http_response_rule_frontend(
    parent_name: str,
    index: int,
    *,
    client: AuthenticatedClient | Client,
    transaction_id: Unset | str = UNSET,
    version: Unset | int = UNSET,
    force_reload: Unset | bool = False,
) -> Response[Any | Error]:
    return await _delete_http_response_rule_frontend.asyncio_detailed(
        parent_name=parent_name,
        index=index,
        client=client,
        transaction_id=transaction_id,
        version=version,
        force_reload=force_reload,
    )


@api_function()
async def replace_http_response_rule_frontend(
    parent_name: str,
    index: int,
    *,
    client: AuthenticatedClient | Client,
    body: HTTPResponseRule,
    transaction_id: Unset | str = UNSET,
    version: Unset | int = UNSET,
    force_reload: Unset | bool = False,
) -> Response[HTTPResponseRule | Error]:
    return await _replace_http_response_rule_frontend.asyncio_detailed(
        parent_name=parent_name,
        index=index,
        client=client,
        body=body,
        transaction_id=transaction_id,
        version=version,
        force_reload=force_reload,
    )


@api_function()
async def get_all_http_response_rule_backend(
    parent_name: str,
    *,
    client: AuthenticatedClient | Client,
    transaction_id: Unset | str = UNSET,
) -> Response[Error | list[HTTPResponseRule]]:
    return await _get_all_http_response_rule_backend.asyncio_detailed(
        parent_name=parent_name, client=client, transaction_id=transaction_id
    )


@api_function()
async def create_http_response_rule_backend(
    parent_name: str,
    index: int,
    *,
    client: AuthenticatedClient | Client,
    body: HTTPResponseRule,
    transaction_id: Unset | str = UNSET,
    version: Unset | int = UNSET,
    force_reload: Unset | bool = False,
) -> Response[Error | HTTPResponseRule]:
    return await _create_http_response_rule_backend.asyncio_detailed(
        parent_name=parent_name,
        index=index,
        client=client,
        body=body,
        transaction_id=transaction_id,
        version=version,
        force_reload=force_reload,
    )


@api_function()
async def delete_http_response_rule_backend(
    parent_name: str,
    index: int,
    *,
    client: AuthenticatedClient | Client,
    transaction_id: Unset | str = UNSET,
    version: Unset | int = UNSET,
    force_reload: Unset | bool = False,
) -> Response[Any | Error]:
    return await _delete_http_response_rule_backend.asyncio_detailed(
        parent_name=parent_name,
        index=index,
        client=client,
        transaction_id=transaction_id,
        version=version,
        force_reload=force_reload,
    )


@api_function()
async def replace_http_response_rule_backend(
    parent_name: str,
    index: int,
    *,
    client: AuthenticatedClient | Client,
    body: HTTPResponseRule,
    transaction_id: Unset | str = UNSET,
    version: Unset | int = UNSET,
    force_reload: Unset | bool = False,
) -> Response[HTTPResponseRule | Error]:
    return await _replace_http_response_rule_backend.asyncio_detailed(
        parent_name=parent_name,
        index=index,
        client=client,
        body=body,
        transaction_id=transaction_id,
        version=version,
        force_reload=force_reload,
    )


# Filter API functions


@api_function()
async def get_all_filter_frontend(
    parent_name: str,
    *,
    client: AuthenticatedClient | Client,
    transaction_id: Unset | str = UNSET,
) -> Response[Error | list[Filter]]:
    return await _get_all_filter_frontend.asyncio_detailed(
        parent_name=parent_name,
        client=client,
        transaction_id=transaction_id,
    )


@api_function()
async def create_filter_frontend(
    parent_name: str,
    index: int,
    *,
    client: AuthenticatedClient | Client,
    body: Filter,
    transaction_id: Unset | str = UNSET,
    version: Unset | int = UNSET,
    force_reload: Unset | bool = False,
) -> Response[Error | Filter]:
    return await _create_filter_frontend.asyncio_detailed(
        parent_name=parent_name,
        index=index,
        client=client,
        body=body,
        transaction_id=transaction_id,
        version=version,
        force_reload=force_reload,
    )


@api_function()
async def delete_filter_frontend(
    parent_name: str,
    index: int,
    *,
    client: AuthenticatedClient | Client,
    transaction_id: Unset | str = UNSET,
    version: Unset | int = UNSET,
    force_reload: Unset | bool = False,
) -> Response[Any | Error]:
    return await _delete_filter_frontend.asyncio_detailed(
        parent_name=parent_name,
        index=index,
        client=client,
        transaction_id=transaction_id,
        version=version,
        force_reload=force_reload,
    )


@api_function()
async def replace_filter_frontend(
    parent_name: str,
    index: int,
    *,
    client: AuthenticatedClient | Client,
    body: Filter,
    transaction_id: Unset | str = UNSET,
    version: Unset | int = UNSET,
    force_reload: Unset | bool = False,
) -> Response[Error | Filter]:
    return await _replace_filter_frontend.asyncio_detailed(
        parent_name=parent_name,
        index=index,
        client=client,
        body=body,
        transaction_id=transaction_id,
        version=version,
        force_reload=force_reload,
    )


@api_function()
async def get_all_filter_backend(
    parent_name: str,
    *,
    client: AuthenticatedClient | Client,
    transaction_id: Unset | str = UNSET,
) -> Response[Error | list[Filter]]:
    return await _get_all_filter_backend.asyncio_detailed(
        parent_name=parent_name,
        client=client,
        transaction_id=transaction_id,
    )


@api_function()
async def create_filter_backend(
    parent_name: str,
    index: int,
    *,
    client: AuthenticatedClient | Client,
    body: Filter,
    transaction_id: Unset | str = UNSET,
    version: Unset | int = UNSET,
    force_reload: Unset | bool = False,
) -> Response[Error | Filter]:
    return await _create_filter_backend.asyncio_detailed(
        parent_name=parent_name,
        index=index,
        client=client,
        body=body,
        transaction_id=transaction_id,
        version=version,
        force_reload=force_reload,
    )


@api_function()
async def delete_filter_backend(
    parent_name: str,
    index: int,
    *,
    client: AuthenticatedClient | Client,
    transaction_id: Unset | str = UNSET,
    version: Unset | int = UNSET,
    force_reload: Unset | bool = False,
) -> Response[Any | Error]:
    return await _delete_filter_backend.asyncio_detailed(
        parent_name=parent_name,
        index=index,
        client=client,
        transaction_id=transaction_id,
        version=version,
        force_reload=force_reload,
    )


@api_function()
async def replace_filter_backend(
    parent_name: str,
    index: int,
    *,
    client: AuthenticatedClient | Client,
    body: Filter,
    transaction_id: Unset | str = UNSET,
    version: Unset | int = UNSET,
    force_reload: Unset | bool = False,
) -> Response[Error | Filter]:
    return await _replace_filter_backend.asyncio_detailed(
        parent_name=parent_name,
        index=index,
        client=client,
        body=body,
        transaction_id=transaction_id,
        version=version,
        force_reload=force_reload,
    )


# Log Target API functions


@api_function()
async def get_all_log_target_backend(
    parent_name: str,
    *,
    client: AuthenticatedClient | Client,
    transaction_id: Unset | str = UNSET,
) -> Response[Error | list[LogTarget]]:
    return await _get_all_log_target_backend.asyncio_detailed(
        parent_name=parent_name,
        client=client,
        transaction_id=transaction_id,
    )


@api_function()
async def create_log_target_backend(
    parent_name: str,
    index: int,
    *,
    client: AuthenticatedClient | Client,
    body: LogTarget,
    transaction_id: Unset | str = UNSET,
    version: Unset | int = UNSET,
    force_reload: Unset | bool = False,
) -> Response[Error | LogTarget]:
    return await _create_log_target_backend.asyncio_detailed(
        parent_name=parent_name,
        index=index,
        client=client,
        body=body,
        transaction_id=transaction_id,
        version=version,
        force_reload=force_reload,
    )


@api_function()
async def delete_log_target_backend(
    parent_name: str,
    index: int,
    *,
    client: AuthenticatedClient | Client,
    transaction_id: Unset | str = UNSET,
    version: Unset | int = UNSET,
    force_reload: Unset | bool = False,
) -> Response[Any | Error]:
    return await _delete_log_target_backend.asyncio_detailed(
        parent_name=parent_name,
        index=index,
        client=client,
        transaction_id=transaction_id,
        version=version,
        force_reload=force_reload,
    )


@api_function()
async def replace_log_target_backend(
    parent_name: str,
    index: int,
    *,
    client: AuthenticatedClient | Client,
    body: LogTarget,
    transaction_id: Unset | str = UNSET,
    version: Unset | int = UNSET,
    force_reload: Unset | bool = False,
) -> Response[Error | LogTarget]:
    return await _replace_log_target_backend.asyncio_detailed(
        parent_name=parent_name,
        index=index,
        client=client,
        body=body,
        transaction_id=transaction_id,
        version=version,
        force_reload=force_reload,
    )


@api_function()
async def get_all_log_target_frontend(
    parent_name: str,
    *,
    client: AuthenticatedClient | Client,
    transaction_id: Unset | str = UNSET,
) -> Response[Error | list[LogTarget]]:
    return await _get_all_log_target_frontend.asyncio_detailed(
        parent_name=parent_name,
        client=client,
        transaction_id=transaction_id,
    )


@api_function()
async def get_all_log_target_global(
    *,
    client: AuthenticatedClient | Client,
    transaction_id: Unset | str = UNSET,
) -> Response[Error | list[LogTarget]]:
    return await _get_all_log_target_global.asyncio_detailed(
        client=client,
        transaction_id=transaction_id,
    )


# ===== Configuration Section API Functions =====
# Explicit wrapper functions for proper IDE support


# Backend functions
@api_function()
async def get_backends(
    *,
    client: AuthenticatedClient | Client,
    transaction_id: Unset | str = UNSET,
    full_section: Unset | bool = False,
) -> Response[Error | list[Backend]]:
    return await _get_backends.asyncio_detailed(
        client=client,
        transaction_id=transaction_id,
        full_section=full_section,
    )


@api_function()
async def create_backend(
    *,
    client: AuthenticatedClient | Client,
    body: Backend,
    transaction_id: Unset | str = UNSET,
    version: Unset | int = UNSET,
    force_reload: Unset | bool = False,
    full_section: Unset | bool = False,
) -> Response[Backend | Error]:
    return await _create_backend.asyncio_detailed(
        client=client,
        body=body,
        transaction_id=transaction_id,
        version=version,
        force_reload=force_reload,
        full_section=full_section,
    )


@api_function()
async def delete_backend(
    name: str,
    *,
    client: AuthenticatedClient | Client,
    transaction_id: Unset | str = UNSET,
    version: Unset | int = UNSET,
    force_reload: Unset | bool = False,
) -> Response[Error | None]:
    return await _delete_backend.asyncio_detailed(
        name=name,
        client=client,
        transaction_id=transaction_id,
        version=version,
        force_reload=force_reload,
    )


@api_function()
async def replace_backend(
    name: str,
    *,
    client: AuthenticatedClient | Client,
    body: Backend,
    transaction_id: Unset | str = UNSET,
    version: Unset | int = UNSET,
    force_reload: Unset | bool = False,
    full_section: Unset | bool = False,
) -> Response[Backend | Error]:
    return await _replace_backend.asyncio_detailed(
        name=name,
        client=client,
        body=body,
        transaction_id=transaction_id,
        version=version,
        force_reload=force_reload,
        full_section=full_section,
    )


# Cache functions
@api_function()
async def get_caches(
    *,
    client: AuthenticatedClient | Client,
    transaction_id: Unset | str = UNSET,
) -> Response[Error | list[Cache]]:
    return await _get_caches.asyncio_detailed(
        client=client,
        transaction_id=transaction_id,
    )


@api_function()
async def create_cache(
    *,
    client: AuthenticatedClient | Client,
    body: Cache,
    transaction_id: Unset | str = UNSET,
    version: Unset | int = UNSET,
    force_reload: Unset | bool = False,
) -> Response[Cache | Error]:
    return await _create_cache.asyncio_detailed(
        client=client,
        body=body,
        transaction_id=transaction_id,
        version=version,
        force_reload=force_reload,
    )


@api_function()
async def delete_cache(
    name: str,
    *,
    client: AuthenticatedClient | Client,
    transaction_id: Unset | str = UNSET,
    version: Unset | int = UNSET,
    force_reload: Unset | bool = False,
) -> Response[Error | None]:
    return await _delete_cache.asyncio_detailed(
        name=name,
        client=client,
        transaction_id=transaction_id,
        version=version,
        force_reload=force_reload,
    )


@api_function()
async def replace_cache(
    name: str,
    *,
    client: AuthenticatedClient | Client,
    body: Cache,
    transaction_id: Unset | str = UNSET,
    version: Unset | int = UNSET,
    force_reload: Unset | bool = False,
) -> Response[Cache | Error]:
    return await _replace_cache.asyncio_detailed(
        name=name,
        client=client,
        body=body,
        transaction_id=transaction_id,
        version=version,
        force_reload=force_reload,
    )


# Defaults functions
@api_function()
async def get_defaults_section(
    name: str,
    *,
    client: AuthenticatedClient | Client,
    transaction_id: Unset | str = UNSET,
    full_section: Unset | bool = True,
) -> Response[Error | Defaults]:
    return await _get_defaults_section.asyncio_detailed(
        name,
        client=client,
        transaction_id=transaction_id,
        full_section=full_section,
    )


@api_function()
async def get_defaults_sections(
    *,
    client: AuthenticatedClient | Client,
    transaction_id: Unset | str = UNSET,
    full_section: Unset | bool = True,
) -> Response[Error | list[Defaults]]:
    # Workaround for HAProxy DataPlane API bug where list endpoint with full_section=true
    # doesn't populate log_target_list, but individual endpoint works correctly
    if full_section is True:
        # First get section names without full_section
        list_response = await _get_defaults_sections.asyncio_detailed(
            client=client,
            transaction_id=transaction_id,
            full_section=False,
        )

        if isinstance(list_response.parsed, Error):
            return list_response

        # Ensure parsed is a list and not None
        if not list_response.parsed:
            return list_response

        # Then fetch each section individually with full_section=true
        full_sections: list[Defaults] = []
        for section in list_response.parsed:
            # Ensure section.name is a string, not Unset
            if not section.name or isinstance(section.name, type(UNSET)):
                continue

            individual_response = await _get_defaults_section.asyncio_detailed(
                section.name,
                client=client,
                transaction_id=transaction_id,
                full_section=True,
            )

            if isinstance(individual_response.parsed, Error):
                # Return error response with correct type annotation
                error_response: Response[Error | list[Defaults]] = cast(
                    Response[Error | list[Defaults]], individual_response
                )
                return error_response

            # Ensure we have a valid Defaults object before appending
            if individual_response.parsed is not None:
                full_sections.append(individual_response.parsed)

        # Create response with full sections
        response: Response[Error | list[Defaults]] = cast(
            Response[Error | list[Defaults]],
            Response(
                status_code=list_response.status_code,
                headers=list_response.headers,
                parsed=full_sections,
                content=list_response.content,
            ),
        )
        return response

    # Use original implementation when full_section is False or UNSET
    return await _get_defaults_sections.asyncio_detailed(
        client=client,
        transaction_id=transaction_id,
        full_section=full_section,
    )


@api_function()
async def replace_defaults_section(
    name: str,
    *,
    client: AuthenticatedClient | Client,
    body: Defaults,
    transaction_id: Unset | str = UNSET,
    version: Unset | int = UNSET,
    force_reload: Unset | bool = False,
    full_section: Unset | bool = True,
) -> Response[Defaults | Error]:
    return await _replace_defaults_section.asyncio_detailed(
        name=name,
        client=client,
        body=body,
        transaction_id=transaction_id,
        version=version,
        force_reload=force_reload,
        full_section=full_section,
    )


@api_function()
async def add_defaults_section(
    *,
    client: AuthenticatedClient | Client,
    body: Defaults,
    transaction_id: Unset | str = UNSET,
    version: Unset | int = UNSET,
    force_reload: Unset | bool = False,
    full_section: Unset | bool = True,
) -> Response[Defaults | Error]:
    return await _add_defaults_section.asyncio_detailed(
        client=client,
        body=body,
        transaction_id=transaction_id,
        version=version,
        force_reload=force_reload,
        full_section=full_section,
    )


@api_function()
async def create_defaults_section(
    *,
    client: AuthenticatedClient | Client,
    body: Defaults,
    transaction_id: Unset | str = UNSET,
    version: Unset | int = UNSET,
    force_reload: Unset | bool = False,
    full_section: Unset | bool = True,
) -> Response[Defaults | Error]:
    return await _create_defaults_section.asyncio_detailed(
        client=client,
        body=body,
        transaction_id=transaction_id,
        version=version,
        force_reload=force_reload,
        full_section=full_section,
    )


@api_function()
async def delete_defaults_section(
    name: str,
    *,
    client: AuthenticatedClient | Client,
    transaction_id: Unset | str = UNSET,
    version: Unset | int = UNSET,
    force_reload: Unset | bool = False,
    full_section: Unset | bool = True,
) -> Response[None | Error]:
    return await _delete_defaults_section.asyncio_detailed(
        name=name,
        client=client,
        transaction_id=transaction_id,
        version=version,
        force_reload=force_reload,
        full_section=full_section,
    )


# FCGI App functions
@api_function()
async def get_fcgi_apps(
    *,
    client: AuthenticatedClient | Client,
    transaction_id: Unset | str = UNSET,
) -> Response[Error | list[FcgiApp]]:
    return await _get_fcgi_apps.asyncio_detailed(
        client=client,
        transaction_id=transaction_id,
    )


@api_function()
async def create_fcgi_app(
    *,
    client: AuthenticatedClient | Client,
    body: FcgiApp,
    transaction_id: Unset | str = UNSET,
    version: Unset | int = UNSET,
    force_reload: Unset | bool = False,
) -> Response[FcgiApp | Error]:
    return await _create_fcgi_app.asyncio_detailed(
        client=client,
        body=body,
        transaction_id=transaction_id,
        version=version,
        force_reload=force_reload,
    )


@api_function()
async def delete_fcgi_app(
    name: str,
    *,
    client: AuthenticatedClient | Client,
    transaction_id: Unset | str = UNSET,
    version: Unset | int = UNSET,
    force_reload: Unset | bool = False,
) -> Response[Error | None]:
    return await _delete_fcgi_app.asyncio_detailed(
        name=name,
        client=client,
        transaction_id=transaction_id,
        version=version,
        force_reload=force_reload,
    )


@api_function()
async def replace_fcgi_app(
    name: str,
    *,
    client: AuthenticatedClient | Client,
    body: FcgiApp,
    transaction_id: Unset | str = UNSET,
    version: Unset | int = UNSET,
    force_reload: Unset | bool = False,
) -> Response[FcgiApp | Error]:
    return await _replace_fcgi_app.asyncio_detailed(
        name=name,
        client=client,
        body=body,
        transaction_id=transaction_id,
        version=version,
        force_reload=force_reload,
    )


# Frontend functions
@api_function()
async def get_frontends(
    *,
    client: AuthenticatedClient | Client,
    transaction_id: Unset | str = UNSET,
    full_section: Unset | bool = False,
) -> Response[Error | list[Frontend]]:
    return await _get_frontends.asyncio_detailed(
        client=client,
        transaction_id=transaction_id,
        full_section=full_section,
    )


@api_function()
async def create_frontend(
    *,
    client: AuthenticatedClient | Client,
    body: Frontend,
    transaction_id: Unset | str = UNSET,
    version: Unset | int = UNSET,
    force_reload: Unset | bool = False,
    full_section: Unset | bool = False,
) -> Response[Frontend | Error]:
    return await _create_frontend.asyncio_detailed(
        client=client,
        body=body,
        transaction_id=transaction_id,
        version=version,
        force_reload=force_reload,
        full_section=full_section,
    )


@api_function()
async def delete_frontend(
    name: str,
    *,
    client: AuthenticatedClient | Client,
    transaction_id: Unset | str = UNSET,
    version: Unset | int = UNSET,
    force_reload: Unset | bool = False,
) -> Response[Error | None]:
    return await _delete_frontend.asyncio_detailed(
        name=name,
        client=client,
        transaction_id=transaction_id,
        version=version,
        force_reload=force_reload,
    )


@api_function()
async def replace_frontend(
    name: str,
    *,
    client: AuthenticatedClient | Client,
    body: Frontend,
    transaction_id: Unset | str = UNSET,
    version: Unset | int = UNSET,
    force_reload: Unset | bool = False,
    full_section: Unset | bool = False,
) -> Response[Frontend | Error]:
    return await _replace_frontend.asyncio_detailed(
        name=name,
        client=client,
        body=body,
        transaction_id=transaction_id,
        version=version,
        force_reload=force_reload,
        full_section=full_section,
    )


# Global functions
@api_function()
async def get_global(
    *,
    client: AuthenticatedClient | Client,
    transaction_id: Unset | str = UNSET,
) -> Response[Error | Global]:
    return await _get_global.asyncio_detailed(
        client=client,
        transaction_id=transaction_id,
    )


@api_function()
async def replace_global(
    *,
    client: AuthenticatedClient | Client,
    body: Global,
    transaction_id: Unset | str = UNSET,
    version: Unset | int = UNSET,
    force_reload: Unset | bool = False,
    full_section: Unset | bool = False,
) -> Response[Error | Global]:
    return await _replace_global.asyncio_detailed(
        client=client,
        body=body,
        transaction_id=transaction_id,
        version=version,
        force_reload=force_reload,
        full_section=full_section,
    )


# HTTP Errors functions
@api_function()
async def get_http_errors_sections(
    *,
    client: AuthenticatedClient | Client,
    transaction_id: Unset | str = UNSET,
) -> Response[Error | list[HttpErrorsSection]]:
    return await _get_http_errors_sections.asyncio_detailed(
        client=client,
        transaction_id=transaction_id,
    )


@api_function()
async def create_http_errors_section(
    *,
    client: AuthenticatedClient | Client,
    body: HttpErrorsSection,
    transaction_id: Unset | str = UNSET,
    version: Unset | int = UNSET,
    force_reload: Unset | bool = False,
) -> Response[HttpErrorsSection | Error]:
    return await _create_http_errors_section.asyncio_detailed(
        client=client,
        body=body,
        transaction_id=transaction_id,
        version=version,
        force_reload=force_reload,
    )


@api_function()
async def delete_http_errors_section(
    name: str,
    *,
    client: AuthenticatedClient | Client,
    transaction_id: Unset | str = UNSET,
    version: Unset | int = UNSET,
    force_reload: Unset | bool = False,
) -> Response[Error | None]:
    return await _delete_http_errors_section.asyncio_detailed(
        name=name,
        client=client,
        transaction_id=transaction_id,
        version=version,
        force_reload=force_reload,
    )


@api_function()
async def replace_http_errors_section(
    name: str,
    *,
    client: AuthenticatedClient | Client,
    body: HttpErrorsSection,
    transaction_id: Unset | str = UNSET,
    version: Unset | int = UNSET,
    force_reload: Unset | bool = False,
) -> Response[HttpErrorsSection | Error]:
    return await _replace_http_errors_section.asyncio_detailed(
        name=name,
        client=client,
        body=body,
        transaction_id=transaction_id,
        version=version,
        force_reload=force_reload,
    )


# Log Forward functions
@api_function()
async def get_log_forwards(
    *,
    client: AuthenticatedClient | Client,
    transaction_id: Unset | str = UNSET,
) -> Response[Error | list[LogForward]]:
    return await _get_log_forwards.asyncio_detailed(
        client=client,
        transaction_id=transaction_id,
    )


@api_function()
async def create_log_forward(
    *,
    client: AuthenticatedClient | Client,
    body: LogForward,
    transaction_id: Unset | str = UNSET,
    version: Unset | int = UNSET,
    force_reload: Unset | bool = False,
) -> Response[LogForward | Error]:
    return await _create_log_forward.asyncio_detailed(
        client=client,
        body=body,
        transaction_id=transaction_id,
        version=version,
        force_reload=force_reload,
    )


@api_function()
async def delete_log_forward(
    name: str,
    *,
    client: AuthenticatedClient | Client,
    transaction_id: Unset | str = UNSET,
    version: Unset | int = UNSET,
    force_reload: Unset | bool = False,
) -> Response[Error | None]:
    return await _delete_log_forward.asyncio_detailed(
        name=name,
        client=client,
        transaction_id=transaction_id,
        version=version,
        force_reload=force_reload,
    )


@api_function()
async def replace_log_forward(
    name: str,
    *,
    client: AuthenticatedClient | Client,
    body: LogForward,
    transaction_id: Unset | str = UNSET,
    version: Unset | int = UNSET,
    force_reload: Unset | bool = False,
) -> Response[LogForward | Error]:
    return await _replace_log_forward.asyncio_detailed(
        name=name,
        client=client,
        body=body,
        transaction_id=transaction_id,
        version=version,
        force_reload=force_reload,
    )


# Log Target frontend functions
@api_function()
async def create_log_target_frontend(
    parent_name: str,
    index: int,
    *,
    client: AuthenticatedClient | Client,
    body: LogTarget,
    transaction_id: Unset | str = UNSET,
    version: Unset | int = UNSET,
    force_reload: Unset | bool = False,
) -> Response[LogTarget | Error]:
    return await _create_log_target_frontend.asyncio_detailed(
        parent_name=parent_name,
        index=index,
        client=client,
        body=body,
        transaction_id=transaction_id,
        version=version,
        force_reload=force_reload,
    )


@api_function()
async def delete_log_target_frontend(
    parent_name: str,
    index: int,
    *,
    client: AuthenticatedClient | Client,
    transaction_id: Unset | str = UNSET,
    version: Unset | int = UNSET,
    force_reload: Unset | bool = False,
) -> Response[Error | None]:
    return await _delete_log_target_frontend.asyncio_detailed(
        parent_name=parent_name,
        index=index,
        client=client,
        transaction_id=transaction_id,
        version=version,
        force_reload=force_reload,
    )


@api_function()
async def replace_log_target_frontend(
    parent_name: str,
    index: int,
    *,
    client: AuthenticatedClient | Client,
    body: LogTarget,
    transaction_id: Unset | str = UNSET,
    version: Unset | int = UNSET,
    force_reload: Unset | bool = False,
) -> Response[LogTarget | Error]:
    return await _replace_log_target_frontend.asyncio_detailed(
        parent_name=parent_name,
        index=index,
        client=client,
        body=body,
        transaction_id=transaction_id,
        version=version,
        force_reload=force_reload,
    )


# Global log target functions
@api_function()
async def create_log_target_global(
    index: int,
    *,
    client: AuthenticatedClient | Client,
    body: LogTarget,
    transaction_id: Unset | str = UNSET,
    version: Unset | int = UNSET,
    force_reload: Unset | bool = False,
) -> Response[LogTarget | Error]:
    return await _create_log_target_global.asyncio_detailed(
        index=index,
        client=client,
        body=body,
        transaction_id=transaction_id,
        version=version,
        force_reload=force_reload,
    )


@api_function()
async def delete_log_target_global(
    index: int,
    *,
    client: AuthenticatedClient | Client,
    transaction_id: Unset | str = UNSET,
    version: Unset | int = UNSET,
    force_reload: Unset | bool = False,
) -> Response[Error | None]:
    return await _delete_log_target_global.asyncio_detailed(
        index=index,
        client=client,
        transaction_id=transaction_id,
        version=version,
        force_reload=force_reload,
    )


@api_function()
async def replace_log_target_global(
    index: int,
    *,
    client: AuthenticatedClient | Client,
    body: LogTarget,
    transaction_id: Unset | str = UNSET,
    version: Unset | int = UNSET,
    force_reload: Unset | bool = False,
) -> Response[LogTarget | Error]:
    return await _replace_log_target_global.asyncio_detailed(
        index=index,
        client=client,
        body=body,
        transaction_id=transaction_id,
        version=version,
        force_reload=force_reload,
    )


# Defaults log target functions
@api_function()
async def get_all_log_target_defaults(
    parent_name: str,
    *,
    client: AuthenticatedClient | Client,
    transaction_id: Unset | str = UNSET,
) -> Response[Error | list[LogTarget]]:
    return await _get_all_log_target_defaults.asyncio_detailed(
        parent_name=parent_name,
        client=client,
        transaction_id=transaction_id,
    )


@api_function()
async def create_log_target_defaults(
    parent_name: str,
    index: int,
    *,
    client: AuthenticatedClient | Client,
    body: LogTarget,
    transaction_id: Unset | str = UNSET,
    version: Unset | int = UNSET,
    force_reload: Unset | bool = False,
) -> Response[LogTarget | Error]:
    return await _create_log_target_defaults.asyncio_detailed(
        parent_name=parent_name,
        index=index,
        client=client,
        body=body,
        transaction_id=transaction_id,
        version=version,
        force_reload=force_reload,
    )


@api_function()
async def delete_log_target_defaults(
    parent_name: str,
    index: int,
    *,
    client: AuthenticatedClient | Client,
    transaction_id: Unset | str = UNSET,
    version: Unset | int = UNSET,
    force_reload: Unset | bool = False,
) -> Response[Error | None]:
    return await _delete_log_target_defaults.asyncio_detailed(
        parent_name=parent_name,
        index=index,
        client=client,
        transaction_id=transaction_id,
        version=version,
        force_reload=force_reload,
    )


@api_function()
async def replace_log_target_defaults(
    parent_name: str,
    index: int,
    *,
    client: AuthenticatedClient | Client,
    body: LogTarget,
    transaction_id: Unset | str = UNSET,
    version: Unset | int = UNSET,
    force_reload: Unset | bool = False,
) -> Response[LogTarget | Error]:
    return await _replace_log_target_defaults.asyncio_detailed(
        parent_name=parent_name,
        index=index,
        client=client,
        body=body,
        transaction_id=transaction_id,
        version=version,
        force_reload=force_reload,
    )


# Peer log target functions
@api_function()
async def get_all_log_target_peer(
    parent_name: str,
    *,
    client: AuthenticatedClient | Client,
    transaction_id: Unset | str = UNSET,
) -> Response[Error | list[LogTarget]]:
    return await _get_all_log_target_peer.asyncio_detailed(
        parent_name=parent_name,
        client=client,
        transaction_id=transaction_id,
    )


@api_function()
async def create_log_target_peer(
    parent_name: str,
    index: int,
    *,
    client: AuthenticatedClient | Client,
    body: LogTarget,
    transaction_id: Unset | str = UNSET,
    version: Unset | int = UNSET,
    force_reload: Unset | bool = False,
) -> Response[LogTarget | Error]:
    return await _create_log_target_peer.asyncio_detailed(
        parent_name=parent_name,
        index=index,
        client=client,
        body=body,
        transaction_id=transaction_id,
        version=version,
        force_reload=force_reload,
    )


@api_function()
async def delete_log_target_peer(
    parent_name: str,
    index: int,
    *,
    client: AuthenticatedClient | Client,
    transaction_id: Unset | str = UNSET,
    version: Unset | int = UNSET,
    force_reload: Unset | bool = False,
) -> Response[Error | None]:
    return await _delete_log_target_peer.asyncio_detailed(
        parent_name=parent_name,
        index=index,
        client=client,
        transaction_id=transaction_id,
        version=version,
        force_reload=force_reload,
    )


@api_function()
async def replace_log_target_peer(
    parent_name: str,
    index: int,
    *,
    client: AuthenticatedClient | Client,
    body: LogTarget,
    transaction_id: Unset | str = UNSET,
    version: Unset | int = UNSET,
    force_reload: Unset | bool = False,
) -> Response[LogTarget | Error]:
    return await _replace_log_target_peer.asyncio_detailed(
        parent_name=parent_name,
        index=index,
        client=client,
        body=body,
        transaction_id=transaction_id,
        version=version,
        force_reload=force_reload,
    )


# Log forward log target functions
@api_function()
async def get_all_log_target_log_forward(
    parent_name: str,
    *,
    client: AuthenticatedClient | Client,
    transaction_id: Unset | str = UNSET,
) -> Response[Error | list[LogTarget]]:
    return await _get_all_log_target_log_forward.asyncio_detailed(
        parent_name=parent_name,
        client=client,
        transaction_id=transaction_id,
    )


@api_function()
async def create_log_target_log_forward(
    parent_name: str,
    index: int,
    *,
    client: AuthenticatedClient | Client,
    body: LogTarget,
    transaction_id: Unset | str = UNSET,
    version: Unset | int = UNSET,
    force_reload: Unset | bool = False,
) -> Response[LogTarget | Error]:
    return await _create_log_target_log_forward.asyncio_detailed(
        parent_name=parent_name,
        index=index,
        client=client,
        body=body,
        transaction_id=transaction_id,
        version=version,
        force_reload=force_reload,
    )


@api_function()
async def delete_log_target_log_forward(
    parent_name: str,
    index: int,
    *,
    client: AuthenticatedClient | Client,
    transaction_id: Unset | str = UNSET,
    version: Unset | int = UNSET,
    force_reload: Unset | bool = False,
) -> Response[Error | None]:
    return await _delete_log_target_log_forward.asyncio_detailed(
        parent_name=parent_name,
        index=index,
        client=client,
        transaction_id=transaction_id,
        version=version,
        force_reload=force_reload,
    )


@api_function()
async def replace_log_target_log_forward(
    parent_name: str,
    index: int,
    *,
    client: AuthenticatedClient | Client,
    body: LogTarget,
    transaction_id: Unset | str = UNSET,
    version: Unset | int = UNSET,
    force_reload: Unset | bool = False,
) -> Response[LogTarget | Error]:
    return await _replace_log_target_log_forward.asyncio_detailed(
        parent_name=parent_name,
        index=index,
        client=client,
        body=body,
        transaction_id=transaction_id,
        version=version,
        force_reload=force_reload,
    )


# Mailers functions
@api_function()
async def get_mailers_sections(
    *,
    client: AuthenticatedClient | Client,
    transaction_id: Unset | str = UNSET,
) -> Response[Error | list[MailersSection]]:
    return await _get_mailers_sections.asyncio_detailed(
        client=client,
        transaction_id=transaction_id,
    )


@api_function()
async def create_mailers_section(
    *,
    client: AuthenticatedClient | Client,
    body: MailersSection,
    transaction_id: Unset | str = UNSET,
    version: Unset | int = UNSET,
    force_reload: Unset | bool = False,
) -> Response[MailersSection | Error]:
    return await _create_mailers_section.asyncio_detailed(
        client=client,
        body=body,
        transaction_id=transaction_id,
        version=version,
        force_reload=force_reload,
    )


@api_function()
async def delete_mailers_section(
    name: str,
    *,
    client: AuthenticatedClient | Client,
    transaction_id: Unset | str = UNSET,
    version: Unset | int = UNSET,
    force_reload: Unset | bool = False,
) -> Response[Error | None]:
    return await _delete_mailers_section.asyncio_detailed(
        name=name,
        client=client,
        transaction_id=transaction_id,
        version=version,
        force_reload=force_reload,
    )


@api_function()
async def edit_mailers_section(
    name: str,
    *,
    client: AuthenticatedClient | Client,
    body: MailersSection,
    transaction_id: Unset | str = UNSET,
    version: Unset | int = UNSET,
    force_reload: Unset | bool = False,
) -> Response[MailersSection | Error]:
    return await _edit_mailers_section.asyncio_detailed(
        name=name,
        client=client,
        body=body,
        transaction_id=transaction_id,
        version=version,
        force_reload=force_reload,
    )


# Peer functions
@api_function()
async def get_peer_sections(
    *,
    client: AuthenticatedClient | Client,
    transaction_id: Unset | str = UNSET,
) -> Response[Error | list[PeerSection]]:
    return await _get_peer_sections.asyncio_detailed(
        client=client,
        transaction_id=transaction_id,
    )


@api_function()
async def create_peer(
    *,
    client: AuthenticatedClient | Client,
    body: PeerSection,
    transaction_id: Unset | str = UNSET,
    version: Unset | int = UNSET,
    force_reload: Unset | bool = False,
) -> Response[PeerSection | Error]:
    return await _create_peer.asyncio_detailed(
        client=client,
        body=body,
        transaction_id=transaction_id,
        version=version,
        force_reload=force_reload,
    )


@api_function()
async def delete_peer(
    name: str,
    *,
    client: AuthenticatedClient | Client,
    transaction_id: Unset | str = UNSET,
    version: Unset | int = UNSET,
    force_reload: Unset | bool = False,
) -> Response[Error | None]:
    return await _delete_peer.asyncio_detailed(
        name=name,
        client=client,
        transaction_id=transaction_id,
        version=version,
        force_reload=force_reload,
    )


# Program functions
@api_function()
async def get_programs(
    *,
    client: AuthenticatedClient | Client,
    transaction_id: Unset | str = UNSET,
) -> Response[Error | list[Program]]:
    return await _get_programs.asyncio_detailed(
        client=client,
        transaction_id=transaction_id,
    )


@api_function()
async def create_program(
    *,
    client: AuthenticatedClient | Client,
    body: Program,
    transaction_id: Unset | str = UNSET,
    version: Unset | int = UNSET,
    force_reload: Unset | bool = False,
) -> Response[Program | Error]:
    return await _create_program.asyncio_detailed(
        client=client,
        body=body,
        transaction_id=transaction_id,
        version=version,
        force_reload=force_reload,
    )


@api_function()
async def delete_program(
    name: str,
    *,
    client: AuthenticatedClient | Client,
    transaction_id: Unset | str = UNSET,
    version: Unset | int = UNSET,
    force_reload: Unset | bool = False,
) -> Response[Error | None]:
    return await _delete_program.asyncio_detailed(
        name=name,
        client=client,
        transaction_id=transaction_id,
        version=version,
        force_reload=force_reload,
    )


@api_function()
async def replace_program(
    name: str,
    *,
    client: AuthenticatedClient | Client,
    body: Program,
    transaction_id: Unset | str = UNSET,
    version: Unset | int = UNSET,
    force_reload: Unset | bool = False,
) -> Response[Program | Error]:
    return await _replace_program.asyncio_detailed(
        name=name,
        client=client,
        body=body,
        transaction_id=transaction_id,
        version=version,
        force_reload=force_reload,
    )


# Resolver functions
@api_function()
async def get_resolvers(
    *,
    client: AuthenticatedClient | Client,
    transaction_id: Unset | str = UNSET,
) -> Response[Error | list[Resolver]]:
    return await _get_resolvers.asyncio_detailed(
        client=client,
        transaction_id=transaction_id,
    )


@api_function()
async def create_resolver(
    *,
    client: AuthenticatedClient | Client,
    body: Resolver,
    transaction_id: Unset | str = UNSET,
    version: Unset | int = UNSET,
    force_reload: Unset | bool = False,
) -> Response[Resolver | Error]:
    return await _create_resolver.asyncio_detailed(
        client=client,
        body=body,
        transaction_id=transaction_id,
        version=version,
        force_reload=force_reload,
    )


@api_function()
async def delete_resolver(
    name: str,
    *,
    client: AuthenticatedClient | Client,
    transaction_id: Unset | str = UNSET,
    version: Unset | int = UNSET,
    force_reload: Unset | bool = False,
) -> Response[Error | None]:
    return await _delete_resolver.asyncio_detailed(
        name=name,
        client=client,
        transaction_id=transaction_id,
        version=version,
        force_reload=force_reload,
    )


@api_function()
async def replace_resolver(
    name: str,
    *,
    client: AuthenticatedClient | Client,
    body: Resolver,
    transaction_id: Unset | str = UNSET,
    version: Unset | int = UNSET,
    force_reload: Unset | bool = False,
) -> Response[Resolver | Error]:
    return await _replace_resolver.asyncio_detailed(
        name=name,
        client=client,
        body=body,
        transaction_id=transaction_id,
        version=version,
        force_reload=force_reload,
    )


# Ring functions
@api_function()
async def get_rings(
    *,
    client: AuthenticatedClient | Client,
    transaction_id: Unset | str = UNSET,
) -> Response[Error | list[Ring]]:
    return await _get_rings.asyncio_detailed(
        client=client,
        transaction_id=transaction_id,
    )


@api_function()
async def create_ring(
    *,
    client: AuthenticatedClient | Client,
    body: Ring,
    transaction_id: Unset | str = UNSET,
    version: Unset | int = UNSET,
    force_reload: Unset | bool = False,
) -> Response[Ring | Error]:
    return await _create_ring.asyncio_detailed(
        client=client,
        body=body,
        transaction_id=transaction_id,
        version=version,
        force_reload=force_reload,
    )


@api_function()
async def delete_ring(
    name: str,
    *,
    client: AuthenticatedClient | Client,
    transaction_id: Unset | str = UNSET,
    version: Unset | int = UNSET,
    force_reload: Unset | bool = False,
) -> Response[Error | None]:
    return await _delete_ring.asyncio_detailed(
        name=name,
        client=client,
        transaction_id=transaction_id,
        version=version,
        force_reload=force_reload,
    )


@api_function()
async def replace_ring(
    name: str,
    *,
    client: AuthenticatedClient | Client,
    body: Ring,
    transaction_id: Unset | str = UNSET,
    version: Unset | int = UNSET,
    force_reload: Unset | bool = False,
) -> Response[Ring | Error]:
    return await _replace_ring.asyncio_detailed(
        name=name,
        client=client,
        body=body,
        transaction_id=transaction_id,
        version=version,
        force_reload=force_reload,
    )


# Userlist functions
@api_function()
async def get_userlists(
    *,
    client: AuthenticatedClient | Client,
    transaction_id: Unset | str = UNSET,
) -> Response[Error | list[Userlist]]:
    return await _get_userlists.asyncio_detailed(
        client=client,
        transaction_id=transaction_id,
    )


@api_function()
async def create_userlist(
    *,
    client: AuthenticatedClient | Client,
    body: Userlist,
    transaction_id: Unset | str = UNSET,
    version: Unset | int = UNSET,
    force_reload: Unset | bool = False,
) -> Response[Userlist | Error]:
    return await _create_userlist.asyncio_detailed(
        client=client,
        body=body,
        transaction_id=transaction_id,
        version=version,
        force_reload=force_reload,
    )


@api_function()
async def delete_userlist(
    name: str,
    *,
    client: AuthenticatedClient | Client,
    transaction_id: Unset | str = UNSET,
    version: Unset | int = UNSET,
    force_reload: Unset | bool = False,
) -> Response[Error | None]:
    return await _delete_userlist.asyncio_detailed(
        name=name,
        client=client,
        transaction_id=transaction_id,
        version=version,
        force_reload=force_reload,
    )


# Response checking functions (moved from utils.py to avoid circular import)
def check_dataplane_response(
    response: Response, operation: str, endpoint: Union[str, "DataplaneEndpoint"]
) -> Response:
    """Uniform error checking for all dataplane API responses.

    This function provides consistent error detection across all dataplane modules
    by checking if the response is an Error object from the generated client.

    Args:
        response: Response from any dataplane API call
        operation: Operation name for context (e.g., "fetch_backends", "create_map")
        endpoint: Endpoint URL or DataplaneEndpoint for error context

    Returns:
        The response if successful

    Raises:
        DataplaneAPIError: If response is an Error object with proper context

    Example:
        response = await get_backends.asyncio(client=client)
        checked_response = check_dataplane_response(response, "fetch_backends", base_url)
    """
    # Error model is now imported at module level

    if isinstance(response.parsed, Error):
        error: Error = response.parsed
        error_msg = f"{operation} failed"
        if error.message:
            error_msg += f": {error.message}"
        if error.code:
            error_msg += f" (HTTP {error.code})"

        logger.warning(
            f"Dataplane API error in {operation}: code={error.code}, message={error.message}"
        )

        raise DataplaneAPIError(
            error_msg,
            endpoint=endpoint,
            operation=operation,
            original_error=None,
        )

    return response


def check_configuration_response(
    response: Response,
    operation: str,
    endpoint: Union[str, "DataplaneEndpoint"],
    config_content: str | None = None,
) -> Response:
    """Specialized error checking for configuration operations (validate/deploy).

    This function handles both Error objects and string responses containing JSON error data.
    It determines whether to raise ValidationError or DataplaneAPIError based on response content.

    Args:
        response: Response from configuration API call (Error object or string)
        operation: Operation name for context (e.g., "validate_configuration", "deploy_configuration")
        endpoint: Endpoint URL or DataplaneEndpoint for error context
        config_content: Optional configuration content for context extraction

    Returns:
        The response if successful

    Raises:
        ValidationError: If response contains HAProxy validation errors
        DataplaneAPIError: If response contains other API errors

    Example:
        response = await post_ha_proxy_configuration.asyncio(client=client, body=config)
        checked_response = check_configuration_response(response, "deploy_configuration", base_url, config)
    """
    from .utils import parse_validation_error_details

    # Error model is now imported at module level

    # First handle Error objects like regular check_dataplane_response
    if isinstance(response.parsed, Error):
        error: Error = response.parsed
        error_msg = f"{operation} failed"
        if error.message:
            error_msg += f": {error.message}"
        if error.code:
            error_msg += f" (HTTP {error.code})"

        logger.warning(
            f"Dataplane API error in {operation}: code={error.code}, message={error.message}"
        )

        raise DataplaneAPIError(
            error_msg,
            endpoint=endpoint,
            operation=operation,
            original_error=None,
        )

    # Handle string responses that may contain JSON error data
    if isinstance(response.parsed, str):
        try:
            error_data = json.loads(response.parsed)
            if isinstance(error_data, dict) and error_data.get("code", 0) >= 400:
                message = error_data.get("message", "")

                # Use existing utility to parse validation details
                validation_details, error_line, error_context = (
                    parse_validation_error_details(message, config_content)
                )

                if (
                    "validation error" in message.lower()
                    or "Fatal errors found in configuration" in message
                    or error_line is not None
                ):
                    # This is a validation error
                    raise ValidationError(
                        f"Configuration validation failed: {validation_details}",
                        endpoint=endpoint,
                        config_size=len(config_content) if config_content else None,
                        validation_details=validation_details,
                        error_line=error_line,
                        config_content=config_content,
                        error_context=error_context,
                    )
                else:
                    # This is a general API error
                    raise DataplaneAPIError(
                        f"{operation} failed: {message}",
                        endpoint=endpoint,
                        operation=operation,
                    )
        except (json.JSONDecodeError, KeyError):
            # Not JSON or malformed - treat as normal response
            pass

    return response
