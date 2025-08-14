"""
Prometheus metrics for HAProxy Template IC monitoring and observability.

This module provides comprehensive metrics collection for monitoring operator
performance, resource counts, operation timing, and error rates.
"""

import time
import logging
from contextlib import contextmanager
from typing import Any, Dict, Iterator, Optional
from functools import wraps

from prometheus_client import (
    Counter,
    Gauge,
    Histogram,
    Info,
    start_http_server,
    generate_latest,
)

logger = logging.getLogger(__name__)

# =============================================================================
# Metric Definitions
# =============================================================================

# Application info
app_info = Info(
    "haproxy_template_ic_info",
    "HAProxy Template IC application information",
)

# Resource counts
watched_resources_total = Gauge(
    "haproxy_template_ic_watched_resources_total",
    "Total number of watched Kubernetes resources",
    ["resource_type", "namespace"],
)

rendered_templates_total = Counter(
    "haproxy_template_ic_rendered_templates_total",
    "Total number of templates rendered",
    ["template_type", "status"],
)

# Operation timing
template_render_duration_seconds = Histogram(
    "haproxy_template_ic_template_render_duration_seconds",
    "Time spent rendering templates",
    ["template_type"],
    buckets=[0.001, 0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0],
)

config_reload_duration_seconds = Histogram(
    "haproxy_template_ic_config_reload_duration_seconds",
    "Time spent reloading configuration",
    buckets=[0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0, 25.0, 50.0],
)

dataplane_api_requests_total = Counter(
    "haproxy_template_ic_dataplane_api_requests_total",
    "Total number of Dataplane API requests",
    ["operation", "status"],
)

dataplane_api_duration_seconds = Histogram(
    "haproxy_template_ic_dataplane_api_duration_seconds",
    "Time spent on Dataplane API operations",
    ["operation"],
    buckets=[0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0],
)

# HAProxy instances
haproxy_instances_total = Gauge(
    "haproxy_template_ic_haproxy_instances_total",
    "Total number of discovered HAProxy instances",
    ["instance_type"],
)

# Errors and failures
errors_total = Counter(
    "haproxy_template_ic_errors_total",
    "Total number of errors",
    ["error_type", "component"],
)

# Configuration state
config_last_reload_timestamp = Gauge(
    "haproxy_template_ic_config_last_reload_timestamp",
    "Timestamp of last configuration reload",
)

config_last_success_timestamp = Gauge(
    "haproxy_template_ic_config_last_success_timestamp",
    "Timestamp of last successful configuration reload",
)

# Management socket connections
management_socket_connections_total = Counter(
    "haproxy_template_ic_management_socket_connections_total",
    "Total number of management socket connections",
)

management_socket_commands_total = Counter(
    "haproxy_template_ic_management_socket_commands_total",
    "Total number of management socket commands",
    ["command", "status"],
)


# =============================================================================
# Metric Collection Helpers
# =============================================================================


class MetricsCollector:
    """Centralized metrics collection for the HAProxy Template IC."""

    def __init__(self):
        """Initialize the metrics collector."""
        self.start_time = time.time()
        self._server_started = False

    def start_metrics_server(self, port: int = 9090) -> None:
        """Start the Prometheus metrics HTTP server."""
        if self._server_started:
            logger.warning("Metrics server already started")
            return

        try:
            start_http_server(port)
            self._server_started = True
            logger.info(f"📊 Metrics server started on port {port}")
        except Exception as e:
            logger.error(f"❌ Failed to start metrics server: {e}")

    def set_app_info(self, version: str = "development") -> None:
        """Set application information metrics."""
        app_info.info(
            {
                "version": version,
                "start_time": str(int(self.start_time)),
            }
        )

    def record_watched_resources(
        self, resources_by_type: Dict[str, Dict[str, Any]]
    ) -> None:
        """Record the count of watched resources by type."""
        # Clear existing gauges
        watched_resources_total.clear()

        for resource_type, resources in resources_by_type.items():
            namespace_counts: Dict[str, int] = {}

            for key, _ in resources.items():
                namespace: str = key[0]
                namespace_counts[namespace] = namespace_counts.get(namespace, 0) + 1

            for namespace, count in namespace_counts.items():
                watched_resources_total.labels(
                    resource_type=resource_type, namespace=namespace
                ).set(count)

    def record_template_render(
        self, template_type: str, status: str = "success"
    ) -> None:
        """Record a template rendering operation."""
        rendered_templates_total.labels(
            template_type=template_type, status=status
        ).inc()

    def record_haproxy_instances(
        self, production_count: int, validation_count: int
    ) -> None:
        """Record HAProxy instance counts."""
        haproxy_instances_total.labels(instance_type="production").set(production_count)
        haproxy_instances_total.labels(instance_type="validation").set(validation_count)

    def record_error(self, error_type: str, component: str) -> None:
        """Record an error occurrence."""
        errors_total.labels(error_type=error_type, component=component).inc()

    def record_config_reload(self, success: bool = True) -> None:
        """Record a configuration reload."""
        timestamp = time.time()
        config_last_reload_timestamp.set(timestamp)

        if success:
            config_last_success_timestamp.set(timestamp)

    def record_management_socket_connection(self) -> None:
        """Record a management socket connection."""
        management_socket_connections_total.inc()

    def record_management_socket_command(
        self, command: str, status: str = "success"
    ) -> None:
        """Record a management socket command."""
        management_socket_commands_total.labels(command=command, status=status).inc()

    def record_dataplane_api_request(
        self, operation: str, status: str = "success"
    ) -> None:
        """Record a Dataplane API request."""
        dataplane_api_requests_total.labels(operation=operation, status=status).inc()

    @contextmanager
    def time_template_render(self, template_type: str) -> Iterator[None]:
        """Context manager to time template rendering operations."""
        start_time = time.time()
        try:
            yield
        finally:
            duration = time.time() - start_time
            template_render_duration_seconds.labels(
                template_type=template_type
            ).observe(duration)

    @contextmanager
    def time_config_reload(self) -> Iterator[None]:
        """Context manager to time configuration reload operations."""
        start_time = time.time()
        try:
            yield
        finally:
            duration = time.time() - start_time
            config_reload_duration_seconds.observe(duration)

    @contextmanager
    def time_dataplane_api_operation(self, operation: str) -> Iterator[None]:
        """Context manager to time Dataplane API operations."""
        start_time = time.time()
        try:
            yield
        finally:
            duration = time.time() - start_time
            dataplane_api_duration_seconds.labels(operation=operation).observe(duration)


# =============================================================================
# Decorators
# =============================================================================


def timed_operation(metric_name: str, labels: Optional[Dict[str, str]] = None):
    """Decorator to time function execution and record in metrics."""

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                result = func(*args, **kwargs)
                return result
            finally:
                duration = time.time() - start_time
                if metric_name == "template_render":
                    template_type = (
                        labels.get("template_type", "unknown") if labels else "unknown"
                    )
                    template_render_duration_seconds.labels(
                        template_type=template_type
                    ).observe(duration)
                elif metric_name == "dataplane_api":
                    operation = (
                        labels.get("operation", "unknown") if labels else "unknown"
                    )
                    dataplane_api_duration_seconds.labels(operation=operation).observe(
                        duration
                    )

        return wrapper

    return decorator


# =============================================================================
# Global Metrics Instance
# =============================================================================

# Global metrics collector instance
metrics = MetricsCollector()


def get_metrics_collector() -> MetricsCollector:
    """Get the global metrics collector instance."""
    return metrics


def export_metrics() -> str:
    """Export current metrics in Prometheus format."""
    return generate_latest().decode("utf-8")
