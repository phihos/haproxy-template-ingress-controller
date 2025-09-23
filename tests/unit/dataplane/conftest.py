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


# ============================================================================
# Universal Dataplane Client Mocking Infrastructure
# ============================================================================


def create_dataplane_response_factory():
    """Factory for creating proper dataplane Response objects."""
    from haproxy_dataplane_v3.types import Response
    from http import HTTPStatus

    def create_response(content):
        """Create proper Response object for dataplane client."""
        return Response(
            status_code=HTTPStatus.OK, content=b"", headers={}, parsed=content
        )

    return create_response


@pytest.fixture
def mock_all_dataplane_clients():
    """
    Universal fixture that mocks all dataplane client API calls.

    This fixture solves the @api_function decorator bypass issue by mocking
    directly at the haproxy_dataplane_v3 client level, preventing all network calls.

    Usage:
        def test_my_function(mock_all_dataplane_clients):
            # Override specific responses as needed
            mock_all_dataplane_clients.configure(
                backends=[Backend(name="test")],
                frontends=[Frontend(name="web")]
            )
            # Test code here - no network calls will be made
    """
    from contextlib import ExitStack
    from unittest.mock import patch

    create_response = create_dataplane_response_factory()

    # Default response data
    default_responses = {
        "backends": [],
        "frontends": [],
        "global": None,
        "empty_list": [],
    }

    # Create mock functions for each response type
    async def mock_get_backends(*args, **kwargs):
        return create_response(default_responses["backends"])

    async def mock_get_frontends(*args, **kwargs):
        return create_response(default_responses["frontends"])

    async def mock_get_global(*args, **kwargs):
        return create_response(default_responses["global"])

    async def mock_empty_list(*args, **kwargs):
        return create_response(default_responses["empty_list"])

    # All dataplane client patches that need to be applied
    client_patches = [
        (
            "haproxy_dataplane_v3.api.backend.get_backends.asyncio_detailed",
            mock_get_backends,
        ),
        (
            "haproxy_dataplane_v3.api.frontend.get_frontends.asyncio_detailed",
            mock_get_frontends,
        ),
        (
            "haproxy_dataplane_v3.api.global_.get_global.asyncio_detailed",
            mock_get_global,
        ),
        (
            "haproxy_dataplane_v3.api.defaults.get_defaults_sections.asyncio_detailed",
            mock_empty_list,
        ),
        (
            "haproxy_dataplane_v3.api.userlist.get_userlists.asyncio_detailed",
            mock_empty_list,
        ),
        ("haproxy_dataplane_v3.api.cache.get_caches.asyncio_detailed", mock_empty_list),
        (
            "haproxy_dataplane_v3.api.fcgi_app.get_fcgi_apps.asyncio_detailed",
            mock_empty_list,
        ),
        (
            "haproxy_dataplane_v3.api.http_errors.get_http_errors_sections.asyncio_detailed",
            mock_empty_list,
        ),
        (
            "haproxy_dataplane_v3.api.log_forward.get_log_forwards.asyncio_detailed",
            mock_empty_list,
        ),
        (
            "haproxy_dataplane_v3.api.mailers.get_mailers_sections.asyncio_detailed",
            mock_empty_list,
        ),
        (
            "haproxy_dataplane_v3.api.resolver.get_resolvers.asyncio_detailed",
            mock_empty_list,
        ),
        (
            "haproxy_dataplane_v3.api.peer.get_peer_sections.asyncio_detailed",
            mock_empty_list,
        ),
        ("haproxy_dataplane_v3.api.ring.get_rings.asyncio_detailed", mock_empty_list),
        (
            "haproxy_dataplane_v3.api.process_manager.get_programs.asyncio_detailed",
            mock_empty_list,
        ),
        (
            "haproxy_dataplane_v3.api.server.get_all_server_backend.asyncio_detailed",
            mock_empty_list,
        ),
        (
            "haproxy_dataplane_v3.api.acl.get_all_acl_backend.asyncio_detailed",
            mock_empty_list,
        ),
        (
            "haproxy_dataplane_v3.api.acl.get_all_acl_frontend.asyncio_detailed",
            mock_empty_list,
        ),
        (
            "haproxy_dataplane_v3.api.http_request_rule.get_all_http_request_rule_backend.asyncio_detailed",
            mock_empty_list,
        ),
        (
            "haproxy_dataplane_v3.api.http_request_rule.get_all_http_request_rule_frontend.asyncio_detailed",
            mock_empty_list,
        ),
        (
            "haproxy_dataplane_v3.api.http_response_rule.get_all_http_response_rule_backend.asyncio_detailed",
            mock_empty_list,
        ),
        (
            "haproxy_dataplane_v3.api.http_response_rule.get_all_http_response_rule_frontend.asyncio_detailed",
            mock_empty_list,
        ),
        (
            "haproxy_dataplane_v3.api.backend_switching_rule.get_backend_switching_rules.asyncio_detailed",
            mock_empty_list,
        ),
        (
            "haproxy_dataplane_v3.api.filter_.get_all_filter_backend.asyncio_detailed",
            mock_empty_list,
        ),
        (
            "haproxy_dataplane_v3.api.filter_.get_all_filter_frontend.asyncio_detailed",
            mock_empty_list,
        ),
        (
            "haproxy_dataplane_v3.api.log_target.get_all_log_target_backend.asyncio_detailed",
            mock_empty_list,
        ),
        (
            "haproxy_dataplane_v3.api.log_target.get_all_log_target_frontend.asyncio_detailed",
            mock_empty_list,
        ),
        (
            "haproxy_dataplane_v3.api.log_target.get_all_log_target_global.asyncio_detailed",
            mock_empty_list,
        ),
        (
            "haproxy_dataplane_v3.api.log_target.get_all_log_target_peer.asyncio_detailed",
            mock_empty_list,
        ),
        (
            "haproxy_dataplane_v3.api.log_target.get_all_log_target_log_forward.asyncio_detailed",
            mock_empty_list,
        ),
        (
            "haproxy_dataplane_v3.api.bind.get_all_bind_frontend.asyncio_detailed",
            mock_empty_list,
        ),
    ]

    # Apply all patches using ExitStack
    with ExitStack() as stack:
        for patch_path, mock_func in client_patches:
            stack.enter_context(patch(patch_path, side_effect=mock_func))

        # Create configurable mock controller
        class DataplaneMockController:
            def configure(self, backends=None, frontends=None, global_config=None):
                """Configure specific response data for test scenarios."""
                if backends is not None:
                    default_responses["backends"] = backends
                if frontends is not None:
                    default_responses["frontends"] = frontends
                if global_config is not None:
                    default_responses["global"] = global_config

            def reset(self):
                """Reset all responses to default empty values."""
                default_responses["backends"] = []
                default_responses["frontends"] = []
                default_responses["global"] = None

        controller = DataplaneMockController()
        yield controller


