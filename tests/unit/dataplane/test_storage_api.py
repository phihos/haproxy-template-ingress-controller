"""
Unit tests for HAProxy Storage API operations.

Tests the storage API functionality including map and certificate operations
using proper mocking to verify correct API call signatures.
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch
from io import BytesIO

from haproxy_template_ic.dataplane.storage_api import StorageAPI
from haproxy_template_ic.dataplane.types import (
    StorageOperationResult,
)
from haproxy_template_ic.dataplane.adapter import ReloadInfo
from haproxy_dataplane_v3.models import Error, MapFile, SSLFile, GeneralUseFile
from haproxy_dataplane_v3.models.create_storage_map_file_body import (
    CreateStorageMapFileBody,
)
from haproxy_dataplane_v3.models.create_storage_ssl_certificate_body import (
    CreateStorageSSLCertificateBody,
)
from haproxy_dataplane_v3.models.create_storage_general_file_body import (
    CreateStorageGeneralFileBody,
)
from haproxy_template_ic.dataplane.types import compute_content_hash
from tests.unit.conftest import (
    assert_storage_api_call_signature,
)
from tests.unit.dataplane.conftest import (
    patch_storage_map_apis,
    patch_storage_certificate_apis,
    patch_storage_file_apis,
)
from tests.unit.dataplane.adapter_fixtures import (
    create_mock_api_response,
    create_storage_async_mock,
)


@pytest.fixture
def storage_api():
    """Create StorageAPI instance with mock client."""
    from haproxy_template_ic.dataplane.endpoint import DataplaneEndpoint
    from haproxy_template_ic.credentials import DataplaneAuth

    auth = DataplaneAuth(username="admin", password="test")
    endpoint = DataplaneEndpoint(
        url="http://localhost:5555/v3", dataplane_auth=auth, pod_name="test-pod"
    )
    return StorageAPI(endpoint)


# API Signature Tests
@pytest.mark.asyncio
async def test_storage_api_create_map_uses_correct_signature(
    storage_api, mock_client, mock_metrics_collector_patch
):
    """Test that create_storage_map_file is called with correct parameters only."""
    # Setup mocks using new helpers
    mock_get_all = Mock()
    mock_api_response = Mock(content=[])
    mock_get_all = AsyncMock(return_value=mock_api_response)
    mock_create = create_storage_async_mock(
        MapFile, storage_name="test.map", reload_id="test-reload-123"
    )

    with (
        patch(
            "haproxy_template_ic.dataplane.storage_api.get_all_storage_map_files",
            mock_get_all,
        ),
        patch(
            "haproxy_template_ic.dataplane.storage_api.create_storage_map_file",
            mock_create,
        ),
        patch(
            "haproxy_template_ic.dataplane.storage_api.get_metrics_collector",
            return_value=mock_metrics_collector_patch,
        ),
    ):
        # This should fail with current implementation due to invalid signature
        maps = {"test.map": "map content"}
        await storage_api.sync_maps(maps)

        # Verify create_storage_map_file was called with correct signature
        mock_create.assert_called_once()
        assert_storage_api_call_signature(
            mock_create.call_args, CreateStorageMapFileBody
        )


@pytest.mark.asyncio
async def test_storage_api_create_certificate_uses_correct_signature(
    storage_api, mock_client, mock_metrics_collector_patch
):
    """Test that create_storage_ssl_certificate is called with correct parameters only."""
    # Setup mocks using new helpers
    mock_get_all = Mock()
    mock_api_response = Mock(content=[])
    mock_get_all = AsyncMock(return_value=mock_api_response)
    mock_create = create_storage_async_mock(
        SSLFile, storage_name="test.crt", reload_id="test-reload-123"
    )

    with (
        patch(
            "haproxy_template_ic.dataplane.storage_api.get_all_storage_ssl_certificates",
            mock_get_all,
        ),
        patch(
            "haproxy_template_ic.dataplane.storage_api.create_storage_ssl_certificate",
            mock_create,
        ),
        patch(
            "haproxy_template_ic.dataplane.storage_api.get_metrics_collector",
            return_value=mock_metrics_collector_patch,
        ),
    ):
        # This should fail with current implementation due to invalid signature
        certificates = {"test.crt": "certificate content"}
        await storage_api.sync_certificates(certificates)

        # Verify create_storage_ssl_certificate was called with correct signature
        mock_create.assert_called_once()
        assert_storage_api_call_signature(
            mock_create.call_args, CreateStorageSSLCertificateBody
        )


@pytest.mark.asyncio
async def test_storage_api_replace_map_uses_correct_signature(
    storage_api, mock_client, mock_metrics_collector_patch
):
    """Test that replace_storage_map_file is called with correct parameters."""
    # Setup mocks - simulate existing map using new helpers
    # Use a different hash than what "new map content" will produce (xxh64:7c81f17bb1d33878)
    existing_map = MapFile(
        storage_name="test.map", description="xxh64:different_hash_value"
    )

    # Set up proper mock that works for both calls
    mock_get_all_response = Mock(content=[existing_map])
    mock_replace_response = create_mock_api_response(
        content=MapFile(storage_name="test.map"), reload_id="test-reload-123"
    )

    # Patch the exact method calls the storage API makes
    with (
        patch(
            "haproxy_template_ic.dataplane.storage_api.get_all_storage_map_files",
            AsyncMock(return_value=mock_get_all_response),
        ),
        patch(
            "haproxy_template_ic.dataplane.storage_api.replace_storage_map_file",
            AsyncMock(return_value=mock_replace_response),
        ) as mock_replace_detailed,
        patch(
            "haproxy_template_ic.dataplane.storage_api.get_metrics_collector",
            return_value=mock_metrics_collector_patch,
        ),
    ):
        # This should test the replace operation
        maps = {"test.map": "new map content"}
        await storage_api.sync_maps(maps)

        # Verify replace_storage_map_file.asyncio_detailed was called with correct signature
        # Replace operations may include name as path parameter
        mock_replace_detailed.assert_called_once()
        assert_storage_api_call_signature(
            mock_replace_detailed.call_args,
            allow_name=True,  # Replace operations can have name parameter
        )


@pytest.mark.asyncio
async def test_storage_api_error_response_handling(
    storage_api, mock_metrics_collector_patch
):
    """Test that Error responses from storage APIs are handled correctly."""
    # Setup mock to return Error object instead of list
    error_response = Error(code=401, message="unauthorized")
    mock_get_all = Mock()
    mock_get_all.asyncio = AsyncMock(return_value=error_response)

    # Mock create operation to handle the creation that will occur
    mock_create = create_storage_async_mock(
        MapFile, storage_name="test.map", reload_id="test-reload-123"
    )

    with (
        patch(
            "haproxy_template_ic.dataplane.storage_api.get_all_storage_map_files",
            mock_get_all,
        ),
        patch(
            "haproxy_template_ic.dataplane.storage_api.create_storage_map_file",
            mock_create,
        ),
        patch(
            "haproxy_template_ic.dataplane.storage_api.get_metrics_collector",
            return_value=mock_metrics_collector_patch,
        ),
    ):
        # This should handle the Error response gracefully
        maps = {"test.map": "map content"}
        await storage_api.sync_maps(maps)

        # Should not crash and should handle the error response properly
        # The existing type guard should log a warning about the error response


@pytest.mark.asyncio
async def test_storage_api_storage_info_handles_error_responses(
    storage_api, mock_metrics_collector_patch
):
    """Test that get_storage_info handles Error responses correctly."""
    # Setup mocks to return Error objects using new helpers
    error_response = Error(code=500, message="server error")
    mock_get_maps = Mock()
    mock_get_maps.asyncio = AsyncMock(return_value=error_response)
    mock_get_certs = Mock()
    mock_get_certs.asyncio = AsyncMock(return_value=error_response)

    with (
        patch(
            "haproxy_template_ic.dataplane.storage_api.get_all_storage_map_files",
            mock_get_maps,
        ),
        patch(
            "haproxy_template_ic.dataplane.storage_api.get_all_storage_ssl_certificates",
            mock_get_certs,
        ),
        patch(
            "haproxy_template_ic.dataplane.storage_api.get_metrics_collector",
            return_value=mock_metrics_collector_patch,
        ),
    ):
        # This should handle Error responses gracefully by returning None
        result = await storage_api.get_storage_info()

        # The function returns None when APIs return errors due to error handling decorator
        assert result is None


# Body Structure Tests
def test_storage_body_create_map_structure():
    """Test CreateStorageMapFileBody construction."""
    from haproxy_dataplane_v3.types import File

    # Test that File object is constructed correctly
    file_obj = File(file_name="test.map", payload=BytesIO(b"map content"))

    # Test that body object accepts File
    body = CreateStorageMapFileBody(file_upload=file_obj)
    assert body.file_upload == file_obj


def test_storage_body_create_certificate_structure():
    """Test CreateStorageSSLCertificateBody construction."""
    from haproxy_dataplane_v3.types import File

    # Test that File object is constructed correctly
    file_obj = File(file_name="test.crt", payload=BytesIO(b"certificate content"))

    # Test that body object accepts File
    body = CreateStorageSSLCertificateBody(file_upload=file_obj)
    assert body.file_upload == file_obj


# Edge Case Tests
@pytest.mark.asyncio
async def test_storage_edge_sync_maps_empty_dict(
    storage_api, mock_metrics_collector_patch
):
    """Test that empty map dict is handled gracefully."""
    # Should return early without making any API calls
    await storage_api.sync_maps({})
    # No assertions needed - should not raise exceptions


@pytest.mark.asyncio
async def test_storage_edge_sync_certificates_empty_dict(
    storage_api, mock_metrics_collector_patch
):
    """Test that empty certificate dict is handled gracefully."""
    # Should return early without making any API calls
    await storage_api.sync_certificates({})
    # No assertions needed - should not raise exceptions


@pytest.mark.asyncio
async def test_storage_edge_sync_maps_with_unicode_content(
    storage_api, mock_client, mock_metrics_collector_patch
):
    """Test map synchronization with Unicode content."""
    with (
        patch(
            "haproxy_template_ic.dataplane.storage_api.get_all_storage_map_files",
            AsyncMock(return_value=Mock(content=[])),
        ),
        patch(
            "haproxy_template_ic.dataplane.storage_api.create_storage_map_file",
            AsyncMock(return_value=Mock(content=MapFile(storage_name="unicode.map"))),
        ),
        patch(
            "haproxy_template_ic.dataplane.storage_api.get_metrics_collector",
            return_value=mock_metrics_collector_patch,
        ),
    ):
        # Test with Unicode content
        maps = {"unicode.map": "# Map with émojis 🚀 and ünïcødé characters"}
        await storage_api.sync_maps(maps)

        # Should handle Unicode encoding properly
        # Verify that the API was called (we can't check call_args with this patching approach)


# File Synchronization Tests
@pytest.mark.asyncio
async def test_storage_api_create_file_uses_correct_signature(
    storage_api, mock_client, mock_metrics_collector_patch
):
    """Test that create_storage_general_file is called with correct parameters only."""
    # Setup mocks using factory
    from tests.unit.dataplane.adapter_fixtures import create_mock_api_response
    from haproxy_dataplane_v3.models import GeneralUseFile

    with (
        patch(
            "haproxy_template_ic.dataplane.storage_api.get_all_storage_general_files",
            AsyncMock(return_value=create_mock_api_response(content=[])),
        ),
        patch(
            "haproxy_template_ic.dataplane.storage_api.create_storage_general_file",
            AsyncMock(
                return_value=create_mock_api_response(
                    content=GeneralUseFile(storage_name="test.txt"),
                    reload_id="test-reload-456",
                )
            ),
        ) as mock_create,
        patch(
            "haproxy_template_ic.dataplane.storage_api.get_metrics_collector",
            return_value=mock_metrics_collector_patch,
        ),
    ):
        # This should call file creation API with correct signature
        files = {"test.txt": "file content"}
        await storage_api.sync_files(files)

        # Verify create_storage_general_file was called with ONLY endpoint and body
        mock_create.assert_called_once()
        call_args = mock_create.call_args

        # Should only have 'endpoint' and 'body' parameters (adapter uses endpoint, not client)
        assert "endpoint" in call_args.kwargs
        assert "body" in call_args.kwargs
        # These parameters should NOT exist (like in maps/certificates)
        assert "name" not in call_args.kwargs, (
            "API call should not include 'name' parameter"
        )
        assert "description" not in call_args.kwargs, (
            "API call should not include 'description' parameter"
        )

        # Verify body is proper type
        assert isinstance(call_args.kwargs["body"], CreateStorageGeneralFileBody)


@pytest.mark.asyncio
async def test_storage_api_replace_file_uses_correct_signature(
    storage_api, mock_client, mock_metrics_collector_patch
):
    """Test that replace_storage_general_file is called with correct parameters."""
    # Setup mocks - simulate existing file with a different hash than new content
    # Use a different hash than what "new file content" will produce (xxh64:915428af9b9b30de)
    existing_file = GeneralUseFile(
        storage_name="test.txt", description="xxh64:different_file_hash_value"
    )

    # Set up proper mock that works for both calls
    mock_get_all_response = Mock(content=[existing_file])
    mock_replace_response = create_mock_api_response(
        content=GeneralUseFile(storage_name="test.txt"), reload_id="test-reload-123"
    )

    # Patch the exact method calls the storage API makes
    with (
        patch(
            "haproxy_template_ic.dataplane.storage_api.get_all_storage_general_files",
            AsyncMock(return_value=mock_get_all_response),
        ),
        patch(
            "haproxy_template_ic.dataplane.storage_api.replace_storage_general_file",
            AsyncMock(return_value=mock_replace_response),
        ) as mock_replace_detailed,
        patch(
            "haproxy_template_ic.dataplane.storage_api.get_metrics_collector",
            return_value=mock_metrics_collector_patch,
        ),
    ):
        # This should test the replace operation
        files = {"test.txt": "new file content"}
        await storage_api.sync_files(files)

        # Verify replace_storage_general_file was called
        mock_replace_detailed.assert_called_once()
        call_args = mock_replace_detailed.call_args

        # Verify correct parameters (new adapter pattern uses endpoint, not client)
        assert "endpoint" in call_args.kwargs
        assert "body" in call_args.kwargs
        # Name parameter is passed via the function itself (likely positional or different call pattern)
        # Description should NOT be a separate parameter (it's in the body)
        assert "description" not in call_args.kwargs, (
            "API call should not include 'description' parameter"
        )


@pytest.mark.asyncio
async def test_storage_api_sync_files_empty_dict(
    storage_api, mock_metrics_collector_patch
):
    """Test that empty files dict is handled gracefully."""
    # Should return early without making any API calls
    await storage_api.sync_files({})
    # No assertions needed - should not raise exceptions


@pytest.mark.asyncio
async def test_storage_api_sync_files_with_unicode_content(
    storage_api, mock_client, mock_metrics_collector_patch
):
    """Test file synchronization with Unicode content."""
    with (
        patch(
            "haproxy_template_ic.dataplane.storage_api.get_all_storage_general_files",
            AsyncMock(return_value=Mock(content=[])),
        ),
        patch(
            "haproxy_template_ic.dataplane.storage_api.create_storage_general_file",
            AsyncMock(
                return_value=Mock(content=GeneralUseFile(storage_name="unicode.txt"))
            ),
        ),
        patch(
            "haproxy_template_ic.dataplane.storage_api.get_metrics_collector",
            return_value=mock_metrics_collector_patch,
        ),
    ):
        # Test with Unicode content
        files = {"unicode.txt": "# File with émojis 🚀 and ünïcødé characters"}
        await storage_api.sync_files(files)

        # Should handle Unicode encoding properly
        # Verify that the API was called (we can't check call_args with this patching approach)


# Body Structure Tests
@pytest.mark.asyncio
async def test_storage_body_includes_description_via_additional_properties(
    storage_api, mock_client, mock_metrics_collector_patch
):
    """Test that description is set via additional_properties in request bodies."""
    mock_get_all = Mock()
    mock_api_response = Mock(content=[])
    mock_get_all = AsyncMock(return_value=mock_api_response)
    mock_create = create_storage_async_mock(
        MapFile, storage_name="test.map", reload_id="test-reload-123"
    )

    with (
        patch(
            "haproxy_template_ic.dataplane.storage_api.get_all_storage_map_files",
            mock_get_all,
        ),
        patch(
            "haproxy_template_ic.dataplane.storage_api.create_storage_map_file",
            mock_create,
        ),
        patch(
            "haproxy_template_ic.dataplane.storage_api.get_metrics_collector",
            return_value=mock_metrics_collector_patch,
        ),
    ):
        # Create map with specific content to generate predictable hash
        maps = {"test.map": "map content"}
        await storage_api.sync_maps(maps)

        # Verify that the body contains description in additional_properties
        mock_create.assert_called_once()
        call_args = mock_create.call_args
        body = call_args.kwargs["body"]

        # Verify the description is set via bracket notation (additional_properties)
        assert "description" in body
        # The description should be a hash of the content
        expected_hash = compute_content_hash("map content")
        assert body["description"] == expected_hash


# Return Type Tests
class TestStorageAPIReturnTypes:
    """Test storage API methods return correct result types."""

    @pytest.mark.asyncio
    async def test_sync_maps_returns_storage_operation_result(
        self, storage_api, mock_client, mock_metrics_collector_patch
    ):
        """Test sync_maps returns StorageOperationResult."""
        mock_api_response = Mock(content=[])
        mock_get_all = AsyncMock(return_value=mock_api_response)

        with (
            patch(
                "haproxy_template_ic.dataplane.storage_api.get_all_storage_map_files",
                mock_get_all,
            ),
            patch(
                "haproxy_template_ic.dataplane.storage_api.get_metrics_collector",
                return_value=mock_metrics_collector_patch,
            ),
        ):
            result = await storage_api.sync_maps({})

            assert isinstance(result, StorageOperationResult)
            assert isinstance(result.reload_info, ReloadInfo)
            assert result.operation_applied is False  # No operations for empty dict

    @pytest.mark.asyncio
    async def test_sync_certificates_returns_storage_operation_result(
        self, storage_api, mock_client, mock_metrics_collector_patch
    ):
        """Test sync_certificates returns StorageOperationResult."""
        mock_get_all = Mock()
        mock_get_all.asyncio = AsyncMock(return_value=[])

        with (
            patch(
                "haproxy_template_ic.dataplane.storage_api.get_all_storage_ssl_certificates",
                mock_get_all,
            ),
            patch(
                "haproxy_template_ic.dataplane.storage_api.get_metrics_collector",
                return_value=mock_metrics_collector_patch,
            ),
        ):
            result = await storage_api.sync_certificates({})

            assert isinstance(result, StorageOperationResult)
            assert isinstance(result.reload_info, ReloadInfo)
            assert result.operation_applied is False  # No operations for empty dict

    @pytest.mark.asyncio
    async def test_sync_acls_returns_storage_operation_result(
        self, storage_api, mock_client, mock_metrics_collector_patch
    ):
        """Test sync_acls returns StorageOperationResult."""
        mock_api_response = Mock()
        mock_api_response.content = []

        with (
            patch(
                "haproxy_template_ic.dataplane.storage_api.get_all_storage_general_files",
                AsyncMock(return_value=mock_api_response),
            ),
            patch(
                "haproxy_template_ic.dataplane.storage_api.get_metrics_collector",
                return_value=mock_metrics_collector_patch,
            ),
        ):
            result = await storage_api.sync_acls({})

            assert isinstance(result, StorageOperationResult)
            assert isinstance(result.reload_info, ReloadInfo)
            assert result.operation_applied is False  # No operations for empty dict

    @pytest.mark.asyncio
    async def test_sync_files_returns_storage_operation_result(
        self, storage_api, mock_client, mock_metrics_collector_patch
    ):
        """Test sync_files returns StorageOperationResult."""
        mock_api_response = Mock(content=[])
        mock_get_all = AsyncMock(return_value=mock_api_response)

        with (
            patch(
                "haproxy_template_ic.dataplane.storage_api.get_all_storage_general_files",
                mock_get_all,
            ),
            patch(
                "haproxy_template_ic.dataplane.storage_api.get_metrics_collector",
                return_value=mock_metrics_collector_patch,
            ),
        ):
            result = await storage_api.sync_files({})

            assert isinstance(result, StorageOperationResult)
            assert isinstance(result.reload_info, ReloadInfo)
            assert result.operation_applied is False  # No operations for empty dict

    @pytest.mark.asyncio
    async def test_reload_info_propagated_from_helper_methods(
        self, storage_api, mock_client, mock_metrics_collector_patch
    ):
        """Test that ReloadInfo is properly propagated from helper methods.

        Helper methods now return result objects containing ReloadInfo,
        and sync methods collect and combine them properly.
        """
        # Use existing factory for consistent mocking
        from tests.unit.dataplane.adapter_fixtures import create_mock_api_response

        with (
            patch(
                "haproxy_template_ic.dataplane.storage_api.get_all_storage_map_files",
                AsyncMock(return_value=create_mock_api_response(content=[])),
            ),
            patch(
                "haproxy_template_ic.dataplane.storage_api.create_storage_map_file",
                AsyncMock(
                    return_value=create_mock_api_response(reload_id="test-reload-123")
                ),
            ),
            patch(
                "haproxy_template_ic.dataplane.storage_api.get_metrics_collector",
                return_value=mock_metrics_collector_patch,
            ),
        ):
            maps = {"test.map": "content"}
            result = await storage_api.sync_maps(maps)

            assert isinstance(result, StorageOperationResult)
            assert result.operation_applied is True
            # ReloadInfo is now properly propagated from helper methods
            assert result.reload_info.reload_triggered is True
            assert result.reload_info.reload_id == "test-reload-123"


class TestStorageAPIMapOperations:
    """Test storage API map operations using context managers."""

    @pytest.mark.asyncio
    async def test_sync_maps_create_operation(self, storage_api):
        """Test map creation with proper context manager."""
        with patch_storage_map_apis() as mocks:
            maps = {"hosts.map": "api.example.com backend1"}
            result = await storage_api.sync_maps(maps)

            # Verify get_all was called to check existing maps
            mocks["get_all"].assert_called_once()
            # Verify create was called for new map
            mocks["create"].assert_called_once()

            assert isinstance(result, StorageOperationResult)
            assert result.operation_applied is True

    @pytest.mark.asyncio
    async def test_sync_maps_replace_operation(self, storage_api):
        """Test map replacement when content changes."""
        # Setup existing map with different hash
        existing_map = MapFile(
            storage_name="hosts.map", description="xxh64:different_hash"
        )

        mock_get_all = AsyncMock(return_value=Mock(content=[existing_map]))
        mock_replace = AsyncMock(
            return_value=Mock(
                status_code=202,
                headers={"Reload-ID": "reload-789"},
                content=MapFile(storage_name="hosts.map"),
            )
        )

        with patch_storage_map_apis(
            mock_get_all=mock_get_all, mock_replace=mock_replace
        ) as mocks:
            maps = {"hosts.map": "new.example.com backend2"}
            result = await storage_api.sync_maps(maps)

            # Verify replace was called instead of create
            mocks["replace"].assert_called_once()
            mocks["create"].assert_not_called()

            assert result.operation_applied is True
            assert result.reload_info.reload_triggered is True

    @pytest.mark.asyncio
    async def test_sync_maps_no_change_needed(self, storage_api):
        """Test when map content hasn't changed."""
        # Setup existing map with same content hash
        map_content = "api.example.com backend1"
        expected_hash = compute_content_hash(map_content)
        existing_map = MapFile(storage_name="hosts.map", description=expected_hash)

        mock_get_all = AsyncMock(return_value=Mock(content=[existing_map]))

        with patch_storage_map_apis(mock_get_all=mock_get_all) as mocks:
            maps = {"hosts.map": map_content}
            result = await storage_api.sync_maps(maps)

            # Verify no create or replace operations
            mocks["create"].assert_not_called()
            mocks["replace"].assert_not_called()

            assert result.operation_applied is False

    @pytest.mark.asyncio
    async def test_sync_maps_multiple_operations(self, storage_api):
        """Test handling multiple maps with mixed operations."""
        # Setup one existing map, one new
        existing_map = MapFile(
            storage_name="existing.map", description="xxh64:old_hash"
        )

        mock_get_all = AsyncMock(return_value=Mock(content=[existing_map]))
        mock_create = AsyncMock(
            return_value=Mock(content=MapFile(storage_name="new.map"))
        )
        mock_replace = AsyncMock(
            return_value=Mock(
                status_code=200,
                headers={},
                content=MapFile(storage_name="existing.map"),
            )
        )

        with patch_storage_map_apis(
            mock_get_all=mock_get_all,
            mock_create=mock_create,
            mock_replace=mock_replace,
        ) as mocks:
            maps = {"new.map": "new content", "existing.map": "updated content"}
            result = await storage_api.sync_maps(maps)

            # Verify both create and replace were called
            mocks["create"].assert_called_once()
            mocks["replace"].assert_called_once()

            assert result.operation_applied is True


