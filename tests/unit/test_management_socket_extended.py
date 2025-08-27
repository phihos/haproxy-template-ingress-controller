"""Extended unit tests for management socket to increase line coverage."""

from unittest.mock import AsyncMock, MagicMock, Mock, patch
import pytest

from haproxy_template_ic.management_socket import (
    ManagementSocketServer,
    _serialize_resource_collection,
    _serialize_kopf_index,
    _serialize_memo_indices,
    serialize_state,
)


class TestSerializeResourceCollection:
    """Test _serialize_resource_collection function edge cases."""

    def test_fallback_for_non_listable_iterables(self):
        """Test fallback for iterables that can't be converted to list."""

        class BadIterable:
            def __iter__(self):
                raise TypeError("Can't iterate")

        bad_iter = BadIterable()
        result = _serialize_resource_collection(bad_iter)
        # When list() fails, it returns the object wrapped
        assert len(result) == 1
        assert isinstance(result[0], BadIterable)

    def test_dict_as_iterable(self):
        """Test that dicts are treated as iterables and return keys."""
        # Dicts are iterable, so they hit the first branch
        resource = {"name": "test", "kind": "Service"}
        result = _serialize_resource_collection(resource)
        assert result == ["name", "kind"]  # Dict iteration gives keys

    def test_fallback_for_other_types(self):
        """Test fallback for non-iterable, non-dict types."""
        result = _serialize_resource_collection(42)
        assert result == [{"data": 42}]


class TestSerializeKopfIndex:
    """Test _serialize_kopf_index function edge cases."""

    def test_index_without_items_method(self):
        """Test handling of index without items method."""

        class BadIndex:
            def __iter__(self):
                return iter([])

            def __getitem__(self, key):
                return []

        result = _serialize_kopf_index(BadIndex())
        assert result == {}

    def test_index_with_key_error(self):
        """Test handling of index that raises KeyError."""

        class ErrorIndex:
            def __iter__(self):
                return iter(["key1"])

            def __getitem__(self, key):
                raise KeyError(f"Key not found: {key}")

            def items(self):
                return []

        result = _serialize_kopf_index(ErrorIndex())
        assert result == {}


class TestSerializeMemIndices:
    """Test _serialize_memo_indices function edge cases."""

    def test_indices_with_serialization_error(self):
        """Test handling of indices that fail to serialize."""
        memo = MagicMock()

        class BadIndex:
            def __iter__(self):
                raise ValueError("Can't iterate")

            def __getitem__(self, key):
                return []

            def items(self):
                raise ValueError("Can't get items")

        memo.indices = {"bad_index": BadIndex()}

        indices, errors = _serialize_memo_indices(memo)
        assert "bad_index" in indices
        assert indices["bad_index"] == {}
        assert len(errors) == 1
        assert "bad_index" in errors[0]

    def test_legacy_index_with_type_error(self):
        """Test handling of legacy _index attributes that raise TypeError."""
        memo = MagicMock()
        memo.indices = None

        class BadLegacyIndex:
            def items(self):
                return [("key", "value")]

        memo.bad_index = BadLegacyIndex()

        # Mock dir() to return our attribute
        with patch(
            "haproxy_template_ic.management_socket.dir", return_value=["bad_index"]
        ):
            with patch(
                "haproxy_template_ic.management_socket.dict",
                side_effect=TypeError("Can't convert"),
            ):
                indices, errors = _serialize_memo_indices(memo)
                assert "bad_index" in indices
                assert indices["bad_index"] == {}
                assert len(errors) == 1
                assert "legacy index" in errors[0]


class TestSerializeState:
    """Test serialize_state function edge cases."""

    def test_config_serialization_error(self):
        """Test handling of config serialization errors."""
        memo = MagicMock()
        memo.config = MagicMock()
        memo.config.model_dump.side_effect = RuntimeError("Config error")

        state = serialize_state(memo)
        assert state["config"] == {}
        assert "serialization_errors" in state
        assert any(
            "config serialization" in err for err in state["serialization_errors"]
        )

    def test_debouncer_serialization_error(self):
        """Test handling of debouncer serialization errors."""
        memo = MagicMock()
        memo.config = None
        memo.haproxy_config_context = None
        memo.cli_options = None
        memo.indices = {}
        memo.debouncer = MagicMock()
        memo.debouncer.get_stats.side_effect = AttributeError("No stats")

        state = serialize_state(memo)
        assert state["debouncer"] is None
        assert "serialization_errors" in state
        assert any(
            "debouncer serialization" in err for err in state["serialization_errors"]
        )

    def test_debouncer_none(self):
        """Test handling when debouncer is None."""
        memo = MagicMock()
        memo.config = None
        memo.haproxy_config_context = None
        memo.cli_options = None
        memo.indices = {}
        memo.debouncer = None  # Explicitly None

        state = serialize_state(memo)
        assert state["debouncer"] is None
        # No errors since this is a normal case
        assert "serialization_errors" not in state or not any(
            "debouncer" in err for err in state.get("serialization_errors", [])
        )


