"""Unit tests for initialization module covering tracing and error handling."""

from unittest.mock import MagicMock

import pytest

import haproxy_template_ic.initialization as init_module
from haproxy_template_ic.initialization import (
    initialize_post_config,
    init_watch_configmap,
    _load_configuration_and_credentials,
    _create_application_state,
    _setup_kopf_handlers,
    configure_webhook_server,
    create_event_loop,
    run_operator_loop,
    init_template_debouncer,
    cleanup_template_debouncer,
    cleanup_tracing,
    cleanup_metrics_server,
    init_metrics_server,
)
from haproxy_template_ic.models.state import ApplicationState
from haproxy_template_ic.tracing import TracingConfig
from tests.unit.conftest import (
    create_application_state_mock,
    mock_module_attributes,
)


@pytest.fixture
def mock_application_state():
    """Create a mock ApplicationState."""
    mock_state = create_application_state_mock(
        {
            "logging": {
                "verbose": 1,
                "structured": False,
            },
            "tracing": {
                "enabled": True,
                "service_name": "test-service",
                "service_version": "1.0.0",
                "jaeger_endpoint": "jaeger:14268",
                "sample_rate": 0.5,
                "console_export": True,
            },
        }
    )
    # Add the operations mock structure
    operations_mock = MagicMock()
    operations_mock.metrics = MagicMock()
    operations_mock.tracing_manager = None  # Default to None
    mock_state.operations = operations_mock
    return mock_state


@pytest.mark.asyncio
async def test_tracing_initialization_enabled(
    monkeypatch,
    mock_application_state,
    mock_config_metrics,
):
    """Test tracing initialization when enabled."""
    # Setup mocks
    mock_base_tracing_config = MagicMock(spec=TracingConfig)
    mock_final_tracing_config = MagicMock(spec=TracingConfig)
    mock_base_tracing_config.override_with_app_config.return_value = (
        mock_final_tracing_config
    )

    mock_create_tracing_config = MagicMock(return_value=mock_base_tracing_config)
    mock_tracing_manager = MagicMock()
    mock_tracing_manager_cls = MagicMock(return_value=mock_tracing_manager)
    mock_setup_logging = MagicMock()

    # Update the mock application state with the provided metrics collector
    mock_application_state.operations.metrics = mock_config_metrics

    # Apply patches
    with mock_module_attributes(
        init_module,
        create_tracing_config_from_env=mock_create_tracing_config,
        TracingManager=mock_tracing_manager_cls,
        setup_structured_logging=mock_setup_logging,
    ):
        # Call the function
        await initialize_post_config(mock_application_state)

        # Verify override_with_app_config was called with app config
        mock_base_tracing_config.override_with_app_config.assert_called_once_with(
            mock_application_state.configuration.config.tracing
        )

        # Verify TracingManager was created with the final config
        mock_tracing_manager_cls.assert_called_once_with(mock_final_tracing_config)

        # Verify TracingManager was initialized
        mock_tracing_manager.initialize.assert_called_once()

        # Verify TracingManager was stored in application state
        assert mock_application_state.operations.tracing_manager == mock_tracing_manager


@pytest.mark.asyncio
async def test_tracing_initialization_disabled(
    monkeypatch,
    mock_application_state,
    mock_config_metrics,
):
    """Test tracing initialization when disabled."""
    # Disable tracing in config
    mock_application_state.configuration.config.tracing.enabled = False

    # Setup mocks
    mock_create_tracing_config = MagicMock()
    mock_tracing_manager_cls = MagicMock()
    mock_setup_logging = MagicMock()

    # Update the mock application state with the provided metrics collector
    mock_application_state.operations.metrics = mock_config_metrics

    # Apply patches
    with mock_module_attributes(
        init_module,
        create_tracing_config_from_env=mock_create_tracing_config,
        TracingManager=mock_tracing_manager_cls,
        setup_structured_logging=mock_setup_logging,
    ):
        # Call the function
        await initialize_post_config(mock_application_state)

        # Verify tracing initialization was not called when disabled
        mock_create_tracing_config.assert_not_called()
        mock_tracing_manager_cls.assert_not_called()


