"""
Tests for haproxy_template_ic.metrics module.

This module contains tests for Prometheus metrics collection functionality.
"""

import threading
import time
from unittest.mock import MagicMock

import pytest

import haproxy_template_ic.metrics as metrics_module
from haproxy_template_ic.metrics import (
    MetricsCollector,
    export_metrics,
    timed_operation,
)
from tests.unit.conftest import (
    create_metrics_collector_mock,
    mock_time_operations,
    assert_metrics_recorded,
)


def test_metrics_collector_initialization():
    """Test MetricsCollector initialization."""
    with mock_time_operations(fixed_time=1234567890.0):
        collector = MetricsCollector()

        assert collector.start_time > 0
        assert not collector._server_started


def test_set_app_info():
    """Test setting application information."""
    collector = create_metrics_collector_mock()

    collector.set_app_info("1.0.0")

    # Verify the method was called
    collector.set_app_info.assert_called_with("1.0.0")


def test_record_watched_resources():
    """Test recording watched resource counts."""
    collector = create_metrics_collector_mock()

    resources_by_type = {
        "ingresses": {
            ("default", "test-ingress"): {"metadata": {"name": "test-ingress"}},
            ("production", "prod-ingress"): {"metadata": {"name": "prod-ingress"}},
            ("default", "another-ingress"): {"metadata": {"name": "another-ingress"}},
        },
        "services": {
            ("default", "test-service"): {"metadata": {"name": "test-service"}},
        },
    }

    collector.record_watched_resources(resources_by_type)

    # Verify the method was called with the correct arguments
    collector.record_watched_resources.assert_called_with(resources_by_type)


def test_record_template_render():
    """Test recording template render operations."""
    collector = create_metrics_collector_mock()

    collector.record_template_render("map", "success")
    collector.record_template_render("haproxy_config", "error")

    # Verify metrics were recorded
    assert_metrics_recorded(collector, "template_render", expected_count=2)


def test_record_haproxy_instances():
    """Test recording HAProxy instance counts."""
    collector = create_metrics_collector_mock()

    collector.record_haproxy_instances(production_count=3, validation_count=1)

    # Verify the method was called with correct arguments
    collector.record_haproxy_instances.assert_called_with(
        production_count=3, validation_count=1
    )


def test_record_error():
    """Test recording error occurrences."""
    collector = create_metrics_collector_mock()

    collector.record_error("template_render_failed", "operator")
    collector.record_error("validation_failed", "dataplane")

    # Verify errors were recorded
    assert_metrics_recorded(collector, "error", expected_count=2)


def test_record_config_reload():
    """Test recording configuration reload operations."""
    collector = create_metrics_collector_mock()

    collector.record_config_reload(success=True)
    collector.record_config_reload(success=False)

    # Verify config reloads were recorded
    assert_metrics_recorded(collector, "config_reload", expected_count=2)


def test_record_dataplane_api_request():
    """Test recording Dataplane API requests."""
    collector = MetricsCollector()

    collector.record_dataplane_api_request("validate", "success")
    collector.record_dataplane_api_request("deploy", "error")

    # Should not raise any exceptions
    assert True


def test_time_template_render_context_manager():
    """Test template render timing context manager."""
    collector = MetricsCollector()

    with collector.time_template_render("map"):
        time.sleep(0.005)  # Simulate work

    # Should not raise any exceptions
    assert True


def test_time_config_reload_context_manager():
    """Test config reload timing context manager."""
    collector = MetricsCollector()

    with collector.time_config_reload():
        time.sleep(0.005)  # Simulate work

    # Should not raise any exceptions
    assert True


def test_time_dataplane_api_operation_context_manager():
    """Test Dataplane API operation timing context manager."""
    collector = MetricsCollector()

    with collector.time_dataplane_api_operation("validate"):
        time.sleep(0.005)  # Simulate work

    # Should not raise any exceptions
    assert True


@pytest.mark.asyncio
async def test_start_metrics_server_success(monkeypatch):
    """Test successful metrics server startup."""
    collector = MetricsCollector()

    async def mock_start_server(*args, **kwargs):
        return None

    mock_start_server = MagicMock(side_effect=mock_start_server)
    monkeypatch.setattr(metrics_module.aio.web, "start_http_server", mock_start_server)

    await collector.start_metrics_server(9090)

    mock_start_server.assert_called_once_with(port=9090)
    assert collector._server_started


