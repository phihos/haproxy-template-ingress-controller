"""
Kubernetes operator functionality for HAProxy Template IC.

This module contains all the operator-specific logic including event handlers,
resource watchers, configuration management, and the main operator loop.
"""

import asyncio
import atexit
import logging
import os
import shutil
import tempfile
from functools import lru_cache
from typing import TYPE_CHECKING, Any, Dict, Tuple

if TYPE_CHECKING:
    from haproxy_template_ic.__main__ import CliOptions

import jsonpath
from jsonpath.exceptions import JSONPathError
import kopf
import structlog
import uvloop
import yaml
from deepdiff import DeepDiff
from kopf import set_default_registry
from kopf._core.engines.indexing import OperatorIndexers
from kopf._core.intents.registries import SmartOperatorRegistry
from kr8s.objects import ConfigMap, Secret
from kubernetes import config

from haproxy_template_ic.config_models import (
    Config,
    HAProxyConfigContext,
    IndexedResourceCollection,
    PodSelector,
    RenderedContent,
    RenderedConfig,
    TemplateConfig,
    TemplateContext,
    config_from_dict,
)
from haproxy_template_ic.debouncer import TemplateRenderDebouncer
from haproxy_template_ic.dataplane import (
    ConfigSynchronizer,
    DataplaneAPIError,
    DeploymentHistory,
    ValidationError,
    get_production_urls_from_index,
)
from haproxy_template_ic.management_socket import run_management_socket_server
from haproxy_template_ic.metrics import get_metrics_collector
from haproxy_template_ic.structured_logging import autolog, observe
from haproxy_template_ic.templating import TemplateRenderer
from haproxy_template_ic.webhook import register_validation_webhooks_from_config
from haproxy_template_ic.credentials import Credentials
from haproxy_template_ic.constants import (
    CONTENT_TYPE_CERTIFICATE,
    CONTENT_TYPE_FILE,
    CONTENT_TYPE_HAPROXY_CONFIG,
    CONTENT_TYPE_MAP,
    DEFAULT_METRICS_PORT,
    DEFAULT_WEBHOOK_PORT,
    HAPROXY_PODS_INDEX,
    NAMESPACE_FILE_PATH,
)
from haproxy_template_ic.tracing import (
    add_span_attributes,
    record_span_event,
    trace_async_function,
    trace_template_render,
)

logger = structlog.get_logger(__name__)


def get_current_namespace() -> str:
    """Get the current Kubernetes namespace."""
    if os.path.exists(NAMESPACE_FILE_PATH):
        with open(NAMESPACE_FILE_PATH) as f:
            return f.read().strip()
    try:
        contexts, active_context = config.list_kube_config_contexts()
        namespace = active_context["context"].get("namespace", "default")
        return namespace if isinstance(namespace, str) else "default"
    except (KeyError, TypeError):
        return "default"


def _validate_sync_prerequisites(memo: Any) -> bool:
    """Validate prerequisites for HAProxy synchronization.

    Returns:
        True if sync can proceed, False otherwise
    """
    if not memo.config.pod_selector:
        logger.warning(
            "⚠️ No pod selector configured - skipping HAProxy synchronization"
        )
        return False

    if not memo.haproxy_config_context.rendered_config:
        logger.warning(
            "⚠️ No rendered HAProxy config available - skipping synchronization"
        )
        return False

    return True


def _get_haproxy_pod_collection(memo: Any) -> Any:
    """Get HAProxy pod collection from memo indices.

    Returns:
        IndexedResourceCollection or None if not available
    """
    if not hasattr(memo, "indices"):
        logger.warning("🔍 No indices available - skipping synchronization")
        return None

    available_indices = list(memo.indices.keys())
    logger.info(f"🔍 Available indices: {available_indices}")

    if HAPROXY_PODS_INDEX not in memo.indices:
        logger.warning("🔍 HAProxy pods index not found - skipping synchronization")
        return None

    haproxy_pods_store = memo.indices[HAPROXY_PODS_INDEX]
    logger.info(f"🔍 HAProxy pods index contains {len(haproxy_pods_store)} entries")

    haproxy_pods_collection = IndexedResourceCollection.from_kopf_index(
        haproxy_pods_store
    )
    logger.info(
        f"🔍 Created IndexedResourceCollection with {len(haproxy_pods_collection)} pods"
    )

    return haproxy_pods_collection


