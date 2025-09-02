"""Test dashboard launcher functionality."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from haproxy_template_ic.dashboard.launcher import DashboardLauncher
from haproxy_template_ic.dashboard.compatibility import CompatibilityLevel


class TestDashboardLauncher:
    """Test DashboardLauncher functionality."""

    @pytest.fixture
    def launcher(self):
        """Create DashboardLauncher instance."""
        return DashboardLauncher(
            namespace="test-namespace",
            context="test-context",
            refresh_interval=5,
            deployment_name="test-deployment",
        )

    def test_initialization(self, launcher):
        """Test launcher initialization."""
        assert launcher.namespace == "test-namespace"
        assert launcher.context == "test-context"
        assert launcher.refresh_interval == 5
        assert launcher.deployment_name == "test-deployment"
        assert launcher.compatibility_level == CompatibilityLevel.BASIC
        assert not launcher.running
        assert launcher.last_update is None

    @pytest.mark.asyncio
    async def test_verify_prerequisites_success(self, launcher):
        """Test successful prerequisite verification."""
        with patch(
            "kr8s.objects.Deployment.get", new_callable=AsyncMock
        ) as mock_deployment_get:
            # Mock successful deployment retrieval
            mock_deployment = MagicMock()
            mock_deployment_get.return_value = mock_deployment

            result = await launcher._verify_prerequisites()

            assert result is True
            mock_deployment_get.assert_called_once_with(
                launcher.deployment_name, namespace=launcher.namespace
            )

    @pytest.mark.asyncio
    async def test_verify_prerequisites_no_kubectl(self, launcher):
        """Test prerequisite verification when kubectl is not available."""
        with patch("asyncio.create_subprocess_exec") as mock_subprocess:
            mock_subprocess.side_effect = FileNotFoundError("kubectl not found")

            result = await launcher._verify_prerequisites()

            assert result is False

    @pytest.mark.asyncio
    async def test_verify_prerequisites_kubectl_fails(self, launcher):
        """Test prerequisite verification when kubectl commands fail."""
        with patch("asyncio.create_subprocess_exec") as mock_subprocess:
            mock_proc = AsyncMock()
            mock_proc.wait.return_value = None
            mock_proc.returncode = 1  # Command failed
            mock_subprocess.return_value = mock_proc

            result = await launcher._verify_prerequisites()

            assert result is False

    @pytest.mark.asyncio
    async def test_verify_prerequisites_cluster_unreachable(self, launcher):
        """Test prerequisite verification when cluster is unreachable."""
        with patch("asyncio.create_subprocess_exec") as mock_subprocess:

            def mock_exec(*args, **kwargs):
                mock_proc = AsyncMock()
                mock_proc.wait.return_value = None
                # First call (kubectl version) succeeds, second fails
                if "version" in args[0]:
                    mock_proc.returncode = 0
                else:
                    mock_proc.returncode = 1
                return mock_proc

            mock_subprocess.side_effect = mock_exec

            result = await launcher._verify_prerequisites()

            assert result is False

    @pytest.mark.asyncio
    async def test_verify_prerequisites_deployment_not_found(self, launcher):
        """Test prerequisite verification when deployment is not found."""
        with patch("asyncio.create_subprocess_exec") as mock_subprocess:

            def mock_exec(*args, **kwargs):
                mock_proc = AsyncMock()
                mock_proc.wait.return_value = None
                # kubectl version and cluster-info succeed, get deployment fails
                if "get" in args[0] and "deployment" in args[0]:
                    mock_proc.returncode = 1
                else:
                    mock_proc.returncode = 0
                return mock_proc

            mock_subprocess.side_effect = mock_exec

            result = await launcher._verify_prerequisites()

            assert result is False

    def test_show_compatibility_info(self, launcher):
        """Test compatibility information display."""
        # Test different compatibility levels
        launcher.compatibility_level = CompatibilityLevel.FULL
        launcher._show_compatibility_info()  # Should not raise exception

        launcher.compatibility_level = CompatibilityLevel.ENHANCED
        launcher._show_compatibility_info()  # Should not raise exception

        launcher.compatibility_level = CompatibilityLevel.BASIC
        launcher._show_compatibility_info()  # Should not raise exception

        launcher.compatibility_level = CompatibilityLevel.LEGACY
        launcher._show_compatibility_info()  # Should not raise exception

    @pytest.mark.asyncio
    async def test_update_layout_success(self, launcher):
        """Test successful layout update."""
        layout = launcher._create_layout()

        sample_data = {
            "config": {"operator_version": "1.0.0", "namespace": "test"},
            "pods": {"discovered": []},
            "indices": {"resources": {}},
            "stats": {},
            "activity": {"recent_events": []},
        }

        # Should not raise exception
        launcher._update_layout(layout, sample_data)

    @pytest.mark.asyncio
    async def test_update_layout_error_handling(self, launcher):
        """Test layout update error handling."""
        layout = launcher._create_layout()

        # Simulate error in panel rendering
        with patch.object(launcher.header_panel, "render") as mock_render:
            mock_render.side_effect = Exception("Panel error")

            # Should handle error gracefully
            launcher._update_layout(layout, {})

    def test_create_footer_text(self, launcher):
        """Test footer text creation."""
        # Test without last update
        footer = launcher._create_footer_text()
        assert "Ctrl+C to exit" in footer
        assert "Initializing" in footer

        # Test with last update
        from datetime import datetime

        launcher.last_update = datetime.now()
        footer = launcher._create_footer_text()
        assert "Ctrl+C to exit" in footer
        assert "Last update:" in footer
        assert f"Refresh: {launcher.refresh_interval}s" in footer

    def test_debug_navigation_methods(self, launcher):
        """Test debug navigation methods work correctly."""
        # Setup debug mode
        launcher.show_debug = True
        launcher.debug_scroll_position = 30  # Start at a higher position
        launcher.debug_total_logs = 100
        launcher.debug_logs_per_page = 20

        initial_position = launcher.debug_scroll_position

        # Test UP navigation (should decrease position)
        result = launcher._handle_debug_navigation("UP")
        assert result is True
        assert launcher.debug_scroll_position < initial_position

        # Test DOWN navigation (should increase position)
        up_position = launcher.debug_scroll_position
        result = launcher._handle_debug_navigation("DOWN")
        assert result is True
        assert launcher.debug_scroll_position > up_position

        # Test PAGEUP navigation (should decrease by larger amount)
        current_position = launcher.debug_scroll_position
        result = launcher._handle_debug_navigation("PAGEUP")
        assert result is True
        assert launcher.debug_scroll_position < current_position

        # Test HOME navigation (should go to start) - only returns True if position changes
        launcher.debug_scroll_position = 10  # Ensure we're not already at 0
        result = launcher._handle_debug_navigation("HOME")
        assert result is True
        assert launcher.debug_scroll_position == 0

        # Test HOME when already at 0 (should return False since position doesn't change)
        result = launcher._handle_debug_navigation("HOME")
        assert result is False  # Position didn't change
        assert launcher.debug_scroll_position == 0  # Still at 0

        # Test non-navigation key
        result = launcher._handle_debug_navigation("x")
        assert result is False  # Should not handle non-navigation keys

    @pytest.mark.asyncio
    async def test_launch_prerequisites_fail(self, launcher):
        """Test launch when prerequisites fail."""
        with patch.object(
            launcher, "_verify_prerequisites", new_callable=AsyncMock
        ) as mock_verify:
            mock_verify.return_value = False

            await launcher.launch()

            mock_verify.assert_called_once()
            # Should return early when prerequisites fail
            assert not launcher.running

    @pytest.mark.asyncio
    async def test_launch_keyboard_interrupt(self, launcher):
        """Test launch handling keyboard interrupt."""
        with (
            patch.object(
                launcher, "_verify_prerequisites", new_callable=AsyncMock
            ) as mock_verify,
            patch.object(
                launcher.data_fetcher, "initialize", new_callable=AsyncMock
            ) as mock_init,
            patch.object(
                launcher, "_run_dashboard", new_callable=AsyncMock
            ) as mock_run,
        ):
            mock_verify.return_value = True
            mock_init.return_value = CompatibilityLevel.BASIC
            mock_run.side_effect = KeyboardInterrupt()

            # Should handle KeyboardInterrupt gracefully
            await launcher.launch()

            assert not launcher.running

    @pytest.mark.asyncio
    async def test_launch_exception_handling(self, launcher):
        """Test launch exception handling."""
        with patch.object(
            launcher, "_verify_prerequisites", new_callable=AsyncMock
        ) as mock_verify:
            mock_verify.side_effect = Exception("Unexpected error")

            # Should handle exception gracefully
            await launcher.launch()

            assert not launcher.running

    @pytest.mark.asyncio
    async def test_run_dashboard_loop(self, launcher):
        """Test dashboard main loop."""
        # Mock data fetcher and stop after first iteration
        sample_data = {"config": {}, "pods": {}}

        with (
            patch.object(
                launcher.data_fetcher, "fetch_all_data", new_callable=AsyncMock
            ) as mock_fetch,
            patch("rich.live.Live") as mock_live,
            patch("asyncio.sleep", new_callable=AsyncMock) as mock_sleep,
        ):
            mock_fetch.return_value = sample_data
            mock_live.return_value.__enter__.return_value = MagicMock()

            # Stop after first iteration
            async def stop_after_first(*args):
                launcher.running = False

            mock_sleep.side_effect = stop_after_first
            launcher.running = True

            await launcher._run_dashboard()

            mock_fetch.assert_called_once()
            mock_sleep.assert_called()  # Changed sleep behavior - just verify it was called

    @pytest.mark.asyncio
    async def test_run_dashboard_fetch_error(self, launcher):
        """Test dashboard handling of data fetch errors."""
        with (
            patch.object(
                launcher.data_fetcher, "fetch_all_data", new_callable=AsyncMock
            ) as mock_fetch,
            patch("rich.live.Live") as mock_live,
            patch("asyncio.sleep", new_callable=AsyncMock) as mock_sleep,
        ):
            mock_fetch.side_effect = Exception("Fetch error")
            mock_live.return_value.__enter__.return_value = MagicMock()

            # Stop after first iteration
            async def stop_after_first(*args):
                launcher.running = False

            mock_sleep.side_effect = stop_after_first
            launcher.running = True

            # Should handle fetch error gracefully and continue
            await launcher._run_dashboard()

            mock_fetch.assert_called_once()
            mock_sleep.assert_called_once()

    @pytest.mark.asyncio
    async def test_stop(self, launcher):
        """Test stopping the dashboard."""
        launcher.running = True

        await launcher.stop()

        assert not launcher.running
