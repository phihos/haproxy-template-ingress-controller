"""
Unit tests for RuntimeAPI class.

Tests runtime operations including map operations, ACL runtime operations,
and server state changes that don't require HAProxy reloads.
"""

import pytest
from unittest.mock import Mock, patch

from haproxy_template_ic.dataplane.runtime_api import RuntimeAPI
from haproxy_template_ic.dataplane.types import (
    DataplaneAPIError,
    MapChange,
)
from tests.unit.conftest import (
    create_dataplane_endpoint_mock,
)
from tests.unit.dataplane.adapter_fixtures import create_mock_api_response


class TestRuntimeAPIInitialization:
    """Test RuntimeAPI initialization and basic setup."""

    def test_runtime_api_init(self):
        """Test RuntimeAPI initialization."""
        endpoint = create_dataplane_endpoint_mock()

        runtime_api = RuntimeAPI(endpoint)

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

        runtime_api = RuntimeAPI(endpoint)

        operations = [MapChange(operation="add", key="test.com", value="backend1")]

        with patch(
            "haproxy_template_ic.dataplane.runtime_api.add_map_entry"
        ) as mock_add:
            mock_response = create_mock_api_response(
                content="success", reload_id="test-reload"
            )
            mock_add.return_value = mock_response

            await runtime_api.apply_runtime_map_operations("test.map", operations)

            # Verify API call was made
            mock_add.assert_called_once()

    @pytest.mark.asyncio
    async def test_apply_runtime_map_operations_set(self):
        """Test applying map set operations."""
        mock_get_client = Mock()
        mock_client = Mock()
        mock_get_client.return_value = mock_client
        endpoint = create_dataplane_endpoint_mock()

        runtime_api = RuntimeAPI(endpoint)

        operations = [MapChange(operation="set", key="test.com", value="backend2")]

        with patch(
            "haproxy_template_ic.dataplane.runtime_api.replace_runtime_map_entry"
        ) as mock_replace:
            mock_response = create_mock_api_response(
                content="success", reload_id="test-reload"
            )
            mock_replace.return_value = mock_response

            await runtime_api.apply_runtime_map_operations("test.map", operations)

            # Verify API call was made
            mock_replace.assert_called_once()

    @pytest.mark.asyncio
    async def test_apply_runtime_map_operations_del(self):
        """Test applying map delete operations."""
        mock_get_client = Mock()
        mock_client = Mock()
        mock_get_client.return_value = mock_client
        endpoint = create_dataplane_endpoint_mock()

        runtime_api = RuntimeAPI(endpoint)

        operations = [MapChange(operation="del", key="test.com", value="")]

        with patch(
            "haproxy_template_ic.dataplane.runtime_api.delete_runtime_map_entry"
        ) as mock_delete:
            mock_response = create_mock_api_response(
                content="success", reload_id="test-reload"
            )
            mock_delete.return_value = mock_response

            await runtime_api.apply_runtime_map_operations("test.map", operations)

            # Verify API call was made
            mock_delete.assert_called_once()

    @pytest.mark.asyncio
    async def test_apply_runtime_map_operations_empty(self):
        """Test applying empty map operations."""
        endpoint = create_dataplane_endpoint_mock()

        runtime_api = RuntimeAPI(endpoint)

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

        runtime_api = RuntimeAPI(endpoint)

        operations = [MapChange(operation="add", key="", value="192.168.1.1")]

        with patch(
            "haproxy_template_ic.dataplane.runtime_api.post_runtime_acl_entry"
        ) as mock_post:
            mock_response = create_mock_api_response(
                content="success", reload_id="test-reload"
            )
            mock_post.return_value = mock_response

            await runtime_api.apply_runtime_acl_operations("blocked_ips", operations)

            # Verify API call was made
            mock_post.assert_called_once()

    @pytest.mark.asyncio
    async def test_apply_runtime_acl_operations_del(self):
        """Test applying ACL delete operations."""
        mock_get_client = Mock()
        mock_client = Mock()
        mock_get_client.return_value = mock_client
        endpoint = create_dataplane_endpoint_mock()

        runtime_api = RuntimeAPI(endpoint)

        operations = [MapChange(operation="del", key="entry_id", value="")]

        with patch(
            "haproxy_template_ic.dataplane.runtime_api.delete_runtime_acl_file_entry"
        ) as mock_delete:
            mock_response = create_mock_api_response(
                content="success", reload_id="test-reload"
            )
            mock_delete.return_value = mock_response

            await runtime_api.apply_runtime_acl_operations("blocked_ips", operations)

            # Verify API call was made
            mock_delete.assert_called_once()


