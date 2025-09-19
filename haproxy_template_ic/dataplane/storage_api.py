"""
Storage API operations for HAProxy Dataplane API.

This module provides the StorageAPI class for managing HAProxy storage resources
including map files, SSL certificates, and general files. Supports content-based
synchronization with change detection and proper MIME type handling.

Key features:
- Map file synchronization with content hashing
- SSL certificate management with PEM format validation
- Generic file storage operations
- Storage information retrieval and resource listing
- Content-based change detection to minimize unnecessary updates
"""

import io
import logging
from collections.abc import Callable
from typing import Any, TYPE_CHECKING

from haproxy_dataplane_v3 import AuthenticatedClient
from haproxy_dataplane_v3.models.create_storage_general_file_body import (
    CreateStorageGeneralFileBody,
)
from haproxy_dataplane_v3.models.create_storage_map_file_body import (
    CreateStorageMapFileBody,
)
from haproxy_dataplane_v3.models.create_storage_ssl_certificate_body import (
    CreateStorageSSLCertificateBody,
)
from haproxy_dataplane_v3.models.general_use_file import GeneralUseFile
from haproxy_dataplane_v3.models.map_file import MapFile
from haproxy_dataplane_v3.models.replace_storage_general_file_body import (
    ReplaceStorageGeneralFileBody,
)
from haproxy_dataplane_v3.models.ssl_file import SSLFile
from haproxy_dataplane_v3.types import UNSET, File

from haproxy_template_ic.core.logging import autolog, log_resource_operation

if TYPE_CHECKING:
    from .endpoint import DataplaneEndpoint

# Storage APIs
from haproxy_dataplane_v3.api.storage import (
    create_storage_map_file,
    create_storage_ssl_certificate,
    create_storage_general_file,
    delete_storage_map,
    delete_storage_ssl_certificate,
    delete_storage_general_file,
    get_all_storage_map_files,
    get_all_storage_ssl_certificates,
    get_all_storage_general_files,
    get_one_storage_map,
    get_one_storage_ssl_certificate,
    get_one_storage_general_file,
    replace_storage_map_file,
    replace_storage_ssl_certificate,
    replace_storage_general_file,
)

from haproxy_template_ic.metrics import get_metrics_collector
from haproxy_template_ic.tracing import record_span_event, set_span_error
from .types import (
    CreateOperationResult,
    DataplaneAPIError,
    DeleteOperationResult,
    UpdateOperationResult,
    compute_content_hash,
    extract_hash_from_description,
    ReloadInfo,
    StorageOperationResult,
)
from .utils import handle_dataplane_errors, _log_fetch_error, check_dataplane_response

__all__ = [
    "StorageAPI",
]

logger = logging.getLogger(__name__)


def _convert_unset_to_none(value: Any) -> str | None:
    """Convert Unset values from dataplane API to None for type safety."""
    return None if value is UNSET else value


