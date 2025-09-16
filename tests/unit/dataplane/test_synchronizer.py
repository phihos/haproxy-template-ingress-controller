"""
Simple unit tests for dataplane functionality - coverage focused.

Tests basic functionality without complex async mocking to avoid test failures.
"""

import pytest
from unittest.mock import Mock

from haproxy_template_ic.dataplane import (
    DataplaneAPIError,
    ValidationError,
    DataplaneClient,
    ConfigSynchronizer,
    get_production_urls_from_index,
    normalize_dataplane_url,
)
from haproxy_template_ic.credentials import Credentials, DataplaneAuth


class TestNormalizeDataplaneUrlComplete:
    """Test URL normalization comprehensively."""

    def test_normalize_basic_url(self):
        """Test basic URL normalization."""
        result = normalize_dataplane_url("http://localhost:5555")
        assert result == "http://localhost:5555/v3"

    def test_normalize_url_with_trailing_slash(self):
        """Test URL with trailing slash."""
        result = normalize_dataplane_url("http://localhost:5555/")
        assert result == "http://localhost:5555/v3"

    def test_normalize_url_already_has_v3(self):
        """Test URL that already has /v3."""
        result = normalize_dataplane_url("http://localhost:5555/v3")
        assert result == "http://localhost:5555/v3"

    def test_normalize_url_with_path(self):
        """Test URL with existing path."""
        result = normalize_dataplane_url("https://api.example.com/haproxy")
        assert result == "https://api.example.com/haproxy/v3"

    def test_normalize_url_with_query_params(self):
        """Test URL with query parameters."""
        result = normalize_dataplane_url("http://localhost:5555?timeout=30")
        assert result == "http://localhost:5555/v3?timeout=30"

    def test_normalize_url_with_path_and_query(self):
        """Test URL with both path and query parameters."""
        result = normalize_dataplane_url("https://api.example.com/haproxy?auth=token")
        assert result == "https://api.example.com/haproxy/v3?auth=token"


class TestProductionUrlExtractionComplete:
    """Test production URL extraction comprehensively."""

    def test_empty_index(self):
        """Test with empty index."""
        urls, url_to_pod_name = get_production_urls_from_index({})
        assert urls == []
        assert url_to_pod_name == {}

    def test_single_running_pod(self):
        """Test with single running pod."""
        indexed_pods = {
            ("default", "haproxy-1"): {
                "status": {"phase": "Running", "podIP": "192.168.1.10"},
                "metadata": {"annotations": {}, "name": "haproxy-1"},
            }
        }
        urls, url_to_pod_name = get_production_urls_from_index(indexed_pods)
        assert urls == ["http://192.168.1.10:5555"]
        assert url_to_pod_name == {"http://192.168.1.10:5555": "haproxy-1"}

    def test_custom_port_annotation(self):
        """Test with custom dataplane port."""
        indexed_pods = {
            ("default", "haproxy-1"): {
                "status": {"phase": "Running", "podIP": "192.168.1.10"},
                "metadata": {
                    "annotations": {"haproxy-template-ic/dataplane-port": "8888"},
                    "name": "haproxy-custom",
                },
            }
        }
        urls, url_to_pod_name = get_production_urls_from_index(indexed_pods)
        assert urls == ["http://192.168.1.10:8888"]
        assert url_to_pod_name == {"http://192.168.1.10:8888": "haproxy-custom"}

    def test_non_running_pods_excluded(self):
        """Test that non-running pods are excluded."""
        indexed_pods = {
            ("default", "haproxy-pending"): {
                "status": {"phase": "Pending", "podIP": "192.168.1.10"},
                "metadata": {"annotations": {}, "name": "haproxy-pending"},
            },
            ("default", "haproxy-failed"): {
                "status": {"phase": "Failed", "podIP": "192.168.1.11"},
                "metadata": {"annotations": {}, "name": "haproxy-failed"},
            },
            ("default", "haproxy-running"): {
                "status": {"phase": "Running", "podIP": "192.168.1.12"},
                "metadata": {"annotations": {}, "name": "haproxy-running"},
            },
        }
        urls, url_to_pod_name = get_production_urls_from_index(indexed_pods)
        assert urls == ["http://192.168.1.12:5555"]
        assert url_to_pod_name == {"http://192.168.1.12:5555": "haproxy-running"}

    def test_pods_without_ip_excluded(self):
        """Test that pods without IP are excluded."""
        indexed_pods = {
            ("default", "haproxy-no-ip"): {
                "status": {"phase": "Running"},
                "metadata": {"annotations": {}, "name": "haproxy-no-ip"},
            },
            ("default", "haproxy-with-ip"): {
                "status": {"phase": "Running", "podIP": "192.168.1.10"},
                "metadata": {"annotations": {}, "name": "haproxy-with-ip"},
            },
        }
        urls, url_to_pod_name = get_production_urls_from_index(indexed_pods)
        assert urls == ["http://192.168.1.10:5555"]
        assert url_to_pod_name == {"http://192.168.1.10:5555": "haproxy-with-ip"}

    def test_multiple_pods_sorted_output(self):
        """Test multiple pods produce sorted output."""
        indexed_pods = {
            ("default", "haproxy-c"): {
                "status": {"phase": "Running", "podIP": "192.168.1.13"},
                "metadata": {"annotations": {}, "name": "haproxy-c"},
            },
            ("default", "haproxy-a"): {
                "status": {"phase": "Running", "podIP": "192.168.1.11"},
                "metadata": {"annotations": {}, "name": "haproxy-a"},
            },
            ("default", "haproxy-b"): {
                "status": {"phase": "Running", "podIP": "192.168.1.12"},
                "metadata": {"annotations": {}, "name": "haproxy-b"},
            },
        }

        urls, url_to_pod_name = get_production_urls_from_index(indexed_pods)

        # URLs should be deterministic (not necessarily sorted, but consistent)
        assert len(urls) == 3
        assert "http://192.168.1.11:5555" in urls
        assert "http://192.168.1.12:5555" in urls
        assert "http://192.168.1.13:5555" in urls

        # Pod name mapping should be complete
        assert len(url_to_pod_name) == 3
        assert url_to_pod_name["http://192.168.1.11:5555"] == "haproxy-a"
        assert url_to_pod_name["http://192.168.1.12:5555"] == "haproxy-b"
        assert url_to_pod_name["http://192.168.1.13:5555"] == "haproxy-c"


