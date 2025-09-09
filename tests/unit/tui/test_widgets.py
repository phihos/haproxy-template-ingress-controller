"""
Unit tests for TUI widget components.

Tests widget data binding, user interactions, and rendering behavior.
"""

import pytest
from unittest.mock import patch, PropertyMock, Mock
from datetime import datetime

from textual.widgets import DataTable

from haproxy_template_ic.tui.models import (
    DashboardData,
    PodInfo,
    TemplateInfo,
    ResourceInfo,
    PerformanceInfo,
    ActivityEvent,
    OperatorInfo,
    ErrorInfo,
)
from haproxy_template_ic.tui.widgets import (
    PodsWidget,
    TemplatesWidget,
    ResourcesWidget,
    PerformanceWidget,
    ActivityWidget,
    HeaderWidget,
)
from haproxy_template_ic.tui.widgets.inspector import TemplateInspectorWidget


class TestPodsWidget:
    """Test PodsWidget component."""

    @pytest.fixture
    def pods_widget(self):
        """Create a PodsWidget instance."""
        return PodsWidget()

    @pytest.fixture
    def sample_pods_data(self):
        """Sample pods data."""
        return [
            PodInfo(
                name="haproxy-pod-1",
                status="Running",
                ip="10.0.0.1",
                cpu="100m",
                memory="128Mi",
                synced="2m ago",
                last_sync=datetime.now(),
                sync_success=True,
                start_time=datetime.now(),
            ),
            PodInfo(
                name="haproxy-pod-2",
                status="Running",
                ip="10.0.0.2",
                cpu="95m",
                memory="120Mi",
                synced="Failed",
                last_sync=None,
                sync_success=False,
                start_time=datetime.now(),
            ),
        ]

    def test_pods_widget_initialization(self, pods_widget):
        """Test PodsWidget initialization."""
        assert isinstance(pods_widget, DataTable)
        assert pods_widget.border_title == "HAProxy Pods"
        assert pods_widget.cursor_type == "row"
        assert pods_widget.zebra_stripes is True

    def test_pods_widget_columns_setup(self, pods_widget):
        """Test that columns can be set up."""
        # We can't test actual column setup without Textual app context
        # Just verify the method exists and widget has required attributes
        assert hasattr(pods_widget, "add_columns")
        assert hasattr(pods_widget, "on_mount")

    def test_pods_widget_data_update_with_pods(self, pods_widget, sample_pods_data):
        """Test widget update with pod data."""
        dashboard_data = DashboardData(pods=sample_pods_data)

        # Mock the DataTable methods
        with patch.object(pods_widget, "clear") as mock_clear:
            with patch.object(pods_widget, "add_row") as mock_add_row:
                with patch.object(pods_widget, "refresh"):
                    pods_widget.watch_dashboard_data(dashboard_data)

        mock_clear.assert_called_once()
        assert mock_add_row.call_count == 2  # Two pods

        # Check that sync status was formatted correctly
        calls = mock_add_row.call_args_list
        assert "haproxy-pod-1" in str(calls[0])
        assert "haproxy-pod-2" in str(calls[1])

    def test_pods_widget_data_update_empty(self, pods_widget):
        """Test widget update with no pods."""

        dashboard_data = DashboardData(pods=[])

        with patch.object(pods_widget, "clear") as mock_clear:
            with patch.object(pods_widget, "add_row") as mock_add_row:
                with patch.object(pods_widget, "refresh") as mock_refresh:
                    pods_widget.watch_dashboard_data(dashboard_data)

        mock_clear.assert_called_once()
        mock_add_row.assert_called_once_with(
            "No HAProxy pods found", "N/A", "⚫ Unknown", "N/A", "N/A"
        )
        mock_refresh.assert_called_once()

    def test_pods_widget_sync_status_formatting(self, pods_widget):
        """Test sync status formatting logic."""
        # Test successful sync
        success_pod = PodInfo(name="test", sync_success=True)
        dashboard_data = DashboardData(pods=[success_pod])

        with patch.object(pods_widget, "add_row") as mock_add_row:
            with patch.object(pods_widget, "clear"):
                with patch.object(pods_widget, "refresh"):
                    pods_widget.watch_dashboard_data(dashboard_data)

        # Check that success status was used
        call_args = mock_add_row.call_args[0]
        assert "✅ Success" in str(call_args)

        # Test failed sync
        failed_pod = PodInfo(name="test", sync_success=False)
        dashboard_data = DashboardData(pods=[failed_pod])

        with patch.object(pods_widget, "add_row") as mock_add_row:
            with patch.object(pods_widget, "clear"):
                with patch.object(pods_widget, "refresh"):
                    pods_widget.watch_dashboard_data(dashboard_data)

        call_args = mock_add_row.call_args[0]
        assert "❌ Failed" in str(call_args)


class TestTemplatesWidget:
    """Test TemplatesWidget component."""

    @pytest.fixture
    def templates_widget(self):
        """Create a TemplatesWidget instance."""
        return TemplatesWidget()

    @pytest.fixture
    def sample_templates_data(self):
        """Sample templates data."""
        return {
            "haproxy.cfg": TemplateInfo(
                name="haproxy.cfg",
                type="config",
                size=1024,
                lines=45,
                status="valid",
                last_modified=datetime.now(),
            ),
            "host.map": TemplateInfo(
                name="host.map", type="map", size=512, lines=20, status="valid"
            ),
            "error.cfg": TemplateInfo(
                name="error.cfg", type="config", size=0, lines=0, status="empty"
            ),
        }

    def test_templates_widget_initialization(self, templates_widget):
        """Test TemplatesWidget initialization."""
        assert isinstance(templates_widget, DataTable)
        assert templates_widget.border_title == "Templates"

    def test_templates_widget_data_update_with_templates(
        self, templates_widget, sample_templates_data
    ):
        """Test widget update with template data."""

        dashboard_data = DashboardData(templates=sample_templates_data)

        with patch.object(templates_widget, "clear") as mock_clear:
            with patch.object(templates_widget, "add_row") as mock_add_row:
                templates_widget.watch_dashboard_data(dashboard_data)

        mock_clear.assert_called_once()
        assert mock_add_row.call_count == 3  # Three templates

        # Verify template data was formatted correctly
        calls = mock_add_row.call_args_list
        call_strs = [str(call) for call in calls]

        assert any("haproxy.cfg" in call_str for call_str in call_strs)
        assert any("host.map" in call_str for call_str in call_strs)
        assert any("config" in call_str for call_str in call_strs)
        assert any("map" in call_str for call_str in call_strs)

    def test_templates_widget_data_update_empty(self, templates_widget):
        """Test widget update with no templates."""

        dashboard_data = DashboardData(templates={})

        with patch.object(templates_widget, "clear") as mock_clear:
            with patch.object(templates_widget, "add_row") as mock_add_row:
                templates_widget.watch_dashboard_data(dashboard_data)

        mock_clear.assert_called_once()
        # Check that two informational rows are added
        assert mock_add_row.call_count == 2
        calls = mock_add_row.call_args_list
        # First call should be about no templates found
        assert "No templates found" in str(calls[0])
        # Second call should be about operator startup
        assert "Operator may be starting up" in str(calls[1])

    def test_templates_widget_template_selection(
        self, templates_widget, sample_templates_data
    ):
        """Test template selection behavior."""
        dashboard_data = DashboardData(templates=sample_templates_data)

        # Set up widget with data
        with patch.object(templates_widget, "clear"):
            with patch.object(templates_widget, "add_row"):
                templates_widget.watch_dashboard_data(dashboard_data)

        # Mock cursor position and selection
        with patch.object(
            type(templates_widget),
            "cursor_row",
            new_callable=PropertyMock,
            return_value=0,
        ):
            with patch.object(
                templates_widget,
                "get_row_at",
                return_value=["haproxy.cfg", "config", "1.0KB", "45", "valid", "-"],
            ):
                # Simulate selection event
                from textual.widgets import DataTable
                from textual.widgets._data_table import RowKey

                row_key = RowKey("test-row")
                DataTable.RowSelected(
                    templates_widget, templates_widget.cursor_row, row_key
                )

                # The widget should emit a custom message
                # This tests the event handling logic
                # (Actual event posting would need a running app)


class TestResourcesWidget:
    """Test ResourcesWidget component."""

    @pytest.fixture
    def resources_widget(self):
        """Create a ResourcesWidget instance."""
        return ResourcesWidget()

    @pytest.fixture
    def sample_resources_data(self):
        """Sample resources data."""
        return ResourceInfo(
            resource_counts={
                "ingresses": 3,
                "services": 5,
                "secrets": 2,
                "configmaps": 1,
            },
            total=11,
            last_update=datetime.now(),
            resource_memory_sizes={"ingresses": 1024, "services": 2048},
        )

    def test_resources_widget_initialization(self, resources_widget):
        """Test ResourcesWidget initialization."""
        assert isinstance(resources_widget, DataTable)
        assert resources_widget.border_title == "Watched Resources"

    def test_resources_widget_data_update_with_resources(
        self, resources_widget, sample_resources_data
    ):
        """Test widget update with resource data."""

        dashboard_data = DashboardData(resources=sample_resources_data)

        with patch.object(resources_widget, "clear") as mock_clear:
            with patch.object(resources_widget, "add_row") as mock_add_row:
                resources_widget.watch_dashboard_data(dashboard_data)

        mock_clear.assert_called_once()

        assert mock_add_row.call_count == 5  # Four resource types + total row

        # Verify resources were added
        calls = mock_add_row.call_args_list
        call_strs = [str(call) for call in calls]

        assert any(
            "Ingresses" in call_str and "3" in call_str for call_str in call_strs
        )
        assert any("Services" in call_str and "5" in call_str for call_str in call_strs)
        assert any("Total" in call_str and "11" in call_str for call_str in call_strs)

    def test_resources_widget_data_update_empty(self, resources_widget):
        """Test widget update with no resources."""

        empty_resources = ResourceInfo()
        dashboard_data = DashboardData(resources=empty_resources)

        with patch.object(resources_widget, "clear") as mock_clear:
            with patch.object(resources_widget, "add_row") as mock_add_row:
                resources_widget.watch_dashboard_data(dashboard_data)

        mock_clear.assert_called_once()
        mock_add_row.assert_called_once_with("❌", "No watched resources", "—", "—")


