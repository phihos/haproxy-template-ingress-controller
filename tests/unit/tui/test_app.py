"""
Unit tests for the TUI App main application class.

Tests app initialization, screen management, reactive properties,
keyboard bindings, and data update handling.
"""

import asyncio
import pytest
from unittest.mock import AsyncMock, Mock, patch
from datetime import datetime, timezone


from haproxy_template_ic.tui.app import TuiApp
from haproxy_template_ic.tui.models import (
    DashboardData,
    OperatorInfo,
    PodInfo,
    TemplateInfo,
    PerformanceInfo,
)
from haproxy_template_ic.activity import ActivityEvent
from haproxy_template_ic.tui.widgets.templates import TemplateSelected


# Create simple fixture functions since they're not in fixtures.py
def sample_dashboard_data():
    """Sample dashboard data."""
    return DashboardData(
        operator=OperatorInfo(
            status="RUNNING",
            version="1.2.3",
            namespace="test-namespace",
            configmap_name="test-config",
        ),
        pods=[
            PodInfo(
                name="test-pod",
                status="Running",
                ip="10.0.0.1",
                cpu="100m",
                memory="128Mi",
            )
        ],
        templates=[
            TemplateInfo(
                name="test.cfg",
                type="haproxy_config",
                status="rendered",
                size=1024,
                last_modified=datetime.now(timezone.utc),
            )
        ],
        performance=PerformanceInfo(
            requests_per_second=100,
            response_time_avg=20.5,
            error_rate=0.01,
            active_connections=500,
        ),
        activities=[
            ActivityEvent(
                timestamp=datetime.now(timezone.utc),
                level="info",
                type="TEST",
                source="test",
                message="Test event",
            )
        ],
    )


