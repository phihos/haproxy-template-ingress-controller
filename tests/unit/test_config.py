import pytest

from haproxy_template_ic.config import (
    Config,
    WatchResourceConfig,
    MapConfig,
    config_from_dict,
    RenderedMap,
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
                "haproxy_config": "global\n    daemon",
            },
            {"app": "myapp"},
            0,
            0,
        ),
        # Config with empty optional fields
        (
            {
                "pod_selector": {"match_labels": {"app": "myapp"}},
                "haproxy_config": "global\n    daemon",
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
                "haproxy_config": "global\n    daemon",
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
                "haproxy_config": "global\n    daemon",
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
                "haproxy_config": "global\n    daemon",
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
                "haproxy_config": "global\n    daemon",
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
                "haproxy_config": "global\n    daemon",
                "watch_resources": {
                    "services": {"group": "", "version": "v1", "kind": "Service"}
                },
            },
            {"name": "services", "group": "", "version": "v1", "kind": "Service"},
        ),
        (
            {
                "pod_selector": {"match_labels": {"app": "myapp"}},
                "haproxy_config": "global\n    daemon",
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
                "haproxy_config": "global\n    daemon",
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
                "haproxy_config": "global\n    daemon",
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
                "haproxy_config": "global\n    daemon",
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
                name="backend-servers", template=Template("backend servers")
            ),
            TemplateSnippet(name="health-check", template=Template("health check")),
            TemplateSnippet(name="logging", template=Template("logging config")),
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
        [TemplateSnippet(name="test-snippet", template=Template("snippet"))]
    )
    certificates = CertificateCollection(
        [CertificateConfig(name="test.pem", template=Template("cert"))]
    )

    config = Config(
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
            {"pod_selector": "invalid_string", "haproxy_config": "global\n    daemon"}
        )

    with pytest.raises(ValueError, match="pod_selector must be a dict"):
        config_from_dict(
            {
                "pod_selector": ["invalid", "list"],
                "haproxy_config": "global\n    daemon",
            }
        )


def test_parse_maps_errors():
    """Test parse_maps error conditions."""
    # Test invalid map config (not dict)
    with pytest.raises(ValueError, match="Map config for '/test' must be a dict"):
        config_from_dict(
            {
                "pod_selector": {"match_labels": {"app": "test"}},
                "haproxy_config": "global\n    daemon",
                "maps": {"/test": "invalid_string"},
            }
        )

    # Test missing template
    with pytest.raises(ValueError, match="Map '/test' missing required 'template'"):
        config_from_dict(
            {
                "pod_selector": {"match_labels": {"app": "test"}},
                "haproxy_config": "global\n    daemon",
                "maps": {"/test": {}},
            }
        )

    # Test invalid maps type
    with pytest.raises(ValueError, match="maps must be a dict"):
        config_from_dict(
            {
                "pod_selector": {"match_labels": {"app": "test"}},
                "haproxy_config": "global\n    daemon",
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
                "haproxy_config": "global\n    daemon",
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
                "haproxy_config": "global\n    daemon",
                "watch_resources": {"test": {}},
            }
        )

    # Test invalid watch_resources type
    with pytest.raises(ValueError, match="watch_resources must be a dict"):
        config_from_dict(
            {
                "pod_selector": {"match_labels": {"app": "test"}},
                "haproxy_config": "global\n    daemon",
                "watch_resources": "invalid_string",
            }
        )


