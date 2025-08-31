"""
Kubernetes resource management for the operator.

Contains functions for indexing resources, managing resource watchers,
and collecting resource metrics.
"""

import logging
from typing import Any, Dict, Tuple

from haproxy_template_ic.models import IndexedResourceCollection
from .utils import extract_nested_field

logger = logging.getLogger(__name__)

__all__ = [
    "update_resource_index",
    "setup_resource_watchers",
    "_collect_resource_indices",
    "_record_resource_metrics",
]


async def update_resource_index(
    **kwargs: Any,
) -> Dict[Tuple[str, ...], Dict[str, Any]]:
    """Update resource index with configurable key."""
    # Extract kopf parameters
    param = kwargs.get("param", "")
    namespace = kwargs.get("namespace", "")
    name = kwargs.get("name", "")
    body = kwargs.get("body", {})
    logger = kwargs.get("logger", logging.getLogger(__name__))
    memo = kwargs.get("memo", None)

    logger.debug(f"📝 Updating index {param} for {namespace}/{name}...")

    # Convert kopf Body to dictionary if needed
    body_dict = dict(body) if hasattr(body, "items") else body

    # Get the watch config for this resource type
    if memo and hasattr(memo, "config") and hasattr(memo.config, "watched_resources"):
        watch_config = memo.config.watched_resources.get(param)
    else:
        watch_config = None

    if not watch_config:
        # Fallback to default indexing (namespace, name)
        return {(namespace, name): body_dict}

    # Extract index key values based on configured fields
    index_values = []
    for field_path in watch_config.index_by:
        value = extract_nested_field(body_dict, field_path)
        index_values.append(value)

    # Trigger template rendering when resource changes
    if memo and hasattr(memo, "debouncer"):
        # Use asyncio to schedule the trigger since this function might not be awaited
        import asyncio

        asyncio.create_task(memo.debouncer.trigger("resource_changes"))
        logger.debug(
            f"⏰ Triggered template rendering due to {param} resource change: {namespace}/{name}"
        )

    return {tuple(index_values): body_dict}


def _collect_resource_indices(memo: Any, metrics: Any) -> Dict[str, Any]:
    """Collect all resource indices as IndexedResourceCollections."""
    indices: Dict[str, IndexedResourceCollection] = {}

    # Get the ignore_fields configuration
    ignore_fields = getattr(memo.config, "watched_resources_ignore_fields", None)

    for resource_id in memo.config.watched_resources:
        try:
            if resource_id in memo.indices:
                index_data = memo.indices[resource_id]
                indices[resource_id] = IndexedResourceCollection.from_kopf_index(
                    index_data, ignore_fields=ignore_fields
                )
            else:
                indices[resource_id] = IndexedResourceCollection()

            logger.debug(
                f"📊 Retrieved index '{resource_id}' with {len(indices[resource_id])} items"
            )
        except Exception as e:
            logger.warning(f"⚠️ Could not retrieve index '{resource_id}': {e}")
            indices[resource_id] = IndexedResourceCollection()

    _record_resource_metrics(metrics, indices)
    return indices


def _record_resource_metrics(metrics: Any, indices: Dict[str, Any]) -> None:
    """Record metrics for watched resources."""
    metrics_data = {}
    for rid, collection in indices.items():
        resource_dict = {}
        for key, resource in collection.items():
            str_key = "_".join(str(k) for k in key)
            resource_dict[str_key] = resource
        metrics_data[rid] = resource_dict
    metrics.record_watched_resources(metrics_data)


def setup_resource_watchers(memo: Any) -> None:
    """Set up resource watchers based on configuration.

    This function dynamically registers kopf resource watchers based on the
    configuration in memo.config.watched_resources.

    Args:
        memo: Kopf memo object containing configuration and indices
    """
    import kopf

    if not hasattr(memo, "config") or not hasattr(memo.config, "watched_resources"):
        logger.warning("No watched_resources configuration found")
        return

    for resource_id, watch_config in memo.config.watched_resources.items():
        try:
            api_version = watch_config.api_version
            kind = watch_config.kind

            logger.info(f"Setting up watcher for {resource_id}: {api_version}/{kind}")

            # Register kopf indexing and handlers
            kopf.index(
                api_version,
                kind,
                id=resource_id,
                param=resource_id,
            )(update_resource_index)

        except Exception as e:
            logger.error(f"Failed to setup watcher for {resource_id}: {e}")
            raise