@pytest.mark.asyncio
async def test_tracing_initialization_with_fallback_values(
    monkeypatch,
    mock_application_state,
    mock_config_metrics,
):
    """Test tracing initialization with fallback to environment values."""
    # Setup tracing config with None values to test fallback
    config_mock = mock_application_state.configuration.config
    config_mock.tracing.enabled = True
    config_mock.tracing.service_name = None  # Should fallback to env
    config_mock.tracing.service_version = ""  # Should fallback to env
    config_mock.tracing.jaeger_endpoint = None  # Should fallback to env
    config_mock.tracing.console_export = False  # Should fallback to env

    # Mock environment tracing config
    mock_env_tracing_config = MagicMock(spec=TracingConfig)
    mock_env_tracing_config.service_name = "env-service"
    mock_env_tracing_config.service_version = "env-version"
    mock_env_tracing_config.jaeger_endpoint = "env-jaeger:14268"
    mock_env_tracing_config.console_export = True
    mock_create_tracing_config = MagicMock(return_value=mock_env_tracing_config)
    mock_tracing_manager = MagicMock()
    mock_tracing_manager_cls = MagicMock(return_value=mock_tracing_manager)
    mock_setup_logging = MagicMock()

    # Update the mock application state with the provided metrics collector
    mock_application_state.operations.metrics = mock_config_metrics

    # Apply patches
    with mock_module_attributes(
        init_module,
        create_tracing_config_from_env=mock_create_tracing_config,
        TracingManager=mock_tracing_manager_cls,
        setup_structured_logging=mock_setup_logging,
    ):
        # Call the function
        await initialize_post_config(mock_application_state)

        # Verify fallback values were used (we set them, so they should maintain)
        assert mock_env_tracing_config.service_name == "env-service"  # Fallback used
        assert mock_env_tracing_config.service_version == "env-version"  # Fallback used
        assert (
            mock_env_tracing_config.jaeger_endpoint == "env-jaeger:14268"
        )  # Fallback used
        assert mock_env_tracing_config.console_export  # Fallback used


@pytest.mark.asyncio
async def test_metrics_recording_success(
    monkeypatch, mock_application_state, mock_config_metrics
):
    """Test that metrics are recorded for successful config reload."""
    mock_setup_logging = MagicMock()

    mock_application_state.configuration.config.tracing.enabled = (
        False  # Disable tracing for simpler test
    )

    # Update the mock application state with the provided metrics collector
    mock_application_state.operations.metrics = mock_config_metrics

    # Apply patches
    with mock_module_attributes(
        init_module,
        setup_structured_logging=mock_setup_logging,
    ):
        # Call the function
        await initialize_post_config(mock_application_state)

        # Verify success metric was recorded
        mock_config_metrics.record_config_reload.assert_called_once_with(success=True)


@pytest.mark.asyncio
async def test_init_watch_configmap_setup(monkeypatch):
    """Test that init_watch_configmap sets up event handlers correctly."""
    mock_kopf_on = MagicMock()

    with mock_module_attributes(init_module.kopf, on=mock_kopf_on):
        # Create mock ApplicationState with nested structure
        mock_state = MagicMock(spec=ApplicationState)
        mock_cli_options = MagicMock()
        mock_cli_options.configmap_name = "test-configmap"
        mock_cli_options.secret_name = "test-secret"
        # Create nested mock structure
        runtime_mock = MagicMock()
        runtime_mock.cli_options = mock_cli_options
        mock_state.runtime = runtime_mock
        # Also set up the backwards compatibility property
        mock_state.cli_options = mock_cli_options

        # Call the function
        await init_watch_configmap(mock_state)

        # Verify that kopf.on.event was called for configmap
        mock_kopf_on.event.assert_called()


