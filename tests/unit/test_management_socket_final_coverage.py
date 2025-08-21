"""
Final coverage improvements for management_socket.py to reach 90%+.
"""

import pytest
from unittest.mock import Mock
from haproxy_template_ic.management_socket import (
    ManagementSocketServer,
    _serialize_resource_collection,
    serialize_state,
)


class TestFinalCoverage:
    """Test to cover the remaining missing lines in management_socket.py."""

    def test_serialize_resource_collection_non_iterable_case(self):
        """Test the else branch for non-iterable types (line 61)."""
        # Test with various non-iterable types
        test_cases = [42, 3.14, object()]

        for test_val in test_cases:
            result = _serialize_resource_collection(test_val)
            assert isinstance(result, list)
            assert len(result) == 1
            assert result[0]["data"] == test_val

    @pytest.mark.asyncio
    async def test_management_socket_server_edge_cases(self):
        """Test edge cases in ManagementSocketServer."""
        memo = Mock()
        server = ManagementSocketServer(memo, "/tmp/test.sock")

        # Test error handling when memo has no deployment_history (lines 324-326)
        memo.deployment_history = None
        result = server._get_deployment_history("test-url")
        assert "error" in result
        assert "No deployment history available" in result["error"]

        # Test when deployment_history exists but endpoint not found (lines 337-340)
        mock_history = Mock()
        mock_history.to_dict.return_value = {
            "deployment_history": {"other-url": "data"}
        }
        memo.deployment_history = mock_history

        result = server._get_deployment_history("missing-url")
        assert "error" in result
        assert "No deployment history found" in result["error"]
        assert "available_endpoints" in result

    def test_serialize_state_edge_cases(self):
        """Test serialize_state with various error conditions."""
        # Test with memo that has indices but they fail to serialize
        memo = Mock()
        memo.config = Mock()
        memo.config.model_dump.return_value = {}
        memo.cli_options = Mock()
        memo.cli_options.configmap_name = "test"

        # Mock indices that will cause serialization errors
        memo.indices = {"test": "invalid_index_type"}  # This should trigger line 108

        result = serialize_state(memo)
        assert "serialization_errors" in result

        # Test memo without haproxy_config_context (lines 162-164)
        memo2 = Mock()
        memo2.config = Mock()
        memo2.config.model_dump.return_value = {}
        memo2.cli_options = Mock()
        memo2.cli_options.configmap_name = "test"
        memo2.indices = {}
        del memo2.haproxy_config_context  # Remove to hit the else branch

        result2 = serialize_state(memo2)
        assert result2["haproxy_config_context"] == {}
