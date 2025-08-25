"""
Unit tests for management socket functionality.

Tests the ManagementSocketServer class and related state serialization functions.
"""

import asyncio
import json
import pytest
from pathlib import Path
from unittest.mock import Mock, AsyncMock, patch

from haproxy_template_ic.management_socket import (
    ManagementSocketServer,
    serialize_state,
    run_management_socket_server,
    _serialize_kopf_index,
)


class TestSerializeKopfIndex:
    """Test the _serialize_kopf_index function."""

    def test_serialize_kopf_index_with_tuple_keys(self):
        """Test that tuple keys are properly formatted with ':' separator."""
        index_data = {
            ("namespace", "name"): [{"metadata": {"name": "resource1"}}],
            ("default", "my-service"): [{"metadata": {"name": "resource2"}}],
            ("echo-server",): [
                {"metadata": {"name": "resource3"}}
            ],  # Single-element tuple
        }

        result = _serialize_kopf_index(index_data)

        # Check that tuple keys are converted to structured strings
        assert "namespace:name" in result
        assert "default:my-service" in result
        assert "echo-server" in result  # Single element tuple becomes just the element

        # Check that the resources are preserved
        assert result["namespace:name"][0]["metadata"]["name"] == "resource1"
        assert result["default:my-service"][0]["metadata"]["name"] == "resource2"
        assert result["echo-server"][0]["metadata"]["name"] == "resource3"

    def test_serialize_kopf_index_with_string_keys(self):
        """Test that string keys are preserved as-is."""
        index_data = {
            "simple-key": [{"metadata": {"name": "resource1"}}],
            "another-key": [{"metadata": {"name": "resource2"}}],
        }

        result = _serialize_kopf_index(index_data)

        assert "simple-key" in result
        assert "another-key" in result
        assert result["simple-key"][0]["metadata"]["name"] == "resource1"
        assert result["another-key"][0]["metadata"]["name"] == "resource2"

    def test_serialize_kopf_index_empty(self):
        """Test serializing an empty index."""
        result = _serialize_kopf_index({})
        assert result == {}

    def test_serialize_kopf_index_invalid_data(self):
        """Test serializing invalid data returns empty dict."""
        result = _serialize_kopf_index(None)
        assert result == {}

        result = _serialize_kopf_index("not an index")
        assert result == {}


