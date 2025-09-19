"""
Transaction management API operations for HAProxy Dataplane API.

This module handles transaction lifecycle management for atomic
configuration changes in HAProxy.
"""

import structlog
from collections.abc import Callable
from dataclasses import asdict
from typing import TYPE_CHECKING

from haproxy_dataplane_v3 import AuthenticatedClient

from haproxy_template_ic.core.logging import autolog

if TYPE_CHECKING:
    from .endpoint import DataplaneEndpoint

# Transaction APIs
from haproxy_dataplane_v3.api.transactions import (
    commit_transaction,
    delete_transaction,
    start_transaction,
)

from haproxy_template_ic.metrics import get_metrics_collector
from haproxy_template_ic.tracing import record_span_event, set_span_error
from .types import (
    DataplaneAPIError,
    TransactionCommitResult,
    ReloadInfo,
)
from .utils import (
    handle_dataplane_errors,
    get_configuration_version,
    check_dataplane_response,
)

__all__ = [
    "TransactionAPI",
]

logger = structlog.get_logger(__name__)


class TransactionAPI:
    """Transaction management API operations for HAProxy Dataplane API."""

    def __init__(
        self,
        get_client: Callable[[], AuthenticatedClient],
        endpoint: "DataplaneEndpoint",
    ):
        """Initialize transaction API.

        Args:
            get_client: Factory function that returns an authenticated client
            endpoint: Dataplane endpoint for error context
        """
        self._get_client = get_client
        self.endpoint = endpoint

    @handle_dataplane_errors("start_transaction")
    @autolog()
    async def start(self) -> str:
        """Start a new transaction for configuration changes.

        Returns:
            Transaction ID for the new transaction

        Raises:
            DataplaneAPIError: If transaction creation fails
        """
        metrics = get_metrics_collector()
        client = self._get_client()

        with metrics.time_dataplane_api_operation("start_transaction"):
            try:
                # Get current configuration version
                version = await get_configuration_version(client)
                if version is None:
                    raise DataplaneAPIError(
                        "Unable to get configuration version for transaction",
                        endpoint=self.endpoint,
                        operation="start_transaction",
                    )

                response = await start_transaction.asyncio_detailed(
                    client=client, version=version
                )
                transaction = check_dataplane_response(
                    response.parsed,
                    "start_transaction",
                    self.endpoint,
                )

                if transaction is not None and hasattr(transaction, "id"):
                    transaction_id = transaction.id
                else:
                    raise DataplaneAPIError(
                        "Invalid transaction response - missing ID",
                        endpoint=self.endpoint,
                        operation="start_transaction",
                    )

                metrics.record_dataplane_api_request("start_transaction", "success")
                record_span_event(
                    "transaction_started",
                    {"transaction_id": transaction_id, "version": version},
                )
                await logger.adebug(
                    f"Started transaction {transaction_id} (version {version})"
                )

                return str(transaction_id)

            except Exception as e:
                metrics.record_dataplane_api_request("start_transaction", "error")
                set_span_error(e, "Transaction start failed")
                raise DataplaneAPIError(
                    f"Failed to start transaction: {e}",
                    endpoint=self.endpoint,
                    operation="start_transaction",
                    original_error=e,
                ) from e

    @handle_dataplane_errors("commit_transaction")
    @autolog()
    async def commit(self, transaction_id: str) -> TransactionCommitResult:
        """Commit a transaction to apply configuration changes.

        Args:
            transaction_id: ID of the transaction to commit

        Returns:
            Dictionary containing commit results

        Raises:
            DataplaneAPIError: If transaction commit fails
        """
        metrics = get_metrics_collector()
        client = self._get_client()

        with metrics.time_dataplane_api_operation("commit_transaction"):
            try:
                # Get detailed response for reload detection
                response = await commit_transaction.asyncio_detailed(
                    client=client, id=transaction_id
                )

                # Check response for errors
                check_dataplane_response(
                    response.parsed,
                    "commit_transaction",
                    self.endpoint,
                )

                # Extract reload information from HTTP response
                reload_info = ReloadInfo.from_response(response, self.endpoint)

                commit_info = TransactionCommitResult(
                    transaction_id=transaction_id,
                    status="committed",
                    reload_info=reload_info,
                )

                metrics.record_dataplane_api_request("commit_transaction", "success")
                record_span_event("transaction_committed", asdict(commit_info))
                await logger.adebug(f"Committed transaction {transaction_id}")

                return commit_info

            except Exception as e:
                metrics.record_dataplane_api_request("commit_transaction", "error")
                set_span_error(e, "Transaction commit failed")
                raise DataplaneAPIError(
                    f"Failed to commit transaction {transaction_id}: {e}",
                    endpoint=self.endpoint,
                    operation="commit_transaction",
                    original_error=e,
                ) from e

    @handle_dataplane_errors("rollback_transaction")
    @autolog()
    async def rollback(self, transaction_id: str) -> None:
        """Rollback a transaction to discard configuration changes.

        Args:
            transaction_id: ID of the transaction to rollback

        Raises:
            DataplaneAPIError: If transaction rollback fails
        """
        metrics = get_metrics_collector()
        client = self._get_client()

        with metrics.time_dataplane_api_operation("rollback_transaction"):
            try:
                response = await delete_transaction.asyncio_detailed(
                    client=client, id=transaction_id
                )
                check_dataplane_response(
                    response.parsed,
                    "rollback_transaction",
                    self.endpoint,
                )

                metrics.record_dataplane_api_request("rollback_transaction", "success")
                record_span_event(
                    "transaction_rolled_back",
                    {"transaction_id": transaction_id},
                )
                await logger.adebug(f"Rolled back transaction {transaction_id}")

            except Exception as e:
                metrics.record_dataplane_api_request("rollback_transaction", "error")
                set_span_error(e, "Transaction rollback failed")
                raise DataplaneAPIError(
                    f"Failed to rollback transaction {transaction_id}: {e}",
                    endpoint=self.endpoint,
                    operation="rollback_transaction",
                    original_error=e,
                ) from e
