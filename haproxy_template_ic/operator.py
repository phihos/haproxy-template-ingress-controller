"""
Kubernetes operator functionality for HAProxy Template IC.

This module contains all the operator-specific logic including event handlers,
resource watchers, configuration management, and the main operator loop.
"""

import asyncio
import logging
from typing import Any, Dict, Tuple

import kopf
import uvloop
import yaml
from deepdiff import DeepDiff
from kopf import set_default_registry
from kopf._core.engines.indexing import OperatorIndexers
from kopf._core.intents.registries import SmartOperatorRegistry
from kr8s.objects import ConfigMap

from haproxy_template_ic.structured_logging import (
    get_structured_logger,
    operation_context,
    component_context_manager,
    resource_context_manager,
    log_kubernetes_event,
)
from haproxy_template_ic.tracing import (
    trace_async_function,
    trace_template_render,
    add_span_attributes,
    record_span_event,
)

from haproxy_template_ic.config_models import (
    HAProxyConfigContext,
    RenderedCertificate,
    RenderedConfig,
    RenderedMap,
    TemplateContext,
    config_from_dict,
)
from haproxy_template_ic.dataplane import (
    ConfigSynchronizer,
    HAProxyPodDiscovery,
    DataplaneAPIError,
    ValidationError,
)
from haproxy_template_ic.management_socket import run_management_socket_server
from haproxy_template_ic.metrics import get_metrics_collector
from haproxy_template_ic.utils import get_current_namespace

logger = get_structured_logger(__name__)


def _is_valid_resource(resource: Any) -> bool:
    """Validate if a resource object is suitable for template rendering.

    Args:
        resource: The resource object to validate

    Returns:
        True if the resource is valid for templates, False otherwise
    """
    # Dictionary resources are always valid
    if isinstance(resource, dict):
        return True

    # List/tuple resources should be non-empty
    if isinstance(resource, (list, tuple)):
        return len(resource) > 0

    # Objects with dict-like interface or attributes are valid
    if hasattr(resource, "__dict__") or hasattr(resource, "get"):
        return True

    # Primitives and other types are not valid resources
    return False


# =============================================================================
# Configuration Management
# =============================================================================


@trace_async_function(
    span_name="load_config_from_configmap",
    attributes={"operation.category": "configuration"},
)
async def load_config_from_configmap(configmap) -> Any:
    """Load configuration from a Kubernetes ConfigMap."""
    # Handle both kr8s ConfigMap objects and dictionary representations
    if hasattr(configmap, "namespace"):
        # kr8s ConfigMap object
        add_span_attributes(
            configmap_namespace=configmap.namespace or "unknown",
            configmap_name=configmap.name or "unknown",
        )
        config_data = configmap.data["config"]
    else:
        # Dictionary representation (from kopf event)
        add_span_attributes(
            configmap_namespace=configmap.get("metadata", {}).get(
                "namespace", "unknown"
            ),
            configmap_name=configmap.get("metadata", {}).get("name", "unknown"),
        )
        config_data = configmap["data"]["config"]

    config = config_from_dict(yaml.safe_load(config_data))

    # Register validation webhooks based on configuration
    from haproxy_template_ic.webhook import register_validation_webhooks_from_config

    register_validation_webhooks_from_config(config)

    return config


@trace_async_function(
    span_name="fetch_configmap", attributes={"operation.category": "kubernetes"}
)
async def fetch_configmap(name: str, namespace: str) -> Any:
    """Fetch ConfigMap from Kubernetes cluster."""
    add_span_attributes(configmap_name=name, configmap_namespace=namespace)
    try:
        result = await ConfigMap.get(name, namespace=namespace)
        record_span_event("configmap_fetched")
        return result
    except Exception as e:
        record_span_event("configmap_fetch_failed", {"error": str(e)})
        raise kopf.TemporaryError(f'Failed to retrieve ConfigMap "{name}": {e}') from e


