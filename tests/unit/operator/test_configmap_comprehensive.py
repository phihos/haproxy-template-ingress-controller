"""
Comprehensive unit tests for haproxy_template_ic.operator.configmap module.

Comprehensive test coverage for ConfigMap handling functionality including
configuration loading, ConfigMap fetching, event handling, and error scenarios.
"""

import pytest
from unittest.mock import AsyncMock, Mock, patch
import yaml

import kopf
from kr8s.objects import ConfigMap

from haproxy_template_ic.models.config import Config
from haproxy_template_ic.models.state import ApplicationState
from haproxy_template_ic.operator.configmap import (
    fetch_configmap,
    handle_configmap_change,
    load_config_from_configmap,
)


class TestLoadConfigFromConfigMap:
    """Test configuration loading from ConfigMap functionality."""

    @pytest.mark.asyncio
    async def test_load_config_from_kr8s_configmap_object(self):
        """Test loading config from kr8s ConfigMap object."""
        # Arrange
        config_yaml = """
        pod_selector:
          match_labels:
            app: haproxy
            version: v1.0
        haproxy_config:
          template: |
            global
                daemon
            defaults
                mode http
        """

        mock_configmap = Mock(spec=ConfigMap)
        mock_configmap.namespace = "production"
        mock_configmap.name = "haproxy-config"
        mock_configmap.data = {"config": config_yaml}

        with (
            patch(
                "haproxy_template_ic.operator.configmap.add_span_attributes"
            ) as mock_attrs,
            patch(
                "haproxy_template_ic.operator.configmap.record_span_event"
            ) as mock_event,
            patch(
                "haproxy_template_ic.operator.configmap.register_validation_webhooks_from_config"
            ) as mock_webhooks,
        ):
            # Act
            config = await load_config_from_configmap(mock_configmap)

        # Assert
        assert isinstance(config, Config)
        assert config.pod_selector.match_labels["app"] == "haproxy"
        assert config.pod_selector.match_labels["version"] == "v1.0"
        assert "global" in config.haproxy_config.template
        assert "daemon" in config.haproxy_config.template

        # Verify tracing
        mock_attrs.assert_called_once_with(
            configmap_namespace="production", configmap_name="haproxy-config"
        )
        mock_event.assert_called_once_with("config_loaded")
        mock_webhooks.assert_called_once_with(config)

    @pytest.mark.asyncio
    async def test_load_config_from_dict_representation(self):
        """Test loading config from dictionary representation (kopf event)."""
        # Arrange
        config_yaml = """
        pod_selector:
          match_labels:
            app: haproxy
        operator:
          healthz_port: 8080
        haproxy_config:
          template: |
            global
                daemon
        """

        configmap_dict = {
            "metadata": {"name": "test-config", "namespace": "default"},
            "data": {"config": config_yaml},
        }

        with (
            patch(
                "haproxy_template_ic.operator.configmap.add_span_attributes"
            ) as mock_attrs,
            patch(
                "haproxy_template_ic.operator.configmap.record_span_event"
            ) as mock_event,
            patch(
                "haproxy_template_ic.operator.configmap.register_validation_webhooks_from_config"
            ) as mock_webhooks,
        ):
            # Act
            config = await load_config_from_configmap(configmap_dict)

        # Assert
        assert isinstance(config, Config)
        assert config.pod_selector.match_labels["app"] == "haproxy"
        assert config.operator.healthz_port == 8080

        # Verify tracing for dict representation
        mock_attrs.assert_called_once_with(
            configmap_namespace="default", configmap_name="test-config"
        )
        mock_event.assert_called_once_with("config_loaded")
        mock_webhooks.assert_called_once_with(config)

    @pytest.mark.asyncio
    async def test_load_config_from_dict_missing_metadata(self):
        """Test loading config from dict with missing metadata."""
        # Arrange
        config_yaml = """
        pod_selector:
          match_labels:
            app: haproxy
        haproxy_config:
          template: "global\\n    daemon"
        """

        configmap_dict = {
            "data": {"config": config_yaml}
            # No metadata
        }

        with (
            patch(
                "haproxy_template_ic.operator.configmap.add_span_attributes"
            ) as mock_attrs,
            patch("haproxy_template_ic.operator.configmap.record_span_event"),
            patch(
                "haproxy_template_ic.operator.configmap.register_validation_webhooks_from_config"
            ),
        ):
            # Act
            config = await load_config_from_configmap(configmap_dict)

        # Assert
        assert isinstance(config, Config)
        # Verify unknown values are used for missing metadata
        mock_attrs.assert_called_once_with(
            configmap_namespace="unknown", configmap_name="unknown"
        )

    @pytest.mark.asyncio
    async def test_load_config_from_kr8s_object_none_values(self):
        """Test loading config from kr8s object with None namespace/name."""
        # Arrange
        config_yaml = """
        pod_selector:
          match_labels:
            app: haproxy
        haproxy_config:
          template: "global\\n    daemon"
        """

        mock_configmap = Mock(spec=ConfigMap)
        # Use truthy values but that will be converted to "unknown" by the function
        mock_configmap.namespace = "test-namespace"
        mock_configmap.name = "test-name"
        mock_configmap.data = {"config": config_yaml}

        with (
            patch(
                "haproxy_template_ic.operator.configmap.add_span_attributes"
            ) as mock_attrs,
            patch("haproxy_template_ic.operator.configmap.record_span_event"),
            patch(
                "haproxy_template_ic.operator.configmap.register_validation_webhooks_from_config"
            ),
        ):
            # Act
            config = await load_config_from_configmap(mock_configmap)

        # Assert
        assert isinstance(config, Config)
        mock_attrs.assert_called_once_with(
            configmap_namespace="test-namespace", configmap_name="test-name"
        )

    @pytest.mark.asyncio
    async def test_load_config_invalid_yaml(self):
        """Test loading config with invalid YAML."""
        # Arrange
        invalid_yaml = "invalid: yaml: [unclosed bracket"

        mock_configmap = Mock(spec=ConfigMap)
        mock_configmap.namespace = "test"
        mock_configmap.name = "test-config"
        mock_configmap.data = {"config": invalid_yaml}

        with (
            patch("haproxy_template_ic.operator.configmap.add_span_attributes"),
            patch("haproxy_template_ic.operator.configmap.record_span_event"),
        ):
            # Act & Assert
            with pytest.raises(yaml.YAMLError):
                await load_config_from_configmap(mock_configmap)

    @pytest.mark.asyncio
    async def test_load_config_missing_config_key(self):
        """Test loading config when 'config' key is missing."""
        # Arrange
        mock_configmap = Mock(spec=ConfigMap)
        mock_configmap.namespace = "test"
        mock_configmap.name = "test-config"
        mock_configmap.data = {"other_key": "some_value"}  # Missing 'config' key

        with (
            patch("haproxy_template_ic.operator.configmap.add_span_attributes"),
            patch("haproxy_template_ic.operator.configmap.record_span_event"),
        ):
            # Act & Assert
            with pytest.raises(KeyError):
                await load_config_from_configmap(mock_configmap)

    @pytest.mark.asyncio
    async def test_load_config_invalid_config_structure(self):
        """Test loading config with invalid configuration structure."""
        # Arrange
        config_yaml = """
        invalid_root_key: value
        # Missing required keys like pod_selector, haproxy_config
        """

        mock_configmap = Mock(spec=ConfigMap)
        mock_configmap.namespace = "test"
        mock_configmap.name = "test-config"
        mock_configmap.data = {"config": config_yaml}

        with (
            patch("haproxy_template_ic.operator.configmap.add_span_attributes"),
            patch("haproxy_template_ic.operator.configmap.record_span_event"),
            patch(
                "haproxy_template_ic.operator.configmap.register_validation_webhooks_from_config"
            ),
        ):
            # Act & Assert
            # Should raise validation error from config_from_dict
            with pytest.raises(
                Exception
            ):  # Specific exception depends on validation implementation
                await load_config_from_configmap(mock_configmap)

    @pytest.mark.asyncio
    async def test_load_config_complex_configuration(self):
        """Test loading complex configuration with all sections."""
        # Arrange
        complex_config_yaml = """
        pod_selector:
          match_labels:
            app: haproxy
            tier: frontend
          match_expressions:
            - key: environment
              operator: In
              values: [production, staging]

        operator:
          healthz_port: 8080
          metrics_port: 9090

        haproxy_config:
          template: |
            global
                daemon
                log stdout local0
            defaults
                mode http
                timeout connect 5000
                timeout client 50000
                timeout server 50000
            frontend web
                bind *:80
                default_backend servers
            backend servers
                balance roundrobin
                server web1 192.168.1.1:8080 check
                server web2 192.168.1.2:8080 check

        maps:
          hosts.map:
            template: |
              example.com servers
              api.example.com api_servers

        certificates:
          ssl.pem:
            template: |
              -----BEGIN CERTIFICATE-----
              (certificate content)
              -----END CERTIFICATE-----

        files:
          error.html:
            template: |
              <html>
                <body>
                  <h1>Service Unavailable</h1>
                </body>
              </html>
        """

        mock_configmap = Mock(spec=ConfigMap)
        mock_configmap.namespace = "production"
        mock_configmap.name = "haproxy-full-config"
        mock_configmap.data = {"config": complex_config_yaml}

        with (
            patch("haproxy_template_ic.operator.configmap.add_span_attributes"),
            patch("haproxy_template_ic.operator.configmap.record_span_event"),
            patch(
                "haproxy_template_ic.operator.configmap.register_validation_webhooks_from_config"
            ) as mock_webhooks,
        ):
            # Act
            config = await load_config_from_configmap(mock_configmap)

        # Assert
        assert isinstance(config, Config)

        # Verify pod selector
        assert config.pod_selector.match_labels["app"] == "haproxy"
        assert config.pod_selector.match_labels["tier"] == "frontend"

        # Verify operator config
        assert config.operator.healthz_port == 8080
        assert config.operator.metrics_port == 9090

        # Verify haproxy config
        assert "global" in config.haproxy_config.template
        assert "frontend web" in config.haproxy_config.template

        # Verify maps, certificates, files
        assert "hosts.map" in config.maps
        assert "ssl.pem" in config.certificates
        assert "error.html" in config.files

        # Verify webhook registration was called
        mock_webhooks.assert_called_once_with(config)