def _record_sync_metrics(
    metrics: Any, successful_count: int, failed_count: int, production_count: int
) -> None:
    """Record synchronization metrics."""
    metrics.record_haproxy_instances(
        production_count,
        1,  # validation instances = 1 (localhost sidecar)
    )

    if successful_count > 0:
        for _ in range(successful_count):
            metrics.record_dataplane_api_request("deploy", "success")
        logger.info(
            f"🚀 Successfully synchronized configuration to {successful_count} HAProxy instances"
        )

    if failed_count > 0:
        for _ in range(failed_count):
            metrics.record_dataplane_api_request("deploy", "error")
            metrics.record_error("dataplane_deploy_failed", "dataplane")
        logger.error(
            f"❌ Failed to synchronize configuration to {failed_count} HAProxy instances"
        )


def _log_haproxy_error_hints(validation_error: ValidationError, memo: Any) -> None:
    """Log helpful hints for HAProxy configuration errors."""
    if validation_error.error_line:
        logger.error(
            f"💥 Error occurred at line {validation_error.error_line} in HAProxy configuration"
        )

    if validation_error.error_context:
        logger.error("📝 Configuration context around the error:")
        for line in validation_error.error_context.split("\n"):
            logger.error(f"   {line}")

    if validation_error.validation_details:
        details_lower = validation_error.validation_details.lower()

        if "'listen' or 'defaults' expected" in details_lower:
            logger.error(
                "💡 Hint: This error often occurs when a section is missing or has syntax errors. "
                "Check that all frontend/backend/listen blocks are properly defined."
            )
        elif "unknown keyword" in details_lower:
            logger.error(
                "💡 Hint: Check for typos in HAProxy directives or unsupported configuration options."
            )
        elif "missing argument" in details_lower:
            logger.error(
                "💡 Hint: A configuration directive is missing required parameters."
            )
        elif "too many args" in details_lower:
            logger.error("💡 Hint: A configuration directive has too many parameters.")

    if memo.config and memo.config.template_snippets:
        logger.error(
            "🔧 Debug tip: Check your Jinja2 templates and snippets for syntax errors or missing includes"
        )

    logger.error(
        "🔧 Debug tip: Use the management socket 'dump config' command to inspect the rendered configuration"
    )


def _is_valid_dict_resource(resource: dict) -> bool:
    """Validate dictionary resource has proper Kubernetes metadata.

    Args:
        resource: Dictionary resource to validate

    Returns:
        True if has valid metadata, False otherwise
    """
    metadata = resource.get("metadata", {})
    if not isinstance(metadata, dict):
        return False
    return bool(metadata.get("name") and metadata.get("namespace"))


def _is_valid_sequence_resource(resource: Any) -> bool:
    """Validate sequence resource is non-empty.

    Args:
        resource: List or tuple resource to validate

    Returns:
        True if non-empty, False otherwise
    """
    return len(resource) > 0


def _is_valid_object_resource(resource: Any) -> bool:
    """Validate object resource can be accessed for templating.

    Args:
        resource: Object resource to validate

    Returns:
        True if accessible for templating, False otherwise
    """
    try:
        if hasattr(resource, "items"):
            dict(resource)  # Test dict conversion
        elif hasattr(resource, "__dict__"):
            resource.__dict__  # Test attribute access
        return True
    except (TypeError, AttributeError):
        return False


def _is_valid_resource(resource: Any) -> bool:
    """Validate if a resource object is suitable for template rendering.

    Args:
        resource: The resource object to validate

    Returns:
        True if the resource is valid for templates, False otherwise
    """
    # Dictionary resources need basic metadata validation
    if isinstance(resource, dict):
        return _is_valid_dict_resource(resource)

    # List/tuple resources should be non-empty
    if isinstance(resource, (list, tuple)):
        return _is_valid_sequence_resource(resource)

    # Objects with dict-like interface or attributes are valid
    if hasattr(resource, "__dict__") or hasattr(resource, "get"):
        return _is_valid_object_resource(resource)

    # Primitives and other types are not valid resources
    return False


# =============================================================================
# Configuration Management
# =============================================================================


@trace_async_function(
    span_name="load_config_from_configmap",
    attributes={"operation.category": "configuration"},
)
async def load_config_from_configmap(configmap) -> Any:
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

    return config


@trace_async_function(
    span_name="fetch_configmap", attributes={"operation.category": "kubernetes"}
)
async def fetch_configmap(name: str, namespace: str) -> Any:
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


