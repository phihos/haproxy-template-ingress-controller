"""
Tests for haproxy_template_ic.management_socket module.

This module contains tests for management socket functionality focusing on
critical paths and edge cases that are likely to detect bugs.
"""

import json
import pytest
from unittest.mock import MagicMock, patch
import socket
import tempfile
import os
import asyncio
from pathlib import Path
from dataclasses import dataclass

from haproxy_template_ic.management_socket import (
    serialize_state,
    ManagementSocketServer,
    run_management_socket_server,
    StateSerializer,
    DataclassJSONEncoder,
)
from .utils import get_test_reporter, progress_context
from haproxy_template_ic.config_models import (
    MapConfig,
    HAProxyConfigContext,
    RenderedMap,
    RenderedConfig,
    RenderedCertificate,
    TemplateContext,
    config_from_dict,
)
# from jinja2 import Template  # No longer needed - using string templates


# =============================================================================
# State Serialization Tests
# =============================================================================


def test_serialize_state_basic():
    """Test basic state serialization with minimal memo."""
    memo = MagicMock()
    # Remove attributes that might be implicitly present in MagicMock
    del memo.config_reload_flag
    del memo.stop_flag
    # Ensure config is None to test the hasattr check
    memo.config = None

    result = serialize_state(memo)

    # When config is None, it should handle it gracefully
    assert "error" not in result
    assert "config" in result
    assert "haproxy_config_context" in result
    assert "metadata" in result
    assert "cli_options" in result
    assert "indices" in result

    # Check that config has default values
    assert result["config"]["pod_selector"] is None
    assert result["config"]["watched_resources"] == {}
    assert result["config"]["maps"] == {}


def test_serialize_state_with_full_config():
    """Test state serialization with complete configuration."""
    from haproxy_template_ic.__main__ import CliOptions

    memo = MagicMock()
    memo.config = config_from_dict(
        {
            "pod_selector": {"match_labels": {"app": "haproxy"}},
            "haproxy_config": {"template": "global\n    daemon"},
            "watched_resources": {
                "pods": {
                    "api_version": "v1",
                    "kind": "Pod",
                    "enable_validation_webhook": False,
                },
                "services": {
                    "api_version": "v1",
                    "kind": "Service",
                    "enable_validation_webhook": False,
                },
            },
            "maps": {
                "/etc/haproxy/maps/backend.map": {
                    "template": "server {{ resources.name }} {{ resources.host }}:{{ resources.port }}"
                }
            },
        }
    )
    memo.haproxy_config_context = HAProxyConfigContext(
        config=memo.config,
        template_context=TemplateContext(),
    )
    memo.haproxy_config_context.rendered_maps = [
        RenderedMap(
            path="/etc/haproxy/maps/backend.map",
            content="server web-pod 10.0.1.5:80",
            map_config=memo.config.maps["/etc/haproxy/maps/backend.map"],
        )
    ]
    memo.cli_options = CliOptions(
        configmap_name="haproxy-config",
        healthz_port=8080,
        verbose=1,
        socket_path="/run/haproxy-template-ic/management.sock",
        metrics_port=9090,
        structured_logging=False,
        tracing_enabled=False,
    )
    memo.config_reload_flag = MagicMock()
    memo.stop_flag = MagicMock()

    # Mock indices
    memo.pods_index = {
        ("default", "web-pod"): {"name": "web-pod", "host": "10.0.1.5", "port": "80"}
    }

    result = serialize_state(memo)

    assert result["config"]["pod_selector"]["match_labels"] == {"app": "haproxy"}
    assert "pods" in result["config"]["watched_resources"]
    assert "services" in result["config"]["watched_resources"]
    assert "/etc/haproxy/maps/backend.map" in result["config"]["maps"]
    assert (
        "/etc/haproxy/maps/backend.map"
        in result["haproxy_config_context"]["rendered_maps"]
    )
    assert result["metadata"]["configmap_name"] == "haproxy-config"
    assert result["metadata"]["has_config_reload_flag"] is True
    assert result["metadata"]["has_stop_flag"] is True
    assert "pods_index" in result["indices"]

    # Check CLI options
    assert "cli_options" in result
    assert result["cli_options"]["configmap_name"] == "haproxy-config"
    assert result["cli_options"]["healthz_port"] == 8080
    assert result["cli_options"]["verbose"] == 1
    assert (
        result["cli_options"]["socket_path"]
        == "/run/haproxy-template-ic/management.sock"
    )


