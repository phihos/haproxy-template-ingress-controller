"""
Test k8s resources functionality.

Tests for update_resource_index function.
"""

import pytest
import logging

from haproxy_template_ic.operator.k8s_resources import (
    update_resource_index,
    handle_resource_event,
)
from tests.unit.conftest import (
    create_k8s_service_resource,
    create_memo_with_watch_config,
    create_watch_config_mock,
    create_memo_mock_with_debouncer,
)


@pytest.mark.asyncio
async def test_update_resource_index_basic():
    """Test basic resource index update."""
    param = "pods"
    namespace = "default"
    name = "test-pod"
    body = {"name": "test-pod", "host": "10.0.1.5", "port": "80"}
    logger = logging.getLogger()

    result = await update_resource_index(
        param=param,
        namespace=namespace,
        name=name,
        body=body,
        logger=logger,
    )

    # Should fallback to default indexing
    assert result == {(namespace, name): body}


@pytest.mark.asyncio
async def test_update_resource_index_no_memo():
    """Test update_resource_index without memo object."""
    body = {"metadata": {"namespace": "test-ns", "name": "test-resource"}}

    result = await update_resource_index(
        param="test-resource",
        namespace="test-ns",
        name="test-resource",
        body=body,
        logger=logging.getLogger(),
    )

    # Should fallback to default indexing
    assert result == {("test-ns", "test-resource"): body}


@pytest.mark.asyncio
async def test_update_resource_index_custom_indexing():
    """Test update_resource_index with custom index_by configuration."""
    # Mock memo with watch config
    watch_config = create_watch_config_mock(
        ["metadata.namespace", "metadata.labels['app']"]
    )
    memo = create_memo_with_watch_config("services", watch_config)

    body = create_k8s_service_resource(
        name="web-service",
        namespace="prod",
        additional_metadata={"labels": {"app": "frontend"}},
    )

    result = await update_resource_index(
        param="services",
        namespace="prod",
        name="web-service",
        body=body,
        logger=logging.getLogger(),
        memo=memo,
    )

    # Should use custom indexing
    assert result == {("prod", "frontend"): body}


@pytest.mark.asyncio
async def test_handle_resource_event_with_memo():
    """Test handle_resource_event triggers debouncer when memo is provided."""
    # Mock memo with debouncer
    memo = create_memo_mock_with_debouncer()

    # Override trigger to assert the expected trigger type
    async def mock_trigger(trigger_type):
        assert trigger_type == "resource_changes"

    memo.operations.debouncer.trigger = mock_trigger

    # Call with memo in kwargs (simulating Kopf behavior)
    await handle_resource_event(
        memo=memo, namespace="test-ns", name="test-resource", body={"test": "data"}
    )

    # If we get here without exception, the function worked correctly


@pytest.mark.asyncio
async def test_handle_resource_event_no_memo():
    """Test handle_resource_event handles missing memo gracefully."""
    # Call without memo - should not raise exception
    await handle_resource_event(
        namespace="test-ns", name="test-resource", body={"test": "data"}
    )

    # If we get here without exception, the function worked correctly


@pytest.mark.asyncio
async def test_handle_resource_event_none_memo():
    """Test handle_resource_event handles None memo gracefully."""
    # Call with None memo - should not raise exception
    await handle_resource_event(
        memo=None, namespace="test-ns", name="test-resource", body={"test": "data"}
    )

    # If we get here without exception, the function worked correctly
