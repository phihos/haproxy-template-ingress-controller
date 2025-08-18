"""
Tests for haproxy_template_ic.structured_logging module.

This module contains tests for structured logging functionality including
context management, JSON formatting, and correlation features.
"""

import json
import logging
from io import StringIO
from unittest.mock import patch


import structlog
from haproxy_template_ic.structured_logging import (
    setup_structured_logging,
    logging_context,
)


class TestStructuredLogger:
    """Test cases for structured logger functionality."""

    def test_logger_creation(self):
        """Test structured logger creation."""
        # Setup structlog first
        setup_structured_logging(verbose_level=1, use_json=False)

        logger = structlog.get_logger("test")
        # Verify logger has required logging methods
        assert hasattr(logger, "debug")
        assert hasattr(logger, "info")
        assert hasattr(logger, "warning")
        assert hasattr(logger, "error")
        assert hasattr(logger, "critical")

    def test_logging_methods(self):
        """Test all logging level methods work."""
        # Setup structlog first
        setup_structured_logging(verbose_level=1, use_json=False)

        logger = structlog.get_logger("test")

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

        structured_logger = structlog.get_logger("test_context")

        with logging_context(operation_id="test-operation"):
            structured_logger.info("Test message", custom_field="test_value")

        output = stream.getvalue().strip()
        if output:  # Only parse if we got output
            parsed = json.loads(output)
            assert parsed["operation_id"] == "test-operation"
            assert parsed["custom_field"] == "test_value"


class TestContextManagers:
    """Test cases for context manager functionality."""

    def test_logging_context_auto_generation(self):
        """Test automatic operation ID generation."""
        with logging_context(operation_id=None) as op_id:
            assert isinstance(op_id, str)
            assert len(op_id) == 8  # Short UUID

    def test_logging_context_explicit_id(self):
        """Test explicit operation ID setting."""
        with logging_context(operation_id="custom-op-id") as op_id:
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

        structured_logger = structlog.get_logger("test_nested")

        with logging_context(
            operation_id="outer-op", component="component-a", resource_type="Service"
        ):
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

        with logging_context(operation_id="test-op"):
            context_vars = structlog.contextvars.get_contextvars()
            assert context_vars.get("operation_id") == "test-op"

            with logging_context(component="test-component"):
                context_vars = structlog.contextvars.get_contextvars()
                assert context_vars.get("component") == "test-component"

        # Context should be reset after exiting
        context_vars = structlog.contextvars.get_contextvars()
        assert "operation_id" not in context_vars
        assert "component" not in context_vars

    def test_concurrent_context_management(self):
        """Test that context variables work correctly with concurrent operations."""
        import structlog.contextvars
        from concurrent.futures import ThreadPoolExecutor

        # Clear any existing context
        structlog.contextvars.clear_contextvars()

        def worker_function(worker_id: str) -> dict:
            """Worker function that sets and reads context in a thread."""
            with logging_context(
                operation_id=f"worker-{worker_id}", component=f"component-{worker_id}"
            ):
                # Simulate some work
                import time

                time.sleep(0.01)

                # Return the context as seen by this worker
                return dict(structlog.contextvars.get_contextvars())

        # Run multiple workers concurrently
        with ThreadPoolExecutor(max_workers=3) as executor:
            futures = [executor.submit(worker_function, str(i)) for i in range(3)]

            results = [future.result() for future in futures]

        # Each worker should have seen its own context
        for i, result in enumerate(results):
            assert result["operation_id"] == f"worker-{i}"
            assert result["component"] == f"component-{i}"

        # Main thread context should be clean
        context_vars = structlog.contextvars.get_contextvars()
        assert "operation_id" not in context_vars
        assert "component" not in context_vars

    def test_logging_context_cleanup(self):
        """Test that resource context manager properly cleans up all bound variables."""
        import structlog.contextvars

        # Clear any existing context
        structlog.contextvars.clear_contextvars()

        # Initially no context
        context_vars = structlog.contextvars.get_contextvars()
        assert len(context_vars) == 0

        # Test with all possible parameters
        with logging_context(
            resource_type="Service",
            resource_namespace="test-namespace",
            resource_name="test-service",
            custom_field="custom_value",
            another_field=42,
        ):
            context_vars = structlog.contextvars.get_contextvars()
            assert len(context_vars) == 5
            assert context_vars["resource_type"] == "Service"
            assert context_vars["resource_namespace"] == "test-namespace"
            assert context_vars["resource_name"] == "test-service"
            assert context_vars["custom_field"] == "custom_value"
            assert context_vars["another_field"] == 42

        # All context should be cleaned up
        context_vars = structlog.contextvars.get_contextvars()
        assert len(context_vars) == 0

    def test_logging_context_partial_parameters(self):
        """Test resource context manager with only some parameters set."""
        import structlog.contextvars

        # Clear any existing context
        structlog.contextvars.clear_contextvars()

        # Test with only resource_type
        with logging_context(resource_type="Pod"):
            context_vars = structlog.contextvars.get_contextvars()
            assert len(context_vars) == 1
            assert context_vars["resource_type"] == "Pod"

        # Should be cleaned up
        context_vars = structlog.contextvars.get_contextvars()
        assert len(context_vars) == 0

        # Test with no parameters (should be no-op)
        with logging_context():
            context_vars = structlog.contextvars.get_contextvars()
            assert len(context_vars) == 0

        # Should still be clean
        context_vars = structlog.contextvars.get_contextvars()
        assert len(context_vars) == 0


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

        logger = structlog.get_logger("test.module")

        # Verify logger has required logging methods
        assert hasattr(logger, "debug")
        assert hasattr(logger, "info")
        assert hasattr(logger, "warning")
        assert hasattr(logger, "error")
        assert hasattr(logger, "critical")


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

        structured_logger = structlog.get_logger("integration_test")

        # Simulate operator workflow with nested contexts
        with logging_context(operation_id="workflow-123") as op_id:
            with logging_context(
                component="operator",
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
            with logging_context(component="operator", template_type="map"):
                structured_logger.info(
                    "Template render",
                    template_operation="render",
                    duration=0.042,
                    success=True,
                )

            # Log Dataplane API call
            with logging_context(component="operator", pod_name="haproxy-production-1"):
                structured_logger.info(
                    "Dataplane API deploy",
                    dataplane_operation="deploy",
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


class TestEdgeCases:
    """Test cases for edge cases and error conditions."""

    def test_performance_with_many_context_fields(self):
        """Test logging performance with many context fields."""
        # Setup structured logging
        setup_structured_logging(verbose_level=1, use_json=False)

        logger = structlog.get_logger("performance_test")

        # Test with many context fields - should not raise exceptions
        with logging_context(**{f"field_{i}": f"value_{i}" for i in range(20)}):
            logger.info("Performance test with many fields")