class TestPerformanceWidget:
    """Test PerformanceWidget component."""

    @pytest.fixture
    def performance_widget(self):
        """Create a PerformanceWidget instance."""
        return PerformanceWidget()

    @pytest.fixture
    def sample_performance_data(self):
        """Sample performance data."""
        from haproxy_template_ic.tui.models import PerformanceMetric

        return PerformanceInfo(
            template_render=PerformanceMetric(p50=50.0, p95=100.0, p99=200.0),
            dataplane_api=PerformanceMetric(p50=25.0, p95=50.0, p99=100.0),
            sync_success_rate=0.95,
            recent_sync_success_rate=0.98,
            total_syncs=100,
            failed_syncs=5,
        )

    @pytest.fixture
    def performance_data_with_history(self):
        """Sample performance data with history for sparklines."""
        from haproxy_template_ic.tui.models import PerformanceMetric

        return PerformanceInfo(
            template_render=PerformanceMetric(
                p50=50.0, p95=100.0, p99=200.0, history=[10.0, 20.0, 30.0, 40.0, 50.0]
            ),
            dataplane_api=PerformanceMetric(
                p50=25.0, p95=50.0, p99=100.0, history=[15.0, 25.0, 35.0, 20.0, 30.0]
            ),
            sync_success_rate=0.95,
            total_syncs=100,
            failed_syncs=5,
            sync_pattern="✅✅❌✅✅",
        )

    def test_performance_widget_initialization(self, performance_widget):
        """Test PerformanceWidget initialization."""
        assert performance_widget.border_title == "Performance Metrics"
        assert hasattr(performance_widget, "dashboard_data")
        assert hasattr(performance_widget, "compose")
        assert hasattr(performance_widget, "watch_dashboard_data")

    def test_performance_widget_compose(self, performance_widget):
        """Test PerformanceWidget compose method."""
        composed = performance_widget.compose()
        compose_list = list(composed)

        assert len(compose_list) == 1
        from textual.widgets import Static

        assert isinstance(compose_list[0], Static)
        assert compose_list[0].id == "performance-content"

    def test_performance_widget_generate_content_no_data(self, performance_widget):
        """Test content generation with no performance data."""
        # Empty performance data
        performance_widget.dashboard_data = DashboardData()

        content = performance_widget._generate_content()

        assert "❌ No performance data available" in content
        assert "ℹ️  Check if HAProxy pods are running" in content
        assert "🔄 Use 'r' to refresh data" in content

    def test_performance_widget_generate_content_with_data(
        self, performance_widget, sample_performance_data
    ):
        """Test content generation with performance data."""
        performance_widget.dashboard_data = DashboardData(
            performance=sample_performance_data
        )

        content = performance_widget._generate_content()

        # Check for main sections
        assert "━━━ Performance Overview ━━━" in content
        assert "📊 Template Rendering" in content
        assert "📡 Dataplane API" in content
        assert "📈 Sync Statistics" in content

    def test_performance_widget_format_percentiles(self, performance_widget):
        """Test _format_percentiles method."""
        from haproxy_template_ic.tui.models import PerformanceMetric

        # Test with valid metric
        metric = PerformanceMetric(p50=50.0, p95=100.0, p99=200.0)
        formatted = performance_widget._format_percentiles(metric)

        assert "P50: 50.0ms" in formatted
        assert "P95: 100.0ms" in formatted
        assert "P99: 200.0ms" in formatted

        # Test with None metric
        formatted = performance_widget._format_percentiles(None)
        assert formatted == "N/A"

        # Test with partial data
        metric_partial = PerformanceMetric(p50=50.0, p95=None, p99=200.0)
        formatted = performance_widget._format_percentiles(metric_partial)

        assert "P50: 50.0ms" in formatted
        assert "P95: N/A" in formatted
        assert "P99: 200.0ms" in formatted

    def test_performance_widget_get_performance_status_template(
        self, performance_widget
    ):
        """Test _get_performance_status for template metrics."""
        from haproxy_template_ic.tui.models import PerformanceMetric

        # Test different template performance levels
        test_cases = [
            (5.0, "⚡ Excellent"),
            (25.0, "✅ Good"),
            (75.0, "⚠️ Slow"),
            (150.0, "🐌 Very Slow"),
        ]

        for p50_val, expected_status in test_cases:
            metric = PerformanceMetric(p50=p50_val, p95=p50_val * 2, p99=p50_val * 4)
            status = performance_widget._get_performance_status(metric, "template")
            assert status == expected_status

    def test_performance_widget_get_performance_status_api(self, performance_widget):
        """Test _get_performance_status for API metrics."""
        from haproxy_template_ic.tui.models import PerformanceMetric

        # Test different API performance levels
        test_cases = [
            (50.0, "⚡ Excellent"),
            (250.0, "✅ Good"),
            (750.0, "⚠️ Slow"),
            (1500.0, "🐌 Very Slow"),
        ]

        for p50_val, expected_status in test_cases:
            metric = PerformanceMetric(p50=p50_val, p95=p50_val * 2, p99=p50_val * 4)
            status = performance_widget._get_performance_status(metric, "api")
            assert status == expected_status

    def test_performance_widget_get_performance_status_invalid(
        self, performance_widget
    ):
        """Test _get_performance_status with invalid data."""
        # Test with None metric
        status = performance_widget._get_performance_status(None, "template")
        assert status == "❓ Unknown"

        # Test with metric with no p50
        from haproxy_template_ic.tui.models import PerformanceMetric

        metric = PerformanceMetric(p50=None, p95=100.0, p99=200.0)
        status = performance_widget._get_performance_status(metric, "template")
        assert status == "❓ Unknown"

        # Test with unknown metric type
        metric = PerformanceMetric(p50=50.0, p95=100.0, p99=200.0)
        status = performance_widget._get_performance_status(metric, "unknown")
        assert status == "❓ Unknown"

    def test_performance_widget_format_duration_from_ms(self, performance_widget):
        """Test _format_duration_from_ms method."""
        # Test different duration scales
        test_cases = [
            (None, "N/A"),
            (0.5, "500μs"),  # Microseconds
            (1.5, "1.5ms"),  # Milliseconds
            (1500.0, "1.500s"),  # Seconds
        ]

        for ms_val, expected in test_cases:
            result = performance_widget._format_duration_from_ms(ms_val)
            assert result == expected

    def test_performance_widget_format_duration(self, performance_widget):
        """Test _format_duration method."""
        # Test different duration scales
        test_cases = [
            (None, "N/A"),
            (0.0005, "500μs"),  # Microseconds
            (0.0015, "1.5ms"),  # Milliseconds
            (1.5, "1.500s"),  # Seconds
        ]

        for sec_val, expected in test_cases:
            result = performance_widget._format_duration(sec_val)
            assert result == expected

    def test_performance_widget_calculate_throughput(self, performance_widget):
        """Test _calculate_throughput method."""
        from haproxy_template_ic.tui.models import PerformanceMetric

        # Test with no history
        metric = PerformanceMetric(p50=50.0)
        throughput = performance_widget._calculate_throughput(metric)
        assert throughput is None

        # Test with insufficient history
        metric = PerformanceMetric(p50=50.0, history=[10.0])
        throughput = performance_widget._calculate_throughput(metric)
        assert throughput is None

        # Test with sufficient history
        metric = PerformanceMetric(p50=50.0, history=[10.0, 20.0, 30.0, 40.0, 50.0])
        throughput = performance_widget._calculate_throughput(metric)
        assert throughput is not None
        assert throughput >= 1.0  # At least 1 op/min

    def test_performance_widget_calculate_uptime(self, performance_widget):
        """Test _calculate_uptime method."""
        from datetime import datetime, timezone, timedelta

        # Test with no start time
        performance_widget.dashboard_data = DashboardData()
        uptime = performance_widget._calculate_uptime()
        assert uptime is None

        # Test with valid start time (1 hour ago)
        start_time = datetime.now(timezone.utc) - timedelta(hours=1, minutes=30)
        start_time_iso = start_time.isoformat().replace("+00:00", "Z")

        operator = OperatorInfo(
            status="RUNNING", namespace="test", controller_pod_start_time=start_time_iso
        )
        performance_widget.dashboard_data = DashboardData(operator=operator)

        uptime = performance_widget._calculate_uptime()
        assert uptime is not None
        assert "1h" in uptime
        assert "30m" in uptime

    def test_performance_widget_create_sparkline(self, performance_widget):
        """Test _create_sparkline method."""
        # Test with insufficient values
        sparkline = performance_widget._create_sparkline([1.0], "Test", "ms")
        assert sparkline is None

        # Test with valid values
        values = [1.0, 2.0, 3.0, 4.0, 5.0]
        sparkline = performance_widget._create_sparkline(values, "Test", "ms")
        assert sparkline is not None
        assert "Test:" in sparkline
        assert "5.000ms" in sparkline  # Current value

        # Test with all same values
        values = [3.0, 3.0, 3.0, 3.0, 3.0]
        sparkline = performance_widget._create_sparkline(values, "Test", "")
        assert sparkline is not None
        assert "→" in sparkline  # Flat trend

        # Test trending up
        values = [1.0, 2.0, 3.0, 4.0, 5.0, 6.0]
        sparkline = performance_widget._create_sparkline(values, "Test", "")
        assert sparkline is not None
        assert "↗️" in sparkline  # Up trend

        # Test trending down
        values = [6.0, 5.0, 4.0, 3.0, 2.0, 1.0]
        sparkline = performance_widget._create_sparkline(values, "Test", "")
        assert sparkline is not None
        assert "↘️" in sparkline  # Down trend

    def test_performance_widget_generate_sparklines(
        self, performance_widget, performance_data_with_history
    ):
        """Test _generate_sparklines method."""
        performance_widget.dashboard_data = DashboardData(
            performance=performance_data_with_history
        )

        sparklines = performance_widget._generate_sparklines()

        assert len(sparklines) > 0
        # Should contain template and API sparklines
        template_found = any("🎨 Templates" in line for line in sparklines)
        api_found = any("🔄 API Calls" in line for line in sparklines)
        pattern_found = any("📊 Sync Pattern" in line for line in sparklines)

        assert (
            template_found or api_found or pattern_found
        )  # At least one should be present

    def test_performance_widget_watch_dashboard_data(
        self, performance_widget, sample_performance_data
    ):
        """Test watch_dashboard_data method."""
        # Mock the query_one method
        mock_content_widget = Mock()
        with patch.object(
            performance_widget, "query_one", return_value=mock_content_widget
        ):
            dashboard_data = DashboardData(performance=sample_performance_data)

            performance_widget.watch_dashboard_data(dashboard_data)

            # Should call update on content widget at least once
            assert mock_content_widget.update.called

    def test_performance_widget_on_mount(self, performance_widget):
        """Test on_mount method."""
        # Mock the query_one method
        mock_content_widget = Mock()
        with patch.object(
            performance_widget, "query_one", return_value=mock_content_widget
        ):
            performance_widget.on_mount()

            # Should call update on content widget at least once
            assert mock_content_widget.update.called

    def test_performance_widget_error_handling(self, performance_widget):
        """Test error handling in watch_dashboard_data and on_mount."""
        # Mock query_one to raise an exception
        with patch.object(
            performance_widget, "query_one", side_effect=Exception("Test error")
        ):
            # Should not raise exception
            performance_widget.watch_dashboard_data(DashboardData())
            performance_widget.on_mount()

    def test_performance_widget_data_update_with_metrics(
        self, performance_widget, sample_performance_data
    ):
        """Test widget update with performance data via reactive property."""
        dashboard_data = DashboardData(performance=sample_performance_data)

        # Test setting dashboard data
        performance_widget.dashboard_data = dashboard_data

        # Verify data was set
        assert performance_widget.dashboard_data.performance == sample_performance_data


