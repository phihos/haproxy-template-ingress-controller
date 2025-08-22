"""
HAProxy Dataplane API integration for template synchronization.

This module provides functionality to:
1. Discover HAProxy pods using pod selectors
2. Validate configurations via validation sidecars
3. Deploy configurations to production HAProxy instances
4. Synchronize state across all HAProxy instances

Uses the complete generated HAProxy Dataplane API v3 client for all operations.
"""

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
    """Simple deployment tracking per endpoint."""

    def __init__(self):
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
                annotations.get("haproxy-template-ic/dataplane-port", "5555")
                if isinstance(annotations, dict)
                else "5555"
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
        timeout: float = 30.0,
        auth: tuple[str, str] = ("admin", "adminpass"),
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

    def _get_client(self):
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
                    wait=wait_exponential_jitter(initial=2, max=30),
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

    async def sync_configuration(
        self, config_context: HAProxyConfigContext
    ) -> Dict[str, Any]:
        """Synchronize configuration to all endpoints."""
        if not config_context.rendered_config:
            raise DataplaneAPIError("No rendered HAProxy configuration available")

        config = config_context.rendered_config.content

        # Prepare all content for synchronization using filenames directly
        maps_to_sync = {rc.filename: rc.content for rc in config_context.rendered_maps}
        certificates_to_sync = {
            rc.filename: rc.content for rc in config_context.rendered_certificates
        }
        files_to_sync = {
            rc.filename: rc.content for rc in config_context.rendered_files
        }

        # Step 1: Sync all content to validation instance first
        validation_client = DataplaneClient(
            self.validation_url,
            auth=(
                self.credentials.validation.username,
                self.credentials.validation.password.get_secret_value(),
            ),
        )

        # Sync maps, certificates, and files to validation instance
        if maps_to_sync:
            logger.info(f"Syncing {len(maps_to_sync)} maps to validation instance")
            await validation_client.sync_maps(maps_to_sync)

        if certificates_to_sync:
            logger.info(
                f"Syncing {len(certificates_to_sync)} certificates to validation instance"
            )
            await validation_client.sync_certificates(certificates_to_sync)

        if files_to_sync:
            logger.info(f"Syncing {len(files_to_sync)} files to validation instance")
            await validation_client.sync_files(files_to_sync)

        # Step 2: Validate configuration at localhost
        logger.info(f"Validating configuration at {self.validation_url}")

        try:
            await validation_client.validate_configuration(config)
        except Exception as e:
            raise ValidationError(f"Configuration validation failed: {e}") from e

        # Step 3: Deploy to production instances
        results: Dict[str, Any] = {"successful": 0, "failed": 0, "errors": []}

        for url in self.production_urls:
            client = DataplaneClient(
                url,
                auth=(
                    self.credentials.dataplane.username,
                    self.credentials.dataplane.password.get_secret_value(),
                ),
            )
            try:
                # Sync all content first, then deploy configuration
                if maps_to_sync:
                    logger.info(f"Syncing {len(maps_to_sync)} maps to {url}")
                    await client.sync_maps(maps_to_sync)

                if certificates_to_sync:
                    logger.info(
                        f"Syncing {len(certificates_to_sync)} certificates to {url}"
                    )
                    await client.sync_certificates(certificates_to_sync)

                if files_to_sync:
                    logger.info(f"Syncing {len(files_to_sync)} files to {url}")
                    await client.sync_files(files_to_sync)

                version = await client.deploy_configuration(config)
                self.deployment_history.record(url, version, True)
                results["successful"] += 1
                logger.info(f"✅ Deployed to {url}, version: {version}")
            except Exception as e:
                self.deployment_history.record(url, "unknown", False, str(e))
                results["failed"] += 1
                results["errors"].append(f"{url}: {e}")

                # Enhanced error logging with config context if available
                error_msg = f"❌ Failed to deploy to {url}: {e}"
                if isinstance(
                    e, DataplaneAPIError
                ) and "Configuration context around error:" in str(e):
                    # The error already contains context, log it as-is
                    logger.error(error_msg)
                else:
                    # Try to extract context for other types of errors
                    try:
                        error_line, error_context = parse_validation_error_details(
                            str(e), config
                        )
                        if error_context:
                            error_msg += f"\n\nConfiguration context around error:\n{error_context}"
                    except Exception:  # nosec B110
                        # If context extraction fails, continue with original error
                        pass
                    logger.error(error_msg)

        logger.info(
            f"Sync complete: {results['successful']} successful, {results['failed']} failed"
        )
        return results
