"""
Template rendering debouncer with guaranteed periodic execution.

This module provides rate-limited template rendering to prevent excessive
re-rendering on rapid Kubernetes resource changes while guaranteeing
templates are refreshed periodically.
"""

import asyncio
import time

import structlog
from kopf._core.engines.indexing import OperatorIndices

from haproxy_template_ic.dataplane.synchronizer import ConfigSynchronizer
from haproxy_template_ic.metrics import MetricsCollector
from haproxy_template_ic.models.config import Config
from haproxy_template_ic.models.context import HAProxyConfigContext
from haproxy_template_ic.models.templates import TriggerContext
from haproxy_template_ic.operator.index_sync import IndexSynchronizationTracker
from .template_renderer import render_haproxy_templates
from haproxy_template_ic.templating import TemplateRenderer

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
        config: Config,
        haproxy_config_context: HAProxyConfigContext,
        template_renderer: TemplateRenderer,
        config_synchronizer: ConfigSynchronizer,
        kopf_indices: OperatorIndices,
        metrics: MetricsCollector,
        index_tracker: IndexSynchronizationTracker,
        stop_timeout: float = 5.0,
        error_retry_delay: float = 1.0,
    ):
        """
        Initialize the debouncer.

        Args:
            min_interval: Minimum seconds between renders (rate limit)
            max_interval: Maximum seconds without render (guaranteed refresh)
            config: Configuration object
            haproxy_config_context: HAProxy configuration context
            template_renderer: Template renderer instance
            config_synchronizer: Configuration synchronizer
            kopf_indices: Kopf indices object
            metrics: Metrics collector
            index_tracker: Index synchronization tracker
            stop_timeout: Maximum seconds to wait for graceful stop (default: 5.0)
            error_retry_delay: Seconds to wait before retrying after unexpected errors (default: 1.0)
        """
        if max_interval < min_interval:
            raise ValueError(
                f"max_interval ({max_interval}) must be >= min_interval ({min_interval})"
            )

        self.config = config
        self.haproxy_config_context = haproxy_config_context
        self.template_renderer = template_renderer
        self.config_synchronizer = config_synchronizer
        self.kopf_indices = kopf_indices
        self.metrics = metrics
        self.min_interval = min_interval
        self.max_interval = max_interval
        self.stop_timeout = stop_timeout
        self.error_retry_delay = error_retry_delay
        self.index_tracker = index_tracker

        self._event = asyncio.Event()
        self._task: asyncio.Task | None = None
        self._last_render_time: float = 0
        self._stop: bool = False
        self._change_count = 0
        self._last_change_time: float = 0
        self._start_lock = asyncio.Lock()
        self._metrics = metrics

        # Trigger tracking for context
        self._pod_changed: bool = False
        self._trigger_source: str = "resource_changes"

        # Log warnings for unusual configurations
        if min_interval < 3:
            logger.warning(
                f"Very short min_interval ({min_interval}s) may cause high CPU usage during rapid changes"
            )
        if max_interval > 3600:
            logger.info(
                f"Long max_interval ({max_interval}s) - templates may become stale during quiet periods"
            )

    async def trigger(self, source: str = "resource_changes") -> None:
        """
        Signal that a resource changed and template rendering may be needed.

        This method is called by kopf event handlers when resources change.
        It doesn't immediately trigger rendering but signals the debouncer.

        Args:
            source: Source of the trigger - "resource_changes", "pod_changes", or "periodic_refresh"
        """
        self._change_count += 1
        self._last_change_time = time.time()

        # Track trigger source and pod changes
        if source == "pod_changes":
            self._pod_changed = True
            self._trigger_source = "pod_changes"
        elif (
            self._trigger_source != "pod_changes"
        ):  # Don't override pod changes with resource changes
            self._trigger_source = source

        self._event.set()

        # Record metric
        if self._metrics:
            self._metrics.record_debouncer_trigger()

    async def _run(self) -> None:
        """
        Background task that handles debounced template rendering.

        This task runs continuously, waiting for change events or timeout,
        and triggers template rendering according to the configured intervals.
        """
        logger.info("Template debouncer background task started")

        # Wait for index initialization to complete
        logger.info("Waiting for index initialization to complete...")
        await self.index_tracker.wait_for_indices_ready()
        logger.info("Index initialization complete - normal operation starting")

        while not self._stop:
            try:
                # Single time calculation per loop iteration for consistency
                current_time = time.time()
                time_since_last_render = current_time - self._last_render_time
                time_until_max = max(0, self.max_interval - time_since_last_render)

                # Update metrics for time since last render
                if self._metrics:
                    self._metrics.update_debouncer_last_render_time(
                        time_since_last_render
                    )

                # Wait for event or timeout (guaranteed execution)
                try:
                    await asyncio.wait_for(self._event.wait(), timeout=time_until_max)
                    # Use tracked trigger source when event was triggered
                    triggered_by = self._trigger_source
                except asyncio.TimeoutError:
                    # Max interval reached - force render
                    triggered_by = "periodic_refresh"

                # Check if we should stop
                if self._stop:
                    break  # type: ignore[unreachable]

                # Recalculate current time after waiting for accurate timing
                current_time = time.time()
                time_since_last_render = current_time - self._last_render_time

                # Skip min_interval wait for periodic refresh or if enough time has already passed
                if (
                    triggered_by != "periodic_refresh"
                    and time_since_last_render < self.min_interval
                ):
                    sleep_time = self.min_interval - time_since_last_render
                    logger.debug(
                        f"Rate limiting: waiting {sleep_time:.1f}s before rendering"
                    )
                    await asyncio.sleep(sleep_time)
                elif triggered_by == "periodic_refresh":
                    logger.debug(
                        f"Skipping min_interval wait for periodic refresh (already waited {self.max_interval}s)"
                    )

                # Clear event and count changes
                self._event.clear()
                changes_batched = self._change_count
                self._change_count = 0

                # Create trigger context
                pod_changed = self._pod_changed
                trigger_context = TriggerContext(
                    trigger_type=triggered_by, pod_changed=pod_changed
                )

                # Log rendering trigger
                match triggered_by:
                    case "resource_changes":
                        message = (
                            f"🔄 Rendering templates: {changes_batched} changes batched"
                        )
                        extra_fields = {}
                    case "pod_changes":
                        message = "🔄 Rendering templates: HAProxy pods changed"
                        extra_fields = {}
                    case _:  # periodic_refresh
                        message = f"⏰ Rendering templates: periodic refresh after {self.max_interval}s"
                        extra_fields = {"interval": self.max_interval}

                logger.info(
                    message,
                    changes_batched=changes_batched,
                    trigger=triggered_by,
                    pod_changed=pod_changed,
                    **extra_fields,
                )

                # Record metrics
                if self._metrics:
                    self._metrics.record_debouncer_render(triggered_by, changes_batched)

                # Reset trigger state after processing
                self._pod_changed = False
                self._trigger_source = "resource_changes"

                # Render templates with trigger context
                self._last_render_time = time.time()
                try:
                    await render_haproxy_templates(
                        config=self.config,
                        haproxy_config_context=self.haproxy_config_context,
                        template_renderer=self.template_renderer,
                        config_synchronizer=self.config_synchronizer,
                        kopf_indices=self.kopf_indices,
                        metrics=self.metrics,
                        logger=logger,
                        trigger_context=trigger_context,
                    )
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
                await asyncio.sleep(self.error_retry_delay)  # Brief pause before retry

        logger.info("Template debouncer background task stopped")

    async def start(self) -> None:
        """
        Start the debouncer background task.

        This should be called during operator startup.
        """
        async with self._start_lock:
            if self._task and not self._task.done():
                logger.warning("Debouncer already running")
                return

            self._stop = False
            self._task = asyncio.create_task(self._run())
            logger.info(
                f"Template debouncer started (min={self.min_interval}s, max={self.max_interval}s)"
            )

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
                await asyncio.wait_for(self._task, timeout=self.stop_timeout)
            except asyncio.TimeoutError:
                logger.warning("Debouncer task did not stop gracefully, cancelling")
                if not self._task.done():
                    self._task.cancel()
                try:
                    await self._task
                except asyncio.CancelledError:
                    pass

        logger.info("Template debouncer stopped")
