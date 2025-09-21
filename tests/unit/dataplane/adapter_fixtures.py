"""
Simple adapter fixtures for dataplane unit tests.

This module provides basic fixtures for testing dataplane functionality.
"""

import pytest
from unittest.mock import Mock
from haproxy_template_ic.dataplane.adapter import ReloadInfo


@pytest.fixture
def mock_reload_info():
    """Create a standard ReloadInfo for testing."""
    return ReloadInfo(reload_id="test-reload-456")


@pytest.fixture
def mock_reload_info_no_reload():
    """Create a ReloadInfo with no reload for testing."""
    return ReloadInfo()


def create_mock_api_response(content=None, reload_id=None):
    """
    Create a mock APIResponse with content and ReloadInfo.

    Args:
        content: The content to return from the API call
        reload_id: Optional reload ID to simulate reload trigger

    Returns:
        Mock object with .content and .reload_info attributes
    """
    mock_response = Mock()
    mock_response.content = content

    if reload_id:
        mock_response.reload_info = ReloadInfo(reload_id=reload_id)
    else:
        mock_response.reload_info = ReloadInfo()

    return mock_response


@pytest.fixture
def api_response_factory():
    """Factory fixture for creating APIResponse mocks."""
    return create_mock_api_response


def create_storage_async_mock(model_class, storage_name="test-storage", reload_id=None):
    """
    Create an AsyncMock for storage API functions that returns proper APIResponse.

    Args:
        model_class: The storage model class (MapFile, SSLFile, GeneralUseFile)
        storage_name: Name for the storage object
        reload_id: Optional reload ID

    Returns:
        AsyncMock that returns APIResponse with model content and reload_info
    """
    from unittest.mock import AsyncMock

    content = model_class(storage_name=storage_name)
    api_response = create_mock_api_response(content=content, reload_id=reload_id)
    return AsyncMock(return_value=api_response)


def create_transaction_async_mock(
    transaction_id="test-transaction-123", reload_id=None
):
    """
    Create an AsyncMock for transaction API functions that returns proper APIResponse.

    Args:
        transaction_id: The transaction ID to return
        reload_id: Optional reload ID for commit operations

    Returns:
        AsyncMock that returns APIResponse with transaction content
    """
    from unittest.mock import AsyncMock, Mock

    # Create a mock transaction object with id attribute
    transaction = Mock()
    transaction.id = transaction_id

    api_response = create_mock_api_response(content=transaction, reload_id=reload_id)
    return AsyncMock(return_value=api_response)


def create_version_async_mock(version=5):
    """
    Create an AsyncMock for get_configuration_version function.

    Args:
        version: The version number to return

    Returns:
        AsyncMock that returns an API response with the version number
    """
    from unittest.mock import AsyncMock

    api_response = create_mock_api_response(content=version)
    return AsyncMock(return_value=api_response)
