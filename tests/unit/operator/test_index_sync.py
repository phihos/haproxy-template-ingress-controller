"""Unit tests for the index synchronization tracker."""

import asyncio
from unittest.mock import Mock

import pytest

from haproxy_template_ic.constants import HAPROXY_PODS_INDEX
from haproxy_template_ic.models.config import Config, OperatorConfig
from haproxy_template_ic.operator.index_sync import IndexSynchronizationTracker
from tests.unit.conftest import create_config_mock_with_watched_resources


@pytest.fixture
def config():
    """Create a mock config for testing."""
    return create_config_mock_with_watched_resources()


@pytest.fixture
def tracker(config):
    """Create an IndexSynchronizationTracker for testing."""
    return IndexSynchronizationTracker(config)


def test_index_sync_tracker_init_proper_resource_tracking(config):
    """Test that all resource types get tracked properly."""
    tracker = IndexSynchronizationTracker(config)

    # All resource types should be tracked (watched resources + HAProxy pods)
    assert len(tracker.resource_types) == 4
    assert "services" in tracker.resource_types
    assert "ingresses" in tracker.resource_types
    assert "secrets" in tracker.resource_types
    assert HAPROXY_PODS_INDEX in tracker.resource_types

    # Should not be complete initially
    assert not tracker.is_initialization_complete()
    assert not tracker._complete
    assert not tracker._ready_event.is_set()


def test_index_sync_tracker_init_empty_resources():
    """Test initialization with no watched resources (but HAProxy pods still tracked)."""
    config = Mock(spec=Config)
    config.operator = Mock(spec=OperatorConfig)
    config.operator.index_initialization_timeout = 5
    config.watched_resources = {}

    tracker = IndexSynchronizationTracker(config)

    # Should only have HAProxy pods resource type
    assert len(tracker.resource_types) == 1
    assert HAPROXY_PODS_INDEX in tracker.resource_types
    assert len(tracker.ready_types) == 0

    # Should not be complete initially since HAProxy pods need to be tracked
    assert not tracker._ready_event.is_set()
    assert not tracker.is_initialization_complete()


def test_index_sync_tracker_mark_ready_triggers_completion(tracker):
    """Test that marking all resource types as ready triggers completion."""
    # Should not be ready initially
    assert not tracker._ready_event.is_set()

    tracker.mark_ready("services")
    tracker.mark_ready("ingresses")

    # Should not be ready yet (missing secrets and HAProxy pods)
    assert not tracker._ready_event.is_set()
    assert not tracker.is_initialization_complete()

    tracker.mark_ready("secrets")

    # Should still not be ready yet (missing HAProxy pods)
    assert not tracker._ready_event.is_set()
    assert not tracker.is_initialization_complete()

    tracker.mark_ready(HAPROXY_PODS_INDEX)

    # Now should be ready
    assert tracker._ready_event.is_set()
    assert tracker.is_initialization_complete()


def test_index_sync_tracker_mark_ready_ignores_unknown_types(tracker):
    """Test that marking unknown resource types is ignored."""
    # Mark unknown resource - should not affect readiness
    tracker.mark_ready("unknown_resource")

    # Should still not be ready (known resources not marked)
    assert not tracker.is_initialization_complete()

    # Complete known resources
    tracker.mark_ready("services")
    tracker.mark_ready("ingresses")
    tracker.mark_ready("secrets")
    tracker.mark_ready(HAPROXY_PODS_INDEX)

    # Now should be ready
    assert tracker.is_initialization_complete()


def test_index_sync_tracker_mark_ready_disabled_after_completion(tracker):
    """Test that marking ready is disabled after initialization completes."""
    # Complete initialization
    tracker.mark_ready("services")
    tracker.mark_ready("ingresses")
    tracker.mark_ready("secrets")
    tracker.mark_ready(HAPROXY_PODS_INDEX)

    assert tracker.is_initialization_complete()

    # Further marking calls should return immediately (no effect)
    initial_ready_count = len(tracker.ready_types)
    tracker.mark_ready("new_resource")
    assert len(tracker.ready_types) == initial_ready_count


@pytest.mark.asyncio
async def test_index_sync_tracker_wait_for_indices_ready_immediate_return(tracker):
    """Test wait_for_indices_ready returns immediately if already complete."""
    # Mark as complete first
    tracker._complete = True
    tracker._ready_event.set()

    # Should return immediately
    await tracker.wait_for_indices_ready()
    assert tracker.is_initialization_complete()


@pytest.mark.asyncio
async def test_index_sync_tracker_wait_for_indices_ready_with_marks(tracker):
    """Test wait_for_indices_ready waits and returns when marks complete."""
    # Start wait in background
    wait_task = asyncio.create_task(tracker.wait_for_indices_ready())

    # Give it a moment to start waiting
    await asyncio.sleep(0.01)
    assert not wait_task.done()

    # Trigger all ready marks
    tracker.mark_ready("services")
    tracker.mark_ready("ingresses")
    tracker.mark_ready("secrets")
    tracker.mark_ready(HAPROXY_PODS_INDEX)

    # Wait should complete
    await wait_task
    assert tracker.is_initialization_complete()


@pytest.mark.asyncio
async def test_index_sync_tracker_wait_for_indices_ready_with_timeout():
    """Test wait_for_indices_ready completes with timeout."""
    config = Mock(spec=Config)
    config.operator = Mock(spec=OperatorConfig)
    config.operator.index_initialization_timeout = 0.1  # Very short timeout
    config.watched_resources = {"services": Mock()}

    tracker = IndexSynchronizationTracker(config)

    # Should complete due to timeout
    await tracker.wait_for_indices_ready()
    assert tracker.is_initialization_complete()


def test_index_sync_tracker_initialization_with_custom_timeout():
    """Test initialization with custom timeout value."""
    config = Mock(spec=Config)
    config.operator = Mock(spec=OperatorConfig)
    config.operator.index_initialization_timeout = 10  # Custom timeout
    config.watched_resources = {"services": Mock()}

    tracker = IndexSynchronizationTracker(config)

    assert tracker.timeout == 10
    assert tracker.resource_types == {"services", HAPROXY_PODS_INDEX}


def test_index_sync_tracker_haproxy_pods_always_tracked():
    """Test that HAProxy pods are always tracked regardless of config."""
    # Even with empty watched resources, HAProxy pods should be tracked
    config = Mock(spec=Config)
    config.operator = Mock(spec=OperatorConfig)
    config.operator.index_initialization_timeout = 5
    config.watched_resources = {}

    tracker = IndexSynchronizationTracker(config)

    # HAProxy pods should always be in resource types
    assert HAPROXY_PODS_INDEX in tracker.resource_types

    # Should not be ready until HAProxy pods ready
    assert not tracker.is_initialization_complete()

    # Complete HAProxy pods initialization
    tracker.mark_ready(HAPROXY_PODS_INDEX)

    # Now should be ready
    assert tracker.is_initialization_complete()


def test_index_sync_tracker_haproxy_pods_with_watched_resources(tracker):
    """Test HAProxy pods integration with watched resources."""
    # Mark all watched resources as ready except HAProxy pods
    tracker.mark_ready("services")
    tracker.mark_ready("ingresses")
    tracker.mark_ready("secrets")

    # Should not be ready - missing HAProxy pods
    assert not tracker.is_initialization_complete()

    # Mark HAProxy pods as ready
    tracker.mark_ready(HAPROXY_PODS_INDEX)

    # Now should be ready
    assert tracker.is_initialization_complete()
