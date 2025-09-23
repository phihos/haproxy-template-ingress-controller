"""
Unit tests for TransactionAPI functionality.

Tests transaction lifecycle management including start, commit, and rollback operations.
"""

import pytest
from unittest.mock import Mock, patch
from dataclasses import asdict

from haproxy_template_ic.dataplane.types import (
    DataplaneAPIError,
    TransactionCommitResult,
)
from tests.unit.conftest import (
    expect_dataplane_error,
)
from tests.unit.dataplane.conftest import (
    create_transaction_api,
)
from tests.unit.dataplane.adapter_fixtures import (
    create_transaction_async_mock,
    create_version_async_mock,
    create_mock_api_response,
)


@pytest.fixture
def transaction_api(test_endpoint):
    """Create TransactionAPI instance for testing."""
    return create_transaction_api(test_endpoint)


@pytest.mark.asyncio
async def test_start_transaction_success(transaction_api, mock_client, mock_metrics):
    """Test successful transaction start."""
    # Mock transaction response
    mock_transaction = Mock()
    mock_transaction.id = "test-transaction-123"

    with (
        patch(
            "haproxy_template_ic.dataplane.transaction_api.get_configuration_version",
            create_version_async_mock(5),
        ) as mock_get_version,
        patch(
            "haproxy_template_ic.dataplane.transaction_api.start_transaction",
            create_transaction_async_mock("test-transaction-123"),
        ) as mock_start_transaction,
        patch(
            "haproxy_template_ic.dataplane.transaction_api.record_span_event"
        ) as mock_record_event,
    ):
        # Execute
        result = await transaction_api.start()

        # Verify
        assert result == "test-transaction-123"
        mock_get_version.assert_called_once()
        mock_start_transaction.assert_called_once()
        mock_record_event.assert_called_once()


@pytest.mark.asyncio
async def test_start_transaction_no_version(transaction_api, mock_metrics):
    """Test transaction start when version retrieval fails."""
    with patch(
        "haproxy_template_ic.dataplane.transaction_api.get_configuration_version"
    ) as mock_get_version:
        mock_get_version.return_value = create_mock_api_response(content=None)

        with pytest.raises(DataplaneAPIError) as exc_info:
            await transaction_api.start()

        assert "Unable to get configuration version" in str(exc_info.value)


@pytest.mark.asyncio
async def test_commit_transaction_success(transaction_api, mock_client, mock_metrics):
    """Test successful transaction commit."""
    with (
        patch(
            "haproxy_template_ic.dataplane.transaction_api.commit_transaction",
            create_transaction_async_mock(
                "test-transaction-123", reload_id="reload-456"
            ),
        ) as mock_commit_transaction,
        patch(
            "haproxy_template_ic.dataplane.transaction_api.record_span_event"
        ) as mock_record_event,
    ):
        # Execute
        result = await transaction_api.commit("test-transaction-123")

        # Verify
        assert isinstance(result, TransactionCommitResult)
        assert result.transaction_id == "test-transaction-123"
        assert result.reload_info.reload_id == "reload-456"
        assert result.reload_info.reload_triggered
        assert result.status == "committed"

        mock_commit_transaction.assert_called_once()
        mock_record_event.assert_called_once_with(
            "transaction_committed", asdict(result)
        )


@pytest.mark.asyncio
async def test_rollback_transaction_success(transaction_api, mock_client, mock_metrics):
    """Test successful transaction rollback."""
    from unittest.mock import AsyncMock

    with (
        patch(
            "haproxy_template_ic.dataplane.transaction_api.delete_transaction",
            AsyncMock(),
        ) as mock_delete_transaction,
        patch(
            "haproxy_template_ic.dataplane.transaction_api.record_span_event"
        ) as mock_record_event,
    ):
        # Execute
        await transaction_api.rollback("test-transaction-123")

        # Verify
        mock_delete_transaction.assert_called_once()
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
    from unittest.mock import AsyncMock

    with (
        patch(
            "haproxy_template_ic.dataplane.transaction_api.commit_transaction",
            AsyncMock(side_effect=Exception("Commit failed")),
        ),
        patch(
            "haproxy_template_ic.dataplane.transaction_api.set_span_error"
        ) as mock_set_error,
    ):
        with expect_dataplane_error(
            "Failed to commit transaction test-transaction-123"
        ) as exc_info:
            await transaction_api.commit("test-transaction-123")

        assert exc_info.value.operation == "commit_transaction"
        mock_set_error.assert_called_once()


@pytest.mark.asyncio
async def test_rollback_transaction_error_handling(transaction_api, mock_metrics):
    """Test error handling in transaction rollback."""
    from unittest.mock import AsyncMock

    with (
        patch(
            "haproxy_template_ic.dataplane.transaction_api.delete_transaction",
            AsyncMock(side_effect=Exception("Rollback failed")),
        ),
        patch(
            "haproxy_template_ic.dataplane.transaction_api.set_span_error"
        ) as mock_set_error,
    ):
        with expect_dataplane_error(
            "Failed to rollback transaction test-transaction-123"
        ) as exc_info:
            await transaction_api.rollback("test-transaction-123")

        assert exc_info.value.operation == "rollback_transaction"
        mock_set_error.assert_called_once()


@pytest.mark.asyncio
async def test_start_transaction_invalid_response(transaction_api, mock_metrics):
    """Test handling of invalid transaction response."""
    from unittest.mock import AsyncMock

    # Create a mock transaction without an id attribute
    mock_transaction = Mock(spec=[])

    with (
        patch(
            "haproxy_template_ic.dataplane.transaction_api.get_configuration_version",
            create_version_async_mock(5),
        ),
        patch(
            "haproxy_template_ic.dataplane.transaction_api.start_transaction",
            AsyncMock(return_value=create_mock_api_response(content=mock_transaction)),
        ),
    ):
        with expect_dataplane_error("Invalid transaction response - missing ID"):
            await transaction_api.start()
