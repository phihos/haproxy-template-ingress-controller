"""
Tests for haproxy_template_ic.management_socket module.

This module contains tests for management socket functionality focusing on
critical paths and edge cases that are likely to detect bugs.
"""

import pytest
from unittest.mock import MagicMock
import socket
import tempfile
import os
import asyncio
from pathlib import Path

from haproxy_template_ic.management_socket import (
    serialize_state,
    ManagementSocketServer,
    run_management_socket_server,
)
from haproxy_template_ic.config import (
    Config,
    MapConfig,
    HAProxyConfigContext,
    RenderedMap,
    WatchResourceConfig,
)
from jinja2 import Template


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
    assert result["config"]["watch_resources"] == {}
    assert result["config"]["maps"] == {}


def test_serialize_state_with_full_config():
    """Test state serialization with complete configuration."""
    from haproxy_template_ic.__main__ import CliOptions

    memo = MagicMock()
    memo.config = Config(
        pod_selector="app=haproxy",
        watch_resources={
            "pods": WatchResourceConfig(kind="Pod", group="", version="v1"),
            "services": WatchResourceConfig(kind="Service", group="", version="v1"),
        },
        maps={
            "/etc/haproxy/maps/backend.map": MapConfig(
                path="/etc/haproxy/maps/backend.map",
                template=Template(
                    "server {{ resources.name }} {{ resources.host }}:{{ resources.port }}"
                ),
            )
        },
    )
    memo.haproxy_config_context = HAProxyConfigContext()
    memo.haproxy_config_context.rendered_maps = {
        "/etc/haproxy/maps/backend.map": RenderedMap(
            path="/etc/haproxy/maps/backend.map",
            content="server web-pod 10.0.1.5:80",
            map_config=MapConfig(
                path="/etc/haproxy/maps/backend.map",
                template=Template(
                    "server {{ resources.name }} {{ resources.host }}:{{ resources.port }}"
                ),
            ),
        )
    }
    memo.cli_options = CliOptions(
        configmap_name="haproxy-config",
        healthz_port=8080,
        verbose=1,
        socket_path="/run/haproxy-template-ic/management.sock",
    )
    memo.config_reload_flag = MagicMock()
    memo.stop_flag = MagicMock()

    # Mock indices
    memo.pods_index = {
        ("default", "web-pod"): {"name": "web-pod", "host": "10.0.1.5", "port": "80"}
    }

    result = serialize_state(memo)

    assert result["config"]["pod_selector"] == "app=haproxy"
    assert "pods" in result["config"]["watch_resources"]
    assert "services" in result["config"]["watch_resources"]
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
    memo.config = Config(pod_selector="app=test")
    logger = MagicMock()

    server = ManagementSocketServer(memo, logger)
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
    logger = MagicMock()

    server = ManagementSocketServer(memo, logger)
    result = await server._process_command("dump indices")

    assert "indices" in result
    assert "pods_index" in result["indices"]
    assert "services_index" in result["indices"]


@pytest.mark.asyncio
async def test_process_management_command_errors():
    """Test error handling in command processing."""
    memo = MagicMock()
    logger = MagicMock()

    server = ManagementSocketServer(memo, logger)

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
    memo = MagicMock()
    logger = MagicMock()

    # Use a temporary socket path
    with tempfile.TemporaryDirectory() as tmpdir:
        socket_path = os.path.join(tmpdir, "test.sock")

        # Create a dummy socket file
        Path(socket_path).touch()
        assert Path(socket_path).exists()

        # Start server (should clean up existing socket)
        server_task = asyncio.create_task(
            run_management_socket_server(memo, logger, socket_path)
        )

        try:
            # Give server time to start
            await asyncio.sleep(0.1)

            # Socket should still exist (server recreated it)
            assert Path(socket_path).exists()

            # Test basic connectivity
            client_socket = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
            client_socket.connect(socket_path)
            client_socket.close()

        finally:
            server_task.cancel()
            try:
                await server_task
            except asyncio.CancelledError:
                pass
