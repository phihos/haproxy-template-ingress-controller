"""
Template rendering functionality for the Kubernetes operator.

Handles rendering of HAProxy configurations, maps, certificates, and other
template-based content with metrics and error handling.
"""

import logging
from typing import Any, Dict, List, Tuple

from kopf._core.engines.indexing import OperatorIndices

from haproxy_template_ic.constants import (
    CONTENT_TYPE_CERTIFICATE,
    CONTENT_TYPE_FILE,
    CONTENT_TYPE_HAPROXY_CONFIG,
    CONTENT_TYPE_MAP,
)
from haproxy_template_ic.tracing import (
    add_span_attributes,
    record_span_event,
    trace_async_function,
    trace_template_render,
)

from ..dataplane.synchronizer import ConfigSynchronizer
from ..metrics import MetricsCollector
from ..models.config import Config
from ..models.context import HAProxyConfigContext, TemplateContext
from ..models.templates import ContentType, RenderedConfig, RenderedContent
from ..templating import TemplateRenderer
from .synchronization import synchronize_with_haproxy_instances

logger = logging.getLogger(__name__)

__all__ = [
    "render_haproxy_templates",
    "_prepare_template_context",
    "_render_haproxy_config",
    "_render_content_templates",
    "_validate_template_errors",
]


def _prepare_template_context(
    haproxy_config_context: HAProxyConfigContext, indices: Dict[str, Any]
) -> Tuple[TemplateContext, Dict[str, Any], List]:
    """Prepare template context and variables for rendering."""
    haproxy_config_context.rendered_content.clear()
    haproxy_config_context._clear_cache()
    haproxy_config_context.rendered_config = None

    template_context = TemplateContext(resources=indices)

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
            f"Template validation error: resource_type={resource_type} resource_uid={resource_uid} error={error_message}"
        )

    template_vars = {
        "resources": template_context.resources,
        "register_error": register_error,
    }

    return template_context, template_vars, validation_errors


def _render_haproxy_config(
    config: Config,
    haproxy_config_context: HAProxyConfigContext,
    template_renderer: TemplateRenderer,
    template_vars: Dict[str, Any],
    metrics: MetricsCollector,
) -> None:
    """Render the main HAProxy configuration template."""
    try:
        with trace_template_render(CONTENT_TYPE_HAPROXY_CONFIG):
            with metrics.time_template_render(CONTENT_TYPE_HAPROXY_CONFIG):
                rendered_content = template_renderer.render(
                    config.haproxy_config.template,
                    template_name="haproxy_config",
                    **template_vars,
                )

        rendered_config = RenderedConfig(content=rendered_content)
        haproxy_config_context.rendered_config = rendered_config
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
    config: Config,
    template_renderer: TemplateRenderer,
    haproxy_config_context: HAProxyConfigContext,
    template_vars: Dict[str, Any],
    metrics: Any,
) -> List:
    """Render all content templates (maps, certificates, files)."""
    content_collections = [
        (CONTENT_TYPE_MAP, config.maps),
        (CONTENT_TYPE_CERTIFICATE, config.certificates),
        (CONTENT_TYPE_FILE, config.files),
    ]

    template_errors = []

    for content_type, items in content_collections:
        for filename, template_config in items.items():
            try:
                with trace_template_render(content_type, filename):
                    with metrics.time_template_render(content_type):
                        rendered_content_text = template_renderer.render(
                            template_config.template,
                            template_name=f"{content_type}/{filename}",
                            **template_vars,
                        )

                rendered_content = RenderedContent(
                    filename=filename,
                    content=rendered_content_text,
                    content_type=ContentType(content_type),
                )
                haproxy_config_context.rendered_content.append(rendered_content)

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
                logger.error(f"❌ Failed to render {content_type} {filename}: {e}")

    return template_errors


def _validate_template_errors(template_errors: List) -> None:
    """Validate and handle template rendering errors."""
    if template_errors:
        error_count = len(template_errors)
        error_summary = f"Template rendering failed with {error_count} error(s):\n"

        for error in template_errors[:5]:  # Show first 5 errors
            error_summary += (
                f"- {error['type']} '{error['filename']}': {error['error']}\n"
            )

        if error_count > 5:
            error_summary += f"... and {error_count - 5} more errors"

        raise RuntimeError(error_summary.strip())


@trace_async_function(
    span_name="render_haproxy_templates",
    attributes={"operation.category": "templating"},
)
async def render_haproxy_templates(
    config: Config,
    haproxy_config_context: HAProxyConfigContext,
    template_renderer: TemplateRenderer,
    config_synchronizer: ConfigSynchronizer,
    kopf_indices: OperatorIndices,
    metrics: MetricsCollector,
    logger: logging.Logger,
    **kwargs: Any,
) -> None:
    """Render all HAProxy templates with comprehensive error handling and metrics."""

    try:
        # Collect all current resource indices
        from .k8s_resources import _collect_resource_indices

        indices = _collect_resource_indices(config, kopf_indices, metrics)

        # Prepare template context
        template_context, template_vars, validation_errors = _prepare_template_context(
            haproxy_config_context, indices
        )

        # Render main HAProxy configuration
        _render_haproxy_config(
            config, haproxy_config_context, template_renderer, template_vars, metrics
        )

        # Render content templates (maps, certificates, files)
        template_errors = _render_content_templates(
            config, template_renderer, haproxy_config_context, template_vars, metrics
        )

        # Validate results
        _validate_template_errors(template_errors)

        # Handle validation errors from templates
        if validation_errors:
            error_count = len(validation_errors)
            logger.warning(
                f"⚠️ Template validation completed with {error_count} warning(s)"
            )
            for error in validation_errors[:3]:  # Show first 3 warnings
                logger.warning(
                    f"Template warning in {error['resource_type']}: {error['error']}"
                )

        haproxy_config_size = (
            len(haproxy_config_context.rendered_config.content)
            if haproxy_config_context.rendered_config
            else 0
        )
        content_items = len(haproxy_config_context.rendered_content)
        resource_types = len(indices)

        logger.info(
            f"🎯 Template rendering completed successfully: haproxy_config_size={haproxy_config_size} content_items={content_items} resource_types={resource_types}"
        )

        record_span_event("template_rendering_completed")
        metrics.record_template_render("all", "success")

        # Trigger synchronization with HAProxy instances
        try:
            await synchronize_with_haproxy_instances(
                config, haproxy_config_context, kopf_indices, config_synchronizer
            )
            logger.debug("🚀 HAProxy synchronization completed successfully")
        except Exception as sync_error:
            logger.error(f"❌ HAProxy synchronization failed: {sync_error}")
            # Don't re-raise - template rendering was successful, sync failure is separate

    except Exception as e:
        metrics.record_template_render("all", "error")
        metrics.record_error("template_rendering_failed", "operator")
        record_span_event("template_rendering_failed", {"error": str(e)})

        logger.error(f"❌ Template rendering failed: {e}")

        # Clear any partial results to prevent inconsistent state
        haproxy_config_context.rendered_content.clear()
        haproxy_config_context.rendered_config = None

        raise
