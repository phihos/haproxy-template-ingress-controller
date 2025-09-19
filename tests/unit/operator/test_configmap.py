"""
Test configmap functionality.

Tests for load_config_from_configmap function.
"""

import pytest

from haproxy_template_ic.operator.configmap import load_config_from_configmap
from tests.unit.conftest import create_configmap_mock


@pytest.mark.asyncio
async def test_configmap_load_config_from_configmap_success():
    """Test successful config loading from ConfigMap."""
    config_data = {
        "config": """
pod_selector:
  match_labels:
    app: haproxy
    component: loadbalancer

haproxy_config:
  template: |
    global
        daemon
    defaults
        mode http
"""
    }
    mock_configmap = create_configmap_mock(config_data)

    config = await load_config_from_configmap(mock_configmap)

    assert config.pod_selector.match_labels["app"] == "haproxy"
    assert config.pod_selector.match_labels["component"] == "loadbalancer"
    assert "global" in config.haproxy_config.template
    assert "daemon" in config.haproxy_config.template


@pytest.mark.asyncio
async def test_configmap_load_config_from_configmap_invalid_yaml():
    """Test config loading with invalid YAML."""
    mock_configmap = create_configmap_mock({"config": "invalid: yaml: [unclosed"})

    with pytest.raises(Exception):  # Should raise YAML parsing error
        await load_config_from_configmap(mock_configmap)
