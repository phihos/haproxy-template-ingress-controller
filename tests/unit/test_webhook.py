"""
Unit tests for webhook validation functionality.

Tests the webhook validation system including ConfigMapValidator and
WebhookRegistry classes.
"""

import pytest
from unittest.mock import Mock
import yaml
import kopf

import haproxy_template_ic.webhook as webhook_module
from haproxy_template_ic.webhook import (
    register_validation_webhooks_from_config,
    _is_haproxy_template_ic_configmap,
    _extract_config_data,
    _validate_resource_structure,
    _validate_ingress_specific,
    _validate_service_specific,
    _validate_secret_specific,
)
from tests.unit.conftest import (
    assert_raises_admission_error,
    create_logger_with_handlers_mock,
    mock_module_attributes,
    mock_yaml_operations,
)


def test_is_haproxy_template_ic_configmap_with_label():
    """Test identification via app label."""
    configmap_data = {
        "metadata": {"labels": {"app.kubernetes.io/name": "haproxy-template-ic"}}
    }
    assert _is_haproxy_template_ic_configmap(configmap_data)


def test_is_haproxy_template_ic_configmap_with_haproxy_label():
    """Test identification via haproxy-template-ic label."""
    configmap_data = {"metadata": {"labels": {"haproxy-template-ic/config": "true"}}}
    assert _is_haproxy_template_ic_configmap(configmap_data)


def test_is_haproxy_template_ic_configmap_with_annotation():
    """Test identification via annotation."""
    configmap_data = {"metadata": {"annotations": {"haproxy-template-ic": "enabled"}}}
    assert _is_haproxy_template_ic_configmap(configmap_data)


def test_is_haproxy_template_ic_configmap_with_structure():
    """Test identification via config structure."""
    configmap_data = {
        "metadata": {"name": "test"},
        "data": {
            "config": yaml.dump({"pod_selector": {"match_labels": {"app": "test"}}})
        },
    }
    assert _is_haproxy_template_ic_configmap(configmap_data)


def test_is_not_haproxy_template_ic_configmap():
    """Test rejection of non-HAProxy ConfigMaps."""
    configmap_data = {
        "metadata": {"name": "other"},
        "data": {"config": "unrelated config"},
    }
    assert not _is_haproxy_template_ic_configmap(configmap_data)


def test_is_haproxy_template_ic_configmap_yaml_error():
    """Test handling of YAML parsing errors."""
    with mock_yaml_operations({"invalid: yaml: content: [unclosed": None}):
        configmap_data = {
            "metadata": {"name": "test"},
            "data": {"config": "invalid: yaml: content: [unclosed"},
        }
        # The mock will return None for invalid YAML, which should be handled gracefully
        result = _is_haproxy_template_ic_configmap(configmap_data)
        assert not result


def test_is_haproxy_template_ic_configmap_type_error():
    """Test handling of type errors in YAML processing."""
    import yaml

    mock_yaml_func = Mock(side_effect=TypeError("Invalid type for YAML parsing"))

    with mock_module_attributes(yaml, safe_load=mock_yaml_func):
        configmap_data = {
            "metadata": {"name": "test"},
            "data": {"config": "some config"},
        }
        result = _is_haproxy_template_ic_configmap(configmap_data)
        assert not result


def test_extract_config_data_success():
    """Test successful config data extraction."""
    configmap_data = {"data": {"config": "test config"}}
    result = _extract_config_data(configmap_data)
    assert result == "test config"


def test_extract_config_data_missing():
    """Test config data extraction with missing config."""
    configmap_data = {"data": {"other": "value"}}
    result = _extract_config_data(configmap_data)
    assert result is None


def test_extract_config_data_no_data():
    """Test config data extraction with no data section."""
    configmap_data = {"metadata": {"name": "test"}}
    result = _extract_config_data(configmap_data)
    assert result is None


@pytest.mark.asyncio
async def test_validate_resource_structure_basic():
    """Test basic resource structure validation."""
    spec = {"rules": [{"host": "example.com"}]}
    meta = {"name": "test-resource"}
    warnings = []

    # Should not raise exception
    await _validate_resource_structure(spec, meta, "Ingress", warnings)


@pytest.mark.asyncio
async def test_validate_resource_structure_missing_name():
    """Test resource validation with missing name."""
    spec = {}
    meta = {}  # Missing name
    warnings = []

    with assert_raises_admission_error("must have a name"):
        await _validate_resource_structure(spec, meta, "Service", warnings)


@pytest.mark.asyncio
async def test_validate_resource_structure_special_chars_warning():
    """Test resource validation with special characters in name."""
    spec = {}
    meta = {"name": "test@resource#with$special%chars"}
    warnings = []

    await _validate_resource_structure(spec, meta, "Service", warnings)
    special_char_warnings = [w for w in warnings if "special characters" in w]
    assert len(special_char_warnings) > 0


@pytest.mark.asyncio
async def test_validate_ingress_specific_no_rules():
    """Test Ingress-specific validation with no rules."""
    spec = {}  # No rules
    warnings = []

    await _validate_ingress_specific(spec, warnings)
    rule_warnings = [w for w in warnings if "no rules defined" in w]
    assert len(rule_warnings) > 0