class TestActivityWidget:
    """Test ActivityWidget component."""

    @pytest.fixture
    def activity_widget(self):
        """Create an ActivityWidget instance."""
        return ActivityWidget()

    @pytest.fixture
    def sample_activity_data(self):
        """Sample activity data."""
        return [
            ActivityEvent(
                type="RELOAD",
                message="Configuration reloaded successfully",
                timestamp=datetime.now().isoformat(),
                source="dataplane",
                metadata={"config_version": "v1.2.3"},
            ),
            ActivityEvent(
                type="SYNC",
                message="Resources synchronized",
                timestamp=datetime.now().isoformat(),
                source="operator",
                metadata={"resource_type": "ingresses"},
            ),
            ActivityEvent(
                type="ERROR",
                message="Template rendering failed",
                timestamp=datetime.now().isoformat(),
                source="template",
                metadata={"error_code": "SYNTAX_ERROR"},
            ),
            ActivityEvent(
                type="CREATE",
                message="New backend created",
                timestamp=datetime.now().isoformat(),
                source="dataplane",
                metadata={"backend_name": "test-backend"},
            ),
            ActivityEvent(
                type="UPDATE",
                message="Backend updated",
                timestamp=datetime.now().isoformat(),
                source="dataplane",
                metadata={"backend_name": "test-backend"},
            ),
            ActivityEvent(
                type="DELETE",
                message="Backend deleted",
                timestamp=datetime.now().isoformat(),
                source="dataplane",
                metadata={"backend_name": "old-backend"},
            ),
            ActivityEvent(
                type="SUCCESS",
                message="Deployment successful",
                timestamp=datetime.now().isoformat(),
                source="operator",
                metadata={"deployment_id": "deploy-123"},
            ),
        ]

    def test_activity_widget_initialization(self, activity_widget):
        """Test ActivityWidget initialization."""
        assert activity_widget.border_title == "Activity Feed"
        assert hasattr(activity_widget, "dashboard_data")
        assert hasattr(activity_widget, "watch_dashboard_data")
        assert hasattr(activity_widget, "_add_activity_entry")
        assert hasattr(activity_widget, "on_mount")
        assert activity_widget._last_activity_count == 0
        assert activity_widget._showing_welcome

    def test_activity_widget_on_mount(self, activity_widget):
        """Test on_mount initialization."""
        with patch.object(activity_widget, "write") as mock_write:
            activity_widget.on_mount()

            # Should write welcome messages
            assert mock_write.call_count == 2
            calls = mock_write.call_args_list
            assert "🚀 HAProxy Template IC Activity Feed" in calls[0][0][0]
            assert (
                "📝 Real-time operator and pod events will appear here"
                in calls[1][0][0]
            )

    def test_activity_widget_watch_dashboard_data_empty(self, activity_widget):
        """Test watch_dashboard_data with empty activities."""
        dashboard_data = DashboardData(activity=[])

        # Should not call _add_activity_entry for empty data
        with patch.object(activity_widget, "_add_activity_entry") as mock_add_entry:
            activity_widget.watch_dashboard_data(dashboard_data)
            mock_add_entry.assert_not_called()

    def test_activity_widget_watch_dashboard_data_first_time(
        self, activity_widget, sample_activity_data
    ):
        """Test watch_dashboard_data with first activity entries."""
        dashboard_data = DashboardData(activity=sample_activity_data[:2])

        with patch.object(activity_widget, "clear") as mock_clear:
            with patch.object(activity_widget, "_add_activity_entry") as mock_add_entry:
                activity_widget.watch_dashboard_data(dashboard_data)

                # Should clear welcome message on first activity
                mock_clear.assert_called_once()
                # Should add all entries
                assert mock_add_entry.call_count == 2
                # Should update last activity count
                assert activity_widget._last_activity_count == 2
                assert not activity_widget._showing_welcome

    def test_activity_widget_watch_dashboard_data_incremental(
        self, activity_widget, sample_activity_data
    ):
        """Test watch_dashboard_data with incremental updates."""
        # Set initial state
        activity_widget._last_activity_count = 3
        activity_widget._showing_welcome = False

        dashboard_data = DashboardData(activity=sample_activity_data)

        with patch.object(activity_widget, "_add_activity_entry") as mock_add_entry:
            activity_widget.watch_dashboard_data(dashboard_data)

            # Should only add new entries (4 new ones since we had 3)
            assert mock_add_entry.call_count == 4
            # Should update count
            assert activity_widget._last_activity_count == 7

    def test_activity_widget_add_activity_entry_error_type(self, activity_widget):
        """Test _add_activity_entry with ERROR event type."""
        entry = ActivityEvent(
            type="ERROR",
            message="Connection failed",
            timestamp=datetime.now().isoformat(),
            source="dataplane",
            metadata={"error_code": "CONNECTION_REFUSED"},
        )

        with patch.object(activity_widget, "write") as mock_write:
            activity_widget._add_activity_entry(entry)

            mock_write.assert_called_once()
            written_text = str(mock_write.call_args[0][0])
            assert "❌" in written_text
            assert "Connection failed" in written_text

    def test_activity_widget_add_activity_entry_success_types(self, activity_widget):
        """Test _add_activity_entry with success event types."""
        test_cases = [
            ("CREATE", "➕", "[green]"),
            ("SUCCESS", "✅", "[green]"),
        ]

        for event_type, expected_icon, expected_style in test_cases:
            entry = ActivityEvent(
                type=event_type,
                message=f"{event_type} event occurred",
                timestamp=datetime.now().isoformat(),
                source="operator",
                metadata={},
            )

            with patch.object(activity_widget, "write") as mock_write:
                activity_widget._add_activity_entry(entry)

                mock_write.assert_called_once()
                written_text = str(mock_write.call_args[0][0])
                assert expected_icon in written_text

    def test_activity_widget_add_activity_entry_update_types(self, activity_widget):
        """Test _add_activity_entry with update event types."""
        test_cases = [
            ("UPDATE", "📝", "[blue]"),
            ("SYNC", "🔄", "[blue]"),
        ]

        for event_type, expected_icon, expected_style in test_cases:
            entry = ActivityEvent(
                type=event_type,
                message=f"{event_type} event occurred",
                timestamp=datetime.now().isoformat(),
                source="operator",
                metadata={},
            )

            with patch.object(activity_widget, "write") as mock_write:
                activity_widget._add_activity_entry(entry)

                mock_write.assert_called_once()
                written_text = str(mock_write.call_args[0][0])
                assert expected_icon in written_text

    def test_activity_widget_add_activity_entry_other_types(self, activity_widget):
        """Test _add_activity_entry with other event types."""
        test_cases = [
            ("DELETE", "➖", "[yellow]"),
            ("RELOAD", "🔄", "[cyan]"),
            ("INFO", "ℹ️", "[white]"),
            ("UNKNOWN", "ℹ️", "[white]"),  # Default
        ]

        for event_type, expected_icon, expected_style in test_cases:
            entry = ActivityEvent(
                type=event_type,
                message=f"{event_type} event occurred",
                timestamp=datetime.now().isoformat(),
                source="operator",
                metadata={},
            )

            with patch.object(activity_widget, "write") as mock_write:
                activity_widget._add_activity_entry(entry)

                mock_write.assert_called_once()
                written_text = str(mock_write.call_args[0][0])
                assert expected_icon in written_text

    def test_activity_widget_add_activity_entry_with_source(self, activity_widget):
        """Test _add_activity_entry with different sources."""
        entry = ActivityEvent(
            type="INFO",
            message="Test message",
            timestamp=datetime.now().isoformat(),
            source="custom-source",
            metadata={},
        )

        with patch.object(activity_widget, "write") as mock_write:
            activity_widget._add_activity_entry(entry)

            mock_write.assert_called_once()
            written_text = str(mock_write.call_args[0][0])
            # The log formatting processes Rich markup, so just verify the message content is present
            assert "Test message" in written_text

    def test_activity_widget_add_activity_entry_system_source(self, activity_widget):
        """Test _add_activity_entry with system source (should be omitted)."""
        entry = ActivityEvent(
            type="INFO",
            message="Test message",
            timestamp=datetime.now().isoformat(),
            source="system",
            metadata={},
        )

        with patch.object(activity_widget, "write") as mock_write:
            activity_widget._add_activity_entry(entry)

            mock_write.assert_called_once()
            written_text = str(mock_write.call_args[0][0])
            assert "[system]" not in written_text  # System source should be omitted

    def test_activity_widget_add_activity_entry_time_formatting(self, activity_widget):
        """Test _add_activity_entry with time formatting."""
        from datetime import datetime, timezone

        # Use a specific timestamp for testing
        timestamp = datetime(2023, 1, 1, 12, 30, 45, tzinfo=timezone.utc)
        entry = ActivityEvent(
            type="INFO",
            message="Test message",
            timestamp=timestamp.isoformat().replace("+00:00", "Z"),
            source="test",
            metadata={},
        )

        with patch.object(activity_widget, "write") as mock_write:
            activity_widget._add_activity_entry(entry)

            mock_write.assert_called_once()
            written_text = str(mock_write.call_args[0][0])
            # Should contain formatted time
            assert ":" in written_text  # Should contain time format

    def test_activity_widget_add_activity_entry_error_handling(self, activity_widget):
        """Test _add_activity_entry error handling."""
        # Create an entry that might cause parsing issues
        entry = ActivityEvent(
            type="INFO",
            message="Test message",
            timestamp="invalid-timestamp",
            source="test",
            metadata={},
        )

        with patch.object(activity_widget, "write") as mock_write:
            # Should not raise exception
            activity_widget._add_activity_entry(entry)

            # Should still write something (fallback)
            mock_write.assert_called_once()

    def test_activity_widget_data_update_with_events(
        self, activity_widget, sample_activity_data
    ):
        """Test widget update with activity events via reactive property."""
        dashboard_data = DashboardData(activity=sample_activity_data)

        # Set the dashboard data via reactive property
        activity_widget.dashboard_data = dashboard_data

        # Verify data was set
        assert activity_widget.dashboard_data.activity == sample_activity_data

    def test_activity_widget_data_update_empty(self, activity_widget):
        """Test widget update with no activity events."""
        dashboard_data = DashboardData(activity=[])

        # Should work without errors
        activity_widget.dashboard_data = dashboard_data
        assert activity_widget.dashboard_data.activity == []


