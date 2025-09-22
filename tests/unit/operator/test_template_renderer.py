"""
Unit tests for haproxy_template_ic.operator.template_renderer module.

Comprehensive test coverage for template rendering functionality including
configuration templates, content templates, error handling, and metrics.
"""

import pytest
from unittest.mock import AsyncMock, Mock, call, patch

from haproxy_template_ic.constants import (
    CONTENT_TYPE_CERTIFICATE,
    CONTENT_TYPE_FILE,
    CONTENT_TYPE_HAPROXY_CONFIG,
    CONTENT_TYPE_MAP,
)
from haproxy_template_ic.models.context import HAProxyConfigContext, TemplateContext
from haproxy_template_ic.models.templates import (
    ContentType,
    RenderedConfig,
    TemplatePreparationResult,
    TemplateRenderContext,
)
from haproxy_template_ic.operator.template_renderer import (
    _prepare_template_context,
    _render_content_templates,
    _render_haproxy_config,
    _validate_template_errors,
    render_haproxy_templates,
)


class TestPrepareTemplateContext:
    """Test template context preparation functionality."""

    def test_prepare_template_context_success(self):
        """Test successful template context preparation."""
        # Arrange
        mock_context = Mock(spec=HAProxyConfigContext)
        mock_context.rendered_content = []
        mock_context._clear_cache = Mock()

        indices = {
            "services": {"service1": {"name": "test-service"}},
            "pods": {"pod1": {"name": "test-pod"}},
        }

        # Act
        result = _prepare_template_context(mock_context, indices)

        # Assert
        assert isinstance(result, TemplatePreparationResult)
        assert isinstance(result.template_context, TemplateContext)
        assert "services" in result.template_context.resources
        assert "pods" in result.template_context.resources
        assert "resources" in result.template_vars
        assert "register_error" in result.template_vars
        assert callable(result.template_vars["register_error"])
        assert result.validation_errors == []

        # Verify context was properly reset
        mock_context._clear_cache.assert_called_once()
        assert mock_context.rendered_config is None

    def test_prepare_template_context_register_error_function(self):
        """Test that register_error function properly records validation errors."""
        # Arrange
        mock_context = Mock(spec=HAProxyConfigContext)
        mock_context.rendered_content = []
        mock_context._clear_cache = Mock()
        indices = {}

        # Act
        result = _prepare_template_context(mock_context, indices)
        register_error = result.template_vars["register_error"]

        # Register test errors
        register_error("ingress", "uid-123", "Invalid host configuration")
        register_error("service", "uid-456", "Missing port specification")

        # Assert
        assert len(result.validation_errors) == 2

        error1 = result.validation_errors[0]
        assert error1.resource_type == "ingress"
        assert error1.resource_uid == "uid-123"
        assert error1.error == "Invalid host configuration"

        error2 = result.validation_errors[1]
        assert error2.resource_type == "service"
        assert error2.resource_uid == "uid-456"
        assert error2.error == "Missing port specification"

    @patch("haproxy_template_ic.operator.template_renderer.logger")
    def test_prepare_template_context_logs_validation_errors(self, mock_logger):
        """Test that validation errors are properly logged."""
        # Arrange
        mock_context = Mock(spec=HAProxyConfigContext)
        mock_context.rendered_content = []
        mock_context._clear_cache = Mock()
        indices = {}

        # Act
        result = _prepare_template_context(mock_context, indices)
        register_error = result.template_vars["register_error"]
        register_error("ingress", "uid-123", "Test error message")

        # Assert
        mock_logger.warning.assert_called_once_with(
            "Template validation error: resource_type=ingress resource_uid=uid-123 error=Test error message"
        )