# =============================================================================
# Command Processing Tests
# =============================================================================


@pytest.mark.asyncio
async def test_process_management_command_dump_all():
    """Test dump all command processing."""
    memo = MagicMock()
    memo.config = config_from_dict(
        {
            "pod_selector": {"match_labels": {"app": "test"}},
            "haproxy_config": {"template": "global\n    daemon"},
        }
    )

    server = ManagementSocketServer(memo)
    result = await server._process_command("dump all")

    assert "config" in result
    assert "haproxy_config_context" in result
    assert "metadata" in result
    assert "indices" in result


@pytest.mark.asyncio
async def test_process_management_command_dump_indices():
    """Test dump indices command processing."""
    memo = MagicMock()
    memo.pods_index = {("default", "pod1"): {"name": "pod1"}}
    memo.services_index = {("default", "svc1"): {"name": "svc1"}}

    server = ManagementSocketServer(memo)
    result = await server._process_command("dump indices")

    assert "indices" in result
    assert "pods_index" in result["indices"]
    assert "services_index" in result["indices"]


@pytest.mark.asyncio
async def test_process_management_command_errors():
    """Test error handling in command processing."""
    memo = MagicMock()

    server = ManagementSocketServer(memo)

    # Test empty command
    result = await server._process_command("")
    assert "error" in result

    # Test unknown command
    result = await server._process_command("unknown")
    assert "error" in result
    assert "Unknown command" in result["error"]

    # Test dump without target
    result = await server._process_command("dump")
    assert "error" in result
    assert "Missing command name" in result["error"]


# =============================================================================
# Socket Server Tests
# =============================================================================


@pytest.mark.asyncio
async def test_management_socket_server_socket_cleanup():
    """Test socket file cleanup on server startup."""
    reporter = get_test_reporter()

    with progress_context(
        "test_management_socket_server_socket_cleanup", reporter
    ) as progress:
        progress.phase("SETUP", "Creating mock memo and temporary socket")
        memo = MagicMock()

        # Use a temporary socket path
        with tempfile.TemporaryDirectory() as tmpdir:
            socket_path = os.path.join(tmpdir, "test.sock")

            progress.phase("PRECONDITION", "Creating dummy socket file")
            # Create a dummy socket file
            Path(socket_path).touch()
            assert Path(socket_path).exists()

            progress.phase("SERVER_START", "Starting management socket server")
            # Start server (should clean up existing socket)
            server_task = asyncio.create_task(
                run_management_socket_server(memo, socket_path)
            )

            try:
                progress.phase("INITIALIZATION", "Waiting for server initialization")
                # Give server time to start
                await asyncio.sleep(0.1)

                progress.phase("VALIDATION", "Testing socket cleanup and connectivity")
                # Socket should still exist (server recreated it)
                assert Path(socket_path).exists()

                # Test basic connectivity
                client_socket = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
                client_socket.connect(socket_path)
                client_socket.close()

                reporter.debug("Socket connectivity test successful")

            finally:
                progress.phase("CLEANUP", "Stopping server task")
                server_task.cancel()
                try:
                    await server_task
                except asyncio.CancelledError:
                    pass


# =============================================================================
# StateSerializer Tests
# =============================================================================


def test_state_serializer_get_configmap_name():
    """Test _get_configmap_name method with various memo states."""
    from haproxy_template_ic.__main__ import CliOptions

    # Test with valid cli_options
    memo = MagicMock()
    memo.cli_options = CliOptions(
        configmap_name="test-config",
        healthz_port=8080,
        verbose=1,
        socket_path="/tmp/test.sock",
        metrics_port=9090,
        structured_logging=False,
        tracing_enabled=False,
    )

    serializer = StateSerializer(memo)
    assert serializer._get_configmap_name() == "test-config"

    # Test with None cli_options
    memo.cli_options = None
    assert serializer._get_configmap_name() is None

    # Test with missing cli_options attribute
    delattr(memo, "cli_options")
    assert serializer._get_configmap_name() is None


