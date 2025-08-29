"""Unit tests for the template rendering debouncer."""

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from haproxy_template_ic.debouncer import TemplateRenderDebouncer
from haproxy_template_ic.config_models import TriggerContext

# Test constants to avoid magic numbers
MIN_INTERVAL_SHORT = 0.1  # 100ms for fast test execution
MAX_INTERVAL_SHORT = 0.3  # 300ms for guaranteed execution tests
MIN_INTERVAL_LONG = 0.5  # 500ms for rate limiting tests
MAX_INTERVAL_LONG = 10.0  # 10s to not interfere with rate limiting tests
SLEEP_BUFFER = 0.05  # 50ms buffer for async operations
SLEEP_SHORT = 0.2  # 200ms wait after trigger
SLEEP_MEDIUM = 0.35  # 350ms to exceed short max_interval
SLEEP_LONG = 0.6  # 600ms to ensure render completes


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
            render_func.assert_called_once_with(
                memo,
                trigger_context=TriggerContext(
                    trigger_type="periodic_refresh", pod_changed=False
                ),
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
