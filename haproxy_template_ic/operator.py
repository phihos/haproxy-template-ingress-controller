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

from haproxy_template_ic.config import (
    HAProxyConfigContext,
    RenderedMap,
    TemplateContext,
    config_from_dict,
)
from haproxy_template_ic.management_socket import run_management_socket_server
from haproxy_template_ic.utils import get_current_namespace

logger = logging.getLogger(__name__)


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
        diff = DeepDiff(memo.config.raw, new_config.raw, verbose_level=2)
        logger.info(f"🔄 Config has changed: {diff}. Reloading...")
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


async def render_haproxy_templates(memo: Any, **kwargs: Any) -> None:
    """Render all HAProxy templates with current context data."""
    logger.debug("🎨 Rendering HAProxy templates...")

    # Collect all indices from registered watch resources
    indices: Dict[str, Dict[str, Any]] = {}
    for watch_config in memo.config.watch_resources:
        try:
            # Get the index for this resource type
            index_data = memo.indices.get(watch_config.id)

            # Convert kopf index store to a dictionary with resource objects
            # The index_data contains kopf store objects, we need the actual resources
            resource_dict = {}
            for key, resource in index_data.items():
                # key is typically (namespace, name), resource is a list of dicts
                try:
                    # Validate resource first
                    if not _is_valid_resource(resource):
                        logger.warning(
                            f"⚠️ Invalid resource type {type(resource)} for {key}, skipping"
                        )
                        continue

                    # Type safety: handle different resource types appropriately
                    if isinstance(resource, dict):
                        # Resource is already a dict (typical case), use as-is
                        resource_dict[key] = resource
                    elif isinstance(resource, (list, tuple)):
                        # Resource is a sequence (like a kopf store), get first element
                        if resource:
                            # Index keys with 0 elements will be removed, so we can be sure there is always [0]
                            # There will not be more than one element since the combination of name + namespace is unique
                            resource_dict[key] = resource[0]
                        else:
                            # This should not happen due to _is_valid_resource check, but handle gracefully
                            logger.warning(f"⚠️ Empty resource list for {key}, skipping")
                            continue
                    else:
                        # Resource is some other type (like a mock object or single resource)
                        # Already validated by _is_valid_resource, so safe to use as-is
                        resource_dict[key] = resource
                except Exception as e:
                    logger.warning(
                        f"⚠️ Failed to process resource {key} -> {resource}: {e}"
                    )
                    # Fallback: try to use resource as-is only if it's valid
                    if _is_valid_resource(resource):
                        try:
                            if isinstance(resource, dict):
                                resource_dict[key] = resource
                            elif isinstance(resource, list) and resource:
                                resource_dict[key] = resource[0]
                            else:
                                # For other valid types, use as-is
                                resource_dict[key] = resource
                        except Exception as fallback_error:
                            logger.warning(
                                f"⚠️ Fallback processing failed for {key}: {fallback_error}"
                            )
                    else:
                        logger.warning(
                            f"⚠️ Skipping invalid resource {key} due to type {type(resource)}"
                        )

            indices[watch_config.id] = resource_dict
            logger.debug(
                f"📊 Retrieved index '{watch_config.id}' with {len(resource_dict)} items"
            )
        except Exception as e:
            logger.warning(f"⚠️ Could not retrieve index '{watch_config.id}': {e}")
            indices[watch_config.id] = {}

    # Clear previous renders
    memo.haproxy_config_context.rendered_maps.clear()

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
                "get_resources": template_context.get_resources,
                "iterate_resources": template_context.iterate_resources,
                "count_resources": template_context.count_resources,
                "has_resources": template_context.has_resources,
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


def setup_resource_watchers(memo: Any) -> None:
    """Set up watchers for Kubernetes resources."""
    resource_count = len(memo.config.watch_resources)
    logger.info(f"👀 Setting up {resource_count} resource watchers...")

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

            api_version = f"{watch_config.group}/{watch_config.version}"
            logger.info(
                f"🔍 Watching {resource_type} ({api_version}) with id '{watch_config.id}'"
            )
        else:
            logger.info(
                f"🔍 Watching {resource_type} (core/v1) with id '{watch_config.id}'"
            )

        kopf.index(resource_type, **kwargs)(update_resource_index)  # type: ignore[arg-type]
        kopf.on.event(resource_type, **event_kwargs)(render_haproxy_templates)  # type: ignore[arg-type]

    logger.info("✅ All resource watchers configured successfully")


# =============================================================================
# Operator Initialization
# =============================================================================


async def initialize_configuration(memo: Any) -> None:
    """Initialize operator configuration from ConfigMap."""
    configmap_name = memo.cli_options.configmap_name
    logger.info(f"⚙️ Initializing config from configmap {configmap_name}.")

    namespace = get_current_namespace() or "default"
    configmap = await fetch_configmap(configmap_name, namespace)
    memo.config = await load_config_from_configmap(configmap)

    logger.info("✅ Configuration loaded successfully.")


async def init_watch_configmap(memo: Any, **kwargs: Any) -> None:
    """Set up startup handlers after configuration is loaded."""

    configmap_name = memo.cli_options.configmap_name
    kopf.on.event(
        "configmap",
        when=lambda name, namespace, type, **_: (
            name == configmap_name
            and namespace == get_current_namespace()
            and type  # Skip initial invocation
        ),
    )(handle_configmap_change)  # type: ignore[arg-type]


async def init_management_socket(memo: Any, **kwargs: Any) -> None:
    # Start management socket server for state inspection
    socket_path = memo.cli_options.socket_path
    memo.socket_server_task = asyncio.create_task(
        run_management_socket_server(memo, socket_path)
    )


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
