"""
Unit tests for activity tracking system.

Tests for ActivityBuffer and PriorityActivityBuffer classes including
event storage, prioritization, and eviction strategies.
"""

import pytest
import asyncio
from datetime import datetime, timezone

from haproxy_template_ic.activity import (
    ActivityBuffer,
    PriorityActivityBuffer,
    EventType,
    ActivityEvent,
)


class TestActivityBuffer:
    """Test basic ActivityBuffer functionality."""

    @pytest.mark.asyncio
    async def test_basic_event_storage(self):
        """Test basic event addition and retrieval."""
        buffer = ActivityBuffer(max_size=10)

        await buffer.add_event(EventType.INFO, "Test message", "test_source")

        events = await buffer.get_recent(5)
        assert len(events) == 1
        assert events[0]["type"] == "INFO"
        assert events[0]["message"] == "Test message"
        assert events[0]["source"] == "test_source"

    def test_sync_event_storage(self):
        """Test synchronous event addition."""
        buffer = ActivityBuffer(max_size=10)

        buffer.add_event_sync(EventType.ERROR, "Error message", "test_source")

        events = buffer.get_recent_sync(5)
        assert len(events) == 1
        assert events[0]["type"] == "ERROR"
        assert events[0]["message"] == "Error message"

    def test_buffer_size_limit(self):
        """Test that buffer respects max_size limit."""
        buffer = ActivityBuffer(max_size=3)

        # Add more events than the limit
        for i in range(5):
            buffer.add_event_sync(EventType.INFO, f"Message {i}", "test")

        events = buffer.get_recent_sync(10)
        assert len(events) == 3
        # Should contain the last 3 events
        assert events[0]["message"] == "Message 2"
        assert events[-1]["message"] == "Message 4"


class TestPriorityActivityBuffer:
    """Test PriorityActivityBuffer functionality."""

    def test_initialization_validation(self):
        """Test that initialization validates tier minimums."""
        # Valid configuration
        buffer = PriorityActivityBuffer(
            max_size=1000,
            high_priority_min=400,
            medium_priority_min=300,
            low_priority_min=100,
        )
        assert buffer.max_size == 1000

        # Invalid - minimums exceed total
        with pytest.raises(ValueError, match="Sum of minimum tier sizes"):
            PriorityActivityBuffer(
                max_size=100,
                high_priority_min=50,
                medium_priority_min=50,
                low_priority_min=50,
            )

    def test_event_tier_classification(self):
        """Test that events are classified into correct tiers."""
        buffer = PriorityActivityBuffer(
            max_size=100,
            high_priority_min=30,
            medium_priority_min=30,
            low_priority_min=20,
        )

        # Test high priority events
        buffer.add_event_sync(EventType.SYNC, "Sync event", "test")
        buffer.add_event_sync(EventType.ERROR, "Error event", "test")
        buffer.add_event_sync(EventType.DEPLOYMENT_SUCCESS, "Deploy success", "test")

        # Test medium priority events
        buffer.add_event_sync(EventType.UPDATE, "Update event", "test")
        buffer.add_event_sync(EventType.CREATE, "Create event", "test")
        buffer.add_event_sync(EventType.DELETE, "Delete event", "test")

        # Test low priority events
        buffer.add_event_sync(EventType.SUCCESS, "Success event", "test")
        buffer.add_event_sync(EventType.INFO, "Info event", "test")

        stats = buffer.get_tier_stats()
        assert stats["high_priority"] == 3
        assert stats["medium_priority"] == 3
        assert stats["low_priority"] == 2
        assert stats["total"] == 8

    def test_priority_eviction_strategy(self):
        """Test that eviction prioritizes low priority events first."""
        # Small buffer to force eviction
        buffer = PriorityActivityBuffer(
            max_size=10, high_priority_min=3, medium_priority_min=3, low_priority_min=2
        )

        # Fill up with different priority events
        for i in range(3):
            buffer.add_event_sync(EventType.SYNC, f"High {i}", "test")
        for i in range(3):
            buffer.add_event_sync(EventType.UPDATE, f"Medium {i}", "test")
        for i in range(3):
            buffer.add_event_sync(EventType.SUCCESS, f"Low {i}", "test")

        stats = buffer.get_tier_stats()
        assert stats["total"] == 9  # 3 + 3 + 3

        # Fill the buffer to capacity, then add one more to force eviction
        buffer.add_event_sync(
            EventType.INFO, "Fill capacity", "test"
        )  # Now at capacity (10)

        stats = buffer.get_tier_stats()
        assert stats["total"] == 10

        # Now add one more high priority event - should evict low priority first
        buffer.add_event_sync(EventType.ERROR, "New high priority", "test")

        stats = buffer.get_tier_stats()
        assert stats["total"] == 10  # Should stay at max
        assert stats["high_priority"] == 4  # 3 + 1 new
        assert stats["medium_priority"] == 3  # unchanged
        assert (
            stats["low_priority"] == 3
        )  # 4 - 1 evicted (at minimum, so one of its own events may have been evicted)

        # Verify we can retrieve all events
        events = buffer.get_recent_sync(20)
        assert len(events) == 10

    def test_guaranteed_minimums_preserved(self):
        """Test that guaranteed minimums per tier are preserved."""
        buffer = PriorityActivityBuffer(
            max_size=15, high_priority_min=5, medium_priority_min=5, low_priority_min=3
        )

        # Fill buffer beyond capacity with low priority events
        for i in range(20):
            buffer.add_event_sync(EventType.INFO, f"Low priority {i}", "test")

        stats = buffer.get_tier_stats()
        # Should respect max_size limit but not exceed minimums
        assert stats["total"] <= 15
        assert stats["low_priority"] >= 3  # At least the minimum

    @pytest.mark.asyncio
    async def test_chronological_merge(self):
        """Test that events from different tiers are merged chronologically."""
        buffer = PriorityActivityBuffer(
            max_size=100,
            high_priority_min=30,
            medium_priority_min=30,
            low_priority_min=20,
        )

        # Add events with slight delays to ensure different timestamps
        await buffer.add_event(EventType.SYNC, "High 1", "test")
        await asyncio.sleep(0.001)  # Small delay
        await buffer.add_event(EventType.UPDATE, "Medium 1", "test")
        await asyncio.sleep(0.001)
        await buffer.add_event(EventType.SUCCESS, "Low 1", "test")
        await asyncio.sleep(0.001)
        await buffer.add_event(EventType.ERROR, "High 2", "test")

        events = await buffer.get_recent(10)
        assert len(events) == 4

        # Events should be in chronological order (oldest first in recent list)
        messages = [event["message"] for event in events]
        assert messages == ["High 1", "Medium 1", "Low 1", "High 2"]

    def test_tier_stats(self):
        """Test tier statistics reporting."""
        buffer = PriorityActivityBuffer(
            max_size=100,
            high_priority_min=30,
            medium_priority_min=30,
            low_priority_min=20,
        )

        # Add various events
        buffer.add_event_sync(EventType.SYNC, "High", "test")
        buffer.add_event_sync(EventType.UPDATE, "Medium", "test")
        buffer.add_event_sync(EventType.SUCCESS, "Low", "test")

        stats = buffer.get_tier_stats()
        expected = {
            "high_priority": 1,
            "medium_priority": 1,
            "low_priority": 1,
            "total": 3,
        }
        assert stats == expected

    @pytest.mark.asyncio
    async def test_clear_all_tiers(self):
        """Test that clear removes events from all tiers."""
        buffer = PriorityActivityBuffer(
            max_size=100,
            high_priority_min=30,
            medium_priority_min=30,
            low_priority_min=20,
        )

        # Add events to all tiers
        await buffer.add_event(EventType.ERROR, "High", "test")
        await buffer.add_event(EventType.UPDATE, "Medium", "test")
        await buffer.add_event(EventType.INFO, "Low", "test")

        assert buffer.current_count == 3

        await buffer.clear()

        assert buffer.current_count == 0
        stats = buffer.get_tier_stats()
        assert all(count == 0 for count in stats.values())


