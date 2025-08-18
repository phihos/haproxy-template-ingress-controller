import pytest
from pydantic import ValidationError

from haproxy_template_ic.templating import TemplateRenderer
from haproxy_template_ic.config_models import (
    Config,
    WatchResourceConfig,
    MapConfig,
    CertificateConfig,
    PodSelector,
    config_from_dict,
    RenderedMap,
    RenderedConfig,
    RenderedCertificate,
    TemplateContext,
    HAProxyConfigContext,
)
from jinja2 import Template


@pytest.mark.parametrize(
    "config_dict,expected_pod_selector,expected_watch_resources_count,expected_maps_count",
    [
        # Basic config with only required fields
        (
            {
                "pod_selector": {"match_labels": {"app": "myapp"}},
                "haproxy_config": {"template": "global\n    daemon"},
            },
            {"app": "myapp"},
            0,
            0,
        ),
        # Config with empty optional fields
        (
            {
                "pod_selector": {"match_labels": {"app": "myapp"}},
                "haproxy_config": {"template": "global\n    daemon"},
                "watched_resources": {},
                "maps": {},
            },
            {"app": "myapp"},
            0,
            0,
        ),
        # Config with watched_resources
        (
            {
                "pod_selector": {"match_labels": {"app": "myapp"}},
                "haproxy_config": {"template": "global\n    daemon"},
                "watched_resources": {
                    "ingresses": {
                        "api_version": "networking.k8s.io/v1",
                        "kind": "Ingress",
                    },
                    "services": {"api_version": "v1", "kind": "Service"},
                },
            },
            {"app": "myapp"},
            2,
            0,
        ),
        # Config with maps
        (
            {
                "pod_selector": {"match_labels": {"app": "myapp"}},
                "haproxy_config": {"template": "global\n    daemon"},
                "maps": {
                    "/etc/haproxy/maps/path-prefix.map": {
                        "template": "server {{ name }} {{ ip }}:{{ port }}",
                    },
                    "/etc/haproxy/maps/backend-servers.map": {
                        "template": "server {{ name }} {{ ip }}:{{ port }}",
                    },
                },
            },
            {"app": "myapp"},
            0,
            2,
        ),
        # Config with all fields
        (
            {
                "pod_selector": {"match_labels": {"app": "myapp"}},
                "haproxy_config": {"template": "global\n    daemon"},
                "watched_resources": {
                    "ingresses": {
                        "api_version": "networking.k8s.io/v1",
                        "kind": "Ingress",
                    }
                },
                "maps": {
                    "/etc/haproxy/maps/path-prefix.map": {
                        "template": "server {{ name }} {{ ip }}:{{ port }}",
                    }
                },
            },
            {"app": "myapp"},
            1,
            1,
        ),
    ],
)
def test_valid_configs(
    config_dict,
    expected_pod_selector,
    expected_watch_resources_count,
    expected_maps_count,
):
    """Test creating valid configs with various field combinations."""
    config = config_from_dict(config_dict)

    assert isinstance(config, Config)
    assert config.pod_selector.match_labels == expected_pod_selector
    assert len(config.watched_resources) == expected_watch_resources_count
    assert len(config.maps) == expected_maps_count


@pytest.mark.parametrize(
    "config_dict,expected_watch_resource",
    [
        (
            {
                "pod_selector": {"match_labels": {"app": "myapp"}},
                "haproxy_config": {"template": "global\n    daemon"},
                "watched_resources": {
                    "ingresses": {
                        "api_version": "networking.k8s.io/v1",
                        "kind": "Ingress",
                    }
                },
            },
            {
                "name": "ingresses",
                "api_version": "networking.k8s.io/v1",
                "kind": "Ingress",
            },
        ),
        (
            {
                "pod_selector": {"match_labels": {"app": "myapp"}},
                "haproxy_config": {"template": "global\n    daemon"},
                "watched_resources": {
                    "services": {"api_version": "v1", "kind": "Service"}
                },
            },
            {"name": "services", "api_version": "v1", "kind": "Service"},
        ),
        (
            {
                "pod_selector": {"match_labels": {"app": "myapp"}},
                "haproxy_config": {"template": "global\n    daemon"},
                "watched_resources": {"pods": {"api_version": "v1", "kind": "Pod"}},
            },
            {"name": "pods", "api_version": "v1", "kind": "Pod"},
        ),
    ],
)
def test_watch_resources_structure(config_dict, expected_watch_resource):
    """Test that watched_resources are properly structured as WatchResourceConfig objects."""
    config = config_from_dict(config_dict)

    # Find the watch resource by key in the dictionary
    target_id = expected_watch_resource["name"]
    assert target_id in config.watched_resources, (
        f"Watch resource with id {target_id} not found"
    )

    watch_resource = config.watched_resources[target_id]
    assert isinstance(watch_resource, WatchResourceConfig)
    assert watch_resource.kind == expected_watch_resource["kind"]
    # Check api_version matches expected
    assert watch_resource.api_version == expected_watch_resource["api_version"]


@pytest.mark.parametrize(
    "config_dict,expected_map",
    [
        (
            {
                "pod_selector": {"match_labels": {"app": "myapp"}},
                "haproxy_config": {"template": "global\n    daemon"},
                "maps": {
                    "/etc/haproxy/maps/path-prefix.map": {
                        "template": "server {{ name }} {{ ip }}:{{ port }}",
                    }
                },
            },
            {
                "name": "/etc/haproxy/maps/path-prefix.map",
                "path": "/etc/haproxy/maps/path-prefix.map",
                "template": "server {{ name }} {{ ip }}:{{ port }}",
                "expected_rendered": "server test-server 192.168.1.1:8080",
            },
        ),
        (
            {
                "pod_selector": {"match_labels": {"app": "myapp"}},
                "haproxy_config": {"template": "global\n    daemon"},
                "maps": {
                    "/etc/haproxy/maps/backend-servers.map": {
                        "template": "server {{ name }} {{ ip }}:{{ port }}",
                    }
                },
            },
            {
                "name": "/etc/haproxy/maps/backend-servers.map",
                "path": "/etc/haproxy/maps/backend-servers.map",
                "template": "server {{ name }} {{ ip }}:{{ port }}",
                "expected_rendered": "server test-server 192.168.1.1:8080",
            },
        ),
        (
            {
                "pod_selector": {"match_labels": {"app": "myapp"}},
                "haproxy_config": {"template": "global\n    daemon"},
                "maps": {
                    "/var/log/app.log": {
                        "template": "log_format {{ format }};",
                    }
                },
            },
            {
                "name": "/var/log/app.log",
                "path": "/var/log/app.log",
                "template": "log_format {{ format }};",
                "expected_rendered": "log_format combined;",
            },
        ),
    ],
)
def test_maps_structure(config_dict, expected_map):
    """Test that maps are properly structured as MapConfig objects."""
    config = config_from_dict(config_dict)

    # Find the map config by path in the dictionary
    target_path = expected_map["name"]
    assert target_path in config.maps, f"Map with path {target_path} not found"

    map_config = config.maps[target_path]
    assert isinstance(map_config, MapConfig)
    # Template should be compilable with the new API
    compiled_template = TemplateRenderer.from_config(config).get_compiled(
        map_config.template
    )
    assert isinstance(compiled_template, Template)
    # Test that the template renders correctly with sample data
    rendered = compiled_template.render(
        name="test-server", ip="192.168.1.1", port="8080", format="combined"
    )
    assert rendered == expected_map["expected_rendered"]


