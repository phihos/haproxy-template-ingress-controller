"""
Test configmap functionality.

Tests for load_config_from_configmap function.
"""

import pytest
from unittest.mock import MagicMock

from haproxy_template_ic.operator.configmap import load_config_from_configmap


class TestConfigMapLoading:
    """Test configuration loading from ConfigMap."""

    @pytest.mark.asyncio
    async def test_load_config_from_configmap_success(self):
        """Test successful config loading from ConfigMap."""
        mock_configmap = MagicMock()
        mock_configmap.data = {
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

        config = await load_config_from_configmap(mock_configmap)

        assert config.pod_selector.match_labels["app"] == "haproxy"
        assert config.pod_selector.match_labels["component"] == "loadbalancer"
        assert "global" in config.haproxy_config.template
        assert "daemon" in config.haproxy_config.template

    @pytest.mark.asyncio
    async def test_load_config_from_configmap_invalid_yaml(self):
        """Test config loading with invalid YAML."""
        mock_configmap = MagicMock()
        mock_configmap.data = {"config": "invalid: yaml: [unclosed"}

        with pytest.raises(Exception):  # Should raise YAML parsing error
            await load_config_from_configmap(mock_configmap)
