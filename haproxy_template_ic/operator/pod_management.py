"""
HAProxy pod management and discovery functionality.

Handles HAProxy pod indexing, lifecycle events, and pod discovery
for the operator's synchronization process.
"""

import logging
from typing import Any

import kopf
from kr8s.asyncio.objects import Pod

from haproxy_template_ic.constants import HAPROXY_PODS_INDEX
from haproxy_template_ic.core.logging import autolog
from haproxy_template_ic.dataplane.endpoint import DataplaneEndpoint
from haproxy_template_ic.dataplane.types import get_production_urls_from_index
from haproxy_template_ic.k8s.kopf_utils import get_resource_collection_from_indices
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
    "create_production_endpoints_from_index",
]


async def haproxy_pods_index(
    namespace: str = "",
    name: str = "",
    body: dict[str, Any] | None = None,
    **kwargs: Any,
) -> dict[tuple[str, str], dict[str, Any]]:
    """Index HAProxy pods for efficient discovery."""
    if body is None:
        body = {}

    logger.info(f"📝 Indexing HAProxy pod {namespace}/{name}")

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
async def fetch_haproxy_pods(match_labels: dict[str, str], namespace: str) -> list[Pod]:
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


def create_production_endpoints_from_index(
    memo: ApplicationState,
) -> list[DataplaneEndpoint]:
    """Create production DataplaneEndpoint objects from HAProxy pod index.

    Args:
        memo: ApplicationState containing kopf indices and credentials

    Returns:
        List of DataplaneEndpoint objects for current HAProxy pods
    """
    haproxy_pods = get_resource_collection_from_indices(
        memo.resources.indices, HAPROXY_PODS_INDEX
    )

    # Convert pod data to URLs and pod names using existing function
    urls, url_to_pod_name = get_production_urls_from_index(haproxy_pods)

    endpoints = []
    for url in urls:
        pod_name = url_to_pod_name.get(url)
        endpoint = DataplaneEndpoint(
            url=url,
            dataplane_auth=memo.configuration.credentials.dataplane,
            pod_name=pod_name,
        )
        endpoints.append(endpoint)
        logger.debug(f"Created production endpoint: {url} for pod: {pod_name}")

    logger.info(f"Created {len(endpoints)} production endpoints from HAProxy pod index")
    return endpoints


@autolog(component="operator")
async def handle_haproxy_pod_event(
    body: dict[str, Any] | None = None,
    meta: dict[str, Any] | None = None,
    type: str | None = None,
    memo: ApplicationState | None = None,
    **kwargs: Any,
) -> None:
    """Handle HAProxy pod events (create, update, delete)."""
    if body is None:
        body = {}
    if meta is None:
        meta = {}
    if type is None:
        type = ""

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

    try:
        production_endpoints = create_production_endpoints_from_index(memo)
        memo.operations.config_synchronizer.update_production_clients(
            production_endpoints
        )
        logger.debug(
            f"🔄 Updated ConfigSynchronizer with {len(production_endpoints)} production endpoints"
        )
    except Exception as e:
        logger.error(f"❌ Failed to update production endpoints: {e}")

    match type:
        case "ADDED":
            logger.info(f"🆕 HAProxy pod created: {namespace}/{name}")
            logger.info(f"📊 Pod status: phase={phase}, podIP={pod_ip}")
            # Always trigger for pod creation
            await memo.operations.debouncer.trigger("pod_changes")
            logger.debug("⏰ Triggered template rendering due to new HAProxy pod")

        case "DELETED":
            logger.info(f"🗑️ HAProxy pod deleted: {namespace}/{name}")
            # Always trigger for pod deletion
            await memo.operations.debouncer.trigger("pod_changes")
            logger.debug("⏰ Triggered template rendering due to HAProxy pod deletion")

        case "MODIFIED":
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
                logger.debug(
                    "⏰ Triggered template rendering due to HAProxy pod update"
                )


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
