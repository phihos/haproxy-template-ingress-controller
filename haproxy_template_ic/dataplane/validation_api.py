"""
Validation and deployment API operations for HAProxy Dataplane API.

This module handles configuration validation and deployment
for HAProxy configuration changes.
"""

import structlog
from dataclasses import asdict
from typing import Any

from haproxy_template_ic.core.logging import autolog
from haproxy_template_ic.metrics import MetricsCollector
from haproxy_template_ic.tracing import record_span_event, set_span_error
from haproxy_dataplane_v3.models import Information

from .adapter import (
    get_configuration_version,
    get_ha_proxy_configuration,
    post_haproxy_configuration,
    get_info,
    get_haproxy_process_info,
    APIResponse,
)
from .endpoint import DataplaneEndpoint
from .types import (
    DataplaneAPIError,
    ValidationError,
    ValidationDeploymentResult,
)
from .utils import (
    handle_dataplane_errors,
    parse_validation_error_details,
    extract_exception_origin,
)

__all__ = [
    "ValidationAPI",
]

logger = structlog.get_logger(__name__)


class ValidationAPI:
    """Validation and deployment API operations for HAProxy Dataplane API."""

    def __init__(
        self,
        endpoint: DataplaneEndpoint,
        metrics: MetricsCollector,
    ):
        """Initialize validation API.

        Args:
            endpoint: Dataplane endpoint for error context
            metrics: MetricsCollector instance for metrics tracking
        """
        self.endpoint = endpoint
        self.metrics = metrics

    @handle_dataplane_errors("get_version")
    async def get_version(self) -> dict[str, Any]:
        """Get HAProxy version and runtime information.

        Returns:
            Dictionary containing version and runtime information

        Raises:
            DataplaneAPIError: If version retrieval fails
        """
        metrics = self.metrics

        with metrics.time_dataplane_api_operation("get_version"):
            try:
                info_response: APIResponse[Information] = await get_info(
                    endpoint=self.endpoint
                )
                process_info_response = await get_haproxy_process_info(
                    endpoint=self.endpoint
                )

                info = info_response.content
                process_info = process_info_response.content

                result = {
                    "api_version": getattr(info, "api_version", "unknown"),
                    "build_date": getattr(info, "build_date", "unknown"),
                    "version": getattr(info, "version", "unknown"),
                    "haproxy": {
                        "version": getattr(process_info, "version", "unknown"),
                        "release_date": getattr(
                            process_info, "release_date", "unknown"
                        ),
                        "uptime": getattr(process_info, "uptime", "unknown"),
                    },
                }

                metrics.record_dataplane_api_request("get_version", "success")
                record_span_event("version_retrieved", result)
                return result

            except Exception as e:
                metrics.record_dataplane_api_request("get_version", "error")
                set_span_error(e, "Version retrieval failed")
                raise DataplaneAPIError(
                    f"Failed to get version: {e}",
                    endpoint=self.endpoint,
                    operation="get_version",
                    original_error=e,
                ) from e

    @handle_dataplane_errors("validate_configuration")
    @autolog()
    async def validate_configuration(self, config_content: str) -> None:
        """Validate HAProxy configuration without applying it.

        Args:
            config_content: The configuration content to validate

        Raises:
            ValidationError: If configuration validation fails
            DataplaneAPIError: If validation request fails
        """
        if not config_content:
            raise ValidationError(
                "Configuration content cannot be empty",
                endpoint=self.endpoint,
            )

        # Ensure configuration ends with newline to avoid "Missing LF on last line" error
        if not config_content.endswith("\n"):
            config_content = config_content + "\n"

        metrics = self.metrics

        await logger.ainfo(f"Validating configuration ({len(config_content)} bytes)")

        with metrics.time_dataplane_api_operation("validate"):
            try:
                # Validate only, don't apply (skip_reload=true)
                response = await post_haproxy_configuration(
                    endpoint=self.endpoint,
                    body=config_content,
                    skip_reload=True,
                    only_validate=True,
                )

                # Extract reload information from adapter response (should be empty for validation-only)
                reload_info = response.reload_info
                if reload_info.reload_triggered:
                    await logger.ainfo(
                        f"Unexpected reload triggered during validation: {reload_info.reload_id}"
                    )

                metrics.record_dataplane_api_request("validate", "success")
                record_span_event(
                    "configuration_validated",
                    {"size": len(config_content)},
                )
                await logger.ainfo("Configuration validation successful")

            except (ValidationError, DataplaneAPIError):
                # ValidationError/DataplaneAPIError from adapter already has proper details, re-raise it
                metrics.record_dataplane_api_request("validate", "error")
                raise
            except Exception as e:
                metrics.record_dataplane_api_request("validate", "error")
                set_span_error(e, "Configuration validation failed")

                # Parse validation error details for non-ValidationError exceptions
                error_response = str(e)
                validation_details, error_line, error_context = (
                    parse_validation_error_details(error_response, config_content)
                )

                raise ValidationError(
                    f"Configuration validation failed: {validation_details}",
                    endpoint=self.endpoint,
                    config_size=len(config_content),
                    validation_details=validation_details,
                    error_line=error_line,
                    config_content=config_content,
                    error_context=error_context,
                    original_error=e,
                ) from e

    @handle_dataplane_errors("deploy_configuration")
    @autolog()
    async def deploy_configuration(
        self, config_content: str
    ) -> ValidationDeploymentResult:
        """Deploy HAProxy configuration with reload.

        Args:
            config_content: The configuration content to deploy

        Returns:
            Dictionary containing deployment results and timing

        Raises:
            ValidationError: If configuration validation fails
            DataplaneAPIError: If deployment fails
        """
        if not config_content:
            raise ValidationError(
                "Configuration content cannot be empty",
                endpoint=self.endpoint,
            )

        # Ensure configuration ends with newline to avoid "Missing LF on last line" error
        if not config_content.endswith("\n"):
            config_content = config_content + "\n"

        metrics = self.metrics

        await logger.ainfo(f"Deploying configuration ({len(config_content)} bytes)")

        with metrics.time_dataplane_api_operation("deploy"):
            try:
                response = await get_configuration_version(endpoint=self.endpoint)
                version = response.content

                # Deploy with reload
                # If version is None, fall back to version=1 as default
                if version is None:
                    version = 1

                # Deploy configuration - adapter handles error checking
                response = await post_haproxy_configuration(
                    endpoint=self.endpoint,
                    body=config_content,
                    skip_reload=False,
                    only_validate=False,
                    version=version,
                )
                # Extract reload info from adapter response
                reload_info = response.reload_info

                deployment_info = ValidationDeploymentResult(
                    size=len(config_content),
                    status="success",
                    version=str(version) if version is not None else "unknown",
                    reload_info=reload_info,
                )

                metrics.record_dataplane_api_request("deploy", "success")
                record_span_event("configuration_deployed", asdict(deployment_info))
                await logger.ainfo(
                    f"Configuration deployment successful: {asdict(deployment_info)}"
                )

                return deployment_info

            except (ValidationError, DataplaneAPIError):
                # ValidationError/DataplaneAPIError from adapter already has proper details, re-raise it
                metrics.record_dataplane_api_request("deploy", "error")
                raise
            except Exception as e:
                metrics.record_dataplane_api_request("deploy", "error")
                set_span_error(e, "Configuration deployment failed")

                # Parse validation error details if it's a validation failure
                error_response = str(e)
                validation_details, error_line, error_context = (
                    parse_validation_error_details(error_response, config_content)
                )

                if validation_details:
                    # Extract origin details for debugging
                    origin_details = f"\n{extract_exception_origin(e)}"

                    raise ValidationError(
                        f"Configuration deployment failed (validation): {validation_details}{origin_details}",
                        endpoint=self.endpoint,
                        config_size=len(config_content),
                        validation_details=validation_details,
                        error_line=error_line,
                        config_content=config_content,
                        error_context=error_context,
                        original_error=e,
                    ) from e
                else:
                    # Extract origin details for debugging
                    origin_details = f"\n{extract_exception_origin(e)}"

                    raise DataplaneAPIError(
                        f"Configuration deployment failed: {e}{origin_details}",
                        endpoint=self.endpoint,
                        operation="deploy",
                        original_error=e,
                    ) from e

    @handle_dataplane_errors("get_current_configuration")
    async def get_current_configuration(self) -> str | None:
        """Get the current HAProxy configuration.

        Returns:
            Current configuration content as string, or None if not available

        Raises:
            DataplaneAPIError: If configuration retrieval fails
        """
        metrics = self.metrics

        with metrics.time_dataplane_api_operation("get_config"):
            try:
                config_response = await get_ha_proxy_configuration(
                    endpoint=self.endpoint
                )
                config = config_response.content

                if config and hasattr(config, "data"):
                    config_content = config.data.decode("utf-8")
                    metrics.record_dataplane_api_request("get_config", "success")
                    record_span_event(
                        "configuration_retrieved",
                        {"size": len(config_content)},
                    )
                    return config_content
                else:
                    await logger.awarning("No configuration data received")
                    metrics.record_dataplane_api_request("get_config", "empty")
                    return None

            except Exception as e:
                metrics.record_dataplane_api_request("get_config", "error")
                set_span_error(e, "Configuration retrieval failed")
                raise DataplaneAPIError(
                    f"Failed to get current configuration: {e}",
                    endpoint=self.endpoint,
                    operation="get_config",
                    original_error=e,
                ) from e