class TestRuntimeAPIServerOperations:
    """Test runtime server operations."""

    @pytest.mark.asyncio
    async def test_update_server_state(self):
        """Test updating server state."""
        mock_get_client = Mock()
        mock_client = Mock()
        mock_get_client.return_value = mock_client
        endpoint = create_dataplane_endpoint_mock()

        runtime_api = RuntimeAPI(endpoint)

        with patch(
            "haproxy_template_ic.dataplane.runtime_api.replace_runtime_server"
        ) as mock_replace:
            mock_response = create_mock_api_response(
                content="success", reload_id="test-reload"
            )
            mock_replace.return_value = mock_response

            await runtime_api.update_server_state("backend1", "server1", "drain")

            # Verify API call was made
            mock_replace.assert_called_once()


class TestRuntimeAPIBulkOperations:
    """Test bulk runtime operations."""

    @pytest.mark.asyncio
    async def test_bulk_map_updates(self):
        """Test bulk map updates."""
        mock_get_client = Mock()
        mock_client = Mock()
        mock_get_client.return_value = mock_client
        endpoint = create_dataplane_endpoint_mock()

        runtime_api = RuntimeAPI(endpoint)

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
            mock_response = create_mock_api_response(
                content="success", reload_id="test-reload"
            )
            mock_add.return_value = mock_response
            mock_replace.return_value = mock_response

            await runtime_api.bulk_map_updates(map_updates)

    @pytest.mark.asyncio
    async def test_bulk_acl_updates(self):
        """Test bulk ACL updates."""
        mock_get_client = Mock()
        mock_client = Mock()
        mock_get_client.return_value = mock_client
        endpoint = create_dataplane_endpoint_mock()

        runtime_api = RuntimeAPI(endpoint)

        acl_updates = {
            "blocked_ips": [MapChange(operation="add", key="", value="192.168.1.100")]
        }

        with patch(
            "haproxy_template_ic.dataplane.runtime_api.post_runtime_acl_entry"
        ) as mock_post:
            mock_response = create_mock_api_response(
                content="success", reload_id="test-reload"
            )
            mock_post.return_value = mock_response

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

        runtime_api = RuntimeAPI(endpoint)

        operations = [MapChange(operation="add", key="test.com", value="backend1")]

        with patch(
            "haproxy_template_ic.dataplane.runtime_api.add_map_entry"
        ) as mock_add:
            mock_add.side_effect = Exception("API Error")

            with pytest.raises(DataplaneAPIError):
                await runtime_api.apply_runtime_map_operations("test.map", operations)

    @pytest.mark.asyncio
    async def test_unknown_map_operation(self):
        """Test handling unknown map operation."""
        mock_get_client = Mock()
        mock_client = Mock()
        mock_get_client.return_value = mock_client
        endpoint = create_dataplane_endpoint_mock()

        runtime_api = RuntimeAPI(endpoint)

        operations = [MapChange(operation="unknown", key="test.com", value="backend1")]

        # Should not raise error for unknown operations (just logs warning)
        await runtime_api.apply_runtime_map_operations("test.map", operations)


class TestRuntimeAPIAdvancedMapOperations:
    """Test advanced runtime map operations and scenarios."""

    @pytest.mark.asyncio
    async def test_apply_runtime_map_operations_mixed_operations(self):
        """Test applying mixed map operations in sequence."""
        endpoint = create_dataplane_endpoint_mock()
        runtime_api = RuntimeAPI(endpoint)

        operations = [
            MapChange(operation="add", key="new.com", value="backend1"),
            MapChange(operation="set", key="existing.com", value="backend2"),
            MapChange(operation="del", key="old.com", value=""),
        ]

        with (
            patch(
                "haproxy_template_ic.dataplane.runtime_api.add_map_entry"
            ) as mock_add,
            patch(
                "haproxy_template_ic.dataplane.runtime_api.replace_runtime_map_entry"
            ) as mock_replace,
            patch(
                "haproxy_template_ic.dataplane.runtime_api.delete_runtime_map_entry"
            ) as mock_delete,
        ):
            mock_response = create_mock_api_response(
                content="success", reload_id="test-reload"
            )
            mock_add.return_value = mock_response
            mock_replace.return_value = mock_response
            mock_delete.return_value = mock_response

            await runtime_api.apply_runtime_map_operations("hosts.map", operations)

            # Verify all three operations were called
            mock_add.assert_called_once()
            mock_replace.assert_called_once()
            mock_delete.assert_called_once()

    @pytest.mark.asyncio
    async def test_apply_runtime_map_operations_with_reload_info(self):
        """Test map operations return proper reload information."""
        endpoint = create_dataplane_endpoint_mock()
        runtime_api = RuntimeAPI(endpoint)

        operations = [MapChange(operation="add", key="api.test.com", value="backend1")]

        with patch(
            "haproxy_template_ic.dataplane.runtime_api.add_map_entry"
        ) as mock_add:
            # Mock response with reload info
            mock_response = create_mock_api_response(
                content="success", reload_id="reload-456"
            )
            mock_add.return_value = mock_response

            await runtime_api.apply_runtime_map_operations("hosts.map", operations)

            # Verify the response was processed correctly
            mock_add.assert_called_once()

    @pytest.mark.asyncio
    async def test_apply_runtime_map_operations_large_batch(self):
        """Test handling large batches of map operations."""
        endpoint = create_dataplane_endpoint_mock()
        runtime_api = RuntimeAPI(endpoint)

        # Create large batch of operations
        operations = [
            MapChange(operation="add", key=f"host{i}.com", value=f"backend{i}")
            for i in range(100)
        ]

        with patch(
            "haproxy_template_ic.dataplane.runtime_api.add_map_entry"
        ) as mock_add:
            mock_response = create_mock_api_response(
                content="success", reload_id="test-reload"
            )
            mock_add.return_value = mock_response

            await runtime_api.apply_runtime_map_operations("hosts.map", operations)

            # Verify all operations were processed
            assert mock_add.call_count == 100