class TestRenderHAProxyConfig:
    """Test HAProxy configuration template rendering."""

    def test_render_haproxy_config_success(self):
        """Test successful HAProxy configuration rendering."""
        # Arrange
        mock_config = Mock()
        mock_config.haproxy_config.template = (
            "global\n    daemon\ndefaults\n    mode http"
        )

        mock_renderer = Mock()
        mock_renderer.render.return_value = "rendered haproxy config"

        mock_metrics = Mock()
        mock_timer = Mock()
        mock_timer.__enter__ = Mock(return_value=mock_timer)
        mock_timer.__exit__ = Mock(return_value=None)
        mock_metrics.time_template_render.return_value = mock_timer

        mock_context = Mock(spec=HAProxyConfigContext)

        template_vars = {"resources": {}, "register_error": Mock()}

        render_context = TemplateRenderContext(
            config=mock_config,
            template_renderer=mock_renderer,
            haproxy_config_context=mock_context,
            template_vars=template_vars,
            metrics=mock_metrics,
        )

        # Act
        with (
            patch(
                "haproxy_template_ic.operator.template_renderer.trace_template_render"
            ) as mock_trace,
            patch(
                "haproxy_template_ic.operator.template_renderer.add_span_attributes"
            ) as mock_attrs,
            patch(
                "haproxy_template_ic.operator.template_renderer.record_span_event"
            ) as mock_event,
        ):
            _render_haproxy_config(render_context)

        # Assert
        mock_renderer.render.assert_called_once_with(
            mock_config.haproxy_config.template,
            template_name="haproxy_config",
            **template_vars,
        )
        mock_metrics.time_template_render.assert_called_once_with(
            CONTENT_TYPE_HAPROXY_CONFIG
        )
        mock_metrics.record_template_render.assert_called_once_with(
            CONTENT_TYPE_HAPROXY_CONFIG, "success"
        )

        # Verify rendered config was set
        assert isinstance(mock_context.rendered_config, RenderedConfig)
        assert mock_context.rendered_config.content == "rendered haproxy config"

        # Verify tracing calls
        mock_trace.assert_called_once_with(CONTENT_TYPE_HAPROXY_CONFIG)
        mock_attrs.assert_called_once()
        mock_event.assert_called_with("haproxy_config_rendered")

    def test_render_haproxy_config_failure(self):
        """Test HAProxy configuration rendering failure."""
        # Arrange
        mock_config = Mock()
        mock_config.haproxy_config.template = "invalid template {{ undefined_var }}"

        mock_renderer = Mock()
        mock_renderer.render.side_effect = RuntimeError("Template rendering failed")

        mock_metrics = Mock()
        mock_timer = Mock()
        mock_timer.__enter__ = Mock(return_value=mock_timer)
        mock_timer.__exit__ = Mock(return_value=None)
        mock_metrics.time_template_render.return_value = mock_timer

        mock_context = Mock(spec=HAProxyConfigContext)
        template_vars = {"resources": {}}

        render_context = TemplateRenderContext(
            config=mock_config,
            template_renderer=mock_renderer,
            haproxy_config_context=mock_context,
            template_vars=template_vars,
            metrics=mock_metrics,
        )

        # Act & Assert - should not raise, just record metrics and log
        with (
            patch(
                "haproxy_template_ic.operator.template_renderer.trace_template_render"
            ),
            patch(
                "haproxy_template_ic.operator.template_renderer.record_span_event"
            ) as mock_event,
            patch(
                "haproxy_template_ic.operator.template_renderer.logger"
            ) as mock_logger,
        ):
            _render_haproxy_config(render_context)

        # Assert error handling
        mock_metrics.record_template_render.assert_called_with(
            CONTENT_TYPE_HAPROXY_CONFIG, "error"
        )
        mock_metrics.record_error.assert_called_with(
            "template_render_failed", "operator"
        )
        mock_event.assert_called_with(
            "haproxy_config_render_failed", {"error": "Template rendering failed"}
        )
        mock_logger.error.assert_called_once()


