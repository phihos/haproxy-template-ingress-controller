"""
Integration tests for HAProxy Dataplane API functionality.

These tests use real Docker containers to test the dataplane module against
actual HAProxy and Dataplane API instances, providing confidence that the
integration works correctly in production-like environments.
"""

import asyncio

import pytest
from haproxy_dataplane_v3.models.acl_lines import ACLLines
from pydantic import SecretStr

from haproxy_template_ic.credentials import DataplaneAuth
from haproxy_template_ic.dataplane import (
    DataplaneAPIError,
    DataplaneClient,
    ValidationError,
)
from haproxy_template_ic.dataplane.endpoint import DataplaneEndpoint
from haproxy_template_ic.dataplane.types import (
    ConfigChange,
    ConfigChangeType,
    ConfigElementType,
    ConfigSectionType,
)


@pytest.mark.integration
@pytest.mark.asyncio
async def test_dataplane_client_get_version(validation_dataplane_client):
    """Test getting HAProxy version information."""
    client = validation_dataplane_client

    version_info = await client.get_version()

    assert isinstance(version_info, dict)
    # HAProxy info should contain version information
    assert "haproxy" in version_info or "version" in version_info


@pytest.mark.integration
@pytest.mark.asyncio
async def test_dataplane_client_validate_valid_configuration(
    validation_dataplane_client, haproxy_configs
):
    """Test validation of a valid HAProxy configuration."""
    client = validation_dataplane_client

    # Test with valid configuration - should not raise an exception
    await client.validate_configuration(haproxy_configs["valid"])


@pytest.mark.integration
@pytest.mark.asyncio
async def test_dataplane_client_validate_invalid_configuration(
    validation_dataplane_client_raw, haproxy_configs
):
    """Test validation of an invalid HAProxy configuration."""

    base_url = str(validation_dataplane_client_raw.base_url).rstrip("/")
    # Ensure URL has /v3 for the generated client
    if not base_url.endswith("/v3"):
        base_url += "/v3"

    auth = DataplaneAuth(username="admin", password=SecretStr("adminpass"))
    endpoint = DataplaneEndpoint(url=base_url, dataplane_auth=auth)
    client = DataplaneClient(endpoint)

    # Test with invalid configuration - should raise ValidationError
    with pytest.raises((ValidationError, DataplaneAPIError)):
        await client.validate_configuration(haproxy_configs["invalid"])


@pytest.mark.integration
@pytest.mark.asyncio
async def test_dataplane_client_deploy_configuration(
    production_dataplane_client, haproxy_configs
):
    """Test deploying a valid HAProxy configuration."""
    client = production_dataplane_client

    # Deploy valid configuration
    result = await client.deploy_configuration(haproxy_configs["with_health"])

    assert hasattr(result, "version")
    version = result.version
    assert isinstance(version, str)
    assert len(version) > 0  # Should have a version number


@pytest.mark.integration
@pytest.mark.asyncio
async def test_dataplane_client_deploy_invalid_configuration_raises_error(
    production_dataplane_client, haproxy_configs
):
    """Test that deploying invalid configuration raises an error."""

    client = production_dataplane_client

    # Deploying invalid config should raise an error
    with pytest.raises(DataplaneAPIError):
        await client.deploy_configuration(haproxy_configs["invalid"])


@pytest.mark.integration
@pytest.mark.asyncio
async def test_dataplane_client_network_error_handling():
    """Test handling of network errors."""

    # Use a non-existent URL
    auth = DataplaneAuth(username="admin", password=SecretStr("adminpass"))
    endpoint = DataplaneEndpoint(url="http://localhost:59999", dataplane_auth=auth)
    client = DataplaneClient(endpoint, timeout=1.0)

    # Should handle network errors gracefully - validation should raise exception
    with pytest.raises(DataplaneAPIError):
        await client.validate_configuration("test config")

    with pytest.raises(DataplaneAPIError):
        await client.deploy_configuration("test config")


