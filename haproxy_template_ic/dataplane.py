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
import io
import logging
import re
from datetime import datetime, UTC
from typing import Any, Dict, List, Optional, TYPE_CHECKING, Tuple
from urllib.parse import urlparse, urlunparse

if TYPE_CHECKING:
    from haproxy_template_ic.config_models import IndexedResourceCollection
    from haproxy_template_ic.credentials import Credentials

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
from tenacity import (
    AsyncRetrying,
    stop_after_attempt,
    wait_exponential_jitter,
    retry_if_exception,
)
from haproxy_template_ic.tracing import (
    trace_dataplane_operation,
    add_span_attributes,
    record_span_event,
    set_span_error,
)

# Import HAProxy Dataplane API v3 client generated with openapi-python-client
from haproxy_dataplane_v3 import AuthenticatedClient
from haproxy_dataplane_v3.api.information import get_info
from haproxy_dataplane_v3.api.configuration import (
    get_configuration_version,
    get_ha_proxy_configuration,
)
from haproxy_dataplane_v3.api.backend import (
    get_backends,
)
from haproxy_dataplane_v3.api.frontend import (
    get_frontends,
)
from haproxy_dataplane_v3.api.global_ import get_global
from haproxy_dataplane_v3.api.defaults import (
    get_defaults_sections,
)
from haproxy_dataplane_v3.api.storage import (
    get_all_storage_map_files,
    get_all_storage_ssl_certificates,
    create_storage_map_file,
    delete_storage_map,
    create_storage_ssl_certificate,
    delete_storage_ssl_certificate,
    get_all_storage_general_files,
    create_storage_general_file,
    delete_storage_general_file,
    replace_storage_general_file,
)
from haproxy_dataplane_v3.models.create_storage_map_file_body import (
    CreateStorageMapFileBody,
)
from haproxy_dataplane_v3.models.create_storage_ssl_certificate_body import (
    CreateStorageSSLCertificateBody,
)
from haproxy_dataplane_v3.models.create_storage_general_file_body import (
    CreateStorageGeneralFileBody,
)
from haproxy_dataplane_v3.models.replace_storage_general_file_body import (
    ReplaceStorageGeneralFileBody,
)
from haproxy_dataplane_v3.types import File
from haproxy_dataplane_v3 import errors

