"""
Kubernetes resource management for the operator.

Contains functions for indexing resources, managing resource watchers,
and collecting resource metrics.
"""

import logging
from typing import Any, Dict, Tuple

from haproxy_template_ic.models import IndexedResourceCollection, ResourceTypeMetadata
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

    # Track resource change timestamp
    if memo:
        # Initialize resource_metadata if not exists
        if not hasattr(memo, "resource_metadata"):
            memo.resource_metadata = {}

        # Initialize metadata for this resource type if not exists
        if param not in memo.resource_metadata:
            memo.resource_metadata[param] = ResourceTypeMetadata(resource_type=param)

        # Update the last change timestamp
        memo.resource_metadata[param].update_change_timestamp()
        logger.debug(
            f"📅 Updated last change timestamp for {param} due to {namespace}/{name}"
        )

        # Generate activity event for resource change
        if hasattr(memo, "activity_buffer"):
            from haproxy_template_ic.activity import EventType

            # Create descriptive message that mentions resource type explicitly
            resource_name = f"{namespace}/{name}" if namespace else name
            event_message = f"{param.title()} resource updated: {resource_name}"

            memo.activity_buffer.add_event_sync(
                event_type=EventType.UPDATE,
                message=event_message,
                source="k8s-resources",
                metadata={"resource_type": param, "namespace": namespace, "name": name},
            )
            logger.debug(
                f"🎯 Generated activity event for {param} resource change: {resource_name}"
            )

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

    # Initialize resource_metadata if not exists
    if not hasattr(memo, "resource_metadata"):
        memo.resource_metadata = {}

    for resource_id in memo.config.watched_resources:
        try:
            if resource_id in memo.indices:
                index_data = memo.indices[resource_id]
                indices[resource_id] = IndexedResourceCollection.from_kopf_index(
                    index_data, ignore_fields=ignore_fields
                )
            else:
                indices[resource_id] = IndexedResourceCollection()

            # Initialize metadata for this resource type if not exists
            if resource_id not in memo.resource_metadata:
                memo.resource_metadata[resource_id] = ResourceTypeMetadata(
                    resource_type=resource_id
                )
                # Set initial timestamp when first tracking this resource type
                memo.resource_metadata[resource_id].update_change_timestamp()
                logger.debug(
                    f"📅 Initialized tracking for {resource_id} with current timestamp"
                )

            # Update statistics in the metadata
            collection = indices[resource_id]
            total_count = len(collection)

            # Calculate namespace distribution
            namespaces = {}
            for resource_list in collection._internal_dict.values():
                for resource in resource_list:
                    namespace = resource.get("metadata", {}).get("namespace", "default")
                    namespaces[namespace] = namespaces.get(namespace, 0) + 1

            namespace_count = len(namespaces)
            memory_size = (
                collection.get_memory_size()
                if hasattr(collection, "get_memory_size")
                else 0
            )

            memo.resource_metadata[resource_id].update_statistics(
                total_count=total_count,
                namespace_count=namespace_count,
                memory_size=memory_size,
                namespaces=namespaces,
            )

            logger.debug(f"📊 Retrieved index '{resource_id}' with {total_count} items")
        except Exception as e:
            logger.warning(f"⚠️ Could not retrieve index '{resource_id}': {e}")
            indices[resource_id] = IndexedResourceCollection()
            # Ensure metadata exists even on error
            if resource_id not in memo.resource_metadata:
                memo.resource_metadata[resource_id] = ResourceTypeMetadata(
                    resource_type=resource_id
                )
                # Set initial timestamp when first tracking this resource type
                memo.resource_metadata[resource_id].update_change_timestamp()
                logger.debug(
                    f"📅 Initialized tracking for {resource_id} with current timestamp (error case)"
                )

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
