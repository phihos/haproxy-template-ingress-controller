"""
Unit tests for webhook validation functionality.

Tests the webhook validation system including ConfigMapValidator and
WebhookRegistry classes.
"""

import pytest
from unittest.mock import Mock, patch
import yaml
import kopf

from haproxy_template_ic.webhook import (
    WebhookRegistry,
    register_validation_webhooks_from_config,
    _webhook_registry,
    _is_haproxy_template_ic_configmap,
    _extract_config_data,
)


class TestHelperFunctions:
    """Test the standalone helper functions."""

    def test_is_haproxy_template_ic_configmap_with_label(self):
        """Test identification via app label."""
        configmap_data = {
            "metadata": {"labels": {"app.kubernetes.io/name": "haproxy-template-ic"}}
        }
        assert _is_haproxy_template_ic_configmap(configmap_data)

    def test_is_haproxy_template_ic_configmap_with_haproxy_label(self):
        """Test identification via haproxy-template-ic label."""
        configmap_data = {
            "metadata": {"labels": {"haproxy-template-ic/config": "true"}}
        }
        assert _is_haproxy_template_ic_configmap(configmap_data)

    def test_is_haproxy_template_ic_configmap_with_annotation(self):
        """Test identification via annotation."""
        configmap_data = {
            "metadata": {"annotations": {"haproxy-template-ic": "enabled"}}
        }
        assert _is_haproxy_template_ic_configmap(configmap_data)

    def test_is_haproxy_template_ic_configmap_with_structure(self):
        """Test identification via config structure."""
        configmap_data = {
            "metadata": {"name": "test"},
            "data": {
                "config": yaml.dump({"pod_selector": {"match_labels": {"app": "test"}}})
            },
        }
        assert _is_haproxy_template_ic_configmap(configmap_data)

    def test_is_not_haproxy_template_ic_configmap(self):
        """Test rejection of non-HAProxy ConfigMaps."""
        configmap_data = {
            "metadata": {"name": "other"},
            "data": {"config": "unrelated config"},
        }
        assert not _is_haproxy_template_ic_configmap(configmap_data)

    def test_is_haproxy_template_ic_configmap_yaml_error(self):
        """Test handling of YAML parsing errors."""
        configmap_data = {
            "metadata": {"name": "test"},
            "data": {"config": "invalid: yaml: content: [unclosed"},
        }
        assert not _is_haproxy_template_ic_configmap(configmap_data)

    def test_is_haproxy_template_ic_configmap_type_error(self):
        """Test handling of type errors in YAML processing."""
        with patch("yaml.safe_load") as mock_yaml:
            mock_yaml.side_effect = TypeError("Invalid type for YAML parsing")

            configmap_data = {
                "metadata": {"name": "test"},
                "data": {"config": "some config"},
            }
            assert not _is_haproxy_template_ic_configmap(configmap_data)

    def test_extract_config_data_success(self):
        """Test successful config data extraction."""
        configmap_data = {"data": {"config": "test config"}}
        result = _extract_config_data(configmap_data)
        assert result == "test config"

    def test_extract_config_data_missing(self):
        """Test config data extraction with missing config."""
        configmap_data = {"data": {"other": "value"}}
        result = _extract_config_data(configmap_data)
        assert result is None

    def test_extract_config_data_no_data(self):
        """Test config data extraction with no data section."""
        configmap_data = {"metadata": {"name": "test"}}
        result = _extract_config_data(configmap_data)
        assert result is None