class TestHeaderWidget:
    """Test HeaderWidget component."""

    @pytest.fixture
    def header_widget(self):
        """Create a HeaderWidget instance."""
        return HeaderWidget()

    @pytest.fixture
    def sample_operator_data(self):
        """Sample operator data."""
        return OperatorInfo(
            status="RUNNING",
            version="1.2.3",
            namespace="test-namespace",
            deployment_name="haproxy-template-ic",
            configmap_name="test-config",
            last_update=datetime.now(),
        )

    def test_header_widget_initialization(self, header_widget):
        """Test HeaderWidget initialization."""
        assert header_widget.border_title == "HAProxy Template IC Dashboard"
        assert hasattr(header_widget, "dashboard_data")
        assert hasattr(header_widget, "render")
        assert hasattr(header_widget, "watch_dashboard_data")

    def test_header_widget_render_basic(self, header_widget):
        """Test basic render functionality."""
        # Test with minimal operator data
        operator = OperatorInfo(
            status="RUNNING",
            version="1.2.3",
            namespace="test-namespace",
        )
        header_widget.dashboard_data = DashboardData(operator=operator)

        rendered = header_widget.render()
        assert "🟢 Status: RUNNING" in rendered
        assert "Version: 1.2.3" in rendered
        assert "Namespace: test-namespace" in rendered
        assert "Config: unknown" in rendered

    def test_header_widget_render_all_status_types(self, header_widget):
        """Test rendering with all status types and their emoji indicators."""
        status_tests = [
            ("RUNNING", "🟢"),
            ("STARTING", "🟡"),
            ("ERROR", "🔴"),
            ("DISCONNECTED", "🔴"),
            ("UNKNOWN", "⚫"),
            ("INVALID_STATUS", "⚫"),  # Unknown status should default to ⚫
        ]

        for status, expected_emoji in status_tests:
            operator = OperatorInfo(status=status, namespace="test")
            header_widget.dashboard_data = DashboardData(operator=operator)

            rendered = header_widget.render()
            assert f"{expected_emoji} Status: {status}" in rendered

    def test_header_widget_render_with_configmap_name(self, header_widget):
        """Test rendering with configmap name."""
        operator = OperatorInfo(
            status="RUNNING",
            namespace="test",
            configmap_name="custom-config",
        )
        header_widget.dashboard_data = DashboardData(operator=operator)

        rendered = header_widget.render()
        assert "Config: custom-config" in rendered

    def test_header_widget_render_with_controller_pod_name(self, header_widget):
        """Test rendering with controller pod name."""
        operator = OperatorInfo(
            status="RUNNING",
            namespace="test",
            controller_pod_name="haproxy-controller-abc123",
        )
        header_widget.dashboard_data = DashboardData(operator=operator)

        rendered = header_widget.render()
        assert "Pod: haproxy-controller-abc123" in rendered

    def test_header_widget_render_with_last_update_datetime(self, header_widget):
        """Test rendering with last_update as datetime."""
        from datetime import datetime, timezone

        last_update = datetime.now(timezone.utc)
        operator = OperatorInfo(status="RUNNING", namespace="test")
        dashboard_data = DashboardData(operator=operator, last_update=last_update)
        header_widget.dashboard_data = dashboard_data

        rendered = header_widget.render()
        # Should contain "Updated:" with some time format
        assert "Updated:" in rendered

    def test_header_widget_render_default_last_update(self, header_widget):
        """Test rendering with default last_update (should contain Updated field)."""
        operator = OperatorInfo(status="RUNNING", namespace="test")
        dashboard_data = DashboardData(operator=operator)  # Uses default last_update
        header_widget.dashboard_data = dashboard_data

        rendered = header_widget.render()
        # Should contain "Updated:" with default last_update
        assert "Updated:" in rendered

    def test_header_widget_render_with_all_fields(self, header_widget):
        """Test rendering with all possible fields."""
        from datetime import datetime, timezone

        operator = OperatorInfo(
            status="RUNNING",
            version="2.1.0",
            namespace="production",
            configmap_name="prod-config",
            controller_pod_name="controller-xyz789",
        )
        last_update = datetime.now(timezone.utc)
        dashboard_data = DashboardData(operator=operator, last_update=last_update)
        header_widget.dashboard_data = dashboard_data

        rendered = header_widget.render()

        # Verify all components are present
        assert "🟢 Status: RUNNING" in rendered
        assert "Version: 2.1.0" in rendered
        assert "Namespace: production" in rendered
        assert "Config: prod-config" in rendered
        assert "Pod: controller-xyz789" in rendered
        assert "Updated:" in rendered

        # Verify components are separated by │
        assert "│" in rendered

    def test_header_widget_render_with_unknown_version(self, header_widget):
        """Test rendering with None version."""
        operator = OperatorInfo(
            status="RUNNING",
            namespace="test",
            version=None,
        )
        header_widget.dashboard_data = DashboardData(operator=operator)

        rendered = header_widget.render()
        assert "Version: unknown" in rendered

    def test_header_widget_watch_dashboard_data(self, header_widget):
        """Test watch_dashboard_data calls refresh."""
        with patch.object(header_widget, "refresh") as mock_refresh:
            operator = OperatorInfo(status="RUNNING", namespace="test")
            dashboard_data = DashboardData(operator=operator)

            header_widget.watch_dashboard_data(dashboard_data)

            mock_refresh.assert_called_once()

    def test_header_widget_data_update_with_operator_info(
        self, header_widget, sample_operator_data
    ):
        """Test widget update with operator information."""
        dashboard_data = DashboardData(operator=sample_operator_data)
        header_widget.dashboard_data = dashboard_data

        # Test that the data was set correctly
        assert header_widget.dashboard_data.operator == sample_operator_data

    def test_header_widget_status_formatting(self, header_widget):
        """Test status indicator formatting with reactive property."""
        statuses = ["RUNNING", "ERROR", "DISCONNECTED", "UNKNOWN"]

        for status in statuses:
            operator = OperatorInfo(status=status, namespace="test")
            dashboard_data = DashboardData(operator=operator)
            header_widget.dashboard_data = dashboard_data

            # Test that status is reflected in render
            rendered = header_widget.render()
            assert f"Status: {status}" in rendered