class TestSerializeState:
    """Test the serialize_state function."""

    def test_serialize_state_complete_memo(self):
        """Test serialization with complete memo object."""
        # Create mock memo with all expected attributes
        memo = Mock()
        memo.config = Mock()
        memo.config.model_dump.return_value = {
            "pod_selector": {"match_labels": {"app": "test"}}
        }

        memo.haproxy_config_context = Mock()
        memo.haproxy_config_context.model_dump.return_value = {
            "rendered_config": "test config"
        }

        memo.cli_options = Mock()
        memo.cli_options.configmap_name = "test-config"
        memo.cli_options.healthz_port = 8080
        memo.cli_options.verbose = 1
        memo.cli_options.socket_path = "/test/socket"

        # Add mock indices using new structure
        mock_index = Mock()
        mock_index.__iter__ = Mock(return_value=iter([("default", "resource1")]))
        mock_index.__getitem__ = Mock(return_value=[{"name": "test-resource"}])
        memo.indices = {"resources": mock_index}

        # Add legacy mock indices for backward compatibility testing
        memo.resource_index = {"resource1": "data1", "resource2": "data2"}
        memo.config_index = {"config1": "data1"}

        # Mock dir() to return our legacy indices
        with patch(
            "builtins.dir",
            return_value=["resource_index", "config_index", "other_attr"],
        ):
            result = serialize_state(memo)

        assert "config" in result
        assert "haproxy_config_context" in result
        assert "metadata" in result
        assert "cli_options" in result
        assert "indices" in result

        assert result["config"]["pod_selector"]["match_labels"]["app"] == "test"
        assert result["haproxy_config_context"]["rendered_config"] == "test config"
        assert result["cli_options"]["configmap_name"] == "test-config"

        # Check that indices contains both new structure and legacy indices
        assert "indices" in result
        assert "resources" in result["indices"]  # New structure
        assert "resource_index" in result["indices"]  # Legacy structure
        assert "config_index" in result["indices"]

    def test_serialize_state_minimal_memo(self):
        """Test serialization with minimal memo object."""
        memo = Mock()
        # Remove attributes to test defaults
        del memo.config
        del memo.haproxy_config_context
        del memo.cli_options

        with patch("builtins.dir", return_value=["other_attr"]):
            result = serialize_state(memo)

        assert result["config"] == {}
        assert result["haproxy_config_context"] == {}
        assert result["cli_options"] == {}
        assert result["metadata"]["configmap_name"] is None

    def test_serialize_state_none_values(self):
        """Test serialization with None values."""
        memo = Mock()
        memo.config = None
        memo.haproxy_config_context = None
        memo.cli_options = None

        with patch("builtins.dir", return_value=[]):
            result = serialize_state(memo)

        assert result["config"] == {}
        assert result["haproxy_config_context"] == {}
        assert result["cli_options"] == {}

    def test_serialize_state_serialization_error(self):
        """Test serialization with error during model_dump."""
        memo = Mock()
        memo.config = Mock()
        memo.config.model_dump.side_effect = RuntimeError("Serialization failed")
        memo.cli_options = Mock()
        memo.cli_options.configmap_name = "test-config"

        result = serialize_state(memo)

        # New behavior: errors are collected in serialization_errors field
        assert "serialization_errors" in result
        assert any(
            "config serialization" in error for error in result["serialization_errors"]
        )
        assert result["metadata"]["configmap_name"] == "test-config"
        assert result["config"] == {}  # Should be empty dict on error

    def test_serialize_state_haproxy_config_context_error(self):
        """Test serialization with haproxy_config_context error."""
        memo = Mock()
        memo.haproxy_config_context = Mock()
        memo.haproxy_config_context.model_dump.side_effect = ValueError("Context error")
        memo.cli_options = Mock()
        memo.cli_options.configmap_name = "test"

        result = serialize_state(memo)

        assert "serialization_errors" in result
        assert any(
            "haproxy_config_context serialization" in error
            for error in result["serialization_errors"]
        )
        assert result["haproxy_config_context"] == {}

    def test_serialize_state_indices_dict_error(self):
        """Test serialization with indices dict conversion error."""
        memo = Mock()
        memo.test_index = Mock()
        # Set memo.indices to None to skip the new code path and test only legacy indices
        memo.indices = None

        # Mock dict() to raise TypeError for this index
        with patch("builtins.dict", side_effect=TypeError("Dict conversion error")):
            with patch("builtins.dir", return_value=["test_index"]):
                result = serialize_state(memo)

        assert "serialization_errors" in result
        assert any(
            "legacy index 'test_index' serialization" in error
            for error in result["serialization_errors"]
        )

    def test_serialize_state_indices_access_error(self):
        """Test serialization with indices access error."""
        memo = Mock()
        # Make dir() raise AttributeError
        with patch("builtins.dir", side_effect=AttributeError("Dir access error")):
            result = serialize_state(memo)

        assert "serialization_errors" in result
        assert any(
            "indices serialization" in error for error in result["serialization_errors"]
        )
        assert result["indices"] == {}

    def test_serialize_state_with_flags(self):
        """Test serialization with boolean flags."""
        memo = Mock()
        memo.config = Mock()
        memo.config.model_dump.return_value = {}
        memo.cli_options = Mock()
        memo.cli_options.configmap_name = "test"
        memo.config_reload_flag = True
        memo.stop_flag = True

        with patch("builtins.dir", return_value=[]):
            result = serialize_state(memo)

        assert result["metadata"]["has_config_reload_flag"] is True
        assert result["metadata"]["has_stop_flag"] is True


