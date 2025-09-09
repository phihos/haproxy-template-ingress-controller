"""
Activity tracking system for the HAProxy Template IC.

Provides event collection and storage for displaying recent operational
activities in the dashboard.
"""

import asyncio
import logging
from collections import deque
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from enum import Enum
from typing import Dict, List, Any, Optional, Deque

from haproxy_template_ic.constants import (
    DEFAULT_ACTIVITY_BUFFER_SIZE,
    DEFAULT_ACTIVITY_QUERY_LIMIT,
)

logger = logging.getLogger(__name__)

__all__ = [
    "EventType",
    "ActivityEvent",
    "ActivityBuffer",
    "PriorityActivityBuffer",
    "get_activity_buffer",
    "DEPLOYMENT_EVENT_TYPES",
    "HIGH_PRIORITY_EVENT_TYPES",
    "MEDIUM_PRIORITY_EVENT_TYPES",
    "LOW_PRIORITY_EVENT_TYPES",
]


class EventType(str, Enum):
    """Types of activity events."""

    CREATE = "CREATE"
    UPDATE = "UPDATE"
    DELETE = "DELETE"
    SYNC = "SYNC"
    SUCCESS = "SUCCESS"
    ERROR = "ERROR"
    INFO = "INFO"
    RELOAD = "RELOAD"

    # Deployment-specific event types
    DEPLOYMENT_START = "DEPLOYMENT_START"
    DEPLOYMENT_SUCCESS = "DEPLOYMENT_SUCCESS"
    DEPLOYMENT_FAILED = "DEPLOYMENT_FAILED"
    RELOAD_TRIGGERED = "RELOAD_TRIGGERED"


# Common event type sets for filtering
DEPLOYMENT_EVENT_TYPES = {
    EventType.DEPLOYMENT_START,
    EventType.DEPLOYMENT_SUCCESS,
    EventType.DEPLOYMENT_FAILED,
    EventType.RELOAD_TRIGGERED,
}

HIGH_PRIORITY_EVENT_TYPES = {
    EventType.SYNC,
    EventType.RELOAD,
    EventType.ERROR,
    EventType.DEPLOYMENT_START,
    EventType.DEPLOYMENT_SUCCESS,
    EventType.DEPLOYMENT_FAILED,
    EventType.RELOAD_TRIGGERED,
}

MEDIUM_PRIORITY_EVENT_TYPES = {
    EventType.CREATE,
    EventType.UPDATE,
    EventType.DELETE,
}

LOW_PRIORITY_EVENT_TYPES = {
    EventType.SUCCESS,
    EventType.INFO,
}


