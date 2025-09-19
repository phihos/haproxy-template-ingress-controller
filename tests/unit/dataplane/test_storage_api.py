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
    ReloadInfo,
)
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


@pytest.fixture
def storage_api(mock_client):
    """Create StorageAPI instance with mock client."""
    get_client = Mock(return_value=mock_client)
    return StorageAPI(get_client, "http://localhost:5555/v3")


# API Signature Tests
@pytest.mark.asyncio
async def test_storage_api_create_map_uses_correct_signature(
    storage_api, mock_client, mock_metrics_collector_patch
):
    """Test that create_storage_map_file is called with correct parameters only."""
    # Setup mocks using new helpers
    mock_get_all = Mock()
    mock_get_all.asyncio_detailed = AsyncMock(return_value=Mock(parsed=[]))
    mock_create = Mock()
    mock_create.asyncio_detailed = AsyncMock(
        return_value=Mock(parsed=MapFile(storage_name="test.map"))
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

        # Verify create_storage_map_file.asyncio_detailed was called with correct signature
        mock_create.asyncio_detailed.assert_called_once()
        assert_storage_api_call_signature(
            mock_create.asyncio_detailed.call_args, CreateStorageMapFileBody
        )


@pytest.mark.asyncio
async def test_storage_api_create_certificate_uses_correct_signature(
    storage_api, mock_client, mock_metrics_collector_patch
):
    """Test that create_storage_ssl_certificate is called with correct parameters only."""
    # Setup mocks using new helpers
    mock_get_all = Mock()
    mock_get_all.asyncio_detailed = AsyncMock(return_value=Mock(parsed=[]))
    mock_create = Mock()
    mock_create.asyncio_detailed = AsyncMock(
        return_value=Mock(parsed=SSLFile(storage_name="test.crt"))
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

        # Verify create_storage_ssl_certificate.asyncio_detailed was called with correct signature
        mock_create.asyncio_detailed.assert_called_once()
        assert_storage_api_call_signature(
            mock_create.asyncio_detailed.call_args, CreateStorageSSLCertificateBody
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

    # Set up proper mock that works for both .asyncio_detailed() calls
    mock_get_all_response = Mock(parsed=[existing_map])
    mock_replace_response = Mock(
        status_code=200, headers={}, parsed=MapFile(storage_name="test.map")
    )

    # Patch the exact method calls the storage API makes
    with (
        patch(
            "haproxy_template_ic.dataplane.storage_api.get_all_storage_map_files.asyncio_detailed",
            AsyncMock(return_value=mock_get_all_response),
        ),
        patch(
            "haproxy_template_ic.dataplane.storage_api.replace_storage_map_file.asyncio_detailed",
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
    mock_create = Mock()
    mock_create.asyncio_detailed = AsyncMock(
        return_value=Mock(parsed=MapFile(storage_name="test.map"))
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
            "haproxy_template_ic.dataplane.storage_api.get_all_storage_map_files.asyncio_detailed",
            AsyncMock(return_value=Mock(parsed=[])),
        ),
        patch(
            "haproxy_template_ic.dataplane.storage_api.create_storage_map_file.asyncio_detailed",
            AsyncMock(return_value=Mock(parsed=MapFile(storage_name="unicode.map"))),
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
    # Setup mocks using new helpers
    mock_get_all = Mock()
    mock_get_all.asyncio_detailed = AsyncMock(return_value=Mock(parsed=[]))
    mock_create = Mock()
    mock_create.asyncio_detailed = AsyncMock(
        return_value=Mock(parsed=GeneralUseFile(storage_name="test.txt"))
    )

    with (
        patch(
            "haproxy_template_ic.dataplane.storage_api.get_all_storage_general_files",
            mock_get_all,
        ),
        patch(
            "haproxy_template_ic.dataplane.storage_api.create_storage_general_file",
            mock_create,
        ),
        patch(
            "haproxy_template_ic.dataplane.storage_api.get_metrics_collector",
            return_value=mock_metrics_collector_patch,
        ),
    ):
        # This should call file creation API with correct signature
        files = {"test.txt": "file content"}
        await storage_api.sync_files(files)

        # Verify create_storage_general_file.asyncio_detailed was called with ONLY client and body
        mock_create.asyncio_detailed.assert_called_once()
        call_args = mock_create.asyncio_detailed.call_args

        # Should only have 'client' and 'body' parameters
        assert "client" in call_args.kwargs
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

    # Set up proper mock that works for both .asyncio_detailed() calls
    mock_get_all_response = Mock(parsed=[existing_file])
    mock_replace_response = Mock(status_code=200, headers={})

    # Patch the exact method calls the storage API makes
    with (
        patch(
            "haproxy_template_ic.dataplane.storage_api.get_all_storage_general_files.asyncio_detailed",
            AsyncMock(return_value=mock_get_all_response),
        ),
        patch(
            "haproxy_template_ic.dataplane.storage_api.replace_storage_general_file.asyncio_detailed",
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

        # Verify replace_storage_general_file.asyncio_detailed was called
        mock_replace_detailed.assert_called_once()
        call_args = mock_replace_detailed.call_args

        # Verify correct parameters
        assert "client" in call_args.kwargs
        assert "body" in call_args.kwargs
        assert (
            "name" in call_args.kwargs
        )  # Name is valid for replace operations (path parameter)
        # Description should NOT be a separate parameter
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
            "haproxy_template_ic.dataplane.storage_api.get_all_storage_general_files.asyncio_detailed",
            AsyncMock(return_value=Mock(parsed=[])),
        ),
        patch(
            "haproxy_template_ic.dataplane.storage_api.create_storage_general_file.asyncio_detailed",
            AsyncMock(
                return_value=Mock(parsed=GeneralUseFile(storage_name="unicode.txt"))
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
    mock_get_all.asyncio_detailed = AsyncMock(return_value=Mock(parsed=[]))
    mock_create = Mock()
    mock_create.asyncio_detailed = AsyncMock(
        return_value=Mock(parsed=MapFile(storage_name="test.map"))
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
        mock_create.asyncio_detailed.assert_called_once()
        call_args = mock_create.asyncio_detailed.call_args
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
        mock_get_all = Mock()
        mock_get_all.asyncio_detailed = AsyncMock(return_value=Mock(parsed=[]))

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
        mock_get_all = Mock()
        mock_get_all.asyncio_detailed = AsyncMock(return_value=Mock(parsed=[]))

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
            result = await storage_api.sync_acls({})

            assert isinstance(result, StorageOperationResult)
            assert isinstance(result.reload_info, ReloadInfo)
            assert result.operation_applied is False  # No operations for empty dict

    @pytest.mark.asyncio
    async def test_sync_files_returns_storage_operation_result(
        self, storage_api, mock_client, mock_metrics_collector_patch
    ):
        """Test sync_files returns StorageOperationResult."""
        mock_get_all = Mock()
        mock_get_all.asyncio_detailed = AsyncMock(return_value=Mock(parsed=[]))

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
        # Mock response with reload ID
        mock_response = Mock(status_code=202, headers={"Reload-ID": "test-reload-123"})

        mock_get_all = Mock()
        mock_get_all.asyncio = AsyncMock(return_value=[])
        mock_create = Mock()
        mock_create.asyncio_detailed = AsyncMock(return_value=mock_response)

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
            maps = {"test.map": "content"}
            result = await storage_api.sync_maps(maps)

            assert isinstance(result, StorageOperationResult)
            assert result.operation_applied is True
            # ReloadInfo is now properly propagated from helper methods
            assert result.reload_info.reload_triggered is True
            assert result.reload_info.reload_id == "test-reload-123"