class StorageAPI:
    """Storage API operations for HAProxy Dataplane API."""

    def __init__(
        self,
        get_client: Callable[[], AuthenticatedClient],
        endpoint: "DataplaneEndpoint",
    ):
        """Initialize storage API.

        Args:
            get_client: Factory function that returns an authenticated client
            endpoint: Dataplane endpoint for error context
        """
        self._get_client = get_client
        self.endpoint = endpoint

    def _extract_storage_content(self, storage_item) -> str | None:
        """Extract content from HAProxy storage API response.

        Args:
            storage_item: Response from get_one_storage_* API calls

        Returns:
            Decoded content string or None if extraction fails
        """
        if not storage_item or not hasattr(storage_item, "payload"):
            return None
        try:
            content = storage_item.payload.read()
            if hasattr(storage_item.payload, "seek"):
                storage_item.payload.seek(0)
            return content.decode("utf-8")
        except Exception:
            return None

    @handle_dataplane_errors("sync_maps")
    @autolog()
    async def sync_maps(self, maps: dict[str, str]) -> StorageOperationResult:
        """Synchronize map files with HAProxy storage.

        Args:
            maps: Dictionary mapping map names to their content

        Returns:
            StorageOperationResult containing operation status and reload information

        Raises:
            DataplaneAPIError: If map synchronization fails
        """
        if not maps:
            logger.debug("No maps to synchronize")
            return StorageOperationResult(
                operation_applied=False,
                reload_info=ReloadInfo(),
            )

        metrics = get_metrics_collector()
        client = self._get_client()

        logger.info(f"Synchronizing {len(maps)} map files")

        # Get existing maps for comparison
        try:
            raw_response = await get_all_storage_map_files.asyncio(client=client)
            existing_maps = (
                check_dataplane_response(
                    raw_response, "get_all_storage_map_files", self.endpoint
                )
                or []
            )
            existing_map_names = {
                m.storage_name for m in existing_maps if m.storage_name
            }
        except Exception as e:
            _log_fetch_error("existing maps", "", e)
            existing_maps = []
            existing_map_names = set()

        maps_to_create = set(maps.keys()) - existing_map_names
        maps_to_update = set(maps.keys()) & existing_map_names
        maps_to_delete = existing_map_names - set(maps.keys())

        reload_infos = []

        for map_name in maps_to_create:
            create_result = await self._create_map(
                client, map_name, maps[map_name], metrics
            )
            reload_infos.append(create_result.reload_info)

        actual_maps_updated = 0
        for map_name in maps_to_update:
            existing_map = next(
                (m for m in existing_maps if m.storage_name == map_name), None
            )
            if existing_map is None:
                raise RuntimeError(f"Map {map_name} should exist in existing_maps")
            update_result = await self._update_map_if_changed(
                client, map_name, maps[map_name], existing_map, metrics
            )
            reload_infos.append(update_result.reload_info)
            if update_result.content_changed:
                actual_maps_updated += 1

        for map_name in maps_to_delete:
            delete_result = await self._delete_map(client, map_name, metrics)
            reload_infos.append(delete_result.reload_info)

        logger.info(
            f"Map sync complete: {len(maps_to_create)} created, "
            f"{actual_maps_updated} updated, {len(maps_to_delete)} deleted"
        )

        has_creates = len(maps_to_create) > 0
        has_updates = actual_maps_updated > 0
        has_deletes = len(maps_to_delete) > 0
        operations_performed = has_creates or has_updates or has_deletes

        combined_reload_info = ReloadInfo.combine(*reload_infos)

        return StorageOperationResult(
            operation_applied=operations_performed,
            reload_info=combined_reload_info,
        )

    @handle_dataplane_errors("sync_certificates")
    @autolog()
    async def sync_certificates(
        self, certificates: dict[str, str]
    ) -> StorageOperationResult:
        """Synchronize SSL certificates with HAProxy storage.

        Args:
            certificates: Dictionary mapping certificate names to their content

        Returns:
            StorageOperationResult containing operation status and reload information

        Raises:
            DataplaneAPIError: If certificate synchronization fails
        """
        if not certificates:
            logger.debug("No certificates to synchronize")
            return StorageOperationResult(
                operation_applied=False,
                reload_info=ReloadInfo(),
            )

        metrics = get_metrics_collector()
        client = self._get_client()

        logger.info(f"Synchronizing {len(certificates)} SSL certificates")

        # Get existing certificates for comparison
        try:
            raw_response = await get_all_storage_ssl_certificates.asyncio(client=client)
            existing_certs = (
                check_dataplane_response(
                    raw_response, "get_all_storage_ssl_certificates", self.endpoint
                )
                or []
            )
            existing_cert_names = {
                c.storage_name for c in existing_certs if c.storage_name
            }
        except Exception as e:
            _log_fetch_error("existing certificates", "", e)
            existing_certs = []
            existing_cert_names = set()

        certs_to_create = set(certificates.keys()) - existing_cert_names
        certs_to_update = set(certificates.keys()) & existing_cert_names
        certs_to_delete = existing_cert_names - set(certificates.keys())

        reload_infos = []

        for cert_name in certs_to_create:
            create_result = await self._create_certificate(
                client, cert_name, certificates[cert_name], metrics
            )
            reload_infos.append(create_result.reload_info)

        actual_certs_updated = 0
        for cert_name in certs_to_update:
            existing_cert = next(
                (c for c in existing_certs if c.storage_name == cert_name), None
            )
            if existing_cert is None:
                raise RuntimeError(
                    f"Certificate {cert_name} should exist in existing_certs"
                )
            update_result = await self._update_certificate_if_changed(
                client, cert_name, certificates[cert_name], existing_cert, metrics
            )
            reload_infos.append(update_result.reload_info)
            if update_result.content_changed:
                actual_certs_updated += 1

        for cert_name in certs_to_delete:
            delete_result = await self._delete_certificate(client, cert_name, metrics)
            reload_infos.append(delete_result.reload_info)

        logger.info(
            f"Certificate sync complete: {len(certs_to_create)} created, "
            f"{actual_certs_updated} updated, {len(certs_to_delete)} deleted"
        )

        operations_performed = (
            len(certs_to_create) > 0
            or actual_certs_updated > 0
            or len(certs_to_delete) > 0
        )

        combined_reload_info = ReloadInfo.combine(*reload_infos)

        return StorageOperationResult(
            operation_applied=operations_performed,
            reload_info=combined_reload_info,
        )

    async def _create_map(
        self, client: Any, map_name: str, content: str, metrics: Any
    ) -> CreateOperationResult:
        """Create a new map file."""
        with metrics.time_dataplane_api_operation("create_map"):
            try:
                content_hash = compute_content_hash(content)
                file_obj = File(
                    file_name=map_name,
                    payload=io.BytesIO(content.encode("utf-8")),
                )

                # Create proper body structure for API call with hash in description
                body = CreateStorageMapFileBody(file_upload=file_obj)
                body["description"] = content_hash

                response = await create_storage_map_file.asyncio_detailed(
                    client=client,
                    body=body,
                )
                reload_info = ReloadInfo.from_response(response, self.endpoint)

                record_span_event(
                    "map_created",
                    {
                        "name": map_name,
                        "size": len(content),
                        "hash": content_hash,
                    },
                )
                metrics.record_dataplane_api_request("create_map", "success")
                await log_resource_operation(
                    "Created",
                    "map",
                    map_name,
                    f"{len(content)} bytes",
                    reload_triggered=reload_info.reload_id is not None,
                )

                return CreateOperationResult(reload_info=reload_info)

            except Exception as e:
                metrics.record_dataplane_api_request("create_map", "error")
                set_span_error(e, f"Map creation failed: {map_name}")
                raise DataplaneAPIError(
                    f"Failed to create map {map_name}: {e}",
                    endpoint=self.endpoint,
                    operation="create_map",
                    original_error=e,
                ) from e

    async def _update_map_if_changed(
        self,
        client: Any,
        map_name: str,
        content: str,
        existing_map: "MapFile",
        metrics: Any,
    ) -> UpdateOperationResult:
        """Update map if content has changed.

        Returns:
            UpdateOperationResult with content_changed flag and reload information.
        """
        try:
            # Check if content changed using hash comparison
            content_hash = compute_content_hash(content)
            description = _convert_unset_to_none(existing_map.description)
            current_hash = extract_hash_from_description(description)

            if current_hash == content_hash:
                logger.debug(f"Map {map_name} unchanged, skipping update")
                return UpdateOperationResult(
                    content_changed=False, reload_info=ReloadInfo()
                )

            # Fallback to direct content comparison if no hash available
            if current_hash is None:
                try:
                    existing_resource = await get_one_storage_map.asyncio(
                        client=client, name=map_name
                    )
                    existing_content = self._extract_storage_content(existing_resource)

                    if existing_content == content:
                        logger.debug(
                            f"Map {map_name} unchanged (content comparison), skipping update"
                        )
                        return UpdateOperationResult(
                            content_changed=False, reload_info=ReloadInfo()
                        )
                except Exception as e:
                    logger.debug(
                        f"Failed to get existing map content for {map_name}: {e}"
                    )
                    # Continue with update if we can't compare content

            # Content changed, update the map
            with metrics.time_dataplane_api_operation("update_map"):
                response = await replace_storage_map_file.asyncio_detailed(
                    name=map_name,
                    client=client,
                    body=content,
                )
                reload_info = ReloadInfo.from_response(response, self.endpoint)

                record_span_event(
                    "map_updated",
                    {
                        "name": map_name,
                        "size": len(content),
                        "old_hash": current_hash,
                        "new_hash": content_hash,
                    },
                )
                metrics.record_dataplane_api_request("update_map", "success")
                await log_resource_operation(
                    "Updated",
                    "map",
                    map_name,
                    f"{len(content)} bytes",
                    reload_triggered=reload_info.reload_id is not None,
                )
                return UpdateOperationResult(
                    content_changed=True, reload_info=reload_info
                )

        except Exception as e:
            metrics.record_dataplane_api_request("update_map", "error")
            set_span_error(e, f"Map update failed: {map_name}")
            raise DataplaneAPIError(
                f"Failed to update map {map_name}: {e}",
                endpoint=self.endpoint,
                operation="update_map",
                original_error=e,
            ) from e

    async def _delete_map(
        self, client: Any, map_name: str, metrics: Any
    ) -> DeleteOperationResult:
        """Delete a map file."""
        with metrics.time_dataplane_api_operation("delete_map"):
            try:
                response = await delete_storage_map.asyncio_detailed(
                    client=client, name=map_name
                )
                reload_info = ReloadInfo.from_response(response, self.endpoint)

                record_span_event("map_deleted", {"name": map_name})
                metrics.record_dataplane_api_request("delete_map", "success")
                await log_resource_operation(
                    "Deleted",
                    "map",
                    map_name,
                    reload_triggered=reload_info.reload_id is not None,
                )

                return DeleteOperationResult(reload_info=reload_info)

            except Exception as e:
                metrics.record_dataplane_api_request("delete_map", "error")
                set_span_error(e, f"Map deletion failed: {map_name}")
                raise DataplaneAPIError(
                    f"Failed to delete map {map_name}: {e}",
                    endpoint=self.endpoint,
                    operation="delete_map",
                    original_error=e,
                ) from e

    async def _create_certificate(
        self, client: Any, cert_name: str, content: str, metrics: Any
    ) -> CreateOperationResult:
        """Create a new SSL certificate."""
        with metrics.time_dataplane_api_operation("create_certificate"):
            try:
                content_hash = compute_content_hash(content)
                file_obj = File(
                    file_name=cert_name,
                    payload=io.BytesIO(content.encode("utf-8")),
                )

                # Create proper body structure for API call with hash in description
                body = CreateStorageSSLCertificateBody(file_upload=file_obj)
                body["description"] = content_hash

                response = await create_storage_ssl_certificate.asyncio_detailed(
                    client=client,
                    body=body,
                )
                reload_info = ReloadInfo.from_response(response, self.endpoint)

                record_span_event(
                    "certificate_created",
                    {
                        "name": cert_name,
                        "size": len(content),
                        "hash": content_hash,
                    },
                )
                metrics.record_dataplane_api_request("create_certificate", "success")
                await log_resource_operation(
                    "Created",
                    "certificate",
                    cert_name,
                    f"{len(content)} bytes",
                    reload_triggered=reload_info.reload_id is not None,
                )

                return CreateOperationResult(reload_info=reload_info)

            except Exception as e:
                metrics.record_dataplane_api_request("create_certificate", "error")
                set_span_error(e, f"Certificate creation failed: {cert_name}")
                raise DataplaneAPIError(
                    f"Failed to create certificate {cert_name}: {e}",
                    endpoint=self.endpoint,
                    operation="create_certificate",
                    original_error=e,
                ) from e

    async def _update_certificate_if_changed(
        self,
        client: Any,
        cert_name: str,
        content: str,
        existing_cert: SSLFile,
        metrics: Any,
    ) -> UpdateOperationResult:
        """Update certificate if content has changed.

        Returns:
            True if certificate was updated, False if unchanged and skipped.
        """
        try:
            # Check if content changed using hash comparison
            content_hash = compute_content_hash(content)
            description = _convert_unset_to_none(existing_cert.description)
            current_hash = extract_hash_from_description(description)

            if current_hash == content_hash:
                logger.debug(f"Certificate {cert_name} unchanged, skipping update")
                return UpdateOperationResult(
                    content_changed=False, reload_info=ReloadInfo()
                )

            # Fallback to direct content comparison if no hash available
            if current_hash is None:
                try:
                    existing_resource = await get_one_storage_ssl_certificate.asyncio(
                        client=client, name=cert_name
                    )
                    existing_content = self._extract_storage_content(existing_resource)

                    if existing_content == content:
                        logger.debug(
                            f"Certificate {cert_name} unchanged (content comparison), skipping update"
                        )
                        return UpdateOperationResult(
                            content_changed=False, reload_info=ReloadInfo()
                        )
                except Exception as e:
                    logger.debug(
                        f"Failed to get existing certificate content for {cert_name}: {e}"
                    )
                    # Continue with update if we can't compare content

            # Content changed, update the certificate
            with metrics.time_dataplane_api_operation("update_certificate"):
                response = await replace_storage_ssl_certificate.asyncio_detailed(
                    name=cert_name,
                    client=client,
                    body=content,
                )
                reload_info = ReloadInfo.from_response(response, self.endpoint)

                record_span_event(
                    "certificate_updated",
                    {
                        "name": cert_name,
                        "size": len(content),
                        "old_hash": current_hash,
                        "new_hash": content_hash,
                    },
                )
                metrics.record_dataplane_api_request("update_certificate", "success")
                await log_resource_operation(
                    "Updated",
                    "certificate",
                    cert_name,
                    f"{len(content)} bytes",
                    reload_triggered=reload_info.reload_id is not None,
                )
                return UpdateOperationResult(
                    content_changed=True, reload_info=reload_info
                )

        except Exception as e:
            metrics.record_dataplane_api_request("update_certificate", "error")
            set_span_error(e, f"Certificate update failed: {cert_name}")
            raise DataplaneAPIError(
                f"Failed to update certificate {cert_name}: {e}",
                endpoint=self.endpoint,
                operation="update_certificate",
                original_error=e,
            ) from e

    async def _delete_certificate(
        self, client: Any, cert_name: str, metrics: Any
    ) -> DeleteOperationResult:
        """Delete an SSL certificate."""
        with metrics.time_dataplane_api_operation("delete_certificate"):
            try:
                response = await delete_storage_ssl_certificate.asyncio_detailed(
                    client=client, name=cert_name
                )
                reload_info = ReloadInfo.from_response(response, self.endpoint)

                record_span_event("certificate_deleted", {"name": cert_name})
                metrics.record_dataplane_api_request("delete_certificate", "success")
                await log_resource_operation(
                    "Deleted",
                    "certificate",
                    cert_name,
                    reload_triggered=reload_info.reload_id is not None,
                )

                return DeleteOperationResult(reload_info=reload_info)

            except Exception as e:
                metrics.record_dataplane_api_request("delete_certificate", "error")
                set_span_error(e, f"Certificate deletion failed: {cert_name}")
                raise DataplaneAPIError(
                    f"Failed to delete certificate {cert_name}: {e}",
                    endpoint=self.endpoint,
                    operation="delete_certificate",
                    original_error=e,
                ) from e

    @handle_dataplane_errors("get_storage_info")
    async def get_storage_info(self) -> dict[str, Any]:
        """Get information about stored files.

        Returns:
            Dictionary containing counts and names of stored files

        Raises:
            DataplaneAPIError: If fetching storage info fails
        """
        metrics = get_metrics_collector()
        client = self._get_client()

        with metrics.time_dataplane_api_operation("get_storage_info"):
            try:
                # Get maps with error handling
                maps_response = await get_all_storage_map_files.asyncio(client=client)
                maps = (
                    check_dataplane_response(
                        maps_response, "get_all_storage_map_files", self.endpoint
                    )
                    or []
                )

                # Get certificates with error handling
                certs_response = await get_all_storage_ssl_certificates.asyncio(
                    client=client
                )
                certificates = (
                    check_dataplane_response(
                        certs_response,
                        "get_all_storage_ssl_certificates",
                        self.endpoint,
                    )
                    or []
                )

                info = {
                    "maps": {
                        "count": len(maps),
                        "names": [m.storage_name for m in maps if m.storage_name],
                    },
                    "certificates": {
                        "count": len(certificates),
                        "names": [
                            c.storage_name for c in certificates if c.storage_name
                        ],
                    },
                }

                metrics.record_dataplane_api_request("get_storage_info", "success")
                return info

            except Exception as e:
                metrics.record_dataplane_api_request("get_storage_info", "error")
                raise DataplaneAPIError(
                    f"Failed to get storage info: {e}",
                    endpoint=self.endpoint,
                    operation="get_storage_info",
                    original_error=e,
                ) from e

    @handle_dataplane_errors("sync_acls")
    @autolog()
    async def sync_acls(self, acls: dict[str, str]) -> StorageOperationResult:
        """Synchronize ACL files with HAProxy storage.

        ACL files are stored as general files in HAProxy storage but also
        utilize runtime operations for dynamic updates without reloads.

        Args:
            acls: Dictionary mapping ACL names to their content

        Returns:
            StorageOperationResult containing operation status and reload information

        Raises:
            DataplaneAPIError: If ACL synchronization fails
        """
        if not acls:
            logger.debug("No ACL files to synchronize")
            return StorageOperationResult(
                operation_applied=False,
                reload_info=ReloadInfo(),
            )

        metrics = get_metrics_collector()
        client = self._get_client()

        logger.info(f"Synchronizing {len(acls)} ACL files")

        # Get existing general files to find ACL files
        try:
            raw_response = await get_all_storage_general_files.asyncio(client=client)
            existing_files = (
                check_dataplane_response(
                    raw_response, "get_all_storage_general_files", self.endpoint
                )
                or []
            )
            # Filter for ACL files (assuming .acl extension)
            existing_acl_names = {
                f.storage_name
                for f in existing_files
                if f.storage_name and f.storage_name.endswith(".acl")
            }
        except Exception as e:
            _log_fetch_error("existing ACL files", "", e)
            existing_files = []
            existing_acl_names = set()

        acls_to_create = set(acls.keys()) - existing_acl_names
        acls_to_update = set(acls.keys()) & existing_acl_names
        acls_to_delete = existing_acl_names - set(acls.keys())

        reload_infos = []

        for acl_name in acls_to_create:
            create_result = await self._create_acl_file(
                client, acl_name, acls[acl_name], metrics
            )
            reload_infos.append(create_result.reload_info)

        actual_acls_updated = 0
        for acl_name in acls_to_update:
            existing_acl = next(
                (f for f in existing_files if f.storage_name == acl_name), None
            )
            if existing_acl is None:
                raise RuntimeError(
                    f"ACL file {acl_name} should exist in existing_files"
                )
            update_result = await self._update_acl_file_if_changed(
                client, acl_name, acls[acl_name], existing_acl, metrics
            )
            reload_infos.append(update_result.reload_info)
            if update_result.content_changed:
                actual_acls_updated += 1

        for acl_name in acls_to_delete:
            delete_result = await self._delete_acl_file(client, acl_name, metrics)
            reload_infos.append(delete_result.reload_info)

        logger.info(
            f"ACL sync complete: {len(acls_to_create)} created, "
            f"{actual_acls_updated} updated, {len(acls_to_delete)} deleted"
        )

        operations_performed = (
            len(acls_to_create) > 0
            or actual_acls_updated > 0
            or len(acls_to_delete) > 0
        )

        combined_reload_info = ReloadInfo.combine(*reload_infos)

        return StorageOperationResult(
            operation_applied=operations_performed,
            reload_info=combined_reload_info,
        )

    async def _create_acl_file(
        self, client: Any, acl_name: str, content: str, metrics: Any
    ) -> CreateOperationResult:
        """Create a new ACL file using general file storage."""
        with metrics.time_dataplane_api_operation("create_acl"):
            try:
                content_hash = compute_content_hash(content)
                file_obj = File(
                    file_name=acl_name,
                    payload=io.BytesIO(content.encode("utf-8")),
                )

                # Create proper body structure for API call with hash in description
                body = CreateStorageGeneralFileBody(file_upload=file_obj)
                body["description"] = content_hash

                response = await create_storage_general_file.asyncio_detailed(
                    client=client,
                    body=body,
                )
                reload_info = ReloadInfo.from_response(response, self.endpoint)

                record_span_event(
                    "acl_created",
                    {
                        "name": acl_name,
                        "size": len(content),
                        "hash": content_hash,
                    },
                )
                metrics.record_dataplane_api_request("create_acl", "success")
                await log_resource_operation(
                    "Created",
                    "ACL",
                    acl_name,
                    f"{len(content)} bytes",
                    reload_triggered=reload_info.reload_id is not None,
                )
                return CreateOperationResult(reload_info=reload_info)

            except Exception as e:
                metrics.record_dataplane_api_request("create_acl", "error")
                set_span_error(e, f"ACL file creation failed: {acl_name}")
                raise DataplaneAPIError(
                    f"Failed to create ACL file {acl_name}: {e}",
                    endpoint=self.endpoint,
                    operation="create_acl",
                    original_error=e,
                ) from e

    async def _update_acl_file_if_changed(
        self,
        client: Any,
        acl_name: str,
        content: str,
        existing_acl: GeneralUseFile,
        metrics: Any,
    ) -> UpdateOperationResult:
        """Update ACL file if content has changed.

        Returns:
            True if ACL file was updated, False if unchanged and skipped.
        """
        try:
            # Check if content changed using hash comparison
            content_hash = compute_content_hash(content)
            description = _convert_unset_to_none(existing_acl.description)
            current_hash = extract_hash_from_description(description)

            if current_hash == content_hash:
                logger.debug(f"ACL file {acl_name} unchanged, skipping update")
                return UpdateOperationResult(
                    content_changed=False, reload_info=ReloadInfo()
                )

            # Fallback to direct content comparison if no hash available
            if current_hash is None:
                try:
                    existing_resource = await get_one_storage_general_file.asyncio(
                        client=client, name=acl_name
                    )
                    existing_content = self._extract_storage_content(existing_resource)

                    if existing_content == content:
                        logger.debug(
                            f"ACL file {acl_name} unchanged (content comparison), skipping update"
                        )
                        return UpdateOperationResult(
                            content_changed=False, reload_info=ReloadInfo()
                        )
                except Exception as e:
                    logger.debug(
                        f"Failed to get existing ACL file content for {acl_name}: {e}"
                    )
                    # Continue with update if we can't compare content

            # Content changed, update the ACL file
            with metrics.time_dataplane_api_operation("update_acl"):
                file_obj = File(
                    file_name=acl_name,
                    payload=io.BytesIO(content.encode("utf-8")),
                )
                body = ReplaceStorageGeneralFileBody(file_upload=file_obj)
                body["description"] = content_hash

                response = await replace_storage_general_file.asyncio_detailed(
                    name=acl_name,
                    client=client,
                    body=body,
                )
                reload_info = ReloadInfo.from_response(response, self.endpoint)

                record_span_event(
                    "acl_updated",
                    {
                        "name": acl_name,
                        "size": len(content),
                        "old_hash": current_hash,
                        "new_hash": content_hash,
                    },
                )
                metrics.record_dataplane_api_request("update_acl", "success")
                await log_resource_operation(
                    "Updated",
                    "ACL",
                    acl_name,
                    f"{len(content)} bytes",
                    reload_triggered=reload_info.reload_id is not None,
                )
                return UpdateOperationResult(
                    content_changed=True, reload_info=reload_info
                )

        except Exception as e:
            metrics.record_dataplane_api_request("update_acl", "error")
            set_span_error(e, f"ACL file update failed: {acl_name}")
            raise DataplaneAPIError(
                f"Failed to update ACL file {acl_name}: {e}",
                endpoint=self.endpoint,
                operation="update_acl",
                original_error=e,
            ) from e

    async def _delete_acl_file(
        self, client: Any, acl_name: str, metrics: Any
    ) -> DeleteOperationResult:
        """Delete an ACL file."""
        with metrics.time_dataplane_api_operation("delete_acl"):
            try:
                response = await delete_storage_general_file.asyncio_detailed(
                    client=client, name=acl_name
                )
                reload_info = ReloadInfo.from_response(response, self.endpoint)

                record_span_event("acl_deleted", {"name": acl_name})
                metrics.record_dataplane_api_request("delete_acl", "success")
                await log_resource_operation(
                    "Deleted",
                    "ACL",
                    acl_name,
                    reload_triggered=reload_info.reload_id is not None,
                )
                return DeleteOperationResult(reload_info=reload_info)

            except Exception as e:
                metrics.record_dataplane_api_request("delete_acl", "error")
                set_span_error(e, f"ACL file deletion failed: {acl_name}")
                raise DataplaneAPIError(
                    f"Failed to delete ACL file {acl_name}: {e}",
                    endpoint=self.endpoint,
                    operation="delete_acl",
                    original_error=e,
                ) from e

    @handle_dataplane_errors("sync_files")
    @autolog()
    async def sync_files(self, files: dict[str, str]) -> StorageOperationResult:
        """Synchronize general files with HAProxy storage.

        Args:
            files: Dictionary mapping file names to their content

        Returns:
            StorageOperationResult containing operation status and reload information

        Raises:
            DataplaneAPIError: If file synchronization fails
        """
        if not files:
            logger.debug("No files to synchronize")
            return StorageOperationResult(
                operation_applied=False,
                reload_info=ReloadInfo(),
            )

        metrics = get_metrics_collector()
        client = self._get_client()

        logger.info(f"Synchronizing {len(files)} general files")

        # Get existing files for comparison
        try:
            raw_response = await get_all_storage_general_files.asyncio(client=client)
            existing_files = (
                check_dataplane_response(
                    raw_response, "get_all_storage_general_files", self.endpoint
                )
                or []
            )
            existing_file_names = {
                f.storage_name for f in existing_files if f.storage_name
            }
        except Exception as e:
            _log_fetch_error("existing files", "", e)
            existing_files = []
            existing_file_names = set()

        files_to_create = set(files.keys()) - existing_file_names
        files_to_update = set(files.keys()) & existing_file_names
        files_to_delete = existing_file_names - set(files.keys())

        reload_infos = []

        for file_name in files_to_create:
            create_result = await self._create_file(
                client, file_name, files[file_name], metrics
            )
            reload_infos.append(create_result.reload_info)

        actual_files_updated = 0
        for file_name in files_to_update:
            existing_file = next(
                (f for f in existing_files if f.storage_name == file_name), None
            )
            if existing_file is None:
                raise RuntimeError(f"File {file_name} should exist in existing_files")
            update_result = await self._update_file_if_changed(
                client, file_name, files[file_name], existing_file, metrics
            )
            reload_infos.append(update_result.reload_info)
            if update_result.content_changed:
                actual_files_updated += 1

        for file_name in files_to_delete:
            delete_result = await self._delete_file(client, file_name, metrics)
            reload_infos.append(delete_result.reload_info)

        logger.info(
            f"File sync complete: {len(files_to_create)} created, "
            f"{actual_files_updated} updated, {len(files_to_delete)} deleted"
        )

        operations_performed = (
            len(files_to_create) > 0
            or actual_files_updated > 0
            or len(files_to_delete) > 0
        )

        combined_reload_info = ReloadInfo.combine(*reload_infos)

        return StorageOperationResult(
            operation_applied=operations_performed,
            reload_info=combined_reload_info,
        )

    async def _create_file(
        self, client: Any, file_name: str, content: str, metrics: Any
    ) -> CreateOperationResult:
        """Create a new general file."""
        with metrics.time_dataplane_api_operation("create_file"):
            try:
                content_hash = compute_content_hash(content)
                file_obj = File(
                    file_name=file_name,
                    payload=io.BytesIO(content.encode("utf-8")),
                )

                # Create proper body structure for API call with hash in description
                body = CreateStorageGeneralFileBody(file_upload=file_obj)
                body["description"] = content_hash

                response = await create_storage_general_file.asyncio_detailed(
                    client=client,
                    body=body,
                )
                reload_info = ReloadInfo.from_response(response, self.endpoint)

                record_span_event(
                    "file_created",
                    {
                        "name": file_name,
                        "size": len(content),
                        "hash": content_hash,
                    },
                )
                metrics.record_dataplane_api_request("create_file", "success")
                await log_resource_operation(
                    "Created",
                    "file",
                    file_name,
                    f"{len(content)} bytes",
                    reload_triggered=reload_info.reload_id is not None,
                )
                return CreateOperationResult(reload_info=reload_info)

            except Exception as e:
                metrics.record_dataplane_api_request("create_file", "error")
                set_span_error(e, f"File creation failed: {file_name}")
                raise DataplaneAPIError(
                    f"Failed to create file {file_name}: {e}",
                    endpoint=self.endpoint,
                    operation="create_file",
                    original_error=e,
                ) from e

    async def _update_file_if_changed(
        self,
        client: Any,
        file_name: str,
        content: str,
        existing_file: GeneralUseFile,
        metrics: Any,
    ) -> UpdateOperationResult:
        """Update file if content has changed.

        Returns:
            True if file was updated, False if unchanged and skipped.
        """
        try:
            # Check if content changed using hash comparison
            content_hash = compute_content_hash(content)
            description = _convert_unset_to_none(existing_file.description)
            current_hash = extract_hash_from_description(description)

            if current_hash == content_hash:
                logger.debug(f"File {file_name} unchanged, skipping update")
                return UpdateOperationResult(
                    content_changed=False, reload_info=ReloadInfo()
                )

            # Fallback to direct content comparison if no hash available
            if current_hash is None:
                try:
                    existing_resource = await get_one_storage_general_file.asyncio(
                        client=client, name=file_name
                    )
                    existing_content = self._extract_storage_content(existing_resource)

                    if existing_content == content:
                        logger.debug(
                            f"File {file_name} unchanged (content comparison), skipping update"
                        )
                        return UpdateOperationResult(
                            content_changed=False, reload_info=ReloadInfo()
                        )
                except Exception as e:
                    logger.debug(
                        f"Failed to get existing file content for {file_name}: {e}"
                    )
                    # Continue with update if we can't compare content

            # Content changed, update the file
            with metrics.time_dataplane_api_operation("update_file"):
                file_obj = File(
                    file_name=file_name,
                    payload=io.BytesIO(content.encode("utf-8")),
                )
                body = ReplaceStorageGeneralFileBody(file_upload=file_obj)
                body["description"] = content_hash

                response = await replace_storage_general_file.asyncio_detailed(
                    name=file_name,
                    client=client,
                    body=body,
                )
                reload_info = ReloadInfo.from_response(response, self.endpoint)

                record_span_event(
                    "file_updated",
                    {
                        "name": file_name,
                        "size": len(content),
                        "old_hash": current_hash,
                        "new_hash": content_hash,
                    },
                )
                metrics.record_dataplane_api_request("update_file", "success")
                await log_resource_operation(
                    "Updated",
                    "file",
                    file_name,
                    f"{len(content)} bytes",
                    reload_triggered=reload_info.reload_id is not None,
                )
                return UpdateOperationResult(
                    content_changed=True, reload_info=reload_info
                )

        except Exception as e:
            metrics.record_dataplane_api_request("update_file", "error")
            set_span_error(e, f"File update failed: {file_name}")
            raise DataplaneAPIError(
                f"Failed to update file {file_name}: {e}",
                endpoint=self.endpoint,
                operation="update_file",
                original_error=e,
            ) from e

    async def _delete_file(
        self, client: Any, file_name: str, metrics: Any
    ) -> DeleteOperationResult:
        """Delete a general file."""
        with metrics.time_dataplane_api_operation("delete_file"):
            try:
                response = await delete_storage_general_file.asyncio_detailed(
                    client=client, name=file_name
                )
                reload_info = ReloadInfo.from_response(response, self.endpoint)

                record_span_event("file_deleted", {"name": file_name})
                metrics.record_dataplane_api_request("delete_file", "success")
                await log_resource_operation(
                    "Deleted",
                    "file",
                    file_name,
                    reload_triggered=reload_info.reload_id is not None,
                )
                return DeleteOperationResult(reload_info=reload_info)

            except Exception as e:
                metrics.record_dataplane_api_request("delete_file", "error")
                set_span_error(e, f"File deletion failed: {file_name}")
                raise DataplaneAPIError(
                    f"Failed to delete file {file_name}: {e}",
                    endpoint=self.endpoint,
                    operation="delete_file",
                    original_error=e,
                ) from e
