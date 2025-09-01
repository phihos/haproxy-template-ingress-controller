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
from typing import TYPE_CHECKING, Any, Optional

import kopf
import structlog
import uvloop
from kopf import set_default_registry
from kopf._core.engines.indexing import OperatorIndexers
from kopf._core.intents.registries import SmartOperatorRegistry
from kubernetes import config

from haproxy_template_ic.credentials import Credentials
from haproxy_template_ic.debouncer import TemplateRenderDebouncer
from haproxy_template_ic.management_socket import run_management_socket_server
from haproxy_template_ic.metrics import get_metrics_collector
from haproxy_template_ic.templating import TemplateRenderer
from haproxy_template_ic.models.config import (
    Config,
    PodSelector,
    TemplateConfig,
)
from haproxy_template_ic.models.context import (
    HAProxyConfigContext,
    TemplateContext,
)
# from haproxy_template_ic.webhook import start_webhook_server  # Function may not exist

from .configmap import (
    fetch_configmap,
    handle_configmap_change,
    load_config_from_configmap,
)
from .secrets import fetch_secret, handle_secret_change
from .k8s_resources import setup_resource_watchers
from .template_renderer import render_haproxy_templates
from .pod_management import setup_haproxy_pod_indexing
from .utils import get_current_namespace

if TYPE_CHECKING:
    from haproxy_template_ic.__main__ import CliOptions

logger = logging.getLogger(__name__)

__all__ = [
    "initialize_configuration",
    "init_watch_configmap",
    "init_management_socket",
    "init_template_debouncer",
    "init_metrics_server",
    "cleanup_template_debouncer",
    "cleanup_tracing",
    "cleanup_metrics_server",
    "configure_webhook_server",
    "create_event_loop",
    "run_operator_loop",
]


async def initialize_configuration(memo: Any) -> None:
    """Initialize operator configuration from ConfigMap."""
    metrics = get_metrics_collector()

    configmap_name = memo.cli_options.configmap_name
    secret_name = memo.cli_options.secret_name
    logger.info(
        f"⚙️ Initializing config from configmap {configmap_name} and credentials from secret {secret_name}."
    )

    try:
        with metrics.time_config_reload():
            namespace = get_current_namespace() or "default"
            # Load configuration from ConfigMap
            configmap = await fetch_configmap(configmap_name, namespace)
            memo.config = await load_config_from_configmap(configmap)
            memo.template_renderer = TemplateRenderer.from_config(memo.config)

            # Load credentials from Secret
            secret = await fetch_secret(secret_name, namespace)
            secret_data = secret.data if hasattr(secret, "data") else secret["data"]
            memo.credentials = Credentials.from_secret(secret_data)

            # Reconfigure logging based on config
            from haproxy_template_ic.structured_logging import setup_structured_logging

            setup_structured_logging(
                verbose_level=memo.config.logging.verbose,
                use_json=memo.config.logging.structured,
            )

            # Initialize distributed tracing if enabled
            if memo.config.tracing.enabled:
                from haproxy_template_ic.tracing import (
                    initialize_tracing,
                    create_tracing_config_from_env,
                )

                tracing_config = create_tracing_config_from_env()
                tracing_config.enabled = memo.config.tracing.enabled
                tracing_config.service_name = (
                    memo.config.tracing.service_name or tracing_config.service_name
                )
                tracing_config.service_version = (
                    memo.config.tracing.service_version
                    or tracing_config.service_version
                )
                tracing_config.jaeger_endpoint = (
                    memo.config.tracing.jaeger_endpoint
                    or tracing_config.jaeger_endpoint
                )
                tracing_config.sample_rate = memo.config.tracing.sample_rate
                tracing_config.console_export = (
                    memo.config.tracing.console_export or tracing_config.console_export
                )
                initialize_tracing(tracing_config)

        metrics.record_config_reload(success=True)
        logger.info("✅ Configuration and credentials loaded successfully.")
    except Exception as e:
        metrics.record_config_reload(success=False)
        metrics.record_error("config_load_failed", "operator")
        logger.error(f"❌ Failed to load configuration or credentials: {e}")
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

    # Watch Secret changes
    secret_name = memo.cli_options.secret_name
    current_namespace = get_current_namespace()
    kopf.on.event(
        "secret",
        when=lambda name, namespace, type, **_: (
            name == secret_name and namespace == current_namespace
        ),
    )(handle_secret_change)  # type: ignore[arg-type]