class TestWebhookRegistry:
    """Test the WebhookRegistry class."""

    @pytest.fixture
    def registry(self):
        """Create a WebhookRegistry instance."""
        return WebhookRegistry()

    def test_register_resource_validation_webhook(self, registry):
        """Test webhook registration."""
        with patch("kopf.on.validate") as mock_validate:
            mock_validate.return_value = lambda func: func

            registry.register_resource_validation_webhook(
                group="networking.k8s.io",
                version="v1",
                kind="Ingress",
                resource_id="ingresses",
            )

            handler_key = "networking.k8s.io/v1/Ingress"
            assert handler_key in registry.registered_handlers
            mock_validate.assert_called()

    @pytest.mark.asyncio
    async def test_register_and_execute_validation_handler(self, registry):
        """Test webhook registration and handler execution."""
        # Capture the handler function when it's registered
        captured_handler = None

        def mock_validate_decorator(*args, **kwargs):
            def decorator(func):
                nonlocal captured_handler
                captured_handler = func
                return func

            return decorator

        with patch("kopf.on.validate", side_effect=mock_validate_decorator):
            registry.register_resource_validation_webhook(
                group="v1",
                version="",
                kind="Service",
                resource_id="services",
            )

        # Now test the captured handler with various scenarios
        assert captured_handler is not None

        # Test None values (should return early)
        await captured_handler(spec=None, meta=None, warnings=[])

        # Test normal validation
        await captured_handler(
            spec={"ports": [{"port": 80}]}, meta={"name": "test-service"}, warnings=[]
        )

        # Test admission error case
        with pytest.raises(kopf.AdmissionError):
            await captured_handler(spec={}, meta={}, warnings=[])

        # Test internal error case by mocking _validate_resource_structure to raise
        with patch.object(
            registry,
            "_validate_resource_structure",
            side_effect=ValueError("Test error"),
        ):
            with pytest.raises(kopf.AdmissionError, match="Internal validation error"):
                await captured_handler(spec={}, meta={"name": "test"}, warnings=[])

    def test_register_resource_validation_webhook_duplicate(self, registry):
        """Test duplicate webhook registration is handled."""
        with patch("kopf.on.validate") as mock_validate:
            mock_validate.return_value = lambda func: func

            # Register twice
            registry.register_resource_validation_webhook(
                group="v1", version="", kind="Service", resource_id="services"
            )
            registry.register_resource_validation_webhook(
                group="v1", version="", kind="Service", resource_id="services"
            )

            # Should only be called once
            assert mock_validate.call_count == 1

    @pytest.mark.asyncio
    async def test_validate_resource_structure_basic(self, registry):
        """Test basic resource structure validation."""
        spec = {"rules": [{"host": "example.com"}]}
        meta = {"name": "test-resource"}
        warnings = []

        # Should not raise exception
        await registry._validate_resource_structure(spec, meta, "Ingress", warnings)

    @pytest.mark.asyncio
    async def test_validate_resource_structure_missing_name(self, registry):
        """Test resource validation with missing name."""
        spec = {}
        meta = {}  # Missing name
        warnings = []

        with pytest.raises(kopf.AdmissionError, match="must have a name"):
            await registry._validate_resource_structure(spec, meta, "Service", warnings)

    @pytest.mark.asyncio
    async def test_validate_resource_structure_special_chars_warning(self, registry):
        """Test resource validation with special characters in name."""
        spec = {}
        meta = {"name": "test@resource#with$special%chars"}
        warnings = []

        await registry._validate_resource_structure(spec, meta, "Service", warnings)
        special_char_warnings = [w for w in warnings if "special characters" in w]
        assert len(special_char_warnings) > 0

    @pytest.mark.asyncio
    async def test_validate_ingress_specific_no_rules(self, registry):
        """Test Ingress-specific validation with no rules."""
        spec = {}  # No rules
        warnings = []

        await registry._validate_ingress_specific(spec, warnings)
        rule_warnings = [w for w in warnings if "no rules defined" in w]
        assert len(rule_warnings) > 0

    @pytest.mark.asyncio
    async def test_validate_ingress_specific_empty_rules(self, registry):
        """Test Ingress-specific validation with empty rules."""
        spec = {"rules": [{}]}  # Empty rule
        warnings = []

        await registry._validate_ingress_specific(spec, warnings)
        rule_warnings = [w for w in warnings if "neither host nor http" in w]
        assert len(rule_warnings) > 0

    @pytest.mark.asyncio
    async def test_validate_ingress_specific_valid_rules(self, registry):
        """Test Ingress-specific validation with valid rules."""
        spec = {"rules": [{"host": "example.com", "http": {"paths": []}}]}
        warnings = []

        await registry._validate_ingress_specific(spec, warnings)
        assert len(warnings) == 0

    @pytest.mark.asyncio
    async def test_validate_service_specific_no_ports(self, registry):
        """Test Service-specific validation with no ports."""
        spec = {}  # No ports
        warnings = []

        await registry._validate_service_specific(spec, warnings)
        port_warnings = [w for w in warnings if "no ports defined" in w]
        assert len(port_warnings) > 0

    @pytest.mark.asyncio
    async def test_validate_service_specific_missing_port(self, registry):
        """Test Service-specific validation with missing port field."""
        spec = {"ports": [{}]}  # Port without 'port' field
        warnings = []

        with pytest.raises(kopf.AdmissionError, match="missing 'port' field"):
            await registry._validate_service_specific(spec, warnings)

    @pytest.mark.asyncio
    async def test_validate_service_specific_valid_ports(self, registry):
        """Test Service-specific validation with valid ports."""
        spec = {"ports": [{"port": 80, "targetPort": 8080}]}
        warnings = []

        await registry._validate_service_specific(spec, warnings)
        assert len(warnings) == 0

    @pytest.mark.asyncio
    async def test_validate_secret_specific_no_data(self, registry):
        """Test Secret-specific validation with no data."""
        spec = {}  # No data
        warnings = []

        await registry._validate_secret_specific(spec, warnings)
        data_warnings = [w for w in warnings if "no data entries" in w]
        assert len(data_warnings) > 0

    @pytest.mark.asyncio
    async def test_validate_secret_specific_with_data(self, registry):
        """Test Secret-specific validation with data."""
        spec = {"data": {"key1": "value1", "key2": "value2"}}
        warnings = []

        await registry._validate_secret_specific(spec, warnings)
        assert len(warnings) == 0

    @pytest.mark.asyncio
    async def test_validate_resource_structure_secret_kind(self, registry):
        """Test resource structure validation specifically for Secret kind."""
        spec = {"data": {"key": "value"}}
        meta = {"name": "test-secret"}
        warnings = []

        # Should call secret-specific validation
        await registry._validate_resource_structure(spec, meta, "Secret", warnings)
        assert len(warnings) == 0

    @pytest.mark.asyncio
    async def test_resource_validation_handler_none_values(self, registry):
        """Test resource validation handler with None spec/meta."""
        from haproxy_template_ic.metrics import get_metrics_collector

        async def resource_validation_handler(**kwargs):
            metrics = get_metrics_collector()

            try:
                with metrics.time_webhook_request():
                    warnings = kwargs.get("warnings", [])
                    spec = kwargs.get("spec", {})
                    meta = kwargs.get("meta", {})

                    if spec is None or meta is None:
                        return  # Should return early for None values

                    await registry._validate_resource_structure(
                        spec, meta, "Service", warnings
                    )
            except kopf.AdmissionError:
                raise
            except Exception as e:
                raise kopf.AdmissionError(f"Internal validation error: {e}")

        # Test with None values - should return without error
        await resource_validation_handler(spec=None, meta=None, warnings=[])

    @pytest.mark.asyncio
    async def test_resource_validation_handler_internal_error(self, registry):
        """Test resource validation handler with internal error."""
        from haproxy_template_ic.metrics import get_metrics_collector

        async def resource_validation_handler(**kwargs):
            metrics = get_metrics_collector()

            try:
                with metrics.time_webhook_request():
                    spec = kwargs.get("spec", {})
                    meta = kwargs.get("meta", {})

                    if spec is None or meta is None:
                        return

                    # Force an unexpected error
                    raise ValueError("Simulated internal error")
            except kopf.AdmissionError:
                raise
            except Exception as e:
                raise kopf.AdmissionError(f"Internal validation error: {e}")

        # Test with error that should be wrapped in admission error
        with pytest.raises(kopf.AdmissionError, match="Internal validation error"):
            await resource_validation_handler(
                spec={}, meta={"name": "test"}, warnings=[]
            )


