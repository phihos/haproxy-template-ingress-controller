"""
Unified operations interface for HAProxy Dataplane API.

This module provides the DataplaneOperations class which coordinates between
specialized API modules (ConfigAPI, RuntimeAPI, StorageAPI, ValidationAPI)
to offer a high-level, unified interface for HAProxy configuration management.

The operations layer abstracts the complexity of working with multiple API
modules and provides transaction management, error handling, and consistent
behavior across different types of dataplane operations.
"""

import asyncio
import logging
from collections.abc import Callable
from dataclasses import asdict
from typing import Any, Dict, List, Optional, TYPE_CHECKING

from haproxy_dataplane_v3 import AuthenticatedClient

if TYPE_CHECKING:
    from .endpoint import DataplaneEndpoint

from haproxy_template_ic.metrics import get_metrics_collector
from haproxy_template_ic.tracing import record_span_event
from .types import (
    ConfigChange,
    DataplaneAPIError,
    MapChange,
    StructuredDeploymentResult,
    ValidateAndDeployResult,
)
from .config_api import ConfigAPI
from .runtime_api import RuntimeAPI
from .storage_api import StorageAPI
from .transaction_api import TransactionAPI
from .validation_api import ValidationAPI
from .utils import (
    handle_dataplane_errors,
    get_configuration_version,
    extract_exception_origin,
)

__all__ = [
    "DataplaneOperations",
]

logger = logging.getLogger(__name__)


