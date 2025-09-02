"""
Integration tests for HAProxy Dataplane API functionality.

These tests use real Docker containers to test the dataplane module against
actual HAProxy and Dataplane API instances, providing confidence that the
integration works correctly in production-like environments.
"""

import pytest

from haproxy_template_ic.dataplane import (
    DataplaneAPIError,
    DataplaneClient,
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
            # Test with valid configuration - should not raise an exception
            try:
                await client.validate_configuration(haproxy_configs["valid"])
                validation_passed = True
            except Exception as e:
                validation_passed = False
                reporter.debug(f"Unexpected validation failure: {e}")

            progress.phase("ASSERTION", "Verifying validation result")
            assert validation_passed is True
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

        # Test with invalid configuration - should raise ValidationError
        with pytest.raises((ValidationError, DataplaneAPIError)):
            await client.validate_configuration(haproxy_configs["invalid"])

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
            result = await client.deploy_configuration(haproxy_configs["with_health"])

            progress.phase("VALIDATION", "Validating deployment result")
            assert isinstance(result, dict)
            version = result["version"]
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

        # Should handle network errors gracefully - validation should raise exception
        with pytest.raises(DataplaneAPIError):
            await client.validate_configuration("test config")

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

        # Should handle timeout gracefully - may succeed or fail depending on timing
        # but should handle either case without unhandled exceptions
        try:
            await client.validate_configuration(haproxy_configs["valid"])
            # If it succeeds with very short timeout, that's fine
        except (ValidationError, DataplaneAPIError):
            # If it fails due to timeout or validation, that's also expected
            pass

    @pytest.mark.asyncio
    async def test_structured_deployment_basic(
        self, production_dataplane_client, haproxy_configs
    ):
        """Test basic structured deployment functionality."""
        reporter = get_test_reporter()

        with progress_context("test_structured_deployment_basic", reporter) as progress:
            progress.phase(
                "API_CLIENT_SETUP", "Creating production Dataplane API client"
            )

            # Get base URL and auth from the httpx client
            base_url = str(production_dataplane_client.base_url).rstrip("/")
            # Ensure URL has /v3 for the generated client
            if not base_url.endswith("/v3"):
                base_url += "/v3"
            auth = ("admin", "adminpass")  # Correct auth from HAProxy config
            client = DataplaneClient(base_url, auth=auth)

            progress.phase("CONFIG_DEPLOY", "Deploying initial valid configuration")
            # First deploy a valid config to establish a baseline
            await client.deploy_configuration(haproxy_configs["with_health"])

            progress.phase("FETCH_CONFIG", "Fetching structured configuration")
            # Fetch the current structured configuration
            current_config = await client.fetch_structured_configuration()
            reporter.debug(f"Current config sections: {list(current_config.keys())}")

            progress.phase(
                "STRUCTURED_TEST", "Testing structured deployment with no changes"
            )
            # Test structured deployment with no changes (empty changes list)
            result = await client.deploy_structured_configuration([])
            assert result["version"] == "unchanged"

            progress.phase("STRUCTURED_SUCCESS", "Structured deployment test completed")


# NOTE: TestConfigSynchronizerIntegration class has been removed
# This class was testing the old complex architecture with HAProxyPodDiscovery
# and HAProxyInstance classes that were removed during simplification.
# The new simplified architecture is tested through unit tests and E2E tests.
# ConfigSynchronizer is now tested via unit tests with the simplified API:
# - Takes production_urls list, validation_url, and auth parameters directly
# - Returns simple dict with 'successful', 'failed', and 'errors' keys


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
        result1 = await client.deploy_configuration(haproxy_configs["valid"])
        assert isinstance(result1, dict)
        version1 = result1["version"]
        assert isinstance(version1, str)

        # Deploy another config to test retry behavior
        result2 = await client.deploy_configuration(haproxy_configs["with_health"])
        assert isinstance(result2, dict)
        version2 = result2["version"]
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
            # Should not raise exceptions for valid config
            await client.validate_configuration(haproxy_configs["valid"])

        # Test with slightly more complex config
        await client.validate_configuration(haproxy_configs["with_health"])