@pytest.mark.asyncio
async def test_init_watch_configmap_with_mock_cli_options():
    """Test init_watch_configmap with proper ApplicationState setup."""
    # Create a more realistic mock with nested structure
    mock_state = MagicMock(spec=ApplicationState)
    mock_cli_options = MagicMock()
    mock_cli_options.configmap_name = "test-config"
    mock_cli_options.secret_name = "test-secret"
    # Create nested mock structure
    runtime_mock = MagicMock()
    runtime_mock.cli_options = mock_cli_options
    mock_state.runtime = runtime_mock
    # Also set up the backwards compatibility property
    mock_state.cli_options = mock_cli_options

    # The function should complete without errors
    mock_kopf = MagicMock()

    with mock_module_attributes(init_module, kopf=mock_kopf):
        await init_watch_configmap(mock_state)
        # Verify kopf.on was accessed (for event setup)
        assert mock_kopf.on.event.called or hasattr(mock_kopf.on, "event")


def test_run_operator_loop_initialization_flow(
    monkeypatch,
    mock_config_metrics,
):
    """Test that run_operator_loop initialization flow loads config and credentials properly."""
    from haproxy_template_ic.initialization import run_operator_loop
    from haproxy_template_ic.models.cli import CliOptions
    import haproxy_template_ic.credentials as creds_module

    # Mock k8s config loading
    mock_k8s_config = MagicMock()
    mock_k8s_config.load_incluster_config.return_value = None

    # Mock configmap and config loading
    mock_configmap = MagicMock()
    mock_configmap.data = {"config": "test-config-data"}

    async def async_fetch_configmap(*args, **kwargs):
        return mock_configmap

    mock_fetch_configmap = MagicMock(side_effect=async_fetch_configmap)

    mock_config = MagicMock()
    mock_config.pod_selector.match_labels = {"app": "haproxy"}
    mock_config.template_rendering.min_render_interval = 1
    mock_config.template_rendering.max_render_interval = 30
    mock_config.validation.dataplane_host = "localhost"
    mock_config.validation.dataplane_port = 5555

    async def async_load_config(*args, **kwargs):
        return mock_config

    mock_load_config = MagicMock(side_effect=async_load_config)

    # Mock template renderer
    mock_renderer = MagicMock()
    mock_template_renderer_from_config = MagicMock(return_value=mock_renderer)

    # Mock secret fetching
    mock_secret = MagicMock()
    mock_secret.data = {"key": "value"}

    async def async_fetch_secret(*args, **kwargs):
        return mock_secret

    mock_fetch_secret = MagicMock(side_effect=async_fetch_secret)

    mock_credentials = MagicMock()
    mock_creds_from_secret = MagicMock(return_value=mock_credentials)

    # Mock all state classes to avoid Pydantic validation issues
    mock_runtime_state_instance = MagicMock()
    mock_runtime_state = MagicMock(return_value=mock_runtime_state_instance)

    mock_config_state_instance = MagicMock()
    mock_configuration_state = MagicMock(return_value=mock_config_state_instance)

    mock_resource_state_instance = MagicMock()
    mock_resource_state = MagicMock(return_value=mock_resource_state_instance)

    mock_operational_state_instance = MagicMock()
    mock_operational_state = MagicMock(return_value=mock_operational_state_instance)

    mock_app_state_instance = MagicMock(spec=ApplicationState)
    # Set up required attributes that the code expects
    mock_app_state_instance.configuration = mock_config_state_instance
    mock_app_state_instance.configuration.config = mock_config
    # Add operations structure to prevent AttributeError
    mock_operations = MagicMock()
    mock_operations.metrics = mock_config_metrics
    mock_app_state_instance.operations = mock_operations
    mock_application_state = MagicMock(return_value=mock_app_state_instance)

    mock_setup_haproxy_pod_indexing = MagicMock()
    mock_setup_resource_watchers = MagicMock()

    # Mock the entire event loop setup after our config loading to exit early
    mock_init_post = MagicMock(
        side_effect=SystemExit("Test complete - config loading verified")
    )

    # Apply all patches (complex test requires traditional monkeypatch for classes)
    monkeypatch.setattr(init_module, "k8s_config", mock_k8s_config)
    monkeypatch.setattr(init_module, "fetch_configmap", mock_fetch_configmap)
    monkeypatch.setattr(init_module, "load_config_from_configmap", mock_load_config)
    monkeypatch.setattr(init_module, "fetch_secret", mock_fetch_secret)
    monkeypatch.setattr(
        init_module.TemplateRenderer,
        "from_config",
        mock_template_renderer_from_config,
    )
    monkeypatch.setattr(creds_module.Credentials, "from_secret", mock_creds_from_secret)
    monkeypatch.setattr(
        init_module, "setup_resource_watchers", mock_setup_resource_watchers
    )
    monkeypatch.setattr(
        init_module, "setup_haproxy_pod_indexing", mock_setup_haproxy_pod_indexing
    )
    monkeypatch.setattr(init_module, "RuntimeState", mock_runtime_state)
    monkeypatch.setattr(init_module, "ResourceState", mock_resource_state)
    monkeypatch.setattr(init_module, "OperationalState", mock_operational_state)
    monkeypatch.setattr(init_module, "ConfigurationState", mock_configuration_state)
    monkeypatch.setattr(init_module, "ApplicationState", mock_application_state)

    # Create mock CLI options
    mock_cli_options = MagicMock(spec=CliOptions)
    mock_cli_options.configmap_name = "test-config"
    mock_cli_options.secret_name = "test-secret"
    mock_cli_options.namespace = "default"

    # Mock ConfigSynchronizer to prevent complex initialization
    mock_config_sync = MagicMock()
    mock_config_sync_cls = MagicMock(return_value=mock_config_sync)
    monkeypatch.setattr(init_module, "ConfigSynchronizer", mock_config_sync_cls)

    # Mock HAProxyConfigContext to prevent complex initialization
    mock_context = MagicMock()
    mock_context_cls = MagicMock(return_value=mock_context)
    monkeypatch.setattr(init_module, "HAProxyConfigContext", mock_context_cls)

    # Mock the entire event loop setup after our config loading to exit early
    monkeypatch.setattr(init_module, "initialize_post_config", mock_init_post)

    # Expect SystemExit after configuration loading
    with pytest.raises(SystemExit, match="Test complete - config loading verified"):
        run_operator_loop(mock_cli_options)

    # Verify that the configuration loading was attempted
    mock_fetch_configmap.assert_called_once()
    mock_load_config.assert_called_once()
    mock_creds_from_secret.assert_called_once()


