"""
HAProxy instance synchronization functionality.

Handles synchronization of rendered templates with HAProxy instances
via the Dataplane API, including validation and deployment.
"""

import logging
from typing import Any, Optional

from haproxy_template_ic.activity import EventType
from haproxy_template_ic.constants import HAPROXY_PODS_INDEX
from haproxy_template_ic.models import IndexedResourceCollection
from haproxy_template_ic.k8s.kopf_utils import get_resource_collection_from_memo
from haproxy_template_ic.dataplane import (
    ConfigSynchronizer,
    DataplaneAPIError,
    ValidationError,
    get_production_urls_from_index,
)
from haproxy_template_ic.metrics import get_metrics_collector
from haproxy_template_ic.tracing import trace_async_function
from .utils import get_current_namespace, get_memo_activity_buffer

logger = logging.getLogger(__name__)

__all__ = [
    "synchronize_with_haproxy_instances",
    "_validate_sync_prerequisites",
    "_get_haproxy_pod_collection",
    "_record_sync_metrics",
    "_log_haproxy_error_hints",
]


def _validate_sync_prerequisites(memo: Any) -> bool:
    """Validate that all prerequisites for synchronization are met."""
    if not hasattr(memo, "haproxy_config_context"):
        logger.warning("⚠️ No HAProxy configuration context available")
        return False

    if not hasattr(memo, "credentials"):
        logger.warning("⚠️ No credentials available for HAProxy synchronization")
        return False

    if not hasattr(memo, "config"):
        logger.warning("⚠️ No operator configuration available")
        return False

    haproxy_config = memo.haproxy_config_context.rendered_config
    if not haproxy_config or not haproxy_config.content:
        logger.warning("⚠️ No rendered HAProxy configuration available")
        return False

    return True


def _get_haproxy_pod_collection(memo: Any) -> Optional[IndexedResourceCollection]:
    """Get HAProxy pod collection from indices."""
    if not hasattr(memo, "indices") or HAPROXY_PODS_INDEX not in memo.indices:
        logger.warning("⚠️ No HAProxy pods index available")
        return None

    return memo.indices[HAPROXY_PODS_INDEX]


def _record_sync_metrics(
    metrics: Any,
    successful_count: int,
    failed_count: int,
    total_urls: int,
) -> None:
    """Record synchronization metrics."""
    if successful_count > 0:
        logger.info(
            f"✅ Successfully synchronized {successful_count}/{total_urls} instances"
        )

    if failed_count > 0:
        logger.warning(
            f"❌ Failed to synchronize {failed_count}/{total_urls} instances"
        )

    metrics.record_haproxy_sync(successful_count, failed_count)


def _log_haproxy_error_hints(validation_error: ValidationError, memo: Any) -> None:
    """Log helpful hints for HAProxy validation errors."""
    if not validation_error.validation_details:
        return

    error_details = validation_error.validation_details.lower()

    # Common HAProxy configuration errors and hints
    hints = []

    if "bind" in error_details and (
        "address" in error_details or "port" in error_details
    ):
        hints.append("Check that bind addresses and ports are valid and available")

    if "backend" in error_details and "server" in error_details:
        hints.append("Verify that backend servers are properly defined")

    if "unknown keyword" in error_details:
        hints.append("Check for HAProxy version compatibility and correct syntax")

    if "parsing" in error_details and "line" in error_details:
        hints.append("Review the HAProxy configuration for syntax errors")

    if "duplicate" in error_details:
        hints.append("Check for duplicate section names or conflicting definitions")

    if hints:
        logger.info("💡 Troubleshooting hints:")
        for hint in hints:
            logger.info(f"   - {hint}")

    # Log rendered config size for context
    if (
        hasattr(memo, "haproxy_config_context")
        and memo.haproxy_config_context.rendered_config
    ):
        config_size = len(memo.haproxy_config_context.rendered_config.content)
        logger.info(f"📊 Configuration size: {config_size} characters")


