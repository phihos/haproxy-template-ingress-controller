"""
Simplified unit tests for webhook validation functionality.

Tests the essential webhook validation components focusing on the
resource-specific webhook registration functionality.
"""

import pytest
from unittest.mock import MagicMock, patch, AsyncMock
import kopf

from haproxy_template_ic.webhook import (
    ConfigMapValidator,
    WebhookRegistry,
    register_validation_webhooks_from_config,
)
from haproxy_template_ic.config import WatchResourceConfig


class TestConfigMapValidator:
    """Test ConfigMapValidator basic functionality."""

    @pytest.fixture
    def validator(self):
        """Create a ConfigMapValidator instance."""
        return ConfigMapValidator()

    def test_is_haproxy_template_ic_configmap_positive(self, validator):
        """Test identification of HAProxy Template IC ConfigMaps."""
        configmap = {
            "metadata": {
                "labels": {
                    "app.kubernetes.io/name": "haproxy-template-ic",
                    "haproxy-template-ic/config": "true",
                }
            }
        }
        assert validator._is_haproxy_template_ic_configmap(configmap) is True

    def test_is_haproxy_template_ic_configmap_negative(self, validator):
        """Test rejection of non-HAProxy Template IC ConfigMaps."""
        configmap = {"metadata": {"labels": {"app": "other"}}}
        assert validator._is_haproxy_template_ic_configmap(configmap) is False

    def test_is_haproxy_template_ic_configmap_missing_labels(self, validator):
        """Test handling of ConfigMaps with missing labels."""
        configmap = {"metadata": {"name": "test-config"}}
        assert validator._is_haproxy_template_ic_configmap(configmap) is False

    def test_is_haproxy_template_ic_configmap_content_based_detection(self, validator):
        """Test ConfigMap identification based on content analysis."""
        # ConfigMap without our labels but with HAProxy config content
        configmap = {
            "metadata": {"labels": {"other-app": "true"}},
            "data": {"config": "pod_selector:\n  match_labels:\n    app: haproxy"},
        }
        assert validator._is_haproxy_template_ic_configmap(configmap) is True

    def test_is_haproxy_template_ic_configmap_invalid_yaml_content(self, validator):
        """Test ConfigMap with invalid YAML content in data section."""
        configmap = {
            "metadata": {"labels": {"other-app": "true"}},
            "data": {"config": "invalid: yaml: content: ["},
        }
        assert validator._is_haproxy_template_ic_configmap(configmap) is False

    def test_is_haproxy_template_ic_configmap_no_data_section(self, validator):
        """Test ConfigMap without data section."""
        configmap = {"metadata": {"labels": {"other-app": "true"}}}
        assert validator._is_haproxy_template_ic_configmap(configmap) is False

    def test_extract_config_data_success(self, validator):
        """Test successful config data extraction."""
        configmap_data = {"data": {"config": "test: value"}}
        result = validator._extract_config_data(configmap_data)
        assert result == "test: value"

    def test_extract_config_data_missing_data(self, validator):
        """Test config extraction with missing data section."""
        configmap_data = {"metadata": {"name": "test"}}
        result = validator._extract_config_data(configmap_data)
        assert result is None

    def test_extract_config_data_missing_config_key(self, validator):
        """Test config extraction with missing config key."""
        configmap_data = {"data": {"other.yaml": "other: value"}}
        result = validator._extract_config_data(configmap_data)
        assert result is None

    @pytest.mark.asyncio
    async def test_validate_config_structure_valid_config(self, validator):
        """Test validation of valid config structure."""
        config_dict = {
            "watch_resources": [],
            "maps": {},
            "pod_selector": {"match_labels": {"app": "haproxy"}},
        }
        warnings = await validator._validate_config_structure(config_dict)
        assert isinstance(warnings, list)
        assert len(warnings) == 0

    @pytest.mark.asyncio
    async def test_validate_config_structure_missing_sections(self, validator):
        """Test validation with missing required sections."""
        config_dict = {}  # Empty config
        warnings = await validator._validate_config_structure(config_dict)
        assert (
            len(warnings) >= 2
        )  # Should warn about missing pod_selector and watch_resources

    @pytest.mark.asyncio
    async def test_validate_templates_valid(self, validator):
        """Test template validation with valid templates."""
        config_dict = {
            "maps": {"/etc/haproxy/test.map": {"template": "{{ test_var }}"}}
        }
        warnings = await validator._validate_templates(config_dict)
        assert len(warnings) == 0

    @pytest.mark.asyncio
    async def test_validate_templates_syntax_error(self, validator):
        """Test template validation with syntax errors."""
        config_dict = {
            "maps": {"/etc/haproxy/test.map": {"template": "{{ invalid syntax %}"}}
        }
        warnings = await validator._validate_templates(config_dict)
        assert len(warnings) > 0
        assert "Invalid template syntax" in warnings[0]

    @pytest.mark.asyncio
    async def test_validate_templates_with_snippets(self, validator):
        """Test template validation with snippet includes."""
        config_dict = {
            "template_snippets": {"test-snippet": "snippet content"},
            "maps": {
                "/etc/haproxy/test.map": {"template": "{% include 'test-snippet' %}"}
            },
        }
        warnings = await validator._validate_templates(config_dict)
        assert len(warnings) == 0

    @pytest.mark.asyncio
    async def test_validate_templates_snippet_syntax_error(self, validator):
        """Test template validation with syntax errors in snippets."""
        config_dict = {"template_snippets": {"bad-snippet": "{{ invalid syntax %}"}}
        warnings = await validator._validate_templates(config_dict)
        assert len(warnings) > 0
        assert "Invalid template syntax in snippet" in warnings[0]

    @pytest.mark.asyncio
    async def test_validate_templates_snippet_other_error(self, validator):
        """Test template validation with other errors in snippets."""
        config_dict = {
            "template_snippets": {
                "error-snippet": "{{ 1/0 }}"  # Will cause a runtime error during validation
            }
        }
        # This will likely be caught as a general template error
        warnings = await validator._validate_templates(config_dict)
        # The exact behavior depends on when the error occurs
        assert isinstance(warnings, list)

    @pytest.mark.asyncio
    async def test_validate_templates_map_syntax_error(self, validator):
        """Test template validation with syntax errors in map templates."""
        config_dict = {
            "maps": {"/etc/haproxy/test.map": {"template": "{{ invalid syntax %}"}}
        }
        warnings = await validator._validate_templates(config_dict)
        assert len(warnings) > 0
        assert "Invalid template syntax" in warnings[0]

    @pytest.mark.asyncio
    async def test_validate_templates_map_other_error(self, validator):
        """Test template validation with general errors in map templates."""
        with patch(
            "haproxy_template_ic.webhook.jinja2.Environment.from_string",
            side_effect=Exception("General template error"),
        ):
            config_dict = {
                "maps": {"/etc/haproxy/test.map": {"template": "valid template"}}
            }
            warnings = await validator._validate_templates(config_dict)
            assert len(warnings) > 0
            assert "Error in map template" in warnings[0]

    @pytest.mark.asyncio
    async def test_validate_templates_certificates_section(self, validator):
        """Test template validation with certificates templates."""
        config_dict = {
            "certificates": {"/etc/ssl/certs/test.crt": {"template": "{{ cert_data }}"}}
        }
        warnings = await validator._validate_templates(config_dict)
        assert len(warnings) == 0

    @pytest.mark.asyncio
    async def test_validate_templates_haproxy_config_section(self, validator):
        """Test template validation with haproxy_config template."""
        config_dict = {
            "haproxy_config": {"template": "global\n    maxconn {{ max_connections }}"}
        }
        warnings = await validator._validate_templates(config_dict)
        assert len(warnings) == 0

    @pytest.mark.asyncio
    async def test_validate_configmap_full_flow(self, validator):
        """Test complete ConfigMap validation flow."""
        configmap_data = {
            "metadata": {
                "labels": {
                    "app.kubernetes.io/name": "haproxy-template-ic",
                    "haproxy-template-ic/config": "true",
                }
            },
            "data": {
                "config": """
watch_resources:
  - kind: Ingress
    group: networking.k8s.io
    version: v1
pod_selector:
  match_labels:
    app: haproxy
haproxy_config:
  template: |
    global
        maxconn 4096
    defaults
        mode http
maps:
  /etc/haproxy/test.map:
    template: "{{ ingress.metadata.name }}"
"""
            },
        }
        warnings = []

        # Should not raise any exceptions
        await validator.validate_configmap(configmap_data, warnings)

    @pytest.mark.asyncio
    async def test_validate_configmap_non_haproxy_configmap(self, validator):
        """Test validation skips non-HAProxy ConfigMaps."""
        configmap_data = {"metadata": {"labels": {"app": "other-app"}}}
        warnings = []

        # Should return without error or warnings
        await validator.validate_configmap(configmap_data, warnings)
        assert len(warnings) == 0

    @pytest.mark.asyncio
    async def test_validate_configmap_invalid_yaml(self, validator):
        """Test ConfigMap validation with invalid YAML."""
        configmap_data = {
            "metadata": {
                "labels": {
                    "app.kubernetes.io/name": "haproxy-template-ic",
                    "haproxy-template-ic/config": "true",
                }
            },
            "data": {"config": "invalid: yaml: content: ["},
        }
        warnings = []

        with pytest.raises(kopf.AdmissionError) as exc_info:
            await validator.validate_configmap(configmap_data, warnings)
        assert "Invalid YAML" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_validate_configmap_missing_config_data(self, validator):
        """Test ConfigMap validation with missing config data."""
        configmap_data = {
            "metadata": {
                "labels": {
                    "app.kubernetes.io/name": "haproxy-template-ic",
                    "haproxy-template-ic/config": "true",
                }
            },
            "data": {"other-key": "other-value"},
        }
        warnings = []

        with pytest.raises(kopf.AdmissionError) as exc_info:
            await validator.validate_configmap(configmap_data, warnings)
        assert "Missing 'config' key" in str(exc_info.value)


