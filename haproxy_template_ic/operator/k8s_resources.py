"""
Kubernetes resource management for the operator.

Contains functions for indexing resources, managing resource watchers,
and collecting resource metrics.
"""

import logging
from typing import Any

import kopf

from haproxy_template_ic.core.validation import has_valid_attr
from haproxy_template_ic.k8s.resource_utils import extract_nested_field
from haproxy_template_ic.models.state import ApplicationState
from haproxy_template_ic.operator.index_sync import create_tracking_decorator

logger = logging.getLogger(__name__)


async def update_resource_index(
    param: str = "",
    namespace: str = "",
    name: str = "",
    body: dict[str, Any] | None = None,
    memo: ApplicationState | None = None,
    **kwargs: Any,
) -> dict[tuple[str, ...], dict[str, Any]]:
    """Update resource index with configurable key."""
    if body is None:
        body = {}

    logger.debug(f"📝 Updating index {param} for {namespace}/{name}...")

    # Convert kopf Body to dictionary if needed
    body_dict = dict(body) if has_valid_attr(body, "items") else body

    if memo:
        watch_config = memo.configuration.config.watched_resources.get(param)
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

    # Note: Template rendering is triggered by event handlers, not index functions
    # This ensures templates only render after index data is guaranteed to be available

    # Ensure index_values only contains strings for proper tuple creation
    return {
        tuple(
            str(value) if value is not None else "" for value in index_values
        ): body_dict
    }


async def handle_resource_event(
    memo: ApplicationState | None = None, **kwargs: Any
) -> None:
    """Event handler that triggers template rendering debouncer."""
    if memo:
        await memo.operations.debouncer.trigger("resource_changes")


def setup_resource_watchers(memo: ApplicationState) -> None:
    """Set up resource watchers and event handlers based on configuration.

    This function dynamically registers kopf resource watchers and event handlers
    based on the configuration in memo.configuration.config.watched_resources.

    Args:
        memo: Application state containing config, index_tracker, and debouncer
    """
    # Create tracking decorator with injected tracker
    track = create_tracking_decorator(memo.operations.index_tracker)

    for (
        resource_id,
        watch_config,
    ) in memo.configuration.config.watched_resources.items():
        try:
            api_version = watch_config.api_version
            kind = watch_config.kind

            logger.info(f"Setting up watcher for {resource_id}: {api_version}/{kind}")

            # Register kopf indexing with tracking
            kopf.index(
                api_version,
                kind,
                id=resource_id,
                param=resource_id,
            )(track(resource_id)(update_resource_index))

            # Register event handler with tracking
            kopf.on.event(
                api_version,
                kind,
                id=f"{resource_id}_events",
            )(track(resource_id)(handle_resource_event))

            logger.debug(f"✅ Registered event handler for {resource_id}")

        except Exception as e:
            logger.error(f"Failed to setup watcher for {resource_id}: {e}")
            raise