@pytest.mark.parametrize(
    "config_dict",
    [
        # Missing required pod_selector field
        {"watched_resources": {}},
        {"maps": {}},
        {},
        # Invalid field types
        {"pod_selector": 123},  # Should be string
        {"pod_selector": None},  # Should be string
        # Extra fields should raise exceptions
        {
            "pod_selector": {"match_labels": {"app": "myapp"}},
            "extra_field": "should_raise_exception",
        },
        {
            "pod_selector": {"match_labels": {"app": "myapp"}},
            "unknown_field": {"nested": "data"},
        },
        {
            "pod_selector": {"match_labels": {"app": "myapp"}},
            "watched_resources": {},
            "maps": {},
            "extra_field": "should_raise_exception",
        },
        # Invalid relative paths in maps
        {
            "pod_selector": {"match_labels": {"app": "myapp"}},
            "maps": {
                "relative/path.conf": {
                    "template": "config",
                }
            },
        },
        {
            "pod_selector": {"match_labels": {"app": "myapp"}},
            "maps": {"config.conf": {"template": "config"}},
        },
        {
            "pod_selector": {"match_labels": {"app": "myapp"}},
            "maps": {"./config.conf": {"template": "config"}},
        },
        # Invalid Jinja2 templates
        {
            "pod_selector": {"match_labels": {"app": "myapp"}},
            "maps": {
                "/etc/haproxy/maps/test.map": {
                    "template": "server {{ name",
                }
            },
        },
        {
            "pod_selector": {"match_labels": {"app": "myapp"}},
            "maps": {
                "/etc/haproxy/maps/test.map": {
                    "template": "server {{ unknown_var }",
                }
            },
        },
        {
            "pod_selector": {"match_labels": {"app": "myapp"}},
            "maps": {
                "/etc/haproxy/maps/test.map": {
                    "template": "server {% if name %}",
                }
            },
        },
        # Missing mandatory kind field in WatchResourceConfig
        {
            "pod_selector": {"match_labels": {"app": "myapp"}},
            "watched_resources": {"pods": {"api_version": "v1", "kind": "Pod"}},
        },
    ],
)
def test_invalid_configs(config_dict):
    """Test that invalid configs raise appropriate exceptions."""
    with pytest.raises(Exception):  # dacite will raise an error for invalid configs
        config_from_dict(config_dict)


# RenderedMap Tests
def test_rendered_map_creation():
    """Test RenderedMap dataclass creation."""
    map_config = MapConfig(template="test {{ name }}")
    rendered_map = RenderedMap(
        path="/etc/haproxy/maps/test.map", content="test content", map_config=map_config
    )

    assert rendered_map.path == "/etc/haproxy/maps/test.map"
    assert rendered_map.content == "test content"
    assert rendered_map.map_config == map_config


def test_rendered_map_is_frozen():
    """Test that RenderedMap is immutable."""
    map_config = MapConfig(template="test")
    rendered_map = RenderedMap(path="/test", content="content", map_config=map_config)

    with pytest.raises((AttributeError, ValidationError)):
        rendered_map.path = "/new/path"


# TemplateContext Tests
def test_template_context_creation():
    """Test TemplateContext dataclass creation."""
    from haproxy_template_ic.config_models import IndexedResourceCollection

    # Create an IndexedResourceCollection for test_resource
    test_collection = IndexedResourceCollection()
    test_collection._internal_dict[("default", "test")] = [
        {"name": "test", "host": "example.com"}
    ]

    resources = {"test_resource": test_collection}
    context = TemplateContext(resources=resources, namespace="test-namespace")

    assert len(context.resources["test_resource"]) == 1
    assert context.namespace == "test-namespace"


def test_template_context_default_resources():
    """Test TemplateContext with default empty resources."""
    context = TemplateContext()

    assert context.resources == {}
    assert context.namespace is None


def test_template_context_is_frozen():
    """Test that TemplateContext is immutable."""
    from haproxy_template_ic.config_models import IndexedResourceCollection

    # Create an IndexedResourceCollection for pods
    pods_collection = IndexedResourceCollection()
    pods_collection._internal_dict[("default", "test-pod")] = {"name": "test"}

    context = TemplateContext(resources={"pods": pods_collection})

    # Create a new collection to try replacing
    new_pods_collection = IndexedResourceCollection()
    new_pods_collection._internal_dict[("default", "new-pod")] = {"name": "new"}

    with pytest.raises(ValidationError):
        context.resources = {"pods": new_pods_collection}

    with pytest.raises(ValidationError):
        context.namespace = "new-namespace"


# HAProxyConfigContext Tests
def test_haproxy_config_context_creation():
    """Test HAProxyConfigContext dataclass creation."""
    # Create required config and template_context
    from haproxy_template_ic.config_models import Config, PodSelector, TemplateContext

    config = Config(
        pod_selector=PodSelector(match_labels={"app": "test"}),
        haproxy_config=MapConfig(template="global\n    daemon"),
    )
    template_context = TemplateContext()

    context = HAProxyConfigContext(config=config, template_context=template_context)

    assert context.rendered_maps == []


def test_haproxy_config_context_with_custom_data():
    """Test HAProxyConfigContext with custom rendered maps."""
    map_config = MapConfig(template="test")
    rendered_map = RenderedMap(path="/test", content="content", map_config=map_config)
    rendered_maps = [rendered_map]

    # Create required config and template_context
    from haproxy_template_ic.config_models import Config, PodSelector, TemplateContext

    config = Config(
        pod_selector=PodSelector(match_labels={"app": "test"}),
        haproxy_config=MapConfig(template="global\n    daemon"),
    )
    template_context = TemplateContext()

    context = HAProxyConfigContext(
        config=config, template_context=template_context, rendered_maps=rendered_maps
    )

    assert context.rendered_maps == rendered_maps


def test_haproxy_config_context_mutable():
    """Test that HAProxyConfigContext is mutable (not frozen)."""
    from haproxy_template_ic.config_models import Config, PodSelector, TemplateContext

    config = Config(
        pod_selector=PodSelector(match_labels={"app": "test"}),
        haproxy_config=MapConfig(template="global\n    daemon"),
    )
    template_context = TemplateContext()

    context = HAProxyConfigContext(config=config, template_context=template_context)
    map_config = MapConfig(template="test")
    rendered_map = RenderedMap(path="/test", content="content", map_config=map_config)

    # Should be able to modify rendered_maps
    context.rendered_maps.append(rendered_map)
    assert len(context.rendered_maps) == 1
    assert context.rendered_maps[0] == rendered_map


# RenderedConfig Tests
def test_rendered_config_creation():
    """Test RenderedConfig dataclass creation."""
    rendered_config = RenderedConfig(content="global\n    daemon")

    assert rendered_config.content == "global\n    daemon"


def test_rendered_config_frozen():
    """Test that RenderedConfig is frozen (immutable)."""
    rendered_config = RenderedConfig(content="global\n    daemon")

    # Should not be able to modify fields (Pydantic immutability)
    with pytest.raises(ValidationError):
        rendered_config.content = "new content"


def test_haproxy_config_context_with_rendered_config():
    """Test HAProxyConfigContext with rendered config."""
    config = Config(
        pod_selector=PodSelector(match_labels={"app": "haproxy"}),
        haproxy_config=MapConfig(template="global\n    daemon"),
    )
    template_context = TemplateContext()

    rendered_config = RenderedConfig(content="global\n    daemon")
    context = HAProxyConfigContext(
        config=config,
        template_context=template_context,
        rendered_config=rendered_config,
    )

    assert context.rendered_config == rendered_config
    assert context.rendered_config.content == "global\n    daemon"