# =============================================================================
# Event Handlers
# =============================================================================


def trigger_reload(memo: Any) -> None:
    """Signal the operator to reload with updated configuration."""
    memo.config_reload_flag.set_result(None)
    memo.stop_flag.set_result(None)


async def handle_configmap_change(
    memo: Any,
    event: Dict[str, Any],
    name: str,
    type: str,
    logger: logging.Logger,
    **kwargs: Any,
) -> None:
    """Handle ConfigMap change events."""
    with operation_context() as operation_id:
        with component_context_manager("operator"):
            with resource_context_manager(
                resource_type="ConfigMap",
                resource_namespace=event["object"].get("metadata", {}).get("namespace"),
                resource_name=name,
            ):
                structured_logger = get_structured_logger(__name__)
                log_kubernetes_event(
                    structured_logger,
                    type,
                    "ConfigMap",
                    event["object"].get("metadata", {}).get("namespace", "unknown"),
                    name,
                    operation_id=operation_id,
                )

                new_config = await load_config_from_configmap(event["object"])
                if memo.config.raw != new_config.raw:
                    diff = DeepDiff(memo.config.raw, new_config.raw, verbose_level=2)
                    diff_str = str(diff)[:500]
                    structured_logger.info(
                        "🔄 Config has changed: reloading", config_diff=diff_str
                    )
                    trigger_reload(memo)


async def update_resource_index(
    param: str,
    namespace: str,
    name: str,
    body: Dict[str, Any],
    logger: logging.Logger,
    **kwargs_: Any,
) -> Dict[Tuple[str, str], Dict[str, Any]]:
    """Update resource index for tracking."""
    logger.debug(f"📝 Updating index {param} for {namespace}/{name}...")
    return {(namespace, name): dict(body)}


