"""
Prometheus metrics for HAProxy Template IC monitoring and observability.

This module provides comprehensive metrics collection for monitoring operator
performance, resource counts, operation timing, and error rates.
"""

import logging
import time
from contextlib import contextmanager
from functools import wraps
from typing import Any, Callable, Dict, Iterator, List, Optional, Tuple, TypeVar, cast

from prometheus_async import aio
from prometheus_client import (
    Counter,
    Gauge,
    Histogram,
    Info,
    generate_latest,
)

from haproxy_template_ic.constants import DEFAULT_METRICS_PORT
from haproxy_template_ic.core.error_handling import handle_exceptions

F = TypeVar("F", bound=Callable[..., Any])

logger = logging.getLogger(__name__)

# Metric Definitions

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

dataplane_fallback_deployments_total = Counter(
    "haproxy_template_ic_dataplane_fallback_deployments_total",
    "Total number of fallback deployments when structured approach fails",
    ["fallback_type"],
)

dataplane_granular_deployments_total = Counter(
    "haproxy_template_ic_dataplane_granular_deployments_total",
    "Total number of successful granular deployments using specific API endpoints",
    ["deployment_method"],
)

dataplane_deployment_methods_total = Counter(
    "haproxy_template_ic_dataplane_deployment_methods_total",
    "Total deployments by method (granular, raw, conditional, fallback)",
    ["method", "success"],
)

# HAProxy instances
haproxy_instances_total = Gauge(
    "haproxy_template_ic_haproxy_instances_total",
    "Total number of discovered HAProxy instances",
    ["instance_type"],
)

haproxy_sync_results_total = Counter(
    "haproxy_template_ic_haproxy_sync_results_total",
    "Total HAProxy synchronization results",
    ["result"],  # "success" or "failure"
)

# Webhook validation metrics
webhook_requests_total = Counter(
    "haproxy_template_ic_webhook_requests_total",
    "Total number of webhook validation requests",
    ["status"],
)