def test_haproxy_config_context_default_rendered_config():
    """Test HAProxyConfigContext default rendered_config is None."""
    config = Config(
        pod_selector=PodSelector(match_labels={"app": "haproxy"}),
        haproxy_config=MapConfig(template="global\n    daemon"),
    )
    template_context = TemplateContext()
    context = HAProxyConfigContext(config=config, template_context=template_context)

    assert context.rendered_config is None
    assert context.rendered_maps == []


# RenderedCertificate Tests
def test_rendered_certificate_creation():
    """Test RenderedCertificate dataclass creation."""
    rendered_certificate = RenderedCertificate(
        path="/etc/haproxy/certs/test.pem", content="cert content"
    )

    assert rendered_certificate.path == "/etc/haproxy/certs/test.pem"
    assert rendered_certificate.content == "cert content"


def test_rendered_certificate_frozen():
    """Test that RenderedCertificate is frozen (immutable)."""
    rendered_certificate = RenderedCertificate(
        path="/etc/haproxy/certs/test.pem", content="cert content"
    )

    # Should not be able to modify fields (Pydantic immutability)
    with pytest.raises(ValidationError):
        rendered_certificate.path = "/new/path.pem"


def test_haproxy_config_context_with_rendered_certificates():
    """Test HAProxyConfigContext with rendered certificates."""
    config = Config(
        pod_selector=PodSelector(match_labels={"app": "haproxy"}),
        haproxy_config=MapConfig(template="global\n    daemon"),
    )
    template_context = TemplateContext()

    rendered_certificate = RenderedCertificate(
        path="/etc/haproxy/certs/test.pem", content="cert content"
    )

    context = HAProxyConfigContext(
        config=config,
        template_context=template_context,
        rendered_certificates=[rendered_certificate],
    )

    assert len(context.rendered_certificates) == 1
    assert context.rendered_certificates[0] == rendered_certificate
    assert context.rendered_certificates[0].path == "/etc/haproxy/certs/test.pem"


def test_haproxy_config_context_default_rendered_certificates():
    """Test HAProxyConfigContext default rendered_certificates is empty list."""
    config = Config(
        pod_selector=PodSelector(match_labels={"app": "haproxy"}),
        haproxy_config=MapConfig(template="global\n    daemon"),
    )
    template_context = TemplateContext()
    context = HAProxyConfigContext(config=config, template_context=template_context)

    assert context.rendered_certificates == []


# =============================================================================
# Collection Classes Tests
# =============================================================================


def test_watch_resource_collection_by_id():
    """Test watch resource collection access by key."""
    from haproxy_template_ic.config_models import WatchResourceConfig

    resources = {
        "pods": WatchResourceConfig(kind="Pod", api_version="v1"),
        "services": WatchResourceConfig(kind="Service", api_version="v1"),
        "ingresses": WatchResourceConfig(
            kind="Ingress", api_version="networking.k8s.io/v1"
        ),
    }

    # Test successful lookup
    found = resources.get("services")
    assert found is not None
    assert found.kind == "Service"

    # Test not found
    not_found = resources.get("nonexistent")
    assert not_found is None

    # Test empty collection
    empty_collection = {}
    assert empty_collection.get("anything") is None


def test_map_collection_by_path():
    """Test map collection access by path key."""
    from haproxy_template_ic.config_models import MapConfig

    maps = {
        "/etc/haproxy/maps/backend.map": MapConfig(template="backend map"),
        "/etc/haproxy/maps/path.map": MapConfig(template="path map"),
        "/etc/haproxy/maps/host.map": MapConfig(template="host map"),
    }

    # Test successful lookup
    found = maps.get("/etc/haproxy/maps/path.map")
    assert found is not None
    assert found.template == "path map"

    # Test not found
    not_found = maps.get("/nonexistent.map")
    assert not_found is None

    # Test empty collection
    empty_collection = {}
    assert empty_collection.get("/anything") is None


def test_template_snippet_collection_by_name():
    """Test template snippet collection access by name (dict-based)."""
    from haproxy_template_ic.config_models import TemplateSnippet

    snippets = {
        "backend-servers": TemplateSnippet(
            name="backend-servers", template="backend servers"
        ),
        "health-check": TemplateSnippet(name="health-check", template="health check"),
        "logging": TemplateSnippet(name="logging", template="logging config"),
    }

    # Test successful lookup
    found = snippets.get("health-check")
    assert found is not None
    assert found.name == "health-check"

    # Test not found
    not_found = snippets.get("nonexistent")
    assert not_found is None

    # Test empty collection
    empty_collection = {}
    assert empty_collection.get("anything") is None


def test_certificate_collection_by_name():
    """Test certificate collection access by path (dict-based)."""

    certificates = {
        "/etc/haproxy/certs/tls.pem": CertificateConfig(template="tls cert"),
        "/etc/haproxy/certs/ca.pem": CertificateConfig(template="ca cert"),
        "/etc/haproxy/certs/server.pem": CertificateConfig(template="server cert"),
    }

    # Test successful lookup
    found = certificates.get("/etc/haproxy/certs/ca.pem")
    assert found is not None
    assert found.template == "ca cert"

    # Test not found
    not_found = certificates.get("/etc/haproxy/certs/nonexistent.pem")
    assert not_found is None

    # Test empty collection
    empty_collection = {}
    assert empty_collection.get("/anything") is None


def test_template_context_get_methods():
    """Test TemplateContext helper methods."""
    from haproxy_template_ic.config_models import (
        TemplateContext,
        Config,
        MapConfig,
        TemplateSnippet,
        PodSelector,
        WatchResourceConfig,
    )

    # Create config with collections for testing
    test_config = Config(
        pod_selector=PodSelector(match_labels={"app": "test"}),
        haproxy_config=MapConfig(template="global\n    daemon"),
        maps={"/test.map": MapConfig(template="test")},
        template_snippets={
            "test-snippet": TemplateSnippet(name="test-snippet", template="snippet")
        },
        certificates={"/test.pem": CertificateConfig(template="cert")},
        watched_resources={"test": WatchResourceConfig(api_version="v1", kind="Pod")},
    )

    # Test accessing config collections directly
    assert test_config.template_snippets.get("test-snippet") is not None
    assert test_config.template_snippets.get("test-snippet").name == "test-snippet"

    assert test_config.maps.get("/test.map") is not None
    assert test_config.maps.get("/test.map").template == "test"

    assert test_config.certificates.get("/test.pem") is not None
    assert test_config.certificates.get("/test.pem").template == "cert"

    # Test not found
    assert test_config.template_snippets.get("nonexistent") is None
    assert test_config.maps.get("/nonexistent.map") is None
    assert test_config.certificates.get("/nonexistent.pem") is None

    # Test basic template context functionality
    from haproxy_template_ic.config_models import IndexedResourceCollection

    test_collection = IndexedResourceCollection()
    context_basic = TemplateContext(resources={"test": test_collection})
    assert len(context_basic.resources["test"]) == 0
    assert context_basic.namespace is None


# =============================================================================
# Parser Error Testing
# =============================================================================


