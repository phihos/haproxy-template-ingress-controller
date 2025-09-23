"""
Transaction management API operations for HAProxy Dataplane API.

This module handles transaction lifecycle management for atomic
configuration changes in HAProxy.
"""

from dataclasses import asdict

import structlog

from haproxy_template_ic.core.logging import autolog
from .endpoint import DataplaneEndpoint
from .adapter import (
    commit_transaction,
    delete_transaction,
    start_transaction,
    get_configuration_version,
)

from haproxy_template_ic.metrics import MetricsCollector
from haproxy_template_ic.tracing import record_span_event, set_span_error

from .types import (
    DataplaneAPIError,
    TransactionCommitResult,
)
from .utils import (
    handle_dataplane_errors,
)

__all__ = [
    "TransactionAPI",
]

logger = structlog.get_logger(__name__)


class TransactionAPI:
    """Transaction management API operations for HAProxy Dataplane API."""

    def __init__(
        self,
        endpoint: DataplaneEndpoint,
        metrics: MetricsCollector,
    ):
        """Initialize transaction API.

        Args:
            endpoint: Dataplane endpoint for error context
            metrics: MetricsCollector instance for metrics tracking
        """
        self.endpoint = endpoint
        self.metrics = metrics

    @handle_dataplane_errors("start_transaction")
    @autolog()
    async def start(self) -> str:
        """Start a new transaction for configuration changes.

        Returns:
            Transaction ID for the new transaction

        Raises:
            DataplaneAPIError: If transaction creation fails
        """
        metrics = self.metrics

        with metrics.time_dataplane_api_operation("start_transaction"):
            try:
                response = await get_configuration_version(endpoint=self.endpoint)
                version = response.content
                if version is None:
                    raise DataplaneAPIError(
                        "Unable to get configuration version for transaction",
                        endpoint=self.endpoint,
                        operation="start_transaction",
                    )

                response = await start_transaction(
                    endpoint=self.endpoint, version=version
                )
                transaction = response.content

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
        metrics = self.metrics

        with metrics.time_dataplane_api_operation("commit_transaction"):
            try:
                # Commit transaction - adapter handles error checking
                response = await commit_transaction(
                    endpoint=self.endpoint, id=transaction_id
                )
                # Extract reload info from adapter response
                reload_info = response.reload_info

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
        metrics = self.metrics

        with metrics.time_dataplane_api_operation("rollback_transaction"):
            try:
                await delete_transaction(endpoint=self.endpoint, id=transaction_id)

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