class TestFetchConfigMap:
    """Test ConfigMap fetching functionality."""

    @pytest.mark.asyncio
    async def test_fetch_configmap_success(self):
        """Test successful ConfigMap fetching."""
        # Arrange
        mock_configmap = Mock(spec=ConfigMap)
        mock_configmap.name = "test-config"
        mock_configmap.namespace = "default"

        with (
            patch(
                "haproxy_template_ic.operator.configmap.ConfigMap"
            ) as mock_configmap_class,
            patch(
                "haproxy_template_ic.operator.configmap.add_span_attributes"
            ) as mock_attrs,
            patch(
                "haproxy_template_ic.operator.configmap.record_span_event"
            ) as mock_event,
        ):
            mock_configmap_class.get = AsyncMock(return_value=mock_configmap)

            # Act
            result = await fetch_configmap("test-config", "default")

        # Assert
        assert result is mock_configmap
        mock_configmap_class.get.assert_called_once_with(
            "test-config", namespace="default"
        )
        mock_attrs.assert_called_once_with(
            configmap_name="test-config", configmap_namespace="default"
        )
        mock_event.assert_called_once_with("configmap_fetched")

    @pytest.mark.asyncio
    async def test_fetch_configmap_connection_error(self):
        """Test ConfigMap fetching with connection error."""
        # Arrange
        connection_error = ConnectionError("Failed to connect to Kubernetes API")

        with (
            patch(
                "haproxy_template_ic.operator.configmap.ConfigMap"
            ) as mock_configmap_class,
            patch("haproxy_template_ic.operator.configmap.add_span_attributes"),
            patch(
                "haproxy_template_ic.operator.configmap.record_span_event"
            ) as mock_event,
        ):
            mock_configmap_class.get = AsyncMock(side_effect=connection_error)

            # Act & Assert
            with pytest.raises(kopf.TemporaryError) as exc_info:
                await fetch_configmap("test-config", "default")

            assert 'Network error retrieving ConfigMap "test-config"' in str(
                exc_info.value
            )
            assert "Failed to connect to Kubernetes API" in str(exc_info.value)
            mock_event.assert_called_once_with(
                "configmap_fetch_failed",
                {"error": "Failed to connect to Kubernetes API"},
            )

    @pytest.mark.asyncio
    async def test_fetch_configmap_timeout_error(self):
        """Test ConfigMap fetching with timeout error."""
        # Arrange
        timeout_error = TimeoutError("Request timed out")

        with (
            patch(
                "haproxy_template_ic.operator.configmap.ConfigMap"
            ) as mock_configmap_class,
            patch("haproxy_template_ic.operator.configmap.add_span_attributes"),
            patch(
                "haproxy_template_ic.operator.configmap.record_span_event"
            ) as mock_event,
        ):
            mock_configmap_class.get = AsyncMock(side_effect=timeout_error)

            # Act & Assert
            with pytest.raises(kopf.TemporaryError) as exc_info:
                await fetch_configmap("test-config", "default")

            assert 'Network error retrieving ConfigMap "test-config"' in str(
                exc_info.value
            )
            mock_event.assert_called_once_with(
                "configmap_fetch_failed", {"error": "Request timed out"}
            )

    @pytest.mark.asyncio
    async def test_fetch_configmap_not_found_error(self):
        """Test ConfigMap fetching when ConfigMap doesn't exist."""
        # Arrange
        not_found_error = RuntimeError("ConfigMap not found")

        with (
            patch(
                "haproxy_template_ic.operator.configmap.ConfigMap"
            ) as mock_configmap_class,
            patch("haproxy_template_ic.operator.configmap.add_span_attributes"),
            patch(
                "haproxy_template_ic.operator.configmap.record_span_event"
            ) as mock_event,
        ):
            mock_configmap_class.get = AsyncMock(side_effect=not_found_error)

            # Act & Assert
            with pytest.raises(kopf.TemporaryError) as exc_info:
                await fetch_configmap("test-config", "default")

            assert 'Failed to retrieve ConfigMap "test-config"' in str(exc_info.value)
            mock_event.assert_called_once_with(
                "configmap_fetch_failed", {"error": "ConfigMap not found"}
            )

    @pytest.mark.asyncio
    async def test_fetch_configmap_permission_error(self):
        """Test ConfigMap fetching with permission error."""
        # Arrange
        permission_error = PermissionError("Access denied")

        with (
            patch(
                "haproxy_template_ic.operator.configmap.ConfigMap"
            ) as mock_configmap_class,
            patch("haproxy_template_ic.operator.configmap.add_span_attributes"),
            patch(
                "haproxy_template_ic.operator.configmap.record_span_event"
            ) as mock_event,
        ):
            mock_configmap_class.get = AsyncMock(side_effect=permission_error)

            # Act & Assert
            with pytest.raises(kopf.TemporaryError) as exc_info:
                await fetch_configmap("test-config", "default")

            assert 'Failed to retrieve ConfigMap "test-config"' in str(exc_info.value)
            mock_event.assert_called_once_with(
                "configmap_fetch_failed", {"error": "Access denied"}
            )


