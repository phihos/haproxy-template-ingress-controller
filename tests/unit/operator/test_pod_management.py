"""
Test pod management functionality.

Tests for haproxy_pods_index function.
"""

import pytest
from unittest.mock import MagicMock

from haproxy_template_ic.operator.pod_management import haproxy_pods_index


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

        result = await haproxy_pods_index(namespace, name, body, logger)

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

        result = await haproxy_pods_index(namespace, name, body, logger)

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

        result = await haproxy_pods_index(namespace, name, body, logger)

        # Should return empty dict to exclude from index
        assert result == {}