@trace_async_function(
    span_name="render_haproxy_templates",
    attributes={"operation.category": "template_rendering"},
)
async def render_haproxy_templates(memo: Any, **kwargs: Any) -> None:
    """Render all HAProxy templates with current context data."""
    with operation_context() as operation_id:
        with component_context_manager("operator"):
            logger.debug("Rendering HAProxy templates", operation_id=operation_id)
            metrics = get_metrics_collector()

            # Collect all indices from registered watch resources
    indices: Dict[str, Dict[str, Any]] = {}
    for resource_id, watch_config in memo.config.watched_resources.items():
        try:
            # Get the index for this resource type
            index_data = memo.indices.get(resource_id)

            # Convert kopf index store to a dictionary with resource objects
            # The index_data is a kopf Store object containing resource data
            resource_dict = {}

            # Handle case where index_data is a Store object
            if hasattr(index_data, "items"):
                # kopf Store objects behave like dictionaries
                for key, resource_data in index_data.items():
                    try:
                        # kopf stores resource data directly as the body/dict
                        # resource_data should be the actual Kubernetes resource dict
                        if isinstance(resource_data, dict):
                            # Accept all dict-like objects (including test mocks)
                            resource_dict[key] = resource_data
                        elif hasattr(resource_data, "__dict__") or hasattr(
                            resource_data, "metadata"
                        ):
                            # Object with attributes (mock objects, k8s objects)
                            resource_dict[key] = resource_data
                        elif isinstance(resource_data, (list, tuple)) and resource_data:
                            # Some cases might return lists, take first item
                            resource_dict[key] = resource_data[0]
                        else:
                            logger.warning(
                                f"⚠️ Unexpected resource type {type(resource_data)} for {key}, skipping"
                            )
                    except Exception as e:
                        logger.warning(
                            f"⚠️ Failed to process resource {key}: {e}, type: {type(resource_data)}"
                        )
            else:
                logger.warning(
                    f"⚠️ Index data for '{resource_id}' is not iterable: {type(index_data)}"
                )

            indices[resource_id] = resource_dict
            logger.debug(
                f"📊 Retrieved index '{resource_id}' with {len(resource_dict)} items"
            )
        except Exception as e:
            logger.warning(f"⚠️ Could not retrieve index '{resource_id}': {e}")
            indices[resource_id] = {}

    # Record watched resource metrics
    metrics.record_watched_resources(indices)

    # Clear previous renders
    memo.haproxy_config_context.rendered_maps.clear()
    memo.haproxy_config_context.rendered_config = None
    memo.haproxy_config_context.rendered_certificates.clear()

    # Create a new template context instance each time with config access
    template_context = TemplateContext(resources=indices, config=memo.config)

    # Create template variables from dataclass fields, excluding config reference
    template_vars = {
        "resources": template_context.resources,
        "environment": template_context.environment,
        "cluster_name": template_context.cluster_name,
        "config_values": template_context.config_values,
        "get_template_snippet": template_context.get_template_snippet,
        "get_map_config": template_context.get_map_config,
        "get_certificate_config": template_context.get_certificate_config,
        "register_error": template_context.register_error,
        "get_resources": template_context.get_resources,
        "iterate_resources": template_context.iterate_resources,
        "count_resources": template_context.count_resources,
        "has_resources": template_context.has_resources,
    }

    # Render the HAProxy config template
    try:
        with trace_template_render("haproxy_config"):
            with metrics.time_template_render("haproxy_config"):
                rendered_content = memo.config.haproxy_config.render(**template_vars)
        rendered_config = RenderedConfig(content=rendered_content, config=memo.config)
        memo.haproxy_config_context.rendered_config = rendered_config
        metrics.record_template_render("haproxy_config", "success")
        add_span_attributes(
            template_size=len(rendered_content), template_vars_count=len(template_vars)
        )
        record_span_event("haproxy_config_rendered")
        logger.debug("✅ Rendered HAProxy configuration template")
    except Exception as e:
        metrics.record_template_render("haproxy_config", "error")
        metrics.record_error("template_render_failed", "operator")
        record_span_event("haproxy_config_render_failed", {"error": str(e)})
        logger.error(f"❌ Failed to render HAProxy configuration template: {e}")

    # Render each map template
    for map_path, map_config in memo.config.maps.items():
        try:
            with trace_template_render("map", map_path):
                with metrics.time_template_render("map"):
                    rendered_content = map_config.compiled_template.render(
                        **template_vars
                    )
            rendered_map = RenderedMap(
                path=map_path, content=rendered_content, map_config=map_config
            )
            memo.haproxy_config_context.rendered_maps.append(rendered_map)
            metrics.record_template_render("map", "success")
            add_span_attributes(map_path=map_path, map_size=len(rendered_content))
            record_span_event("map_rendered", {"path": map_path})
            logger.debug(f"✅ Rendered template for {map_path}")
        except Exception as e:
            metrics.record_template_render("map", "error")
            metrics.record_error("template_render_failed", "operator")
            record_span_event("map_render_failed", {"path": map_path, "error": str(e)})
            logger.error(f"❌ Failed to render template for {map_path}: {e}")

    # Render each certificate template
    for cert_path, certificate_config in memo.config.certificates.items():
        try:
            with trace_template_render("certificate", cert_path):
                with metrics.time_template_render("certificate"):
                    rendered_content = certificate_config.compiled_template.render(
                        **template_vars
                    )
            rendered_certificate = RenderedCertificate(
                path=cert_path,
                content=rendered_content,
            )
            memo.haproxy_config_context.rendered_certificates.append(
                rendered_certificate
            )
            metrics.record_template_render("certificate", "success")
            add_span_attributes(
                certificate_name=certificate_config.name,
                certificate_size=len(rendered_content),
            )
            record_span_event("certificate_rendered", {"name": certificate_config.name})
            logger.debug(
                f"✅ Rendered certificate template for {certificate_config.name}"
            )
        except Exception as e:
            metrics.record_template_render("certificate", "error")
            metrics.record_error("template_render_failed", "operator")
            record_span_event(
                "certificate_render_failed",
                {"name": certificate_config.name, "error": str(e)},
            )
            logger.error(
                f"❌ Failed to render certificate template for {certificate_config.name}: {e}"
            )

    # Synchronize rendered configuration with HAProxy instances
    await synchronize_with_haproxy_instances(memo)