class TestManagementSocketServer:
    """Test the ManagementSocketServer class."""

    @pytest.fixture
    def mock_memo(self):
        """Create a mock memo object for testing."""
        memo = Mock()
        memo.config = Mock()
        memo.config.maps = {"map1": Mock()}
        memo.config.watched_resources = {"resource1": Mock()}
        memo.config.template_snippets = {"snippet1": Mock()}
        memo.config.certificates = {"cert1": Mock()}
        memo.haproxy_config_context = Mock()
        memo.haproxy_config_context.model_dump.return_value = {"test": "data"}
        return memo

    @pytest.fixture
    def server(self, mock_memo, tmp_path):
        """Create a ManagementSocketServer instance for testing."""
        socket_path = str(tmp_path / "test.sock")
        return ManagementSocketServer(mock_memo, socket_path)

    def test_init(self, mock_memo, tmp_path):
        """Test ManagementSocketServer initialization."""
        socket_path = str(tmp_path / "test.sock")
        server = ManagementSocketServer(mock_memo, socket_path)

        assert server.memo == mock_memo
        assert server.socket_path == Path(socket_path)
        assert server.server is None

    @pytest.mark.asyncio
    async def test_process_command_empty(self, server):
        """Test processing empty command."""
        result = await server._process_command("")
        assert "error" in result
        assert "Empty command" in result["error"]

    @pytest.mark.asyncio
    async def test_process_command_dump_all(self, server):
        """Test 'dump all' command."""
        with patch(
            "haproxy_template_ic.management_socket.serialize_state"
        ) as mock_serialize:
            mock_serialize.return_value = {"test": "data"}
            result = await server._process_command("dump all")
            assert result == {"test": "data"}
            mock_serialize.assert_called_once_with(server.memo)

    @pytest.mark.asyncio
    async def test_process_command_dump_indices(self, server):
        """Test 'dump indices' command."""
        # Set up new-style indices
        server.memo.indices = {}  # Empty dict instead of Mock

        # Set up old-style indices for backward compatibility test
        server.memo.resource_index = {"res1": "data1"}
        server.memo.config_index = {"conf1": "data1"}

        with patch(
            "builtins.dir",
            return_value=["resource_index", "config_index", "other", "indices"],
        ):
            result = await server._process_command("dump indices")

        assert "indices" in result
        assert "resource_index" in result["indices"]
        assert "config_index" in result["indices"]

    @pytest.mark.asyncio
    async def test_process_command_dump_config(self, server):
        """Test 'dump config' command."""
        result = await server._process_command("dump config")
        assert "haproxy_config_context" in result

    @pytest.mark.asyncio
    async def test_process_command_dump_config_no_context(self, server):
        """Test 'dump config' command with no context."""
        server.memo.haproxy_config_context = None
        result = await server._process_command("dump config")

        assert "haproxy_config_context" in result
        assert result["haproxy_config_context"]["rendered_config"] is None

    @pytest.mark.asyncio
    async def test_process_command_dump_unknown(self, server):
        """Test 'dump' command with unknown subcommand."""
        result = await server._process_command("dump unknown")
        assert "error" in result
        assert "Unknown dump command" in result["error"]

    @pytest.mark.asyncio
    async def test_process_command_dump_missing_subcommand(self, server):
        """Test 'dump' command without subcommand."""
        result = await server._process_command("dump")
        assert "error" in result
        assert "Missing command name" in result["error"]

    @pytest.mark.asyncio
    async def test_process_command_get_maps(self, server):
        """Test 'get maps' command."""
        mock_map = Mock()
        mock_map.model_dump.return_value = {"template": "test template"}
        server.memo.config.maps = {"test-map": mock_map}

        result = await server._process_command("get maps test-map")
        assert "result" in result
        assert result["result"]["template"] == "test template"

    @pytest.mark.asyncio
    async def test_process_command_get_map_not_found(self, server):
        """Test 'get maps' command with non-existent map."""
        server.memo.config.maps = {}

        result = await server._process_command("get maps nonexistent")
        assert "error" in result
        assert "Map not found" in result["error"]

    @pytest.mark.asyncio
    async def test_process_command_get_watched_resources(self, server):
        """Test 'get watched_resources' command."""
        mock_resource = Mock()
        mock_resource.model_dump.return_value = {"kind": "Ingress"}
        server.memo.config.watched_resources = {"ingresses": mock_resource}

        result = await server._process_command("get watched_resources ingresses")
        assert "result" in result
        assert result["result"]["kind"] == "Ingress"

    @pytest.mark.asyncio
    async def test_process_command_get_template_snippets(self, server):
        """Test 'get template_snippets' command."""
        mock_snippet = Mock()
        mock_snippet.model_dump.return_value = {"template": "test snippet"}
        server.memo.config.template_snippets = {"test-snippet": mock_snippet}

        result = await server._process_command("get template_snippets test-snippet")
        assert "result" in result
        assert result["result"]["template"] == "test snippet"

    @pytest.mark.asyncio
    async def test_process_command_get_certificates(self, server):
        """Test 'get certificates' command."""
        mock_cert = Mock()
        mock_cert.model_dump.return_value = {"template": "cert template"}
        server.memo.config.certificates = {"test-cert": mock_cert}

        result = await server._process_command("get certificates test-cert")
        assert "result" in result
        assert result["result"]["template"] == "cert template"

    @pytest.mark.asyncio
    async def test_process_command_get_no_model_dump(self, server):
        """Test 'get' command with object without model_dump method."""
        server.memo.config.maps = {"test": "simple string"}

        result = await server._process_command("get maps test")
        assert "result" in result
        assert result["result"]["data"] == "simple string"

    @pytest.mark.asyncio
    async def test_process_command_get_unknown_collection(self, server):
        """Test 'get' command with unknown collection."""
        result = await server._process_command("get unknown_collection item")
        assert "error" in result
        assert "Unknown collection type" in result["error"]

    @pytest.mark.asyncio
    async def test_process_command_get_missing_args(self, server):
        """Test 'get' command with missing arguments."""
        result = await server._process_command("get maps")
        assert "error" in result
        assert "Missing arguments" in result["error"]

    @pytest.mark.asyncio
    async def test_process_command_unknown_command(self, server):
        """Test unknown command."""
        result = await server._process_command("unknown command")
        assert "error" in result
        assert "Unknown command" in result["error"]

    def test_dump_indices(self, server):
        """Test _dump_indices method with new memo.indices structure."""
        # Test new-style memo.indices dictionary
        server.memo.indices = {
            "ingresses": {
                ("default", "my-ingress"): [{"metadata": {"name": "my-ingress"}}],
                ("kube-system", "system-ingress"): [
                    {"metadata": {"name": "system-ingress"}}
                ],
            },
            "endpoints": {
                ("echo-server",): [{"metadata": {"name": "echo-endpoint"}}],
            },
        }

        # Also test old-style _index attributes for backward compatibility
        server.memo.resource_index = {"res1": "data1"}
        server.memo.config_index = {"conf1": "data1"}
        server.memo.other_attr = "not an index"

        with patch(
            "builtins.dir",
            return_value=["resource_index", "config_index", "other_attr", "indices"],
        ):
            result = server._dump_indices()

        assert "indices" in result
        # Should have both new-style indices and old-style indices
        assert "ingresses" in result["indices"]
        assert "endpoints" in result["indices"]
        assert "resource_index" in result["indices"]
        assert "config_index" in result["indices"]
        assert "other_attr" not in result["indices"]

        # Check that tuple keys are properly serialized with ':' separator
        assert "default:my-ingress" in result["indices"]["ingresses"]
        assert "kube-system:system-ingress" in result["indices"]["ingresses"]
        assert "echo-server" in result["indices"]["endpoints"]

    def test_dump_config_with_context(self, server):
        """Test _dump_config method with context."""
        server.memo.haproxy_config_context = Mock()
        server.memo.haproxy_config_context.model_dump.return_value = {"test": "data"}

        result = server._dump_config()
        assert "haproxy_config_context" in result
        assert result["haproxy_config_context"]["test"] == "data"

    def test_dump_config_without_context(self, server):
        """Test _dump_config method without context."""
        server.memo.haproxy_config_context = None

        result = server._dump_config()
        assert "haproxy_config_context" in result
        assert result["haproxy_config_context"]["rendered_config"] is None

    @pytest.mark.asyncio
    async def test_handle_client_success(self, server):
        """Test successful client handling."""
        mock_reader = AsyncMock()
        mock_writer = AsyncMock()

        mock_reader.read.return_value = b"dump all"

        with patch.object(server, "_process_command") as mock_process:
            mock_process.return_value = {"status": "ok"}

            await server._handle_client(mock_reader, mock_writer)

            mock_process.assert_called_once_with("dump all")
            mock_writer.write.assert_called_once()
            mock_writer.drain.assert_called_once()
            mock_writer.close.assert_called_once()
            mock_writer.wait_closed.assert_called_once()

    @pytest.mark.asyncio
    async def test_handle_client_empty_command(self, server):
        """Test client handling with empty command."""
        mock_reader = AsyncMock()
        mock_writer = AsyncMock()

        mock_reader.read.return_value = b""  # Empty command

        with patch.object(server, "_process_command") as mock_process:
            mock_process.return_value = {"status": "ok"}

            await server._handle_client(mock_reader, mock_writer)

            # Should default to "dump all"
            mock_process.assert_called_once_with("dump all")

    @pytest.mark.asyncio
    async def test_handle_client_process_error(self, server):
        """Test client handling with processing error."""
        mock_reader = AsyncMock()
        mock_writer = AsyncMock()

        mock_reader.read.return_value = b"dump all"

        with patch.object(
            server, "_process_command", side_effect=RuntimeError("Process error")
        ):
            await server._handle_client(mock_reader, mock_writer)

            # Should send error response
            mock_writer.write.assert_called()
            written_data = mock_writer.write.call_args[0][0]
            response = json.loads(written_data.decode())
            assert "error" in response

    @pytest.mark.asyncio
    async def test_handle_client_write_error(self, server):
        """Test client handling with write error."""
        mock_reader = AsyncMock()
        mock_writer = AsyncMock()

        mock_reader.read.return_value = b"dump all"
        mock_writer.write.side_effect = RuntimeError("Write error")

        with patch.object(server, "_process_command") as mock_process:
            mock_process.return_value = {"status": "ok"}

            # Should not raise exception
            await server._handle_client(mock_reader, mock_writer)

    @pytest.mark.asyncio
    async def test_handle_client_error_response_write_error(self, server):
        """Test client handling when error response write fails."""
        mock_reader = AsyncMock()
        mock_writer = AsyncMock()

        mock_reader.read.return_value = b"dump all"

        # First, make _process_command raise an error
        with patch.object(
            server, "_process_command", side_effect=RuntimeError("Process error")
        ):
            # Then make the error response write fail
            mock_writer.write.side_effect = RuntimeError("Send error")

            # Should not raise exception - error is just logged
            await server._handle_client(mock_reader, mock_writer)

            # Should have tried to write once for error response
            assert mock_writer.write.call_count == 1

    @pytest.mark.asyncio
    @patch("asyncio.start_unix_server")
    async def test_run_success(self, mock_start_server, server, tmp_path):
        """Test successful server run."""
        # Create a mock server that can be used as async context manager
        mock_server_instance = AsyncMock()
        mock_server_instance.__aenter__ = AsyncMock(return_value=mock_server_instance)
        mock_server_instance.__aexit__ = AsyncMock(return_value=None)
        mock_server_instance.serve_forever = AsyncMock(
            side_effect=asyncio.CancelledError()
        )

        mock_start_server.return_value = mock_server_instance
        server.server = mock_server_instance

        with pytest.raises(asyncio.CancelledError):
            await server.run()

        mock_start_server.assert_called_once()

    @pytest.mark.asyncio
    @patch("asyncio.start_unix_server")
    async def test_run_with_existing_socket(self, mock_start_server, server, tmp_path):
        """Test server run with existing socket file."""
        # Create existing socket file
        server.socket_path.touch()
        assert server.socket_path.exists()

        mock_server_instance = AsyncMock()
        mock_server_instance.__aenter__ = AsyncMock(return_value=mock_server_instance)
        mock_server_instance.__aexit__ = AsyncMock(return_value=None)
        mock_server_instance.serve_forever = AsyncMock(
            side_effect=asyncio.CancelledError()
        )

        mock_start_server.return_value = mock_server_instance
        server.server = mock_server_instance

        with pytest.raises(asyncio.CancelledError):
            await server.run()

        # Socket file should be removed before starting
        mock_start_server.assert_called_once()

    @pytest.mark.asyncio
    @patch("asyncio.start_unix_server")
    async def test_run_server_error(self, mock_start_server, server):
        """Test server run with server error."""
        mock_start_server.side_effect = RuntimeError("Server error")

        # Should not raise exception (error is logged)
        await server.run()

    def test_cleanup(self, server):
        """Test server cleanup."""
        mock_server_instance = Mock()
        server.server = mock_server_instance

        # Create socket file
        server.socket_path.touch()

        server._cleanup()

        mock_server_instance.close.assert_called_once()
        assert not server.socket_path.exists()

    def test_cleanup_no_server(self, server):
        """Test cleanup with no server instance."""
        server.server = None

        # Should not raise exception
        server._cleanup()

    def test_cleanup_socket_doesnt_exist(self, server):
        """Test cleanup when socket file doesn't exist."""
        server.server = None
        # Don't create socket file

        # Should not raise exception
        server._cleanup()


