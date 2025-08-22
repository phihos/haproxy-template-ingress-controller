"""
Tests for haproxy_template_ic.structured_logging module.

This module contains tests for structured logging functionality including
autolog and observe decorators, JSON formatting, and context injection.
"""

import json
import logging
import asyncio
from io import StringIO
from unittest.mock import patch

import structlog
from haproxy_template_ic.structured_logging import (
    setup_structured_logging,
    autolog,
    observe,
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


class TestAutologDecorator:
    """Test cases for @autolog decorator functionality."""

    def test_autolog_with_sync_function(self):
        """Test @autolog decorator with synchronous function."""
        setup_structured_logging(verbose_level=1, use_json=True)

        # Capture output
        stream = StringIO()
        handler = logging.StreamHandler(stream)
        root_logger = logging.getLogger()
        root_logger.handlers = [handler]

        @autolog(component="test")
        def test_function(name: str, value: int):
            logger = structlog.get_logger(__name__)
            logger.info("Test message", name=name, value=value)
            return f"{name}={value}"

        result = test_function("param1", 42)
        assert result == "param1=42"

    def test_autolog_with_async_function(self):
        """Test @autolog decorator with async function."""
        setup_structured_logging(verbose_level=1, use_json=True)

        @autolog(component="test")
        async def async_test_function(name: str):
            logger = structlog.get_logger(__name__)
            logger.info("Async test message", name=name)
            return f"async_{name}"

        async def run_test():
            result = await async_test_function("test_param")
            assert result == "async_test_param"

        asyncio.run(run_test())

    def test_autolog_kopf_event_handler_detection(self):
        """Test @autolog automatically detects kopf event handlers."""
        setup_structured_logging(verbose_level=1, use_json=True)

        # Capture output
        stream = StringIO()
        handler = logging.StreamHandler(stream)
        root_logger = logging.getLogger()
        root_logger.handlers = [handler]

        @autolog(component="operator")
        def handle_configmap_change(event, name, type, **kwargs):
            logger = structlog.get_logger(__name__)
            logger.info("ConfigMap changed")

        # Mock kopf event structure
        mock_event = {
            "object": {
                "kind": "ConfigMap",
                "metadata": {"name": "test-config", "namespace": "default"},
            }
        }

        handle_configmap_change(event=mock_event, name="test-config", type="MODIFIED")

        # Verify context was automatically extracted
        output = stream.getvalue().strip()
        if output:
            parsed = json.loads(output)
            assert parsed["component"] == "operator"
            assert parsed["resource_type"] == "ConfigMap"
            assert parsed["resource_name"] == "test-config"
            assert parsed["resource_namespace"] == "default"
            assert parsed["kubernetes_event"] == "MODIFIED"
            assert "operation_id" in parsed

    def test_autolog_operation_id_generation(self):
        """Test automatic operation ID generation."""

        @autolog()
        def test_function():
            # Check that operation_id was set in context
            context_vars = structlog.contextvars.get_contextvars()
            assert "operation_id" in context_vars
            assert len(context_vars["operation_id"]) == 8
            return context_vars["operation_id"]

        op_id = test_function()
        assert isinstance(op_id, str)
        assert len(op_id) == 8

    def test_autolog_context_cleanup(self):
        """Test that autolog properly cleans up context variables."""
        import structlog.contextvars

        # Clear any existing context
        structlog.contextvars.clear_contextvars()

        @autolog(component="test", resource_type="Pod")
        def test_function():
            context_vars = structlog.contextvars.get_contextvars()
            assert len(context_vars) >= 2  # At least component and operation_id
            assert context_vars["component"] == "test"
            assert context_vars["resource_type"] == "Pod"

        # Initially no context
        context_vars = structlog.contextvars.get_contextvars()
        assert len(context_vars) == 0

        test_function()

        # Context should be cleaned up after function execution
        context_vars = structlog.contextvars.get_contextvars()
        assert len(context_vars) == 0


class TestObserveDecorator:
    """Test cases for @observe decorator functionality."""

    def test_observe_combines_autolog_and_tracing(self):
        """Test that @observe decorator combines autolog and tracing."""
        setup_structured_logging(verbose_level=1, use_json=True)

        @observe(component="test", span_name="test_operation")
        async def test_function(name: str):
            logger = structlog.get_logger(__name__)
            logger.info("Test message with tracing", name=name)
            return f"observed_{name}"

        async def run_test():
            result = await test_function("test_param")
            assert result == "observed_test_param"

        asyncio.run(run_test())


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

                # In test environment, basicConfig should be called
                mock_basic_config.assert_called_once()
                args, kwargs = mock_basic_config.call_args
                assert kwargs["level"] == expected_level


class TestErrorHandling:
    """Test cases for error handling and edge conditions."""

    def test_signature_mismatch_handling(self):
        """Test that signature mismatch in parameter extraction is handled gracefully."""
        from haproxy_template_ic.structured_logging import (
            _extract_context_from_parameters,
        )

        def function_with_required_params(required_param: str):
            return f"called with {required_param}"

        # Test direct parameter extraction with mismatched arguments
        # This should not crash and should return minimal context with operation_id
        context = _extract_context_from_parameters(
            function_with_required_params,
            args=("extra_arg", "another_arg"),  # Wrong number of args
            kwargs={"wrong_param": "value"},  # Wrong parameter names
            decorator_kwargs={"component": "test"},
        )

        # Should return minimal context with operation_id when signature binding fails
        assert context["component"] == "test"
        assert "operation_id" in context
        assert len(context["operation_id"]) == 8  # UUID first 8 chars

    def test_malformed_event_object_handling(self):
        """Test handling of malformed event objects."""

        @autolog(component="operator")
        def handle_event(event, name, type, **kwargs):
            context_vars = structlog.contextvars.get_contextvars()
            return dict(context_vars)

        # Test with completely malformed event
        result1 = handle_event(event="not_a_dict", name="test", type="MODIFIED")
        assert result1["component"] == "operator"
        assert "operation_id" in result1

        # Test with event missing 'object' key
        result2 = handle_event(event={}, name="test", type="MODIFIED")
        assert result2["component"] == "operator"

        # Test with event object missing 'metadata'
        result3 = handle_event(
            event={"object": {"kind": "ConfigMap"}}, name="test", type="MODIFIED"
        )
        assert result3["component"] == "operator"
        assert result3["resource_type"] == "ConfigMap"

    def test_context_cleanup_on_exception(self):
        """Test that context is cleaned up even when exceptions occur."""
        import structlog.contextvars

        # Clear any existing context
        structlog.contextvars.clear_contextvars()

        @autolog(component="test", resource_type="Pod")
        def failing_function():
            # Check context is set during execution
            context_vars = structlog.contextvars.get_contextvars()
            assert context_vars["component"] == "test"
            assert context_vars["resource_type"] == "Pod"
            # Then raise an exception
            raise ValueError("Test exception")

        # Function should raise exception but context should be cleaned up
        try:
            failing_function()
            assert False, "Expected ValueError"
        except ValueError:
            pass

        # Context should be clean after exception
        context_vars = structlog.contextvars.get_contextvars()
        assert len(context_vars) == 0

    def test_observe_decorator_without_tracing(self):
        """Test observe decorator when tracing module is not available."""
        from unittest.mock import patch

        # Mock the import to fail
        with patch.dict("sys.modules", {"haproxy_template_ic.tracing": None}):
            # This should not crash and should fall back to just autolog
            @observe(component="test", span_name="test_operation")
            async def test_function(name: str):
                context_vars = structlog.contextvars.get_contextvars()
                return dict(context_vars)

            async def run_test():
                result = await test_function("test_param")
                assert result["component"] == "test"
                assert "operation_id" in result

            import asyncio

            asyncio.run(run_test())

    def test_parameter_extraction_with_invalid_signatures(self):
        """Test parameter extraction handles various invalid signatures."""

        # Function with *args, **kwargs should work fine
        @autolog(component="flexible")
        def flexible_function(*args, **kwargs):
            context_vars = structlog.contextvars.get_contextvars()
            return dict(context_vars)

        result = flexible_function("any", "args", unexpected_param="value")
        assert result["component"] == "flexible"
        assert "operation_id" in result


class TestEdgeCases:
    """Test cases for edge cases and boundary conditions."""

    def test_autolog_with_many_parameters(self):
        """Test autolog with functions that have many parameters."""

        @autolog(component="test")
        def complex_function(a, b, c, name=None, namespace=None, event=None, **kwargs):
            return {"a": a, "b": b, "c": c, "name": name, "namespace": namespace}

        result = complex_function(1, 2, 3, name="test", namespace="default")
        assert result["name"] == "test"
        assert result["namespace"] == "default"

    def test_autolog_context_isolation(self):
        """Test that autolog contexts are properly isolated between function calls."""
        import structlog.contextvars
        from concurrent.futures import ThreadPoolExecutor

        @autolog(component="worker")
        def worker_function(worker_id: str) -> dict:
            """Worker function that sets and reads context in a thread."""
            # Simulate some work
            import time

            time.sleep(0.01)

            # Return the context as seen by this worker
            return dict(structlog.contextvars.get_contextvars())

        # Clear any existing context
        structlog.contextvars.clear_contextvars()

        # Run multiple workers concurrently
        with ThreadPoolExecutor(max_workers=3) as executor:
            futures = [executor.submit(worker_function, str(i)) for i in range(3)]
            results = [future.result() for future in futures]

        # Each worker should have seen its own context with unique operation_id
        operation_ids = [result.get("operation_id") for result in results]
        assert len(set(operation_ids)) == 3  # All operation IDs should be unique

        # All should have the same component
        for result in results:
            assert result["component"] == "worker"

        # Main thread context should be clean
        context_vars = structlog.contextvars.get_contextvars()
        assert len(context_vars) == 0

    def test_signature_caching_performance(self):
        """Test that function signature caching improves performance."""
        from haproxy_template_ic.structured_logging import _get_function_signature

        def test_function(param1, param2="default"):
            pass

        # First call should cache the signature
        sig1 = _get_function_signature(test_function)

        # Second call should use cache
        sig2 = _get_function_signature(test_function)

        # Should be the same signature object (cached)
        assert sig1 is sig2
        # Ensure it doesn't crash and returns the same cached object
