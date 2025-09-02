"""
HAProxy pod management and discovery functionality.

Handles HAProxy pod indexing, lifecycle events, and pod discovery
for the operator's synchronization process.
"""

import logging
from typing import Any, Dict, Tuple

import kopf
from haproxy_template_ic.activity import EventType
from haproxy_template_ic.constants import HAPROXY_PODS_INDEX
from haproxy_template_ic.structured_logging import autolog

logger = logging.getLogger(__name__)

__all__ = [
    "haproxy_pods_index",
    "handle_haproxy_pod_create",
    "handle_haproxy_pod_delete",
    "handle_haproxy_pod_update",
    "setup_haproxy_pod_indexing",
]


async def haproxy_pods_index(
    **kwargs: Any,
) -> Dict[Tuple[str, str], Dict[str, Any]]:
    """Index HAProxy pods for efficient discovery."""
    # Extract kopf parameters
    namespace = kwargs.get("namespace", "")
    name = kwargs.get("name", "")
    body = kwargs.get("body", {})
    logger = kwargs.get("logger", logging.getLogger(__name__))

    logger.info(f"📝 Indexing HAProxy pod {namespace}/{name}")

    # Check if pod is being deleted using deletionTimestamp
    # Note: Index handlers don't receive event type like event handlers do,
    # so we need to check the deletionTimestamp to determine if pod is being deleted
    metadata = body.get("metadata", {})
    deletion_timestamp = metadata.get("deletionTimestamp")

    if deletion_timestamp:
        logger.info(f"🗑️ Pod {namespace}/{name} is being deleted, excluding from index")
        return {}  # Return empty dict to remove from index

    # Only index running pods with assigned IPs
    status = body.get("status", {})
    phase = status.get("phase")
    pod_ip = status.get("podIP")

    if phase != "Running" or not pod_ip:
        logger.debug(
            f"⏳ Pod {namespace}/{name} not ready for indexing: phase={phase}, podIP={pod_ip}"
        )
        return {}  # Return empty dict to exclude from index

    logger.debug(
        f"✅ Successfully indexed HAProxy pod {namespace}/{name} with IP {pod_ip}"
    )
    return {(namespace, name): dict(body)}


@autolog(component="operator")
async def handle_haproxy_pod_create(
    body: Dict[str, Any],
    meta: Dict[str, Any],
    logger: logging.Logger,
    memo: Any,
    **kwargs: Any,
) -> None:
    """Handle HAProxy pod creation events."""
    namespace = meta["namespace"]
    name = meta["name"]

    logger.info(f"🆕 HAProxy pod created: {namespace}/{name}")

    # Extract pod status for logging
    status = body.get("status", {})
    phase = status.get("phase", "Unknown")
    pod_ip = status.get("podIP", "Not assigned")

    logger.info(f"📊 Pod status: phase={phase}, podIP={pod_ip}")

    # Record activity event
    if hasattr(memo, "activity_buffer") and memo.activity_buffer:
        memo.activity_buffer.add_event_sync(
            EventType.CREATE,
            f"HAProxy pod created: {namespace}/{name} (phase={phase})",
            source="pod_management",
            metadata={
                "namespace": namespace,
                "name": name,
                "phase": phase,
                "pod_ip": pod_ip,
            },
        )

    # Trigger template rendering and sync after a brief delay to allow pod to stabilize
    if hasattr(memo, "debouncer"):
        await memo.debouncer.trigger("pod_changes")
        logger.debug("⏰ Triggered template rendering due to new HAProxy pod")


@autolog(component="operator")
async def handle_haproxy_pod_delete(
    body: Dict[str, Any],
    meta: Dict[str, Any],
    logger: logging.Logger,
    memo: Any,
    **kwargs: Any,
) -> None:
    """Handle HAProxy pod deletion events."""
    namespace = meta["namespace"]
    name = meta["name"]

    logger.info(f"🗑️ HAProxy pod deleted: {namespace}/{name}")

    # Record activity event
    if hasattr(memo, "activity_buffer") and memo.activity_buffer:
        memo.activity_buffer.add_event_sync(
            EventType.DELETE,
            f"HAProxy pod deleted: {namespace}/{name}",
            source="pod_management",
            metadata={"namespace": namespace, "name": name},
        )

    # The pod will be automatically removed from the index by the indexing function
    # Trigger template rendering and sync to update remaining instances
    if hasattr(memo, "debouncer"):
        await memo.debouncer.trigger("pod_changes")
        logger.debug("⏰ Triggered template rendering due to HAProxy pod deletion")


