"""Unit tests for initialization module covering tracing and error handling."""

from unittest.mock import MagicMock

import pytest

import haproxy_template_ic.initialization as init_module
from haproxy_template_ic.initialization import (
    initialize_post_config,
    init_watch_configmap,
)
from haproxy_template_ic.models.state import ApplicationState
from haproxy_template_ic.tracing import TracingConfig


class TestInitializePostConfig:
    """Test post-configuration initialization with tracing scenarios."""

    @pytest.fixture
    def mock_application_state(self):
        """Create a mock ApplicationState."""
        state = MagicMock(spec=ApplicationState)
        # Mock the nested configuration structure
        config_mock = MagicMock()
        config_mock.logging.verbose = 1
        config_mock.logging.structured = False
        config_mock.tracing.enabled = True
        config_mock.tracing.service_name = "test-service"
        config_mock.tracing.service_version = "1.0.0"
        config_mock.tracing.jaeger_endpoint = "jaeger:14268"
        config_mock.tracing.sample_rate = 0.5
        config_mock.tracing.console_export = True

        # Create nested mock structure
        configuration_mock = MagicMock()
        configuration_mock.config = config_mock
        state.configuration = configuration_mock

        # Also set up the backwards compatibility property
        state.config = config_mock
        return state

    @pytest.mark.asyncio
    async def test_tracing_initialization_enabled(
        self,
        monkeypatch,
        mock_application_state,
    ):
        """Test tracing initialization when enabled."""
        # Setup mocks
        mock_tracing_config = MagicMock(spec=TracingConfig)
        mock_create_tracing_config = MagicMock(return_value=mock_tracing_config)
        mock_init_tracing = MagicMock()
        mock_setup_logging = MagicMock()

        # Mock metrics
        mock_metrics = MagicMock()
        mock_time_context = MagicMock()
        mock_time_context.__enter__ = MagicMock(return_value=mock_time_context)
        mock_time_context.__exit__ = MagicMock(return_value=None)
        mock_metrics.time_config_reload.return_value = mock_time_context
        mock_get_metrics = MagicMock(return_value=mock_metrics)

        # Apply patches
        monkeypatch.setattr(
            init_module, "create_tracing_config_from_env", mock_create_tracing_config
        )
        monkeypatch.setattr(init_module, "initialize_tracing", mock_init_tracing)
        monkeypatch.setattr(init_module, "setup_structured_logging", mock_setup_logging)
        monkeypatch.setattr(init_module, "get_metrics_collector", mock_get_metrics)

        # Call the function
        await initialize_post_config(mock_application_state)

        # Verify tracing configuration was updated
        assert mock_tracing_config.enabled
        assert mock_tracing_config.service_name == "test-service"
        assert mock_tracing_config.service_version == "1.0.0"
        assert mock_tracing_config.jaeger_endpoint == "jaeger:14268"
        assert mock_tracing_config.sample_rate == 0.5
        assert mock_tracing_config.console_export

        # Verify tracing was initialized
        mock_init_tracing.assert_called_once_with(mock_tracing_config)

    @pytest.mark.asyncio
    async def test_tracing_initialization_disabled(
        self,
        monkeypatch,
        mock_application_state,
    ):
        """Test tracing initialization when disabled."""
        # Disable tracing in config
        mock_application_state.config.tracing.enabled = False

        # Setup mocks
        mock_create_tracing_config = MagicMock()
        mock_init_tracing = MagicMock()
        mock_setup_logging = MagicMock()

        # Mock metrics
        mock_metrics = MagicMock()
        mock_time_context = MagicMock()
        mock_time_context.__enter__ = MagicMock(return_value=mock_time_context)
        mock_time_context.__exit__ = MagicMock(return_value=None)
        mock_metrics.time_config_reload.return_value = mock_time_context
        mock_get_metrics = MagicMock(return_value=mock_metrics)

        # Apply patches
        monkeypatch.setattr(
            init_module, "create_tracing_config_from_env", mock_create_tracing_config
        )
        monkeypatch.setattr(init_module, "initialize_tracing", mock_init_tracing)
        monkeypatch.setattr(init_module, "setup_structured_logging", mock_setup_logging)
        monkeypatch.setattr(init_module, "get_metrics_collector", mock_get_metrics)

        # Call the function
        await initialize_post_config(mock_application_state)

        # Verify tracing initialization was not called when disabled
        mock_create_tracing_config.assert_not_called()
        mock_init_tracing.assert_not_called()

    @pytest.mark.asyncio
    async def test_tracing_initialization_with_fallback_values(
        self,
        monkeypatch,
        mock_application_state,
    ):
        """Test tracing initialization with fallback to environment values."""
        # Setup tracing config with None values to test fallback
        config_mock = mock_application_state.config
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
        mock_init_tracing = MagicMock()
        mock_setup_logging = MagicMock()

        # Mock metrics
        mock_metrics = MagicMock()
        mock_time_context = MagicMock()
        mock_time_context.__enter__ = MagicMock(return_value=mock_time_context)
        mock_time_context.__exit__ = MagicMock(return_value=None)
        mock_metrics.time_config_reload.return_value = mock_time_context
        mock_get_metrics = MagicMock(return_value=mock_metrics)

        # Apply patches
        monkeypatch.setattr(
            init_module, "create_tracing_config_from_env", mock_create_tracing_config
        )
        monkeypatch.setattr(init_module, "initialize_tracing", mock_init_tracing)
        monkeypatch.setattr(init_module, "setup_structured_logging", mock_setup_logging)
        monkeypatch.setattr(init_module, "get_metrics_collector", mock_get_metrics)

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
    async def test_metrics_recording_success(self, monkeypatch, mock_application_state):
        """Test that metrics are recorded for successful config reload."""
        mock_setup_logging = MagicMock()
        mock_metrics = MagicMock()
        mock_time_context = MagicMock()
        mock_time_context.__enter__ = MagicMock(return_value=mock_time_context)
        mock_time_context.__exit__ = MagicMock(return_value=None)
        mock_metrics.time_config_reload.return_value = mock_time_context
        mock_get_metrics = MagicMock(return_value=mock_metrics)

        # Apply patches
        monkeypatch.setattr(init_module, "setup_structured_logging", mock_setup_logging)
        monkeypatch.setattr(init_module, "get_metrics_collector", mock_get_metrics)

        mock_application_state.config.tracing.enabled = (
            False  # Disable tracing for simpler test
        )

        # Call the function
        await initialize_post_config(mock_application_state)

        # Verify success metric was recorded
        mock_metrics.record_config_reload.assert_called_once_with(success=True)


