"""
Additional tests for config models to improve coverage.

Tests additional edge cases and error paths in the config_models module.
"""

import pytest

from haproxy_template_ic.config_models import (
    IndexedResourceCollection,
    HAProxyConfigContext,
    TemplateContext,
    PodSelector,
    WatchResourceConfig,
    CertificateConfig,
    RenderedConfig,
    RenderedMap,
    RenderedCertificate,
    MapConfig,
    config_from_dict,
)


class TestIndexedResourceCollectionEdgeCases:
    """Test IndexedResourceCollection edge cases."""

    def test_get_indexed_single_no_results(self):
        """Test get_indexed_single with no results returns None."""
        collection = IndexedResourceCollection()

        result = collection.get_indexed_single("nonexistent")
        assert result is None

    def test_from_kopf_index_empty(self):
        """Test creating collection from empty kopf index."""
        empty_index = {}
        collection = IndexedResourceCollection.from_kopf_index(empty_index)

        assert len(collection) == 0
        assert list(collection.items()) == []

    def test_collection_basic_functionality(self):
        """Test basic collection functionality."""
        collection = IndexedResourceCollection()

        # Empty collection should have no items
        assert len(collection) == 0
        assert list(collection.values()) == []
        assert list(collection.items()) == []


class TestConfigValidationEdgeCases:
    """Test configuration validation edge cases."""

    def test_pod_selector_validation(self):
        """Test PodSelector validation requirements."""
        # PodSelector requires at least one label
        with pytest.raises(Exception):  # Pydantic validation error
            PodSelector(match_labels={})

        # Valid selector should work
        selector = PodSelector(match_labels={"app": "haproxy"})
        assert selector.match_labels == {"app": "haproxy"}

    def test_watch_resource_config_defaults(self):
        """Test WatchResourceConfig with default values."""
        config = WatchResourceConfig(api_version="v1", kind="ConfigMap")

        assert config.group == ""  # Core API group is empty string
        assert config.version == "v1"
        assert config.enable_validation_webhook is True  # Default is True
        assert config.index_by == ["metadata.namespace", "metadata.name"]

    def test_watch_resource_config_with_group_version(self):
        """Test WatchResourceConfig parsing group/version from api_version."""
        config = WatchResourceConfig(api_version="apps/v1", kind="Deployment")

        assert config.group == "apps"
        assert config.version == "v1"

    def test_certificate_config_validation(self):
        """Test CertificateConfig validation."""
        config = CertificateConfig(template="cert content here")
        assert config.template == "cert content here"

    def test_rendered_components(self):
        """Test rendered component classes."""
        # Test RenderedConfig
        config = RenderedConfig(content="global\n    daemon")
        assert config.content == "global\n    daemon"

        # Test RenderedMap
        map_config = MapConfig(template="host.map template")
        rendered_map = RenderedMap(
            path="/etc/haproxy/maps/host.map",
            content="example.com backend1",
            map_config=map_config,
        )
        assert rendered_map.path == "/etc/haproxy/maps/host.map"
        assert rendered_map.content == "example.com backend1"
        assert rendered_map.map_config == map_config

        # Test RenderedCertificate
        cert = RenderedCertificate(
            path="/etc/haproxy/certs/tls.pem", content="-----BEGIN CERTIFICATE-----"
        )
        assert cert.path == "/etc/haproxy/certs/tls.pem"
        assert cert.content == "-----BEGIN CERTIFICATE-----"