def test_parse_template_snippets_errors():
    """Test parse_template_snippets error conditions."""
    # Test dict format errors
    with pytest.raises(ValueError, match="Template snippet 'test' must be a dict"):
        config_from_dict(
            {
                "pod_selector": {"match_labels": {"app": "test"}},
                "haproxy_config": "global\n    daemon",
                "template_snippets": {"test": "invalid_string"},
            }
        )

    # Test missing template in dict format
    with pytest.raises(
        ValueError, match="Template snippet 'test' missing required 'template'"
    ):
        config_from_dict(
            {
                "pod_selector": {"match_labels": {"app": "test"}},
                "haproxy_config": "global\n    daemon",
                "template_snippets": {"test": {}},
            }
        )

    # Test list format errors
    with pytest.raises(ValueError, match="Template snippet must be a dict"):
        config_from_dict(
            {
                "pod_selector": {"match_labels": {"app": "test"}},
                "haproxy_config": "global\n    daemon",
                "template_snippets": ["invalid_string"],
            }
        )

    # Test missing name in list format
    with pytest.raises(ValueError, match="Template snippet missing required 'name'"):
        config_from_dict(
            {
                "pod_selector": {"match_labels": {"app": "test"}},
                "haproxy_config": "global\n    daemon",
                "template_snippets": [{"template": "test"}],
            }
        )

    # Test missing template in list format
    with pytest.raises(
        ValueError, match="Template snippet missing required 'template'"
    ):
        config_from_dict(
            {
                "pod_selector": {"match_labels": {"app": "test"}},
                "haproxy_config": "global\n    daemon",
                "template_snippets": [{"name": "test"}],
            }
        )

    # Test invalid type
    with pytest.raises(ValueError, match="template_snippets must be a dict or list"):
        config_from_dict(
            {
                "pod_selector": {"match_labels": {"app": "test"}},
                "haproxy_config": "global\n    daemon",
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
                "haproxy_config": "global\n    daemon",
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
                "haproxy_config": "global\n    daemon",
                "certificates": {"test": {}},
            }
        )

    # Test list format errors
    with pytest.raises(ValueError, match="Certificate must be a dict"):
        config_from_dict(
            {
                "pod_selector": {"match_labels": {"app": "test"}},
                "haproxy_config": "global\n    daemon",
                "certificates": ["invalid_string"],
            }
        )

    # Test missing name in list format
    with pytest.raises(ValueError, match="Certificate missing required 'name'"):
        config_from_dict(
            {
                "pod_selector": {"match_labels": {"app": "test"}},
                "haproxy_config": "global\n    daemon",
                "certificates": [{"template": "test"}],
            }
        )

    # Test missing template in list format
    with pytest.raises(ValueError, match="Certificate missing required 'template'"):
        config_from_dict(
            {
                "pod_selector": {"match_labels": {"app": "test"}},
                "haproxy_config": "global\n    daemon",
                "certificates": [{"name": "test"}],
            }
        )

    # Test invalid type
    with pytest.raises(ValueError, match="certificates must be a dict or list"):
        config_from_dict(
            {
                "pod_selector": {"match_labels": {"app": "test"}},
                "haproxy_config": "global\n    daemon",
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
                "haproxy_config": "global\n    daemon",
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
            "haproxy_config": "global\n    daemon",
            "maps": [
                {"path": "/test1.map", "template": "test1"},
                {"path": "/test2.map", "template": "test2"},
            ],
        }
    )

    assert len(config.maps) == 2
    assert config.maps.by_path("/test1.map") is not None
    assert config.maps.by_path("/test2.map") is not None

    # Test template_snippets list format
    config = config_from_dict(
        {
            "pod_selector": {"match_labels": {"app": "test"}},
            "haproxy_config": "global\n    daemon",
            "template_snippets": [
                {"name": "snippet1", "template": "test1"},
                {"name": "snippet2", "template": "test2"},
            ],
        }
    )

    assert len(config.template_snippets) == 2
    assert config.template_snippets.by_name("snippet1") is not None
    assert config.template_snippets.by_name("snippet2") is not None

    # Test certificates list format
    config = config_from_dict(
        {
            "pod_selector": {"match_labels": {"app": "test"}},
            "haproxy_config": "global\n    daemon",
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
            "haproxy_config": "global\n    daemon",
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
                "haproxy_config": "global\n    daemon",
                "maps": ["invalid_string"],
            }
        )

    with pytest.raises(ValueError, match="Map missing required 'path'"):
        config_from_dict(
            {
                "pod_selector": {"match_labels": {"app": "test"}},
                "haproxy_config": "global\n    daemon",
                "maps": [{"template": "test"}],
            }
        )

    with pytest.raises(ValueError, match="Map missing required 'template'"):
        config_from_dict(
            {
                "pod_selector": {"match_labels": {"app": "test"}},
                "haproxy_config": "global\n    daemon",
                "maps": [{"path": "/test.map"}],
            }
        )

    with pytest.raises(ValueError, match="Map path 'relative' must be absolute"):
        config_from_dict(
            {
                "pod_selector": {"match_labels": {"app": "test"}},
                "haproxy_config": "global\n    daemon",
                "maps": [{"path": "relative", "template": "test"}],
            }
        )

    # Test watch_resources list format errors
    with pytest.raises(ValueError, match="Watch resource must be a dict"):
        config_from_dict(
            {
                "pod_selector": {"match_labels": {"app": "test"}},
                "haproxy_config": "global\n    daemon",
                "watch_resources": ["invalid_string"],
            }
        )

    with pytest.raises(ValueError, match="Watch resource missing required 'kind'"):
        config_from_dict(
            {
                "pod_selector": {"match_labels": {"app": "test"}},
                "haproxy_config": "global\n    daemon",
                "watch_resources": [{"id": "test"}],
            }
        )