async def synchronize_with_haproxy_instances(memo: Any) -> None:
    """Synchronize rendered configuration with HAProxy instances via Dataplane API."""
    metrics = get_metrics_collector()

    if not memo.config.pod_selector:
        logger.warning(
            "⚠️ No pod selector configured - skipping HAProxy synchronization"
        )
        return

    if not memo.haproxy_config_context.rendered_config:
        logger.warning(
            "⚠️ No rendered HAProxy config available - skipping synchronization"
        )
        return

    try:
        # Create pod discovery service
        current_namespace = get_current_namespace()
        pod_discovery = HAProxyPodDiscovery(
            pod_selector=memo.config.pod_selector, namespace=current_namespace
        )

        # Create synchronizer and perform sync
        synchronizer = ConfigSynchronizer(pod_discovery)
        results = await synchronizer.synchronize_configuration(
            memo.haproxy_config_context
        )

        # Log results and record metrics
        successful = [r for r in results if r.success]
        failed = [r for r in results if not r.success]

        # Record HAProxy instance counts and sync results
        production_instances = [
            r.instance for r in results if not r.instance.is_validation_sidecar
        ]
        validation_instances = [
            r.instance for r in results if r.instance.is_validation_sidecar
        ]
        metrics.record_haproxy_instances(
            len(production_instances), len(validation_instances)
        )

        if successful:
            for result in successful:
                metrics.record_dataplane_api_request("deploy", "success")
            logger.info(
                f"🚀 Successfully synchronized configuration to {len(successful)} HAProxy instances"
            )

        if failed:
            for result in failed:
                metrics.record_dataplane_api_request("deploy", "error")
                metrics.record_error("dataplane_deploy_failed", "dataplane")
            logger.error(
                f"❌ Failed to synchronize configuration to {len(failed)} HAProxy instances"
            )
            for result in failed:
                logger.error(f"   - {result.instance.name}: {result.error}")

    except ValidationError as e:
        metrics.record_error("validation_failed", "dataplane")
        logger.error(f"❌ Configuration validation failed: {e}")
    except DataplaneAPIError as e:
        metrics.record_error("dataplane_api_failed", "dataplane")
        logger.error(f"❌ Dataplane API error: {e}")
    except Exception as e:
        metrics.record_error("sync_unexpected_error", "dataplane")
        logger.error(f"❌ Unexpected error during synchronization: {e}")


# =============================================================================
# Resource Watchers
# =============================================================================


def setup_resource_watchers(memo: Any) -> None:
    """Set up watchers for Kubernetes resources."""
    resource_count = len(memo.config.watched_resources)
    logger.info(f"👀 Setting up {resource_count} resource watchers...")

    for resource_id, watch_config in memo.config.watched_resources.items():
        resource_type = watch_config.kind.lower()

        # Set up index and event handler with group/version if specified
        kwargs = {"id": resource_id, "param": resource_id}
        event_kwargs = {"id": f"{resource_id}_event"}

        if watch_config.group and watch_config.version:
            kwargs.update(
                {"group": watch_config.group, "version": watch_config.version}
            )
            event_kwargs.update(
                {"group": watch_config.group, "version": watch_config.version}
            )

            api_version = f"{watch_config.group}/{watch_config.version}"
            logger.info(
                f"🔍 Watching {resource_type} ({api_version}) with id '{resource_id}'"
            )
        else:
            logger.info(
                f"🔍 Watching {resource_type} (core/v1) with id '{resource_id}'"
            )

        kopf.index(resource_type, **kwargs)(update_resource_index)  # type: ignore[arg-type]
        kopf.on.event(resource_type, **event_kwargs)(render_haproxy_templates)  # type: ignore[arg-type]

    logger.info("✅ All resource watchers configured successfully")


