"""
Runtime API operations for HAProxy Dataplane API.

This module handles runtime operations that don't require HAProxy reloads,
including map operations, ACL operations, and server state changes.
"""
# mypy: ignore-errors

import logging
from collections.abc import Callable
from typing import Dict, List, TYPE_CHECKING

from haproxy_dataplane_v3 import AuthenticatedClient

if TYPE_CHECKING:
    from .endpoint import DataplaneEndpoint
from haproxy_dataplane_v3.models import (
    ReplaceRuntimeMapEntryBody,
    OneMapEntry,
    OneACLFileEntry,
    RuntimeServer,
)

# Runtime APIs
from haproxy_dataplane_v3.api.acl_runtime import (
    delete_services_haproxy_runtime_acls_parent_name_entries_id,
    post_services_haproxy_runtime_acls_parent_name_entries,
)
from haproxy_dataplane_v3.api.maps import (
    add_map_entry,
    delete_runtime_map_entry,
    replace_runtime_map_entry,
)
from haproxy_dataplane_v3.api.server import (
    replace_runtime_server,
)

from haproxy_template_ic.metrics import get_metrics_collector
from haproxy_template_ic.tracing import record_span_event, set_span_error
from .types import DataplaneAPIError, MapChange
from .utils import handle_dataplane_errors

__all__ = [
    "RuntimeAPI",
]

logger = logging.getLogger(__name__)


