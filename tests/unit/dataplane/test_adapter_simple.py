"""
Simple unit tests for Dataplane Adapter core functionality.

Tests basic adapter functionality without complex mocking.
"""

import pytest
from unittest.mock import Mock, patch
from haproxy_dataplane_v3.models import Error

from haproxy_template_ic.dataplane.adapter import (
    ReloadInfo,
    APIResponse,
    is_not_error,
    _refresh_version_for_retry,
)


def test_reload_info_creation():
    """Test ReloadInfo creation with no reload."""
    reload_info = ReloadInfo()
    assert reload_info.reload_id is None
    assert not reload_info.reload_triggered


def test_reload_info_with_reload():
    """Test ReloadInfo creation with reload."""
    reload_info = ReloadInfo(reload_id="test-reload-123")
    assert reload_info.reload_id == "test-reload-123"
    assert reload_info.reload_triggered


def test_reload_info_combine_no_reloads():
    """Test combining ReloadInfo instances with no reloads."""
    r1 = ReloadInfo()
    r2 = ReloadInfo()

    combined = ReloadInfo.combine(r1, r2)

    assert not combined.reload_triggered
    assert combined.reload_id is None


def test_reload_info_combine_with_reload():
    """Test combining ReloadInfo instances with one reload."""
    r1 = ReloadInfo()
    r2 = ReloadInfo(reload_id="test-reload-456")

    combined = ReloadInfo.combine(r1, r2)

    assert combined.reload_triggered
    assert combined.reload_id == "test-reload-456"


def test_reload_info_combine_multiple_reloads():
    """Test combining ReloadInfo instances with multiple reloads."""
    r1 = ReloadInfo(reload_id="first-reload")
    r2 = ReloadInfo(reload_id="second-reload")

    combined = ReloadInfo.combine(r1, r2)

    assert combined.reload_triggered
    # Should use the first reload_id found
    assert combined.reload_id == "first-reload"


def test_reload_info_from_response_no_reload():
    """Test ReloadInfo.from_response with no reload (status != 202)."""
    response = Mock()
    response.status_code = 200
    response.headers = {}

    reload_info = ReloadInfo.from_response(response)

    assert not reload_info.reload_triggered
    assert reload_info.reload_id is None


def test_reload_info_from_response_with_reload():
    """Test ReloadInfo.from_response with reload (status == 202)."""
    response = Mock()
    response.status_code = 202
    response.headers = {"Reload-ID": "test-reload-789"}

    reload_info = ReloadInfo.from_response(response)

    assert reload_info.reload_triggered
    assert reload_info.reload_id == "test-reload-789"


def test_reload_info_from_response_case_insensitive():
    """Test ReloadInfo.from_response with different header cases."""
    response = Mock()
    response.status_code = 202
    response.headers = {"reload-id": "test-reload-lower"}

    reload_info = ReloadInfo.from_response(response)

    assert reload_info.reload_triggered
    assert reload_info.reload_id == "test-reload-lower"


def test_api_response_creation():
    """Test APIResponse creation with content and reload info."""
    content = {"test": "data"}
    reload_info = ReloadInfo(reload_id="test-reload")

    api_response = APIResponse(content=content, reload_info=reload_info)

    assert api_response.content == content
    assert api_response.reload_info == reload_info


def test_is_not_error_with_error():
    """Test is_not_error TypeGuard with Error object."""
    error = Error(message="test error", code=400)

    assert not is_not_error(error)


def test_is_not_error_with_valid_content():
    """Test is_not_error TypeGuard with valid content."""
    content = {"valid": "data"}

    assert is_not_error(content)


@pytest.mark.asyncio
async def test_refresh_version_for_retry_missing_params():
    """Test _refresh_version_for_retry when parameters are missing."""
    kwargs = {"other_param": "value"}

    # Should not raise exception when endpoint/version missing
    await _refresh_version_for_retry(kwargs)

    # kwargs should remain unchanged
    assert kwargs == {"other_param": "value"}


@pytest.mark.asyncio
async def test_refresh_version_for_retry_with_params():
    """Test _refresh_version_for_retry with endpoint and version present."""
    mock_endpoint = Mock()
    kwargs = {"endpoint": mock_endpoint, "version": "old_version"}

    # Mock the get_configuration_version function
    with patch(
        "haproxy_template_ic.dataplane.adapter.get_configuration_version"
    ) as mock_get_version:
        mock_response = Mock()
        mock_response.content = "new_version"
        mock_get_version.return_value = mock_response

        await _refresh_version_for_retry(kwargs)

        # Version should be updated
        assert kwargs["version"] == "new_version"
        mock_get_version.assert_called_once_with(endpoint=mock_endpoint)


@pytest.mark.asyncio
async def test_refresh_version_for_retry_exception():
    """Test _refresh_version_for_retry when get_configuration_version fails."""
    mock_endpoint = Mock()
    kwargs = {"endpoint": mock_endpoint, "version": "old_version"}

    # Mock the get_configuration_version function to raise exception
    with patch(
        "haproxy_template_ic.dataplane.adapter.get_configuration_version"
    ) as mock_get_version:
        mock_get_version.side_effect = Exception("API error")

        # Should not raise exception, should log warning
        await _refresh_version_for_retry(kwargs)

        # Version should remain unchanged when refresh fails
        assert kwargs["version"] == "old_version"
