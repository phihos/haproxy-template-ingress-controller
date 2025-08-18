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
    get_structured_logger,
    setup_structured_logging,
    operation_context,
    component_context_manager,
    resource_context_manager,
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

    def test_custom_logfmt_renderer_special_characters(self):
        """Test custom logfmt renderer handles special characters correctly."""
        event_dict = {
            "timestamp": "2025-01-01 12:00:00,000",
            "level": "INFO",
            "logger": "test.module",
            "event": "Test message",
            "multiline": "line1\nline2\nline3",
            "with_tabs": "col1\tcol2\tcol3",
            "with_carriage": "data\rmore_data",
            "with_quotes": 'value with "quotes" inside',
            "with_backslashes": "path\\to\\file",
            "normal": "simple_value",
        }

        result = custom_logfmt_renderer(None, None, event_dict)

        # Should properly escape newlines
        assert 'multiline="line1\\nline2\\nline3"' in result
        # Should properly escape tabs
        assert 'with_tabs="col1\\tcol2\\tcol3"' in result
        # Should properly escape carriage returns
        assert 'with_carriage="data\\rmore_data"' in result
        # Should properly escape quotes
        assert 'with_quotes="value with \\"quotes\\" inside"' in result
        # Should properly escape backslashes
        assert 'with_backslashes="path\\\\to\\\\file"' in result
        # Should not quote normal values
        assert "normal=simple_value" in result

    def test_custom_timestamp_processor_thread_safety(self):
        """Test timestamp processor captures time consistently."""
        import time

        # Mock time.time and time.gmtime to verify they're called consistently
        original_time = time.time
        original_gmtime = time.gmtime

        mock_time_value = 1640995200.122  # Fixed timestamp with milliseconds
        mock_time_calls = []
        mock_gmtime_calls = []

        def mock_time():
            mock_time_calls.append(mock_time_value)
            return mock_time_value

        def mock_gmtime(timestamp):
            mock_gmtime_calls.append(timestamp)
            return original_gmtime(timestamp)

        try:
            time.time = mock_time
            time.gmtime = mock_gmtime

            event_dict = {"event": "test message"}
            result = custom_timestamp_processor(None, None, event_dict)

            # Should have called time.time() once
            assert len(mock_time_calls) == 1
            # Should have called time.gmtime() once with the same timestamp
            assert len(mock_gmtime_calls) == 1
            assert mock_gmtime_calls[0] == mock_time_value

            # Should have correct timestamp format with milliseconds
            assert "timestamp" in result
            assert result["timestamp"] == "2022-01-01 00:00:00,121"

        finally:
            time.time = original_time
            time.gmtime = original_gmtime


class TestStructuredLogger:
    """Test cases for structured logger functionality."""

    def test_logger_creation(self):
        """Test structured logger creation."""
        # Setup structlog first
        setup_structured_logging(verbose_level=1, use_json=False)

        logger = get_structured_logger("test")
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

    def test_concurrent_context_management(self):
        """Test that context variables work correctly with concurrent operations."""
        import structlog.contextvars
        from concurrent.futures import ThreadPoolExecutor

        # Clear any existing context
        structlog.contextvars.clear_contextvars()

        def worker_function(worker_id: str) -> dict:
            """Worker function that sets and reads context in a thread."""
            with operation_context(f"worker-{worker_id}"):
                with component_context_manager(f"component-{worker_id}"):
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

    def test_resource_context_manager_cleanup(self):
        """Test that resource context manager properly cleans up all bound variables."""
        import structlog.contextvars

        # Clear any existing context
        structlog.contextvars.clear_contextvars()

        # Initially no context
        context_vars = structlog.contextvars.get_contextvars()
        assert len(context_vars) == 0

        # Test with all possible parameters
        with resource_context_manager(
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

    def test_resource_context_manager_partial_parameters(self):
        """Test resource context manager with only some parameters set."""
        import structlog.contextvars

        # Clear any existing context
        structlog.contextvars.clear_contextvars()

        # Test with only resource_type
        with resource_context_manager(resource_type="Pod"):
            context_vars = structlog.contextvars.get_contextvars()
            assert len(context_vars) == 1
            assert context_vars["resource_type"] == "Pod"

        # Should be cleaned up
        context_vars = structlog.contextvars.get_contextvars()
        assert len(context_vars) == 0

        # Test with no parameters (should be no-op)
        with resource_context_manager():
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

        logger = get_structured_logger("test.module")

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
                with resource_context_manager(template_type="map"):
                    structured_logger.info(
                        "Template render",
                        template_operation="render",
                        duration=0.042,
                        success=True,
                    )

                # Log Dataplane API call
                with resource_context_manager(pod_name="haproxy-production-1"):
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
        """Test performance of logfmt renderer with many context fields."""
        # Setup structured logging
        setup_structured_logging(verbose_level=1, use_json=False)

        # Create event dict with many fields
        event_dict = {
            "timestamp": "2025-01-01 12:00:00,000",
            "level": "INFO",
            "logger": "test.module",
            "event": "Performance test",
        }

        # Add many context fields
        for i in range(50):
            event_dict[f"field_{i}"] = f"value_{i}"
            event_dict[f"quoted_field_{i}"] = f"value with spaces {i}"

        # Should not raise exceptions and should format correctly
        result = custom_logfmt_renderer(None, None, event_dict)

        assert "Performance test" in result
        assert "field_0=value_0" in result
        assert 'quoted_field_0="value with spaces 0"' in result
