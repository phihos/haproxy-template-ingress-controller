"""
Unit tests for RuntimeAPI class.

Tests runtime operations including map operations, ACL runtime operations,
and server state changes that don't require HAProxy reloads.
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch

from haproxy_template_ic.dataplane.runtime_api import RuntimeAPI
from haproxy_template_ic.dataplane.types import (
    DataplaneAPIError,
    MapChange,
)
from tests.unit.conftest import (
    create_dataplane_endpoint_mock,
)


class TestRuntimeAPIInitialization:
    """Test RuntimeAPI initialization and basic setup."""

    def test_runtime_api_init(self):
        """Test RuntimeAPI initialization."""
        mock_get_client = Mock()
        endpoint = create_dataplane_endpoint_mock()

        runtime_api = RuntimeAPI(mock_get_client, endpoint)

        assert runtime_api._get_client == mock_get_client
        assert runtime_api.endpoint == endpoint


class TestRuntimeAPIMapOperations:
    """Test runtime map operations."""

    @pytest.mark.asyncio
    async def test_apply_runtime_map_operations_add(self):
        """Test applying map add operations."""
        mock_get_client = Mock()
        mock_client = Mock()
        mock_get_client.return_value = mock_client
        endpoint = create_dataplane_endpoint_mock()

        runtime_api = RuntimeAPI(mock_get_client, endpoint)

        operations = [MapChange(operation="add", key="test.com", value="backend1")]

        with patch(
            "haproxy_template_ic.dataplane.runtime_api.add_map_entry"
        ) as mock_add:
            mock_add.asyncio = AsyncMock(return_value=None)

            await runtime_api.apply_runtime_map_operations("test.map", operations)

            # Verify API call was made
            mock_add.asyncio.assert_called_once()

    @pytest.mark.asyncio
    async def test_apply_runtime_map_operations_set(self):
        """Test applying map set operations."""
        mock_get_client = Mock()
        mock_client = Mock()
        mock_get_client.return_value = mock_client
        endpoint = create_dataplane_endpoint_mock()

        runtime_api = RuntimeAPI(mock_get_client, endpoint)

        operations = [MapChange(operation="set", key="test.com", value="backend2")]

        with patch(
            "haproxy_template_ic.dataplane.runtime_api.replace_runtime_map_entry"
        ) as mock_replace:
            mock_replace.asyncio = AsyncMock(return_value=None)

            await runtime_api.apply_runtime_map_operations("test.map", operations)

            # Verify API call was made
            mock_replace.asyncio.assert_called_once()

    @pytest.mark.asyncio
    async def test_apply_runtime_map_operations_del(self):
        """Test applying map delete operations."""
        mock_get_client = Mock()
        mock_client = Mock()
        mock_get_client.return_value = mock_client
        endpoint = create_dataplane_endpoint_mock()

        runtime_api = RuntimeAPI(mock_get_client, endpoint)

        operations = [MapChange(operation="del", key="test.com", value="")]

        with patch(
            "haproxy_template_ic.dataplane.runtime_api.delete_runtime_map_entry"
        ) as mock_delete:
            mock_delete.asyncio = AsyncMock(return_value=None)

            await runtime_api.apply_runtime_map_operations("test.map", operations)

            # Verify API call was made
            mock_delete.asyncio.assert_called_once()

    @pytest.mark.asyncio
    async def test_apply_runtime_map_operations_empty(self):
        """Test applying empty map operations."""
        mock_get_client = Mock()
        endpoint = create_dataplane_endpoint_mock()

        runtime_api = RuntimeAPI(mock_get_client, endpoint)

        # Should not raise error for empty operations
        await runtime_api.apply_runtime_map_operations("test.map", [])


class TestRuntimeAPIACLOperations:
    """Test runtime ACL operations."""

    @pytest.mark.asyncio
    async def test_apply_runtime_acl_operations_add(self):
        """Test applying ACL add operations."""
        mock_get_client = Mock()
        mock_client = Mock()
        mock_get_client.return_value = mock_client
        endpoint = create_dataplane_endpoint_mock()

        runtime_api = RuntimeAPI(mock_get_client, endpoint)

        operations = [MapChange(operation="add", key="", value="192.168.1.1")]

        with patch(
            "haproxy_template_ic.dataplane.runtime_api.post_services_haproxy_runtime_acls_parent_name_entries"
        ) as mock_post:
            mock_post.asyncio = AsyncMock(return_value=None)

            await runtime_api.apply_runtime_acl_operations("blocked_ips", operations)

            # Verify API call was made
            mock_post.asyncio.assert_called_once()

    @pytest.mark.asyncio
    async def test_apply_runtime_acl_operations_del(self):
        """Test applying ACL delete operations."""
        mock_get_client = Mock()
        mock_client = Mock()
        mock_get_client.return_value = mock_client
        endpoint = create_dataplane_endpoint_mock()

        runtime_api = RuntimeAPI(mock_get_client, endpoint)

        operations = [MapChange(operation="del", key="entry_id", value="")]

        with patch(
            "haproxy_template_ic.dataplane.runtime_api.delete_services_haproxy_runtime_acls_parent_name_entries_id"
        ) as mock_delete:
            mock_delete.asyncio = AsyncMock(return_value=None)

            await runtime_api.apply_runtime_acl_operations("blocked_ips", operations)

            # Verify API call was made
            mock_delete.asyncio.assert_called_once()


class TestRuntimeAPIServerOperations:
    """Test runtime server operations."""

    @pytest.mark.asyncio
    async def test_update_server_state(self):
        """Test updating server state."""
        mock_get_client = Mock()
        mock_client = Mock()
        mock_get_client.return_value = mock_client
        endpoint = create_dataplane_endpoint_mock()

        runtime_api = RuntimeAPI(mock_get_client, endpoint)

        with patch(
            "haproxy_template_ic.dataplane.runtime_api.replace_runtime_server"
        ) as mock_replace:
            mock_replace.asyncio = AsyncMock(return_value=None)

            await runtime_api.update_server_state("backend1", "server1", "drain")

            # Verify API call was made
            mock_replace.asyncio.assert_called_once()


class TestRuntimeAPIBulkOperations:
    """Test bulk runtime operations."""

    @pytest.mark.asyncio
    async def test_bulk_map_updates(self):
        """Test bulk map updates."""
        mock_get_client = Mock()
        mock_client = Mock()
        mock_get_client.return_value = mock_client
        endpoint = create_dataplane_endpoint_mock()

        runtime_api = RuntimeAPI(mock_get_client, endpoint)

        map_updates = {
            "hosts.map": [
                MapChange(operation="add", key="api.test.com", value="api_backend")
            ],
            "paths.map": [
                MapChange(operation="set", key="/api", value="api_backend_v2")
            ],
        }

        with (
            patch(
                "haproxy_template_ic.dataplane.runtime_api.add_map_entry"
            ) as mock_add,
            patch(
                "haproxy_template_ic.dataplane.runtime_api.replace_runtime_map_entry"
            ) as mock_replace,
        ):
            mock_add.asyncio = AsyncMock(return_value=None)
            mock_replace.asyncio = AsyncMock(return_value=None)

            await runtime_api.bulk_map_updates(map_updates)

    @pytest.mark.asyncio
    async def test_bulk_acl_updates(self):
        """Test bulk ACL updates."""
        mock_get_client = Mock()
        mock_client = Mock()
        mock_get_client.return_value = mock_client
        endpoint = create_dataplane_endpoint_mock()

        runtime_api = RuntimeAPI(mock_get_client, endpoint)

        acl_updates = {
            "blocked_ips": [MapChange(operation="add", key="", value="192.168.1.100")]
        }

        with patch(
            "haproxy_template_ic.dataplane.runtime_api.post_services_haproxy_runtime_acls_parent_name_entries"
        ) as mock_post:
            mock_post.asyncio = AsyncMock(return_value=None)

            await runtime_api.bulk_acl_updates(acl_updates)


class TestRuntimeAPIErrorHandling:
    """Test error handling and edge cases."""

    @pytest.mark.asyncio
    async def test_map_operations_with_api_error(self):
        """Test map operations with API errors."""
        mock_get_client = Mock()
        mock_client = Mock()
        mock_get_client.return_value = mock_client
        endpoint = create_dataplane_endpoint_mock()

        runtime_api = RuntimeAPI(mock_get_client, endpoint)

        operations = [MapChange(operation="add", key="test.com", value="backend1")]

        with patch(
            "haproxy_template_ic.dataplane.runtime_api.add_map_entry"
        ) as mock_add:
            mock_add.asyncio = AsyncMock(side_effect=Exception("API Error"))

            with pytest.raises(DataplaneAPIError):
                await runtime_api.apply_runtime_map_operations("test.map", operations)

    @pytest.mark.asyncio
    async def test_unknown_map_operation(self):
        """Test handling unknown map operation."""
        mock_get_client = Mock()
        mock_client = Mock()
        mock_get_client.return_value = mock_client
        endpoint = create_dataplane_endpoint_mock()

        runtime_api = RuntimeAPI(mock_get_client, endpoint)

        operations = [MapChange(operation="unknown", key="test.com", value="backend1")]

        # Should not raise error for unknown operations (just logs warning)
        await runtime_api.apply_runtime_map_operations("test.map", operations)