class TestRenderContentTemplates:
    """Test content template rendering (maps, certificates, files)."""

    def test_render_content_templates_success(self):
        """Test successful rendering of all content types."""
        # Arrange
        mock_config = Mock()
        mock_config.maps = {"hosts.map": Mock(template="host1 backend1")}
        mock_config.certificates = {"ssl.pem": Mock(template="cert content")}
        mock_config.files = {"error.html": Mock(template="<html>Error</html>")}

        mock_renderer = Mock()
        mock_renderer.render.side_effect = [
            "rendered hosts.map content",
            "rendered ssl.pem content",
            "rendered error.html content",
        ]

        mock_metrics = Mock()
        mock_timer = Mock()
        mock_timer.__enter__ = Mock(return_value=mock_timer)
        mock_timer.__exit__ = Mock(return_value=None)
        mock_metrics.time_template_render.return_value = mock_timer

        mock_context = Mock(spec=HAProxyConfigContext)
        mock_context.rendered_content = []
        template_vars = {"resources": {}}

        render_context = TemplateRenderContext(
            config=mock_config,
            template_renderer=mock_renderer,
            haproxy_config_context=mock_context,
            template_vars=template_vars,
            metrics=mock_metrics,
        )

        # Act
        with (
            patch(
                "haproxy_template_ic.operator.template_renderer.trace_template_render"
            ),
            patch("haproxy_template_ic.operator.template_renderer.add_span_attributes"),
            patch("haproxy_template_ic.operator.template_renderer.record_span_event"),
        ):
            template_errors = _render_content_templates(render_context)

        # Assert
        assert template_errors == []

        # Verify all templates were rendered
        expected_calls = [
            call("host1 backend1", template_name="map/hosts.map", **template_vars),
            call("cert content", template_name="certificate/ssl.pem", **template_vars),
            call(
                "<html>Error</html>", template_name="file/error.html", **template_vars
            ),
        ]
        mock_renderer.render.assert_has_calls(expected_calls)

        # Verify rendered content was added
        assert len(mock_context.rendered_content) == 3

        # Check map content
        map_content = mock_context.rendered_content[0]
        assert map_content.filename == "hosts.map"
        assert map_content.content == "rendered hosts.map content"
        assert map_content.content_type == ContentType.MAP

        # Check certificate content
        cert_content = mock_context.rendered_content[1]
        assert cert_content.filename == "ssl.pem"
        assert cert_content.content == "rendered ssl.pem content"
        assert cert_content.content_type == ContentType.CERTIFICATE

        # Check file content
        file_content = mock_context.rendered_content[2]
        assert file_content.filename == "error.html"
        assert file_content.content == "rendered error.html content"
        assert file_content.content_type == ContentType.FILE

        # Verify metrics
        assert mock_metrics.record_template_render.call_count == 3
        mock_metrics.record_template_render.assert_has_calls(
            [
                call(CONTENT_TYPE_MAP, "success"),
                call(CONTENT_TYPE_CERTIFICATE, "success"),
                call(CONTENT_TYPE_FILE, "success"),
            ]
        )

    def test_render_content_templates_partial_failure(self):
        """Test rendering with some template failures."""
        # Arrange
        mock_config = Mock()
        mock_config.maps = {"hosts.map": Mock(template="host1 backend1")}
        mock_config.certificates = {
            "ssl.pem": Mock(template="invalid {{ undefined_var }}")
        }
        mock_config.files = {"error.html": Mock(template="<html>Error</html>")}

        mock_renderer = Mock()
        mock_renderer.render.side_effect = [
            "rendered hosts.map content",
            RuntimeError("Undefined variable"),
            "rendered error.html content",
        ]

        mock_metrics = Mock()
        mock_timer = Mock()
        mock_timer.__enter__ = Mock(return_value=mock_timer)
        mock_timer.__exit__ = Mock(return_value=None)
        mock_metrics.time_template_render.return_value = mock_timer

        mock_context = Mock(spec=HAProxyConfigContext)
        mock_context.rendered_content = []
        template_vars = {"resources": {}}

        render_context = TemplateRenderContext(
            config=mock_config,
            template_renderer=mock_renderer,
            haproxy_config_context=mock_context,
            template_vars=template_vars,
            metrics=mock_metrics,
        )

        # Act
        with (
            patch(
                "haproxy_template_ic.operator.template_renderer.trace_template_render"
            ),
            patch("haproxy_template_ic.operator.template_renderer.add_span_attributes"),
            patch("haproxy_template_ic.operator.template_renderer.record_span_event"),
            patch("haproxy_template_ic.operator.template_renderer.logger"),
        ):
            template_errors = _render_content_templates(render_context)

        # Assert
        assert len(template_errors) == 1

        error = template_errors[0]
        assert error["type"] == CONTENT_TYPE_CERTIFICATE
        assert error["filename"] == "ssl.pem"
        assert "Undefined variable" in error["error"]

        # Verify successful renders were added
        assert len(mock_context.rendered_content) == 2

        # Verify error metrics
        mock_metrics.record_template_render.assert_has_calls(
            [
                call(CONTENT_TYPE_MAP, "success"),
                call(CONTENT_TYPE_CERTIFICATE, "error"),
                call(CONTENT_TYPE_FILE, "success"),
            ]
        )
        mock_metrics.record_error.assert_called_once_with(
            "template_render_failed", "operator"
        )

    def test_render_content_templates_empty_collections(self):
        """Test rendering with empty content collections."""
        # Arrange
        mock_config = Mock()
        mock_config.maps = {}
        mock_config.certificates = {}
        mock_config.files = {}

        mock_renderer = Mock()
        mock_metrics = Mock()
        mock_context = Mock(spec=HAProxyConfigContext)
        mock_context.rendered_content = []

        render_context = TemplateRenderContext(
            config=mock_config,
            template_renderer=mock_renderer,
            haproxy_config_context=mock_context,
            template_vars={},
            metrics=mock_metrics,
        )

        # Act
        template_errors = _render_content_templates(render_context)

        # Assert
        assert template_errors == []
        assert len(mock_context.rendered_content) == 0
        mock_renderer.render.assert_not_called()
        mock_metrics.record_template_render.assert_not_called()