class RuntimeAPI:
    """Runtime API operations for HAProxy Dataplane API."""

    def __init__(
        self,
        get_client: Callable[[], AuthenticatedClient],
        endpoint: "DataplaneEndpoint",
    ):
        """Initialize runtime API.

        Args:
            get_client: Factory function that returns an authenticated client
            endpoint: Dataplane endpoint for error context
        """
        self._get_client = get_client
        self.endpoint = endpoint

    @handle_dataplane_errors("apply_runtime_map_operations")
    async def apply_runtime_map_operations(
        self, map_name: str, operations: List[MapChange]
    ) -> None:
        """Apply runtime map operations without HAProxy reload.

        Args:
            map_name: Name of the map file to modify
            operations: List of map changes to apply

        Raises:
            DataplaneAPIError: If any map operation fails
        """
        if not operations:
            logger.debug(f"No map operations to apply for {map_name}")
            return

        metrics = get_metrics_collector()
        client = self._get_client()

        logger.info(f"Applying {len(operations)} runtime map operations to {map_name}")

        for operation in operations:
            with metrics.time_dataplane_api_operation(f"map_{operation.operation}"):
                try:
                    if operation.operation == "add":
                        body = OneMapEntry(key=operation.key, value=operation.value)
                        await add_map_entry.asyncio(
                            client=client,
                            name=map_name,
                            body=body,
                        )
                        logger.debug(
                            f"Added map entry: {operation.key} -> {operation.value}"
                        )

                    elif operation.operation == "set":
                        body = ReplaceRuntimeMapEntryBody(value=operation.value)
                        await replace_runtime_map_entry.asyncio(
                            client=client,
                            name=map_name,
                            id=operation.key,
                            body=body,
                        )
                        logger.debug(
                            f"Updated map entry: {operation.key} -> {operation.value}"
                        )

                    elif operation.operation == "del":
                        await delete_runtime_map_entry.asyncio(
                            client=client, name=map_name, id=operation.key
                        )
                        logger.debug(f"Deleted map entry: {operation.key}")

                    else:
                        logger.warning(f"Unknown map operation: {operation.operation}")
                        continue

                    record_span_event(
                        f"map_{operation.operation}_success",
                        {
                            "map_name": map_name,
                            "key": operation.key,
                            "value": operation.value,
                        },
                    )
                    metrics.record_dataplane_api_request(
                        f"map_{operation.operation}", "success"
                    )

                except Exception as e:
                    metrics.record_dataplane_api_request(
                        f"map_{operation.operation}", "error"
                    )
                    set_span_error(e, f"Map {operation.operation} failed")
                    raise DataplaneAPIError(
                        f"Map {operation.operation} failed for key {operation.key}: {e}",
                        endpoint=self.endpoint,
                        operation=f"map_{operation.operation}",
                        original_error=e,
                    ) from e

        logger.info(
            f"Successfully applied {len(operations)} map operations to {map_name}"
        )

    @handle_dataplane_errors("apply_runtime_acl_operations")
    async def apply_runtime_acl_operations(
        self, acl_id: str, operations: List[MapChange]
    ) -> None:
        """Apply runtime ACL operations without HAProxy reload.

        Args:
            acl_id: ID/name of the ACL to modify
            operations: List of ACL changes to apply

        Raises:
            DataplaneAPIError: If any ACL operation fails
        """
        if not operations:
            logger.debug(f"No ACL operations to apply for {acl_id}")
            return

        metrics = get_metrics_collector()
        client = self._get_client()

        logger.info(f"Applying {len(operations)} runtime ACL operations to {acl_id}")

        for operation in operations:
            with metrics.time_dataplane_api_operation(f"acl_{operation.operation}"):
                try:
                    if operation.operation == "add":
                        body = OneACLFileEntry(value=operation.value)
                        await post_services_haproxy_runtime_acls_parent_name_entries.asyncio(
                            client=client,
                            parent_name=acl_id,
                            body=body,
                        )
                        logger.debug(f"Added ACL entry: {operation.value}")

                    elif operation.operation == "del":
                        # For ACL deletion, the key is the entry ID/value
                        await delete_services_haproxy_runtime_acls_parent_name_entries_id.asyncio(
                            client=client,
                            parent_name=acl_id,
                            id=operation.key,
                        )
                        logger.debug(f"Deleted ACL entry: {operation.key}")

                    else:
                        logger.warning(f"Unknown ACL operation: {operation.operation}")
                        continue

                    record_span_event(
                        f"acl_{operation.operation}_success",
                        {
                            "acl_id": acl_id,
                            "key": operation.key,
                            "value": operation.value,
                        },
                    )
                    metrics.record_dataplane_api_request(
                        f"acl_{operation.operation}", "success"
                    )

                except Exception as e:
                    metrics.record_dataplane_api_request(
                        f"acl_{operation.operation}", "error"
                    )
                    set_span_error(e, f"ACL {operation.operation} failed")
                    raise DataplaneAPIError(
                        f"ACL {operation.operation} failed for {operation.key}: {e}",
                        endpoint=self.endpoint,
                        operation=f"acl_{operation.operation}",
                        original_error=e,
                    ) from e

        logger.info(
            f"Successfully applied {len(operations)} ACL operations to {acl_id}"
        )

    @handle_dataplane_errors("update_server_state")
    async def update_server_state(
        self, backend_name: str, server_name: str, state: str
    ) -> None:
        """Update server state via runtime API.

        Args:
            backend_name: Name of the backend containing the server
            server_name: Name of the server to update
            state: New server state (e.g., 'ready', 'maint', 'drain')

        Raises:
            DataplaneAPIError: If server state update fails
        """
        metrics = get_metrics_collector()
        client = self._get_client()

        logger.info(f"Updating server {backend_name}/{server_name} state to {state}")

        with metrics.time_dataplane_api_operation("server_state_update"):
            try:
                body = RuntimeServer(admin_state=state)
                await replace_runtime_server.asyncio(
                    client=client,
                    backend=backend_name,
                    name=server_name,
                    body=body,
                )

                record_span_event(
                    "server_state_update_success",
                    {
                        "backend": backend_name,
                        "server": server_name,
                        "state": state,
                    },
                )
                metrics.record_dataplane_api_request("server_state_update", "success")
                logger.info(
                    f"Successfully updated server {backend_name}/{server_name} to {state}"
                )

            except Exception as e:
                metrics.record_dataplane_api_request("server_state_update", "error")
                set_span_error(e, "Server state update failed")
                raise DataplaneAPIError(
                    f"Failed to update server {backend_name}/{server_name} state: {e}",
                    endpoint=self.endpoint,
                    operation="server_state_update",
                    original_error=e,
                ) from e

    @handle_dataplane_errors("bulk_map_updates")
    async def bulk_map_updates(self, map_updates: Dict[str, List[MapChange]]) -> None:
        """Apply bulk map updates across multiple maps.

        Args:
            map_updates: Dictionary mapping map names to their operations

        Raises:
            DataplaneAPIError: If any map update fails
        """
        if not map_updates:
            logger.debug("No map updates to apply")
            return

        logger.info(f"Applying bulk updates to {len(map_updates)} maps")

        for map_name, operations in map_updates.items():
            await self.apply_runtime_map_operations(map_name, operations)

        logger.info(f"Successfully applied bulk updates to {len(map_updates)} maps")

    @handle_dataplane_errors("bulk_acl_updates")
    async def bulk_acl_updates(self, acl_updates: Dict[str, List[MapChange]]) -> None:
        """Apply bulk ACL updates across multiple ACLs.

        Args:
            acl_updates: Dictionary mapping ACL IDs to their operations

        Raises:
            DataplaneAPIError: If any ACL update fails
        """
        if not acl_updates:
            logger.debug("No ACL updates to apply")
            return

        logger.info(f"Applying bulk updates to {len(acl_updates)} ACLs")

        for acl_id, operations in acl_updates.items():
            await self.apply_runtime_acl_operations(acl_id, operations)

        logger.info(f"Successfully applied bulk updates to {len(acl_updates)} ACLs")
