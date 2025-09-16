"""
HAProxy pod management and discovery functionality.

Handles HAProxy pod indexing, lifecycle events, and pod discovery
for the operator's synchronization process.
"""

import logging
from typing import Any, Dict, List, Tuple

import kopf
from kr8s.asyncio.objects import Pod

from haproxy_template_ic.constants import HAPROXY_PODS_INDEX
from haproxy_template_ic.core.logging import autolog
from haproxy_template_ic.models.state import ApplicationState
from haproxy_template_ic.operator.index_sync import create_tracking_decorator
from haproxy_template_ic.operator.utils import get_current_namespace
from haproxy_template_ic.tracing import (
    add_span_attributes,
    record_span_event,
    trace_async_function,
)

logger = logging.getLogger(__name__)

__all__ = [
    "haproxy_pods_index",
    "handle_haproxy_pod_event",
    "setup_haproxy_pod_indexing",
    "fetch_haproxy_pods",
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


@trace_async_function(
    span_name="fetch_haproxy_pods", attributes={"operation.category": "kubernetes"}
)
async def fetch_haproxy_pods(match_labels: Dict[str, str], namespace: str) -> List[Pod]:
    """Fetch HAProxy pods from Kubernetes cluster using pod selector.

    Args:
        match_labels: Labels to match pods against
        namespace: Kubernetes namespace to search in

    Returns:
        List of running HAProxy pods with assigned IPs
    """
    add_span_attributes(namespace=namespace, match_labels=str(match_labels))

    try:
        # Convert match_labels dict to label selector string
        label_selector = ",".join(f"{k}={v}" for k, v in match_labels.items())

        # Fetch pods using kr8s (async version returns async generator)
        all_pods_generator = Pod.list(
            namespace=namespace, label_selector=label_selector
        )
        all_pods = [pod async for pod in all_pods_generator]

        # Filter for pods with assigned IPs (don't require Running phase during initialization)
        pods_with_ips = []
        for pod in all_pods:
            if pod.status.podIP:
                pods_with_ips.append(pod)

        logger.info(
            f"Found {len(pods_with_ips)} HAProxy pods with IPs out of {len(all_pods)} total"
        )
        record_span_event(
            "pods_fetched",
            {"pods_with_ips_count": len(pods_with_ips), "total_count": len(all_pods)},
        )

        return pods_with_ips

    except (ConnectionError, TimeoutError) as e:
        record_span_event("pods_fetch_failed", {"error": str(e)})
        raise kopf.TemporaryError(
            f"Network error retrieving HAProxy pods with selector {match_labels}: {e}"
        ) from e
    except Exception as e:
        record_span_event("pods_fetch_failed", {"error": str(e)})
        raise kopf.TemporaryError(f"Failed to retrieve HAProxy pods: {e}") from e


@autolog(component="operator")
async def handle_haproxy_pod_event(
    body: Dict[str, Any] | None = None,
    meta: Dict[str, Any] | None = None,
    type: str | None = None,
    logger: logging.Logger | None = None,
    memo: ApplicationState | None = None,
    **kwargs: Any,
) -> None:
    """Handle HAProxy pod events (create, update, delete)."""
    # Extract parameters from kwargs if not provided positionally
    body = body or kwargs.get("body", {})
    meta = meta or kwargs.get("meta", {})
    type = type or kwargs.get("type", "")
    logger = logger or kwargs.get("logger", logging.getLogger(__name__))
    memo = memo or kwargs.get("memo")

    # Validate required parameters
    if not memo:
        logger.warning("No memo provided to handle_haproxy_pod_event")
        return

    if not meta or not body:
        logger.warning(
            "Missing required parameters (meta or body) in handle_haproxy_pod_event"
        )
        return

    namespace = meta["namespace"]
    name = meta["name"]

    # Extract pod status for logging
    status = body.get("status", {})
    phase = status.get("phase", "Unknown")
    pod_ip = status.get("podIP", "Not assigned")

    if type == "ADDED":
        logger.info(f"🆕 HAProxy pod created: {namespace}/{name}")
        logger.info(f"📊 Pod status: phase={phase}, podIP={pod_ip}")
        # Always trigger for pod creation
        await memo.operations.debouncer.trigger("pod_changes")
        logger.debug("⏰ Triggered template rendering due to new HAProxy pod")

    elif type == "DELETED":
        logger.info(f"🗑️ HAProxy pod deleted: {namespace}/{name}")
        # Always trigger for pod deletion
        await memo.operations.debouncer.trigger("pod_changes")
        logger.debug("⏰ Triggered template rendering due to HAProxy pod deletion")

    elif type == "MODIFIED":
        # Check readiness condition for updates
        ready_condition = None
        conditions = status.get("conditions", [])
        for condition in conditions:
            if condition.get("type") == "Ready":
                ready_condition = condition.get("status", "Unknown")
                break

        logger.info(
            f"🔄 HAProxy pod updated: {namespace}/{name} phase={phase} pod_ip={pod_ip} ready={ready_condition}"
        )

        # Only trigger sync if pod became ready or has IP assigned
        if phase == "Running" and pod_ip and pod_ip != "Not assigned":
            await memo.operations.debouncer.trigger("pod_changes")
            logger.debug("⏰ Triggered template rendering due to HAProxy pod update")


def setup_haproxy_pod_indexing(memo: ApplicationState) -> None:
    """Set up HAProxy pod indexing and event handlers.

    This function registers kopf handlers for HAProxy pod lifecycle management.
    It uses the pod_selector from the configuration to determine which pods to watch.
    Only watches pods in the current namespace for proper isolation.

    Args:
        memo: Kopf memo object containing configuration
    """
    pod_selector = memo.configuration.config.pod_selector
    current_namespace = get_current_namespace()

    logger.info(
        f"Setting up HAProxy pod indexing with selector: {pod_selector.match_labels} in namespace: {current_namespace}"
    )

    try:
        # Create tracking decorator with injected tracker
        track = create_tracking_decorator(memo.operations.index_tracker)

        # Register kopf index for HAProxy pods (namespace-scoped) with tracking
        kopf.index(
            "v1",
            "pods",
            id=HAPROXY_PODS_INDEX,
            labels=pod_selector.match_labels,
            when=lambda namespace, **_: namespace == current_namespace,
        )(track(HAPROXY_PODS_INDEX)(haproxy_pods_index))

        # Register event handler for HAProxy pod lifecycle (namespace-scoped) with tracking
        kopf.on.event(
            "v1",
            "pods",
            labels=pod_selector.match_labels,
            when=lambda namespace, **_: namespace == current_namespace,
        )(track(HAPROXY_PODS_INDEX)(handle_haproxy_pod_event))

        logger.info(
            "✅ HAProxy pod indexing and event handlers registered successfully"
        )

    except Exception as e:
        logger.error(f"Failed to setup HAProxy pod indexing: {e}")
        raise