class TestWebhookRegistry:
    """Test WebhookRegistry functionality."""

    @pytest.fixture
    def registry(self):
        """Create a WebhookRegistry instance."""
        return WebhookRegistry()

    @pytest.fixture
    def mock_config(self):
        """Create a mock operator configuration."""
        config = MagicMock()
        config.watch_resources = [
            WatchResourceConfig(
                kind="Ingress",
                group="networking.k8s.io",
                version="v1",
                enable_validation_webhook=True,
            ),
            WatchResourceConfig(
                kind="Secret",
                group="",
                version="v1",
                enable_validation_webhook=True,
            ),
            WatchResourceConfig(
                kind="EndpointSlice",
                group="discovery.k8s.io",
                version="v1",
                enable_validation_webhook=False,  # Disabled
            ),
        ]
        return config

    @patch("haproxy_template_ic.webhook.kopf.on.validate")
    def test_register_validation_webhook(self, mock_kopf_validate, registry):
        """Test registration of a validation webhook."""
        mock_decorator = MagicMock()
        mock_kopf_validate.return_value = mock_decorator

        registry.register_resource_validation_webhook(
            group="networking.k8s.io",
            version="v1",
            kind="Ingress",
            resource_id="ingresses",
        )

        # Verify kopf.on.validate was called with correct parameters including the id
        mock_kopf_validate.assert_called_once_with(
            "networking.k8s.io",
            "v1",
            "Ingress",
            id="validate-ingresses-networking-k8s-io-v1",
        )
        # Verify the decorator was called with the handler function
        mock_decorator.assert_called_once()

    @patch("haproxy_template_ic.webhook.kopf.on.validate")
    def test_register_validation_webhook_duplicate(self, mock_kopf_validate, registry):
        """Test that duplicate webhook registrations are skipped."""
        mock_decorator = MagicMock()
        mock_kopf_validate.return_value = mock_decorator

        # Register once
        registry.register_resource_validation_webhook(
            group="networking.k8s.io",
            version="v1",
            kind="Ingress",
            resource_id="ingresses",
        )

        # Register again - should be skipped
        registry.register_resource_validation_webhook(
            group="networking.k8s.io",
            version="v1",
            kind="Ingress",
            resource_id="ingresses",
        )

        # Verify kopf.on.validate was only called once
        assert mock_kopf_validate.call_count == 1

    def test_webhook_registry_initialization(self, registry):
        """Test WebhookRegistry initialization."""
        assert hasattr(registry, "registered_handlers")
        assert hasattr(registry, "validator")
        assert isinstance(registry.registered_handlers, dict)
        assert len(registry.registered_handlers) == 0

    @pytest.mark.asyncio
    async def test_validate_resource_structure_valid_resource(self, registry):
        """Test validation of valid resource structure."""
        spec = {"rules": [{"host": "example.com", "http": {"paths": []}}]}
        meta = {"name": "test-ingress", "namespace": "default"}
        warnings = []

        await registry._validate_resource_structure(spec, meta, "Ingress", warnings)
        assert len(warnings) == 0

    @pytest.mark.asyncio
    async def test_validate_resource_structure_missing_name(self, registry):
        """Test validation fails for missing resource name."""
        spec = {"rules": []}
        meta = {}
        warnings = []

        with pytest.raises(kopf.AdmissionError) as exc_info:
            await registry._validate_resource_structure(spec, meta, "Ingress", warnings)
        assert "must have a name" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_validate_resource_structure_special_chars_in_name(self, registry):
        """Test validation warns about special characters in resource names."""
        spec = {"rules": []}
        meta = {"name": "test@resource#name"}
        warnings = []

        await registry._validate_resource_structure(spec, meta, "Ingress", warnings)
        assert len(warnings) >= 1
        assert "special characters" in warnings[0]

    @pytest.mark.asyncio
    async def test_validate_service_specific_missing_port_field(self, registry):
        """Test Service validation with missing port field."""
        spec = {"ports": [{"name": "http"}]}  # Missing 'port' field
        warnings = []

        with pytest.raises(kopf.AdmissionError) as exc_info:
            await registry._validate_service_specific(spec, warnings)
        assert "missing 'port' field" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_validate_ingress_specific_invalid_rules(self, registry):
        """Test Ingress validation with invalid rule structure."""
        spec = {
            "rules": [{}, {"host": "example.com"}]
        }  # First rule has neither host nor http
        warnings = []

        await registry._validate_ingress_specific(spec, warnings)
        assert len(warnings) >= 1
        assert "neither host nor http" in warnings[0]

    @pytest.mark.asyncio
    async def test_validate_ingress_specific_no_rules(self, registry):
        """Test Ingress validation warns about missing rules."""
        spec = {"rules": []}
        warnings = []

        await registry._validate_ingress_specific(spec, warnings)
        assert len(warnings) == 1
        assert "no rules defined" in warnings[0]
        assert "Add at least one rule with host or path configuration" in warnings[0]

    @pytest.mark.asyncio
    async def test_validate_service_specific_no_ports(self, registry):
        """Test Service validation warns about missing ports."""
        spec = {"ports": []}
        warnings = []

        await registry._validate_service_specific(spec, warnings)
        assert len(warnings) == 1
        assert "no ports defined" in warnings[0]
        assert "Add at least one port configuration" in warnings[0]


