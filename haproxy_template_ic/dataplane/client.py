"""
HAProxy Dataplane API client for configuration management.

This module provides the simplified DataplaneClient class that coordinates
between the various API modules for common operations.
"""

import logging
from typing import Any


from haproxy_template_ic.constants import DEFAULT_API_TIMEOUT
from haproxy_template_ic.metrics import MetricsCollector
from .types import (
    ConfigChange,
    MapChange,
    RuntimeOperationResult,
    StorageOperationResult,
    StructuredDeploymentResult,
    ValidationDeploymentResult,
    ValidateAndDeployResult,
)
from .adapter import ReloadInfo
from .endpoint import DataplaneEndpoint
from .operations import DataplaneOperations

__all__ = [
    "DataplaneClient",
]

logger = logging.getLogger(__name__)


class DataplaneClient:
    """Simplified HAProxy Dataplane API client.

    This client provides a high-level interface for HAProxy Dataplane API operations
    by coordinating between specialized API modules for configuration, runtime,
    storage, and validation operations.

    Example:
        Basic usage with error handling:

        >>> from haproxy_template_ic.credentials import DataplaneAuth
        >>> from pydantic import SecretStr
        >>> auth = DataplaneAuth(username="admin", password=SecretStr("password"))
        >>> endpoint = DataplaneEndpoint("http://localhost:5555", dataplane_auth=auth)
        >>> client = DataplaneClient(endpoint)
        >>> # Use client methods as needed
    """

    def __init__(
        self,
        endpoint: DataplaneEndpoint,
        metrics: MetricsCollector,
        timeout: float = DEFAULT_API_TIMEOUT,
    ):
        """Initialize the client with a DataplaneEndpoint.

        Args:
            endpoint: DataplaneEndpoint containing URL, auth, and pod context
            metrics: MetricsCollector instance for metrics tracking
            timeout: Request timeout in seconds
        """
        self.endpoint = endpoint
        self.base_url = endpoint.url
        self.timeout = timeout
        self.auth = (
            endpoint.dataplane_auth.username,
            endpoint.dataplane_auth.password.get_secret_value(),
        )

        # Initialize unified operations interface
        self.operations = DataplaneOperations(self.endpoint, metrics)

    @property
    def endpoint_context(self) -> str:
        """Get endpoint context for error reporting."""
        return f"{self.endpoint.url} (pod: {self.endpoint.pod_name or 'unknown'})"

    def get_endpoint_context(self) -> DataplaneEndpoint:
        """Get endpoint context object."""
        return self.endpoint

    # === High-level API Methods ===

    async def get_version(self) -> dict[str, Any]:
        """Get HAProxy version and runtime information.

        Returns:
            Dictionary containing version and runtime information

        Raises:
            DataplaneAPIError: If version retrieval fails
        """
        return await self.operations.validation.get_version()

    async def validate_configuration(self, config_content: str) -> None:
        """Validate HAProxy configuration without applying it.

        Args:
            config_content: The configuration content to validate

        Raises:
            ValidationError: If configuration validation fails
            DataplaneAPIError: If validation request fails
        """
        return await self.operations.validation.validate_configuration(config_content)

    async def deploy_configuration(
        self, config_content: str
    ) -> ValidationDeploymentResult:
        """Deploy HAProxy configuration with reload.

        Args:
            config_content: The configuration content to deploy

        Returns:
            Dictionary containing deployment results and timing

        Raises:
            ValidationError: If configuration validation fails
            DataplaneAPIError: If deployment fails
        """
        return await self.operations.validation.deploy_configuration(config_content)

    async def validate_and_deploy(self, config_content: str) -> ValidateAndDeployResult:
        """Validate configuration and deploy if valid.

        Args:
            config_content: Configuration content to validate and deploy

        Returns:
            Dictionary containing validation and deployment results

        Raises:
            ValidationError: If configuration validation fails
            DataplaneAPIError: If deployment fails
        """
        return await self.operations.validate_and_deploy(config_content)

    async def get_current_configuration(self) -> str | None:
        """Get the current HAProxy configuration.

        Returns:
            Current configuration content as string, or None if not available

        Raises:
            DataplaneAPIError: If configuration retrieval fails
        """
        return await self.operations.validation.get_current_configuration()

    async def sync_maps(
        self,
        maps: dict[str, str],
        operations: set[str] = {"create", "update", "delete"},
    ) -> StorageOperationResult:
        """Synchronize map files with HAProxy storage.

        Args:
            maps: Dictionary mapping map names to their content
            operations: Set of operations to perform ("create", "update", "delete")

        Returns:
            StorageOperationResult containing operation status and reload information

        Raises:
            DataplaneAPIError: If map synchronization fails
        """
        return await self.operations.storage.sync_maps(maps, operations)

    async def sync_certificates(
        self,
        certificates: dict[str, str],
        operations: set[str] = {"create", "update", "delete"},
    ) -> StorageOperationResult:
        """Synchronize SSL certificates with HAProxy storage.

        Args:
            certificates: Dictionary mapping certificate names to their content
            operations: Set of operations to perform ("create", "update", "delete")

        Returns:
            StorageOperationResult containing operation status and reload information

        Raises:
            DataplaneAPIError: If certificate synchronization fails
        """
        return await self.operations.storage.sync_certificates(certificates, operations)

    async def sync_acls(
        self,
        acls: dict[str, str],
        operations: set[str] = {"create", "update", "delete"},
    ) -> StorageOperationResult:
        """Synchronize ACL files with HAProxy storage.

        Args:
            acls: Dictionary mapping ACL names to their content
            operations: Set of operations to perform ("create", "update", "delete")

        Returns:
            StorageOperationResult containing operation status and reload information

        Raises:
            DataplaneAPIError: If ACL synchronization fails
        """
        return await self.operations.storage.sync_acls(acls, operations)

    async def sync_files(
        self,
        files: dict[str, str],
        operations: set[str] = {"create", "update", "delete"},
    ) -> StorageOperationResult:
        """Synchronize generic files with HAProxy storage.

        Args:
            files: Dictionary mapping file names to their content
            operations: Set of operations to perform ("create", "update", "delete")

        Returns:
            StorageOperationResult containing operation status and reload information

        Raises:
            DataplaneAPIError: If file synchronization fails
        """
        return await self.operations.storage.sync_files(files, operations)

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
        return await self.operations.runtime.apply_runtime_map_operations(
            map_name, operations
        )

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
        return await self.operations.runtime.apply_runtime_acl_operations(
            acl_id, operations
        )

    async def update_server_state(
        self, backend_name: str, server_name: str, state: str
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
        return await self.operations.runtime.update_server_state(
            backend_name, server_name, state
        )

    async def deploy_structured_configuration(
        self, changes: list[ConfigChange], use_transaction: bool = True
    ) -> StructuredDeploymentResult:
        """Deploy structured configuration changes.

        Args:
            changes: List of configuration changes to apply
            use_transaction: Whether to use transactions for atomic changes

        Returns:
            Dictionary containing deployment results

        Raises:
            DataplaneAPIError: If deployment fails
        """
        return await self.operations.deploy_structured_configuration(
            changes, use_transaction
        )

    async def fetch_structured_configuration(self) -> dict[str, Any]:
        """Fetch complete structured configuration components from HAProxy instance.

        Returns:
            Dictionary containing all configuration sections and their nested elements

        Raises:
            DataplaneAPIError: If fetching configuration fails
        """
        return await self.operations.config.fetch_structured_configuration()

    async def get_cluster_info(self) -> dict[str, Any]:
        """Get comprehensive cluster information.

        Returns:
            Dictionary containing version, storage, and configuration info

        Raises:
            DataplaneAPIError: If information retrieval fails
        """
        return await self.operations.get_cluster_info()

    # === Transaction Operations ===

    async def start_transaction(self) -> str:
        """Start a new transaction for configuration changes.

        Returns:
            Transaction ID for the new transaction

        Raises:
            DataplaneAPIError: If transaction creation fails
        """
        return await self.operations.transactions.start()

    async def commit_transaction(self, transaction_id: str) -> dict[str, Any]:
        """Commit a transaction to apply configuration changes.

        Args:
            transaction_id: ID of the transaction to commit

        Returns:
            Dictionary containing commit results

        Raises:
            DataplaneAPIError: If transaction commit fails
        """
        return await self.operations.transactions.commit(transaction_id)

    async def rollback_transaction(self, transaction_id: str) -> None:
        """Rollback a transaction to discard configuration changes.

        Args:
            transaction_id: ID of the transaction to rollback

        Raises:
            DataplaneAPIError: If transaction rollback fails
        """
        return await self.operations.transactions.rollback(transaction_id)

    # === Bulk Operations ===

    async def sync_storage_resources(
        self,
        maps: dict[str, str] | None = None,
        certificates: dict[str, str] | None = None,
        acls: dict[str, str] | None = None,
        files: dict[str, str] | None = None,
    ) -> ReloadInfo:
        """Synchronize multiple storage resource types.

        Args:
            maps: Map files to synchronize (name -> content)
            certificates: SSL certificates to synchronize (name -> content)
            acls: ACL files to synchronize (name -> content)
            files: Other files to synchronize (name -> content)

        Returns:
            ReloadInfo aggregated from all storage operations

        Raises:
            DataplaneAPIError: If any synchronization fails
        """
        return await self.operations.sync_storage_resources(
            maps, certificates, acls, files
        )

    async def apply_runtime_changes(
        self,
        map_changes: dict[str, list[MapChange]] | None = None,
        acl_changes: dict[str, list[MapChange]] | None = None,
        server_changes: list[dict[str, Any]] | None = None,
    ) -> ReloadInfo:
        """Apply runtime changes without HAProxy reload.

        Args:
            map_changes: Map changes grouped by map name
            acl_changes: ACL changes grouped by ACL ID
            server_changes: Server state changes

        Returns:
            ReloadInfo aggregated from all runtime operations

        Raises:
            DataplaneAPIError: If any runtime operation fails
        """
        return await self.operations.apply_runtime_changes(
            map_changes, acl_changes, server_changes
        )