def test_state_serializer_serialize_cli_options():
    """Test _serialize_cli_options method edge cases."""

    # Test with missing cli_options attribute
    memo = MagicMock()
    delattr(memo, "cli_options")

    serializer = StateSerializer(memo)
    result = serializer._serialize_cli_options()
    assert result == {}

    # Test with None cli_options
    memo.cli_options = None
    result = serializer._serialize_cli_options()
    assert result == {}


def test_state_serializer_serialize_config_with_template_source():
    """Test _serialize_config method with maps."""
    memo = MagicMock()

    memo.config = config_from_dict(
        {
            "pod_selector": {"match_labels": {"app": "test"}},
            "haproxy_config": {"template": "global\n    daemon"},
            "watched_resources": {},
            "maps": {
                "/test/map": {"template": "test template"},
            },
        }
    )

    serializer = StateSerializer(memo)
    result = serializer._serialize_config()

    assert result["maps"]["/test/map"]["template_source"] == "test template"

    # Add another map to the config
    memo.config.maps["/test/map2"] = MapConfig(template="test template 2")

    result = serializer._serialize_config()
    assert result["maps"]["/test/map"]["template_source"] == "test template"
    assert result["maps"]["/test/map2"]["template_source"] == "test template 2"


def test_state_serializer_serialize_haproxy_config_context():
    """Test _serialize_haproxy_config_context method edge cases."""
    memo = MagicMock()

    # Test with missing haproxy_config_context
    delattr(memo, "haproxy_config_context")

    serializer = StateSerializer(memo)
    result = serializer._serialize_haproxy_config_context()
    assert result == {
        "rendered_maps": {},
        "rendered_config": None,
        "rendered_certificates": {},
    }

    # Test with None haproxy_config_context
    memo.haproxy_config_context = None
    result = serializer._serialize_haproxy_config_context()
    assert result == {
        "rendered_maps": {},
        "rendered_config": None,
        "rendered_certificates": {},
    }


def test_state_serializer_serialize_haproxy_config_context_with_rendered_config():
    """Test _serialize_haproxy_config_context method with rendered config."""
    from haproxy_template_ic.config_models import (
        HAProxyConfigContext,
    )

    memo = MagicMock()

    # Create a real rendered config
    rendered_config = RenderedConfig(content="global\n    daemon")

    # Create HAProxyConfigContext with rendered config
    memo.haproxy_config_context = HAProxyConfigContext(
        config=config_from_dict(
            {
                "pod_selector": {"match_labels": {"app": "test"}},
                "haproxy_config": {"template": "global\n    daemon"},
            }
        ),
        template_context=TemplateContext(),
        rendered_maps=[],
        rendered_config=rendered_config,
    )

    serializer = StateSerializer(memo)
    result = serializer._serialize_haproxy_config_context()

    assert result["rendered_maps"] == {}
    assert result["rendered_config"] is not None
    assert result["rendered_config"]["content"] == "global\n    daemon"


def test_state_serializer_serialize_haproxy_config_context_with_rendered_certificates():
    """Test _serialize_haproxy_config_context method with rendered certificates."""
    from haproxy_template_ic.config_models import (
        HAProxyConfigContext,
    )

    memo = MagicMock()

    # Create a real rendered certificate
    rendered_certificate = RenderedCertificate(
        path="/test/cert", content="cert content"
    )

    # Create HAProxyConfigContext with rendered certificate
    memo.haproxy_config_context = HAProxyConfigContext(
        config=config_from_dict(
            {
                "pod_selector": {"match_labels": {"app": "test"}},
                "haproxy_config": {"template": "global\n    daemon"},
            }
        ),
        template_context=TemplateContext(),
        rendered_maps=[],
        rendered_config=None,
        rendered_certificates=[rendered_certificate],
    )

    serializer = StateSerializer(memo)
    result = serializer._serialize_haproxy_config_context()

    assert result["rendered_maps"] == {}
    assert result["rendered_config"] is None
    assert result["rendered_certificates"] is not None
    assert "/test/cert" in result["rendered_certificates"]
    assert result["rendered_certificates"]["/test/cert"]["name"] == "/test/cert"
    assert result["rendered_certificates"]["/test/cert"]["content"] == "cert content"
    # Note: certificate_config_name field was removed in new model
    # assert (
    #     result["rendered_certificates"]["test-cert"]["certificate_config_name"]
    #     == "test-cert"
    # )


