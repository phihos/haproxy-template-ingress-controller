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
        ({"pod_selector": "app=myapp"}, "app=myapp", 0, 0),
        # Config with empty optional fields
        (
            {"pod_selector": "app=myapp", "watch_resources": {}, "maps": {}},
            "app=myapp",
            0,
            0,
        ),
        # Config with watch_resources
        (
            {
                "pod_selector": "app=myapp",
                "watch_resources": {
                    "ingresses": {
                        "group": "networking.k8s.io",
                        "version": "v1",
                        "kind": "Ingress",
                    },
                    "services": {"group": "", "version": "v1", "kind": "Service"},
                },
            },
            "app=myapp",
            2,
            0,
        ),
        # Config with maps
        (
            {
                "pod_selector": "app=myapp",
                "maps": {
                    "/etc/haproxy/maps/path-prefix.map": {
                        "path": "/etc/haproxy/maps/path-prefix.map",
                        "template": "server {{ name }} {{ ip }}:{{ port }}",
                    },
                    "/etc/haproxy/maps/backend-servers.map": {
                        "path": "/etc/haproxy/maps/backend-servers.map",
                        "template": "server {{ name }} {{ ip }}:{{ port }}",
                    },
                },
            },
            "app=myapp",
            0,
            2,
        ),
        # Config with all fields
        (
            {
                "pod_selector": "app=myapp",
                "watch_resources": {
                    "ingresses": {"group": "networking.k8s.io", "kind": "Ingress"}
                },
                "maps": {
                    "/etc/haproxy/maps/path-prefix.map": {
                        "path": "/etc/haproxy/maps/path-prefix.map",
                        "template": "server {{ name }} {{ ip }}:{{ port }}",
                    }
                },
            },
            "app=myapp",
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
    assert config.pod_selector == expected_pod_selector
    assert len(config.watch_resources) == expected_watch_resources_count
    assert len(config.maps) == expected_maps_count


@pytest.mark.parametrize(
    "config_dict,expected_watch_resource",
    [
        (
            {
                "pod_selector": "app=myapp",
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
                "pod_selector": "app=myapp",
                "watch_resources": {
                    "services": {"group": "", "version": "v1", "kind": "Service"}
                },
            },
            {"name": "services", "group": "", "version": "v1", "kind": "Service"},
        ),
        (
            {
                "pod_selector": "app=myapp",
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

    watch_resource = config.watch_resources[expected_watch_resource["name"]]
    assert isinstance(watch_resource, WatchResourceConfig)
    assert watch_resource.group == expected_watch_resource["group"]
    assert watch_resource.version == expected_watch_resource["version"]
    assert watch_resource.kind == expected_watch_resource["kind"]


@pytest.mark.parametrize(
    "config_dict,expected_map",
    [
        (
            {
                "pod_selector": "app=myapp",
                "maps": {
                    "/etc/haproxy/maps/path-prefix.map": {
                        "path": "/etc/haproxy/maps/path-prefix.map",
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
                "pod_selector": "app=myapp",
                "maps": {
                    "/etc/haproxy/maps/backend-servers.map": {
                        "path": "/etc/haproxy/maps/backend-servers.map",
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
                "pod_selector": "app=myapp",
                "maps": {
                    "/var/log/app.log": {
                        "path": "/var/log/app.log",
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

    map_config = config.maps[expected_map["name"]]
    assert isinstance(map_config, MapConfig)
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
        {"pod_selector": "app=myapp", "extra_field": "should_raise_exception"},
        {"pod_selector": "app=myapp", "unknown_field": {"nested": "data"}},
        {
            "pod_selector": "app=myapp",
            "watch_resources": {},
            "maps": {},
            "extra_field": "should_raise_exception",
        },
        # Invalid relative paths in maps
        {
            "pod_selector": "app=myapp",
            "maps": {
                "relative/path.conf": {
                    "path": "/etc/app/config.conf",
                    "template": "config",
                }
            },
        },
        {
            "pod_selector": "app=myapp",
            "maps": {
                "config.conf": {"path": "/etc/app/config.conf", "template": "config"}
            },
        },
        {
            "pod_selector": "app=myapp",
            "maps": {
                "./config.conf": {"path": "/etc/app/config.conf", "template": "config"}
            },
        },
        # Invalid Jinja2 templates
        {
            "pod_selector": "app=myapp",
            "maps": {
                "/etc/haproxy/maps/test.map": {
                    "path": "/etc/haproxy/maps/test.map",
                    "template": "server {{ name }",
                }
            },
        },
        {
            "pod_selector": "app=myapp",
            "maps": {
                "/etc/haproxy/maps/test.map": {
                    "path": "/etc/haproxy/maps/test.map",
                    "template": "server {{ name }",
                }
            },
        },
        {
            "pod_selector": "app=myapp",
            "maps": {
                "/etc/haproxy/maps/test.map": {
                    "path": "/etc/haproxy/maps/test.map",
                    "template": "server {% if name %}",
                }
            },
        },
        # Missing mandatory kind field in WatchResourceConfig
        {
            "pod_selector": "app=myapp",
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
    map_config = MapConfig(path="/test/path", template=Template("test {{ name }}"))
    rendered_map = RenderedMap(
        path="/etc/haproxy/maps/test.map", content="test content", map_config=map_config
    )

    assert rendered_map.path == "/etc/haproxy/maps/test.map"
    assert rendered_map.content == "test content"
    assert rendered_map.map_config == map_config


def test_rendered_map_is_frozen():
    """Test that RenderedMap is immutable."""
    map_config = MapConfig(path="/test/path", template=Template("test"))
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

    assert context.rendered_maps == {}


def test_haproxy_config_context_with_custom_data():
    """Test HAProxyConfigContext with custom rendered maps."""
    map_config = MapConfig(path="/test", template=Template("test"))
    rendered_map = RenderedMap(path="/test", content="content", map_config=map_config)
    rendered_maps = {"/test": rendered_map}

    context = HAProxyConfigContext(rendered_maps=rendered_maps)

    assert context.rendered_maps == rendered_maps


def test_haproxy_config_context_mutable():
    """Test that HAProxyConfigContext is mutable (not frozen)."""
    context = HAProxyConfigContext()
    map_config = MapConfig(path="/test", template=Template("test"))
    rendered_map = RenderedMap(path="/test", content="content", map_config=map_config)

    # Should be able to modify rendered_maps
    context.rendered_maps["/test"] = rendered_map
    assert "/test" in context.rendered_maps
