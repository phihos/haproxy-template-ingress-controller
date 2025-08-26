"""Extended unit tests for debouncer to increase line coverage."""

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from haproxy_template_ic.debouncer import TemplateRenderDebouncer


class TestDebouncerWarnings:
    """Test warning messages for unusual configurations."""

    def test_warning_for_very_long_max_interval(self):
        """Test that a warning is logged for max_interval > 3600."""
        render_func = AsyncMock()
        memo = MagicMock()

        with patch("haproxy_template_ic.debouncer.logger") as mock_logger:
            _ = TemplateRenderDebouncer(
                min_interval=60,
                max_interval=7200,  # 2 hours
                render_func=render_func,
                memo=memo,
            )

            # Check that info was called about long max_interval
            mock_logger.info.assert_any_call(
                "Long max_interval (7200s) - templates may become stale during quiet periods"
            )


class TestDebouncerMetricsImportError:
    """Test debouncer behavior when metrics module is not available."""

    @pytest.mark.asyncio
    async def test_trigger_without_metrics(self):
        """Test trigger method when metrics module import fails."""
        render_func = AsyncMock()
        memo = MagicMock()

        debouncer = TemplateRenderDebouncer(
            min_interval=1, max_interval=5, render_func=render_func, memo=memo
        )

        # Mock the import to fail
        with patch.dict("sys.modules", {"haproxy_template_ic.metrics": None}):
            await debouncer.trigger()

            # Should complete without error
            assert debouncer._change_count == 1
            assert debouncer._last_change_time > 0

    @pytest.mark.asyncio
    async def test_run_metrics_update_import_error(self):
        """Test _run method metrics update when import fails."""
        render_func = AsyncMock()
        memo = MagicMock()

        debouncer = TemplateRenderDebouncer(
            min_interval=0.1, max_interval=0.2, render_func=render_func, memo=memo
        )

        debouncer.start()

        try:
            # Patch the metrics import to fail
            with patch.dict("sys.modules", {"haproxy_template_ic.metrics": None}):
                await debouncer.trigger()
                await asyncio.sleep(0.15)

                # Should have rendered despite import error
                assert render_func.called
        finally:
            await debouncer.stop()

    @pytest.mark.asyncio
    async def test_run_metrics_render_import_error(self):
        """Test _run method metrics recording when import fails."""
        render_func = AsyncMock()
        memo = MagicMock()

        debouncer = TemplateRenderDebouncer(
            min_interval=0.1, max_interval=0.2, render_func=render_func, memo=memo
        )

        debouncer.start()

        try:
            # Let it run for a periodic refresh with no metrics
            with patch.dict("sys.modules", {"haproxy_template_ic.metrics": None}):
                await asyncio.sleep(0.25)  # Wait for max_interval

                # Should have rendered despite import error
                assert render_func.called
        finally:
            await debouncer.stop()


class TestDebouncerEdgeCases:
    """Test debouncer edge cases and error conditions."""

    @pytest.mark.asyncio
    async def test_cancelled_error_during_run(self):
        """Test handling of CancelledError in _run method."""
        render_func = AsyncMock()
        memo = MagicMock()

        debouncer = TemplateRenderDebouncer(
            min_interval=0.1, max_interval=1.0, render_func=render_func, memo=memo
        )

        # Manually set _stop to False to enter the loop
        debouncer._stop = False

        # Create a custom task that we can cancel
        task = asyncio.create_task(debouncer._run())

        # Give it time to start
        await asyncio.sleep(0.05)

        # Cancel the task
        task.cancel()

        # Wait for it to complete - should not raise
        try:
            await task
        except asyncio.CancelledError:
            pass  # Expected

        # The method should have logged the cancellation

    @pytest.mark.asyncio
    async def test_unexpected_error_in_run(self):
        """Test handling of unexpected errors in _run method."""
        render_func = AsyncMock()
        memo = MagicMock()

        debouncer = TemplateRenderDebouncer(
            min_interval=0.1, max_interval=0.5, render_func=render_func, memo=memo
        )

        # Patch asyncio.wait_for to raise an unexpected error once
        call_count = 0
        original_wait_for = asyncio.wait_for

        async def mock_wait_for(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                raise RuntimeError("Unexpected error")
            return await original_wait_for(*args, **kwargs)

        with patch("asyncio.wait_for", mock_wait_for):
            with patch("haproxy_template_ic.debouncer.logger") as mock_logger:
                debouncer.start()

                try:
                    # Give it time to hit the error and recover
                    await asyncio.sleep(1.5)

                    # Should have logged the error
                    error_calls = [
                        call
                        for call in mock_logger.error.call_args_list
                        if "Unexpected error in debouncer task" in str(call)
                    ]
                    assert len(error_calls) > 0

                    # Debouncer should still be running
                    stats = debouncer.get_stats()
                    assert stats["is_running"] is True
                finally:
                    await debouncer.stop()

    @pytest.mark.asyncio
    async def test_stop_with_timeout(self):
        """Test stop method when task doesn't stop gracefully."""

        # Create a render function that takes a very long time
        async def slow_render(memo):
            await asyncio.sleep(100)  # Very long render

        memo = MagicMock()

        debouncer = TemplateRenderDebouncer(
            min_interval=0.01,  # Very short so render triggers quickly
            max_interval=10,  # Long max_interval so it won't trigger periodic refresh
            render_func=slow_render,
            memo=memo,
        )

        # Manually override the _run method to ignore stop signals
        async def stubborn_run():
            # This version ignores the stop flag
            while True:
                try:
                    await asyncio.sleep(100)  # Never exits
                except asyncio.CancelledError:
                    # Re-raise to let stop() handle it
                    raise

        debouncer._run = stubborn_run
        debouncer.start()

        # Give it a moment to start
        await asyncio.sleep(0.01)

        # Now try to stop - it should timeout and cancel
        with patch("haproxy_template_ic.debouncer.logger") as mock_logger:
            await debouncer.stop()

            # Should have warned about ungraceful stop
            warning_calls = [
                call
                for call in mock_logger.warning.call_args_list
                if "did not stop gracefully" in str(call)
            ]
            assert len(warning_calls) > 0

    @pytest.mark.asyncio
    async def test_stop_with_cancelled_error_during_await(self):
        """Test stop method handling CancelledError when awaiting task."""
        render_func = AsyncMock()
        memo = MagicMock()

        debouncer = TemplateRenderDebouncer(
            min_interval=0.1, max_interval=1.0, render_func=render_func, memo=memo
        )

        # Start the debouncer normally to have a real task
        debouncer.start()

        # Wait a bit and then cancel the task to simulate a cancelled task
        await asyncio.sleep(0.05)
        debouncer._task.cancel()

        # Stop should handle the CancelledError gracefully
        await debouncer.stop()

        # Task should be done
        assert debouncer._task.done()


class TestDebouncerGetStats:
    """Test get_stats method with various states."""

    def test_get_stats_with_no_last_change_time(self):
        """Test get_stats when no changes have been triggered."""
        render_func = AsyncMock()
        memo = MagicMock()

        debouncer = TemplateRenderDebouncer(
            min_interval=5, max_interval=60, render_func=render_func, memo=memo
        )

        stats = debouncer.get_stats()

        assert stats["time_since_last_change"] is None
        assert stats["last_change_time"] == 0
        assert stats["pending_changes"] == 0