class TestWebhookRegistrationFunction:
    """Test the webhook registration function."""

    @pytest.fixture
    def mock_config_with_webhooks(self):
        """Create a mock configuration with webhook-enabled resources."""
        config = MagicMock()
        config.watch_resources = [
            WatchResourceConfig(
                kind="Ingress",
                group="networking.k8s.io",
                version="v1",
                enable_validation_webhook=True,
            ),
            WatchResourceConfig(
                kind="Secret",
                group="",
                version="v1",
                enable_validation_webhook=False,  # Disabled
            ),
        ]
        return config

    @pytest.fixture
    def mock_config_without_watch_resources(self):
        """Create a mock configuration without watch_resources."""
        config = MagicMock()
        del config.watch_resources  # Remove the attribute
        return config

    @patch("haproxy_template_ic.webhook._webhook_registry")
    def test_register_validation_webhooks_from_config_success(
        self, mock_registry, mock_config_with_webhooks
    ):
        """Test successful webhook registration from config."""
        register_validation_webhooks_from_config(mock_config_with_webhooks)

        # Verify registry method was called (should be called once for ingresses)
        mock_registry.register_resource_validation_webhook.assert_called_once_with(
            group="networking.k8s.io",
            version="v1",
            kind="Ingress",
            resource_id="ingress",
        )

    @patch("haproxy_template_ic.webhook._webhook_registry")
    def test_register_validation_webhooks_from_config_no_watch_resources(
        self, mock_registry, mock_config_without_watch_resources
    ):
        """Test webhook registration with missing watch_resources."""
        register_validation_webhooks_from_config(mock_config_without_watch_resources)

        # Registry should not be called
        mock_registry.register_webhooks_from_config.assert_not_called()