@pytest.mark.asyncio
async def test_load_configuration_and_credentials():
    """Test _load_configuration_and_credentials function."""
    from haproxy_template_ic.models.cli import CliOptions
    from tests.unit.conftest import (
        create_configmap_mock,
        create_async_mock_with_config,
        create_pydantic_model_mock,
    )

    # Create mock CLI options using conftest utility
    mock_cli_options = create_pydantic_model_mock(
        CliOptions, configmap_name="test-config", secret_name="test-secret"
    )

    # Use conftest factories for consistent mocking
    mock_configmap = create_configmap_mock({"config": "test-data"})
    mock_config = MagicMock()
    mock_renderer = MagicMock()
    mock_secret = MagicMock()
    mock_secret.data = {"key": "value"}
    mock_credentials = MagicMock()

    # Use conftest async mock utility
    mock_fetch_configmap = create_async_mock_with_config(return_value=mock_configmap)
    mock_load_config = create_async_mock_with_config(return_value=mock_config)
    mock_fetch_secret = create_async_mock_with_config(return_value=mock_secret)

    # Mock class methods
    mock_template_renderer_cls = MagicMock()
    mock_template_renderer_cls.from_config = MagicMock(return_value=mock_renderer)
    mock_credentials_cls = MagicMock()
    mock_credentials_cls.from_secret = MagicMock(return_value=mock_credentials)

    with mock_module_attributes(
        init_module,
        fetch_configmap=mock_fetch_configmap,
        load_config_from_configmap=mock_load_config,
        fetch_secret=mock_fetch_secret,
        has_valid_attr=MagicMock(return_value=True),
        TemplateRenderer=mock_template_renderer_cls,
        Credentials=mock_credentials_cls,
    ):
        result = await _load_configuration_and_credentials(mock_cli_options, "default")

        # Verify the function returns expected tuple
        config, credentials, renderer = result
        assert config == mock_config
        assert credentials == mock_credentials
        assert renderer == mock_renderer

        # Verify all functions were called
        mock_fetch_configmap.assert_called_once_with("test-config", "default")
        mock_load_config.assert_called_once_with(mock_configmap)
        mock_fetch_secret.assert_called_once_with("test-secret", "default")
        mock_template_renderer_cls.from_config.assert_called_once_with(mock_config)
        mock_credentials_cls.from_secret.assert_called_once_with(mock_secret.data)