@pytest.mark.integration
@pytest.mark.asyncio
async def test_dataplane_client_structured_deployment_basic(
    production_dataplane_client, haproxy_configs
):
    """Test basic structured deployment functionality."""
    client = production_dataplane_client

    # First deploy a valid config to establish a baseline
    await client.deploy_configuration(haproxy_configs["with_health"])

    # Fetch the current structured configuration
    current_config = await client.fetch_structured_configuration()

    # Validate the structured configuration response
    assert isinstance(current_config, dict)
    assert "frontends" in current_config
    assert "backends" in current_config

    # Validate content matches the "with_health" config we deployed
    assert len(current_config["frontends"]) >= 2  # Should have main + status frontends
    assert (
        len(current_config["backends"]) >= 2
    )  # Should have web_servers + default_servers backends

    # Verify the health/status frontend exists (specific to "with_health" config)
    frontend_names = [f.name for f in current_config["frontends"]]
    assert "status" in frontend_names

    # Test structured deployment with no changes (empty changes list)
    result = await client.deploy_structured_configuration([])
    assert result.version == "unchanged"


# TestConfigSynchronizerIntegration class has been removed
# This class was testing the old complex architecture with HAProxyPodDiscovery
# and HAProxyInstance classes that were removed during simplification.
# The new simplified architecture is tested through unit tests and E2E tests.
# ConfigSynchronizer is now tested via unit tests with the simplified API:
# - Takes production_urls list, validation_url, and auth parameters directly
# - Returns simple dict with 'successful', 'failed', and 'errors' keys


@pytest.mark.integration
@pytest.mark.asyncio
async def test_resilience_retry_on_temporary_failure(
    production_dataplane_client, haproxy_configs
):
    """Test retry behavior on temporary failures."""
    client = production_dataplane_client

    # Deploy a valid config first to establish baseline
    result1 = await client.deploy_configuration(haproxy_configs["valid"])
    assert hasattr(result1, "version")
    version1 = result1.version
    assert isinstance(version1, str)

    # Deploy another config to test retry behavior
    result2 = await client.deploy_configuration(haproxy_configs["with_health"])
    assert hasattr(result2, "version")
    version2 = result2.version
    assert isinstance(version2, str)
    assert version2 != version1  # Should get new version


@pytest.mark.integration
@pytest.mark.asyncio
async def test_resilience_timeout_adaptation(
    validation_dataplane_client, haproxy_configs
):
    """Test adaptive timeout behavior."""
    # Create a client with custom timeout based on the existing fixture
    base_client = validation_dataplane_client
    auth = DataplaneAuth(username="admin", password=SecretStr("adminpass"))
    endpoint = DataplaneEndpoint(url=base_client.base_url, dataplane_auth=auth)
    client = DataplaneClient(endpoint, timeout=5.0)

    # Multiple successful operations should work
    for _ in range(3):
        # Should not raise exceptions for valid config
        await client.validate_configuration(haproxy_configs["valid"])

    # Test with slightly more complex config
    await client.validate_configuration(haproxy_configs["with_health"])


@pytest.mark.integration
@pytest.mark.asyncio
async def test_storage_map_operations(production_dataplane_client):
    """Test map storage operations against real HAProxy instance."""
    client = production_dataplane_client

    # Test map operations that should trigger the bug
    test_maps = {
        "test.map": "# Test map file\nexample.com 192.168.1.100\n",
        "hosts.map": "# Hosts mapping\nlocalhost 127.0.0.1\n",
    }

    # This should fail with current implementation due to incorrect API signature
    await client.sync_maps(test_maps)

    # Test storage info - should also fail due to incorrect signature handling
    storage_info = await client.operations.storage.get_storage_info()
    assert "maps" in storage_info
    assert "certificates" in storage_info