@autolog(component="operator")
async def handle_haproxy_pod_update(
    body: Dict[str, Any],
    meta: Dict[str, Any],
    logger: logging.Logger,
    memo: Any,
    **kwargs: Any,
) -> None:
    """Handle HAProxy pod update events."""
    namespace = meta["namespace"]
    name = meta["name"]

    # Extract relevant status information
    status = body.get("status", {})
    phase = status.get("phase", "Unknown")
    pod_ip = status.get("podIP", "Not assigned")
    ready_condition = None

    # Check readiness condition
    conditions = status.get("conditions", [])
    for condition in conditions:
        if condition.get("type") == "Ready":
            ready_condition = condition.get("status", "Unknown")
            break

    logger.info(
        f"🔄 HAProxy pod updated: {namespace}/{name} phase={phase} pod_ip={pod_ip} ready={ready_condition}"
    )

    # Record activity event for significant state changes
    if hasattr(memo, "activity_buffer") and memo.activity_buffer:
        # Only record activity for significant state changes
        if (
            phase == "Running"
            and pod_ip
            and pod_ip != "Not assigned"
            and ready_condition == "True"
        ):
            memo.activity_buffer.add_event_sync(
                EventType.SUCCESS,
                f"HAProxy pod ready: {namespace}/{name} (IP: {pod_ip})",
                source="pod_management",
                metadata={
                    "namespace": namespace,
                    "name": name,
                    "phase": phase,
                    "pod_ip": pod_ip,
                    "ready": ready_condition,
                },
            )
        elif phase in ["Pending", "ContainerCreating"]:
            memo.activity_buffer.add_event_sync(
                EventType.INFO,
                f"HAProxy pod starting: {namespace}/{name} (phase={phase})",
                source="pod_management",
                metadata={
                    "namespace": namespace,
                    "name": name,
                    "phase": phase,
                    "ready": ready_condition,
                },
            )

    # Trigger sync if pod became ready or IP changed
    if phase == "Running" and pod_ip and pod_ip != "Not assigned":
        if hasattr(memo, "debouncer"):
            await memo.debouncer.trigger("pod_changes")
            logger.debug("⏰ Triggered template rendering due to HAProxy pod update")


def setup_haproxy_pod_indexing(memo: Any) -> None:
    """Set up HAProxy pod indexing and event handlers.

    This function registers kopf handlers for HAProxy pod lifecycle management.
    It uses the pod_selector from the configuration to determine which pods to watch.

    Args:
        memo: Kopf memo object containing configuration
    """
    if not hasattr(memo, "config") or not hasattr(memo.config, "pod_selector"):
        logger.warning("No pod_selector configuration found")
        return

    pod_selector = memo.config.pod_selector

    logger.info(
        f"Setting up HAProxy pod indexing with selector: {pod_selector.match_labels}"
    )

    try:
        # Register kopf index for HAProxy pods
        kopf.index(
            "v1",
            "pods",
            id=HAPROXY_PODS_INDEX,
            labels=pod_selector.match_labels,
        )(haproxy_pods_index)

        # Register event handlers for HAProxy pod lifecycle
        @kopf.on.create(
            "v1",
            "pods",
            labels=pod_selector.match_labels,
        )
        async def haproxy_pod_create_handler(**kwargs):
            return await handle_haproxy_pod_create(**kwargs)

        @kopf.on.delete(
            "v1",
            "pods",
            labels=pod_selector.match_labels,
        )
        async def haproxy_pod_delete_handler(**kwargs):
            return await handle_haproxy_pod_delete(**kwargs)

        @kopf.on.update(
            "v1",
            "pods",
            labels=pod_selector.match_labels,
        )
        async def haproxy_pod_update_handler(**kwargs):
            return await handle_haproxy_pod_update(**kwargs)

        logger.info(
            "✅ HAProxy pod indexing and event handlers registered successfully"
        )

    except Exception as e:
        logger.error(f"Failed to setup HAProxy pod indexing: {e}")
        raise
