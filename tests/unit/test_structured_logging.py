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
    StructuredFormatter,
    StructuredLogger,
    get_structured_logger,
    setup_structured_logging,
    operation_context,
    component_context_manager,
    resource_context_manager,
    log_template_operation,
    log_dataplane_operation,
    log_kubernetes_event,
)


class TestStructuredFormatter:
    """Test cases for StructuredFormatter class."""

    def test_basic_json_formatting(self):
        """Test basic JSON log formatting."""
        formatter = StructuredFormatter()

        # Create a basic log record
        logger = logging.getLogger("test")
        record = logger.makeRecord(
            name="test.module",
            level=logging.INFO,
            fn="test.py",
            lno=42,
            msg="Test message",
            args=(),
            exc_info=None,
        )

        formatted = formatter.format(record)
        parsed = json.loads(formatted)

        assert parsed["level"] == "INFO"
        assert parsed["logger"] == "test.module"
        assert parsed["message"] == "Test message"
        assert "timestamp" in parsed

    def test_context_injection(self):
        """Test context variable injection into log records."""
        formatter = StructuredFormatter()
        logger = logging.getLogger("test")

        with operation_context("test-op-123"):
            with component_context_manager("test-component"):
                with resource_context_manager(
                    resource_type="Pod",
                    resource_namespace="default",
                    resource_name="test-pod",
                ):
                    record = logger.makeRecord(
                        name="test.module",
                        level=logging.INFO,
                        fn="test.py",
                        lno=42,
                        msg="Test message",
                        args=(),
                        exc_info=None,
                    )

                    formatted = formatter.format(record)
                    parsed = json.loads(formatted)

                    assert parsed["operation_id"] == "test-op-123"
                    assert parsed["component"] == "test-component"
                    assert parsed["resource_type"] == "Pod"
                    assert parsed["resource_namespace"] == "default"
                    assert parsed["resource_name"] == "test-pod"

    def test_extra_fields(self):
        """Test that extra fields are included in output."""
        formatter = StructuredFormatter()
        logger = logging.getLogger("test")

        record = logger.makeRecord(
            name="test.module",
            level=logging.INFO,
            fn="test.py",
            lno=42,
            msg="Test message",
            args=(),
            exc_info=None,
        )

        # Add extra fields
        record.custom_field = "custom_value"
        record.duration = 0.123

        formatted = formatter.format(record)
        parsed = json.loads(formatted)

        assert parsed["custom_field"] == "custom_value"
        assert parsed["duration"] == 0.123


class TestStructuredLogger:
    """Test cases for StructuredLogger class."""

    def test_logger_creation(self):
        """Test structured logger creation."""
        base_logger = logging.getLogger("test")
        structured_logger = StructuredLogger(base_logger)

        assert structured_logger.logger is base_logger

    def test_logging_methods(self):
        """Test all logging level methods work."""
        base_logger = logging.getLogger("test")
        structured_logger = StructuredLogger(base_logger)

        # Should not raise exceptions
        structured_logger.debug("Debug message")
        structured_logger.info("Info message")
        structured_logger.warning("Warning message")
        structured_logger.error("Error message")
        structured_logger.critical("Critical message")

    def test_context_aware_logging(self):
        """Test that structured logger respects context."""
        # Setup logger with string handler to capture output
        stream = StringIO()
        handler = logging.StreamHandler(stream)
        handler.setFormatter(StructuredFormatter())

        base_logger = logging.getLogger("test_context")
        base_logger.setLevel(logging.INFO)
        base_logger.handlers = [handler]

        structured_logger = StructuredLogger(base_logger)

        with operation_context("test-operation"):
            structured_logger.info("Test message", custom_field="test_value")

        output = stream.getvalue()
        parsed = json.loads(output.strip())

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
        # Setup logger to capture structured output
        stream = StringIO()
        handler = logging.StreamHandler(stream)
        handler.setFormatter(StructuredFormatter())

        logger = logging.getLogger("test_nested")
        logger.setLevel(logging.INFO)
        logger.handlers = [handler]

        structured_logger = StructuredLogger(logger)

        with operation_context("outer-op"):
            with component_context_manager("component-a"):
                with resource_context_manager(resource_type="Service"):
                    structured_logger.info("Nested message")

        output = stream.getvalue()
        parsed = json.loads(output.strip())

        assert parsed["operation_id"] == "outer-op"
        assert parsed["component"] == "component-a"
        assert parsed["resource_type"] == "Service"

    def test_context_isolation(self):
        """Test that contexts are properly isolated."""
        from haproxy_template_ic.structured_logging import (
            operation_id_context,
            component_context,
            resource_context,
        )

        # Initially no context
        assert operation_id_context.get() is None
        assert component_context.get() is None
        assert resource_context.get() is None

        with operation_context("test-op"):
            assert operation_id_context.get() == "test-op"

            with component_context_manager("test-component"):
                assert component_context.get() == "test-component"

        # Context should be reset after exiting
        assert operation_id_context.get() is None
        assert component_context.get() is None


