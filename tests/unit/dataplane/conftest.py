"""
Shared test fixtures for dataplane unit tests.

This module provides dataplane-specific fixtures to eliminate duplication
across dataplane test files.
"""

import pytest
from contextlib import contextmanager
from unittest.mock import Mock, AsyncMock, patch

from haproxy_template_ic.dataplane.endpoint import DataplaneEndpoint
from haproxy_template_ic.dataplane.types import (
    ConfigChange,
    ConfigChangeType,
    ConfigSectionType,
)


@pytest.fixture(scope="module")
def test_endpoint(test_auth):
    """Create test endpoint with sample configuration."""
    return DataplaneEndpoint(
        url="http://localhost:5555/v3",
        dataplane_auth=test_auth,
    )


@pytest.fixture
def mock_client():
    """Create a mock authenticated HTTP client."""
    return Mock()


@pytest.fixture
def mock_get_client(mock_client):
    """Create a mock client factory function."""
    return Mock(return_value=mock_client)


@pytest.fixture
def mock_metrics():
    """Create mock metrics collector for dataplane operations."""
    # Create mock context manager for timing
    mock_timer = Mock()
    mock_timer.__enter__ = Mock(return_value=mock_timer)
    mock_timer.__exit__ = Mock(return_value=None)

    # Create mock metrics instance
    mock_metrics_instance = Mock()
    mock_metrics_instance.time_dataplane_api_operation.return_value = mock_timer
    mock_metrics_instance.record_dataplane_api_request = Mock()

    return mock_metrics_instance


# ConfigChange factory functions
def create_frontend_config_change(
    section_name: str = "web",
    bind_port: str = "*:80",
    change_type: ConfigChangeType = ConfigChangeType.CREATE,
) -> ConfigChange:
    """Create a standard frontend ConfigChange for testing."""
    return ConfigChange(
        change_type=change_type,
        section_type=ConfigSectionType.FRONTEND,
        section_name=section_name,
        new_config={"bind": bind_port},
    )


def create_backend_config_change(
    section_name: str = "api", change_type: ConfigChangeType = ConfigChangeType.CREATE
) -> ConfigChange:
    """Create a standard backend ConfigChange for testing."""
    return ConfigChange(
        change_type=change_type,
        section_type=ConfigSectionType.BACKEND,
        section_name=section_name,
        new_config={"balance": "roundrobin"},
    )


@pytest.fixture
def mock_metrics_collector_patch():
    """Create mock metrics collector that matches the patch pattern used in storage API tests."""
    return Mock(
        time_dataplane_api_operation=Mock(
            return_value=Mock(__enter__=Mock(), __exit__=Mock())
        ),
        record_dataplane_api_request=Mock(),
    )


# Storage API patch context managers
@contextmanager
def patch_storage_map_apis(
    mock_get_all=None, mock_create=None, mock_replace=None, mock_metrics=None
):
    """
    Context manager for patching storage map APIs.

    Args:
        mock_get_all: AsyncMock for get_all_storage_map_files (default: returns [])
        mock_create: AsyncMock for create_storage_map_file (default: returns MapFile)
        mock_replace: AsyncMock for replace_storage_map_file (default: returns MapFile)
        mock_metrics: Mock for get_metrics_collector (default: returns basic mock)
    """
    from haproxy_dataplane_v3.models import MapFile

    # Set up default mocks if not provided
    if mock_get_all is None:
        mock_get_all = AsyncMock(return_value=[])
    if mock_create is None:
        mock_create = AsyncMock(return_value=MapFile(storage_name="test.map"))
    if mock_replace is None:
        mock_replace = AsyncMock(return_value=MapFile(storage_name="test.map"))
    if mock_metrics is None:
        mock_metrics = Mock(
            time_dataplane_api_operation=Mock(
                return_value=Mock(__enter__=Mock(), __exit__=Mock())
            ),
            record_dataplane_api_request=Mock(),
        )

    # Apply all patches
    with patch.multiple(
        "haproxy_template_ic.dataplane.storage_api",
        get_all_storage_map_files=mock_get_all,
        create_storage_map_file=mock_create,
        replace_storage_map_file=mock_replace,
        get_metrics_collector=lambda: mock_metrics,
    ):
        yield {
            "get_all": mock_get_all,
            "create": mock_create,
            "replace": mock_replace,
            "metrics": mock_metrics,
        }