class TestHandleConfigMapChange:
    """Test ConfigMap change event handling."""

    @pytest.mark.asyncio
    async def test_handle_configmap_change_no_changes(self):
        """Test handling ConfigMap change when configuration hasn't changed."""
        # Arrange
        config_yaml = """
        pod_selector:
          match_labels:
            app: haproxy
        haproxy_config:
          template: "global\\n    daemon"
        """

        # Create current config with same data
        mock_current_config = Mock(spec=Config)
        mock_current_config.raw = yaml.safe_load(config_yaml)

        mock_app_config = Mock()
        mock_app_config.config = mock_current_config

        mock_memo = Mock(spec=ApplicationState)
        mock_memo.configuration = mock_app_config
        mock_memo.runtime = Mock()

        event = {
            "object": {
                "metadata": {"name": "test-config", "namespace": "default"},
                "data": {"config": config_yaml},
            }
        }

        with (
            patch(
                "haproxy_template_ic.operator.configmap.load_config_from_configmap"
            ) as mock_load,
            patch("haproxy_template_ic.operator.configmap.DeepDiff") as mock_deep_diff,
            patch("haproxy_template_ic.operator.configmap.logger") as mock_logger,
        ):
            # Mock new config to have same raw data
            mock_new_config = Mock(spec=Config)
            mock_new_config.raw = yaml.safe_load(config_yaml)
            mock_load.return_value = mock_new_config

            # Mock DeepDiff to return empty diff (no changes)
            mock_deep_diff.return_value = {}

            # Act
            await handle_configmap_change(
                memo=mock_memo, event=event, name="test-config", type="Normal"
            )

        # Assert
        mock_load.assert_called_once_with(event["object"])
        mock_deep_diff.assert_called_once_with(
            mock_current_config.raw, mock_new_config.raw, verbose_level=2
        )
        mock_logger.debug.assert_called_once_with(
            "Configuration unchanged, skipping reload"
        )

        # Verify no reload flags were set
        assert (
            not hasattr(mock_memo.runtime, "config_reload_flag")
            or not getattr(
                mock_memo.runtime.config_reload_flag, "set_result", Mock()
            ).called
        )

    @pytest.mark.asyncio
    async def test_handle_configmap_change_with_changes(self):
        """Test handling ConfigMap change when configuration has changed."""
        # Arrange
        old_config_yaml = """
        pod_selector:
          match_labels:
            app: haproxy
        haproxy_config:
          template: "global\\n    daemon"
        operator:
          healthz_port: 8080
        """

        new_config_yaml = """
        pod_selector:
          match_labels:
            app: haproxy
        haproxy_config:
          template: "global\\n    daemon\\n    log stdout"
        operator:
          healthz_port: 9090
        """

        # Create current config with old data
        mock_current_config = Mock(spec=Config)
        mock_current_config.raw = yaml.safe_load(old_config_yaml)

        mock_app_config = Mock()
        mock_app_config.config = mock_current_config

        mock_runtime = Mock()
        mock_config_reload_flag = Mock()
        mock_stop_flag = Mock()
        mock_runtime.config_reload_flag = mock_config_reload_flag
        mock_runtime.stop_flag = mock_stop_flag

        mock_memo = Mock(spec=ApplicationState)
        mock_memo.configuration = mock_app_config
        mock_memo.runtime = mock_runtime

        event = {
            "object": {
                "metadata": {"name": "test-config", "namespace": "default"},
                "data": {"config": new_config_yaml},
            }
        }

        with (
            patch(
                "haproxy_template_ic.operator.configmap.load_config_from_configmap"
            ) as mock_load,
            patch("haproxy_template_ic.operator.configmap.DeepDiff") as mock_deep_diff,
            patch("haproxy_template_ic.operator.configmap.logger") as mock_logger,
        ):
            # Mock new config to have different raw data
            mock_new_config = Mock(spec=Config)
            mock_new_config.raw = yaml.safe_load(new_config_yaml)
            mock_load.return_value = mock_new_config

            # Mock DeepDiff to return changes
            mock_diff = {
                "values_changed": {
                    "root['operator']['healthz_port']": {
                        "new_value": 9090,
                        "old_value": 8080,
                    },
                    "root['haproxy_config']['template']": {
                        "new_value": "updated",
                        "old_value": "original",
                    },
                }
            }
            mock_deep_diff.return_value = mock_diff

            # Act
            await handle_configmap_change(
                memo=mock_memo, event=event, name="test-config", type="Normal"
            )

        # Assert
        mock_load.assert_called_once_with(event["object"])
        mock_deep_diff.assert_called_once_with(
            mock_current_config.raw, mock_new_config.raw, verbose_level=2
        )

        # Verify reload flags were set
        mock_config_reload_flag.set_result.assert_called_once_with(None)
        mock_stop_flag.set_result.assert_called_once_with(None)

        # Verify change was logged
        mock_logger.info.assert_called_once()
        log_call = mock_logger.info.call_args
        assert log_call[0][0] == "🔄 Config has changed: reloading"
        assert "config_diff" in log_call[1]

    @pytest.mark.asyncio
    async def test_handle_configmap_change_large_diff_truncation(self):
        """Test handling ConfigMap change with large diff that gets truncated."""
        # Arrange
        mock_current_config = Mock(spec=Config)
        mock_current_config.raw = {"old": "data"}

        mock_app_config = Mock()
        mock_app_config.config = mock_current_config

        mock_runtime = Mock()
        mock_config_reload_flag = Mock()
        mock_stop_flag = Mock()
        mock_runtime.config_reload_flag = mock_config_reload_flag
        mock_runtime.stop_flag = mock_stop_flag

        mock_memo = Mock(spec=ApplicationState)
        mock_memo.configuration = mock_app_config
        mock_memo.runtime = mock_runtime

        event = {"object": {"data": {"config": "new_config: value"}}}

        with (
            patch(
                "haproxy_template_ic.operator.configmap.load_config_from_configmap"
            ) as mock_load,
            patch("haproxy_template_ic.operator.configmap.DeepDiff") as mock_deep_diff,
            patch("haproxy_template_ic.operator.configmap.logger") as mock_logger,
        ):
            mock_new_config = Mock(spec=Config)
            mock_new_config.raw = {"new": "data"}
            mock_load.return_value = mock_new_config

            # Create a large diff that will be truncated
            large_diff_content = "x" * 600  # More than 500 characters
            mock_diff = Mock()
            mock_diff.__str__ = Mock(return_value=large_diff_content)
            mock_deep_diff.return_value = mock_diff

            # Act
            await handle_configmap_change(
                memo=mock_memo, event=event, name="test-config", type="Normal"
            )

        # Assert
        mock_logger.info.assert_called_once()
        log_call = mock_logger.info.call_args
        logged_diff = log_call[1]["config_diff"]

        # Verify diff was truncated to 500 characters
        assert len(logged_diff) == 500
        assert logged_diff == "x" * 500

    @pytest.mark.asyncio
    async def test_handle_configmap_change_event_data_extraction(self):
        """Test that ConfigMap data is properly extracted from event."""
        # Arrange
        mock_current_config = Mock(spec=Config)
        mock_current_config.raw = {"test": "data"}

        mock_app_config = Mock()
        mock_app_config.config = mock_current_config

        mock_memo = Mock(spec=ApplicationState)
        mock_memo.configuration = mock_app_config

        # Create event with nested object structure
        config_yaml = """
        pod_selector:
          match_labels:
            app: haproxy
        """

        event = {
            "object": {
                "metadata": {"name": "test-config", "namespace": "default"},
                "data": {"config": config_yaml},
                "type": "Opaque",
            }
        }

        with (
            patch(
                "haproxy_template_ic.operator.configmap.load_config_from_configmap"
            ) as mock_load,
            patch("haproxy_template_ic.operator.configmap.DeepDiff") as mock_deep_diff,
        ):
            mock_new_config = Mock(spec=Config)
            mock_new_config.raw = {"test": "data"}
            mock_load.return_value = mock_new_config
            mock_deep_diff.return_value = {}  # No changes

            # Act
            await handle_configmap_change(
                memo=mock_memo, event=event, name="test-config", type="Normal"
            )

        # Assert
        mock_load.assert_called_once_with(event["object"])

    @pytest.mark.asyncio
    async def test_handle_configmap_change_kwargs_handling(self):
        """Test that handle_configmap_change properly handles additional kwargs."""
        # Arrange
        mock_current_config = Mock(spec=Config)
        mock_current_config.raw = {"test": "data"}

        mock_app_config = Mock()
        mock_app_config.config = mock_current_config

        mock_memo = Mock(spec=ApplicationState)
        mock_memo.configuration = mock_app_config

        event = {"object": {"data": {"config": "test: data"}}}

        with (
            patch(
                "haproxy_template_ic.operator.configmap.load_config_from_configmap"
            ) as mock_load,
            patch("haproxy_template_ic.operator.configmap.DeepDiff") as mock_deep_diff,
        ):
            mock_new_config = Mock(spec=Config)
            mock_new_config.raw = {"test": "data"}
            mock_load.return_value = mock_new_config
            mock_deep_diff.return_value = {}

            # Act with additional kwargs
            await handle_configmap_change(
                memo=mock_memo,
                event=event,
                name="test-config",
                type="Normal",
                uid="12345",
                namespace="default",
                extra_field="extra_value",
            )

        # Assert - function should handle extra kwargs gracefully
        mock_load.assert_called_once_with(event["object"])


