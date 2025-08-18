"""
Unit tests for dataplane functionality.

Tests the HAProxy Dataplane API integration including pod discovery,
client operations, and configuration synchronization.
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch

from haproxy_template_ic.dataplane import (
    HAProxyInstance,
    SyncResult,
    DataplaneAPIError,
    ValidationError,
    HAProxyPodDiscovery,
    DataplaneClient,
    ConfigSynchronizer,
)
from haproxy_template_ic.config_models import PodSelector, HAProxyConfigContext


class TestHAProxyInstance:
    """Test the HAProxyInstance dataclass."""

    def test_haproxy_instance_creation(self):
        """Test HAProxyInstance creation."""
        mock_pod = Mock()
        mock_pod.namespace = "default"
        mock_pod.name = "haproxy-pod"

        instance = HAProxyInstance(
            pod=mock_pod,
            dataplane_url="http://192.168.1.1:5555",
            is_validation_sidecar=False,
        )

        assert instance.pod == mock_pod
        assert instance.dataplane_url == "http://192.168.1.1:5555"
        assert instance.is_validation_sidecar is False

    def test_haproxy_instance_name_property(self):
        """Test HAProxyInstance name property."""
        mock_pod = Mock()
        mock_pod.namespace = "kube-system"
        mock_pod.name = "haproxy-loadbalancer"

        instance = HAProxyInstance(
            pod=mock_pod,
            dataplane_url="http://192.168.1.1:5555",
        )

        assert instance.name == "kube-system/haproxy-loadbalancer"

    def test_haproxy_instance_validation_sidecar_default(self):
        """Test HAProxyInstance validation sidecar default value."""
        mock_pod = Mock()
        instance = HAProxyInstance(
            pod=mock_pod,
            dataplane_url="http://192.168.1.1:5555",
        )

        assert instance.is_validation_sidecar is False


class TestSyncResult:
    """Test the SyncResult dataclass."""

    def test_sync_result_success(self):
        """Test successful SyncResult creation."""
        mock_instance = Mock()
        result = SyncResult(
            success=True,
            instance=mock_instance,
            config_version="v123",
        )

        assert result.success is True
        assert result.instance == mock_instance
        assert result.error is None
        assert result.config_version == "v123"

    def test_sync_result_failure(self):
        """Test failed SyncResult creation."""
        mock_instance = Mock()
        result = SyncResult(
            success=False,
            instance=mock_instance,
            error="Deployment failed",
        )

        assert result.success is False
        assert result.instance == mock_instance
        assert result.error == "Deployment failed"
        assert result.config_version is None


class TestDataplaneAPIError:
    """Test custom exception classes."""

    def test_dataplane_api_error(self):
        """Test DataplaneAPIError exception."""
        error = DataplaneAPIError("Test error message")
        assert str(error) == "Test error message"

    def test_validation_error_inheritance(self):
        """Test ValidationError inherits from DataplaneAPIError."""
        error = ValidationError("Validation failed")
        assert isinstance(error, DataplaneAPIError)
        assert str(error) == "Validation failed"


class TestHAProxyPodDiscovery:
    """Test the HAProxyPodDiscovery class."""

    @pytest.fixture
    def pod_selector(self):
        """Create a PodSelector for testing."""
        return PodSelector(match_labels={"app": "haproxy", "component": "loadbalancer"})

    @pytest.fixture
    def discovery(self, pod_selector):
        """Create HAProxyPodDiscovery instance."""
        return HAProxyPodDiscovery(pod_selector, namespace="default")

    @pytest.fixture
    def mock_running_pod(self):
        """Create a mock running pod."""
        pod = Mock()
        pod.namespace = "default"
        pod.name = "haproxy-pod-1"
        pod.status.phase = "Running"
        pod.status.pod_ip = "192.168.1.10"
        pod.metadata = {
            "labels": {},
            "annotations": {},
        }
        return pod

    @pytest.fixture
    def mock_validation_pod(self):
        """Create a mock validation sidecar pod."""
        pod = Mock()
        pod.namespace = "default"
        pod.name = "haproxy-validation-pod"
        pod.status.phase = "Running"
        pod.status.pod_ip = "192.168.1.11"
        pod.metadata = {
            "labels": {"haproxy-template-ic/role": "validation"},
            "annotations": {},
        }
        return pod

    def test_init(self, pod_selector):
        """Test HAProxyPodDiscovery initialization."""
        discovery = HAProxyPodDiscovery(pod_selector, namespace="test-namespace")
        assert discovery.pod_selector == pod_selector
        assert discovery.namespace == "test-namespace"

    def test_init_no_namespace(self, pod_selector):
        """Test HAProxyPodDiscovery initialization without namespace."""
        discovery = HAProxyPodDiscovery(pod_selector)
        assert discovery.pod_selector == pod_selector
        assert discovery.namespace is None

    @pytest.mark.asyncio
    @patch("kr8s.get")
    async def test_discover_instances_success(
        self, mock_kr8s_get, discovery, mock_running_pod
    ):
        """Test successful pod discovery."""
        mock_kr8s_get.return_value = [mock_running_pod]

        instances = await discovery.discover_instances()

        assert len(instances) == 1
        assert instances[0].pod == mock_running_pod
        assert instances[0].dataplane_url == "http://192.168.1.10:5555"
        assert instances[0].is_validation_sidecar is False

        mock_kr8s_get.assert_called_once_with(
            "pods",
            label_selector="app=haproxy,component=loadbalancer",
            namespace="default",
        )

    @pytest.mark.asyncio
    @patch("kr8s.get")
    async def test_discover_instances_with_validation_sidecar(
        self, mock_kr8s_get, discovery, mock_running_pod, mock_validation_pod
    ):
        """Test pod discovery with validation sidecar."""
        mock_kr8s_get.return_value = [mock_running_pod, mock_validation_pod]

        instances = await discovery.discover_instances()

        assert len(instances) == 2

        # Find regular and validation instances
        regular_instance = next(i for i in instances if not i.is_validation_sidecar)
        validation_instance = next(i for i in instances if i.is_validation_sidecar)

        assert regular_instance.pod == mock_running_pod
        assert validation_instance.pod == mock_validation_pod
        assert validation_instance.is_validation_sidecar is True

    @pytest.mark.asyncio
    @patch("kr8s.get")
    async def test_discover_instances_skip_non_running(self, mock_kr8s_get, discovery):
        """Test pod discovery skips non-running pods."""
        pending_pod = Mock()
        pending_pod.namespace = "default"
        pending_pod.name = "pending-pod"
        pending_pod.status.phase = "Pending"

        mock_kr8s_get.return_value = [pending_pod]

        instances = await discovery.discover_instances()

        assert len(instances) == 0

    @pytest.mark.asyncio
    @patch("kr8s.get")
    async def test_discover_instances_no_pods(self, mock_kr8s_get, discovery):
        """Test pod discovery with no matching pods."""
        mock_kr8s_get.return_value = []

        instances = await discovery.discover_instances()

        assert len(instances) == 0

    @pytest.mark.asyncio
    @patch("kr8s.get")
    async def test_discover_instances_kr8s_error(self, mock_kr8s_get, discovery):
        """Test pod discovery with kr8s error."""
        mock_kr8s_get.side_effect = RuntimeError("Kubernetes API error")

        with pytest.raises(DataplaneAPIError, match="Pod discovery failed"):
            await discovery.discover_instances()

    def test_is_validation_sidecar_true(self, discovery):
        """Test validation sidecar identification."""
        pod = Mock()
        pod.metadata = {"labels": {"haproxy-template-ic/role": "validation"}}

        assert discovery._is_validation_sidecar(pod) is True

    def test_is_validation_sidecar_false(self, discovery):
        """Test non-validation sidecar identification."""
        pod = Mock()
        pod.metadata = {"labels": {"app": "haproxy"}}

        assert discovery._is_validation_sidecar(pod) is False

    def test_is_validation_sidecar_no_labels(self, discovery):
        """Test sidecar identification with no labels."""
        pod = Mock()
        pod.metadata = {}

        assert discovery._is_validation_sidecar(pod) is False

    def test_build_dataplane_url_default_port(self, discovery):
        """Test dataplane URL building with default port."""
        pod = Mock()
        pod.status.pod_ip = "192.168.1.100"
        pod.metadata = {"annotations": {}}

        url = discovery._build_dataplane_url(pod)
        assert url == "http://192.168.1.100:5555"

    def test_build_dataplane_url_custom_port(self, discovery):
        """Test dataplane URL building with custom port."""
        pod = Mock()
        pod.status.pod_ip = "192.168.1.100"
        pod.metadata = {"annotations": {"haproxy-template-ic/dataplane-port": "8080"}}

        url = discovery._build_dataplane_url(pod)
        assert url == "http://192.168.1.100:8080"

    def test_build_dataplane_url_no_ip(self, discovery):
        """Test dataplane URL building with no pod IP."""
        pod = Mock()
        pod.namespace = "default"
        pod.name = "test-pod"
        pod.status.pod_ip = None
        pod.metadata = {"annotations": {}}

        with pytest.raises(DataplaneAPIError, match="has no IP address"):
            discovery._build_dataplane_url(pod)


class TestDataplaneClient:
    """Test the DataplaneClient class."""

    @pytest.fixture
    def client(self):
        """Create a DataplaneClient instance."""
        return DataplaneClient(
            "http://192.168.1.1:5555", timeout=10.0, auth=("admin", "test")
        )

    def test_init_with_v3_path(self):
        """Test client initialization with /v3 path."""
        client = DataplaneClient("http://192.168.1.1:5555/v3")
        assert client.base_url == "http://192.168.1.1:5555/v3"

    def test_init_without_v3_path(self):
        """Test client initialization without /v3 path."""
        client = DataplaneClient("http://192.168.1.1:5555")
        assert client.base_url == "http://192.168.1.1:5555/v3"

    def test_init_default_auth(self):
        """Test client initialization with default auth."""
        client = DataplaneClient("http://192.168.1.1:5555")
        assert client.auth == ("admin", "adminpass")

    def test_init_custom_auth(self):
        """Test client initialization with custom auth."""
        client = DataplaneClient("http://192.168.1.1:5555", auth=("user", "pass"))
        assert client.auth == ("user", "pass")

    def test_get_configuration_lazy_init(self, client):
        """Test lazy configuration initialization."""
        assert client._configuration is None
        config = client._get_configuration()
        assert config is not None
        assert client._configuration is config

        # Second call should return same instance
        config2 = client._get_configuration()
        assert config2 is config

    @pytest.mark.asyncio
    @patch("haproxy_template_ic.dataplane.ApiClient")
    @patch("haproxy_template_ic.dataplane.InformationApi")
    async def test_get_version_success(
        self, mock_info_api_class, mock_api_client_class, client
    ):
        """Test successful version retrieval."""
        # Mock the API response
        mock_info_response = Mock()
        mock_info_response.haproxy = {"version": "2.8.0"}
        mock_info_response.api = {"build_date": "2023-01-01"}
        mock_info_response.system = {"os": "linux"}

        mock_info_api = AsyncMock()
        mock_info_api.get_info.return_value = mock_info_response
        mock_info_api_class.return_value = mock_info_api

        mock_api_client = AsyncMock()
        mock_api_client.__aenter__ = AsyncMock(return_value=mock_api_client)
        mock_api_client.__aexit__ = AsyncMock(return_value=None)
        mock_api_client_class.return_value = mock_api_client

        result = await client.get_version()

        assert result["version"] == "2.8.0"
        assert result["build_date"] == "2023-01-01"
        assert result["os"] == "linux"

    @pytest.mark.asyncio
    @patch("haproxy_template_ic.dataplane.ApiClient")
    @patch("haproxy_template_ic.dataplane.InformationApi")
    async def test_get_version_api_exception(
        self, mock_info_api_class, mock_api_client_class, client
    ):
        """Test version retrieval with API exception."""
        from haproxy_dataplane_v3.exceptions import ApiException

        mock_info_api = AsyncMock()
        mock_info_api.get_info.side_effect = ApiException("API Error")
        mock_info_api_class.return_value = mock_info_api

        mock_api_client = AsyncMock()
        mock_api_client.__aenter__ = AsyncMock(return_value=mock_api_client)
        mock_api_client.__aexit__ = AsyncMock(return_value=None)
        mock_api_client_class.return_value = mock_api_client

        with pytest.raises(DataplaneAPIError, match="Failed to get version"):
            await client.get_version()

    @pytest.mark.asyncio
    @patch("haproxy_template_ic.dataplane.ApiClient")
    @patch("haproxy_template_ic.dataplane.ConfigurationApi")
    async def test_validate_configuration_success(
        self, mock_config_api_class, mock_api_client_class, client
    ):
        """Test successful configuration validation."""
        mock_config_api = AsyncMock()
        mock_config_api.post_ha_proxy_configuration.return_value = None
        mock_config_api_class.return_value = mock_config_api

        mock_api_client = AsyncMock()
        mock_api_client.__aenter__ = AsyncMock(return_value=mock_api_client)
        mock_api_client.__aexit__ = AsyncMock(return_value=None)
        mock_api_client_class.return_value = mock_api_client

        result = await client.validate_configuration("global\n  daemon")

        assert result is True
        mock_config_api.post_ha_proxy_configuration.assert_called_once()
        call_args = mock_config_api.post_ha_proxy_configuration.call_args
        assert call_args.kwargs["only_validate"] is True
        assert call_args.kwargs["skip_version"] is True

    @pytest.mark.asyncio
    @patch("haproxy_template_ic.dataplane.ApiClient")
    @patch("haproxy_template_ic.dataplane.ConfigurationApi")
    async def test_validate_configuration_bad_request(
        self, mock_config_api_class, mock_api_client_class, client
    ):
        """Test configuration validation with bad request."""
        from haproxy_dataplane_v3.exceptions import BadRequestException

        mock_config_api = AsyncMock()
        mock_config_api.post_ha_proxy_configuration.side_effect = BadRequestException(
            "Invalid config"
        )
        mock_config_api_class.return_value = mock_config_api

        mock_api_client = AsyncMock()
        mock_api_client.__aenter__ = AsyncMock(return_value=mock_api_client)
        mock_api_client.__aexit__ = AsyncMock(return_value=None)
        mock_api_client_class.return_value = mock_api_client

        result = await client.validate_configuration("invalid config")

        assert result is False

    @pytest.mark.asyncio
    @patch("haproxy_template_ic.dataplane.ApiClient")
    @patch("haproxy_template_ic.dataplane.ConfigurationApi")
    async def test_deploy_configuration_success(
        self, mock_config_api_class, mock_api_client_class, client
    ):
        """Test successful configuration deployment."""
        mock_config_api = AsyncMock()
        mock_config_api.get_configuration_version.side_effect = [
            1,
            2,
        ]  # Current, then new version
        mock_config_api.post_ha_proxy_configuration.return_value = None
        mock_config_api_class.return_value = mock_config_api

        mock_api_client = AsyncMock()
        mock_api_client.__aenter__ = AsyncMock(return_value=mock_api_client)
        mock_api_client.__aexit__ = AsyncMock(return_value=None)
        mock_api_client_class.return_value = mock_api_client

        result = await client.deploy_configuration("global\n  daemon")

        assert result == "2"
        assert mock_config_api.get_configuration_version.call_count == 2
        mock_config_api.post_ha_proxy_configuration.assert_called_once()

    @pytest.mark.asyncio
    @patch("haproxy_template_ic.dataplane.ApiClient")
    @patch("haproxy_template_ic.dataplane.ConfigurationApi")
    async def test_deploy_configuration_with_retry(
        self, mock_config_api_class, mock_api_client_class, client
    ):
        """Test configuration deployment with retry mechanism."""
        mock_config_api = AsyncMock()
        mock_config_api.get_configuration_version.side_effect = [1, 2]
        mock_config_api.post_ha_proxy_configuration.return_value = None
        mock_config_api_class.return_value = mock_config_api

        mock_api_client = AsyncMock()
        mock_api_client.__aenter__ = AsyncMock(return_value=mock_api_client)
        mock_api_client.__aexit__ = AsyncMock(return_value=None)
        mock_api_client_class.return_value = mock_api_client

        # Mock tenacity to avoid actual retry delays
        class MockAsyncRetrying:
            async def __aiter__(self):
                attempt = Mock()
                attempt.__enter__ = Mock(return_value=attempt)
                attempt.__exit__ = Mock(return_value=None)
                yield attempt

        with patch(
            "haproxy_template_ic.dataplane.AsyncRetrying",
            return_value=MockAsyncRetrying(),
        ):
            result = await client.deploy_configuration("global\n  daemon")

        assert result == "2"

    @pytest.mark.asyncio
    @patch("haproxy_template_ic.dataplane.ApiClient")
    @patch("haproxy_template_ic.dataplane.ConfigurationApi")
    async def test_deploy_configuration_bad_request_no_retry(
        self, mock_config_api_class, mock_api_client_class, client
    ):
        """Test configuration deployment with BadRequestException (no retry)."""
        from haproxy_dataplane_v3.exceptions import BadRequestException

        mock_config_api = AsyncMock()
        mock_config_api.get_configuration_version.return_value = 1
        mock_config_api.post_ha_proxy_configuration.side_effect = BadRequestException(
            "Bad config"
        )
        mock_config_api_class.return_value = mock_config_api

        mock_api_client = AsyncMock()
        mock_api_client.__aenter__ = AsyncMock(return_value=mock_api_client)
        mock_api_client.__aexit__ = AsyncMock(return_value=None)
        mock_api_client_class.return_value = mock_api_client

        with pytest.raises(DataplaneAPIError, match="Configuration deployment failed"):
            await client.deploy_configuration("bad config")


class TestConfigSynchronizer:
    """Test the ConfigSynchronizer class."""

    @pytest.fixture
    def mock_pod_discovery(self):
        """Create a mock HAProxyPodDiscovery."""
        return Mock(spec=HAProxyPodDiscovery)

    @pytest.fixture
    def synchronizer(self, mock_pod_discovery):
        """Create a ConfigSynchronizer instance."""
        return ConfigSynchronizer(mock_pod_discovery)

    @pytest.fixture
    def mock_config_context(self):
        """Create a mock HAProxyConfigContext."""
        context = Mock(spec=HAProxyConfigContext)
        context.rendered_config = Mock()
        context.rendered_config.content = "global\n  daemon"
        return context

    @pytest.fixture
    def mock_production_instance(self):
        """Create a mock production HAProxy instance."""
        instance = Mock(spec=HAProxyInstance)
        instance.is_validation_sidecar = False
        instance.dataplane_url = "http://192.168.1.1:5555"
        instance.name = "default/haproxy-prod"
        return instance

    @pytest.fixture
    def mock_validation_instance(self):
        """Create a mock validation HAProxy instance."""
        instance = Mock(spec=HAProxyInstance)
        instance.is_validation_sidecar = True
        instance.dataplane_url = "http://192.168.1.2:5556"
        instance.name = "default/haproxy-validation"
        return instance

    def test_init(self, mock_pod_discovery):
        """Test ConfigSynchronizer initialization."""
        synchronizer = ConfigSynchronizer(mock_pod_discovery)
        assert synchronizer.pod_discovery == mock_pod_discovery

    @pytest.mark.asyncio
    async def test_synchronize_configuration_no_instances(
        self, synchronizer, mock_config_context
    ):
        """Test synchronization with no discovered instances."""
        synchronizer.pod_discovery.discover_instances = AsyncMock(return_value=[])

        results = await synchronizer.synchronize_configuration(mock_config_context)

        assert results == []

    @pytest.mark.asyncio
    async def test_synchronize_configuration_success(
        self,
        synchronizer,
        mock_config_context,
        mock_production_instance,
        mock_validation_instance,
    ):
        """Test successful configuration synchronization."""
        instances = [mock_production_instance, mock_validation_instance]
        synchronizer.pod_discovery.discover_instances = AsyncMock(
            return_value=instances
        )

        # Mock validation success
        with patch.object(
            synchronizer, "_validate_with_sidecars", return_value=True
        ) as mock_validate:
            with patch.object(synchronizer, "_deploy_to_production") as mock_deploy:
                mock_deploy.return_value = [
                    SyncResult(
                        success=True,
                        instance=mock_production_instance,
                        config_version="v1",
                    )
                ]

                results = await synchronizer.synchronize_configuration(
                    mock_config_context
                )

                assert len(results) == 1
                assert results[0].success is True
                mock_validate.assert_called_once_with(
                    [mock_validation_instance], "global\n  daemon"
                )
                mock_deploy.assert_called_once_with(
                    [mock_production_instance], "global\n  daemon"
                )

    @pytest.mark.asyncio
    async def test_synchronize_configuration_validation_failure(
        self,
        synchronizer,
        mock_config_context,
        mock_production_instance,
        mock_validation_instance,
    ):
        """Test synchronization with validation failure."""
        instances = [mock_production_instance, mock_validation_instance]
        synchronizer.pod_discovery.discover_instances = AsyncMock(
            return_value=instances
        )

        # Mock validation failure
        with patch.object(synchronizer, "_validate_with_sidecars", return_value=False):
            with pytest.raises(
                ValidationError, match="Configuration validation failed"
            ):
                await synchronizer.synchronize_configuration(mock_config_context)

    @pytest.mark.asyncio
    async def test_synchronize_configuration_no_validation_sidecars(
        self, synchronizer, mock_config_context, mock_production_instance
    ):
        """Test synchronization with no validation sidecars."""
        instances = [mock_production_instance]  # Only production instances
        synchronizer.pod_discovery.discover_instances = AsyncMock(
            return_value=instances
        )

        with patch.object(synchronizer, "_deploy_to_production") as mock_deploy:
            mock_deploy.return_value = [
                SyncResult(
                    success=True, instance=mock_production_instance, config_version="v1"
                )
            ]

            results = await synchronizer.synchronize_configuration(mock_config_context)

            assert len(results) == 1
            mock_deploy.assert_called_once()

    def test_build_complete_config(self, synchronizer, mock_config_context):
        """Test building complete configuration."""
        config = synchronizer._build_complete_config(mock_config_context)
        assert config == "global\n  daemon"

    def test_build_complete_config_no_rendered_config(self, synchronizer):
        """Test building configuration with no rendered config."""
        context = Mock()
        context.rendered_config = None

        with pytest.raises(
            DataplaneAPIError, match="No rendered HAProxy configuration"
        ):
            synchronizer._build_complete_config(context)

    @pytest.mark.asyncio
    async def test_validate_with_sidecars_success(
        self, synchronizer, mock_validation_instance
    ):
        """Test successful validation with sidecars."""
        validation_instances = [mock_validation_instance]
        config = "global\n  daemon"

        with patch.object(
            synchronizer, "_validate_instance", return_value=True
        ) as mock_validate:
            result = await synchronizer._validate_with_sidecars(
                validation_instances, config
            )

            assert result is True
            mock_validate.assert_called_once()

    @pytest.mark.asyncio
    async def test_validate_with_sidecars_failure(
        self, synchronizer, mock_validation_instance
    ):
        """Test validation failure with sidecars."""
        validation_instances = [mock_validation_instance]
        config = "global\n  daemon"

        with patch.object(synchronizer, "_validate_instance", return_value=False):
            result = await synchronizer._validate_with_sidecars(
                validation_instances, config
            )

            assert result is False

    @pytest.mark.asyncio
    async def test_validate_with_sidecars_exception(
        self, synchronizer, mock_validation_instance
    ):
        """Test validation with exception."""
        validation_instances = [mock_validation_instance]
        config = "global\n  daemon"

        with patch.object(
            synchronizer, "_validate_instance", side_effect=RuntimeError("Error")
        ):
            result = await synchronizer._validate_with_sidecars(
                validation_instances, config
            )

            assert result is False

    @pytest.mark.asyncio
    @patch("haproxy_template_ic.dataplane.DataplaneClient")
    async def test_validate_instance_success(
        self, mock_client_class, synchronizer, mock_validation_instance
    ):
        """Test successful instance validation."""
        mock_client = AsyncMock()
        mock_client.validate_configuration.return_value = True
        mock_client_class.return_value = mock_client

        # Mock tenacity retry
        class MockAsyncRetrying:
            async def __aiter__(self):
                attempt = Mock()
                attempt.__enter__ = Mock(return_value=attempt)
                attempt.__exit__ = Mock(return_value=None)
                yield attempt

        with patch(
            "haproxy_template_ic.dataplane.AsyncRetrying",
            return_value=MockAsyncRetrying(),
        ):
            result = await synchronizer._validate_instance(
                mock_client, mock_validation_instance, "config"
            )

            assert result is True

    @pytest.mark.asyncio
    @patch("haproxy_template_ic.dataplane.DataplaneClient")
    async def test_validate_instance_failure(
        self, mock_client_class, synchronizer, mock_validation_instance
    ):
        """Test instance validation failure."""
        mock_client = AsyncMock()
        mock_client.validate_configuration.return_value = False
        mock_client_class.return_value = mock_client

        # Mock tenacity retry
        class MockAsyncRetrying:
            async def __aiter__(self):
                attempt = Mock()
                attempt.__enter__ = Mock(return_value=attempt)
                attempt.__exit__ = Mock(return_value=None)
                yield attempt

        with patch(
            "haproxy_template_ic.dataplane.AsyncRetrying",
            return_value=MockAsyncRetrying(),
        ):
            with pytest.raises(ValidationError):
                await synchronizer._validate_instance(
                    mock_client, mock_validation_instance, "bad config"
                )

    @pytest.mark.asyncio
    async def test_deploy_to_production_success(
        self, synchronizer, mock_production_instance
    ):
        """Test successful deployment to production."""
        production_instances = [mock_production_instance]
        config = "global\n  daemon"

        mock_sync_result = SyncResult(
            success=True, instance=mock_production_instance, config_version="v1"
        )
        with patch.object(
            synchronizer, "_deploy_to_instance", return_value=mock_sync_result
        ):
            results = await synchronizer._deploy_to_production(
                production_instances, config
            )

            assert len(results) == 1
            assert results[0].success is True

    @pytest.mark.asyncio
    async def test_deploy_to_production_with_exception(
        self, synchronizer, mock_production_instance
    ):
        """Test deployment to production with exception."""
        production_instances = [mock_production_instance]
        config = "global\n  daemon"

        with patch.object(
            synchronizer,
            "_deploy_to_instance",
            side_effect=RuntimeError("Deploy error"),
        ):
            results = await synchronizer._deploy_to_production(
                production_instances, config
            )

            assert len(results) == 1
            assert results[0].success is False
            assert "Deploy error" in results[0].error

    @pytest.mark.asyncio
    @patch("haproxy_template_ic.dataplane.DataplaneClient")
    async def test_deploy_to_instance_success(
        self, mock_client_class, synchronizer, mock_production_instance
    ):
        """Test successful deployment to single instance."""
        mock_client = AsyncMock()
        mock_client.deploy_configuration.return_value = "v123"
        mock_client_class.return_value = mock_client

        result = await synchronizer._deploy_to_instance(
            mock_client, mock_production_instance, "config"
        )

        assert result.success is True
        assert result.config_version == "v123"
        assert result.instance == mock_production_instance

    @pytest.mark.asyncio
    @patch("haproxy_template_ic.dataplane.DataplaneClient")
    async def test_deploy_to_instance_failure(
        self, mock_client_class, synchronizer, mock_production_instance
    ):
        """Test deployment failure to single instance."""
        mock_client = AsyncMock()
        mock_client.deploy_configuration.side_effect = RuntimeError("Deploy failed")
        mock_client_class.return_value = mock_client

        result = await synchronizer._deploy_to_instance(
            mock_client, mock_production_instance, "config"
        )

        assert result.success is False
        assert "Deploy failed" in result.error
        assert result.instance == mock_production_instance
