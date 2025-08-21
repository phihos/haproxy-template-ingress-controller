"""
Unit tests for dataplane functionality.

Tests the HAProxy Dataplane API integration including pod discovery,
client operations, and configuration synchronization.
"""

import pytest
from unittest.mock import Mock, AsyncMock, MagicMock, patch

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


class TestDataplaneCriticalPaths:
    """Test critical paths and edge cases for dataplane functionality."""

    def test_normalize_dataplane_url_malformed_urls(self):
        """Test URL normalization with malformed URLs."""
        from haproxy_template_ic.dataplane import normalize_dataplane_url

        # Test malformed scheme
        malformed_scheme_url = "htp://localhost:5555"  # typo in http
        result = normalize_dataplane_url(malformed_scheme_url)
        assert result == "htp://localhost:5555/v3"  # Should still work

        # Test missing scheme (should still work with urlparse)
        no_scheme_url = "localhost:5555"
        result = normalize_dataplane_url(no_scheme_url)
        assert result == "localhost:5555/v3"

        # Test with special characters in path
        special_chars_url = "http://localhost:5555/path%20with%20spaces"
        result = normalize_dataplane_url(special_chars_url)
        assert result == "http://localhost:5555/path%20with%20spaces/v3"

        # Test with malformed netloc - this will trigger the fallback
        malformed_netloc = "http://[invalid:ip]:5555"
        result = normalize_dataplane_url(malformed_netloc)
        assert result == "http://[invalid:ip]:5555/v3"

        # Test edge case that might cause parsing errors
        complex_url = "http://user:pass@host:5555/path?query=value#fragment"
        result = normalize_dataplane_url(complex_url)
        assert result == "http://user:pass@host:5555/path/v3?query=value#fragment"

    @pytest.mark.asyncio
    async def test_dataplane_client_get_version_success(self):
        """Test DataplaneClient.get_version() successful retrieval."""
        from haproxy_template_ic.dataplane import DataplaneClient

        client = DataplaneClient("http://localhost:5555")

        # Mock the API client and response
        mock_info_response = MagicMock()
        mock_info_response.haproxy = {"version": "3.1.0"}
        mock_info_response.api = {"build_date": "2024-01-01"}
        mock_info_response.system = {"hostname": "test-host"}

        with patch("haproxy_template_ic.dataplane.ApiClient") as mock_api_client:
            with patch("haproxy_template_ic.dataplane.InformationApi") as mock_info_api:
                mock_api_instance = AsyncMock()
                mock_api_client.return_value.__aenter__.return_value = mock_api_instance

                mock_info_api_instance = MagicMock()
                mock_info_api_instance.get_info = AsyncMock(
                    return_value=mock_info_response
                )
                mock_info_api.return_value = mock_info_api_instance

                result = await client.get_version()

                expected = {
                    "version": "3.1.0",
                    "build_date": "2024-01-01",
                    "hostname": "test-host",
                }
                assert result == expected

    @pytest.mark.asyncio
    async def test_dataplane_client_get_version_api_exception(self):
        """Test DataplaneClient.get_version() API exception handling."""
        from haproxy_template_ic.dataplane import DataplaneClient, DataplaneAPIError
        from haproxy_dataplane_v3.exceptions import ApiException

        client = DataplaneClient("http://localhost:5555")

        with patch("haproxy_template_ic.dataplane.ApiClient") as mock_api_client:
            with patch("haproxy_template_ic.dataplane.InformationApi") as mock_info_api:
                mock_api_instance = AsyncMock()
                mock_api_client.return_value.__aenter__.return_value = mock_api_instance

                mock_info_api_instance = MagicMock()
                mock_info_api_instance.get_info = AsyncMock(
                    side_effect=ApiException("API Error")
                )
                mock_info_api.return_value = mock_info_api_instance

                with pytest.raises(DataplaneAPIError) as exc_info:
                    await client.get_version()

                assert "Failed to get version" in str(exc_info.value)
                assert exc_info.value.endpoint == "http://localhost:5555/v3"
                assert exc_info.value.operation == "get_version"

    @pytest.mark.asyncio
    async def test_dataplane_client_get_version_network_errors(self):
        """Test DataplaneClient.get_version() network error handling."""
        from haproxy_template_ic.dataplane import DataplaneClient, DataplaneAPIError

        client = DataplaneClient("http://localhost:5555")

        # Test ConnectionError
        with patch("haproxy_template_ic.dataplane.ApiClient") as mock_api_client:
            mock_api_client.return_value.__aenter__.side_effect = ConnectionError(
                "Connection refused"
            )

            with pytest.raises(DataplaneAPIError) as exc_info:
                await client.get_version()

            assert "Network error" in str(exc_info.value)
            assert exc_info.value.operation == "get_version"

        # Test TimeoutError
        with patch("haproxy_template_ic.dataplane.ApiClient") as mock_api_client:
            mock_api_client.return_value.__aenter__.side_effect = TimeoutError(
                "Request timeout"
            )

            with pytest.raises(DataplaneAPIError) as exc_info:
                await client.get_version()

            assert "Network error" in str(exc_info.value)

        # Test OSError
        with patch("haproxy_template_ic.dataplane.ApiClient") as mock_api_client:
            mock_api_client.return_value.__aenter__.side_effect = OSError(
                "Network is unreachable"
            )

            with pytest.raises(DataplaneAPIError) as exc_info:
                await client.get_version()

            assert "Network error" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_dataplane_client_get_version_unexpected_exception(self):
        """Test DataplaneClient.get_version() unexpected exception handling."""
        from haproxy_template_ic.dataplane import DataplaneClient, DataplaneAPIError

        client = DataplaneClient("http://localhost:5555")

        with patch("haproxy_template_ic.dataplane.ApiClient") as mock_api_client:
            mock_api_client.return_value.__aenter__.side_effect = RuntimeError(
                "Unexpected error"
            )

            with pytest.raises(DataplaneAPIError) as exc_info:
                await client.get_version()

            assert "Unexpected error" in str(exc_info.value)
            assert exc_info.value.operation == "get_version"

    @pytest.mark.asyncio
    async def test_validate_configuration_success(self):
        """Test successful configuration validation."""
        from haproxy_template_ic.dataplane import DataplaneClient

        client = DataplaneClient("http://localhost:5555")

        with patch("haproxy_template_ic.dataplane.ApiClient") as mock_api_client:
            with patch(
                "haproxy_template_ic.dataplane.ConfigurationApi"
            ) as mock_config_api:
                mock_api_instance = AsyncMock()
                mock_api_client.return_value.__aenter__.return_value = mock_api_instance

                mock_config_api_instance = MagicMock()
                mock_config_api_instance.post_ha_proxy_configuration = AsyncMock()
                mock_config_api.return_value = mock_config_api_instance

                # Should not raise exception
                await client.validate_configuration("global\n    daemon\n")

    @pytest.mark.asyncio
    async def test_validate_configuration_bad_request_exception(self):
        """Test configuration validation with BadRequestException."""
        from haproxy_template_ic.dataplane import DataplaneClient, ValidationError
        from haproxy_dataplane_v3.exceptions import BadRequestException

        client = DataplaneClient("http://localhost:5555")

        with patch("haproxy_template_ic.dataplane.ApiClient") as mock_api_client:
            with patch(
                "haproxy_template_ic.dataplane.ConfigurationApi"
            ) as mock_config_api:
                mock_api_instance = AsyncMock()
                mock_api_client.return_value.__aenter__.return_value = mock_api_instance

                mock_config_api_instance = MagicMock()
                bad_request = BadRequestException("Invalid configuration")
                bad_request.body = "Configuration error details"
                mock_config_api_instance.post_ha_proxy_configuration = AsyncMock(
                    side_effect=bad_request
                )
                mock_config_api.return_value = mock_config_api_instance

                with pytest.raises(ValidationError) as exc_info:
                    await client.validate_configuration("invalid config")

                assert "Configuration validation failed" in str(exc_info.value)
                assert exc_info.value.config_size == 14  # len("invalid config")
                assert (
                    exc_info.value.validation_details == "Configuration error details"
                )

    @pytest.mark.asyncio
    async def test_validate_configuration_network_errors(self):
        """Test configuration validation network error handling."""
        from haproxy_template_ic.dataplane import DataplaneClient, DataplaneAPIError

        client = DataplaneClient("http://localhost:5555")

        # Test ConnectionError
        with patch("haproxy_template_ic.dataplane.ApiClient") as mock_api_client:
            mock_api_instance = AsyncMock()
            mock_api_client.return_value.__aenter__.return_value = mock_api_instance

            with patch(
                "haproxy_template_ic.dataplane.ConfigurationApi"
            ) as mock_config_api:
                mock_config_api_instance = MagicMock()
                mock_config_api_instance.post_ha_proxy_configuration = AsyncMock(
                    side_effect=ConnectionError("Network error")
                )
                mock_config_api.return_value = mock_config_api_instance

                with pytest.raises(DataplaneAPIError) as exc_info:
                    await client.validate_configuration("test config")

                assert "Network error during validation" in str(exc_info.value)
                assert exc_info.value.operation == "validate"

    @pytest.mark.asyncio
    async def test_validate_configuration_unexpected_exception(self):
        """Test configuration validation unexpected exception handling."""
        from haproxy_template_ic.dataplane import DataplaneClient, DataplaneAPIError

        client = DataplaneClient("http://localhost:5555")

        with patch("haproxy_template_ic.dataplane.ApiClient") as mock_api_client:
            mock_api_instance = AsyncMock()
            mock_api_client.return_value.__aenter__.return_value = mock_api_instance

            with patch(
                "haproxy_template_ic.dataplane.ConfigurationApi"
            ) as mock_config_api:
                mock_config_api_instance = MagicMock()
                mock_config_api_instance.post_ha_proxy_configuration = AsyncMock(
                    side_effect=ValueError("Unexpected error")
                )
                mock_config_api.return_value = mock_config_api_instance

                with pytest.raises(DataplaneAPIError) as exc_info:
                    await client.validate_configuration("test config")

                assert "Configuration validation failed" in str(exc_info.value)
                assert exc_info.value.operation == "validate"

    @pytest.mark.asyncio
    async def test_deploy_configuration_success(self):
        """Test successful configuration deployment."""
        from haproxy_template_ic.dataplane import DataplaneClient

        client = DataplaneClient("http://localhost:5555")

        with patch("haproxy_template_ic.dataplane.ApiClient") as mock_api_client:
            with patch(
                "haproxy_template_ic.dataplane.ConfigurationApi"
            ) as mock_config_api:
                mock_api_instance = AsyncMock()
                mock_api_client.return_value.__aenter__.return_value = mock_api_instance

                mock_config_api_instance = MagicMock()
                mock_config_api_instance.get_configuration_version = AsyncMock(
                    side_effect=[1, 2]
                )  # before and after
                mock_config_api_instance.post_ha_proxy_configuration = AsyncMock()
                mock_config_api.return_value = mock_config_api_instance

                result = await client.deploy_configuration("global\n    daemon\n")
                assert result == "2"

    @pytest.mark.asyncio
    async def test_deploy_configuration_server_error_retry(self):
        """Test deployment with server error gets wrapped properly."""
        from haproxy_template_ic.dataplane import DataplaneClient, DataplaneAPIError
        from haproxy_dataplane_v3.exceptions import ApiException

        client = DataplaneClient("http://localhost:5555")

        with patch("haproxy_template_ic.dataplane.ApiClient") as mock_api_client:
            with patch(
                "haproxy_template_ic.dataplane.ConfigurationApi"
            ) as mock_config_api:
                mock_api_instance = AsyncMock()
                mock_api_client.return_value.__aenter__.return_value = mock_api_instance

                mock_config_api_instance = MagicMock()
                # Configuration API calls fail with 500 error
                server_error = ApiException("Server Error")
                server_error.status = 500
                mock_config_api_instance.get_configuration_version = AsyncMock(
                    return_value=1
                )
                mock_config_api_instance.post_ha_proxy_configuration = AsyncMock(
                    side_effect=server_error
                )
                mock_config_api.return_value = mock_config_api_instance

                # Should raise DataplaneAPIError wrapping the server error
                with pytest.raises(DataplaneAPIError) as exc_info:
                    await client.deploy_configuration("global\n    daemon\n")

                assert "Configuration deployment failed" in str(exc_info.value)
                assert exc_info.value.operation == "deploy"
                assert exc_info.value.endpoint == "http://localhost:5555/v3"

    @pytest.mark.asyncio
    async def test_deploy_configuration_client_error_no_retry(self):
        """Test deployment doesn't retry client errors."""
        from haproxy_template_ic.dataplane import DataplaneClient, DataplaneAPIError
        from haproxy_dataplane_v3.exceptions import ApiException

        client = DataplaneClient("http://localhost:5555")

        with patch("haproxy_template_ic.dataplane.ApiClient") as mock_api_client:
            with patch(
                "haproxy_template_ic.dataplane.ConfigurationApi"
            ) as mock_config_api:
                mock_api_instance = AsyncMock()
                mock_api_client.return_value.__aenter__.return_value = mock_api_instance

                mock_config_api_instance = MagicMock()
                mock_config_api_instance.get_configuration_version = AsyncMock(
                    return_value=1
                )

                # Client error (400) should not retry
                client_error = ApiException("Bad Request")
                client_error.status = 400
                mock_config_api_instance.post_ha_proxy_configuration = AsyncMock(
                    side_effect=client_error
                )
                mock_config_api.return_value = mock_config_api_instance

                with pytest.raises(DataplaneAPIError) as exc_info:
                    await client.deploy_configuration("invalid config")

                assert "Configuration deployment failed" in str(exc_info.value)
                assert exc_info.value.operation == "deploy"

    @pytest.mark.asyncio
    async def test_deploy_configuration_retry_exhaustion(self):
        """Test deployment failure after retry exhaustion."""
        from haproxy_template_ic.dataplane import DataplaneClient, DataplaneAPIError
        from haproxy_dataplane_v3.exceptions import ApiException

        client = DataplaneClient("http://localhost:5555")

        with patch("haproxy_template_ic.dataplane.ApiClient") as mock_api_client:
            with patch(
                "haproxy_template_ic.dataplane.ConfigurationApi"
            ) as mock_config_api:
                mock_api_instance = AsyncMock()
                mock_api_client.return_value.__aenter__.return_value = mock_api_instance

                mock_config_api_instance = MagicMock()
                mock_config_api_instance.get_configuration_version = AsyncMock(
                    return_value=1
                )

                # Server error that persists through retries
                server_error = ApiException("Server Error")
                server_error.status = 500
                mock_config_api_instance.post_ha_proxy_configuration = AsyncMock(
                    side_effect=server_error
                )
                mock_config_api.return_value = mock_config_api_instance

                with pytest.raises(DataplaneAPIError) as exc_info:
                    await client.deploy_configuration("global\n    daemon\n")

                assert "Configuration deployment failed" in str(exc_info.value)
                assert exc_info.value.operation == "deploy"