@pytest.fixture
def mock_dataplane_empty(mock_all_dataplane_clients):
    """
    Convenience fixture for tests that need empty dataplane responses.

    All API calls return empty lists or None. Perfect for testing error handling
    or scenarios with no existing configuration.
    """
    mock_all_dataplane_clients.reset()  # Already defaults to empty
    return mock_all_dataplane_clients


@pytest.fixture
def mock_dataplane_large_config(mock_all_dataplane_clients):
    """
    Convenience fixture for performance testing with large configuration datasets.

    Provides the same 100 backends + 50 frontends used in the performance test,
    ensuring consistent performance testing across the codebase.
    """
    from haproxy_dataplane_v3.models import Backend, Frontend

    large_backend_list = [Backend(name=f"backend-{i}") for i in range(100)]
    large_frontend_list = [Frontend(name=f"frontend-{i}") for i in range(50)]

    mock_all_dataplane_clients.configure(
        backends=large_backend_list, frontends=large_frontend_list
    )
    return mock_all_dataplane_clients


def mock_dataplane_with_data(backends=None, frontends=None, global_config=None):
    """
    Factory function for creating dataplane mocks with specific test data.

    Use this when you need custom test data that doesn't fit the standard fixtures.

    Example:
        @pytest.fixture
        def my_custom_mock(mock_all_dataplane_clients):
            return mock_dataplane_with_data(
                backends=[Backend(name="api")],
                frontends=[Frontend(name="web")]
            )(mock_all_dataplane_clients)
    """

    def configure_mock(mock_controller):
        mock_controller.configure(
            backends=backends or [],
            frontends=frontends or [],
            global_config=global_config,
        )
        return mock_controller

    return configure_mock
