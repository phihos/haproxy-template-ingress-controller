"""
Unified operations interface for HAProxy Dataplane API.

This module provides the DataplaneOperations class which coordinates between
specialized API modules (ConfigAPI, RuntimeAPI, StorageAPI, ValidationAPI)
to offer a high-level, unified interface for HAProxy configuration management.

The operations layer abstracts the complexity of working with multiple API
modules and provides transaction management, error handling, and consistent
behavior across different types of dataplane operations.
"""

import logging
from dataclasses import asdict
from typing import Any

from haproxy_template_ic.core.logging import autolog
from haproxy_template_ic.metrics import MetricsCollector
from haproxy_template_ic.tracing import record_span_event

from .adapter import ReloadInfo, get_configuration_version
from .config_api import ConfigAPI
from .endpoint import DataplaneEndpoint
from .runtime_api import RuntimeAPI
from .storage_api import StorageAPI
from .transaction_api import TransactionAPI
from .types import (
    ConfigChange,
    DataplaneAPIError,
    MapChange,
    StructuredDeploymentResult,
    ValidateAndDeployResult,
)
from .utils import (
    extract_exception_origin,
    handle_dataplane_errors,
)
from .validation_api import ValidationAPI

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
        endpoint: DataplaneEndpoint,
        metrics: MetricsCollector,
    ):
        """Initialize unified operations.

        Args:
            endpoint: Dataplane endpoint for error context
            metrics: MetricsCollector instance for metrics tracking
        """
        self.endpoint = endpoint
        self.metrics = metrics

        self.config = ConfigAPI(endpoint, metrics)
        self.runtime = RuntimeAPI(endpoint, metrics)
        self.storage = StorageAPI(endpoint, metrics)
        self.transactions = TransactionAPI(endpoint, metrics)
        self.validation = ValidationAPI(endpoint, metrics)

    # === Storage Operations ===

    @handle_dataplane_errors("sync_storage_resources")
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
        with self.metrics.time_dataplane_api_operation("sync_storage_resources"):
            reload_infos = []

            if maps:
                logger.info(f"Synchronizing {len(maps)} map files")
                result = await self.storage.sync_maps(maps)
                reload_infos.append(result.reload_info)

            if certificates:
                logger.info(f"Synchronizing {len(certificates)} certificates")
                result = await self.storage.sync_certificates(certificates)
                reload_infos.append(result.reload_info)

            if acls:
                logger.info(f"Synchronizing {len(acls)} ACL files")
                result = await self.storage.sync_acls(acls)
                reload_infos.append(result.reload_info)

            if files:
                logger.info(f"Synchronizing {len(files)} general files")
                result = await self.storage.sync_files(files)
                reload_infos.append(result.reload_info)

            # Record success metrics and return aggregated reload information
            record_span_event(
                "storage_sync_complete",
                {
                    "maps_count": len(maps) if maps else 0,
                    "certificates_count": len(certificates) if certificates else 0,
                    "acls_count": len(acls) if acls else 0,
                    "files_count": len(files) if files else 0,
                },
            )
            self.metrics.record_dataplane_api_request(
                "sync_storage_resources", "success"
            )
            logger.info("Storage resource synchronization completed successfully")

            return ReloadInfo.combine(*reload_infos)

    # === Runtime Operations ===

    @handle_dataplane_errors("apply_runtime_changes")
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
        with self.metrics.time_dataplane_api_operation("apply_runtime_changes"):
            reload_infos = []

            # Apply map changes
            if map_changes:
                result = await self.runtime.bulk_map_updates(map_changes)
                reload_infos.append(result.reload_info)

            # Apply ACL changes
            if acl_changes:
                result = await self.runtime.bulk_acl_updates(acl_changes)
                reload_infos.append(result.reload_info)

            # Apply server changes
            if server_changes:
                for change in server_changes:
                    result = await self.runtime.update_server_state(
                        change["backend"], change["server"], change["state"]
                    )
                    reload_infos.append(result.reload_info)

            record_span_event(
                "runtime_changes_applied",
                {
                    "map_changes": len(map_changes) if map_changes else 0,
                    "acl_changes": len(acl_changes) if acl_changes else 0,
                    "server_changes": len(server_changes) if server_changes else 0,
                },
            )
            self.metrics.record_dataplane_api_request(
                "apply_runtime_changes", "success"
            )
            logger.info("Runtime changes applied successfully")

            return ReloadInfo.combine(*reload_infos)

    # === Configuration Operations ===

    @handle_dataplane_errors("deploy_structured_configuration")
    async def deploy_structured_configuration(
        self,
        changes: list[ConfigChange],
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
        with self.metrics.time_dataplane_api_operation("deploy_structured_config"):
            if not changes:
                logger.info("No configuration changes to deploy")
                return StructuredDeploymentResult(
                    changes_applied=0,
                    transaction_used=False,
                    version="unchanged",
                    reload_info=ReloadInfo(),  # No reload for empty changes
                )

            logger.info(f"Deploying {len(changes)} structured configuration changes")

            try:
                if use_transaction:
                    return await self._deploy_with_transaction(changes)
                else:
                    return await self._deploy_without_transaction(changes)

            except Exception as e:
                self.metrics.record_dataplane_api_request(
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

    @autolog()
    async def _deploy_with_transaction(
        self, changes: list[ConfigChange]
    ) -> StructuredDeploymentResult:
        """Deploy changes within a transaction, with runtime-first optimization for servers."""
        # Separate server changes for runtime API optimization
        server_changes, other_changes = self._separate_server_changes(changes)

        logger.debug(
            f"🔄 Separated changes: {len(server_changes)} server changes (runtime-attempted), "
            f"{len(other_changes)} other changes (transaction-required)"
        )

        # Try runtime API for server changes first (without transaction)
        runtime_failed_servers = await self._try_server_runtime_deployment(
            server_changes
        )

        # Combine failed servers with other changes for transaction
        transaction_changes = other_changes + runtime_failed_servers

        if not transaction_changes:
            # All changes were successful via runtime API
            return await self._create_runtime_only_result(server_changes)

        # Deploy remaining changes via transaction
        transaction_id = None

        try:
            transaction_id = await self.transactions.start()

            response = await get_configuration_version(endpoint=self.endpoint)
            version = response.content
            # Apply all transaction changes
            for change in transaction_changes:
                await self.config.apply_config_change(change, version, transaction_id)

            # Commit transaction
            commit_result = await self.transactions.commit(transaction_id)

            final_version_response = await get_configuration_version(
                endpoint=self.endpoint
            )

            successful_runtime_servers = len(server_changes) - len(
                runtime_failed_servers
            )
            total_changes_applied = (
                len(transaction_changes) + successful_runtime_servers
            )

            result = StructuredDeploymentResult(
                changes_applied=total_changes_applied,
                transaction_used=True,
                transaction_id=transaction_id,
                version=str(final_version_response.content)
                if final_version_response.content is not None
                else "unknown",
                reload_info=commit_result.reload_info,  # Propagate reload info from transaction commit
            )

            if successful_runtime_servers > 0:
                logger.info(
                    f"✅ {successful_runtime_servers} server changes applied via runtime API, "
                    f"{len(transaction_changes)} changes applied via transaction"
                )

            record_span_event(
                "structured_config_deployed",
                {
                    **asdict(result),
                    **asdict(commit_result),
                    "runtime_servers_applied": successful_runtime_servers,
                    "transaction_changes_applied": len(transaction_changes),
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

    def _separate_server_changes(
        self, changes: list[ConfigChange]
    ) -> tuple[list[ConfigChange], list[ConfigChange]]:
        """Separate server changes from other changes for runtime API optimization.

        This method intelligently routes server operations:
        - Server CREATE in new backends → transaction (runtime API will fail)
        - Server CREATE in existing backends → runtime API attempt
        - Server UPDATE/DELETE → runtime API attempt

        Args:
            changes: List of configuration changes

        Returns:
            Tuple of (runtime_eligible_server_changes, transaction_required_changes)
        """
        from .types import ConfigElementType, ConfigSectionType, ConfigChangeType

        # Identify backends being created in this deployment
        new_backends = self._get_backends_being_created(changes)

        runtime_eligible_servers = []
        transaction_required_changes = []

        for change in changes:
            if (
                change.element_type == ConfigElementType.SERVER
                and change.section_type == ConfigSectionType.BACKEND
            ):
                # Check if this server CREATE is in a new backend
                if (
                    change.change_type == ConfigChangeType.CREATE
                    and change.section_name in new_backends
                ):
                    # Server CREATE in new backend → must use transaction
                    logger.debug(
                        f"🔄 Server CREATE in new backend '{change.section_name}' → transaction required"
                    )
                    transaction_required_changes.append(change)
                else:
                    # Server UPDATE/DELETE or CREATE in existing backend → try runtime API
                    runtime_eligible_servers.append(change)
            else:
                # All non-server changes go through transaction
                transaction_required_changes.append(change)

        return runtime_eligible_servers, transaction_required_changes

    def _get_backends_being_created(self, changes: list[ConfigChange]) -> set[str]:
        """Identify backend names that are being created in this deployment.

        Args:
            changes: List of configuration changes

        Returns:
            Set of backend names being created
        """
        from .types import ConfigSectionType, ConfigChangeType

        new_backends = set()

        for change in changes:
            if (
                change.element_type is None  # Section-level change, not element-level
                and change.section_type == ConfigSectionType.BACKEND
                and change.change_type == ConfigChangeType.CREATE
            ):
                new_backends.add(change.section_name)

        if new_backends:
            logger.debug(
                f"🏗️ Detected {len(new_backends)} new backends: {sorted(new_backends)}"
            )

        return new_backends

    @autolog()
    async def _try_server_runtime_deployment(
        self, server_changes: list[ConfigChange]
    ) -> list[ConfigChange]:
        """Try to deploy server changes via runtime API (no transaction).

        Args:
            server_changes: List of server changes to attempt via runtime API

        Returns:
            List of server changes that failed runtime API (need transaction fallback)
        """
        if not server_changes:
            return []

        logger.info(
            f"🏃 Attempting {len(server_changes)} server changes via runtime API"
        )

        runtime_failed_servers = []
        version_response = await get_configuration_version(endpoint=self.endpoint)
        version = version_response.content

        for i, change in enumerate(server_changes):
            logger.debug(
                f"🏃 Applying server change {i + 1}/{len(server_changes)}: {change}"
            )
            try:
                # Try to apply server change without transaction (enables runtime API)
                await self.config.apply_config_change(change, version)
            except Exception as server_error:
                logger.warning(
                    f"⚠️  Runtime API failed for server {change.element_id}, will retry via transaction: {server_error}"
                )
                runtime_failed_servers.append(change)

        # Log results
        if runtime_failed_servers:
            logger.info(
                f"🔄 {len(runtime_failed_servers)} server changes failed runtime API, will retry via transaction"
            )

        successful_runtime_servers = len(server_changes) - len(runtime_failed_servers)
        if successful_runtime_servers > 0:
            logger.info(
                f"✅ {successful_runtime_servers} server changes applied via runtime API"
            )

        return runtime_failed_servers

    @autolog()
    async def _create_runtime_only_result(
        self, server_changes: list[ConfigChange]
    ) -> StructuredDeploymentResult:
        """Create result for when all changes were applied via runtime API.

        Args:
            server_changes: List of server changes that were applied via runtime API

        Returns:
            Deployment result indicating no transaction was used
        """
        logger.info(
            "✅ All changes were server changes applied via runtime API - no transaction needed"
        )

        final_version_response = await get_configuration_version(endpoint=self.endpoint)

        result = StructuredDeploymentResult(
            changes_applied=len(server_changes),
            transaction_used=False,  # Runtime API was used, no transaction
            version=str(final_version_response.content)
            if final_version_response.content is not None
            else "unknown",
            reload_info=ReloadInfo(),  # No reload for runtime-only changes
        )

        record_span_event(
            "runtime_only_deployment",
            {
                **asdict(result),
                "server_changes_count": len(server_changes),
            },
        )

        return result

    async def _deploy_without_transaction(
        self, changes: list[ConfigChange]
    ) -> StructuredDeploymentResult:
        """Deploy changes without transaction (less atomic)."""
        response = await get_configuration_version(endpoint=self.endpoint)
        version = response.content

        applied_changes = 0
        reload_infos = []

        for change in changes:
            try:
                if version is not None:
                    change_result = await self.config.apply_config_change(
                        change, version
                    )
                    applied_changes += 1
                    reload_infos.append(change_result.reload_info)
            except Exception as e:
                logger.error(f"Failed to apply change {change}: {e}")
                # Continue with remaining changes

        final_version_response = await get_configuration_version(endpoint=self.endpoint)

        deployment_result = StructuredDeploymentResult(
            changes_applied=applied_changes,
            transaction_used=False,
            version=str(final_version_response.content)
            if final_version_response.content is not None
            else "unknown",
            total_changes=len(changes),
            reload_info=ReloadInfo.combine(
                *reload_infos
            ),  # Aggregate reload info from individual changes
        )

        record_span_event("structured_config_deployed", asdict(deployment_result))
        return deployment_result

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
        with self.metrics.time_dataplane_api_operation("validate_and_deploy"):
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
            self.metrics.record_dataplane_api_request("validate_and_deploy", "success")

            return result

    # === Information Operations ===

    @handle_dataplane_errors("get_cluster_info")
    async def get_cluster_info(self) -> dict[str, Any]:
        """Get comprehensive cluster information.

        Returns:
            Dictionary containing version, storage, and configuration info

        Raises:
            DataplaneAPIError: If information retrieval fails
        """
        with self.metrics.time_dataplane_api_operation("get_cluster_info"):
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

                self.metrics.record_dataplane_api_request("get_cluster_info", "success")
                return result

            except Exception as e:
                self.metrics.record_dataplane_api_request("get_cluster_info", "error")
                raise DataplaneAPIError(
                    f"Failed to get cluster info: {e}",
                    endpoint=self.endpoint,
                    operation="get_cluster_info",
                    original_error=e,
                ) from e