# =============================================================================
# Operator Initialization
# =============================================================================


async def initialize_configuration(memo: Any) -> None:
    """Initialize operator configuration from ConfigMap."""
    metrics = get_metrics_collector()

    configmap_name = memo.cli_options.configmap_name
    logger.info(f"⚙️ Initializing config from configmap {configmap_name}.")

    try:
        with metrics.time_config_reload():
            namespace = get_current_namespace() or "default"
            configmap = await fetch_configmap(configmap_name, namespace)
            memo.config = await load_config_from_configmap(configmap)

        metrics.record_config_reload(success=True)
        logger.info("✅ Configuration loaded successfully.")
    except Exception as e:
        metrics.record_config_reload(success=False)
        metrics.record_error("config_load_failed", "operator")
        logger.error(f"❌ Failed to load configuration: {e}")
        raise


async def init_watch_configmap(memo: Any, **kwargs: Any) -> None:
    """Set up startup handlers after configuration is loaded."""

    configmap_name = memo.cli_options.configmap_name
    kopf.on.event(
        "configmap",
        when=lambda name, namespace, type, **_: (
            name == configmap_name and namespace == get_current_namespace()
        ),
    )(handle_configmap_change)  # type: ignore[arg-type]


async def init_management_socket(memo: Any, **kwargs: Any) -> None:
    # Start management socket server for state inspection
    socket_path = memo.cli_options.socket_path
    memo.socket_server_task = asyncio.create_task(
        run_management_socket_server(memo, socket_path)
    )


async def init_metrics_server(memo: Any, **kwargs: Any) -> None:
    """Initialize and start the Prometheus metrics server."""
    metrics = get_metrics_collector()
    metrics_port = getattr(memo.cli_options, "metrics_port", 9090)
    # Start metrics server as a background task
    memo.metrics_server_task = asyncio.create_task(
        metrics.start_metrics_server(metrics_port)
    )


def configure_webhook_server(
    settings: kopf.OperatorSettings, memo: Any, **kwargs: Any
) -> None:
    """Configure webhook server for admission control."""
    import os
    import tempfile

    # Check if any resources have webhook validation enabled
    has_webhooks = any(
        getattr(watch_config, "enable_validation_webhook", False)
        for watch_config in memo.config.watched_resources.values()
    )

    if not has_webhooks:
        logger.info(
            "⏭️ No validation webhooks configured - skipping webhook server setup"
        )
        return

    logger.info("🔌 Configuring webhook server for admission control...")

    cert_dir = "/tmp/webhook-certs"  # nosec B108 - Standard K8s volume mount path
    cert_file = f"{cert_dir}/webhook-cert.pem"
    key_file = f"{cert_dir}/webhook-key.pem"
    ca_file = f"{cert_dir}/webhook-ca.pem"

    if os.path.exists(cert_file) and os.path.exists(key_file):
        # Create a writable temporary directory for kopf's CA dump
        temp_dir = tempfile.mkdtemp(prefix="webhook-ca-")
        temp_ca_file = f"{temp_dir}/webhook-ca.pem"

        # Copy the CA file to writable location if it exists
        if os.path.exists(ca_file):
            import shutil

            shutil.copy2(ca_file, temp_ca_file)
            ca_dump_file = temp_ca_file
        else:
            # Fall back to using certificate file as CA
            ca_dump_file = temp_ca_file

        settings.admission.server = kopf.WebhookServer(
            addr="0.0.0.0",  # nosec B104 - Kubernetes webhook must bind all interfaces
            port=9443,
            certfile=cert_file,
            pkeyfile=key_file,
            cadump=ca_dump_file,
        )
        logger.info(
            "✅ Webhook server configured on port 9443 with mounted TLS certificates"
        )
    else:
        # Create a writable temporary directory for self-signed certificates
        temp_dir = tempfile.mkdtemp(prefix="webhook-ca-")
        temp_ca_file = f"{temp_dir}/webhook-ca.pem"

        settings.admission.server = kopf.WebhookServer(
            addr="0.0.0.0",  # nosec B104 - Kubernetes webhook must bind all interfaces
            port=9443,
            cadump=temp_ca_file,
        )
        logger.info(
            "✅ Webhook server configured on port 9443 with self-signed certificates"
        )

    settings.admission.managed = "haproxy-template-ic.io"


