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

# Import adapter fixtures

# Import API response mocking helpers


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
def patch_storage_apis(
    storage_type: str,
    mock_get_all=None,
    mock_create=None,
    mock_replace=None,
    mock_metrics=None,
):
    """
    Generic context manager for patching storage APIs.

    Args:
        storage_type: Type of storage ('map', 'certificate', 'file')
        mock_get_all: AsyncMock for get_all operation (default: returns [])
        mock_create: AsyncMock for create operation (default: returns appropriate model)
        mock_replace: AsyncMock for replace operation (default: returns appropriate model)
        mock_metrics: Mock for metrics collector (default: returns basic mock)
    """
    from haproxy_dataplane_v3.models import MapFile, SSLFile, GeneralUseFile

    # Map storage types to their corresponding models and API function names
    storage_config = {
        "map": {
            "model": MapFile,
            "extension": "map",
            "get_all": "get_all_storage_map_files",
            "create": "create_storage_map_file",
            "replace": "replace_storage_map_file",
        },
        "certificate": {
            "model": SSLFile,
            "extension": "crt",
            "get_all": "get_all_storage_ssl_certificates",
            "create": "create_storage_ssl_certificate",
            "replace": "replace_storage_ssl_certificate",
        },
        "file": {
            "model": GeneralUseFile,
            "extension": "txt",
            "get_all": "get_all_storage_general_files",
            "create": "create_storage_general_file",
            "replace": "replace_storage_general_file",
        },
    }

    if storage_type not in storage_config:
        raise ValueError(f"Unknown storage type: {storage_type}")

    config = storage_config[storage_type]

    # Set up default mocks if not provided
    if mock_get_all is None:
        from tests.unit.dataplane.adapter_fixtures import create_mock_api_response

        mock_get_all = AsyncMock(return_value=create_mock_api_response(content=[]))

    if mock_create is None:
        from tests.unit.dataplane.adapter_fixtures import create_storage_async_mock

        mock_create = create_storage_async_mock(
            config["model"],
            storage_name=f"test.{config['extension']}",
            reload_id="test-reload-123",
        )

    if mock_replace is None:
        from tests.unit.dataplane.adapter_fixtures import create_storage_async_mock

        mock_replace = create_storage_async_mock(
            config["model"],
            storage_name=f"test.{config['extension']}",
            reload_id="test-reload-123",
        )

    if mock_metrics is None:
        mock_metrics = Mock(
            time_dataplane_api_operation=Mock(
                return_value=Mock(__enter__=Mock(), __exit__=Mock())
            ),
            record_dataplane_api_request=Mock(),
        )

    # Build patches dictionary
    patches = {
        config["get_all"]: mock_get_all,
        config["create"]: mock_create,
        config["replace"]: mock_replace,
    }

    # Apply all patches
    with patch.multiple("haproxy_template_ic.dataplane.storage_api", **patches):
        yield {
            "get_all": mock_get_all,
            "create": mock_create,
            "replace": mock_replace,
            "metrics": mock_metrics,
        }


# Convenience functions for backward compatibility
@contextmanager
def patch_storage_map_apis(
    mock_get_all=None, mock_create=None, mock_replace=None, mock_metrics=None
):
    """Context manager for patching storage map APIs."""
    with patch_storage_apis(
        "map", mock_get_all, mock_create, mock_replace, mock_metrics
    ) as mocks:
        yield mocks


@contextmanager
def patch_storage_certificate_apis(
    mock_get_all=None, mock_create=None, mock_replace=None, mock_metrics=None
):
    """Context manager for patching storage certificate APIs."""
    with patch_storage_apis(
        "certificate", mock_get_all, mock_create, mock_replace, mock_metrics
    ) as mocks:
        yield mocks


@contextmanager
def patch_storage_file_apis(
    mock_get_all=None, mock_create=None, mock_replace=None, mock_metrics=None
):
    """Context manager for patching storage general file APIs."""
    with patch_storage_apis(
        "file", mock_get_all, mock_create, mock_replace, mock_metrics
    ) as mocks:
        yield mocks


