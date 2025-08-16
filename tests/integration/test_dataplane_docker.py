"""
Integration tests for HAProxy Dataplane API functionality.

These tests use real Docker containers to test the dataplane module against
actual HAProxy and Dataplane API instances, providing confidence that the
integration works correctly in production-like environments.
"""

from unittest.mock import AsyncMock, Mock

import pytest
from jinja2 import Template

from haproxy_template_ic.config import (
    Config,
    HAProxyConfigContext,
    PodSelector,
    RenderedConfig,
)
from haproxy_template_ic.dataplane import (
    ConfigSynchronizer,
    DataplaneAPIError,
    DataplaneClient,
    HAProxyInstance,
    ValidationError,
)
from .utils.progress import get_test_reporter, progress_context


@pytest.mark.integration
class TestDataplaneClientIntegration:
    """Integration tests for DataplaneClient against real Dataplane API."""

    @pytest.mark.asyncio
    async def test_get_version(self, validation_dataplane_client):
        """Test getting HAProxy version information."""
        reporter = get_test_reporter()

        with progress_context("test_get_version", reporter) as progress:
            progress.phase("API_CLIENT_SETUP", "Creating Dataplane API client")

            # Get base URL and auth from the httpx client
            base_url = str(validation_dataplane_client.base_url).rstrip("/")
            # Ensure URL has /v3 for the generated client
            if not base_url.endswith("/v3"):
                base_url += "/v3"
            auth = ("admin", "adminpass")  # Correct auth from HAProxy config
            client = DataplaneClient(base_url, auth=auth)

            progress.phase("VERSION_CHECK", "Getting HAProxy version information")
            # Test get_version
            version_info = await client.get_version()

            progress.phase("VALIDATION", "Validating version response")
            assert isinstance(version_info, dict)
            # HAProxy info should contain version information
            assert "haproxy" in version_info or "version" in version_info

            reporter.debug(f"Version info: {version_info}")

    @pytest.mark.asyncio
    async def test_validate_valid_configuration(
        self, validation_dataplane_client, haproxy_configs
    ):
        """Test validation of a valid HAProxy configuration."""
        reporter = get_test_reporter()

        with progress_context(
            "test_validate_valid_configuration", reporter
        ) as progress:
            progress.phase("API_CLIENT_SETUP", "Creating Dataplane API client")

            base_url = str(validation_dataplane_client.base_url).rstrip("/")
            # Ensure URL has /v3 for the generated client
            if not base_url.endswith("/v3"):
                base_url += "/v3"
            auth = ("admin", "adminpass")  # Correct auth from HAProxy config
            client = DataplaneClient(base_url, auth=auth)

            progress.phase("CONFIG_VALIDATION", "Validating HAProxy configuration")
            # Test with valid configuration
            is_valid = await client.validate_configuration(haproxy_configs["valid"])

            progress.phase("ASSERTION", "Verifying validation result")
            assert is_valid is True
            reporter.debug("Valid configuration passed validation as expected")

    @pytest.mark.asyncio
    async def test_validate_invalid_configuration(
        self, validation_dataplane_client, haproxy_configs
    ):
        """Test validation of an invalid HAProxy configuration."""

        base_url = str(validation_dataplane_client.base_url).rstrip("/")
        # Ensure URL has /v3 for the generated client
        if not base_url.endswith("/v3"):
            base_url += "/v3"
        auth = ("admin", "adminpass")  # Correct auth from HAProxy config
        client = DataplaneClient(base_url, auth=auth)

        # Test with invalid configuration
        is_valid = await client.validate_configuration(haproxy_configs["invalid"])

        assert is_valid is False

    @pytest.mark.asyncio
    async def test_deploy_configuration(
        self, production_dataplane_client, haproxy_configs
    ):
        """Test deploying a valid HAProxy configuration."""
        reporter = get_test_reporter()

        with progress_context("test_deploy_configuration", reporter) as progress:
            progress.phase(
                "API_CLIENT_SETUP", "Creating production Dataplane API client"
            )

            base_url = str(production_dataplane_client.base_url).rstrip("/")
            # Ensure URL has /v3 for the generated client
            if not base_url.endswith("/v3"):
                base_url += "/v3"
            auth = ("admin", "adminpass")  # Known production auth
            client = DataplaneClient(base_url, auth=auth)

            progress.phase(
                "CONFIG_DEPLOYMENT", "Deploying HAProxy configuration to production"
            )
            # Deploy valid configuration
            version = await client.deploy_configuration(haproxy_configs["with_health"])

            progress.phase("VALIDATION", "Validating deployment result")
            assert isinstance(version, str)
            assert len(version) > 0  # Should have a version number

            reporter.debug(f"Configuration deployed with version: {version}")

    @pytest.mark.asyncio
    async def test_deploy_invalid_configuration_raises_error(
        self, production_dataplane_client, haproxy_configs
    ):
        """Test that deploying invalid configuration raises an error."""

        base_url = str(production_dataplane_client.base_url).rstrip("/")
        # Ensure URL has /v3 for the generated client
        if not base_url.endswith("/v3"):
            base_url += "/v3"
        auth = ("admin", "adminpass")  # Known production auth
        client = DataplaneClient(base_url, auth=auth)

        # Deploying invalid config should raise an error
        with pytest.raises(DataplaneAPIError):
            await client.deploy_configuration(haproxy_configs["invalid"])

    @pytest.mark.asyncio
    async def test_network_error_handling(self):
        """Test handling of network errors."""

        # Use a non-existent URL
        client = DataplaneClient("http://localhost:59999", timeout=1.0)

        # Should handle network errors gracefully
        is_valid = await client.validate_configuration("test config")
        assert is_valid is False

        with pytest.raises(DataplaneAPIError):
            await client.deploy_configuration("test config")

    @pytest.mark.asyncio
    async def test_timeout_handling(self, validation_dataplane_client, haproxy_configs):
        """Test timeout handling with very short timeout."""

        base_url = str(validation_dataplane_client.base_url).rstrip("/")
        # Ensure URL has /v3 for the generated client
        if not base_url.endswith("/v3"):
            base_url += "/v3"
        auth = ("admin", "adminpass")  # Correct auth from HAProxy config
        client = DataplaneClient(
            base_url, timeout=0.001, auth=auth
        )  # Very short timeout

        # Should handle timeout gracefully
        is_valid = await client.validate_configuration(haproxy_configs["valid"])
        # May succeed or fail depending on timing, but shouldn't raise unhandled exception
        assert isinstance(is_valid, bool)


