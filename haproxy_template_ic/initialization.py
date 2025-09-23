"""
Operator initialization and lifecycle management.

Contains functions for initializing the operator configuration,
setting up services, managing startup/shutdown, and the main operator loop.
"""

import asyncio
import atexit
import logging
import os
import shutil
import tempfile
from typing import TYPE_CHECKING, Any

import kopf
import structlog
import uvloop
from kopf import set_default_registry
from kopf._core.engines.indexing import OperatorIndexers
from kopf._core.intents.registries import SmartOperatorRegistry
from kubernetes import config as k8s_config

from haproxy_template_ic.core.logging import setup_structured_logging
from haproxy_template_ic.core.validation import has_valid_attr
from haproxy_template_ic.credentials import Credentials
from haproxy_template_ic.dataplane.endpoint import (
    DataplaneEndpoint,
    DataplaneEndpointSet,
)
from haproxy_template_ic.dataplane.synchronizer import ConfigSynchronizer
from haproxy_template_ic.metrics import MetricsCollector
from haproxy_template_ic.models.context import HAProxyConfigContext, TemplateContext
from haproxy_template_ic.models.state import (
    ApplicationState,
    ConfigurationState,
    OperationalState,
    ResourceState,
    RuntimeState,
)

from haproxy_template_ic.operator.configmap import (
    fetch_configmap,
    handle_configmap_change,
    load_config_from_configmap,
)
from haproxy_template_ic.operator.debouncer import TemplateRenderDebouncer
from haproxy_template_ic.operator.index_sync import IndexSynchronizationTracker
from haproxy_template_ic.operator.k8s_resources import setup_resource_watchers
from haproxy_template_ic.operator.pod_management import (
    setup_haproxy_pod_indexing,
)
from haproxy_template_ic.operator.secrets import fetch_secret, handle_secret_change
from haproxy_template_ic.operator.utils import get_current_namespace
from haproxy_template_ic.templating import TemplateRenderer
from haproxy_template_ic.tracing import (
    TracingManager,
    create_tracing_config_from_env,
)

if TYPE_CHECKING:
    from haproxy_template_ic.models.cli import CliOptions

logger = logging.getLogger(__name__)

__all__ = [
    "initialize_post_config",
    "init_watch_configmap",
    "init_template_debouncer",
    "init_metrics_server",
    "cleanup_template_debouncer",
    "cleanup_tracing",
    "cleanup_metrics_server",
    "configure_webhook_server",
    "create_event_loop",
    "run_operator_loop",
]


async def initialize_post_config(memo: ApplicationState) -> None:
    """Initialize logging and tracing after configuration is loaded."""
    metrics = memo.operations.metrics

    try:
        with metrics.time_config_reload():
            # Reconfigure logging based on config
            setup_structured_logging(
                verbose_level=memo.configuration.config.logging.verbose,
                use_json=memo.configuration.config.logging.structured,
            )

            # Initialize distributed tracing if enabled
            if memo.configuration.config.tracing.enabled:
                base_tracing_config = create_tracing_config_from_env()
                final_tracing_config = base_tracing_config.override_with_app_config(
                    memo.configuration.config.tracing
                )
                tracing_manager = TracingManager(final_tracing_config)
                tracing_manager.initialize()
                memo.operations.tracing_manager = tracing_manager

        metrics.record_config_reload(success=True)
        logger.info("✅ Configuration and credentials loaded successfully.")
    except Exception as e:
        metrics.record_config_reload(success=False)
        metrics.record_error("config_load_failed", "operator")
        logger.error(f"❌ Failed to initialize post-config settings: {e}")
        raise


async def init_watch_configmap(memo: ApplicationState, **kwargs: Any) -> None:
    """Set up startup handlers after configuration is loaded."""

    configmap_name = memo.runtime.cli_options.configmap_name
    kopf.on.event(
        "configmap",
        when=lambda name, namespace, type, **_: (
            name == configmap_name and namespace == get_current_namespace()
        ),
    )(handle_configmap_change)  # type: ignore[arg-type]

    # Watch Secret changes
    secret_name = memo.runtime.cli_options.secret_name
    current_namespace = get_current_namespace()
    kopf.on.event(
        "secret",
        when=lambda name, namespace, type, **_: (
            name == secret_name and namespace == current_namespace
        ),
    )(handle_secret_change)  # type: ignore[arg-type]


async def init_template_debouncer(memo: ApplicationState, **kwargs: Any) -> None:
    """Initialize and start the template rendering debouncer."""
    await memo.operations.debouncer.start()


async def cleanup_template_debouncer(memo: ApplicationState, **kwargs: Any) -> None:
    """Stop the template rendering debouncer on shutdown."""
    logger.info("Stopping template debouncer...")
    await memo.operations.debouncer.stop()