# API Factory Functions to eliminate constructor duplication
def create_config_api(endpoint=None):
    """Create ConfigAPI instance with metrics for testing."""
    from haproxy_template_ic.dataplane.config_api import ConfigAPI
    from haproxy_template_ic.metrics import MetricsCollector
    from tests.unit.conftest import create_dataplane_endpoint_mock

    if endpoint is None:
        endpoint = create_dataplane_endpoint_mock()
    metrics = MetricsCollector()
    return ConfigAPI(endpoint, metrics)


def create_runtime_api(endpoint=None):
    """Create RuntimeAPI instance with metrics for testing."""
    from haproxy_template_ic.dataplane.runtime_api import RuntimeAPI
    from haproxy_template_ic.metrics import MetricsCollector
    from tests.unit.conftest import create_dataplane_endpoint_mock

    if endpoint is None:
        endpoint = create_dataplane_endpoint_mock()
    metrics = MetricsCollector()
    return RuntimeAPI(endpoint, metrics)


def create_storage_api(endpoint=None):
    """Create StorageAPI instance with metrics for testing."""
    from haproxy_template_ic.dataplane.storage_api import StorageAPI
    from haproxy_template_ic.metrics import MetricsCollector
    from tests.unit.conftest import create_dataplane_endpoint_mock

    if endpoint is None:
        endpoint = create_dataplane_endpoint_mock()
    metrics = MetricsCollector()
    return StorageAPI(endpoint, metrics)


def create_validation_api(endpoint=None):
    """Create ValidationAPI instance with metrics for testing."""
    from haproxy_template_ic.dataplane.validation_api import ValidationAPI
    from haproxy_template_ic.metrics import MetricsCollector
    from tests.unit.conftest import create_dataplane_endpoint_mock

    if endpoint is None:
        endpoint = create_dataplane_endpoint_mock()
    metrics = MetricsCollector()
    return ValidationAPI(endpoint, metrics)


def create_transaction_api(endpoint=None):
    """Create TransactionAPI instance with metrics for testing."""
    from haproxy_template_ic.dataplane.transaction_api import TransactionAPI
    from haproxy_template_ic.metrics import MetricsCollector
    from tests.unit.conftest import create_dataplane_endpoint_mock

    if endpoint is None:
        endpoint = create_dataplane_endpoint_mock()
    metrics = MetricsCollector()
    return TransactionAPI(endpoint, metrics)


def create_dataplane_operations(endpoint=None):
    """Create DataplaneOperations instance with metrics for testing."""
    from haproxy_template_ic.dataplane.operations import DataplaneOperations
    from haproxy_template_ic.metrics import MetricsCollector
    from tests.unit.conftest import create_dataplane_endpoint_mock

    if endpoint is None:
        endpoint = create_dataplane_endpoint_mock()
    metrics = MetricsCollector()
    return DataplaneOperations(endpoint, metrics)


def create_dataplane_client(endpoint=None, timeout=60.0):
    """Create DataplaneClient instance with metrics for testing."""
    from haproxy_template_ic.dataplane.client import DataplaneClient
    from haproxy_template_ic.metrics import MetricsCollector
    from tests.unit.conftest import create_dataplane_endpoint_mock

    if endpoint is None:
        endpoint = create_dataplane_endpoint_mock()
    metrics = MetricsCollector()
    return DataplaneClient(endpoint, metrics, timeout)


def create_config_synchronizer(endpoints=None):
    """Create ConfigSynchronizer instance with metrics for testing."""
    from haproxy_template_ic.dataplane.synchronizer import ConfigSynchronizer
    from haproxy_template_ic.metrics import MetricsCollector
    from tests.unit.conftest import create_dataplane_endpoint_mock

    if endpoints is None:
        from haproxy_template_ic.dataplane.endpoint import DataplaneEndpointSet

        endpoints = DataplaneEndpointSet([create_dataplane_endpoint_mock()])
    metrics = MetricsCollector()
    return ConfigSynchronizer(endpoints=endpoints, metrics=metrics)
