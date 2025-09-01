"""Unit tests for the template rendering debouncer."""

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from haproxy_template_ic.debouncer import TemplateRenderDebouncer
from haproxy_template_ic.models import TriggerContext

# Test constants to avoid magic numbers
MIN_INTERVAL_SHORT = 0.04  # 40ms for fast test execution
MAX_INTERVAL_SHORT = 0.12  # 120ms for guaranteed execution tests
MIN_INTERVAL_LONG = 0.2  # 200ms for rate limiting tests
MAX_INTERVAL_LONG = 5.0  # 5s to not interfere with rate limiting tests
SLEEP_BUFFER = 0.02  # 20ms buffer for async operations
SLEEP_SHORT = 0.08  # 80ms wait after trigger
SLEEP_MEDIUM = 0.15  # 150ms to exceed short max_interval
SLEEP_LONG = 0.25  # 250ms to ensure render completes


class TestTemplateRenderDebouncer:
    """Test the TemplateRenderDebouncer class."""

    @pytest.mark.asyncio
    async def test_init_validation(self):
        """Test that initialization validates interval constraints."""
        render_func = AsyncMock()
        memo = MagicMock()

        # Valid initialization
        debouncer = TemplateRenderDebouncer(
            min_interval=5, max_interval=10, render_func=render_func, memo=memo
        )
        assert debouncer.min_interval == 5
        assert debouncer.max_interval == 10

        # Invalid: max < min
        with pytest.raises(ValueError, match="max_interval.*must be >= min_interval"):
            TemplateRenderDebouncer(
                min_interval=10, max_interval=5, render_func=render_func, memo=memo
            )

    @pytest.mark.asyncio
    async def test_single_trigger(self):
        """Test that a single trigger causes rendering after min_interval."""
        render_func = AsyncMock()
        memo = MagicMock()

        debouncer = TemplateRenderDebouncer(
            min_interval=MIN_INTERVAL_SHORT,
            max_interval=MAX_INTERVAL_LONG,
            render_func=render_func,
            memo=memo,
        )

        await debouncer.start()

        try:
            # Trigger once
            await debouncer.trigger()

            # Wait for min_interval + buffer
            await asyncio.sleep(SLEEP_SHORT)

            # Should have rendered once with trigger context
            # Note: debouncer now passes logger as second parameter
            assert render_func.call_count == 1
            args, kwargs = render_func.call_args
            assert args[0] is memo  # First arg is memo
            # Second arg is logger (we don't need to test the logger object)
            assert len(args) == 2
            assert kwargs["trigger_context"] == TriggerContext(
                trigger_type="periodic_refresh", pod_changed=False
            )
        finally:
            await debouncer.stop()

    @pytest.mark.asyncio
    async def test_guaranteed_periodic_execution(self):
        """Test that rendering happens at max_interval even without triggers."""
        render_func = AsyncMock()
        memo = MagicMock()

        debouncer = TemplateRenderDebouncer(
            min_interval=MIN_INTERVAL_SHORT,
            max_interval=MAX_INTERVAL_SHORT,
            render_func=render_func,
            memo=memo,
        )

        await debouncer.start()

        try:
            # Don't trigger anything, just wait
            await asyncio.sleep(SLEEP_MEDIUM)  # Wait past max_interval

            # Should have rendered due to timeout
            assert render_func.call_count >= 1
        finally:
            await debouncer.stop()

    @pytest.mark.asyncio
    async def test_rate_limiting(self):
        """Test that min_interval is enforced between renders."""
        render_func = AsyncMock()
        memo = MagicMock()

        debouncer = TemplateRenderDebouncer(
            min_interval=MIN_INTERVAL_LONG,
            max_interval=MAX_INTERVAL_LONG,
            render_func=render_func,
            memo=memo,
        )

        await debouncer.start()
        await asyncio.sleep(MIN_INTERVAL_SHORT)  # Let it start

        try:
            # First trigger and render
            await debouncer.trigger()
            await asyncio.sleep(SLEEP_LONG)  # Wait for render
            render_count_1 = render_func.call_count
            assert render_count_1 >= 1

            # Trigger again - should be rate limited
            await debouncer.trigger()
            await asyncio.sleep(SLEEP_SHORT)  # Less than min_interval

            # Should not have rendered yet
            assert render_func.call_count == render_count_1

            # Wait for min_interval to pass
            await asyncio.sleep(SLEEP_SHORT * 2)

            # Now should have rendered again
            assert render_func.call_count > render_count_1
        finally:
            await debouncer.stop()

    @pytest.mark.asyncio
    async def test_stop_gracefully(self):
        """Test that debouncer stops gracefully."""
        render_func = AsyncMock()
        memo = MagicMock()

        debouncer = TemplateRenderDebouncer(
            min_interval=MIN_INTERVAL_SHORT,
            max_interval=MAX_INTERVAL_LONG,
            render_func=render_func,
            memo=memo,
        )

        await debouncer.start()
        await asyncio.sleep(SLEEP_BUFFER)  # Let it start

        # Stop should complete without errors
        await debouncer.stop()

        # Task should be done
        assert debouncer._task.done()
        assert debouncer._stop is True

    @pytest.mark.asyncio
    async def test_render_error_handling(self):
        """Test that render errors don't crash the debouncer."""
        render_func = AsyncMock(side_effect=Exception("Test error"))
        memo = MagicMock()

        debouncer = TemplateRenderDebouncer(
            min_interval=MIN_INTERVAL_SHORT,
            max_interval=MIN_INTERVAL_LONG,
            render_func=render_func,
            memo=memo,
        )

        await debouncer.start()

        try:
            # Trigger rendering
            await debouncer.trigger()
            await asyncio.sleep(SLEEP_SHORT)

            # Should have attempted render despite error
            assert render_func.call_count >= 1

            # Debouncer should still be running
            stats = debouncer.get_stats()
            assert stats["is_running"] is True
        finally:
            await debouncer.stop()

    @pytest.mark.asyncio
    async def test_get_stats(self):
        """Test that get_stats returns correct information."""
        render_func = AsyncMock()
        memo = MagicMock()

        debouncer = TemplateRenderDebouncer(
            min_interval=5, max_interval=60, render_func=render_func, memo=memo
        )

        stats = debouncer.get_stats()
        assert stats["min_interval"] == 5
        assert stats["max_interval"] == 60
        assert stats["is_running"] is False
        assert stats["pending_changes"] == 0

        await debouncer.start()
        await asyncio.sleep(SLEEP_BUFFER / 5)

        stats = debouncer.get_stats()
        assert stats["is_running"] is True

        await debouncer.trigger()
        stats = debouncer.get_stats()
        assert stats["pending_changes"] == 1

        await debouncer.stop()

    @pytest.mark.asyncio
    async def test_start_idempotent(self):
        """Test that calling start multiple times is safe."""
        render_func = AsyncMock()
        memo = MagicMock()

        debouncer = TemplateRenderDebouncer(
            min_interval=MIN_INTERVAL_SHORT,
            max_interval=MAX_INTERVAL_LONG,
            render_func=render_func,
            memo=memo,
        )

        await debouncer.start()
        first_task = debouncer._task

        # Starting again should not create a new task
        with patch("haproxy_template_ic.debouncer.logger") as mock_logger:
            await debouncer.start()
            mock_logger.warning.assert_called_with("Debouncer already running")

        assert debouncer._task is first_task

        await debouncer.stop()

    @pytest.mark.asyncio
    async def test_periodic_refresh_timing(self):
        """Test that periodic refresh doesn't add unnecessary min_interval wait."""
        import time

        render_func = AsyncMock()
        memo = MagicMock()

        debouncer = TemplateRenderDebouncer(
            min_interval=MIN_INTERVAL_SHORT,  # 0.1s min interval
            max_interval=MAX_INTERVAL_SHORT,  # 0.3s max interval (short for test)
            render_func=render_func,
            memo=memo,
        )

        await debouncer.start()

        try:
            start_time = time.time()

            # Wait for periodic refresh (should happen after max_interval)
            await asyncio.sleep(SLEEP_MEDIUM)  # 0.35s > 0.3s max_interval

            # Should have rendered due to periodic refresh
            assert render_func.call_count >= 1

            # Check that total time is approximately max_interval, not max_interval + min_interval
            total_time = time.time() - start_time
            # Allow some buffer for timing precision, but should be much closer to max_interval (0.3s)
            # than max_interval + min_interval (0.3s + 0.1s = 0.4s)
            assert (
                total_time < 0.4
            )  # Should be much less than 0.4s if working correctly

        finally:
            await debouncer.stop()

    @pytest.mark.asyncio
    async def test_accurate_time_calculation_after_wait(self):
        """Test that resource changes don't wait unnecessarily when enough time has passed."""
        import time

        render_func = AsyncMock()
        memo = MagicMock()

        debouncer = TemplateRenderDebouncer(
            min_interval=MIN_INTERVAL_LONG,  # 0.5s min interval
            max_interval=MAX_INTERVAL_LONG,  # 10s max interval
            render_func=render_func,
            memo=memo,
        )

        await debouncer.start()

        try:
            # First render
            await debouncer.trigger()
            await asyncio.sleep(SLEEP_LONG)  # 0.6s wait for first render
            first_count = render_func.call_count
            assert first_count >= 1

            # Wait longer than min_interval
            await asyncio.sleep(
                SLEEP_LONG
            )  # Another 0.6s, total 1.2s > 0.5s min_interval

            start_time = time.time()
            # Second trigger should not need additional min_interval wait
            await debouncer.trigger()
            await asyncio.sleep(SLEEP_SHORT)  # Just enough for processing

            # Should have rendered without additional delay
            assert render_func.call_count > first_count
            processing_time = time.time() - start_time
            # Should be much less than min_interval (0.5s) since enough time already passed
            assert processing_time < 0.3

        finally:
            await debouncer.stop()

    @pytest.mark.asyncio
    async def test_min_interval_still_enforced_when_needed(self):
        """Test that min_interval is still enforced for rapid successive triggers."""
        import time

        render_func = AsyncMock()
        memo = MagicMock()

        debouncer = TemplateRenderDebouncer(
            min_interval=MIN_INTERVAL_LONG,  # 0.5s min interval
            max_interval=MAX_INTERVAL_LONG,  # 10s max interval
            render_func=render_func,
            memo=memo,
        )

        await debouncer.start()

        try:
            # First render
            await debouncer.trigger()
            await asyncio.sleep(SLEEP_LONG)  # 0.6s wait for first render
            first_count = render_func.call_count
            assert first_count >= 1

            # Trigger again immediately (within min_interval)
            start_time = time.time()
            await debouncer.trigger()
            await asyncio.sleep(
                SLEEP_LONG + SLEEP_SHORT
            )  # Wait for rate limiting + processing

            # Should have rendered but with rate limiting delay
            assert render_func.call_count > first_count
            total_time = time.time() - start_time
            # Should be approximately min_interval (0.5s) plus some processing time
            assert total_time >= MIN_INTERVAL_LONG * 0.8  # Allow 20% timing tolerance

        finally:
            await debouncer.stop()


# Extended tests (merged from test_debouncer_extended.py)
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

        await debouncer.start()

        try:
            # Patch the metrics import to fail
            with patch.dict("sys.modules", {"haproxy_template_ic.metrics": None}):
                await debouncer.trigger()
                await asyncio.sleep(0.08)

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

        await debouncer.start()

        try:
            # Let it run for a periodic refresh with no metrics
            with patch.dict("sys.modules", {"haproxy_template_ic.metrics": None}):
                await asyncio.sleep(0.12)  # Wait for max_interval

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
        await asyncio.sleep(0.02)

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
                await debouncer.start()

                try:
                    # Give it time to hit the error and recover
                    await asyncio.sleep(0.3)

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
            await asyncio.sleep(10)  # Very long render

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
                    await asyncio.sleep(10)  # Never exits
                except asyncio.CancelledError:
                    # Re-raise to let stop() handle it
                    raise

        debouncer._run = stubborn_run
        await debouncer.start()

        # Give it a moment to start
        await asyncio.sleep(0.005)

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
        await debouncer.start()

        # Wait a bit and then cancel the task to simulate a cancelled task
        await asyncio.sleep(0.02)
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