async def cleanup_tracing(memo: ApplicationState, **kwargs: Any) -> None:
    """Clean up distributed tracing."""
    try:
        if memo.operations.tracing_manager:
            memo.operations.tracing_manager.shutdown()
            logger.debug("🔍 Tracing shutdown complete")
    except Exception as e:
        logger.error(f"❌ Error shutting down tracing: {e}")


async def cleanup_metrics_server(memo: ApplicationState, **kwargs: Any) -> None:
    """Clean up metrics server."""
    try:
        await memo.operations.metrics.stop_metrics_server()
        logger.debug("📊 Metrics server shutdown complete")
    except Exception as e:
        logger.error(f"❌ Error shutting down metrics server: {e}")


async def init_metrics_server(memo: ApplicationState, **kwargs: Any) -> None:
    """Start the metrics server."""
    metrics_port = memo.configuration.config.operator.metrics_port
    await memo.operations.metrics.start_metrics_server(port=metrics_port)
    logger.info(f"📊 Metrics server started on port {metrics_port}")


def configure_webhook_server(
    webhook_port: int = 9443,
    webhook_cert_dir: str | None = None,
) -> None:
    """Configure and start the webhook server if enabled."""
    logger.info("🔗 Setting up webhook server")

    if not webhook_cert_dir:
        webhook_cert_dir = tempfile.mkdtemp(prefix="haproxy-template-ic-webhook-")
        logger.info(f"📁 Created temporary webhook cert directory: {webhook_cert_dir}")

        # Register cleanup for temporary directory
        def cleanup_cert_dir():
            if os.path.exists(webhook_cert_dir):
                shutil.rmtree(webhook_cert_dir)
                logger.debug(f"🗑️ Cleaned up webhook cert directory: {webhook_cert_dir}")

        atexit.register(cleanup_cert_dir)

    try:
        logger.info(f"🔗 Webhook server configured for port {webhook_port}")
        logger.info(f"📜 Webhook certificates directory: {webhook_cert_dir}")
    except Exception as e:
        logger.error(f"❌ Failed to configure webhook server: {e}")
        raise


def create_event_loop() -> asyncio.AbstractEventLoop:
    """Create and configure the asyncio event loop."""
    return uvloop.EventLoopPolicy().new_event_loop()


async def _load_configuration_and_credentials(
    cli_options: "CliOptions", namespace: str
) -> tuple[Any, Any, Any]:
    """Load configuration from ConfigMap and credentials from Secret.

    Args:
        cli_options: CLI options containing ConfigMap and Secret names
        namespace: Kubernetes namespace

    Returns:
        Tuple of (config, credentials, renderer)

    Raises:
        Exception: If configuration or credentials loading fails
    """
    configmap_name = cli_options.configmap_name
    secret_name = cli_options.secret_name

    configmap = await fetch_configmap(configmap_name, namespace)
    config = await load_config_from_configmap(configmap)
    renderer = TemplateRenderer.from_config(config)

    secret = await fetch_secret(secret_name, namespace)
    secret_data = secret.data if has_valid_attr(secret, "data") else secret["data"]
    credentials = Credentials.from_secret(secret_data)

    return config, credentials, renderer


def _create_application_state(
    cli_options: "CliOptions",
    config: Any,
    credentials: Credentials,
    renderer: TemplateRenderer,
    stop_flag: asyncio.Future[None],
    config_reload_flag: asyncio.Future[None],
    indexers: OperatorIndexers,
) -> ApplicationState:
    """Create the main application state object.

    Args:
        cli_options: CLI configuration options
        config: Loaded application configuration
        credentials: Loaded credentials
        renderer: Template renderer instance
        stop_flag: Asyncio future for stopping the operator
        config_reload_flag: Asyncio future for config reload
        indexers: Kopf indexers object

    Returns:
        Configured ApplicationState object
    """
    # Construct validation URL from configuration
    validation_url = (
        f"http://{config.validation.dataplane_host}:{config.validation.dataplane_port}"
    )
    url_to_pod_name: dict[str, str] = {}

    validation_endpoint = DataplaneEndpoint(
        url=validation_url,
        dataplane_auth=credentials.validation,
        pod_name=url_to_pod_name.get(validation_url),
    )

    # No production endpoints during initialization - they're created dynamically
    endpoints = DataplaneEndpointSet(validation=validation_endpoint, production=[])

    index_tracker = IndexSynchronizationTracker(config)
    metrics_collector = MetricsCollector()

    config_synchronizer = ConfigSynchronizer(
        endpoints=endpoints, metrics=metrics_collector
    )

    haproxy_config_context = HAProxyConfigContext(
        template_context=TemplateContext(),
        rendered_config=None,
    )

    return ApplicationState(
        runtime=RuntimeState(
            stop_flag=stop_flag,
            config_reload_flag=config_reload_flag,
            cli_options=cli_options,
        ),
        configuration=ConfigurationState(
            config=config,
            haproxy_config_context=haproxy_config_context,
            credentials=credentials,
            template_renderer=renderer,
        ),
        resources=ResourceState(
            indices=indexers.indices,
        ),
        operations=OperationalState(
            debouncer=TemplateRenderDebouncer(
                min_interval=config.template_rendering.min_render_interval,
                max_interval=config.template_rendering.max_render_interval,
                config=config,
                haproxy_config_context=haproxy_config_context,
                template_renderer=renderer,
                config_synchronizer=config_synchronizer,
                kopf_indices=indexers.indices,
                metrics=metrics_collector,
                index_tracker=index_tracker,
            ),
            metrics=metrics_collector,
            config_synchronizer=config_synchronizer,
            index_tracker=index_tracker,
        ),
    )