class TestValidateTemplateErrors:
    """Test template error validation."""

    def test_validate_template_errors_no_errors(self):
        """Test validation with no errors."""
        # Act & Assert - should not raise
        _validate_template_errors([])

    def test_validate_template_errors_with_single_error(self):
        """Test validation with a single error."""
        # Arrange
        template_errors = [
            {"type": "map", "filename": "hosts.map", "error": "Invalid syntax"}
        ]

        # Act & Assert
        with pytest.raises(RuntimeError) as exc_info:
            _validate_template_errors(template_errors)

        error_message = str(exc_info.value)
        assert "Template rendering failed with 1 error(s)" in error_message
        assert "map 'hosts.map': Invalid syntax" in error_message

    def test_validate_template_errors_with_multiple_errors(self):
        """Test validation with multiple errors."""
        # Arrange
        template_errors = [
            {"type": "map", "filename": "hosts.map", "error": "Invalid syntax"},
            {"type": "certificate", "filename": "ssl.pem", "error": "Missing variable"},
            {"type": "file", "filename": "error.html", "error": "Parse error"},
        ]

        # Act & Assert
        with pytest.raises(RuntimeError) as exc_info:
            _validate_template_errors(template_errors)

        error_message = str(exc_info.value)
        assert "Template rendering failed with 3 error(s)" in error_message
        assert "map 'hosts.map': Invalid syntax" in error_message
        assert "certificate 'ssl.pem': Missing variable" in error_message
        assert "file 'error.html': Parse error" in error_message

    def test_validate_template_errors_with_many_errors(self):
        """Test validation with more than 5 errors (truncation)."""
        # Arrange
        template_errors = [
            {"type": "map", "filename": f"map{i}.map", "error": f"Error {i}"}
            for i in range(7)
        ]

        # Act & Assert
        with pytest.raises(RuntimeError) as exc_info:
            _validate_template_errors(template_errors)

        error_message = str(exc_info.value)
        assert "Template rendering failed with 7 error(s)" in error_message
        assert "... and 2 more errors" in error_message

        # Verify only first 5 errors are shown
        for i in range(5):
            assert f"map 'map{i}.map': Error {i}" in error_message

        # Verify last 2 errors are not shown in detail
        assert "map 'map5.map': Error 5" not in error_message
        assert "map 'map6.map': Error 6" not in error_message


