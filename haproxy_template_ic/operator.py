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
from kr8s.objects import ConfigMap

from haproxy_template_ic.config import (
    config_from_dict,
    HAProxyConfigContext,
    RenderedMap,
    TemplateContext,
)
from haproxy_template_ic.utils import get_current_namespace
from haproxy_template_ic.management_socket import run_management_socket_server


# =============================================================================
# Configuration Management
# =============================================================================


async def load_config_from_configmap(configmap: Dict[str, Any]) -> Any:
    """Load configuration from a Kubernetes ConfigMap."""
    return config_from_dict(yaml.safe_load(configmap["data"]["config"]))


async def fetch_configmap(name: str, namespace: str) -> Any:
    """Fetch ConfigMap from Kubernetes cluster."""
    try:
        return await ConfigMap.get(name, namespace=namespace)
    except Exception as e:
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
    logger.info(f'📋 Configmap "{name}" changed with type {type}.')

    new_config = await load_config_from_configmap(event["object"])
    if memo.config != new_config:
        diff = DeepDiff(memo.config, new_config, verbose_level=2)
        logger.info(f"🔄 Config has changed: {diff}. Reloading...")
        trigger_reload(memo)


async def update_resource_index(
    param: str,
    namespace: str,
    name: str,
    spec: Dict[str, Any],
    logger: logging.Logger,
    **kwargs_: Any,
) -> Dict[Tuple[str, str], Dict[str, Any]]:
    """Update resource index for tracking."""
    logger.debug(f"📝 Updating index {param} for {namespace}/{name}...")
    return {(namespace, name): spec}


async def render_haproxy_templates(
    memo: Any, indices: Dict[str, Any], logger: logging.Logger, **kwargs: Any
) -> None:
    """Render all HAProxy templates with current context data."""
    logger.debug("🎨 Rendering HAProxy templates...")

    # Create a new template context instance each time with config access
    template_context = TemplateContext(resources=indices, config=memo.config)

    # Render each map template
    for map_config in memo.config.maps:
        try:
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
            }
            rendered_content = map_config.template.render(**template_vars)
            rendered_map = RenderedMap(
                path=map_config.path, content=rendered_content, map_config=map_config
            )
            memo.haproxy_config_context.rendered_maps.append(rendered_map)
            logger.debug(f"✅ Rendered template for {map_config.path}")
        except Exception as e:
            logger.error(f"❌ Failed to render template for {map_config.path}: {e}")


# =============================================================================
# Resource Watchers
# =============================================================================


async def setup_resource_watchers(
    memo: Any, logger: logging.Logger, **kwargs: Any
) -> None:
    """Set up watchers for Kubernetes resources."""
    for watch_config in memo.config.watch_resources:
        resource_type = watch_config.kind.lower()

        # Set up index and event handler with group/version if specified
        kwargs = {"id": watch_config.id, "param": watch_config.id}
        event_kwargs = {"id": f"{watch_config.id}_event"}

        if watch_config.group and watch_config.version:
            kwargs.update(
                {"group": watch_config.group, "version": watch_config.version}
            )
            event_kwargs.update(
                {"group": watch_config.group, "version": watch_config.version}
            )

        kopf.index(resource_type, **kwargs)(update_resource_index)  # type: ignore[arg-type]
        kopf.on.event(resource_type, **event_kwargs)(render_haproxy_templates)  # type: ignore[arg-type]


# =============================================================================
# Operator Initialization
# =============================================================================


async def initialize_configuration(
    memo: Any, logger: logging.Logger, **kwargs: Any
) -> None:
    """Initialize operator configuration from ConfigMap."""
    configmap_name = memo.cli_options.configmap_name
    logger.info(f"⚙️ Initializing config from configmap {configmap_name}.")

    namespace = get_current_namespace() or "default"
    configmap = await fetch_configmap(configmap_name, namespace)
    memo.config = await load_config_from_configmap(configmap)

    # Set up event handlers
    kopf.on.startup()(setup_resource_watchers)  # type: ignore[arg-type]
    kopf.on.event(
        "configmap",
        when=lambda name, namespace, type, **_: (
            name == configmap_name
            and namespace == get_current_namespace()
            and type  # Skip initial invocation
        ),
    )(handle_configmap_change)  # type: ignore[arg-type]

    # Start management socket server for state inspection
    socket_path = memo.cli_options.socket_path
    memo.socket_server_task = asyncio.create_task(
        run_management_socket_server(memo, logger, socket_path)
    )

    logger.info("✅ Configuration initialized successfully.")


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


def run_operator_loop(cli_options: Any, logger: logging.Logger) -> None:
    """Run the main operator loop with config reload capability."""
    while True:
        # Set up operator
        kopf.on.startup()(initialize_configuration)  # type: ignore[arg-type]
        memo, loop, stop_flag = create_operator_memo(cli_options)

        # Run operator
        kopf.run(
            clusterwide=True,
            loop=loop,
            liveness_endpoint=f"http://0.0.0.0:{cli_options.healthz_port}/healthz",
            stop_flag=stop_flag,
            memo=memo,
        )

        # Check if we should exit or reload
        if not memo.config_reload_flag.done():
            break  # Normal shutdown

        logger.info("🔄 Configuration changed. Reinitializing...")

    logger.info("👋 Operator shutdown complete.")
