import pytest
from unittest.mock import AsyncMock, MagicMock, patch
import yaml
import kopf

from haproxy_template_ic.__main__ import (
    load_config_from_configmap,
    fetch_configmap,
    parse_configmap,
    trigger_reload,
    handle_configmap_change,
    update_resource_index,
    setup_logging,
    create_operator_memo,
)
from haproxy_template_ic.config import Config


# Configuration Management Tests
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
async def test_load_config_from_configmap_missing_config_key():
    """Test config loading with missing config key."""
    configmap = {"data": {"other_key": "value"}}

    with pytest.raises(KeyError):
        await load_config_from_configmap(configmap)


@pytest.mark.asyncio
async def test_fetch_configmap_success():
    """Test successful ConfigMap fetching."""
    mock_configmap = {"metadata": {"name": "test"}, "data": {"config": "test"}}

    with patch("kr8s.objects.ConfigMap.get", new_callable=AsyncMock) as mock_get:
        mock_get.return_value = mock_configmap

        result = await fetch_configmap("test-config", "test-namespace")

        assert result == mock_configmap
        mock_get.assert_called_once_with("test-config", namespace="test-namespace")


@pytest.mark.asyncio
async def test_fetch_configmap_failure():
    """Test ConfigMap fetching failure."""
    with patch("kr8s.objects.ConfigMap.get", new_callable=AsyncMock) as mock_get:
        mock_get.side_effect = Exception("Connection failed")

        with pytest.raises(kopf.TemporaryError) as exc_info:
            await fetch_configmap("test-config", "test-namespace")

        assert "Failed to retrieve ConfigMap" in str(exc_info.value)


@pytest.mark.asyncio
async def test_parse_configmap_success():
    """Test successful ConfigMap parsing."""
    config_data = {"pod_selector": "app=test"}
    configmap = {"data": {"config": yaml.dump(config_data, Dumper=yaml.CDumper)}}

    result = await parse_configmap(configmap, "test-config")

    assert isinstance(result, Config)
    assert result.pod_selector == "app=test"


@pytest.mark.asyncio
async def test_parse_configmap_parsing_failure():
    """Test ConfigMap parsing failure."""
    configmap = {"data": {"config": "invalid yaml"}}

    with pytest.raises(kopf.TemporaryError) as exc_info:
        await parse_configmap(configmap, "test-config")

    assert "Failed to parse ConfigMap" in str(exc_info.value)


# Event Handlers Tests
def test_trigger_reload():
    """Test reload triggering."""
    memo = MagicMock()
    memo.config_reload_flag = MagicMock()
    memo.stop_flag = MagicMock()

    trigger_reload(memo)

    memo.config_reload_flag.set_result.assert_called_once_with(None)
    memo.stop_flag.set_result.assert_called_once_with(None)


@pytest.mark.asyncio
async def test_handle_configmap_change_no_change():
    """Test ConfigMap change handler when no change detected."""
    memo = MagicMock()
    memo.config = Config(pod_selector="app=test")
    event = {
        "object": {
            "data": {
                "config": yaml.dump({"pod_selector": "app=test"}, Dumper=yaml.CDumper)
            }
        }
    }
    logger = MagicMock()

    with patch("haproxy_template_ic.__main__.load_config_from_configmap") as mock_load:
        mock_load.return_value = Config(pod_selector="app=test")

        await handle_configmap_change(memo, event, "test-config", "MODIFIED", logger)

        logger.info.assert_called_once()
        assert "📋 Configmap" in logger.info.call_args[0][0]


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

    with patch("haproxy_template_ic.__main__.load_config_from_configmap") as mock_load:
        with patch("haproxy_template_ic.__main__.trigger_reload") as mock_trigger:
            mock_load.return_value = Config(pod_selector="app=new")

            await handle_configmap_change(
                memo, event, "test-config", "MODIFIED", logger
            )

            assert logger.info.call_count == 2
            assert "🔄 Config has changed" in logger.info.call_args_list[1][0][0]
            mock_trigger.assert_called_once_with(memo)


@pytest.mark.asyncio
async def test_update_resource_index():
    """Test resource index updating."""
    logger = MagicMock()

    result = await update_resource_index(
        "test-param", "test-namespace", "test-name", {"spec": "value"}, logger
    )

    expected = {("test-namespace", "test-name"): {"spec": "value"}}
    assert result == expected
    logger.debug.assert_called_once()
    assert "📝 Updating index" in logger.debug.call_args[0][0]


# Logging Setup Tests
def test_setup_logging_warning_level():
    """Test logging setup with warning level."""
    with patch("logging.basicConfig") as mock_basic_config:
        setup_logging(0)
        mock_basic_config.assert_called_once()
        # Check that WARNING level is set
        call_args = mock_basic_config.call_args
        assert call_args[1]["level"] == 30  # WARNING level


def test_setup_logging_info_level():
    """Test logging setup with info level."""
    with patch("logging.basicConfig") as mock_basic_config:
        setup_logging(1)
        mock_basic_config.assert_called_once()
        # Check that INFO level is set
        call_args = mock_basic_config.call_args
        assert call_args[1]["level"] == 20  # INFO level


def test_setup_logging_debug_level():
    """Test logging setup with debug level."""
    with patch("logging.basicConfig") as mock_basic_config:
        setup_logging(2)
        mock_basic_config.assert_called_once()
        # Check that DEBUG level is set
        call_args = mock_basic_config.call_args
        assert call_args[1]["level"] == 10  # DEBUG level


def test_setup_logging_high_verbosity():
    """Test logging setup with high verbosity level."""
    with patch("logging.basicConfig") as mock_basic_config:
        setup_logging(5)  # Higher than defined levels
        mock_basic_config.assert_called_once()
        # Should default to DEBUG level
        call_args = mock_basic_config.call_args
        assert call_args[1]["level"] == 10  # DEBUG level


# Operator Memo Tests
def test_create_operator_memo():
    """Test operator memo creation."""
    with patch("uvloop.EventLoopPolicy") as mock_policy:
        mock_loop = MagicMock()
        mock_policy.return_value.new_event_loop.return_value = mock_loop

        memo, loop, stop_flag = create_operator_memo("test-config")

        assert memo.configmap_name == "test-config"
        assert loop == mock_loop
        assert stop_flag is not None
        assert memo.stop_flag == stop_flag
        assert memo.config_reload_flag is not None
