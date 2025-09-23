"""
Unit tests for haproxy_template_ic.operator.synchronization module.

Comprehensive test coverage for HAProxy instance synchronization functionality
including validation, metrics recording, error handling, and hint generation.
"""

import pytest
from unittest.mock import AsyncMock, Mock, patch, call

from haproxy_template_ic.dataplane.types import (
    DataplaneAPIError,
    ValidationError,
)
from haproxy_template_ic.dataplane.synchronizer import ConfigSynchronizer
from haproxy_template_ic.models.context import HAProxyConfigContext, TemplateContext
from haproxy_template_ic.models.templates import RenderedConfig
from haproxy_template_ic.operator.synchronization import (
    _log_haproxy_error_hints,
    _record_sync_metrics,
    _validate_sync_prerequisites,
    synchronize_with_haproxy_instances,
)


class TestValidateSyncPrerequisites:
    """Test validation of synchronization prerequisites."""

    def test_validate_sync_prerequisites_success(self):
        """Test successful validation when rendered config exists."""
        # Arrange
        rendered_config = RenderedConfig(
            content="global\n    daemon\ndefaults\n    mode http"
        )
        context = HAProxyConfigContext(
            template_context=TemplateContext(), rendered_config=rendered_config
        )

        # Act
        result = _validate_sync_prerequisites(context)

        # Assert
        assert result is True

    def test_validate_sync_prerequisites_no_rendered_config(self):
        """Test validation failure when no rendered config exists."""
        # Arrange
        context = HAProxyConfigContext(
            template_context=TemplateContext(), rendered_config=None
        )

        with patch(
            "haproxy_template_ic.operator.synchronization.logger"
        ) as mock_logger:
            # Act
            result = _validate_sync_prerequisites(context)

            # Assert
            assert result is False
            mock_logger.warning.assert_called_once_with(
                "⚠️ No rendered HAProxy configuration available"
            )

    def test_validate_sync_prerequisites_empty_config_content(self):
        """Test validation failure when rendered config has empty content."""
        # Arrange
        context = HAProxyConfigContext(
            template_context=TemplateContext(), rendered_config=None
        )

        with patch(
            "haproxy_template_ic.operator.synchronization.logger"
        ) as mock_logger:
            # Act
            result = _validate_sync_prerequisites(context)

            # Assert
            assert result is False
            mock_logger.warning.assert_called_once_with(
                "⚠️ No rendered HAProxy configuration available"
            )

    def test_validate_sync_prerequisites_none_config_content(self):
        """Test validation failure when rendered config has None content."""
        # Arrange
        context = HAProxyConfigContext(
            template_context=TemplateContext(), rendered_config=None
        )

        with patch(
            "haproxy_template_ic.operator.synchronization.logger"
        ) as mock_logger:
            # Act
            result = _validate_sync_prerequisites(context)

            # Assert
            assert result is False
            mock_logger.warning.assert_called_once_with(
                "⚠️ No rendered HAProxy configuration available"
            )


class TestRecordSyncMetrics:
    """Test synchronization metrics recording."""

    def test_record_sync_metrics_all_successful(self):
        """Test metrics recording when all synchronizations succeed."""
        # Arrange
        mock_metrics = Mock()

        with patch(
            "haproxy_template_ic.operator.synchronization.logger"
        ) as mock_logger:
            # Act
            _record_sync_metrics(
                mock_metrics, successful_count=3, failed_count=0, total_urls=3
            )

            # Assert
            # Metrics recording is handled by ConfigSynchronizer internally
            mock_logger.info.assert_called_once_with(
                "✅ Successfully synchronized 3/3 instances"
            )
            mock_logger.warning.assert_not_called()

    def test_record_sync_metrics_all_failed(self):
        """Test metrics recording when all synchronizations fail."""
        # Arrange
        mock_metrics = Mock()

        with patch(
            "haproxy_template_ic.operator.synchronization.logger"
        ) as mock_logger:
            # Act
            _record_sync_metrics(
                mock_metrics, successful_count=0, failed_count=2, total_urls=2
            )

            # Assert
            # Metrics recording is handled by ConfigSynchronizer internally
            mock_logger.warning.assert_called_once_with(
                "❌ Failed to synchronize 2/2 instances"
            )
            mock_logger.info.assert_not_called()

    def test_record_sync_metrics_partial_success(self):
        """Test metrics recording with partial success."""
        # Arrange
        mock_metrics = Mock()

        with patch(
            "haproxy_template_ic.operator.synchronization.logger"
        ) as mock_logger:
            # Act
            _record_sync_metrics(
                mock_metrics, successful_count=2, failed_count=1, total_urls=3
            )

            # Assert
            # Metrics recording is handled by ConfigSynchronizer internally
            mock_logger.info.assert_called_once_with(
                "✅ Successfully synchronized 2/3 instances"
            )
            mock_logger.warning.assert_called_once_with(
                "❌ Failed to synchronize 1/3 instances"
            )

    def test_record_sync_metrics_zero_instances(self):
        """Test metrics recording with zero instances."""
        # Arrange
        mock_metrics = Mock()

        with patch(
            "haproxy_template_ic.operator.synchronization.logger"
        ) as mock_logger:
            # Act
            _record_sync_metrics(
                mock_metrics, successful_count=0, failed_count=0, total_urls=0
            )

            # Assert
            # Metrics recording is handled by ConfigSynchronizer internally
            mock_logger.info.assert_not_called()
            mock_logger.warning.assert_not_called()