def test_state_serializer_serialize_indices_with_actual_indices():
    """Test _serialize_indices method with real indices that have items method."""
    memo = MagicMock()

    # Create real index-like objects with items method
    memo.pods_index = {"key1": "value1", "key2": "value2"}
    memo.services_index = {"svc1": "value1"}
    memo._private_index = {"should": "not appear"}  # Should be ignored (starts with _)
    memo.not_an_index = "string value"  # Should be ignored (no items method)

    serializer = StateSerializer(memo)
    result = serializer._serialize_indices()

    # _serialize_indices returns the indices dict directly
    assert "pods_index" in result
    assert "services_index" in result
    assert "_private_index" not in result
    assert "not_an_index" not in result
    assert result["pods_index"] == {"key1": "value1", "key2": "value2"}


def test_state_serializer_serialize_indices_empty():
    """Test _serialize_indices method with no indices."""
    memo = MagicMock()

    # Only add non-index attributes
    memo.some_attr = "value"
    memo._private_attr = "private"

    serializer = StateSerializer(memo)
    result = serializer._serialize_indices()

    # _serialize_indices returns the indices dict directly
    assert result == {}


def test_state_serializer_serialize_exception_handling():
    """Test StateSerializer.serialize method exception handling."""
    memo = MagicMock()

    # Mock memo to raise exception during serialization
    def failing_config():
        raise RuntimeError("Simulated serialization error")

    serializer = StateSerializer(memo)
    serializer._serialize_config = failing_config

    result = serializer.serialize()
    assert "error" in result
    assert "Failed to serialize state" in result["error"]
    assert "metadata" in result


# =============================================================================
# Enhanced Command Processing Tests
# =============================================================================


@pytest.mark.asyncio
async def test_process_command_dump_config():
    """Test dump config command specifically."""
    memo = MagicMock()
    memo.haproxy_config_context = HAProxyConfigContext(
        config=config_from_dict(
            {
                "pod_selector": {"match_labels": {"app": "test"}},
                "haproxy_config": {"template": "global\n    daemon"},
            }
        ),
        template_context=TemplateContext(),
        rendered_maps=[
            RenderedMap(
                path="/test/map",
                content="test content",
                map_config=MapConfig(template="test"),
            )
        ],
    )

    server = ManagementSocketServer(memo)
    result = await server._process_command("dump config")

    assert "haproxy_config_context" in result
    assert "/test/map" in result["haproxy_config_context"]["rendered_maps"]


@pytest.mark.asyncio
async def test_process_command_dump_config_empty():
    """Test dump config command with no config context."""
    memo = MagicMock()
    memo.haproxy_config_context = None

    server = ManagementSocketServer(memo)
    result = await server._process_command("dump config")

    assert result == {
        "haproxy_config_context": {
            "rendered_maps": {},
            "rendered_config": None,
            "rendered_certificates": {},
        }
    }


@pytest.mark.asyncio
async def test_process_command_dump_config_with_rendered_config():
    """Test dump config command with rendered HAProxy config."""

    memo = MagicMock()

    # Create a real rendered config
    rendered_config = RenderedConfig(content="global\n    daemon")

    memo.haproxy_config_context = HAProxyConfigContext(
        config=config_from_dict(
            {
                "pod_selector": {"match_labels": {"app": "test"}},
                "haproxy_config": {"template": "global\n    daemon"},
            }
        ),
        template_context=TemplateContext(),
        rendered_config=rendered_config,
        rendered_maps=[],
    )

    server = ManagementSocketServer(memo)
    result = await server._process_command("dump config")

    assert "haproxy_config_context" in result
    assert result["haproxy_config_context"]["rendered_maps"] == {}
    assert result["haproxy_config_context"]["rendered_config"] is not None
    assert (
        result["haproxy_config_context"]["rendered_config"]["content"]
        == "global\n    daemon"
    )


