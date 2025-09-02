"""
Unit tests for TUI widget components.

Tests widget data binding, user interactions, and rendering behavior.
"""

import pytest
from unittest.mock import patch, PropertyMock
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

    def test_performance_widget_initialization(self, performance_widget):
        """Test PerformanceWidget initialization."""
        assert hasattr(performance_widget, "border_title")
        # Performance widget might be a custom container widget

    def test_performance_widget_data_update_with_metrics(
        self, performance_widget, sample_performance_data
    ):
        """Test widget update with performance data."""
        dashboard_data = DashboardData(performance=sample_performance_data)

        # Performance widget likely updates text content
        with patch.object(performance_widget, "watch_dashboard_data") as mock_watch:
            mock_watch.return_value = None

            # Call the watch method if it exists
            if hasattr(performance_widget, "watch_dashboard_data"):
                performance_widget.watch_dashboard_data(dashboard_data)


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
                timestamp=datetime.now(),
                type="RELOAD",
                source="dataplane",
                message="Configuration reloaded successfully",
            ),
            ActivityEvent(
                timestamp=datetime.now(),
                type="SYNC",
                source="operator",
                message="Resources synchronized",
                metadata={"resource_type": "ingresses"},
            ),
            ActivityEvent(
                timestamp=datetime.now(),
                type="ERROR",
                source="template",
                message="Template rendering failed",
            ),
        ]

    def test_activity_widget_initialization(self, activity_widget):
        """Test ActivityWidget initialization."""
        assert hasattr(activity_widget, "border_title")
        # Activity widget might be a custom container or list widget

    def test_activity_widget_data_update_with_events(
        self, activity_widget, sample_activity_data
    ):
        """Test widget update with activity events."""
        dashboard_data = DashboardData(activity=sample_activity_data)

        # Activity widget might update with scrolling log content
        with patch.object(activity_widget, "watch_dashboard_data") as mock_watch:
            mock_watch.return_value = None

            if hasattr(activity_widget, "watch_dashboard_data"):
                activity_widget.watch_dashboard_data(dashboard_data)

    def test_activity_widget_data_update_empty(self, activity_widget):
        """Test widget update with no activity events."""
        dashboard_data = DashboardData(activity=[])

        if hasattr(activity_widget, "watch_dashboard_data"):
            activity_widget.watch_dashboard_data(dashboard_data)


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
        assert hasattr(
            header_widget, "compose"
        )  # Header widgets typically have compose method

    def test_header_widget_data_update_with_operator_info(
        self, header_widget, sample_operator_data
    ):
        """Test widget update with operator information."""
        dashboard_data = DashboardData(operator=sample_operator_data)

        if hasattr(header_widget, "watch_dashboard_data"):
            header_widget.watch_dashboard_data(dashboard_data)

    def test_header_widget_status_formatting(self, header_widget):
        """Test status indicator formatting."""
        # Test different status values
        statuses = ["RUNNING", "ERROR", "DISCONNECTED", "UNKNOWN"]

        for status in statuses:
            operator = OperatorInfo(status=status, namespace="test")
            dashboard_data = DashboardData(operator=operator)

            if hasattr(header_widget, "watch_dashboard_data"):
                header_widget.watch_dashboard_data(dashboard_data)


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
