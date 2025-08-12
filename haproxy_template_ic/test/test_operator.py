"""
Tests for haproxy_template_ic.operator module.

This module contains tests for Kubernetes operator functionality focusing on
critical paths and edge cases that are likely to detect bugs.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
import yaml
import kopf
import asyncio

from haproxy_template_ic.operator import (
    load_config_from_configmap,
    fetch_configmap,
    trigger_reload,
    handle_configmap_change,
    update_resource_index,
    create_operator_memo,
    render_haproxy_templates,
)
from haproxy_template_ic.config import (
    Config,
    MapConfig,
    HAProxyConfigContext,
    RenderedMap,
)
from jinja2 import Template


# =============================================================================
# Configuration Management Tests
# =============================================================================


@pytest.mark.asyncio
async def test_load_config_from_configmap_success():
    """Test successful config loading from ConfigMap."""
    config_data = {"pod_selector": "app=test"}
    configmap = {"data": {"config": yaml.dump(config_data, Dumper=yaml.CDumper)}}

    result = await load_config_from_configmap(configmap)

    assert isinstance(result, Config)
    assert result.pod_selector == "app=test"


@pytest.mark.asyncio
async def test_load_config_from_configmap_invalid_yaml():
    """Test config loading with invalid YAML."""
    configmap = {"data": {"config": "invalid: yaml: content:"}}

    with pytest.raises(Exception):
        await load_config_from_configmap(configmap)


@pytest.mark.asyncio
async def test_fetch_configmap_failure():
    """Test ConfigMap fetching failure."""
    with patch("kr8s.objects.ConfigMap.get", new_callable=AsyncMock) as mock_get:
        mock_get.side_effect = Exception("Connection failed")

        with pytest.raises(kopf.TemporaryError) as exc_info:
            await fetch_configmap("test-config", "test-namespace")

        assert "Failed to retrieve ConfigMap" in str(exc_info.value)


@pytest.mark.asyncio
async def test_load_config_from_configmap_parsing_failure():
    """Test ConfigMap loading failure."""
    configmap = {"data": {"config": "invalid"}}

    with patch("haproxy_template_ic.operator.config_from_dict") as mock_config:
        mock_config.side_effect = Exception("Parse error")

        with pytest.raises(Exception) as exc_info:
            await load_config_from_configmap(configmap)

        assert "Parse error" in str(exc_info.value)


# =============================================================================
# Event Handler Tests
# =============================================================================


def test_trigger_reload():
    """Test reload trigger functionality."""
    memo = MagicMock()
    memo.config_reload_flag = MagicMock()
    memo.stop_flag = MagicMock()

    trigger_reload(memo)

    memo.config_reload_flag.set_result.assert_called_once_with(None)
    memo.stop_flag.set_result.assert_called_once_with(None)


@pytest.mark.asyncio
async def test_handle_configmap_change_with_change():
    """Test ConfigMap change handler when change is detected."""
    memo = MagicMock()
    memo.config = Config(pod_selector="app=old")
    event = {
        "object": {
            "data": {
                "config": yaml.dump({"pod_selector": "app=new"}, Dumper=yaml.CDumper)
            }
        }
    }
    logger = MagicMock()

    with patch("haproxy_template_ic.operator.load_config_from_configmap") as mock_load:
        with patch("haproxy_template_ic.operator.trigger_reload") as mock_trigger:
            mock_load.return_value = Config(pod_selector="app=new")

            await handle_configmap_change(
                memo, event, "test-config", "MODIFIED", logger
            )

            # Should trigger reload since config changed
            mock_trigger.assert_called_once_with(memo)


@pytest.mark.asyncio
async def test_update_resource_index():
    """Test resource index update functionality."""
    param = "pods"
    namespace = "default"
    name = "test-pod"
    spec = {"name": "test-pod", "host": "10.0.1.5", "port": "80"}
    logger = MagicMock()

    result = await update_resource_index(param, namespace, name, spec, logger)

    assert result == {(namespace, name): spec}
    logger.debug.assert_called_once_with(
        f"📝 Updating index {param} for {namespace}/{name}..."
    )


# =============================================================================
# Template Rendering Tests
# =============================================================================


@pytest.mark.asyncio
async def test_render_haproxy_templates_success():
    """Test successful template rendering."""
    memo = MagicMock()
    memo.config = MagicMock()
    memo.config.maps = {
        "/etc/haproxy/maps/backend.map": MapConfig(
            path="/etc/haproxy/maps/backend.map",
            template=Template(
                "server {{ resources.name }} {{ resources.host }}:{{ resources.port }}"
            ),
        )
    }
    memo.haproxy_config_context = HAProxyConfigContext()
    indices = {"name": "server1", "host": "10.0.1.5", "port": "80"}
    logger = MagicMock()

    await render_haproxy_templates(memo, indices, logger)

    # Check that rendered map was added
    assert "/etc/haproxy/maps/backend.map" in memo.haproxy_config_context.rendered_maps
    rendered_map = memo.haproxy_config_context.rendered_maps[
        "/etc/haproxy/maps/backend.map"
    ]
    assert isinstance(rendered_map, RenderedMap)
    assert "server server1 10.0.1.5:80" in rendered_map.content


@pytest.mark.asyncio
async def test_render_haproxy_templates_jinja_error():
    """Test template rendering with Jinja error."""
    memo = MagicMock()
    memo.config = MagicMock()
    memo.config.maps = {
        "/etc/haproxy/maps/backend.map": MapConfig(
            path="/etc/haproxy/maps/backend.map",
            template=Template("server {{ undefined_variable.invalid_attr }}"),
        )
    }
    memo.haproxy_config_context = HAProxyConfigContext()
    indices = {"name": "server1"}
    logger = MagicMock()

    await render_haproxy_templates(memo, indices, logger)

    # Should log error but not crash
    logger.error.assert_called_once()
    assert "Failed to render template" in logger.error.call_args[0][0]


# =============================================================================
# Operator State Management Tests
# =============================================================================


def test_create_operator_memo():
    """Test operator memo creation."""
    from haproxy_template_ic.__main__ import CliOptions

    cli_options = CliOptions(
        configmap_name="test-config",
        healthz_port=8080,
        verbose=1,
        socket_path="/run/haproxy-template-ic/management.sock",
    )

    memo, loop, stop_flag = create_operator_memo(cli_options)

    assert memo.cli_options == cli_options
    assert memo.cli_options.configmap_name == "test-config"
    assert memo.cli_options.socket_path == "/run/haproxy-template-ic/management.sock"
    assert hasattr(memo, "config_reload_flag")
    assert hasattr(memo, "stop_flag")
    assert hasattr(memo, "haproxy_config_context")
    assert isinstance(memo.haproxy_config_context, HAProxyConfigContext)
    assert isinstance(loop, asyncio.AbstractEventLoop)
    assert isinstance(stop_flag, asyncio.Future)
