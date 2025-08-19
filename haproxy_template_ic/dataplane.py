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
import logging
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

import kr8s
from kr8s.objects import Pod

from haproxy_template_ic.config_models import HAProxyConfigContext, PodSelector
from haproxy_template_ic.metrics import get_metrics_collector
from tenacity import (
    AsyncRetrying,
    stop_after_attempt,
    wait_exponential_jitter,
    retry_if_exception,
)
from haproxy_template_ic.tracing import (
    trace_async_function,
    trace_dataplane_operation,
    add_span_attributes,
    record_span_event,
    set_span_error,
)

# Import HAProxy Dataplane API v3 client with built-in lazy loading support
from haproxy_dataplane_v3 import ApiClient, Configuration
from haproxy_dataplane_v3.api import ConfigurationApi, InformationApi
from haproxy_dataplane_v3.exceptions import ApiException, BadRequestException

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class HAProxyInstance:
    """Represents a single HAProxy instance with Dataplane API access."""

    pod: Pod
    dataplane_url: str
    is_validation_sidecar: bool = False

    @property
    def name(self) -> str:
        """Get a human-readable name for this instance."""
        return f"{self.pod.namespace}/{self.pod.name}"


@dataclass(frozen=True)
class SyncResult:
    """Result of a synchronization operation."""

    success: bool
    instance: HAProxyInstance
    error: Optional[str] = None
    config_version: Optional[str] = None


class DataplaneAPIError(Exception):
    """Base exception for Dataplane API errors."""

    pass


class ValidationError(DataplaneAPIError):
    """Raised when configuration validation fails."""

    pass


class HAProxyPodDiscovery:
    """Discovers HAProxy pods matching the configured selector."""

    def __init__(self, pod_selector: PodSelector, namespace: Optional[str] = None):
        self.pod_selector = pod_selector
        self.namespace = namespace

    @trace_async_function(
        span_name="discover_haproxy_instances",
        attributes={"operation.category": "pod_discovery"},
    )
    async def discover_instances(self) -> List[HAProxyInstance]:
        """Discover all HAProxy instances matching the pod selector."""
        add_span_attributes(
            selector_labels=str(self.pod_selector.match_labels),
            namespace=self.namespace or "all",
        )
        try:
            # Build label selector from pod_selector.match_labels
            label_selector = ",".join(
                [
                    f"{key}={value}"
                    for key, value in self.pod_selector.match_labels.items()
                ]
            )

            # Get pods matching the selector
            pods = kr8s.get(
                "pods", label_selector=label_selector, namespace=self.namespace
            )

            instances = []
            for pod in pods:
                if pod.status.phase != "Running":
                    logger.debug(f"Skipping non-running pod {pod.namespace}/{pod.name}")
                    continue

                # Determine if this is a validation sidecar
                is_validation = self._is_validation_sidecar(pod)

                # Build Dataplane API URL
                dataplane_url = self._build_dataplane_url(pod)

                instance = HAProxyInstance(
                    pod=pod,
                    dataplane_url=dataplane_url,
                    is_validation_sidecar=is_validation,
                )
                instances.append(instance)

            add_span_attributes(
                total_instances=len(instances),
                production_instances=len(
                    [i for i in instances if not i.is_validation_sidecar]
                ),
                validation_instances=len(
                    [i for i in instances if i.is_validation_sidecar]
                ),
            )
            record_span_event(
                "pod_discovery_completed",
                {"total_pods": len(instances), "label_selector": label_selector},
            )
            logger.info(f"Discovered {len(instances)} HAProxy instances")
            return instances

        except Exception as e:
            record_span_event("pod_discovery_failed", {"error": str(e)})
            set_span_error(e, "Failed to discover HAProxy instances")
            logger.error(f"Failed to discover HAProxy instances: {e}")
            raise DataplaneAPIError(f"Pod discovery failed: {e}") from e

    def _is_validation_sidecar(self, pod: Pod) -> bool:
        """Determine if a pod is a validation sidecar."""
        # Check for validation sidecar annotation/label
        return (
            pod.metadata.get("labels", {}).get("haproxy-template-ic/role")
            == "validation"
        )

    def _build_dataplane_url(self, pod: Pod) -> str:
        """Build the Dataplane API URL for a pod."""
        # Default Dataplane API port is 5555
        dataplane_port = pod.metadata.get("annotations", {}).get(
            "haproxy-template-ic/dataplane-port", "5555"
        )

        # Use pod IP for direct access
        pod_ip = pod.status.podIP
        if not pod_ip:
            raise DataplaneAPIError(f"Pod {pod.namespace}/{pod.name} has no IP address")

        # Return the complete URL with v3 base path (this will be the host for Configuration)
        return f"http://{pod_ip}:{dataplane_port}"