class TestRunManagementSocketServer:
    """Test the run_management_socket_server function."""

    @pytest.mark.asyncio
    async def test_run_management_socket_server_success(self):
        """Test successful server run."""
        mock_memo = Mock()
        socket_path = "/test/socket"

        with patch(
            "haproxy_template_ic.management_socket.ManagementSocketServer"
        ) as mock_server_class:
            mock_server = AsyncMock()
            mock_server_class.return_value = mock_server
            mock_server.run = AsyncMock()

            await run_management_socket_server(mock_memo, socket_path)

            mock_server_class.assert_called_once_with(mock_memo, socket_path)
            mock_server.run.assert_called_once()

    @pytest.mark.asyncio
    async def test_run_management_socket_server_error(self):
        """Test server run with error."""
        mock_memo = Mock()

        with patch(
            "haproxy_template_ic.management_socket.ManagementSocketServer"
        ) as mock_server_class:
            mock_server = AsyncMock()
            mock_server_class.return_value = mock_server
            mock_server.run = AsyncMock(side_effect=RuntimeError("Server error"))

            # Should not raise exception (error is logged)
            await run_management_socket_server(mock_memo)

    @pytest.mark.asyncio
    async def test_run_management_socket_server_default_path(self):
        """Test server run with default socket path."""
        mock_memo = Mock()

        with patch(
            "haproxy_template_ic.management_socket.ManagementSocketServer"
        ) as mock_server_class:
            mock_server = AsyncMock()
            mock_server_class.return_value = mock_server
            mock_server.run = AsyncMock()

            await run_management_socket_server(mock_memo)

            mock_server_class.assert_called_once_with(
                mock_memo, "/run/haproxy-template-ic/management.sock"
            )