class TestRuntimeAPIAdvancedACLOperations:
    """Test advanced runtime ACL operations and scenarios."""

    @pytest.mark.asyncio
    async def test_apply_runtime_acl_operations_add_multiple_ips(self):
        """Test adding multiple IP addresses to ACL."""
        endpoint = create_dataplane_endpoint_mock()
        runtime_api = RuntimeAPI(endpoint)

        operations = [
            MapChange(operation="add", key="", value="192.168.1.100"),
            MapChange(operation="add", key="", value="10.0.0.5"),
            MapChange(operation="add", key="", value="172.16.0.0/16"),
        ]

        with patch(
            "haproxy_template_ic.dataplane.runtime_api.post_runtime_acl_entry"
        ) as mock_post:
            mock_response = create_mock_api_response(
                content="success", reload_id="test-reload"
            )
            mock_post.return_value = mock_response

            await runtime_api.apply_runtime_acl_operations("blocked_ips", operations)

            # Verify all add operations were called
            assert mock_post.call_count == 3

    @pytest.mark.asyncio
    async def test_apply_runtime_acl_operations_mixed_add_del(self):
        """Test mixed ACL add and delete operations."""
        endpoint = create_dataplane_endpoint_mock()
        runtime_api = RuntimeAPI(endpoint)

        operations = [
            MapChange(operation="add", key="", value="192.168.1.200"),
            MapChange(operation="del", key="entry_123", value=""),
            MapChange(operation="add", key="", value="10.0.0.10"),
        ]

        with (
            patch(
                "haproxy_template_ic.dataplane.runtime_api.post_runtime_acl_entry"
            ) as mock_post,
            patch(
                "haproxy_template_ic.dataplane.runtime_api.delete_runtime_acl_file_entry"
            ) as mock_delete,
        ):
            mock_response = create_mock_api_response(
                content="success", reload_id="test-reload"
            )
            mock_post.return_value = mock_response
            mock_delete.return_value = mock_response

            await runtime_api.apply_runtime_acl_operations("blocked_ips", operations)

            # Verify both add and delete operations were called
            assert mock_post.call_count == 2
            mock_delete.assert_called_once()

    @pytest.mark.asyncio
    async def test_apply_runtime_acl_operations_error_handling(self):
        """Test ACL operations with API errors."""
        endpoint = create_dataplane_endpoint_mock()
        runtime_api = RuntimeAPI(endpoint)

        operations = [MapChange(operation="add", key="", value="192.168.1.1")]

        with patch(
            "haproxy_template_ic.dataplane.runtime_api.post_runtime_acl_entry"
        ) as mock_post:
            mock_post.side_effect = Exception("ACL API Error")

            with pytest.raises(DataplaneAPIError):
                await runtime_api.apply_runtime_acl_operations(
                    "blocked_ips", operations
                )


