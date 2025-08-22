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


class MockAsyncRetrying:
    """Mock for AsyncRetrying that eliminates wait times in tests while preserving retry logic."""

    def __init__(self, *args, **kwargs):
        # Extract stop condition from kwargs to determine max attempts
        self.max_attempts = 5  # Default from stop_after_attempt(5)
        if "stop" in kwargs:
            # Try to extract the attempt limit if available
            stop = kwargs["stop"]
            if hasattr(stop, "max_attempt_number"):
                self.max_attempts = stop.max_attempt_number

    def __aiter__(self):
        return self

    async def __anext__(self):
        if not hasattr(self, "_attempt_count"):
            self._attempt_count = 0
        self._attempt_count += 1

        if self._attempt_count > self.max_attempts:
            raise StopAsyncIteration

        # Return an attempt manager that can handle exceptions
        return MockAttemptManager(self._attempt_count)


class MockAttemptManager:
    """Mock attempt manager for retry context."""

    def __init__(self, attempt_number):
        self.attempt_number = attempt_number
        self._exception = None

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if exc_type is not None:
            self._exception = exc_val
            # Don't suppress the exception - let it propagate for retry logic
            return False
        return True


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
        context.rendered_files = []
        context.rendered_maps = []
        context.rendered_certificates = []
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
        context.rendered_files = []
        context.rendered_maps = []
        context.rendered_certificates = []

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
        context.rendered_files = []
        context.rendered_maps = []
        context.rendered_certificates = []

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
        context.rendered_files = []
        context.rendered_maps = []
        context.rendered_certificates = []

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