@pytest.mark.asyncio
async def test_process_command_dump_config_with_rendered_certificates():
    """Test dump config command with rendered certificates."""

    memo = MagicMock()

    # Create a real rendered certificate
    rendered_certificate = RenderedCertificate(
        path="/test/cert", content="cert content"
    )

    memo.haproxy_config_context = HAProxyConfigContext(
        config=config_from_dict(
            {
                "pod_selector": {"match_labels": {"app": "test"}},
                "haproxy_config": {"template": "global\n    daemon"},
            }
        ),
        template_context=TemplateContext(),
        rendered_certificates=[rendered_certificate],
        rendered_maps=[],
        rendered_config=None,
    )

    server = ManagementSocketServer(memo)
    result = await server._process_command("dump config")

    assert "haproxy_config_context" in result
    assert result["haproxy_config_context"]["rendered_maps"] == {}
    assert result["haproxy_config_context"]["rendered_config"] is None
    assert result["haproxy_config_context"]["rendered_certificates"] is not None
    assert "/test/cert" in result["haproxy_config_context"]["rendered_certificates"]
    assert (
        result["haproxy_config_context"]["rendered_certificates"]["/test/cert"]["name"]
        == "/test/cert"
    )
    assert (
        result["haproxy_config_context"]["rendered_certificates"]["/test/cert"][
            "content"
        ]
        == "cert content"
    )


@pytest.mark.asyncio
async def test_process_command_dump_unknown_subcommand():
    """Test dump command with unknown subcommand."""
    memo = MagicMock()

    server = ManagementSocketServer(memo)
    result = await server._process_command("dump unknown")

    assert "error" in result
    assert "Unknown dump command: unknown" in result["error"]
    assert "Available: all, indices, config" in result["error"]


@pytest.mark.asyncio
async def test_dump_indices_basic():
    """Test _dump_indices method with normal indices."""
    memo = MagicMock()

    # Add actual index attributes
    memo.pods_index = {"key": "value"}
    memo.services_index = {"svc": "data"}
    memo._private_index = {"private": "data"}  # Should be ignored
    memo.not_index = "string"  # Should be ignored

    server = ManagementSocketServer(memo)
    result = server._dump_indices()

    assert "indices" in result
    assert "pods_index" in result["indices"]
    assert "services_index" in result["indices"]
    assert "_private_index" not in result["indices"]
    assert "not_index" not in result["indices"]


# =============================================================================
# Socket Server Error Handling Tests
# =============================================================================


@pytest.mark.asyncio
async def test_management_socket_server_handle_client_empty_command():
    """Test client handler with empty command data."""
    from haproxy_template_ic.__main__ import CliOptions

    memo = MagicMock()
    # Provide actual config to avoid JSON serialization issues
    memo.config = config_from_dict(
        {
            "pod_selector": {"match_labels": {"app": "test"}},
            "haproxy_config": {"template": "global\n    daemon"},
        }
    )
    memo.cli_options = CliOptions(
        configmap_name="test-config",
        healthz_port=8080,
        verbose=1,
        socket_path="/tmp/test.sock",
        metrics_port=9090,
        structured_logging=False,
        tracing_enabled=False,
    )
    memo.haproxy_config_context = HAProxyConfigContext(
        config=memo.config,
        template_context=TemplateContext(),
    )
    memo.config_reload_flag = MagicMock()
    memo.stop_flag = MagicMock()

    server = ManagementSocketServer(memo)

    # Mock reader/writer
    reader = MagicMock()
    writer = MagicMock()

    # Mock empty read
    reader.read = AsyncMock(return_value=b"")
    writer.write = MagicMock()
    writer.drain = AsyncMock()
    writer.close = MagicMock()
    writer.wait_closed = AsyncMock()

    await server._handle_client(reader, writer)

    # Should use default "dump all" command
    writer.write.assert_called()
    written_data = writer.write.call_args[0][0]
    response = json.loads(written_data.decode("utf-8"))
    assert "config" in response  # dump all response


@pytest.mark.asyncio
async def test_management_socket_server_handle_client_exception():
    """Test client handler with exception during processing."""
    memo = MagicMock()
    server = ManagementSocketServer(memo)

    # Mock reader/writer
    reader = MagicMock()
    writer = MagicMock()

    # Mock reader to raise exception
    reader.read = AsyncMock(side_effect=RuntimeError("Simulated error"))
    writer.write = MagicMock()
    writer.drain = AsyncMock()
    writer.close = MagicMock()
    writer.wait_closed = AsyncMock()

    await server._handle_client(reader, writer)

    # Should write error response
    writer.write.assert_called()


