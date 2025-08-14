import pytest

from haproxy_template_ic.config import (
    Config,
    WatchResourceConfig,
    MapConfig,
    CertificateConfig,
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
                "watch_resources": {},
                "maps": {},
            },
            {"app": "myapp"},
            0,
            0,
        ),
        # Config with watch_resources
        (
            {
                "pod_selector": {"match_labels": {"app": "myapp"}},
                "haproxy_config": {"template": "global\n    daemon"},
                "watch_resources": {
                    "ingresses": {
                        "group": "networking.k8s.io",
                        "version": "v1",
                        "kind": "Ingress",
                    },
                    "services": {"group": "", "version": "v1", "kind": "Service"},
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
                "watch_resources": {
                    "ingresses": {"group": "networking.k8s.io", "kind": "Ingress"}
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
    assert len(config.watch_resources) == expected_watch_resources_count
    assert len(config.maps) == expected_maps_count


@pytest.mark.parametrize(
    "config_dict,expected_watch_resource",
    [
        (
            {
                "pod_selector": {"match_labels": {"app": "myapp"}},
                "haproxy_config": {"template": "global\n    daemon"},
                "watch_resources": {
                    "ingresses": {
                        "group": "networking.k8s.io",
                        "version": "v1",
                        "kind": "Ingress",
                    }
                },
            },
            {
                "name": "ingresses",
                "group": "networking.k8s.io",
                "version": "v1",
                "kind": "Ingress",
            },
        ),
        (
            {
                "pod_selector": {"match_labels": {"app": "myapp"}},
                "haproxy_config": {"template": "global\n    daemon"},
                "watch_resources": {
                    "services": {"group": "", "version": "v1", "kind": "Service"}
                },
            },
            {"name": "services", "group": "", "version": "v1", "kind": "Service"},
        ),
        (
            {
                "pod_selector": {"match_labels": {"app": "myapp"}},
                "haproxy_config": {"template": "global\n    daemon"},
                "watch_resources": {
                    "pods": {"group": None, "version": None, "kind": "Pod"}
                },
            },
            {"name": "pods", "group": None, "version": None, "kind": "Pod"},
        ),
    ],
)
def test_watch_resources_structure(config_dict, expected_watch_resource):
    """Test that watch_resources are properly structured as WatchResourceConfig objects."""
    config = config_from_dict(config_dict)

    # Find the watch resource by id in the list
    target_id = expected_watch_resource["name"]
    watch_resource = None
    for wr in config.watch_resources:
        if wr.id == target_id:
            watch_resource = wr
            break

    assert watch_resource is not None, f"Watch resource with id {target_id} not found"
    assert isinstance(watch_resource, WatchResourceConfig)
    assert watch_resource.id == expected_watch_resource["name"]
    assert watch_resource.group == expected_watch_resource["group"]
    assert watch_resource.version == expected_watch_resource["version"]
    assert watch_resource.kind == expected_watch_resource["kind"]


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

    # Find the map config by path in the list
    target_path = expected_map["name"]
    map_config = None
    for map_cfg in config.maps:
        if map_cfg.path == target_path:
            map_config = map_cfg
            break

    assert map_config is not None, f"Map with path {target_path} not found"
    assert isinstance(map_config, MapConfig)
    # Path is now stored in the MapConfig object
    assert map_config.path == expected_map["path"]
    assert isinstance(map_config.template, Template)
    # Test that the template renders correctly with sample data
    rendered = map_config.template.render(
        name="test-server", ip="192.168.1.1", port="8080", format="combined"
    )
    assert rendered == expected_map["expected_rendered"]


@pytest.mark.parametrize(
    "config_dict",
    [
        # Missing required pod_selector field
        {"watch_resources": {}},
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
            "watch_resources": {},
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
            "watch_resources": {"pods": {"group": "v1", "version": "v1"}},
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
    map_config = MapConfig(template=Template("test {{ name }}"))
    rendered_map = RenderedMap(
        path="/etc/haproxy/maps/test.map", content="test content", map_config=map_config
    )

    assert rendered_map.path == "/etc/haproxy/maps/test.map"
    assert rendered_map.content == "test content"
    assert rendered_map.map_config == map_config


def test_rendered_map_is_frozen():
    """Test that RenderedMap is immutable."""
    map_config = MapConfig(template=Template("test"))
    rendered_map = RenderedMap(path="/test", content="content", map_config=map_config)

    with pytest.raises(AttributeError):
        rendered_map.path = "/new/path"


# TemplateContext Tests
def test_template_context_creation():
    """Test TemplateContext dataclass creation."""
    resources = {"name": "test", "host": "example.com"}
    context = TemplateContext(resources=resources, cluster_name="test-cluster")

    assert context.resources == resources
    assert context.cluster_name == "test-cluster"


def test_template_context_default_resources():
    """Test TemplateContext with default empty resources."""
    context = TemplateContext()

    assert context.resources == {}
    assert context.cluster_name == "default"


def test_template_context_is_frozen():
    """Test that TemplateContext is immutable."""
    context = TemplateContext(resources={"name": "test"})

    with pytest.raises(AttributeError):
        context.resources = {"name": "new"}

    with pytest.raises(AttributeError):
        context.cluster_name = "new-cluster"


# HAProxyConfigContext Tests
def test_haproxy_config_context_creation():
    """Test HAProxyConfigContext dataclass creation."""
    context = HAProxyConfigContext()

    assert context.rendered_maps == []


def test_haproxy_config_context_with_custom_data():
    """Test HAProxyConfigContext with custom rendered maps."""
    map_config = MapConfig(template=Template("test"), path="/test")
    rendered_map = RenderedMap(path="/test", content="content", map_config=map_config)
    rendered_maps = [rendered_map]

    context = HAProxyConfigContext(rendered_maps=rendered_maps)

    assert context.rendered_maps == rendered_maps


def test_haproxy_config_context_mutable():
    """Test that HAProxyConfigContext is mutable (not frozen)."""
    context = HAProxyConfigContext()
    map_config = MapConfig(template=Template("test"), path="/test")
    rendered_map = RenderedMap(path="/test", content="content", map_config=map_config)

    # Should be able to modify rendered_maps
    context.rendered_maps.append(rendered_map)
    assert len(context.rendered_maps) == 1
    assert context.rendered_maps[0] == rendered_map


# RenderedConfig Tests
def test_rendered_config_creation():
    """Test RenderedConfig dataclass creation."""
    config = Config(
        raw={},
        pod_selector={"match_labels": {}},
        haproxy_config=Template("global\n    daemon"),
    )

    rendered_config = RenderedConfig(content="global\n    daemon", config=config)

    assert rendered_config.content == "global\n    daemon"
    assert rendered_config.config == config


def test_rendered_config_frozen():
    """Test that RenderedConfig is frozen (immutable)."""
    config = Config(
        raw={},
        pod_selector={"match_labels": {}},
        haproxy_config=Template("global\n    daemon"),
    )

    rendered_config = RenderedConfig(content="global\n    daemon", config=config)

    # Should not be able to modify fields
    with pytest.raises(AttributeError):
        rendered_config.content = "new content"

    with pytest.raises(AttributeError):
        rendered_config.config = config


def test_haproxy_config_context_with_rendered_config():
    """Test HAProxyConfigContext with rendered config."""
    config = Config(
        raw={},
        pod_selector={"match_labels": {}},
        haproxy_config=Template("global\n    daemon"),
    )

    rendered_config = RenderedConfig(content="global\n    daemon", config=config)
    context = HAProxyConfigContext(rendered_config=rendered_config)

    assert context.rendered_config == rendered_config
    assert context.rendered_config.content == "global\n    daemon"


def test_haproxy_config_context_default_rendered_config():
    """Test HAProxyConfigContext default rendered_config is None."""
    context = HAProxyConfigContext()

    assert context.rendered_config is None
    assert context.rendered_maps == []


# RenderedCertificate Tests
def test_rendered_certificate_creation():
    """Test RenderedCertificate dataclass creation."""
    certificate_config = CertificateConfig(
        template=Template("cert content"), name="test-cert"
    )

    rendered_certificate = RenderedCertificate(
        name="test-cert", content="cert content", certificate_config=certificate_config
    )

    assert rendered_certificate.name == "test-cert"
    assert rendered_certificate.content == "cert content"
    assert rendered_certificate.certificate_config == certificate_config


def test_rendered_certificate_frozen():
    """Test that RenderedCertificate is frozen (immutable)."""
    certificate_config = CertificateConfig(
        template=Template("cert content"), name="test-cert"
    )

    rendered_certificate = RenderedCertificate(
        name="test-cert", content="cert content", certificate_config=certificate_config
    )

    # Should not be able to modify fields
    with pytest.raises(AttributeError):
        rendered_certificate.name = "new-name"

    with pytest.raises(AttributeError):
        rendered_certificate.content = "new content"

    with pytest.raises(AttributeError):
        rendered_certificate.certificate_config = certificate_config


def test_haproxy_config_context_with_rendered_certificates():
    """Test HAProxyConfigContext with rendered certificates."""
    certificate_config = CertificateConfig(
        template=Template("cert content"), name="test-cert"
    )

    rendered_certificate = RenderedCertificate(
        name="test-cert", content="cert content", certificate_config=certificate_config
    )

    context = HAProxyConfigContext(rendered_certificates=[rendered_certificate])

    assert len(context.rendered_certificates) == 1
    assert context.rendered_certificates[0] == rendered_certificate
    assert context.rendered_certificates[0].name == "test-cert"


def test_haproxy_config_context_default_rendered_certificates():
    """Test HAProxyConfigContext default rendered_certificates is empty list."""
    context = HAProxyConfigContext()

    assert context.rendered_certificates == []


# =============================================================================
# Collection Classes Tests
# =============================================================================


def test_watch_resource_collection_by_id():
    """Test WatchResourceCollection.by_id method."""
    from haproxy_template_ic.config import WatchResourceCollection, WatchResourceConfig

    resources = WatchResourceCollection(
        [
            WatchResourceConfig(kind="Pod", group="", version="v1", id="pods"),
            WatchResourceConfig(kind="Service", group="", version="v1", id="services"),
            WatchResourceConfig(
                kind="Ingress", group="networking.k8s.io", version="v1", id="ingresses"
            ),
        ]
    )

    # Test successful lookup
    found = resources.by_id("services")
    assert found is not None
    assert found.kind == "Service"
    assert found.id == "services"

    # Test not found
    not_found = resources.by_id("nonexistent")
    assert not_found is None

    # Test empty collection
    empty_collection = WatchResourceCollection([])
    assert empty_collection.by_id("anything") is None


def test_map_collection_by_path():
    """Test MapCollection.by_path method."""
    from haproxy_template_ic.config import MapCollection, MapConfig
    from jinja2 import Template

    maps = MapCollection(
        [
            MapConfig(
                path="/etc/haproxy/maps/backend.map", template=Template("backend map")
            ),
            MapConfig(path="/etc/haproxy/maps/path.map", template=Template("path map")),
            MapConfig(path="/etc/haproxy/maps/host.map", template=Template("host map")),
        ]
    )

    # Test successful lookup
    found = maps.by_path("/etc/haproxy/maps/path.map")
    assert found is not None
    assert found.path == "/etc/haproxy/maps/path.map"

    # Test not found
    not_found = maps.by_path("/nonexistent.map")
    assert not_found is None

    # Test empty collection
    empty_collection = MapCollection([])
    assert empty_collection.by_path("/anything") is None


def test_template_snippet_collection_by_name():
    """Test TemplateSnippetCollection.by_name method."""
    from haproxy_template_ic.config import TemplateSnippetCollection, TemplateSnippet
    from jinja2 import Template

    snippets = TemplateSnippetCollection(
        [
            TemplateSnippet(
                name="backend-servers",
                template=Template("backend servers"),
                source="backend servers",
            ),
            TemplateSnippet(
                name="health-check",
                template=Template("health check"),
                source="health check",
            ),
            TemplateSnippet(
                name="logging",
                template=Template("logging config"),
                source="logging config",
            ),
        ]
    )

    # Test successful lookup
    found = snippets.by_name("health-check")
    assert found is not None
    assert found.name == "health-check"

    # Test not found
    not_found = snippets.by_name("nonexistent")
    assert not_found is None

    # Test empty collection
    empty_collection = TemplateSnippetCollection([])
    assert empty_collection.by_name("anything") is None


def test_certificate_collection_by_name():
    """Test CertificateCollection.by_name method."""
    from haproxy_template_ic.config import CertificateCollection, CertificateConfig
    from jinja2 import Template

    certificates = CertificateCollection(
        [
            CertificateConfig(name="tls.pem", template=Template("tls cert")),
            CertificateConfig(name="ca.pem", template=Template("ca cert")),
            CertificateConfig(name="server.pem", template=Template("server cert")),
        ]
    )

    # Test successful lookup
    found = certificates.by_name("ca.pem")
    assert found is not None
    assert found.name == "ca.pem"

    # Test not found
    not_found = certificates.by_name("nonexistent.pem")
    assert not_found is None

    # Test empty collection
    empty_collection = CertificateCollection([])
    assert empty_collection.by_name("anything") is None


def test_template_context_get_methods():
    """Test TemplateContext get_* methods."""
    from haproxy_template_ic.config import (
        TemplateContext,
        Config,
        WatchResourceCollection,
        MapCollection,
        TemplateSnippetCollection,
        CertificateCollection,
        MapConfig,
        TemplateSnippet,
        CertificateConfig,
        PodSelector,
    )
    from jinja2 import Template

    # Create config with collections
    maps = MapCollection([MapConfig(path="/test.map", template=Template("test"))])
    snippets = TemplateSnippetCollection(
        [
            TemplateSnippet(
                name="test-snippet", template=Template("snippet"), source="snippet"
            )
        ]
    )
    certificates = CertificateCollection(
        [CertificateConfig(name="test.pem", template=Template("cert"))]
    )

    config = Config(
        raw={"test": "config"},
        pod_selector=PodSelector(match_labels={"app": "test"}),
        haproxy_config=Template("global\n    daemon"),
        maps=maps,
        template_snippets=snippets,
        certificates=certificates,
        watch_resources=WatchResourceCollection([]),
    )

    context = TemplateContext(config=config)

    # Test successful lookups
    assert context.get_template_snippet("test-snippet") is not None
    assert context.get_template_snippet("test-snippet").name == "test-snippet"

    assert context.get_map_config("/test.map") is not None
    assert context.get_map_config("/test.map").path == "/test.map"

    assert context.get_certificate_config("test.pem") is not None
    assert context.get_certificate_config("test.pem").name == "test.pem"

    # Test not found
    assert context.get_template_snippet("nonexistent") is None
    assert context.get_map_config("/nonexistent.map") is None
    assert context.get_certificate_config("nonexistent.pem") is None

    # Test with no config
    context_no_config = TemplateContext()
    assert context_no_config.get_template_snippet("anything") is None
    assert context_no_config.get_map_config("anything") is None
    assert context_no_config.get_certificate_config("anything") is None


# =============================================================================
# Parser Error Testing
# =============================================================================


def test_config_from_dict_error_conditions():
    """Test error conditions in config_from_dict."""
    # Test non-dict input
    with pytest.raises(ValueError, match="Configuration must be a dictionary"):
        config_from_dict("not a dict")

    with pytest.raises(ValueError, match="Configuration must be a dictionary"):
        config_from_dict(["list", "not", "dict"])

    # Test missing required fields
    with pytest.raises(ValueError, match="Missing required field: pod_selector"):
        config_from_dict({})

    with pytest.raises(ValueError, match="Missing required field: haproxy_config"):
        config_from_dict({"pod_selector": {"match_labels": {"app": "test"}}})


def test_parse_pod_selector_errors():
    """Test parse_pod_selector error conditions."""
    from haproxy_template_ic.config import config_from_dict

    # Test invalid pod_selector type
    with pytest.raises(ValueError, match="pod_selector must be a dict"):
        config_from_dict(
            {
                "pod_selector": "invalid_string",
                "haproxy_config": {"template": "global\n    daemon"},
            }
        )

    with pytest.raises(ValueError, match="pod_selector must be a dict"):
        config_from_dict(
            {
                "pod_selector": ["invalid", "list"],
                "haproxy_config": {"template": "global\n    daemon"},
            }
        )


def test_parse_maps_errors():
    """Test parse_maps error conditions."""
    # Test invalid map config (not dict)
    with pytest.raises(ValueError, match="Map config for '/test' must be a dict"):
        config_from_dict(
            {
                "pod_selector": {"match_labels": {"app": "test"}},
                "haproxy_config": {"template": "global\n    daemon"},
                "maps": {"/test": "invalid_string"},
            }
        )

    # Test missing template
    with pytest.raises(ValueError, match="Map '/test' missing required 'template'"):
        config_from_dict(
            {
                "pod_selector": {"match_labels": {"app": "test"}},
                "haproxy_config": {"template": "global\n    daemon"},
                "maps": {"/test": {}},
            }
        )

    # Test invalid maps type
    with pytest.raises(ValueError, match="maps must be a dict"):
        config_from_dict(
            {
                "pod_selector": {"match_labels": {"app": "test"}},
                "haproxy_config": {"template": "global\n    daemon"},
                "maps": "invalid_string",
            }
        )


def test_parse_watch_resources_errors():
    """Test parse_watch_resources error conditions."""
    # Test invalid watch resource (not dict)
    with pytest.raises(ValueError, match="Watch resource 'test' must be a dict"):
        config_from_dict(
            {
                "pod_selector": {"match_labels": {"app": "test"}},
                "haproxy_config": {"template": "global\n    daemon"},
                "watch_resources": {"test": "invalid_string"},
            }
        )

    # Test missing kind
    with pytest.raises(
        ValueError, match="Watch resource 'test' missing required 'kind'"
    ):
        config_from_dict(
            {
                "pod_selector": {"match_labels": {"app": "test"}},
                "haproxy_config": {"template": "global\n    daemon"},
                "watch_resources": {"test": {}},
            }
        )

    # Test invalid watch_resources type
    with pytest.raises(ValueError, match="watch_resources must be a dict"):
        config_from_dict(
            {
                "pod_selector": {"match_labels": {"app": "test"}},
                "haproxy_config": {"template": "global\n    daemon"},
                "watch_resources": "invalid_string",
            }
        )


def test_parse_template_snippets_errors():
    """Test parse_template_snippets error conditions."""
    # Test dict format errors
    with pytest.raises(ValueError, match="Template snippet 'test' must be a string"):
        config_from_dict(
            {
                "pod_selector": {"match_labels": {"app": "test"}},
                "haproxy_config": {"template": "global\n    daemon"},
                # Using a dict for a snippet should be invalid now
                "template_snippets": {"test": {"template": "invalid"}},
            }
        )

    # Dict value must be a string, any non-string is invalid
    with pytest.raises(ValueError, match="Template snippet 'test' must be a string"):
        config_from_dict(
            {
                "pod_selector": {"match_labels": {"app": "test"}},
                "haproxy_config": {"template": "global\n    daemon"},
                "template_snippets": {"test": 123},
            }
        )

    # Test list format errors
    with pytest.raises(ValueError, match="template_snippets must be a dict"):
        config_from_dict(
            {
                "pod_selector": {"match_labels": {"app": "test"}},
                "haproxy_config": {"template": "global\n    daemon"},
                "template_snippets": ["invalid_string"],
            }
        )

    # Test invalid type
    with pytest.raises(ValueError, match="template_snippets must be a dict"):
        config_from_dict(
            {
                "pod_selector": {"match_labels": {"app": "test"}},
                "haproxy_config": {"template": "global\n    daemon"},
                "template_snippets": "invalid_string",
            }
        )


def test_parse_certificates_errors():
    """Test parse_certificates error conditions."""
    # Test dict format errors
    with pytest.raises(ValueError, match="Certificate 'test' must be a dict"):
        config_from_dict(
            {
                "pod_selector": {"match_labels": {"app": "test"}},
                "haproxy_config": {"template": "global\n    daemon"},
                "certificates": {"test": "invalid_string"},
            }
        )

    # Test missing template in dict format
    with pytest.raises(
        ValueError, match="Certificate 'test' missing required 'template'"
    ):
        config_from_dict(
            {
                "pod_selector": {"match_labels": {"app": "test"}},
                "haproxy_config": {"template": "global\n    daemon"},
                "certificates": {"test": {}},
            }
        )

    # Test list format errors
    with pytest.raises(ValueError, match="Certificate must be a dict"):
        config_from_dict(
            {
                "pod_selector": {"match_labels": {"app": "test"}},
                "haproxy_config": {"template": "global\n    daemon"},
                "certificates": ["invalid_string"],
            }
        )

    # Test missing name in list format
    with pytest.raises(ValueError, match="Certificate missing required 'name'"):
        config_from_dict(
            {
                "pod_selector": {"match_labels": {"app": "test"}},
                "haproxy_config": {"template": "global\n    daemon"},
                "certificates": [{"template": "test"}],
            }
        )

    # Test missing template in list format
    with pytest.raises(ValueError, match="Certificate missing required 'template'"):
        config_from_dict(
            {
                "pod_selector": {"match_labels": {"app": "test"}},
                "haproxy_config": {"template": "global\n    daemon"},
                "certificates": [{"name": "test"}],
            }
        )

    # Test invalid type
    with pytest.raises(ValueError, match="certificates must be a dict or list"):
        config_from_dict(
            {
                "pod_selector": {"match_labels": {"app": "test"}},
                "haproxy_config": {"template": "global\n    daemon"},
                "certificates": "invalid_string",
            }
        )


def test_parse_resource_filter_errors():
    """Test parse_resource_filter error conditions."""
    # Test invalid filter type - this should cause an AttributeError when trying to call .get()
    with pytest.raises(AttributeError, match="'str' object has no attribute 'get'"):
        config_from_dict(
            {
                "pod_selector": {"match_labels": {"app": "test"}},
                "haproxy_config": {"template": "global\n    daemon"},
                "watch_resources": {
                    "test": {"kind": "Pod", "filter": "invalid_string"}
                },
            }
        )


def test_list_format_parsing():
    """Test parsing list format for maps, template_snippets, and certificates."""
    # Test maps list format
    config = config_from_dict(
        {
            "pod_selector": {"match_labels": {"app": "test"}},
            "haproxy_config": {"template": "global\n    daemon"},
            "maps": [
                {"path": "/test1.map", "template": "test1"},
                {"path": "/test2.map", "template": "test2"},
            ],
        }
    )

    assert len(config.maps) == 2
    assert config.maps.by_path("/test1.map") is not None
    assert config.maps.by_path("/test2.map") is not None

    # Test template_snippets dict format
    config = config_from_dict(
        {
            "pod_selector": {"match_labels": {"app": "test"}},
            "haproxy_config": {"template": "global\n    daemon"},
            "template_snippets": {
                "snippet1": "test1",
                "snippet2": "test2",
            },
        }
    )

    assert len(config.template_snippets) == 2
    assert config.template_snippets.by_name("snippet1") is not None
    assert config.template_snippets.by_name("snippet2") is not None

    # Test certificates list format
    config = config_from_dict(
        {
            "pod_selector": {"match_labels": {"app": "test"}},
            "haproxy_config": {"template": "global\n    daemon"},
            "certificates": [
                {"name": "cert1.pem", "template": "test1"},
                {"name": "cert2.pem", "template": "test2"},
            ],
        }
    )

    assert len(config.certificates) == 2
    assert config.certificates.by_name("cert1.pem") is not None
    assert config.certificates.by_name("cert2.pem") is not None

    # Test watch_resources list format
    config = config_from_dict(
        {
            "pod_selector": {"match_labels": {"app": "test"}},
            "haproxy_config": {"template": "global\n    daemon"},
            "watch_resources": [
                {"id": "pods", "kind": "Pod"},
                {"id": "services", "kind": "Service", "group": "", "version": "v1"},
            ],
        }
    )

    assert len(config.watch_resources) == 2
    assert config.watch_resources.by_id("pods") is not None
    assert config.watch_resources.by_id("services") is not None


def test_list_format_errors():
    """Test error conditions for list format parsing."""
    # Test maps list format errors
    with pytest.raises(ValueError, match="Map config must be a dict"):
        config_from_dict(
            {
                "pod_selector": {"match_labels": {"app": "test"}},
                "haproxy_config": {"template": "global\n    daemon"},
                "maps": ["invalid_string"],
            }
        )

    with pytest.raises(ValueError, match="Map missing required 'path'"):
        config_from_dict(
            {
                "pod_selector": {"match_labels": {"app": "test"}},
                "haproxy_config": {"template": "global\n    daemon"},
                "maps": [{"template": "test"}],
            }
        )

    with pytest.raises(ValueError, match="Map missing required 'template'"):
        config_from_dict(
            {
                "pod_selector": {"match_labels": {"app": "test"}},
                "haproxy_config": {"template": "global\n    daemon"},
                "maps": [{"path": "/test.map"}],
            }
        )

    with pytest.raises(ValueError, match="Map path 'relative' must be absolute"):
        config_from_dict(
            {
                "pod_selector": {"match_labels": {"app": "test"}},
                "haproxy_config": {"template": "global\n    daemon"},
                "maps": [{"path": "relative", "template": "test"}],
            }
        )

    # Test watch_resources list format errors
    with pytest.raises(ValueError, match="Watch resource must be a dict"):
        config_from_dict(
            {
                "pod_selector": {"match_labels": {"app": "test"}},
                "haproxy_config": {"template": "global\n    daemon"},
                "watch_resources": ["invalid_string"],
            }
        )

    with pytest.raises(ValueError, match="Watch resource missing required 'kind'"):
        config_from_dict(
            {
                "pod_selector": {"match_labels": {"app": "test"}},
                "haproxy_config": {"template": "global\n    daemon"},
                "watch_resources": [{"id": "test"}],
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
            "ingress-backends": "server {{ name }} {{ ip }}:{{ port }} check"
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
    snippet = config.template_snippets.by_name("ingress-backends")
    assert snippet is not None
    assert snippet.name == "ingress-backends"

    # Test that map template can include the snippet
    map_config = config.maps.by_path("/etc/haproxy/maps/backends.map")
    assert map_config is not None

    # Render the template with snippet inclusion
    rendered = map_config.template.render(
        name="web-server", ip="192.168.1.10", port="80"
    )
    assert rendered == "server web-server 192.168.1.10:80 check"


def test_template_snippet_multiple_includes():
    """Test multiple template snippets included in one template."""
    config_dict = {
        "pod_selector": {"match_labels": {"app": "test"}},
        "haproxy_config": {"template": "global\n    daemon"},
        "template_snippets": {
            "backend-header": "backend {{ backend_name }}",
            "server-entry": "    server {{ name }} {{ ip }}:{{ port }} check",
            "backend-footer": "    option httpchk GET /health",
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
    map_config = config.maps.by_path("/etc/haproxy/maps/backend.map")
    rendered = map_config.template.render(
        backend_name="web-servers", name="web-1", ip="192.168.1.10", port="80"
    )

    expected = "backend web-servers\n    server web-1 192.168.1.10:80 check\n    option httpchk GET /health"
    assert rendered == expected


def test_template_snippet_with_variables():
    """Test template snippets that contain variables."""
    config_dict = {
        "pod_selector": {"match_labels": {"app": "test"}},
        "haproxy_config": {"template": "global\n    daemon"},
        "template_snippets": {
            "server-with-weight": "server {{ name }} {{ ip }}:{{ port }} weight {{ weight | default(100) }} check"
        },
        "maps": {
            "/etc/haproxy/maps/weighted.map": {
                "template": "{% for server in servers %}{% with name=server.name, ip=server.ip, port=server.port, weight=server.weight %}{% include 'server-with-weight' %}{% endwith %}\n{% endfor %}"
            }
        },
    }

    config = config_from_dict(config_dict)

    map_config = config.maps.by_path("/etc/haproxy/maps/weighted.map")
    servers = [
        {"name": "web-1", "ip": "192.168.1.10", "port": "80", "weight": 150},
        {"name": "web-2", "ip": "192.168.1.11", "port": "80"},
    ]

    rendered = map_config.template.render(servers=servers)
    expected = "server web-1 192.168.1.10:80 weight 150 check\nserver web-2 192.168.1.11:80 weight 100 check\n"
    assert rendered == expected


def test_template_snippet_nested_includes():
    """Test template snippets that include other snippets."""
    config_dict = {
        "pod_selector": {"match_labels": {"app": "test"}},
        "haproxy_config": {"template": "global\n    daemon"},
        "template_snippets": {
            "health-check": "check inter 5s",
            "server-base": "server {{ name }} {{ ip }}:{{ port }}",
            "server-full": "{% include 'server-base' %} {% include 'health-check' %}",
        },
        "maps": {
            "/etc/haproxy/maps/servers.map": {"template": "{% include 'server-full' %}"}
        },
    }

    config = config_from_dict(config_dict)

    map_config = config.maps.by_path("/etc/haproxy/maps/servers.map")
    rendered = map_config.template.render(name="api-server", ip="10.0.1.5", port="8080")

    expected = "server api-server 10.0.1.5:8080 check inter 5s"
    assert rendered == expected


def test_template_snippet_not_found_error():
    """Test error when trying to include a non-existent snippet."""
    config_dict = {
        "pod_selector": {"match_labels": {"app": "test"}},
        "haproxy_config": {"template": "global\n    daemon"},
        "template_snippets": {"existing-snippet": "some content"},
        "maps": {
            "/etc/haproxy/maps/error.map": {
                "template": "{% include 'non-existent-snippet' %}"
            }
        },
    }

    config = config_from_dict(config_dict)

    map_config = config.maps.by_path("/etc/haproxy/maps/error.map")

    # Should raise TemplateNotFound when trying to render
    from jinja2 import TemplateNotFound

    with pytest.raises(TemplateNotFound, match="non-existent-snippet"):
        map_config.template.render()


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
    map_config = config.maps.by_path("/etc/haproxy/maps/no-snippets.map")
    rendered = map_config.template.render()
    assert rendered == "plain template without includes"


def test_template_snippet_complex_example():
    """Test a complex real-world example with multiple snippets."""
    config_dict = {
        "pod_selector": {"match_labels": {"app": "haproxy"}},
        "haproxy_config": {"template": "global\n    daemon"},
        "template_snippets": {
            "path-map-entry": "{% if resource.spec.rules %}{% for rule in resource.spec.rules %}{% for path in rule.http.paths %}{{ path.path }} {{ rule.host }}_{{ path.backend.service.name }}\n{% endfor %}{% endfor %}{% endif %}",
            "backend-config": "backend {{ backend_name }}\n    balance roundrobin\n    option httpchk GET {{ health_path | default('/health') }}",
            "server-entry": "    server {{ name }} {{ ip }}:{{ port }} check",
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
    assert config.template_snippets.by_name("path-map-entry") is not None
    assert config.template_snippets.by_name("backend-config") is not None
    assert config.template_snippets.by_name("server-entry") is not None

    # Test the complex template rendering
    map_config = config.maps.by_path("/etc/haproxy/maps/path-exact.map")
    assert map_config is not None

    # Mock ingress data
    mock_resources = {
        "ingresses": {
            ("default", "example-ingress"): {
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

    rendered = map_config.template.render(resources=mock_resources)
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
        "template_snippets": {"greeting": "Hello {{ name }}"},
        "maps": {"/test.map": {"template": "{% include 'greeting' %}"}},
    }

    config_1 = config_from_dict(config_dict_1)
    map_config_1 = config_1.maps.by_path("/test.map")
    rendered_1 = map_config_1.template.render(name="World")
    assert rendered_1 == "Hello World"

    # Second configuration with updated snippet
    config_dict_2 = {
        "pod_selector": {"match_labels": {"app": "test"}},
        "haproxy_config": {"template": "global\n    daemon"},
        "template_snippets": {"greeting": "Hi {{ name }}!"},
        "maps": {"/test.map": {"template": "{% include 'greeting' %}"}},
    }

    config_2 = config_from_dict(config_dict_2)
    map_config_2 = config_2.maps.by_path("/test.map")
    rendered_2 = map_config_2.template.render(name="World")
    assert rendered_2 == "Hi World!"


def test_template_context_helper_methods():
    """Test the new helper methods for resource access."""
    # Create a template context with some test resources
    test_resources = {
        "ingresses": {
            ("default", "ing1"): {"metadata": {"name": "ing1"}},
            ("default", "ing2"): {"metadata": {"name": "ing2"}},
        },
        "services": {
            ("default", "svc1"): {"metadata": {"name": "svc1"}},
        },
        "empty_type": {},
    }

    context = TemplateContext(resources=test_resources)

    # Test get_resources
    assert len(context.get_resources("ingresses")) == 2
    assert len(context.get_resources("services")) == 1
    assert len(context.get_resources("empty_type")) == 0
    assert len(context.get_resources("nonexistent")) == 0

    # Test iterate_resources
    ingress_items = list(context.iterate_resources("ingresses"))
    assert len(ingress_items) == 2
    assert ingress_items[0][0] == ("default", "ing1")
    assert ingress_items[1][0] == ("default", "ing2")

    # Test count_resources
    assert context.count_resources("ingresses") == 2
    assert context.count_resources("services") == 1
    assert context.count_resources("empty_type") == 0
    assert context.count_resources("nonexistent") == 0

    # Test has_resources
    assert context.has_resources("ingresses") is True
    assert context.has_resources("services") is True
    assert context.has_resources("empty_type") is False
    assert context.has_resources("nonexistent") is False


def test_template_environment_caching():
    """Test that template environment caching works correctly."""
    from haproxy_template_ic.config import (
        _get_cached_environment,
        _get_snippets_hash,
        _make_jinja_template,
        TemplateSnippetCollection,
        TemplateSnippet,
    )

    # Test that same snippets hash returns cached environment
    hash1 = _get_snippets_hash(None)
    hash2 = _get_snippets_hash(None)
    assert hash1 == hash2

    env1 = _get_cached_environment(hash1)
    env2 = _get_cached_environment(hash2)
    assert env1 is env2  # Should be the same cached instance

    # Test with different snippet collections
    snippets1 = TemplateSnippetCollection(
        [
            TemplateSnippet(
                name="test1",
                source="hello",
                template=_make_jinja_template("hello", context_name="test1"),
            )
        ]
    )
    snippets2 = TemplateSnippetCollection(
        [
            TemplateSnippet(
                name="test2",
                source="world",
                template=_make_jinja_template("world", context_name="test2"),
            )
        ]
    )

    hash_a = _get_snippets_hash(snippets1)
    hash_b = _get_snippets_hash(snippets2)
    assert hash_a != hash_b  # Different snippets should have different hashes


def test_b64decode_filter():
    """Test the custom base64 decode filter."""
    import base64
    from haproxy_template_ic.config import _make_jinja_template

    # Test valid base64 string
    test_string = "Hello, World!"
    encoded = base64.b64encode(test_string.encode("utf-8")).decode("ascii")

    template_str = f"{{{{ '{encoded}' | b64decode }}}}"
    template = _make_jinja_template(template_str, context_name="test_b64decode")
    result = template.render()

    assert result == test_string

    # Test another string with special characters
    test_string2 = "Special chars: ñáéíóú!@#$%^&*()"
    encoded2 = base64.b64encode(test_string2.encode("utf-8")).decode("ascii")

    template_str2 = f"{{{{ '{encoded2}' | b64decode }}}}"
    template2 = _make_jinja_template(template_str2, context_name="test_b64decode2")
    result2 = template2.render()

    assert result2 == test_string2

    # Test invalid base64 should raise error
    template_str_invalid = "{{ 'invalid_base64!' | b64decode }}"
    template_invalid = _make_jinja_template(
        template_str_invalid, context_name="test_b64decode_invalid"
    )

    with pytest.raises(ValueError, match="Failed to decode base64 value"):
        template_invalid.render()


def test_type_safety_enhancements():
    """Test the new type safety enhancements for config parsing."""

    # Test watch resources with non-string kind (dict format)
    with pytest.raises(ValueError, match="kind must be a string"):
        config_from_dict(
            {
                "pod_selector": {"match_labels": {"app": "test"}},
                "haproxy_config": {"template": "global\n    daemon"},
                "watch_resources": {
                    "test": {"kind": 123}  # Non-string kind
                },
            }
        )

    # Test watch resources with non-string kind (list format)
    with pytest.raises(ValueError, match="kind must be a string"):
        config_from_dict(
            {
                "pod_selector": {"match_labels": {"app": "test"}},
                "haproxy_config": {"template": "global\n    daemon"},
                "watch_resources": [
                    {"kind": ["Pod"]}  # Non-string kind
                ],
            }
        )

    # Test maps with non-string template (dict format)
    with pytest.raises(ValueError, match="template must be a string"):
        config_from_dict(
            {
                "pod_selector": {"match_labels": {"app": "test"}},
                "haproxy_config": {"template": "global\n    daemon"},
                "maps": {
                    "/test.map": {"template": 123}  # Non-string template
                },
            }
        )

    # Test maps with non-string path (list format)
    with pytest.raises(ValueError, match="path must be a string"):
        config_from_dict(
            {
                "pod_selector": {"match_labels": {"app": "test"}},
                "haproxy_config": {"template": "global\n    daemon"},
                "maps": [
                    {"path": 123, "template": "test"}  # Non-string path
                ],
            }
        )

    # Test maps with non-string template (list format)
    with pytest.raises(ValueError, match="template must be a string"):
        config_from_dict(
            {
                "pod_selector": {"match_labels": {"app": "test"}},
                "haproxy_config": {"template": "global\n    daemon"},
                "maps": [
                    {"path": "/test.map", "template": ["test"]}  # Non-string template
                ],
            }
        )

    # Test certificates with non-string template (dict format)
    with pytest.raises(ValueError, match="template must be a string"):
        config_from_dict(
            {
                "pod_selector": {"match_labels": {"app": "test"}},
                "haproxy_config": {"template": "global\n    daemon"},
                "certificates": {
                    "test.crt": {"template": {"key": "value"}}  # Non-string template
                },
            }
        )

    # Test certificates with non-string name (list format)
    with pytest.raises(ValueError, match="name must be a string"):
        config_from_dict(
            {
                "pod_selector": {"match_labels": {"app": "test"}},
                "haproxy_config": {"template": "global\n    daemon"},
                "certificates": [
                    {"name": 123, "template": "test"}  # Non-string name
                ],
            }
        )

    # Test certificates with non-string template (list format)
    with pytest.raises(ValueError, match="template must be a string"):
        config_from_dict(
            {
                "pod_selector": {"match_labels": {"app": "test"}},
                "haproxy_config": {"template": "global\n    daemon"},
                "certificates": [
                    {"name": "test.crt", "template": None}  # Non-string template
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

    # Create mock ingress resources
    mock_resources = {
        "ingresses": {
            ("default", "test-ingress"): {
                "metadata": {"name": "test-ingress", "namespace": "default"},
                "spec": {
                    "rules": [
                        {"host": "example.com"},
                        {"host": "www.example.com"},
                        {"host": "api.example.com"},
                    ]
                },
            },
            ("production", "prod-ingress"): {
                "metadata": {"name": "prod-ingress", "namespace": "production"},
                "spec": {"rules": [{"host": "prod.example.com"}]},
            },
        }
    }

    # Create template context
    context = TemplateContext(resources=mock_resources, config=config)

    # Render the host map
    host_map_config = config.maps.by_path("/etc/haproxy/maps/host.map")
    template_vars = {
        "resources": context.resources,
        "config": context.config,
    }

    rendered_content = host_map_config.template.render(**template_vars)

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

    # Create mock TLS secret
    mock_resources = {
        "secrets": {
            ("default", "example-tls"): {
                "metadata": {
                    "name": "example-tls",
                    "namespace": "default",
                    "labels": {"haproxy-template-ic/tls": "true"},
                },
                "type": "kubernetes.io/tls",
                "data": {"tls.crt": cert_b64, "tls.key": key_b64},
            }
        }
    }

    # Create template context
    context = TemplateContext(resources=mock_resources, config=config)

    # Render the certificate template
    cert_config = config.certificates.by_name("/etc/haproxy/certs/tls.pem")
    template_vars = {
        "resources": context.resources,
        "config": context.config,
    }

    rendered_content = cert_config.template.render(**template_vars)

    # Verify the certificate and key were decoded correctly
    assert cert_data in rendered_content
    assert key_data in rendered_content
    assert "# Certificate for example-tls in default" in rendered_content