class TestHAProxyConfigContext:
    """Test HAProxyConfigContext functionality."""

    def test_context_initialization(self):
        """Test HAProxyConfigContext initialization."""
        from haproxy_template_ic.config_models import Config

        config = Config(
            pod_selector=PodSelector(match_labels={"app": "test"}),
            haproxy_config=MapConfig(template="test config"),
        )

        template_context = TemplateContext(namespace="test")

        context = HAProxyConfigContext(
            config=config, template_context=template_context, rendered_config=None
        )

        assert context.config == config
        assert context.template_context == template_context
        assert context.rendered_config is None
        assert context.rendered_maps == []
        assert context.rendered_certificates == []

    def test_context_with_rendered_content(self):
        """Test HAProxyConfigContext with rendered content."""
        from haproxy_template_ic.config_models import Config

        config = Config(
            pod_selector=PodSelector(match_labels={"app": "test"}),
            haproxy_config=MapConfig(template="test config"),
        )

        template_context = TemplateContext(namespace="test")
        rendered_config = RenderedConfig(content="rendered content")

        context = HAProxyConfigContext(
            config=config,
            template_context=template_context,
            rendered_config=rendered_config,
        )

        assert context.rendered_config.content == "rendered content"


class TestConfigFromDict:
    """Test config_from_dict function edge cases."""

    def test_config_from_dict_minimal(self):
        """Test config creation with minimal required fields."""
        config_dict = {
            "pod_selector": {"match_labels": {"app": "haproxy"}},
            "haproxy_config": {"template": "global\n    daemon"},
        }

        config = config_from_dict(config_dict)

        assert config.pod_selector.match_labels == {"app": "haproxy"}
        assert config.haproxy_config.template == "global\n    daemon"
        assert config.watched_resources == {}
        assert config.maps == {}
        assert config.certificates == {}
        assert config.template_snippets == {}

    def test_config_from_dict_complex(self):
        """Test config creation with all optional fields."""
        config_dict = {
            "pod_selector": {
                "match_labels": {"app": "haproxy", "component": "loadbalancer"}
            },
            "haproxy_config": {
                "template": "global\n    daemon\ndefaults\n    mode http"
            },
            "watched_resources": {
                "ingresses": {
                    "api_version": "networking.k8s.io/v1",
                    "kind": "Ingress",
                    "enable_validation_webhook": True,
                    "index_by": ["metadata.namespace", "metadata.name"],
                }
            },
            "maps": {
                "/etc/haproxy/maps/host.map": {
                    "template": "{% for ingress in resources.ingresses %}{{ ingress.spec.host }}\n{% endfor %}"
                }
            },
            "certificates": {
                "/etc/haproxy/certs/tls.pem": {
                    "template": "{{ secret.data.tls_crt | b64decode }}"
                }
            },
            "template_snippets": {
                "backend-config": {
                    "name": "backend-config",
                    "template": "server web1 192.168.1.10:80 check",
                }
            },
            "validation_dataplane_url": "http://localhost:5555",
        }

        config = config_from_dict(config_dict)

        assert len(config.watched_resources) == 1
        assert "ingresses" in config.watched_resources
        assert config.watched_resources["ingresses"].enable_validation_webhook is True

        assert len(config.maps) == 1
        assert "/etc/haproxy/maps/host.map" in config.maps

        assert len(config.certificates) == 1
        assert "/etc/haproxy/certs/tls.pem" in config.certificates

        assert len(config.template_snippets) == 1
        assert (
            config.template_snippets["backend-config"].template
            == "server web1 192.168.1.10:80 check"
        )

        assert config.validation_dataplane_url == "http://localhost:5555"

    def test_config_from_dict_invalid_structure(self):
        """Test config creation with invalid structure raises appropriate errors."""
        # Missing required pod_selector
        with pytest.raises(Exception):
            config_from_dict({"haproxy_config": {"template": "test"}})

        # Missing required haproxy_config
        with pytest.raises(Exception):
            config_from_dict({"pod_selector": {"match_labels": {"app": "test"}}})


class TestTemplateContext:
    """Test TemplateContext functionality."""

    def test_template_context_with_resources(self):
        """Test TemplateContext with resources."""
        resources = {
            "ingresses": IndexedResourceCollection(),
            "services": IndexedResourceCollection(),
        }

        context = TemplateContext(resources=resources, namespace="production")

        assert context.resources == resources
        assert context.namespace == "production"
        assert len(context.resources) == 2

    def test_template_context_empty_resources(self):
        """Test TemplateContext with empty resources."""
        context = TemplateContext(namespace="test")

        assert context.resources == {}
        assert context.namespace == "test"
