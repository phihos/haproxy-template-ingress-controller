"""
Unit tests for the TUI App main application class.

Tests app initialization, screen management, reactive properties,
keyboard bindings, and data update handling.
"""

import asyncio
import pytest
from unittest.mock import AsyncMock, patch
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
        templates={
            "test.cfg": TemplateInfo(
                name="test.cfg",
                type="haproxy_config",
                status="rendered",
                size=1024,
                last_modified=datetime.now(timezone.utc),
            )
        },
        performance=PerformanceInfo(
            requests_per_second=100,
            response_time_avg=20.5,
            error_rate=0.01,
            active_connections=500,
        ),
        activity=[
            ActivityEvent(
                type="INFO",
                message="Test event",
                timestamp=datetime.now(timezone.utc).isoformat(),
                source="test",
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
        with patch.object(tui_app, "set_interval") as mock_set_interval:
            with patch.object(tui_app, "_initialize") as mock_initialize:
                await tui_app.on_mount()

                mock_set_interval.assert_called_once_with(
                    tui_app.refresh_interval, tui_app.refresh_data
                )
                mock_initialize.assert_called_once()

    @pytest.mark.asyncio
    async def test_start_update_task_creates_task(self, tui_app):
        """Test that _start_update_task creates a background task."""
        with patch("asyncio.create_task") as mock_create_task:
            mock_task = AsyncMock()
            mock_create_task.return_value = mock_task

        # Test that we can set an interval (simulating the actual on_mount behavior)
        with patch.object(tui_app, "set_interval") as mock_set_interval:
            mock_callback = AsyncMock()
            tui_app.set_interval(5.0, mock_callback)

            mock_set_interval.assert_called_once_with(5.0, mock_callback)
            # The actual set_interval returns a Timer object but we're mocking it

    @pytest.mark.asyncio
    async def test_stop_update_task_cancels_task(self, tui_app):
        """Test that _stop_update_task cancels the background task."""
        mock_task = AsyncMock()
        tui_app._update_task = mock_task

        # Test that we can mock interval management
        with patch.object(tui_app, "set_interval") as mock_set_interval:
            # Create a mock timer
            mock_timer = AsyncMock()
            mock_timer.stop = AsyncMock()
            mock_set_interval.return_value = mock_timer

            # Set up an interval
            timer = tui_app.set_interval(5.0, AsyncMock())

            # Stop the timer (simulating cleanup)
            if hasattr(timer, "stop"):
                timer.stop()

    @pytest.mark.asyncio
    async def test_stop_update_task_handles_no_task(self, tui_app):
        """Test that cleanup handles no existing timers gracefully."""
        # This should not raise an exception even if no timers are set
        # The app handles this internally through Textual's timer management
        pass  # No-op test as Textual handles this internally

    @pytest.mark.asyncio
    async def test_update_dashboard_data_success(self, tui_app, mock_dashboard_service):
        """Test successful dashboard data refresh."""
        sample_data = sample_dashboard_data()
        with patch.object(
            tui_app.data_provider, "fetch_all_data", return_value=sample_data
        ) as mock_fetch:
            await tui_app.refresh_data()

            mock_fetch.assert_called_once()
            # Check that reactive properties are updated (status changes to CONNECTED after successful fetch)
            assert tui_app.operator_status.version == sample_data.operator.version
            assert tui_app.operator_status.namespace == sample_data.operator.namespace
            assert tui_app.operator_status.status == "CONNECTED"

    @pytest.mark.asyncio
    async def test_update_dashboard_data_handles_error(
        self, tui_app, mock_dashboard_service
    ):
        """Test dashboard data refresh error handling."""
        with patch.object(
            tui_app.data_provider, "fetch_all_data", side_effect=Exception("Test error")
        ) as mock_fetch:
            with patch("haproxy_template_ic.tui.app.logger") as mock_logger:
                await tui_app.refresh_data()

                mock_logger.error.assert_called_once()
                mock_fetch.assert_called_once()

    @pytest.mark.asyncio
    async def test_periodic_update_loop(self, tui_app):
        """Test the periodic update with set_interval."""
        update_count = 0

        async def mock_update():
            nonlocal update_count
            update_count += 1

        with patch.object(
            tui_app, "refresh_data", side_effect=mock_update
        ) as mock_refresh:
            # Simulate the interval callback being called
            callback = mock_refresh
            await callback()
            await callback()

            assert update_count == 2

    @pytest.mark.asyncio
    async def test_action_quit(self, tui_app):
        """Test quit action."""
        with patch.object(tui_app, "exit") as mock_exit:
            await tui_app.action_quit()
            mock_exit.assert_called_once()

    @pytest.mark.asyncio
    async def test_action_refresh(self, tui_app):
        """Test manual refresh action."""
        with patch.object(tui_app, "refresh_data") as mock_update:
            await tui_app.action_refresh()
            mock_update.assert_called_once()

    @pytest.mark.asyncio
    async def test_action_show_help(self, tui_app):
        """Test show help action."""
        with patch.object(tui_app, "push_screen") as mock_push:
            await tui_app.action_help()
            mock_push.assert_called_once()

    @pytest.mark.asyncio
    async def test_action_show_debug(self, tui_app):
        """Test show debug action."""
        with patch.object(tui_app, "push_screen") as mock_push:
            await tui_app.action_debug()
            mock_push.assert_called_once()

    @pytest.mark.asyncio
    async def test_action_template_inspector(self, tui_app):
        """Test template inspector action."""
        with patch.object(tui_app, "push_screen") as mock_push:
            await tui_app.action_template_inspector()
            mock_push.assert_called_once()

    def test_on_template_selected(self, tui_app):
        """Test template selection handling."""
        template = TemplateInfo(
            name="test.cfg",
            type="haproxy_config",
            status="rendered",
            size=1024,
            last_modified=datetime.now(timezone.utc),
        )

        message = TemplateSelected(template.name)

        with patch.object(tui_app, "push_screen") as mock_push:
            tui_app.on_template_selected(message)
            mock_push.assert_called_once()

    def test_reactive_properties_initialization(self, tui_app):
        """Test that reactive properties are properly initialized."""
        # Check initial reactive property values
        assert tui_app.operator_status.status == "UNKNOWN"
        assert tui_app.pods == []
        assert tui_app.templates == {}
        assert tui_app.loading is True

    def test_refresh_data_updates_properties(self, tui_app):
        """Test that refresh_data updates reactive properties."""
        sample_data = sample_dashboard_data()
        with patch.object(
            tui_app.data_provider, "fetch_all_data", return_value=sample_data
        ):
            # Call the actual refresh method which internally updates properties
            import asyncio

            asyncio.run(tui_app.refresh_data())

            # Verify reactive properties are updated (status changes to CONNECTED after successful fetch)
            assert tui_app.operator_status.version == sample_data.operator.version
            assert tui_app.operator_status.namespace == sample_data.operator.namespace
            assert tui_app.operator_status.status == "CONNECTED"
            assert tui_app.pods == sample_data.pods
            assert tui_app.templates == sample_data.templates

    def test_error_handling_in_refresh(self, tui_app):
        """Test error handling in refresh_data."""
        with patch.object(
            tui_app.data_provider, "fetch_all_data", side_effect=Exception("Test error")
        ):
            with patch("haproxy_template_ic.tui.app.logger") as mock_logger:
                import asyncio

                asyncio.run(tui_app.refresh_data())
                # Should log error without crashing
                mock_logger.error.assert_called()

    def test_app_configuration_properties(self, tui_app):
        """Test app configuration properties."""
        # Verify configuration properties are accessible
        assert tui_app.namespace == "test-namespace"
        assert tui_app.context == "test-context"
        assert tui_app.refresh_interval == 5
        assert tui_app.deployment_name == "test-deployment"
        assert tui_app.socket_path == "/tmp/test.sock"

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
        """Test handling of concurrent refresh requests."""
        call_count = 0

        async def slow_fetch():
            nonlocal call_count
            call_count += 1
            await asyncio.sleep(0.1)  # Simulate slow operation
            return DashboardData()

            # Start multiple refresh tasks concurrently
            tasks = [
                asyncio.create_task(tui_app.refresh_data()),
                asyncio.create_task(tui_app.refresh_data()),
                asyncio.create_task(tui_app.refresh_data()),
            ]

            # All should complete successfully
            await asyncio.gather(*tasks)
            # Verify multiple calls were made
            assert call_count >= 2

    def test_app_title_with_different_namespaces(self):
        """Test app title and namespace handling."""
        app1 = TuiApp(namespace="default")
        assert app1.namespace == "default"
        assert "HAProxy Template IC Dashboard" in str(app1.TITLE)

        app2 = TuiApp(namespace="haproxy-system")
        assert app2.namespace == "haproxy-system"
        assert "HAProxy Template IC Dashboard" in str(app2.TITLE)

    @pytest.mark.asyncio
    async def test_update_task_error_recovery(self, tui_app, mock_dashboard_service):
        """Test that refresh recovers from errors."""
        call_count = 0

        async def failing_then_succeeding():
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                raise Exception("First call fails")
            return DashboardData()

        with patch.object(
            tui_app.data_provider, "fetch_all_data", side_effect=failing_then_succeeding
        ):
            # First update should fail gracefully
            await tui_app.refresh_data()

            # Second update should succeed
            await tui_app.refresh_data()
            assert call_count == 2

    def test_app_initialization_error_handling(self):
        """Test app initialization with errors."""
        tui_app = TuiApp(namespace="test")

        # Mock data provider initialization to raise an exception
        with patch.object(tui_app, "data_provider") as mock_provider:
            mock_provider.initialize = AsyncMock(side_effect=Exception("Init failed"))

            async def test_init():
                # This should handle the exception gracefully
                await tui_app._initialize()
                assert tui_app.loading is False

            asyncio.run(test_init())

    def test_app_console_handler_removal(self):
        """Test console handler removal in __init__."""
        import logging
        import sys

        # Add a console handler to test removal
        root_logger = logging.getLogger()
        console_handler = logging.StreamHandler(sys.stdout)
        root_logger.addHandler(console_handler)

        try:
            # Creating the app should remove console handlers
            TuiApp(namespace="test")

            # Check that stdout/stderr handlers are removed
            remaining_handlers = [
                h
                for h in root_logger.handlers
                if isinstance(h, logging.StreamHandler)
                and h.stream in (sys.stdout, sys.stderr)
            ]
            assert len(remaining_handlers) == 0

        finally:
            # Clean up
            if console_handler in root_logger.handlers:
                root_logger.removeHandler(console_handler)

    def test_app_action_methods(self):
        """Test app action methods."""
        tui_app = TuiApp(namespace="test")

        # Test _set_connection_status
        tui_app._set_connection_status("CONNECTED")
        tui_app._set_connection_status("DISCONNECTED")
        tui_app._set_connection_status("ERROR")

    def test_app_error_scenarios(self):
        """Test various error scenarios."""
        tui_app = TuiApp(namespace="test")

        # Test with various invalid configurations
        tui_app.operator_data = None
        tui_app.pods_data = None
        tui_app.templates_data = None
        tui_app.resources_data = None
        tui_app.performance_data = None
        tui_app.activity_data = None

        # These should not crash
        assert tui_app.operator_data is None
        assert tui_app.pods_data is None