@pytest.mark.asyncio
async def test_management_socket_server_handle_client_write_exception():
    """Test client handler with exception during response writing."""
    memo = MagicMock()
    server = ManagementSocketServer(memo)

    # Mock reader/writer
    reader = MagicMock()
    writer = MagicMock()

    reader.read = AsyncMock(return_value=b"dump all")
    writer.write = MagicMock(side_effect=RuntimeError("Write error"))
    writer.drain = AsyncMock(side_effect=RuntimeError("Drain error"))
    writer.close = MagicMock()
    writer.wait_closed = AsyncMock()

    await server._handle_client(reader, writer)

    # Should handle exception gracefully (logged internally)


@pytest.mark.asyncio
async def test_management_socket_server_cleanup():
    """Test server cleanup method."""
    memo = MagicMock()

    with tempfile.TemporaryDirectory() as tmpdir:
        socket_path = os.path.join(tmpdir, "test.sock")
        server = ManagementSocketServer(memo, socket_path)

        # Create a mock server
        mock_server = MagicMock()
        server.server = mock_server

        # Create socket file
        Path(socket_path).touch()
        assert Path(socket_path).exists()

        # Test cleanup
        server._cleanup()

        mock_server.close.assert_called_once()
        assert not Path(socket_path).exists()


@pytest.mark.asyncio
async def test_run_management_socket_server_exception():
    """Test run_management_socket_server function exception handling."""
    memo = MagicMock()

    # Mock ManagementSocketServer.run to raise exception
    with tempfile.TemporaryDirectory() as tmpdir:
        socket_path = os.path.join(tmpdir, "test.sock")

        # Create server that will fail
        server = ManagementSocketServer(memo, socket_path)

        async def failing_run():
            raise RuntimeError("Simulated server error")

        server.run = failing_run

        # Patch ManagementSocketServer constructor
        import haproxy_template_ic.management_socket as ms

        original_constructor = ms.ManagementSocketServer

        def mock_constructor(*args, **kwargs):
            return server

        ms.ManagementSocketServer = mock_constructor

        try:
            await run_management_socket_server(memo, socket_path)
            # Should not raise exception but log error (internally)
        finally:
            ms.ManagementSocketServer = original_constructor


# =============================================================================
# Async Mock Helper
# =============================================================================


class AsyncMock:
    """Helper class for async mocking."""

    def __init__(self, return_value=None, side_effect=None):
        self.return_value = return_value
        self.side_effect = side_effect
        self.call_count = 0
        self.call_args_list = []

    async def __call__(self, *args, **kwargs):
        self.call_count += 1
        self.call_args_list.append((args, kwargs))

        if self.side_effect:
            if isinstance(self.side_effect, Exception):
                raise self.side_effect
            return self.side_effect(*args, **kwargs)

        return self.return_value


# =============================================================================
# Additional Coverage Tests
# =============================================================================


@pytest.mark.asyncio
async def test_management_socket_server_handle_client_unicode_command():
    """Test client handler with unicode command data."""
    from haproxy_template_ic.__main__ import CliOptions

    memo = MagicMock()
    memo.config = config_from_dict(
        {
            "pod_selector": {"match_labels": {"app": "test"}},
            "haproxy_config": {"template": "global\n    daemon"},
        }
    )
    memo.cli_options = CliOptions(
        configmap_name="unicode-test",
        healthz_port=8080,
        verbose=1,
        socket_path="/tmp/test.sock",
        metrics_port=9090,
        structured_logging=False,
        tracing_enabled=False,
    )
    memo.haproxy_config_context = HAProxyConfigContext(
        config=memo.config,
        template_context=TemplateContext(),
    )
    memo.config_reload_flag = MagicMock()
    memo.stop_flag = MagicMock()

    server = ManagementSocketServer(memo)

    # Mock reader/writer
    reader = MagicMock()
    writer = MagicMock()

    # Unicode command
    reader.read = AsyncMock(return_value="dump all ❄️".encode("utf-8"))
    writer.write = MagicMock()
    writer.drain = AsyncMock()
    writer.close = MagicMock()
    writer.wait_closed = AsyncMock()

    await server._handle_client(reader, writer)

    # Should handle unicode gracefully and return dump all response
    writer.write.assert_called()
    written_data = writer.write.call_args[0][0]
    response = json.loads(written_data.decode("utf-8"))
    assert "config" in response


