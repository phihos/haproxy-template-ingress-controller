"""
Index initialization synchronization tracker.

Ensures template rendering only begins after all Kopf indices are initialized,
with timeout protection for zero-resource edge cases.
"""

import asyncio
import functools
import logging
from typing import Set, Callable
from haproxy_template_ic.constants import HAPROXY_PODS_INDEX
from haproxy_template_ic.models.config import Config

logger = logging.getLogger(__name__)


def create_tracking_decorator(
    tracker: "IndexSynchronizationTracker",
) -> Callable[[str], Callable[[Callable], Callable]]:
    """Factory function that creates tracking decorators with injected tracker."""

    def track_index_sync(resource_type: str):
        def decorator(func: Callable) -> Callable:
            @functools.wraps(func)
            async def wrapper(*args, **kwargs):
                tracker.mark_ready(resource_type)
                return await func(*args, **kwargs)

            return wrapper

        return decorator

    return track_index_sync


class IndexSynchronizationTracker:
    """
    Tracks index initialization completion with timeout protection.

    Simple event counting system that marks resource types as ready
    when their handlers are called, with timeout for zero-resource cases.
    """

    def __init__(self, config: Config):
        """Initialize tracker with resource types and timeout."""
        self.timeout = config.operator.index_initialization_timeout
        self.resource_types = set(config.watched_resources.keys())
        self.resource_types.add(HAPROXY_PODS_INDEX)  # Always track HAProxy pods

        self.ready_types: Set[str] = set()
        self._ready_event = asyncio.Event()
        self._complete = False

        if not self.resource_types:
            self._complete = True
            self._ready_event.set()
            logger.info("No resources to track - initialization complete")
        else:
            logger.info(
                f"Tracking {len(self.resource_types)} resource types with {self.timeout}s timeout"
            )

    def mark_ready(self, resource_type: str) -> None:
        """Mark a resource type as ready (handler called)."""
        if self._complete or resource_type not in self.resource_types:
            return

        if resource_type not in self.ready_types:
            self.ready_types.add(resource_type)
            logger.debug(f"Resource type {resource_type} marked ready")

            if self.ready_types == self.resource_types:
                self._complete = True
                self._ready_event.set()
                logger.debug("Index initialization complete for all resource types")

    async def wait_for_indices_ready(self) -> None:
        """Wait for all indices to be ready or timeout."""
        if self._complete:
            return

        try:
            await asyncio.wait_for(self._ready_event.wait(), timeout=self.timeout)
        except asyncio.TimeoutError:
            logger.info(
                f"Index initialization timeout after {self.timeout}s - proceeding"
            )
            self._complete = True
            self._ready_event.set()

    def is_initialization_complete(self) -> bool:
        """Check if initialization is complete."""
        return self._complete
