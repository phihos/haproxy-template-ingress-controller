"""
Unit test configuration with global network request prevention.

This module provides pytest configuration specifically for unit tests,
including an autouse fixture that prevents any network requests from
being made during unit test execution.
"""

import pytest
from contextlib import contextmanager, asynccontextmanager
from typing import Dict, Any, Optional
from unittest.mock import Mock, AsyncMock
from pydantic import SecretStr

from haproxy_template_ic.credentials import DataplaneAuth


@pytest.fixture(autouse=True)
def no_network_requests(monkeypatch):
    """
    Remove network request capabilities for all unit tests.

    This autouse fixture automatically runs for every unit test and removes
    the ability to make HTTP requests, ensuring true unit test isolation.

    Following pytest documentation pattern:
    https://docs.pytest.org/en/7.1.x/how-to/monkeypatch.html#global-patch-example-preventing-requests-from-remote-operations

    Any attempt to make network requests will result in AttributeError,
    forcing tests to properly mock their dependencies.
    """
    # Remove httpx.AsyncClient HTTP methods to prevent async HTTP requests
    # These are used directly in DataplaneClient for text/plain requests
    monkeypatch.delattr("httpx.AsyncClient.post")
    monkeypatch.delattr("httpx.AsyncClient.get")
    monkeypatch.delattr("httpx.AsyncClient.put")
    monkeypatch.delattr("httpx.AsyncClient.delete")
    monkeypatch.delattr("httpx.AsyncClient.patch")
    monkeypatch.delattr("httpx.AsyncClient.head")
    monkeypatch.delattr("httpx.AsyncClient.options")

    # Remove httpx.Client HTTP methods to prevent sync HTTP requests
    monkeypatch.delattr("httpx.Client.post")
    monkeypatch.delattr("httpx.Client.get")
    monkeypatch.delattr("httpx.Client.put")
    monkeypatch.delattr("httpx.Client.delete")
    monkeypatch.delattr("httpx.Client.patch")
    monkeypatch.delattr("httpx.Client.head")
    monkeypatch.delattr("httpx.Client.options")


@pytest.fixture(scope="module")
def test_auth():
    """Create test dataplane auth with sample credentials."""
    return DataplaneAuth(
        username="admin",
        password=SecretStr("secret123"),
    )


@pytest.fixture
def mock_metrics_base():
    """Create a base mock metrics collector that can be customized."""
    # Create mock context manager for timing
    mock_timer = Mock()
    mock_timer.__enter__ = Mock(return_value=mock_timer)
    mock_timer.__exit__ = Mock(return_value=None)

    # Create mock metrics instance
    mock_metrics_instance = Mock()
    # Add generic record method that all metrics instances have
    mock_metrics_instance.record_dataplane_api_request = Mock()

    # Return a function that allows customizing timer methods
    def create_metrics_with_timer(timer_method_name):
        setattr(mock_metrics_instance, timer_method_name, Mock(return_value=mock_timer))
        return mock_metrics_instance

    # For backward compatibility, add common timer method
    mock_metrics_instance.time_dataplane_api_operation = Mock(return_value=mock_timer)

    return mock_metrics_instance


@pytest.fixture
def mock_config_metrics():
    """Create mock metrics collector for config operations."""
    # Create mock context manager for timing
    mock_timer = Mock()
    mock_timer.__enter__ = Mock(return_value=mock_timer)
    mock_timer.__exit__ = Mock(return_value=None)

    # Create mock metrics instance with config-specific timer
    mock_metrics_instance = Mock()
    mock_metrics_instance.time_config_reload.return_value = mock_timer
    mock_metrics_instance.record_config_reload = Mock()

    return mock_metrics_instance


