"""
Tests for haproxy_template_ic.tracing module.

This module contains comprehensive tests for distributed tracing functionality
including OpenTelemetry integration, span management, and instrumentation.
"""

import os
from unittest.mock import MagicMock, Mock

import pytest
from opentelemetry.trace import StatusCode

import haproxy_template_ic.tracing as tracing_module
from haproxy_template_ic.tracing import (
    TracingConfig,
    TracingManager,
    initialize_tracing,
    get_tracing_manager,
    get_tracer,
    trace_operation,
    trace_async_function,
    trace_function,
    add_span_attributes,
    record_span_event,
    set_span_error,
    trace_template_render,
    trace_dataplane_operation,
    trace_kubernetes_operation,
    create_tracing_config_from_env,
    shutdown_tracing,
)
from tests.unit.conftest import patch_tracing_manager


def test_tracing_config_defaults():
    """Test tracing configuration default values."""
    config = TracingConfig()

    assert config.enabled is False
    assert config.service_name == "haproxy-template-ic"
    assert config.service_version == "1.0.0"
    assert config.jaeger_endpoint is None
    assert config.sample_rate == 1.0
    assert config.console_export is False


def test_tracing_config_custom_values():
    """Test tracing configuration with custom values."""
    config = TracingConfig(
        enabled=True,
        service_name="custom-service",
        service_version="2.0.0",
        jaeger_endpoint="localhost:14268",
        sample_rate=0.5,
        console_export=True,
    )

    assert config.enabled is True
    assert config.service_name == "custom-service"
    assert config.service_version == "2.0.0"
    assert config.jaeger_endpoint == "localhost:14268"
    assert config.sample_rate == 0.5
    assert config.console_export is True


def test_tracing_manager_initialization_disabled():
    """Test tracing manager with tracing disabled."""
    config = TracingConfig(enabled=False)
    manager = TracingManager(config)

    manager.initialize()

    assert manager.tracer_provider is None
    assert manager.tracer is None
    assert not manager._instrumented


def test_tracing_manager_initialization_enabled(
    monkeypatch,
):
    """Test tracing manager with tracing enabled."""
    config = TracingConfig(enabled=True, console_export=True)
    manager = TracingManager(config)

    # Setup mocks
    mock_set_tracer_provider = MagicMock()
    mock_tracer_provider = MagicMock()
    mock_tracer_provider_cls = MagicMock(return_value=mock_tracer_provider)
    mock_httpx_instr = MagicMock()
    mock_asyncio_instr = MagicMock()

    # Apply patches
    monkeypatch.setattr(
        tracing_module.trace, "set_tracer_provider", mock_set_tracer_provider
    )
    monkeypatch.setattr(tracing_module, "TracerProvider", mock_tracer_provider_cls)
    monkeypatch.setattr(tracing_module, "HTTPXClientInstrumentor", mock_httpx_instr)
    monkeypatch.setattr(tracing_module, "AsyncioInstrumentor", mock_asyncio_instr)

    # Mock instrumentors
    mock_httpx_instrumentor = MagicMock()
    mock_asyncio_instrumentor = MagicMock()
    mock_httpx_instr.return_value = mock_httpx_instrumentor
    mock_asyncio_instr.return_value = mock_asyncio_instrumentor

    manager.initialize()

    # Verify tracer provider was configured
    mock_tracer_provider_cls.assert_called_once()
    mock_set_tracer_provider.assert_called_once_with(mock_tracer_provider)

    # Verify instrumentation was set up
    mock_httpx_instrumentor.instrument.assert_called_once()
    mock_asyncio_instrumentor.instrument.assert_called_once()
    assert manager._instrumented


def test_jaeger_exporter_configuration(monkeypatch):
    """Test Jaeger exporter configuration."""
    config = TracingConfig(enabled=True, jaeger_endpoint="localhost:14268")
    manager = TracingManager(config)

    # Setup mocks
    mock_tracer_provider = MagicMock()
    # Explicitly mock methods that will be called to prevent AsyncMock creation
    mock_tracer_provider.add_span_processor = MagicMock()
    mock_tracer_provider_cls = MagicMock(return_value=mock_tracer_provider)
    mock_batch_processor = MagicMock()
    mock_jaeger_exporter = MagicMock()

    # Apply patches
    monkeypatch.setattr(tracing_module, "TracerProvider", mock_tracer_provider_cls)
    monkeypatch.setattr(tracing_module, "BatchSpanProcessor", mock_batch_processor)
    monkeypatch.setattr(tracing_module, "JaegerExporter", mock_jaeger_exporter)

    manager.initialize()

    # Verify Jaeger exporter was configured
    mock_jaeger_exporter.assert_called_once_with(
        agent_host_name="localhost", agent_port=14268
    )
    # Verify the span processor was added
    mock_tracer_provider.add_span_processor.assert_called_once()


