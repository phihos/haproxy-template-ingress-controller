"""
Unit tests for DataplaneOperations unified interface.

Tests the high-level operations interface that coordinates between
specialized API modules.
"""

import pytest
from unittest.mock import Mock, patch

from haproxy_template_ic.dataplane.operations import DataplaneOperations
from haproxy_template_ic.dataplane.types import (
    DataplaneAPIError,
    StructuredDeploymentResult,
)
from .conftest import create_frontend_config_change
from tests.unit.conftest import (
    create_async_mock_with_return_value,
    create_async_mock_coroutine,
)


@pytest.fixture
def operations(mock_get_client):
    """Create DataplaneOperations instance for testing."""
    return DataplaneOperations(mock_get_client, "http://localhost:5555/v3")


def test_operations_initialization(operations):
    """Test that operations initializes all API modules."""
    assert operations.config is not None
    assert operations.runtime is not None
    assert operations.storage is not None
    assert operations.transactions is not None
    assert operations.validation is not None


@pytest.mark.asyncio
async def test_deploy_structured_configuration_empty_changes(operations):
    """Test deployment with no changes."""
    result = await operations.deploy_structured_configuration([])

    assert isinstance(result, StructuredDeploymentResult)
    assert result.changes_applied == 0
    assert result.transaction_used is False
    assert result.version == "unchanged"


@pytest.mark.asyncio
async def test_deploy_with_transaction_success(operations):
    """Test successful deployment with transaction."""
    changes = [create_frontend_config_change()]

    from haproxy_template_ic.dataplane.types import TransactionCommitResult, ReloadInfo

    mock_commit_result = TransactionCommitResult(
        transaction_id="txn-123",
        status="committed",
        reload_info=ReloadInfo(reload_id="reload-456"),
    )

    with (
        patch.object(
            operations.transactions,
            "start",
            return_value=create_async_mock_coroutine("txn-123"),
        ),
        patch.object(
            operations.transactions,
            "commit",
            return_value=create_async_mock_coroutine(mock_commit_result),
        ),
        patch(
            "haproxy_template_ic.dataplane.operations.get_configuration_version"
        ) as mock_get_version,
        patch.object(operations.config, "apply_config_change") as mock_apply_change,
    ):
        mock_get_version.side_effect = [5, 6]  # Before and after versions

        result = await operations.deploy_structured_configuration(changes)

        assert isinstance(result, StructuredDeploymentResult)
        assert result.changes_applied == 1
        assert result.transaction_used is True
        assert result.transaction_id == "txn-123"
        assert result.version == "6"

        # Verify transaction flow
        operations.transactions.start.assert_called_once()
        mock_apply_change.assert_called_once_with(changes[0], 5, "txn-123")
        operations.transactions.commit.assert_called_once_with("txn-123")


@pytest.mark.asyncio
async def test_deploy_with_transaction_rollback_on_error(operations):
    """Test transaction rollback on deployment error."""
    changes = [create_frontend_config_change()]

    with (
        patch.object(
            operations.transactions,
            "start",
            return_value=create_async_mock_coroutine("txn-123"),
        ),
        patch.object(
            operations.transactions,
            "rollback",
            return_value=create_async_mock_coroutine(),
        ) as mock_rollback,
        patch(
            "haproxy_template_ic.dataplane.operations.get_configuration_version"
        ) as mock_get_version,
        patch.object(
            operations.config,
            "apply_config_change",
            side_effect=Exception("Apply failed"),
        ),
    ):
        mock_get_version.return_value = 5

        with pytest.raises(DataplaneAPIError):
            await operations.deploy_structured_configuration(changes)

        # Verify rollback was called
        mock_rollback.assert_called_once_with("txn-123")


@pytest.mark.asyncio
async def test_deploy_without_transaction(operations):
    """Test deployment without transaction."""
    changes = [
        create_frontend_config_change("web1"),
        create_frontend_config_change("web2", "*:81"),
    ]

    with (
        patch(
            "haproxy_template_ic.dataplane.operations.get_configuration_version"
        ) as mock_get_version,
        patch.object(operations.config, "apply_config_change") as mock_apply_change,
    ):
        mock_get_version.side_effect = [5, 6]  # Before and after versions
        mock_apply_change.side_effect = [None, Exception("Second change failed")]

        result = await operations.deploy_structured_configuration(
            changes, use_transaction=False
        )

        assert isinstance(result, StructuredDeploymentResult)
        assert result.changes_applied == 1  # Only first succeeded
        assert result.transaction_used is False
        assert result.total_changes == 2
        assert result.version == "6"