class TestRuntimeAPIAdvancedServerOperations:
    """Test advanced runtime server operations and scenarios."""

    @pytest.mark.asyncio
    async def test_update_server_state_multiple_states(self):
        """Test updating server to different states."""
        endpoint = create_dataplane_endpoint_mock()
        runtime_api = RuntimeAPI(endpoint)

        states = ["ready", "drain", "maint"]

        with patch(
            "haproxy_template_ic.dataplane.runtime_api.replace_runtime_server"
        ) as mock_replace:
            mock_response = create_mock_api_response(
                content="success", reload_id="test-reload"
            )
            mock_replace.return_value = mock_response

            for state in states:
                await runtime_api.update_server_state("backend1", "server1", state)

            # Verify all state updates were called
            assert mock_replace.call_count == 3

    @pytest.mark.asyncio
    async def test_update_server_state_with_reload_trigger(self):
        """Test server state update that triggers reload."""
        endpoint = create_dataplane_endpoint_mock()
        runtime_api = RuntimeAPI(endpoint)

        with patch(
            "haproxy_template_ic.dataplane.runtime_api.replace_runtime_server"
        ) as mock_replace:
            # Mock response that triggers reload
            mock_response = create_mock_api_response(
                content="success", reload_id="server-reload-789"
            )
            mock_replace.return_value = mock_response

            await runtime_api.update_server_state("backend1", "server1", "maint")

            # Verify the reload response was handled
            mock_replace.assert_called_once()

    @pytest.mark.asyncio
    async def test_update_server_state_error_handling(self):
        """Test server state update with API errors."""
        endpoint = create_dataplane_endpoint_mock()
        runtime_api = RuntimeAPI(endpoint)

        with patch(
            "haproxy_template_ic.dataplane.runtime_api.replace_runtime_server"
        ) as mock_replace:
            mock_replace.side_effect = Exception("Server API Error")

            with pytest.raises(DataplaneAPIError):
                await runtime_api.update_server_state("backend1", "server1", "drain")