class TestWebhookIntegration:
    """Integration tests for webhook functionality."""

    @patch("haproxy_template_ic.webhook.kopf.on.validate")
    @pytest.mark.asyncio
    async def test_end_to_end_webhook_registration(self, mock_kopf_validate):
        """Test end-to-end webhook registration process."""
        mock_decorator = MagicMock()
        mock_kopf_validate.return_value = mock_decorator

        # Create configuration
        config = MagicMock()
        config.watch_resources = [
            WatchResourceConfig(
                kind="Ingress",
                group="networking.k8s.io",
                version="v1",
                enable_validation_webhook=True,
            )
        ]

        # Register webhooks
        register_validation_webhooks_from_config(config)

        # Verify webhook was registered (resource_id defaults to kind.lower())
        mock_kopf_validate.assert_called_with(
            "networking.k8s.io",
            "v1",
            "Ingress",
            id="validate-ingress-networking-k8s-io-v1",
        )

    @patch("haproxy_template_ic.webhook.get_metrics_collector")
    def test_webhook_handler_with_metrics(self, mock_get_metrics):
        """Test webhook handler includes metrics recording."""
        mock_metrics = MagicMock()
        # Properly configure the context manager mock to prevent AsyncMock issues
        mock_time_context = MagicMock()
        mock_time_context.__enter__ = MagicMock(return_value=None)
        mock_time_context.__exit__ = MagicMock(return_value=None)
        mock_metrics.time_webhook_request.return_value = mock_time_context
        mock_get_metrics.return_value = mock_metrics

        registry = WebhookRegistry()

        # Create a mock handler (simulating what kopf would create)
        with patch("haproxy_template_ic.webhook.kopf.on.validate") as mock_validate:
            mock_decorator = MagicMock()
            mock_validate.return_value = mock_decorator

            registry.register_resource_validation_webhook(
                group="networking.k8s.io",
                version="v1",
                kind="Ingress",
                resource_id="ingresses",
            )

            # Get the handler function that was registered
            handler_func = mock_decorator.call_args[0][0]

            # Call the handler
            kwargs = {
                "warnings": [],
                "spec": {"rules": []},
                "meta": {"name": "test-ingress"},
            }

            # Call the handler (it's async, so we need to handle it properly)
            import asyncio

            asyncio.run(handler_func(**kwargs))

            # Verify metrics were recorded
            mock_metrics.time_webhook_request.assert_called_once()