@trace_async_function(
    span_name="synchronize_with_haproxy_instances",
    attributes={"operation.category": "synchronization"},
)
async def synchronize_with_haproxy_instances(memo: Any, force: bool = False) -> None:
    """Synchronize rendered configuration with HAProxy instances via Dataplane API.

    Args:
        memo: Operator memo object
        force: Whether to force synchronization regardless of content changes
    """
    logger.debug("🚀 SYNC FUNCTION CALLED - Starting synchronization...")
    metrics = get_metrics_collector()

    if not _validate_sync_prerequisites(memo):
        return

    try:
        haproxy_pods_store = _get_haproxy_pod_collection(memo)
        if haproxy_pods_store is None:
            return

        # Convert kopf Store to IndexedResourceCollection
        haproxy_pods_collection = get_resource_collection_from_memo(
            memo, HAPROXY_PODS_INDEX
        )

        production_urls, url_to_pod_name = get_production_urls_from_index(
            haproxy_pods_collection
        )
        if not production_urls:
            logger.warning(
                "⚠️ No production HAProxy pods found - skipping synchronization"
            )
            return

        # Emit sync start event
        if activity_buffer := get_memo_activity_buffer(memo):
            activity_buffer.add_event_sync(
                EventType.SYNC,
                f"Starting configuration sync to {len(production_urls)} HAProxy instance{'s' if len(production_urls) > 1 else ''}",
                source="synchronization",
                metadata={
                    "pod_count": len(production_urls),
                    "namespace": get_current_namespace(),
                    "sync_phase": "start",
                },
            )

        # Cache ConfigSynchronizer in memo to reuse HTTP connections across sync operations
        if not hasattr(memo, "config_synchronizer"):
            # Construct validation dataplane URL from CLI options
            validation_url = f"http://{memo.config.validation.dataplane_host}:{memo.config.validation.dataplane_port}"
            memo.config_synchronizer = ConfigSynchronizer(
                production_urls=production_urls,
                validation_url=validation_url,
                credentials=memo.credentials,
                activity_buffer=memo.activity_buffer,
                url_to_pod_name=url_to_pod_name,
            )
            logger.debug("🔄 Created new ConfigSynchronizer instance")
        else:
            # Update production URLs in case there were missed pod events
            memo.config_synchronizer._update_production_clients(
                production_urls, url_to_pod_name
            )
            logger.debug("♻️  Reusing cached ConfigSynchronizer instance")

        synchronizer = memo.config_synchronizer

        results = await synchronizer.sync_configuration(memo.haproxy_config_context)

        successful_count = results.get("successful", 0)
        failed_count = results.get("failed", 0)
        errors = results.get("errors", [])

        _record_sync_metrics(
            metrics, successful_count, failed_count, len(production_urls)
        )

        # Record activity events for sync completion
        if activity_buffer := get_memo_activity_buffer(memo):
            # Always emit sync completion event
            if failed_count == 0:
                # All successful
                activity_buffer.add_event_sync(
                    EventType.SYNC,
                    f"Configuration sync complete: {successful_count}/{len(production_urls)} instances updated",
                    source="synchronization",
                    metadata={
                        "successful": successful_count,
                        "failed": failed_count,
                        "total_urls": len(production_urls),
                        "sync_phase": "complete",
                        "status": "success",
                    },
                )
            elif successful_count > 0:
                # Partial success
                memo.activity_buffer.add_event_sync(
                    EventType.SYNC,
                    f"Configuration sync partial: {successful_count} successful, {failed_count} failed",
                    source="synchronization",
                    metadata={
                        "successful": successful_count,
                        "failed": failed_count,
                        "total_urls": len(production_urls),
                        "sync_phase": "complete",
                        "status": "partial",
                        "errors": [str(error) for error in errors[:3]],
                    },
                )
            else:
                # All failed
                memo.activity_buffer.add_event_sync(
                    EventType.ERROR,
                    f"Configuration sync failed: {failed_count}/{len(production_urls)} instances failed",
                    source="synchronization",
                    metadata={
                        "successful": successful_count,
                        "failed": failed_count,
                        "total_urls": len(production_urls),
                        "sync_phase": "complete",
                        "status": "failed",
                        "errors": [str(error) for error in errors[:3]],
                    },
                )

        for error in errors:
            logger.error(f"   - {error}")

    except ValidationError as e:
        metrics.record_error("validation_failed", "dataplane")
        logger.error(f"❌ Configuration validation failed: {e}")
        _log_haproxy_error_hints(e, memo)

        # Record validation failure activity
        if hasattr(memo, "activity_buffer") and memo.activity_buffer:
            memo.activity_buffer.add_event_sync(
                EventType.ERROR,
                f"Configuration validation failed: {str(e)[:100]}",
                source="synchronization",
                metadata={"error": str(e)[:500], "type": "validation_error"},
            )

    except DataplaneAPIError as e:
        metrics.record_error("dataplane_api_failed", "dataplane")
        logger.error(f"❌ Dataplane API error: {e}")
        import traceback

        logger.error(traceback.format_exc())

        # Record dataplane API failure activity
        if hasattr(memo, "activity_buffer") and memo.activity_buffer:
            memo.activity_buffer.add_event_sync(
                EventType.ERROR,
                f"Dataplane API error: {str(e)[:100]}",
                source="synchronization",
                metadata={"error": str(e)[:500], "type": "dataplane_api_error"},
            )

    except Exception as e:
        metrics.record_error("sync_unexpected_error", "dataplane")
        logger.error(f"❌ Unexpected error during synchronization: {e}")

        # Record unexpected sync error activity
        if hasattr(memo, "activity_buffer") and memo.activity_buffer:
            memo.activity_buffer.add_event_sync(
                EventType.ERROR,
                f"Unexpected sync error: {str(e)[:100]}",
                source="synchronization",
                metadata={"error": str(e)[:500], "type": "unexpected_error"},
            )
