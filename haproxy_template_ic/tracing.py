"""
Distributed tracing functionality for HAProxy Template IC.

This module provides OpenTelemetry-based distributed tracing to enable
end-to-end observability across the entire template rendering and deployment
pipeline. It includes automatic instrumentation for async operations, HTTP
requests, and custom business logic spans.
"""

import functools
import os
from contextlib import contextmanager
from typing import Any, Dict, Optional, Iterator, Callable, TypeVar, Awaitable
from dataclasses import dataclass

from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor, ConsoleSpanExporter
from opentelemetry.exporter.jaeger.thrift import JaegerExporter
from opentelemetry.instrumentation.httpx import HTTPXClientInstrumentor
from opentelemetry.instrumentation.asyncio import AsyncioInstrumentor
from opentelemetry.sdk.resources import Resource
from opentelemetry.semconv.resource import ResourceAttributes
from opentelemetry.trace import Status, StatusCode

import structlog

from haproxy_template_ic.core.error_handling import handle_exceptions

logger = structlog.get_logger(__name__)

F = TypeVar("F", bound=Callable[..., Any])
AsyncF = TypeVar("AsyncF", bound=Callable[..., Awaitable[Any]])


@dataclass
class TracingConfig:
    """Configuration for distributed tracing."""

    enabled: bool = False
    service_name: str = "haproxy-template-ic"
    service_version: str = "1.0.0"
    jaeger_endpoint: Optional[str] = None
    sample_rate: float = 1.0
    console_export: bool = False


class TracingManager:
    """Manages OpenTelemetry tracing configuration and lifecycle."""

    def __init__(self, config: TracingConfig):
        self.config = config
        self.tracer_provider: Optional[TracerProvider] = None
        self.tracer: Optional[trace.Tracer] = None
        self._instrumented = False

    def initialize(self) -> None:
        """Initialize distributed tracing with configured exporters."""
        if not self.config.enabled:
            logger.info("Distributed tracing is disabled")
            return

        logger.info(
            "Initializing distributed tracing",
            service_name=self.config.service_name,
            jaeger_endpoint=self.config.jaeger_endpoint,
        )

        # Create resource with service metadata
        resource = Resource.create(
            {
                ResourceAttributes.SERVICE_NAME: self.config.service_name,
                ResourceAttributes.SERVICE_VERSION: self.config.service_version,
                ResourceAttributes.SERVICE_INSTANCE_ID: os.getenv(
                    "HOSTNAME", "unknown"
                ),
            }
        )

        # Configure tracer provider
        self.tracer_provider = TracerProvider(resource=resource)
        trace.set_tracer_provider(self.tracer_provider)

        # Add span processors/exporters
        self._configure_exporters()

        # Get tracer instance
        self.tracer = trace.get_tracer(__name__)

        # Auto-instrument libraries
        self._setup_auto_instrumentation()

        logger.info("Distributed tracing initialized successfully")

    def _configure_exporters(self) -> None:
        """Configure span exporters based on configuration."""
        if not self.tracer_provider:
            return

        # Console exporter for development
        if self.config.console_export:
            console_exporter = ConsoleSpanExporter()
            console_processor = BatchSpanProcessor(console_exporter)
            self.tracer_provider.add_span_processor(console_processor)
            logger.debug("Added console span exporter")

        # Jaeger exporter for production
        if self.config.jaeger_endpoint:
            self._setup_jaeger_exporter()

    @handle_exceptions(logger=logger, context="jaeger exporter configuration")
    def _setup_jaeger_exporter(self) -> None:
        """Set up Jaeger exporter with error handling."""
        if not self.config.jaeger_endpoint:
            return

        jaeger_endpoint = self.config.jaeger_endpoint
        jaeger_exporter = JaegerExporter(
            agent_host_name=jaeger_endpoint.split(":")[0],
            agent_port=int(jaeger_endpoint.split(":")[1])
            if ":" in jaeger_endpoint
            else 14268,
        )
        jaeger_processor = BatchSpanProcessor(jaeger_exporter)
        if self.tracer_provider:
            self.tracer_provider.add_span_processor(jaeger_processor)
        logger.info("Added Jaeger span exporter", endpoint=jaeger_endpoint)

    @handle_exceptions(logger=logger, context="auto-instrumentation setup")
    def _setup_auto_instrumentation(self) -> None:
        """Set up automatic instrumentation for common libraries."""
        if self._instrumented:
            return

        # Instrument HTTPX for Dataplane API calls
        HTTPXClientInstrumentor().instrument()
        logger.debug("HTTPX instrumentation enabled")

        # Instrument asyncio for async operation tracing
        AsyncioInstrumentor().instrument()
        logger.debug("Asyncio instrumentation enabled")

        self._instrumented = True

    @handle_exceptions(logger=logger, context="tracing shutdown")
    def shutdown(self) -> None:
        """Shutdown tracing and flush any pending spans."""
        if self.tracer_provider:
            self.tracer_provider.shutdown()
            logger.info("Distributed tracing shutdown complete")


# Global tracing manager instance
_tracing_manager: Optional[TracingManager] = None


def get_tracing_manager() -> Optional[TracingManager]:
    """Get the global tracing manager instance."""
    return _tracing_manager


