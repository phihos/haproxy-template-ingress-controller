"""
Tests for haproxy_template_ic.metrics module.

This module contains tests for Prometheus metrics collection functionality.
"""

import time
from unittest.mock import patch

import pytest

from haproxy_template_ic.metrics import (
    MetricsCollector,
    get_metrics_collector,
    export_metrics,
    timed_operation,
)


class TestMetricsCollector:
    """Test cases for MetricsCollector class."""

    def test_metrics_collector_initialization(self):
        """Test MetricsCollector initialization."""
        collector = MetricsCollector()

        assert collector.start_time > 0
        assert not collector._server_started

    def test_set_app_info(self):
        """Test setting application information."""
        collector = MetricsCollector()

        collector.set_app_info("1.0.0")

        # Should not raise any exceptions
        assert True

    def test_record_watched_resources(self):
        """Test recording watched resource counts."""
        collector = MetricsCollector()

        resources_by_type = {
            "ingresses": {
                ("default", "test-ingress"): {"metadata": {"name": "test-ingress"}},
                ("production", "prod-ingress"): {"metadata": {"name": "prod-ingress"}},
                ("default", "another-ingress"): {
                    "metadata": {"name": "another-ingress"}
                },
            },
            "services": {
                ("default", "test-service"): {"metadata": {"name": "test-service"}},
            },
        }

        collector.record_watched_resources(resources_by_type)

        # Should not raise any exceptions
        assert True

    def test_record_template_render(self):
        """Test recording template render operations."""
        collector = MetricsCollector()

        collector.record_template_render("map", "success")
        collector.record_template_render("haproxy_config", "error")

        # Should not raise any exceptions
        assert True

    def test_record_haproxy_instances(self):
        """Test recording HAProxy instance counts."""
        collector = MetricsCollector()

        collector.record_haproxy_instances(production_count=3, validation_count=1)

        # Should not raise any exceptions
        assert True

    def test_record_error(self):
        """Test recording error occurrences."""
        collector = MetricsCollector()

        collector.record_error("template_render_failed", "operator")
        collector.record_error("validation_failed", "dataplane")

        # Should not raise any exceptions
        assert True

    def test_record_config_reload(self):
        """Test recording configuration reload operations."""
        collector = MetricsCollector()

        collector.record_config_reload(success=True)
        collector.record_config_reload(success=False)

        # Should not raise any exceptions
        assert True

    def test_record_management_socket_operations(self):
        """Test recording management socket operations."""
        collector = MetricsCollector()

        collector.record_management_socket_connection()
        collector.record_management_socket_command("dump_all", "success")
        collector.record_management_socket_command("invalid", "error")

        # Should not raise any exceptions
        assert True

    def test_record_dataplane_api_request(self):
        """Test recording Dataplane API requests."""
        collector = MetricsCollector()

        collector.record_dataplane_api_request("validate", "success")
        collector.record_dataplane_api_request("deploy", "error")

        # Should not raise any exceptions
        assert True

    def test_time_template_render_context_manager(self):
        """Test template render timing context manager."""
        collector = MetricsCollector()

        with collector.time_template_render("map"):
            time.sleep(0.01)  # Simulate work

        # Should not raise any exceptions
        assert True

    def test_time_config_reload_context_manager(self):
        """Test config reload timing context manager."""
        collector = MetricsCollector()

        with collector.time_config_reload():
            time.sleep(0.01)  # Simulate work

        # Should not raise any exceptions
        assert True

    def test_time_dataplane_api_operation_context_manager(self):
        """Test Dataplane API operation timing context manager."""
        collector = MetricsCollector()

        with collector.time_dataplane_api_operation("validate"):
            time.sleep(0.01)  # Simulate work

        # Should not raise any exceptions
        assert True

    @patch("haproxy_template_ic.metrics.start_http_server")
    def test_start_metrics_server_success(self, mock_start_server):
        """Test successful metrics server startup."""
        collector = MetricsCollector()

        collector.start_metrics_server(9090)

        mock_start_server.assert_called_once_with(9090)
        assert collector._server_started

    @patch("haproxy_template_ic.metrics.start_http_server")
    def test_start_metrics_server_already_started(self, mock_start_server):
        """Test starting metrics server when already started."""
        collector = MetricsCollector()
        collector._server_started = True

        collector.start_metrics_server(9090)

        mock_start_server.assert_not_called()

    @patch("haproxy_template_ic.metrics.start_http_server")
    def test_start_metrics_server_failure(self, mock_start_server):
        """Test metrics server startup failure."""
        collector = MetricsCollector()
        mock_start_server.side_effect = Exception("Port already in use")

        collector.start_metrics_server(9090)

        mock_start_server.assert_called_once_with(9090)
        assert not collector._server_started


