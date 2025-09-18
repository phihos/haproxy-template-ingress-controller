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
from typing import Any, Dict, Optional, TYPE_CHECKING

from haproxy_dataplane_v3 import AuthenticatedClient
from haproxy_dataplane_v3.types import UNSET

if TYPE_CHECKING:
    from .endpoint import DataplaneEndpoint
from haproxy_dataplane_v3.models.map_file import MapFile
from haproxy_dataplane_v3.models.ssl_file import SSLFile
from haproxy_dataplane_v3.models.general_use_file import GeneralUseFile
from haproxy_dataplane_v3.models.create_storage_map_file_body import (
    CreateStorageMapFileBody,
)
from haproxy_dataplane_v3.models.create_storage_ssl_certificate_body import (
    CreateStorageSSLCertificateBody,
)
from haproxy_dataplane_v3.models.create_storage_general_file_body import (
    CreateStorageGeneralFileBody,
)
from haproxy_dataplane_v3.models.replace_storage_general_file_body import (
    ReplaceStorageGeneralFileBody,
)
from haproxy_dataplane_v3.types import File

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
    DataplaneAPIError,
    compute_content_hash,
    extract_hash_from_description,
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

    def _extract_storage_content(self, storage_item) -> Optional[str]:
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
    async def sync_maps(self, maps: Dict[str, str]) -> None:
        """Synchronize map files with HAProxy storage.

        Args:
            maps: Dictionary mapping map names to their content

        Raises:
            DataplaneAPIError: If map synchronization fails
        """
        if not maps:
            logger.debug("No maps to synchronize")
            return

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

        # Track maps to create, update, and delete
        maps_to_create = set(maps.keys()) - existing_map_names
        maps_to_update = set(maps.keys()) & existing_map_names
        maps_to_delete = existing_map_names - set(maps.keys())

        # Create new maps
        for map_name in maps_to_create:
            await self._create_map(client, map_name, maps[map_name], metrics)

        # Update existing maps (if content changed)
        actual_maps_updated = 0
        for map_name in maps_to_update:
            existing_map = next(
                (m for m in existing_maps if m.storage_name == map_name), None
            )
            # existing_map is guaranteed to exist since map_name is in maps_to_update
            if existing_map is None:
                raise RuntimeError(f"Map {map_name} should exist in existing_maps")
            was_updated = await self._update_map_if_changed(
                client, map_name, maps[map_name], existing_map, metrics
            )
            if was_updated:
                actual_maps_updated += 1

        # Delete obsolete maps
        for map_name in maps_to_delete:
            await self._delete_map(client, map_name, metrics)

        logger.info(
            f"Map sync complete: {len(maps_to_create)} created, "
            f"{actual_maps_updated} updated, {len(maps_to_delete)} deleted"
        )

    @handle_dataplane_errors("sync_certificates")
    async def sync_certificates(self, certificates: Dict[str, str]) -> None:
        """Synchronize SSL certificates with HAProxy storage.

        Args:
            certificates: Dictionary mapping certificate names to their content

        Raises:
            DataplaneAPIError: If certificate synchronization fails
        """
        if not certificates:
            logger.debug("No certificates to synchronize")
            return

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

        # Track certificates to create, update, and delete
        certs_to_create = set(certificates.keys()) - existing_cert_names
        certs_to_update = set(certificates.keys()) & existing_cert_names
        certs_to_delete = existing_cert_names - set(certificates.keys())

        # Create new certificates
        for cert_name in certs_to_create:
            await self._create_certificate(
                client, cert_name, certificates[cert_name], metrics
            )

        # Update existing certificates (if content changed)
        actual_certs_updated = 0
        for cert_name in certs_to_update:
            existing_cert = next(
                (c for c in existing_certs if c.storage_name == cert_name), None
            )
            # existing_cert is guaranteed to exist since cert_name is in certs_to_update
            if existing_cert is None:
                raise RuntimeError(
                    f"Certificate {cert_name} should exist in existing_certs"
                )
            was_updated = await self._update_certificate_if_changed(
                client, cert_name, certificates[cert_name], existing_cert, metrics
            )
            if was_updated:
                actual_certs_updated += 1

        # Delete obsolete certificates
        for cert_name in certs_to_delete:
            await self._delete_certificate(client, cert_name, metrics)

        logger.info(
            f"Certificate sync complete: {len(certs_to_create)} created, "
            f"{actual_certs_updated} updated, {len(certs_to_delete)} deleted"
        )

    async def _create_map(
        self, client: Any, map_name: str, content: str, metrics: Any
    ) -> None:
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

                await create_storage_map_file.asyncio(
                    client=client,
                    body=body,
                )

                record_span_event(
                    "map_created",
                    {
                        "name": map_name,
                        "size": len(content),
                        "hash": content_hash,
                    },
                )
                metrics.record_dataplane_api_request("create_map", "success")
                logger.debug(f"Created map: {map_name} ({len(content)} bytes)")

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
    ) -> bool:
        """Update map if content has changed.

        Returns:
            True if map was updated, False if unchanged and skipped.
        """
        try:
            # Check if content changed using hash comparison
            content_hash = compute_content_hash(content)
            description = _convert_unset_to_none(existing_map.description)
            current_hash = extract_hash_from_description(description)

            if current_hash == content_hash:
                logger.debug(f"Map {map_name} unchanged, skipping update")
                return False

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
                        return False
                except Exception as e:
                    logger.debug(
                        f"Failed to get existing map content for {map_name}: {e}"
                    )
                    # Continue with update if we can't compare content

            # Content changed, update the map
            with metrics.time_dataplane_api_operation("update_map"):
                await replace_storage_map_file.asyncio(
                    name=map_name,
                    client=client,
                    body=content,
                )

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
                logger.debug(f"Updated map: {map_name} ({len(content)} bytes)")
                return True

        except Exception as e:
            metrics.record_dataplane_api_request("update_map", "error")
            set_span_error(e, f"Map update failed: {map_name}")
            raise DataplaneAPIError(
                f"Failed to update map {map_name}: {e}",
                endpoint=self.endpoint,
                operation="update_map",
                original_error=e,
            ) from e

    async def _delete_map(self, client: Any, map_name: str, metrics: Any) -> None:
        """Delete a map file."""
        with metrics.time_dataplane_api_operation("delete_map"):
            try:
                await delete_storage_map.asyncio(client=client, name=map_name)

                record_span_event("map_deleted", {"name": map_name})
                metrics.record_dataplane_api_request("delete_map", "success")
                logger.debug(f"Deleted map: {map_name}")

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
    ) -> None:
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

                await create_storage_ssl_certificate.asyncio(
                    client=client,
                    body=body,
                )

                record_span_event(
                    "certificate_created",
                    {
                        "name": cert_name,
                        "size": len(content),
                        "hash": content_hash,
                    },
                )
                metrics.record_dataplane_api_request("create_certificate", "success")
                logger.debug(f"Created certificate: {cert_name} ({len(content)} bytes)")

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
    ) -> bool:
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
                return False

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
                        return False
                except Exception as e:
                    logger.debug(
                        f"Failed to get existing certificate content for {cert_name}: {e}"
                    )
                    # Continue with update if we can't compare content

            # Content changed, update the certificate
            with metrics.time_dataplane_api_operation("update_certificate"):
                await replace_storage_ssl_certificate.asyncio(
                    name=cert_name,
                    client=client,
                    body=content,
                )

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
                logger.debug(f"Updated certificate: {cert_name} ({len(content)} bytes)")
                return True

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
    ) -> None:
        """Delete an SSL certificate."""
        with metrics.time_dataplane_api_operation("delete_certificate"):
            try:
                await delete_storage_ssl_certificate.asyncio(
                    client=client, name=cert_name
                )

                record_span_event("certificate_deleted", {"name": cert_name})
                metrics.record_dataplane_api_request("delete_certificate", "success")
                logger.debug(f"Deleted certificate: {cert_name}")

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
    async def get_storage_info(self) -> Dict[str, Any]:
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

    @handle_dataplane_errors("sync_files")
    async def sync_files(self, files: Dict[str, str]) -> None:
        """Synchronize general files with HAProxy storage.

        Args:
            files: Dictionary mapping file names to their content

        Raises:
            DataplaneAPIError: If file synchronization fails
        """
        if not files:
            logger.debug("No files to synchronize")
            return

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

        # Track files to create, update, and delete
        files_to_create = set(files.keys()) - existing_file_names
        files_to_update = set(files.keys()) & existing_file_names
        files_to_delete = existing_file_names - set(files.keys())

        # Create new files
        for file_name in files_to_create:
            await self._create_file(client, file_name, files[file_name], metrics)

        # Update existing files (if content changed)
        actual_files_updated = 0
        for file_name in files_to_update:
            existing_file = next(
                (f for f in existing_files if f.storage_name == file_name), None
            )
            # existing_file is guaranteed to exist since file_name is in files_to_update
            if existing_file is None:
                raise RuntimeError(f"File {file_name} should exist in existing_files")
            was_updated = await self._update_file_if_changed(
                client, file_name, files[file_name], existing_file, metrics
            )
            if was_updated:
                actual_files_updated += 1

        # Delete obsolete files
        for file_name in files_to_delete:
            await self._delete_file(client, file_name, metrics)

        logger.info(
            f"File sync complete: {len(files_to_create)} created, "
            f"{actual_files_updated} updated, {len(files_to_delete)} deleted"
        )

    async def _create_file(
        self, client: Any, file_name: str, content: str, metrics: Any
    ) -> None:
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

                await create_storage_general_file.asyncio(
                    client=client,
                    body=body,
                )

                record_span_event(
                    "file_created",
                    {
                        "name": file_name,
                        "size": len(content),
                        "hash": content_hash,
                    },
                )
                metrics.record_dataplane_api_request("create_file", "success")
                logger.debug(f"Created file: {file_name} ({len(content)} bytes)")

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
    ) -> bool:
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
                return False

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
                        return False
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

                await replace_storage_general_file.asyncio(
                    name=file_name,
                    client=client,
                    body=body,
                )

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
                logger.debug(f"Updated file: {file_name} ({len(content)} bytes)")
                return True

        except Exception as e:
            metrics.record_dataplane_api_request("update_file", "error")
            set_span_error(e, f"File update failed: {file_name}")
            raise DataplaneAPIError(
                f"Failed to update file {file_name}: {e}",
                endpoint=self.endpoint,
                operation="update_file",
                original_error=e,
            ) from e

    async def _delete_file(self, client: Any, file_name: str, metrics: Any) -> None:
        """Delete a general file."""
        with metrics.time_dataplane_api_operation("delete_file"):
            try:
                await delete_storage_general_file.asyncio(client=client, name=file_name)

                record_span_event("file_deleted", {"name": file_name})
                metrics.record_dataplane_api_request("delete_file", "success")
                logger.debug(f"Deleted file: {file_name}")

            except Exception as e:
                metrics.record_dataplane_api_request("delete_file", "error")
                set_span_error(e, f"File deletion failed: {file_name}")
                raise DataplaneAPIError(
                    f"Failed to delete file {file_name}: {e}",
                    endpoint=self.endpoint,
                    operation="delete_file",
                    original_error=e,
                ) from e