@pytest.mark.asyncio
async def test_sync_storage_resources(operations, mock_metrics):
    """Test storage resource synchronization."""
    maps = {"geo.map": "US 1\nEU 2"}
    certificates = {"ssl.pem": "-----BEGIN CERTIFICATE-----\n..."}

    with (
        patch.object(operations.storage, "sync_maps") as mock_sync_maps,
        patch.object(operations.storage, "sync_certificates") as mock_sync_certs,
        patch(
            "haproxy_template_ic.dataplane.operations.get_metrics_collector",
            return_value=mock_metrics,
        ),
    ):
        # Setup async mocks
        from haproxy_template_ic.dataplane.types import (
            StorageOperationResult,
            ReloadInfo,
        )

        mock_storage_result = StorageOperationResult(
            operation_applied=True, reload_info=ReloadInfo()
        )
        mock_sync_maps.return_value = create_async_mock_coroutine(mock_storage_result)
        mock_sync_certs.return_value = create_async_mock_coroutine(mock_storage_result)

        await operations.sync_storage_resources(maps=maps, certificates=certificates)

        # Verify storage sync calls
        mock_sync_maps.assert_called_once_with(maps)
        mock_sync_certs.assert_called_once_with(certificates)
        # Note: sync_storage_resources runs operations sequentially, not with gather


@pytest.mark.asyncio
async def test_apply_runtime_changes(operations, mock_metrics):
    """Test runtime changes application."""
    map_changes = {"geo.map": []}
    server_changes = [{"backend": "api", "server": "api1", "state": "ready"}]

    with (
        patch.object(operations.runtime, "bulk_map_updates") as mock_map_updates,
        patch.object(operations.runtime, "update_server_state") as mock_server_update,
        patch(
            "haproxy_template_ic.dataplane.operations.get_metrics_collector",
            return_value=mock_metrics,
        ),
    ):
        # Setup async mocks
        from haproxy_template_ic.dataplane.types import (
            RuntimeOperationResult,
            ReloadInfo,
        )

        mock_result = RuntimeOperationResult(
            operation_applied=True, reload_info=ReloadInfo()
        )
        mock_map_updates.return_value = create_async_mock_coroutine(mock_result)
        mock_server_result = RuntimeOperationResult(
            operation_applied=True, reload_info=ReloadInfo()
        )
        mock_server_update.return_value = create_async_mock_coroutine(
            mock_server_result
        )

        await operations.apply_runtime_changes(
            map_changes=map_changes, server_changes=server_changes
        )

        mock_map_updates.assert_called_once_with(map_changes)
        mock_server_update.assert_called_once_with("api", "api1", "ready")


@pytest.mark.asyncio
async def test_validate_and_deploy(operations, mock_metrics):
    """Test validation and deployment flow."""
    config_content = "global\n    daemon"

    mock_deployment_result = Mock()
    mock_deployment_result.size = len(config_content)
    mock_deployment_result.status = "success"

    with (
        patch.object(operations.validation, "validate_configuration") as mock_validate,
        patch.object(
            operations.validation,
            "deploy_configuration",
            return_value=mock_deployment_result,
        ) as mock_deploy,
        patch(
            "haproxy_template_ic.dataplane.operations.get_metrics_collector",
            return_value=mock_metrics,
        ),
    ):
        # Setup async mocks
        mock_validate.return_value = create_async_mock_coroutine()
        mock_deploy.return_value = create_async_mock_coroutine(mock_deployment_result)

        result = await operations.validate_and_deploy(config_content)

        mock_validate.assert_called_once_with(config_content)
        mock_deploy.assert_called_once_with(config_content)

        assert result.validation == "success"
        assert result.deployment == mock_deployment_result


@pytest.mark.asyncio
async def test_get_cluster_info(operations, mock_metrics):
    """Test cluster information retrieval."""
    mock_version_info = {"api_version": "3.0", "version": "dataplane-2.8.0"}
    mock_storage_info = {"maps": 5, "certificates": 2}
    current_config = "global\n    daemon"
    structured_config = {
        "frontends": [{"name": "web"}],
        "backends": [{"name": "api"}],
    }

    with (
        patch.object(
            operations.validation, "get_version", return_value=mock_version_info
        ),
        patch.object(
            operations.storage, "get_storage_info", return_value=mock_storage_info
        ),
        patch.object(
            operations.validation,
            "get_current_configuration",
            return_value=current_config,
        ),
        patch.object(operations.config, "fetch_structured_configuration"),
        patch(
            "haproxy_template_ic.dataplane.operations.get_metrics_collector",
            return_value=mock_metrics,
        ),
    ):
        # Setup async mocks - these methods should return awaitables
        operations.validation.get_version = create_async_mock_with_return_value(
            mock_version_info
        )
        operations.storage.get_storage_info = create_async_mock_with_return_value(
            mock_storage_info
        )
        operations.validation.get_current_configuration = (
            create_async_mock_with_return_value(current_config)
        )
        operations.config.fetch_structured_configuration = (
            create_async_mock_with_return_value(structured_config)
        )

        result = await operations.get_cluster_info()

        assert result["version"] == mock_version_info
        assert result["storage"] == mock_storage_info
        assert result["configuration"]["current_size"] == len(current_config)
        assert result["endpoint"] == "http://localhost:5555/v3"
