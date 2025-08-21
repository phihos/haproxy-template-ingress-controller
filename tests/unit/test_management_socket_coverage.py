"""
Additional tests for management socket to improve coverage.

Tests for missing coverage areas in management_socket.py module.
"""

import pytest
from pathlib import Path
from unittest.mock import Mock, AsyncMock, patch

from haproxy_template_ic.management_socket import (
    ManagementSocketServer,
    serialize_state,
    run_management_socket_server,
    _serialize_resource_collection,
    _serialize_kopf_index,
)


class TestSerializeResourceCollection:
    """Test _serialize_resource_collection function edge cases."""

    def test_serialize_non_listable_iterable(self):
        """Test serialization of non-listable iterables."""
        # Create a mock iterable that raises TypeError on list()
        mock_iterable = Mock()
        mock_iterable.__iter__ = Mock(return_value=iter([1, 2, 3]))

        # Mock list() to raise TypeError to trigger fallback
        with patch("builtins.list", side_effect=TypeError("Cannot convert to list")):
            result = _serialize_resource_collection(mock_iterable)
            assert result == [mock_iterable]

    def test_serialize_resource_collection_fallback(self):
        """Test fallback for non-dict, non-iterable types."""
        # Test with integer (not dict, not iterable except as itself)
        result = _serialize_resource_collection(42)
        assert result == [{"data": 42}]

        # Test with string (special case - should not iterate over chars)
        result = _serialize_resource_collection("test")
        assert result == [{"data": "test"}]

        # Test with custom object
        class CustomObject:
            pass

        obj = CustomObject()
        result = _serialize_resource_collection(obj)
        assert result == [{"data": obj}]

    def test_serialize_resource_collection_dict(self):
        """Test serialization of dictionary resources."""
        resource_dict = {"name": "test-resource", "status": "active"}
        result = _serialize_resource_collection(resource_dict)
        # Dictionary is iterable (over keys) so it becomes list of keys
        assert result == ["name", "status"]


class TestSerializeKopfIndex:
    """Test _serialize_kopf_index function edge cases."""

    def test_serialize_kopf_index_invalid_object(self):
        """Test serialization of objects that don't implement the protocol."""
        # Test with object missing __iter__
        mock_obj = Mock()
        mock_obj.__getitem__ = Mock()
        del mock_obj.__iter__  # Remove __iter__ method

        result = _serialize_kopf_index(mock_obj)
        assert result == {}

    def test_serialize_kopf_index_missing_getitem(self):
        """Test serialization of objects missing __getitem__."""
        # Test with object missing __getitem__
        mock_obj = Mock()
        mock_obj.__iter__ = Mock()
        del mock_obj.__getitem__  # Remove __getitem__ method

        result = _serialize_kopf_index(mock_obj)
        assert result == {}


class TestManagementSocketServerCoverage:
    """Test ManagementSocketServer edge cases for improved coverage."""

    def test_server_initialization_with_none_memo(self):
        """Test server initialization with None memo."""
        server = ManagementSocketServer(None, "/tmp/test.sock")
        assert server.socket_path == Path("/tmp/test.sock")
        assert server.memo is None

    @pytest.mark.asyncio
    async def test_handle_client_readline_error(self):
        """Test handle_client when read raises an exception."""
        memo = Mock()
        server = ManagementSocketServer(memo, "/tmp/test.sock")

        # Mock StreamReader and StreamWriter
        reader = AsyncMock()
        writer = AsyncMock()

        # Make read raise an exception
        reader.read.side_effect = Exception("Connection error")

        # Should handle the exception gracefully
        await server._handle_client(reader, writer)

        # Verify writer.close() was called despite the error
        writer.close.assert_called_once()

    @pytest.mark.asyncio
    async def test_handle_client_process_command_exception(self):
        """Test handle_client when process_command raises an exception."""
        memo = Mock()
        server = ManagementSocketServer(memo, "/tmp/test.sock")

        reader = AsyncMock()
        writer = AsyncMock()

        # Mock read to return a command
        reader.read.return_value = b"test command\n"

        # Mock process_command to raise an exception
        with patch.object(
            server, "_process_command", side_effect=Exception("Processing error")
        ):
            await server._handle_client(reader, writer)

        # Should write error response
        writer.write.assert_called()
        writer.close.assert_called_once()

    def test_cleanup_permission_error(self):
        """Test cleanup when socket removal raises PermissionError."""
        memo = Mock()
        server = ManagementSocketServer(memo, "/tmp/test.sock")

        # Mock pathlib methods
        with patch("pathlib.Path.exists", return_value=True):
            with patch(
                "pathlib.Path.unlink", side_effect=PermissionError("Permission denied")
            ):
                # Should raise PermissionError since _cleanup doesn't handle it
                with pytest.raises(PermissionError):
                    server._cleanup()

    @pytest.mark.asyncio
    async def test_run_socket_permission_error(self):
        """Test run method when socket creation fails due to permissions."""
        memo = Mock()
        server = ManagementSocketServer(memo, "/tmp/test.sock")

        # Mock pathlib methods
        with patch("pathlib.Path.exists", return_value=False):
            # Mock start_unix_server to raise PermissionError
            with patch(
                "asyncio.start_unix_server",
                side_effect=PermissionError("Permission denied"),
            ):
                # Should not raise exception due to try/except handling
                await server.run()

    @pytest.mark.asyncio
    async def test_run_with_server_cleanup_on_exception(self):
        """Test run method with server cleanup when exception occurs."""
        memo = Mock()
        server = ManagementSocketServer(memo, "/tmp/test.sock")

        # Mock pathlib methods
        with patch("pathlib.Path.exists", return_value=False):
            # Create a mock unix server
            mock_unix_server = AsyncMock()
            mock_unix_server.serve_forever.side_effect = Exception("Server error")
            mock_unix_server.close = Mock()

            with patch("asyncio.start_unix_server", return_value=mock_unix_server):
                # Should not raise exception due to finally block handling
                await server.run()

                # Verify server cleanup was attempted
                mock_unix_server.close.assert_called_once()