@contextmanager
def patch_storage_certificate_apis(
    mock_get_all=None, mock_create=None, mock_replace=None, mock_metrics=None
):
    """
    Context manager for patching storage certificate APIs.

    Args:
        mock_get_all: AsyncMock for get_all_storage_ssl_certificates (default: returns [])
        mock_create: AsyncMock for create_storage_ssl_certificate (default: returns SSLFile)
        mock_replace: AsyncMock for replace_storage_ssl_certificate (default: returns SSLFile)
        mock_metrics: Mock for get_metrics_collector (default: returns basic mock)
    """
    from haproxy_dataplane_v3.models import SSLFile

    # Set up default mocks if not provided
    if mock_get_all is None:
        mock_get_all = AsyncMock(return_value=[])
    if mock_create is None:
        mock_create = AsyncMock(return_value=SSLFile(storage_name="test.crt"))
    if mock_replace is None:
        mock_replace = AsyncMock(return_value=SSLFile(storage_name="test.crt"))
    if mock_metrics is None:
        mock_metrics = Mock(
            time_dataplane_api_operation=Mock(
                return_value=Mock(__enter__=Mock(), __exit__=Mock())
            ),
            record_dataplane_api_request=Mock(),
        )

    patches = {}
    if mock_get_all:
        patches["get_all_storage_ssl_certificates"] = mock_get_all
    if mock_create:
        patches["create_storage_ssl_certificate"] = mock_create
    if mock_replace:
        patches["replace_storage_ssl_certificate"] = mock_replace
    if mock_metrics:
        patches["get_metrics_collector"] = lambda: mock_metrics

    # Apply all patches
    with patch.multiple("haproxy_template_ic.dataplane.storage_api", **patches):
        yield {
            "get_all": mock_get_all,
            "create": mock_create,
            "replace": mock_replace,
            "metrics": mock_metrics,
        }


@contextmanager
def patch_storage_file_apis(
    mock_get_all=None, mock_create=None, mock_replace=None, mock_metrics=None
):
    """
    Context manager for patching storage general file APIs.

    Args:
        mock_get_all: AsyncMock for get_all_storage_general_files (default: returns [])
        mock_create: AsyncMock for create_storage_general_file (default: returns GeneralUseFile)
        mock_replace: AsyncMock for replace_storage_general_file (default: returns GeneralUseFile)
        mock_metrics: Mock for get_metrics_collector (default: returns basic mock)
    """
    from haproxy_dataplane_v3.models import GeneralUseFile

    # Set up default mocks if not provided
    if mock_get_all is None:
        mock_get_all = AsyncMock(return_value=[])
    if mock_create is None:
        mock_create = AsyncMock(return_value=GeneralUseFile(storage_name="test.txt"))
    if mock_replace is None:
        mock_replace = AsyncMock(return_value=GeneralUseFile(storage_name="test.txt"))
    if mock_metrics is None:
        mock_metrics = Mock(
            time_dataplane_api_operation=Mock(
                return_value=Mock(__enter__=Mock(), __exit__=Mock())
            ),
            record_dataplane_api_request=Mock(),
        )

    patches = {}
    if mock_get_all:
        patches["get_all_storage_general_files"] = mock_get_all
    if mock_create:
        patches["create_storage_general_file"] = mock_create
    if mock_replace:
        patches["replace_storage_general_file"] = mock_replace
    if mock_metrics:
        patches["get_metrics_collector"] = lambda: mock_metrics

    # Apply all patches
    with patch.multiple("haproxy_template_ic.dataplane.storage_api", **patches):
        yield {
            "get_all": mock_get_all,
            "create": mock_create,
            "replace": mock_replace,
            "metrics": mock_metrics,
        }