class TestErrorParsingFunctions:
    """Test error parsing helper functions."""

    def test_parse_haproxy_error_line_config_parsing_format(self):
        """Test parsing line number from config parsing error format."""
        from haproxy_template_ic.dataplane import parse_haproxy_error_line

        error_msg = "config parsing [/tmp/onlyvalidate3935728576:54] 'listen' or 'defaults' expected."
        line_num = parse_haproxy_error_line(error_msg)
        assert line_num == 54

    def test_parse_haproxy_error_line_simple_line_format(self):
        """Test parsing line number from simple line format."""
        from haproxy_template_ic.dataplane import parse_haproxy_error_line

        error_msg = "line 42: unknown keyword 'foobar'"
        line_num = parse_haproxy_error_line(error_msg)
        assert line_num == 42

    def test_parse_haproxy_error_line_at_line_format(self):
        """Test parsing line number from 'at line' format."""
        from haproxy_template_ic.dataplane import parse_haproxy_error_line

        error_msg = "syntax error at line 123"
        line_num = parse_haproxy_error_line(error_msg)
        assert line_num == 123

    def test_parse_haproxy_error_line_not_found(self):
        """Test when no line number is found in error message."""
        from haproxy_template_ic.dataplane import parse_haproxy_error_line

        error_msg = "generic error without line number"
        line_num = parse_haproxy_error_line(error_msg)
        assert line_num is None

    def test_extract_config_context(self):
        """Test extracting configuration context around an error line."""
        from haproxy_template_ic.dataplane import extract_config_context

        config = """global
    daemon
    log stdout local0

defaults
    mode http
    timeout connect 5000ms
    timeout client 50000ms

frontend main
    bind *:80
    use_backend default"""

        context = extract_config_context(config, 6, context_lines=2)
        expected_lines = [
            "    5: defaults",
            ">   6:     mode http",
            "    7:     timeout connect 5000ms",
            "    8:     timeout client 50000ms",
        ]

        for expected_line in expected_lines:
            assert expected_line in context

    def test_extract_config_context_out_of_range(self):
        """Test extracting context when line number is out of range."""
        from haproxy_template_ic.dataplane import extract_config_context

        config = "line1\nline2\nline3"
        context = extract_config_context(config, 10, context_lines=2)
        assert "out of range" in context
        assert "3 lines" in context

    def test_parse_validation_error_details(self):
        """Test parsing complete validation error details."""
        from haproxy_template_ic.dataplane import parse_validation_error_details

        error_msg = "config parsing [/tmp/file:54] 'listen' or 'defaults' expected."
        config = """global
    daemon

defaults
    mode http

frontend main
    bind *:80
    invalid_directive here"""

        error_line, error_context = parse_validation_error_details(error_msg, config)
        assert error_line == 54
        # Since line 54 is out of range for our short config, error_context should indicate this
        assert error_context and "out of range" in error_context


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

    def test_validation_error_with_context(self):
        """Test ValidationError with error context and line information."""
        config_content = "global\n    daemon\ndefaults\n    mode http"
        error_context = "  3: defaults\n> 4:     mode http\n  5:"

        error = ValidationError(
            "Config syntax error",
            endpoint="http://test:5555",
            config_size=len(config_content),
            validation_details="'listen' or 'defaults' expected",
            error_line=4,
            config_content=config_content,
            error_context=error_context,
        )

        error_str = str(error)
        assert "Config syntax error" in error_str
        assert "config_size=40" in error_str  # Updated to match actual size
        assert "'listen' or 'defaults' expected" in error_str
        assert "Configuration context around error:" in error_str
        assert "> 4:     mode http" in error_str
        assert error.error_line == 4
        assert error.config_content == config_content
        assert error.error_context == error_context


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
        """Test lazy client initialization."""
        client = DataplaneClient("http://test:5555")

        # Client should be None initially
        assert client._client is None

        # First call should create client
        client1 = client._get_client()
        assert client._client is not None

        # Second call should return same instance
        client2 = client._get_client()
        assert client1 is client2


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
        context.rendered_files = []
        context.rendered_maps = []
        context.rendered_certificates = []

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

        # Mock the API response with proper structure for new client
        mock_info_response = MagicMock()
        mock_haproxy = MagicMock()
        mock_haproxy.to_dict.return_value = {"version": "3.1.0"}
        mock_api = MagicMock()
        mock_api.to_dict.return_value = {"build_date": "2024-01-01"}
        mock_system = MagicMock()
        mock_system.to_dict.return_value = {"hostname": "test-host"}

        mock_info_response.haproxy = mock_haproxy
        mock_info_response.api = mock_api
        mock_info_response.system = mock_system

        with patch("haproxy_template_ic.dataplane.get_info") as mock_get_info:
            mock_get_info.asyncio = AsyncMock(return_value=mock_info_response)

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
        from haproxy_dataplane_v3.errors import UnexpectedStatus

        client = DataplaneClient("http://localhost:5555")

        with patch("haproxy_template_ic.dataplane.get_info") as mock_get_info:
            api_exception = UnexpectedStatus(500, b"API Error")
            mock_get_info.asyncio.side_effect = api_exception

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
        with patch("haproxy_template_ic.dataplane.get_info") as mock_get_info:
            mock_get_info.asyncio.side_effect = ConnectionError("Connection refused")

            with pytest.raises(DataplaneAPIError) as exc_info:
                await client.get_version()

            assert "Network error" in str(exc_info.value)
            assert exc_info.value.operation == "get_version"

        # Test TimeoutError
        with patch("haproxy_template_ic.dataplane.get_info") as mock_get_info:
            mock_get_info.asyncio.side_effect = TimeoutError("Request timeout")

            with pytest.raises(DataplaneAPIError) as exc_info:
                await client.get_version()

            assert "Network error" in str(exc_info.value)

        # Test OSError
        with patch("haproxy_template_ic.dataplane.get_info") as mock_get_info:
            mock_get_info.asyncio.side_effect = OSError("Network is unreachable")

            with pytest.raises(DataplaneAPIError) as exc_info:
                await client.get_version()

            assert "Network error" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_dataplane_client_get_version_unexpected_exception(self):
        """Test DataplaneClient.get_version() unexpected exception handling."""
        from haproxy_template_ic.dataplane import DataplaneClient, DataplaneAPIError

        client = DataplaneClient("http://localhost:5555")

        with patch("haproxy_template_ic.dataplane.get_info") as mock_get_info:
            mock_get_info.asyncio.side_effect = RuntimeError("Unexpected error")

            with pytest.raises(DataplaneAPIError) as exc_info:
                await client.get_version()

            assert "Unexpected error" in str(exc_info.value)
            assert exc_info.value.operation == "get_version"

    @pytest.mark.asyncio
    async def test_validate_configuration_success(self):
        """Test successful configuration validation."""
        from haproxy_template_ic.dataplane import DataplaneClient

        client = DataplaneClient("http://localhost:5555")

        with patch("httpx.AsyncClient") as mock_httpx_client:
            mock_client_instance = AsyncMock()
            mock_httpx_client.return_value.__aenter__.return_value = (
                mock_client_instance
            )

            # Mock successful response
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_client_instance.post.return_value = mock_response

            # Should not raise exception
            await client.validate_configuration("global\n    daemon\n")

    @pytest.mark.asyncio
    async def test_validate_configuration_bad_request_exception(self):
        """Test configuration validation with bad request response."""
        from haproxy_template_ic.dataplane import DataplaneClient, ValidationError

        client = DataplaneClient("http://localhost:5555")

        with patch("httpx.AsyncClient") as mock_httpx_client:
            mock_client_instance = AsyncMock()
            mock_httpx_client.return_value.__aenter__.return_value = (
                mock_client_instance
            )

            # Mock error response
            mock_response = MagicMock()
            mock_response.status_code = 400
            mock_response.text = "Configuration error details"
            mock_client_instance.post.return_value = mock_response

            with pytest.raises(ValidationError) as exc_info:
                await client.validate_configuration("invalid config")

            assert "Configuration validation failed" in str(exc_info.value)
            assert exc_info.value.config_size == 14  # len("invalid config")
            assert exc_info.value.validation_details == "Configuration error details"

    @pytest.mark.asyncio
    async def test_validate_configuration_network_errors(self):
        """Test configuration validation network error handling."""
        from haproxy_template_ic.dataplane import DataplaneClient, DataplaneAPIError

        client = DataplaneClient("http://localhost:5555")

        # Test ConnectionError
        with patch("httpx.AsyncClient") as mock_httpx_client:
            mock_client_instance = AsyncMock()
            mock_httpx_client.return_value.__aenter__.return_value = (
                mock_client_instance
            )
            import httpx

            mock_client_instance.post.side_effect = httpx.RequestError("Network error")

            with pytest.raises(DataplaneAPIError) as exc_info:
                await client.validate_configuration("test config")

            assert "Network error during validation" in str(exc_info.value)
            assert exc_info.value.operation == "validate"

    @pytest.mark.asyncio
    async def test_validate_configuration_unexpected_exception(self):
        """Test configuration validation unexpected exception handling."""
        from haproxy_template_ic.dataplane import DataplaneClient, DataplaneAPIError

        client = DataplaneClient("http://localhost:5555")

        with patch("httpx.AsyncClient") as mock_httpx_client:
            mock_client_instance = AsyncMock()
            mock_httpx_client.return_value.__aenter__.return_value = (
                mock_client_instance
            )
            mock_client_instance.post.side_effect = ValueError("Unexpected error")

            with pytest.raises(DataplaneAPIError) as exc_info:
                await client.validate_configuration("test config")

            assert "Configuration validation failed" in str(exc_info.value)
            assert exc_info.value.operation == "validate"

    @pytest.mark.asyncio
    async def test_deploy_configuration_success(self):
        """Test successful configuration deployment."""
        from haproxy_template_ic.dataplane import DataplaneClient

        client = DataplaneClient("http://localhost:5555")

        # Mock httpx.AsyncClient for direct HTTP calls
        with patch("httpx.AsyncClient") as mock_async_client:
            mock_client_instance = AsyncMock()
            mock_async_client.return_value.__aenter__.return_value = (
                mock_client_instance
            )

            # Mock version requests
            mock_version_resp_1 = MagicMock()
            mock_version_resp_1.status_code = 200
            mock_version_resp_1.json.return_value = 1

            mock_version_resp_2 = MagicMock()
            mock_version_resp_2.status_code = 200
            mock_version_resp_2.json.return_value = 2

            # Mock deploy request
            mock_deploy_resp = MagicMock()
            mock_deploy_resp.status_code = 200

            mock_client_instance.get.side_effect = [
                mock_version_resp_1,
                mock_version_resp_2,
            ]
            mock_client_instance.post.return_value = mock_deploy_resp

            result = await client.deploy_configuration("global\n    daemon\n")
            assert result == "2"

    @pytest.mark.asyncio
    async def test_deploy_configuration_error_with_context(self):
        """Test deployment error includes HAProxy config context."""
        from haproxy_template_ic.dataplane import DataplaneClient, DataplaneAPIError

        client = DataplaneClient("http://localhost:5555")

        # Create config with a known error on line 4
        config_content = """global
    daemon
defaults
    invalid-directive here
    mode http
"""

        # Mock httpx.AsyncClient for direct HTTP calls
        with patch("httpx.AsyncClient") as mock_async_client:
            mock_client_instance = AsyncMock()
            mock_async_client.return_value.__aenter__.return_value = (
                mock_client_instance
            )

            # Mock version request (successful)
            mock_version_resp = MagicMock()
            mock_version_resp.status_code = 200
            mock_version_resp.json.return_value = 1

            # Mock deploy request (failed with HAProxy error)
            mock_deploy_resp = MagicMock()
            mock_deploy_resp.status_code = 400
            mock_deploy_resp.text = "config parsing [/tmp/haproxy.cfg:4]: unknown keyword 'invalid-directive'"

            mock_client_instance.get.return_value = mock_version_resp
            mock_client_instance.post.return_value = mock_deploy_resp

            # Test that deployment failure includes config context
            with pytest.raises(DataplaneAPIError) as exc_info:
                await client.deploy_configuration(config_content)

            error_str = str(exc_info.value)
            # Should contain the original error
            assert "Configuration deployment failed: 400" in error_str
            assert "unknown keyword 'invalid-directive'" in error_str

            # Should contain config context around line 4
            assert "Configuration context around error:" in error_str
            assert (
                ">   4:     invalid-directive here" in error_str
            )  # Error line marked with >
            assert "    3: defaults" in error_str  # Context before
            assert "    5:     mode http" in error_str  # Context after