def test_state_serializer_serialize_metadata():
    """Test _serialize_metadata method with different memo states."""
    from haproxy_template_ic.__main__ import CliOptions

    memo = MagicMock()
    memo.cli_options = CliOptions(
        configmap_name="metadata-test",
        healthz_port=8080,
        verbose=1,
        socket_path="/tmp/test.sock",
        metrics_port=9090,
        structured_logging=False,
        tracing_enabled=False,
    )
    memo.config_reload_flag = MagicMock()
    memo.stop_flag = MagicMock()

    serializer = StateSerializer(memo)
    result = serializer._serialize_metadata()

    assert result["configmap_name"] == "metadata-test"
    assert result["has_config_reload_flag"] is True
    assert result["has_stop_flag"] is True

    # Test with missing flags
    delattr(memo, "config_reload_flag")
    delattr(memo, "stop_flag")

    result = serializer._serialize_metadata()
    assert result["has_config_reload_flag"] is False
    assert result["has_stop_flag"] is False


@pytest.mark.asyncio
async def test_management_socket_server_run_cancellation():
    """Test server run method handles cancellation properly."""
    memo = MagicMock()

    with tempfile.TemporaryDirectory() as tmpdir:
        socket_path = os.path.join(tmpdir, "test.sock")
        server = ManagementSocketServer(memo, socket_path)

        # Mock start_unix_server to return a server that raises CancelledError
        mock_server = MagicMock()

        async def mock_serve_forever():
            # Simulate some work before cancellation
            await asyncio.sleep(0.01)
            raise asyncio.CancelledError("Test cancellation")

        mock_server.serve_forever = mock_serve_forever
        mock_server.__aenter__ = AsyncMock(return_value=mock_server)
        mock_server.__aexit__ = AsyncMock()

        async def mock_start_unix_server(*args, **kwargs):
            return mock_server

        with patch("asyncio.start_unix_server", side_effect=mock_start_unix_server):
            with pytest.raises(asyncio.CancelledError):
                await server.run()

        # Should log cancellation message (internally)


def test_state_serializer_serialize_config_without_maps():
    """Test _serialize_config method with config that has no maps."""
    memo = MagicMock()
    memo.config = config_from_dict(
        {
            "pod_selector": {"match_labels": {"app": "test"}},
            "haproxy_config": {"template": "global\n    daemon"},
            "watched_resources": {
                "pods": {
                    "api_version": "v1",
                    "kind": "Pod",
                    "enable_validation_webhook": False,
                }
            },
            "maps": {},  # Empty maps
        }
    )

    serializer = StateSerializer(memo)
    result = serializer._serialize_config()

    assert result["pod_selector"]["match_labels"] == {"app": "test"}
    assert "pods" in result["watched_resources"]
    assert result["maps"] == {}


@pytest.mark.asyncio
async def test_process_command_with_extra_spaces():
    """Test command processing with extra whitespace."""
    memo = MagicMock()
    memo.config = config_from_dict(
        {
            "pod_selector": {"match_labels": {"app": "test"}},
            "haproxy_config": {"template": "global\n    daemon"},
        }
    )

    server = ManagementSocketServer(memo)

    # Test command with extra spaces
    result = await server._process_command("  dump   all  ")
    assert "config" in result


# =============================================================================
# Additional Coverage Tests
# =============================================================================


def test_dataclass_json_encoder_with_non_dataclass():
    """Test DataclassJSONEncoder with non-dataclass object."""

    @dataclass
    class TestDataclass:
        value: str

    encoder = DataclassJSONEncoder()

    # Test with dataclass
    result = encoder.default(TestDataclass("test"))
    assert result == {"value": "test"}

    # Test with non-dataclass (should raise TypeError)
    with pytest.raises(TypeError):
        encoder.default({"not": "dataclass"})


def test_dump_indices_with_serialization_error():
    """Test _dump_indices handling of serialization errors."""
    memo = MagicMock()

    # Create a problematic attribute that will cause serialization error (must end with _index)
    class ProblematicIndex:
        def items(self):
            raise ValueError("Serialization error")

    memo.test_index = ProblematicIndex()

    server = ManagementSocketServer(memo)
    result = server._dump_indices()

    # Should handle the error gracefully
    assert "indices" in result
    assert "test_index" in result["indices"]
    assert "error:" in result["indices"]["test_index"]