@dataclass
class ActivityEvent:
    """Represents a single activity event."""

    type: EventType
    message: str
    timestamp: str
    source: str = "unknown"
    metadata: Optional[Dict[str, Any]] = None

    @classmethod
    def create(
        cls,
        event_type: EventType,
        message: str,
        source: str = "unknown",
        metadata: Optional[Dict[str, Any]] = None,
    ) -> "ActivityEvent":
        """Create a new activity event with current timestamp."""
        return cls(
            type=event_type,
            message=message,
            timestamp=datetime.now(timezone.utc).isoformat(),
            source=source,
            metadata=metadata or {},
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return asdict(self)


class ActivityBuffer:
    """Thread-safe circular buffer for storing activity events."""

    def __init__(self, max_size: int = DEFAULT_ACTIVITY_BUFFER_SIZE):
        """Initialize activity buffer.

        Args:
            max_size: Maximum number of events to store (default: DEFAULT_ACTIVITY_BUFFER_SIZE)
        """
        self._buffer: Deque[ActivityEvent] = deque(maxlen=max_size)
        self._lock = asyncio.Lock()
        self._total_events = 0
        self._max_size = max_size

        logger.debug(f"Initialized ActivityBuffer with max_size={max_size}")

    def _add_event_impl(
        self,
        event_type: EventType,
        message: str,
        source: str = "unknown",
        metadata: Optional[Dict[str, Any]] = None,
    ) -> ActivityEvent:
        """Shared implementation for adding events."""
        event = ActivityEvent.create(event_type, message, source, metadata)
        self._buffer.append(event)
        self._total_events += 1
        logger.debug(f"Added activity event: {event.type.value} - {message[:50]}...")
        return event

    async def add_event(
        self,
        event_type: EventType,
        message: str,
        source: str = "unknown",
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Add a new event to the buffer."""
        async with self._lock:
            self._add_event_impl(event_type, message, source, metadata)

    def add_event_sync(
        self,
        event_type: EventType,
        message: str,
        source: str = "unknown",
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Add event synchronously (for use in non-async contexts)."""
        # Note: This is not thread-safe, but needed for synchronous contexts
        # In practice, most usage will be async or single-threaded
        self._add_event_impl(event_type, message, source, metadata)

    def _get_recent_impl(
        self, count: int = DEFAULT_ACTIVITY_QUERY_LIMIT
    ) -> List[Dict[str, Any]]:
        """Shared implementation for getting recent events."""
        recent = list(self._buffer)[-count:] if count > 0 else list(self._buffer)
        return [event.to_dict() for event in recent]

    async def get_recent(
        self, count: int = DEFAULT_ACTIVITY_QUERY_LIMIT
    ) -> List[Dict[str, Any]]:
        """Get the most recent events."""
        async with self._lock:
            return self._get_recent_impl(count)

    def get_recent_sync(
        self, count: int = DEFAULT_ACTIVITY_QUERY_LIMIT
    ) -> List[Dict[str, Any]]:
        """Get recent events synchronously."""
        # Note: This is not thread-safe, but needed for synchronous contexts
        return self._get_recent_impl(count)

    async def clear(self) -> None:
        """Clear all events from the buffer."""
        async with self._lock:
            self._buffer.clear()
            logger.debug("Cleared activity buffer")

    @property
    def total_count(self) -> int:
        """Get total number of events ever added."""
        return self._total_events

    @property
    def current_count(self) -> int:
        """Get current number of events in buffer."""
        return len(self._buffer)

    @property
    def max_size(self) -> int:
        """Get maximum buffer size."""
        return self._max_size

    def _filter_events_by_types(
        self,
        event_types: set[EventType],
        endpoint: Optional[str] = None,
        count: int = DEFAULT_ACTIVITY_QUERY_LIMIT,
    ) -> List[Dict[str, Any]]:
        """Filter events by types and optionally by endpoint."""
        filtered_events = []
        for event in self._buffer:
            if event.type in event_types:
                if endpoint is None:
                    filtered_events.append(event)
                elif event.metadata and event.metadata.get("endpoint") == endpoint:
                    filtered_events.append(event)

        recent_events = filtered_events[-count:] if count > 0 else filtered_events
        return [event.to_dict() for event in recent_events]

    async def get_deployment_events(
        self, endpoint: Optional[str] = None, count: int = DEFAULT_ACTIVITY_QUERY_LIMIT
    ) -> List[Dict[str, Any]]:
        """Get deployment-related events, optionally filtered by endpoint."""
        async with self._lock:
            return self._filter_events_by_types(DEPLOYMENT_EVENT_TYPES, endpoint, count)

    async def get_events_by_type(
        self, event_types: List[EventType], count: int = DEFAULT_ACTIVITY_QUERY_LIMIT
    ) -> List[Dict[str, Any]]:
        """Get events filtered by event type."""
        async with self._lock:
            return self._filter_events_by_types(set(event_types), None, count)

class PriorityActivityBuffer(ActivityBuffer):
    """Priority-based activity buffer that ensures important events are retained.

    Maintains separate storage tiers for different event priorities:
    - High priority: SYNC, RELOAD, DEPLOYMENT_*, ERROR (critical operations)
    - Medium priority: CREATE, DELETE, UPDATE (resource changes)
    - Low priority: SUCCESS, INFO (routine operations)

    Guarantees minimum retention per tier while sharing remaining capacity.
    """

    def __init__(
        self,
        max_size: int = DEFAULT_ACTIVITY_BUFFER_SIZE,
        high_priority_min: int = 1000,
        medium_priority_min: int = 500,
        low_priority_min: int = 100,
    ):
        """Initialize priority-based activity buffer.

        Args:
            max_size: Total maximum number of events to store
            high_priority_min: Minimum events guaranteed for high priority tier
            medium_priority_min: Minimum events guaranteed for medium priority tier
            low_priority_min: Minimum events guaranteed for low priority tier
        """
        # Validate tier minimums don't exceed total capacity
        total_min = high_priority_min + medium_priority_min + low_priority_min
        if total_min > max_size:
            raise ValueError(
                f"Sum of minimum tier sizes ({total_min}) exceeds max_size ({max_size})"
            )

        super().__init__(max_size)

        # Tier configuration
        self._high_priority_min = high_priority_min
        self._medium_priority_min = medium_priority_min
        self._low_priority_min = low_priority_min
        self._shared_pool_size = max_size - total_min

        # Separate storage for each tier
        self._high_priority: Deque[ActivityEvent] = deque()
        self._medium_priority: Deque[ActivityEvent] = deque()
        self._low_priority: Deque[ActivityEvent] = deque()

        # Define event type priorities using constants
        self._high_priority_types = HIGH_PRIORITY_EVENT_TYPES
        self._medium_priority_types = MEDIUM_PRIORITY_EVENT_TYPES
        self._low_priority_types = LOW_PRIORITY_EVENT_TYPES

        logger.debug(
            f"Initialized PriorityActivityBuffer: total={max_size}, "
            f"high_min={high_priority_min}, med_min={medium_priority_min}, "
            f"low_min={low_priority_min}, shared={self._shared_pool_size}"
        )

    def _get_event_tier(self, event_type: EventType) -> str:
        """Determine which tier an event belongs to."""
        if event_type in self._high_priority_types:
            return "high"
        elif event_type in self._medium_priority_types:
            return "medium"
        else:
            return "low"

    def _get_tier_deque(self, tier: str) -> Deque[ActivityEvent]:
        """Get the deque for a specific tier."""
        if tier == "high":
            return self._high_priority
        elif tier == "medium":
            return self._medium_priority
        else:
            return self._low_priority

    def _get_tier_capacity(self, tier: str) -> int:
        """Get current capacity available for a tier."""
        tier_deque = self._get_tier_deque(tier)
        tier_min = {
            "high": self._high_priority_min,
            "medium": self._medium_priority_min,
            "low": self._low_priority_min,
        }[tier]

        current_size = len(tier_deque)
        return max(0, tier_min + self._get_shared_allocation() - current_size)

    def _get_shared_allocation(self) -> int:
        """Calculate how much shared pool capacity each tier gets."""
        return self._shared_pool_size // 3

    def _evict_if_needed(self, target_tier: str) -> None:
        """Evict old events if needed to make room for new event in target tier."""
        total_events = (
            len(self._high_priority)
            + len(self._medium_priority)
            + len(self._low_priority)
        )

        # If adding one more event would exceed max_size, we need to evict
        if total_events < self._max_size:
            return  # No eviction needed

        # Evict oldest events from lowest priority tiers first
        # Never evict below guaranteed minimums

        # Try to evict from low priority first (if not the target)
        if target_tier != "low" and len(self._low_priority) > self._low_priority_min:
            self._low_priority.popleft()
            logger.debug("Evicted oldest low-priority event")
            return

        # Then try medium priority
        if (
            target_tier != "medium"
            and len(self._medium_priority) > self._medium_priority_min
        ):
            self._medium_priority.popleft()
            logger.debug("Evicted oldest medium-priority event")
            return

        # Finally high priority (only if not at minimum)
        if target_tier != "high" and len(self._high_priority) > self._high_priority_min:
            self._high_priority.popleft()
            logger.debug("Evicted oldest high-priority event")
            return

        # If target tier is at minimum, we can still evict one of its own events
        target_deque = self._get_tier_deque(target_tier)
        if len(target_deque) > 0:
            target_deque.popleft()
            logger.debug(f"Evicted oldest {target_tier}-priority event (at minimum)")

    def _add_event_to_tier(
        self,
        event_type: EventType,
        message: str,
        source: str = "unknown",
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Shared implementation for adding events to appropriate priority tier."""
        event = ActivityEvent.create(event_type, message, source, metadata)
        tier = self._get_event_tier(event_type)

        self._evict_if_needed(tier)

        tier_deque = self._get_tier_deque(tier)
        tier_deque.append(event)
        self._total_events += 1

        logger.debug(
            f"Added {tier}-priority event: {event.type.value} - {message[:50]}..."
        )

    async def add_event(
        self,
        event_type: EventType,
        message: str,
        source: str = "unknown",
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Add a new event to the appropriate priority tier."""
        async with self._lock:
            self._add_event_to_tier(event_type, message, source, metadata)

    def add_event_sync(
        self,
        event_type: EventType,
        message: str,
        source: str = "unknown",
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Add event synchronously to appropriate priority tier."""
        self._add_event_to_tier(event_type, message, source, metadata)

    async def get_recent(
        self, count: int = DEFAULT_ACTIVITY_QUERY_LIMIT
    ) -> List[Dict[str, Any]]:
        """Get the most recent events from all tiers, merged chronologically."""
        async with self._lock:
            return self._get_merged_recent(count)

    def get_recent_sync(
        self, count: int = DEFAULT_ACTIVITY_QUERY_LIMIT
    ) -> List[Dict[str, Any]]:
        """Get recent events synchronously from all tiers, merged chronologically."""
        return self._get_merged_recent(count)

    def _get_merged_recent(self, count: int) -> List[Dict[str, Any]]:
        """Merge recent events from all tiers in chronological order."""
        # Combine all events from all tiers
        all_events = (
            list(self._high_priority)
            + list(self._medium_priority)
            + list(self._low_priority)
        )

        # Sort by timestamp (most recent last)
        all_events.sort(key=lambda e: e.timestamp)

        # Get the last 'count' events and convert to dicts
        recent = all_events[-count:] if count > 0 else all_events
        return [event.to_dict() for event in recent]

    async def clear(self) -> None:
        """Clear all events from all tiers."""
        async with self._lock:
            self._high_priority.clear()
            self._medium_priority.clear()
            self._low_priority.clear()
            logger.debug("Cleared all tiers in priority activity buffer")

    @property
    def current_count(self) -> int:
        """Get current number of events in all tiers."""
        return (
            len(self._high_priority)
            + len(self._medium_priority)
            + len(self._low_priority)
        )

    def get_tier_stats(self) -> Dict[str, int]:
        """Get statistics about events in each tier."""
        return {
            "high_priority": len(self._high_priority),
            "medium_priority": len(self._medium_priority),
            "low_priority": len(self._low_priority),
            "total": self.current_count,
        }


# Global activity buffer instance
_global_activity_buffer: Optional[ActivityBuffer] = None


def get_activity_buffer() -> ActivityBuffer:
    """Get the global activity buffer instance."""
    global _global_activity_buffer
    if _global_activity_buffer is None:
        _global_activity_buffer = PriorityActivityBuffer()
        logger.info("Created global PriorityActivityBuffer instance")
    return _global_activity_buffer


def set_activity_buffer(buffer: ActivityBuffer) -> None:
    """Set the global activity buffer instance."""
    global _global_activity_buffer
    _global_activity_buffer = buffer
    logger.debug("Set global ActivityBuffer instance")