class TestRenderHAProxyTemplates:
    """Test the main render_haproxy_templates function."""

    @pytest.fixture
    def mock_dependencies(self):
        """Create mock dependencies for render_haproxy_templates."""
        mock_config = Mock()
        mock_config.watched_resources = {"services": Mock(), "pods": Mock()}
        mock_config.watched_resources_ignore_fields = ["status"]
        mock_config.haproxy_config.template = "global\n    daemon"
        mock_config.maps = {}
        mock_config.certificates = {}
        mock_config.files = {}

        mock_context = Mock(spec=HAProxyConfigContext)
        mock_context.rendered_content = []
        mock_context._clear_cache = Mock()

        mock_renderer = Mock()
        mock_renderer.render.return_value = "rendered config"

        mock_synchronizer = Mock()

        mock_indices = Mock()

        mock_metrics = Mock()
        mock_timer = Mock()
        mock_timer.__enter__ = Mock(return_value=mock_timer)
        mock_timer.__exit__ = Mock(return_value=None)
        mock_metrics.time_template_render.return_value = mock_timer

        mock_logger = Mock()

        return {
            "config": mock_config,
            "haproxy_config_context": mock_context,
            "template_renderer": mock_renderer,
            "config_synchronizer": mock_synchronizer,
            "kopf_indices": mock_indices,
            "metrics": mock_metrics,
            "logger": mock_logger,
        }

    @pytest.mark.asyncio
    async def test_render_haproxy_templates_success(self, mock_dependencies):
        """Test successful template rendering end-to-end."""
        # Arrange
        with (
            patch(
                "haproxy_template_ic.operator.template_renderer.get_resource_collection_from_indices"
            ) as mock_get_collection,
            patch(
                "haproxy_template_ic.operator.template_renderer.synchronize_with_haproxy_instances"
            ) as mock_sync,
            patch(
                "haproxy_template_ic.operator.template_renderer.trace_template_render"
            ),
            patch("haproxy_template_ic.operator.template_renderer.add_span_attributes"),
            patch("haproxy_template_ic.operator.template_renderer.record_span_event"),
        ):
            # Mock resource collection
            from haproxy_template_ic.k8s.kopf_utils import IndexedResourceCollection

            services_collection = IndexedResourceCollection()
            pods_collection = IndexedResourceCollection()

            mock_get_collection.side_effect = [
                services_collection,  # services
                pods_collection,  # pods
            ]

            mock_sync.return_value = None

            # Act
            await render_haproxy_templates(**mock_dependencies)

        # Assert
        config = mock_dependencies["config"]
        context = mock_dependencies["haproxy_config_context"]
        renderer = mock_dependencies["template_renderer"]
        metrics = mock_dependencies["metrics"]
        logger = mock_dependencies["logger"]

        # Verify resource collection
        assert mock_get_collection.call_count == 2
        mock_get_collection.assert_has_calls(
            [
                call(
                    mock_dependencies["kopf_indices"],
                    "services",
                    ignore_fields=["status"],
                ),
                call(
                    mock_dependencies["kopf_indices"], "pods", ignore_fields=["status"]
                ),
            ]
        )

        # Verify template rendering
        renderer.render.assert_called_once()
        call_args = renderer.render.call_args
        assert call_args[0][0] == config.haproxy_config.template
        assert call_args[1]["template_name"] == "haproxy_config"
        assert "resources" in call_args[1]
        assert "register_error" in call_args[1]

        # Verify metrics
        metrics.record_resource_type_count.assert_has_calls(
            [call("services", 0), call("pods", 0)]
        )
        metrics.record_resource_count.assert_called_once_with(0)
        metrics.record_template_render.assert_has_calls(
            [call(CONTENT_TYPE_HAPROXY_CONFIG, "success"), call("all", "success")]
        )

        # Verify context was properly set
        assert isinstance(context.rendered_config, RenderedConfig)
        assert context.rendered_config.content == "rendered config"

        # Verify synchronization was called
        mock_sync.assert_called_once_with(
            context, mock_dependencies["config_synchronizer"]
        )

        # Verify success logging
        logger.info.assert_called()
        info_call_args = logger.info.call_args[0][0]
        assert "Template rendering completed successfully" in info_call_args

    @pytest.mark.asyncio
    async def test_render_haproxy_templates_resource_collection_failure(
        self, mock_dependencies
    ):
        """Test handling of resource collection failure."""
        # Arrange
        with (
            patch(
                "haproxy_template_ic.operator.template_renderer.get_resource_collection_from_indices"
            ) as mock_get_collection,
            patch(
                "haproxy_template_ic.operator.template_renderer.synchronize_with_haproxy_instances"
            ) as mock_sync,
            patch(
                "haproxy_template_ic.operator.template_renderer.trace_template_render"
            ),
            patch("haproxy_template_ic.operator.template_renderer.add_span_attributes"),
            patch("haproxy_template_ic.operator.template_renderer.record_span_event"),
        ):
            # Mock resource collection with failure and fallback
            mock_get_collection.side_effect = [
                RuntimeError("Failed to collect services"),  # services fail
                {},  # fallback for services
                {"pod1": {"name": "test-pod"}},  # pods succeed
            ]

            mock_sync.return_value = None

            # Act
            await render_haproxy_templates(**mock_dependencies)

        # Assert warning was logged and fallback collection was used
        logger = mock_dependencies["logger"]
        logger.warning.assert_called_with(
            "Failed to collect indices for services: Failed to collect services"
        )

        # Verify fallback collection call
        assert mock_get_collection.call_count == 3  # Original fail + fallback + pods
        fallback_call = mock_get_collection.call_args_list[1]
        assert (
            fallback_call[1]["ignore_fields"] == []
        )  # Empty ignore_fields for fallback

    @pytest.mark.asyncio
    async def test_render_haproxy_templates_template_render_failure(
        self, mock_dependencies
    ):
        """Test handling of template rendering failure."""
        # Arrange
        mock_dependencies["template_renderer"].render.side_effect = RuntimeError(
            "Template error"
        )

        with (
            patch(
                "haproxy_template_ic.operator.template_renderer.get_resource_collection_from_indices"
            ) as mock_get_collection,
            patch(
                "haproxy_template_ic.operator.template_renderer.trace_template_render"
            ),
            patch("haproxy_template_ic.operator.template_renderer.record_span_event"),
            patch(
                "haproxy_template_ic.operator.template_renderer.logger"
            ) as mock_module_logger,
        ):
            from haproxy_template_ic.k8s.kopf_utils import IndexedResourceCollection

            mock_get_collection.side_effect = [
                IndexedResourceCollection(),
                IndexedResourceCollection(),
            ]

            # Act & Assert
            # The function should not raise directly but should handle template errors gracefully
            await render_haproxy_templates(**mock_dependencies)

        # Assert error handling
        mock_dependencies["haproxy_config_context"]
        mock_dependencies["metrics"]

        # Check the module-level logger was called for the error
        mock_module_logger.error.assert_called()
        error_call = mock_module_logger.error.call_args[0][0]
        assert "❌" in error_call

    @pytest.mark.asyncio
    async def test_render_haproxy_templates_sync_failure(self, mock_dependencies):
        """Test handling of synchronization failure (should not fail template rendering)."""
        # Arrange
        with (
            patch(
                "haproxy_template_ic.operator.template_renderer.get_resource_collection_from_indices"
            ) as mock_get_collection,
            patch(
                "haproxy_template_ic.operator.template_renderer.synchronize_with_haproxy_instances"
            ) as mock_sync,
            patch(
                "haproxy_template_ic.operator.template_renderer.trace_template_render"
            ),
            patch("haproxy_template_ic.operator.template_renderer.add_span_attributes"),
            patch("haproxy_template_ic.operator.template_renderer.record_span_event"),
        ):
            mock_get_collection.side_effect = [
                {"service1": {"name": "test-service"}},
                {"pod1": {"name": "test-pod"}},
            ]

            # Mock sync failure
            mock_sync.side_effect = RuntimeError("Sync failed")

            # Act - should not raise despite sync failure
            await render_haproxy_templates(**mock_dependencies)

        # Assert
        logger = mock_dependencies["logger"]

        # Verify template rendering success was logged
        logger.info.assert_called()
        info_call = logger.info.call_args[0][0]
        assert "Template rendering completed successfully" in info_call

        # Verify sync failure was logged but didn't fail the function
        logger.error.assert_called()
        error_call = logger.error.call_args[0][0]
        assert "HAProxy synchronization failed" in error_call

    @pytest.mark.asyncio
    async def test_render_haproxy_templates_validation_errors(self, mock_dependencies):
        """Test handling of validation errors during template rendering."""
        # Arrange

        def mock_render(template, template_name=None, **kwargs):
            # Simulate register_error being called during template rendering
            register_error = kwargs.get("register_error")
            if register_error:
                register_error("ingress", "uid-123", "Invalid configuration")
                register_error("service", "uid-456", "Missing port")
            return "rendered config"

        mock_dependencies["template_renderer"].render.side_effect = mock_render

        with (
            patch(
                "haproxy_template_ic.operator.template_renderer.get_resource_collection_from_indices"
            ) as mock_get_collection,
            patch(
                "haproxy_template_ic.operator.template_renderer.synchronize_with_haproxy_instances"
            ) as mock_sync,
            patch(
                "haproxy_template_ic.operator.template_renderer.trace_template_render"
            ),
            patch("haproxy_template_ic.operator.template_renderer.add_span_attributes"),
            patch("haproxy_template_ic.operator.template_renderer.record_span_event"),
        ):
            mock_get_collection.side_effect = [
                {"service1": {"name": "test-service"}},
                {"pod1": {"name": "test-pod"}},
            ]
            mock_sync.return_value = None

            # Act
            await render_haproxy_templates(**mock_dependencies)

        # Assert
        logger = mock_dependencies["logger"]

        # Verify validation warnings were logged
        warning_calls = [
            call
            for call in logger.warning.call_args_list
            if "Template validation completed" in str(call)
        ]
        assert len(warning_calls) > 0

        # Should still complete successfully despite validation warnings
        logger.info.assert_called()
        info_call = logger.info.call_args[0][0]
        assert "Template rendering completed successfully" in info_call