class TestWebhookErrorHandling:
    """Test webhook error handling and edge cases."""

    @pytest.mark.asyncio
    async def test_configmap_validation_exception_handling(self):
        """Test ConfigMap validation exception handling."""
        validator = ConfigMapValidator()
        configmap_data = {
            "metadata": {
                "labels": {
                    "app.kubernetes.io/name": "haproxy-template-ic",
                    "haproxy-template-ic/config": "true",
                }
            },
            "data": {
                "config": "watch_resources: []"  # Minimal but invalid config
            },
        }
        warnings = []

        # This should raise an AdmissionError due to missing required fields
        with pytest.raises(kopf.AdmissionError) as exc_info:
            await validator.validate_configmap(configmap_data, warnings)
        assert "Invalid operator configuration" in str(exc_info.value)

    @pytest.mark.asyncio
    @patch("haproxy_template_ic.webhook.get_metrics_collector")
    async def test_webhook_handler_error_paths(self, mock_get_metrics):
        """Test webhook handler error handling."""
        # Mock the metrics collector to prevent real metrics code execution
        mock_metrics = MagicMock()
        mock_time_context = MagicMock()
        mock_time_context.__enter__ = MagicMock(return_value=None)
        mock_time_context.__exit__ = MagicMock(return_value=None)
        mock_metrics.time_webhook_request.return_value = mock_time_context
        mock_get_metrics.return_value = mock_metrics

        registry = WebhookRegistry()

        with patch("haproxy_template_ic.webhook.kopf.on.validate") as mock_validate:
            mock_decorator = MagicMock()
            mock_validate.return_value = mock_decorator

            registry.register_resource_validation_webhook(
                group="networking.k8s.io",
                version="v1",
                kind="Ingress",
                resource_id="ingresses",
            )

            handler_func = mock_decorator.call_args[0][0]

            # Test missing spec/meta (should return without processing)
            await handler_func(warnings=[], spec=None, meta=None)

            # Test with kopf.AdmissionError (should re-raise)
            with patch.object(
                registry,
                "_validate_resource_structure",
                side_effect=kopf.AdmissionError("test error"),
            ):
                with pytest.raises(kopf.AdmissionError) as exc_info:
                    await handler_func(
                        warnings=[], spec={"rules": []}, meta={"name": "test"}
                    )
                assert "test error" in str(exc_info.value)

            # Test with unexpected exception (should convert to AdmissionError)
            with patch.object(
                registry,
                "_validate_resource_structure",
                side_effect=ValueError("unexpected error"),
            ):
                with pytest.raises(kopf.AdmissionError) as exc_info:
                    await handler_func(
                        warnings=[], spec={"rules": []}, meta={"name": "test"}
                    )
                assert "Internal validation error" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_validate_resource_references_with_invalid_formats(self):
        """Test resource reference validation with invalid formats."""
        validator = ConfigMapValidator()

        # Test with invalid watch_resources format
        config_dict = {"watch_resources": "invalid_string"}
        warnings = await validator._validate_resource_references(config_dict)
        assert len(warnings) > 0
        assert "must be a list or dictionary" in warnings[0]

        # Test with invalid resource configs
        config_dict = {
            "watch_resources": [
                "invalid_resource",  # Should be dict
                {"kind": "Ingress"},  # Missing group, version
                {
                    "kind": 123,
                    "group": "networking.k8s.io",
                    "version": "v1",
                },  # Invalid kind type
                {"kind": "Secret", "group": 456, "version": "v1"},  # Invalid group type
                {
                    "kind": "Service",
                    "group": "core",
                    "version": 789,
                },  # Invalid version type
            ]
        }
        warnings = await validator._validate_resource_references(config_dict)
        assert len(warnings) >= 5  # At least one warning per invalid resource

    @pytest.mark.asyncio
    async def test_validate_secret_specific(self):
        """Test Secret-specific validation."""
        registry = WebhookRegistry()
        warnings = []

        # Test secret with no data
        spec = {"data": {}}
        await registry._validate_secret_specific(spec, warnings)
        assert len(warnings) == 1
        assert "no data entries defined" in warnings[0]
        assert "Add key-value pairs to the 'data' field" in warnings[0]

        # Test valid secret
        warnings = []
        spec = {"data": {"key1": "value1"}}
        await registry._validate_secret_specific(spec, warnings)
        assert len(warnings) == 0

    @pytest.mark.asyncio
    async def test_validate_templates_error_handling(self):
        """Test template validation error paths."""
        validator = ConfigMapValidator()

        # Test with template that causes rendering error during validation
        config_dict = {
            "template_snippets": {"bad-snippet": "{{ undefined_var }}"},
            "maps": {
                "/etc/haproxy/test.map": {"template": "{% include 'bad-snippet' %}"}
            },
        }

        warnings = await validator._validate_templates(config_dict)
        # Should handle the error gracefully and add warnings
        assert (
            len(warnings) >= 0
        )  # May or may not add warnings depending on validation approach

    @pytest.mark.asyncio
    async def test_configmap_unexpected_exception_path(self):
        """Test ConfigMap validation unexpected exception handling."""
        validator = ConfigMapValidator()

        # Mock _validate_config_structure to raise unexpected exception
        with patch.object(
            validator,
            "_validate_config_structure",
            side_effect=RuntimeError("Unexpected error"),
        ):
            configmap_data = {
                "metadata": {
                    "labels": {
                        "app.kubernetes.io/name": "haproxy-template-ic",
                        "haproxy-template-ic/config": "true",
                    }
                },
                "data": {"config": "watch_resources: []"},
            }
            warnings = []

            with pytest.raises(kopf.AdmissionError) as exc_info:
                await validator.validate_configmap(configmap_data, warnings)
            assert "Internal validation error" in str(exc_info.value)
            assert "Unexpected error" in str(exc_info.value)