def _setup_kopf_handlers(memo: ApplicationState) -> None:
    """Set up kopf handlers and resource watchers."""
    # They must be set up before kopf.run or else they will not be initialized properly
    setup_resource_watchers(memo)
    setup_haproxy_pod_indexing(memo)

    # Watch the configmap for any changes to reload when necessary
    kopf.on.startup()(init_watch_configmap)
    kopf.on.startup()(init_template_debouncer)
    kopf.on.startup()(init_metrics_server)

    # Register cleanup handlers
    kopf.on.cleanup()(cleanup_template_debouncer)
    kopf.on.cleanup()(cleanup_tracing)
    kopf.on.cleanup()(cleanup_metrics_server)


def run_operator_loop(cli_options: "CliOptions") -> None:
    """Run the main operator loop with config reload capability."""
    logger = structlog.get_logger("operator")

    try:
        k8s_config.load_incluster_config()
        logger.info("✅ Loaded in-cluster Kubernetes configuration")
    except Exception:
        try:
            k8s_config.load_kube_config()
            logger.info("✅ Loaded kubeconfig Kubernetes configuration")
        except Exception as e:
            logger.error(f"❌ Failed to load Kubernetes configuration: {e}")
            raise

    while True:  # Config reload loop
        # Explicitly set registry to prevent persistence of handlers across reloads
        registry = SmartOperatorRegistry()
        set_default_registry(registry)

        # Explicitly set up the index containers
        indexers = OperatorIndexers()

        # Explicitly create the asyncio event loop to be able to run some tasks manually before passing it to kopf.run
        loop = create_event_loop()

        # Explicitly create the stop_flag to be able to stop the operator from within
        stop_flag: asyncio.Future[None] = asyncio.Future(loop=loop)

        # This flag is not required by the operator, but we use it together with stop_flag to stop and reload the operator
        # When the stop flag is set, but this flag is not then the application will terminate
        # When both are set the operator will be reinitialized with a fresh config
        config_reload_flag: asyncio.Future[None] = asyncio.Future(loop=loop)

        asyncio.set_event_loop(loop)

        namespace = get_current_namespace() or "default"
        configmap_name = cli_options.configmap_name
        secret_name = cli_options.secret_name

        logger.info(
            f"⚙️ Loading config from configmap {configmap_name} and credentials from secret {secret_name}."
        )

        try:
            config, credentials, renderer = loop.run_until_complete(
                _load_configuration_and_credentials(cli_options, namespace)
            )
        except Exception as e:
            logger.error(f"❌ Failed to load configuration or credentials: {e}")
            raise

        memo = _create_application_state(
            cli_options,
            config,
            credentials,
            renderer,
            stop_flag,
            config_reload_flag,
            indexers,
        )

        # Set app info metrics
        memo.operations.metrics.set_app_info()

        try:
            loop.run_until_complete(initialize_post_config(memo))
            _setup_kopf_handlers(memo)

            # Run operator
            kopf.run(
                clusterwide=True,
                loop=loop,
                liveness_endpoint=f"http://0.0.0.0:{memo.configuration.config.operator.healthz_port}/healthz",
                stop_flag=stop_flag,
                memo=memo,
                registry=registry,
                indexers=indexers,
            )
            loop.close()
            if not memo.runtime.config_reload_flag.done():
                break  # Normal shutdown

            # Config changed, loop back to reload
            logger.info("🔄 Reloading configuration...")

        except KeyboardInterrupt:
            logger.info("👋 Operator stopped by user")
            break
        except Exception as e:
            logger.error(f"❌ Operator failed: {e}")
            raise
