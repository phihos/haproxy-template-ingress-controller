"""
Unit tests for TransactionAPI functionality.

Tests transaction lifecycle management including start, commit, and rollback operations.
"""

import pytest
from unittest.mock import Mock, patch
from dataclasses import asdict

from haproxy_template_ic.dataplane.transaction_api import TransactionAPI
from haproxy_template_ic.dataplane.types import (
    DataplaneAPIError,
    TransactionCommitResult,
)
from tests.unit.conftest import (
    create_async_mock_with_return_value,
    create_async_mock_with_config,
    create_async_exception_mock,
    expect_dataplane_error,
)


@pytest.fixture
def transaction_api(mock_get_client):
    """Create TransactionAPI instance for testing."""
    from haproxy_template_ic.dataplane.endpoint import DataplaneEndpoint
    from haproxy_template_ic.credentials import DataplaneAuth

    auth = DataplaneAuth(username="admin", password="test")
    endpoint = DataplaneEndpoint(
        url="http://localhost:5555/v3", dataplane_auth=auth, pod_name="test-pod"
    )
    return TransactionAPI(mock_get_client, endpoint)


@pytest.mark.asyncio
async def test_start_transaction_success(transaction_api, mock_client, mock_metrics):
    """Test successful transaction start."""
    # Mock transaction response
    mock_transaction = Mock()
    mock_transaction.id = "test-transaction-123"

    with (
        patch(
            "haproxy_template_ic.dataplane.transaction_api.get_configuration_version"
        ) as mock_get_version,
        patch(
            "haproxy_template_ic.dataplane.transaction_api.start_transaction"
        ) as mock_start_transaction,
        patch(
            "haproxy_template_ic.dataplane.transaction_api.check_dataplane_response"
        ) as mock_check_response,
        patch(
            "haproxy_template_ic.dataplane.transaction_api.get_metrics_collector",
            return_value=mock_metrics,
        ),
        patch(
            "haproxy_template_ic.dataplane.transaction_api.record_span_event"
        ) as mock_record_event,
    ):
        # Setup mocks
        mock_get_version.return_value = 5
        # Make asyncio_detailed method return an awaitable
        mock_start_transaction.asyncio_detailed = create_async_mock_with_return_value(
            Mock(parsed=mock_transaction)
        )
        mock_check_response.return_value = mock_transaction

        # Execute
        result = await transaction_api.start()

        # Verify
        assert result == "test-transaction-123"
        mock_get_version.assert_called_once_with(mock_client)
        mock_start_transaction.asyncio_detailed.assert_called_once_with(
            client=mock_client, version=5
        )
        mock_record_event.assert_called_once()


@pytest.mark.asyncio
async def test_start_transaction_no_version(transaction_api, mock_metrics):
    """Test transaction start when version retrieval fails."""
    with (
        patch(
            "haproxy_template_ic.dataplane.transaction_api.get_configuration_version"
        ) as mock_get_version,
        patch(
            "haproxy_template_ic.dataplane.transaction_api.get_metrics_collector",
            return_value=mock_metrics,
        ),
    ):
        mock_get_version.return_value = None

        with pytest.raises(DataplaneAPIError) as exc_info:
            await transaction_api.start()

        assert "Unable to get configuration version" in str(exc_info.value)


@pytest.mark.asyncio
async def test_commit_transaction_success(transaction_api, mock_client, mock_metrics):
    """Test successful transaction commit."""
    # Mock commit response
    mock_result = Mock()
    mock_result.status_code = 202
    mock_result.headers = {"Reload-ID": "reload-456"}

    with (
        patch(
            "haproxy_template_ic.dataplane.transaction_api.commit_transaction"
        ) as mock_commit_transaction,
        patch(
            "haproxy_template_ic.dataplane.transaction_api.check_dataplane_response"
        ) as mock_check_response,
        patch(
            "haproxy_template_ic.dataplane.transaction_api.get_metrics_collector",
            return_value=mock_metrics,
        ),
        patch(
            "haproxy_template_ic.dataplane.transaction_api.record_span_event"
        ) as mock_record_event,
    ):
        # Setup mocks
        mock_commit_transaction.asyncio_detailed = create_async_mock_with_return_value(
            Mock(
                parsed=mock_result, status_code=202, headers={"Reload-ID": "reload-456"}
            )
        )
        mock_check_response.return_value = mock_result

        # Execute
        result = await transaction_api.commit("test-transaction-123")

        # Verify
        assert isinstance(result, TransactionCommitResult)
        assert result.transaction_id == "test-transaction-123"
        assert result.reload_info.reload_id == "reload-456"
        assert result.reload_info.reload_triggered
        assert result.status == "committed"

        mock_commit_transaction.asyncio_detailed.assert_called_once_with(
            client=mock_client, id="test-transaction-123"
        )
        mock_record_event.assert_called_once_with(
            "transaction_committed", asdict(result)
        )