webhook_request_duration_seconds = Histogram(
    "haproxy_template_ic_webhook_request_duration_seconds",
    "Time spent processing webhook validation requests",
    buckets=[0.001, 0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0],
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

# Template debouncer metrics
debouncer_triggers_total = Counter(
    "haproxy_template_ic_debouncer_triggers_total",
    "Total number of debouncer trigger events",
)

debouncer_renders_total = Counter(
    "haproxy_template_ic_debouncer_renders_total",
    "Total number of template renders triggered by debouncer",
    ["trigger_type"],  # "resource_changes" or "periodic_refresh"
)

debouncer_batched_changes = Histogram(
    "haproxy_template_ic_debouncer_batched_changes",
    "Number of changes batched per render",
    buckets=[1, 2, 5, 10, 20, 50, 100, 200, 500, 1000],
)

debouncer_time_since_last_render = Gauge(
    "haproxy_template_ic_debouncer_time_since_last_render_seconds",
    "Time since last template render in seconds",
)


# Metric Collection Helpers


class MetricsCollector:
    """Centralized metrics collection for the HAProxy Template IC."""

    def __init__(self):
        """Initialize the metrics collector."""
        self.start_time = time.time()
        self._server_started = False

    @handle_exceptions(logger=logger, context="metrics server startup")
    async def start_metrics_server(self, port: int = DEFAULT_METRICS_PORT) -> None:
        """Start the Prometheus metrics HTTP server using asyncio."""
        if self._server_started:
            logger.warning("Metrics server already started")
            return

        await aio.web.start_http_server(port=port)
        self._server_started = True
        logger.info(f"📊 Metrics server started on port {port}")

    @handle_exceptions(logger=logger, context="metrics server shutdown")
    async def stop_metrics_server(self) -> None:
        """Stop the Prometheus metrics HTTP server."""
        if not self._server_started:
            logger.debug("Metrics server not running, nothing to stop")
            return

        # Note: prometheus_async doesn't provide a direct stop method
        # The server will be stopped when the event loop shuts down
        self._server_started = False
        logger.debug("📊 Metrics server stopped")

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
            # Also store in history for sparklines
            _metrics_history.add_template_render_time(duration)

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
            # Also store in history for sparklines
            _metrics_history.add_dataplane_api_time(duration)

    def increment_dataplane_fallback(self, fallback_type: str) -> None:
        """Increment the counter for dataplane deployment fallbacks.

        Args:
            fallback_type: Type of fallback (e.g., 'structured_to_conditional', 'conditional_to_regular')
        """
        dataplane_fallback_deployments_total.labels(fallback_type=fallback_type).inc()

    def increment_dataplane_granular_success(self, method: str = "granular") -> None:
        """Increment the counter for successful granular deployments.

        Args:
            method: The granular deployment method used (default: 'granular')
        """
        dataplane_granular_deployments_total.labels(deployment_method=method).inc()
        dataplane_deployment_methods_total.labels(method=method, success="true").inc()

    def increment_dataplane_granular_fallback(self) -> None:
        """Increment the counter when granular deployments fall back to raw."""
        dataplane_deployment_methods_total.labels(
            method="granular", success="false"
        ).inc()

    def record_dataplane_deployment_method(
        self, method: str, success: bool = True
    ) -> None:
        """Record a dataplane deployment by method.

        Args:
            method: Deployment method ('granular', 'raw', 'conditional', 'fallback', 'skipped')
            success: Whether the deployment was successful
        """
        success_str = "true" if success else "false"
        dataplane_deployment_methods_total.labels(
            method=method, success=success_str
        ).inc()
        # Also record sync result in history for dashboard sparklines
        _metrics_history.add_sync_result(success)

    def record_debouncer_trigger(self) -> None:
        """Record a debouncer trigger event."""
        debouncer_triggers_total.inc()

    def record_debouncer_render(self, trigger_type: str, changes_batched: int) -> None:
        """Record a template render triggered by the debouncer.

        Args:
            trigger_type: "resource_changes" or "periodic_refresh"
            changes_batched: Number of changes batched in this render
        """
        debouncer_renders_total.labels(trigger_type=trigger_type).inc()
        if changes_batched > 0:
            debouncer_batched_changes.observe(changes_batched)

    def update_debouncer_last_render_time(self, time_since_last_render: float) -> None:
        """Update the time since last render gauge.

        Args:
            time_since_last_render: Seconds since last render
        """
        debouncer_time_since_last_render.set(time_since_last_render)

    def record_haproxy_sync(self, successful_count: int, failed_count: int) -> None:
        """Record HAProxy synchronization results.

        Args:
            successful_count: Number of successful synchronizations
            failed_count: Number of failed synchronizations
        """
        if successful_count > 0:
            haproxy_sync_results_total.labels(result="success").inc(successful_count)
        if failed_count > 0:
            haproxy_sync_results_total.labels(result="failure").inc(failed_count)

    @contextmanager
    def time_webhook_request(self) -> Iterator[None]:
        """Context manager to time webhook validation requests."""
        start_time = time.time()
        try:
            yield
            # Record success
            webhook_requests_total.labels(status="success").inc()
        except Exception:
            # Record failure
            webhook_requests_total.labels(status="failure").inc()
            raise
        finally:
            duration = time.time() - start_time
            webhook_request_duration_seconds.observe(duration)


# Decorators


def timed_operation(
    metric_name: str, labels: Optional[Dict[str, str]] = None
) -> Callable[[F], F]:
    """Decorator to time function execution and record in metrics."""

    def decorator(func: F) -> F:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
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

        return cast(F, wrapper)

    return decorator


# Global Metrics Instance

# Global metrics collector instance
metrics = MetricsCollector()


def get_metrics_collector() -> MetricsCollector:
    """Get the global metrics collector instance."""
    return metrics


def export_metrics() -> str:
    """Export current metrics in Prometheus format."""
    return generate_latest().decode("utf-8")


@handle_exceptions(
    logger=logger, default_return={}, context="histogram percentiles calculation"
)
def calculate_histogram_percentiles(
    histogram, percentiles: list = [50, 95, 99]
) -> Dict[str, Any]:
    """Calculate approximate percentiles from a Prometheus histogram.

    Args:
        histogram: Prometheus Histogram metric
        percentiles: List of percentiles to calculate (e.g., [50, 95, 99])

    Returns:
        Dictionary mapping percentile keys (e.g., 'p50', 'p95', 'p99') to values in milliseconds
    """
    result = {}

    # Get all samples from the histogram
    samples = []
    for sample in histogram.collect():
        for metric in sample.samples:
            if metric.name.endswith("_bucket"):
                # Extract bucket upper bound and count
                le = metric.labels.get("le", "")
                if le and le != "+Inf":
                    try:
                        bucket_upper_bound = float(le)
                        count = metric.value
                        samples.append((bucket_upper_bound, count))
                    except ValueError:
                        continue

    if not samples:
        # No samples, return N/A for all percentiles
        return {f"p{p}": "N/A" for p in percentiles}

    # Sort by bucket upper bound
    samples.sort(key=lambda x: x[0])

    # Calculate total count
    total_count = max(count for _, count in samples) if samples else 0

    for percentile in percentiles:
        target_count = (percentile / 100.0) * total_count

        # Find the bucket that contains this percentile
        percentile_value = 0.0

        for i, (bucket_bound, count) in enumerate(samples):
            cumulative_count = count

            if cumulative_count >= target_count:
                # Found the bucket containing the percentile
                if i == 0:
                    # First bucket, use simple estimate
                    percentile_value = bucket_bound * (target_count / cumulative_count)
                else:
                    # Linear interpolation between buckets
                    prev_bound, prev_count = samples[i - 1]
                    ratio = (target_count - prev_count) / (
                        cumulative_count - prev_count
                    )
                    percentile_value = prev_bound + ratio * (bucket_bound - prev_bound)
                break
        else:
            # If we get here, use the highest bucket
            percentile_value = samples[-1][0] if samples else 0.0

        # Convert from seconds to milliseconds and round
        result[f"p{percentile}"] = round(percentile_value * 1000, 1)

    return result


@handle_exceptions(
    logger=logger, default_return={}, context="performance metrics calculation"
)
def get_performance_metrics() -> Dict[str, Any]:
    """Get performance metrics for dashboard display.

    Returns:
        Dictionary containing template_render, dataplane_api, and sync_success_rate metrics with historical data
    """
    performance: Dict[str, Any] = {}

    # Template render metrics
    template_percentiles = calculate_histogram_percentiles(
        template_render_duration_seconds
    )
    if template_percentiles:
        template_render_data = template_percentiles.copy()
        # Add historical data for sparklines
        template_render_data["history"] = _metrics_history.get_template_render_values()
        performance["template_render"] = template_render_data

    # Dataplane API metrics
    api_percentiles = calculate_histogram_percentiles(dataplane_api_duration_seconds)
    if api_percentiles:
        dataplane_api_data = api_percentiles.copy()
        # Add historical data for sparklines
        dataplane_api_data["history"] = _metrics_history.get_dataplane_api_values()
        performance["dataplane_api"] = dataplane_api_data

    # Add sync pattern and recent success rate from history
    sync_pattern = _metrics_history.get_sync_success_pattern()
    if sync_pattern:
        performance["sync_pattern"] = sync_pattern
        performance["recent_sync_success_rate"] = (
            _metrics_history.get_recent_sync_success_rate()
        )

    return performance


class MetricsHistory:
    """Store rolling buffer of metrics data for sparkline visualization."""

    def __init__(self, max_samples: int = 30):
        """Initialize with maximum number of samples to store."""
        self.max_samples = max_samples
        self.template_render_times: List[
            Tuple[float, float]
        ] = []  # List of (timestamp, duration_ms)
        self.dataplane_api_times: List[
            Tuple[float, float]
        ] = []  # List of (timestamp, duration_ms)
        self.sync_results: List[
            Tuple[float, bool]
        ] = []  # List of (timestamp, success_boolean)

    def add_template_render_time(self, duration_seconds: float) -> None:
        """Add template render time sample."""
        timestamp = time.time()
        duration_ms = duration_seconds * 1000  # Convert to milliseconds
        self._add_sample(self.template_render_times, timestamp, duration_ms)

    def add_dataplane_api_time(self, duration_seconds: float) -> None:
        """Add dataplane API time sample."""
        timestamp = time.time()
        duration_ms = duration_seconds * 1000  # Convert to milliseconds
        self._add_sample(self.dataplane_api_times, timestamp, duration_ms)

    def add_sync_result(self, success: bool) -> None:
        """Add sync success/failure result."""
        timestamp = time.time()
        self._add_sample(self.sync_results, timestamp, success)

    def _add_sample(self, buffer: list, timestamp: float, value) -> None:
        """Add sample to buffer and maintain max size."""
        buffer.append((timestamp, value))
        if len(buffer) > self.max_samples:
            buffer.pop(0)  # Remove oldest sample

    def get_template_render_values(self) -> list:
        """Get template render durations for sparkline."""
        return [duration for _, duration in self.template_render_times]

    def get_dataplane_api_values(self) -> list:
        """Get dataplane API durations for sparkline."""
        return [duration for _, duration in self.dataplane_api_times]

    def get_sync_success_pattern(self) -> str:
        """Get sync success/failure pattern as string of symbols."""
        if not self.sync_results:
            return ""

        pattern = ""
        for _, success in self.sync_results[-20:]:  # Last 20 results
            pattern += "▲" if success else "▼"
        return pattern

    def get_recent_sync_success_rate(self) -> float:
        """Calculate success rate from recent samples."""
        if not self.sync_results:
            return 0.0

        recent_results = [success for _, success in self.sync_results[-10:]]  # Last 10
        if not recent_results:
            return 0.0

        success_count = sum(recent_results)
        return success_count / len(recent_results)


# Global metrics history instance
_metrics_history = MetricsHistory()


def get_metrics_history() -> MetricsHistory:
    """Get the global metrics history instance."""
    return _metrics_history