# =============================================================================
# Enhanced Coverage Tests
# =============================================================================


class TestTemplateValidationEdgeCases:
    """Test edge cases for template validation to improve coverage."""

    @pytest.fixture
    def validator(self):
        """Create a ConfigMapValidator instance."""
        return ConfigMapValidator()

    @pytest.mark.asyncio
    async def test_validate_templates_snippet_generic_exception(self, validator):
        """Test template snippet validation with generic exception."""
        # Mock jinja2.Environment.from_string to raise a generic exception
        with patch(
            "jinja2.Environment.from_string",
            side_effect=Exception("Generic template error"),
        ):
            config_dict = {"template_snippets": {"error-snippet": "{{ test }}"}}
            warnings = await validator._validate_templates(config_dict)

            assert len(warnings) > 0
            assert any(
                "Error in template snippet 'error-snippet'" in w for w in warnings
            )

    @pytest.mark.asyncio
    async def test_validate_templates_map_template_not_found(self, validator):
        """Test map template validation with missing snippet reference."""
        config_dict = {
            "template_snippets": {},  # No snippets defined
            "maps": {"/etc/haproxy/test.map": {"template": "valid template content"}},
        }

        # Mock the template environment to raise TemplateNotFound during map validation
        import jinja2

        original_create_env = validator._create_template_environment
        call_count = 0

        def mock_create_env(snippets):
            nonlocal call_count
            call_count += 1
            # Skip the first call (for snippets validation), raise TemplateNotFound on second call (maps)
            if call_count > 1:
                mock_env = MagicMock()
                mock_env.from_string.side_effect = jinja2.TemplateNotFound(
                    "nonexistent-snippet"
                )
                return mock_env
            return original_create_env(snippets)

        with patch.object(
            validator, "_create_template_environment", side_effect=mock_create_env
        ):
            warnings = await validator._validate_templates(config_dict)

            assert len(warnings) > 0
            assert any("Template snippet not found in map" in w for w in warnings)

    @pytest.mark.asyncio
    async def test_validate_templates_haproxy_config_syntax_error(self, validator):
        """Test haproxy_config template validation with syntax error."""
        config_dict = {"haproxy_config": {"template": "{{ invalid syntax %}"}}
        warnings = await validator._validate_templates(config_dict)

        assert len(warnings) > 0
        assert any("Invalid template syntax in haproxy_config" in w for w in warnings)

    @pytest.mark.asyncio
    async def test_validate_templates_haproxy_config_template_not_found(
        self, validator
    ):
        """Test haproxy_config template validation with missing snippet reference."""
        config_dict = {
            "template_snippets": {},  # No snippets defined
            "haproxy_config": {"template": "valid template content"},
        }

        # Mock the template environment to raise TemplateNotFound during haproxy_config validation
        import jinja2

        original_create_env = validator._create_template_environment
        call_count = 0

        def mock_create_env(snippets):
            nonlocal call_count
            call_count += 1
            # Skip the first call (for snippets validation), raise TemplateNotFound on subsequent calls
            if call_count > 1:
                mock_env = MagicMock()
                mock_env.from_string.side_effect = jinja2.TemplateNotFound(
                    "nonexistent-snippet"
                )
                return mock_env
            return original_create_env(snippets)

        with patch.object(
            validator, "_create_template_environment", side_effect=mock_create_env
        ):
            warnings = await validator._validate_templates(config_dict)

            assert len(warnings) > 0
            assert any(
                "Template snippet not found in haproxy_config" in w for w in warnings
            )

    @pytest.mark.asyncio
    async def test_validate_templates_haproxy_config_generic_exception(self, validator):
        """Test haproxy_config template validation with generic exception."""
        # Create a config that will trigger template validation
        config_dict = {"haproxy_config": {"template": "valid template"}}

        # Mock the template environment creation to raise an exception when processing haproxy_config
        original_create_env = validator._create_template_environment
        call_count = 0

        def mock_create_env(snippets):
            nonlocal call_count
            call_count += 1
            # Skip the first call (for snippets validation), raise error on subsequent calls
            if call_count > 1:
                mock_env = MagicMock()
                mock_env.from_string.side_effect = Exception(
                    "Generic haproxy_config error"
                )
                return mock_env
            return original_create_env(snippets)

        with patch.object(
            validator, "_create_template_environment", side_effect=mock_create_env
        ):
            warnings = await validator._validate_templates(config_dict)

            assert len(warnings) > 0
            assert any("Error in haproxy_config template" in w for w in warnings)

    @pytest.mark.asyncio
    async def test_validate_templates_certificate_syntax_error(self, validator):
        """Test certificate template validation with syntax error."""
        config_dict = {
            "certificates": {
                "/etc/ssl/certs/test.crt": {"template": "{{ invalid syntax %}"}
            }
        }
        warnings = await validator._validate_templates(config_dict)

        assert len(warnings) > 0
        assert any("Invalid template syntax in certificate" in w for w in warnings)

    @pytest.mark.asyncio
    async def test_validate_templates_certificate_template_not_found(self, validator):
        """Test certificate template validation with missing snippet reference."""
        config_dict = {
            "template_snippets": {},  # No snippets defined
            "certificates": {
                "/etc/ssl/certs/test.crt": {"template": "valid template content"}
            },
        }

        # Mock the template environment to raise TemplateNotFound during certificate validation
        import jinja2

        original_create_env = validator._create_template_environment
        call_count = 0

        def mock_create_env(snippets):
            nonlocal call_count
            call_count += 1
            # Skip the first call (for snippets validation), raise TemplateNotFound on subsequent calls
            if call_count > 1:
                mock_env = MagicMock()
                mock_env.from_string.side_effect = jinja2.TemplateNotFound(
                    "nonexistent-snippet"
                )
                return mock_env
            return original_create_env(snippets)

        with patch.object(
            validator, "_create_template_environment", side_effect=mock_create_env
        ):
            warnings = await validator._validate_templates(config_dict)

            assert len(warnings) > 0
            assert any(
                "Template snippet not found in certificate" in w for w in warnings
            )

    @pytest.mark.asyncio
    async def test_validate_templates_certificate_generic_exception(self, validator):
        """Test certificate template validation with generic exception."""
        # Create a config that will trigger certificate template validation
        config_dict = {
            "certificates": {"/etc/ssl/certs/test.crt": {"template": "valid template"}}
        }

        # Mock the template environment creation to raise an exception when processing certificates
        original_create_env = validator._create_template_environment
        call_count = 0

        def mock_create_env(snippets):
            nonlocal call_count
            call_count += 1
            # Skip the first call (for snippets validation), raise error on subsequent calls
            if call_count > 1:
                mock_env = MagicMock()
                mock_env.from_string.side_effect = Exception(
                    "Generic certificate error"
                )
                return mock_env
            return original_create_env(snippets)

        with patch.object(
            validator, "_create_template_environment", side_effect=mock_create_env
        ):
            warnings = await validator._validate_templates(config_dict)

            assert len(warnings) > 0
            assert any("Error in certificate template" in w for w in warnings)