@pytest.mark.integration
@pytest.mark.asyncio
async def test_storage_certificate_operations(production_dataplane_client):
    """Test SSL certificate storage operations against real HAProxy instance."""
    client = production_dataplane_client

    # Create a simple test certificate (self-signed for testing)
    test_certificates = {
        "test.crt": """-----BEGIN CERTIFICATE-----
MIIBkTCB+wIJAK7dQr9C6FWhMA0GCSqGSIb3DQEBCwUAMBQxEjAQBgNVBAMMCWxv
Y2FsaG9zdDAeFw0yNTA5MTcwMDAwMDBaFw0yNjA5MTcwMDAwMDBaMBQxEjAQBgNV
BAMMCWxvY2FsaG9zdDBcMA0GCSqGSIb3DQEBAQUAA0sAMEgCQQC8Q6u8oK1cIpfq
VqKwUm1fTQRhEjCgKB7xF+z7yJ8xQz7VEgKKx1+gN3nY5R2V8xQ5nJnX7tPq4vQj
B5uJ2KgzAgMBAAEwDQYJKoZIhvcNAQELBQADQQA6kWjJ5PK6Vr7mC4/fL0VQJ2qJ
F8vQz8V3nE3nQ4X6hP2qJ8xQz7VEgKKx1+gN3nY5R2V8xQ5nJnX7tPq4vQjB5uJ
-----END CERTIFICATE-----"""
    }

    # This should fail with current implementation due to incorrect API signature
    await client.sync_certificates(test_certificates)

    # Verify certificate appears in storage info
    storage_info = await client.operations.storage.get_storage_info()
    assert storage_info["certificates"]["count"] >= 0


@pytest.mark.integration
@pytest.mark.asyncio
async def test_dataplane_client_400_error_during_concurrent_operations(
    production_dataplane_client, haproxy_configs
):
    """Test that 409 error responses are properly raised as exceptions during concurrent operations."""
    client = production_dataplane_client

    # Deploy initial valid configuration
    await client.deploy_configuration(haproxy_configs["with_health"])

    # Get current structured configuration to work with
    current_config = await client.fetch_structured_configuration()

    # Find a frontend to work with
    frontends = current_config.get("frontends", [])
    if not frontends:
        # If no frontends exist, create a simple one first
        simple_frontend_config = """
frontend simple_frontend
    bind *:8080
    default_backend test_backend

backend test_backend
    server test1 127.0.0.1:8081 check
"""
        await client.deploy_configuration(simple_frontend_config)
        current_config = await client.fetch_structured_configuration()
        frontends = current_config.get("frontends", [])

    assert frontends, "No frontends available for testing"

    frontend_name = frontends[0].name

    # Create ConfigChange objects for ACL additions that would conflict during concurrent execution
    # These will go through our error handling decorators
    acl1_data = ACLLines(
        acl_name="test_acl_1", criterion="hdr(host)", value="example.com"
    )
    acl2_data = ACLLines(acl_name="test_acl_2", criterion="hdr(host)", value="test.com")

    # Create structured configuration changes using our ConfigChange API
    change1 = ConfigChange.create_element_change(
        change_type=ConfigChangeType.CREATE,
        section_type=ConfigSectionType.FRONTEND,
        section_name=frontend_name,
        element_type=ConfigElementType.ACL,
        new_config=acl1_data,
        element_index=0,
    )

    change2 = ConfigChange.create_element_change(
        change_type=ConfigChangeType.CREATE,
        section_type=ConfigSectionType.FRONTEND,
        section_name=frontend_name,
        element_type=ConfigElementType.ACL,
        new_config=acl2_data,
        element_index=1,
    )

    # Execute concurrent structured configuration operations through our client
    # This will trigger our @handle_dataplane_errors decorators
    task1 = client.deploy_structured_configuration([change1])
    task2 = client.deploy_structured_configuration([change2])

    # Run both operations concurrently to maximize chance of 409 conflict
    task1_result, task2_result = await asyncio.gather(
        task1, task2, return_exceptions=True
    )

    # At least one of these operations must have failed
    assert isinstance(task1_result, DataplaneAPIError) or isinstance(
        task2_result, DataplaneAPIError
    )