class DataplaneClient:
    """Wrapper around the generated HAProxy Dataplane API v3 client."""

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
        normalized_url = base_url.rstrip("/")
        if not normalized_url.endswith("/v3"):
            normalized_url += "/v3"

        self.base_url = normalized_url
        self.timeout = timeout
        self.auth = auth

        # Defer configuration creation until first use
        self._configuration = None

    def _get_configuration(self):
        """Lazy initialization of Configuration object."""
        if self._configuration is None:
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
            raise DataplaneAPIError(f"Failed to get version: {e}") from e
        except Exception as e:
            logger.error(f"Unexpected error getting version from {self.base_url}: {e}")
            raise DataplaneAPIError(f"Unexpected error: {e}") from e

    async def validate_configuration(self, config_content: str) -> bool:
        """Validate HAProxy configuration without applying it."""
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
                        return True

                except BadRequestException as e:
                    # Handle BadRequestException (configuration validation failed)
                    logger.warning(f"Configuration validation failed: {e}")
                    if hasattr(e, "body") and e.body:
                        logger.warning(f"Validation error details: {e.body}")
                    record_span_event(
                        "validation_failed", {"error": "validation_failed"}
                    )
                    return False
                except (ApiException, Exception) as e:
                    record_span_event("validation_failed", {"error": str(e)})
                    set_span_error(e, "Configuration validation failed")
                    return False

    async def deploy_configuration(self, config_content: str) -> str:
        """Deploy HAProxy configuration and reload."""
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
                        lambda e: isinstance(e, (ApiException, DataplaneAPIError))
                        and not isinstance(e, BadRequestException)
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
                raise DataplaneAPIError(f"Configuration deployment failed: {e}") from e

        # This should never be reached but satisfies mypy
        raise DataplaneAPIError("Unexpected error in deployment")