class TestWidgetIntegration:
    """Integration tests for widget components."""

    def test_widget_reactive_properties(self):
        """Test that widgets have reactive dashboard_data properties."""
        widgets_to_test = [PodsWidget, TemplatesWidget, ResourcesWidget]

        for widget_class in widgets_to_test:
            widget_class()

            # Check that dashboard_data is defined as a class attribute (reactive property)
            assert hasattr(widget_class, "dashboard_data")
            # Check that it's a reactive descriptor
            from textual.reactive import Reactive

            assert isinstance(widget_class.dashboard_data, Reactive)

    def test_widget_data_flow(self):
        """Test complete data flow through widgets."""
        # Create full dashboard data
        dashboard_data = DashboardData(
            operator=OperatorInfo(status="RUNNING", namespace="test"),
            pods=[PodInfo(name="test-pod", sync_success=True)],
            templates={"test.cfg": TemplateInfo(name="test.cfg", type="config")},
            resources=ResourceInfo(resource_counts={"ingresses": 1}, total=1),
            activity=[
                ActivityEvent(
                    timestamp=datetime.now(),
                    type="SYNC",
                    source="test",
                    message="Test event",
                )
            ],
        )

        # Test that all widgets can handle the data
        widgets = [
            PodsWidget(),
            TemplatesWidget(),
            ResourcesWidget(),
            PerformanceWidget(),
            ActivityWidget(),
            HeaderWidget(),
        ]

        for widget in widgets:
            if hasattr(widget, "watch_dashboard_data"):
                # Mock the widget methods that require Textual app context
                with patch.object(widget, "clear", create=True):
                    with patch.object(widget, "add_row", create=True):
                        with patch.object(widget, "refresh", create=True):
                            # Should not raise exceptions
                            try:
                                widget.watch_dashboard_data(dashboard_data)
                            except Exception as e:
                                pytest.fail(
                                    f"Widget {type(widget).__name__} failed to handle dashboard data: {e}"
                                )

    def test_widget_error_handling(self):
        """Test widget behavior with error data."""
        error_data = DashboardData(
            operator=OperatorInfo(status="ERROR", namespace="test"),
            error_infos=[
                ErrorInfo(
                    type="CONNECTION_ERROR",
                    message="Connection failed",
                    details="Could not connect to cluster",
                    suggestions=["Check cluster status"],
                )
            ],
        )

        widgets = [PodsWidget(), TemplatesWidget(), ResourcesWidget()]

        for widget in widgets:
            if hasattr(widget, "watch_dashboard_data"):
                # Mock the widget methods to avoid Textual app context issues
                with patch.object(widget, "clear", create=True):
                    with patch.object(widget, "add_row", create=True):
                        with patch.object(widget, "refresh", create=True):
                            widget.watch_dashboard_data(error_data)

    def test_widget_empty_data_handling(self):
        """Test widget behavior with empty data."""
        empty_data = DashboardData()

        widgets = [PodsWidget(), TemplatesWidget(), ResourcesWidget()]

        for widget in widgets:
            if hasattr(widget, "watch_dashboard_data"):
                # Should handle empty data gracefully (with mocking)
                with patch.object(widget, "clear", create=True):
                    with patch.object(widget, "add_row", create=True):
                        with patch.object(widget, "refresh", create=True):
                            widget.watch_dashboard_data(empty_data)