class TestStorageAPICertificateOperations:
    """Test storage API certificate operations using context managers."""

    @pytest.mark.asyncio
    async def test_sync_certificates_create_operation(self, storage_api):
        """Test certificate creation with proper context manager."""
        with patch_storage_certificate_apis() as mocks:
            certificates = {"server.crt": "-----BEGIN CERTIFICATE-----\n..."}
            result = await storage_api.sync_certificates(certificates)

            # Verify get_all was called to check existing certificates
            mocks["get_all"].assert_called_once()
            # Verify create was called for new certificate
            mocks["create"].assert_called_once()

            assert isinstance(result, StorageOperationResult)
            assert result.operation_applied is True

    @pytest.mark.asyncio
    async def test_sync_certificates_replace_operation(self, storage_api):
        """Test certificate replacement when content changes."""
        # Setup existing certificate with different hash
        existing_cert = SSLFile(
            storage_name="server.crt", description="xxh64:old_cert_hash"
        )

        mock_get_all = AsyncMock(return_value=Mock(content=[existing_cert]))
        mock_replace = AsyncMock(
            return_value=Mock(
                status_code=202,
                headers={"Reload-ID": "reload-cert-123"},
                content=SSLFile(storage_name="server.crt"),
            )
        )

        with patch_storage_certificate_apis(
            mock_get_all=mock_get_all, mock_replace=mock_replace
        ) as mocks:
            certificates = {
                "server.crt": "-----BEGIN CERTIFICATE-----\nnew cert\n-----END CERTIFICATE-----"
            }
            result = await storage_api.sync_certificates(certificates)

            # Verify replace was called instead of create
            mocks["replace"].assert_called_once()
            mocks["create"].assert_not_called()

            assert result.operation_applied is True
            assert result.reload_info.reload_triggered is True

    @pytest.mark.asyncio
    async def test_sync_certificates_with_pem_chain(self, storage_api):
        """Test certificate sync with full PEM chain."""
        pem_chain = """-----BEGIN CERTIFICATE-----
MIIChTCCAe4CAQAwDQYJKoZIhvcNAQEFBQAwXjELMAkGA1UEBhMCVVMx
-----END CERTIFICATE-----
-----BEGIN CERTIFICATE-----
MIIBkjCB/AIBATANBgkqhkiG9w0BAQUFADBOMQswCQYDVQQGEwJVUzEQ
-----END CERTIFICATE-----"""

        with patch_storage_certificate_apis() as mocks:
            certificates = {"chain.crt": pem_chain}
            result = await storage_api.sync_certificates(certificates)

            # Verify the content was properly handled
            mocks["create"].assert_called_once()
            assert result.operation_applied is True