def test_state_serializer_with_index_serialization_error():
    """Test StateSerializer handling of index serialization errors."""
    memo = MagicMock()

    # Create a problematic index that will cause serialization error
    class ProblematicIndex:
        def items(self):
            raise ValueError("Iteration error")

    # Mock the dir() function to return our test_index
    with patch("builtins.dir", return_value=["test_index"]):
        # Set the problematic index as an attribute
        memo.test_index = ProblematicIndex()

        serializer = StateSerializer(memo)
        result = serializer._serialize_indices()

        # Should handle the error gracefully
        assert "test_index" in result
        assert result["test_index"] == "serialization_error"


@pytest.mark.asyncio
async def test_get_command_with_invalid_collection_type():
    """Test get command with invalid collection type."""
    memo = MagicMock()
    memo.config = config_from_dict(
        {
            "pod_selector": {"match_labels": {"app": "test"}},
            "haproxy_config": {"template": "global\n    daemon"},
        }
    )

    server = ManagementSocketServer(memo)

    # Test with invalid collection type
    result = await server._process_command("get invalid_type some_id")
    assert "error" in result
    assert "Unknown collection type" in result["error"]


@pytest.mark.asyncio
async def test_get_command_missing_args():
    """Test get command with missing arguments."""
    memo = MagicMock()
    memo.config = config_from_dict(
        {
            "pod_selector": {"match_labels": {"app": "test"}},
            "haproxy_config": {"template": "global\n    daemon"},
        }
    )

    server = ManagementSocketServer(memo)

    # Test with missing arguments
    result = await server._process_command("get maps")
    assert "error" in result
    assert "Missing arguments" in result["error"]


@pytest.mark.asyncio
async def test_get_command_for_all_collection_types():
    """Test get command for all collection types with found and not found cases."""
    memo = MagicMock()
    # Create config with all collection types
    memo.config = config_from_dict(
        {
            "pod_selector": {"match_labels": {"app": "test"}},
            "haproxy_config": {"template": "global\n    daemon"},
            "maps": {"/test/map": {"template": "test"}},
            "watched_resources": {
                "pods": {
                    "api_version": "v1",
                    "kind": "Pod",
                    "enable_validation_webhook": False,
                }
            },
            "template_snippets": {
                "test-snippet": {"name": "test-snippet", "template": "snippet"}
            },
            "certificates": {"/test/cert": {"template": "cert"}},
        }
    )

    server = ManagementSocketServer(memo)

    # Test maps - found
    result = await server._process_command("get maps /test/map")
    assert "result" in result
    assert result["result"]["path"] == "/test/map"

    # Test maps - not found
    result = await server._process_command("get maps /nonexistent")
    assert "error" in result
    assert "Map not found" in result["error"]

    # Test watched_resources - found
    result = await server._process_command("get watched_resources pods")
    assert "result" in result
    assert result["result"]["id"] == "pods"

    # Test watched_resources - not found
    result = await server._process_command("get watched_resources nonexistent")
    assert "error" in result
    assert "Watch resource not found" in result["error"]

    # Test template_snippets - found
    result = await server._process_command("get template_snippets test-snippet")
    assert "result" in result
    assert result["result"]["name"] == "test-snippet"

    # Test template_snippets - not found
    result = await server._process_command("get template_snippets nonexistent")
    assert "error" in result
    assert "Template snippet not found" in result["error"]

    # Test certificates - found
    result = await server._process_command("get certificates /test/cert")
    assert "result" in result
    assert result["result"]["path"] == "/test/cert"

    # Test certificates - not found
    result = await server._process_command("get certificates nonexistent")
    assert "error" in result
    assert "Certificate not found" in result["error"]


@pytest.mark.asyncio
async def test_management_socket_server_with_general_exception():
    """Test ManagementSocketServer run method with general exception."""
    mock_memo = MagicMock()
    server = ManagementSocketServer(mock_memo)

    mock_server = MagicMock()

    async def mock_serve_forever():
        # Simulate a general exception
        raise RuntimeError("General server error")

    mock_server.serve_forever = mock_serve_forever
    mock_server.__aenter__ = AsyncMock(return_value=mock_server)
    mock_server.__aexit__ = AsyncMock()

    async def mock_start_unix_server(*args, **kwargs):
        return mock_server

    with patch("asyncio.start_unix_server", side_effect=mock_start_unix_server):
        # Should not raise, but log the error
        await server.run()

    # Should log the error (internally)