class TestInspectorWidget:
    """Test TemplateInspectorWidget component."""

    @pytest.fixture
    def inspector_widget(self):
        """Create a TemplateInspectorWidget instance."""
        from haproxy_template_ic.tui.widgets.inspector import TemplateInspectorWidget

        return TemplateInspectorWidget()

    @pytest.fixture
    def sample_templates_data(self):
        """Sample templates data for testing."""
        return {
            "haproxy.cfg": TemplateInfo(
                name="haproxy.cfg",
                type="config",
                status="rendered",
                size=1024,
                last_modified=datetime.now(),
            ),
            "backend.map": TemplateInfo(
                name="backend.map",
                type="map",
                status="valid",
                size=256,
                last_modified=datetime.now(),
            ),
            "ssl.pem": TemplateInfo(
                name="ssl.pem",
                type="certificate",
                status="valid",
                size=2048,
                last_modified=datetime.now(),
            ),
            "globals.snippet": TemplateInfo(
                name="globals.snippet",
                type="snippet",
                status="valid",
                size=128,
                last_modified=datetime.now(),
            ),
        }

    @pytest.fixture
    def sample_template_content(self):
        """Sample template content for testing."""
        return {
            "source": "global\n    daemon\n    log stdout:514 len 65536 local0 debug",
            "rendered": "global\n    daemon\n    log stdout:514 len 65536 local0 debug\n    stats socket /run/haproxy.sock",
            "type": "config",
            "errors": [],
        }

    def test_inspector_widget_initialization(self, inspector_widget):
        """Test TemplateInspectorWidget initialization."""
        from haproxy_template_ic.tui.widgets.inspector import TemplateInspectorWidget

        assert isinstance(inspector_widget, TemplateInspectorWidget)
        assert inspector_widget.templates_data == {}
        assert inspector_widget.template_content == {}
        assert inspector_widget.selected_template == ""
        assert inspector_widget.last_highlighted_template == ""
        assert inspector_widget.border_title == "Template Inspector"
        assert hasattr(inspector_widget, "compose")
        assert hasattr(inspector_widget, "on_mount")

    def test_inspector_widget_compose(self, inspector_widget):
        """Test TemplateInspectorWidget composition."""
        # Test that compose method exists and can be inspected
        assert hasattr(inspector_widget, "compose")
        assert callable(inspector_widget.compose)

        # We can't easily test compose() without a Textual app context,
        # but we can verify the method exists and is properly defined

    def test_inspector_widget_on_mount(self, inspector_widget):
        """Test on_mount initialization."""
        with patch.object(inspector_widget, "_update_template_tree") as mock_update:
            inspector_widget.on_mount()
            mock_update.assert_called_once()

    def test_inspector_widget_watch_templates_data(
        self, inspector_widget, sample_templates_data
    ):
        """Test watch_templates_data reactive property."""
        with patch.object(inspector_widget, "_update_template_tree") as mock_update:
            inspector_widget.templates_data = sample_templates_data

            # Should trigger template tree update
            assert mock_update.called

    def test_inspector_widget_watch_template_content(
        self, inspector_widget, sample_template_content
    ):
        """Test watch_template_content reactive property."""
        with patch.object(inspector_widget, "_update_content_display") as mock_update:
            inspector_widget.template_content = sample_template_content

            # Should trigger content display update
            assert mock_update.called

    def test_inspector_widget_watch_selected_template(
        self, inspector_widget, sample_templates_data
    ):
        """Test watch_selected_template reactive property."""
        inspector_widget.templates_data = sample_templates_data

        with patch.object(inspector_widget, "call_after_refresh") as mock_call_after:
            inspector_widget.selected_template = "haproxy.cfg"

            # Should call after refresh for highlighting
            assert mock_call_after.called

    def test_inspector_widget_detect_template_type(self, inspector_widget):
        """Test _detect_template_type method."""
        test_cases = [
            ("haproxy.cfg", "config"),
            ("test.cfg", "config"),
            ("backend.map", "map"),
            ("ssl.pem", "certificate"),
            ("cert.crt", "certificate"),
            ("key.key", "certificate"),
            ("globals.snippet", "snippet"),
            ("test-snippet", "snippet"),
            ("snippet-test", "snippet"),
            ("unknown.txt", "config"),  # Default
        ]

        for filename, expected_type in test_cases:
            result = inspector_widget._detect_template_type(filename)
            assert result == expected_type

    def test_inspector_widget_get_lexer_for_template(self, inspector_widget):
        """Test _get_lexer_for_template method."""
        test_cases = [
            ("haproxy.cfg", "config", "haproxy"),
            ("test.cfg", "config", "haproxy"),
            ("backend.map", "map", "yaml"),
            ("ssl.pem", "certificate", "text"),
            ("cert.crt", "certificate", "text"),
            ("globals.snippet", "snippet", "jinja2"),
            ("test.yaml", "unknown", "yaml"),
            ("test.json", "unknown", "json"),
            ("unknown.txt", "unknown", "jinja2"),  # Default
        ]

        for filename, template_type, expected_lexer in test_cases:
            result = inspector_widget._get_lexer_for_template(filename, template_type)
            assert result == expected_lexer

    def test_inspector_widget_set_template_content(
        self, inspector_widget, sample_template_content
    ):
        """Test set_template_content method."""
        inspector_widget.set_template_content(sample_template_content)
        assert inspector_widget.template_content == sample_template_content

    def test_inspector_widget_update_template_tree_empty(self, inspector_widget):
        """Test _update_template_tree with no templates."""
        from textual.widgets import Tree

        mock_tree = Mock(spec=Tree)
        mock_tree.root = Mock()

        with patch.object(inspector_widget, "query_one", return_value=mock_tree):
            inspector_widget._update_template_tree()

            # Should call clear and set label (may be called multiple times due to reactive properties)
            assert mock_tree.clear.called
            mock_tree.root.set_label.assert_called_with("No templates available")

    def test_inspector_widget_update_template_tree_with_data(
        self, inspector_widget, sample_templates_data
    ):
        """Test _update_template_tree with template data."""
        from textual.widgets import Tree

        mock_tree = Mock(spec=Tree)
        mock_tree.root = Mock()
        mock_config_node = Mock()
        mock_map_node = Mock()
        mock_cert_node = Mock()
        mock_snippet_node = Mock()

        mock_tree.root.add.side_effect = [
            mock_config_node,
            mock_map_node,
            mock_cert_node,
            mock_snippet_node,
        ]

        inspector_widget.templates_data = sample_templates_data

        with patch.object(inspector_widget, "query_one", return_value=mock_tree):
            inspector_widget._update_template_tree()

            mock_tree.clear.assert_called_once()
            mock_tree.root.set_label.assert_called_with("Templates")
            # Should expand all nodes
            mock_tree.root.expand_all.assert_called_once()

    def test_inspector_widget_highlight_template_in_tree(self, inspector_widget):
        """Test _highlight_template_in_tree method."""
        from textual.widgets import Tree

        # Mock tree and nodes
        mock_tree = Mock(spec=Tree)
        mock_root = Mock()
        mock_target_node = Mock()
        mock_parent_node = Mock()

        mock_target_node.label = "haproxy.cfg"
        mock_target_node.children = []  # Leaf node
        mock_target_node.parent = mock_parent_node
        mock_root.children = [mock_parent_node]
        mock_parent_node.children = [mock_target_node]
        mock_tree.root = mock_root

        with patch.object(inspector_widget, "query_one", return_value=mock_tree):
            inspector_widget._highlight_template_in_tree("haproxy.cfg")

            # Should expand parent and select node
            mock_parent_node.expand.assert_called_once()
            mock_root.expand_all.assert_called_once()
            mock_tree.select_node.assert_called_once_with(mock_target_node)
            mock_tree.action_select_cursor.assert_called_once()

    def test_inspector_widget_on_tree_node_highlighted_leaf(
        self, inspector_widget, sample_templates_data
    ):
        """Test on_tree_node_highlighted with leaf node."""

        # Mock event for leaf node
        mock_event = Mock()
        mock_event.node = Mock()
        mock_event.node.label = "haproxy.cfg"
        mock_event.node.is_root = False
        mock_event.node.children = []  # Leaf node

        inspector_widget.templates_data = sample_templates_data

        with patch.object(inspector_widget, "post_message") as mock_post:
            inspector_widget.on_tree_node_highlighted(mock_event)

            # Should post TemplateContentChanged message (may be called multiple times)
            assert mock_post.called
            # Find the TemplateContentChanged message among the calls
            template_content_changed_found = False
            for call in mock_post.call_args_list:
                message = call[0][0]
                if (
                    hasattr(message, "template_name")
                    and message.template_name == "haproxy.cfg"
                ):
                    template_content_changed_found = True
                    break
            assert template_content_changed_found

    def test_inspector_widget_on_tree_node_highlighted_non_leaf(self, inspector_widget):
        """Test on_tree_node_highlighted with non-leaf node."""
        # Mock event for non-leaf node (category)
        mock_event = Mock()
        mock_event.node = Mock()
        mock_event.node.label = "Configuration Files"
        mock_event.node.is_root = False
        mock_event.node.children = [Mock()]  # Has children

        with patch.object(inspector_widget, "post_message") as mock_post:
            inspector_widget.on_tree_node_highlighted(mock_event)

            # Should not post message for category nodes
            mock_post.assert_not_called()

    def test_inspector_widget_update_content_display_empty(self, inspector_widget):
        """Test _update_content_display with empty content."""
        from textual.containers import ScrollableContainer

        mock_scroll_container = Mock(spec=ScrollableContainer)

        with patch.object(
            inspector_widget, "query_one", return_value=mock_scroll_container
        ):
            inspector_widget._update_content_display()

            # Should remove children and add default message (may be called multiple times)
            assert mock_scroll_container.remove_children.called
            assert mock_scroll_container.mount.called

    def test_inspector_widget_update_content_display_with_content(
        self, inspector_widget, sample_template_content
    ):
        """Test _update_content_display with template content."""
        from textual.containers import ScrollableContainer

        mock_scroll_container = Mock(spec=ScrollableContainer)
        inspector_widget.selected_template = "haproxy.cfg"
        inspector_widget.template_content = sample_template_content

        with patch.object(
            inspector_widget, "query_one", return_value=mock_scroll_container
        ):
            inspector_widget._update_content_display()

            # Should update content display
            mock_scroll_container.remove_children.assert_called_once()
            # Should mount multiple Static widgets for different content parts
            assert mock_scroll_container.mount.call_count >= 1

    def test_inspector_widget_update_content_display_with_errors(
        self, inspector_widget
    ):
        """Test _update_content_display with errors."""
        from textual.containers import ScrollableContainer

        mock_scroll_container = Mock(spec=ScrollableContainer)
        inspector_widget.selected_template = "haproxy.cfg"
        inspector_widget.template_content = {
            "source": "invalid config",
            "rendered": "",
            "type": "config",
            "errors": ["Syntax error on line 1", "Missing required section"],
        }

        with patch.object(
            inspector_widget, "query_one", return_value=mock_scroll_container
        ):
            inspector_widget._update_content_display()

            # Should display errors
            mock_scroll_container.remove_children.assert_called_once()
            # Should mount content with error information
            assert mock_scroll_container.mount.call_count >= 1

    def test_inspector_widget_update_content_display_snippet(self, inspector_widget):
        """Test _update_content_display with snippet type."""
        from textual.containers import ScrollableContainer

        mock_scroll_container = Mock(spec=ScrollableContainer)
        inspector_widget.selected_template = "globals.snippet"
        inspector_widget.template_content = {
            "source": "# Global settings\ndaemon",
            "rendered": "",
            "type": "snippet",
            "errors": [],
        }

        with patch.object(
            inspector_widget, "query_one", return_value=mock_scroll_container
        ):
            inspector_widget._update_content_display()

            # Should display snippet information
            mock_scroll_container.remove_children.assert_called_once()
            assert mock_scroll_container.mount.call_count >= 1

    def test_inspector_widget_error_handling(self, inspector_widget):
        """Test error handling in various methods."""
        # Test _update_template_tree error handling
        with patch.object(
            inspector_widget, "query_one", side_effect=Exception("Test error")
        ):
            # Should not raise exception
            inspector_widget._update_template_tree()

        # Test _highlight_template_in_tree error handling
        with patch.object(
            inspector_widget, "query_one", side_effect=Exception("Test error")
        ):
            # Should not raise exception
            inspector_widget._highlight_template_in_tree("test.cfg")

        # Test _update_content_display error handling
        with patch.object(
            inspector_widget, "query_one", side_effect=Exception("Test error")
        ):
            # Should not raise exception
            inspector_widget._update_content_display()

    def test_inspector_widget_different_template_types(self):
        """Test TemplateInspectorWidget with different template types."""
        from haproxy_template_ic.tui.widgets.inspector import TemplateInspectorWidget

        template_types = ["haproxy_config", "map", "certificate", "snippet"]
        templates_data = {}

        for template_type in template_types:
            template = TemplateInfo(
                name=f"test.{template_type}",
                type=template_type,
                status="rendered",
                size=512,
                last_modified=datetime.now(),
            )
            templates_data[template.name] = template

        widget = TemplateInspectorWidget()
        widget.templates_data = templates_data

        assert len(widget.templates_data) == len(template_types)

    def test_inspector_widget_reactive_properties(
        self, inspector_widget, sample_templates_data, sample_template_content
    ):
        """Test all reactive properties work correctly."""
        # Test templates_data reactive property
        inspector_widget.templates_data = sample_templates_data
        assert inspector_widget.templates_data == sample_templates_data

        # Test template_content reactive property
        inspector_widget.template_content = sample_template_content
        assert inspector_widget.template_content == sample_template_content

        # Test selected_template reactive property
        inspector_widget.selected_template = "haproxy.cfg"
        assert inspector_widget.selected_template == "haproxy.cfg"

        # Test last_highlighted_template reactive property
        inspector_widget.last_highlighted_template = "backend.map"
        assert inspector_widget.last_highlighted_template == "backend.map"

    def test_inspector_widget_edge_cases(self, inspector_widget):
        """Test edge cases and error conditions."""
        # Test with None values
        inspector_widget.templates_data = None
        inspector_widget.template_content = None
        inspector_widget.selected_template = None

        # Test with empty string
        inspector_widget.selected_template = ""
        assert inspector_widget.selected_template == ""

        # Test type detection with edge cases - check the actual logic
        edge_cases = [
            ("unknown.xyz", "config"),  # Falls back to config
            ("file", "config"),  # Falls back to config
            ("", "config"),  # Falls back to config
            ("test.pem", "certificate"),
            ("host.map", "map"),
        ]

        for filename, expected_type in edge_cases:
            result = inspector_widget._detect_template_type(filename)
            assert result == expected_type

    def test_inspector_widget_content_methods(self, inspector_widget):
        """Test content-related methods."""
        # Test _update_content_display without arguments (uses current state)
        inspector_widget._update_content_display()

        # Test _get_lexer_for_template with different types
        lexer_haproxy = inspector_widget._get_lexer_for_template(
            "haproxy.cfg", "config"
        )
        assert lexer_haproxy is not None

        lexer_map = inspector_widget._get_lexer_for_template("host.map", "map")
        assert lexer_map is not None

        # Test with unknown type
        lexer_unknown = inspector_widget._get_lexer_for_template("test.xyz", "unknown")
        assert lexer_unknown is not None

    """Enhanced tests for ActivityWidget component."""

    @pytest.fixture
    def activity_widget(self):
        """Create an ActivityWidget instance."""
        return ActivityWidget()

    @pytest.fixture
    def sample_activities(self):
        """Sample activity events."""
        return [
            ActivityEvent(
                type="RESOURCE_UPDATE",
                message="Ingress updated",
                timestamp=datetime.now().isoformat(),
                source="operator",
                metadata={"resource_type": "ingress"},
            ),
            ActivityEvent(
                type="SYNC",
                message="Sync warning",
                timestamp=datetime.now().isoformat(),
                source="synchronizer",
                metadata={},
            ),
            ActivityEvent(
                type="ERROR",
                message="Connection failed",
                timestamp=datetime.now().isoformat(),
                source="dataplane",
                metadata={"error_code": "CONNECTION_REFUSED"},
            ),
        ]

    def test_activity_widget_update_with_activities(
        self, activity_widget, sample_activities
    ):
        """Test activity widget with activity data."""
        with patch.object(activity_widget, "write") as mock_write:
            # Create dashboard data with activities
            dashboard_data = DashboardData(activity=sample_activities)
            activity_widget.dashboard_data = dashboard_data

            # Should have called write for the activity entries
            assert mock_write.call_count >= len(sample_activities)

    def test_activity_widget_empty_activities(self, activity_widget):
        """Test activity widget with empty activities."""
        dashboard_data = DashboardData(activity=[])

        with patch.object(activity_widget, "_add_activity_entry") as mock_add_entry:
            activity_widget.watch_dashboard_data(dashboard_data)
            # Should not call _add_activity_entry for empty activities
            mock_add_entry.assert_not_called()

    def test_activity_widget_update_with_new_data(
        self, activity_widget, sample_activities
    ):
        """Test activity widget updates with new data."""
        # First update
        dashboard_data = DashboardData(activity=sample_activities[:1])
        activity_widget.watch_dashboard_data(dashboard_data)
        assert activity_widget._last_activity_count == 1

        # Second update with more activities
        dashboard_data = DashboardData(activity=sample_activities)
        with patch.object(activity_widget, "_add_activity_entry") as mock_add_entry:
            activity_widget.watch_dashboard_data(dashboard_data)
            # Should only add new entries (2 new ones)
            assert mock_add_entry.call_count == 2

    def test_activity_widget_format_activity_with_metadata(self, activity_widget):
        """Test activity formatting with metadata."""
        activity = ActivityEvent(
            type="RESOURCE_UPDATE",
            message="Resource updated",
            timestamp=datetime.now().isoformat(),
            source="operator",
            metadata={"resource_type": "ingress", "resource_name": "test-ingress"},
        )

        # Test that widget can handle activities with metadata
        dashboard_data = DashboardData(activity=[activity])
        # Should not raise an exception
        activity_widget.watch_dashboard_data(dashboard_data)

    def test_activity_widget_format_activity_no_metadata(self, activity_widget):
        """Test activity formatting without metadata."""
        activity = ActivityEvent(
            type="TEST",
            message="Test message",
            timestamp=datetime.now().isoformat(),
            source="test",
            metadata=None,
        )

        # Test that widget can handle activities with no metadata
        dashboard_data = DashboardData(activity=[activity])
        # Should not raise an exception
        activity_widget.watch_dashboard_data(dashboard_data)


