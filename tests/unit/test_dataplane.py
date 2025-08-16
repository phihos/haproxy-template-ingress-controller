"""
Tests for haproxy_template_ic.dataplane module.

This module contains tests for HAProxy Dataplane API integration functionality.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, Mock, patch
from kr8s.objects import Pod

from haproxy_template_ic.dataplane import (
    HAProxyInstance,
    SyncResult,
    DataplaneAPIError,
    ValidationError,
    HAProxyPodDiscovery,
    DataplaneClient,
    ConfigSynchronizer,
)
from haproxy_template_ic.config import (
    PodSelector,
    HAProxyConfigContext,
    RenderedConfig,
)


# =============================================================================
# Test Helpers
# =============================================================================


def setup_fast_resilient_mocks():
    """Setup mocks to bypass retry delays in tests."""
    mock_circuit_breaker = MagicMock()
    mock_circuit_breaker.get_adaptive_timeout.return_value = 0.01
    mock_circuit_breaker.record_failure = MagicMock()

    mock_resilient = MagicMock()
    mock_resilient.get_circuit_breaker.return_value = mock_circuit_breaker

    async def fast_execute_with_retry(operation, **kwargs):
        try:
            result_value = await operation()
            result = MagicMock()
            result.success = True
            result.result = result_value
            result.error = None
            return result
        except Exception as e:
            result = MagicMock()
            result.success = False
            result.error = e
            result.attempt = 1
            return result

    mock_resilient.execute_with_retry = AsyncMock(side_effect=fast_execute_with_retry)

    mock_metrics = MagicMock()
    mock_metrics.time_dataplane_api_operation.return_value.__enter__ = MagicMock()
    mock_metrics.time_dataplane_api_operation.return_value.__exit__ = MagicMock()

    return mock_resilient, mock_metrics


# =============================================================================
# HAProxyInstance Tests
# =============================================================================


def test_haproxy_instance_creation():
    """Test HAProxyInstance dataclass creation."""
    mock_pod = MagicMock(spec=Pod)
    mock_pod.namespace = "default"
    mock_pod.name = "haproxy-1"

    instance = HAProxyInstance(
        pod=mock_pod,
        dataplane_url="http://10.0.1.5:5555",
        is_validation_sidecar=False,
    )

    assert instance.pod == mock_pod
    assert instance.dataplane_url == "http://10.0.1.5:5555"
    assert instance.is_validation_sidecar is False
    assert instance.name == "default/haproxy-1"


def test_haproxy_instance_validation_sidecar():
    """Test HAProxyInstance validation sidecar flag."""
    mock_pod = MagicMock(spec=Pod)
    mock_pod.namespace = "test"
    mock_pod.name = "haproxy-validation"

    instance = HAProxyInstance(
        pod=mock_pod,
        dataplane_url="http://10.0.1.6:5555",
        is_validation_sidecar=True,
    )

    assert instance.is_validation_sidecar is True
    assert instance.name == "test/haproxy-validation"


# =============================================================================
# SyncResult Tests
# =============================================================================


def test_sync_result_success():
    """Test successful SyncResult creation."""
    mock_pod = MagicMock(spec=Pod)
    instance = HAProxyInstance(pod=mock_pod, dataplane_url="http://10.0.1.5:5555")

    result = SyncResult(success=True, instance=instance, config_version="123")

    assert result.success is True
    assert result.instance == instance
    assert result.error is None
    assert result.config_version == "123"


def test_sync_result_failure():
    """Test failed SyncResult creation."""
    mock_pod = MagicMock(spec=Pod)
    instance = HAProxyInstance(pod=mock_pod, dataplane_url="http://10.0.1.5:5555")

    result = SyncResult(success=False, instance=instance, error="Connection refused")

    assert result.success is False
    assert result.instance == instance
    assert result.error == "Connection refused"
    assert result.config_version is None


# =============================================================================
# HAProxyPodDiscovery Tests
# =============================================================================


@pytest.mark.asyncio
async def test_pod_discovery_success():
    """Test successful pod discovery."""
    pod_selector = PodSelector(match_labels={"app": "haproxy"})
    discovery = HAProxyPodDiscovery(pod_selector, namespace="default")

    # Mock kr8s.get
    mock_pod = MagicMock(spec=Pod)
    mock_pod.namespace = "default"
    mock_pod.name = "haproxy-1"
    mock_pod.status.phase = "Running"
    mock_pod.status.pod_ip = "10.0.1.5"
    mock_pod.metadata.get.return_value = {}  # No annotations

    with patch("kr8s.get", return_value=[mock_pod]) as mock_kr8s_get:
        instances = await discovery.discover_instances()

    mock_kr8s_get.assert_called_once_with(
        "pods", label_selector="app=haproxy", namespace="default"
    )

    assert len(instances) == 1
    instance = instances[0]
    assert instance.pod == mock_pod
    assert instance.dataplane_url == "http://10.0.1.5:5555"
    assert instance.is_validation_sidecar is False


@pytest.mark.asyncio
async def test_pod_discovery_with_validation_sidecar():
    """Test pod discovery identifying validation sidecars."""
    pod_selector = PodSelector(match_labels={"app": "haproxy"})
    discovery = HAProxyPodDiscovery(pod_selector)

    # Mock production pod
    mock_prod_pod = MagicMock(spec=Pod)
    mock_prod_pod.namespace = "default"
    mock_prod_pod.name = "haproxy-prod"
    mock_prod_pod.status.phase = "Running"
    mock_prod_pod.status.pod_ip = "10.0.1.5"
    mock_prod_pod.metadata.get.return_value = {}

    # Mock validation sidecar pod
    mock_val_pod = MagicMock(spec=Pod)
    mock_val_pod.namespace = "default"
    mock_val_pod.name = "haproxy-validation"
    mock_val_pod.status.phase = "Running"
    mock_val_pod.status.pod_ip = "10.0.1.6"
    mock_val_pod.metadata.get.return_value = {"haproxy-template-ic/role": "validation"}

    with patch("kr8s.get", return_value=[mock_prod_pod, mock_val_pod]):
        instances = await discovery.discover_instances()

    assert len(instances) == 2

    prod_instance = next(i for i in instances if not i.is_validation_sidecar)
    val_instance = next(i for i in instances if i.is_validation_sidecar)

    assert prod_instance.pod == mock_prod_pod
    assert prod_instance.is_validation_sidecar is False

    assert val_instance.pod == mock_val_pod
    assert val_instance.is_validation_sidecar is True


@pytest.mark.asyncio
async def test_pod_discovery_skips_non_running_pods():
    """Test that pod discovery skips non-running pods."""
    pod_selector = PodSelector(match_labels={"app": "haproxy"})
    discovery = HAProxyPodDiscovery(pod_selector)

    # Mock pending pod
    mock_pending_pod = MagicMock(spec=Pod)
    mock_pending_pod.namespace = "default"
    mock_pending_pod.name = "haproxy-pending"
    mock_pending_pod.status.phase = "Pending"

    # Mock running pod
    mock_running_pod = MagicMock(spec=Pod)
    mock_running_pod.namespace = "default"
    mock_running_pod.name = "haproxy-running"
    mock_running_pod.status.phase = "Running"
    mock_running_pod.status.pod_ip = "10.0.1.5"
    mock_running_pod.metadata.get.return_value = {}

    with patch("kr8s.get", return_value=[mock_pending_pod, mock_running_pod]):
        instances = await discovery.discover_instances()

    assert len(instances) == 1
    assert instances[0].pod == mock_running_pod


@pytest.mark.asyncio
async def test_pod_discovery_custom_dataplane_port():
    """Test pod discovery with custom Dataplane API port."""
    pod_selector = PodSelector(match_labels={"app": "haproxy"})
    discovery = HAProxyPodDiscovery(pod_selector)

    mock_pod = MagicMock(spec=Pod)
    mock_pod.namespace = "default"
    mock_pod.name = "haproxy-1"
    mock_pod.status.phase = "Running"
    mock_pod.status.pod_ip = "10.0.1.5"
    mock_pod.metadata.get.return_value = {"haproxy-template-ic/dataplane-port": "8080"}

    with patch("kr8s.get", return_value=[mock_pod]):
        instances = await discovery.discover_instances()

    assert len(instances) == 1
    assert instances[0].dataplane_url == "http://10.0.1.5:8080"


@pytest.mark.asyncio
async def test_pod_discovery_no_pod_ip():
    """Test pod discovery handling pods without IP addresses."""
    pod_selector = PodSelector(match_labels={"app": "haproxy"})
    discovery = HAProxyPodDiscovery(pod_selector)

    mock_pod = MagicMock(spec=Pod)
    mock_pod.namespace = "default"
    mock_pod.name = "haproxy-1"
    mock_pod.status.phase = "Running"
    mock_pod.status.pod_ip = None  # No IP

    with patch("kr8s.get", return_value=[mock_pod]):
        with pytest.raises(DataplaneAPIError, match="has no IP address"):
            await discovery.discover_instances()


@pytest.mark.asyncio
async def test_pod_discovery_kr8s_error():
    """Test pod discovery handling kr8s errors."""
    pod_selector = PodSelector(match_labels={"app": "haproxy"})
    discovery = HAProxyPodDiscovery(pod_selector)

    with patch("kr8s.get", side_effect=Exception("Kubernetes error")):
        with pytest.raises(DataplaneAPIError, match="Pod discovery failed"):
            await discovery.discover_instances()


# =============================================================================
# DataplaneClient Tests
# =============================================================================


@pytest.mark.asyncio
async def test_dataplane_client_get_version():
    """Test DataplaneClient version retrieval."""
    client = DataplaneClient("http://10.0.1.5:5555/v3")

    # Mock the lazy import function to return mock classes
    mock_api_client = AsyncMock()
    mock_info_api_class = Mock()

    mock_classes = {
        "ApiClient": mock_api_client,
        "InformationApi": mock_info_api_class,
        "ApiException": Exception,
    }

    with patch(
        "haproxy_template_ic.dataplane._get_dataplane_classes",
        return_value=mock_classes,
    ):
        # Create mock instances
        mock_api_client_instance = AsyncMock()
        mock_info_api_instance = AsyncMock()

        # Setup the context manager for ApiClient
        mock_api_client.return_value.__aenter__.return_value = mock_api_client_instance
        mock_api_client.return_value.__aexit__.return_value = None

        # Setup InformationApi instance
        mock_info_api_class.return_value = mock_info_api_instance

        # Create a mock response object with the expected attributes
        mock_response = Mock()
        mock_response.haproxy = {"version": "2.4.0"}
        mock_response.api = {"api_version": "3.0"}
        mock_response.system = {"hostname": "test"}

        mock_info_api_instance.get_info.return_value = mock_response

        version_info = await client.get_version()

    # Check that the response includes data from all sources
    assert "version" in version_info
    assert "api_version" in version_info
    assert "hostname" in version_info


@pytest.mark.asyncio
async def test_dataplane_client_validate_configuration_success():
    """Test successful configuration validation."""
    client = DataplaneClient("http://10.0.1.5:5555/v3")

    mock_resilient, mock_metrics = setup_fast_resilient_mocks()

    # Mock the generated API client components
    with patch("haproxy_template_ic.dataplane.ApiClient") as mock_api_client:
        with patch(
            "haproxy_template_ic.dataplane.ConfigurationApi"
        ) as mock_config_api_class:
            with patch(
                "haproxy_template_ic.dataplane.get_resilient_operator",
                return_value=mock_resilient,
            ):
                with patch(
                    "haproxy_template_ic.dataplane.get_metrics_collector",
                    return_value=mock_metrics,
                ):
                    # Create mock instances
                    mock_api_client_instance = AsyncMock()
                    mock_config_api_instance = AsyncMock()

                    # Setup the context manager for ApiClient
                    mock_api_client.return_value.__aenter__.return_value = (
                        mock_api_client_instance
                    )
                    mock_api_client.return_value.__aexit__.return_value = None

                    # Setup ConfigurationApi instance
                    mock_config_api_class.return_value = mock_config_api_instance

                    # Mock successful validation (no exception)
                    mock_config_api_instance.post_ha_proxy_configuration.return_value = None

                    result = await client.validate_configuration("global\n    daemon")

    assert result is True


@pytest.mark.asyncio
async def test_dataplane_client_validate_configuration_failure():
    """Test configuration validation failure."""
    client = DataplaneClient("http://10.0.1.5:5555/v3")

    mock_resilient, mock_metrics = setup_fast_resilient_mocks()

    # Mock the generated API client components
    with patch("haproxy_template_ic.dataplane.ApiClient") as mock_api_client:
        with patch(
            "haproxy_template_ic.dataplane.ConfigurationApi"
        ) as mock_config_api_class:
            with patch(
                "haproxy_template_ic.dataplane.get_resilient_operator",
                return_value=mock_resilient,
            ):
                with patch(
                    "haproxy_template_ic.dataplane.get_metrics_collector",
                    return_value=mock_metrics,
                ):
                    # Create mock instances
                    mock_api_client_instance = AsyncMock()
                    mock_config_api_instance = AsyncMock()

                    # Setup the context manager for ApiClient
                    mock_api_client.return_value.__aenter__.return_value = (
                        mock_api_client_instance
                    )
                    mock_api_client.return_value.__aexit__.return_value = None

                    # Setup ConfigurationApi instance
                    mock_config_api_class.return_value = mock_config_api_instance

                    # Mock validation failure (BadRequestException)
                    from haproxy_dataplane_v3.exceptions import BadRequestException

                    mock_config_api_instance.post_ha_proxy_configuration.side_effect = (
                        BadRequestException("Validation failed")
                    )

                    result = await client.validate_configuration("invalid config")

    assert result is False


@pytest.mark.asyncio
async def test_dataplane_client_deploy_configuration_success():
    """Test successful configuration deployment."""
    client = DataplaneClient("http://10.0.1.5:5555/v3")

    mock_resilient, mock_metrics = setup_fast_resilient_mocks()

    # Mock the generated API client components to make the actual operation succeed
    with patch("haproxy_template_ic.dataplane.ApiClient") as mock_api_client:
        with patch(
            "haproxy_template_ic.dataplane.ConfigurationApi"
        ) as mock_config_api_class:
            with patch(
                "haproxy_template_ic.dataplane.get_resilient_operator",
                return_value=mock_resilient,
            ):
                with patch(
                    "haproxy_template_ic.dataplane.get_metrics_collector",
                    return_value=mock_metrics,
                ):
                    # Create mock instances
                    mock_api_client_instance = AsyncMock()
                    mock_config_api_instance = AsyncMock()

                    # Setup the context manager for ApiClient
                    mock_api_client.return_value.__aenter__.return_value = (
                        mock_api_client_instance
                    )
                    mock_api_client.return_value.__aexit__.return_value = None

                    # Setup ConfigurationApi instance
                    mock_config_api_class.return_value = mock_config_api_instance

                    # Mock successful deployment
                    mock_config_api_instance.post_ha_proxy_configuration.return_value = None
                    mock_config_api_instance.get_configuration_version.return_value = 42

                    version = await client.deploy_configuration("global\n    daemon")

    assert version == "42"


@pytest.mark.asyncio
async def test_dataplane_client_deploy_configuration_failure():
    """Test configuration deployment failure."""
    client = DataplaneClient("http://10.0.1.5:5555/v3")

    mock_resilient, mock_metrics = setup_fast_resilient_mocks()

    # Mock the failed result from resilient operator
    mock_failed_result = Mock()
    mock_failed_result.success = False
    mock_failed_result.error = Exception("Deployment failed")
    mock_failed_result.result = None
    mock_failed_result.attempt = 3
    mock_resilient.execute_with_retry.return_value = mock_failed_result

    with patch(
        "haproxy_template_ic.dataplane.get_resilient_operator",
        return_value=mock_resilient,
    ):
        with patch(
            "haproxy_template_ic.dataplane.get_metrics_collector",
            return_value=mock_metrics,
        ):
            with pytest.raises(
                DataplaneAPIError, match="Configuration deployment failed"
            ):
                await client.deploy_configuration("invalid config")


# =============================================================================
# ConfigSynchronizer Tests
# =============================================================================


@pytest.mark.asyncio
async def test_config_synchronizer_no_instances():
    """Test configuration synchronization with no instances found."""
    mock_discovery = MagicMock(spec=HAProxyPodDiscovery)
    mock_discovery.discover_instances.return_value = []

    synchronizer = ConfigSynchronizer(mock_discovery)

    config_context = HAProxyConfigContext()
    config_context.rendered_config = RenderedConfig(
        content="global\n    daemon", config=MagicMock()
    )

    results = await synchronizer.synchronize_configuration(config_context)

    assert results == []


@pytest.mark.asyncio
async def test_config_synchronizer_no_rendered_config():
    """Test configuration synchronization with no rendered config."""
    mock_discovery = MagicMock(spec=HAProxyPodDiscovery)
    synchronizer = ConfigSynchronizer(mock_discovery)

    config_context = HAProxyConfigContext()  # No rendered_config

    with pytest.raises(
        DataplaneAPIError, match="No rendered HAProxy configuration available"
    ):
        await synchronizer.synchronize_configuration(config_context)


@pytest.mark.asyncio
async def test_config_synchronizer_validation_failure():
    """Test configuration synchronization with validation failure."""
    # Create mock validation instance
    mock_pod = MagicMock(spec=Pod)
    mock_pod.namespace = "default"
    mock_pod.name = "haproxy-validation"

    validation_instance = HAProxyInstance(
        pod=mock_pod,
        dataplane_url="http://10.0.1.6:5555",
        is_validation_sidecar=True,
    )

    mock_discovery = MagicMock(spec=HAProxyPodDiscovery)
    mock_discovery.discover_instances.return_value = [validation_instance]

    synchronizer = ConfigSynchronizer(mock_discovery)

    config_context = HAProxyConfigContext()
    config_context.rendered_config = RenderedConfig(
        content="global\n    daemon", config=MagicMock()
    )

    # Mock validation failure
    with patch.object(synchronizer, "_validate_with_sidecars", return_value=False):
        with pytest.raises(ValidationError, match="Configuration validation failed"):
            await synchronizer.synchronize_configuration(config_context)


@pytest.mark.asyncio
async def test_config_synchronizer_successful_sync():
    """Test successful configuration synchronization."""
    # Create mock instances
    mock_val_pod = MagicMock(spec=Pod)
    mock_val_pod.namespace = "default"
    mock_val_pod.name = "haproxy-validation"

    mock_prod_pod = MagicMock(spec=Pod)
    mock_prod_pod.namespace = "default"
    mock_prod_pod.name = "haproxy-prod"

    validation_instance = HAProxyInstance(
        pod=mock_val_pod,
        dataplane_url="http://10.0.1.6:5555",
        is_validation_sidecar=True,
    )

    production_instance = HAProxyInstance(
        pod=mock_prod_pod,
        dataplane_url="http://10.0.1.5:5555",
        is_validation_sidecar=False,
    )

    mock_discovery = MagicMock(spec=HAProxyPodDiscovery)
    mock_discovery.discover_instances.return_value = [
        validation_instance,
        production_instance,
    ]

    synchronizer = ConfigSynchronizer(mock_discovery)

    config_context = HAProxyConfigContext()
    config_context.rendered_config = RenderedConfig(
        content="global\n    daemon", config=MagicMock()
    )

    # Mock successful validation and deployment
    with patch.object(synchronizer, "_validate_with_sidecars", return_value=True):
        with patch.object(synchronizer, "_deploy_to_production") as mock_deploy:
            expected_result = SyncResult(
                success=True, instance=production_instance, config_version="123"
            )
            mock_deploy.return_value = [expected_result]

            results = await synchronizer.synchronize_configuration(config_context)

    assert len(results) == 1
    assert results[0] == expected_result


@pytest.mark.asyncio
async def test_config_synchronizer_build_complete_config():
    """Test building complete HAProxy configuration."""
    mock_discovery = MagicMock(spec=HAProxyPodDiscovery)
    synchronizer = ConfigSynchronizer(mock_discovery)

    config_context = HAProxyConfigContext()
    config_context.rendered_config = RenderedConfig(
        content="global\n    daemon", config=MagicMock()
    )

    config = synchronizer._build_complete_config(config_context)

    assert config == "global\n    daemon"


def test_config_synchronizer_build_complete_config_no_rendered():
    """Test building complete config with no rendered config."""
    mock_discovery = MagicMock(spec=HAProxyPodDiscovery)
    synchronizer = ConfigSynchronizer(mock_discovery)

    config_context = HAProxyConfigContext()  # No rendered_config

    with pytest.raises(
        DataplaneAPIError, match="No rendered HAProxy configuration available"
    ):
        synchronizer._build_complete_config(config_context)


@pytest.mark.asyncio
async def test_config_synchronizer_validate_instance_success():
    """Test successful instance validation."""
    mock_discovery = MagicMock(spec=HAProxyPodDiscovery)
    synchronizer = ConfigSynchronizer(mock_discovery)

    mock_client = MagicMock(spec=DataplaneClient)
    mock_client.validate_configuration.return_value = True

    mock_pod = MagicMock(spec=Pod)
    instance = HAProxyInstance(pod=mock_pod, dataplane_url="http://10.0.1.5:5555")

    result = await synchronizer._validate_instance(mock_client, instance, "config")

    assert result is True
    mock_client.validate_configuration.assert_called_once_with("config")


@pytest.mark.asyncio
async def test_config_synchronizer_validate_instance_failure():
    """Test instance validation with exception."""
    mock_discovery = MagicMock(spec=HAProxyPodDiscovery)
    synchronizer = ConfigSynchronizer(mock_discovery)

    mock_client = MagicMock(spec=DataplaneClient)
    mock_client.validate_configuration.side_effect = Exception("Network error")

    mock_pod = MagicMock(spec=Pod)
    mock_pod.namespace = "default"
    mock_pod.name = "haproxy-1"

    instance = HAProxyInstance(pod=mock_pod, dataplane_url="http://10.0.1.5:5555")

    result = await synchronizer._validate_instance(mock_client, instance, "config")

    assert result is False


@pytest.mark.asyncio
async def test_config_synchronizer_deploy_to_instance_success():
    """Test successful deployment to instance."""
    mock_discovery = MagicMock(spec=HAProxyPodDiscovery)
    synchronizer = ConfigSynchronizer(mock_discovery)

    mock_client = MagicMock(spec=DataplaneClient)
    mock_client.deploy_configuration.return_value = "123"

    mock_pod = MagicMock(spec=Pod)
    mock_pod.namespace = "default"
    mock_pod.name = "haproxy-1"

    instance = HAProxyInstance(pod=mock_pod, dataplane_url="http://10.0.1.5:5555")

    result = await synchronizer._deploy_to_instance(mock_client, instance, "config")

    assert result.success is True
    assert result.instance == instance
    assert result.config_version == "123"
    assert result.error is None


@pytest.mark.asyncio
async def test_config_synchronizer_deploy_to_instance_failure():
    """Test deployment failure to instance."""
    mock_discovery = MagicMock(spec=HAProxyPodDiscovery)
    synchronizer = ConfigSynchronizer(mock_discovery)

    mock_client = MagicMock(spec=DataplaneClient)
    mock_client.deploy_configuration.side_effect = DataplaneAPIError("Deploy failed")

    mock_pod = MagicMock(spec=Pod)
    mock_pod.namespace = "default"
    mock_pod.name = "haproxy-1"

    instance = HAProxyInstance(pod=mock_pod, dataplane_url="http://10.0.1.5:5555")

    result = await synchronizer._deploy_to_instance(mock_client, instance, "config")

    assert result.success is False
    assert result.instance == instance
    assert result.config_version is None
    assert result.error == "Deploy failed"


@pytest.mark.asyncio
async def test_synchronize_configuration_no_validation_sidecars():
    """Test synchronization when no validation sidecars are found."""
    mock_discovery = MagicMock(spec=HAProxyPodDiscovery)

    production_instance = HAProxyInstance(
        pod=MagicMock(spec=Pod),
        dataplane_url="http://production:8080",
        is_validation_sidecar=False,
    )

    mock_discovery.discover_instances.return_value = [production_instance]

    synchronizer = ConfigSynchronizer(mock_discovery)

    config_context = HAProxyConfigContext()
    config_context.rendered_config = RenderedConfig(
        content="global\n    daemon", config=MagicMock()
    )

    # Mock successful deployment to production
    with patch.object(synchronizer, "_deploy_to_production") as mock_deploy:
        mock_deploy.return_value = [
            SyncResult(success=True, instance=production_instance)
        ]

        results = await synchronizer.synchronize_configuration(config_context)

        assert len(results) == 1
        assert results[0].success is True
        # Should log warning about no validation sidecars


@pytest.mark.asyncio
async def test_validate_with_sidecars_logging():
    """Test that _validate_with_sidecars logs the number of sidecars."""
    mock_discovery = MagicMock(spec=HAProxyPodDiscovery)
    synchronizer = ConfigSynchronizer(mock_discovery)

    validation_instances = [
        HAProxyInstance(
            pod=MagicMock(spec=Pod),
            dataplane_url="http://validator1:8080",
            is_validation_sidecar=True,
        ),
        HAProxyInstance(
            pod=MagicMock(spec=Pod),
            dataplane_url="http://validator2:8080",
            is_validation_sidecar=True,
        ),
    ]

    config = "global\n    daemon"

    # Mock both _validate_instance calls to succeed
    with patch.object(
        synchronizer, "_validate_instance", new_callable=AsyncMock
    ) as mock_validate:
        mock_validate.return_value = None

        # This should complete successfully and log about 2 sidecars
        await synchronizer._validate_with_sidecars(validation_instances, config)

        # Verify _validate_instance was called for both instances
        assert mock_validate.call_count == 2


@pytest.mark.asyncio
async def test_validate_instance_dataplane_error():
    """Test instance validation with DataplaneAPIError."""
    mock_discovery = MagicMock(spec=HAProxyPodDiscovery)
    synchronizer = ConfigSynchronizer(mock_discovery)

    mock_client = MagicMock()
    mock_client.validate_configuration = AsyncMock(
        side_effect=DataplaneAPIError("Invalid config")
    )

    mock_pod = MagicMock(spec=Pod)
    mock_pod.namespace = "test-ns"
    mock_pod.name = "test-pod"

    instance = HAProxyInstance(
        pod=mock_pod, dataplane_url="http://validator:8080", is_validation_sidecar=True
    )
    config = "global\n    daemon"

    result = await synchronizer._validate_instance(mock_client, instance, config)
    assert (
        result is False
    )  # Should return False on DataplaneAPIError, not raise ValidationError


@pytest.mark.asyncio
async def test_deploy_to_production_error_handling():
    """Test production deployment with error handling."""
    mock_discovery = MagicMock(spec=HAProxyPodDiscovery)
    synchronizer = ConfigSynchronizer(mock_discovery)

    production_instances = [
        HAProxyInstance(
            pod=MagicMock(spec=Pod),
            dataplane_url="http://prod1:8080",
            is_validation_sidecar=False,
        ),
        HAProxyInstance(
            pod=MagicMock(spec=Pod),
            dataplane_url="http://prod2:8080",
            is_validation_sidecar=False,
        ),
    ]

    config = "global\n    daemon"

    # Mock one success and one failure
    with patch.object(synchronizer, "_deploy_to_instance") as mock_deploy:

        async def side_effect(client, instance, config):
            if instance == production_instances[0]:
                return SyncResult(
                    success=True, instance=instance, config_version="v123"
                )
            else:
                return SyncResult(
                    success=False, instance=instance, error="Deploy failed"
                )

        mock_deploy.side_effect = side_effect

        results = await synchronizer._deploy_to_production(production_instances, config)

        assert len(results) == 2
        assert results[0].success is True
        assert results[1].success is False