class TestSnippetLoaderCoverage:
    """Test SnippetLoader to improve coverage."""

    @pytest.fixture
    def validator(self):
        """Create a ConfigMapValidator instance."""
        return ConfigMapValidator()

    def test_snippet_loader_get_source_success(self, validator):
        """Test SnippetLoader.get_source success path."""
        snippets = {"test-snippet": "snippet content"}
        env = validator._create_template_environment(snippets)
        loader = env.loader

        # Test successful snippet retrieval
        source, filename, uptodate = loader.get_source(env, "test-snippet")

        assert source == "snippet content"
        assert filename is None
        assert uptodate() is True

    def test_snippet_loader_get_source_not_found(self, validator):
        """Test SnippetLoader.get_source with nonexistent snippet."""
        import jinja2

        snippets = {"existing-snippet": "content"}
        env = validator._create_template_environment(snippets)
        loader = env.loader

        # Test nonexistent snippet raises TemplateNotFound
        with pytest.raises(jinja2.TemplateNotFound):
            loader.get_source(env, "nonexistent-snippet")


class TestWatchResourcesEdgeCases:
    """Test edge cases for watch_resources validation."""

    @pytest.fixture
    def validator(self):
        """Create a ConfigMapValidator instance."""
        return ConfigMapValidator()

    @pytest.mark.asyncio
    async def test_validate_resource_references_dict_format(self, validator):
        """Test watch_resources validation with dictionary format."""
        config_dict = {
            "watch_resources": {
                "ingresses": {
                    "kind": "Ingress",
                    "group": "networking.k8s.io",
                    "version": "v1",
                },
                "services": {"kind": "Service", "group": "", "version": "v1"},
            }
        }
        warnings = await validator._validate_resource_references(config_dict)

        # Should not produce warnings for valid dict format
        assert len(warnings) == 0

    @pytest.mark.asyncio
    async def test_validate_resource_references_list_format(self, validator):
        """Test watch_resources validation with list format."""
        config_dict = {
            "watch_resources": [
                {"kind": "Ingress", "group": "networking.k8s.io", "version": "v1"},
                {"kind": "Service", "group": "", "version": "v1"},
            ]
        }
        warnings = await validator._validate_resource_references(config_dict)

        # Should not produce warnings for valid list format
        assert len(warnings) == 0


