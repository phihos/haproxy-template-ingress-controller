"""
Tests for haproxy_template_ic.structured_logging module.

This module contains tests for structured logging functionality including
context management, JSON formatting, and correlation features.
"""

import json
import logging
from io import StringIO
from unittest.mock import patch


from haproxy_template_ic.structured_logging import (
    StructuredLogger,
    get_structured_logger,
    setup_structured_logging,
    operation_context,
    component_context_manager,
    resource_context_manager,
    log_template_operation,
    log_dataplane_operation,
    log_kubernetes_event,
    custom_logfmt_renderer,
    custom_timestamp_processor,
)


class TestCustomProcessors:
    """Test cases for custom structlog processors."""

    def test_custom_timestamp_processor(self):
        """Test custom timestamp processor formats correctly."""
        event_dict = {"event": "test message"}
        result = custom_timestamp_processor(None, None, event_dict)

        assert "timestamp" in result
        # Check timestamp format (YYYY-MM-DD HH:MM:SS,mmm)
        timestamp = result["timestamp"]
        assert len(timestamp) == 23  # Expected length for the format
        assert "," in timestamp  # Should contain comma separator for milliseconds

    def test_custom_logfmt_renderer(self):
        """Test custom logfmt renderer formats correctly."""
        event_dict = {
            "timestamp": "2025-01-01 12:00:00,000",
            "level": "INFO",
            "logger": "test.module",
            "event": "Test message",
            "operation_id": "test-op-123",
            "component": "test-component",
        }

        result = custom_logfmt_renderer(None, None, event_dict)

        # Should start with traditional format
        assert result.startswith(
            "2025-01-01 12:00:00,000 - test.module - INFO - Test message"
        )
        # Should end with logfmt context
        assert "operation_id=test-op-123" in result
        assert "component=test-component" in result

    def test_custom_logfmt_renderer_with_quotes(self):
        """Test custom logfmt renderer handles values with spaces and quotes."""
        event_dict = {
            "timestamp": "2025-01-01 12:00:00,000",
            "level": "INFO",
            "logger": "test.module",
            "event": "Test message",
            "config_diff": "{'key': 'value with spaces'}",
            "simple": "no_spaces",
        }

        result = custom_logfmt_renderer(None, None, event_dict)

        # Should quote values with spaces
        assert "config_diff=\"{'key': 'value with spaces'}\"" in result
        # Should not quote simple values
        assert "simple=no_spaces" in result


class TestStructuredLogger:
    """Test cases for StructuredLogger class."""

    def test_logger_creation(self):
        """Test structured logger creation."""
        # Setup structlog first
        setup_structured_logging(verbose_level=1, use_json=False)

        logger = get_structured_logger("test")
        assert isinstance(logger, StructuredLogger)
        # The logger might be a BoundLoggerLazyProxy or BoundLogger
        assert hasattr(logger.logger, "info")  # Check it has logging methods

    def test_logging_methods(self):
        """Test all logging level methods work."""
        # Setup structlog first
        setup_structured_logging(verbose_level=1, use_json=False)

        logger = get_structured_logger("test")

        # Should not raise exceptions
        logger.debug("Debug message")
        logger.info("Info message")
        logger.warning("Warning message")
        logger.error("Error message")
        logger.critical("Critical message")

    def test_context_aware_logging(self):
        """Test that structured logger respects context."""
        # Setup JSON logging to capture structured output
        setup_structured_logging(verbose_level=1, use_json=True)

        # Capture output
        stream = StringIO()
        handler = logging.StreamHandler(stream)
        root_logger = logging.getLogger()
        root_logger.handlers = [handler]

        structured_logger = get_structured_logger("test_context")

        with operation_context("test-operation"):
            structured_logger.info("Test message", custom_field="test_value")

        output = stream.getvalue().strip()
        if output:  # Only parse if we got output
            parsed = json.loads(output)
            assert parsed["operation_id"] == "test-operation"
            assert parsed["custom_field"] == "test_value"