class TestStorageAPIFileOperations:
    """Test storage API general file operations using context managers."""

    @pytest.mark.asyncio
    async def test_sync_files_create_operation(self, storage_api):
        """Test general file creation with proper context manager."""
        with patch_storage_file_apis() as mocks:
            files = {"config.txt": "server_setting=value"}
            result = await storage_api.sync_files(files)

            # Verify get_all was called to check existing files
            mocks["get_all"].assert_called_once()
            # Verify create was called for new file
            mocks["create"].assert_called_once()

            assert isinstance(result, StorageOperationResult)
            assert result.operation_applied is True

    @pytest.mark.asyncio
    async def test_sync_files_replace_operation(self, storage_api):
        """Test file replacement when content changes."""
        # Setup existing file with different hash
        existing_file = GeneralUseFile(
            storage_name="config.txt", description="xxh64:old_file_hash"
        )

        mock_get_all = AsyncMock(return_value=Mock(content=[existing_file]))
        mock_replace = AsyncMock(
            return_value=Mock(
                status_code=200,
                headers={},
                content=GeneralUseFile(storage_name="config.txt"),
            )
        )

        with patch_storage_file_apis(
            mock_get_all=mock_get_all, mock_replace=mock_replace
        ) as mocks:
            files = {"config.txt": "updated_setting=new_value"}
            result = await storage_api.sync_files(files)

            # Verify replace was called instead of create
            mocks["replace"].assert_called_once()
            mocks["create"].assert_not_called()

            assert result.operation_applied is True

    @pytest.mark.asyncio
    async def test_sync_acls_using_general_files(self, storage_api):
        """Test ACL sync using general file operations."""
        with patch_storage_file_apis() as mocks:
            acls = {"blocked_ips.acl": "192.168.1.100\n10.0.0.5"}
            result = await storage_api.sync_acls(acls)

            # Verify ACL sync uses general file APIs
            mocks["get_all"].assert_called_once()
            mocks["create"].assert_called_once()

            assert isinstance(result, StorageOperationResult)
            assert result.operation_applied is True


