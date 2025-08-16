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

from haproxy_template_ic.config import HAProxyConfigContext, PodSelector
from haproxy_template_ic.metrics import get_metrics_collector
from haproxy_template_ic.resilience import (
    get_resilient_operator,
    RetryPolicy,
    CircuitBreakerConfig,
    TimeoutConfig,
    ErrorCategory,
)
from haproxy_template_ic.tracing import (
    trace_async_function,
    trace_dataplane_operation,
    add_span_attributes,
    record_span_event,
    set_span_error,
)

# Import the complete generated client
from haproxy_dataplane_v3 import ApiClient, Configuration
from haproxy_dataplane_v3.api import (
    ConfigurationApi,
    InformationApi,
)
from haproxy_dataplane_v3.exceptions import (
    ApiException,
    BadRequestException,
)

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
        pod_ip = pod.status.pod_ip
        if not pod_ip:
            raise DataplaneAPIError(f"Pod {pod.namespace}/{pod.name} has no IP address")

        # Return the complete URL with v3 base path (this will be the host for Configuration)
        return f"http://{pod_ip}:{dataplane_port}"


class DataplaneClient:
    """Wrapper around the generated HAProxy Dataplane API v3 client."""

    def __init__(
        self, base_url: str, timeout: float = 30.0, auth: Optional[tuple] = None
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
        self.auth = auth or ("admin", "adminpass")  # Default auth

        # Create the generated API client configuration
        self._configuration = Configuration(
            host=self.base_url,
            username=self.auth[0],
            password=self.auth[1],
        )

    async def get_version(self) -> Dict[str, Any]:
        """Get HAProxy version information using the generated client."""
        try:
            async with ApiClient(self._configuration) as api_client:
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
            resilient_operator = get_resilient_operator()

            # Get adaptive timeout from circuit breaker if available and ensure it's configured
            circuit_name = f"haproxy_validation_{hash(self.base_url)}"
            circuit_breaker = resilient_operator.get_circuit_breaker(
                circuit_name, timeout_config=TimeoutConfig(initial_timeout=self.timeout)
            )
            adaptive_timeout = circuit_breaker.get_adaptive_timeout() or self.timeout

            caught_error: Optional[Exception] = None
            success: bool = False

            # Important: catch exceptions inside timing context to avoid mock __exit__ suppressing them
            with metrics.time_dataplane_api_operation("validate"):
                try:
                    async with ApiClient(self._configuration) as api_client:
                        config_api = ConfigurationApi(api_client)

                        # Use the generated client to validate configuration
                        # Ensure config ends with newline to avoid HAProxy truncation errors
                        config_data = config_content.rstrip() + "\n"
                        await config_api.post_ha_proxy_configuration(
                            data=config_data,
                            only_validate=True,
                            skip_version=True,
                            _request_timeout=adaptive_timeout,
                        )
                        success = True

                except BadRequestException as e:
                    # Configuration validation failed
                    logger.warning(f"Configuration validation failed: {e}")
                    if hasattr(e, "body") and e.body:
                        logger.warning(f"Validation error details: {e.body}")
                    caught_error = None  # Don't treat validation failure as an error
                    success = False
                except ApiException as e:
                    caught_error = e
                except Exception as e:
                    caught_error = e

            if success:
                record_span_event("validation_successful")
                return True

            # Failure path
            record_span_event(
                "validation_failed",
                {"error": str(caught_error) if caught_error else "validation_failed"},
            )
            if caught_error is not None:
                set_span_error(caught_error, "Configuration validation failed")
            return False

    async def deploy_configuration(self, config_content: str) -> str:
        """Deploy HAProxy configuration and reload."""
        with trace_dataplane_operation("deploy", self.base_url):
            add_span_attributes(
                config_size=len(config_content), dataplane_url=self.base_url
            )

            metrics = get_metrics_collector()
            resilient_operator = get_resilient_operator()

            # Configure retry policy for deployment operations
            deployment_retry_policy = RetryPolicy(
                max_attempts=5,
                base_delay=2.0,
                max_delay=30.0,
                retryable_categories=[
                    ErrorCategory.NETWORK,
                    ErrorCategory.SERVER_ERROR,
                    ErrorCategory.RATE_LIMIT,
                ],
            )

            async def deployment_operation():
                with metrics.time_dataplane_api_operation("deploy"):
                    try:
                        async with ApiClient(self._configuration) as api_client:
                            config_api = ConfigurationApi(api_client)

                            # Get current configuration version first
                            current_version = (
                                await config_api.get_configuration_version(
                                    _request_timeout=self.timeout
                                )
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

                    except ApiException as e:
                        # Convert to the expected exception type for resilience handling
                        raise DataplaneAPIError(str(e)) from e

            circuit_name = f"haproxy_deployment_{hash(self.base_url)}"
            result = await resilient_operator.execute_with_retry(
                operation=deployment_operation,
                operation_name="deploy_config",
                retry_policy=deployment_retry_policy,
                circuit_breaker_name=circuit_name,
                instance_url=self.base_url,
                config_size=len(config_content),
            )

            has_error = getattr(result, "error", None) is not None
            is_success = bool(getattr(result, "success", False)) and not has_error
            version_value = getattr(result, "result", None)

            if is_success and version_value:
                add_span_attributes(config_version=version_value)
                record_span_event("deployment_successful", {"version": version_value})
                return version_value

            # Failure path
            record_span_event(
                "deployment_failed", {"error": str(getattr(result, "error", "unknown"))}
            )
            error = getattr(result, "error", None)
            if error is not None:
                set_span_error(error, "Configuration deployment failed")
            attempts = getattr(result, "attempt", "?")
            error_msg = (
                f"Configuration deployment failed after {attempts} attempts: "
                f"{getattr(result, 'error', 'unknown error')}"
            )
            logger.error(error_msg)
            raise DataplaneAPIError(error_msg) from getattr(result, "error", None)


class ConfigSynchronizer:
    """Orchestrates configuration synchronization across HAProxy instances."""

    def __init__(self, pod_discovery: HAProxyPodDiscovery):
        self.pod_discovery = pod_discovery
        self.resilient_operator = get_resilient_operator()

        # Configure circuit breaker for overall synchronization health
        self.sync_circuit_config = CircuitBreakerConfig(
            failure_threshold=3,
            recovery_timeout=120,  # 2 minutes recovery time
            success_threshold=2,
        )

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
            # Determine auth based on instance type
            auth = ("admin", "adminpass")
            client = DataplaneClient(instance.dataplane_url, auth=auth)
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
        """Validate configuration on a single instance with circuit breaking."""
        # Check circuit breaker for this specific instance
        circuit_name = f"validation_{instance.name}"
        circuit_breaker = self.resilient_operator.get_circuit_breaker(
            circuit_name, self.sync_circuit_config
        )

        if not circuit_breaker.can_execute():
            logger.warning(f"Circuit breaker open for validation on {instance.name}")
            return False

        try:
            success = await client.validate_configuration(config)
            if success:
                circuit_breaker.record_success()
            else:
                circuit_breaker.record_failure()
            return success
        except Exception as e:
            circuit_breaker.record_failure()
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
            # Use default production auth
            auth = ("admin", "adminpass")
            client = DataplaneClient(instance.dataplane_url, auth=auth)
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
