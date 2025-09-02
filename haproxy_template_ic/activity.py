"""
Activity tracking system for the HAProxy Template IC.

Provides event collection and storage for displaying recent operational
activities in the dashboard.
"""

import asyncio
from collections import deque
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from enum import Enum
from typing import Dict, List, Any, Optional, Deque
import logging

logger = logging.getLogger(__name__)

__all__ = ["EventType", "ActivityEvent", "ActivityBuffer", "get_activity_buffer"]


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

    def __init__(self, max_size: int = 5000):
        """Initialize activity buffer.

        Args:
            max_size: Maximum number of events to store (default: 5000)
        """
        self._buffer: Deque[ActivityEvent] = deque(maxlen=max_size)
        self._lock = asyncio.Lock()
        self._total_events = 0
        self._max_size = max_size

        logger.debug(f"Initialized ActivityBuffer with max_size={max_size}")

    async def add_event(
        self,
        event_type: EventType,
        message: str,
        source: str = "unknown",
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Add a new event to the buffer."""
        event = ActivityEvent.create(event_type, message, source, metadata)

        async with self._lock:
            self._buffer.append(event)
            self._total_events += 1

        logger.debug(f"Added activity event: {event.type.value} - {message[:50]}...")

    def add_event_sync(
        self,
        event_type: EventType,
        message: str,
        source: str = "unknown",
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Add event synchronously (for use in non-async contexts)."""
        event = ActivityEvent.create(event_type, message, source, metadata)

        # Note: This is not thread-safe, but needed for synchronous contexts
        # In practice, most usage will be async or single-threaded
        self._buffer.append(event)
        self._total_events += 1

        logger.debug(
            f"Added activity event (sync): {event.type.value} - {message[:50]}..."
        )

    async def get_recent(self, count: int = 1000) -> List[Dict[str, Any]]:
        """Get the most recent events."""
        async with self._lock:
            # Get the last 'count' events and convert to dicts
            recent = list(self._buffer)[-count:] if count > 0 else list(self._buffer)
            return [event.to_dict() for event in recent]

    def get_recent_sync(self, count: int = 1000) -> List[Dict[str, Any]]:
        """Get recent events synchronously."""
        # Note: This is not thread-safe, but needed for synchronous contexts
        recent = list(self._buffer)[-count:] if count > 0 else list(self._buffer)
        return [event.to_dict() for event in recent]

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


# Global activity buffer instance
_global_activity_buffer: Optional[ActivityBuffer] = None


def get_activity_buffer() -> ActivityBuffer:
    """Get the global activity buffer instance."""
    global _global_activity_buffer
    if _global_activity_buffer is None:
        _global_activity_buffer = ActivityBuffer()
        logger.info("Created global ActivityBuffer instance")
    return _global_activity_buffer


def set_activity_buffer(buffer: ActivityBuffer) -> None:
    """Set the global activity buffer instance (for testing)."""
    global _global_activity_buffer
    _global_activity_buffer = buffer
    logger.debug("Set global ActivityBuffer instance")