class TestTuiApp:
    """Test the main TuiApp application class."""

    @pytest.fixture
    def app_params(self):
        """Default app parameters."""
        return {
            "namespace": "test-namespace",
            "context": "test-context",
            "refresh_interval": 5,
            "deployment_name": "test-deployment",
            "socket_path": "/tmp/test.sock",
        }

    @pytest.fixture
    def tui_app(self, app_params):
        """Create a TuiApp instance."""
        return TuiApp(**app_params)

    @pytest.fixture
    def mock_dashboard_service(self):
        """Mock DashboardService."""
        service = AsyncMock()
        service.get_dashboard_data.return_value = sample_dashboard_data()
        return service

    def test_app_initialization(self, app_params):
        """Test TuiApp initialization with parameters."""
        app = TuiApp(**app_params)

        assert app.namespace == "test-namespace"
        assert app.context == "test-context"
        assert app.refresh_interval == 5
        assert app.deployment_name == "test-deployment"
        assert app.socket_path == "/tmp/test.sock"
        # Check reactive properties are initialized
        assert app.operator_status.status == "UNKNOWN"
        assert app.pods == []
        assert app.templates == {}
        assert app.loading is True

    def test_app_initialization_defaults(self):
        """Test TuiApp initialization with default parameters."""
        app = TuiApp(namespace="default")

        assert app.namespace == "default"
        assert app.context is None
        assert app.refresh_interval == 5
        assert app.deployment_name == "haproxy-template-ic"
        assert app.socket_path is None

    @patch("haproxy_template_ic.tui.app.DashboardService")
    def test_compose_creates_widgets(self, mock_service_class, tui_app):
        """Test that compose creates all required widgets."""
        mock_service = AsyncMock()
        mock_service_class.return_value = mock_service

        # Mock the compose result to avoid actual Textual rendering
        with patch.object(tui_app, "compose") as mock_compose:
            mock_compose.return_value = []
            list(tui_app.compose())
            mock_compose.assert_called_once()

    def test_css_property(self, tui_app):
        """Test CSS property returns path to styles."""
        css_path = str(tui_app.CSS_PATH)
        assert css_path.endswith("styles.css")

    def test_title_property(self, tui_app):
        """Test app title property."""
        assert tui_app.TITLE == "HAProxy Template IC Dashboard"

    def test_bindings_defined(self, tui_app):
        """Test that keyboard bindings are defined."""
        bindings = tui_app.BINDINGS
        assert len(bindings) > 0

        # Check for expected bindings
        binding_keys = [binding.key for binding in bindings]
        assert "q" in binding_keys
        assert "r" in binding_keys
        assert "h" in binding_keys
        assert "t" in binding_keys
        assert "d" in binding_keys

    @pytest.mark.asyncio
    async def test_on_mount_starts_dashboard_service(self, tui_app):
        """Test that on_mount starts the dashboard service."""
        with patch(
            "haproxy_template_ic.tui.app.DashboardService"
        ) as mock_service_class:
            mock_service = AsyncMock()
            mock_service_class.return_value = mock_service

            with patch.object(tui_app, "_start_update_task") as mock_start_task:
                await tui_app.on_mount()

                mock_service_class.assert_called_once_with(
                    namespace="test-namespace",
                    context="test-context",
                    deployment_name="test-deployment",
                    socket_path="/tmp/test.sock",
                )
                mock_start_task.assert_called_once()

    @pytest.mark.asyncio
    async def test_on_unmount_stops_services(self, tui_app):
        """Test that on_unmount stops services properly."""
        # Set up mocked services
        tui_app._update_task = AsyncMock()
        tui_app._dashboard_service = AsyncMock()

        with patch.object(tui_app, "_stop_update_task") as mock_stop_task:
            await tui_app.on_unmount()

            mock_stop_task.assert_called_once()
            tui_app._dashboard_service.cleanup.assert_called_once()

    @pytest.mark.asyncio
    async def test_start_update_task_creates_task(self, tui_app):
        """Test that _start_update_task creates a background task."""
        with patch("asyncio.create_task") as mock_create_task:
            mock_task = AsyncMock()
            mock_create_task.return_value = mock_task

            await tui_app._start_update_task()

            mock_create_task.assert_called_once()
            assert tui_app._update_task == mock_task

    @pytest.mark.asyncio
    async def test_stop_update_task_cancels_task(self, tui_app):
        """Test that _stop_update_task cancels the background task."""
        mock_task = AsyncMock()
        tui_app._update_task = mock_task

        await tui_app._stop_update_task()

        mock_task.cancel.assert_called_once()
        assert tui_app._update_task is None

    @pytest.mark.asyncio
    async def test_stop_update_task_handles_no_task(self, tui_app):
        """Test that _stop_update_task handles case with no task."""
        tui_app._update_task = None

        # Should not raise an exception
        await tui_app._stop_update_task()

        assert tui_app._update_task is None

    @pytest.mark.asyncio
    async def test_update_dashboard_data_success(
        self, tui_app, mock_dashboard_service, sample_dashboard_data
    ):
        """Test successful dashboard data update."""
        tui_app._dashboard_service = mock_dashboard_service

        await tui_app._update_dashboard_data()

        mock_dashboard_service.get_dashboard_data.assert_called_once()
        assert tui_app.dashboard_data == sample_dashboard_data

    @pytest.mark.asyncio
    async def test_update_dashboard_data_handles_error(
        self, tui_app, mock_dashboard_service
    ):
        """Test dashboard data update error handling."""
        tui_app._dashboard_service = mock_dashboard_service
        mock_dashboard_service.get_dashboard_data.side_effect = Exception("Test error")

        with patch("haproxy_template_ic.tui.app.logger") as mock_logger:
            await tui_app._update_dashboard_data()

            mock_logger.error.assert_called_once()
            assert tui_app.dashboard_data is None

    @pytest.mark.asyncio
    async def test_periodic_update_loop(self, tui_app):
        """Test the periodic update loop."""
        update_count = 0

        async def mock_update():
            nonlocal update_count
            update_count += 1
            if update_count >= 2:
                # Cancel after 2 updates to avoid infinite loop
                raise asyncio.CancelledError()

        with patch.object(tui_app, "_update_dashboard_data", side_effect=mock_update):
            with patch("asyncio.sleep", new_callable=AsyncMock):
                try:
                    await tui_app._periodic_update()
                except asyncio.CancelledError:
                    pass

                assert update_count >= 2

    def test_action_quit(self, tui_app):
        """Test quit action."""
        with patch.object(tui_app, "exit") as mock_exit:
            tui_app.action_quit()
            mock_exit.assert_called_once()

    @pytest.mark.asyncio
    async def test_action_refresh(self, tui_app):
        """Test manual refresh action."""
        with patch.object(tui_app, "_update_dashboard_data") as mock_update:
            await tui_app.action_refresh()
            mock_update.assert_called_once()

    def test_action_show_help(self, tui_app):
        """Test show help action."""
        with patch.object(tui_app, "push_screen") as mock_push:
            tui_app.action_show_help()
            mock_push.assert_called_once()

    def test_action_show_debug(self, tui_app):
        """Test show debug action."""
        with patch.object(tui_app, "push_screen") as mock_push:
            tui_app.action_show_debug()
            mock_push.assert_called_once()

    def test_action_template_inspector(self, tui_app):
        """Test template inspector action."""
        with patch.object(tui_app, "push_screen") as mock_push:
            tui_app.action_template_inspector()
            mock_push.assert_called_once()

    @pytest.mark.asyncio
    async def test_on_template_selected(self, tui_app):
        """Test template selection handling."""
        template = TemplateInfo(
            name="test.cfg",
            type="haproxy_config",
            status="rendered",
            size=1024,
            last_modified=datetime.now(timezone.utc),
        )

        message = TemplateSelected(template=template)

        with patch.object(tui_app, "push_screen") as mock_push:
            await tui_app.on_template_selected(message)
            mock_push.assert_called_once()

    def test_watch_dashboard_data_updates_widgets(self, tui_app, sample_dashboard_data):
        """Test that dashboard_data watcher updates widgets."""
        # Mock the widgets
        mock_header = Mock()
        mock_activity = Mock()
        mock_pods = Mock()
        mock_resources = Mock()
        mock_templates = Mock()
        mock_performance = Mock()

        # Mock query_one to return our mocked widgets
        def mock_query_one(selector):
            if selector == "HeaderWidget":
                return mock_header
            elif selector == "ActivityWidget":
                return mock_activity
            elif selector == "PodsWidget":
                return mock_pods
            elif selector == "ResourcesWidget":
                return mock_resources
            elif selector == "TemplatesWidget":
                return mock_templates
            elif selector == "PerformanceWidget":
                return mock_performance
            return Mock()

        with patch.object(tui_app, "query_one", side_effect=mock_query_one):
            # Trigger the watcher by setting dashboard_data
            tui_app.dashboard_data = sample_dashboard_data

            # Check that all widgets were updated
            assert mock_header.operator_info == sample_dashboard_data.operator_info
            assert mock_activity.activities == sample_dashboard_data.activities
            assert mock_pods.pods == sample_dashboard_data.pods
            assert mock_resources.resources == sample_dashboard_data.resources
            assert mock_templates.templates == sample_dashboard_data.templates
            assert mock_performance.performance == sample_dashboard_data.performance

    def test_watch_dashboard_data_handles_missing_widgets(
        self, tui_app, sample_dashboard_data
    ):
        """Test that dashboard_data watcher handles missing widgets gracefully."""
        # Mock query_one to raise NoMatches for some widgets
        from textual.css.query import NoMatches

        def mock_query_one(selector):
            if selector in ["HeaderWidget", "ActivityWidget"]:
                raise NoMatches(f"No {selector} found")
            return Mock()

        with patch.object(tui_app, "query_one", side_effect=mock_query_one):
            with patch("haproxy_template_ic.tui.app.logger") as mock_logger:
                # Should not raise an exception
                tui_app.dashboard_data = sample_dashboard_data

                # Should log debug messages for missing widgets
                assert mock_logger.debug.call_count >= 2

    def test_watch_dashboard_data_none_value(self, tui_app):
        """Test that dashboard_data watcher handles None values."""
        with patch.object(tui_app, "query_one") as mock_query_one:
            # Setting to None should not call query_one
            tui_app.dashboard_data = None
            mock_query_one.assert_not_called()

    @pytest.mark.asyncio
    async def test_dashboard_data_reactive_property(
        self, tui_app, sample_dashboard_data
    ):
        """Test dashboard_data as a reactive property."""
        # Initial value should be None
        assert tui_app.dashboard_data is None

        # Setting value should trigger reactive update
        tui_app.dashboard_data = sample_dashboard_data
        assert tui_app.dashboard_data == sample_dashboard_data

    def test_app_with_different_configurations(self):
        """Test app with different configuration scenarios."""
        # Minimal configuration
        app1 = TuiApp(namespace="minimal")
        assert app1.namespace == "minimal"
        assert app1.context is None

        # Full configuration
        app2 = TuiApp(
            namespace="full",
            context="custom-context",
            refresh_interval=10,
            deployment_name="custom-deployment",
            socket_path="/custom/socket.sock",
        )
        assert app2.namespace == "full"
        assert app2.context == "custom-context"
        assert app2.refresh_interval == 10
        assert app2.deployment_name == "custom-deployment"
        assert app2.socket_path == "/custom/socket.sock"

    @pytest.mark.asyncio
    async def test_concurrent_update_handling(self, tui_app, mock_dashboard_service):
        """Test handling of concurrent update requests."""
        tui_app._dashboard_service = mock_dashboard_service

        # Simulate slow service call
        async def slow_get_data():
            await asyncio.sleep(0.1)
            return sample_dashboard_data()

        mock_dashboard_service.get_dashboard_data = slow_get_data

        # Start multiple update tasks concurrently
        tasks = [
            asyncio.create_task(tui_app._update_dashboard_data()),
            asyncio.create_task(tui_app._update_dashboard_data()),
            asyncio.create_task(tui_app._update_dashboard_data()),
        ]

        # All should complete successfully
        await asyncio.gather(*tasks)
        assert tui_app.dashboard_data is not None

    def test_app_title_with_different_namespaces(self):
        """Test app title formatting with different namespaces."""
        app1 = TuiApp(namespace="default")
        assert app1.title == "HAProxy Template IC Dashboard - default"

        app2 = TuiApp(namespace="haproxy-system")
        assert app2.title == "HAProxy Template IC Dashboard - haproxy-system"

    @pytest.mark.asyncio
    async def test_update_task_error_recovery(self, tui_app, mock_dashboard_service):
        """Test that update task recovers from errors."""
        tui_app._dashboard_service = mock_dashboard_service

        call_count = 0

        async def failing_then_succeeding():
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                raise Exception("First call fails")
            return sample_dashboard_data()

        mock_dashboard_service.get_dashboard_data.side_effect = failing_then_succeeding

        # First update should fail
        await tui_app._update_dashboard_data()
        assert tui_app.dashboard_data is None

        # Second update should succeed
        await tui_app._update_dashboard_data()
        assert tui_app.dashboard_data is not None
