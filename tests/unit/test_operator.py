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
    synchronize_with_haproxy_instances,
    setup_resource_watchers,
    initialize_configuration,
    _is_valid_resource,
    get_current_namespace,
)
from haproxy_template_ic.config_models import (
    Config,
    MapConfig,
    PodSelector,
    HAProxyConfigContext,
    RenderedMap,
    RenderedConfig,
    RenderedCertificate,
    TemplateContext,
    WatchResourceConfig,
    config_from_dict,
)
from haproxy_template_ic.templating import TemplateRenderer
from jinja2 import Template


# =============================================================================
# Configuration Management Tests
# =============================================================================


@pytest.mark.asyncio
async def test_load_config_from_configmap_success():
    """Test successful config loading from ConfigMap."""
    config_data = {
        "pod_selector": {"match_labels": {"app": "test"}},
        "haproxy_config": {"template": "global\n    daemon"},
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
@patch("haproxy_template_ic.operator.get_current_namespace")
async def test_handle_configmap_change_with_change(mock_get_namespace):
    """Test ConfigMap change handler when change is detected."""
    mock_get_namespace.return_value = "default"
    memo = MagicMock()
    memo.config = Config(
        pod_selector=PodSelector(match_labels={"app": "old"}),
        haproxy_config=MapConfig(template="global\n    daemon"),
    )
    event = {
        "object": {
            "data": {
                "config": yaml.dump(
                    {
                        "pod_selector": {"match_labels": {"app": "new"}},
                        "haproxy_config": {"template": "global\n    daemon"},
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
                haproxy_config=MapConfig(template="global\n    daemon"),
            )

            await handle_configmap_change(
                memo, event, "test-config", "MODIFIED", logger
            )

            # Should trigger reload since config changed
            mock_trigger.assert_called_once_with(memo)


@pytest.mark.asyncio
@patch("haproxy_template_ic.operator.get_current_namespace")
async def test_handle_configmap_change_no_change(mock_get_namespace):
    """Test ConfigMap change handler when no change is detected."""
    mock_get_namespace.return_value = "default"
    memo = MagicMock()
    config = Config(
        pod_selector=PodSelector(match_labels={"app": "test"}),
        haproxy_config=MapConfig(template="global\n    daemon"),
    )
    memo.config = config

    event = {
        "object": {
            "data": {
                "config": yaml.dump(
                    {
                        "pod_selector": {"match_labels": {"app": "test"}},
                        "haproxy_config": {"template": "global\n    daemon"},
                    },
                    Dumper=yaml.CDumper,
                )
            }
        }
    }
    logger = MagicMock()

    with patch("haproxy_template_ic.operator.load_config_from_configmap") as mock_load:
        with patch("haproxy_template_ic.operator.trigger_reload") as mock_trigger:
            mock_load.return_value = config  # Same config object

            await handle_configmap_change(
                memo, event, "test-config", "MODIFIED", logger
            )

            # Should not trigger reload since config is the same
            mock_trigger.assert_not_called()


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
@patch("haproxy_template_ic.operator.synchronize_with_haproxy_instances")
@patch("haproxy_template_ic.operator.get_current_namespace")
async def test_render_haproxy_templates_success(mock_get_namespace, mock_sync):
    """Test successful template rendering."""
    mock_get_namespace.return_value = "default"
    memo = MagicMock()
    memo.config = config_from_dict(
        {
            "pod_selector": {"match_labels": {"app": "test"}},
            "haproxy_config": {"template": "global\n    daemon"},
            "watched_resources": {
                "pods": {
                    "api_version": "v1",
                    "kind": "Pod",
                    "enable_validation_webhook": False,
                }
            },
            "maps": {
                "/etc/haproxy/maps/backend.map": {
                    "template": "{% for key, pod in resources.get('pods', {}).items() %}server {{ pod.metadata.name }} {{ pod.status.podIP }}:80{% endfor %}"
                }
            },
        }
    )
    memo.haproxy_config_context = HAProxyConfigContext(
        config=memo.config,
        template_context=TemplateContext(),
    )
    memo.template_renderer = TemplateRenderer.from_config(memo.config)
    memo.template_renderer = TemplateRenderer.from_config(memo.config)

    # Mock the indices with test data
    mock_indices = MagicMock()
    # Create a mock Kubernetes Pod object
    mock_pod = MagicMock()
    mock_pod.metadata.name = "test-pod"
    mock_pod.status.podIP = "10.0.1.5"

    # Mock kopf Index interface
    mock_index = MagicMock()
    mock_index.__iter__.return_value = iter(["default/test-pod"])
    mock_store = MagicMock()
    mock_store.__iter__.return_value = iter([mock_pod])
    mock_index.__getitem__.return_value = mock_store

    mock_indices.get.return_value = mock_index
    memo.indices = mock_indices

    logger = MagicMock()

    await render_haproxy_templates(memo, logger=logger)

    # Check that rendered HAProxy config was added
    assert memo.haproxy_config_context.rendered_config is not None
    rendered_config = memo.haproxy_config_context.rendered_config
    assert isinstance(rendered_config, RenderedConfig)
    assert rendered_config.content == "global\n    daemon"

    # Check that rendered map was added
    assert len(memo.haproxy_config_context.rendered_maps) == 1
    rendered_map = memo.haproxy_config_context.rendered_maps[0]
    assert isinstance(rendered_map, RenderedMap)
    assert rendered_map.path == "/etc/haproxy/maps/backend.map"
    assert "server test-pod 10.0.1.5:80" in rendered_map.content

    # Check that no certificates were rendered (none configured)
    assert len(memo.haproxy_config_context.rendered_certificates) == 0


@pytest.mark.asyncio
@patch("haproxy_template_ic.operator.synchronize_with_haproxy_instances")
@patch("haproxy_template_ic.operator.get_current_namespace")
async def test_render_haproxy_templates_with_ingress(mock_get_namespace, mock_sync):
    """Test template rendering with ingress resources like in example-configmap.yaml."""
    mock_get_namespace.return_value = "default"
    memo = MagicMock()
    memo.config = config_from_dict(
        {
            "pod_selector": {"match_labels": {"app": "test"}},
            "haproxy_config": {"template": "global\n    daemon"},
            "watched_resources": {
                "ingresses": {
                    "api_version": "networking.k8s.io/v1",
                    "kind": "Ingress",
                    "enable_validation_webhook": False,
                }
            },
            "maps": {
                "/etc/haproxy/maps/path-exact.map": {
                    "template": (
                        "{% for _, ingress in resources.get('ingresses', {}).items() %}"
                        "{% for rule in (ingress.spec.get('rules', []) | selectattr('http', 'defined')) %}"
                        "{{ rule.host }}{{ rule.http.paths[0].path }} backend_name"
                        "{% endfor %}"
                        "{% endfor %}"
                    )
                }
            },
        }
    )
    memo.haproxy_config_context = HAProxyConfigContext(
        config=memo.config,
        template_context=TemplateContext(),
    )
    memo.template_renderer = TemplateRenderer.from_config(memo.config)

    # Mock the indices with test ingress data
    mock_indices = MagicMock()
    # Create a mock Kubernetes Ingress object
    mock_ingress = MagicMock()
    mock_ingress.spec = {
        "rules": [
            {
                "host": "example.com",
                "http": {
                    "paths": [
                        {
                            "path": "/api",
                            "pathType": "Exact",
                            "backend": {
                                "service": {
                                    "name": "api-service",
                                    "port": {"number": 80},
                                }
                            },
                        }
                    ]
                },
            }
        ]
    }

    # Mock kopf Index interface
    mock_index = MagicMock()
    mock_index.__iter__.return_value = iter(["default/test-ingress"])
    mock_store = MagicMock()
    mock_store.__iter__.return_value = iter([mock_ingress])
    mock_index.__getitem__.return_value = mock_store
    mock_indices.get.return_value = mock_index
    memo.indices = mock_indices

    logger = MagicMock()

    await render_haproxy_templates(memo, logger=logger)

    # Check that rendered map was added
    assert len(memo.haproxy_config_context.rendered_maps) == 1
    rendered_map = memo.haproxy_config_context.rendered_maps[0]
    assert isinstance(rendered_map, RenderedMap)
    assert rendered_map.path == "/etc/haproxy/maps/path-exact.map"
    assert "example.com/api backend_name" in rendered_map.content


@pytest.mark.asyncio
@patch("haproxy_template_ic.operator.synchronize_with_haproxy_instances")
@patch("haproxy_template_ic.operator.get_current_namespace")
async def test_kopf_index_store_resource_access(mock_get_namespace, mock_sync):
    """Test that resources from kopf index stores have proper .spec attribute access."""
    mock_get_namespace.return_value = "default"
    memo = MagicMock()
    memo.config = config_from_dict(
        {
            "pod_selector": {"match_labels": {"app": "test"}},
            "haproxy_config": {"template": "global\n    daemon"},
            "watched_resources": {
                "ingresses": {
                    "api_version": "networking.k8s.io/v1",
                    "kind": "Ingress",
                    "enable_validation_webhook": False,
                }
            },
            "maps": {
                "/etc/haproxy/maps/test.map": {
                    # This template pattern was failing with the original error:
                    # "'kopf._core.engines.indexing.Store object' has no attribute 'spec'"
                    "template": (
                        "{% for _, ingress in resources.get('ingresses', {}).items() %}"
                        "ingress={{ ingress.spec.rules|length }}"
                        "{% endfor %}"
                    )
                }
            },
        }
    )
    memo.haproxy_config_context = HAProxyConfigContext(
        config=memo.config,
        template_context=TemplateContext(),
    )
    memo.template_renderer = TemplateRenderer.from_config(memo.config)

    # Mock kopf index store with a proper resource object
    mock_indices = MagicMock()
    mock_ingress = MagicMock()
    mock_ingress.spec = {"rules": [{"host": "test.com"}]}

    # Mock kopf Index interface
    mock_index = MagicMock()
    mock_index.__iter__.return_value = iter(["default/test-ingress"])
    mock_store = MagicMock()
    mock_store.__iter__.return_value = iter([mock_ingress])
    mock_index.__getitem__.return_value = mock_store
    mock_indices.get.return_value = mock_index
    memo.indices = mock_indices

    logger = MagicMock()

    # This should NOT raise "'kopf._core.engines.indexing.Store object' has no attribute 'spec'"
    await render_haproxy_templates(memo, logger=logger)

    # Verify the template rendered correctly
    assert len(memo.haproxy_config_context.rendered_maps) == 1
    rendered_map = memo.haproxy_config_context.rendered_maps[0]
    assert "ingress=1" in rendered_map.content


def test_jinja2_dict_access_patterns():
    """Test that Jinja2 templates work correctly with plain dictionaries.

    Jinja2 automatically converts dot notation to subscript access,
    so ingress.spec.rules becomes ingress['spec']['rules'] when needed.
    """

    # Test data resembling a Kubernetes Ingress resource
    test_data = {
        "metadata": {"name": "test-ingress", "namespace": "default"},
        "spec": {
            "rules": [
                {
                    "host": "example.com",
                    "http": {"paths": [{"path": "/api", "pathType": "Exact"}]},
                }
            ]
        },
    }

    # Test templates that use dot notation - Jinja2 should handle this automatically
    template = Template("{{ ingress.metadata.name }}")
    result = template.render(ingress=test_data)
    assert result == "test-ingress"

    template = Template("{{ ingress.spec.rules[0].host }}")
    result = template.render(ingress=test_data)
    assert result == "example.com"

    # Test templates with filters that expect dict-like access
    template = Template(
        "{% for rule in ingress.spec.rules %}{{ rule.host }}{% endfor %}"
    )
    result = template.render(ingress=test_data)
    assert result == "example.com"


@pytest.mark.asyncio
@patch("haproxy_template_ic.operator.synchronize_with_haproxy_instances")
@patch("haproxy_template_ic.operator.get_current_namespace")
@patch("haproxy_template_ic.operator.logger")
async def test_render_haproxy_templates_jinja_error(
    mock_logger, mock_get_namespace, mock_sync
):
    """Test template rendering with Jinja error."""
    mock_get_namespace.return_value = "default"
    memo = MagicMock()
    memo.config = config_from_dict(
        {
            "pod_selector": {"match_labels": {"app": "test"}},
            "haproxy_config": {"template": "global\n    daemon"},
            "watched_resources": {},
            "maps": {
                "/etc/haproxy/maps/backend.map": {
                    "template": "server {{ undefined_variable.invalid_attr }}"
                }
            },
        }
    )
    memo.haproxy_config_context = HAProxyConfigContext(
        config=memo.config,
        template_context=TemplateContext(),
    )
    memo.template_renderer = TemplateRenderer.from_config(memo.config)

    # Mock the indices
    mock_indices = MagicMock()
    # Mock empty kopf Index interface
    mock_index = MagicMock()
    mock_index.__iter__.return_value = iter([])
    mock_indices.get.return_value = mock_index
    memo.indices = mock_indices

    await render_haproxy_templates(memo)

    # Should log error but not crash
    mock_logger.error.assert_called()
    assert "Failed to render template" in mock_logger.error.call_args_list[0][0][0]
    # Sync should be called but will handle the error gracefully
    mock_sync.assert_called_once()


@pytest.mark.asyncio
@patch("haproxy_template_ic.operator.synchronize_with_haproxy_instances")
@patch("haproxy_template_ic.operator.get_current_namespace")
async def test_render_haproxy_config_with_template_variables(
    mock_get_namespace, mock_sync
):
    """Test HAProxy config rendering with template variables from resources."""
    mock_get_namespace.return_value = "default"
    memo = MagicMock()
    memo.config = config_from_dict(
        {
            "pod_selector": {"match_labels": {"app": "test"}},
            "haproxy_config": {
                "template": "global\n{% for _, pod in resources.get('pods', {}).items() %}    # Pod: {{ pod.metadata.name }}\n{% endfor %}    daemon"
            },
            "watched_resources": {
                "pods": {
                    "api_version": "v1",
                    "kind": "Pod",
                    "enable_validation_webhook": False,
                }
            },
            "maps": {},
        }
    )
    memo.haproxy_config_context = HAProxyConfigContext(
        config=memo.config,
        template_context=TemplateContext(),
    )
    memo.template_renderer = TemplateRenderer.from_config(memo.config)

    # Mock the indices with test data
    mock_indices = MagicMock()

    # Create a mock Kubernetes Pod object
    mock_pod = MagicMock()
    mock_pod.metadata.name = "test-pod"

    # Mock kopf Index interface
    mock_index = MagicMock()
    mock_index.__iter__.return_value = iter(["default/test-pod"])
    mock_store = MagicMock()
    mock_store.__iter__.return_value = iter([mock_pod])
    mock_index.__getitem__.return_value = mock_store
    mock_indices.get.return_value = mock_index
    memo.indices = mock_indices

    logger = MagicMock()

    await render_haproxy_templates(memo, logger=logger)

    # Check that rendered HAProxy config was added with template variables
    assert memo.haproxy_config_context.rendered_config is not None
    rendered_config = memo.haproxy_config_context.rendered_config
    assert isinstance(rendered_config, RenderedConfig)
    assert "global\n" in rendered_config.content
    assert "# Pod: test-pod" in rendered_config.content
    assert "daemon" in rendered_config.content


@pytest.mark.asyncio
@patch("haproxy_template_ic.operator.synchronize_with_haproxy_instances")
@patch("haproxy_template_ic.operator.get_current_namespace")
@patch("haproxy_template_ic.operator.logger")
async def test_render_haproxy_config_jinja_error(
    mock_logger, mock_get_namespace, mock_sync
):
    """Test HAProxy config rendering with Jinja error."""
    mock_get_namespace.return_value = "default"
    memo = MagicMock()
    memo.config = config_from_dict(
        {
            "pod_selector": {"match_labels": {"app": "test"}},
            "haproxy_config": {
                "template": "global\n    {{ undefined_variable.invalid_attr }}"
            },
            "watched_resources": {},
            "maps": {},
        }
    )
    memo.haproxy_config_context = HAProxyConfigContext(
        config=memo.config,
        template_context=TemplateContext(),
    )
    memo.template_renderer = TemplateRenderer.from_config(memo.config)

    # Mock the indices
    mock_indices = MagicMock()
    # Mock empty kopf Index interface
    mock_index = MagicMock()
    mock_index.__iter__.return_value = iter([])
    mock_indices.get.return_value = mock_index
    memo.indices = mock_indices

    await render_haproxy_templates(memo)

    # Should log error but not crash, and rendered_config should be None
    mock_logger.error.assert_called()
    assert "Failed to render HAProxy configuration template" in str(
        mock_logger.error.call_args
    )
    assert memo.haproxy_config_context.rendered_config is None


@pytest.mark.asyncio
@patch("haproxy_template_ic.operator.synchronize_with_haproxy_instances")
@patch("haproxy_template_ic.operator.get_current_namespace")
async def test_render_certificates_with_template_variables(
    mock_get_namespace, mock_sync
):
    """Test certificate rendering with template variables from resources."""
    mock_get_namespace.return_value = "default"
    memo = MagicMock()
    memo.config = config_from_dict(
        {
            "pod_selector": {"match_labels": {"app": "test"}},
            "haproxy_config": {"template": "global\n    daemon"},
            "watched_resources": {
                "secrets": {
                    "api_version": "v1",
                    "kind": "Secret",
                    "enable_validation_webhook": False,
                }
            },
            "maps": {},
            "certificates": {
                "/etc/ssl/certs/tls.pem": {
                    "template": (
                        "{% for _, secret in resources.get('secrets', {}).items() %}"
                        "# Certificate for {{ secret.metadata.name }}\n"
                        "{{ secret.data.get('tls.crt', 'MISSING') }}\n"
                        "{{ secret.data.get('tls.key', 'MISSING') }}\n"
                        "{% endfor %}"
                    )
                }
            },
        }
    )
    memo.haproxy_config_context = HAProxyConfigContext(
        config=memo.config,
        template_context=TemplateContext(),
    )
    memo.template_renderer = TemplateRenderer.from_config(memo.config)

    # Mock the indices with test secret data
    mock_indices = MagicMock()

    # Create a mock Kubernetes Secret object
    mock_secret = MagicMock()
    mock_secret.metadata.name = "test-secret"
    mock_secret.data = {"tls.crt": "certificate data", "tls.key": "key data"}

    # Mock kopf Index interface
    mock_index = MagicMock()
    mock_index.__iter__.return_value = iter(["default/test-secret"])
    mock_store = MagicMock()
    mock_store.__iter__.return_value = iter([mock_secret])
    mock_index.__getitem__.return_value = mock_store
    mock_indices.get.return_value = mock_index
    memo.indices = mock_indices

    logger = MagicMock()

    await render_haproxy_templates(memo, logger=logger)

    # Check that rendered certificate was added
    assert len(memo.haproxy_config_context.rendered_certificates) == 1
    rendered_certificate = memo.haproxy_config_context.rendered_certificates[0]
    assert isinstance(rendered_certificate, RenderedCertificate)
    assert rendered_certificate.path == "/etc/ssl/certs/tls.pem"
    assert "# Certificate for test-secret" in rendered_certificate.content
    assert "certificate data" in rendered_certificate.content
    assert "key data" in rendered_certificate.content


@pytest.mark.asyncio
@patch("haproxy_template_ic.operator.synchronize_with_haproxy_instances")
@patch("haproxy_template_ic.operator.get_current_namespace")
@patch("haproxy_template_ic.operator.logger")
async def test_render_certificates_jinja_error(
    mock_logger, mock_get_namespace, mock_sync
):
    """Test certificate rendering with Jinja error."""
    mock_get_namespace.return_value = "default"
    memo = MagicMock()
    memo.config = config_from_dict(
        {
            "pod_selector": {"match_labels": {"app": "test"}},
            "haproxy_config": {"template": "global\n    daemon"},
            "watched_resources": {},
            "maps": {},
            "certificates": {
                "/etc/ssl/certs/bad-cert.pem": {
                    "template": "{{ undefined_variable.invalid_attr }}"
                }
            },
        }
    )
    memo.haproxy_config_context = HAProxyConfigContext(
        config=memo.config,
        template_context=TemplateContext(),
    )
    memo.template_renderer = TemplateRenderer.from_config(memo.config)

    # Mock the indices
    mock_indices = MagicMock()
    # Mock empty kopf Index interface
    mock_index = MagicMock()
    mock_index.__iter__.return_value = iter([])
    mock_indices.get.return_value = mock_index
    memo.indices = mock_indices

    await render_haproxy_templates(memo)

    # Should log error but not crash, and rendered_certificates should be empty
    mock_logger.error.assert_called()

    # Check for certificate error in any of the error calls
    error_messages = [str(call) for call in mock_logger.error.call_args_list]
    assert any(
        "Failed to render certificate template for /etc/ssl/certs/bad-cert.pem" in msg
        for msg in error_messages
    )
    assert len(memo.haproxy_config_context.rendered_certificates) == 0
    # Sync should be called but will handle the error gracefully
    mock_sync.assert_called_once()


@pytest.mark.asyncio
@patch("haproxy_template_ic.operator.HAProxyPodDiscovery")
@patch("haproxy_template_ic.operator.ConfigSynchronizer")
@patch("haproxy_template_ic.operator.get_current_namespace")
async def test_synchronize_with_haproxy_instances_success(
    mock_get_namespace, mock_synchronizer_class, mock_discovery_class
):
    """Test successful HAProxy instance synchronization."""
    memo = MagicMock()
    memo.config.pod_selector = PodSelector(match_labels={"app": "haproxy"})
    memo.config.dataplane_auth.username = "admin"
    memo.config.dataplane_auth.password = "adminpass"
    memo.haproxy_config_context.rendered_config = RenderedConfig(
        content="global\n    daemon", config=memo.config
    )

    # Mock dependencies
    mock_get_namespace.return_value = "default"
    mock_discovery = MagicMock()
    mock_discovery_class.return_value = mock_discovery

    mock_synchronizer = MagicMock()
    mock_synchronizer_class.return_value = mock_synchronizer

    # Mock successful sync results
    from haproxy_template_ic.dataplane import SyncResult

    mock_instance = MagicMock()
    mock_instance.name = "default/haproxy-1"

    success_result = SyncResult(
        success=True, instance=mock_instance, config_version="123"
    )
    mock_synchronizer.synchronize_configuration.return_value = [success_result]

    # Call the function
    await synchronize_with_haproxy_instances(memo)

    # Verify calls
    mock_discovery_class.assert_called_once_with(
        pod_selector=memo.config.pod_selector, namespace="default"
    )
    mock_synchronizer_class.assert_called_once_with(
        mock_discovery, dataplane_auth=("admin", "adminpass")
    )
    mock_synchronizer.synchronize_configuration.assert_called_once_with(
        memo.haproxy_config_context
    )


@pytest.mark.asyncio
async def test_synchronize_with_haproxy_instances_no_pod_selector():
    """Test synchronization with no pod selector configured."""
    memo = MagicMock()
    memo.config.pod_selector = None

    # Should return early without attempting synchronization
    await synchronize_with_haproxy_instances(memo)

    # No assertions needed - function should just log and return


@pytest.mark.asyncio
async def test_synchronize_with_haproxy_instances_no_rendered_config():
    """Test synchronization with no rendered HAProxy config."""
    memo = MagicMock()
    memo.config.pod_selector = PodSelector(match_labels={"app": "haproxy"})
    memo.haproxy_config_context.rendered_config = None

    # Should return early without attempting synchronization
    await synchronize_with_haproxy_instances(memo)

    # No assertions needed - function should just log and return


@pytest.mark.asyncio
@patch("haproxy_template_ic.operator.HAProxyPodDiscovery")
@patch("haproxy_template_ic.operator.ConfigSynchronizer")
@patch("haproxy_template_ic.operator.get_current_namespace")
async def test_synchronize_with_haproxy_instances_validation_error(
    mock_get_namespace, mock_synchronizer_class, mock_discovery_class
):
    """Test synchronization handling validation errors."""
    from haproxy_template_ic.dataplane import ValidationError

    memo = MagicMock()
    memo.config.pod_selector = PodSelector(match_labels={"app": "haproxy"})
    memo.haproxy_config_context.rendered_config = RenderedConfig(
        content="global\n    daemon", config=memo.config
    )

    # Mock validation error
    mock_get_namespace.return_value = "default"
    mock_discovery = MagicMock()
    mock_discovery_class.return_value = mock_discovery

    mock_synchronizer = MagicMock()
    mock_synchronizer_class.return_value = mock_synchronizer
    mock_synchronizer.synchronize_configuration.side_effect = ValidationError(
        "Config invalid"
    )

    # Should not raise exception, just log error
    await synchronize_with_haproxy_instances(memo)


@pytest.mark.asyncio
@patch("haproxy_template_ic.operator.HAProxyPodDiscovery")
@patch("haproxy_template_ic.operator.ConfigSynchronizer")
@patch("haproxy_template_ic.operator.get_current_namespace")
async def test_synchronize_with_haproxy_instances_with_failures(
    mock_get_namespace, mock_synchronizer_class, mock_discovery_class
):
    """Test synchronization with some instance failures."""
    memo = MagicMock()
    memo.config.pod_selector = PodSelector(match_labels={"app": "haproxy"})
    memo.haproxy_config_context.rendered_config = RenderedConfig(
        content="global\n    daemon", config=memo.config
    )

    # Mock dependencies
    mock_get_namespace.return_value = "default"
    mock_discovery = MagicMock()
    mock_discovery_class.return_value = mock_discovery

    mock_synchronizer = MagicMock()
    mock_synchronizer_class.return_value = mock_synchronizer

    # Mock mixed results
    from haproxy_template_ic.dataplane import SyncResult

    mock_success_instance = MagicMock()
    mock_success_instance.name = "default/haproxy-1"
    mock_failed_instance = MagicMock()
    mock_failed_instance.name = "default/haproxy-2"

    success_result = SyncResult(
        success=True, instance=mock_success_instance, config_version="123"
    )
    failed_result = SyncResult(
        success=False, instance=mock_failed_instance, error="Connection timeout"
    )

    mock_synchronizer.synchronize_configuration.return_value = [
        success_result,
        failed_result,
    ]

    # Should handle mixed results gracefully
    await synchronize_with_haproxy_instances(memo)


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
        metrics_port=9090,
        structured_logging=False,
        tracing_enabled=False,
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
    # Create mock memo with watch resources
    memo = MagicMock()
    memo.config.watched_resources = {
        "pods": WatchResourceConfig(
            api_version="v1",
            kind="Pod",
            enable_validation_webhook=False,
        ),
        "ingresses": WatchResourceConfig(
            api_version="networking.k8s.io/v1",
            kind="Ingress",
            enable_validation_webhook=False,
        ),
    }

    # Mock the decorators to return the original function
    mock_index.return_value = lambda func: func
    mock_event.return_value = lambda func: func

    # Call the function
    setup_resource_watchers(memo)

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
async def test_initialize_configuration(
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

    # Create test memo
    memo = MagicMock()
    cli_options = CliOptions(
        configmap_name="test-config",
        healthz_port=8080,
        verbose=1,
        socket_path="/test/socket",
        metrics_port=9090,
        structured_logging=False,
        tracing_enabled=False,
    )
    memo.cli_options = cli_options

    # Call the function
    await initialize_configuration(memo)

    # Verify the calls
    mock_get_namespace.assert_called_once()
    mock_fetch_configmap.assert_called_once_with("test-config", "test-namespace")
    mock_load_config.assert_called_once_with(mock_configmap)
    assert memo.config == mock_config


class TestGetCurrentNamespace:
    """Test get_current_namespace function."""

    @patch("os.path.exists")
    @patch("builtins.open")
    def test_get_current_namespace_from_file(self, mock_open, mock_exists):
        """Test namespace detection from service account file."""
        mock_exists.return_value = True
        mock_file = MagicMock()
        mock_file.read.return_value = "test-namespace\n"
        mock_open.return_value.__enter__.return_value = mock_file

        result = get_current_namespace()

        assert result == "test-namespace"
        mock_open.assert_called_once_with(
            "/var/run/secrets/kubernetes.io/serviceaccount/namespace"
        )

    @patch("os.path.exists")
    @patch("haproxy_template_ic.operator.config.list_kube_config_contexts")
    def test_get_current_namespace_from_kube_config(
        self, mock_list_contexts, mock_exists
    ):
        """Test namespace detection from kube config."""
        mock_exists.return_value = False
        mock_list_contexts.return_value = (
            [],
            {"context": {"namespace": "kube-namespace"}},
        )

        result = get_current_namespace()

        assert result == "kube-namespace"

    @patch("os.path.exists")
    @patch("haproxy_template_ic.operator.config.list_kube_config_contexts")
    def test_get_current_namespace_kube_config_error(
        self, mock_list_contexts, mock_exists
    ):
        """Test namespace detection with kube config error."""
        mock_exists.return_value = False
        mock_list_contexts.side_effect = KeyError("No context")

        result = get_current_namespace()

        assert result == "default"

    @patch("os.path.exists")
    @patch("haproxy_template_ic.operator.config.list_kube_config_contexts")
    def test_get_current_namespace_non_string_namespace(
        self, mock_list_contexts, mock_exists
    ):
        """Test namespace detection with non-string namespace."""
        mock_exists.return_value = False
        mock_list_contexts.return_value = (
            [],
            {"context": {"namespace": 123}},  # Non-string namespace
        )

        result = get_current_namespace()

        assert result == "default"


class TestSynchronizeErrorPaths:
    """Test error handling paths in synchronize_with_haproxy_instances."""

    @pytest.mark.asyncio
    @patch("haproxy_template_ic.operator.HAProxyPodDiscovery")
    @patch("haproxy_template_ic.operator.ConfigSynchronizer")
    @patch("haproxy_template_ic.operator.get_current_namespace")
    async def test_synchronize_with_haproxy_instances_validation_sidecar_results(
        self, mock_get_namespace, mock_synchronizer_class, mock_discovery_class
    ):
        """Test synchronization with validation sidecar instances."""
        memo = MagicMock()
        memo.config.pod_selector = PodSelector(match_labels={"app": "haproxy"})
        memo.haproxy_config_context.rendered_config = RenderedConfig(
            content="global\n    daemon", config=memo.config
        )

        # Mock dependencies
        mock_get_namespace.return_value = "default"
        mock_discovery = MagicMock()
        mock_discovery_class.return_value = mock_discovery

        mock_synchronizer = MagicMock()
        mock_synchronizer_class.return_value = mock_synchronizer

        # Mock results with validation sidecars
        from haproxy_template_ic.dataplane import SyncResult

        mock_production_instance = MagicMock()
        mock_production_instance.name = "default/haproxy-1"
        mock_production_instance.is_validation_sidecar = False

        mock_validation_instance = MagicMock()
        mock_validation_instance.name = "default/haproxy-validation"
        mock_validation_instance.is_validation_sidecar = True

        success_result = SyncResult(
            success=True, instance=mock_production_instance, config_version="123"
        )
        validation_result = SyncResult(
            success=True, instance=mock_validation_instance, config_version="123"
        )

        mock_synchronizer.synchronize_configuration.return_value = [
            success_result,
            validation_result,
        ]

        # Should handle both types of instances
        await synchronize_with_haproxy_instances(memo)


# =============================================================================
# DeepDiff with Jinja Templates Tests
# =============================================================================


# TODO: These tests are for JinjaTemplateOperator which was removed
# def test_jinja_template_operator_give_up_diffing_different():
#     """Test JinjaTemplateOperator give_up_diffing method with different templates."""

#     operator = JinjaTemplateOperator()

#     # Mock level and diff_instance
#     level = MagicMock()
#     level.t1 = _make_jinja_template("global\n    daemon")
#     level.t2 = _make_jinja_template("global\n    maxconn 4096")
#     level.path.return_value = "root.haproxy_config"

#     diff_instance = MagicMock()

#     # Run give_up_diffing
#     result = operator.give_up_diffing(level, diff_instance)

#     # Should return True and call custom_report_result for different templates
#     assert result is True
#     diff_instance.custom_report_result.assert_called_once_with("values_changed", level)
#     # Verify that the level objects were temporarily replaced with source content
#     # (Note: In practice, they get restored, but during the call they contain source)


# def test_jinja_template_operator_give_up_diffing_identical():
#     """Test JinjaTemplateOperator give_up_diffing method with identical templates."""

#     operator = JinjaTemplateOperator()

#     # Mock level and diff_instance
#     level = MagicMock()
#     template_content = "global\n    daemon"
#     level.t1 = _make_jinja_template(template_content)
#     level.t2 = _make_jinja_template(template_content)
#     level.path.return_value = "root.haproxy_config"

#     diff_instance = MagicMock()

#     # Run give_up_diffing
#     result = operator.give_up_diffing(level, diff_instance)

#     # Should return True but not call custom_report_result for identical templates
#     assert result is True
#     diff_instance.custom_report_result.assert_not_called()


# def test_deepdiff_with_custom_operator_different_templates():
#     """Test DeepDiff with custom operator for different templates."""
#     from deepdiff import DeepDiff

#     # Create config objects with different templates
#     config1 = Config(
#         pod_selector=PodSelector(match_labels={"app": "test"}),
#         haproxy_config=_make_jinja_template("global\n    daemon"),
#     )
#     config2 = Config(
#         pod_selector=PodSelector(match_labels={"app": "test"}),
#         haproxy_config=_make_jinja_template("global\n    maxconn 4096"),
#     )

#     # Use custom operator - this should not raise any loader errors
#     diff = DeepDiff(config1, config2, custom_operators=[JinjaTemplateOperator()])

#     # Should detect differences without raising exceptions
#     assert diff != {}
#     assert "values_changed" in diff
#     # The important thing is that we can diff templates without errors
#     assert "root.haproxy_config" in diff["values_changed"]


# def test_deepdiff_with_custom_operator_identical_templates():
#     """Test DeepDiff with custom operator for identical templates."""
#     from deepdiff import DeepDiff

#     # Create config objects with identical templates
#     template_content = "global\n    daemon"
#     config1 = Config(
#         pod_selector=PodSelector(match_labels={"app": "test"}),
#         haproxy_config=_make_jinja_template(template_content),
#     )
#     config2 = Config(
#         pod_selector=PodSelector(match_labels={"app": "test"}),
#         haproxy_config=_make_jinja_template(template_content),
#     )

#     # Use custom operator - this should not raise any loader errors
#     diff = DeepDiff(config1, config2, custom_operators=[JinjaTemplateOperator()])

#     # Should not detect differences
#     assert diff == {}


# def test_custom_operator_prevents_loader_errors():
#     """Test that custom operator prevents 'no loader for this environment specified' errors."""
#     from deepdiff import DeepDiff

#     # Create templates that could potentially cause loader errors
#     template1 = _make_jinja_template("{% for item in items %}{{ item }}{% endfor %}")
#     template2 = _make_jinja_template("{% for user in users %}{{ user }}{% endfor %}")

#     config1 = Config(
#         pod_selector=PodSelector(match_labels={"app": "test"}),
#         haproxy_config=template1,
#     )
#     config2 = Config(
#         pod_selector=PodSelector(match_labels={"app": "test"}),
#         haproxy_config=template2,
#     )

#     # This should not raise "TypeError: no loader for this environment specified"
#     try:
#         diff = DeepDiff(config1, config2, custom_operators=[JinjaTemplateOperator()])
#         # If we get here without exception, the custom operator is working
#         assert diff != {}  # Templates are different
#     except TypeError as e:
#         if "no loader for this environment specified" in str(e):
#             pytest.fail("Custom operator failed to prevent loader error")
#         else:
#             raise


def test_resource_validation():
    """Test the _is_valid_resource function for type safety."""
    # Valid resources
    assert _is_valid_resource({"metadata": {"name": "test"}}) is True  # dict
    assert (
        _is_valid_resource([{"metadata": {"name": "test"}}]) is True
    )  # non-empty list
    assert _is_valid_resource(("item1", "item2")) is True  # non-empty tuple

    # Mock objects should be valid (they have __dict__)
    mock_obj = MagicMock()
    assert _is_valid_resource(mock_obj) is True

    # Objects with dict-like interface
    class DictLike:
        def get(self, key, default=None):
            return default

    assert _is_valid_resource(DictLike()) is True

    # Invalid resources
    assert _is_valid_resource([]) is False  # empty list
    assert _is_valid_resource(()) is False  # empty tuple
    assert _is_valid_resource("string") is False  # string primitive
    assert _is_valid_resource(123) is False  # number primitive
    assert _is_valid_resource(None) is False  # None
    assert _is_valid_resource(True) is False  # boolean primitive


# =============================================================================
# Enhanced Coverage Tests
# =============================================================================


@pytest.mark.asyncio
async def test_load_config_from_configmap_kr8s_object():
    """Test config loading from kr8s ConfigMap object (not just dict)."""
    config_data = {
        "pod_selector": {"match_labels": {"app": "test"}},
        "haproxy_config": {"template": "global\n    daemon"},
    }

    # Create mock kr8s ConfigMap object
    mock_configmap = MagicMock()
    mock_configmap.namespace = "test-namespace"
    mock_configmap.name = "test-config"
    mock_configmap.data = {"config": yaml.dump(config_data, Dumper=yaml.CDumper)}

    result = await load_config_from_configmap(mock_configmap)

    assert isinstance(result, Config)
    assert result.pod_selector.match_labels == {"app": "test"}


@pytest.mark.asyncio
async def test_fetch_configmap_success():
    """Test successful ConfigMap fetching."""
    mock_configmap = MagicMock()

    with patch("kr8s.objects.ConfigMap.get", new_callable=AsyncMock) as mock_get:
        mock_get.return_value = mock_configmap

        result = await fetch_configmap("test-config", "test-namespace")

        assert result == mock_configmap
        mock_get.assert_called_once_with("test-config", namespace="test-namespace")


@pytest.mark.asyncio
@patch("haproxy_template_ic.operator.synchronize_with_haproxy_instances")
@patch("haproxy_template_ic.operator.get_current_namespace")
async def test_render_haproxy_templates_resource_type_edge_cases(
    mock_get_namespace, mock_sync
):
    """Test resource type edge cases in render_haproxy_templates."""
    mock_get_namespace.return_value = "default"
    memo = MagicMock()
    memo.config = config_from_dict(
        {
            "pod_selector": {"match_labels": {"app": "test"}},
            "haproxy_config": {"template": "global\n    daemon"},
            "watched_resources": {
                "pods": {
                    "api_version": "v1",
                    "kind": "Pod",
                    "enable_validation_webhook": False,
                }
            },
            "maps": {},
        }
    )
    memo.haproxy_config_context = HAProxyConfigContext(
        config=memo.config,
        template_context=TemplateContext(),
    )
    memo.template_renderer = TemplateRenderer.from_config(memo.config)

    # Mock indices with different resource types
    mock_indices = MagicMock()
    mock_store = MagicMock()

    # Test list resource type
    mock_list_resource = ["resource_data"]
    # Test object with __dict__
    mock_object_resource = MagicMock()
    mock_object_resource.__dict__ = {"test": "data"}
    # Test object with metadata attribute
    mock_metadata_resource = MagicMock()
    mock_metadata_resource.metadata = {"name": "test"}
    # Test unexpected resource type (should trigger warning)
    mock_unexpected_resource = "string_resource"

    mock_store.items.return_value = [
        ("key1", mock_list_resource),
        ("key2", mock_object_resource),
        ("key3", mock_metadata_resource),
        ("key4", mock_unexpected_resource),
    ]

    mock_indices.get.return_value = mock_store
    memo.indices = mock_indices

    with patch("haproxy_template_ic.operator.logger"):
        await render_haproxy_templates(memo)

        # IndexedResourceCollection should handle all resource types without warnings
        # The implementation stores all resources and converts them to the internal format
        # No specific validation warnings are expected for resource types


@pytest.mark.asyncio
@patch("haproxy_template_ic.operator.synchronize_with_haproxy_instances")
@patch("haproxy_template_ic.operator.get_current_namespace")
async def test_render_haproxy_templates_missing_index(mock_get_namespace, mock_sync):
    """Test render_haproxy_templates when indices are missing."""
    mock_get_namespace.return_value = "default"
    memo = MagicMock()
    memo.config = config_from_dict(
        {
            "pod_selector": {"match_labels": {"app": "test"}},
            "haproxy_config": {"template": "global\n    daemon"},
            "watched_resources": {
                "pods": {
                    "api_version": "v1",
                    "kind": "Pod",
                    "enable_validation_webhook": False,
                }
            },
            "maps": {},
        }
    )
    memo.haproxy_config_context = HAProxyConfigContext(
        config=memo.config,
        template_context=TemplateContext(),
    )
    memo.template_renderer = TemplateRenderer.from_config(memo.config)

    # Mock indices that raise exception when accessing specific id
    mock_indices = MagicMock()
    mock_indices.get.side_effect = Exception("Index not found")
    memo.indices = mock_indices

    with patch("haproxy_template_ic.operator.logger") as mock_logger:
        await render_haproxy_templates(memo)

        # Should log warning and continue with empty dict
        mock_logger.warning.assert_called()
        warning_calls = [str(call) for call in mock_logger.warning.call_args_list]
        assert any("Could not retrieve index" in call for call in warning_calls)


@pytest.mark.asyncio
@patch("haproxy_template_ic.operator.HAProxyPodDiscovery")
@patch("haproxy_template_ic.operator.ConfigSynchronizer")
@patch("haproxy_template_ic.operator.get_current_namespace")
@patch("haproxy_template_ic.operator.logger")
async def test_synchronize_success_and_failure_logging(
    mock_logger, mock_get_namespace, mock_synchronizer_class, mock_discovery_class
):
    """Test synchronization success and failure logging paths."""
    memo = MagicMock()
    memo.config.pod_selector = PodSelector(match_labels={"app": "haproxy"})
    memo.haproxy_config_context.rendered_config = RenderedConfig(
        content="global\n    daemon", config=memo.config
    )

    # Mock dependencies
    mock_get_namespace.return_value = "default"
    mock_discovery = MagicMock()
    mock_discovery_class.return_value = mock_discovery

    mock_synchronizer = MagicMock()
    mock_synchronizer_class.return_value = mock_synchronizer

    # Mock mixed results - success and failure
    from haproxy_template_ic.dataplane import SyncResult

    mock_success_instance = MagicMock()
    mock_success_instance.name = "default/haproxy-1"
    mock_success_instance.is_validation_sidecar = False

    mock_failed_instance = MagicMock()
    mock_failed_instance.name = "default/haproxy-2"
    mock_failed_instance.is_validation_sidecar = False

    success_result = SyncResult(
        success=True, instance=mock_success_instance, config_version="123"
    )
    failed_result = SyncResult(
        success=False, instance=mock_failed_instance, error="Connection timeout"
    )

    mock_synchronizer.synchronize_configuration.return_value = [
        success_result,
        failed_result,
    ]

    await synchronize_with_haproxy_instances(memo)

    # Just verify the function completed without error - logging is tested elsewhere
    # The main goal is to cover the success/failure code paths


@pytest.mark.asyncio
@patch("haproxy_template_ic.operator.HAProxyPodDiscovery")
@patch("haproxy_template_ic.operator.ConfigSynchronizer")
@patch("haproxy_template_ic.operator.get_current_namespace")
@patch("haproxy_template_ic.operator.logger")
async def test_synchronize_dataplane_api_error(
    mock_logger, mock_get_namespace, mock_synchronizer_class, mock_discovery_class
):
    """Test DataplaneAPIError handling in synchronization."""
    from haproxy_template_ic.dataplane import DataplaneAPIError

    memo = MagicMock()
    memo.config.pod_selector = PodSelector(match_labels={"app": "haproxy"})
    memo.haproxy_config_context.rendered_config = RenderedConfig(
        content="global\n    daemon", config=memo.config
    )

    # Mock DataplaneAPIError
    mock_get_namespace.return_value = "default"
    mock_discovery = MagicMock()
    mock_discovery_class.return_value = mock_discovery

    mock_synchronizer = MagicMock()
    mock_synchronizer_class.return_value = mock_synchronizer
    mock_synchronizer.synchronize_configuration.side_effect = DataplaneAPIError(
        "API connection failed"
    )

    await synchronize_with_haproxy_instances(memo)

    # Should log DataplaneAPIError
    error_logs = [str(call) for call in mock_logger.error.call_args_list]
    assert any("Dataplane API error" in log for log in error_logs)


@pytest.mark.asyncio
@patch("haproxy_template_ic.operator.get_current_namespace")
@patch("haproxy_template_ic.operator.fetch_configmap")
@patch("haproxy_template_ic.operator.load_config_from_configmap")
@patch("haproxy_template_ic.operator.logger")
async def test_initialize_configuration_failure(
    mock_logger, mock_load_config, mock_fetch_configmap, mock_get_namespace
):
    """Test initialize_configuration failure handling."""
    from haproxy_template_ic.__main__ import CliOptions

    # Set up failure scenario
    mock_get_namespace.return_value = "test-namespace"
    mock_fetch_configmap.side_effect = Exception("Network error")

    # Create test memo
    memo = MagicMock()
    cli_options = CliOptions(
        configmap_name="test-config",
        healthz_port=8080,
        verbose=1,
        socket_path="/test/socket",
        metrics_port=9090,
        structured_logging=False,
        tracing_enabled=False,
    )
    memo.cli_options = cli_options

    # Should raise the exception after logging error
    with pytest.raises(Exception, match="Network error"):
        await initialize_configuration(memo)

    # Verify error logging
    error_logs = [str(call) for call in mock_logger.error.call_args_list]
    assert any("Failed to load configuration" in log for log in error_logs)


@pytest.mark.asyncio
@patch("kopf.on.event")
@patch("haproxy_template_ic.operator.get_current_namespace")
async def test_init_watch_configmap(mock_get_namespace, mock_event):
    """Test init_watch_configmap startup handler."""
    from haproxy_template_ic.operator import init_watch_configmap
    from haproxy_template_ic.__main__ import CliOptions

    memo = MagicMock()
    cli_options = CliOptions(
        configmap_name="test-config",
        healthz_port=8080,
        verbose=1,
        socket_path="/test/socket",
        metrics_port=9090,
        structured_logging=False,
        tracing_enabled=False,
    )
    memo.cli_options = cli_options

    mock_get_namespace.return_value = "test-namespace"
    mock_event.return_value = lambda func: func  # Mock decorator

    await init_watch_configmap(memo)

    # Verify kopf.on.event was called with correct parameters
    mock_event.assert_called_once()
    call_args = mock_event.call_args
    assert "configmap" in call_args[0]
    assert "when" in call_args[1]


@pytest.mark.asyncio
@patch("asyncio.create_task")
@patch("haproxy_template_ic.operator.run_management_socket_server")
async def test_init_management_socket(mock_run_socket, mock_create_task):
    """Test init_management_socket startup handler."""
    from haproxy_template_ic.operator import init_management_socket
    from haproxy_template_ic.__main__ import CliOptions

    memo = MagicMock()
    cli_options = CliOptions(
        configmap_name="test-config",
        healthz_port=8080,
        verbose=1,
        socket_path="/test/socket",
        metrics_port=9090,
        structured_logging=False,
        tracing_enabled=False,
    )
    memo.cli_options = cli_options

    mock_task = MagicMock()
    mock_create_task.return_value = mock_task

    await init_management_socket(memo)

    # Verify task was created and stored
    mock_create_task.assert_called_once()
    assert memo.socket_server_task == mock_task


@pytest.mark.asyncio
@patch("asyncio.create_task")
@patch("haproxy_template_ic.operator.get_metrics_collector")
async def test_init_metrics_server(mock_get_metrics, mock_create_task):
    """Test init_metrics_server startup handler."""
    from haproxy_template_ic.operator import init_metrics_server
    from haproxy_template_ic.__main__ import CliOptions

    memo = MagicMock()
    cli_options = CliOptions(
        configmap_name="test-config",
        healthz_port=8080,
        verbose=1,
        socket_path="/test/socket",
        metrics_port=9090,
        structured_logging=False,
        tracing_enabled=False,
    )
    memo.cli_options = cli_options

    mock_metrics = MagicMock()

    # Create a simple async function to return as coroutine
    async def mock_start_server(port):
        pass

    mock_metrics.start_metrics_server = MagicMock(side_effect=mock_start_server)
    mock_get_metrics.return_value = mock_metrics
    mock_task = MagicMock()

    # Mock create_task to return the task and consume the coroutine
    def mock_create_task_func(coro):
        # If it's a coroutine, close it to avoid warnings
        if hasattr(coro, "close"):
            coro.close()
        return mock_task

    mock_create_task.side_effect = mock_create_task_func

    await init_metrics_server(memo)

    # Verify metrics server start was called and task was created
    mock_metrics.start_metrics_server.assert_called_once_with(9090)
    mock_create_task.assert_called_once()
    assert memo.metrics_server_task == mock_task


@patch("haproxy_template_ic.operator.logger")
def test_configure_webhook_server_no_webhooks(mock_logger):
    """Test webhook server configuration with no webhooks enabled."""
    from haproxy_template_ic.operator import configure_webhook_server

    settings = MagicMock()
    memo = MagicMock()

    # Mock config with no webhook validation enabled
    watch_config = MagicMock()
    # Use getattr with default False to simulate the actual code behavior
    watch_config.__dict__["enable_validation_webhook"] = False
    memo.config.watched_resources = {"test": watch_config}

    configure_webhook_server(settings, memo)

    # Should log and return early without configuring server
    info_logs = [str(call) for call in mock_logger.info.call_args_list]
    assert any("No validation webhooks configured" in log for log in info_logs)


@patch("os.path.exists")
@patch("tempfile.mkdtemp")
@patch("haproxy_template_ic.operator.logger")
def test_configure_webhook_server_with_existing_certs(
    mock_logger, mock_mkdtemp, mock_exists
):
    """Test webhook server configuration with existing TLS certificates."""
    from haproxy_template_ic.operator import configure_webhook_server

    settings = MagicMock()
    memo = MagicMock()

    # Mock config with webhook validation enabled
    watch_config = MagicMock()
    watch_config.enable_validation_webhook = True
    memo.config.watched_resources = {"test_resource": watch_config}

    # Mock existing certificate files
    def exists_side_effect(path):
        return path.endswith("webhook-cert.pem") or path.endswith("webhook-key.pem")

    mock_exists.side_effect = exists_side_effect
    mock_mkdtemp.return_value = "/tmp/test-ca"

    configure_webhook_server(settings, memo)

    # Should configure webhook server with existing certs
    info_logs = [str(call) for call in mock_logger.info.call_args_list]
    assert any(
        "Webhook server configured on port 9443 with mounted TLS certificates" in log
        for log in info_logs
    )


@patch("os.path.exists")
@patch("tempfile.mkdtemp")
@patch("haproxy_template_ic.operator.logger")
def test_configure_webhook_server_self_signed(mock_logger, mock_mkdtemp, mock_exists):
    """Test webhook server configuration with self-signed certificates."""
    from haproxy_template_ic.operator import configure_webhook_server

    settings = MagicMock()
    memo = MagicMock()

    # Mock config with webhook validation enabled
    watch_config = MagicMock()
    watch_config.enable_validation_webhook = True
    memo.config.watched_resources = {"test_resource": watch_config}

    # Mock no existing certificate files
    mock_exists.return_value = False
    mock_mkdtemp.return_value = "/tmp/test-ca"

    configure_webhook_server(settings, memo)

    # Should configure webhook server with self-signed certs
    info_logs = [str(call) for call in mock_logger.info.call_args_list]
    assert any(
        "Webhook server configured on port 9443 with self-signed certificates" in log
        for log in info_logs
    )


@patch("kopf.run")
@patch("kopf.on.startup")
@patch("haproxy_template_ic.operator.setup_resource_watchers")
@patch("haproxy_template_ic.operator.initialize_configuration")
@patch("uvloop.EventLoopPolicy")
@patch("kopf.set_default_registry")
@patch("haproxy_template_ic.operator.get_metrics_collector")
@patch("haproxy_template_ic.operator.logger")
def test_run_operator_loop_normal_shutdown(
    mock_logger,
    mock_get_metrics,
    mock_set_registry,
    mock_uvloop_policy,
    mock_init_config,
    mock_setup_watchers,
    mock_startup,
    mock_kopf_run,
):
    """Test run_operator_loop with normal shutdown."""
    from haproxy_template_ic.operator import run_operator_loop
    from haproxy_template_ic.__main__ import CliOptions

    # Mock dependencies
    mock_metrics = MagicMock()
    mock_get_metrics.return_value = mock_metrics

    mock_event_loop = MagicMock()
    mock_loop_policy = MagicMock()
    mock_loop_policy.new_event_loop.return_value = mock_event_loop
    mock_uvloop_policy.return_value = mock_loop_policy

    # Mock startup decorator
    mock_startup.return_value = lambda func: func

    # Mock asyncio future for stop conditions
    mock_future = MagicMock()
    mock_future.done.return_value = False  # Normal shutdown (no reload)

    # Mock kopf components
    mock_registry = MagicMock()
    mock_indexers = MagicMock()

    with patch(
        "kopf._core.intents.registries.SmartOperatorRegistry",
        return_value=mock_registry,
    ):
        with patch(
            "kopf._core.engines.indexing.OperatorIndexers", return_value=mock_indexers
        ):
            with patch("asyncio.Future", return_value=mock_future):
                with patch("asyncio.set_event_loop"):
                    # Create CLI options
                    cli_options = CliOptions(
                        configmap_name="test-config",
                        healthz_port=8080,
                        verbose=1,
                        socket_path="/test/socket",
                        metrics_port=9090,
                        structured_logging=False,
                        tracing_enabled=False,
                    )

                    run_operator_loop(cli_options)

                    # Verify key operations were called
                    mock_event_loop.run_until_complete.assert_called()
                    mock_setup_watchers.assert_called()

                    # Verify final shutdown log
                    shutdown_logs = [
                        str(call) for call in mock_logger.info.call_args_list
                    ]
                    assert any(
                        "Operator shutdown complete" in log for log in shutdown_logs
                    )


@patch("kopf.run")
@patch("kopf.on.startup")
@patch("haproxy_template_ic.operator.setup_resource_watchers")
@patch("haproxy_template_ic.operator.initialize_configuration")
@patch("uvloop.EventLoopPolicy")
@patch("kopf.set_default_registry")
@patch("haproxy_template_ic.operator.get_metrics_collector")
@patch("haproxy_template_ic.operator.logger")
def test_run_operator_loop_with_config_reload(
    mock_logger,
    mock_get_metrics,
    mock_set_registry,
    mock_uvloop_policy,
    mock_init_config,
    mock_setup_watchers,
    mock_startup,
    mock_kopf_run,
):
    """Test run_operator_loop with config reload scenario."""
    from haproxy_template_ic.operator import run_operator_loop
    from haproxy_template_ic.__main__ import CliOptions

    # Mock dependencies
    mock_metrics = MagicMock()
    mock_get_metrics.return_value = mock_metrics

    mock_event_loop = MagicMock()
    mock_loop_policy = MagicMock()
    mock_loop_policy.new_event_loop.return_value = mock_event_loop
    mock_uvloop_policy.return_value = mock_loop_policy

    # Mock startup decorator
    mock_startup.return_value = lambda func: func

    # Mock reload scenario - first iteration has reload flag set, second doesn't
    mock_reload_future = MagicMock()
    mock_reload_future.done.side_effect = [
        True,
        False,
    ]  # First reload, then normal shutdown

    mock_registry = MagicMock()
    mock_indexers = MagicMock()

    with patch(
        "kopf._core.intents.registries.SmartOperatorRegistry",
        return_value=mock_registry,
    ):
        with patch(
            "kopf._core.engines.indexing.OperatorIndexers", return_value=mock_indexers
        ):
            with patch("asyncio.Future", return_value=mock_reload_future):
                with patch("asyncio.set_event_loop"):
                    # Create CLI options
                    cli_options = CliOptions(
                        configmap_name="test-config",
                        healthz_port=8080,
                        verbose=1,
                        socket_path="/test/socket",
                        metrics_port=9090,
                        structured_logging=False,
                        tracing_enabled=False,
                    )

                    run_operator_loop(cli_options)

                    # Verify reload logging
                    reload_logs = [
                        str(call) for call in mock_logger.info.call_args_list
                    ]
                    assert any(
                        "Configuration changed. Reinitializing" in log
                        for log in reload_logs
                    )

                    # Should be called twice (initial + reload)
                    assert mock_kopf_run.call_count == 2


# =============================================================================
# Extended Coverage Tests for Missing Lines
# =============================================================================


def test_extract_nested_field_basic_access():
    """Test extract_nested_field with basic dot notation access."""
    from haproxy_template_ic.operator import extract_nested_field

    obj = {"metadata": {"name": "test-pod", "namespace": "default"}}

    # Basic field access
    assert extract_nested_field(obj, "metadata.name") == "test-pod"
    assert extract_nested_field(obj, "metadata.namespace") == "default"

    # Missing field returns empty string
    assert extract_nested_field(obj, "metadata.missing") == ""
    assert extract_nested_field(obj, "spec.containers") == ""


def test_extract_nested_field_bracket_notation():
    """Test extract_nested_field with bracket notation for keys with special chars."""
    from haproxy_template_ic.operator import extract_nested_field

    obj = {
        "metadata": {
            "labels": {
                "kubernetes.io/service-name": "my-service",
                "app": "web-server",
                "version": "v1.0",
            }
        }
    }

    # Bracket notation with single quotes
    assert (
        extract_nested_field(obj, "metadata.labels['kubernetes.io/service-name']")
        == "my-service"
    )
    assert extract_nested_field(obj, "metadata.labels['app']") == "web-server"

    # Bracket notation with double quotes
    assert (
        extract_nested_field(obj, 'metadata.labels["kubernetes.io/service-name"]')
        == "my-service"
    )
    assert extract_nested_field(obj, 'metadata.labels["version"]') == "v1.0"

    # Bracket notation without quotes
    assert extract_nested_field(obj, "metadata.labels[app]") == "web-server"

    # Missing key in bracket notation
    assert extract_nested_field(obj, "metadata.labels['missing']") == ""


def test_extract_nested_field_malformed_brackets():
    """Test extract_nested_field with malformed bracket notation."""
    from haproxy_template_ic.operator import extract_nested_field

    obj = {"metadata": {"labels": {"app": "test"}}}

    # Malformed bracket notation should return empty string
    assert extract_nested_field(obj, "metadata.labels[") == ""
    assert extract_nested_field(obj, "metadata.labels]") == ""
    assert extract_nested_field(obj, "metadata.labels['missing") == ""
    assert extract_nested_field(obj, "metadata.labels[missing']") == ""

    # Test specific ValueError/IndexError paths
    assert extract_nested_field(obj, "metadata.labels[]") == ""  # Empty brackets
    assert extract_nested_field(obj, "metadata.labels[no_closing_bracket") == ""

    # Mismatched quotes (should use as-is)
    obj_with_mismatched = {"metadata": {"labels": {"'key\"": "value"}}}
    assert (
        extract_nested_field(obj_with_mismatched, "metadata.labels['key\"]") == "value"
    )


def test_extract_nested_field_non_dict_objects():
    """Test extract_nested_field with non-dict current values."""
    from haproxy_template_ic.operator import extract_nested_field

    obj = {
        "metadata": "not-a-dict",
        "spec": {"containers": ["container1", "container2"]},
    }

    # Non-dict metadata returns the string value itself
    assert extract_nested_field(obj, "metadata") == "not-a-dict"

    # But accessing fields on non-dict returns the non-dict as string
    assert extract_nested_field(obj, "metadata.name") == "not-a-dict"

    # List value converted to string when accessing further
    assert (
        extract_nested_field(obj, "spec.containers.name")
        == "['container1', 'container2']"
    )


def test_extract_nested_field_none_values():
    """Test extract_nested_field with None values."""
    from haproxy_template_ic.operator import extract_nested_field

    obj = {"metadata": {"name": None, "labels": {"app": None}}}

    # None values should return empty string
    assert extract_nested_field(obj, "metadata.name") == ""
    assert extract_nested_field(obj, "metadata.labels.app") == ""


@pytest.mark.asyncio
async def test_update_resource_index_no_memo():
    """Test update_resource_index without memo object."""
    import logging
    from haproxy_template_ic.operator import update_resource_index

    body = {"metadata": {"namespace": "test-ns", "name": "test-resource"}}

    result = await update_resource_index(
        param="services",
        namespace="test-ns",
        name="test-resource",
        body=body,
        logger=logging.getLogger(),
    )

    # Should fallback to default indexing (namespace, name)
    assert result == {("test-ns", "test-resource"): body}


@pytest.mark.asyncio
async def test_update_resource_index_no_config():
    """Test update_resource_index with memo but no config."""
    import logging
    from haproxy_template_ic.operator import update_resource_index

    # Mock memo without config
    memo = MagicMock()
    memo.config = None

    body = {"metadata": {"namespace": "test-ns", "name": "test-resource"}}

    result = await update_resource_index(
        param="services",
        namespace="test-ns",
        name="test-resource",
        body=body,
        logger=logging.getLogger(),
        memo=memo,
    )

    # Should fallback to default indexing
    assert result == {("test-ns", "test-resource"): body}


@pytest.mark.asyncio
async def test_update_resource_index_custom_indexing():
    """Test update_resource_index with custom index_by configuration."""
    import logging
    from haproxy_template_ic.operator import update_resource_index

    # Mock memo with watch config
    memo = MagicMock()
    watch_config = MagicMock()
    watch_config.index_by = ["metadata.namespace", "metadata.labels['app']"]
    memo.config.watched_resources = {"services": watch_config}

    body = {
        "metadata": {
            "namespace": "prod",
            "name": "web-service",
            "labels": {"app": "frontend"},
        }
    }

    result = await update_resource_index(
        param="services",
        namespace="prod",
        name="web-service",
        body=body,
        logger=logging.getLogger(),
        memo=memo,
    )

    # Should use custom indexing
    assert result == {("prod", "frontend"): body}


@pytest.mark.asyncio
async def test_update_resource_index_missing_fields():
    """Test update_resource_index with missing index fields."""
    import logging
    from haproxy_template_ic.operator import update_resource_index

    # Mock memo with watch config
    memo = MagicMock()
    watch_config = MagicMock()
    watch_config.index_by = [
        "metadata.namespace",
        "metadata.missing",
        "spec.selector.app",
    ]
    memo.config.watched_resources = {"services": watch_config}

    body = {"metadata": {"namespace": "prod", "name": "web-service"}}

    result = await update_resource_index(
        param="services",
        namespace="prod",
        name="web-service",
        body=body,
        logger=logging.getLogger(),
        memo=memo,
    )

    # Missing fields should result in empty strings
    assert result == {("prod", "", ""): body}


@pytest.mark.asyncio
async def test_render_haproxy_templates_empty_index():
    """Test render_haproxy_templates with empty index creating empty collection."""
    with patch(
        "haproxy_template_ic.operator.get_current_namespace", return_value="test"
    ):
        with patch(
            "haproxy_template_ic.operator.synchronize_with_haproxy_instances"
        ) as mock_sync:
            with patch(
                "haproxy_template_ic.operator.get_metrics_collector"
            ) as mock_metrics:
                mock_metrics.return_value = MagicMock()

                # Create memo with config but no indices
                memo = MagicMock()
                memo.config.watched_resources = {"services": MagicMock()}
                memo.config.maps = {}
                memo.config.certificates = {}
                memo.config.haproxy_config.template = "test config"
                memo.template_renderer.render.return_value = "rendered config"
                memo.haproxy_config_context = MagicMock()
                memo.haproxy_config_context.rendered_maps = []
                memo.haproxy_config_context.rendered_certificates = []
                memo.indices = {"services": None}  # Empty index

                await render_haproxy_templates(memo)

                # Should handle empty index gracefully
                mock_sync.assert_called_once()


@pytest.mark.asyncio
async def test_synchronize_mixed_results_logging():
    """Test synchronize_with_haproxy_instances with mixed success and failure results."""
    from haproxy_template_ic.operator import synchronize_with_haproxy_instances

    with patch(
        "haproxy_template_ic.operator.get_current_namespace", return_value="test"
    ):
        with patch(
            "haproxy_template_ic.operator.get_metrics_collector"
        ) as mock_metrics:
            with patch("haproxy_template_ic.operator.HAProxyPodDiscovery"):
                with patch(
                    "haproxy_template_ic.operator.ConfigSynchronizer"
                ) as mock_sync_class:
                    with patch("haproxy_template_ic.operator.logger") as mock_logger:
                        # Setup memo
                        memo = MagicMock()
                        memo.config.pod_selector = MagicMock()
                        memo.config.dataplane_auth.username = "admin"
                        memo.config.dataplane_auth.password = "pass"
                        memo.haproxy_config_context = MagicMock()
                        memo.haproxy_config_context.rendered_config = MagicMock()

                        # Mock results with mixed success/failure
                        result1 = MagicMock()
                        result1.success = True
                        result1.instance.name = "instance1"
                        result1.instance.is_validation_sidecar = False

                        result2 = MagicMock()
                        result2.success = False
                        result2.instance.name = "instance2"
                        result2.instance.is_validation_sidecar = False
                        result2.error = "Connection failed"

                        result3 = MagicMock()
                        result3.success = True
                        result3.instance.name = "validation"
                        result3.instance.is_validation_sidecar = True

                        mock_synchronizer = mock_sync_class.return_value
                        mock_synchronizer.synchronize_configuration = AsyncMock(
                            return_value=[result1, result2, result3]
                        )

                        mock_metrics_collector = mock_metrics.return_value

                        await synchronize_with_haproxy_instances(memo)

                        # Verify success logging
                        success_calls = [
                            call for call in mock_logger.info.call_args_list
                        ]
                        assert any(
                            "Successfully synchronized configuration to 2 HAProxy instances"
                            in str(call)
                            for call in success_calls
                        )

                        # Verify failure logging
                        error_calls = [
                            call for call in mock_logger.error.call_args_list
                        ]
                        assert any(
                            "Failed to synchronize configuration to 1 HAProxy instances"
                            in str(call)
                            for call in error_calls
                        )
                        assert any(
                            "instance2: Connection failed" in str(call)
                            for call in error_calls
                        )

                        # Verify metrics calls
                        mock_metrics_collector.record_haproxy_instances.assert_called_with(
                            2, 1
                        )
                        assert (
                            mock_metrics_collector.record_dataplane_api_request.call_count
                            == 3
                        )
                        mock_metrics_collector.record_error.assert_called_with(
                            "dataplane_deploy_failed", "dataplane"
                        )


def test_configure_webhook_server_ca_file_copying():
    """Test configure_webhook_server CA file copying functionality."""
    from haproxy_template_ic.operator import configure_webhook_server

    with patch("os.path.exists") as mock_exists:
        with patch("tempfile.mkdtemp", return_value="/tmp/webhook-ca-123"):
            with patch("shutil.copy2") as mock_copy:
                # Mock certificate files exist, including CA file
                def exists_side_effect(path):
                    return path in [
                        "/tmp/webhook-certs/webhook-cert.pem",
                        "/tmp/webhook-certs/webhook-key.pem",
                        "/tmp/webhook-certs/webhook-ca.pem",
                    ]

                mock_exists.side_effect = exists_side_effect

                # Setup memo with webhook-enabled resources
                memo = MagicMock()
                watch_config = MagicMock()
                watch_config.enable_validation_webhook = True
                memo.config.watched_resources = {"ingresses": watch_config}

                settings = MagicMock()

                configure_webhook_server(settings, memo)

                # Should copy CA file to writable location
                mock_copy.assert_called_once_with(
                    "/tmp/webhook-certs/webhook-ca.pem",
                    "/tmp/webhook-ca-123/webhook-ca.pem",
                )

                # Should configure webhook server with copied CA file
                assert (
                    settings.admission.server.cadump
                    == "/tmp/webhook-ca-123/webhook-ca.pem"
                )


def test_configure_webhook_server_no_ca_file():
    """Test configure_webhook_server without existing CA file."""
    from haproxy_template_ic.operator import configure_webhook_server

    with patch("os.path.exists") as mock_exists:
        with patch("tempfile.mkdtemp", return_value="/tmp/webhook-ca-456"):
            # Mock certificate files exist, but no CA file
            def exists_side_effect(path):
                return path in [
                    "/tmp/webhook-certs/webhook-cert.pem",
                    "/tmp/webhook-certs/webhook-key.pem",
                ]

            mock_exists.side_effect = exists_side_effect

            # Setup memo with webhook-enabled resources
            memo = MagicMock()
            watch_config = MagicMock()
            watch_config.enable_validation_webhook = True
            memo.config.watched_resources = {"ingresses": watch_config}

            settings = MagicMock()

            configure_webhook_server(settings, memo)

            # Should use temp CA file location (fallback)
            assert (
                settings.admission.server.cadump == "/tmp/webhook-ca-456/webhook-ca.pem"
            )