class TestSetupLogging:
    """Test cases for logging setup functionality."""

    def test_setup_traditional_logging(self):
        """Test setup with traditional formatter."""
        with patch("logging.getLogger") as mock_get_logger:
            mock_logger = mock_get_logger.return_value
            mock_logger.handlers = []

            setup_structured_logging(verbose_level=1, use_json=False)

            # Should have configured the logger
            mock_logger.setLevel.assert_called_with(logging.INFO)

    def test_setup_json_logging(self):
        """Test setup with JSON formatter."""
        with patch("logging.getLogger") as mock_get_logger:
            mock_logger = mock_get_logger.return_value
            mock_logger.handlers = []

            setup_structured_logging(verbose_level=2, use_json=True)

            # Should have configured the logger with DEBUG level
            mock_logger.setLevel.assert_called_with(logging.DEBUG)

    def test_verbose_levels(self):
        """Test different verbose levels."""
        test_cases = [
            (0, logging.WARNING),
            (1, logging.INFO),
            (2, logging.DEBUG),
            (999, logging.DEBUG),  # Default for unknown levels
        ]

        for verbose_level, expected_level in test_cases:
            with patch("logging.getLogger") as mock_get_logger:
                mock_logger = mock_get_logger.return_value
                mock_logger.handlers = []

                setup_structured_logging(verbose_level=verbose_level)

                mock_logger.setLevel.assert_called_with(expected_level)


class TestConvenienceFunctions:
    """Test cases for convenience logging functions."""

    def test_get_structured_logger(self):
        """Test structured logger factory function."""
        logger = get_structured_logger("test.module")

        assert isinstance(logger, StructuredLogger)
        assert logger.logger.name == "test.module"

    def test_log_template_operation(self):
        """Test template operation logging helper."""
        # Setup logger to capture output
        stream = StringIO()
        handler = logging.StreamHandler(stream)
        handler.setFormatter(StructuredFormatter())

        base_logger = logging.getLogger("test_template")
        base_logger.setLevel(logging.INFO)
        base_logger.handlers = [handler]

        structured_logger = StructuredLogger(base_logger)

        log_template_operation(
            structured_logger,
            template_type="haproxy_config",
            operation="render",
            duration=0.123,
        )

        output = stream.getvalue()
        parsed = json.loads(output.strip())

        assert parsed["message"] == "Template render"
        assert parsed["template_type"] == "haproxy_config"
        assert parsed["template_operation"] == "render"
        assert parsed["duration"] == 0.123

    def test_log_dataplane_operation(self):
        """Test Dataplane API operation logging helper."""
        # Setup logger to capture output
        stream = StringIO()
        handler = logging.StreamHandler(stream)
        handler.setFormatter(StructuredFormatter())

        base_logger = logging.getLogger("test_dataplane")
        base_logger.setLevel(logging.INFO)
        base_logger.handlers = [handler]

        structured_logger = StructuredLogger(base_logger)

        log_dataplane_operation(
            structured_logger,
            operation="validate",
            pod_name="haproxy-pod-1",
            status="success",
        )

        output = stream.getvalue()
        parsed = json.loads(output.strip())

        assert parsed["message"] == "Dataplane API validate"
        assert parsed["pod_name"] == "haproxy-pod-1"
        assert parsed["dataplane_operation"] == "validate"
        assert parsed["status"] == "success"

    def test_log_kubernetes_event(self):
        """Test Kubernetes event logging helper."""
        # Setup logger to capture output
        stream = StringIO()
        handler = logging.StreamHandler(stream)
        handler.setFormatter(StructuredFormatter())

        base_logger = logging.getLogger("test_k8s")
        base_logger.setLevel(logging.INFO)
        base_logger.handlers = [handler]

        structured_logger = StructuredLogger(base_logger)

        log_kubernetes_event(
            structured_logger,
            event_type="MODIFIED",
            resource_type="Ingress",
            namespace="default",
            name="test-ingress",
            reason="ConfigChanged",
        )

        output = stream.getvalue()
        parsed = json.loads(output.strip())

        assert parsed["message"] == "Kubernetes MODIFIED"
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
        stream = StringIO()
        handler = logging.StreamHandler(stream)
        handler.setFormatter(StructuredFormatter())

        # Create logger
        base_logger = logging.getLogger("integration_test")
        base_logger.setLevel(logging.INFO)
        base_logger.handlers = [handler]

        structured_logger = StructuredLogger(base_logger)

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
        lines = stream.getvalue().strip().split("\n")
        entries = [json.loads(line) for line in lines]

        # Verify all entries have the operation ID
        for entry in entries:
            assert entry["operation_id"] == op_id
            assert entry["component"] == "operator"

        # Verify specific log content
        config_entry = entries[0]
        assert config_entry["message"] == "Configuration changed"
        assert config_entry["resource_type"] == "ConfigMap"
        assert config_entry["change_type"] == "template_update"

        template_entry = entries[1]
        assert template_entry["message"] == "Template render"
        assert template_entry["template_type"] == "map"
        assert template_entry["duration"] == 0.042

        dataplane_entry = entries[2]
        assert dataplane_entry["message"] == "Dataplane API deploy"
        assert dataplane_entry["pod_name"] == "haproxy-production-1"
        assert dataplane_entry["version"] == "1.2.3"