# Kubernetes resource factory functions
def create_k8s_pod_resource(
    name: str = "test-pod",
    namespace: str = "default",
    phase: str = "Running",
    additional_metadata: Optional[Dict[str, Any]] = None,
    additional_status: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Create a Kubernetes Pod resource with common test patterns."""
    metadata = {"name": name}
    if namespace:
        metadata["namespace"] = namespace
    if additional_metadata:
        metadata.update(additional_metadata)

    resource = {
        "apiVersion": "v1",
        "kind": "Pod",
        "metadata": metadata,
    }

    if phase or additional_status:
        status = {}
        if phase:
            status["phase"] = phase
        if additional_status:
            status.update(additional_status)
        resource["status"] = status

    return resource


def create_k8s_service_resource(
    name: str = "test-service",
    namespace: str = "default",
    port: int = 80,
    additional_metadata: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Create a Kubernetes Service resource with common test patterns."""
    metadata = {"name": name}
    if namespace:
        metadata["namespace"] = namespace
    if additional_metadata:
        metadata.update(additional_metadata)

    return {
        "apiVersion": "v1",
        "kind": "Service",
        "metadata": metadata,
        "spec": {
            "ports": [{"port": port}],
            "selector": {"app": name},
        },
    }


def create_k8s_configmap_resource(
    name: str = "test-configmap",
    namespace: str = "default",
    data: Optional[Dict[str, str]] = None,
    additional_metadata: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Create a Kubernetes ConfigMap resource with common test patterns."""
    metadata = {"name": name}
    if namespace:
        metadata["namespace"] = namespace
    if additional_metadata:
        metadata.update(additional_metadata)

    return {
        "apiVersion": "v1",
        "kind": "ConfigMap",
        "metadata": metadata,
        "data": data or {"config": "test-data"},
    }


# Assertion helper functions
def assert_storage_api_call_signature(
    call_args, expected_body_type=None, allow_name=False
):
    """
    Validate storage API call signature follows expected pattern.

    Args:
        call_args: Mock call_args object from the API call
        expected_body_type: Optional type to validate the body against
        allow_name: Whether 'name' parameter is allowed (for replace operations)
    """
    # Should always have client and body
    assert "client" in call_args.kwargs, "API call should include 'client' parameter"
    assert "body" in call_args.kwargs, "API call should include 'body' parameter"

    # Should not have these parameters (they're part of the body)
    if not allow_name:
        assert "name" not in call_args.kwargs, (
            "API call should not include 'name' parameter"
        )
    assert "description" not in call_args.kwargs, (
        "API call should not include 'description' parameter"
    )

    # Validate body type if specified
    if expected_body_type:
        assert isinstance(call_args.kwargs["body"], expected_body_type), (
            f"API call body should be {expected_body_type.__name__}"
        )


def assert_mock_called_with_args(mock_obj, *expected_args, **expected_kwargs):
    """
    Assert mock was called once with specific args and kwargs.

    Provides clearer error messages than the built-in assert_called_once_with.
    """
    mock_obj.assert_called_once()
    actual_args, actual_kwargs = mock_obj.call_args

    # Check positional arguments
    assert actual_args == expected_args, (
        f"Expected args {expected_args}, got {actual_args}"
    )

    # Check keyword arguments
    for key, expected_value in expected_kwargs.items():
        assert key in actual_kwargs, f"Missing expected kwarg '{key}'"
        assert actual_kwargs[key] == expected_value, (
            f"Expected {key}={expected_value}, got {actual_kwargs[key]}"
        )


def assert_has_required_kwargs(call_args, *required_keys):
    """Assert that call_args.kwargs contains all required keys."""
    for key in required_keys:
        assert key in call_args.kwargs, f"Missing required kwarg '{key}'"


def assert_missing_kwargs(call_args, *forbidden_keys):
    """Assert that call_args.kwargs does not contain forbidden keys."""
    for key in forbidden_keys:
        assert key not in call_args.kwargs, f"Unexpected kwarg '{key}' found"


def assert_type_instance(obj, expected_type, obj_name="object"):
    """Assert object is instance of expected type with clear error message."""
    assert isinstance(obj, expected_type), (
        f"{obj_name} should be {expected_type.__name__}, got {type(obj).__name__}"
    )


# Exception testing utilities
@contextmanager
def assert_raises_value_error(match_pattern=None):
    """
    Context manager for asserting ValueError with optional message matching.

    Args:
        match_pattern: Optional regex pattern to match against the error message
    """
    import pytest

    if match_pattern:
        with pytest.raises(ValueError, match=match_pattern):
            yield
    else:
        with pytest.raises(ValueError):
            yield


@contextmanager
def assert_raises_template_error(error_type=None, match_pattern=None):
    """
    Context manager for asserting template-related errors.

    Args:
        error_type: Template error type (TemplateSyntaxError, TemplateNotFound, etc.)
        match_pattern: Optional regex pattern to match against the error message
    """
    import pytest
    from jinja2 import TemplateSyntaxError

    if error_type is None:
        error_type = TemplateSyntaxError

    if match_pattern:
        with pytest.raises(error_type, match=match_pattern):
            yield
    else:
        with pytest.raises(error_type):
            yield


# AsyncMock factory patterns for dataplane tests
def create_async_mock_with_return_value(return_value):
    """Create an AsyncMock that returns a specific value."""
    mock = AsyncMock()
    mock.return_value = return_value
    return mock


def create_async_mock_coroutine(return_value=None):
    """Create an AsyncMock that returns an awaitable coroutine."""
    return AsyncMock(return_value=return_value)()


def create_dataplane_client_mock():
    """Create a mock dataplane client with common async methods."""
    client = Mock()
    # Common async methods that return awaitables
    client.get = AsyncMock()
    client.post = AsyncMock()
    client.put = AsyncMock()
    client.delete = AsyncMock()
    client.patch = AsyncMock()
    return client


def create_transaction_operations_mock():
    """Create a mock transaction operations object."""
    mock = Mock()
    mock.start = AsyncMock()
    mock.commit = AsyncMock()
    mock.rollback = AsyncMock()
    return mock


def create_validation_operations_mock():
    """Create a mock validation operations object."""
    mock = Mock()
    mock.validate_configuration = AsyncMock()
    mock.deploy_configuration = AsyncMock()
    mock.get_version = AsyncMock()
    mock.get_current_configuration = AsyncMock()
    return mock


def create_storage_operations_mock():
    """Create a mock storage operations object."""
    mock = Mock()
    mock.sync_maps = AsyncMock()
    mock.sync_certificates = AsyncMock()
    mock.get_storage_info = AsyncMock()
    return mock


def create_runtime_operations_mock():
    """Create a mock runtime operations object."""
    mock = Mock()
    mock.bulk_map_updates = AsyncMock()
    mock.update_server_state = AsyncMock()
    return mock


def create_config_operations_mock():
    """Create a mock config operations object."""
    mock = Mock()
    mock.apply_config_change = AsyncMock()
    mock.fetch_structured_configuration = AsyncMock()
    return mock


# K8s resource mock factory patterns


def create_watch_config_mock(index_by=None):
    """Create a mock watch config object."""
    watch_config = Mock()
    watch_config.index_by = index_by or []
    return watch_config


def create_memo_with_watch_config(resource_name, watch_config):
    """Create a memo mock with watched resources configuration."""
    memo = Mock()
    memo.configuration = Mock()
    memo.configuration.config = Mock()
    memo.configuration.config.watched_resources = {resource_name: watch_config}
    memo.operations = Mock()
    memo.operations.debouncer = Mock()

    async def mock_trigger(trigger_type):
        pass

    memo.operations.debouncer.trigger = mock_trigger
    return memo


def create_config_mock_with_watched_resources(watched_resources=None):
    """Create a config mock with watched resources for index sync tests."""
    from haproxy_template_ic.models.config import Config, OperatorConfig

    config = Mock(spec=Config)
    config.operator = Mock(spec=OperatorConfig)
    config.operator.index_initialization_timeout = 5
    config.watched_resources = watched_resources or {
        "services": Mock(),
        "ingresses": Mock(),
        "secrets": Mock(),
    }
    return config


def create_configmap_mock(data=None):
    """Create a mock ConfigMap object."""
    mock_configmap = Mock()
    mock_configmap.data = data or {}
    return mock_configmap


# Timing and performance mock utilities
def create_mock_timer(expected_duration=None):
    """Create a mock timer that tracks timing operations."""
    import time

    timer = Mock()
    timer.start_time = None
    timer.end_time = None
    timer.duration = expected_duration or 0.1

    def start():
        timer.start_time = time.time()

    def stop():
        timer.end_time = time.time()
        return timer.duration

    timer.start = start
    timer.stop = stop
    timer.elapsed = lambda: timer.duration if timer.start_time else 0

    return timer


@contextmanager
def mock_timing_operations(expected_duration=0.1):
    """Context manager for mocking time-based operations."""
    import time
    from unittest.mock import patch

    original_time = time.time
    start_time = original_time()

    def mock_time():
        return start_time + expected_duration

    with patch("time.time", side_effect=mock_time):
        yield expected_duration


@contextmanager
def mock_async_sleep(total_duration=0.1):
    """Context manager for mocking asyncio.sleep calls."""
    from unittest.mock import patch

    sleep_calls = []

    async def mock_sleep(duration):
        sleep_calls.append(duration)
        # Don't actually sleep, just record the call

    with patch("asyncio.sleep", side_effect=mock_sleep) as mock:
        mock.sleep_calls = sleep_calls
        yield mock


def create_performance_metrics_mock():
    """Create a mock object for performance metrics collection."""
    metrics = Mock()
    metrics.start_time = 0.0
    metrics.end_time = 0.1
    metrics.duration = 0.1
    metrics.operations_count = 0
    metrics.throughput = 10.0

    def record_operation():
        metrics.operations_count += 1

    metrics.record_operation = record_operation
    metrics.get_throughput = lambda: metrics.throughput
    metrics.get_average_duration = lambda: metrics.duration

    return metrics


# Standard mock object factories for common patterns
def create_click_context_mock(params=None):
    """Create a mock Click context object."""
    from unittest.mock import MagicMock
    import click

    ctx = MagicMock(spec=click.Context)
    ctx.params = params or {}
    ctx.resilient_parsing = False
    ctx.allow_extra_args = False
    ctx.allow_interspersed_args = True
    return ctx


def create_runner_result_mock(exit_code=0, output="", exception=None):
    """Create a mock CliRunner result object."""
    from unittest.mock import MagicMock
    from click.testing import Result

    result = MagicMock(spec=Result)
    result.exit_code = exit_code
    result.output = output
    result.exception = exception
    result.exc_info = None if exception is None else (type(exception), exception, None)
    return result


def create_yaml_config_mock(data=None):
    """Create a mock YAML configuration object."""
    import yaml

    if data is None:
        data = {
            "pod_selector": {"match_labels": {"app": "test"}},
            "haproxy_config": {"template": "global\n    daemon"},
        }

    mock_config = Mock()
    mock_config.data = {"config": yaml.dump(data)}
    return mock_config


def create_pydantic_model_mock(model_class, **fields):
    """Create a mock Pydantic model with specified fields."""
    from unittest.mock import MagicMock

    mock_model = MagicMock(spec=model_class)
    for field_name, field_value in fields.items():
        setattr(mock_model, field_name, field_value)
    return mock_model


def create_application_state_mock(config_dict=None):
    """Create a mock ApplicationState with nested configuration."""
    from unittest.mock import MagicMock
    from haproxy_template_ic.models.state import ApplicationState

    # Default configuration structure
    if config_dict is None:
        config_dict = {
            "logging": {"verbose": 1, "structured": False},
            "tracing": {
                "enabled": True,
                "service_name": "test-service",
                "service_version": "1.0.0",
                "jaeger_endpoint": "jaeger:14268",
                "sample_rate": 0.5,
                "console_export": True,
            },
        }

    state = MagicMock(spec=ApplicationState)

    # Create nested mock structure for configuration
    config_mock = MagicMock()
    for key, value in config_dict.items():
        if isinstance(value, dict):
            section_mock = MagicMock()
            for subkey, subvalue in value.items():
                setattr(section_mock, subkey, subvalue)
            setattr(config_mock, key, section_mock)
        else:
            setattr(config_mock, key, value)

    configuration_mock = MagicMock()
    configuration_mock.config = config_mock
    state.configuration = configuration_mock
    state.config = config_mock  # Backwards compatibility

    return state


def create_kopf_index_mock(resources=None):
    """Create a mock Kopf index with test resources."""
    from unittest.mock import MagicMock

    if resources is None:
        resources = {
            ("default", "test-resource"): [
                {
                    "metadata": {"name": "test-resource", "namespace": "default"},
                    "spec": {"selector": {"app": "test"}},
                }
            ]
        }

    mock_index = MagicMock()
    mock_index.__iter__.return_value = iter(resources.keys())

    def mock_getitem(key):
        mock_store = MagicMock()
        mock_store.__iter__.return_value = iter(resources.get(key, []))
        return mock_store

    mock_index.__getitem__.side_effect = mock_getitem
    return mock_index


def create_logger_with_handlers_mock():
    """Create a mock logger with common handler methods."""
    from unittest.mock import MagicMock
    import logging

    logger = MagicMock(spec=logging.Logger)
    logger.debug = MagicMock()
    logger.info = MagicMock()
    logger.warning = MagicMock()
    logger.error = MagicMock()
    logger.critical = MagicMock()
    logger.setLevel = MagicMock()
    logger.addHandler = MagicMock()
    logger.removeHandler = MagicMock()
    logger.level = logging.INFO
    return logger


def create_metrics_collector_mock():
    """Create a comprehensive mock metrics collector."""
    from unittest.mock import MagicMock
    from haproxy_template_ic.metrics import MetricsCollector

    collector = MagicMock(spec=MetricsCollector)
    collector.start_time = 1234567890.0
    collector._server_started = False
    collector.set_app_info = MagicMock()
    collector.record_watched_resources = MagicMock()
    collector.record_template_render = MagicMock()
    collector.record_haproxy_instances = MagicMock()
    collector.record_error = MagicMock()
    collector.record_config_reload = MagicMock()
    collector.start_metrics_server = MagicMock()
    collector.export_metrics = MagicMock()
    return collector


def create_haproxy_response_mock(status="success", data=None, reload_id=None):
    """Create a mock HAProxy dataplane API response."""
    from unittest.mock import MagicMock

    response = MagicMock()
    response.status = status
    response.data = data or {}
    response.reload_id = reload_id or "reload-123"
    response.json = MagicMock(return_value=response.data)
    response.status_code = 200 if status == "success" else 400
    return response


def create_template_engine_mock(templates=None):
    """Create a mock Jinja2 template engine."""
    from unittest.mock import MagicMock
    from jinja2 import Environment, Template

    if templates is None:
        templates = {
            "test.j2": "Hello {{ name }}!",
            "config.j2": "global\n    daemon\n{{ content }}",
        }

    env = MagicMock(spec=Environment)

    def mock_get_template(name):
        template = MagicMock(spec=Template)
        template.name = name
        template.render = MagicMock(
            return_value=templates.get(name, f"Template {name}")
        )
        return template

    env.get_template = mock_get_template
    env.from_string = MagicMock(return_value=mock_get_template("from_string"))
    return env


def create_k8s_client_mock(resources=None):
    """Create a mock Kubernetes client."""
    from unittest.mock import MagicMock

    if resources is None:
        resources = {
            "pods": [{"metadata": {"name": "test-pod"}}],
            "services": [{"metadata": {"name": "test-service"}}],
        }

    client = MagicMock()

    # Common k8s client methods
    for resource_type, resource_list in resources.items():
        resource_api = MagicMock()
        resource_api.list.return_value = MagicMock(items=resource_list)
        setattr(client, resource_type, resource_api)

    return client


def create_filesystem_mock(file_structure=None):
    """Create a mock filesystem structure."""
    from unittest.mock import MagicMock

    if file_structure is None:
        file_structure = {
            "/etc/haproxy/haproxy.cfg": "global\n    daemon\n",
            "/tmp/test.map": "key1 value1\nkey2 value2\n",
            "/var/log/haproxy.log": "log entry 1\nlog entry 2\n",
        }

    fs = MagicMock()

    def mock_open(filename, mode="r"):
        content = file_structure.get(filename, "")
        file_mock = MagicMock()
        file_mock.read.return_value = content
        file_mock.write = MagicMock()
        file_mock.close = MagicMock()
        file_mock.__enter__ = MagicMock(return_value=file_mock)
        file_mock.__exit__ = MagicMock(return_value=False)
        return file_mock

    fs.open = mock_open
    fs.exists = MagicMock(side_effect=lambda path: path in file_structure)
    fs.isfile = MagicMock(side_effect=lambda path: path in file_structure)
    fs.listdir = MagicMock(return_value=list(file_structure.keys()))

    return fs


# Context manager utilities for monkeypatch patterns
@contextmanager
def mock_module_attributes(module, **overrides):
    """Context manager for temporarily mocking module attributes."""
    from unittest.mock import patch

    patches = []
    for attr_name, mock_value in overrides.items():
        full_path = f"{module.__name__}.{attr_name}"
        patcher = patch(full_path, mock_value)
        patches.append(patcher)

    try:
        mocks = [p.start() for p in patches]
        yield dict(zip(overrides.keys(), mocks))
    finally:
        for p in patches:
            p.stop()


@contextmanager
def mock_environment_variables(**env_vars):
    """Context manager for temporarily setting environment variables."""
    import os

    original_values = {}

    # Store original values
    for key in env_vars:
        original_values[key] = os.environ.get(key)

    try:
        # Set new values
        for key, value in env_vars.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value
        yield
    finally:
        # Restore original values
        for key, original_value in original_values.items():
            if original_value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = original_value


@contextmanager
def mock_file_operations(files=None):
    """Context manager for mocking file operations."""
    from unittest.mock import patch, mock_open

    if files is None:
        files = {}

    def mock_open_func(filename, mode="r", *args, **kwargs):
        if filename in files:
            return mock_open(read_data=files[filename])()
        # For files not in mock structure, create empty mock
        return mock_open(read_data="")()

    def mock_exists(path):
        return path in files

    with (
        patch("builtins.open", side_effect=mock_open_func),
        patch("os.path.exists", side_effect=mock_exists),
        patch("os.path.isfile", side_effect=mock_exists),
    ):
        yield


@contextmanager
def mock_network_calls(responses=None):
    """Context manager for mocking network calls."""
    from unittest.mock import patch, MagicMock

    if responses is None:
        responses = {}

    def mock_request(method, url, *args, **kwargs):
        response_data = responses.get(url, {"status_code": 200, "json": {}})
        response = MagicMock()
        response.status_code = response_data.get("status_code", 200)
        response.json.return_value = response_data.get("json", {})
        response.text = response_data.get("text", "")
        return response

    with (
        patch("httpx.request", side_effect=mock_request),
        patch("httpx.get", side_effect=mock_request),
        patch("httpx.post", side_effect=mock_request),
        patch("httpx.put", side_effect=mock_request),
        patch("httpx.delete", side_effect=mock_request),
    ):
        yield


@contextmanager
def mock_yaml_operations(yaml_data=None):
    """Context manager for mocking YAML operations."""
    from unittest.mock import patch
    import yaml

    if yaml_data is None:
        yaml_data = {"default": "config"}

    def mock_safe_load(stream):
        if isinstance(stream, str):
            return yaml_data.get(stream, yaml_data.get("default", {}))
        return yaml_data.get("default", {})

    def mock_dump(data, *args, **kwargs):
        return f"# YAML dump of {type(data).__name__}\nkey: value"

    with (
        patch.object(yaml, "safe_load", side_effect=mock_safe_load),
        patch.object(yaml, "dump", side_effect=mock_dump),
    ):
        yield


@contextmanager
def mock_time_operations(fixed_time=1234567890.0, sleep_duration=0.1):
    """Context manager for mocking time-based operations."""
    from unittest.mock import patch

    call_count = 0

    def mock_time():
        nonlocal call_count
        call_count += 1
        return fixed_time + (call_count * 0.001)  # Slight progression

    async def mock_sleep(duration):
        pass  # Don't actually sleep

    def mock_sync_sleep(duration):
        pass  # Don't actually sleep

    with (
        patch("time.time", side_effect=mock_time),
        patch("asyncio.sleep", side_effect=mock_sleep),
        patch("time.sleep", side_effect=mock_sync_sleep),
    ):
        yield


@contextmanager
def mock_logging_operations(logger_name="test"):
    """Context manager for mocking logging operations."""
    from unittest.mock import patch
    import logging

    mock_logger = create_logger_with_handlers_mock()

    with (
        patch("logging.getLogger", return_value=mock_logger),
        patch.object(logging, "basicConfig"),
        patch.object(logging, "info"),
        patch.object(logging, "warning"),
        patch.object(logging, "error"),
    ):
        yield mock_logger


@contextmanager
def mock_kubernetes_operations(resources=None):
    """Context manager for mocking Kubernetes operations."""
    from unittest.mock import patch

    if resources is None:
        resources = {"pods": [], "services": [], "configmaps": []}

    mock_client = create_k8s_client_mock(resources)

    with (
        patch("kr8s.asyncio.objects.Pod") as mock_pod,
        patch("kr8s.asyncio.objects.Service") as mock_service,
        patch("kr8s.asyncio.objects.ConfigMap") as mock_configmap,
    ):
        mock_pod.list.return_value = resources.get("pods", [])
        mock_service.list.return_value = resources.get("services", [])
        mock_configmap.list.return_value = resources.get("configmaps", [])

        yield {
            "client": mock_client,
            "pod": mock_pod,
            "service": mock_service,
            "configmap": mock_configmap,
        }


# Parametrized test data generators
def generate_k8s_name_test_cases():
    """Generate test cases for Kubernetes name validation."""
    return [
        # Valid names
        ("valid-name", True, None),
        ("valid123", True, None),
        ("v", True, None),
        ("a1b2c3", True, None),
        ("my-app-config", True, None),
        ("haproxy-template-ic-config", True, None),
        ("a" * 253, True, None),  # Maximum length
        # Invalid names
        ("", False, "Invalid K8s name format"),
        ("a" * 254, False, "Invalid K8s name format"),  # Too long
        ("Invalid", False, "Invalid K8s name format"),  # Uppercase
        ("-invalid", False, "Invalid K8s name format"),  # Starts with hyphen
        ("invalid-", False, "Invalid K8s name format"),  # Ends with hyphen
        ("invalid_name", False, "Invalid K8s name format"),  # Underscore
        ("café", False, "Invalid K8s name format"),  # Unicode
    ]


def generate_config_validation_test_cases():
    """Generate test cases for configuration validation."""
    return [
        # Valid configurations
        (
            {
                "pod_selector": {"match_labels": {"app": "myapp"}},
                "haproxy_config": {"template": "global\n    daemon"},
            },
            True,
            None,
        ),
        (
            {
                "pod_selector": {"match_labels": {"app": "test", "version": "v1"}},
                "haproxy_config": {
                    "template": "global\n    daemon\ndefaults\n    mode http"
                },
                "watched_resources": {
                    "ingresses": {
                        "api_version": "networking.k8s.io/v1",
                        "kind": "Ingress",
                    }
                },
            },
            True,
            None,
        ),
        # Invalid configurations
        (
            {
                "haproxy_config": {"template": "global\n    daemon"}
                # Missing pod_selector
            },
            False,
            "pod_selector",
        ),
        (
            {
                "pod_selector": {"match_labels": {"app": "myapp"}},
                # Missing haproxy_config
            },
            False,
            "haproxy_config",
        ),
        (
            {
                "pod_selector": {},  # Empty pod_selector
                "haproxy_config": {"template": "global\n    daemon"},
            },
            False,
            "match_labels",
        ),
    ]


def generate_credential_test_cases():
    """Generate test cases for credential validation."""
    return [
        # Valid cases
        (
            {
                "dataplane_username": "admin",
                "dataplane_password": "pass1",
                "validation_username": "admin",
                "validation_password": "pass2",
            },
            True,
            None,
        ),
        # Base64 bytes
        (
            {
                "dataplane_username": b"YWRtaW4=",
                "dataplane_password": b"cGFzczE=",
                "validation_username": b"YWRtaW4=",
                "validation_password": b"cGFzczI=",
            },
            True,
            None,
        ),
        # Whitespace trimming
        (
            {
                "dataplane_username": " admin ",
                "dataplane_password": "pass1 ",
                "validation_username": "admin",
                "validation_password": " pass2 ",
            },
            True,
            None,
        ),
        # Error cases
        ({"dataplane_username": "admin"}, False, "Missing/invalid"),
        (
            {
                "dataplane_username": "admin",
                "dataplane_password": "",
                "validation_username": "admin",
                "validation_password": "pass",
            },
            False,
            "Missing/invalid",
        ),
        (
            {
                "dataplane_username": "admin",
                "dataplane_password": 123,
                "validation_username": "admin",
                "validation_password": "pass",
            },
            False,
            "Missing/invalid",
        ),
    ]


def generate_endpoint_test_cases():
    """Generate test cases for endpoint configuration."""
    return [
        # Valid endpoints
        ("http://localhost:5555", "http://localhost:5555/v3"),
        ("http://localhost:5555/v3", "http://localhost:5555/v3"),
        ("https://api.example.com:8080", "https://api.example.com:8080/v3"),
        ("https://api.example.com:8080/v3", "https://api.example.com:8080/v3"),
        # Edge cases
        ("http://localhost", "http://localhost/v3"),
        ("https://api.example.com", "https://api.example.com/v3"),
    ]


def generate_haproxy_config_samples(variations=5):
    """Generate sample HAProxy configurations for testing."""
    samples = []

    for i in range(variations):
        config = f"""global
    daemon
    stats socket /var/run/haproxy.sock mode 600 level admin
    stats timeout 30s
    user haproxy
    group haproxy

defaults
    mode http
    timeout connect 5000ms
    timeout client 50000ms
    timeout server 50000ms
    option httplog
    log global

frontend web_frontend_{i}
    bind *:80{i}
    default_backend web_servers_{i}

backend web_servers_{i}
    balance roundrobin
    server web{i} 192.168.1.{i + 1}:80{i} check
"""
        samples.append(config.strip())

    return samples


def generate_k8s_resource_samples(kind, count=3):
    """Generate sample Kubernetes resources for testing."""
    resources = []

    for i in range(count):
        if kind == "Pod":
            resource = {
                "apiVersion": "v1",
                "kind": "Pod",
                "metadata": {
                    "name": f"test-pod-{i}",
                    "namespace": "default",
                    "labels": {"app": "test", "instance": str(i)},
                },
                "spec": {
                    "containers": [
                        {
                            "name": "app",
                            "image": f"nginx:{i}.0",
                            "ports": [{"containerPort": 80 + i}],
                        }
                    ]
                },
                "status": {"phase": "Running", "podIP": f"10.0.0.{i + 1}"},
            }
        elif kind == "Service":
            resource = {
                "apiVersion": "v1",
                "kind": "Service",
                "metadata": {"name": f"test-service-{i}", "namespace": "default"},
                "spec": {
                    "selector": {"app": "test"},
                    "ports": [{"port": 80 + i, "targetPort": 80 + i}],
                },
            }
        elif kind == "Ingress":
            resource = {
                "apiVersion": "networking.k8s.io/v1",
                "kind": "Ingress",
                "metadata": {"name": f"test-ingress-{i}", "namespace": "default"},
                "spec": {
                    "rules": [
                        {
                            "host": f"test{i}.example.com",
                            "http": {
                                "paths": [
                                    {
                                        "path": "/",
                                        "pathType": "Prefix",
                                        "backend": {
                                            "service": {
                                                "name": f"test-service-{i}",
                                                "port": {"number": 80 + i},
                                            }
                                        },
                                    }
                                ]
                            },
                        }
                    ]
                },
            }
        else:
            raise ValueError(f"Unsupported resource kind: {kind}")

        resources.append(resource)

    return resources


def generate_template_test_data(template_types=None):
    """Generate test data for template testing."""
    if template_types is None:
        template_types = ["haproxy_config", "map", "certificate"]

    test_data = {}

    for template_type in template_types:
        if template_type == "haproxy_config":
            test_data[template_type] = {
                "template": """global
    daemon
    stats socket /var/run/haproxy.sock mode 600 level admin

defaults
    mode http
    timeout connect 5000ms

{% for frontend in frontends %}
frontend {{ frontend.name }}
    bind *:{{ frontend.port }}
    default_backend {{ frontend.backend }}
{% endfor %}

{% for backend in backends %}
backend {{ backend.name }}
    balance {{ backend.balance }}
    {% for server in backend.servers %}
    server {{ server.name }} {{ server.address }}:{{ server.port }} check
    {% endfor %}
{% endfor %}""",
                "context": {
                    "frontends": [
                        {"name": "web", "port": 80, "backend": "web_servers"}
                    ],
                    "backends": [
                        {
                            "name": "web_servers",
                            "balance": "roundrobin",
                            "servers": [
                                {
                                    "name": "web1",
                                    "address": "192.168.1.1",
                                    "port": 8080,
                                },
                                {
                                    "name": "web2",
                                    "address": "192.168.1.2",
                                    "port": 8080,
                                },
                            ],
                        }
                    ],
                },
            }
        elif template_type == "map":
            test_data[template_type] = {
                "template": """{% for entry in entries %}{{ entry.key }} {{ entry.value }}
{% endfor %}""",
                "context": {
                    "entries": [
                        {"key": "/api", "value": "api_backend"},
                        {"key": "/web", "value": "web_backend"},
                        {"key": "/", "value": "default_backend"},
                    ]
                },
            }
        elif template_type == "certificate":
            test_data[template_type] = {
                "template": """-----BEGIN CERTIFICATE-----
{{ certificate_data }}
-----END CERTIFICATE-----
-----BEGIN PRIVATE KEY-----
{{ private_key_data }}
-----END PRIVATE KEY-----""",
                "context": {
                    "certificate_data": "MIIBkTCB+wIJAL...",
                    "private_key_data": "MIIEvQIBADANBg...",
                },
            }

    return test_data


def generate_error_scenarios(error_types=None):
    """Generate test scenarios for error handling."""
    if error_types is None:
        error_types = ["network", "validation", "authentication", "timeout"]

    scenarios = {}

    for error_type in error_types:
        if error_type == "network":
            scenarios[error_type] = [
                {"exception": "ConnectionError", "message": "Connection refused"},
                {"exception": "TimeoutError", "message": "Request timed out"},
                {"exception": "NetworkError", "message": "Network unreachable"},
            ]
        elif error_type == "validation":
            scenarios[error_type] = [
                {"exception": "ValidationError", "message": "Invalid configuration"},
                {"exception": "ValueError", "message": "Invalid value for field"},
                {"exception": "TypeError", "message": "Expected string, got int"},
            ]
        elif error_type == "authentication":
            scenarios[error_type] = [
                {"exception": "AuthenticationError", "message": "Invalid credentials"},
                {"exception": "PermissionError", "message": "Access denied"},
                {"exception": "UnauthorizedError", "message": "Token expired"},
            ]
        elif error_type == "timeout":
            scenarios[error_type] = [
                {"exception": "TimeoutError", "message": "Operation timed out"},
                {
                    "exception": "asyncio.TimeoutError",
                    "message": "Async operation timed out",
                },
            ]

    return scenarios


# Assertion helpers for common test verification patterns


def assert_config_field_equals(config, path, expected):
    """Assert that a nested configuration field equals expected value."""
    current = config
    path_parts = path.split(".")

    for part in path_parts[:-1]:
        if hasattr(current, part):
            current = getattr(current, part)
        elif isinstance(current, dict) and part in current:
            current = current[part]
        else:
            raise AssertionError(
                f"Path '{path}' not found in config. Failed at '{part}'"
            )

    final_part = path_parts[-1]
    if hasattr(current, final_part):
        actual = getattr(current, final_part)
    elif isinstance(current, dict) and final_part in current:
        actual = current[final_part]
    else:
        raise AssertionError(
            f"Final field '{final_part}' not found in config at path '{path}'"
        )

    assert actual == expected, f"Expected {path} to be {expected}, but got {actual}"


def assert_log_contains(caplog, level, message_pattern):
    """Assert that logs contain a message matching the pattern at the specified level."""
    import re
    import logging

    level_num = getattr(logging, level.upper()) if isinstance(level, str) else level

    matching_records = [
        record
        for record in caplog.records
        if record.levelno == level_num and re.search(message_pattern, record.message)
    ]

    if not matching_records:
        all_messages = [
            f"[{record.levelname}] {record.message}" for record in caplog.records
        ]
        raise AssertionError(
            f"No {level} log messages found matching pattern '{message_pattern}'. "
            f"All log messages: {all_messages}"
        )


def assert_yaml_structure_valid(yaml_content, schema):
    """Assert that YAML content matches expected structure."""
    import yaml

    try:
        data = yaml.safe_load(yaml_content)
    except yaml.YAMLError as e:
        raise AssertionError(f"Invalid YAML: {e}")

    def validate_structure(actual, expected, path=""):
        if isinstance(expected, dict):
            if not isinstance(actual, dict):
                raise AssertionError(f"Expected dict at {path}, got {type(actual)}")

            for key, expected_value in expected.items():
                current_path = f"{path}.{key}" if path else key
                if key not in actual:
                    raise AssertionError(
                        f"Missing required key '{key}' at {current_path}"
                    )
                validate_structure(actual[key], expected_value, current_path)

        elif isinstance(expected, list):
            if not isinstance(actual, list):
                raise AssertionError(f"Expected list at {path}, got {type(actual)}")

            if len(expected) > 0:
                # Validate that all items match the first schema item
                for i, item in enumerate(actual):
                    validate_structure(item, expected[0], f"{path}[{i}]")

        elif isinstance(expected, type):
            if not isinstance(actual, expected):
                raise AssertionError(
                    f"Expected {expected} at {path}, got {type(actual)}"
                )

    validate_structure(data, schema)


def assert_haproxy_config_valid(config_content):
    """Assert that HAProxy configuration content is structurally valid."""
    lines = config_content.strip().split("\n")

    # Basic structure validation
    sections = []
    current_section = None

    for line_num, line in enumerate(lines, 1):
        line = line.strip()
        if not line or line.startswith("#"):
            continue

        # Check for section headers
        if line in ["global", "defaults"] or line.startswith(
            ("frontend ", "backend ", "listen ")
        ):
            current_section = line
            sections.append(current_section)
        elif current_section is None:
            raise AssertionError(
                f"Configuration directive '{line}' at line {line_num} not within a section"
            )

    # Ensure required sections exist
    if "global" not in [s for s in sections]:
        raise AssertionError("HAProxy configuration missing required 'global' section")


def assert_k8s_resource_valid(resource, kind=None):
    """Assert that a Kubernetes resource has valid structure."""
    required_fields = ["apiVersion", "kind", "metadata"]

    for field in required_fields:
        if field not in resource:
            raise AssertionError(f"Kubernetes resource missing required field: {field}")

    if kind and resource["kind"] != kind:
        raise AssertionError(f"Expected kind '{kind}', got '{resource['kind']}'")

    # Validate metadata
    metadata = resource["metadata"]
    if "name" not in metadata:
        raise AssertionError(
            "Kubernetes resource metadata missing required 'name' field"
        )

    # Basic name validation
    name = metadata["name"]
    if not name or not isinstance(name, str):
        raise AssertionError(f"Invalid resource name: {name}")


def assert_mock_calls_in_order(mock, expected_calls):
    """Assert that mock was called with specific arguments in specific order."""
    actual_calls = mock.call_args_list

    if len(actual_calls) != len(expected_calls):
        raise AssertionError(
            f"Expected {len(expected_calls)} calls, got {len(actual_calls)}. "
            f"Actual calls: {actual_calls}"
        )

    for i, (actual_call, expected_call) in enumerate(zip(actual_calls, expected_calls)):
        if actual_call != expected_call:
            raise AssertionError(
                f"Call {i} mismatch. Expected: {expected_call}, Actual: {actual_call}"
            )


def assert_template_rendered_correctly(template_content, context, expected_patterns):
    """Assert that template renders correctly with given context."""
    from jinja2 import Template
    import re

    try:
        template = Template(template_content)
        rendered = template.render(context)
    except Exception as e:
        raise AssertionError(f"Template rendering failed: {e}")

    for pattern in expected_patterns:
        if not re.search(pattern, rendered):
            raise AssertionError(
                f"Expected pattern '{pattern}' not found in rendered template. "
                f"Rendered content: {rendered}"
            )


def assert_metrics_recorded(metrics_mock, metric_type, expected_count=None):
    """Assert that specific metrics were recorded."""
    method_name = f"record_{metric_type}"

    if not hasattr(metrics_mock, method_name):
        raise AssertionError(f"Metrics mock does not have method '{method_name}'")

    method = getattr(metrics_mock, method_name)

    if not method.called:
        raise AssertionError(f"Metric '{metric_type}' was not recorded")

    if expected_count is not None:
        actual_count = method.call_count
        if actual_count != expected_count:
            raise AssertionError(
                f"Expected {expected_count} calls to record_{metric_type}, got {actual_count}"
            )


@contextmanager
def assert_raises_admission_error(match_pattern=None):
    """
    Context manager for asserting kopf.AdmissionError with message matching.

    Args:
        match_pattern: Optional regex pattern to match against the error message
    """
    import pytest
    import kopf

    if match_pattern:
        with pytest.raises(kopf.AdmissionError, match=match_pattern):
            yield
    else:
        with pytest.raises(kopf.AdmissionError):
            yield


@contextmanager
def assert_raises_system_exit(match_pattern=None):
    """
    Context manager for asserting SystemExit with optional message matching.

    Args:
        match_pattern: Optional regex pattern to match against the error message
    """
    import pytest

    if match_pattern:
        with pytest.raises(SystemExit, match=match_pattern):
            yield
    else:
        with pytest.raises(SystemExit):
            yield


def assert_exception_raised(func, exception_type, match_pattern=None, *args, **kwargs):
    """
    Helper function to assert that a function raises a specific exception.

    Args:
        func: Function to call
        exception_type: Expected exception type
        match_pattern: Optional regex pattern to match against error message
        *args, **kwargs: Arguments to pass to the function
    """
    import pytest

    if match_pattern:
        with pytest.raises(exception_type, match=match_pattern):
            func(*args, **kwargs)
    else:
        with pytest.raises(exception_type):
            func(*args, **kwargs)


# Tracing mock fixtures for OpenTelemetry patterns
@pytest.fixture(scope="module")
def mock_span():
    """Create a mock OpenTelemetry span."""
    span = Mock()
    span.set_attribute = Mock()
    span.record_exception = Mock()
    span.add_event = Mock()
    span.set_status = Mock()
    return span


@pytest.fixture(scope="module")
def mock_tracer(mock_span):
    """Create a mock OpenTelemetry tracer."""
    tracer = Mock()
    # Create proper context manager for span
    span_context = Mock()
    span_context.__enter__ = Mock(return_value=mock_span)
    span_context.__exit__ = Mock(return_value=None)
    tracer.start_as_current_span = Mock(return_value=span_context)
    return tracer


@pytest.fixture(scope="module")
def mock_tracer_provider(mock_tracer):
    """Create a mock OpenTelemetry tracer provider."""
    provider = Mock()
    provider.get_tracer = Mock(return_value=mock_tracer)
    provider.add_span_processor = Mock()
    provider.shutdown = Mock()
    return provider


@pytest.fixture(scope="module")
def mock_tracing_config():
    """Create a mock tracing configuration."""
    from haproxy_template_ic.tracing import TracingConfig

    return TracingConfig(
        enabled=True,
        service_name="test-service",
        service_version="1.0.0",
        jaeger_endpoint="localhost:14268",
        sample_rate=0.5,
        console_export=True,
    )


@pytest.fixture
def mock_tracing_manager(mock_tracer_provider, mock_tracer):
    """Create a mock tracing manager."""
    manager = Mock()
    manager.tracer_provider = mock_tracer_provider
    manager.tracer = mock_tracer
    manager.initialize = Mock()
    manager.shutdown = Mock()
    manager._instrumented = False
    return manager


# API mock factory functions
def create_successful_api_response(data=None):
    """Create a successful API response mock."""
    response = Mock()
    response.status_code = 200
    response.json = Mock(return_value=data or {"status": "success"})
    response.text = "success"
    return response


def create_api_error_response(status_code=500, message="Internal Server Error"):
    """Create an API error response mock."""
    response = Mock()
    response.status_code = status_code
    response.json = Mock(return_value={"error": message})
    response.text = message
    return response


def create_validation_response(valid=True, errors=None):
    """Create a validation API response mock."""
    response_data = {"valid": valid, "errors": errors or []}
    return create_successful_api_response(response_data)


def create_deployment_response(reload_id="reload-123", status="success"):
    """Create a deployment response mock with reload_id."""
    response = Mock()
    response.reload_id = reload_id
    response.status = status
    return response


def create_api_info_response(
    api_version="3.0", build_date="2023-01-01", version="dataplane-2.8.0"
):
    """Create a dataplane API info response mock."""
    response = Mock()
    response.api_version = api_version
    response.build_date = build_date
    response.version = version
    return response


def create_haproxy_process_info_response(
    version="3.1.0", release_date="2023-12-01", uptime="5d 3h 42m"
):
    """Create a HAProxy process info response mock."""
    response = Mock()
    response.version = version
    response.release_date = release_date
    response.uptime = uptime
    return response


def create_configuration_response(config_data=None):
    """Create a configuration response mock with data."""
    if config_data is not None:
        # Create a mock with data attribute
        response = Mock()
        response.data = config_data
        return response
    else:
        # Create a mock without any attributes - use a simple object
        class EmptyResponse:
            pass

        return EmptyResponse()


def create_template_config_mock(template_snippets=None, **kwargs):
    """Create a mock config object for templating tests."""
    config = Mock()
    config.template_snippets = template_snippets or {}

    # Set any additional attributes from kwargs
    for key, value in kwargs.items():
        setattr(config, key, value)

    return config


def create_template_snippet_mock(template_content="template content"):
    """Create a mock template snippet object."""
    snippet = Mock()
    snippet.template = template_content
    return snippet


def create_fallback_snippet_mock(fallback_content="fallback content"):
    """Create a mock template snippet with fallback behavior."""
    snippet = Mock()
    # Remove template attribute to trigger fallback
    if hasattr(snippet, "template"):
        delattr(snippet, "template")
    snippet.__str__ = Mock(return_value=fallback_content)
    return snippet


def create_logger_mock():
    """Create a standardized logger mock for operator tests."""
    from unittest.mock import MagicMock

    logger = MagicMock()
    logger.info = MagicMock()
    logger.warning = MagicMock()
    logger.error = MagicMock()
    logger.debug = MagicMock()
    return logger


# Performance test utilities
def simulate_work(duration=0.01):
    """Simulate work for performance testing."""
    import time

    time.sleep(duration)


def measure_operation_time(func, *args, **kwargs):
    """Measure operation execution time."""
    import time

    start_time = time.time()
    result = func(*args, **kwargs)
    end_time = time.time()
    return result, end_time - start_time


# Configuration mock utilities
@pytest.fixture
def mock_app_config():
    """Create a mock application configuration."""
    config = Mock()
    config.pod_selector = Mock()
    config.pod_selector.match_labels = {"app": "haproxy"}
    config.template_rendering = Mock()
    config.template_rendering.min_render_interval = 1
    config.template_rendering.max_render_interval = 30
    config.validation = Mock()
    config.validation.dataplane_host = "localhost"
    config.validation.dataplane_port = 5555
    config.watched_resources_ignore_fields = []
    config.watched_resources = {}
    return config


@pytest.fixture
def mock_dataplane_config():
    """Create a mock dataplane configuration."""
    config = Mock()
    config.host = "localhost"
    config.port = 5555
    config.timeout = 30
    config.retry_count = 3
    return config


# Complex patch context managers
@contextmanager
def patch_tracing_manager(mock_manager=None):
    """
    Context manager for patching tracing system components.

    Args:
        mock_manager: Optional mock manager to use (default: creates one)
    """
    from unittest.mock import patch

    if mock_manager is None:
        mock_manager = Mock()
        mock_manager.tracer = Mock()
        mock_manager.initialize = Mock()
        mock_manager.shutdown = Mock()

    tracer_to_return = mock_manager.tracer if mock_manager else None
    patches = {
        "initialize_tracing": Mock(),
        "get_tracing_manager": Mock(return_value=mock_manager),
        "get_tracer": Mock(return_value=tracer_to_return),
        "shutdown_tracing": Mock(),
    }

    with patch.multiple("haproxy_template_ic.tracing", **patches):
        yield mock_manager


@contextmanager
def patch_logging_system():
    """Context manager for patching logging system components."""
    from unittest.mock import patch

    mock_logger = Mock()
    mock_logger.info = Mock()
    mock_logger.warning = Mock()
    mock_logger.error = Mock()
    mock_logger.debug = Mock()

    patches = {
        "setup_structured_logging": Mock(),
        "get_logger": Mock(return_value=mock_logger),
    }

    with patch.multiple("haproxy_template_ic.core.logging", **patches):
        yield mock_logger


@contextmanager
def patch_dataplane_apis(mock_client=None, mock_metrics=None):
    """
    Context manager for patching dataplane API components.

    Args:
        mock_client: Optional mock client to use
        mock_metrics: Optional mock metrics collector to use
    """
    from unittest.mock import patch, AsyncMock

    if mock_client is None:
        mock_client = Mock()

    if mock_metrics is None:
        mock_metrics = Mock()
        mock_metrics.time_dataplane_api_operation = Mock(
            return_value=Mock(__enter__=Mock(), __exit__=Mock())
        )
        mock_metrics.record_dataplane_api_request = Mock()

    patches = {
        "get_metrics_collector": Mock(return_value=mock_metrics),
        "check_dataplane_response": Mock(
            side_effect=lambda response, op, endpoint: response
        ),
        "record_span_event": Mock(),
    }

    # Create module-specific patches to avoid conflicts
    # These API functions have .asyncio attributes that need to be mocked
    post_ha_proxy_config_mock = Mock()
    post_ha_proxy_config_mock.asyncio = AsyncMock()

    get_ha_proxy_config_mock = Mock()
    get_ha_proxy_config_mock.asyncio = AsyncMock()

    get_info_mock = Mock()
    get_info_mock.asyncio = AsyncMock()

    get_haproxy_process_info_mock = Mock()
    get_haproxy_process_info_mock.asyncio = AsyncMock()

    validation_patches = {
        **patches,
        "post_ha_proxy_configuration": post_ha_proxy_config_mock,
        "get_ha_proxy_configuration": get_ha_proxy_config_mock,
        "get_info": get_info_mock,
        "get_haproxy_process_info": get_haproxy_process_info_mock,
    }

    utils_patches = {
        **patches,
        "get_configuration_version": AsyncMock(),
    }

    transaction_patches = {
        **patches,
        "start_transaction": AsyncMock(),
        "commit_transaction": AsyncMock(),
        "delete_transaction": AsyncMock(),
    }

    with (
        patch.multiple(
            "haproxy_template_ic.dataplane.validation_api", **validation_patches
        ),
        patch.multiple("haproxy_template_ic.dataplane.utils", **utils_patches),
        patch.multiple(
            "haproxy_template_ic.dataplane.transaction_api", **transaction_patches
        ),
    ):
        # Return all API mocks combined for backward compatibility
        all_api_mocks = {
            **validation_patches,
            **utils_patches,
            **transaction_patches,
            # Include individual mock objects for direct access
            "post_ha_proxy_configuration": post_ha_proxy_config_mock,
            "get_ha_proxy_configuration": get_ha_proxy_config_mock,
            "get_info": get_info_mock,
            "get_haproxy_process_info": get_haproxy_process_info_mock,
        }
        yield {
            "client": mock_client,
            "metrics": mock_metrics,
            "api_mocks": all_api_mocks,
        }


@contextmanager
def patch_debouncer_environment():
    """Context manager for patching debouncer test environment."""
    from unittest.mock import patch, AsyncMock

    mock_logger = Mock()

    patches = {
        "logger": mock_logger,
    }

    with (
        patch.multiple("haproxy_template_ic.operator.debouncer", **patches),
        patch("asyncio.wait_for", new=AsyncMock()),
    ):
        yield mock_logger


@contextmanager
def patch_debouncer_logger():
    """Context manager for patching only the debouncer logger."""
    from unittest.mock import patch

    mock_logger = Mock()
    mock_logger.info = Mock()
    mock_logger.warning = Mock()
    mock_logger.error = Mock()
    mock_logger.debug = Mock()

    with patch("haproxy_template_ic.operator.debouncer.logger", mock_logger):
        yield mock_logger


# =============================================================================
# Operator-specific Mock Factories
# =============================================================================


def create_debouncer_mock_factory(
    min_interval=0.1, max_interval=1.0, config=None, **kwargs
):
    """Create a comprehensive TemplateRenderDebouncer mock with all required dependencies."""
    from unittest.mock import MagicMock, AsyncMock
    from haproxy_template_ic.operator.debouncer import TemplateRenderDebouncer
    from haproxy_template_ic.operator.index_sync import IndexSynchronizationTracker
    from haproxy_template_ic.dataplane.synchronizer import ConfigSynchronizer
    from haproxy_template_ic.metrics import MetricsCollector
    from haproxy_template_ic.models.config import Config
    from haproxy_template_ic.models.context import HAProxyConfigContext
    from haproxy_template_ic.templating import TemplateRenderer
    from kopf._core.engines.indexing import OperatorIndices

    # Create config mock with required attributes
    if config is None:
        config = MagicMock(spec=Config)
        config.watched_resources_ignore_fields = []
        config.watched_resources = {}

    # Create context mock with required attributes
    context_mock = MagicMock(spec=HAProxyConfigContext)
    context_mock.rendered_content = []

    # Create index tracker mock that immediately resolves
    index_tracker_mock = MagicMock(spec=IndexSynchronizationTracker)
    index_tracker_mock.wait_for_indices_ready = AsyncMock(return_value=None)
    index_tracker_mock.is_initialization_complete.return_value = True

    # Default dependencies
    defaults = {
        "config": config,
        "haproxy_config_context": context_mock,
        "template_renderer": MagicMock(spec=TemplateRenderer),
        "config_synchronizer": MagicMock(spec=ConfigSynchronizer),
        "kopf_indices": MagicMock(spec=OperatorIndices),
        "metrics": MagicMock(spec=MetricsCollector),
        "index_tracker": index_tracker_mock,
    }

    # Override defaults with any provided kwargs
    defaults.update(kwargs)

    return TemplateRenderDebouncer(
        min_interval=min_interval, max_interval=max_interval, **defaults
    )


def create_pod_index_mock(pod_data=None):
    """Create a mock for haproxy pod index operations."""
    from unittest.mock import MagicMock

    if pod_data is None:
        pod_data = {
            ("default", "haproxy-1"): create_k8s_pod_resource(
                name="haproxy-1",
                namespace="default",
                phase="Running",
                additional_status={"podIP": "10.0.0.1"},
            ),
            ("default", "haproxy-2"): create_k8s_pod_resource(
                name="haproxy-2",
                namespace="default",
                phase="Running",
                additional_status={"podIP": "10.0.0.2"},
            ),
        }

    index_mock = MagicMock()
    index_mock.items.return_value = pod_data.items()
    index_mock.get.side_effect = lambda key, default=None: pod_data.get(key, default)
    index_mock.__len__ = MagicMock(return_value=len(pod_data))
    index_mock.__iter__ = MagicMock(return_value=iter(pod_data.keys()))
    index_mock.__contains__ = MagicMock(side_effect=lambda key: key in pod_data)

    return index_mock


def create_index_synchronization_tracker_mock(is_ready=True):
    """Create a mock IndexSynchronizationTracker for testing."""
    from unittest.mock import MagicMock, AsyncMock
    from haproxy_template_ic.operator.index_sync import IndexSynchronizationTracker

    tracker = MagicMock(spec=IndexSynchronizationTracker)
    tracker.wait_for_indices_ready = AsyncMock(return_value=None)
    tracker.is_initialization_complete.return_value = is_ready
    tracker.track_index_creation = MagicMock()
    tracker.set_index_ready = MagicMock()
    tracker.reset = MagicMock()

    # Mock the internal state
    tracker._initialization_complete = is_ready
    tracker._ready_indices = set()
    tracker._tracked_indices = set()

    return tracker


def create_memo_mock_with_debouncer(trigger_response=None):
    """Create a memo mock with a properly configured debouncer for operator tests."""
    from unittest.mock import MagicMock, AsyncMock

    # Create debouncer mock
    debouncer_mock = MagicMock()
    if trigger_response:
        debouncer_mock.trigger = AsyncMock(side_effect=trigger_response)
    else:
        debouncer_mock.trigger = AsyncMock(return_value=None)

    # Create operations mock
    operations_mock = MagicMock()
    operations_mock.debouncer = debouncer_mock

    # Create main memo mock
    memo_mock = MagicMock()
    memo_mock.operations = operations_mock

    return memo_mock


def create_haproxy_config_context_mock(rendered_content=None, **kwargs):
    """Create a mock HAProxyConfigContext for testing."""
    from unittest.mock import MagicMock
    from haproxy_template_ic.models.context import HAProxyConfigContext

    context = MagicMock(spec=HAProxyConfigContext)

    # Set default rendered content
    if rendered_content is None:
        rendered_content = [
            ("haproxy.cfg", "global\n    daemon\ndefaults\n    mode http"),
            ("backend.map", "host1 backend1\nhost2 backend2"),
        ]

    context.rendered_content = rendered_content

    # Allow additional attributes to be set
    for key, value in kwargs.items():
        setattr(context, key, value)

    return context


@asynccontextmanager
async def managed_debouncer(*args, **kwargs):
    """Context manager that handles debouncer start/stop lifecycle for testing."""

    debouncer = create_debouncer_mock_factory(*args, **kwargs)
    await debouncer.start()
    try:
        yield debouncer
    finally:
        await debouncer.stop()


# =============================================================================
# Templating-specific Mock Factories
# =============================================================================


def create_template_snippet_factory(name=None, template=None):
    """Create a TemplateSnippet mock or real object for testing."""
    from haproxy_template_ic.models import TemplateSnippet

    if name is None:
        name = "test-snippet"
    if template is None:
        template = "Test template content for {{ name }}"

    return TemplateSnippet(name=name, template=template)


def create_jinja_environment_mock(filters=None, snippets=None):
    """Create a mock Jinja2 Environment for testing."""
    from unittest.mock import MagicMock
    from jinja2 import Environment, Template, TemplateNotFound

    env = MagicMock(spec=Environment)

    # Set up default filters
    default_filters = {"b64decode": MagicMock(), "get_path": MagicMock()}
    if filters:
        default_filters.update(filters)
    env.filters = default_filters

    # Set up template loading behavior
    def mock_from_string(template_str):
        template = MagicMock(spec=Template)
        template.render.return_value = f"Rendered: {template_str}"
        return template

    env.from_string = MagicMock(side_effect=mock_from_string)

    # Set up snippet loading if provided
    if snippets:

        def mock_get_template(template_name):
            if template_name in snippets:
                snippet = snippets[template_name]
                template = MagicMock(spec=Template)
                template.render.return_value = snippet.template
                return template
            raise TemplateNotFound(template_name)

        env.get_template = MagicMock(side_effect=mock_get_template)

    # Set up environment properties
    env.autoescape = False
    env.trim_blocks = False
    env.lstrip_blocks = False

    return env


def create_template_compiler_mock(snippets=None):
    """Create a mock TemplateCompiler for testing."""
    from unittest.mock import MagicMock
    from haproxy_template_ic.templating import TemplateCompiler
    from jinja2 import Template

    compiler = MagicMock(spec=TemplateCompiler)
    compiler.environment = create_jinja_environment_mock(snippets=snippets)

    # Mock compile_template to return a usable Template mock
    def mock_compile_template(template_str):
        template = MagicMock(spec=Template)
        template.render.return_value = f"Compiled: {template_str}"
        return template

    compiler.compile_template = MagicMock(side_effect=mock_compile_template)

    return compiler


def create_template_renderer_mock(snippets=None, cache_size=0):
    """Create a mock TemplateRenderer for testing."""
    from unittest.mock import MagicMock
    from haproxy_template_ic.templating import TemplateRenderer

    renderer = MagicMock(spec=TemplateRenderer)
    renderer._compiler = create_template_compiler_mock(snippets)
    renderer._compiled_templates = {}

    # Mock render method
    def mock_render(template_str, **context):
        return f"Rendered: {template_str} with context: {context}"

    renderer.render = MagicMock(side_effect=mock_render)

    # Mock cache properties
    renderer.cache_size = cache_size
    renderer.clear_cache = MagicMock()

    # Mock template validation
    renderer.validate_template = MagicMock(return_value=[])

    return renderer


@contextmanager
def mock_template_environment(snippets=None, filters=None):
    """Context manager for mocking Jinja2 template environment operations."""
    from unittest.mock import patch

    env_mock = create_jinja_environment_mock(filters=filters, snippets=snippets)

    with patch(
        "haproxy_template_ic.templating.get_template_environment", return_value=env_mock
    ):
        yield env_mock


@contextmanager
def mock_jinja_compilation():
    """Context manager for mocking Jinja2 template compilation."""
    from unittest.mock import patch, MagicMock
    from jinja2 import Template

    def mock_compile(template_str):
        template = MagicMock(spec=Template)
        template.render.return_value = f"Mocked render of: {template_str[:50]}"
        return template

    with patch(
        "haproxy_template_ic.templating.compile_template", side_effect=mock_compile
    ):
        yield mock_compile


# =============================================================================
# Dataplane-specific Mock Factories
# =============================================================================


def create_dataplane_auth_mock(username="admin", password="password"):
    """Create a mock DataplaneAuth for testing."""
    from unittest.mock import MagicMock
    from haproxy_template_ic.credentials import DataplaneAuth
    from pydantic import SecretStr

    auth = MagicMock(spec=DataplaneAuth)
    auth.username = username
    auth.password = SecretStr(password)

    return auth


def create_dataplane_endpoint_mock(url=None, auth=None):
    """Create a DataplaneEndpoint using real class with mocked auth for testing."""
    from haproxy_template_ic.dataplane.endpoint import DataplaneEndpoint

    if url is None:
        url = "http://localhost:5555/v3"

    if auth is None:
        auth = create_dataplane_auth_mock()

    # Use the real class to get proper URL normalization and validation
    return DataplaneEndpoint(url=url, dataplane_auth=auth)


def create_dataplane_endpoint_set_mock(validation_url=None, production_urls=None):
    """Create a DataplaneEndpointSet using real class with mocked auth for testing."""
    from haproxy_template_ic.dataplane.endpoint import DataplaneEndpointSet

    if validation_url is None:
        validation_url = "http://localhost:5555/v3"
    if production_urls is None:
        production_urls = ["http://192.168.1.1:5555/v3", "http://192.168.1.2:5555/v3"]

    validation_auth = create_dataplane_auth_mock("admin", "validation_pass")
    production_auth = create_dataplane_auth_mock("admin", "production_pass")

    validation_endpoint = create_dataplane_endpoint_mock(
        validation_url, validation_auth
    )
    production_endpoints = [
        create_dataplane_endpoint_mock(url, production_auth) for url in production_urls
    ]

    # Use the real class to get proper behavior
    return DataplaneEndpointSet(
        validation=validation_endpoint, production=production_endpoints
    )


@contextmanager
def mock_dataplane_operations():
    """Context manager for mocking dataplane API operations."""
    from unittest.mock import patch, AsyncMock

    mock_operations = {
        "validate_config": AsyncMock(return_value={"valid": True}),
        "deploy_config": AsyncMock(return_value={"success": True}),
        "get_runtime_info": AsyncMock(return_value={"version": "3.1.0"}),
        "health_check": AsyncMock(return_value={"status": "healthy"}),
    }

    with patch.multiple("haproxy_template_ic.dataplane.operations", **mock_operations):
        yield mock_operations


# =============================================================================
# Assertion Helpers for Specialized Testing
# =============================================================================


def assert_template_validates(template_str, context=None, snippets=None):
    """Assert that a template string validates and renders without errors."""
    from haproxy_template_ic.templating import TemplateRenderer

    if context is None:
        context = {}

    renderer = TemplateRenderer(snippets)
    warnings = renderer.validate_template(template_str)
    assert warnings == [], f"Template validation failed with warnings: {warnings}"

    try:
        result = renderer.render(template_str, **context)
        assert isinstance(result, str), "Template rendering should return a string"
    except Exception as e:
        pytest.fail(f"Template rendering failed: {e}")


def assert_snippet_includes_work(snippets_dict, main_template=None):
    """Assert that snippet includes work properly in a template."""
    from haproxy_template_ic.templating import TemplateRenderer

    if main_template is None:
        # Create a template that includes all snippets
        includes = [f'{{% include "{name}" %}}' for name in snippets_dict.keys()]
        main_template = "\n".join(includes)

    renderer = TemplateRenderer(snippets_dict)
    try:
        result = renderer.render(main_template)
        assert isinstance(result, str), "Snippet rendering should return a string"
        assert len(result) > 0, "Snippet rendering should produce non-empty output"
    except Exception as e:
        pytest.fail(f"Snippet includes failed: {e}")


def assert_dataplane_operation_called(mock_client, operation, *args, **kwargs):
    """Assert that a specific dataplane operation was called with expected arguments."""
    operation_method = getattr(mock_client, operation, None)
    assert operation_method is not None, (
        f"Operation '{operation}' not found on mock client"
    )

    if args or kwargs:
        operation_method.assert_called_with(*args, **kwargs)
    else:
        operation_method.assert_called()


def assert_debouncer_triggered(mock_debouncer, trigger_type=None):
    """Assert that a debouncer was properly triggered."""
    assert hasattr(mock_debouncer, "trigger"), (
        "Mock debouncer should have a trigger method"
    )
    mock_debouncer.trigger.assert_called()

    if trigger_type:
        # Check if trigger was called with the expected type
        call_args = mock_debouncer.trigger.call_args
        if call_args and call_args[0]:
            assert call_args[0][0] == trigger_type, (
                f"Expected trigger type '{trigger_type}'"
            )


# =============================================================================
# Phase 2 DRY: Extended Mock Factory Library
# =============================================================================


def create_generic_mock(spec=None, **kwargs):
    """Create a generic Mock with common attributes and behaviors."""
    mock = Mock(spec=spec)

    # Common mock attributes that appear frequently in tests
    if "return_value" in kwargs:
        mock.return_value = kwargs["return_value"]
    if "side_effect" in kwargs:
        mock.side_effect = kwargs["side_effect"]

    # Add common async support if needed
    if kwargs.get("async_support", False):
        mock.asyncio = AsyncMock()
        if "async_return_value" in kwargs:
            mock.asyncio.return_value = kwargs["async_return_value"]
        if "async_side_effect" in kwargs:
            mock.asyncio.side_effect = kwargs["async_side_effect"]

    return mock


def create_magic_mock_with_attrs(**attrs):
    """Create a MagicMock with specified attributes pre-configured."""
    mock = Mock()
    for attr_name, attr_value in attrs.items():
        setattr(mock, attr_name, attr_value)
    return mock


def create_async_mock_with_config(return_value=None, side_effect=None, **kwargs):
    """Create an AsyncMock with common configurations."""
    mock = AsyncMock()

    if return_value is not None:
        mock.return_value = return_value
    if side_effect is not None:
        mock.side_effect = side_effect

    # Add any additional configurations
    for key, value in kwargs.items():
        setattr(mock, key, value)

    return mock


def create_exception_mock(exception_class=Exception, message="Test error"):
    """Create a mock that raises an exception when called."""
    mock = Mock()
    mock.side_effect = exception_class(message)
    return mock


def create_async_exception_mock(exception_class=Exception, message="Test error"):
    """Create an async mock that raises an exception when called."""
    mock = AsyncMock()
    mock.side_effect = exception_class(message)
    return mock


def create_called_once_mock(return_value=None):
    """Create a mock configured to be called exactly once."""
    mock = Mock(return_value=return_value)
    return mock


def create_api_response_mock(data=None, status_code=200, headers=None):
    """Create a mock API response object."""
    mock = Mock()
    mock.data = data
    mock.status_code = status_code
    mock.headers = headers or {}

    # Common response attributes
    mock.json = Mock(return_value=data) if data else Mock()
    mock.text = str(data) if data else ""

    return mock


def create_context_manager_mock(return_value=None, enter_return=None):
    """Create a mock that works as a context manager."""
    mock = Mock()

    # Configure context manager methods
    mock.__enter__ = Mock(return_value=enter_return or mock)
    mock.__exit__ = Mock(return_value=None)

    if return_value is not None:
        mock.return_value = return_value

    return mock


def create_timer_context_mock():
    """Create a mock timer context manager for metrics timing."""
    mock_timer = Mock()
    mock_timer.__enter__ = Mock(return_value=mock_timer)
    mock_timer.__exit__ = Mock(return_value=None)
    return mock_timer


def create_dataplane_api_mock_set():
    """Create a complete set of mocked dataplane API functions."""
    return {
        "get_info": create_generic_mock(async_support=True, async_return_value=Mock()),
        "get_haproxy_process_info": create_generic_mock(
            async_support=True, async_return_value=Mock()
        ),
        "post_ha_proxy_configuration": create_generic_mock(
            async_support=True, async_return_value=Mock()
        ),
        "get_ha_proxy_configuration": create_generic_mock(
            async_support=True, async_return_value=Mock()
        ),
        "start_transaction": create_generic_mock(
            async_support=True, async_return_value=Mock()
        ),
        "commit_transaction": create_generic_mock(
            async_support=True, async_return_value=Mock()
        ),
        "delete_transaction": create_generic_mock(
            async_support=True, async_return_value=Mock()
        ),
    }


# =============================================================================
# Assertion Helpers for Common Test Patterns
# =============================================================================


def assert_mock_called_with_pattern(mock_obj, call_index=0, **expected_kwargs):
    """Assert that a mock was called with expected keyword arguments."""
    assert mock_obj.called, f"Mock {mock_obj} was not called"

    call_args = mock_obj.call_args_list[call_index]
    actual_kwargs = call_args.kwargs

    for key, expected_value in expected_kwargs.items():
        assert key in actual_kwargs, (
            f"Expected keyword argument '{key}' not found in call"
        )
        assert actual_kwargs[key] == expected_value, (
            f"Expected {key}={expected_value}, got {actual_kwargs[key]}"
        )


def assert_exception_message_contains(exc_info, expected_text):
    """Assert that an exception message contains expected text."""
    actual_message = str(exc_info.value)
    assert expected_text in actual_message, (
        f"Expected '{expected_text}' in exception message: {actual_message}"
    )


def assert_async_mock_awaited_once(async_mock):
    """Assert that an async mock was awaited exactly once."""
    assert async_mock.called, f"Async mock {async_mock} was not called"
    assert async_mock.call_count == 1, f"Expected 1 call, got {async_mock.call_count}"


def assert_mock_call_pattern(mock_obj, expected_calls):
    """Assert that a mock was called with a specific pattern of calls."""
    actual_calls = [call.args for call in mock_obj.call_args_list]
    assert len(actual_calls) == len(expected_calls), (
        f"Expected {len(expected_calls)} calls, got {len(actual_calls)}"
    )

    for i, (actual, expected) in enumerate(zip(actual_calls, expected_calls)):
        assert actual == expected, f"Call {i}: expected {expected}, got {actual}"


def assert_dataplane_metrics_recorded(mock_metrics, operation, status="success"):
    """Assert that dataplane API metrics were recorded for an operation."""
    mock_metrics.record_dataplane_api_request.assert_called_with(operation, status)


def assert_timing_context_used(mock_metrics, operation):
    """Assert that a timing context was used for an operation."""
    timer_method = getattr(mock_metrics, f"time_{operation}", None)
    if timer_method:
        timer_method.assert_called_once()
    else:
        # Fallback to generic timing method
        mock_metrics.time_dataplane_api_operation.assert_called_with(operation)


# =============================================================================
# Context Manager Helpers for Complex Patching
# =============================================================================


@contextmanager
def patch_multiple_async_operations(target_module, **operations):
    """Context manager to patch multiple async operations at once."""
    from unittest.mock import patch

    patches = {}
    mocks = {}

    try:
        for op_name, config in operations.items():
            if isinstance(config, dict):
                return_value = config.get("return_value")
                side_effect = config.get("side_effect")
            else:
                return_value = config
                side_effect = None

            mock = create_async_mock_with_config(
                return_value=return_value, side_effect=side_effect
            )
            patches[op_name] = patch(f"{target_module}.{op_name}", mock)
            mocks[op_name] = mock

        # Start all patches
        for patch_obj in patches.values():
            patch_obj.start()

        yield mocks

    finally:
        # Stop all patches
        for patch_obj in patches.values():
            patch_obj.stop()


@contextmanager
def patch_dataplane_api_operations(**operations):
    """Context manager specifically for patching dataplane API operations."""
    base_module = "haproxy_template_ic.dataplane"

    # Common dataplane operations with their modules
    api_modules = {
        "get_info": f"{base_module}.validation_api",
        "get_haproxy_process_info": f"{base_module}.validation_api",
        "post_ha_proxy_configuration": f"{base_module}.validation_api",
        "get_ha_proxy_configuration": f"{base_module}.validation_api",
        "start_transaction": f"{base_module}.transaction_api",
        "commit_transaction": f"{base_module}.transaction_api",
        "delete_transaction": f"{base_module}.transaction_api",
    }

    with patch_multiple_async_operations(
        base_module, **{op: operations.get(op, Mock()) for op in api_modules}
    ) as mocks:
        yield mocks


@contextmanager
def patch_metrics_and_tracing():
    """Context manager to patch common metrics and tracing operations."""
    from unittest.mock import patch

    mock_metrics = create_metrics_collector_mock()
    mock_timer = create_timer_context_mock()
    mock_metrics.time_dataplane_api_operation.return_value = mock_timer

    with (
        patch(
            "haproxy_template_ic.dataplane.validation_api.get_metrics_collector",
            return_value=mock_metrics,
        ),
        patch("haproxy_template_ic.dataplane.validation_api.record_span_event"),
        patch("haproxy_template_ic.dataplane.validation_api.set_span_error"),
    ):
        yield mock_metrics


@contextmanager
def patch_async_sleep():
    """Context manager to patch asyncio.sleep for faster test execution."""
    from unittest.mock import patch

    with patch("asyncio.sleep", new_callable=AsyncMock) as mock_sleep:
        yield mock_sleep


# =============================================================================
# Error Testing Helpers
# =============================================================================


def create_validation_error_scenarios():
    """Create common validation error test scenarios."""
    return [
        ("empty_config", "", "Configuration content cannot be empty"),
        ("invalid_syntax", "invalid haproxy config", "Configuration validation failed"),
        ("missing_global", "frontend web\n    bind *:80", "Missing global section"),
    ]


def create_api_error_scenarios():
    """Create common API error test scenarios."""
    return [
        ("network_error", "Connection failed", "Network connectivity issue"),
        ("auth_error", "Authentication failed", "Invalid credentials"),
        ("timeout_error", "Request timeout", "Operation timed out"),
        ("server_error", "Internal server error", "Server-side error"),
    ]


@contextmanager
def expect_validation_error(expected_message=None):
    """Context manager for testing validation errors."""
    from haproxy_template_ic.dataplane.types import ValidationError

    with pytest.raises(ValidationError) as exc_info:
        yield exc_info

    if expected_message:
        assert_exception_message_contains(exc_info, expected_message)


@contextmanager
def expect_dataplane_error(expected_message=None):
    """Context manager for testing dataplane API errors."""
    from haproxy_template_ic.dataplane.types import DataplaneAPIError

    with pytest.raises(DataplaneAPIError) as exc_info:
        yield exc_info

    if expected_message:
        assert_exception_message_contains(exc_info, expected_message)