class TestRegistrationFromConfig:
    """Test configuration-based webhook registration."""

    def test_register_validation_webhooks_from_config_no_resources(self):
        """Test registration with no watched resources."""
        config = Mock()
        config.watched_resources = {}

        with patch.object(
            _webhook_registry, "register_resource_validation_webhook"
        ) as mock_register:
            register_validation_webhooks_from_config(config)
            mock_register.assert_not_called()

    def test_register_validation_webhooks_from_config_disabled(self):
        """Test registration with disabled webhooks."""
        config = Mock()
        resource_config = Mock()
        resource_config.enable_validation_webhook = False
        resource_config.kind = "Service"
        config.watched_resources = {"services": resource_config}

        with patch.object(
            _webhook_registry, "register_resource_validation_webhook"
        ) as mock_register:
            register_validation_webhooks_from_config(config)
            mock_register.assert_not_called()

    def test_register_validation_webhooks_from_config_enabled(self):
        """Test registration with enabled webhooks."""
        config = Mock()
        resource_config = Mock()
        resource_config.enable_validation_webhook = True
        resource_config.kind = "Ingress"
        resource_config.api_version = "networking.k8s.io/v1"
        config.watched_resources = {"ingresses": resource_config}

        with patch.object(
            _webhook_registry, "register_resource_validation_webhook"
        ) as mock_register:
            register_validation_webhooks_from_config(config)
            mock_register.assert_called_once_with(
                group="networking.k8s.io",
                version="v1",
                kind="Ingress",
                resource_id="ingresses",
            )

    def test_register_validation_webhooks_from_config_core_api(self):
        """Test registration with core API resources."""
        config = Mock()
        resource_config = Mock()
        resource_config.enable_validation_webhook = True
        resource_config.kind = "Service"
        resource_config.api_version = "v1"  # Core API, no group
        config.watched_resources = {"services": resource_config}

        with patch.object(
            _webhook_registry, "register_resource_validation_webhook"
        ) as mock_register:
            register_validation_webhooks_from_config(config)
            mock_register.assert_called_once_with(
                group="", version="v1", kind="Service", resource_id="services"
            )

    def test_register_validation_webhooks_from_config_no_attribute(self):
        """Test registration with config missing watched_resources."""
        config = Mock()
        del config.watched_resources  # Remove attribute

        with patch.object(
            _webhook_registry, "register_resource_validation_webhook"
        ) as mock_register:
            register_validation_webhooks_from_config(config)
            mock_register.assert_not_called()


class TestGlobalInstances:
    """Test global validator and registry instances."""

    def test_global_registry_exists(self):
        """Test that global registry instance exists."""
        assert _webhook_registry is not None
        assert isinstance(_webhook_registry, WebhookRegistry)
