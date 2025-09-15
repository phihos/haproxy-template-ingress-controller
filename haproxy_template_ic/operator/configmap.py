"""
ConfigMap handling for the Kubernetes operator.

Contains functions for loading configuration from ConfigMaps,
fetching ConfigMaps from the cluster, and handling ConfigMap change events.
"""

import logging
from typing import Any

import kopf
import structlog
import yaml
from deepdiff import DeepDiff
from kr8s.objects import ConfigMap

from haproxy_template_ic.core.logging import autolog
from haproxy_template_ic.models.config import Config, config_from_dict
from haproxy_template_ic.models.state import ApplicationState
from haproxy_template_ic.tracing import (
    add_span_attributes,
    record_span_event,
    trace_async_function,
)
from haproxy_template_ic.webhook import register_validation_webhooks_from_config

__all__ = [
    "load_config_from_configmap",
    "fetch_configmap",
    "handle_configmap_change",
]


@trace_async_function(
    span_name="load_config_from_configmap",
    attributes={"operation.category": "configuration"},
)
async def load_config_from_configmap(configmap) -> Config:
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
    register_validation_webhooks_from_config(config)

    record_span_event("config_loaded")

    return config


@trace_async_function(
    span_name="fetch_configmap", attributes={"operation.category": "kubernetes"}
)
async def fetch_configmap(name: str, namespace: str) -> ConfigMap:
    """Fetch ConfigMap from Kubernetes cluster."""
    add_span_attributes(configmap_name=name, configmap_namespace=namespace)
    try:
        result = await ConfigMap.get(name, namespace=namespace)
        record_span_event("configmap_fetched")
        return result
    except (ConnectionError, TimeoutError) as e:
        record_span_event("configmap_fetch_failed", {"error": str(e)})
        raise kopf.TemporaryError(
            f'Network error retrieving ConfigMap "{name}": {e}'
        ) from e
    except Exception as e:
        record_span_event("configmap_fetch_failed", {"error": str(e)})
        raise kopf.TemporaryError(f'Failed to retrieve ConfigMap "{name}": {e}') from e


@autolog(component="operator")
async def handle_configmap_change(
    memo: ApplicationState,
    event: dict[str, Any],
    name: str,
    type: str,
    logger: logging.Logger,
    **kwargs: Any,
) -> None:
    """Handle ConfigMap change events."""
    # Logging context is automatically injected by @autolog decorator
    structured_logger = structlog.get_logger(__name__)
    structured_logger.info(f"Kubernetes {type}")

    new_config = await load_config_from_configmap(event["object"])

    # Check if configuration has actually changed
    # Compare raw configuration dictionaries using DeepDiff
    diff = DeepDiff(memo.config.raw, new_config.raw, verbose_level=2)

    # Debug logging to understand what's being compared
    structured_logger.debug(
        "🔄 Comparing configs",
        old_pod_selector=memo.config.raw.get("pod_selector"),
        new_pod_selector=new_config.raw.get("pod_selector"),
    )

    if not diff:
        structured_logger.info("Configuration unchanged, skipping reload")
        return

    # Configuration has changed - show the diff and trigger reload
    diff_str = str(diff)[:500]  # Limit to 500 characters for log readability
    structured_logger.info("🔄 Config has changed: reloading", config_diff=diff_str)

    # Trigger reload by setting the flag
    memo.config_reload_flag.set_result(None)
    memo.stop_flag.set_result(None)