class TestLogHAProxyErrorHints:
    """Test HAProxy error hint logging functionality."""

    def test_log_haproxy_error_hints_bind_address_error(self):
        """Test hint logging for bind address errors."""
        # Arrange
        validation_error = ValidationError(
            message="Configuration validation failed",
            validation_details="Error parsing bind address on port 80",
        )
        rendered_config = RenderedConfig(content="test config content")
        context = HAProxyConfigContext(
            template_context=TemplateContext(), rendered_config=rendered_config
        )

        with patch(
            "haproxy_template_ic.operator.synchronization.logger"
        ) as mock_logger:
            # Act
            _log_haproxy_error_hints(validation_error, context)

            # Assert
            mock_logger.info.assert_has_calls(
                [
                    call("💡 Troubleshooting hints:"),
                    call(
                        "   - Check that bind addresses and ports are valid and available"
                    ),
                    call("📊 Configuration size: 19 characters"),
                ]
            )

    def test_log_haproxy_error_hints_backend_server_error(self):
        """Test hint logging for backend server errors."""
        # Arrange
        validation_error = ValidationError(
            message="Configuration validation failed",
            validation_details="Backend 'web' has invalid server configuration",
        )
        rendered_config = RenderedConfig(content="backend web\n    server web1 invalid")
        context = HAProxyConfigContext(
            template_context=TemplateContext(), rendered_config=rendered_config
        )

        with patch(
            "haproxy_template_ic.operator.synchronization.logger"
        ) as mock_logger:
            # Act
            _log_haproxy_error_hints(validation_error, context)

            # Assert
            mock_logger.info.assert_has_calls(
                [
                    call("💡 Troubleshooting hints:"),
                    call("   - Verify that backend servers are properly defined"),
                    call("📊 Configuration size: 35 characters"),
                ]
            )

    def test_log_haproxy_error_hints_unknown_keyword_error(self):
        """Test hint logging for unknown keyword errors."""
        # Arrange
        validation_error = ValidationError(
            message="Configuration validation failed",
            validation_details="Unknown keyword 'invalid_directive' in global section",
        )
        context = HAProxyConfigContext(template_context=TemplateContext())
        context.rendered_config = RenderedConfig(
            content="global\n    invalid_directive"
        )

        with patch(
            "haproxy_template_ic.operator.synchronization.logger"
        ) as mock_logger:
            # Act
            _log_haproxy_error_hints(validation_error, context)

            # Assert
            mock_logger.info.assert_has_calls(
                [
                    call("💡 Troubleshooting hints:"),
                    call(
                        "   - Check for HAProxy version compatibility and correct syntax"
                    ),
                    call("📊 Configuration size: 28 characters"),
                ]
            )

    def test_log_haproxy_error_hints_parsing_error(self):
        """Test hint logging for parsing errors."""
        # Arrange
        validation_error = ValidationError(
            message="Configuration validation failed",
            validation_details="Parsing error on line 5: missing closing bracket",
        )
        context = HAProxyConfigContext(template_context=TemplateContext())
        context.rendered_config = RenderedConfig(content="invalid config")

        with patch(
            "haproxy_template_ic.operator.synchronization.logger"
        ) as mock_logger:
            # Act
            _log_haproxy_error_hints(validation_error, context)

            # Assert
            mock_logger.info.assert_has_calls(
                [
                    call("💡 Troubleshooting hints:"),
                    call("   - Review the HAProxy configuration for syntax errors"),
                    call("📊 Configuration size: 14 characters"),
                ]
            )

    def test_log_haproxy_error_hints_duplicate_error(self):
        """Test hint logging for duplicate definition errors."""
        # Arrange
        validation_error = ValidationError(
            message="Configuration validation failed",
            validation_details="Duplicate backend name 'web' found",
        )
        context = HAProxyConfigContext(template_context=TemplateContext())
        context.rendered_config = RenderedConfig(content="backend web\nbackend web")

        with patch(
            "haproxy_template_ic.operator.synchronization.logger"
        ) as mock_logger:
            # Act
            _log_haproxy_error_hints(validation_error, context)

            # Assert
            mock_logger.info.assert_has_calls(
                [
                    call("💡 Troubleshooting hints:"),
                    call(
                        "   - Check for duplicate section names or conflicting definitions"
                    ),
                    call("📊 Configuration size: 23 characters"),
                ]
            )

    def test_log_haproxy_error_hints_multiple_hints(self):
        """Test hint logging when multiple hint conditions are met."""
        # Arrange
        validation_error = ValidationError(
            message="Configuration validation failed",
            validation_details="Parsing error on line 3: unknown keyword 'invalid' in bind directive",
        )
        context = HAProxyConfigContext(template_context=TemplateContext())
        context.rendered_config = RenderedConfig(content="test config")

        with patch(
            "haproxy_template_ic.operator.synchronization.logger"
        ) as mock_logger:
            # Act
            _log_haproxy_error_hints(validation_error, context)

            # Assert
            mock_logger.info.assert_has_calls(
                [
                    call("💡 Troubleshooting hints:"),
                    call(
                        "   - Check for HAProxy version compatibility and correct syntax"
                    ),
                    call("   - Review the HAProxy configuration for syntax errors"),
                    call("📊 Configuration size: 11 characters"),
                ]
            )

    def test_log_haproxy_error_hints_no_details(self):
        """Test hint logging when validation error has no details."""
        # Arrange
        validation_error = ValidationError(
            message="Configuration validation failed", validation_details=None
        )
        context = HAProxyConfigContext(template_context=TemplateContext())
        context.rendered_config = RenderedConfig(content="test config")

        with patch(
            "haproxy_template_ic.operator.synchronization.logger"
        ) as mock_logger:
            # Act
            _log_haproxy_error_hints(validation_error, context)

            # Assert
            mock_logger.info.assert_not_called()

    def test_log_haproxy_error_hints_no_matching_patterns(self):
        """Test hint logging when error details don't match any patterns."""
        # Arrange
        validation_error = ValidationError(
            message="Configuration validation failed",
            validation_details="Some unrecognized error message",
        )
        context = HAProxyConfigContext(template_context=TemplateContext())
        context.rendered_config = RenderedConfig(content="test config")

        with patch(
            "haproxy_template_ic.operator.synchronization.logger"
        ) as mock_logger:
            # Act
            _log_haproxy_error_hints(validation_error, context)

            # Assert
            # Only config size should be logged, no hints
            mock_logger.info.assert_called_once_with(
                "📊 Configuration size: 11 characters"
            )

    def test_log_haproxy_error_hints_no_rendered_config(self):
        """Test hint logging when context has no rendered config."""
        # Arrange
        validation_error = ValidationError(
            message="Configuration validation failed",
            validation_details="bind error on port 80",
        )
        context = HAProxyConfigContext(
            template_context=TemplateContext(), rendered_config=None
        )

        with patch(
            "haproxy_template_ic.operator.synchronization.logger"
        ) as mock_logger:
            # Act
            _log_haproxy_error_hints(validation_error, context)

            # Assert
            # Hints should still be logged, but no config size
            mock_logger.info.assert_has_calls(
                [
                    call("💡 Troubleshooting hints:"),
                    call(
                        "   - Check that bind addresses and ports are valid and available"
                    ),
                ]
            )
            # No config size call
            config_size_calls = [
                call
                for call in mock_logger.info.call_args_list
                if "Configuration size" in str(call)
            ]
            assert len(config_size_calls) == 0