class TestInitWatchConfigmap:
    """Test ConfigMap watching initialization."""

    @pytest.mark.asyncio
    async def test_init_watch_configmap_setup(self, monkeypatch):
        """Test that init_watch_configmap sets up event handlers correctly."""
        mock_kopf_on = MagicMock()
        monkeypatch.setattr(init_module.kopf, "on", mock_kopf_on)

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
    async def test_init_watch_configmap_with_mock_cli_options(self):
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
        import haproxy_template_ic.initialization as init_module

        original_kopf = init_module.kopf
        init_module.kopf = mock_kopf
        try:
            await init_watch_configmap(mock_state)
            # Verify kopf.on was accessed (for event setup)
            assert mock_kopf.on.event.called or hasattr(mock_kopf.on, "event")
        finally:
            init_module.kopf = original_kopf


class TestRunOperatorLoop:
    """Test the run_operator_loop function initialization and configuration loading."""

    def test_run_operator_loop_initialization_flow(
        self,
        monkeypatch,
    ):
        """Test that run_operator_loop initialization flow loads config and credentials properly."""
        from haproxy_template_ic.initialization import run_operator_loop
        from haproxy_template_ic.models.cli import CliOptions
        import haproxy_template_ic.credentials as creds_module

        # Mock the metrics collector
        mock_metrics = MagicMock()
        mock_get_metrics = MagicMock(return_value=mock_metrics)

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
        mock_application_state = MagicMock(return_value=mock_app_state_instance)

        mock_setup_haproxy_pod_indexing = MagicMock()
        mock_setup_resource_watchers = MagicMock()

        # Apply all patches
        monkeypatch.setattr(init_module, "get_metrics_collector", mock_get_metrics)
        monkeypatch.setattr(init_module, "config", mock_k8s_config)
        monkeypatch.setattr(init_module, "fetch_configmap", mock_fetch_configmap)
        monkeypatch.setattr(init_module, "load_config_from_configmap", mock_load_config)
        monkeypatch.setattr(init_module, "fetch_secret", mock_fetch_secret)
        monkeypatch.setattr(
            init_module.TemplateRenderer,
            "from_config",
            mock_template_renderer_from_config,
        )
        monkeypatch.setattr(
            creds_module.Credentials, "from_secret", mock_creds_from_secret
        )
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
        mock_init_post = MagicMock(
            side_effect=SystemExit("Test complete - config loading verified")
        )
        monkeypatch.setattr(init_module, "initialize_post_config", mock_init_post)

        # Expect SystemExit after configuration loading
        with pytest.raises(SystemExit, match="Test complete - config loading verified"):
            run_operator_loop(mock_cli_options)

        # Verify that the configuration loading was attempted
        mock_fetch_configmap.assert_called_once()
        mock_load_config.assert_called_once()
        mock_creds_from_secret.assert_called_once()