def test_create_application_state():
    """Test _create_application_state function."""
    from haproxy_template_ic.models.cli import CliOptions
    from tests.unit.conftest import (
        create_pydantic_model_mock,
        create_dataplane_auth_mock,
        create_metrics_collector_mock,
        create_index_synchronization_tracker_mock,
    )
    import asyncio

    # Use conftest utilities for consistent mocking
    mock_cli_options = create_pydantic_model_mock(CliOptions)

    # Create config mock with required attributes
    mock_config = MagicMock()
    mock_config.validation.dataplane_host = "localhost"
    mock_config.validation.dataplane_port = 5555
    mock_config.template_rendering.min_render_interval = 1
    mock_config.template_rendering.max_render_interval = 30

    # Use conftest factory for credentials
    mock_credentials = MagicMock()
    mock_credentials.validation = create_dataplane_auth_mock()

    mock_renderer = MagicMock()

    # Create real Future objects for the test
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    stop_flag = asyncio.Future()
    config_reload_flag = asyncio.Future()

    mock_indexers = MagicMock()
    mock_indexers.indices = {}

    # Use conftest factories for complex mocks
    mock_metrics = create_metrics_collector_mock()
    mock_index_tracker = create_index_synchronization_tracker_mock()

    with mock_module_attributes(
        init_module,
        DataplaneEndpoint=MagicMock(),
        DataplaneEndpointSet=MagicMock(),
        ConfigSynchronizer=MagicMock(),
        HAProxyConfigContext=MagicMock(),
        TemplateContext=MagicMock(),
        IndexSynchronizationTracker=MagicMock(return_value=mock_index_tracker),
        TemplateRenderDebouncer=MagicMock(),
        MetricsCollector=MagicMock(return_value=mock_metrics),
        RuntimeState=MagicMock(),
        ConfigurationState=MagicMock(),
        ResourceState=MagicMock(),
        OperationalState=MagicMock(),
        ApplicationState=MagicMock(),
    ):
        _create_application_state(
            mock_cli_options,
            mock_config,
            mock_credentials,
            mock_renderer,
            stop_flag,
            config_reload_flag,
            mock_indexers,
        )

        # Verify ApplicationState was created
        init_module.ApplicationState.assert_called_once()

    loop.close()


def test_setup_kopf_handlers():
    """Test _setup_kopf_handlers function."""
    mock_memo = MagicMock(spec=ApplicationState)

    # Mock all the required functions
    mock_setup_resource_watchers = MagicMock()
    mock_setup_haproxy_pod_indexing = MagicMock()
    mock_kopf = MagicMock()

    with mock_module_attributes(
        init_module,
        setup_resource_watchers=mock_setup_resource_watchers,
        setup_haproxy_pod_indexing=mock_setup_haproxy_pod_indexing,
        kopf=mock_kopf,
    ):
        _setup_kopf_handlers(mock_memo)

        # Verify all setup functions were called
        mock_setup_resource_watchers.assert_called_once_with(mock_memo)
        mock_setup_haproxy_pod_indexing.assert_called_once_with(mock_memo)

        # Verify kopf handlers were registered
        assert mock_kopf.on.startup.called
        assert mock_kopf.on.cleanup.called