@pytest.mark.asyncio
async def test_validate_ingress_specific_empty_rules():
    """Test Ingress-specific validation with empty rules."""
    spec = {"rules": [{}]}  # Empty rule
    warnings = []

    await _validate_ingress_specific(spec, warnings)
    rule_warnings = [w for w in warnings if "neither host nor http" in w]
    assert len(rule_warnings) > 0


@pytest.mark.asyncio
async def test_validate_ingress_specific_valid_rules():
    """Test Ingress-specific validation with valid rules."""
    spec = {"rules": [{"host": "example.com", "http": {"paths": []}}]}
    warnings = []

    await _validate_ingress_specific(spec, warnings)
    assert len(warnings) == 0


@pytest.mark.asyncio
async def test_validate_service_specific_no_ports():
    """Test Service-specific validation with no ports."""
    spec = {}  # No ports
    warnings = []

    await _validate_service_specific(spec, warnings)
    port_warnings = [w for w in warnings if "no ports defined" in w]
    assert len(port_warnings) > 0


@pytest.mark.asyncio
async def test_validate_service_specific_missing_port():
    """Test Service-specific validation with missing port field."""
    spec = {"ports": [{}]}  # Port without 'port' field
    warnings = []

    with pytest.raises(kopf.AdmissionError, match="missing 'port' field"):
        await _validate_service_specific(spec, warnings)


@pytest.mark.asyncio
async def test_validate_service_specific_valid_ports():
    """Test Service-specific validation with valid ports."""
    spec = {"ports": [{"port": 80, "targetPort": 8080}]}
    warnings = []

    await _validate_service_specific(spec, warnings)
    assert len(warnings) == 0


@pytest.mark.asyncio
async def test_validate_secret_specific_no_data():
    """Test Secret-specific validation with no data."""
    spec = {}  # No data
    warnings = []

    await _validate_secret_specific(spec, warnings)
    data_warnings = [w for w in warnings if "no data entries" in w]
    assert len(data_warnings) > 0


@pytest.mark.asyncio
async def test_validate_secret_specific_with_data():
    """Test Secret-specific validation with data."""
    spec = {"data": {"key1": "value1", "key2": "value2"}}
    warnings = []

    await _validate_secret_specific(spec, warnings)
    assert len(warnings) == 0


@pytest.mark.asyncio
async def test_validate_resource_structure_secret_kind():
    """Test resource structure validation specifically for Secret kind."""
    spec = {"data": {"key": "value"}}
    meta = {"name": "test-secret"}
    warnings = []

    # Should call secret-specific validation
    await _validate_resource_structure(spec, meta, "Secret", warnings)
    assert len(warnings) == 0


def test_register_validation_webhooks_from_config_no_resources():
    """Test registration with no watched resources."""
    config = Mock()
    config.watched_resources = {}

    # Should not raise any exceptions
    register_validation_webhooks_from_config(config)


def test_register_validation_webhooks_from_config_disabled():
    """Test registration with disabled webhooks."""
    config = Mock()
    resource_config = Mock()
    resource_config.enable_validation_webhook = False
    resource_config.kind = "Service"
    config.watched_resources = {"services": resource_config}

    # Should not raise any exceptions
    register_validation_webhooks_from_config(config)


def test_register_validation_webhooks_from_config_enabled():
    """Test registration with enabled webhooks."""
    config = Mock()
    resource_config = Mock()
    resource_config.enable_validation_webhook = True
    resource_config.kind = "Ingress"
    resource_config.api_version = "networking.k8s.io/v1"
    config.watched_resources = {"ingresses": resource_config}

    # Should not raise any exceptions - function is now stateless
    register_validation_webhooks_from_config(config)


def test_register_validation_webhooks_from_config_core_api():
    """Test registration with core API resources."""
    config = Mock()
    resource_config = Mock()
    resource_config.enable_validation_webhook = True
    resource_config.kind = "Service"
    resource_config.api_version = "v1"  # Core API, no group
    config.watched_resources = {"services": resource_config}

    # Should not raise any exceptions - function is now stateless
    register_validation_webhooks_from_config(config)


def test_register_validation_webhooks_from_config_no_attribute():
    """Test registration with config missing watched_resources."""
    config = Mock()
    del config.watched_resources  # Remove attribute

    # Should not raise any exceptions
    register_validation_webhooks_from_config(config)


def test_register_validation_webhooks_logs_enabled_webhooks():
    """Test that enabled webhooks are logged correctly."""
    mock_logger = create_logger_with_handlers_mock()

    with mock_module_attributes(webhook_module, logger=mock_logger):
        config = Mock()
        resource_config1 = Mock()
        resource_config1.enable_validation_webhook = True
        resource_config1.kind = "Ingress"
        resource_config2 = Mock()
        resource_config2.enable_validation_webhook = False
        resource_config2.kind = "Service"
        config.watched_resources = {
            "ingresses": resource_config1,
            "services": resource_config2,
        }

        register_validation_webhooks_from_config(config)

        # Should log enabled webhooks
        mock_logger.info.assert_called()
        call_args = mock_logger.info.call_args_list[0][0][0]
        assert "Webhook validation configured for: Ingress (id: ingresses)" in call_args
