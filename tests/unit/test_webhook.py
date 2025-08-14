"""
Simplified unit tests for webhook validation functionality.

Tests the essential webhook validation components focusing on the
resource-specific webhook registration functionality.
"""

import pytest
from unittest.mock import MagicMock, patch
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

        # Verify kopf.on.validate was called with correct parameters
        mock_kopf_validate.assert_called_once_with("networking.k8s.io", "v1", "Ingress")
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
    async def test_validate_ingress_specific_no_rules(self, registry):
        """Test Ingress validation warns about missing rules."""
        spec = {"rules": []}
        warnings = []

        await registry._validate_ingress_specific(spec, warnings)
        assert len(warnings) == 1
        assert "no rules defined" in warnings[0]

    @pytest.mark.asyncio
    async def test_validate_service_specific_no_ports(self, registry):
        """Test Service validation warns about missing ports."""
        spec = {"ports": []}
        warnings = []

        await registry._validate_service_specific(spec, warnings)
        assert len(warnings) == 1
        assert "no ports defined" in warnings[0]


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

        # Verify webhook was registered
        mock_kopf_validate.assert_called_with("networking.k8s.io", "v1", "Ingress")

    @patch("haproxy_template_ic.webhook.get_metrics_collector")
    def test_webhook_handler_with_metrics(self, mock_get_metrics):
        """Test webhook handler includes metrics recording."""
        mock_metrics = MagicMock()
        mock_time_context = MagicMock()
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