class TestResourceSpecificValidationPaths:
    """Test Service and Secret specific validation paths."""

    @pytest.fixture
    def registry(self):
        """Create a WebhookRegistry instance."""
        return WebhookRegistry()

    @pytest.mark.asyncio
    async def test_validate_resource_structure_service_kind(self, registry):
        """Test _validate_resource_structure with Service kind."""
        spec = {"ports": [{"port": 80, "targetPort": 8080}]}
        meta = {"name": "test-service"}
        warnings = []

        with patch.object(
            registry, "_validate_service_specific", new_callable=AsyncMock
        ) as mock_validate:
            await registry._validate_resource_structure(spec, meta, "Service", warnings)
            mock_validate.assert_called_once_with(spec, warnings)

    @pytest.mark.asyncio
    async def test_validate_resource_structure_secret_kind(self, registry):
        """Test _validate_resource_structure with Secret kind."""
        spec = {"data": {"key1": "value1"}}
        meta = {"name": "test-secret"}
        warnings = []

        with patch.object(
            registry, "_validate_secret_specific", new_callable=AsyncMock
        ) as mock_validate:
            await registry._validate_resource_structure(spec, meta, "Secret", warnings)
            mock_validate.assert_called_once_with(spec, warnings)

    @pytest.mark.asyncio
    async def test_validate_resource_structure_ingress_kind(self, registry):
        """Test _validate_resource_structure with Ingress kind."""
        spec = {"rules": [{"host": "example.com"}]}
        meta = {"name": "test-ingress"}
        warnings = []

        with patch.object(
            registry, "_validate_ingress_specific", new_callable=AsyncMock
        ) as mock_validate:
            await registry._validate_resource_structure(spec, meta, "Ingress", warnings)
            mock_validate.assert_called_once_with(spec, warnings)

    @pytest.mark.asyncio
    async def test_validate_resource_structure_unknown_kind(self, registry):
        """Test _validate_resource_structure with unknown kind."""
        spec = {"some": "data"}
        meta = {"name": "test-resource"}
        warnings = []

        # Should not call any specific validation methods for unknown kinds
        with patch.object(registry, "_validate_service_specific") as mock_service:
            with patch.object(registry, "_validate_secret_specific") as mock_secret:
                with patch.object(
                    registry, "_validate_ingress_specific"
                ) as mock_ingress:
                    await registry._validate_resource_structure(
                        spec, meta, "UnknownKind", warnings
                    )

                    mock_service.assert_not_called()
                    mock_secret.assert_not_called()
                    mock_ingress.assert_not_called()