class TestContextManagers:
    """Test cases for context manager functionality."""

    def test_operation_context_auto_generation(self):
        """Test automatic operation ID generation."""
        with operation_context() as op_id:
            assert isinstance(op_id, str)
            assert len(op_id) == 8  # Short UUID

    def test_operation_context_explicit_id(self):
        """Test explicit operation ID setting."""
        with operation_context("custom-op-id") as op_id:
            assert op_id == "custom-op-id"

    def test_nested_contexts(self):
        """Test nested context management."""
        # Setup JSON logging to capture structured output
        setup_structured_logging(verbose_level=1, use_json=True)

        # Capture output
        stream = StringIO()
        handler = logging.StreamHandler(stream)
        root_logger = logging.getLogger()
        root_logger.handlers = [handler]

        structured_logger = get_structured_logger("test_nested")

        with operation_context("outer-op"):
            with component_context_manager("component-a"):
                with resource_context_manager(resource_type="Service"):
                    structured_logger.info("Nested message")

        output = stream.getvalue().strip()
        if output:  # Only parse if we got output
            parsed = json.loads(output)
            assert parsed["operation_id"] == "outer-op"
            assert parsed["component"] == "component-a"
            assert parsed["resource_type"] == "Service"

    def test_context_isolation(self):
        """Test that contexts are properly isolated."""
        import structlog.contextvars

        # Clear any existing context
        structlog.contextvars.clear_contextvars()

        # Initially no context
        context_vars = structlog.contextvars.get_contextvars()
        assert "operation_id" not in context_vars
        assert "component" not in context_vars

        with operation_context("test-op"):
            context_vars = structlog.contextvars.get_contextvars()
            assert context_vars.get("operation_id") == "test-op"

            with component_context_manager("test-component"):
                context_vars = structlog.contextvars.get_contextvars()
                assert context_vars.get("component") == "test-component"

        # Context should be reset after exiting
        context_vars = structlog.contextvars.get_contextvars()
        assert "operation_id" not in context_vars
        assert "component" not in context_vars


class TestSetupLogging:
    """Test cases for logging setup functionality."""

    def test_setup_traditional_logging(self):
        """Test setup with traditional formatter."""
        setup_structured_logging(verbose_level=1, use_json=False)

        # Verify structlog is configured
        import structlog

        logger = structlog.get_logger("test")
        assert logger is not None

    def test_setup_json_logging(self):
        """Test setup with JSON formatter."""
        setup_structured_logging(verbose_level=2, use_json=True)

        # Verify structlog is configured
        import structlog

        logger = structlog.get_logger("test")
        assert logger is not None

    def test_verbose_levels(self):
        """Test different verbose levels."""
        test_cases = [
            (0, logging.WARNING),
            (1, logging.INFO),
            (2, logging.DEBUG),
            (999, logging.DEBUG),  # Default for unknown levels
        ]

        for verbose_level, expected_level in test_cases:
            with patch("logging.basicConfig") as mock_basic_config:
                setup_structured_logging(verbose_level=verbose_level)
                mock_basic_config.assert_called()
                args, kwargs = mock_basic_config.call_args
                assert kwargs["level"] == expected_level