class TestStorageAPIErrorHandlingWithContextManagers:
    """Test error handling scenarios using context managers."""

    @pytest.mark.asyncio
    async def test_map_sync_handles_api_errors(self, storage_api):
        """Test map sync with API errors using context manager."""
        from haproxy_template_ic.dataplane.types import DataplaneAPIError

        # Setup get_all to succeed but create to fail (this will properly propagate the error)
        mock_get_all = AsyncMock(return_value=Mock(content=[]))
        mock_create = AsyncMock(side_effect=Exception("Create operation failed"))

        with patch_storage_map_apis(mock_get_all=mock_get_all, mock_create=mock_create):
            with pytest.raises(DataplaneAPIError):
                await storage_api.sync_maps({"test.map": "content"})

    @pytest.mark.asyncio
    async def test_certificate_sync_handles_create_errors(self, storage_api):
        """Test certificate sync with create operation errors."""
        from haproxy_template_ic.dataplane.types import DataplaneAPIError

        # Setup get_all to succeed but create to fail
        mock_get_all = AsyncMock(return_value=Mock(content=[]))
        mock_create = AsyncMock(side_effect=Exception("Create failed"))

        with patch_storage_certificate_apis(
            mock_get_all=mock_get_all, mock_create=mock_create
        ):
            with pytest.raises(DataplaneAPIError):
                await storage_api.sync_certificates({"test.crt": "cert content"})

    @pytest.mark.asyncio
    async def test_file_sync_handles_replace_errors(self, storage_api):
        """Test file sync with replace operation errors."""
        from haproxy_template_ic.dataplane.types import DataplaneAPIError

        # Setup existing file and failing replace
        existing_file = GeneralUseFile(
            storage_name="config.txt", description="xxh64:old_hash"
        )

        mock_get_all = AsyncMock(return_value=Mock(content=[existing_file]))
        mock_replace = AsyncMock(side_effect=Exception("Replace operation failed"))

        with patch_storage_file_apis(
            mock_get_all=mock_get_all, mock_replace=mock_replace
        ):
            with pytest.raises(DataplaneAPIError):
                await storage_api.sync_files({"config.txt": "new content"})


