"""
Tests for haproxy_template_ic.dataplane module.

This module contains tests for HAProxy Dataplane API integration functionality.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
import httpx
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
# HAProxyInstance Tests
# =============================================================================


def test_haproxy_instance_creation():
    """Test HAProxyInstance dataclass creation."""
    mock_pod = MagicMock(spec=Pod)
    mock_pod.namespace = "default"
    mock_pod.name = "haproxy-1"

    instance = HAProxyInstance(
        pod=mock_pod,
        dataplane_url="http://10.0.1.5:5555/v2",
        is_validation_sidecar=False,
    )

    assert instance.pod == mock_pod
    assert instance.dataplane_url == "http://10.0.1.5:5555/v2"
    assert instance.is_validation_sidecar is False
    assert instance.name == "default/haproxy-1"


def test_haproxy_instance_validation_sidecar():
    """Test HAProxyInstance validation sidecar flag."""
    mock_pod = MagicMock(spec=Pod)
    mock_pod.namespace = "test"
    mock_pod.name = "haproxy-validation"

    instance = HAProxyInstance(
        pod=mock_pod,
        dataplane_url="http://10.0.1.6:5555/v2",
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
    instance = HAProxyInstance(pod=mock_pod, dataplane_url="http://10.0.1.5:5555/v2")

    result = SyncResult(success=True, instance=instance, config_version="123")

    assert result.success is True
    assert result.instance == instance
    assert result.error is None
    assert result.config_version == "123"


def test_sync_result_failure():
    """Test failed SyncResult creation."""
    mock_pod = MagicMock(spec=Pod)
    instance = HAProxyInstance(pod=mock_pod, dataplane_url="http://10.0.1.5:5555/v2")

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
    assert instance.dataplane_url == "http://10.0.1.5:5555/v2"
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
    assert instances[0].dataplane_url == "http://10.0.1.5:8080/v2"


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
    client = DataplaneClient("http://10.0.1.5:5555/v2")

    mock_response = MagicMock()
    mock_response.json.return_value = {"version": "2.4.0"}

    with patch("httpx.AsyncClient") as mock_client_class:
        mock_client = AsyncMock()
        mock_client_class.return_value.__aenter__.return_value = mock_client
        mock_client.get.return_value = mock_response

        version_info = await client.get_version()

    mock_client.get.assert_called_once_with("http://10.0.1.5:5555/v2/info")
    mock_response.raise_for_status.assert_called_once()
    assert version_info == {"version": "2.4.0"}


@pytest.mark.asyncio
async def test_dataplane_client_validate_configuration_success():
    """Test successful configuration validation."""
    client = DataplaneClient("http://10.0.1.5:5555/v2")

    mock_response = MagicMock()

    with patch("httpx.AsyncClient") as mock_client_class:
        mock_client = AsyncMock()
        mock_client_class.return_value.__aenter__.return_value = mock_client
        mock_client.post.return_value = mock_response

        result = await client.validate_configuration("global\n    daemon")

    mock_client.post.assert_called_once_with(
        "http://10.0.1.5:5555/v2/services/haproxy/configuration/raw",
        content="global\n    daemon",
        headers={"Content-Type": "text/plain"},
        params={"force_reload": "false", "version": "0"},
    )
    mock_response.raise_for_status.assert_called_once()
    assert result is True


@pytest.mark.asyncio
async def test_dataplane_client_validate_configuration_failure():
    """Test configuration validation failure."""
    client = DataplaneClient("http://10.0.1.5:5555/v2")

    with patch("httpx.AsyncClient") as mock_client_class:
        mock_client = AsyncMock()
        mock_client_class.return_value.__aenter__.return_value = mock_client
        mock_client.post.side_effect = httpx.HTTPStatusError(
            "400 Bad Request",
            request=MagicMock(),
            response=MagicMock(text="Invalid configuration"),
        )

        result = await client.validate_configuration("invalid config")

    assert result is False


@pytest.mark.asyncio
async def test_dataplane_client_deploy_configuration_success():
    """Test successful configuration deployment."""
    client = DataplaneClient("http://10.0.1.5:5555/v2")

    mock_deploy_response = MagicMock()
    mock_version_response = MagicMock()
    mock_version_response.json.return_value = {"version": 42}

    with patch("httpx.AsyncClient") as mock_client_class:
        mock_client = AsyncMock()
        mock_client_class.return_value.__aenter__.return_value = mock_client
        mock_client.post.return_value = mock_deploy_response
        mock_client.get.return_value = mock_version_response

        version = await client.deploy_configuration("global\n    daemon")

    # Check deployment call
    assert mock_client.post.call_count == 1
    deploy_call = mock_client.post.call_args
    assert deploy_call[1]["content"] == "global\n    daemon"
    assert deploy_call[1]["params"]["force_reload"] == "true"

    # Check version retrieval call
    mock_client.get.assert_called_once_with(
        "http://10.0.1.5:5555/v2/services/haproxy/configuration/version"
    )

    assert version == "42"


@pytest.mark.asyncio
async def test_dataplane_client_deploy_configuration_failure():
    """Test configuration deployment failure."""
    client = DataplaneClient("http://10.0.1.5:5555/v2")

    with patch("httpx.AsyncClient") as mock_client_class:
        mock_client = AsyncMock()
        mock_client_class.return_value.__aenter__.return_value = mock_client
        mock_client.post.side_effect = httpx.HTTPStatusError(
            "500 Internal Server Error",
            request=MagicMock(),
            response=MagicMock(text="Deployment failed"),
        )

        with pytest.raises(DataplaneAPIError, match="Configuration deployment failed"):
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
        dataplane_url="http://10.0.1.6:5555/v2",
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
        dataplane_url="http://10.0.1.6:5555/v2",
        is_validation_sidecar=True,
    )

    production_instance = HAProxyInstance(
        pod=mock_prod_pod,
        dataplane_url="http://10.0.1.5:5555/v2",
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
    instance = HAProxyInstance(pod=mock_pod, dataplane_url="http://10.0.1.5:5555/v2")

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

    instance = HAProxyInstance(pod=mock_pod, dataplane_url="http://10.0.1.5:5555/v2")

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

    instance = HAProxyInstance(pod=mock_pod, dataplane_url="http://10.0.1.5:5555/v2")

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

    instance = HAProxyInstance(pod=mock_pod, dataplane_url="http://10.0.1.5:5555/v2")

    result = await synchronizer._deploy_to_instance(mock_client, instance, "config")

    assert result.success is False
    assert result.instance == instance
    assert result.config_version is None
    assert result.error == "Deploy failed"