def test_tracing_manager_shutdown():
    """Test tracing manager shutdown."""
    config = TracingConfig(enabled=True)
    manager = TracingManager(config)

    # Mock tracer provider
    mock_tracer_provider = MagicMock()
    manager.tracer_provider = mock_tracer_provider

    manager.shutdown()

    mock_tracer_provider.shutdown.assert_called_once()


def test_initialize_tracing(mock_tracing_manager, monkeypatch):
    """Test global tracing initialization."""
    config = TracingConfig(enabled=True)

    mock_manager_cls = MagicMock(return_value=mock_tracing_manager)
    monkeypatch.setattr(tracing_module, "TracingManager", mock_manager_cls)

    initialize_tracing(config)

    mock_manager_cls.assert_called_once_with(config)
    mock_tracing_manager.initialize.assert_called_once()

    # Verify global state was set
    manager = get_tracing_manager()
    assert manager is mock_tracing_manager


def test_get_tracer_with_manager(mock_tracing_manager, monkeypatch):
    """Test get_tracer with active tracing manager."""
    # Set the global tracing manager
    monkeypatch.setattr(tracing_module, "_tracing_manager", mock_tracing_manager)
    tracer = get_tracer()
    assert tracer is mock_tracing_manager.tracer


def test_get_tracer_without_manager(monkeypatch):
    """Test get_tracer without active tracing manager."""
    monkeypatch.setattr(tracing_module, "_tracing_manager", None)
    tracer = get_tracer()
    assert tracer is None


def test_shutdown_tracing(mock_tracing_manager):
    """Test shutdown tracing."""
    with patch_tracing_manager(mock_tracing_manager):
        shutdown_tracing()
        # The patch context manager handles the shutdown verification


def test_trace_operation_with_tracer(mock_tracer, mock_span):
    """Test trace_operation context manager with active tracer."""
    # Use the passed mock_tracer which already has context manager support
    with patch_tracing_manager(Mock(tracer=mock_tracer)):
        attributes = {"test": "value"}

        with trace_operation("test_operation", attributes) as span:
            assert span is mock_span

        mock_tracer.start_as_current_span.assert_called_once_with("test_operation")
        mock_span.set_attribute.assert_called_once_with("test", "value")


def test_trace_operation_without_tracer(monkeypatch):
    """Test trace_operation context manager without active tracer."""
    monkeypatch.setattr(
        "haproxy_template_ic.tracing.get_tracer", Mock(return_value=None)
    )

    with trace_operation("test_operation") as span:
        assert span is None


def test_trace_operation_with_exception(mock_tracer, mock_span):
    """Test trace_operation context manager with exception."""
    # Use the passed mock_tracer which already has context manager support
    with patch_tracing_manager(Mock(tracer=mock_tracer)):
        test_exception = ValueError("test error")

        with pytest.raises(ValueError):
            with trace_operation("test_operation"):
                raise test_exception

        mock_span.set_status.assert_called_once()
        mock_span.record_exception.assert_called_once_with(test_exception)


def test_add_span_attributes(mock_span, monkeypatch):
    """Test adding attributes to current span."""
    mock_span.is_recording.return_value = True
    # Reset the mock to ensure clean state
    mock_span.set_attribute.reset_mock()
    mock_get_current_span = MagicMock(return_value=mock_span)
    monkeypatch.setattr(tracing_module.trace, "get_current_span", mock_get_current_span)

    add_span_attributes(key1="value1", key2="value2")

    # Verify exactly 2 calls were made with the expected arguments
    assert mock_span.set_attribute.call_count == 2
    mock_span.set_attribute.assert_any_call("key1", "value1")
    mock_span.set_attribute.assert_any_call("key2", "value2")