class TestTimedOperationDecorator:
    """Test cases for the timed_operation decorator."""

    def test_timed_operation_template_render(self):
        """Test timing decorator for template render operations."""

        @timed_operation("template_render", {"template_type": "map"})
        def render_template():
            time.sleep(0.01)
            return "rendered content"

        result = render_template()

        assert result == "rendered content"

    def test_timed_operation_dataplane_api(self):
        """Test timing decorator for Dataplane API operations."""

        @timed_operation("dataplane_api", {"operation": "validate"})
        def api_call():
            time.sleep(0.01)
            return {"status": "success"}

        result = api_call()

        assert result == {"status": "success"}

    def test_timed_operation_with_exception(self):
        """Test timing decorator when function raises exception."""

        @timed_operation("template_render", {"template_type": "test"})
        def failing_function():
            time.sleep(0.01)
            raise ValueError("Test error")

        with pytest.raises(ValueError, match="Test error"):
            failing_function()


class TestGlobalMetricsInstance:
    """Test cases for global metrics functionality."""

    def test_get_metrics_collector(self):
        """Test getting the global metrics collector instance."""
        collector1 = get_metrics_collector()
        collector2 = get_metrics_collector()

        assert collector1 is collector2  # Should be the same instance

    def test_export_metrics(self):
        """Test exporting metrics in Prometheus format."""
        metrics_output = export_metrics()

        assert isinstance(metrics_output, str)
        assert len(metrics_output) > 0


class TestMetricsIntegration:
    """Integration tests for metrics functionality."""

    def test_complete_workflow_metrics(self):
        """Test a complete workflow with various metrics recording."""
        collector = get_metrics_collector()

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
            time.sleep(0.001)
        collector.record_template_render("haproxy_config", "success")

        # Simulate Dataplane API operations
        with collector.time_dataplane_api_operation("validate"):
            time.sleep(0.001)
        collector.record_dataplane_api_request("validate", "success")

        # Simulate HAProxy instances
        collector.record_haproxy_instances(2, 1)

        # Simulate configuration reload
        with collector.time_config_reload():
            time.sleep(0.001)
        collector.record_config_reload(success=True)

        # Simulate management socket activity
        collector.record_management_socket_connection()
        collector.record_management_socket_command("dump_all", "success")

        # Should complete without errors
        assert True

    def test_error_scenarios_metrics(self):
        """Test metrics recording for various error scenarios."""
        collector = get_metrics_collector()

        # Template render errors
        collector.record_template_render("map", "error")
        collector.record_error("template_render_failed", "operator")

        # Dataplane API errors
        collector.record_dataplane_api_request("deploy", "error")
        collector.record_error("dataplane_deploy_failed", "dataplane")

        # Configuration errors
        collector.record_config_reload(success=False)
        collector.record_error("config_load_failed", "operator")

        # Management socket errors
        collector.record_management_socket_command("invalid", "error")

        # Should complete without errors
        assert True

    def test_concurrent_metrics_recording(self):
        """Test that metrics recording is thread-safe."""
        import threading

        collector = get_metrics_collector()

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