class TestTemplatesWidgetEnhanced:
    """Enhanced tests for TemplatesWidget component."""

    @pytest.fixture
    def templates_widget(self):
        """Create a TemplatesWidget instance."""
        return TemplatesWidget()

    @pytest.fixture
    def sample_templates(self):
        """Sample template data."""
        return [
            TemplateInfo(
                name="haproxy.cfg",
                type="haproxy_config",
                status="rendered",
                size=2048,
                last_modified=datetime.now(),
            ),
            TemplateInfo(
                name="host.map",
                type="map",
                status="error",
                size=512,
                last_modified=datetime.now(),
            ),
            TemplateInfo(
                name="cert.pem",
                type="certificate",
                status="rendered",
                size=4096,
                last_modified=datetime.now(),
            ),
        ]

    def test_templates_widget_with_different_types(self, templates_widget):
        """Test templates widget with different template types."""
        # Mock the add_columns method to avoid Textual app context issues
        with patch.object(templates_widget, "add_columns"):
            with patch.object(templates_widget, "clear"):
                with patch.object(templates_widget, "add_row") as mock_add_row:
                    templates_widget.on_mount()  # Initialize columns

                    template_types = ["haproxy_config", "map", "certificate", "snippet"]
                    templates_data = {}

                    for template_type in template_types:
                        template = TemplateInfo(
                            name=f"test.{template_type}",
                            type=template_type,
                            status="rendered",
                            size=1024,
                            last_modified=datetime.now(),
                        )
                        templates_data[template.name] = template

                    dashboard_data = DashboardData(templates=templates_data)
                    templates_widget.watch_dashboard_data(dashboard_data)

                    # Should have called add_row for each template
                    assert mock_add_row.call_count == len(template_types)

    def test_templates_widget_format_template_different_statuses(
        self, templates_widget
    ):
        """Test template formatting with different statuses."""
        # Mock the widget methods to test status handling
        with patch.object(templates_widget, "add_columns"):
            with patch.object(templates_widget, "clear"):
                with patch.object(templates_widget, "add_row") as mock_add_row:
                    templates_widget.on_mount()

                    # Test different statuses
                    template = TemplateInfo(
                        name="test.cfg",
                        type="config",
                        status="valid",
                        size=1024,
                        last_modified=datetime.now(),
                    )
                    templates_data = {"test.cfg": template}
                    dashboard_data = DashboardData(templates=templates_data)
                    templates_widget.watch_dashboard_data(dashboard_data)

                    # Should have called add_row with status indicator
                    mock_add_row.assert_called_once()
                    call_args = mock_add_row.call_args[0]
                    assert (
                        "✅" in call_args[0]
                    )  # Status indicator should be first column

    def test_templates_widget_format_size(self, templates_widget):
        """Test size formatting in templates widget."""
        # Mock the widget methods to test size formatting
        with patch.object(templates_widget, "add_columns"):
            with patch.object(templates_widget, "clear"):
                with patch.object(templates_widget, "add_row") as mock_add_row:
                    templates_widget.on_mount()

                    # Test size formatting
                    template = TemplateInfo(
                        name="test.cfg",
                        type="config",
                        status="valid",
                        size=1024,
                        last_modified=datetime.now(),
                    )
                    templates_data = {"test.cfg": template}
                    dashboard_data = DashboardData(templates=templates_data)
                    templates_widget.watch_dashboard_data(dashboard_data)

                    # Should have called add_row with formatted size
                    mock_add_row.assert_called_once()
                    call_args = mock_add_row.call_args[0]
                    # Size should be formatted (1024 bytes = 1.0KB)
                    assert "1.0KB" in call_args[3]  # Size is in 4th column (index 3)

    def test_templates_widget_on_row_selected(self, templates_widget, sample_templates):
        """Test row selection in templates widget."""
        # Mock the DataTable methods and test the actual row selection event handler
        with patch.object(templates_widget, "get_row") as mock_get_row:
            with patch.object(templates_widget, "post_message") as mock_post_message:
                # Mock row data - template name is in second column
                mock_get_row.return_value = [
                    "✅",  # Status indicator
                    "haproxy.cfg",  # Template name
                    "config",  # Type
                    "2.0KB",  # Size
                    "2m ago",  # Last modified
                ]

                # Create mock event with row_key
                mock_event = Mock()
                mock_event.row_key = "test_row_key"

                # Call the actual event handler method
                templates_widget.on_data_table_row_selected(mock_event)

                # Should post TemplateSelected message with template name
                mock_post_message.assert_called_once()
                call_args = mock_post_message.call_args[0][0]
                assert call_args.template_name == "haproxy.cfg"

    def test_templates_widget_on_row_selected_no_template(self, templates_widget):
        """Test row selection when template not found."""
        with patch.object(templates_widget, "get_row") as mock_get_row:
            with patch.object(templates_widget, "post_message") as mock_post_message:
                # Mock row data with "No templates found" message
                mock_get_row.return_value = [
                    "ℹ️",  # Status indicator
                    "No templates found",  # Template name
                    "Check ConfigMap",  # Type
                    "0B",  # Size
                    "N/A",  # Last modified
                ]

                # Create mock event
                mock_event = Mock()
                mock_event.row_key = "test_row_key"

                # Should not post message for "No templates found" row
                templates_widget.on_data_table_row_selected(mock_event)

                # Should not post message for informational row
                mock_post_message.assert_not_called()

    def test_templates_widget_reactive_property(
        self, templates_widget, sample_templates
    ):
        """Test templates reactive property."""
        # Setting templates should work
        templates_widget.templates = sample_templates
        assert templates_widget.templates == sample_templates

    def test_templates_widget_watch_templates_update(
        self, templates_widget, sample_templates
    ):
        """Test templates watcher method."""
        with patch.object(templates_widget, "clear"):
            with patch.object(templates_widget, "add_row") as mock_add_row:
                with patch.object(templates_widget, "refresh"):
                    from haproxy_template_ic.tui.models import DashboardData

                    dashboard_data = DashboardData(
                        templates={t.name: t for t in sample_templates}
                    )
                    templates_widget.watch_dashboard_data(dashboard_data)

                    # Should add row for each template
                    assert mock_add_row.call_count == len(sample_templates)


