"""
Unit tests for DataplaneClient functionality.

Tests the main DataplaneClient class and its delegation patterns.
"""

import pytest
from unittest.mock import patch

from haproxy_template_ic.dataplane import DataplaneClient
from haproxy_template_ic.dataplane.endpoint import DataplaneEndpoint
from tests.unit.conftest import (
    create_async_mock_coroutine,
    create_dataplane_endpoint_mock,
)
from tests.unit.dataplane.conftest import (
    create_dataplane_client,
)


@pytest.fixture
def client(test_endpoint):
    """Create DataplaneClient instance for testing."""
    from .conftest import create_dataplane_client

    return create_dataplane_client(test_endpoint)


def test_client_initialization_defaults(test_endpoint):
    """Test DataplaneClient initialization with defaults."""
    client = create_dataplane_client(test_endpoint)

    assert client.base_url == "http://localhost:5555/v3"
    assert client.operations is not None
    assert client.operations.endpoint.url == "http://localhost:5555/v3"


def test_client_initialization_custom(test_auth):
    """Test DataplaneClient initialization with custom parameters."""
    custom_endpoint = create_dataplane_endpoint_mock(
        url="https://api.example.com/v3",
        auth=test_auth,
    )
    client = create_dataplane_client(custom_endpoint, timeout=60)

    assert client.base_url == "https://api.example.com/v3"
    assert client.operations.endpoint.url == "https://api.example.com/v3"
    assert client.timeout == 60


def test_client_configuration_lazy_loading(client):
    """Test that client configuration is lazily loaded."""
    # Client should be created without immediately creating HTTP client
    assert client.operations is not None
    # Actual HTTP client creation happens when operations are called


@pytest.mark.asyncio
async def test_transaction_delegation(client):
    """Test that transaction methods delegate to operations."""
    with (
        patch.object(client.operations.transactions, "start") as mock_start,
        patch.object(client.operations.transactions, "commit") as mock_commit,
        patch.object(client.operations.transactions, "rollback") as mock_rollback,
    ):
        # Setup async mocks
        mock_start.return_value = create_async_mock_coroutine("txn-123")
        mock_commit.return_value = create_async_mock_coroutine({"status": "committed"})
        mock_rollback.return_value = create_async_mock_coroutine(None)

        # Test start_transaction delegation
        result = await client.start_transaction()
        assert result == "txn-123"
        mock_start.assert_called_once()

        # Test commit_transaction delegation
        await client.commit_transaction("txn-123")
        mock_commit.assert_called_once_with("txn-123")

        # Test rollback_transaction delegation
        await client.rollback_transaction("txn-123")
        mock_rollback.assert_called_once_with("txn-123")


@pytest.mark.asyncio
async def test_storage_delegation(client):
    """Test that storage methods delegate to storage API."""
    maps = {"geo.map": "US 1"}
    certificates = {"ssl.pem": "-----BEGIN CERTIFICATE-----"}

    with (
        patch.object(client.operations.storage, "sync_maps") as mock_sync_maps,
        patch.object(client.operations.storage, "sync_certificates") as mock_sync_certs,
    ):
        # Setup async mocks
        mock_sync_maps.return_value = create_async_mock_coroutine(None)
        mock_sync_certs.return_value = create_async_mock_coroutine(None)

        await client.sync_maps(maps)
        await client.sync_certificates(certificates)

        mock_sync_maps.assert_called_once_with(maps, {"create", "update", "delete"})
        mock_sync_certs.assert_called_once_with(
            certificates, {"create", "update", "delete"}
        )


@pytest.mark.asyncio
async def test_configuration_delegation(client):
    """Test that configuration methods delegate to operations."""
    config_content = "global\n    daemon"

    with (
        patch.object(client.operations, "validate_and_deploy") as mock_validate_deploy,
        patch.object(
            client.operations.validation, "validate_configuration"
        ) as mock_validate,
    ):
        # Setup async mocks
        mock_validate_deploy.return_value = create_async_mock_coroutine(
            {"validation": "success"}
        )
        mock_validate.return_value = create_async_mock_coroutine(None)

        # Test validate_and_deploy delegation
        await client.validate_and_deploy(config_content)
        mock_validate_deploy.assert_called_once_with(config_content)

        # Test validate_configuration delegation
        await client.validate_configuration(config_content)
        mock_validate.assert_called_once_with(config_content)


@pytest.mark.asyncio
async def test_info_delegation(client):
    """Test that info methods delegate to operations."""
    with (
        patch.object(client.operations, "get_cluster_info") as mock_get_cluster_info,
        patch.object(client.operations.validation, "get_version") as mock_get_version,
    ):
        # Setup async mocks
        mock_get_cluster_info.return_value = create_async_mock_coroutine(
            {"version": "3.1.0"}
        )
        mock_get_version.return_value = create_async_mock_coroutine(
            {"version": "3.1.0"}
        )

        await client.get_cluster_info()
        mock_get_cluster_info.assert_called_once()

        await client.get_version()
        mock_get_version.assert_called_once()


def test_client_url_normalization_on_init(test_auth):
    """Test that client normalizes URLs during initialization."""
    # URL without /v3 should be normalized via DataplaneEndpoint
    endpoint_without_v3 = DataplaneEndpoint(
        url="http://localhost:5555",
        dataplane_auth=test_auth,
    )
    from haproxy_template_ic.metrics import MetricsCollector

    metrics = MetricsCollector()
    client = DataplaneClient(endpoint=endpoint_without_v3, metrics=metrics)
    assert client.base_url == "http://localhost:5555/v3"

    # URL with /v3 should remain unchanged
    endpoint_with_v3 = DataplaneEndpoint(
        url="http://localhost:5555/v3",
        dataplane_auth=test_auth,
    )
    client = DataplaneClient(endpoint=endpoint_with_v3, metrics=metrics)
    assert client.base_url == "http://localhost:5555/v3"


def test_client_auth_handling(test_endpoint):
    """Test that client properly handles authentication."""
    client = create_dataplane_client(test_endpoint)

    # Auth should be stored and accessible
    assert client.endpoint == test_endpoint
    assert client.auth[0] == "admin"  # username
    assert client.auth[1] == "secret123"  # password