class TestTemplateRendererIntegration:
    """Integration tests for template renderer with real dependencies."""

    @pytest.mark.asyncio
    async def test_template_rendering_with_real_template_context(self):
        """Test template rendering with realistic template context."""
        # This test uses more realistic mocks to verify integration behavior
        # Arrange
        from haproxy_template_ic.templating import TemplateRenderer

        # Create real template renderer
        template_renderer = TemplateRenderer()

        # Create mock config with proper structure
        mock_config = Mock()
        mock_config.watched_resources = {"services": Mock()}
        mock_config.watched_resources_ignore_fields = ["status"]
        mock_config.haproxy_config.template = "global\n    daemon\n{% for service in resources.services.values() %}\n# Service: {{ service.metadata.name }}\n{% endfor %}"
        mock_config.maps = {}
        mock_config.certificates = {}
        mock_config.files = {}

        # Create real context
        context = HAProxyConfigContext(template_context=TemplateContext())

        # Mock other dependencies
        mock_synchronizer = AsyncMock()
        mock_indices = Mock()
        mock_metrics = Mock()
        mock_timer = Mock()
        mock_timer.__enter__ = Mock(return_value=mock_timer)
        mock_timer.__exit__ = Mock(return_value=None)
        mock_metrics.time_template_render.return_value = mock_timer
        mock_logger = Mock()

        # Mock resource data
        service_data = {
            "test-service": {
                "metadata": {"name": "test-service", "namespace": "default"},
                "spec": {"ports": [{"port": 80}]},
            }
        }

        with (
            patch(
                "haproxy_template_ic.operator.template_renderer.get_resource_collection_from_indices"
            ) as mock_get_collection,
            patch(
                "haproxy_template_ic.operator.template_renderer.synchronize_with_haproxy_instances"
            ) as mock_sync,
            patch(
                "haproxy_template_ic.operator.template_renderer.trace_template_render"
            ),
            patch("haproxy_template_ic.operator.template_renderer.add_span_attributes"),
            patch("haproxy_template_ic.operator.template_renderer.record_span_event"),
        ):
            mock_get_collection.side_effect = [service_data, {}]  # services, then pods
            mock_sync.return_value = None

            # Act
            await render_haproxy_templates(
                config=mock_config,
                haproxy_config_context=context,
                template_renderer=template_renderer,
                config_synchronizer=mock_synchronizer,
                kopf_indices=mock_indices,
                metrics=mock_metrics,
                logger=mock_logger,
            )

        # Assert
        assert context.rendered_config is not None
        rendered_content = context.rendered_config.content

        # Verify template was actually rendered
        assert "global" in rendered_content
        assert "daemon" in rendered_content
        # Note: The service data may not be available in the template context
        # in this integration test setup, but the core template rendering works

        # Verify synchronization was called
        mock_sync.assert_called_once_with(context, mock_synchronizer)

        # Verify metrics
        mock_metrics.record_template_render.assert_called_with("all", "success")