class TestStorageAPIIntegrationScenarios:
    """Test storage API in realistic integration scenarios."""

    @pytest.mark.asyncio
    async def test_full_ingress_deployment_storage_sync(self, storage_api):
        """Test storage sync for a complete ingress deployment."""
        # Setup realistic ingress deployment data
        maps = {
            "hosts.map": "api.example.com backend_api\nweb.example.com backend_web",
            "paths.map": "/api backend_api\n/static backend_static",
        }

        certificates = {
            "example.crt": "-----BEGIN CERTIFICATE-----\nMIIC...\n-----END CERTIFICATE-----",
            "wildcard.crt": "-----BEGIN CERTIFICATE-----\nMIID...\n-----END CERTIFICATE-----",
        }

        acls = {"blocked_ips.acl": "192.168.1.100\n10.0.0.5\n172.16.0.0/16"}

        # Use context managers for all storage types
        with (
            patch_storage_map_apis() as map_mocks,
            patch_storage_certificate_apis() as cert_mocks,
            patch_storage_file_apis() as file_mocks,
        ):
            # Execute all storage operations
            map_result = await storage_api.sync_maps(maps)
            cert_result = await storage_api.sync_certificates(certificates)
            acl_result = await storage_api.sync_acls(acls)

            # Verify all operations were applied
            assert map_result.operation_applied is True
            assert cert_result.operation_applied is True
            assert acl_result.operation_applied is True

            # Verify all API calls were made
            map_mocks["get_all"].assert_called_once()
            cert_mocks["get_all"].assert_called_once()
            file_mocks["get_all"].assert_called_once()

    @pytest.mark.asyncio
    async def test_storage_info_collection(self, storage_api):
        """Test get_storage_info with realistic data."""
        # Setup mock data for all storage types
        map_files = [
            MapFile(storage_name="hosts.map", description="xxh64:hash1"),
            MapFile(storage_name="paths.map", description="xxh64:hash2"),
        ]

        ssl_files = [
            SSLFile(storage_name="server.crt", description="xxh64:cert_hash"),
            SSLFile(storage_name="wildcard.crt", description="xxh64:wild_hash"),
        ]

        mock_map_get = AsyncMock(return_value=Mock(content=map_files))
        mock_cert_get = AsyncMock(return_value=Mock(content=ssl_files))

        with (
            patch_storage_map_apis(mock_get_all=mock_map_get),
            patch_storage_certificate_apis(mock_get_all=mock_cert_get),
        ):
            storage_info = await storage_api.get_storage_info()

            # Verify storage info was collected properly
            assert storage_info is not None
            assert storage_info["maps"]["count"] == 2
            assert storage_info["certificates"]["count"] == 2
            assert "hosts.map" in storage_info["maps"]["names"]
            assert "server.crt" in storage_info["certificates"]["names"]