logger = logging.getLogger(__name__)


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
            logger.debug(f"🔍 Added production URL: {url}")

    logger.info(f"🔍 Found {len(urls)} production URLs: {urls}")
    return urls


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
            import base64
            import httpx

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

    async def get_version(self) -> Dict[str, Any]:
        """Get HAProxy version information using the generated client."""
        try:
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

        except errors.UnexpectedStatus as e:
            raise DataplaneAPIError(
                f"Failed to get version: {e}",
                endpoint=self.base_url,
                operation="get_version",
                original_error=e,
            ) from e
        except (ConnectionError, TimeoutError, OSError) as e:
            raise DataplaneAPIError(
                f"Network error: {e}",
                endpoint=self.base_url,
                operation="get_version",
                original_error=e,
            ) from e
        except Exception as e:
            raise DataplaneAPIError(
                f"Unexpected error: {e}",
                endpoint=self.base_url,
                operation="get_version",
                original_error=e,
            ) from e

    async def validate_configuration(self, config_content: str) -> None:
        """Validate HAProxy configuration without applying it.

        Uses direct httpx calls since openapi-python-client doesn't support
        text/plain content type for configuration endpoints.

        Raises:
            ValidationError: If configuration validation fails
            DataplaneAPIError: If API communication fails
        """
        import httpx

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
        """Deploy HAProxy configuration and reload.

        Uses direct httpx calls since openapi-python-client doesn't support
        text/plain content type for configuration endpoints.

        This method includes retry logic for transient failures (network issues,
        temporary dataplane unavailability), but excludes validation errors
        from retries since retrying won't fix config errors.
        """
        import httpx

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
                                "force_reload": "true",
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

    async def sync_maps(self, maps: Dict[str, str]) -> None:
        """Synchronize HAProxy map files to storage."""

        metrics = get_metrics_collector()

        with metrics.time_dataplane_api_operation("sync_maps"):
            client = self._get_client()

            try:
                # Get existing maps and create lookup dict
                existing_maps = await get_all_storage_map_files.asyncio(client=client)
                if existing_maps is None:
                    existing_maps = []
                existing_dict = {
                    f.storage_name: f for f in existing_maps if f.storage_name
                }

                target_names = set(maps.keys())
                existing_names = set(existing_dict.keys())

                # Create new maps
                for name in target_names - existing_names:
                    content = maps[name]
                    body = CreateStorageMapFileBody(
                        file_upload=File(
                            payload=io.BytesIO(content.encode("utf-8")),
                            file_name=name,
                            mime_type="text/plain",
                        )
                    )
                    await create_storage_map_file.asyncio(client=client, body=body)
                    logger.debug(f"🗺️ Created map {name}")

                # Update changed maps (always update - no hash comparison available)
                for name in target_names & existing_names:
                    content = maps[name]
                    # For updates, we delete and recreate since replace isn't available
                    await delete_storage_map.asyncio(client=client, name=name)
                    body = CreateStorageMapFileBody(
                        file_upload=File(
                            payload=io.BytesIO(content.encode("utf-8")),
                            file_name=name,
                            mime_type="text/plain",
                        )
                    )
                    await create_storage_map_file.asyncio(client=client, body=body)
                    logger.debug(f"🔄 Updated map {name}")

                # Delete obsolete maps
                for name in existing_names - target_names:
                    await delete_storage_map.asyncio(client=client, name=name)
                    logger.debug(f"🗑️ Deleted map {name}")

                # Record successful sync
                metrics.record_dataplane_api_request("sync_maps", "success")

            except Exception as e:
                metrics.record_dataplane_api_request("sync_maps", "error")
                raise DataplaneAPIError(
                    f"Map sync failed: {e}", operation="sync_maps"
                ) from e

    async def sync_certificates(self, certificates: Dict[str, str]) -> None:
        """Synchronize SSL certificates to storage."""

        metrics = get_metrics_collector()

        with metrics.time_dataplane_api_operation("sync_certificates"):
            client = self._get_client()

            try:
                # Get existing SSL certs and create lookup dict
                existing_certs = await get_all_storage_ssl_certificates.asyncio(
                    client=client
                )
                if existing_certs is None:
                    existing_certs = []
                existing_dict = {
                    f.storage_name: f for f in existing_certs if f.storage_name
                }

                target_names = set(certificates.keys())
                existing_names = set(existing_dict.keys())

                # Create new certificates
                for name in target_names - existing_names:
                    content = certificates[name]
                    body = CreateStorageSSLCertificateBody(
                        file_upload=File(
                            payload=io.BytesIO(content.encode("utf-8")),
                            file_name=name,
                            mime_type="application/x-pem-file",
                        )
                    )
                    await create_storage_ssl_certificate.asyncio(
                        client=client, body=body
                    )
                    logger.debug(f"🔐 Created certificate {name}")

                # Update changed certificates (always update - no hash comparison available)
                for name in target_names & existing_names:
                    content = certificates[name]
                    # For updates, we delete and recreate since replace isn't available
                    await delete_storage_ssl_certificate.asyncio(
                        client=client, name=name
                    )
                    body = CreateStorageSSLCertificateBody(
                        file_upload=File(
                            payload=io.BytesIO(content.encode("utf-8")),
                            file_name=name,
                            mime_type="application/x-pem-file",
                        )
                    )
                    await create_storage_ssl_certificate.asyncio(
                        client=client, body=body
                    )
                    logger.debug(f"🔄 Updated certificate {name}")

                # Delete obsolete certificates
                for name in existing_names - target_names:
                    await delete_storage_ssl_certificate.asyncio(
                        client=client, name=name
                    )
                    logger.debug(f"🗑️ Deleted certificate {name}")

                # Record successful sync
                metrics.record_dataplane_api_request("sync_certificates", "success")

            except Exception as e:
                metrics.record_dataplane_api_request("sync_certificates", "error")
                raise DataplaneAPIError(
                    f"Certificate sync failed: {e}", operation="sync_certificates"
                ) from e

    async def sync_files(self, files: Dict[str, str]) -> None:
        """Synchronize general-purpose files to HAProxy storage."""

        metrics = get_metrics_collector()

        with metrics.time_dataplane_api_operation("sync_files"):
            client = self._get_client()

            try:
                # Get existing general files and create lookup dict
                existing_files = await get_all_storage_general_files.asyncio(
                    client=client
                )
                if existing_files is None:
                    existing_files = []
                existing_dict = {
                    f.storage_name: f for f in existing_files if f.storage_name
                }

                target_names = set(files.keys())
                existing_names = set(existing_dict.keys())

                # Create new files
                for name in target_names - existing_names:
                    content = files[name]
                    body = CreateStorageGeneralFileBody(
                        file_upload=File(
                            payload=io.BytesIO(content.encode("utf-8")),
                            file_name=name,
                            mime_type="text/plain",
                        )
                    )
                    await create_storage_general_file.asyncio(client=client, body=body)
                    logger.debug(f"📄 Created file {name}")

                # Update changed files (always update - no hash comparison available)
                for name in target_names & existing_names:
                    content = files[name]
                    body = ReplaceStorageGeneralFileBody(
                        file_upload=File(
                            payload=io.BytesIO(content.encode("utf-8")),
                            file_name=name,
                            mime_type="text/plain",
                        )
                    )
                    await replace_storage_general_file.asyncio(
                        client=client, name=name, body=body
                    )
                    logger.debug(f"📝 Updated file {name}")

                # Delete obsolete files
                for name in existing_names - target_names:
                    await delete_storage_general_file.asyncio(client=client, name=name)
                    logger.debug(f"🗑️ Deleted file {name}")

                # Record successful sync
                metrics.record_dataplane_api_request("sync_files", "success")

            except Exception as e:
                metrics.record_dataplane_api_request("sync_files", "error")
                raise DataplaneAPIError(
                    f"File sync failed: {e}", operation="sync_files"
                ) from e

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
            logger.debug(f"Could not fetch current configuration: {e}")
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
                    version_response = await get_configuration_version.asyncio(
                        client=client
                    )
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

    async def fetch_structured_configuration(self) -> Dict[str, Any]:
        """Fetch structured configuration components from this HAProxy instance.

        Returns:
            Dictionary containing:
            - backends: List of backend configurations
            - frontends: List of frontend configurations
            - defaults: List of defaults sections
            - global: Global configuration section

        Raises:
            DataplaneAPIError: If fetching configuration fails
        """
        metrics = get_metrics_collector()

        with metrics.time_dataplane_api_operation("fetch_structured"):
            client = self._get_client()

            try:
                # Fetch all components with timing
                with metrics.time_dataplane_api_operation("fetch_backends"):
                    backends = await get_backends.asyncio(client=client) or []

                with metrics.time_dataplane_api_operation("fetch_frontends"):
                    frontends = await get_frontends.asyncio(client=client) or []

                with metrics.time_dataplane_api_operation("fetch_defaults"):
                    defaults = await get_defaults_sections.asyncio(client=client) or []

                with metrics.time_dataplane_api_operation("fetch_global"):
                    global_config = await get_global.asyncio(client=client)

                # Record successful fetch
                metrics.record_dataplane_api_request("fetch_structured", "success")

                # Record component counts
                add_span_attributes(
                    backends_count=len(backends),
                    frontends_count=len(frontends),
                    defaults_count=len(defaults),
                    has_global=global_config is not None,
                )

                return {
                    "backends": backends,
                    "frontends": frontends,
                    "defaults": defaults,
                    "global": global_config,
                }
            except Exception as e:
                metrics.record_dataplane_api_request("fetch_structured", "error")
                logger.debug(f"Could not fetch structured configuration: {e}")
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

    def _prepare_sync_content(
        self, config_context: HAProxyConfigContext
    ) -> Tuple[Dict[str, str], Dict[str, str], Dict[str, str]]:
        """Prepare content for synchronization."""
        return (
            {rc.filename: rc.content for rc in config_context.rendered_maps},
            {rc.filename: rc.content for rc in config_context.rendered_certificates},
            {rc.filename: rc.content for rc in config_context.rendered_files},
        )

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
            logger.info(f"Syncing {len(maps)} maps to {url}")
            await client.sync_maps(maps)

        if certificates:
            logger.info(f"Syncing {len(certificates)} certificates to {url}")
            await client.sync_certificates(certificates)

        if files:
            logger.info(f"Syncing {len(files)} files to {url}")
            await client.sync_files(files)

    async def _validate_configuration(self, config: str) -> None:
        """Validate configuration using the validation instance."""
        validation_client = DataplaneClient(
            self.validation_url,
            auth=(
                self.credentials.validation.username,
                self.credentials.validation.password.get_secret_value(),
            ),
        )

        logger.info(f"Validating configuration at {self.validation_url}")
        try:
            await validation_client.validate_configuration(config)
        except Exception as e:
            raise ValidationError(f"Configuration validation failed: {e}") from e

    def _compare_structured_configs(
        self, current: Dict[str, Any], new: Dict[str, Any]
    ) -> List[str]:
        """Compare two structured configurations and return list of changes.

        Args:
            current: Current structured configuration
            new: New structured configuration

        Returns:
            List of change descriptions, empty if configs are identical
        """
        import time

        start_time = time.time()
        changes: List[str] = []

        # Helper function to convert to dict if has to_dict method
        def to_dict_safe(obj):
            return obj.to_dict() if hasattr(obj, "to_dict") else obj

        # Compare backends - optimized with dict comprehensions
        current_backends = {
            b.name: to_dict_safe(b)
            for b in current.get("backends", [])
            if hasattr(b, "name")
        }
        new_backends = {
            b.name: to_dict_safe(b)
            for b in new.get("backends", [])
            if hasattr(b, "name")
        }

        # Find changes in backends efficiently
        current_names = set(current_backends.keys())
        new_names = set(new_backends.keys())

        changes.extend(f"remove backend {name}" for name in current_names - new_names)
        changes.extend(f"add backend {name}" for name in new_names - current_names)
        changes.extend(
            f"modify backend {name}"
            for name in current_names & new_names
            if current_backends[name] != new_backends[name]
        )

        # Compare frontends - same optimization
        current_frontends = {
            f.name: to_dict_safe(f)
            for f in current.get("frontends", [])
            if hasattr(f, "name")
        }
        new_frontends = {
            f.name: to_dict_safe(f)
            for f in new.get("frontends", [])
            if hasattr(f, "name")
        }

        current_names = set(current_frontends.keys())
        new_names = set(new_frontends.keys())

        changes.extend(f"remove frontend {name}" for name in current_names - new_names)
        changes.extend(f"add frontend {name}" for name in new_names - current_names)
        changes.extend(
            f"modify frontend {name}"
            for name in current_names & new_names
            if current_frontends[name] != new_frontends[name]
        )

        # Compare defaults sections
        current_defaults = [to_dict_safe(d) for d in current.get("defaults", [])]
        new_defaults = [to_dict_safe(d) for d in new.get("defaults", [])]

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

        # Compare global section
        current_global = to_dict_safe(current.get("global"))
        new_global = to_dict_safe(new.get("global"))

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
        client = DataplaneClient(
            url,
            auth=(
                self.credentials.dataplane.username,
                self.credentials.dataplane.password.get_secret_value(),
            ),
        )

        # Sync auxiliary content first (maps, certs, files)
        await self._sync_content_to_client(
            client, maps_to_sync, certificates_to_sync, files_to_sync, url
        )

        # Fetch current structured config from production instance
        try:
            production_structured = await client.fetch_structured_configuration()

            # Compare structured configurations
            changes_needed = self._compare_structured_configs(
                production_structured, validation_structured
            )

            if not changes_needed:
                # No changes needed - skip deployment
                logger.info(f"⏭️  No structural changes for {url}, skipping deployment")
                return {"method": "skipped", "version": "unchanged"}
            else:
                # Changes detected - deploy
                logger.debug(
                    f"📝 {len(changes_needed)} changes detected for {url}: {', '.join(changes_needed[:5])}"
                )
                version = await client.deploy_configuration(config)
                return {"method": "structured", "version": version}

        except Exception as fetch_error:
            # Fallback to conditional deployment if structured comparison fails
            logger.warning(
                f"⚠️  Structured comparison failed for {url}, falling back to conditional: {fetch_error}"
            )
            try:
                version = await client.deploy_configuration_conditionally(config)
                return {"method": "conditional", "version": version}
            except Exception as conditional_error:
                # Final fallback to regular deployment
                logger.warning(
                    f"⚠️  Conditional deployment also failed for {url}, using regular deployment: {conditional_error}"
                )
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
            except Exception:  # nosec B110
                pass
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

        # Step 1: Sync content to validation instance and validate
        validation_client = DataplaneClient(
            self.validation_url,
            auth=(
                self.credentials.validation.username,
                self.credentials.validation.password.get_secret_value(),
            ),
        )

        logger.info("🔍 Validating configuration and syncing auxiliary content")
        await self._sync_content_to_client(
            validation_client,
            maps_to_sync,
            certificates_to_sync,
            files_to_sync,
            "validation instance",
        )
        await self._validate_configuration(config)

        # Step 2: Deploy config to validation instance and fetch structured components
        logger.info(
            "📤 Deploying config to validation instance for structured comparison"
        )
        await validation_client.deploy_configuration(config)

        # Fetch structured config from validation instance
        logger.info("🔍 Fetching structured configuration from validation instance")
        validation_structured = await validation_client.fetch_structured_configuration()

        # Step 3: Deploy to production instances using structured comparison
        results: Dict[str, Any] = {
            "successful": 0,
            "failed": 0,
            "skipped": 0,
            "errors": [],
        }

        logger.info(f"🚀 Deploying to {len(self.production_urls)} production instances")

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
        if results["skipped"] > 0:
            logger.info(
                f"🎯 Sync complete: {results['successful']} deployed, "
                f"{results['skipped']} skipped (unchanged), "
                f"{results['failed']} failed out of {total_instances} instances"
            )
        else:
            logger.info(
                f"Sync complete: {results['successful']} successful, {results['failed']} failed"
            )

        return results
