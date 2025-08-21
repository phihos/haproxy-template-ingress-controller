"""
HAProxy Dataplane API integration for template synchronization.

This module provides functionality to:
1. Discover HAProxy pods using pod selectors
2. Validate configurations via validation sidecars
3. Deploy configurations to production HAProxy instances
4. Synchronize state across all HAProxy instances

Uses the complete generated HAProxy Dataplane API v3 client for all operations.
"""

import logging
from datetime import datetime, UTC
from typing import Any, Dict, List, Optional, TYPE_CHECKING
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

# Import HAProxy Dataplane API v3 client with built-in lazy loading support
from haproxy_dataplane_v3 import ApiClient, Configuration
from haproxy_dataplane_v3.api import ConfigurationApi, InformationApi, StorageApi
from haproxy_dataplane_v3.exceptions import ApiException, BadRequestException

logger = logging.getLogger(__name__)


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
    """

    def __init__(
        self,
        message: str,
        endpoint: Optional[str] = None,
        config_size: Optional[int] = None,
        validation_details: Optional[str] = None,
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

    def __str__(self) -> str:
        """Return detailed validation error message."""
        base_message = super().__str__()
        detail_parts = []

        if self.config_size:
            detail_parts.append(f"config_size={self.config_size}")
        if self.validation_details:
            detail_parts.append(f"details={self.validation_details}")

        if detail_parts:
            return f"{base_message} [{', '.join(detail_parts)}]"
        return base_message


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

        # Defer configuration creation until first use
        self._configuration = None

    def _get_configuration(self):
        """Lazy initialization of Configuration object."""
        if self._configuration is None:
            logger.debug(f"Creating dataplane configuration for {self.base_url}")
            self._configuration = Configuration(
                host=self.base_url,
                username=self.auth[0],
                password=self.auth[1],
            )
        return self._configuration

    async def get_version(self) -> Dict[str, Any]:
        """Get HAProxy version information using the generated client."""
        try:
            async with ApiClient(self._get_configuration()) as api_client:
                info_api = InformationApi(api_client)
                info_response = await info_api.get_info(_request_timeout=self.timeout)

                # Convert the generated model to dict format expected by existing code
                result = {}
                if hasattr(info_response, "haproxy") and info_response.haproxy:
                    result.update(info_response.haproxy)
                if hasattr(info_response, "api") and info_response.api:
                    result.update(info_response.api)
                if hasattr(info_response, "system") and info_response.system:
                    result.update(info_response.system)

                return result

        except ApiException as e:
            logger.error(f"API error getting version from {self.base_url}: {e}")
            raise DataplaneAPIError(
                f"Failed to get version: {e}",
                endpoint=self.base_url,
                operation="get_version",
                original_error=e,
            ) from e
        except (ConnectionError, TimeoutError, OSError) as e:
            logger.error(f"Network error getting version from {self.base_url}: {e}")
            raise DataplaneAPIError(
                f"Network error: {e}",
                endpoint=self.base_url,
                operation="get_version",
                original_error=e,
            ) from e
        except Exception as e:
            logger.error(f"Unexpected error getting version from {self.base_url}: {e}")
            raise DataplaneAPIError(
                f"Unexpected error: {e}",
                endpoint=self.base_url,
                operation="get_version",
                original_error=e,
            ) from e

    async def validate_configuration(self, config_content: str) -> None:
        """Validate HAProxy configuration without applying it.

        Note: This method does not retry on failures. Validation failures are typically
        due to invalid configuration, so retrying would not help.

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
                    async with ApiClient(self._get_configuration()) as api_client:
                        config_api = ConfigurationApi(api_client)

                        # Use the generated client to validate configuration
                        # Ensure config ends with newline to avoid HAProxy truncation errors
                        config_data = config_content.rstrip() + "\n"
                        await config_api.post_ha_proxy_configuration(
                            data=config_data,
                            only_validate=True,
                            skip_version=True,
                            _request_timeout=self.timeout,
                        )
                        record_span_event("validation_successful")

                except BadRequestException as e:
                    # Handle BadRequestException (configuration validation failed)
                    validation_details = getattr(e, "body", None)
                    logger.warning(f"Configuration validation failed: {e}")
                    if validation_details:
                        logger.warning(f"Validation details: {validation_details}")
                    record_span_event(
                        "validation_failed", {"error": "validation_failed"}
                    )
                    set_span_error(e, "Configuration validation failed")
                    raise ValidationError(
                        f"Configuration validation failed: {e}",
                        endpoint=self.base_url,
                        config_size=len(config_content),
                        validation_details=str(validation_details)
                        if validation_details
                        else None,
                        original_error=e,
                    ) from e
                except (ConnectionError, TimeoutError, OSError) as e:
                    # Handle network-related exceptions
                    record_span_event("validation_failed", {"error": str(e)})
                    set_span_error(e, "Configuration validation failed")
                    logger.error(f"Network error during validation: {e}")
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
                    logger.error(f"Unexpected error during validation: {e}")
                    raise DataplaneAPIError(
                        f"Configuration validation failed: {e}",
                        endpoint=self.base_url,
                        operation="validate",
                        original_error=e,
                    ) from e

    async def deploy_configuration(self, config_content: str) -> str:
        """Deploy HAProxy configuration and reload.

        This method includes retry logic for transient failures (network issues,
        temporary dataplane unavailability), but excludes BadRequestException
        (invalid configuration) from retries since retrying won't fix config errors.
        """
        with trace_dataplane_operation("deploy", self.base_url):
            add_span_attributes(
                config_size=len(config_content), dataplane_url=self.base_url
            )

            metrics = get_metrics_collector()

            async def deployment_operation():
                with metrics.time_dataplane_api_operation("deploy"):
                    async with ApiClient(self._get_configuration()) as api_client:
                        config_api = ConfigurationApi(api_client)

                        # Get current configuration version first
                        current_version = await config_api.get_configuration_version(
                            _request_timeout=self.timeout
                        )

                        # Deploy configuration with reload using generated client
                        # Ensure config ends with newline to avoid HAProxy truncation errors
                        config_data = config_content.rstrip() + "\n"
                        await config_api.post_ha_proxy_configuration(
                            data=config_data,
                            version=current_version,
                            force_reload=True,
                            _request_timeout=self.timeout,
                        )

                        # Get the new configuration version
                        new_version = await config_api.get_configuration_version(
                            _request_timeout=self.timeout
                        )
                        return str(new_version)

            try:
                # Simple retry with tenacity
                async for attempt in AsyncRetrying(
                    stop=stop_after_attempt(5),
                    wait=wait_exponential_jitter(initial=2, max=30),
                    retry=retry_if_exception(
                        lambda e: (
                            (
                                isinstance(e, ApiException) and e.status >= 500
                            )  # Server errors only
                            or (
                                isinstance(e, DataplaneAPIError)
                                and not isinstance(e, ValidationError)
                            )
                        )
                    ),
                ):
                    with attempt:
                        version = await deployment_operation()
                        add_span_attributes(config_version=version)
                        record_span_event("deployment_successful", {"version": version})
                        return version
            except Exception as e:
                record_span_event("deployment_failed", {"error": str(e)})
                set_span_error(e, "Configuration deployment failed")
                logger.error(f"Configuration deployment failed: {e}")
                raise DataplaneAPIError(
                    f"Configuration deployment failed: {e}",
                    endpoint=self.base_url,
                    operation="deploy",
                    original_error=e,
                ) from e

        # This should never be reached but satisfies mypy
        raise DataplaneAPIError(
            "Unexpected error in deployment", endpoint=self.base_url, operation="deploy"
        )

    async def sync_maps(self, maps: Dict[str, str]) -> None:
        """Synchronize HAProxy map files to storage."""

        metrics = get_metrics_collector()

        with metrics.time_dataplane_api_operation("sync_maps"):
            async with ApiClient(self._get_configuration()) as api_client:
                storage_api = StorageApi(api_client)

                try:
                    # Get existing maps and create lookup dict
                    existing_maps = await storage_api.get_all_storage_maps(
                        _request_timeout=self.timeout
                    )
                    existing_dict = {f.storage_name: f for f in existing_maps}

                    target_names = set(maps.keys())
                    existing_names = set(existing_dict.keys())

                    # Create new maps
                    for name in target_names - existing_names:
                        content = maps[name]
                        await storage_api.create_storage_map_file(
                            file_upload=(name, content.encode("utf-8")),
                            _request_timeout=self.timeout,
                        )
                        logger.debug(f"🗺️ Created map {name}")

                    # Update changed maps (always update - no hash comparison available)
                    for name in target_names & existing_names:
                        content = maps[name]
                        await storage_api.replace_storage_map_file(
                            name=name,
                            file_upload=(name, content.encode("utf-8")),
                            skip_reload=True,
                            _request_timeout=self.timeout,
                        )
                        logger.debug(f"🔄 Updated map {name}")

                    # Delete obsolete maps
                    for name in existing_names - target_names:
                        await storage_api.delete_storage_map_file(
                            name=name, _request_timeout=self.timeout
                        )
                        logger.debug(f"🗑️ Deleted map {name}")

                    # Record successful sync
                    metrics.record_dataplane_api_request("sync_maps", "success")

                except Exception as e:
                    metrics.record_dataplane_api_request("sync_maps", "error")
                    logger.error(f"Map sync failed: {e}")
                    raise DataplaneAPIError(
                        f"Map sync failed: {e}", operation="sync_maps"
                    ) from e

    async def sync_certificates(self, certificates: Dict[str, str]) -> None:
        """Synchronize SSL certificates to storage."""

        metrics = get_metrics_collector()

        with metrics.time_dataplane_api_operation("sync_certificates"):
            async with ApiClient(self._get_configuration()) as api_client:
                storage_api = StorageApi(api_client)

                try:
                    # Get existing SSL certs and create lookup dict
                    existing_certs = await storage_api.get_all_ssl_certificates(
                        _request_timeout=self.timeout
                    )
                    existing_dict = {f.storage_name: f for f in existing_certs}

                    target_names = set(certificates.keys())
                    existing_names = set(existing_dict.keys())

                    # Create new certificates
                    for name in target_names - existing_names:
                        content = certificates[name]
                        await storage_api.create_ssl_certificate(
                            file_upload=(name, content.encode("utf-8")),
                            _request_timeout=self.timeout,
                        )
                        logger.debug(f"🔐 Created certificate {name}")

                    # Update changed certificates (always update - no hash comparison available)
                    for name in target_names & existing_names:
                        content = certificates[name]
                        await storage_api.replace_ssl_certificate(
                            name=name,
                            file_upload=(name, content.encode("utf-8")),
                            skip_reload=True,
                            _request_timeout=self.timeout,
                        )
                        logger.debug(f"🔄 Updated certificate {name}")

                    # Delete obsolete certificates
                    for name in existing_names - target_names:
                        await storage_api.delete_ssl_certificate(
                            name=name, _request_timeout=self.timeout
                        )
                        logger.debug(f"🗑️ Deleted certificate {name}")

                    # Record successful sync
                    metrics.record_dataplane_api_request("sync_certificates", "success")

                except Exception as e:
                    metrics.record_dataplane_api_request("sync_certificates", "error")
                    logger.error(f"Certificate sync failed: {e}")
                    raise DataplaneAPIError(
                        f"Certificate sync failed: {e}", operation="sync_certificates"
                    ) from e

    async def sync_files(self, files: Dict[str, str]) -> None:
        """Synchronize general-purpose files to HAProxy storage."""

        metrics = get_metrics_collector()

        with metrics.time_dataplane_api_operation("sync_files"):
            async with ApiClient(self._get_configuration()) as api_client:
                storage_api = StorageApi(api_client)

                try:
                    # Get existing files and create lookup dict
                    existing_files = await storage_api.get_all_storage_general_files(
                        _request_timeout=self.timeout
                    )
                    existing_dict = {f.storage_name: f for f in existing_files}

                    target_names = set(files.keys())
                    existing_names = set(existing_dict.keys())

                    # Create new files
                    for name in target_names - existing_names:
                        content = files[name]
                        await storage_api.create_storage_general_file(
                            file_upload=(name, content.encode("utf-8")),
                            _request_timeout=self.timeout,
                        )
                        logger.debug(f"📄 Created file {name}")

                    # Update changed files (always update - no hash comparison reliable)
                    for name in target_names & existing_names:
                        content = files[name]
                        await storage_api.replace_storage_general_file(
                            name=name,
                            file_upload=(name, content.encode("utf-8")),
                            skip_reload=True,
                            _request_timeout=self.timeout,
                        )
                        logger.debug(f"📝 Updated file {name}")

                    # Delete obsolete files
                    for name in existing_names - target_names:
                        await storage_api.delete_storage_general_file(
                            name=name, _request_timeout=self.timeout
                        )
                        logger.debug(f"🗑️ Deleted file {name}")

                    # Record successful sync
                    metrics.record_dataplane_api_request("sync_files", "success")

                except Exception as e:
                    metrics.record_dataplane_api_request("sync_files", "error")
                    logger.error(f"File sync failed: {e}")
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
            logger.error(f"Validation failed: {e}")
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
                logger.error(f"❌ Failed to deploy to {url}: {e}")

        logger.info(
            f"Sync complete: {results['successful']} successful, {results['failed']} failed"
        )
        return results