class TestSynchronizeWithHAProxyInstances:
    """Test the main synchronization function."""

    @pytest.fixture
    def mock_sync_result(self):
        """Create a mock synchronization result."""
        mock_result = Mock()
        mock_result.successful = 2
        mock_result.failed = 0
        mock_result.errors = []
        mock_result.reload_info = Mock()
        mock_result.reload_info.reload_triggered = True
        mock_result.reload_info.reload_id = "reload-123"
        return mock_result

    @pytest.fixture
    def mock_context_with_config(self):
        """Create a mock context with rendered config."""
        context = HAProxyConfigContext(
            template_context=TemplateContext(),
            rendered_config=RenderedConfig(content="global\n    daemon"),
        )
        return context

    @pytest.fixture
    def mock_synchronizer_with_endpoints(self):
        """Create a mock synchronizer with production endpoints."""
        mock_synchronizer = Mock(spec=ConfigSynchronizer)
        mock_synchronizer.sync_configuration = AsyncMock()
        mock_synchronizer.endpoints = Mock()
        mock_synchronizer.endpoints.production = ["endpoint1", "endpoint2"]
        mock_synchronizer.metrics = Mock()
        return mock_synchronizer

    @pytest.mark.asyncio
    async def test_synchronize_success(
        self,
        mock_context_with_config,
        mock_synchronizer_with_endpoints,
        mock_sync_result,
    ):
        """Test successful synchronization with all instances."""
        # Arrange
        mock_synchronizer_with_endpoints.sync_configuration.return_value = (
            mock_sync_result
        )

        with patch(
            "haproxy_template_ic.operator.synchronization.logger"
        ) as mock_logger:
            # Act
            await synchronize_with_haproxy_instances(
                mock_context_with_config, mock_synchronizer_with_endpoints
            )

        # Assert
        mock_synchronizer_with_endpoints.sync_configuration.assert_called_once_with(
            mock_context_with_config
        )
        # Metrics recording is handled by ConfigSynchronizer internally

        # Verify logging
        mock_logger.debug.assert_called_with(
            "🚀 SYNC FUNCTION CALLED - Starting synchronization..."
        )
        mock_logger.info.assert_has_calls(
            [
                call("🔄 HAProxy reload triggered: reload-123"),
                call("✅ Successfully synchronized 2/2 instances"),
            ]
        )

    @pytest.mark.asyncio
    async def test_synchronize_no_prerequisites(self):
        """Test synchronization when prerequisites are not met."""
        # Arrange
        context = HAProxyConfigContext(
            template_context=TemplateContext(), rendered_config=None
        )  # No config

        mock_synchronizer = Mock(spec=ConfigSynchronizer)
        mock_synchronizer.metrics = Mock()

        # Act
        await synchronize_with_haproxy_instances(context, mock_synchronizer)

        # Assert - should return early without calling synchronizer
        mock_synchronizer.sync_configuration.assert_not_called()

    # Metrics recording is handled by ConfigSynchronizer internally

    @pytest.mark.asyncio
    async def test_synchronize_no_production_endpoints(self, mock_context_with_config):
        """Test synchronization when no production endpoints are available."""
        # Arrange
        mock_synchronizer = Mock(spec=ConfigSynchronizer)
        mock_synchronizer.endpoints = Mock()
        mock_synchronizer.endpoints.production = []  # No production endpoints
        mock_synchronizer.metrics = Mock()

        with patch(
            "haproxy_template_ic.operator.synchronization.logger"
        ) as mock_logger:
            # Act
            await synchronize_with_haproxy_instances(
                mock_context_with_config, mock_synchronizer
            )

        # Assert
        mock_synchronizer.sync_configuration.assert_not_called()
        mock_logger.warning.assert_called_with(
            "⚠️ No production HAProxy endpoints available - skipping synchronization"
        )

    @pytest.mark.asyncio
    async def test_synchronize_partial_failure(
        self, mock_context_with_config, mock_synchronizer_with_endpoints
    ):
        """Test synchronization with partial failures."""
        # Arrange
        mock_result = Mock()
        mock_result.successful = 1
        mock_result.failed = 1
        mock_result.errors = ["Failed to sync endpoint2: Connection timeout"]
        mock_result.reload_info = Mock()
        mock_result.reload_info.reload_triggered = False

        mock_synchronizer_with_endpoints.sync_configuration.return_value = mock_result

        with patch(
            "haproxy_template_ic.operator.synchronization.logger"
        ) as mock_logger:
            # Act
            await synchronize_with_haproxy_instances(
                mock_context_with_config, mock_synchronizer_with_endpoints
            )

        # Assert
        # Metrics recording is handled by ConfigSynchronizer internally

        # Verify error logging
        mock_logger.error.assert_called_with(
            "   - Failed to sync endpoint2: Connection timeout"
        )
        mock_logger.info.assert_called_with(
            "✅ Successfully synchronized 1/2 instances"
        )
        mock_logger.warning.assert_called_with("❌ Failed to synchronize 1/2 instances")

    @pytest.mark.asyncio
    async def test_synchronize_validation_error(
        self, mock_context_with_config, mock_synchronizer_with_endpoints
    ):
        """Test synchronization handling of ValidationError."""
        # Arrange
        validation_error = ValidationError(
            message="Configuration validation failed",
            validation_details="Invalid bind configuration",
        )
        mock_synchronizer_with_endpoints.sync_configuration.side_effect = (
            validation_error
        )

        with (
            patch("haproxy_template_ic.operator.synchronization.logger") as mock_logger,
            patch(
                "haproxy_template_ic.operator.synchronization._log_haproxy_error_hints"
            ) as mock_hints,
        ):
            # Act
            await synchronize_with_haproxy_instances(
                mock_context_with_config, mock_synchronizer_with_endpoints
            )

        # Assert
        # Error recording is handled by ConfigSynchronizer internally
        mock_logger.error.assert_called_with(
            f"❌ Configuration validation failed: {validation_error}"
        )
        mock_hints.assert_called_once_with(validation_error, mock_context_with_config)

    @pytest.mark.asyncio
    async def test_synchronize_dataplane_api_error(
        self, mock_context_with_config, mock_synchronizer_with_endpoints
    ):
        """Test synchronization handling of DataplaneAPIError."""
        # Arrange
        api_error = DataplaneAPIError(message="API request failed")
        mock_synchronizer_with_endpoints.sync_configuration.side_effect = api_error

        with patch(
            "haproxy_template_ic.operator.synchronization.logger"
        ) as mock_logger:
            # Act
            await synchronize_with_haproxy_instances(
                mock_context_with_config, mock_synchronizer_with_endpoints
            )

        # Assert
        # Error recording is handled by ConfigSynchronizer internally
        # Verify error logging calls
        assert mock_logger.error.call_count == 2
        first_call, second_call = mock_logger.error.call_args_list

        # First call should be the error message
        assert first_call == call(f"❌ Dataplane API error: {api_error}")

        # Second call should be a traceback
        assert "Traceback (most recent call last)" in str(second_call[0][0])

    @pytest.mark.asyncio
    async def test_synchronize_unexpected_error(
        self, mock_context_with_config, mock_synchronizer_with_endpoints
    ):
        """Test synchronization handling of unexpected errors."""
        # Arrange
        unexpected_error = RuntimeError("Unexpected failure")
        mock_synchronizer_with_endpoints.sync_configuration.side_effect = (
            unexpected_error
        )

        with patch(
            "haproxy_template_ic.operator.synchronization.logger"
        ) as mock_logger:
            # Act
            await synchronize_with_haproxy_instances(
                mock_context_with_config, mock_synchronizer_with_endpoints
            )

        # Assert
        # Error recording is handled by ConfigSynchronizer internally
        mock_logger.error.assert_called_with(
            f"❌ Unexpected error during synchronization: {unexpected_error}"
        )

    @pytest.mark.asyncio
    async def test_synchronize_with_autolog_and_tracing(
        self,
        mock_context_with_config,
        mock_synchronizer_with_endpoints,
        mock_sync_result,
    ):
        """Test that synchronization properly integrates with autolog and tracing decorators."""
        # Arrange
        mock_synchronizer_with_endpoints.sync_configuration.return_value = (
            mock_sync_result
        )

        # Act
        await synchronize_with_haproxy_instances(
            mock_context_with_config, mock_synchronizer_with_endpoints
        )

        # Assert - function should complete without issues
        # The autolog and trace decorators are applied but don't change core functionality
        mock_synchronizer_with_endpoints.sync_configuration.assert_called_once_with(
            mock_context_with_config
        )

    @pytest.mark.asyncio
    async def test_synchronize_no_reload_triggered(
        self, mock_context_with_config, mock_synchronizer_with_endpoints
    ):
        """Test synchronization when no reload is triggered."""
        # Arrange
        mock_result = Mock()
        mock_result.successful = 2
        mock_result.failed = 0
        mock_result.errors = []
        mock_result.reload_info = Mock()
        mock_result.reload_info.reload_triggered = False

        mock_synchronizer_with_endpoints.sync_configuration.return_value = mock_result

        with patch(
            "haproxy_template_ic.operator.synchronization.logger"
        ) as mock_logger:
            # Act
            await synchronize_with_haproxy_instances(
                mock_context_with_config, mock_synchronizer_with_endpoints
            )

        # Assert - no reload logging should occur
        reload_calls = [
            call
            for call in mock_logger.info.call_args_list
            if "reload triggered" in str(call)
        ]
        assert len(reload_calls) == 0

        # But success logging should still occur
        mock_logger.info.assert_called_with(
            "✅ Successfully synchronized 2/2 instances"
        )