def test_config_from_dict_error_conditions():
    """Test error conditions in config_from_dict."""
    # Test non-dict input - Pydantic will handle this
    with pytest.raises(ValueError):
        config_from_dict("not a dict")

    with pytest.raises(ValueError):
        config_from_dict(["list", "not", "dict"])

    # Test missing required fields - Pydantic validation errors
    with pytest.raises(ValueError):
        config_from_dict({})

    with pytest.raises(ValueError):
        config_from_dict({"pod_selector": {"match_labels": {"app": "test"}}})


def test_parse_pod_selector_errors():
    """Test pod_selector validation error conditions."""
    from haproxy_template_ic.config_models import config_from_dict

    # Test invalid pod_selector type - Pydantic validation
    with pytest.raises(ValueError):
        config_from_dict(
            {
                "pod_selector": "invalid_string",
                "haproxy_config": {"template": "global\n    daemon"},
            }
        )

    with pytest.raises(ValueError):
        config_from_dict(
            {
                "pod_selector": ["invalid", "list"],
                "haproxy_config": {"template": "global\n    daemon"},
            }
        )


def test_parse_maps_errors():
    """Test maps validation error conditions."""
    # Test that dict format is required for maps
    config = config_from_dict(
        {
            "pod_selector": {"match_labels": {"app": "test"}},
            "haproxy_config": {"template": "global\n    daemon"},
            "maps": {"/test": {"template": "simple_template"}},
        }
    )
    assert config.maps["/test"].template == "simple_template"

    # Test that missing template field raises validation error
    with pytest.raises(ValueError, match="Field required"):
        config_from_dict(
            {
                "pod_selector": {"match_labels": {"app": "test"}},
                "haproxy_config": {"template": "global\n    daemon"},
                "maps": {"/test": {}},
            }
        )

    # Test invalid maps type - this should still raise an error
    with pytest.raises(ValueError):
        config_from_dict(
            {
                "pod_selector": {"match_labels": {"app": "test"}},
                "haproxy_config": {"template": "global\n    daemon"},
                "maps": "invalid_string",
            }
        )


def test_parse_watched_resources_errors():
    """Test watched_resources validation error conditions."""
    # Test invalid watch resource (not dict) - should raise validation error
    with pytest.raises(ValueError, match="Input should be a valid dictionary"):
        config_from_dict(
            {
                "pod_selector": {"match_labels": {"app": "test"}},
                "haproxy_config": {"template": "global\n    daemon"},
                "watched_resources": {"test": "invalid_string"},
            }
        )

    # Test missing kind - this should still raise an error
    with pytest.raises(ValueError):
        config_from_dict(
            {
                "pod_selector": {"match_labels": {"app": "test"}},
                "haproxy_config": {"template": "global\n    daemon"},
                "watched_resources": {"test": {}},
            }
        )

    # Test non-dict watched_resources - should raise validation error
    with pytest.raises(ValueError, match="Input should be a valid dictionary"):
        config_from_dict(
            {
                "pod_selector": {"match_labels": {"app": "test"}},
                "haproxy_config": {"template": "global\n    daemon"},
                "watched_resources": "invalid_string",
            }
        )


def test_parse_template_snippets_errors():
    """Test template_snippets validation error conditions."""
    # Test dict format - snippets now accept dict format with name and template
    # So this is actually valid in the new format, testing valid snippet creation
    config = config_from_dict(
        {
            "pod_selector": {"match_labels": {"app": "test"}},
            "haproxy_config": {"template": "global\n    daemon"},
            "template_snippets": {
                "test": {"name": "test", "template": "valid template string"}
            },
        }
    )
    assert "test" in config.template_snippets

    # Test invalid non-string value - Pydantic validation
    with pytest.raises(ValueError):
        config_from_dict(
            {
                "pod_selector": {"match_labels": {"app": "test"}},
                "haproxy_config": {"template": "global\n    daemon"},
                "template_snippets": {"test": 123},
            }
        )

    # Test invalid type - Pydantic validation
    with pytest.raises(ValueError):
        config_from_dict(
            {
                "pod_selector": {"match_labels": {"app": "test"}},
                "haproxy_config": {"template": "global\n    daemon"},
                "template_snippets": "invalid_string",
            }
        )


def test_parse_certificates_errors():
    """Test certificates validation error conditions."""
    # Test invalid certificate format - Pydantic validation
    with pytest.raises(ValueError):
        config_from_dict(
            {
                "pod_selector": {"match_labels": {"app": "test"}},
                "haproxy_config": {"template": "global\n    daemon"},
                "certificates": {"test": "invalid_string"},
            }
        )

    # Test missing template - Pydantic validation
    with pytest.raises(ValueError):
        config_from_dict(
            {
                "pod_selector": {"match_labels": {"app": "test"}},
                "haproxy_config": {"template": "global\n    daemon"},
                "certificates": {"test": {}},
            }
        )

    # Test invalid certificates format - Pydantic validation (no longer supports list format)
    with pytest.raises(ValueError):
        config_from_dict(
            {
                "pod_selector": {"match_labels": {"app": "test"}},
                "haproxy_config": {"template": "global\n    daemon"},
                "certificates": ["invalid_string"],
            }
        )

    # Test invalid certificates type - Pydantic validation
    with pytest.raises(ValueError):
        config_from_dict(
            {
                "pod_selector": {"match_labels": {"app": "test"}},
                "haproxy_config": {"template": "global\n    daemon"},
                "certificates": "invalid_string",
            }
        )


def test_parse_resource_filter_errors():
    """Test resource filter validation error conditions."""
    # Test invalid filter type - Pydantic validation will handle this
    with pytest.raises(ValueError):
        config_from_dict(
            {
                "pod_selector": {"match_labels": {"app": "test"}},
                "haproxy_config": {"template": "global\n    daemon"},
                "watched_resources": {
                    "test": {
                        "api_version": "v1",
                        "kind": "Pod",
                        "resource_filter": "invalid_string",
                    }
                },
            }
        )


def test_list_format_parsing():
    """Test parsing dict format for maps, template_snippets, and certificates."""
    # Test maps dict format (new format only supports dict)
    config = config_from_dict(
        {
            "pod_selector": {"match_labels": {"app": "test"}},
            "haproxy_config": {"template": "global\n    daemon"},
            "maps": {
                "/test1.map": {"template": "test1"},
                "/test2.map": {"template": "test2"},
            },
        }
    )

    assert len(config.maps) == 2
    assert config.maps.get("/test1.map") is not None
    assert config.maps.get("/test2.map") is not None

    # Test template_snippets dict format
    config = config_from_dict(
        {
            "pod_selector": {"match_labels": {"app": "test"}},
            "haproxy_config": {"template": "global\n    daemon"},
            "template_snippets": {
                "snippet1": {"name": "snippet1", "template": "test1"},
                "snippet2": {"name": "snippet2", "template": "test2"},
            },
        }
    )

    assert len(config.template_snippets) == 2
    assert config.template_snippets.get("snippet1") is not None
    assert config.template_snippets.get("snippet2") is not None

    # Test certificates dict format (new format only supports dict)
    config = config_from_dict(
        {
            "pod_selector": {"match_labels": {"app": "test"}},
            "haproxy_config": {"template": "global\n    daemon"},
            "certificates": {
                "/etc/haproxy/certs/cert1.pem": {"template": "test1"},
                "/etc/haproxy/certs/cert2.pem": {"template": "test2"},
            },
        }
    )

    assert len(config.certificates) == 2
    assert config.certificates.get("/etc/haproxy/certs/cert1.pem") is not None
    assert config.certificates.get("/etc/haproxy/certs/cert2.pem") is not None

    # Test watched_resources dict format
    config = config_from_dict(
        {
            "pod_selector": {"match_labels": {"app": "test"}},
            "haproxy_config": {"template": "global\n    daemon"},
            "watched_resources": {
                "pods": {"api_version": "v1", "kind": "Pod"},
                "services": {"api_version": "v1", "kind": "Service"},
            },
        }
    )

    assert len(config.watched_resources) == 2
    assert config.watched_resources.get("pods") is not None
    assert config.watched_resources.get("services") is not None