class DataplaneOperations:
    """Unified operations interface for HAProxy Dataplane API.

    This class combines configuration, runtime, storage, and validation operations
    into a single interface, providing a simplified API for common dataplane tasks.
    """

    def __init__(
        self,
        get_client: Callable[[], AuthenticatedClient],
        endpoint: "DataplaneEndpoint",
    ):
        """Initialize unified operations.

        Args:
            get_client: Factory function that returns an authenticated client
            endpoint: Dataplane endpoint for error context
        """
        self._get_client = get_client
        self.endpoint = endpoint

        # Initialize specialized API modules
        self.config = ConfigAPI(get_client, endpoint)
        self.runtime = RuntimeAPI(get_client, endpoint)
        self.storage = StorageAPI(get_client, endpoint)
        self.transactions = TransactionAPI(get_client, endpoint)
        self.validation = ValidationAPI(get_client, endpoint)

    # === Storage Operations ===

    @handle_dataplane_errors("sync_storage_resources")
    async def sync_storage_resources(
        self,
        maps: Optional[Dict[str, str]] = None,
        certificates: Optional[Dict[str, str]] = None,
        acls: Optional[Dict[str, str]] = None,
        files: Optional[Dict[str, str]] = None,
    ) -> None:
        """Synchronize multiple storage resource types.

        Args:
            maps: Map files to synchronize (name -> content)
            certificates: SSL certificates to synchronize (name -> content)
            acls: ACL files to synchronize (name -> content)
            files: Other files to synchronize (name -> content)

        Raises:
            DataplaneAPIError: If any synchronization fails
        """
        metrics = get_metrics_collector()

        with metrics.time_dataplane_api_operation("sync_storage_resources"):
            tasks = []

            if maps:
                logger.info(f"Synchronizing {len(maps)} map files")
                tasks.append(self.storage.sync_maps(maps))

            if certificates:
                logger.info(f"Synchronizing {len(certificates)} certificates")
                tasks.append(self.storage.sync_certificates(certificates))

            # Note: ACL and general file sync would need additional API methods
            if acls:
                logger.warning("ACL file sync not yet implemented")

            if files:
                logger.warning("General file sync not yet implemented")

            # Execute all sync operations
            if tasks:
                try:
                    # Run all synchronization tasks
                    await asyncio.gather(*tasks)

                    record_span_event(
                        "storage_sync_complete",
                        {
                            "maps_count": len(maps) if maps else 0,
                            "certificates_count": len(certificates)
                            if certificates
                            else 0,
                        },
                    )
                    metrics.record_dataplane_api_request(
                        "sync_storage_resources", "success"
                    )
                    logger.info(
                        "Storage resource synchronization completed successfully"
                    )

                except Exception as e:
                    metrics.record_dataplane_api_request(
                        "sync_storage_resources", "error"
                    )
                    raise DataplaneAPIError(
                        f"Storage synchronization failed: {e}",
                        endpoint=self.endpoint,
                        operation="sync_storage_resources",
                        original_error=e,
                    ) from e

    # === Runtime Operations ===

    @handle_dataplane_errors("apply_runtime_changes")
    async def apply_runtime_changes(
        self,
        map_changes: Optional[Dict[str, List[MapChange]]] = None,
        acl_changes: Optional[Dict[str, List[MapChange]]] = None,
        server_changes: Optional[List[Dict[str, Any]]] = None,
    ) -> None:
        """Apply runtime changes without HAProxy reload.

        Args:
            map_changes: Map changes grouped by map name
            acl_changes: ACL changes grouped by ACL ID
            server_changes: Server state changes

        Raises:
            DataplaneAPIError: If any runtime operation fails
        """
        metrics = get_metrics_collector()

        with metrics.time_dataplane_api_operation("apply_runtime_changes"):
            try:
                # Apply map changes
                if map_changes:
                    await self.runtime.bulk_map_updates(map_changes)

                # Apply ACL changes
                if acl_changes:
                    await self.runtime.bulk_acl_updates(acl_changes)

                # Apply server changes
                if server_changes:
                    for change in server_changes:
                        await self.runtime.update_server_state(
                            change["backend"], change["server"], change["state"]
                        )

                record_span_event(
                    "runtime_changes_applied",
                    {
                        "map_changes": len(map_changes) if map_changes else 0,
                        "acl_changes": len(acl_changes) if acl_changes else 0,
                        "server_changes": len(server_changes) if server_changes else 0,
                    },
                )
                metrics.record_dataplane_api_request("apply_runtime_changes", "success")
                logger.info("Runtime changes applied successfully")

            except Exception as e:
                metrics.record_dataplane_api_request("apply_runtime_changes", "error")
                raise DataplaneAPIError(
                    f"Runtime changes failed: {e}",
                    endpoint=self.endpoint,
                    operation="apply_runtime_changes",
                    original_error=e,
                ) from e

    # === Configuration Operations ===

    @handle_dataplane_errors("deploy_structured_configuration")
    async def deploy_structured_configuration(
        self,
        changes: List[ConfigChange],
        use_transaction: bool = True,
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
        metrics = get_metrics_collector()

        with metrics.time_dataplane_api_operation("deploy_structured_config"):
            if not changes:
                logger.info("No configuration changes to deploy")
                return StructuredDeploymentResult(
                    changes_applied=0,
                    transaction_used=False,
                    version="unchanged",
                )

            logger.info(f"Deploying {len(changes)} structured configuration changes")

            try:
                if use_transaction:
                    return await self._deploy_with_transaction(changes)
                else:
                    return await self._deploy_without_transaction(changes)

            except Exception as e:
                metrics.record_dataplane_api_request(
                    "deploy_structured_config", "error"
                )

                # Extract detailed origin information for debugging
                origin_details = extract_exception_origin(e)

                raise DataplaneAPIError(
                    f"Structured configuration deployment failed: {e}\n{origin_details}",
                    endpoint=self.endpoint,
                    operation="deploy_structured_config",
                    original_error=e,
                ) from e

    async def _deploy_with_transaction(
        self, changes: List[ConfigChange]
    ) -> StructuredDeploymentResult:
        """Deploy changes within a transaction."""
        transaction_id = None

        try:
            # Start transaction
            transaction_id = await self.transactions.start()

            # Get current version for changes
            client = self._get_client()
            version = await get_configuration_version(client)
            if version is None:
                raise DataplaneAPIError(
                    "Unable to get configuration version for transaction",
                    endpoint=self.endpoint,
                    operation="deploy_with_transaction",
                )

            # Apply all changes
            for change in changes:
                await self.config.apply_config_change(change, version, transaction_id)

            # Commit transaction
            commit_result = await self.transactions.commit(transaction_id)

            # Get final configuration version after commit
            final_version = await get_configuration_version(client)

            result = StructuredDeploymentResult(
                changes_applied=len(changes),
                transaction_used=True,
                transaction_id=transaction_id,
                version=str(final_version) if final_version is not None else "unknown",
            )

            record_span_event(
                "structured_config_deployed",
                {
                    **asdict(result),
                    **asdict(commit_result),
                },
            )
            return result

        except Exception:
            # Rollback on failure
            if transaction_id:
                try:
                    await self.transactions.rollback(transaction_id)
                    logger.info(
                        f"Rolled back transaction {transaction_id} due to error"
                    )
                except Exception as rollback_error:
                    logger.error(
                        f"Failed to rollback transaction {transaction_id}: {rollback_error}"
                    )
            raise

    async def _deploy_without_transaction(
        self, changes: List[ConfigChange]
    ) -> StructuredDeploymentResult:
        """Deploy changes without transaction (less atomic)."""
        client = self._get_client()
        version = await get_configuration_version(client)

        applied_changes = 0

        for change in changes:
            try:
                if version is not None:
                    await self.config.apply_config_change(change, version)
                    applied_changes += 1
            except Exception as e:
                logger.error(f"Failed to apply change {change}: {e}")
                # Continue with remaining changes

        # Get final configuration version after changes
        final_version = await get_configuration_version(client)

        result = StructuredDeploymentResult(
            changes_applied=applied_changes,
            transaction_used=False,
            version=str(final_version) if final_version is not None else "unknown",
            total_changes=len(changes),
        )

        record_span_event("structured_config_deployed", asdict(result))
        return result

    # === Validation Operations ===

    @handle_dataplane_errors("validate_and_deploy")
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
        metrics = get_metrics_collector()

        with metrics.time_dataplane_api_operation("validate_and_deploy"):
            # First validate
            await self.validation.validate_configuration(config_content)

            # Then deploy
            deployment_result = await self.validation.deploy_configuration(
                config_content
            )

            result = ValidateAndDeployResult(
                validation="success",
                deployment=deployment_result,
            )

            record_span_event("config_validated_and_deployed", asdict(result))
            metrics.record_dataplane_api_request("validate_and_deploy", "success")

            return result

    # === Information Operations ===

    @handle_dataplane_errors("get_cluster_info")
    async def get_cluster_info(self) -> Dict[str, Any]:
        """Get comprehensive cluster information.

        Returns:
            Dictionary containing version, storage, and configuration info

        Raises:
            DataplaneAPIError: If information retrieval fails
        """
        metrics = get_metrics_collector()

        with metrics.time_dataplane_api_operation("get_cluster_info"):
            try:
                # Get version information
                version_info = await self.validation.get_version()

                # Get storage information
                storage_info = await self.storage.get_storage_info()

                # Get current configuration
                current_config = await self.validation.get_current_configuration()
                config_size = len(current_config) if current_config else 0

                # Get structured configuration summary
                structured_config = await self.config.fetch_structured_configuration()

                result = {
                    "version": version_info,
                    "storage": storage_info,
                    "configuration": {
                        "current_size": config_size,
                        "structured_sections": {
                            section: len(items) if isinstance(items, list) else 1
                            for section, items in structured_config.items()
                            if items
                            and not section.startswith(
                                ("backend_", "frontend_", "global_")
                            )
                        },
                    },
                    "endpoint": self.endpoint,
                }

                metrics.record_dataplane_api_request("get_cluster_info", "success")
                return result

            except Exception as e:
                metrics.record_dataplane_api_request("get_cluster_info", "error")
                raise DataplaneAPIError(
                    f"Failed to get cluster info: {e}",
                    endpoint=self.endpoint,
                    operation="get_cluster_info",
                    original_error=e,
                ) from e