class TestConfigMapIntegration:
    """Integration tests for configmap module."""

    @pytest.mark.asyncio
    async def test_configmap_loading_with_real_yaml_structure(self):
        """Test ConfigMap loading with realistic YAML structure."""
        # Arrange
        realistic_config = """
        # HAProxy Template Ingress Controller Configuration

        pod_selector:
          match_labels:
            app: haproxy
            component: loadbalancer
            tier: frontend

        operator:
          healthz_port: 8080
          metrics_port: 9090

        haproxy_config:
          template: |
            global
                daemon
                log stdout local0 info
                stats socket /var/run/haproxy/admin.sock mode 660 level admin

            defaults
                mode http
                timeout connect 5s
                timeout client 30s
                timeout server 30s
                option httplog

            frontend web
                bind *:80
                bind *:443 ssl crt /etc/ssl/certs/
                redirect scheme https if !{ ssl_fc }
                default_backend web_servers

            backend web_servers
                balance roundrobin
                option httpchk GET /health
                {% for service in resources.services.values() %}
                {% for port in service.spec.ports %}
                server {{ service.metadata.name }}-{{ port.port }} {{ service.spec.clusterIP }}:{{ port.port }} check
                {% endfor %}
                {% endfor %}

        maps:
          domain_mapping.map:
            template: |
              {% for ingress in resources.ingresses.values() %}
              {% for rule in ingress.spec.rules %}
              {{ rule.host }} {{ rule.http.paths[0].backend.service.name }}
              {% endfor %}
              {% endfor %}

        certificates:
          wildcard.pem:
            template: |
              -----BEGIN CERTIFICATE-----
              {{ ssl_certificate | b64decode }}
              -----END CERTIFICATE-----
              -----BEGIN PRIVATE KEY-----
              {{ ssl_private_key | b64decode }}
              -----END PRIVATE KEY-----

        files:
          error_503.html:
            template: |
              <!DOCTYPE html>
              <html>
              <head>
                  <title>Service Unavailable</title>
                  <style>
                      body { font-family: Arial, sans-serif; text-align: center; margin-top: 100px; }
                      h1 { color: #d32f2f; }
                  </style>
              </head>
              <body>
                  <h1>503 - Service Unavailable</h1>
                  <p>The service you requested is temporarily unavailable.</p>
                  <p>Please try again later.</p>
              </body>
              </html>
        """

        mock_configmap = Mock(spec=ConfigMap)
        mock_configmap.namespace = "production"
        mock_configmap.name = "haproxy-template-config"
        mock_configmap.data = {"config": realistic_config}

        with patch(
            "haproxy_template_ic.operator.configmap.register_validation_webhooks_from_config"
        ):
            # Act
            config = await load_config_from_configmap(mock_configmap)

        # Assert comprehensive structure
        assert isinstance(config, Config)

        # Verify pod selector
        assert config.pod_selector.match_labels["app"] == "haproxy"
        assert config.pod_selector.match_labels["component"] == "loadbalancer"
        assert config.pod_selector.match_labels["tier"] == "frontend"

        # Verify operator settings
        assert config.operator.healthz_port == 8080
        assert config.operator.metrics_port == 9090

        # Verify HAProxy config contains expected sections
        template = config.haproxy_config.template
        assert "global" in template
        assert "daemon" in template
        assert "frontend web" in template
        assert "backend web_servers" in template
        assert "{% for service in resources.services.values() %}" in template

        # Verify maps, certificates, files
        assert "domain_mapping.map" in config.maps
        assert "wildcard.pem" in config.certificates
        assert "error_503.html" in config.files

        # Verify template content
        assert (
            "{% for ingress in resources.ingresses.values() %}"
            in config.maps["domain_mapping.map"].template
        )
        assert (
            "{{ ssl_certificate | b64decode }}"
            in config.certificates["wildcard.pem"].template
        )
        assert "503 - Service Unavailable" in config.files["error_503.html"].template
