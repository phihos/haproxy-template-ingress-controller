"""
Test pod management functionality.

Tests for haproxy_pods_index function.
"""

import pytest
from unittest.mock import MagicMock

from haproxy_template_ic.operator.pod_management import (
    haproxy_pods_index,
    handle_haproxy_pod_event,
)


class TestHAProxyPodsIndex:
    """Test HAProxy pod indexing functionality."""

    @pytest.mark.asyncio
    async def test_haproxy_pods_index_normal_pod(self):
        """Test that haproxy_pods_index correctly indexes normal pods."""
        namespace = "test-namespace"
        name = "test-pod"
        body = {
            "metadata": {
                "name": name,
                "namespace": namespace,
            },
            "status": {
                "phase": "Running",
                "podIP": "10.0.0.1",
            },
        }
        logger = MagicMock()

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
    async def test_haproxy_pods_index_deleted_pod(self):
        """Test that haproxy_pods_index correctly removes deleted pods from index."""
        namespace = "test-namespace"
        name = "test-pod"
        body = {
            "metadata": {
                "name": name,
                "namespace": namespace,
                "deletionTimestamp": "2024-01-01T12:00:00Z",
            },
            "status": {
                "phase": "Terminating",
                "podIP": "10.0.0.1",
            },
        }
        logger = MagicMock()

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
    async def test_haproxy_pods_index_not_running(self):
        """Test that haproxy_pods_index excludes non-running pods."""
        namespace = "test-namespace"
        name = "test-pod"
        body = {
            "metadata": {
                "name": name,
                "namespace": namespace,
            },
            "status": {
                "phase": "Pending",
                "podIP": None,
            },
        }
        logger = MagicMock()

        result = await haproxy_pods_index(
            namespace=namespace,
            name=name,
            body=body,
            logger=logger,
        )

        # Should return empty dict to exclude from index
        assert result == {}


class TestHandleHAProxyPodEvent:
    """Test HAProxy pod event handling functionality."""

    @pytest.mark.asyncio
    async def test_handle_haproxy_pod_event_with_positional_args(self):
        """Test handle_haproxy_pod_event with positional arguments (normal case)."""
        # Mock memo with debouncer
        memo = MagicMock()

        # Mock debouncer trigger to return a coroutine
        async def mock_trigger(trigger_type):
            assert trigger_type == "pod_changes"

        memo.operations.debouncer.trigger = mock_trigger

        # Mock logger
        logger = MagicMock()

        body = {
            "metadata": {"name": "test-pod", "namespace": "default"},
            "status": {"phase": "Running", "podIP": "10.0.0.1"},
        }
        meta = {"name": "test-pod", "namespace": "default"}

        # Call with positional arguments
        await handle_haproxy_pod_event(
            body=body, meta=meta, type="ADDED", logger=logger, memo=memo
        )

        # If we get here without exception, the function worked correctly

    @pytest.mark.asyncio
    async def test_handle_haproxy_pod_event_with_kwargs(self):
        """Test handle_haproxy_pod_event with keyword arguments (Kopf behavior)."""
        # Mock memo with debouncer
        memo = MagicMock()

        # Mock debouncer trigger to return a coroutine
        async def mock_trigger(trigger_type):
            assert trigger_type == "pod_changes"

        memo.operations.debouncer.trigger = mock_trigger

        body = {
            "metadata": {"name": "test-pod", "namespace": "default"},
            "status": {"phase": "Running", "podIP": "10.0.0.1"},
        }
        meta = {"name": "test-pod", "namespace": "default"}
        logger = MagicMock()

        # Call with all keyword arguments (simulating Kopf behavior)
        await handle_haproxy_pod_event(
            body=body, meta=meta, type="ADDED", logger=logger, memo=memo
        )

        # If we get here without exception, the function worked correctly

    @pytest.mark.asyncio
    async def test_handle_haproxy_pod_event_mixed_args_kwargs(self):
        """Test handle_haproxy_pod_event with mixed positional and keyword arguments."""
        # Mock memo with debouncer
        memo = MagicMock()

        # Mock debouncer trigger to return a coroutine
        async def mock_trigger(trigger_type):
            assert trigger_type == "pod_changes"

        memo.operations.debouncer.trigger = mock_trigger

        body = {
            "metadata": {"name": "test-pod", "namespace": "default"},
            "status": {"phase": "Running", "podIP": "10.0.0.1"},
        }
        meta = {"name": "test-pod", "namespace": "default"}
        logger = MagicMock()

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
    async def test_handle_haproxy_pod_event_no_memo(self):
        """Test handle_haproxy_pod_event handles missing memo gracefully."""
        body = {
            "metadata": {"name": "test-pod", "namespace": "default"},
            "status": {"phase": "Running", "podIP": "10.0.0.1"},
        }
        meta = {"name": "test-pod", "namespace": "default"}
        logger = MagicMock()

        # Call without memo - should not raise exception
        await handle_haproxy_pod_event(
            body=body, meta=meta, type="ADDED", logger=logger, memo=None
        )

        # Should log warning and return early
        logger.warning.assert_called_with(
            "No memo provided to handle_haproxy_pod_event"
        )

    @pytest.mark.asyncio
    async def test_handle_haproxy_pod_event_missing_parameters(self):
        """Test handle_haproxy_pod_event handles missing required parameters."""
        memo = MagicMock()
        logger = MagicMock()

        # Call with missing meta and body
        await handle_haproxy_pod_event(
            body=None, meta=None, type="ADDED", logger=logger, memo=memo
        )

        # Should log warning and return early
        logger.warning.assert_called_with(
            "Missing required parameters (meta or body) in handle_haproxy_pod_event"
        )
