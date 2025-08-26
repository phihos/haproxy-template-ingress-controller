"""
Template rendering debouncer with guaranteed periodic execution.

This module provides rate-limited template rendering to prevent excessive
re-rendering on rapid Kubernetes resource changes while guaranteeing
templates are refreshed periodically.
"""

import asyncio
import threading
import time
from typing import Any, Callable, Coroutine, Optional

import structlog

logger = structlog.get_logger(__name__)


class TemplateRenderDebouncer:
    """
    Debounces template rendering with guaranteed periodic execution.

    This class implements a debouncing mechanism that:
    - Rate limits template rendering to at most once per min_interval seconds
    - Guarantees template rendering at least once per max_interval seconds
    - Batches multiple resource change events within the debounce window
    """

    def __init__(
        self,
        min_interval: int,
        max_interval: int,
        render_func: Callable[..., Coroutine[Any, Any, None]],
        memo: Any,
    ):
        """
        Initialize the debouncer.

        Args:
            min_interval: Minimum seconds between renders (rate limit)
            max_interval: Maximum seconds without render (guaranteed refresh)
            render_func: Async function to call for rendering
            memo: Operator memo object to pass to render function
        """
        if max_interval < min_interval:
            raise ValueError(
                f"max_interval ({max_interval}) must be >= min_interval ({min_interval})"
            )

        self.min_interval = min_interval
        self.max_interval = max_interval
        self.render_func = render_func
        self.memo = memo

        self._event = asyncio.Event()
        self._task: Optional[asyncio.Task] = None
        self._last_render_time: float = 0
        self._stop: bool = False
        self._change_count = 0
        self._last_change_time: float = 0
        self._start_lock = threading.Lock()

        # Log warnings for unusual configurations
        if min_interval < 3:
            logger.warning(
                f"Very short min_interval ({min_interval}s) may cause high CPU usage during rapid changes"
            )
        if max_interval > 3600:
            logger.info(
                f"Long max_interval ({max_interval}s) - templates may become stale during quiet periods"
            )

        logger.info(
            "Template debouncer initialized",
            min_interval=min_interval,
            max_interval=max_interval,
        )

    async def trigger(self) -> None:
        """
        Signal that a resource changed and template rendering may be needed.

        This method is called by kopf event handlers when resources change.
        It doesn't immediately trigger rendering but signals the debouncer.
        """
        self._change_count += 1
        self._last_change_time = time.time()
        self._event.set()

        # Record metric
        try:
            from haproxy_template_ic.metrics import get_metrics_collector

            metrics = get_metrics_collector()
            metrics.record_debouncer_trigger()
        except ImportError:
            pass  # Metrics not available

    async def _run(self) -> None:
        """
        Background task that handles debounced template rendering.

        This task runs continuously, waiting for change events or timeout,
        and triggers template rendering according to the configured intervals.
        """
        logger.info("Template debouncer background task started")

        while not self._stop:
            try:
                # Single time calculation per loop iteration for consistency
                current_time = time.time()
                time_since_last_render = current_time - self._last_render_time
                time_until_max = max(0, self.max_interval - time_since_last_render)

                # Update metrics for time since last render
                try:
                    from haproxy_template_ic.metrics import get_metrics_collector

                    metrics = get_metrics_collector()
                    metrics.update_debouncer_last_render_time(time_since_last_render)
                except ImportError:
                    pass  # Metrics not available

                # Wait for event or timeout (guaranteed execution)
                try:
                    await asyncio.wait_for(self._event.wait(), timeout=time_until_max)
                    triggered_by = "resource_changes"
                except asyncio.TimeoutError:
                    # Max interval reached - force render
                    triggered_by = "periodic_refresh"

                # Check if we should stop
                if self._stop:
                    break  # type: ignore[unreachable]

                # Enforce minimum interval (reuse current_time for consistency)
                current_time = time.time()
                time_since_last_render = current_time - self._last_render_time
                if time_since_last_render < self.min_interval:
                    sleep_time = self.min_interval - time_since_last_render
                    logger.debug(
                        f"Rate limiting: waiting {sleep_time:.1f}s before rendering"
                    )
                    await asyncio.sleep(sleep_time)

                # Clear event and count changes
                self._event.clear()
                changes_batched = self._change_count
                self._change_count = 0

                # Log rendering trigger
                if triggered_by == "resource_changes":
                    logger.info(
                        f"🔄 Rendering templates: {changes_batched} changes batched",
                        changes_batched=changes_batched,
                        trigger=triggered_by,
                    )
                else:
                    logger.info(
                        f"⏰ Rendering templates: periodic refresh after {self.max_interval}s",
                        interval=self.max_interval,
                        trigger=triggered_by,
                    )

                # Record metrics
                try:
                    from haproxy_template_ic.metrics import get_metrics_collector

                    metrics = get_metrics_collector()
                    metrics.record_debouncer_render(triggered_by, changes_batched)
                except ImportError:
                    pass  # Metrics not available

                # Render templates
                self._last_render_time = time.time()
                try:
                    await self.render_func(self.memo)
                except Exception as e:
                    logger.error(
                        f"Error during template rendering: {e}",
                        error=str(e),
                        trigger=triggered_by,
                    )
                    # Continue running even if rendering fails

            except asyncio.CancelledError:
                logger.info("Template debouncer task cancelled")
                break
            except Exception as e:
                logger.error(f"Unexpected error in debouncer task: {e}", error=str(e))
                # Continue running to maintain service availability
                await asyncio.sleep(1)  # Brief pause before retry

        logger.info("Template debouncer background task stopped")

    def start(self) -> None:
        """
        Start the debouncer background task (thread-safe).

        This should be called during operator startup.
        """
        with self._start_lock:
            if self._task and not self._task.done():
                logger.warning("Debouncer already running")
                return

            self._stop = False
            self._task = asyncio.create_task(self._run())
            logger.info("Template debouncer started")

    async def stop(self) -> None:
        """
        Stop the debouncer gracefully.

        This should be called during operator shutdown or reload.
        """
        logger.info("Stopping template debouncer...")

        self._stop = True
        self._event.set()  # Wake up the background task

        if self._task:
            try:
                await asyncio.wait_for(self._task, timeout=5)
            except asyncio.TimeoutError:
                logger.warning("Debouncer task did not stop gracefully, cancelling")
                self._task.cancel()
                try:
                    await self._task
                except asyncio.CancelledError:
                    pass

        logger.info("Template debouncer stopped")

    def get_stats(self) -> dict:
        """
        Get current debouncer statistics.

        Returns:
            Dictionary with debouncer stats for monitoring/debugging
        """
        current_time = time.time()
        return {
            "min_interval": self.min_interval,
            "max_interval": self.max_interval,
            "last_render_time": self._last_render_time,
            "time_since_last_render": current_time - self._last_render_time,
            "pending_changes": self._change_count,
            "last_change_time": self._last_change_time,
            "time_since_last_change": current_time - self._last_change_time
            if self._last_change_time
            else None,
            "is_running": self._task and not self._task.done() if self._task else False,
        }
