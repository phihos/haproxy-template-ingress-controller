"""
Unit tests for DataplaneClientPool and PooledClient classes.

Tests connection pooling, reference counting, TTL-based cleanup,
and client lifecycle management.
"""

import time
import pytest
from unittest.mock import Mock

from haproxy_template_ic.dataplane.client_pool import (
    DataplaneClientPool,
    PooledClient,
)
from haproxy_dataplane_v3 import AuthenticatedClient
from tests.unit.conftest import (
    create_dataplane_endpoint_mock,
)


class TestPooledClient:
    """Test PooledClient wrapper functionality."""

    def test_pooled_client_creation(self):
        """Test basic PooledClient creation."""
        mock_client = Mock(spec=AuthenticatedClient)
        pooled_client = PooledClient(client=mock_client)

        assert pooled_client.client == mock_client
        assert pooled_client.reference_count == 0
        assert pooled_client.last_used > 0
        assert pooled_client.created_at > 0

    def test_pooled_client_add_reference(self):
        """Test reference counting increment."""
        mock_client = Mock(spec=AuthenticatedClient)
        pooled_client = PooledClient(client=mock_client)

        initial_time = pooled_client.last_used
        time.sleep(0.001)  # Small delay to ensure time difference

        pooled_client.add_reference()

        assert pooled_client.reference_count == 1
        assert pooled_client.last_used > initial_time

    def test_pooled_client_remove_reference(self):
        """Test reference counting decrement."""
        mock_client = Mock(spec=AuthenticatedClient)
        pooled_client = PooledClient(client=mock_client)

        # Add some references first
        pooled_client.add_reference()
        pooled_client.add_reference()
        assert pooled_client.reference_count == 2

        # Remove one reference
        pooled_client.remove_reference()
        assert pooled_client.reference_count == 1

        # Remove another reference
        pooled_client.remove_reference()
        assert pooled_client.reference_count == 0

    def test_pooled_client_is_idle(self):
        """Test idle detection."""
        mock_client = Mock(spec=AuthenticatedClient)
        pooled_client = PooledClient(client=mock_client)

        # Client should not be idle immediately after creation
        assert not pooled_client.is_idle(idle_timeout=10.0)

        # Set last_used to a past time
        pooled_client.last_used = time.time() - 20.0

        # Client should be idle with 10-second timeout
        assert pooled_client.is_idle(idle_timeout=10.0)

    def test_pooled_client_is_expired(self):
        """Test TTL expiration detection."""
        mock_client = Mock(spec=AuthenticatedClient)
        pooled_client = PooledClient(client=mock_client)

        # Set created_at to a past time
        pooled_client.created_at = time.time() - 120.0

        # Client should be expired with 60-second TTL
        assert pooled_client.is_expired(max_age=60.0)

        # Client should not be expired with 200-second TTL
        assert not pooled_client.is_expired(max_age=200.0)


class TestDataplaneClientPool:
    """Test DataplaneClientPool functionality."""

    def test_client_pool_creation(self):
        """Test basic client pool creation."""
        pool = DataplaneClientPool(
            idle_timeout=300.0,
            max_age=3600.0,
            cleanup_interval=60.0,
        )

        assert pool._idle_timeout == 300.0
        assert pool._max_age == 3600.0
        assert pool._cleanup_interval == 60.0
        assert len(pool._clients) == 0

    @pytest.mark.asyncio
    async def test_get_client(self):
        """Test getting client."""
        endpoint = create_dataplane_endpoint_mock()
        pool = DataplaneClientPool()

        client = await pool.get_client(endpoint, timeout=10.0)

        assert isinstance(client, AuthenticatedClient)
        # AuthenticatedClient stores URL as base_url property
        assert hasattr(client, "_base_url") or hasattr(client, "base_url")

    @pytest.mark.asyncio
    async def test_get_client_reuse(self):
        """Test client reuse for same endpoint."""
        endpoint = create_dataplane_endpoint_mock()
        pool = DataplaneClientPool()

        client1 = await pool.get_client(endpoint, timeout=10.0)
        client2 = await pool.get_client(endpoint, timeout=10.0)

        # Should reuse the same client
        assert client1 is client2

    @pytest.mark.asyncio
    async def test_release_client(self):
        """Test releasing client reference."""
        endpoint = create_dataplane_endpoint_mock()
        pool = DataplaneClientPool()

        client = await pool.get_client(endpoint, timeout=10.0)
        await pool.release_client(endpoint, timeout=10.0)

        # Should not raise error
        assert client is not None

    @pytest.mark.asyncio
    async def test_close_all(self):
        """Test closing all clients."""
        endpoint = create_dataplane_endpoint_mock()
        pool = DataplaneClientPool()

        await pool.get_client(endpoint, timeout=10.0)
        await pool.close_all()

        assert pool._is_closed is True

    @pytest.mark.asyncio
    async def test_get_client_after_close(self):
        """Test getting client after pool is closed."""
        endpoint = create_dataplane_endpoint_mock()
        pool = DataplaneClientPool()

        # Initialize the pool first by getting a client
        await pool.get_client(endpoint, timeout=10.0)
        await pool.close_all()

        with pytest.raises(ValueError, match="Client pool is closed"):
            await pool.get_client(endpoint, timeout=10.0)

    def test_get_pool_stats(self):
        """Test pool statistics."""
        pool = DataplaneClientPool()
        stats = pool.get_pool_stats()

        assert isinstance(stats, dict)
        # Check for correct structure based on implementation
        assert "statistics" in stats
        assert "clients_created" in stats["statistics"]
        assert "clients_reused" in stats["statistics"]
        assert "cleanup_runs" in stats["statistics"]
        assert "pool_config" in stats
        assert "active_connections" in stats
