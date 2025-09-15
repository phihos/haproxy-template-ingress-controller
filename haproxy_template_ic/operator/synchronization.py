"""
HAProxy instance synchronization functionality.

Handles synchronization of rendered templates with HAProxy instances
via the Dataplane API, including validation and deployment.
"""

import logging
import traceback
from typing import Any

from kopf._core.engines.indexing import Index, OperatorIndices

from haproxy_template_ic.constants import HAPROXY_PODS_INDEX
from haproxy_template_ic.dataplane.errors import DataplaneAPIError, ValidationError
from haproxy_template_ic.dataplane.models import get_production_urls_from_index
from haproxy_template_ic.dataplane.synchronizer import ConfigSynchronizer
from haproxy_template_ic.k8s.kopf_utils import get_resource_collection_from_indices
from haproxy_template_ic.metrics import get_metrics_collector
from haproxy_template_ic.models.config import Config
from haproxy_template_ic.models.context import HAProxyConfigContext
from haproxy_template_ic.tracing import trace_async_function

logger = logging.getLogger(__name__)

__all__ = [
    "synchronize_with_haproxy_instances",
    "_validate_sync_prerequisites",
    "_get_haproxy_pod_collection",
    "_record_sync_metrics",
    "_log_haproxy_error_hints",
]


def _validate_sync_prerequisites(haproxy_config_context: HAProxyConfigContext) -> bool:
    """Validate that all prerequisites for synchronization are met."""
    haproxy_config = haproxy_config_context.rendered_config
    if not haproxy_config or not haproxy_config.content:
        logger.warning("⚠️ No rendered HAProxy configuration available")
        return False

    return True


def _get_haproxy_pod_collection(
    indices: OperatorIndices,
) -> Index[Any, Any] | None:
    """Get HAProxy pod collection from indices."""
    if HAPROXY_PODS_INDEX not in indices:
        logger.warning("⚠️ No HAProxy pods index available")
        return None

    return indices[HAPROXY_PODS_INDEX]


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


def _log_haproxy_error_hints(
    validation_error: ValidationError,
    haproxy_config_context: HAProxyConfigContext,
) -> None:
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
    if haproxy_config_context.rendered_config:
        config_size = len(haproxy_config_context.rendered_config.content)
        logger.info(f"📊 Configuration size: {config_size} characters")


@trace_async_function(
    span_name="synchronize_with_haproxy_instances",
    attributes={"operation.category": "synchronization"},
)
async def synchronize_with_haproxy_instances(
    config: Config,
    haproxy_config_context: HAProxyConfigContext,
    indices: OperatorIndices,
    config_synchronizer: ConfigSynchronizer,
    force: bool = False,
) -> None:
    """Synchronize rendered configuration with HAProxy instances via Dataplane API.

    Args:
        memo: Operator memo object
        force: Whether to force synchronization regardless of content changes
    """
    logger.debug("🚀 SYNC FUNCTION CALLED - Starting synchronization...")
    metrics = get_metrics_collector()

    if not _validate_sync_prerequisites(haproxy_config_context):
        return

    try:
        haproxy_pods_store = _get_haproxy_pod_collection(indices)
        if haproxy_pods_store is None:
            return

        # Convert kopf Store to IndexedResourceCollection
        haproxy_pods_collection = get_resource_collection_from_indices(
            indices, HAPROXY_PODS_INDEX
        )

        production_urls, url_to_pod_name = get_production_urls_from_index(
            haproxy_pods_collection
        )
        if not production_urls:
            logger.warning(
                "⚠️ No production HAProxy pods found - skipping synchronization"
            )
            return

        # Update production URLs in case there were missed pod events
        config_synchronizer.update_production_clients(production_urls, url_to_pod_name)
        logger.debug("♻️ Updated ConfigSynchronizer with current configuration")

        synchronizer = config_synchronizer

        results = await synchronizer.sync_configuration(haproxy_config_context)

        successful_count = results.get("successful", 0)
        failed_count = results.get("failed", 0)
        errors = results.get("errors", [])

        _record_sync_metrics(
            metrics, successful_count, failed_count, len(production_urls)
        )
        for error in errors:
            logger.error(f"   - {error}")

    except ValidationError as e:
        metrics.record_error("validation_failed", "dataplane")
        logger.error(f"❌ Configuration validation failed: {e}")
        _log_haproxy_error_hints(e, haproxy_config_context)

    except DataplaneAPIError as e:
        metrics.record_error("dataplane_api_failed", "dataplane")
        logger.error(f"❌ Dataplane API error: {e}")
        logger.error(traceback.format_exc())

    except Exception as e:
        metrics.record_error("sync_unexpected_error", "dataplane")
        logger.error(f"❌ Unexpected error during synchronization: {e}")
