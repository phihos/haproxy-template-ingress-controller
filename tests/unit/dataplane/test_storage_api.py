"""
Unit tests for HAProxy Storage API operations.

Tests the storage API functionality including map and certificate operations
using proper mocking to verify correct API call signatures.
"""

import pytest
from unittest.mock import Mock, patch
from io import BytesIO

from haproxy_template_ic.dataplane.storage_api import StorageAPI
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
    create_async_mock_with_config,
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
    mock_get_all = create_async_mock_with_config(return_value=[])
    mock_create = create_async_mock_with_config(
        return_value=MapFile(storage_name="test.map")
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

        # Verify create_storage_map_file.asyncio was called with correct signature
        mock_create.asyncio.assert_called_once()
        assert_storage_api_call_signature(
            mock_create.asyncio.call_args, CreateStorageMapFileBody
        )


@pytest.mark.asyncio
async def test_storage_api_create_certificate_uses_correct_signature(
    storage_api, mock_client, mock_metrics_collector_patch
):
    """Test that create_storage_ssl_certificate is called with correct parameters only."""
    # Setup mocks using new helpers
    mock_get_all = create_async_mock_with_config(return_value=[])
    mock_create = create_async_mock_with_config(
        return_value=SSLFile(storage_name="test.crt")
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

        # Verify create_storage_ssl_certificate.asyncio was called with correct signature
        mock_create.asyncio.assert_called_once()
        assert_storage_api_call_signature(
            mock_create.asyncio.call_args, CreateStorageSSLCertificateBody
        )


@pytest.mark.asyncio
async def test_storage_api_replace_map_uses_correct_signature(
    storage_api, mock_client, mock_metrics_collector_patch
):
    """Test that replace_storage_map_file is called with correct parameters."""
    # Setup mocks - simulate existing map using new helpers
    existing_map = MapFile(storage_name="test.map", description="old_hash")
    mock_get_all = create_async_mock_with_config(return_value=[existing_map])
    mock_replace = create_async_mock_with_config(
        return_value=MapFile(storage_name="test.map")
    )

    with (
        patch(
            "haproxy_template_ic.dataplane.storage_api.get_all_storage_map_files.asyncio",
            mock_get_all,
        ),
        patch(
            "haproxy_template_ic.dataplane.storage_api.replace_storage_map_file.asyncio",
            mock_replace,
        ),
        patch(
            "haproxy_template_ic.dataplane.storage_api.get_metrics_collector",
            return_value=mock_metrics_collector_patch,
        ),
    ):
        # This should test the replace operation
        maps = {"test.map": "new map content"}
        await storage_api.sync_maps(maps)

        # Verify replace_storage_map_file.asyncio was called with correct signature
        # Replace operations may include name as path parameter
        mock_replace.assert_called_once()
        assert_storage_api_call_signature(
            mock_replace.call_args,
            allow_name=True,  # Replace operations can have name parameter
        )


@pytest.mark.asyncio
async def test_storage_api_error_response_handling(
    storage_api, mock_metrics_collector_patch
):
    """Test that Error responses from storage APIs are handled correctly."""
    # Setup mock to return Error object instead of list
    error_response = Error(code=401, message="unauthorized")
    mock_get_all = create_async_mock_with_config(return_value=error_response)

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
    mock_get_maps = create_async_mock_with_config(return_value=error_response)
    mock_get_certs = create_async_mock_with_config(return_value=error_response)

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
        # This should handle Error responses gracefully
        result = await storage_api.get_storage_info()

        # Should return empty counts when APIs return errors
        assert result["maps"]["count"] == 0
        assert result["certificates"]["count"] == 0
        assert result["maps"]["names"] == []
        assert result["certificates"]["names"] == []


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
    mock_get_all = create_async_mock_with_config(return_value=[])
    mock_create = create_async_mock_with_config(
        return_value=MapFile(storage_name="unicode.map")
    )

    with (
        patch(
            "haproxy_template_ic.dataplane.storage_api.get_all_storage_map_files.asyncio",
            mock_get_all,
        ),
        patch(
            "haproxy_template_ic.dataplane.storage_api.create_storage_map_file.asyncio",
            mock_create,
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
        mock_create.assert_called_once()
        call_args = mock_create.call_args
        assert "client" in call_args.kwargs
        assert "body" in call_args.kwargs
        assert isinstance(call_args.kwargs["body"], CreateStorageMapFileBody)


# File Synchronization Tests
@pytest.mark.asyncio
async def test_storage_api_create_file_uses_correct_signature(
    storage_api, mock_client, mock_metrics_collector_patch
):
    """Test that create_storage_general_file is called with correct parameters only."""
    # Setup mocks using new helpers
    mock_get_all = create_async_mock_with_config(return_value=[])
    mock_create = create_async_mock_with_config(
        return_value=GeneralUseFile(storage_name="test.txt")
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

        # Verify create_storage_general_file.asyncio was called with ONLY client and body
        mock_create.asyncio.assert_called_once()
        call_args = mock_create.asyncio.call_args

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
    existing_file = GeneralUseFile(
        storage_name="test.txt", description="xxh64:different_hash"
    )
    mock_get_all = create_async_mock_with_config(return_value=[existing_file])
    mock_replace = create_async_mock_with_config(return_value=None)

    with (
        patch(
            "haproxy_template_ic.dataplane.storage_api.get_all_storage_general_files.asyncio",
            mock_get_all,
        ),
        patch(
            "haproxy_template_ic.dataplane.storage_api.replace_storage_general_file.asyncio",
            mock_replace,
        ),
        patch(
            "haproxy_template_ic.dataplane.storage_api.get_metrics_collector",
            return_value=mock_metrics_collector_patch,
        ),
    ):
        # This should test the replace operation
        files = {"test.txt": "new file content"}
        await storage_api.sync_files(files)

        # Verify replace_storage_general_file.asyncio was called
        mock_replace.assert_called_once()
        call_args = mock_replace.call_args

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
    mock_get_all = create_async_mock_with_config(return_value=[])
    mock_create = create_async_mock_with_config(
        return_value=GeneralUseFile(storage_name="unicode.txt")
    )

    with (
        patch(
            "haproxy_template_ic.dataplane.storage_api.get_all_storage_general_files.asyncio",
            mock_get_all,
        ),
        patch(
            "haproxy_template_ic.dataplane.storage_api.create_storage_general_file.asyncio",
            mock_create,
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
        mock_create.assert_called_once()
        call_args = mock_create.call_args
        assert "client" in call_args.kwargs
        assert "body" in call_args.kwargs
        assert isinstance(call_args.kwargs["body"], CreateStorageGeneralFileBody)


# Body Structure Tests
@pytest.mark.asyncio
async def test_storage_body_includes_description_via_additional_properties(
    storage_api, mock_client, mock_metrics_collector_patch
):
    """Test that description is set via additional_properties in request bodies."""
    mock_get_all = create_async_mock_with_config(return_value=[])
    mock_create = create_async_mock_with_config(
        return_value=MapFile(storage_name="test.map")
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
        mock_create.asyncio.assert_called_once()
        call_args = mock_create.asyncio.call_args
        body = call_args.kwargs["body"]

        # Verify the description is set via bracket notation (additional_properties)
        assert "description" in body
        # The description should be a hash of the content
        expected_hash = compute_content_hash("map content")
        assert body["description"] == expected_hash