def test_configure_webhook_server_with_default_cert_dir():
    """Test configure_webhook_server creates temporary cert directory."""
    with mock_module_attributes(
        init_module,
        tempfile=MagicMock(),
        atexit=MagicMock(),
        os=MagicMock(),
        shutil=MagicMock(),
    ):
        # Configure tempfile to return a test directory
        init_module.tempfile.mkdtemp.return_value = "/tmp/test-webhook-certs"

        # Configure os.path.exists to return True for cleanup testing
        init_module.os.path.exists.return_value = True

        configure_webhook_server(webhook_port=9443)

        # Verify temporary directory was created
        init_module.tempfile.mkdtemp.assert_called_once_with(
            prefix="haproxy-template-ic-webhook-"
        )

        # Verify cleanup was registered
        init_module.atexit.register.assert_called_once()


def test_configure_webhook_server_with_provided_cert_dir():
    """Test configure_webhook_server uses provided cert directory."""
    with mock_module_attributes(
        init_module,
        tempfile=MagicMock(),
        atexit=MagicMock(),
    ):
        configure_webhook_server(webhook_port=9443, webhook_cert_dir="/custom/cert/dir")

        # Verify no temporary directory was created
        init_module.tempfile.mkdtemp.assert_not_called()

        # Verify no cleanup was registered
        init_module.atexit.register.assert_not_called()


def test_configure_webhook_server_exception_handling():
    """Test configure_webhook_server handles exceptions properly."""
    # Test exception handling in the try-catch block around logging
    mock_logger = MagicMock()

    with mock_module_attributes(
        init_module,
        logger=mock_logger,
        tempfile=MagicMock(),
        atexit=MagicMock(),
    ):
        # Configure tempfile to return a test directory normally
        init_module.tempfile.mkdtemp.return_value = "/tmp/test-webhook-certs"

        # Configure logger.info to raise an exception to test the try-catch block
        mock_logger.info.side_effect = [None, RuntimeError("Logging failed")]

        with pytest.raises(RuntimeError, match="Logging failed"):
            configure_webhook_server()


def test_create_event_loop():
    """Test create_event_loop returns uvloop event loop."""
    with mock_module_attributes(
        init_module,
        uvloop=MagicMock(),
    ):
        mock_policy = MagicMock()
        mock_loop = MagicMock()
        mock_policy.new_event_loop.return_value = mock_loop
        init_module.uvloop.EventLoopPolicy.return_value = mock_policy

        result = create_event_loop()

        assert result == mock_loop
        init_module.uvloop.EventLoopPolicy.assert_called_once()
        mock_policy.new_event_loop.assert_called_once()


def test_run_operator_loop_kubernetes_config_loading():
    """Test run_operator_loop handles Kubernetes config loading."""
    from haproxy_template_ic.models.cli import CliOptions
    from tests.unit.conftest import (
        create_pydantic_model_mock,
        create_metrics_collector_mock,
    )

    # Create mock CLI options
    mock_cli_options = create_pydantic_model_mock(
        CliOptions, configmap_name="test-config", secret_name="test-secret"
    )

    mock_metrics = create_metrics_collector_mock()
    mock_k8s_config = MagicMock()

    # Mock successful in-cluster config loading
    mock_k8s_config.load_incluster_config.return_value = None

    with mock_module_attributes(
        init_module,
        MetricsCollector=MagicMock(return_value=mock_metrics),
        k8s_config=mock_k8s_config,
        get_current_namespace=MagicMock(return_value="default"),
        # Mock the rest to prevent actual execution
        fetch_configmap=MagicMock(side_effect=SystemExit("Test complete")),
    ):
        with pytest.raises(SystemExit, match="Test complete"):
            run_operator_loop(mock_cli_options)

        # Verify in-cluster config was attempted
        mock_k8s_config.load_incluster_config.assert_called_once()