def test_record_span_event(mock_span, monkeypatch):
    """Test recording events on current span."""
    mock_span.is_recording.return_value = True
    mock_get_current_span = MagicMock(return_value=mock_span)
    monkeypatch.setattr(tracing_module.trace, "get_current_span", mock_get_current_span)

    attributes = {"key": "value"}
    record_span_event("test_event", attributes)

    mock_span.add_event.assert_called_once_with("test_event", attributes)


def test_set_span_error(mock_span, monkeypatch):
    """Test setting span error status."""
    mock_span.is_recording.return_value = True
    mock_get_current_span = MagicMock(return_value=mock_span)
    monkeypatch.setattr(tracing_module.trace, "get_current_span", mock_get_current_span)

    test_error = ValueError("test error")
    set_span_error(test_error, "Custom description")

    mock_span.set_status.assert_called_once()
    status_call = mock_span.set_status.call_args[0][0]
    assert status_call.status_code == StatusCode.ERROR
    assert status_call.description == "Custom description"
    mock_span.record_exception.assert_called_once_with(test_error)


@pytest.mark.asyncio
async def test_trace_async_function_decorator(mock_span, monkeypatch):
    """Test async function tracing decorator."""
    # Properly configure the context manager mock
    mock_context = MagicMock()
    mock_context.__enter__ = MagicMock(return_value=mock_span)
    mock_context.__exit__ = MagicMock(return_value=None)
    mock_trace_operation = MagicMock(return_value=mock_context)
    monkeypatch.setattr(tracing_module, "trace_operation", mock_trace_operation)

    @trace_async_function("custom_span_name", {"attr": "value"})
    async def test_function(arg1: str) -> str:
        return f"result: {arg1}"

    result = await test_function("test_arg")

    assert result == "result: test_arg"
    mock_trace_operation.assert_called_once_with("custom_span_name", {"attr": "value"})
    mock_span.set_attribute.assert_any_call("function.name", "test_function")
    mock_span.set_attribute.assert_any_call("function.module", test_function.__module__)


def test_trace_function_decorator(mock_span, monkeypatch):
    """Test synchronous function tracing decorator."""
    # Properly configure the context manager mock
    mock_context = MagicMock()
    mock_context.__enter__ = MagicMock(return_value=mock_span)
    mock_context.__exit__ = MagicMock(return_value=None)
    mock_trace_operation = MagicMock(return_value=mock_context)
    monkeypatch.setattr(tracing_module, "trace_operation", mock_trace_operation)

    @trace_function("custom_span_name", {"attr": "value"})
    def test_function(arg1: str) -> str:
        return f"result: {arg1}"

    result = test_function("test_arg")

    assert result == "result: test_arg"
    mock_trace_operation.assert_called_once_with("custom_span_name", {"attr": "value"})
    mock_span.set_attribute.assert_any_call("function.name", "test_function")
    mock_span.set_attribute.assert_any_call("function.module", test_function.__module__)


def test_trace_template_render(monkeypatch):
    """Test template render tracing context manager."""
    mock_trace_operation = MagicMock()
    monkeypatch.setattr(tracing_module, "trace_operation", mock_trace_operation)

    with trace_template_render("map", "test.map"):
        pass

    expected_attributes = {
        "template.type": "map",
        "template.path": "test.map",
        "operation.category": "template_rendering",
    }
    mock_trace_operation.assert_called_once_with(
        "render_map_template", expected_attributes
    )


def test_trace_dataplane_operation(monkeypatch):
    """Test dataplane operation tracing context manager."""
    mock_trace_operation = MagicMock()
    monkeypatch.setattr(tracing_module, "trace_operation", mock_trace_operation)

    with trace_dataplane_operation("validate", "http://localhost:5555"):
        pass

    expected_attributes = {
        "dataplane.operation": "validate",
        "dataplane.instance_url": "http://localhost:5555",
        "operation.category": "dataplane_api",
    }
    mock_trace_operation.assert_called_once_with(
        "dataplane_validate", expected_attributes
    )


def test_trace_kubernetes_operation(monkeypatch):
    """Test Kubernetes operation tracing context manager."""
    mock_trace_operation = MagicMock()
    monkeypatch.setattr(tracing_module, "trace_operation", mock_trace_operation)

    with trace_kubernetes_operation("pods", "default", "test-pod"):
        pass

    expected_attributes = {
        "k8s.resource.type": "pods",
        "k8s.resource.namespace": "default",
        "k8s.resource.name": "test-pod",
        "operation.category": "kubernetes",
    }
    mock_trace_operation.assert_called_once_with(
        "k8s_pods_operation", expected_attributes
    )