def test_list_format_errors():
    """Test error conditions for validation."""
    # Test invalid maps format - Pydantic validation
    with pytest.raises(ValueError):
        config_from_dict(
            {
                "pod_selector": {"match_labels": {"app": "test"}},
                "haproxy_config": {"template": "global\n    daemon"},
                "maps": ["invalid_string"],
            }
        )

    # Test map path validation (relative paths not allowed)
    with pytest.raises(ValueError):
        config_from_dict(
            {
                "pod_selector": {"match_labels": {"app": "test"}},
                "haproxy_config": {"template": "global\n    daemon"},
                "maps": {"relative": {"template": "test"}},
            }
        )

    # Test watch_resources list format - should raise validation error
    with pytest.raises(ValueError, match="Input should be a valid dictionary"):
        config_from_dict(
            {
                "pod_selector": {"match_labels": {"app": "test"}},
                "haproxy_config": {"template": "global\n    daemon"},
                "watched_resources": ["invalid_string"],
            }
        )

    # Test watch_resources list with dict - should also raise validation error
    with pytest.raises(ValueError, match="Input should be a valid dictionary"):
        config_from_dict(
            {
                "pod_selector": {"match_labels": {"app": "test"}},
                "haproxy_config": {"template": "global\n    daemon"},
                "watched_resources": [{"id": "test"}],
            }
        )


# =============================================================================
# Template Snippet Include Tests
# =============================================================================


def test_template_snippet_basic_include():
    """Test basic template snippet inclusion using {% include %}."""
    config_dict = {
        "pod_selector": {"match_labels": {"app": "test"}},
        "haproxy_config": {"template": "global\n    daemon"},
        "template_snippets": {
            "ingress-backends": {
                "name": "ingress-backends",
                "template": "server {{ name }} {{ ip }}:{{ port }} check",
            }
        },
        "maps": {
            "/etc/haproxy/maps/backends.map": {
                "template": "{% include 'ingress-backends' %}"
            }
        },
    }

    config = config_from_dict(config_dict)

    # Test that snippet was parsed correctly
    assert len(config.template_snippets) == 1
    snippet = config.template_snippets.get("ingress-backends")
    assert snippet is not None
    assert snippet.name == "ingress-backends"

    # Test that map template can include the snippet
    map_config = config.maps.get("/etc/haproxy/maps/backends.map")
    assert map_config is not None

    # Render the template with snippet inclusion using the new API
    rendered = TemplateRenderer.from_config(config).render(
        map_config.template, name="web-server", ip="192.168.1.10", port="80"
    )
    assert rendered == "server web-server 192.168.1.10:80 check"


def test_template_snippet_multiple_includes():
    """Test multiple template snippets included in one template."""
    config_dict = {
        "pod_selector": {"match_labels": {"app": "test"}},
        "haproxy_config": {"template": "global\n    daemon"},
        "template_snippets": {
            "backend-header": {
                "name": "backend-header",
                "template": "backend {{ backend_name }}",
            },
            "server-entry": {
                "name": "server-entry",
                "template": "    server {{ name }} {{ ip }}:{{ port }} check",
            },
            "backend-footer": {
                "name": "backend-footer",
                "template": "    option httpchk GET /health",
            },
        },
        "maps": {
            "/etc/haproxy/maps/backend.map": {
                "template": "{% include 'backend-header' %}\n{% include 'server-entry' %}\n{% include 'backend-footer' %}"
            }
        },
    }

    config = config_from_dict(config_dict)

    # Test all snippets were parsed
    assert len(config.template_snippets) == 3

    # Render the template with multiple snippet inclusions
    map_config = config.maps.get("/etc/haproxy/maps/backend.map")
    rendered = (
        TemplateRenderer.from_config(config)
        .get_compiled(map_config.template)
        .render(backend_name="web-servers", name="web-1", ip="192.168.1.10", port="80")
    )

    expected = "backend web-servers    server web-1 192.168.1.10:80 check    option httpchk GET /health"
    assert rendered == expected


def test_template_snippet_with_variables():
    """Test template snippets that contain variables."""
    config_dict = {
        "pod_selector": {"match_labels": {"app": "test"}},
        "haproxy_config": {"template": "global\n    daemon"},
        "template_snippets": {
            "server-with-weight": {
                "name": "server-with-weight",
                "template": "server {{ name }} {{ ip }}:{{ port }} weight {{ weight | default(100) }} check",
            }
        },
        "maps": {
            "/etc/haproxy/maps/weighted.map": {
                "template": "{% for server in servers %}{% with name=server.name, ip=server.ip, port=server.port, weight=server.weight %}{% include 'server-with-weight' %}{% endwith %}\n{% endfor %}"
            }
        },
    }

    config = config_from_dict(config_dict)

    map_config = config.maps.get("/etc/haproxy/maps/weighted.map")
    servers = [
        {"name": "web-1", "ip": "192.168.1.10", "port": "80", "weight": 150},
        {"name": "web-2", "ip": "192.168.1.11", "port": "80"},
    ]

    rendered = (
        TemplateRenderer.from_config(config)
        .get_compiled(map_config.template)
        .render(servers=servers)
    )
    expected = "server web-1 192.168.1.10:80 weight 150 checkserver web-2 192.168.1.11:80 weight 100 check"
    assert rendered == expected


def test_template_snippet_nested_includes():
    """Test template snippets that include other snippets."""
    config_dict = {
        "pod_selector": {"match_labels": {"app": "test"}},
        "haproxy_config": {"template": "global\n    daemon"},
        "template_snippets": {
            "health-check": {"name": "health-check", "template": "check inter 5s"},
            "server-base": {
                "name": "server-base",
                "template": "server {{ name }} {{ ip }}:{{ port }}",
            },
            "server-full": {
                "name": "server-full",
                "template": "{% include 'server-base' %} {% include 'health-check' %}",
            },
        },
        "maps": {
            "/etc/haproxy/maps/servers.map": {"template": "{% include 'server-full' %}"}
        },
    }

    config = config_from_dict(config_dict)

    map_config = config.maps.get("/etc/haproxy/maps/servers.map")
    rendered = (
        TemplateRenderer.from_config(config)
        .get_compiled(map_config.template)
        .render(name="api-server", ip="10.0.1.5", port="8080")
    )

    expected = "server api-server 10.0.1.5:8080 check inter 5s"
    assert rendered == expected


def test_template_snippet_not_found_error():
    """Test error when trying to include a non-existent snippet."""
    config_dict = {
        "pod_selector": {"match_labels": {"app": "test"}},
        "haproxy_config": {"template": "global\n    daemon"},
        "template_snippets": {
            "existing-snippet": {"name": "existing-snippet", "template": "some content"}
        },
        "maps": {
            "/etc/haproxy/maps/error.map": {
                "template": "{% include 'non-existent-snippet' %}"
            }
        },
    }

    config = config_from_dict(config_dict)

    map_config = config.maps.get("/etc/haproxy/maps/error.map")

    # Should raise TemplateNotFound when trying to render
    from jinja2 import TemplateNotFound

    with pytest.raises(TemplateNotFound, match="non-existent-snippet"):
        TemplateRenderer.from_config(config).get_compiled(map_config.template).render()