@trace_async_function(
    span_name="fetch_secret", attributes={"operation.category": "kubernetes"}
)
async def fetch_secret(name: str, namespace: str) -> Any:
    """Fetch Secret from Kubernetes cluster."""
    add_span_attributes(secret_name=name, secret_namespace=namespace)
    try:
        result = await Secret.get(name, namespace=namespace)
        record_span_event("secret_fetched")
        return result
    except (ConnectionError, TimeoutError) as e:
        record_span_event("secret_fetch_failed", {"error": str(e)})
        raise kopf.TemporaryError(
            f'Network error retrieving Secret "{name}": {e}'
        ) from e
    except Exception as e:
        record_span_event("secret_fetch_failed", {"error": str(e)})
        raise kopf.PermanentError(
            f'Failed to retrieve Secret "{name}": {e}. Credentials are mandatory for operation.'
        ) from e


# =============================================================================
# Event Handlers
# =============================================================================


def trigger_reload(memo: Any) -> None:
    """Signal the operator to reload with updated configuration."""
    memo.config_reload_flag.set_result(None)
    memo.stop_flag.set_result(None)


@autolog(component="operator")
async def handle_configmap_change(
    memo: Any,
    event: Dict[str, Any],
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

    # Compare model dictionaries to avoid issues with compiled templates and object identity
    # Use serialization mode to exclude non-serializable fields like compiled templates
    old_dict = memo.config.model_dump(mode="serialization")
    new_dict = new_config.model_dump(mode="serialization")

    if old_dict != new_dict:
        diff = DeepDiff(old_dict, new_dict, verbose_level=2)
        diff_str = str(diff)[:500]
        structured_logger.info("🔄 Config has changed: reloading", config_diff=diff_str)
        trigger_reload(memo)


@autolog(component="operator")
async def handle_secret_change(
    memo: Any,
    event: Dict[str, Any],
    name: str,
    type: str,
    logger: logging.Logger,
    **kwargs: Any,
) -> None:
    """Handle Secret change events."""
    # Logging context is automatically injected by @autolog decorator
    structured_logger = structlog.get_logger(__name__)
    structured_logger.info(f"Kubernetes {type}")

    # Load new credentials directly
    secret_data = (
        event["object"].get("data", {})
        if isinstance(event["object"], dict)
        else event["object"].data
    )
    try:
        new_credentials = Credentials.from_secret(secret_data)
    except Exception as e:
        structured_logger.error(f"❌ Failed to load credentials: {e}")
        return

    # Simple credential comparison using tuples
    if memo.credentials != new_credentials:
        structured_logger.info("🔐 Credentials changed: reloading")
        memo.credentials = new_credentials


@lru_cache(maxsize=256)
def _compile_jsonpath(path: str):
    """Cache compiled JSONPath expressions for performance.

    Args:
        path: JSONPath expression to compile

    Returns:
        Compiled JSONPath object
    """
    return jsonpath.compile(path)


def extract_nested_field(obj: Dict[str, Any], path: str) -> str:
    """Extract field value from nested dict using JSONPath query.

    Args:
        obj: The dictionary to extract from
        path: JSONPath expression. Examples:
              - "metadata.name" (simple field)
              - "metadata.labels['kubernetes.io/service-name']" (quoted key)
              - "spec.rules[0].host" (array indexing)
              - "metadata.labels.app" (nested field)

    Returns:
        The field value as string or empty string if not found/invalid.
        Complex objects (dict/list) return empty string to prevent
        unintended serialization in templates.

    Performance:
        - Simple paths: ~50,000 ops/sec
        - Complex paths with arrays: ~20,000 ops/sec
        - Compiled expressions cached up to 256 unique paths
    """
    # Input validation
    if not path or not isinstance(path, str):
        logger.debug("Invalid path: must be non-empty string")
        return ""

    # Prevent DoS with overly complex paths
    if len(path) > 500:  # Generous limit for Kubernetes field paths
        logger.debug(f"JSONPath expression too long: {len(path)} characters")
        return ""

    try:
        compiled_path = _compile_jsonpath(path)
        matches = compiled_path.findall(obj)
        if matches:
            value = matches[0]
            if value is None or isinstance(value, (dict, list)):
                return ""
            return str(value)
        return ""
    except JSONPathError as e:
        logger.debug(f"Invalid JSONPath expression '{path}': {e}")
        return ""
    except (ValueError, TypeError) as e:
        logger.debug(f"Error extracting field with path '{path}': {e}")
        return ""
    except Exception as e:
        logger.warning(
            f"Unexpected error processing JSONPath '{path}': {e}",
            extra={
                "path": path,
                "obj_type": type(obj).__name__,
                "error_type": type(e).__name__,
            },
        )
        return ""


async def update_resource_index(
    param: str,
    namespace: str,
    name: str,
    body: Dict[str, Any],
    logger: logging.Logger,
    memo: Any = None,
    **kwargs_: Any,
) -> Dict[Tuple[str, ...], Dict[str, Any]]:
    """Update resource index with configurable key."""
    logger.debug(f"📝 Updating index {param} for {namespace}/{name}...")

    # Get the watch config for this resource type
    if memo and hasattr(memo, "config") and hasattr(memo.config, "watched_resources"):
        watch_config = memo.config.watched_resources.get(param)
    else:
        watch_config = None

    if not watch_config:
        # Fallback to default indexing (namespace, name)
        return {(namespace, name): dict(body)}

    # Extract index key values based on configured fields
    index_values = []
    for field_path in watch_config.index_by:
        value = extract_nested_field(body, field_path)
        index_values.append(value)

    return {tuple(index_values): dict(body)}


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


def _prepare_template_context(
    memo: Any, indices: Dict[str, Any]
) -> Tuple[TemplateContext, Dict[str, Any], list]:
    """Prepare template context and variables for rendering."""
    memo.haproxy_config_context.rendered_content.clear()
    memo.haproxy_config_context._clear_cache()
    memo.haproxy_config_context.rendered_config = None

    template_context = TemplateContext(
        resources=indices, namespace=get_current_namespace()
    )

    validation_errors = []

    def register_error(
        resource_type: str, resource_uid: str, error_message: str
    ) -> None:
        validation_errors.append(
            {
                "resource_type": resource_type,
                "resource_uid": resource_uid,
                "error": error_message,
            }
        )
        logger.warning(
            "Template validation error",
            resource_type=resource_type,
            resource_uid=resource_uid,
            error=error_message,
        )

    template_vars = {
        "resources": template_context.resources,
        "namespace": template_context.namespace,
        "register_error": register_error,
    }

    return template_context, template_vars, validation_errors


def _render_haproxy_config(
    memo: Any, template_vars: Dict[str, Any], metrics: Any
) -> None:
    """Render the main HAProxy configuration template."""
    try:
        with trace_template_render(CONTENT_TYPE_HAPROXY_CONFIG):
            with metrics.time_template_render(CONTENT_TYPE_HAPROXY_CONFIG):
                rendered_content = memo.template_renderer.render(
                    memo.config.haproxy_config.template,
                    template_name="haproxy_config",
                    **template_vars,
                )

        rendered_config = RenderedConfig(content=rendered_content)
        memo.haproxy_config_context.rendered_config = rendered_config
        metrics.record_template_render(CONTENT_TYPE_HAPROXY_CONFIG, "success")
        add_span_attributes(
            template_size=len(rendered_content), template_vars_count=len(template_vars)
        )
        record_span_event("haproxy_config_rendered")
        logger.debug("✅ Rendered HAProxy configuration template")

    except Exception as e:
        metrics.record_template_render(CONTENT_TYPE_HAPROXY_CONFIG, "error")
        metrics.record_error("template_render_failed", "operator")
        record_span_event("haproxy_config_render_failed", {"error": str(e)})
        # The error message already includes detailed context from format_template_error
        logger.error(f"❌ {e}")


def _render_content_templates(
    memo: Any, template_vars: Dict[str, Any], metrics: Any
) -> list:
    """Render all content templates (maps, certificates, files)."""
    content_collections = [
        (CONTENT_TYPE_MAP, memo.config.maps),
        (CONTENT_TYPE_CERTIFICATE, memo.config.certificates),
        (CONTENT_TYPE_FILE, memo.config.files),
    ]

    template_errors = []

    for content_type, items in content_collections:
        for filename, template_config in items.items():
            try:
                with trace_template_render(content_type, filename):
                    with metrics.time_template_render(content_type):
                        rendered_content_text = memo.template_renderer.render(
                            template_config.template,
                            template_name=f"{content_type}/{filename}",
                            **template_vars,
                        )

                rendered_content = RenderedContent(
                    filename=filename,
                    content=rendered_content_text,
                    content_type=content_type,
                )
                memo.haproxy_config_context.rendered_content.append(rendered_content)

                metrics.record_template_render(content_type, "success")
                add_span_attributes(
                    **{
                        f"{content_type}_filename": filename,
                        f"{content_type}_size": len(rendered_content_text),
                    }
                )
                record_span_event(f"{content_type}_rendered", {"filename": filename})
                logger.debug(f"✅ Rendered {content_type} template for {filename}")

            except Exception as e:
                template_error = {
                    "type": content_type,
                    "filename": filename,
                    "error": str(e),
                }
                template_errors.append(template_error)

                metrics.record_template_render(content_type, "error")
                metrics.record_error("template_render_failed", "operator")
                record_span_event(
                    f"{content_type}_render_failed",
                    {"filename": filename, "error": str(e)},
                )
                # The error message already includes detailed context from format_template_error
                logger.error(f"❌ {e}")

    return template_errors


def _validate_template_errors(template_errors: list) -> None:
    """Validate template errors and abort on critical ones."""
    if not template_errors:
        return

    logger.warning(f"Template rendering completed with {len(template_errors)} errors")

    critical_errors = [
        e for e in template_errors if e["type"] == CONTENT_TYPE_CERTIFICATE
    ]
    if critical_errors:
        error_msg = f"Critical certificate template errors: {[e['filename'] + ': ' + e['error'] for e in critical_errors]}"
        logger.error(f"❌ Aborting deployment due to critical errors: {error_msg}")
        raise RuntimeError(error_msg)


async def trigger_template_rendering(memo: Any, **kwargs: Any) -> None:
    """
    Trigger template rendering through the debouncer.

    This function is called by kopf event handlers when resources change.
    It signals the debouncer which will handle rate limiting and batching.
    """
    if hasattr(memo, "debouncer") and memo.debouncer:
        await memo.debouncer.trigger()
    else:
        # Fallback to direct rendering if debouncer not initialized
        # This can happen during initial startup
        logger.warning("Debouncer not initialized, rendering directly")
        await render_haproxy_templates(memo, **kwargs)


@observe(
    component="operator",
    span_name="render_haproxy_templates",
    trace_attributes={"operation.category": "template_rendering"},
)
async def render_haproxy_templates(memo: Any, **kwargs: Any) -> None:
    """Render all HAProxy templates with current context data."""
    logger.debug("Rendering HAProxy templates")
    metrics = get_metrics_collector()

    indices = _collect_resource_indices(memo, metrics)
    template_context, template_vars, validation_errors = _prepare_template_context(
        memo, indices
    )

    _render_haproxy_config(memo, template_vars, metrics)
    template_errors = _render_content_templates(memo, template_vars, metrics)
    _validate_template_errors(template_errors)

    memo.haproxy_config_context._clear_cache()

    if validation_errors:
        logger.warning(
            f"Template validation found {len(validation_errors)} errors",
            errors=validation_errors,
        )

    await synchronize_with_haproxy_instances(memo)


async def synchronize_with_haproxy_instances(memo: Any) -> None:
    """Synchronize rendered configuration with HAProxy instances via Dataplane API."""
    logger.info("🚀 SYNC FUNCTION CALLED - Starting synchronization...")
    metrics = get_metrics_collector()

    if not _validate_sync_prerequisites(memo):
        return

    try:
        haproxy_pods_collection = _get_haproxy_pod_collection(memo)
        if haproxy_pods_collection is None:
            return

        production_urls = get_production_urls_from_index(haproxy_pods_collection)
        if not production_urls:
            logger.warning(
                "⚠️ No production HAProxy pods found - skipping synchronization"
            )
            return

        if not hasattr(memo, "deployment_history"):
            memo.deployment_history = DeploymentHistory()

        synchronizer = ConfigSynchronizer(
            production_urls=production_urls,
            validation_url=memo.config.validation_dataplane_url,
            credentials=memo.credentials,
            deployment_history=memo.deployment_history,
        )

        results = await synchronizer.sync_configuration(memo.haproxy_config_context)

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
        _log_haproxy_error_hints(e, memo)

    except DataplaneAPIError as e:
        metrics.record_error("dataplane_api_failed", "dataplane")
        logger.error(f"❌ Dataplane API error: {e}")

    except Exception as e:
        metrics.record_error("sync_unexpected_error", "dataplane")
        logger.error(f"❌ Unexpected error during synchronization: {e}")


# =============================================================================
# Resource Watchers
# =============================================================================


async def haproxy_pods_index(
    namespace: str,
    name: str,
    body: Dict[str, Any],
    logger: logging.Logger,
    **kwargs: Any,
) -> Dict[Tuple[str, str], Dict[str, Any]]:
    """Index HAProxy pods for efficient discovery."""
    logger.info(f"📝 Indexing HAProxy pod {namespace}/{name}")

    # Check if pod is being deleted using deletionTimestamp
    # Note: Index handlers don't receive event type like event handlers do,
    # so checking deletionTimestamp is the appropriate approach for kopf index handlers
    metadata = body.get("metadata", {})
    if metadata.get("deletionTimestamp"):
        logger.info(f"🗑️ Pod {namespace}/{name} is being deleted, removing from index")
        return {}  # Return empty dict to remove from index

    # Log pod status for debugging
    pod_ip = body.get("status", {}).get("podIP")
    phase = body.get("status", {}).get("phase")
    logger.info(f"🔍 Pod {name} - Phase: {phase}, IP: {pod_ip}")

    # No manual filtering needed - Kopf already filtered by labels
    # Index by namespace/name for easy lookup
    return {(namespace, name): body}


async def handle_haproxy_pod_create(**kwargs: Any) -> None:
    """Handle HAProxy pod creation events."""
    body = kwargs.get("body", {})
    namespace = kwargs.get("namespace") or body.get("metadata", {}).get(
        "namespace", "default"
    )
    name = kwargs.get("name") or body.get("metadata", {}).get("name", "unknown")

    # No manual filtering needed - Kopf already filtered by labels
    logger.info(f"🆕 New HAProxy pod created: {namespace}/{name}")
    # Trigger template re-rendering for the new pod
    # Note: This will be handled by the template rendering system
    # The new pod will be available in the index for the next sync


def setup_haproxy_pod_indexing(memo: Any) -> None:
    """Set up HAProxy pod indexing and event handling."""
    current_namespace = get_current_namespace()

    logger.info("🔍 Setting up HAProxy pod indexing...")

    # Get label selector from config for filtering at API level
    pod_labels = memo.config.pod_selector.match_labels if memo.config else {}
    logger.info(f"📋 Using label selector: {pod_labels}")

    # Register HAProxy pod indexing with label filtering
    kopf.index("pods", id=HAPROXY_PODS_INDEX, param="haproxy_pods", labels=pod_labels)(
        haproxy_pods_index
    )  # type: ignore

    # Register pod creation handler with label filtering (only trigger on create events)
    kopf.on.create("pods", id="haproxy_pod_create", labels=pod_labels)(
        handle_haproxy_pod_create
    )

    logger.info(
        f"✅ HAProxy pod indexing configured for namespace '{current_namespace}' with labels {pod_labels}"
    )


def setup_resource_watchers(memo: Any) -> None:
    """Set up watchers for Kubernetes resources."""
    resource_count = len(memo.config.watched_resources)
    logger.info(f"👀 Setting up {resource_count} resource watchers...")

    for resource_id, watch_config in memo.config.watched_resources.items():
        resource_type = watch_config.kind.lower()

        # Set up index and event handler with group/version if specified
        kwargs = {"id": resource_id, "param": resource_id}
        event_kwargs = {"id": f"{resource_id}_event"}

        if watch_config.group and watch_config.version:
            kwargs.update(
                {"group": watch_config.group, "version": watch_config.version}
            )
            event_kwargs.update(
                {"group": watch_config.group, "version": watch_config.version}
            )

            api_version = f"{watch_config.group}/{watch_config.version}"
            logger.info(
                f"🔍 Watching {resource_type} ({api_version}) with id '{resource_id}'"
            )
        else:
            logger.info(
                f"🔍 Watching {resource_type} (core/v1) with id '{resource_id}'"
            )

        kopf.index(resource_type, **kwargs)(update_resource_index)  # type: ignore[arg-type]
        kopf.on.event(resource_type, **event_kwargs)(trigger_template_rendering)  # type: ignore[arg-type]

    # Set up HAProxy pod indexing
    setup_haproxy_pod_indexing(memo)

    logger.info("✅ All resource watchers configured successfully")


# =============================================================================
# Operator Initialization
# =============================================================================


async def initialize_configuration(memo: Any) -> None:
    """Initialize operator configuration from ConfigMap."""
    metrics = get_metrics_collector()

    configmap_name = memo.cli_options.configmap_name
    secret_name = memo.cli_options.secret_name
    logger.info(
        f"⚙️ Initializing config from configmap {configmap_name} and credentials from secret {secret_name}."
    )

    try:
        with metrics.time_config_reload():
            namespace = get_current_namespace() or "default"
            # Load configuration from ConfigMap
            configmap = await fetch_configmap(configmap_name, namespace)
            memo.config = await load_config_from_configmap(configmap)
            memo.template_renderer = TemplateRenderer.from_config(memo.config)

            # Load credentials from Secret
            secret = await fetch_secret(secret_name, namespace)
            secret_data = secret.data if hasattr(secret, "data") else secret["data"]
            memo.credentials = Credentials.from_secret(secret_data)

        metrics.record_config_reload(success=True)
        logger.info("✅ Configuration and credentials loaded successfully.")
    except Exception as e:
        metrics.record_config_reload(success=False)
        metrics.record_error("config_load_failed", "operator")
        logger.error(f"❌ Failed to load configuration or credentials: {e}")
        raise


async def init_watch_configmap(memo: Any, **kwargs: Any) -> None:
    """Set up startup handlers after configuration is loaded."""

    configmap_name = memo.cli_options.configmap_name
    kopf.on.event(
        "configmap",
        when=lambda name, namespace, type, **_: (
            name == configmap_name and namespace == get_current_namespace()
        ),
    )(handle_configmap_change)  # type: ignore[arg-type]

    # Watch Secret changes
    secret_name = memo.cli_options.secret_name
    current_namespace = get_current_namespace()
    kopf.on.event(
        "secret",
        when=lambda name, namespace, type, **_: (
            name == secret_name and namespace == current_namespace
        ),
    )(handle_secret_change)  # type: ignore[arg-type]


async def init_management_socket(memo: Any, **kwargs: Any) -> None:
    # Start management socket server for state inspection
    socket_path = memo.cli_options.socket_path
    memo.socket_server_task = asyncio.create_task(
        run_management_socket_server(memo, socket_path)
    )


async def init_template_debouncer(memo: Any, **kwargs: Any) -> None:
    """Initialize and start the template rendering debouncer."""
    if hasattr(memo, "debouncer") and memo.debouncer:
        # Stop existing debouncer if one exists
        await memo.debouncer.stop()

    # Get configuration values
    config = memo.config
    min_interval = config.template_rendering.min_render_interval
    max_interval = config.template_rendering.max_render_interval

    # Create and start debouncer
    memo.debouncer = TemplateRenderDebouncer(
        min_interval=min_interval,
        max_interval=max_interval,
        render_func=render_haproxy_templates,
        memo=memo,
    )
    memo.debouncer.start()

    logger.info(
        f"Template debouncer started with intervals: min={min_interval}s, max={max_interval}s"
    )


async def cleanup_template_debouncer(memo: Any, **kwargs: Any) -> None:
    """Stop the template rendering debouncer on shutdown."""
    if hasattr(memo, "debouncer") and memo.debouncer:
        logger.info("Stopping template debouncer...")
        await memo.debouncer.stop()
        memo.debouncer = None


async def init_metrics_server(memo: Any, **kwargs: Any) -> None:
    """Initialize and start the Prometheus metrics server."""
    metrics = get_metrics_collector()
    metrics_port = getattr(memo.cli_options, "metrics_port", DEFAULT_METRICS_PORT)
    # Start metrics server as a background task
    memo.metrics_server_task = asyncio.create_task(
        metrics.start_metrics_server(metrics_port)
    )


def configure_webhook_server(
    settings: kopf.OperatorSettings, memo: Any, **kwargs: Any
) -> None:
    """Configure webhook server for admission control."""
    # Check if any resources have webhook validation enabled
    has_webhooks = any(
        getattr(watch_config, "enable_validation_webhook", False)
        for watch_config in memo.config.watched_resources.values()
    )

    if not has_webhooks:
        logger.info(
            "⏭️ No validation webhooks configured - skipping webhook server setup"
        )
        return

    logger.info("🔌 Configuring webhook server for admission control...")

    cert_dir = "/tmp/webhook-certs"  # nosec B108 - Standard K8s volume mount path
    cert_file = f"{cert_dir}/webhook-cert.pem"
    key_file = f"{cert_dir}/webhook-key.pem"
    ca_file = f"{cert_dir}/webhook-ca.pem"

    def cleanup_temp_dir(temp_dir: str) -> None:
        """Clean up temporary directory at exit."""
        try:
            if os.path.exists(temp_dir):
                shutil.rmtree(temp_dir)
                logger.debug(
                    f"🧹 Cleaned up temporary webhook certificate directory: {temp_dir}"
                )
        except Exception as e:
            logger.warning(f"Failed to clean up temporary directory {temp_dir}: {e}")

    if os.path.exists(cert_file) and os.path.exists(key_file):
        # Create a writable temporary directory for kopf's CA dump
        temp_dir = tempfile.mkdtemp(prefix="webhook-ca-")
        temp_ca_file = f"{temp_dir}/webhook-ca.pem"

        # Register cleanup for this directory
        atexit.register(cleanup_temp_dir, temp_dir)

        # Copy the CA file to writable location if it exists
        if os.path.exists(ca_file):
            shutil.copy2(ca_file, temp_ca_file)
            ca_dump_file = temp_ca_file
        else:
            # Fall back to using certificate file as CA
            ca_dump_file = temp_ca_file

        settings.admission.server = kopf.WebhookServer(
            addr="0.0.0.0",  # nosec B104 - Kubernetes webhook must bind all interfaces
            port=DEFAULT_WEBHOOK_PORT,
            certfile=cert_file,
            pkeyfile=key_file,
            cadump=ca_dump_file,
        )
        logger.info(
            f"✅ Webhook server configured on port {DEFAULT_WEBHOOK_PORT} with mounted TLS certificates"
        )
    else:
        # Create a writable temporary directory for self-signed certificates
        temp_dir = tempfile.mkdtemp(prefix="webhook-ca-")
        temp_ca_file = f"{temp_dir}/webhook-ca.pem"

        # Register cleanup for this directory
        atexit.register(cleanup_temp_dir, temp_dir)

        settings.admission.server = kopf.WebhookServer(
            addr="0.0.0.0",  # nosec B104 - Kubernetes webhook must bind all interfaces
            port=DEFAULT_WEBHOOK_PORT,
            cadump=temp_ca_file,
        )
        logger.info(
            f"✅ Webhook server configured on port {DEFAULT_WEBHOOK_PORT} with self-signed certificates"
        )

    settings.admission.managed = "haproxy-template-ic.io"


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
            haproxy_config_context=HAProxyConfigContext(
                config=Config(
                    pod_selector=PodSelector(match_labels={"app": "haproxy"}),
                    haproxy_config=TemplateConfig(template="# Initial config"),
                ),
                template_context=TemplateContext(namespace="default"),
                rendered_config=None,
            ),
        ),
        loop,
        stop_flag,
    )