class TestActivityEvent:
    """Test ActivityEvent class."""

    def test_event_creation(self):
        """Test activity event creation with timestamp."""
        event = ActivityEvent.create(
            EventType.SYNC, "Test sync event", "test_source", {"key": "value"}
        )

        assert event.type == EventType.SYNC
        assert event.message == "Test sync event"
        assert event.source == "test_source"
        assert event.metadata == {"key": "value"}

        # Timestamp should be recent
        timestamp = datetime.fromisoformat(event.timestamp.replace("Z", "+00:00"))
        now = datetime.now(timezone.utc)
        assert (now - timestamp).total_seconds() < 1.0

    def test_event_to_dict(self):
        """Test event serialization to dict."""
        event = ActivityEvent.create(EventType.ERROR, "Error message", "test")
        event_dict = event.to_dict()

        assert event_dict["type"] == "ERROR"
        assert event_dict["message"] == "Error message"
        assert event_dict["source"] == "test"
        assert "timestamp" in event_dict
        assert event_dict["metadata"] == {}


@pytest.mark.asyncio
class TestBufferIntegration:
    """Integration tests for buffer behavior under various conditions."""

    async def test_mixed_async_sync_operations(self):
        """Test mixing async and sync operations."""
        buffer = PriorityActivityBuffer(
            max_size=50,
            high_priority_min=15,
            medium_priority_min=15,
            low_priority_min=10,
        )

        # Mix async and sync additions
        await buffer.add_event(EventType.SYNC, "Async high", "test")
        buffer.add_event_sync(EventType.UPDATE, "Sync medium", "test")
        await buffer.add_event(EventType.INFO, "Async low", "test")

        # Test both retrieval methods
        async_events = await buffer.get_recent(10)
        sync_events = buffer.get_recent_sync(10)

        assert len(async_events) == 3
        assert len(sync_events) == 3

        # Both methods should return the same events
        assert [e["message"] for e in async_events] == [
            e["message"] for e in sync_events
        ]

    async def test_high_frequency_events(self):
        """Test behavior under high frequency event addition."""
        buffer = PriorityActivityBuffer(
            max_size=100,
            high_priority_min=30,
            medium_priority_min=30,
            low_priority_min=20,
        )

        # Simulate high frequency template rendering (low priority)
        for i in range(150):  # More than buffer capacity
            buffer.add_event_sync(EventType.SUCCESS, f"Template render {i}", "template")

        # Add some critical events
        for i in range(10):
            await buffer.add_event(EventType.SYNC, f"Critical sync {i}", "operator")

        stats = buffer.get_tier_stats()

        # Should preserve high priority events
        assert stats["high_priority"] == 10
        # Low priority should be trimmed but still have some events
        assert stats["low_priority"] >= 20  # At least minimum
        assert stats["total"] <= 100  # Respects max size

        # Verify we can find the critical events
        events = await buffer.get_recent(200)
        sync_events = [e for e in events if "Critical sync" in e["message"]]
        assert len(sync_events) == 10  # All critical events preserved