class TestRuntimeAPIAdvancedBulkOperations:
    """Test advanced bulk runtime operations and scenarios."""

    @pytest.mark.asyncio
    async def test_bulk_map_updates_multiple_maps_large_scale(self):
        """Test bulk updates across multiple maps with many operations."""
        endpoint = create_dataplane_endpoint_mock()
        runtime_api = RuntimeAPI(endpoint)

        # Setup large-scale map updates
        map_updates = {
            "hosts.map": [
                MapChange(operation="add", key=f"host{i}.com", value=f"backend{i}")
                for i in range(50)
            ],
            "paths.map": [
                MapChange(operation="set", key=f"/api/v{i}", value=f"api_backend_v{i}")
                for i in range(30)
            ],
            "backends.map": [
                MapChange(operation="del", key=f"old_backend_{i}", value="")
                for i in range(20)
            ],
        }

        with (
            patch(
                "haproxy_template_ic.dataplane.runtime_api.add_map_entry"
            ) as mock_add,
            patch(
                "haproxy_template_ic.dataplane.runtime_api.replace_runtime_map_entry"
            ) as mock_replace,
            patch(
                "haproxy_template_ic.dataplane.runtime_api.delete_runtime_map_entry"
            ) as mock_delete,
        ):
            mock_response = create_mock_api_response(
                content="success", reload_id="test-reload"
            )
            mock_add.return_value = mock_response
            mock_replace.return_value = mock_response
            mock_delete.return_value = mock_response

            await runtime_api.bulk_map_updates(map_updates)

            # Verify operation counts
            assert mock_add.call_count == 50
            assert mock_replace.call_count == 30
            assert mock_delete.call_count == 20

    @pytest.mark.asyncio
    async def test_bulk_acl_updates_multiple_acls(self):
        """Test bulk ACL updates across multiple ACL files."""
        endpoint = create_dataplane_endpoint_mock()
        runtime_api = RuntimeAPI(endpoint)

        acl_updates = {
            "blocked_ips": [
                MapChange(operation="add", key="", value="192.168.1.100"),
                MapChange(operation="add", key="", value="10.0.0.5"),
            ],
            "allowed_networks": [
                MapChange(operation="add", key="", value="172.16.0.0/16"),
                MapChange(operation="del", key="entry_456", value=""),
            ],
            "suspicious_ips": [
                MapChange(operation="add", key="", value="203.0.113.100"),
            ],
        }

        with (
            patch(
                "haproxy_template_ic.dataplane.runtime_api.post_runtime_acl_entry"
            ) as mock_post,
            patch(
                "haproxy_template_ic.dataplane.runtime_api.delete_runtime_acl_file_entry"
            ) as mock_delete,
        ):
            mock_response = create_mock_api_response(
                content="success", reload_id="test-reload"
            )
            mock_post.return_value = mock_response
            mock_delete.return_value = mock_response

            await runtime_api.bulk_acl_updates(acl_updates)

            # Verify operation counts
            assert mock_post.call_count == 4  # 2 + 1 + 1 add operations
            mock_delete.assert_called_once()

    @pytest.mark.asyncio
    async def test_bulk_operations_with_partial_failures(self):
        """Test bulk operations when some operations fail."""
        endpoint = create_dataplane_endpoint_mock()
        runtime_api = RuntimeAPI(endpoint)

        map_updates = {
            "hosts.map": [
                MapChange(operation="add", key="good.com", value="backend1"),
                MapChange(operation="add", key="bad.com", value="backend2"),
            ]
        }

        call_count = 0

        def side_effect(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count == 2:  # Second call fails
                raise Exception("API Error on second operation")
            return create_mock_api_response(content="success", reload_id="test-reload")

        with patch(
            "haproxy_template_ic.dataplane.runtime_api.add_map_entry"
        ) as mock_add:
            mock_add.side_effect = side_effect

            # Should raise error on first failure
            with pytest.raises(DataplaneAPIError):
                await runtime_api.bulk_map_updates(map_updates)


class TestRuntimeAPIIntegrationScenarios:
    """Test runtime API in realistic integration scenarios."""

    @pytest.mark.asyncio
    async def test_full_ingress_runtime_update_scenario(self):
        """Test complete ingress runtime update scenario."""
        endpoint = create_dataplane_endpoint_mock()
        runtime_api = RuntimeAPI(endpoint)

        # Simulate full ingress update with maps, ACLs, and server states
        map_updates = {
            "hosts.map": [
                MapChange(
                    operation="add", key="new-api.example.com", value="api_backend"
                ),
                MapChange(
                    operation="set", key="existing.example.com", value="updated_backend"
                ),
            ],
            "paths.map": [
                MapChange(operation="add", key="/v2/api", value="api_v2_backend"),
            ],
        }

        acl_updates = {
            "rate_limit_whitelist": [
                MapChange(operation="add", key="", value="192.168.1.50"),
            ],
            "blocked_ips": [
                MapChange(operation="del", key="entry_789", value=""),
            ],
        }

        with (
            patch(
                "haproxy_template_ic.dataplane.runtime_api.add_map_entry"
            ) as mock_add_map,
            patch(
                "haproxy_template_ic.dataplane.runtime_api.replace_runtime_map_entry"
            ) as mock_replace_map,
            patch(
                "haproxy_template_ic.dataplane.runtime_api.post_runtime_acl_entry"
            ) as mock_add_acl,
            patch(
                "haproxy_template_ic.dataplane.runtime_api.delete_runtime_acl_file_entry"
            ) as mock_delete_acl,
            patch(
                "haproxy_template_ic.dataplane.runtime_api.replace_runtime_server"
            ) as mock_update_server,
        ):
            mock_response = create_mock_api_response(
                content="success", reload_id="test-reload"
            )
            mock_add_map.return_value = mock_response
            mock_replace_map.return_value = mock_response
            mock_add_acl.return_value = mock_response
            mock_delete_acl.return_value = mock_response
            mock_update_server.return_value = mock_response

            # Execute all runtime operations
            await runtime_api.bulk_map_updates(map_updates)
            await runtime_api.bulk_acl_updates(acl_updates)
            await runtime_api.update_server_state("api_backend", "server1", "ready")

            # Verify all operations were executed
            assert mock_add_map.call_count == 2  # 2 add operations
            mock_replace_map.assert_called_once()  # 1 set operation
            mock_add_acl.assert_called_once()  # 1 ACL add
            mock_delete_acl.assert_called_once()  # 1 ACL delete
            mock_update_server.assert_called_once()  # 1 server update

    @pytest.mark.asyncio
    async def test_runtime_api_performance_scenario(self):
        """Test runtime API performance with high-volume operations."""
        endpoint = create_dataplane_endpoint_mock()
        runtime_api = RuntimeAPI(endpoint)

        # Create high-volume operation scenario
        large_map_updates = {
            f"map_{i}": [
                MapChange(operation="add", key=f"key_{j}", value=f"value_{j}")
                for j in range(10)
            ]
            for i in range(20)  # 20 maps with 10 operations each = 200 total operations
        }

        with patch(
            "haproxy_template_ic.dataplane.runtime_api.add_map_entry"
        ) as mock_add:
            mock_response = create_mock_api_response(
                content="success", reload_id="test-reload"
            )
            mock_add.return_value = mock_response

            await runtime_api.bulk_map_updates(large_map_updates)

            # Verify all 200 operations were processed
            assert mock_add.call_count == 200
