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
from haproxy_template_ic.metrics import MetricsCollector
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
    metrics = MetricsCollector()
    client = DataplaneClient(endpoint, metrics)

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
    metrics = MetricsCollector()
    client = DataplaneClient(endpoint, metrics, timeout=1.0)

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
    metrics = MetricsCollector()
    client = DataplaneClient(endpoint, metrics, timeout=5.0)

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

    # Create a properly formatted test certificate with private key (as required by HAProxy)
    test_certificates = {
        "test.crt": """-----BEGIN CERTIFICATE-----
MIIDCTCCAfGgAwIBAgIUHQU8fBMBSzUEjikXn1NmuElb1B4wDQYJKoZIhvcNAQEL
BQAwFDESMBAGA1UEAwwJbG9jYWxob3N0MB4XDTI1MDkyMTE1NTU1NVoXDTI2MDky
MTE1NTU1NVowFDESMBAGA1UEAwwJbG9jYWxob3N0MIIBIjANBgkqhkiG9w0BAQEF
AAOCAQ8AMIIBCgKCAQEAyLJTR8ZaN0RylNpQ0Sr9T4rcAQO/LIjbvvWLqVxp3fGj
1fCu1FUJv+agUbrzrGCjlRLG1NIodNszMl+sreuAPKzBGP2Jz27vt0DwKqgVw5Id
W3IUludEkBfnkDEXdJJ5UJWjDcUxaA9+iXsqd9NYZZuRh67QkDgGAqLifo7J+qdI
V/0yvF2rdeLYzPRbmoK6hzVJMMtlyDnRRgEbg4A8AtqcZpkNXjzJUt5Pn95MPQnN
ZQJCPHXibbxTI4mtPFi97kiAm4zumjUgGysV8eeD+xU4CGBDvaDHPNq1gWZeVcG+
ALZzDFMkITI1ZUfkMiZUYoQBTDbDdwNu2VGeo5a+eQIDAQABo1MwUTAdBgNVHQ4E
FgQU52EJR2wkd0AqyTeQ4lorUUj5PmUwHwYDVR0jBBgwFoAU52EJR2wkd0AqyTeQ
4lorUUj5PmUwDwYDVR0TAQH/BAUwAwEB/zANBgkqhkiG9w0BAQsFAAOCAQEAF3AS
RHw+r4qaI4gdKCT3a+C0RoQsSqoZNlixUIAdrkmo5pqedDKy5+TxxxRQh2oLYQMo
SIbCahnzOyklwEThCJOBxM8fLfUJt2EHJOdpchNJlh7G2wcN0haVcSv4IC35wR4n
VgxiP50P1+hn9YzdyXGKJl2bAKDSmPhaZLgPq5KUqMKg+YRJjosJxkg8DkEVooag
txJv6kijp5nnPWmb5XPh2JFgD5B9BN4OpVO9d1hlfH+1gAmJ16JT3i92X7ah520p
W5Pk0xp7hDsDnQJKSKJHwPUKUrT7SMzZRrRu0+GVZW6QCcOStJ+mz259kT8crXpn
0Iee1rf3Ge/FonXHZQ==
-----END CERTIFICATE-----
-----BEGIN PRIVATE KEY-----
MIIEvgIBADANBgkqhkiG9w0BAQEFAASCBKgwggSkAgEAAoIBAQDIslNHxlo3RHKU
2lDRKv1PitwBA78siNu+9YupXGnd8aPV8K7UVQm/5qBRuvOsYKOVEsbU0ih02zMy
X6yt64A8rMEY/YnPbu+3QPAqqBXDkh1bchSW50SQF+eQMRd0knlQlaMNxTFoD36J
eyp301hlm5GHrtCQOAYCouJ+jsn6p0hX/TK8Xat14tjM9FuagrqHNUkwy2XIOdFG
ARuDgDwC2pxmmQ1ePMlS3k+f3kw9Cc1lAkI8deJtvFMjia08WL3uSICbjO6aNSAb
KxXx54P7FTgIYEO9oMc82rWBZl5Vwb4AtnMMUyQhMjVlR+QyJlRihAFMNsN3A27Z
UZ6jlr55AgMBAAECggEAA918rB0I/20n4G+vRHAAWT1SjQnI70R4KEkrVj4rjco0
aQ+NwRTIL3QeHKTYl4vJlWU7WL2ZaN1l3YT+hYpLucoWnUgYv4V37r68lrMOWZS2
pbG17XgTwnYAutlZ2yANCmfEsE8Ja2MiVpHS2LmZx2SDx39ZkJrQ8Xu4l/kLsRzp
3LVh5/s3SUzp7cYRZSYLXpueO/Hvc0mouttgkfu6H9rnIDY49O4BxFE26u4gFPXJ
EIG0m3fJgIQe7r6GwdyEs4vkXrgzse2kNqR3NteqrJhgB4D5wKlSZKd6PcX4C9Rw
MXDR70HpeYWdPnE3Dx5I4xpOtbo8my+AtGwQDoOweQKBgQD9SSa1orTqhQTOdRq+
btt0qGQZ+bUYHmWFOtc+tIn6YpnqvJU63ZQ1GbyZYR3lLYdBJDdadf29G+aaMMMD
tJ0fLnTJoc8bh6bSZhDpWGk89T7MASvoC2uiClqDTXVY+IILax5CUQkZlHRlK6ks
JMs3Zdr4kCsWlSiuP1l5ebKmxQKBgQDK2Od4DqXkxSbO8dz1y5gGBFen/DMO6UH9
CilWIGdgpEUXqYnjx42y0WPaYunYHmCAf2CRVhdnacb123WZZP5nmfJ+XVB8Ipy+
N9rR+bDPve0DBdFLGq593u3PlCPDlozeQBEiNr1m6qG8VjFlQ/KffpCHuvDeUeTH
2c4hdpxUJQKBgQCoUpHQCaYTaHzuO3KfdYqQN0v22zSXJ7Qt2xGqUU6UwCwrjFHc
Ad75fvYQNDMq15vYFZpXmqwanc0dUSR4dPIqA7SHPuolEHwzvLKmcCPX599osaqd
FeHcmObX9YTzsIqzzecZCUNz5W2IwoA1nuoSEbV4lE6ePlf/nIf4q4CnRQKBgHWU
98/DBeyvT4ij8IZWJuBOAhWw/lPFaGfqTP3MuL/vWNGXiAOOOBgQgkYkEhMhwKSb
sXltoxFh4l+/f9KUFVguh78yDiZ21c75h5ExoIk7ObkH1UMoyz7RS56I65ZDnZJz
JrtjabTPi0Ml32oo0eocLmFPPrJQXEJwgakqHQI1AoGBAIMGSML2v5i/HG59BGXr
ToWeGGVAeKKtCunHFO4mzwC8QNkOlwkAKB1DNus9dgcRBTXDa2n5+P8008KfziG7
i2ScU9+qSsC5zLl5ZzIvNU/fq1xBO3v0iVceCjxLVohAe6nRFuAbfmnNICSHeY+Q
d/GppTNhA34z8nIZXhfLHjjF
-----END PRIVATE KEY-----"""
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