async def init_management_socket(memo: Any, **kwargs: Any) -> None:
    """Initialize management socket server for state inspection."""
    socket_path = memo.config.operator.socket_path
    memo.socket_server_task = asyncio.create_task(
        run_management_socket_server(memo, socket_path)
    )


async def init_template_debouncer(memo: Any, **kwargs: Any) -> None:
    """Initialize and start the template rendering debouncer."""
    if hasattr(memo, "debouncer") and memo.debouncer:
        # Stop existing debouncer if one exists
        await memo.debouncer.stop()

    # Get configuration values
    config = memo.config
    min_interval = config.template_rendering.min_render_interval
    max_interval = config.template_rendering.max_render_interval

    # Create and start debouncer
    memo.debouncer = TemplateRenderDebouncer(
        min_interval=min_interval,
        max_interval=max_interval,
        render_func=render_haproxy_templates,
        memo=memo,
    )
    await memo.debouncer.start()


async def cleanup_template_debouncer(memo: Any, **kwargs: Any) -> None:
    """Stop the template rendering debouncer on shutdown."""
    if hasattr(memo, "debouncer") and memo.debouncer:
        logger.info("Stopping template debouncer...")
        await memo.debouncer.stop()
        memo.debouncer = None


async def cleanup_tracing(memo: Any, **kwargs: Any) -> None:
    """Clean up distributed tracing."""
    try:
        if hasattr(memo, "config") and memo.config.tracing.enabled:
            from haproxy_template_ic.tracing import shutdown_tracing

            shutdown_tracing()
            logger.debug("🔍 Tracing shutdown complete")
    except Exception as e:
        logger.error(f"❌ Error shutting down tracing: {e}")


async def cleanup_metrics_server(memo: Any, **kwargs: Any) -> None:
    """Clean up metrics server."""
    try:
        if hasattr(memo, "metrics") and memo.metrics:
            await memo.metrics.stop_metrics_server()
            memo.metrics = None
            logger.debug("📊 Metrics server shutdown complete")
    except Exception as e:
        logger.error(f"❌ Error shutting down metrics server: {e}")


async def cleanup_management_socket(memo: Any, **kwargs: Any) -> None:
    """Clean up management socket server."""
    try:
        if hasattr(memo, "socket_server_task") and memo.socket_server_task:
            memo.socket_server_task.cancel()
            try:
                await memo.socket_server_task
            except asyncio.CancelledError:
                pass  # Expected when cancelling
            memo.socket_server_task = None
            logger.debug("🔌 Management socket server shutdown complete")
    except Exception as e:
        logger.error(f"❌ Error shutting down management socket server: {e}")


async def init_metrics_server(memo: Any, **kwargs: Any) -> None:
    """Start the metrics server."""
    metrics_port = memo.config.operator.metrics_port

    # Check if metrics server is already initialized
    if hasattr(memo, "metrics") and memo.metrics:
        logger.warning("⚠️ Metrics server already started")
        return

    memo.metrics = get_metrics_collector()
    await memo.metrics.start_metrics_server(port=metrics_port)
    logger.info(f"📊 Metrics server started on port {metrics_port}")


def configure_webhook_server(
    webhook_port: int = 9443,
    webhook_cert_dir: Optional[str] = None,
) -> None:
    """Configure and start the webhook server if enabled."""
    logger.info("🔗 Setting up webhook server")

    if not webhook_cert_dir:
        # Create temporary directory for self-signed certificates
        webhook_cert_dir = tempfile.mkdtemp(prefix="haproxy-template-ic-webhook-")
        logger.info(f"📁 Created temporary webhook cert directory: {webhook_cert_dir}")

        # Register cleanup for temporary directory
        def cleanup_cert_dir():
            if os.path.exists(webhook_cert_dir):
                shutil.rmtree(webhook_cert_dir)
                logger.debug(f"🗑️ Cleaned up webhook cert directory: {webhook_cert_dir}")

        atexit.register(cleanup_cert_dir)

    try:
        # TODO: Implement webhook server startup
        logger.info(f"🔗 Webhook server would start on port {webhook_port}")
        logger.info(f"📜 Webhook certificates directory: {webhook_cert_dir}")
    except Exception as e:
        logger.error(f"❌ Failed to start webhook server: {e}")
        raise