@pytest.mark.asyncio
async def test_rollback_transaction_success(transaction_api, mock_client, mock_metrics):
    """Test successful transaction rollback."""
    with (
        patch(
            "haproxy_template_ic.dataplane.transaction_api.delete_transaction"
        ) as mock_delete_transaction,
        patch(
            "haproxy_template_ic.dataplane.transaction_api.check_dataplane_response"
        ) as mock_check_response,
        patch(
            "haproxy_template_ic.dataplane.transaction_api.get_metrics_collector",
            return_value=mock_metrics,
        ),
        patch(
            "haproxy_template_ic.dataplane.transaction_api.record_span_event"
        ) as mock_record_event,
    ):
        # Setup mocks
        mock_delete_transaction.asyncio_detailed = create_async_mock_with_return_value(
            Mock(parsed=Mock())
        )
        mock_check_response.return_value = Mock()

        # Execute
        await transaction_api.rollback("test-transaction-123")

        # Verify
        mock_delete_transaction.asyncio_detailed.assert_called_once_with(
            client=mock_client, id="test-transaction-123"
        )
        mock_record_event.assert_called_once_with(
            "transaction_rolled_back", {"transaction_id": "test-transaction-123"}
        )


@pytest.mark.asyncio
async def test_start_transaction_error_handling(transaction_api, mock_metrics):
    """Test error handling in transaction start."""
    with (
        patch(
            "haproxy_template_ic.dataplane.transaction_api.get_configuration_version"
        ) as mock_get_version,
        patch(
            "haproxy_template_ic.dataplane.transaction_api.get_metrics_collector",
            return_value=mock_metrics,
        ),
        patch(
            "haproxy_template_ic.dataplane.transaction_api.set_span_error"
        ) as mock_set_error,
    ):
        mock_get_version.side_effect = Exception("Network error")

        with expect_dataplane_error("Failed to start transaction") as exc_info:
            await transaction_api.start()

        assert exc_info.value.operation == "start_transaction"
        mock_set_error.assert_called_once()


@pytest.mark.asyncio
async def test_commit_transaction_error_handling(transaction_api, mock_metrics):
    """Test error handling in transaction commit."""
    with (
        patch(
            "haproxy_template_ic.dataplane.transaction_api.commit_transaction"
        ) as mock_commit_transaction,
        patch(
            "haproxy_template_ic.dataplane.transaction_api.get_metrics_collector",
            return_value=mock_metrics,
        ),
        patch(
            "haproxy_template_ic.dataplane.transaction_api.set_span_error"
        ) as mock_set_error,
    ):
        mock_commit_transaction.asyncio_detailed = create_async_exception_mock(
            message="Commit failed"
        )

        with expect_dataplane_error(
            "Failed to commit transaction test-transaction-123"
        ) as exc_info:
            await transaction_api.commit("test-transaction-123")

        assert exc_info.value.operation == "commit_transaction"
        mock_set_error.assert_called_once()


@pytest.mark.asyncio
async def test_rollback_transaction_error_handling(transaction_api, mock_metrics):
    """Test error handling in transaction rollback."""
    with (
        patch(
            "haproxy_template_ic.dataplane.transaction_api.delete_transaction"
        ) as mock_delete_transaction,
        patch(
            "haproxy_template_ic.dataplane.transaction_api.get_metrics_collector",
            return_value=mock_metrics,
        ),
        patch(
            "haproxy_template_ic.dataplane.transaction_api.set_span_error"
        ) as mock_set_error,
    ):
        mock_delete_transaction.asyncio_detailed = create_async_exception_mock(
            message="Rollback failed"
        )

        with expect_dataplane_error(
            "Failed to rollback transaction test-transaction-123"
        ) as exc_info:
            await transaction_api.rollback("test-transaction-123")

        assert exc_info.value.operation == "rollback_transaction"
        mock_set_error.assert_called_once()


@pytest.mark.asyncio
async def test_start_transaction_invalid_response(transaction_api, mock_metrics):
    """Test handling of invalid transaction response."""
    mock_transaction = Mock(spec=[])  # Mock with no attributes (no id)

    with (
        patch(
            "haproxy_template_ic.dataplane.transaction_api.get_configuration_version"
        ) as mock_get_version,
        patch(
            "haproxy_template_ic.dataplane.transaction_api.start_transaction"
        ) as mock_start_transaction,
        patch(
            "haproxy_template_ic.dataplane.transaction_api.check_dataplane_response"
        ) as mock_check_response,
        patch(
            "haproxy_template_ic.dataplane.transaction_api.get_metrics_collector",
            return_value=mock_metrics,
        ),
    ):
        mock_get_version.return_value = 5
        mock_start_transaction.asyncio_detailed = create_async_mock_with_config(
            return_value=Mock(parsed=mock_transaction)
        )
        mock_check_response.return_value = mock_transaction

        with expect_dataplane_error("Invalid transaction response - missing ID"):
            await transaction_api.start()