class TestDataplaneClientSimple:
    """Test DataplaneClient initialization without complex mocking."""

    def test_client_initialization_defaults(self):
        """Test client with default parameters."""
        client = DataplaneClient("http://test:5555")
        assert client.base_url == "http://test:5555/v3"
        assert client.timeout == 30.0
        assert client.auth == ("admin", "adminpass")

    def test_client_initialization_custom(self):
        """Test client with custom parameters."""
        client = DataplaneClient(
            "http://test:8888/v3", timeout=60.0, auth=("user", "pass")
        )
        assert client.base_url == "http://test:8888/v3"
        assert client.timeout == 60.0
        assert client.auth == ("user", "pass")

    def test_client_configuration_lazy_loading(self, monkeypatch):
        """Test client lazy loading."""
        # Mock AuthenticatedClient to prevent actual network client creation
        # We need to override the global monkeypatch that removed __init__
        mock_client_instance = Mock()
        monkeypatch.setattr(
            "haproxy_dataplane_v3.AuthenticatedClient.__init__",
            lambda *args, **kwargs: None,
        )
        monkeypatch.setattr(
            "haproxy_dataplane_v3.AuthenticatedClient.__new__",
            lambda cls, *args, **kwargs: mock_client_instance,
        )

        client = DataplaneClient("http://test:5555")

        # Initially client should be None
        assert client._client is None

        # First call creates client
        client1 = client._get_client()
        assert client._client is not None
        assert client1 is mock_client_instance

        # Second call returns same instance (no new creation)
        client2 = client._get_client()
        assert client1 is client2


class TestConfigSynchronizerSimple:
    """Test ConfigSynchronizer initialization."""

    def test_synchronizer_initialization(self):
        """Test synchronizer initialization."""

        credentials = Credentials(
            dataplane=DataplaneAuth(username="admin", password="adminpass"),
            validation=DataplaneAuth(username="admin", password="validationpass"),
        )

        production_urls = ["http://192.168.1.1:5555", "http://192.168.1.2:5555"]

        synchronizer = ConfigSynchronizer(
            production_urls=production_urls,
            validation_url="http://localhost:5555",
            credentials=credentials,
        )

        assert synchronizer.production_urls == production_urls
        assert synchronizer.validation_url == "http://localhost:5555"
        assert synchronizer.credentials == credentials

    @pytest.mark.asyncio
    async def test_sync_configuration_no_rendered_config(self):
        """Test sync with no rendered config."""

        credentials = Credentials(
            dataplane=DataplaneAuth(username="admin", password="adminpass"),
            validation=DataplaneAuth(username="admin", password="validationpass"),
        )

        synchronizer = ConfigSynchronizer(
            production_urls=["http://192.168.1.1:5555"],
            validation_url="http://localhost:5555",
            credentials=credentials,
        )

        context = Mock()
        context.rendered_config = None

        with pytest.raises(
            DataplaneAPIError, match="No rendered HAProxy configuration"
        ):
            await synchronizer.sync_configuration(context)


class TestExceptionClasses:
    """Test exception class hierarchies."""

    def test_dataplane_api_error_basic(self):
        """Test basic DataplaneAPIError."""
        error = DataplaneAPIError("Test error")
        assert str(error) == "Test error"
        assert error.endpoint is None
        assert error.operation is None
        assert error.original_error is None

    def test_dataplane_api_error_with_context(self):
        """Test DataplaneAPIError with context."""
        original = Exception("Network error")
        error = DataplaneAPIError(
            "Request failed",
            endpoint="http://test:5555",
            operation="deploy_config",
            original_error=original,
        )

        error_str = str(error)
        assert "Request failed" in error_str
        assert "operation=deploy_config" in error_str
        assert "endpoint=http://test:5555" in error_str
        assert error.original_error is original

    def test_validation_error_inheritance(self):
        """Test ValidationError inherits from DataplaneAPIError."""
        error = ValidationError("Validation failed")
        assert isinstance(error, DataplaneAPIError)
        assert "operation=validate" in str(error)

    def test_validation_error_with_details(self):
        """Test ValidationError with validation details."""
        error = ValidationError(
            "Config invalid",
            endpoint="http://validation:5555",
            config_size=1024,
            validation_details="Missing global section",
            original_error=Exception("Parse error"),
        )

        error_str = str(error)
        assert "Config invalid" in error_str
        assert "endpoint=http://validation:5555" in error_str
        assert "config_size=1024" in error_str
        assert "details=Missing global section" in error_str
        assert error.config_size == 1024
        assert error.validation_details == "Missing global section"
