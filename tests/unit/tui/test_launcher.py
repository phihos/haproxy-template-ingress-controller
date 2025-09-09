"""
Unit tests for the TUI Launcher.

Tests launcher initialization, async application launch,
error handling, and synchronous wrapper methods.
"""

import asyncio
import pytest
from unittest.mock import AsyncMock, patch

from haproxy_template_ic.tui.launcher import TuiLauncher


class TestTuiLauncher:
    """Test the TuiLauncher class."""

    @pytest.fixture
    def launcher_params(self):
        """Default launcher parameters."""
        return {
            "namespace": "test-namespace",
            "context": "test-context",
            "refresh_interval": 10,
            "deployment_name": "test-deployment",
            "socket_path": "/tmp/test.sock",
        }

    @pytest.fixture
    def tui_launcher(self, launcher_params):
        """Create a TuiLauncher instance."""
        return TuiLauncher(**launcher_params)

    def test_launcher_initialization(self, launcher_params):
        """Test TuiLauncher initialization with all parameters."""
        launcher = TuiLauncher(**launcher_params)

        assert launcher.namespace == "test-namespace"
        assert launcher.context == "test-context"
        assert launcher.refresh_interval == 10
        assert launcher.deployment_name == "test-deployment"
        assert launcher.socket_path == "/tmp/test.sock"

    def test_launcher_initialization_minimal(self):
        """Test TuiLauncher initialization with minimal parameters."""
        launcher = TuiLauncher(namespace="minimal")

        assert launcher.namespace == "minimal"
        assert launcher.context is None
        assert launcher.refresh_interval == 5  # default
        assert launcher.deployment_name == "haproxy-template-ic"  # default
        assert launcher.socket_path is None

    def test_launcher_initialization_partial(self):
        """Test TuiLauncher initialization with partial parameters."""
        launcher = TuiLauncher(
            namespace="partial", refresh_interval=15, socket_path="/custom/path.sock"
        )

        assert launcher.namespace == "partial"
        assert launcher.context is None  # default
        assert launcher.refresh_interval == 15
        assert launcher.deployment_name == "haproxy-template-ic"  # default
        assert launcher.socket_path == "/custom/path.sock"

    @pytest.mark.asyncio
    @patch("haproxy_template_ic.tui.launcher.TuiApp")
    async def test_launch_success(self, mock_app_class, tui_launcher):
        """Test successful async launch of TUI app."""
        # Mock the TuiApp instance and its run_async method
        mock_app = AsyncMock()
        mock_app_class.return_value = mock_app

        with patch("haproxy_template_ic.tui.launcher.logger") as mock_logger:
            await tui_launcher.launch()

            # Verify app was created with correct parameters
            mock_app_class.assert_called_once_with(
                namespace="test-namespace",
                context="test-context",
                refresh_interval=10,
                deployment_name="test-deployment",
                socket_path="/tmp/test.sock",
            )

            # Verify app was launched
            mock_app.run_async.assert_called_once()

            # Verify start message was logged
            mock_logger.info.assert_called_with(
                "Starting TUI dashboard for namespace 'test-namespace'"
            )

    @pytest.mark.asyncio
    @patch("haproxy_template_ic.tui.launcher.TuiApp")
    async def test_launch_keyboard_interrupt(self, mock_app_class, tui_launcher):
        """Test launch handling of KeyboardInterrupt."""
        # Mock the TuiApp to raise KeyboardInterrupt
        mock_app = AsyncMock()
        mock_app.run_async.side_effect = KeyboardInterrupt()
        mock_app_class.return_value = mock_app

        with patch("haproxy_template_ic.tui.launcher.logger") as mock_logger:
            await tui_launcher.launch()

            # Verify keyboard interrupt was logged
            mock_logger.info.assert_called_with("TUI dashboard stopped by user")

    @pytest.mark.asyncio
    @patch("haproxy_template_ic.tui.launcher.TuiApp")
    async def test_launch_general_exception(self, mock_app_class, tui_launcher):
        """Test launch handling of general exceptions."""
        # Mock the TuiApp to raise a general exception
        mock_app = AsyncMock()
        test_error = RuntimeError("Test error")
        mock_app.run_async.side_effect = test_error
        mock_app_class.return_value = mock_app

        with patch("haproxy_template_ic.tui.launcher.logger") as mock_logger:
            with pytest.raises(RuntimeError, match="Test error"):
                await tui_launcher.launch()

            # Verify error was logged
            mock_logger.error.assert_called_with(
                "TUI dashboard error: Test error", exc_info=True
            )

    @pytest.mark.asyncio
    @patch("haproxy_template_ic.tui.launcher.TuiApp")
    async def test_launch_app_creation_failure(self, mock_app_class, tui_launcher):
        """Test launch handling when app creation fails."""
        # Mock TuiApp constructor to raise exception
        mock_app_class.side_effect = ValueError("App creation failed")

        with patch("haproxy_template_ic.tui.launcher.logger") as mock_logger:
            with pytest.raises(ValueError, match="App creation failed"):
                await tui_launcher.launch()

            # Verify error was logged
            mock_logger.error.assert_called_with(
                "TUI dashboard error: App creation failed", exc_info=True
            )

    @patch("haproxy_template_ic.tui.launcher.asyncio.run")
    def test_run_success(self, mock_asyncio_run, tui_launcher):
        """Test synchronous run method success."""
        # Mock asyncio.run to succeed
        mock_asyncio_run.return_value = None

        tui_launcher.run()

        # Verify asyncio.run was called with launch coroutine
        mock_asyncio_run.assert_called_once()

        # Get the coroutine that was passed to asyncio.run
        call_args = mock_asyncio_run.call_args[0]
        assert len(call_args) == 1
        # The argument should be a coroutine (we can't easily test the exact content)

    @patch("haproxy_template_ic.tui.launcher.asyncio.run")
    def test_run_keyboard_interrupt(self, mock_asyncio_run, tui_launcher):
        """Test synchronous run method handling KeyboardInterrupt."""
        # Mock asyncio.run to raise KeyboardInterrupt
        mock_asyncio_run.side_effect = KeyboardInterrupt()

        with patch("haproxy_template_ic.tui.launcher.logger") as mock_logger:
            tui_launcher.run()

            # Verify keyboard interrupt was logged
            mock_logger.info.assert_called_with("TUI dashboard stopped by user")

    @patch("haproxy_template_ic.tui.launcher.asyncio.run")
    def test_run_general_exception(self, mock_asyncio_run, tui_launcher):
        """Test synchronous run method handling general exceptions."""
        # Mock asyncio.run to raise a general exception
        test_error = RuntimeError("Test runtime error")
        mock_asyncio_run.side_effect = test_error

        with patch("haproxy_template_ic.tui.launcher.logger") as mock_logger:
            with pytest.raises(RuntimeError, match="Test runtime error"):
                tui_launcher.run()

            # Verify error was logged
            mock_logger.error.assert_called_with(
                "TUI dashboard error: Test runtime error", exc_info=True
            )

    @pytest.mark.asyncio
    @patch("haproxy_template_ic.tui.launcher.TuiApp")
    async def test_launch_with_different_parameters(self, mock_app_class):
        """Test launch with different parameter combinations."""
        # Test with minimal parameters
        launcher1 = TuiLauncher(namespace="minimal")
        mock_app1 = AsyncMock()
        mock_app_class.return_value = mock_app1

        await launcher1.launch()

        mock_app_class.assert_called_with(
            namespace="minimal",
            context=None,
            refresh_interval=5,
            deployment_name="haproxy-template-ic",
            socket_path=None,
        )

        # Test with all parameters
        launcher2 = TuiLauncher(
            namespace="full",
            context="custom-context",
            refresh_interval=30,
            deployment_name="custom-deployment",
            socket_path="/custom/socket.sock",
        )
        mock_app2 = AsyncMock()
        mock_app_class.return_value = mock_app2

        await launcher2.launch()

        mock_app_class.assert_called_with(
            namespace="full",
            context="custom-context",
            refresh_interval=30,
            deployment_name="custom-deployment",
            socket_path="/custom/socket.sock",
        )

    @pytest.mark.asyncio
    @patch("haproxy_template_ic.tui.launcher.TuiApp")
    async def test_launch_logs_namespace_info(self, mock_app_class, tui_launcher):
        """Test that launch logs the correct namespace information."""
        mock_app = AsyncMock()
        mock_app_class.return_value = mock_app

        with patch("haproxy_template_ic.tui.launcher.logger") as mock_logger:
            await tui_launcher.launch()

            # Verify the specific log message format
            mock_logger.info.assert_called_with(
                "Starting TUI dashboard for namespace 'test-namespace'"
            )

    def test_launcher_parameter_types(self):
        """Test launcher parameter type handling."""
        # Test with different types
        launcher = TuiLauncher(
            namespace="test",
            context="ctx",
            refresh_interval=15,
            deployment_name="deploy",
            socket_path="/path/to/socket",
        )

        assert isinstance(launcher.namespace, str)
        assert isinstance(launcher.context, str)
        assert isinstance(launcher.refresh_interval, int)
        assert isinstance(launcher.deployment_name, str)
        assert isinstance(launcher.socket_path, str)

    def test_launcher_none_parameters(self):
        """Test launcher with None parameters."""
        launcher = TuiLauncher(namespace="test", context=None, socket_path=None)

        assert launcher.namespace == "test"
        assert launcher.context is None
        assert launcher.socket_path is None

    @pytest.mark.asyncio
    async def test_multiple_concurrent_launches(self):
        """Test behavior of multiple concurrent launch calls."""
        launcher = TuiLauncher(namespace="concurrent")

        with patch("haproxy_template_ic.tui.launcher.TuiApp") as mock_app_class:
            # Create different mock apps for each call
            mock_apps = [AsyncMock() for _ in range(3)]
            mock_app_class.side_effect = mock_apps

            # Start multiple launches concurrently
            tasks = [
                asyncio.create_task(launcher.launch()),
                asyncio.create_task(launcher.launch()),
                asyncio.create_task(launcher.launch()),
            ]

            await asyncio.gather(*tasks)

            # Each launch should create its own app instance
            assert mock_app_class.call_count == 3
            for mock_app in mock_apps:
                mock_app.run_async.assert_called_once()

    def test_launcher_string_representation(self, tui_launcher):
        """Test launcher object representation."""
        # Test that the object can be created and basic attributes accessed
        # (This is more for coverage than functional testing)
        assert hasattr(tui_launcher, "namespace")
        assert hasattr(tui_launcher, "context")
        assert hasattr(tui_launcher, "refresh_interval")
        assert hasattr(tui_launcher, "deployment_name")
        assert hasattr(tui_launcher, "socket_path")

    @pytest.mark.asyncio
    @patch("haproxy_template_ic.tui.launcher.TuiApp")
    async def test_launch_app_run_async_call(self, mock_app_class, tui_launcher):
        """Test that launch correctly calls app.run_async()."""
        mock_app = AsyncMock()
        mock_app_class.return_value = mock_app

        await tui_launcher.launch()

        # Verify run_async was called exactly once with no arguments
        mock_app.run_async.assert_called_once_with()

    @patch("asyncio.run")
    def test_run_method_calls_asyncio_run(self, mock_asyncio_run, tui_launcher):
        """Test that run method correctly calls asyncio.run."""
        tui_launcher.run()

        # Verify asyncio.run was called once
        mock_asyncio_run.assert_called_once()

        # Verify the argument is a coroutine
        call_args = mock_asyncio_run.call_args
        assert len(call_args[0]) == 1  # One positional argument

        # The argument should be a coroutine object
        coro = call_args[0][0]
        assert hasattr(coro, "__await__")  # Check if it's awaitable