@pytest.mark.asyncio
async def test_start_metrics_server_already_started(monkeypatch):
    """Test starting metrics server when already started."""
    collector = MetricsCollector()
    collector._server_started = True
    mock_start_server = MagicMock()
    monkeypatch.setattr(metrics_module.aio.web, "start_http_server", mock_start_server)

    await collector.start_metrics_server(9090)

    mock_start_server.assert_not_called()


@pytest.mark.asyncio
async def test_start_metrics_server_failure(monkeypatch):
    """Test metrics server startup failure."""
    collector = MetricsCollector()

    async def mock_start_server(*args, **kwargs):
        raise Exception("Port already in use")

    mock_start_server = MagicMock(side_effect=mock_start_server)
    monkeypatch.setattr(metrics_module.aio.web, "start_http_server", mock_start_server)

    await collector.start_metrics_server(9090)

    mock_start_server.assert_called_once_with(port=9090)
    assert not collector._server_started


def test_timed_operation_template_render():
    """Test timing decorator for template render operations."""

    @timed_operation("template_render", {"template_type": "map"})
    def render_template():
        time.sleep(0.01)
        return "rendered content"

    result = render_template()

    assert result == "rendered content"


def test_timed_operation_dataplane_api():
    """Test timing decorator for Dataplane API operations."""

    @timed_operation("dataplane_api", {"operation": "validate"})
    def api_call():
        time.sleep(0.01)
        return {"status": "success"}

    result = api_call()

    assert result == {"status": "success"}


def test_timed_operation_with_exception():
    """Test timing decorator when function raises exception."""

    @timed_operation("template_render", {"template_type": "test"})
    def failing_function():
        time.sleep(0.01)
        raise ValueError("Test error")

    with pytest.raises(ValueError, match="Test error"):
        failing_function()


def test_export_metrics():
    """Test exporting metrics in Prometheus format."""
    metrics_output = export_metrics()

    assert isinstance(metrics_output, str)
    assert len(metrics_output) > 0


def test_complete_workflow_metrics():
    """Test a complete workflow with various metrics recording."""
    collector = MetricsCollector()

    # Simulate a complete operator workflow
    collector.set_app_info("test-version")

    # Simulate watched resources
    resources = {
        "ingresses": {
            ("default", "test"): {"metadata": {"name": "test"}},
        }
    }
    collector.record_watched_resources(resources)

    # Simulate template rendering
    with collector.time_template_render("haproxy_config"):
        time.sleep(0.0005)
    collector.record_template_render("haproxy_config", "success")

    # Simulate Dataplane API operations
    with collector.time_dataplane_api_operation("validate"):
        time.sleep(0.0005)
    collector.record_dataplane_api_request("validate", "success")

    # Simulate HAProxy instances
    collector.record_haproxy_instances(2, 1)

    # Simulate configuration reload
    with collector.time_config_reload():
        time.sleep(0.0005)
    collector.record_config_reload(success=True)

    # Management socket functionality has been removed
    # collector.record_management_socket_connection()
    # collector.record_management_socket_command("dump_all", "success")

    # Should complete without errors
    assert True


def test_error_scenarios_metrics():
    """Test metrics recording for various error scenarios."""
    collector = MetricsCollector()

    # Template render errors
    collector.record_template_render("map", "error")
    collector.record_error("template_render_failed", "operator")

    # Dataplane API errors
    collector.record_dataplane_api_request("deploy", "error")
    collector.record_error("dataplane_deploy_failed", "dataplane")

    # Configuration errors
    collector.record_config_reload(success=False)
    collector.record_error("config_load_failed", "operator")

    # Management socket functionality has been removed
    # collector.record_management_socket_command("invalid", "error")

    # Should complete without errors
    assert True


def test_concurrent_metrics_recording():
    """Test that metrics recording is thread-safe."""

    collector = MetricsCollector()

    def record_metrics():
        for _ in range(10):
            collector.record_template_render("test", "success")
            collector.record_dataplane_api_request("test", "success")
            collector.record_error("test", "test")

    threads = []
    for _ in range(5):
        thread = threading.Thread(target=record_metrics)
        threads.append(thread)
        thread.start()

    for thread in threads:
        thread.join()

    # Should complete without errors
    assert True