def initialize_tracing(config: TracingConfig) -> None:
    """Initialize global tracing with configuration."""
    global _tracing_manager
    _tracing_manager = TracingManager(config)
    _tracing_manager.initialize()


def get_tracer() -> Optional[trace.Tracer]:
    """Get the configured tracer instance."""
    if _tracing_manager and _tracing_manager.tracer:
        return _tracing_manager.tracer
    return None


@contextmanager
def trace_operation(
    operation_name: str,
    attributes: Optional[Dict[str, Any]] = None,
    set_status_on_exception: bool = True,
) -> Iterator[Optional[trace.Span]]:
    """Context manager for tracing operations with error handling."""
    tracer = get_tracer()
    if not tracer:
        yield None
        return

    with tracer.start_as_current_span(operation_name) as span:
        try:
            # Add custom attributes
            if attributes:
                for key, value in attributes.items():
                    span.set_attribute(str(key), str(value))

            yield span

        except Exception as e:
            if set_status_on_exception:
                span.set_status(Status(StatusCode.ERROR, str(e)))
                span.record_exception(e)
            raise


def trace_async_function(
    span_name: Optional[str] = None, attributes: Optional[Dict[str, Any]] = None
) -> Callable[[AsyncF], AsyncF]:
    """Decorator for tracing async functions."""

    def decorator(func: AsyncF) -> AsyncF:
        operation_name = span_name or f"{func.__module__}.{func.__name__}"

        @functools.wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            with trace_operation(operation_name, attributes) as span:
                if span:
                    # Add function metadata
                    span.set_attribute("function.name", func.__name__)
                    span.set_attribute("function.module", func.__module__)

                return await func(*args, **kwargs)

        return wrapper  # type: ignore[return-value]

    return decorator


def trace_function(
    span_name: Optional[str] = None, attributes: Optional[Dict[str, Any]] = None
) -> Callable[[F], F]:
    """Decorator for tracing synchronous functions."""

    def decorator(func: F) -> F:
        operation_name = span_name or f"{func.__module__}.{func.__name__}"

        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            with trace_operation(operation_name, attributes) as span:
                if span:
                    # Add function metadata
                    span.set_attribute("function.name", func.__name__)
                    span.set_attribute("function.module", func.__module__)

                return func(*args, **kwargs)

        return wrapper  # type: ignore[return-value]

    return decorator


def add_span_attributes(**attributes: Any) -> None:
    """Add attributes to the current active span."""
    current_span = trace.get_current_span()
    if current_span and current_span.is_recording():
        for key, value in attributes.items():
            current_span.set_attribute(str(key), str(value))


def record_span_event(name: str, attributes: Optional[Dict[str, Any]] = None) -> None:
    """Record an event on the current active span."""
    current_span = trace.get_current_span()
    if current_span and current_span.is_recording():
        current_span.add_event(name, attributes or {})


def set_span_error(error: Exception, description: Optional[str] = None) -> None:
    """Mark the current span as having an error."""
    current_span = trace.get_current_span()
    if current_span and current_span.is_recording():
        current_span.set_status(Status(StatusCode.ERROR, description or str(error)))
        current_span.record_exception(error)


# Convenience context managers for common operations
@contextmanager
def trace_template_render(
    template_type: str, template_path: str = ""
) -> Iterator[None]:
    """Context manager for tracing template rendering operations."""
    attributes = {
        "template.type": template_type,
        "template.path": template_path,
        "operation.category": "template_rendering",
    }

    with trace_operation(f"render_{template_type}_template", attributes):
        yield


@contextmanager
def trace_dataplane_operation(operation: str, instance_url: str = "") -> Iterator[None]:
    """Context manager for tracing Dataplane API operations."""
    attributes = {
        "dataplane.operation": operation,
        "dataplane.instance_url": instance_url,
        "operation.category": "dataplane_api",
    }

    with trace_operation(f"dataplane_{operation}", attributes):
        yield


@contextmanager
def trace_kubernetes_operation(
    resource_type: str, namespace: str = "", name: str = ""
) -> Iterator[None]:
    """Context manager for tracing Kubernetes operations."""
    attributes = {
        "k8s.resource.type": resource_type,
        "k8s.resource.namespace": namespace,
        "k8s.resource.name": name,
        "operation.category": "kubernetes",
    }

    with trace_operation(f"k8s_{resource_type}_operation", attributes):
        yield


def create_tracing_config_from_env() -> TracingConfig:
    """Create tracing configuration from environment variables."""
    return TracingConfig(
        enabled=os.getenv("TRACING_ENABLED", "false").lower() == "true",
        service_name=os.getenv("TRACING_SERVICE_NAME", "haproxy-template-ic"),
        service_version=os.getenv("TRACING_SERVICE_VERSION", "1.0.0"),
        jaeger_endpoint=os.getenv("JAEGER_ENDPOINT"),
        sample_rate=float(os.getenv("TRACING_SAMPLE_RATE", "1.0")),
        console_export=os.getenv("TRACING_CONSOLE_EXPORT", "false").lower() == "true",
    )


# Cleanup function for graceful shutdown
def shutdown_tracing() -> None:
    """Shutdown distributed tracing."""
    if _tracing_manager:
        _tracing_manager.shutdown()
