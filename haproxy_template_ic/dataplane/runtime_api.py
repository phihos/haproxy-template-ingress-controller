"""
Runtime API operations for HAProxy Dataplane API.

This module handles runtime operations that don't require HAProxy reloads,
including map operations, ACL operations, and server state changes.
"""
# ty: type checking disabled temporarily - generated API client issues

import structlog

from haproxy_template_ic.core.logging import autolog
from .endpoint import DataplaneEndpoint
from haproxy_dataplane_v3.models import (
    ReplaceRuntimeMapEntryBody,
    OneMapEntry,
    OneACLFileEntry,
    RuntimeServer,
    RuntimeServerAdminState,
)

from .adapter import (
    add_map_entry,
    delete_runtime_map_entry,
    replace_runtime_map_entry,
    replace_runtime_server,
    post_runtime_acl_entry,
    delete_runtime_acl_file_entry,
)

from haproxy_template_ic.metrics import get_metrics_collector
from haproxy_template_ic.tracing import record_span_event, set_span_error
from .types import DataplaneAPIError, MapChange, RuntimeOperationResult
from .adapter import ReloadInfo
from .utils import handle_dataplane_errors

__all__ = [
    "RuntimeAPI",
]

logger = structlog.get_logger(__name__)


class RuntimeAPI:
    """Runtime API operations for HAProxy Dataplane API."""

    def __init__(
        self,
        endpoint: DataplaneEndpoint,
    ):
        """Initialize runtime API.

        Args:
            endpoint: Dataplane endpoint for error context
        """
        self.endpoint = endpoint

    @handle_dataplane_errors("apply_runtime_map_operations")
    @autolog()
    async def apply_runtime_map_operations(
        self, map_name: str, operations: list[MapChange]
    ) -> RuntimeOperationResult:
        """Apply runtime map operations without HAProxy reload.

        Args:
            map_name: Name of the map file to modify
            operations: List of map changes to apply

        Returns:
            RuntimeOperationResult containing operation status and reload information

        Raises:
            DataplaneAPIError: If any map operation fails
        """
        if not operations:
            await logger.adebug(f"No map operations to apply for {map_name}")
            return RuntimeOperationResult(
                operation_applied=False,
                reload_info=ReloadInfo(),
            )

        metrics = get_metrics_collector()
        reload_infos = []

        await logger.ainfo(
            f"Applying {len(operations)} runtime map operations to {map_name}"
        )

        for operation in operations:
            try:
                if operation.operation == "add":
                    body = OneMapEntry(key=operation.key, value=operation.value)
                    response = await add_map_entry(
                        endpoint=self.endpoint,
                        parent_name=map_name,
                        body=body,
                    )
                    reload_infos.append(response.reload_info)
                    await logger.adebug(
                        f"Added map entry: {operation.key} -> {operation.value}"
                    )

                elif operation.operation == "set":
                    body = ReplaceRuntimeMapEntryBody(value=operation.value)
                    response = await replace_runtime_map_entry(
                        endpoint=self.endpoint,
                        parent_name=map_name,
                        id=operation.key,
                        body=body,
                    )
                    reload_infos.append(response.reload_info)
                    await logger.adebug(
                        f"Updated map entry: {operation.key} -> {operation.value}"
                    )

                elif operation.operation == "del":
                    response = await delete_runtime_map_entry(
                        endpoint=self.endpoint, parent_name=map_name, id=operation.key
                    )
                    reload_infos.append(response.reload_info)
                    await logger.adebug(f"Deleted map entry: {operation.key}")

                else:
                    await logger.awarning(
                        f"Unknown map operation: {operation.operation}"
                    )
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

        await logger.ainfo(
            f"Successfully applied {len(operations)} map operations to {map_name}"
        )

        return RuntimeOperationResult(
            operation_applied=True,
            reload_info=ReloadInfo.combine(*reload_infos),
        )

    @handle_dataplane_errors("apply_runtime_acl_operations")
    @autolog()
    async def apply_runtime_acl_operations(
        self, acl_id: str, operations: list[MapChange]
    ) -> RuntimeOperationResult:
        """Apply runtime ACL operations without HAProxy reload.

        Args:
            acl_id: ID/name of the ACL to modify
            operations: List of ACL changes to apply

        Returns:
            RuntimeOperationResult containing operation status and reload information

        Raises:
            DataplaneAPIError: If any ACL operation fails
        """
        if not operations:
            await logger.adebug(f"No ACL operations to apply for {acl_id}")
            return RuntimeOperationResult(
                operation_applied=False,
                reload_info=ReloadInfo(),
            )

        metrics = get_metrics_collector()
        reload_infos = []

        await logger.ainfo(
            f"Applying {len(operations)} runtime ACL operations to {acl_id}"
        )

        for operation in operations:
            try:
                if operation.operation == "add":
                    body = OneACLFileEntry(value=operation.value)
                    response = await post_runtime_acl_entry(
                        endpoint=self.endpoint,
                        parent_name=acl_id,
                        body=body,
                    )
                    reload_infos.append(response.reload_info)
                    await logger.adebug(f"Added ACL entry: {operation.value}")

                elif operation.operation == "del":
                    # For ACL deletion, the key is the entry ID/value
                    response = await delete_runtime_acl_file_entry(
                        endpoint=self.endpoint,
                        parent_name=acl_id,
                        id=operation.key,
                    )
                    reload_infos.append(response.reload_info)
                    await logger.adebug(f"Deleted ACL entry: {operation.key}")

                else:
                    await logger.awarning(
                        f"Unknown ACL operation: {operation.operation}"
                    )
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

        await logger.ainfo(
            f"Successfully applied {len(operations)} ACL operations to {acl_id}"
        )

        return RuntimeOperationResult(
            operation_applied=True,
            reload_info=ReloadInfo.combine(*reload_infos),
        )

    @handle_dataplane_errors("update_server_state")
    @autolog()
    async def update_server_state(
        self, backend_name: str, server_name: str, state: RuntimeServerAdminState
    ) -> RuntimeOperationResult:
        """Update server state via runtime API.

        Args:
            backend_name: Name of the backend containing the server
            server_name: Name of the server to update
            state: New server state (e.g., 'ready', 'maint', 'drain')

        Returns:
            RuntimeOperationResult containing operation status and reload information

        Raises:
            DataplaneAPIError: If server state update fails
        """
        metrics = get_metrics_collector()

        await logger.ainfo(
            f"Updating server {backend_name}/{server_name} state to {state}"
        )

        try:
            body = RuntimeServer(admin_state=state)
            response = await replace_runtime_server(
                endpoint=self.endpoint,
                parent_name=backend_name,
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
            await logger.ainfo(
                f"Successfully updated server {backend_name}/{server_name} to {state}"
            )

            return RuntimeOperationResult(
                operation_applied=True,
                reload_info=response.reload_info,
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
    async def bulk_map_updates(
        self, map_updates: dict[str, list[MapChange]]
    ) -> RuntimeOperationResult:
        """Apply bulk map updates across multiple maps.

        Args:
            map_updates: Dictionary mapping map names to their operations

        Returns:
            RuntimeOperationResult containing operation status and reload information

        Raises:
            DataplaneAPIError: If any map update fails
        """
        if not map_updates:
            await logger.adebug("No map updates to apply")
            return RuntimeOperationResult(
                operation_applied=False,
                reload_info=ReloadInfo(),
            )

        await logger.ainfo(f"Applying bulk updates to {len(map_updates)} maps")
        reload_infos = []

        for map_name, operations in map_updates.items():
            result = await self.apply_runtime_map_operations(map_name, operations)
            reload_infos.append(result.reload_info)

        await logger.ainfo(
            f"Successfully applied bulk updates to {len(map_updates)} maps"
        )

        return RuntimeOperationResult(
            operation_applied=True,
            reload_info=ReloadInfo.combine(*reload_infos),
        )

    @handle_dataplane_errors("bulk_acl_updates")
    async def bulk_acl_updates(
        self, acl_updates: dict[str, list[MapChange]]
    ) -> RuntimeOperationResult:
        """Apply bulk ACL updates across multiple ACLs.

        Args:
            acl_updates: Dictionary mapping ACL IDs to their operations

        Returns:
            RuntimeOperationResult containing operation status and reload information

        Raises:
            DataplaneAPIError: If any ACL update fails
        """
        if not acl_updates:
            await logger.adebug("No ACL updates to apply")
            return RuntimeOperationResult(
                operation_applied=False,
                reload_info=ReloadInfo(),
            )

        await logger.ainfo(f"Applying bulk updates to {len(acl_updates)} ACLs")
        reload_infos = []

        for acl_id, operations in acl_updates.items():
            result = await self.apply_runtime_acl_operations(acl_id, operations)
            reload_infos.append(result.reload_info)

        await logger.ainfo(
            f"Successfully applied bulk updates to {len(acl_updates)} ACLs"
        )

        return RuntimeOperationResult(
            operation_applied=True,
            reload_info=ReloadInfo.combine(*reload_infos),
        )