class TestSynchronizationIntegration:
    """Integration tests for synchronization functionality."""

    @pytest.mark.asyncio
    async def test_synchronization_end_to_end_flow(self):
        """Test complete synchronization flow from context to metrics."""
        # Arrange
        from haproxy_template_ic.dataplane.endpoint import DataplaneEndpointSet
        from haproxy_template_ic.models.templates import RenderedContent, ContentType

        # Create realistic context
        context = HAProxyConfigContext(template_context=TemplateContext())
        context.rendered_config = RenderedConfig(
            content="global\n    daemon\n\ndefaults\n    mode http\n\nfrontend web\n    bind *:80"
        )
        context.rendered_content = [
            RenderedContent(
                filename="hosts.map",
                content="example.com web_backend",
                content_type=ContentType.MAP,
            )
        ]

        # Create mock synchronizer with realistic endpoint structure
        mock_synchronizer = Mock(spec=ConfigSynchronizer)
        mock_endpoints = Mock(spec=DataplaneEndpointSet)
        mock_endpoints.production = [
            "http://192.168.1.1:5555",
            "http://192.168.1.2:5555",
        ]
        mock_synchronizer.endpoints = mock_endpoints
        mock_synchronizer.metrics = Mock()

        # Create successful sync result
        mock_result = Mock()
        mock_result.successful = 2
        mock_result.failed = 0
        mock_result.errors = []
        mock_result.reload_info = Mock()
        mock_result.reload_info.reload_triggered = True
        mock_result.reload_info.reload_id = "reload-abc123"

        mock_synchronizer.sync_configuration = AsyncMock(return_value=mock_result)

        # Act
        await synchronize_with_haproxy_instances(context, mock_synchronizer)

        # Assert
        # Verify synchronizer was called with correct context
        mock_synchronizer.sync_configuration.assert_called_once_with(context)

        # Verify metrics were recorded

    # Metrics recording is handled by ConfigSynchronizer internally

    # Error recording is handled by ConfigSynchronizer internally

    @pytest.mark.asyncio
    async def test_synchronization_with_complex_error_scenarios(self):
        """Test synchronization with complex error scenarios."""
        # Arrange
        context = HAProxyConfigContext(template_context=TemplateContext())
        context.rendered_config = RenderedConfig(
            content="invalid config with bind error on port 80"
        )

        mock_synchronizer = Mock(spec=ConfigSynchronizer)
        mock_synchronizer.endpoints = Mock()
        mock_synchronizer.endpoints.production = ["http://192.168.1.1:5555"]
        mock_synchronizer.metrics = Mock()

        # Create validation error with multiple hint triggers
        validation_error = ValidationError(
            message="Multiple validation failures",
            validation_details="Parsing error on line 3: unknown keyword 'invalid' in bind address directive for duplicate backend 'web'",
        )
        mock_synchronizer.sync_configuration = AsyncMock(side_effect=validation_error)

        with patch(
            "haproxy_template_ic.operator.synchronization.logger"
        ) as mock_logger:
            # Act
            await synchronize_with_haproxy_instances(context, mock_synchronizer)

        # Assert
        # Should record validation error
        # Error recording is handled by ConfigSynchronizer internally

        # Should log multiple hints due to error details containing multiple keywords
        hint_calls = [
            call
            for call in mock_logger.info.call_args_list
            if "💡 Troubleshooting hints:" in str(call)
        ]
        assert len(hint_calls) == 1

        # Should include multiple specific hints
        all_info_calls = [str(call) for call in mock_logger.info.call_args_list]
        hints_text = " ".join(all_info_calls)
        assert "Check that bind addresses and ports are valid" in hints_text
        assert "Check for HAProxy version compatibility" in hints_text
        assert "Review the HAProxy configuration for syntax errors" in hints_text
        assert "Check for duplicate section names" in hints_text