class ConfigSynchronizer:
    """Orchestrates configuration synchronization across HAProxy instances."""

    def __init__(
        self,
        pod_discovery: HAProxyPodDiscovery,
        dataplane_auth: tuple[str, str] = ("admin", "adminpass"),
    ):
        self.pod_discovery = pod_discovery
        self.dataplane_auth = dataplane_auth

    @trace_async_function(
        span_name="synchronize_configuration",
        attributes={"operation.category": "config_sync"},
    )
    async def synchronize_configuration(
        self, config_context: HAProxyConfigContext
    ) -> List[SyncResult]:
        """Synchronize rendered configuration to all HAProxy instances."""
        logger.info("Starting configuration synchronization")
        record_span_event("sync_started")

        # Discover all HAProxy instances
        instances = await self.pod_discovery.discover_instances()
        if not instances:
            logger.warning("No HAProxy instances found for synchronization")
            return []

        # Separate validation sidecars from production instances
        validation_instances = [i for i in instances if i.is_validation_sidecar]
        production_instances = [i for i in instances if not i.is_validation_sidecar]

        logger.info(
            f"Found {len(validation_instances)} validation sidecars, {len(production_instances)} production instances"
        )

        # Generate the complete HAProxy configuration
        haproxy_config = self._build_complete_config(config_context)

        # Step 1: Validate configuration using sidecars
        if validation_instances:
            validation_success = await self._validate_with_sidecars(
                validation_instances, haproxy_config
            )
            if not validation_success:
                raise ValidationError("Configuration validation failed on sidecars")
        else:
            logger.warning("No validation sidecars found - skipping validation step")

        # Step 2: Deploy to production instances
        results = await self._deploy_to_production(production_instances, haproxy_config)

        # Log summary
        successful = [r for r in results if r.success]
        failed = [r for r in results if not r.success]

        add_span_attributes(
            total_results=len(results),
            successful_syncs=len(successful),
            failed_syncs=len(failed),
            validation_instances_count=len(validation_instances),
            production_instances_count=len(production_instances),
        )

        if successful:
            record_span_event(
                "sync_completed_with_successes",
                {"successful_count": len(successful), "failed_count": len(failed)},
            )

        if failed:
            record_span_event(
                "sync_completed_with_failures",
                {"failed_instances": [r.instance.name for r in failed]},
            )

        logger.info(
            f"Synchronization complete: {len(successful)} successful, {len(failed)} failed"
        )

        if failed:
            for result in failed:
                logger.error(f"Failed to sync {result.instance.name}: {result.error}")

        return results

    def _build_complete_config(self, config_context: HAProxyConfigContext) -> str:
        """Build the complete HAProxy configuration from rendered templates."""
        if not config_context.rendered_config:
            raise DataplaneAPIError("No rendered HAProxy configuration available")

        # Start with the main HAProxy config
        config_parts = [config_context.rendered_config.content]

        # Add any additional configuration sections
        # (In the future, this could include dynamically generated backends, etc.)

        return "\n\n".join(config_parts)

    async def _validate_with_sidecars(
        self, validation_instances: List[HAProxyInstance], config: str
    ) -> bool:
        """Validate configuration using validation sidecars."""
        logger.info(
            f"Validating configuration with {len(validation_instances)} sidecars"
        )

        validation_tasks = []
        for instance in validation_instances:
            # Use configured auth for validation instances
            client = DataplaneClient(instance.dataplane_url, auth=self.dataplane_auth)
            task = asyncio.create_task(
                self._validate_instance(client, instance, config)
            )
            validation_tasks.append(task)

        # Wait for all validations to complete
        results = await asyncio.gather(*validation_tasks, return_exceptions=True)

        # Check if all validations succeeded
        for i, result in enumerate(results):
            instance = validation_instances[i]
            if isinstance(result, Exception):
                logger.error(f"Validation failed on {instance.name}: {result}")
                return False
            elif not result:
                logger.error(f"Configuration validation failed on {instance.name}")
                return False

        logger.info("Configuration validation successful on all sidecars")
        return True

    async def _validate_instance(
        self, client: DataplaneClient, instance: HAProxyInstance, config: str
    ) -> bool:
        """Validate configuration on a single instance."""
        try:
            # Simple retry with tenacity for validation
            async for attempt in AsyncRetrying(
                stop=stop_after_attempt(2),
                wait=wait_exponential_jitter(initial=1, max=5),
                retry=retry_if_exception(
                    lambda e: isinstance(e, (ApiException, DataplaneAPIError))
                    and not isinstance(e, ValidationError)
                ),
            ):
                with attempt:
                    is_valid = await client.validate_configuration(config)
                    if not is_valid:
                        raise ValidationError(
                            f"Configuration validation failed on {instance.name}"
                        )
                    return True
            return False  # Should never reach here but satisfies mypy
        except ValidationError:
            # Re-raise ValidationError as it indicates a configuration problem
            raise
        except Exception as e:
            logger.error(f"Validation error on {instance.name}: {e}")
            return False

    async def _deploy_to_production(
        self, production_instances: List[HAProxyInstance], config: str
    ) -> List[SyncResult]:
        """Deploy configuration to production instances."""
        logger.info(
            f"Deploying configuration to {len(production_instances)} production instances"
        )

        deployment_tasks = []
        for instance in production_instances:
            # Use configured auth for production instances
            client = DataplaneClient(instance.dataplane_url, auth=self.dataplane_auth)
            task = asyncio.create_task(
                self._deploy_to_instance(client, instance, config)
            )
            deployment_tasks.append(task)

        # Wait for all deployments to complete
        results = await asyncio.gather(*deployment_tasks, return_exceptions=True)

        # Convert results to SyncResult objects
        sync_results: List[SyncResult] = []
        for i, result in enumerate(results):
            instance = production_instances[i]
            if isinstance(result, Exception):
                sync_results.append(
                    SyncResult(success=False, instance=instance, error=str(result))
                )
            else:
                # result is SyncResult since no exception occurred
                sync_results.append(result)  # type: ignore[arg-type]

        return sync_results

    async def _deploy_to_instance(
        self, client: DataplaneClient, instance: HAProxyInstance, config: str
    ) -> SyncResult:
        """Deploy configuration to a single instance."""
        try:
            version = await client.deploy_configuration(config)
            logger.info(
                f"Successfully deployed configuration to {instance.name}, version: {version}"
            )
            return SyncResult(success=True, instance=instance, config_version=version)
        except Exception as e:
            logger.error(f"Deployment failed on {instance.name}: {e}")
            return SyncResult(success=False, instance=instance, error=str(e))