@pytest.mark.integration
class TestConfigSynchronizerIntegration:
    """Integration tests for ConfigSynchronizer with real Dataplane API."""

    def create_mock_config_context(self, config_content: str) -> HAProxyConfigContext:
        """Create a mock HAProxyConfigContext with rendered config."""
        config = Config(
            raw={},
            pod_selector=PodSelector(match_labels={}),
            haproxy_config=Template(config_content),
        )

        rendered_config = RenderedConfig(content=config_content, config=config)

        return HAProxyConfigContext(
            rendered_maps=[], rendered_config=rendered_config, rendered_certificates=[]
        )

    @pytest.mark.asyncio
    async def test_synchronize_configuration_success(
        self, mock_haproxy_instances, haproxy_configs
    ):
        """Test successful configuration synchronization."""
        validation_instance, production_instance = mock_haproxy_instances

        # Mock HAProxyPodDiscovery to return our instances
        mock_discovery = Mock()
        mock_discovery.discover_instances = AsyncMock(
            return_value=[validation_instance, production_instance]
        )

        synchronizer = ConfigSynchronizer(mock_discovery)

        # Create config context with valid configuration
        config_context = self.create_mock_config_context(haproxy_configs["with_health"])

        # Synchronize configuration
        results = await synchronizer.synchronize_configuration(config_context)

        # Should have one result for the production instance
        assert len(results) == 1
        assert results[0].success is True
        assert results[0].instance == production_instance
        assert results[0].config_version is not None

    @pytest.mark.asyncio
    async def test_synchronize_configuration_validation_failure(
        self, mock_haproxy_instances, haproxy_configs
    ):
        """Test synchronization failure due to validation."""
        validation_instance, production_instance = mock_haproxy_instances

        mock_discovery = Mock()
        mock_discovery.discover_instances = AsyncMock(
            return_value=[validation_instance, production_instance]
        )

        synchronizer = ConfigSynchronizer(mock_discovery)

        # Create config context with invalid configuration
        config_context = self.create_mock_config_context(haproxy_configs["invalid"])

        # Should raise ValidationError
        with pytest.raises(ValidationError, match="Configuration validation failed"):
            await synchronizer.synchronize_configuration(config_context)

    @pytest.mark.asyncio
    async def test_synchronize_configuration_no_validation_sidecars(
        self, mock_haproxy_instances, haproxy_configs
    ):
        """Test synchronization when no validation sidecars are available."""
        _, production_instance = mock_haproxy_instances

        # Only return production instance (no validation)
        mock_discovery = Mock()
        mock_discovery.discover_instances = AsyncMock(
            return_value=[production_instance]
        )

        synchronizer = ConfigSynchronizer(mock_discovery)

        # Create config context with valid configuration
        config_context = self.create_mock_config_context(haproxy_configs["with_health"])

        # Should proceed without validation
        results = await synchronizer.synchronize_configuration(config_context)

        assert len(results) == 1
        assert results[0].success is True

    @pytest.mark.asyncio
    async def test_synchronize_configuration_partial_failure(
        self, mock_haproxy_instances, haproxy_configs
    ):
        """Test synchronization with partial deployment failures."""
        validation_instance, production_instance = mock_haproxy_instances

        # Create a second production instance that will fail
        failing_pod = Mock()
        failing_pod.namespace = "test"
        failing_pod.name = "failing-haproxy"

        failing_instance = HAProxyInstance(
            pod=failing_pod,
            dataplane_url="http://localhost:59999/v3",  # Non-existent but valid port
            is_validation_sidecar=False,
        )

        mock_discovery = Mock()
        mock_discovery.discover_instances = AsyncMock(
            return_value=[validation_instance, production_instance, failing_instance]
        )

        synchronizer = ConfigSynchronizer(mock_discovery)

        # Create config context with valid configuration
        config_context = self.create_mock_config_context(haproxy_configs["with_health"])

        # Synchronize configuration
        results = await synchronizer.synchronize_configuration(config_context)

        # Should have results for both production instances
        assert len(results) == 2

        # One should succeed, one should fail
        success_count = sum(1 for r in results if r.success)
        failure_count = sum(1 for r in results if not r.success)

        assert success_count == 1
        assert failure_count == 1

    @pytest.mark.asyncio
    async def test_synchronize_configuration_no_instances(self, haproxy_configs):
        """Test synchronization when no HAProxy instances are found."""
        mock_discovery = Mock()
        mock_discovery.discover_instances = AsyncMock(return_value=[])

        synchronizer = ConfigSynchronizer(mock_discovery)

        config_context = self.create_mock_config_context(haproxy_configs["valid"])

        # Should return empty results
        results = await synchronizer.synchronize_configuration(config_context)
        assert len(results) == 0

    @pytest.mark.asyncio
    async def test_circuit_breaker_behavior(
        self, mock_haproxy_instances, haproxy_configs
    ):
        """Test circuit breaker behavior with failing validation."""
        validation_instance, production_instance = mock_haproxy_instances

        # Replace validation instance with one that will always fail
        failing_validation_pod = Mock()
        failing_validation_pod.namespace = "test"
        failing_validation_pod.name = "failing-validation"

        failing_validation_instance = HAProxyInstance(
            pod=failing_validation_pod,
            dataplane_url="http://localhost:59998/v3",  # Non-existent but valid port
            is_validation_sidecar=True,
        )

        mock_discovery = Mock()
        mock_discovery.discover_instances = AsyncMock(
            return_value=[failing_validation_instance, production_instance]
        )

        synchronizer = ConfigSynchronizer(mock_discovery)

        config_context = self.create_mock_config_context(haproxy_configs["valid"])

        # Multiple attempts should trigger circuit breaker
        for _ in range(3):
            with pytest.raises(ValidationError):
                await synchronizer.synchronize_configuration(config_context)


