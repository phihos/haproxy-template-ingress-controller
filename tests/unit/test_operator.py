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
    setup_resource_watchers,
    initialize_configuration,
)
from haproxy_template_ic.config import (
    Config,
    MapConfig,
    MapCollection,
    PodSelector,
    HAProxyConfigContext,
    RenderedMap,
    WatchResourceCollection,
    WatchResourceConfig,
)
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
async def test_handle_configmap_change_with_change():
    """Test ConfigMap change handler when change is detected."""
    memo = MagicMock()
    memo.config = Config(
        raw={
            "pod_selector": {"match_labels": {"app": "old"}},
            "haproxy_config": {"template": "global\n    daemon"},
        },
        pod_selector=PodSelector(match_labels={"app": "old"}),
        haproxy_config=Template("global\n    daemon"),
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
                raw={
                    "pod_selector": {"match_labels": {"app": "new"}},
                    "haproxy_config": {"template": "global\n    daemon"},
                },
                pod_selector=PodSelector(match_labels={"app": "new"}),
                haproxy_config=Template("global\n    daemon"),
            )

            await handle_configmap_change(
                memo, event, "test-config", "MODIFIED", logger
            )

            # Should trigger reload since config changed
            mock_trigger.assert_called_once_with(memo)


@pytest.mark.asyncio
async def test_handle_configmap_change_no_change():
    """Test ConfigMap change handler when no change is detected."""
    memo = MagicMock()
    config = Config(
        raw={
            "pod_selector": {"match_labels": {"app": "test"}},
            "haproxy_config": {"template": "global\n    daemon"},
        },
        pod_selector=PodSelector(match_labels={"app": "test"}),
        haproxy_config=Template("global\n    daemon"),
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
async def test_render_haproxy_templates_success():
    """Test successful template rendering."""
    memo = MagicMock()
    memo.config = Config(
        raw={
            "pod_selector": {"match_labels": {"app": "test"}},
            "haproxy_config": {"template": "global\n    daemon"},
        },
        pod_selector=PodSelector(match_labels={"app": "test"}),
        haproxy_config=Template("global\n    daemon"),
        watch_resources=WatchResourceCollection(
            [WatchResourceConfig(kind="Pod", id="pods")]
        ),
        maps=MapCollection(
            [
                MapConfig(
                    template=Template(
                        "{% for key, pod in resources.get('pods', {}).items() %}server {{ pod.metadata.name }} {{ pod.status.podIP }}:80{% endfor %}"
                    ),
                    path="/etc/haproxy/maps/backend.map",
                )
            ]
        ),
    )
    memo.haproxy_config_context = HAProxyConfigContext()

    # Mock the indices with test data
    mock_indices = MagicMock()
    # Create a mock Kubernetes Pod object
    mock_pod = MagicMock()
    mock_pod.metadata.name = "test-pod"
    mock_pod.status.podIP = "10.0.1.5"

    mock_indices.get.return_value = {("default", "test-pod"): mock_pod}
    memo.indices = mock_indices

    logger = MagicMock()

    await render_haproxy_templates(memo, logger=logger)

    # Check that rendered map was added
    assert len(memo.haproxy_config_context.rendered_maps) == 1
    rendered_map = memo.haproxy_config_context.rendered_maps[0]
    assert isinstance(rendered_map, RenderedMap)
    assert rendered_map.path == "/etc/haproxy/maps/backend.map"
    assert "server test-pod 10.0.1.5:80" in rendered_map.content


@pytest.mark.asyncio
async def test_render_haproxy_templates_with_ingress():
    """Test template rendering with ingress resources like in example-configmap.yaml."""
    memo = MagicMock()
    memo.config = Config(
        raw={
            "pod_selector": {"match_labels": {"app": "test"}},
            "haproxy_config": {"template": "global\n    daemon"},
        },
        pod_selector=PodSelector(match_labels={"app": "test"}),
        haproxy_config=Template("global\n    daemon"),
        watch_resources=WatchResourceCollection(
            [WatchResourceConfig(kind="Ingress", id="ingresses")]
        ),
        maps=MapCollection(
            [
                MapConfig(
                    template=Template(
                        "{% for _, ingress in resources.get('ingresses', {}).items() %}"
                        "{% for rule in (ingress.spec.get('rules', []) | selectattr('http', 'defined')) %}"
                        "{{ rule.host }}{{ rule.http.paths[0].path }} backend_name"
                        "{% endfor %}"
                        "{% endfor %}"
                    ),
                    path="/etc/haproxy/maps/path-exact.map",
                )
            ]
        ),
    )
    memo.haproxy_config_context = HAProxyConfigContext()

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

    mock_indices.get.return_value = {("default", "test-ingress"): mock_ingress}
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
async def test_kopf_index_store_resource_access():
    """Test that resources from kopf index stores have proper .spec attribute access."""
    memo = MagicMock()
    memo.config = Config(
        raw={
            "pod_selector": {"match_labels": {"app": "test"}},
            "haproxy_config": {"template": "global\n    daemon"},
        },
        pod_selector=PodSelector(match_labels={"app": "test"}),
        haproxy_config=Template("global\n    daemon"),
        watch_resources=WatchResourceCollection(
            [WatchResourceConfig(kind="Ingress", id="ingresses")]
        ),
        maps=MapCollection(
            [
                MapConfig(
                    # This template pattern was failing with the original error:
                    # "'kopf._core.engines.indexing.Store object' has no attribute 'spec'"
                    template=Template(
                        "{% for _, ingress in resources.get('ingresses', {}).items() %}"
                        "ingress={{ ingress.spec.rules|length }}"
                        "{% endfor %}"
                    ),
                    path="/etc/haproxy/maps/test.map",
                )
            ]
        ),
    )
    memo.haproxy_config_context = HAProxyConfigContext()

    # Mock kopf index store with a proper resource object
    mock_indices = MagicMock()
    mock_ingress = MagicMock()
    mock_ingress.spec = {"rules": [{"host": "test.com"}]}

    mock_indices.get.return_value = {("default", "test-ingress"): mock_ingress}
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
    from jinja2 import Template

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
@patch("haproxy_template_ic.operator.logger")
async def test_render_haproxy_templates_jinja_error(mock_logger):
    """Test template rendering with Jinja error."""
    memo = MagicMock()
    memo.config = Config(
        raw={
            "pod_selector": {"match_labels": {"app": "test"}},
            "haproxy_config": {"template": "global\n    daemon"},
        },
        pod_selector=PodSelector(match_labels={"app": "test"}),
        haproxy_config=Template("global\n    daemon"),
        watch_resources=WatchResourceCollection([]),
        maps=MapCollection(
            [
                MapConfig(
                    template=Template("server {{ undefined_variable.invalid_attr }}"),
                    path="/etc/haproxy/maps/backend.map",
                )
            ]
        ),
    )
    memo.haproxy_config_context = HAProxyConfigContext()

    # Mock the indices
    mock_indices = MagicMock()
    mock_indices.get.return_value = {}
    memo.indices = mock_indices

    await render_haproxy_templates(memo)

    # Should log error but not crash
    mock_logger.error.assert_called_once()
    assert "Failed to render template" in mock_logger.error.call_args[0][0]


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
    watch_resources = WatchResourceCollection(
        [
            WatchResourceConfig(kind="Pod", group="", version="v1", id="pods"),
            WatchResourceConfig(
                kind="Ingress", group="networking.k8s.io", version="v1", id="ingresses"
            ),
        ]
    )
    memo.config.watch_resources = watch_resources

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
    )
    memo.cli_options = cli_options

    # Call the function
    await initialize_configuration(memo)

    # Verify the calls
    mock_get_namespace.assert_called_once()
    mock_fetch_configmap.assert_called_once_with("test-config", "test-namespace")
    mock_load_config.assert_called_once_with(mock_configmap)
    assert memo.config == mock_config


@pytest.mark.skip(
    reason="Implementation changed - this test needs to be rewritten for new architecture"
)
def test_run_operator_loop_normal_shutdown():
    """Test run_operator_loop with normal shutdown."""
    pass


@pytest.mark.skip(
    reason="Implementation changed - this test needs to be rewritten for new architecture"
)
def test_run_operator_loop_with_reload():
    """Test run_operator_loop with config reload."""
    pass


# =============================================================================
# DeepDiff with Jinja Templates Tests
# =============================================================================


# TODO: These tests are for JinjaTemplateOperator which was removed
# def test_jinja_template_operator_give_up_diffing_different():
#     """Test JinjaTemplateOperator give_up_diffing method with different templates."""
#     from haproxy_template_ic.config import _make_jinja_template

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
#     from haproxy_template_ic.config import _make_jinja_template

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
#     from haproxy_template_ic.config import _make_jinja_template
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
#     from haproxy_template_ic.config import _make_jinja_template
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
#     from haproxy_template_ic.config import _make_jinja_template
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