def test_create_tracing_config_from_env_defaults(monkeypatch):
    """Test creating tracing config with default environment values."""
    # Clear environment variables
    for key in list(os.environ.keys()):
        if key.startswith(("TRACING_", "JAEGER_")):
            monkeypatch.delenv(key, raising=False)
    config = create_tracing_config_from_env()

    assert config.enabled is False
    assert config.service_name == "haproxy-template-ic"
    assert config.service_version == "1.0.0"
    assert config.jaeger_endpoint is None
    assert config.sample_rate == 1.0
    assert config.console_export is False


def test_create_tracing_config_from_env_custom(monkeypatch):
    """Test creating tracing config with custom environment values."""
    env_vars = {
        "TRACING_ENABLED": "true",
        "TRACING_SERVICE_NAME": "custom-service",
        "TRACING_SERVICE_VERSION": "2.0.0",
        "JAEGER_ENDPOINT": "jaeger:14268",
        "TRACING_SAMPLE_RATE": "0.5",
        "TRACING_CONSOLE_EXPORT": "true",
    }

    # Set environment variables
    for key, value in env_vars.items():
        monkeypatch.setenv(key, value)
    config = create_tracing_config_from_env()

    assert config.enabled is True
    assert config.service_name == "custom-service"
    assert config.service_version == "2.0.0"
    assert config.jaeger_endpoint == "jaeger:14268"
    assert config.sample_rate == 0.5
    assert config.console_export is True


@pytest.mark.asyncio
async def test_end_to_end_tracing_disabled():
    """Test end-to-end tracing workflow when disabled."""
    config = TracingConfig(enabled=False)
    initialize_tracing(config)

    @trace_async_function("test_operation")
    async def test_function():
        add_span_attributes(test="value")
        record_span_event("test_event")
        return "success"

    result = await test_function()
    assert result == "success"

    # Verify no tracer is available
    assert get_tracer() is None


@pytest.mark.asyncio
async def test_end_to_end_tracing_enabled(
    monkeypatch,
):
    """Test end-to-end tracing workflow when enabled."""
    config = TracingConfig(enabled=True)

    # Setup mocks
    mock_tracer_provider = MagicMock()
    mock_tracer = MagicMock()
    mock_tracer_provider_cls = MagicMock(return_value=mock_tracer_provider)
    mock_set_tracer_provider = MagicMock()

    # Mock instrumentors
    mock_httpx_instrumentor = MagicMock()
    mock_asyncio_instrumentor = MagicMock()
    mock_httpx_instr = MagicMock(return_value=mock_httpx_instrumentor)
    mock_asyncio_instr = MagicMock(return_value=mock_asyncio_instrumentor)

    # Apply patches
    monkeypatch.setattr(tracing_module, "TracerProvider", mock_tracer_provider_cls)
    monkeypatch.setattr(
        tracing_module.trace, "set_tracer_provider", mock_set_tracer_provider
    )
    monkeypatch.setattr(tracing_module, "HTTPXClientInstrumentor", mock_httpx_instr)
    monkeypatch.setattr(tracing_module, "AsyncioInstrumentor", mock_asyncio_instr)

    mock_get_tracer = MagicMock(return_value=mock_tracer)
    monkeypatch.setattr(tracing_module.trace, "get_tracer", mock_get_tracer)

    initialize_tracing(config)

    # Verify initialization
    assert get_tracing_manager() is not None
    mock_tracer_provider_cls.assert_called_once()
    mock_httpx_instrumentor.instrument.assert_called_once()
    mock_asyncio_instrumentor.instrument.assert_called_once()


def test_tracing_with_errors_handled_gracefully():
    """Test that tracing errors don't break application functionality."""
    config = TracingConfig(enabled=True, jaeger_endpoint="invalid:endpoint")

    # This should not raise an exception even with invalid endpoint
    initialize_tracing(config)

    # Application functionality should continue to work
    @trace_function("test_operation")
    def test_function():
        return "success"

    result = test_function()
    assert result == "success"