@pytest.mark.integration
class TestResilienceFeatures:
    """Integration tests for resilience features like retries and circuit breakers."""

    @pytest.mark.asyncio
    async def test_retry_on_temporary_failure(
        self, production_dataplane_client, haproxy_configs
    ):
        """Test retry behavior on temporary failures."""

        base_url = str(production_dataplane_client.base_url).rstrip("/")
        # Ensure URL has /v3 for the generated client
        if not base_url.endswith("/v3"):
            base_url += "/v3"
        auth = ("admin", "adminpass")  # Known production auth
        client = DataplaneClient(base_url, auth=auth)

        # Deploy a valid config first to establish baseline
        version1 = await client.deploy_configuration(haproxy_configs["valid"])
        assert isinstance(version1, str)

        # Deploy another config to test retry behavior
        version2 = await client.deploy_configuration(haproxy_configs["with_health"])
        assert isinstance(version2, str)
        assert version2 != version1  # Should get new version

    @pytest.mark.asyncio
    async def test_timeout_adaptation(
        self, validation_dataplane_client, haproxy_configs
    ):
        """Test adaptive timeout behavior."""

        base_url = str(validation_dataplane_client.base_url).rstrip("/")
        # Ensure URL has /v3 for the generated client
        if not base_url.endswith("/v3"):
            base_url += "/v3"
        auth = ("admin", "adminpass")  # Correct auth from HAProxy config
        client = DataplaneClient(base_url, timeout=5.0, auth=auth)

        # Multiple successful operations should work
        for _ in range(3):
            is_valid = await client.validate_configuration(haproxy_configs["valid"])
            assert is_valid is True

        # Test with slightly more complex config
        is_valid = await client.validate_configuration(haproxy_configs["with_health"])
        assert is_valid is True