def test_template_snippet_empty_collection():
    """Test behavior when no template snippets are defined."""
    config_dict = {
        "pod_selector": {"match_labels": {"app": "test"}},
        "haproxy_config": {"template": "global\n    daemon"},
        "maps": {
            "/etc/haproxy/maps/no-snippets.map": {
                "template": "plain template without includes"
            }
        },
    }

    config = config_from_dict(config_dict)

    # Should have empty snippet collection
    assert len(config.template_snippets) == 0

    # Template without includes should still work
    map_config = config.maps.get("/etc/haproxy/maps/no-snippets.map")
    rendered = (
        TemplateRenderer.from_config(config).get_compiled(map_config.template).render()
    )
    assert rendered == "plain template without includes"


def test_template_snippet_complex_example():
    """Test a complex real-world example with multiple snippets."""
    config_dict = {
        "pod_selector": {"match_labels": {"app": "haproxy"}},
        "haproxy_config": {"template": "global\n    daemon"},
        "template_snippets": {
            "path-map-entry": {
                "name": "path-map-entry",
                "template": "{% if resource.spec.rules %}{% for rule in resource.spec.rules %}{% for path in rule.http.paths %}{{ path.path }} {{ rule.host }}_{{ path.backend.service.name }}\n{% endfor %}{% endfor %}{% endif %}",
            },
            "backend-config": {
                "name": "backend-config",
                "template": "backend {{ backend_name }}\n    balance roundrobin\n    option httpchk GET {{ health_path | default('/health') }}",
            },
            "server-entry": {
                "name": "server-entry",
                "template": "    server {{ name }} {{ ip }}:{{ port }} check",
            },
        },
        "maps": {
            "/etc/haproxy/maps/path-exact.map": {
                "template": "{% for resource_key, resource in resources.ingresses.items() %}{% include 'path-map-entry' %}{% endfor %}"
            }
        },
    }

    config = config_from_dict(config_dict)

    # Test that all snippets were created
    assert len(config.template_snippets) == 3
    assert config.template_snippets.get("path-map-entry") is not None
    assert config.template_snippets.get("backend-config") is not None
    assert config.template_snippets.get("server-entry") is not None

    # Test the complex template rendering
    map_config = config.maps.get("/etc/haproxy/maps/path-exact.map")
    assert map_config is not None

    # Mock ingress data
    mock_resources = {
        "ingresses": {
            "default/example-ingress": {
                "spec": {
                    "rules": [
                        {
                            "host": "example.com",
                            "http": {
                                "paths": [
                                    {
                                        "path": "/api",
                                        "backend": {"service": {"name": "api-service"}},
                                    },
                                    {
                                        "path": "/web",
                                        "backend": {"service": {"name": "web-service"}},
                                    },
                                ]
                            },
                        }
                    ]
                }
            }
        }
    }

    rendered = (
        TemplateRenderer.from_config(config)
        .get_compiled(map_config.template)
        .render(resources=mock_resources)
    )
    expected_lines = ["/api example.com_api-service", "/web example.com_web-service"]

    # Check that both paths are in the rendered output
    for expected_line in expected_lines:
        assert expected_line in rendered


def test_template_snippet_update_during_config_reload():
    """Test that snippets are properly updated when configuration is reloaded."""
    # First configuration
    config_dict_1 = {
        "pod_selector": {"match_labels": {"app": "test"}},
        "haproxy_config": {"template": "global\n    daemon"},
        "template_snippets": {
            "greeting": {"name": "greeting", "template": "Hello {{ name }}"}
        },
        "maps": {"/test.map": {"template": "{% include 'greeting' %}"}},
    }

    config_1 = config_from_dict(config_dict_1)
    map_config_1 = config_1.maps.get("/test.map")
    rendered_1 = TemplateRenderer.from_config(config_1).render(
        map_config_1.template, name="World"
    )
    assert rendered_1 == "Hello World"

    # Second configuration with updated snippet
    config_dict_2 = {
        "pod_selector": {"match_labels": {"app": "test"}},
        "haproxy_config": {"template": "global\n    daemon"},
        "template_snippets": {
            "greeting": {"name": "greeting", "template": "Hi {{ name }}!"}
        },
        "maps": {"/test.map": {"template": "{% include 'greeting' %}"}},
    }

    config_2 = config_from_dict(config_dict_2)
    map_config_2 = config_2.maps.get("/test.map")
    rendered_2 = TemplateRenderer.from_config(config_2).render(
        map_config_2.template, name="World"
    )
    assert rendered_2 == "Hi World!"


def test_template_context_helper_methods():
    """Test the new helper methods for resource access."""
    from haproxy_template_ic.config_models import IndexedResourceCollection

    # Create IndexedResourceCollections for each resource type
    ingresses_collection = IndexedResourceCollection()
    ingresses_collection._internal_dict[("default", "ing1")] = {
        "metadata": {"name": "ing1"}
    }
    ingresses_collection._internal_dict[("default", "ing2")] = {
        "metadata": {"name": "ing2"}
    }

    services_collection = IndexedResourceCollection()
    services_collection._internal_dict[("default", "svc1")] = {
        "metadata": {"name": "svc1"}
    }

    empty_collection = IndexedResourceCollection()

    test_resources = {
        "ingresses": ingresses_collection,
        "services": services_collection,
        "empty_type": empty_collection,
    }

    context = TemplateContext(resources=test_resources)

    # Test basic resource access
    assert len(context.resources.get("ingresses", IndexedResourceCollection())) == 2
    assert len(context.resources.get("services", IndexedResourceCollection())) == 1
    assert len(context.resources.get("empty_type", IndexedResourceCollection())) == 0
    assert len(context.resources.get("nonexistent", IndexedResourceCollection())) == 0

    # Test resource iteration - now returns tuple keys like (namespace, name)
    ingress_items = list(
        context.resources.get("ingresses", IndexedResourceCollection()).items()
    )
    assert len(ingress_items) == 2
    # The keys are now tuples, not strings
    keys = [item[0] for item in ingress_items]
    assert ("default", "ing1") in keys
    assert ("default", "ing2") in keys

    # Test resource counting
    assert len(context.resources.get("ingresses", IndexedResourceCollection())) == 2
    assert len(context.resources.get("services", IndexedResourceCollection())) == 1
    assert len(context.resources.get("empty_type", IndexedResourceCollection())) == 0
    assert len(context.resources.get("nonexistent", IndexedResourceCollection())) == 0

    # Test resource existence
    assert bool(context.resources.get("ingresses", IndexedResourceCollection())) is True
    assert bool(context.resources.get("services", IndexedResourceCollection())) is True
    assert (
        bool(context.resources.get("empty_type", IndexedResourceCollection())) is False
    )
    assert (
        bool(context.resources.get("nonexistent", IndexedResourceCollection())) is False
    )