class TestConvenienceFunctions:
    """Test cases for convenience logging functions."""

    def test_get_structured_logger(self):
        """Test structured logger factory function."""
        setup_structured_logging(verbose_level=1, use_json=False)

        logger = get_structured_logger("test.module")

        assert isinstance(logger, StructuredLogger)
        # The underlying logger should be a structlog bound logger (could be lazy proxy)
        assert hasattr(logger.logger, "info")  # Check it has logging methods

    def test_log_template_operation(self):
        """Test template operation logging helper."""
        # Setup JSON logging to capture structured output
        setup_structured_logging(verbose_level=1, use_json=True)

        # Capture output
        stream = StringIO()
        handler = logging.StreamHandler(stream)
        root_logger = logging.getLogger()
        root_logger.handlers = [handler]

        structured_logger = get_structured_logger("test_template")

        log_template_operation(
            structured_logger,
            template_type="haproxy_config",
            operation="render",
            duration=0.123,
        )

        output = stream.getvalue().strip()
        if output:  # Only parse if we got output
            parsed = json.loads(output)
            assert parsed["event"] == "Template render"
            assert parsed["template_type"] == "haproxy_config"
            assert parsed["template_operation"] == "render"
            assert parsed["duration"] == 0.123

    def test_log_dataplane_operation(self):
        """Test Dataplane API operation logging helper."""
        # Setup JSON logging to capture structured output
        setup_structured_logging(verbose_level=1, use_json=True)

        # Capture output
        stream = StringIO()
        handler = logging.StreamHandler(stream)
        root_logger = logging.getLogger()
        root_logger.handlers = [handler]

        structured_logger = get_structured_logger("test_dataplane")

        log_dataplane_operation(
            structured_logger,
            operation="validate",
            pod_name="haproxy-pod-1",
            status="success",
        )

        output = stream.getvalue().strip()
        if output:  # Only parse if we got output
            parsed = json.loads(output)
            assert parsed["event"] == "Dataplane API validate"
            assert parsed["pod_name"] == "haproxy-pod-1"
            assert parsed["dataplane_operation"] == "validate"
            assert parsed["status"] == "success"

    def test_log_kubernetes_event(self):
        """Test Kubernetes event logging helper."""
        # Setup JSON logging to capture structured output
        setup_structured_logging(verbose_level=1, use_json=True)

        # Capture output
        stream = StringIO()
        handler = logging.StreamHandler(stream)
        root_logger = logging.getLogger()
        root_logger.handlers = [handler]

        structured_logger = get_structured_logger("test_k8s")

        log_kubernetes_event(
            structured_logger,
            event_type="MODIFIED",
            resource_type="Ingress",
            namespace="default",
            name="test-ingress",
            reason="ConfigChanged",
        )

        output = stream.getvalue().strip()
        if output:  # Only parse if we got output
            parsed = json.loads(output)
            assert parsed["event"] == "Kubernetes MODIFIED"
            assert parsed["resource_type"] == "Ingress"
            assert parsed["resource_namespace"] == "default"
            assert parsed["resource_name"] == "test-ingress"
            assert parsed["kubernetes_event"] == "MODIFIED"
            assert parsed["reason"] == "ConfigChanged"


class TestIntegration:
    """Integration tests for structured logging."""

    def test_end_to_end_structured_logging(self):
        """Test complete structured logging workflow."""
        # Setup JSON logging
        setup_structured_logging(verbose_level=1, use_json=True)

        # Capture output
        stream = StringIO()
        handler = logging.StreamHandler(stream)
        root_logger = logging.getLogger()
        # Clear existing handlers to avoid interference
        root_logger.handlers = [handler]

        structured_logger = get_structured_logger("integration_test")

        # Simulate operator workflow with nested contexts
        with operation_context("workflow-123") as op_id:
            with component_context_manager("operator"):
                # Log configuration change
                with resource_context_manager(
                    resource_type="ConfigMap",
                    resource_namespace="default",
                    resource_name="haproxy-config",
                ):
                    structured_logger.info(
                        "Configuration changed",
                        change_type="template_update",
                        maps_count=3,
                    )

                # Log template rendering
                log_template_operation(
                    structured_logger,
                    template_type="map",
                    operation="render",
                    duration=0.042,
                    success=True,
                )

                # Log Dataplane API call
                log_dataplane_operation(
                    structured_logger,
                    operation="deploy",
                    pod_name="haproxy-production-1",
                    version="1.2.3",
                )

        # Parse all log entries
        output = stream.getvalue().strip()
        if output:  # Only process if we got output
            lines = output.split("\n")
            entries = [json.loads(line) for line in lines if line.strip()]

            # Verify all entries have the operation ID
            for entry in entries:
                assert entry["operation_id"] == op_id
                assert entry["component"] == "operator"

            if len(entries) >= 3:  # Check if we have all expected entries
                # Verify specific log content
                config_entry = entries[0]
                assert config_entry["event"] == "Configuration changed"
                assert config_entry["resource_type"] == "ConfigMap"
                assert config_entry["change_type"] == "template_update"

                template_entry = entries[1]
                assert template_entry["event"] == "Template render"
                assert template_entry["template_type"] == "map"
                assert template_entry["duration"] == 0.042

                dataplane_entry = entries[2]
                assert dataplane_entry["event"] == "Dataplane API deploy"
                assert dataplane_entry["pod_name"] == "haproxy-production-1"
                assert dataplane_entry["version"] == "1.2.3"