class TestInspectorWidgetCoverageEnhancement:
    """Enhanced coverage tests for TemplateInspectorWidget missing lines."""

    @pytest.fixture
    def inspector_widget(self):
        """Create a TemplateInspectorWidget instance."""
        return TemplateInspectorWidget()

    def test_inspector_widget_compose_coverage(self, inspector_widget):
        """Test compose method to cover lines 49-56."""
        # Mock Vertical and Static widgets to test composition without Textual context
        with (
            patch(
                "haproxy_template_ic.tui.widgets.inspector.Vertical"
            ) as mock_vertical,
            patch("haproxy_template_ic.tui.widgets.inspector.Static") as mock_static,
            patch("haproxy_template_ic.tui.widgets.inspector.Tree") as mock_tree,
            patch(
                "haproxy_template_ic.tui.widgets.inspector.ScrollableContainer"
            ) as mock_scroll,
        ):
            # Mock context managers
            mock_vertical.return_value.__enter__ = lambda self: self
            mock_vertical.return_value.__exit__ = lambda self, *args: None
            mock_scroll.return_value.__enter__ = lambda self: self
            mock_scroll.return_value.__exit__ = lambda self, *args: None

            # Call compose to trigger widget creation
            list(inspector_widget.compose())

            # Should create two vertical panels
            assert mock_vertical.call_count >= 2
            # Should create header static widgets
            mock_static.assert_any_call("Templates", classes="panel-header")
            mock_static.assert_any_call("Content", classes="panel-header")
            # Should create tree widget
            mock_tree.assert_called_once_with("Templates", id="template-tree")
            # Should create scrollable container
            mock_scroll.assert_called_once_with(id="template-scroll")

    def test_inspector_widget_detect_template_type_fallback(self, inspector_widget):
        """Test _detect_template_type fallback to cover line 102."""
        # Test template info without type attribute
        mock_template_info = Mock(spec=[])  # No 'type' attribute

        templates_data = {"test.unknown": mock_template_info}
        inspector_widget.templates_data = templates_data

        # Should call _detect_template_type for fallback
        result = inspector_widget._detect_template_type("test.unknown")
        assert result == "config"  # Default fallback

    def test_inspector_widget_highlight_template_selected_check(self, inspector_widget):
        """Test _update_template_tree with selected template to cover line 139."""
        from textual.widgets import Tree

        # Mock tree and setup selected template
        mock_tree = Mock(spec=Tree)
        mock_tree.root = Mock()
        inspector_widget.selected_template = "test.cfg"
        inspector_widget.templates_data = {"test.cfg": Mock()}

        with patch.object(inspector_widget, "query_one", return_value=mock_tree):
            with patch.object(
                inspector_widget, "_highlight_template_in_tree"
            ) as mock_highlight:
                inspector_widget._update_template_tree()

                # Should call highlight method when selected template is set
                mock_highlight.assert_called_with("test.cfg")

    def test_inspector_widget_highlight_template_node_not_found(self, inspector_widget):
        """Test _highlight_template_in_tree when node not found to cover line 160."""
        from textual.widgets import Tree

        # Mock tree with no matching nodes
        mock_tree = Mock(spec=Tree)
        mock_root = Mock()
        mock_root.children = []  # No children
        mock_tree.root = mock_root

        with patch.object(inspector_widget, "query_one", return_value=mock_tree):
            # Should not raise exception when template node is not found
            inspector_widget._highlight_template_in_tree("nonexistent.cfg")

    def test_inspector_widget_highlight_template_warning_log(self, inspector_widget):
        """Test _highlight_template_in_tree warning log to cover line 179."""
        from textual.widgets import Tree

        # Mock tree with no matching nodes to trigger warning
        mock_tree = Mock(spec=Tree)
        mock_root = Mock()
        mock_root.children = []
        mock_tree.root = mock_root

        with patch.object(inspector_widget, "query_one", return_value=mock_tree):
            with patch(
                "haproxy_template_ic.tui.widgets.inspector.logger"
            ) as mock_logger:
                inspector_widget._highlight_template_in_tree("missing.cfg")

                # Should log warning when template node is not found
                assert mock_logger.warning.called

    def test_inspector_widget_tree_node_highlighted_root_check(self, inspector_widget):
        """Test on_tree_node_highlighted with root node to cover lines 223-224."""
        # Mock event with root node
        mock_event = Mock()
        mock_event.node = Mock()
        mock_event.node.is_root = True
        mock_event.node.children = []

        with patch.object(inspector_widget, "post_message") as mock_post:
            inspector_widget.on_tree_node_highlighted(mock_event)

            # Should not post message for root node
            mock_post.assert_not_called()

    def test_inspector_widget_tree_node_highlighted_message_post(
        self, inspector_widget
    ):
        """Test on_tree_node_highlighted message posting to cover line 228."""
        # Mock event with leaf node
        mock_event = Mock()
        mock_event.node = Mock()
        mock_event.node.is_root = False
        mock_event.node.children = []
        mock_event.node.label = "test.cfg"

        inspector_widget.templates_data = {"test.cfg": Mock()}

        with patch.object(inspector_widget, "post_message") as mock_post:
            inspector_widget.on_tree_node_highlighted(mock_event)

            # Should post a message
            assert mock_post.called

    def test_inspector_widget_tree_node_highlighted_set_selected(
        self, inspector_widget
    ):
        """Test on_tree_node_highlighted setting selected template to cover line 241."""
        # Mock event with leaf node
        mock_event = Mock()
        mock_event.node = Mock()
        mock_event.node.is_root = False
        mock_event.node.children = []
        mock_event.node.label = "selected.cfg"

        inspector_widget.templates_data = {"selected.cfg": Mock()}

        inspector_widget.on_tree_node_highlighted(mock_event)

        # Should set selected_template
        assert inspector_widget.selected_template == "selected.cfg"

    def test_inspector_widget_update_content_display_source_section(
        self, inspector_widget
    ):
        """Test _update_content_display source section to cover lines 296-298."""
        from textual.containers import ScrollableContainer

        mock_scroll_container = Mock(spec=ScrollableContainer)
        inspector_widget.selected_template = "test.cfg"
        inspector_widget.template_content = {
            "source": "test source content",
            "type": "config",
            "errors": [],
        }

        with patch.object(
            inspector_widget, "query_one", return_value=mock_scroll_container
        ):
            with patch(
                "haproxy_template_ic.tui.widgets.inspector.Static"
            ) as mock_static:
                inspector_widget._update_content_display()

                # Should create static widgets for source content
                assert mock_static.call_count >= 2  # Header + content

    def test_inspector_widget_update_content_display_rendered_section(
        self, inspector_widget
    ):
        """Test _update_content_display rendered section to cover lines 337-339."""
        from textual.containers import ScrollableContainer

        mock_scroll_container = Mock(spec=ScrollableContainer)
        inspector_widget.selected_template = "test.cfg"
        inspector_widget.template_content = {
            "source": "source content",
            "rendered": "rendered content",
            "type": "config",
            "errors": [],
        }

        with patch.object(
            inspector_widget, "query_one", return_value=mock_scroll_container
        ):
            with patch(
                "haproxy_template_ic.tui.widgets.inspector.Static"
            ) as mock_static:
                inspector_widget._update_content_display()

                # Should create static widgets including rendered section
                assert mock_static.call_count >= 4  # Source + rendered sections

    def test_inspector_widget_update_content_display_snippet_no_rendered(
        self, inspector_widget
    ):
        """Test _update_content_display for snippet without rendered to cover line 341."""
        from textual.containers import ScrollableContainer

        mock_scroll_container = Mock(spec=ScrollableContainer)
        inspector_widget.selected_template = "snippet.cfg"
        inspector_widget.template_content = {
            "source": "snippet content",
            "rendered": "",  # Empty rendered for snippets
            "type": "snippet",
            "errors": [],
        }

        with patch.object(
            inspector_widget, "query_one", return_value=mock_scroll_container
        ):
            with patch(
                "haproxy_template_ic.tui.widgets.inspector.Static"
            ) as mock_static:
                inspector_widget._update_content_display()

                # Should create static widgets but skip rendered section for snippets
                mock_static.assert_called()

    def test_inspector_widget_update_content_display_errors_section(
        self, inspector_widget
    ):
        """Test _update_content_display errors section to cover lines 356-357."""
        from textual.containers import ScrollableContainer

        mock_scroll_container = Mock(spec=ScrollableContainer)
        inspector_widget.selected_template = "test.cfg"
        inspector_widget.template_content = {
            "source": "source content",
            "type": "config",
            "errors": ["Error 1", "Error 2"],
        }

        with patch.object(
            inspector_widget, "query_one", return_value=mock_scroll_container
        ):
            with patch(
                "haproxy_template_ic.tui.widgets.inspector.Static"
            ) as mock_static:
                inspector_widget._update_content_display()

                # Should create static widgets including errors section
                assert mock_static.call_count >= 3  # Source + errors

    def test_inspector_widget_update_content_display_exception_handling(
        self, inspector_widget
    ):
        """Test _update_content_display exception handling to cover line 363."""
        # Mock query_one to raise exception
        with patch.object(
            inspector_widget, "query_one", side_effect=Exception("Query error")
        ):
            with patch(
                "haproxy_template_ic.tui.widgets.inspector.logger"
            ) as mock_logger:
                inspector_widget._update_content_display()

                # Should log error when exception occurs (may be called multiple times due to reactivity)
                assert mock_logger.error.called