class TestManagementSocketCriticalPaths:
    """Test critical paths and edge cases for management socket."""

    @pytest.fixture
    def server(self):
        """Create a test server instance."""
        memo = Mock()
        return ManagementSocketServer(memo, "/tmp/test.sock")

    @pytest.mark.asyncio
    async def test_server_cleanup_on_cancellation(self, server):
        """Test server cleanup when serve_forever is cancelled."""
        mock_server_instance = AsyncMock()
        mock_server_instance.serve_forever.side_effect = asyncio.CancelledError()
        mock_server_instance.close = Mock()
        mock_server_instance.__aenter__ = AsyncMock(return_value=mock_server_instance)
        mock_server_instance.__aexit__ = AsyncMock(return_value=None)

        with patch("asyncio.start_unix_server", return_value=mock_server_instance):
            with patch.object(server, "_cleanup") as mock_cleanup:
                with pytest.raises(asyncio.CancelledError):
                    await server.run()

                # Verify cleanup was called in finally block
                mock_cleanup.assert_called_once()

    @pytest.mark.asyncio
    async def test_server_cleanup_with_active_connections(self, server):
        """Test cleanup with active client connections."""
        # Create mock server that tracks active connections
        mock_server_instance = AsyncMock()
        mock_server_instance.serve_forever.side_effect = Exception("Server error")
        mock_server_instance.close = Mock()
        mock_server_instance.__aenter__ = AsyncMock(return_value=mock_server_instance)
        mock_server_instance.__aexit__ = AsyncMock(return_value=None)

        with patch("asyncio.start_unix_server", return_value=mock_server_instance):
            with patch("pathlib.Path.exists", return_value=True):
                with patch("pathlib.Path.unlink") as mock_unlink:
                    await server.run()

                    # Verify server was closed and socket removed
                    mock_server_instance.close.assert_called_once()
                    # The cleanup is called in finally block, so it should be called at least once
                    assert mock_unlink.call_count >= 1

    @pytest.mark.asyncio
    async def test_handle_client_connection_drop_during_read(self, server):
        """Test _handle_client when connection drops during read."""
        reader = AsyncMock()
        writer = AsyncMock()

        # Simulate connection drop during read
        reader.read.side_effect = ConnectionError("Connection dropped")

        # Should handle gracefully without raising
        await server._handle_client(reader, writer)

        writer.close.assert_called_once()
        writer.wait_closed.assert_called_once()

    @pytest.mark.asyncio
    async def test_handle_client_write_failure_with_partial_data(self, server):
        """Test _handle_client when write fails with partial data."""
        reader = AsyncMock()
        writer = AsyncMock()

        reader.read.return_value = b"dump all\n"

        # Mock _process_command to return data
        with patch.object(server, "_process_command", return_value={"status": "ok"}):
            # Make writer.write fail
            writer.write.side_effect = BrokenPipeError("Broken pipe")

            # Should handle gracefully
            await server._handle_client(reader, writer)

            writer.close.assert_called_once()

    @pytest.mark.asyncio
    async def test_handle_client_error_response_write_failure(self, server):
        """Test error response write failure (lines 414-416)."""
        reader = AsyncMock()
        writer = AsyncMock()

        reader.read.return_value = b"dump all\n"

        # Make _process_command raise an exception
        with patch.object(
            server, "_process_command", side_effect=RuntimeError("Process error")
        ):
            # Make first write succeed, second write (error response) fail
            writer.write.side_effect = [
                None,
                BrokenPipeError("Cannot write error response"),
            ]
            writer.drain = AsyncMock(
                side_effect=[None, BrokenPipeError("Cannot drain")]
            )

            # Should handle gracefully - error is just logged
            await server._handle_client(reader, writer)

            # Verify writes were attempted
            assert writer.write.call_count >= 1
            writer.close.assert_called_once()

    def test_cleanup_permission_error_on_socket_removal(self, server):
        """Test cleanup when socket removal raises PermissionError."""
        mock_server_instance = Mock()
        server.server = mock_server_instance

        with patch("pathlib.Path.exists", return_value=True):
            with patch(
                "pathlib.Path.unlink", side_effect=PermissionError("Permission denied")
            ):
                # Should raise PermissionError as it's not caught in _cleanup
                with pytest.raises(PermissionError):
                    server._cleanup()

                # Server should still be closed before the exception
                mock_server_instance.close.assert_called_once()

    def test_cleanup_with_socket_locked_by_process(self, server):
        """Test cleanup with socket file locked by another process."""
        mock_server_instance = Mock()
        server.server = mock_server_instance

        with patch("pathlib.Path.exists", return_value=True):
            with patch("pathlib.Path.unlink", side_effect=OSError("Resource busy")):
                # Should raise OSError as it's not caught in _cleanup
                with pytest.raises(OSError):
                    server._cleanup()

    @pytest.mark.asyncio
    async def test_process_command_deployment_history_missing_attribute(self, server):
        """Test deployment history when memo has no deployment_history attribute (lines 324-326)."""
        # Remove deployment_history attribute to trigger the condition
        server.memo.deployment_history = None

        result = await server._process_command("dump deployments")

        expected = {"deployment_history": {}}
        assert result == expected

    @pytest.mark.asyncio
    async def test_process_command_deployment_history_endpoint_found(self, server):
        """Test deployment history when endpoint is found in deployment data (line 335)."""
        # Mock deployment history with data
        mock_history = Mock()
        mock_history.to_dict.return_value = {
            "deployment_history": {
                "http://pod1:5555": {"version": "123", "success": True},
                "http://pod2:5555": {"version": "124", "success": True},
            }
        }
        server.memo.deployment_history = mock_history

        result = await server._process_command("get deployment http://pod1:5555")

        expected_result = {"version": "123", "success": True}
        assert result == {"result": expected_result}

    @pytest.mark.asyncio
    async def test_process_command_get_template_snippet(self, server):
        """Test template snippet retrieval (line 269)."""
        # Mock config with template snippets
        server.memo.config.template_snippets = {
            "backend-name": Mock(
                model_dump=Mock(return_value={"template": "backend_{{ name }}"})
            )
        }

        result = await server._process_command("get template_snippets backend-name")

        expected = {"result": {"template": "backend_{{ name }}"}}
        assert result == expected

    def test_serialize_resource_collection_dict_fallback(self):
        """Test _serialize_resource_collection fallback for dicts (line 58)."""
        from haproxy_template_ic.management_socket import _serialize_resource_collection

        # Test with a single dict resource - dicts are iterable so they iterate over keys
        resource_dict = {"name": "test-resource", "status": "active"}
        result = _serialize_resource_collection(resource_dict)

        # Dict iterates over keys, so result should be list of keys
        assert result == ["name", "status"]

        # Test the actual fallback path with non-iterable type
        result = _serialize_resource_collection(42)
        assert result == [{"data": 42}]

    def test_serialize_state_metadata_serialization_error(self):
        """Test serialize_state metadata serialization error (lines 162-164)."""
        from haproxy_template_ic.management_socket import serialize_state

        memo = Mock()
        memo.config = Mock()
        memo.config.model_dump.return_value = {}

        # Create a mock CLI options that raises an exception when accessed
        class FailingCliOptions:
            def __getattr__(self, name):
                if name == "configmap_name":
                    raise TypeError("Metadata error")
                return Mock()

        memo.cli_options = FailingCliOptions()
        memo.haproxy_config_context = Mock()
        memo.haproxy_config_context.model_dump.return_value = {}
        memo.indices = {}

        result = serialize_state(memo)

        # Should have serialization errors
        assert "serialization_errors" in result
        assert any(
            "metadata serialization" in error
            for error in result["serialization_errors"]
        )

    def test_serialize_state_cli_options_serialization_error(self):
        """Test serialize_state CLI options serialization error (lines 177-179)."""
        from haproxy_template_ic.management_socket import serialize_state

        memo = Mock()
        memo.config = Mock()
        memo.config.model_dump.return_value = {}
        memo.cli_options = None  # This will trigger the AttributeError path
        memo.haproxy_config_context = Mock()
        memo.haproxy_config_context.model_dump.return_value = {}
        memo.indices = {}

        result = serialize_state(memo)

        # Should have empty cli_options
        assert result["cli_options"] == {}

    @pytest.mark.asyncio
    async def test_dump_deployments_command(self, server):
        """Test dump deployments command (lines 241-242)."""
        # Mock deployment history
        mock_history = Mock()
        mock_history.to_dict.return_value = {
            "deployment_history": {
                "http://pod1:5555": {"version": "123", "success": True}
            }
        }
        server.memo.deployment_history = mock_history

        result = await server._process_command("dump deployments")

        expected = {
            "deployment_history": {
                "http://pod1:5555": {"version": "123", "success": True}
            }
        }
        assert result == expected