class TestManagementSocketServer:
    """Test ManagementSocketServer edge cases."""

    @pytest.mark.asyncio
    async def test_handle_client_send_error(self):
        """Test handling of error when sending error response fails."""
        memo = MagicMock()
        server = ManagementSocketServer(memo, "/tmp/test.sock")

        reader = AsyncMock()
        reader.read = AsyncMock(side_effect=Exception("Read error"))

        writer = AsyncMock()
        writer.write = Mock(side_effect=Exception("Write error"))
        writer.drain = AsyncMock()
        writer.close = Mock()
        writer.wait_closed = AsyncMock()

        with patch.object(server.logger, "error") as mock_error:
            with patch.object(server.logger, "debug") as mock_debug:
                await server._handle_client(reader, writer)

                # Should log the original error
                assert mock_error.called
                # Should log the send error in debug
                assert mock_debug.called
                assert "Failed to send error response" in str(mock_debug.call_args)

    def test_dump_debouncer_with_debouncer(self):
        """Test _dump_debouncer when debouncer exists."""
        memo = MagicMock()
        memo.debouncer = MagicMock()
        memo.debouncer.get_stats.return_value = {"min_interval": 5, "max_interval": 60}

        server = ManagementSocketServer(memo)
        result = server._dump_debouncer()

        assert result == {"debouncer": {"min_interval": 5, "max_interval": 60}}

    def test_dump_debouncer_without_debouncer(self):
        """Test _dump_debouncer when no debouncer exists."""
        memo = MagicMock(spec=[])  # No debouncer attribute

        server = ManagementSocketServer(memo)
        result = server._dump_debouncer()

        assert result == {"debouncer": None}

    def test_get_deployment_history_with_endpoint(self):
        """Test _get_deployment_history with existing endpoint."""
        memo = MagicMock()
        memo.deployment_history = MagicMock()
        memo.deployment_history.to_dict.return_value = {
            "deployment_history": {
                "http://endpoint1": {"status": "success"},
                "http://endpoint2": {"status": "failed"},
            }
        }

        server = ManagementSocketServer(memo)
        result = server._get_deployment_history("http://endpoint1")

        assert result == {"result": {"status": "success"}}

    def test_get_deployment_history_missing_endpoint(self):
        """Test _get_deployment_history with non-existent endpoint."""
        memo = MagicMock()
        memo.deployment_history = MagicMock()
        memo.deployment_history.to_dict.return_value = {
            "deployment_history": {"http://endpoint1": {"status": "success"}}
        }

        server = ManagementSocketServer(memo)
        result = server._get_deployment_history("http://missing")

        assert "error" in result
        assert "No deployment history found" in result["error"]
        assert result["available_endpoints"] == ["http://endpoint1"]

    def test_get_deployment_history_no_history(self):
        """Test _get_deployment_history when no history exists."""
        memo = MagicMock(spec=[])  # No deployment_history attribute

        server = ManagementSocketServer(memo)
        result = server._get_deployment_history("http://endpoint1")

        assert result == {"error": "No deployment history available"}

    def test_dump_indices_with_error(self):
        """Test _dump_indices when serialization fails."""
        memo = MagicMock()

        class BadIndex:
            pass

        memo.indices = {"failing_index": BadIndex()}

        server = ManagementSocketServer(memo)

        with patch(
            "haproxy_template_ic.management_socket._serialize_kopf_index",
            side_effect=Exception("Serialization failed"),
        ):
            result = server._dump_indices()

            assert "indices" in result
            assert "failing_index" in result["indices"]
            assert "error" in result["indices"]["failing_index"]
            assert "Failed to serialize" in result["indices"]["failing_index"]["error"]

    def test_dump_indices_legacy_with_error(self):
        """Test _dump_indices with legacy index that fails."""
        memo = MagicMock()
        memo.indices = None

        class BadLegacyIndex:
            def items(self):
                return []

        memo.legacy_index = BadLegacyIndex()

        server = ManagementSocketServer(memo)

        with patch(
            "haproxy_template_ic.management_socket.dir", return_value=["legacy_index"]
        ):
            with patch(
                "haproxy_template_ic.management_socket.dict",
                side_effect=Exception("Dict conversion failed"),
            ):
                result = server._dump_indices()

                assert "indices" in result
                assert "legacy_index" in result["indices"]
                assert "error" in result["indices"]["legacy_index"]