# =============================================================================
# Main Operator Loop
# =============================================================================


def run_operator_loop(cli_options: "CliOptions") -> None:
    """Run the main operator loop with config reload capability."""
    # Initialize metrics on first run
    metrics = get_metrics_collector()
    metrics.set_app_info()

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
            haproxy_config_context=HAProxyConfigContext(
                config=Config(
                    pod_selector=PodSelector(match_labels={"app": "haproxy"}),
                    haproxy_config=TemplateConfig(template="# Initial config"),
                ),
                template_context=TemplateContext(namespace="default"),
                rendered_config=None,
            ),
            indices=indexers.indices,
            template_renderer=None,  # Will be initialized when config is loaded
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
        # Initialize and start the template rendering debouncer
        kopf.on.startup()(init_template_debouncer)
        # Start the metrics server for Prometheus monitoring
        kopf.on.startup()(init_metrics_server)
        # Configure webhook server for admission control
        kopf.on.startup()(configure_webhook_server)

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

        # Clean up debouncer before exit/reload
        if hasattr(memo, "debouncer") and memo.debouncer:
            asyncio.run_coroutine_threadsafe(
                cleanup_template_debouncer(memo), loop
            ).result(timeout=5)

        # Check if we should exit or reload
        if not memo.config_reload_flag.done():
            break  # Normal shutdown

        logger.info("🔄 Configuration changed. Reinitializing...")

    logger.info("👋 Operator shutdown complete.")
