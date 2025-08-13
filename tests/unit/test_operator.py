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
    setup_resource_watchers,
    initialize_configuration,
    run_operator_loop,
)
from haproxy_template_ic.config import (
    Config,
    MapConfig,
    PodSelector,
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
    config_data = {
        "pod_selector": {"match_labels": {"app": "test"}},
        "haproxy_config": "global\n    daemon",
    }
    configmap = {"data": {"config": yaml.dump(config_data, Dumper=yaml.CDumper)}}

    result = await load_config_from_configmap(configmap)

    assert isinstance(result, Config)
    assert result.pod_selector.match_labels == {"app": "test"}


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
    memo.config = Config(
        pod_selector=PodSelector(match_labels={"app": "old"}),
        haproxy_config=Template("global\n    daemon"),
    )
    event = {
        "object": {
            "data": {
                "config": yaml.dump(
                    {
                        "pod_selector": {"match_labels": {"app": "new"}},
                        "haproxy_config": "global\n    daemon",
                    },
                    Dumper=yaml.CDumper,
                )
            }
        }
    }
    logger = MagicMock()

    with patch("haproxy_template_ic.operator.load_config_from_configmap") as mock_load:
        with patch("haproxy_template_ic.operator.trigger_reload") as mock_trigger:
            mock_load.return_value = Config(
                pod_selector=PodSelector(match_labels={"app": "new"}),
                haproxy_config=Template("global\n    daemon"),
            )

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
    memo.config = Config(
        pod_selector=PodSelector(match_labels={"app": "test"}),
        haproxy_config=Template("global\n    daemon"),
        maps=[
            MapConfig(
                template=Template(
                    "server {{ resources.name }} {{ resources.host }}:{{ resources.port }}"
                ),
                path="/etc/haproxy/maps/backend.map",
            )
        ],
    )
    memo.haproxy_config_context = HAProxyConfigContext()
    indices = {"name": "server1", "host": "10.0.1.5", "port": "80"}
    logger = MagicMock()

    await render_haproxy_templates(memo, indices, logger)

    # Check that rendered map was added
    assert len(memo.haproxy_config_context.rendered_maps) == 1
    rendered_map = memo.haproxy_config_context.rendered_maps[0]
    assert isinstance(rendered_map, RenderedMap)
    assert rendered_map.path == "/etc/haproxy/maps/backend.map"
    assert "server server1 10.0.1.5:80" in rendered_map.content


@pytest.mark.asyncio
async def test_render_haproxy_templates_jinja_error():
    """Test template rendering with Jinja error."""
    memo = MagicMock()
    memo.config = Config(
        pod_selector=PodSelector(match_labels={"app": "test"}),
        haproxy_config=Template("global\n    daemon"),
        maps=[
            MapConfig(
                template=Template("server {{ undefined_variable.invalid_attr }}"),
                path="/etc/haproxy/maps/backend.map",
            )
        ],
    )
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


# =============================================================================
# Additional Coverage Tests for Missing Lines
# =============================================================================


@pytest.mark.asyncio
@patch("kopf.index")
@patch("kopf.on.event")
async def test_setup_resource_watchers(mock_event, mock_index):
    """Test setup_resource_watchers function."""
    from haproxy_template_ic.config import WatchResourceConfig, WatchResourceCollection

    # Create mock memo with watch resources
    memo = MagicMock()
    watch_resources = WatchResourceCollection(
        [
            WatchResourceConfig(kind="Pod", group="", version="v1", id="pods"),
            WatchResourceConfig(
                kind="Ingress", group="networking.k8s.io", version="v1", id="ingresses"
            ),
        ]
    )
    memo.config.watch_resources = watch_resources

    # Mock the decorators to return the original function
    mock_index.return_value = lambda func: func
    mock_event.return_value = lambda func: func

    logger = MagicMock()

    # Call the function
    await setup_resource_watchers(memo, logger)

    # Verify that kopf.index and kopf.on.event were called for each resource
    assert mock_index.call_count == 2
    assert mock_event.call_count == 2

    # Check the first resource (Pod without group/version)
    mock_index.assert_any_call("pod", id="pods", param="pods")
    mock_event.assert_any_call("pod", id="pods_event")

    # Check the second resource (Ingress with group/version)
    mock_index.assert_any_call(
        "ingress",
        id="ingresses",
        param="ingresses",
        group="networking.k8s.io",
        version="v1",
    )
    mock_event.assert_any_call(
        "ingress", id="ingresses_event", group="networking.k8s.io", version="v1"
    )


@pytest.mark.asyncio
@patch("haproxy_template_ic.operator.get_current_namespace")
@patch("haproxy_template_ic.operator.fetch_configmap")
@patch("haproxy_template_ic.operator.load_config_from_configmap")
@patch("haproxy_template_ic.operator.run_management_socket_server")
@patch("kopf.on.startup")
@patch("kopf.on.event")
@patch("asyncio.create_task")
async def test_initialize_configuration(
    mock_create_task,
    mock_event,
    mock_startup,
    mock_run_socket,
    mock_load_config,
    mock_fetch_configmap,
    mock_get_namespace,
):
    """Test initialize_configuration function."""
    from haproxy_template_ic.__main__ import CliOptions

    # Set up mocks
    mock_get_namespace.return_value = "test-namespace"
    mock_configmap = {"data": {"config": "test config"}}
    mock_fetch_configmap.return_value = mock_configmap
    mock_config = MagicMock()
    mock_load_config.return_value = mock_config
    mock_startup.return_value = lambda func: func
    mock_event.return_value = lambda func: func
    mock_task = MagicMock()
    mock_create_task.return_value = mock_task

    # Create test memo
    memo = MagicMock()
    cli_options = CliOptions(
        configmap_name="test-config",
        healthz_port=8080,
        verbose=1,
        socket_path="/test/socket",
    )
    memo.cli_options = cli_options

    logger = MagicMock()

    # Call the function
    await initialize_configuration(memo, logger)

    # Verify the calls
    mock_get_namespace.assert_called_once()
    mock_fetch_configmap.assert_called_once_with("test-config", "test-namespace")
    mock_load_config.assert_called_once_with(mock_configmap)
    assert memo.config == mock_config
    mock_startup.assert_called_once()
    mock_event.assert_called_once()
    mock_create_task.assert_called_once()
    assert memo.socket_server_task == mock_task

    logger.info.assert_any_call("⚙️ Initializing config from configmap test-config.")
    logger.info.assert_any_call("✅ Configuration initialized successfully.")


@patch("kopf.run")
@patch("kopf.on.startup")
@patch("haproxy_template_ic.operator.create_operator_memo")
def test_run_operator_loop_normal_shutdown(
    mock_create_memo, mock_startup, mock_kopf_run
):
    """Test run_operator_loop with normal shutdown."""
    from haproxy_template_ic.__main__ import CliOptions

    # Set up mocks
    cli_options = CliOptions(
        configmap_name="test-config",
        healthz_port=8080,
        verbose=1,
        socket_path="/test/socket",
    )

    memo = MagicMock()
    loop = MagicMock()
    stop_flag = MagicMock()

    # Mock config_reload_flag as not done (normal shutdown)
    memo.config_reload_flag.done.return_value = False

    mock_create_memo.return_value = (memo, loop, stop_flag)
    mock_startup.return_value = lambda func: func

    logger = MagicMock()

    # Call the function
    run_operator_loop(cli_options, logger)

    # Verify the calls
    mock_create_memo.assert_called_once_with(cli_options)
    mock_startup.assert_called_once()
    mock_kopf_run.assert_called_once_with(
        clusterwide=True,
        loop=loop,
        liveness_endpoint="http://0.0.0.0:8080/healthz",
        stop_flag=stop_flag,
        memo=memo,
    )

    # Should check config_reload_flag and exit
    memo.config_reload_flag.done.assert_called_once()
    logger.info.assert_called_with("👋 Operator shutdown complete.")


@patch("kopf.run")
@patch("kopf.on.startup")
@patch("haproxy_template_ic.operator.create_operator_memo")
def test_run_operator_loop_with_reload(mock_create_memo, mock_startup, mock_kopf_run):
    """Test run_operator_loop with config reload."""
    from haproxy_template_ic.__main__ import CliOptions

    # Set up mocks
    cli_options = CliOptions(
        configmap_name="test-config",
        healthz_port=8080,
        verbose=1,
        socket_path="/test/socket",
    )

    memo = MagicMock()
    loop = MagicMock()
    stop_flag = MagicMock()

    # Mock config_reload_flag as done (config reload scenario)
    # First call returns True (reload), second call returns False (exit)
    memo.config_reload_flag.done.side_effect = [True, False]

    mock_create_memo.return_value = (memo, loop, stop_flag)
    mock_startup.return_value = lambda func: func

    logger = MagicMock()

    # Call the function
    run_operator_loop(cli_options, logger)

    # Verify the calls - should be called twice due to reload
    assert mock_create_memo.call_count == 2
    assert mock_startup.call_count == 2
    assert mock_kopf_run.call_count == 2

    # Should log reload message
    logger.info.assert_any_call("🔄 Configuration changed. Reinitializing...")
    logger.info.assert_called_with("👋 Operator shutdown complete.")