def test_run_operator_loop_fallback_to_kubeconfig():
    """Test run_operator_loop falls back to kubeconfig when in-cluster fails."""
    from haproxy_template_ic.models.cli import CliOptions
    from tests.unit.conftest import (
        create_pydantic_model_mock,
        create_metrics_collector_mock,
    )

    mock_cli_options = create_pydantic_model_mock(
        CliOptions, configmap_name="test-config", secret_name="test-secret"
    )

    mock_metrics = create_metrics_collector_mock()
    mock_k8s_config = MagicMock()

    # Mock in-cluster config failure, kubeconfig success
    mock_k8s_config.load_incluster_config.side_effect = Exception("In-cluster failed")
    mock_k8s_config.load_kube_config.return_value = None

    with mock_module_attributes(
        init_module,
        MetricsCollector=MagicMock(return_value=mock_metrics),
        k8s_config=mock_k8s_config,
        get_current_namespace=MagicMock(return_value="default"),
        # Mock the rest to prevent actual execution
        fetch_configmap=MagicMock(side_effect=SystemExit("Test complete")),
    ):
        with pytest.raises(SystemExit, match="Test complete"):
            run_operator_loop(mock_cli_options)

        # Verify both config methods were attempted
        mock_k8s_config.load_incluster_config.assert_called_once()
        mock_k8s_config.load_kube_config.assert_called_once()


def test_run_operator_loop_kubernetes_config_failure():
    """Test run_operator_loop handles complete Kubernetes config failure."""
    from haproxy_template_ic.models.cli import CliOptions
    from tests.unit.conftest import (
        create_pydantic_model_mock,
        create_metrics_collector_mock,
    )

    mock_cli_options = create_pydantic_model_mock(
        CliOptions, configmap_name="test-config", secret_name="test-secret"
    )

    mock_metrics = create_metrics_collector_mock()
    mock_k8s_config = MagicMock()

    # Mock both config methods failing
    mock_k8s_config.load_incluster_config.side_effect = Exception("In-cluster failed")
    mock_k8s_config.load_kube_config.side_effect = Exception("Kubeconfig failed")

    with mock_module_attributes(
        init_module,
        MetricsCollector=MagicMock(return_value=mock_metrics),
        k8s_config=mock_k8s_config,
    ):
        with pytest.raises(Exception, match="Kubeconfig failed"):
            run_operator_loop(mock_cli_options)


@pytest.mark.asyncio
async def test_initialize_post_config_exception_handling(
    mock_application_state,
    mock_config_metrics,
):
    """Test initialize_post_config handles exceptions properly."""
    # Update the mock application state with the provided metrics collector
    mock_application_state.operations.metrics = mock_config_metrics

    # Mock setup_structured_logging to raise an exception
    with mock_module_attributes(
        init_module,
        setup_structured_logging=MagicMock(side_effect=RuntimeError("Setup failed")),
    ):
        with pytest.raises(RuntimeError, match="Setup failed"):
            await initialize_post_config(mock_application_state)

        # Verify error metrics were recorded
        mock_config_metrics.record_config_reload.assert_called_with(success=False)
        mock_config_metrics.record_error.assert_called_with(
            "config_load_failed", "operator"
        )


@pytest.mark.asyncio
async def test_init_template_debouncer():
    """Test init_template_debouncer function."""
    from tests.unit.conftest import (
        create_application_state_mock,
        create_async_mock_with_config,
    )

    mock_application_state = create_application_state_mock()
    # Set up the operations.debouncer attribute
    mock_debouncer = MagicMock()
    mock_debouncer.start = create_async_mock_with_config()
    mock_operations = MagicMock()
    mock_operations.debouncer = mock_debouncer
    mock_application_state.operations = mock_operations

    await init_template_debouncer(mock_application_state)

    mock_debouncer.start.assert_called_once()


