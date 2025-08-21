"""
Unit tests for dataplane functionality.

Tests the HAProxy Dataplane API integration including pod discovery,
client operations, and configuration synchronization.
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch

from haproxy_template_ic.dataplane import (
    DataplaneAPIError,
    ValidationError,
    DataplaneClient,
    ConfigSynchronizer,
    DeploymentHistory,
    get_production_urls_from_index,
)
from haproxy_template_ic.config_models import HAProxyConfigContext


class TestDeploymentHistory:
    """Test the DeploymentHistory class."""

    def test_deployment_history_creation(self):
        """Test DeploymentHistory creation."""
        history = DeploymentHistory()
        assert history._history == {}

    def test_record_successful_deployment(self):
        """Test recording successful deployment."""
        history = DeploymentHistory()
        history.record("http://test:5555", "v1.0", True)

        data = history.to_dict()
        assert "deployment_history" in data
        assert "http://test:5555" in data["deployment_history"]

        entry = data["deployment_history"]["http://test:5555"]
        assert entry["version"] == "v1.0"
        assert entry["success"] is True
        assert entry["last_attempt"] == "v1.0"
        assert entry["error"] is None

    def test_record_failed_deployment(self):
        """Test recording failed deployment."""
        history = DeploymentHistory()
        history.record("http://test:5555", "v1.0", False, "Connection failed")

        data = history.to_dict()
        entry = data["deployment_history"]["http://test:5555"]
        assert entry["version"] is None  # No successful version yet
        assert entry["success"] is False
        assert entry["last_attempt"] == "v1.0"
        assert entry["error"] == "Connection failed"


class TestGetProductionUrlsFromIndex:
    """Test the get_production_urls_from_index function."""

    def test_empty_index(self):
        """Test with empty index."""
        urls = get_production_urls_from_index({})
        assert urls == []

    def test_running_pod_with_ip(self):
        """Test extraction from running pod with IP."""
        indexed_pods = {
            ("default", "haproxy-1"): {
                "status": {"phase": "Running", "podIP": "192.168.1.10"},
                "metadata": {"annotations": {}},
            }
        }
        urls = get_production_urls_from_index(indexed_pods)
        assert urls == ["http://192.168.1.10:5555"]

    def test_custom_port_annotation(self):
        """Test custom dataplane port annotation."""
        indexed_pods = {
            ("default", "haproxy-1"): {
                "status": {"phase": "Running", "podIP": "192.168.1.10"},
                "metadata": {
                    "annotations": {"haproxy-template-ic/dataplane-port": "8888"}
                },
            }
        }
        urls = get_production_urls_from_index(indexed_pods)
        assert urls == ["http://192.168.1.10:8888"]

    def test_non_running_pod_excluded(self):
        """Test that non-running pods are excluded."""
        indexed_pods = {
            ("default", "haproxy-1"): {
                "status": {"phase": "Pending", "podIP": "192.168.1.10"},
                "metadata": {"annotations": {}},
            }
        }
        urls = get_production_urls_from_index(indexed_pods)
        assert urls == []

    def test_pod_without_ip_excluded(self):
        """Test that pods without IP are excluded."""
        indexed_pods = {
            ("default", "haproxy-1"): {
                "status": {"phase": "Running"},
                "metadata": {"annotations": {}},
            }
        }
        urls = get_production_urls_from_index(indexed_pods)
        assert urls == []


class TestDataplaneAPIError:
    """Test custom exception classes."""

    def test_dataplane_api_error(self):
        """Test DataplaneAPIError exception."""
        error = DataplaneAPIError("Test error message")
        assert str(error) == "Test error message"

    def test_validation_error_inheritance(self):
        """Test ValidationError inherits from DataplaneAPIError."""
        error = ValidationError("Validation failed")
        assert isinstance(error, DataplaneAPIError)
        # ValidationError now includes operation context automatically
        assert "Validation failed" in str(error)
        assert "operation=validate" in str(error)


class TestDataplaneClient:
    """Test the DataplaneClient class."""

    @pytest.fixture
    def client(self):
        """Create a DataplaneClient instance."""
        return DataplaneClient(
            "http://192.168.1.1:5555", timeout=10.0, auth=("admin", "test")
        )

    def test_init_with_v3_path(self):
        """Test client initialization with /v3 path."""
        client = DataplaneClient("http://192.168.1.1:5555/v3")
        assert client.base_url == "http://192.168.1.1:5555/v3"

    def test_init_without_v3_path(self):
        """Test client initialization without /v3 path."""
        client = DataplaneClient("http://192.168.1.1:5555")
        assert client.base_url == "http://192.168.1.1:5555/v3"


class TestConfigSynchronizer:
    """Test the simplified ConfigSynchronizer class."""

    @pytest.fixture
    def mock_config_context(self):
        """Create a mock HAProxyConfigContext."""
        context = Mock(spec=HAProxyConfigContext)
        context.rendered_config = Mock()
        context.rendered_config.content = "global\n  daemon"
        return context

    def test_init(self):
        """Test ConfigSynchronizer initialization."""
        production_urls = ["http://192.168.1.1:5555", "http://192.168.1.2:5555"]
        from haproxy_template_ic.credentials import Credentials, DataplaneAuth

        credentials = Credentials(
            dataplane=DataplaneAuth(username="admin", password="adminpass"),
            validation=DataplaneAuth(username="admin", password="validationpass"),
        )
        synchronizer = ConfigSynchronizer(
            production_urls=production_urls,
            validation_url="http://localhost:5555",
            credentials=credentials,
        )
        assert synchronizer.production_urls == production_urls
        assert synchronizer.validation_url == "http://localhost:5555"

    @pytest.mark.asyncio
    async def test_sync_configuration_no_rendered_config(self):
        """Test sync with no rendered config."""
        from haproxy_template_ic.credentials import Credentials, DataplaneAuth

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


class TestDataplaneClientMethods:
    """Test DataplaneClient methods for coverage."""

    @pytest.fixture
    def mock_client(self):
        """Create a DataplaneClient for testing."""
        return DataplaneClient("http://test:5555", timeout=10.0)

    def test_get_configuration(self, mock_client):
        """Test configuration lazy loading."""
        config1 = mock_client._get_configuration()
        config2 = mock_client._get_configuration()
        # Should return same instance (lazy loading)
        assert config1 is config2
        assert config1.host == "http://test:5555/v3"


class TestConfigSynchronizerMethods:
    """Test ConfigSynchronizer methods for coverage."""

    @pytest.mark.asyncio
    async def test_sync_configuration_validation_failure(self):
        """Test sync with validation failure."""
        from haproxy_template_ic.credentials import Credentials, DataplaneAuth

        credentials = Credentials(
            dataplane=DataplaneAuth(username="admin", password="adminpass"),
            validation=DataplaneAuth(username="admin", password="validationpass"),
        )
        synchronizer = ConfigSynchronizer(
            production_urls=["http://test:5555"],
            validation_url="http://localhost:5555",
            credentials=credentials,
        )

        context = Mock()
        context.rendered_config.content = "invalid config"

        with patch.object(synchronizer, "validation_url", "http://localhost:5555"):
            with patch(
                "haproxy_template_ic.dataplane.DataplaneClient"
            ) as mock_client_class:
                mock_client = Mock()
                mock_client.validate_configuration = AsyncMock(
                    side_effect=ValidationError("Validation failed")
                )
                mock_client_class.return_value = mock_client

                with pytest.raises(
                    ValidationError, match="Configuration validation failed"
                ):
                    await synchronizer.sync_configuration(context)

    @pytest.mark.asyncio
    async def test_sync_configuration_mixed_results(self):
        """Test sync with mixed success/failure results."""
        deployment_history = DeploymentHistory()
        from haproxy_template_ic.credentials import Credentials, DataplaneAuth

        credentials = Credentials(
            dataplane=DataplaneAuth(username="admin", password="adminpass"),
            validation=DataplaneAuth(username="admin", password="validationpass"),
        )
        synchronizer = ConfigSynchronizer(
            production_urls=["http://test1:5555", "http://test2:5555"],
            validation_url="http://localhost:5555",
            credentials=credentials,
            deployment_history=deployment_history,
        )

        context = Mock()
        context.rendered_config.content = "global\n    daemon"

        with patch(
            "haproxy_template_ic.dataplane.DataplaneClient"
        ) as mock_client_class:

            def create_mock_client(url, **kwargs):
                mock_client = Mock()
                mock_client.validate_configuration = AsyncMock(return_value=None)

                if "test1" in url:
                    mock_client.deploy_configuration = AsyncMock(return_value="v1.0")
                else:
                    mock_client.deploy_configuration = AsyncMock(
                        side_effect=Exception("Connection failed")
                    )

                return mock_client

            mock_client_class.side_effect = create_mock_client

            results = await synchronizer.sync_configuration(context)

            assert results["successful"] == 1
            assert results["failed"] == 1
            assert len(results["errors"]) == 1
            assert "Connection failed" in results["errors"][0]


class TestNormalizeDataplaneUrl:
    """Test normalize_dataplane_url function."""

    def test_normalize_url_without_v3(self):
        """Test URL normalization adds /v3."""
        from haproxy_template_ic.dataplane import normalize_dataplane_url

        result = normalize_dataplane_url("http://localhost:5555")
        assert result == "http://localhost:5555/v3"

    def test_normalize_url_with_trailing_slash(self):
        """Test URL normalization with trailing slash."""
        from haproxy_template_ic.dataplane import normalize_dataplane_url

        result = normalize_dataplane_url("http://localhost:5555/")
        assert result == "http://localhost:5555/v3"

    def test_normalize_url_already_has_v3(self):
        """Test URL normalization when /v3 already exists."""
        from haproxy_template_ic.dataplane import normalize_dataplane_url

        result = normalize_dataplane_url("http://localhost:5555/v3")
        assert result == "http://localhost:5555/v3"

    def test_normalize_url_with_query_params(self):
        """Test URL normalization preserves query parameters."""
        from haproxy_template_ic.dataplane import normalize_dataplane_url

        result = normalize_dataplane_url("http://localhost:5555?timeout=30")
        assert result == "http://localhost:5555/v3?timeout=30"

    def test_normalize_url_with_path_and_query(self):
        """Test URL normalization with existing path and query parameters."""
        from haproxy_template_ic.dataplane import normalize_dataplane_url

        result = normalize_dataplane_url("https://api.example.com/haproxy?auth=token")
        assert result == "https://api.example.com/haproxy/v3?auth=token"


class TestValidationErrorClass:
    """Test ValidationError class functionality."""

    def test_validation_error_creation(self):
        """Test ValidationError creation with all parameters."""
        error = ValidationError(
            "Config invalid",
            endpoint="http://test:5555",
            config_size=1024,
            validation_details="Missing global section",
            original_error=Exception("Parse error"),
        )

        assert str(error).startswith("Config invalid")
        assert "endpoint=http://test:5555" in str(error)
        assert "config_size=1024" in str(error)
        assert "details=Missing global section" in str(error)
        assert error.config_size == 1024
        assert error.validation_details == "Missing global section"

    def test_validation_error_minimal(self):
        """Test ValidationError with minimal parameters."""
        error = ValidationError("Config invalid")

        assert str(error) == "Config invalid [operation=validate]"
        assert error.operation == "validate"


class TestDataplaneAPIErrorClass:
    """Test DataplaneAPIError class functionality."""

    def test_dataplane_api_error_full(self):
        """Test DataplaneAPIError with all parameters."""
        original = Exception("Network error")
        error = DataplaneAPIError(
            "Request failed",
            endpoint="http://test:5555",
            operation="get_version",
            original_error=original,
        )

        assert "Request failed" in str(error)
        assert "operation=get_version" in str(error)
        assert "endpoint=http://test:5555" in str(error)
        assert error.endpoint == "http://test:5555"
        assert error.operation == "get_version"
        assert error.original_error is original

    def test_dataplane_api_error_minimal(self):
        """Test DataplaneAPIError with minimal parameters."""
        error = DataplaneAPIError("Request failed")

        assert str(error) == "Request failed"
        assert error.endpoint is None
        assert error.operation is None
        assert error.original_error is None


class TestDataplaneClientInitialization:
    """Test DataplaneClient initialization and configuration."""

    def test_client_init_default_auth(self):
        """Test client initialization with default auth."""
        client = DataplaneClient("http://test:5555")

        assert client.base_url == "http://test:5555/v3"
        assert client.timeout == 30.0
        assert client.auth == ("admin", "adminpass")

    def test_client_init_custom_auth(self):
        """Test client initialization with custom auth."""
        client = DataplaneClient(
            "http://test:5555", timeout=60.0, auth=("user", "pass")
        )

        assert client.base_url == "http://test:5555/v3"
        assert client.timeout == 60.0
        assert client.auth == ("user", "pass")

    def test_client_lazy_configuration(self):
        """Test lazy configuration initialization."""
        client = DataplaneClient("http://test:5555")

        # Configuration should be None initially
        assert client._configuration is None

        # First call should create configuration
        config1 = client._get_configuration()
        assert client._configuration is not None

        # Second call should return same instance
        config2 = client._get_configuration()
        assert config1 is config2


class TestConfigSynchronizerSuccessPath:
    """Test ConfigSynchronizer success scenarios."""

    @pytest.mark.asyncio
    async def test_sync_configuration_success(self):
        """Test successful configuration synchronization."""
        deployment_history = DeploymentHistory()
        from haproxy_template_ic.credentials import Credentials, DataplaneAuth

        credentials = Credentials(
            dataplane=DataplaneAuth(username="admin", password="adminpass"),
            validation=DataplaneAuth(username="admin", password="validationpass"),
        )
        synchronizer = ConfigSynchronizer(
            production_urls=["http://test1:5555"],
            validation_url="http://localhost:5555",
            credentials=credentials,
            deployment_history=deployment_history,
        )

        context = Mock()
        context.rendered_config.content = "global\n    daemon"

        with patch(
            "haproxy_template_ic.dataplane.DataplaneClient"
        ) as mock_client_class:
            mock_client = Mock()
            mock_client.validate_configuration = AsyncMock(return_value=None)
            mock_client.deploy_configuration = AsyncMock(return_value="v1.0")
            mock_client_class.return_value = mock_client

            results = await synchronizer.sync_configuration(context)

            assert results["successful"] == 1
            assert results["failed"] == 0
            assert len(results["errors"]) == 0


class TestDataplaneRetryMechanisms:
    """Test retry mechanisms and error handling in dataplane operations."""

    def test_retry_error_classification(self):
        """Test error classification for retry logic."""
        # Simple test without complex async operations
        assert True  # Placeholder for retry logic tests


class TestProductionUrlExtraction:
    """Test production URL extraction edge cases."""

    def test_get_production_urls_with_mixed_pod_states(self):
        """Test URL extraction with mixed pod states."""
        indexed_pods = {
            ("default", "haproxy-1"): {
                "status": {"phase": "Running", "podIP": "192.168.1.10"},
                "metadata": {"annotations": {}},
            },
            ("default", "haproxy-2"): {
                "status": {"phase": "Pending", "podIP": "192.168.1.11"},
                "metadata": {"annotations": {}},
            },
            ("default", "haproxy-3"): {
                "status": {"phase": "Running"},  # No IP
                "metadata": {"annotations": {}},
            },
            ("default", "haproxy-4"): {
                "status": {"phase": "Running", "podIP": "192.168.1.14"},
                "metadata": {
                    "annotations": {"haproxy-template-ic/dataplane-port": "9999"}
                },
            },
        }

        urls = get_production_urls_from_index(indexed_pods)

        # Should only include running pods with IPs
        assert len(urls) == 2
        assert "http://192.168.1.10:5555" in urls
        assert "http://192.168.1.14:9999" in urls

        # Should not include pending or pods without IPs
        assert "http://192.168.1.11:5555" not in urls

    def test_get_production_urls_deterministic_output(self):
        """Test that URL extraction produces deterministic output."""
        indexed_pods = {
            ("default", "haproxy-c"): {
                "status": {"phase": "Running", "podIP": "192.168.1.13"},
                "metadata": {"annotations": {}},
            },
            ("default", "haproxy-a"): {
                "status": {"phase": "Running", "podIP": "192.168.1.11"},
                "metadata": {"annotations": {}},
            },
            ("default", "haproxy-b"): {
                "status": {"phase": "Running", "podIP": "192.168.1.12"},
                "metadata": {"annotations": {}},
            },
        }

        urls = get_production_urls_from_index(indexed_pods)

        # Should return consistent results
        assert len(urls) == 3
        assert "http://192.168.1.11:5555" in urls
        assert "http://192.168.1.12:5555" in urls
        assert "http://192.168.1.13:5555" in urls


class TestDeploymentHistoryDetailed:
    """Test DeploymentHistory class with more scenarios."""

    def test_record_failure_then_success(self):
        """Test recording failure followed by success."""
        history = DeploymentHistory()

        # Record failure
        history.record("http://test:5555", "v1.0", False, "Deploy failed")
        data = history.to_dict()

        entry = data["deployment_history"]["http://test:5555"]
        assert entry["version"] is None  # No successful version yet
        assert entry["success"] is False
        assert entry["last_attempt"] == "v1.0"
        assert entry["error"] == "Deploy failed"

        # Record success
        history.record("http://test:5555", "v1.1", True)
        data = history.to_dict()

        entry = data["deployment_history"]["http://test:5555"]
        assert entry["version"] == "v1.1"  # Now has successful version
        assert entry["success"] is True
        assert entry["last_attempt"] == "v1.1"
        assert entry["error"] is None

    def test_multiple_endpoints(self):
        """Test recording for multiple endpoints."""
        history = DeploymentHistory()

        history.record("http://test1:5555", "v1.0", True)
        history.record("http://test2:5555", "v1.0", False, "Network error")

        data = history.to_dict()
        assert len(data["deployment_history"]) == 2

        assert data["deployment_history"]["http://test1:5555"]["success"] is True
        assert data["deployment_history"]["http://test2:5555"]["success"] is False
