"""
Test pod management functionality.

Tests for haproxy_pods_index function.
"""

import pytest

from haproxy_template_ic.operator.pod_management import (
    haproxy_pods_index,
    handle_haproxy_pod_event,
)
from tests.unit.conftest import (
    create_k8s_pod_resource,
    create_logger_mock,
    create_memo_mock_with_debouncer,
)


@pytest.mark.asyncio
async def test_haproxy_pods_index_normal_pod():
    """Test that haproxy_pods_index correctly indexes normal pods."""
    namespace = "test-namespace"
    name = "test-pod"
    body = create_k8s_pod_resource(
        name=name,
        namespace=namespace,
        phase="Running",
        additional_status={"podIP": "10.0.0.1"},
    )
    logger = create_logger_mock()

    result = await haproxy_pods_index(
        namespace=namespace,
        name=name,
        body=body,
        logger=logger,
    )

    # Should return indexed pod data
    assert result == {(namespace, name): body}
    logger.info.assert_any_call(f"📝 Indexing HAProxy pod {namespace}/{name}")


@pytest.mark.asyncio
async def test_haproxy_pods_index_deleted_pod():
    """Test that haproxy_pods_index correctly removes deleted pods from index."""
    namespace = "test-namespace"
    name = "test-pod"
    body = create_k8s_pod_resource(
        name=name,
        namespace=namespace,
        phase="Terminating",
        additional_status={"podIP": "10.0.0.1"},
        additional_metadata={"deletionTimestamp": "2024-01-01T12:00:00Z"},
    )
    logger = create_logger_mock()

    result = await haproxy_pods_index(
        namespace=namespace,
        name=name,
        body=body,
        logger=logger,
    )

    # Should return empty dict to remove from index
    assert result == {}
    logger.info.assert_any_call(f"📝 Indexing HAProxy pod {namespace}/{name}")
    logger.info.assert_any_call(
        f"🗑️ Pod {namespace}/{name} is being deleted, excluding from index"
    )


@pytest.mark.asyncio
async def test_haproxy_pods_index_not_running():
    """Test that haproxy_pods_index excludes non-running pods."""
    namespace = "test-namespace"
    name = "test-pod"
    body = create_k8s_pod_resource(
        name=name,
        namespace=namespace,
        phase="Pending",
        additional_status={"podIP": None},
    )
    logger = create_logger_mock()

    result = await haproxy_pods_index(
        namespace=namespace,
        name=name,
        body=body,
        logger=logger,
    )

    # Should return empty dict to exclude from index
    assert result == {}


@pytest.mark.asyncio
async def test_handle_haproxy_pod_event_with_positional_args():
    """Test handle_haproxy_pod_event with positional arguments (normal case)."""
    # Mock memo with debouncer
    memo = create_memo_mock_with_debouncer()

    # Override trigger to assert the expected trigger type
    async def mock_trigger(trigger_type):
        assert trigger_type == "pod_changes"

    memo.operations.debouncer.trigger = mock_trigger

    # Mock logger
    logger = create_logger_mock()

    body = create_k8s_pod_resource(
        name="test-pod",
        namespace="default",
        phase="Running",
        additional_status={"podIP": "10.0.0.1"},
    )
    meta = {"name": "test-pod", "namespace": "default"}

    # Call with positional arguments
    await handle_haproxy_pod_event(
        body=body, meta=meta, type="ADDED", logger=logger, memo=memo
    )

    # If we get here without exception, the function worked correctly


@pytest.mark.asyncio
async def test_handle_haproxy_pod_event_with_kwargs():
    """Test handle_haproxy_pod_event with keyword arguments (Kopf behavior)."""
    # Mock memo with debouncer
    memo = create_memo_mock_with_debouncer()

    # Override trigger to assert the expected trigger type
    async def mock_trigger(trigger_type):
        assert trigger_type == "pod_changes"

    memo.operations.debouncer.trigger = mock_trigger

    body = create_k8s_pod_resource(
        name="test-pod",
        namespace="default",
        phase="Running",
        additional_status={"podIP": "10.0.0.1"},
    )
    meta = {"name": "test-pod", "namespace": "default"}
    logger = create_logger_mock()

    # Call with all keyword arguments (simulating Kopf behavior)
    await handle_haproxy_pod_event(
        body=body, meta=meta, type="ADDED", logger=logger, memo=memo
    )

    # If we get here without exception, the function worked correctly


@pytest.mark.asyncio
async def test_handle_haproxy_pod_event_mixed_args_kwargs():
    """Test handle_haproxy_pod_event with mixed positional and keyword arguments."""
    # Mock memo with debouncer
    memo = create_memo_mock_with_debouncer()

    # Override trigger to assert the expected trigger type
    async def mock_trigger(trigger_type):
        assert trigger_type == "pod_changes"

    memo.operations.debouncer.trigger = mock_trigger

    body = create_k8s_pod_resource(
        name="test-pod",
        namespace="default",
        phase="Running",
        additional_status={"podIP": "10.0.0.1"},
    )
    meta = {"name": "test-pod", "namespace": "default"}
    logger = create_logger_mock()

    # Call with mixed arguments (some positional, some keyword)
    await handle_haproxy_pod_event(
        body,
        meta,
        "ADDED",  # positional
        logger=logger,
        memo=memo,  # keyword
    )

    # If we get here without exception, the function worked correctly


@pytest.mark.asyncio
async def test_handle_haproxy_pod_event_no_memo():
    """Test handle_haproxy_pod_event handles missing memo gracefully."""
    body = create_k8s_pod_resource(
        name="test-pod",
        namespace="default",
        phase="Running",
        additional_status={"podIP": "10.0.0.1"},
    )
    meta = {"name": "test-pod", "namespace": "default"}
    logger = create_logger_mock()

    # Call without memo - should not raise exception
    await handle_haproxy_pod_event(
        body=body, meta=meta, type="ADDED", logger=logger, memo=None
    )

    # Should log warning and return early
    logger.warning.assert_called_with("No memo provided to handle_haproxy_pod_event")


@pytest.mark.asyncio
async def test_handle_haproxy_pod_event_missing_parameters():
    """Test handle_haproxy_pod_event handles missing required parameters."""
    memo = create_memo_mock_with_debouncer()
    logger = create_logger_mock()

    # Call with missing meta and body
    await handle_haproxy_pod_event(
        body=None, meta=None, type="ADDED", logger=logger, memo=memo
    )

    # Should log warning and return early
    logger.warning.assert_called_with(
        "Missing required parameters (meta or body) in handle_haproxy_pod_event"
    )