class TestRunManagementSocketServerCoverage:
    """Test run_management_socket_server function edge cases."""

    @pytest.mark.asyncio
    async def test_run_management_socket_server_with_custom_path(self):
        """Test run_management_socket_server with custom socket path."""
        memo = Mock()
        custom_path = "/custom/socket/path.sock"

        with patch(
            "haproxy_template_ic.management_socket.ManagementSocketServer"
        ) as MockServer:
            mock_server_instance = AsyncMock()
            MockServer.return_value = mock_server_instance

            await run_management_socket_server(memo, custom_path)

            # Verify server was created with correct argument order
            MockServer.assert_called_once_with(memo, custom_path)
            mock_server_instance.run.assert_called_once()

    @pytest.mark.asyncio
    async def test_run_management_socket_server_exception_handling(self):
        """Test run_management_socket_server exception handling."""
        memo = Mock()

        with patch(
            "haproxy_template_ic.management_socket.ManagementSocketServer"
        ) as MockServer:
            mock_server_instance = AsyncMock()
            mock_server_instance.run.side_effect = Exception("Server startup failed")
            MockServer.return_value = mock_server_instance

            # Should not propagate the exception due to except block
            await run_management_socket_server(memo)

            # Run should have been called
            mock_server_instance.run.assert_called_once()


class TestSerializeStateAdditionalCoverage:
    """Test serialize_state function additional edge cases."""

    def test_serialize_state_memo_with_missing_attributes(self):
        """Test serialize_state with memo missing some attributes."""
        memo = Mock()
        # Set config to None to trigger hasattr() false condition
        memo.config = None
        memo.cli_options = Mock()
        memo.cli_options.configmap_name = "test"

        result = serialize_state(memo)

        # Should have empty config when config is None/falsy
        assert "config" in result
        assert result["config"] == {}

    def test_serialize_state_indices_iteration_error(self):
        """Test serialize_state when indices iteration fails."""
        memo = Mock()
        memo.config = Mock()
        memo.config.model_dump.return_value = {"test": "config"}
        memo.cli_options = Mock()
        memo.cli_options.configmap_name = "test"

        # Test error path - when _serialize_memo_indices raises TypeError (which is caught)
        with patch(
            "haproxy_template_ic.management_socket._serialize_memo_indices",
            side_effect=TypeError("Indices error"),
        ):
            result = serialize_state(memo)

            # Should handle iteration error gracefully
            assert "serialization_errors" in result
            assert any(
                "indices serialization: Indices error" in error
                for error in result["serialization_errors"]
            )

    def test_serialize_state_with_complex_index_data(self):
        """Test serialize_state with complex index data structures."""
        memo = Mock()
        memo.config = Mock()
        memo.config.model_dump.return_value = {"test": "config"}
        memo.cli_options = Mock()
        memo.cli_options.configmap_name = "test"

        # Create complex index data
        mock_index = Mock()
        mock_index.__iter__ = Mock(
            return_value=iter([("ns1", "pod1"), ("ns2", "pod2")])
        )
        mock_index.__getitem__ = Mock(
            side_effect=lambda key: [{"name": f"resource-{key[0]}-{key[1]}"}]
        )

        memo.indices = {"pods": mock_index}

        result = serialize_state(memo)

        # Should serialize complex index data successfully
        assert "indices" in result
        assert "pods" in result["indices"]