def test_template_compilation():
    """Test that template compilation works correctly with the new Pydantic implementation."""
    # Test that templates get compiled during config creation
    config_dict = {
        "pod_selector": {"match_labels": {"app": "test"}},
        "haproxy_config": {"template": "global\n    daemon"},
        "template_snippets": {
            "greeting": {"name": "greeting", "template": "Hello {{ name }}"}
        },
        "maps": {"/test.map": {"template": "{% include 'greeting' %}"}},
    }

    config = config_from_dict(config_dict)

    # Verify templates are compiled
    renderer = TemplateRenderer.from_config(config)
    assert renderer.get_compiled(config.haproxy_config.template) is not None
    assert (
        renderer.get_compiled(config.template_snippets["greeting"].template) is not None
    )
    assert renderer.get_compiled(config.maps["/test.map"].template) is not None

    # Test that templates can be rendered
    rendered = (
        TemplateRenderer.from_config(config)
        .get_compiled(config.maps["/test.map"].template)
        .render(name="World")
    )
    assert rendered == "Hello World"


def test_b64decode_filter():
    """Test the custom base64 decode filter."""
    import base64

    # Test valid base64 string using the new config system
    test_string = "Hello, World!"
    encoded = base64.b64encode(test_string.encode("utf-8")).decode("ascii")

    config_dict = {
        "pod_selector": {"match_labels": {"app": "test"}},
        "haproxy_config": {"template": "global\n    daemon"},
        "maps": {"/test.map": {"template": f"{{{{ '{encoded}' | b64decode }}}}"}},
    }

    config = config_from_dict(config_dict)
    result = (
        TemplateRenderer.from_config(config)
        .get_compiled(config.maps["/test.map"].template)
        .render()
    )
    assert result == test_string

    # Test another string with special characters
    test_string2 = "Special chars: ñáéíóú!@#$%^&*()"
    encoded2 = base64.b64encode(test_string2.encode("utf-8")).decode("ascii")

    config_dict2 = {
        "pod_selector": {"match_labels": {"app": "test"}},
        "haproxy_config": {"template": "global\n    daemon"},
        "maps": {"/test2.map": {"template": f"{{{{ '{encoded2}' | b64decode }}}}"}},
    }

    config2 = config_from_dict(config_dict2)
    result2 = TemplateRenderer.from_config(config2).render(
        config2.maps["/test2.map"].template
    )
    assert result2 == test_string2

    # Test invalid base64 should raise error
    config_dict_invalid = {
        "pod_selector": {"match_labels": {"app": "test"}},
        "haproxy_config": {"template": "global\n    daemon"},
        "maps": {"/invalid.map": {"template": "{{ 'invalid_base64!' | b64decode }}"}},
    }

    config_invalid = config_from_dict(config_dict_invalid)
    with pytest.raises(ValueError, match="Failed to decode base64 value"):
        TemplateRenderer.from_config(config_invalid).render(
            config_invalid.maps["/invalid.map"].template
        )


def test_type_safety_enhancements():
    """Test the new type safety enhancements for config parsing."""

    # Test watch resources with non-string kind (dict format)
    with pytest.raises(ValueError, match="Input should be a valid string"):
        config_from_dict(
            {
                "pod_selector": {"match_labels": {"app": "test"}},
                "haproxy_config": {"template": "global\n    daemon"},
                "watched_resources": {
                    "test": {"kind": 123}  # Non-string kind
                },
            }
        )

    # Test watch resources with list format - should now raise error with Pydantic
    with pytest.raises(ValueError, match="Input should be a valid dictionary"):
        config_from_dict(
            {
                "pod_selector": {"match_labels": {"app": "test"}},
                "haproxy_config": {"template": "global\n    daemon"},
                "watched_resources": [
                    {"kind": ["Pod"]}  # List format is no longer accepted
                ],
            }
        )

    # Test maps with non-string template (dict format)
    with pytest.raises(ValueError, match="Input should be a valid string"):
        config_from_dict(
            {
                "pod_selector": {"match_labels": {"app": "test"}},
                "haproxy_config": {"template": "global\n    daemon"},
                "maps": {
                    "/test.map": {"template": 123}  # Non-string template
                },
            }
        )

    # Test maps with list format - should raise error
    with pytest.raises(ValueError, match="Input should be a valid dictionary"):
        config_from_dict(
            {
                "pod_selector": {"match_labels": {"app": "test"}},
                "haproxy_config": {"template": "global\n    daemon"},
                "maps": [
                    {"path": 123, "template": "test"}  # List format not supported
                ],
            }
        )

    # Test maps with list format - should raise error
    with pytest.raises(ValueError, match="Input should be a valid dictionary"):
        config_from_dict(
            {
                "pod_selector": {"match_labels": {"app": "test"}},
                "haproxy_config": {"template": "global\n    daemon"},
                "maps": [
                    {
                        "path": "/test.map",
                        "template": ["test"],
                    }  # List format not supported
                ],
            }
        )

    # Test certificates with non-string template (dict format)
    with pytest.raises(ValueError, match="Input should be a valid string"):
        config_from_dict(
            {
                "pod_selector": {"match_labels": {"app": "test"}},
                "haproxy_config": {"template": "global\n    daemon"},
                "certificates": {
                    "test.crt": {"template": {"key": "value"}}  # Non-string template
                },
            }
        )

    # Test certificates with list format - should raise error
    with pytest.raises(ValueError, match="Input should be a valid dictionary"):
        config_from_dict(
            {
                "pod_selector": {"match_labels": {"app": "test"}},
                "haproxy_config": {"template": "global\n    daemon"},
                "certificates": [
                    {"name": 123, "template": "test"}  # List format not supported
                ],
            }
        )

    # Test certificates with list format - should raise error
    with pytest.raises(ValueError, match="Input should be a valid dictionary"):
        config_from_dict(
            {
                "pod_selector": {"match_labels": {"app": "test"}},
                "haproxy_config": {"template": "global\n    daemon"},
                "certificates": [
                    {"name": "test.crt", "template": None}  # List format not supported
                ],
            }
        )


def test_host_map_template_rendering():
    """Test that host map template renders correctly with ingress resources."""
    # Create a config with host map template
    config_dict = {
        "pod_selector": {"match_labels": {"app": "haproxy"}},
        "haproxy_config": {"template": "global\n    daemon"},
        "maps": {
            "/etc/haproxy/maps/host.map": {
                "template": """{% for _, ingress in resources.get('ingresses', {}).items() %}
{% if ingress.spec and ingress.spec.rules %}
{% for rule in ingress.spec.rules %}
{% if rule.host %}
{{ rule.host }} {{ rule.host }}
{% endif %}
{% endfor %}
{% endif %}
{% endfor %}"""
            }
        },
    }

    config = config_from_dict(config_dict)

    # Create mock ingress resources using IndexedResourceCollection
    from haproxy_template_ic.config_models import IndexedResourceCollection

    ingresses_collection = IndexedResourceCollection()
    ingresses_collection._internal_dict[("default", "test-ingress")] = [
        {
            "metadata": {"name": "test-ingress", "namespace": "default"},
            "spec": {
                "rules": [
                    {"host": "example.com"},
                    {"host": "www.example.com"},
                    {"host": "api.example.com"},
                ]
            },
        }
    ]
    ingresses_collection._internal_dict[("production", "prod-ingress")] = [
        {
            "metadata": {"name": "prod-ingress", "namespace": "production"},
            "spec": {"rules": [{"host": "prod.example.com"}]},
        }
    ]

    mock_resources = {"ingresses": ingresses_collection}

    # Create template context
    context = TemplateContext(resources=mock_resources)

    # Render the host map
    host_map_config = config.maps.get("/etc/haproxy/maps/host.map")
    template_vars = {
        "resources": context.resources,
        "namespace": context.namespace,
    }

    rendered_content = (
        TemplateRenderer.from_config(config)
        .get_compiled(host_map_config.template)
        .render(**template_vars)
    )

    # Verify the rendered content contains expected hosts
    assert "example.com example.com" in rendered_content
    assert "www.example.com www.example.com" in rendered_content
    assert "api.example.com api.example.com" in rendered_content
    assert "prod.example.com prod.example.com" in rendered_content

    # Verify it doesn't contain empty entries
    assert "  " not in rendered_content  # No double spaces from empty hosts