def create_event_loop() -> asyncio.AbstractEventLoop:
    """Create and configure the asyncio event loop."""
    return uvloop.EventLoopPolicy().new_event_loop()


def run_operator_loop(cli_options: "CliOptions") -> None:
    """Run the main operator loop with config reload capability."""
    # Initialize metrics
    metrics = get_metrics_collector()
    metrics.set_app_info()

    logger = structlog.get_logger("operator")

    # Load Kubernetes configuration once
    try:
        config.load_incluster_config()
        logger.info("✅ Loaded in-cluster Kubernetes configuration")
    except Exception:
        try:
            config.load_kube_config()
            logger.info("✅ Loaded kubeconfig Kubernetes configuration")
        except Exception as e:
            logger.error(f"❌ Failed to load Kubernetes configuration: {e}")
            raise

    while True:  # Config reload loop
        # Set up operator
        # Explicitly set registry to prevent persistence of handlers across reloads
        registry = SmartOperatorRegistry()
        set_default_registry(registry)

        # Explicitly set up the index containers to be able to retrieve all indices via memo
        indexers = OperatorIndexers()

        # Explicitly create the asyncio event loop to be able to run some tasks manually before passing it to kopf.run
        loop = create_event_loop()

        # Explicitly create the stop_flag to be able to stop the operator from within
        stop_flag: asyncio.Future[None] = asyncio.Future(loop=loop)

        # This flag is not required by the operator, but we use it together with stop_flag to stop and reload the operator
        # When the stop flag is set, but this flag is not then the application will terminate
        # When both are set the operator will be reinitialized with a fresh config
        config_reload_flag: asyncio.Future[None] = asyncio.Future(loop=loop)

        # Explicitly create and prepopulate the memo object, that contains most of the shared state
        memo = kopf.Memo(
            stop_flag=stop_flag,
            cli_options=cli_options,
            config_reload_flag=config_reload_flag,
            haproxy_config_context=HAProxyConfigContext(
                config=Config(
                    pod_selector=PodSelector(match_labels={"app": "haproxy"}),
                    haproxy_config=TemplateConfig(template="# Initial config"),
                ),
                template_context=TemplateContext(namespace="default"),
                rendered_config=None,
            ),
            indices=indexers.indices,
            template_renderer=None,  # Will be initialized when config is loaded
        )

        asyncio.set_event_loop(loop)

        try:
            # Fetch config from configmap, validate it and attach it to the memo
            loop.run_until_complete(initialize_configuration(memo))

            # Set up kopf indices
            # They must be set up before kopf.run or else they will not be initialized properly
            setup_resource_watchers(memo)
            setup_haproxy_pod_indexing(memo)

            # Watch the configmap for any changes to reload when necessary
            kopf.on.startup()(init_watch_configmap)
            # Start the management socket server to retrieve internal information and trigger actions
            kopf.on.startup()(init_management_socket)
            # Initialize and start the template rendering debouncer
            kopf.on.startup()(init_template_debouncer)
            # Start the metrics server for Prometheus monitoring
            kopf.on.startup()(init_metrics_server)

            # Register cleanup handlers
            kopf.on.cleanup()(cleanup_template_debouncer)
            kopf.on.cleanup()(cleanup_tracing)
            kopf.on.cleanup()(cleanup_metrics_server)
            kopf.on.cleanup()(cleanup_management_socket)

            # Run operator
            kopf.run(
                clusterwide=True,
                loop=loop,
                liveness_endpoint=f"http://0.0.0.0:{memo.config.operator.healthz_port}/healthz",
                stop_flag=stop_flag,
                memo=memo,
                registry=registry,
                indexers=indexers,
            )
            loop.close()
            # Check if we should exit or reload
            if not memo.config_reload_flag.done():
                break  # Normal shutdown

            # Config changed, loop back to reload
            logger.info("🔄 Reloading configuration...")

        except KeyboardInterrupt:
            logger.info("👋 Operator stopped by user")
            break
        except Exception as e:
            logger.error(f"❌ Operator failed: {e}")
            raise