# =============================================================================
# Operator State Management
# =============================================================================


def create_operator_memo(cli_options: Any) -> Any:
    """Create memo object for operator state."""
    loop = uvloop.EventLoopPolicy().new_event_loop()
    stop_flag: asyncio.Future[None] = asyncio.Future(loop=loop)
    config_reload_flag: asyncio.Future[None] = asyncio.Future(loop=loop)

    return (
        kopf.Memo(
            stop_flag=stop_flag,
            cli_options=cli_options,
            config_reload_flag=config_reload_flag,
            haproxy_config_context=HAProxyConfigContext(),
        ),
        loop,
        stop_flag,
    )


# =============================================================================
# Main Operator Loop
# =============================================================================


def run_operator_loop(cli_options: Any) -> None:
    """Run the main operator loop with config reload capability."""
    # Initialize metrics on first run
    metrics = get_metrics_collector()
    metrics.set_app_info()

    while True:
        # Set up operator
        # Explicitly set registry to prevent persistence of handlers across reloads
        registry = SmartOperatorRegistry()
        set_default_registry(registry)

        # Explicitly set up the index containers to be able to retrieve all indices via memo
        indexers = OperatorIndexers()

        # Explicitly create the asyncio event loop to be able to run some tasks manually before passing it to kopf.run
        loop = uvloop.EventLoopPolicy().new_event_loop()

        # Explicitly create the stop_flag to be able to stop the operator from within
        stop_flag: asyncio.Future[None] = asyncio.Future(loop=loop)

        # This flag is not required by the operator, but we use it together with stop_flag to stop and reload the operator
        # When the stop flag is set, but this flag is not then the application will terminate
        # When both are set the operator will be reinitialized with a fresh config
        config_reload_flag: asyncio.Future[None] = asyncio.Future(loop=loop)

        # Explicitly create and prepopulate the memo object, that contains most oif the shared state
        memo = kopf.Memo(
            stop_flag=stop_flag,
            cli_options=cli_options,
            config_reload_flag=config_reload_flag,
            haproxy_config_context=HAProxyConfigContext(),
            indices=indexers.indices,
        )

        asyncio.set_event_loop(loop)
        # Fetch config from configmap, validate it and attach it to the memo
        loop.run_until_complete(initialize_configuration(memo))

        # Set up kopf indices
        # They must be set up before kopf.run or else they will not be initialized properly
        setup_resource_watchers(memo)

        # Watch the configmap for any changes to reload when necessary
        kopf.on.startup()(init_watch_configmap)
        # Start the management socket server to retrieve internal information and trigger actions
        kopf.on.startup()(init_management_socket)
        # Start the metrics server for Prometheus monitoring
        kopf.on.startup()(init_metrics_server)
        # Configure webhook server for admission control
        kopf.on.startup()(configure_webhook_server)

        # Run operator
        kopf.run(
            clusterwide=True,
            loop=loop,
            liveness_endpoint=f"http://0.0.0.0:{cli_options.healthz_port}/healthz",
            stop_flag=stop_flag,
            memo=memo,
            registry=registry,
            indexers=indexers,
        )

        # Check if we should exit or reload
        if not memo.config_reload_flag.done():
            break  # Normal shutdown

        logger.info("🔄 Configuration changed. Reinitializing...")

    logger.info("👋 Operator shutdown complete.")