def test_complete_ingress_configuration_with_certificates():
    """Test a complete ingress controller configuration including certificates with b64decode."""
    import base64

    # Create TLS certificate data
    cert_data = (
        "-----BEGIN CERTIFICATE-----\nMIIB...test cert...\n-----END CERTIFICATE-----"
    )
    key_data = (
        "-----BEGIN PRIVATE KEY-----\nMIIE...test key...\n-----END PRIVATE KEY-----"
    )

    cert_b64 = base64.b64encode(cert_data.encode("utf-8")).decode("ascii")
    key_b64 = base64.b64encode(key_data.encode("utf-8")).decode("ascii")

    config_dict = {
        "pod_selector": {"match_labels": {"app": "haproxy"}},
        "haproxy_config": {"template": "global\n    daemon"},
        "certificates": {
            "/etc/haproxy/certs/tls.pem": {
                "template": """{% for _, secret in resources.get('secrets', {}).items() %}
{% if secret.type == "kubernetes.io/tls" and secret.metadata.labels.get('haproxy-template-ic/tls') == 'true' %}
# Certificate for {{ secret.metadata.name }} in {{ secret.metadata.namespace }}
{{ secret.data.get('tls.crt') | b64decode }}
{{ secret.data.get('tls.key') | b64decode }}

{% endif %}
{% endfor %}"""
            }
        },
    }

    config = config_from_dict(config_dict)

    # Create mock TLS secret using IndexedResourceCollection
    from haproxy_template_ic.config_models import IndexedResourceCollection

    secrets_collection = IndexedResourceCollection()
    secrets_collection._internal_dict[("default", "example-tls")] = [
        {
            "metadata": {
                "name": "example-tls",
                "namespace": "default",
                "labels": {"haproxy-template-ic/tls": "true"},
            },
            "type": "kubernetes.io/tls",
            "data": {"tls.crt": cert_b64, "tls.key": key_b64},
        }
    ]

    mock_resources = {"secrets": secrets_collection}

    # Create template context
    context = TemplateContext(resources=mock_resources)

    # Render the certificate template
    cert_config = config.certificates.get("/etc/haproxy/certs/tls.pem")
    template_vars = {
        "resources": context.resources,
        "namespace": context.namespace,
    }

    rendered_content = (
        TemplateRenderer.from_config(config)
        .get_compiled(cert_config.template)
        .render(**template_vars)
    )

    # Verify the certificate and key were decoded correctly
    assert cert_data in rendered_content
    assert key_data in rendered_content
    assert "# Certificate for example-tls in default" in rendered_content


# =============================================================================
# HAProxyConfigContext Helper Method Tests
# =============================================================================


def test_haproxy_config_context_get_rendered_map_by_path():
    """Test getting rendered map by path."""
    config = Config(
        pod_selector=PodSelector(match_labels={"app": "haproxy"}),
        haproxy_config=MapConfig(template="global\n    daemon"),
    )
    template_context = TemplateContext()

    map_config = MapConfig(template="test")
    rendered_map1 = RenderedMap(
        path="/test1.map", content="content1", map_config=map_config
    )
    rendered_map2 = RenderedMap(
        path="/test2.map", content="content2", map_config=map_config
    )

    context = HAProxyConfigContext(
        config=config,
        template_context=template_context,
        rendered_maps=[rendered_map1, rendered_map2],
    )

    # Test finding existing map
    found_map = context.get_rendered_map_by_path("/test1.map")
    assert found_map == rendered_map1
    assert found_map.content == "content1"

    # Test not found
    not_found = context.get_rendered_map_by_path("/nonexistent.map")
    assert not_found is None


def test_haproxy_config_context_get_rendered_certificate_by_path():
    """Test getting rendered certificate by path."""
    config = Config(
        pod_selector=PodSelector(match_labels={"app": "haproxy"}),
        haproxy_config=MapConfig(template="global\n    daemon"),
    )
    template_context = TemplateContext()

    cert1 = RenderedCertificate(path="/cert1.pem", content="cert1 content")
    cert2 = RenderedCertificate(path="/cert2.pem", content="cert2 content")

    context = HAProxyConfigContext(
        config=config,
        template_context=template_context,
        rendered_certificates=[cert1, cert2],
    )

    # Test finding existing certificate
    found_cert = context.get_rendered_certificate_by_path("/cert1.pem")
    assert found_cert == cert1
    assert found_cert.content == "cert1 content"

    # Test not found
    not_found = context.get_rendered_certificate_by_path("/nonexistent.pem")
    assert not_found is None


# =============================================================================
# Type Alias and Constraint Tests
# =============================================================================


def test_watch_resource_config_group_property():
    """Test WatchResourceConfig group property extraction."""
    # Test with group
    resource = WatchResourceConfig(api_version="networking.k8s.io/v1", kind="Ingress")
    assert resource.group == "networking.k8s.io"

    # Test without group (core API)
    resource = WatchResourceConfig(api_version="v1", kind="Service")
    assert resource.group == ""


def test_watch_resource_config_version_property():
    """Test WatchResourceConfig version property extraction."""
    # Test with group
    resource = WatchResourceConfig(api_version="networking.k8s.io/v1", kind="Ingress")
    assert resource.version == "v1"

    # Test without group (core API)
    resource = WatchResourceConfig(api_version="v1", kind="Service")
    assert resource.version == "v1"

    # Test with version suffix
    resource = WatchResourceConfig(api_version="apps/v1beta1", kind="Deployment")
    assert resource.version == "v1beta1"


def test_template_snippet_name_validation():
    """Test TemplateSnippet name validation in config."""
    from haproxy_template_ic.config_models import TemplateSnippet

    # Test valid snippet creation
    snippet = TemplateSnippet(name="valid-name", template="test template")
    assert snippet.name == "valid-name"

    # Test name validation in config
    config_dict = {
        "pod_selector": {"match_labels": {"app": "haproxy"}},
        "haproxy_config": {"template": "global\n    daemon"},
        "template_snippets": {
            "test-snippet": {
                "name": "different-name",  # Doesn't match key
                "template": "test",
            }
        },
    }

    with pytest.raises(ValueError, match="must match snippet.name"):
        config_from_dict(config_dict)


def test_resource_filter_creation():
    """Test ResourceFilter model creation."""
    from haproxy_template_ic.config_models import ResourceFilter

    # Test with all fields
    filter_obj = ResourceFilter(
        namespace_selector={"environment": "production"},
        label_selector={"app": "web", "version": "v1.0.0"},
    )

    assert filter_obj.namespace_selector == {"environment": "production"}
    assert filter_obj.label_selector == {"app": "web", "version": "v1.0.0"}

    # Test with optional fields None
    filter_obj = ResourceFilter()
    assert filter_obj.namespace_selector is None
    assert filter_obj.label_selector is None


def test_pod_selector_frozen():
    """Test that PodSelector is frozen."""
    from haproxy_template_ic.config_models import PodSelector

    selector = PodSelector(match_labels={"app": "test"})

    # Should not be able to modify (frozen dataclass)
    with pytest.raises(ValidationError):
        selector.match_labels = {"app": "modified"}