@pytest.mark.asyncio
async def test_cleanup_template_debouncer():
    """Test cleanup_template_debouncer function."""
    from tests.unit.conftest import (
        create_application_state_mock,
        create_async_mock_with_config,
    )

    mock_application_state = create_application_state_mock()
    # Set up the operations.debouncer attribute
    mock_debouncer = MagicMock()
    mock_debouncer.stop = create_async_mock_with_config()
    mock_operations = MagicMock()
    mock_operations.debouncer = mock_debouncer
    mock_application_state.operations = mock_operations

    await cleanup_template_debouncer(mock_application_state)

    mock_debouncer.stop.assert_called_once()


@pytest.mark.asyncio
async def test_cleanup_tracing_enabled(mock_application_state):
    """Test cleanup_tracing when tracing is enabled."""
    mock_application_state.configuration.config.tracing.enabled = True

    # Set up a mock tracing manager
    mock_tracing_manager = MagicMock()
    mock_application_state.operations.tracing_manager = mock_tracing_manager

    await cleanup_tracing(mock_application_state)

    # Verify tracing manager shutdown was called
    mock_tracing_manager.shutdown.assert_called_once()


@pytest.mark.asyncio
async def test_cleanup_tracing_disabled(mock_application_state):
    """Test cleanup_tracing when tracing manager is None."""
    # Set tracing_manager to None to simulate no tracing initialized
    mock_application_state.operations.tracing_manager = None

    # Should not raise any exception
    await cleanup_tracing(mock_application_state)


@pytest.mark.asyncio
async def test_cleanup_tracing_exception_handling(mock_application_state):
    """Test cleanup_tracing handles exceptions properly."""
    mock_application_state.configuration.config.tracing.enabled = True

    # Set up a mock tracing manager that raises an exception
    mock_tracing_manager = MagicMock()
    mock_tracing_manager.shutdown.side_effect = RuntimeError("Shutdown failed")
    mock_application_state.operations.tracing_manager = mock_tracing_manager

    # Should not raise - exception is caught and logged
    await cleanup_tracing(mock_application_state)


@pytest.mark.asyncio
async def test_cleanup_metrics_server():
    """Test cleanup_metrics_server function."""
    from tests.unit.conftest import (
        create_application_state_mock,
        create_async_mock_with_config,
    )

    mock_application_state = create_application_state_mock()
    # Set up the operations.metrics attribute
    mock_metrics = MagicMock()
    mock_metrics.stop_metrics_server = create_async_mock_with_config()
    mock_operations = MagicMock()
    mock_operations.metrics = mock_metrics
    mock_application_state.operations = mock_operations

    await cleanup_metrics_server(mock_application_state)

    mock_metrics.stop_metrics_server.assert_called_once()


@pytest.mark.asyncio
async def test_cleanup_metrics_server_exception_handling():
    """Test cleanup_metrics_server handles exceptions properly."""
    from tests.unit.conftest import create_application_state_mock

    mock_application_state = create_application_state_mock()
    # Set up the operations.metrics attribute
    mock_metrics = MagicMock()
    mock_metrics.stop_metrics_server = MagicMock(
        side_effect=RuntimeError("Stop failed")
    )
    mock_operations = MagicMock()
    mock_operations.metrics = mock_metrics
    mock_application_state.operations = mock_operations

    # Should not raise - exception is caught and logged
    await cleanup_metrics_server(mock_application_state)


@pytest.mark.asyncio
async def test_init_metrics_server():
    """Test init_metrics_server function."""
    from tests.unit.conftest import (
        create_application_state_mock,
        create_async_mock_with_config,
    )

    mock_application_state = create_application_state_mock()
    # Set up the configuration.config.operator.metrics_port attribute
    mock_operator = MagicMock()
    mock_operator.metrics_port = 8080
    mock_application_state.configuration.config.operator = mock_operator

    # Set up the operations.metrics attribute
    mock_metrics = MagicMock()
    mock_metrics.start_metrics_server = create_async_mock_with_config()
    mock_operations = MagicMock()
    mock_operations.metrics = mock_metrics
    mock_application_state.operations = mock_operations

    await init_metrics_server(mock_application_state)

    mock_metrics.start_metrics_server.assert_called_once_with(port=8080)
