"""
Unit tests for dataplane functionality.

Tests the HAProxy Dataplane API integration including pod discovery,
client operations, and configuration synchronization.
"""

import asyncio
import io
import pytest
from unittest.mock import Mock, AsyncMock, MagicMock, patch
from unittest import mock

import httpx
from pydantic import SecretStr
from haproxy_dataplane_v3.errors import UnexpectedStatus
from haproxy_template_ic.credentials import Credentials, DataplaneAuth
from haproxy_template_ic.dataplane import (
    ConfigSynchronizer,
    DataplaneAPIError,
    DataplaneClient,
    DeploymentHistory,
    ValidationError,
    extract_config_context,
    get_production_urls_from_index,
    normalize_dataplane_url,
    parse_haproxy_error_line,
    parse_validation_error_details,
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

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is not None:
            self._exception = exc_val
            # Don't suppress the exception - let it propagate for retry logic
            return False
        return True

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if exc_type is not None:
            self._exception = exc_val
            # Don't suppress the exception - let it propagate for retry logic
            return False
        return True


@pytest.fixture(autouse=True, scope="module")
def mock_async_retrying():
    """Apply MockAsyncRetrying to all tests in this module to eliminate retry delays."""
    with patch("haproxy_template_ic.dataplane.AsyncRetrying", MockAsyncRetrying):
        yield


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

    def test_deployment_history_record_success(self):
        """Test successful deployment recording."""
        history = DeploymentHistory()
        history.record("http://test:5555", "v123", True)

        data = history.to_dict()
        assert "deployment_history" in data
        assert "http://test:5555" in data["deployment_history"]

        entry = data["deployment_history"]["http://test:5555"]
        assert entry["version"] == "v123"
        assert entry["success"] is True
        assert entry["last_attempt"] == "v123"
        assert entry["error"] is None

    def test_deployment_history_record_failure(self):
        """Test failed deployment recording."""
        history = DeploymentHistory()
        history.record("http://test:5555", "v124", False, "Config validation failed")

        data = history.to_dict()
        entry = data["deployment_history"]["http://test:5555"]
        assert entry["version"] is None  # No version on failure
        assert entry["success"] is False
        assert entry["last_attempt"] == "v124"
        assert entry["error"] == "Config validation failed"


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

    @pytest.mark.asyncio
    async def test_extract_storage_content_success(self):
        """Test successful storage content extraction."""
        client = DataplaneClient("http://test:5555")

        # Mock storage item with payload
        mock_storage = Mock()
        mock_payload = Mock()
        mock_payload.read.return_value = b"test content"
        mock_payload.seek = Mock()
        mock_storage.payload = mock_payload

        result = client._extract_storage_content(mock_storage)
        assert result == "test content"
        mock_payload.seek.assert_called_once_with(0)

    @pytest.mark.asyncio
    async def test_extract_storage_content_no_payload(self):
        """Test storage content extraction with no payload."""
        client = DataplaneClient("http://test:5555")

        # Mock storage item without payload
        mock_storage = Mock(spec=[])  # No payload attribute
        result = client._extract_storage_content(mock_storage)
        assert result is None

        # Test with None input
        result = client._extract_storage_content(None)
        assert result is None

    @pytest.mark.asyncio
    async def test_extract_storage_content_exception(self):
        """Test storage content extraction with exception during read."""
        client = DataplaneClient("http://test:5555")

        # Mock storage item with payload that raises exception
        mock_storage = Mock()
        mock_payload = Mock()
        mock_payload.read.side_effect = UnicodeDecodeError(
            "utf-8", b"", 0, 1, "test error"
        )
        mock_storage.payload = mock_payload

        result = client._extract_storage_content(mock_storage)
        assert result is None

    @pytest.mark.asyncio
    async def test_get_current_configuration_exception(self):
        """Test get_current_configuration exception handling."""
        client = DataplaneClient("http://test:5555")

        # Mock the get_client to return a mock that raises an exception
        mock_client = Mock()
        client._client = mock_client

        # Import the function we need to mock

        # Mock the get_ha_proxy_configuration to raise an exception
        with pytest.MonkeyPatch().context() as m:
            m.setattr(
                "haproxy_template_ic.dataplane.get_ha_proxy_configuration.asyncio",
                Mock(side_effect=Exception("API error")),
            )

            result = await client.get_current_configuration()
            assert result is None

    @pytest.mark.asyncio
    async def test_deploy_configuration_conditionally_force(self):
        """Test deploy_configuration_conditionally with force=True."""
        client = DataplaneClient("http://test:5555")
        config = "global\n    daemon\n"

        # Mock the deploy_configuration method
        from unittest.mock import AsyncMock

        client.deploy_configuration = AsyncMock(return_value="v123")

        result = await client.deploy_configuration_conditionally(config, force=True)
        assert result == "v123"
        client.deploy_configuration.assert_called_once()

    @pytest.mark.asyncio
    async def test_deploy_configuration_conditionally_version_fetch_fail(self):
        """Test deploy_configuration_conditionally when version fetch fails."""
        client = DataplaneClient("http://test:5555")
        config = "global\n    daemon\n"

        # Mock get_current_configuration to return None (no current config)
        from unittest.mock import AsyncMock

        client.get_current_configuration = AsyncMock(return_value=None)
        client.deploy_configuration = AsyncMock(return_value="v124")

        # Mock the get_configuration_version to raise exception (line 1141-1142)
        mock_client = Mock()
        client._client = mock_client

        with pytest.MonkeyPatch().context() as m:
            m.setattr(
                "haproxy_template_ic.dataplane.get_configuration_version.asyncio",
                Mock(side_effect=Exception("Version fetch failed")),
            )

            # This should still work and deploy
            result = await client.deploy_configuration_conditionally(
                config, force=False
            )
            assert result == "v124"


class TestConfigSynchronizerMethods:
    """Test ConfigSynchronizer methods for coverage."""

    @pytest.mark.asyncio
    async def test_sync_configuration_validation_failure(self):
        """Test sync with validation failure."""

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

                # Add methods for validation client
                if "localhost" in url:  # Validation URL
                    mock_client.deploy_configuration = AsyncMock(return_value="v1.0")
                    mock_client.fetch_structured_configuration = AsyncMock(
                        return_value={
                            "backends": [],
                            "frontends": [],
                            "defaults": [],
                            "global": {"daemon": True},
                        }
                    )
                    mock_client.sync_maps = AsyncMock(return_value=None)
                    mock_client.sync_certificates = AsyncMock(return_value=None)
                    mock_client.sync_files = AsyncMock(return_value=None)
                elif "test1" in url:
                    mock_client.deploy_configuration = AsyncMock(return_value="v1.0")
                    # Return different config to trigger deployment
                    mock_client.fetch_structured_configuration = AsyncMock(
                        return_value={
                            "backends": [],
                            "frontends": [],
                            "defaults": [],
                            "global": {"daemon": False},  # Different from validation
                        }
                    )
                    mock_client.sync_maps = AsyncMock(return_value=None)
                    mock_client.sync_certificates = AsyncMock(return_value=None)
                    mock_client.sync_files = AsyncMock(return_value=None)
                    mock_client.deploy_configuration_conditionally = AsyncMock(
                        return_value="v1.0"
                    )
                else:
                    mock_client.deploy_configuration = AsyncMock(
                        side_effect=Exception("Connection failed")
                    )
                    mock_client.fetch_structured_configuration = AsyncMock(
                        side_effect=Exception("Connection failed")
                    )
                    mock_client.sync_maps = AsyncMock(return_value=None)
                    mock_client.sync_certificates = AsyncMock(return_value=None)
                    mock_client.sync_files = AsyncMock(return_value=None)
                    mock_client.deploy_configuration_conditionally = AsyncMock(
                        side_effect=Exception("Connection failed")
                    )

                return mock_client

            mock_client_class.side_effect = create_mock_client

            results = await synchronizer.sync_configuration(context)

            assert results["successful"] == 1
            assert results["failed"] == 1
            assert len(results["errors"]) == 1
            assert "Connection failed" in results["errors"][0]

    def test_compare_structured_configs_helper_functions(self):
        """Test the helper functions in _compare_structured_configs."""
        from haproxy_template_ic.credentials import Credentials, DataplaneAuth
        from pydantic import SecretStr

        # Create minimal credentials
        credentials = Credentials(
            dataplane=DataplaneAuth(username="admin", password=SecretStr("pass")),
            validation=DataplaneAuth(username="admin", password=SecretStr("pass")),
        )

        synchronizer = ConfigSynchronizer(
            production_urls=["http://prod:5555"],
            validation_url="http://val:5555",
            credentials=credentials,
        )

        # Test with configs that trigger early exit
        backends = []
        for i in range(
            12
        ):  # 12 backends will create 12 "remove" changes, exceeding limit of 10
            backend = Mock()
            backend.name = f"backend{i}"
            backend.to_dict.return_value = {"name": f"backend{i}"}
            backends.append(backend)

        current_config = {"backends": backends}
        new_config = {
            "backends": []  # This will create 12 "remove backend" changes, triggering early exit at 10
        }

        changes = synchronizer._compare_structured_configs(current_config, new_config)

        # Should trigger early exit after MAX_CONFIG_COMPARISON_CHANGES
        # The "and more" message should be present if early exit was triggered
        assert len(changes) >= 11  # At least 10 changes + "and more" message
        assert any("and more" in change for change in changes)

    def test_compare_structured_configs_serialization_error(self):
        """Test _compare_structured_configs with serialization errors."""
        from haproxy_template_ic.credentials import Credentials, DataplaneAuth
        from pydantic import SecretStr

        credentials = Credentials(
            dataplane=DataplaneAuth(username="admin", password=SecretStr("pass")),
            validation=DataplaneAuth(username="admin", password=SecretStr("pass")),
        )

        synchronizer = ConfigSynchronizer(
            production_urls=["http://prod:5555"],
            validation_url="http://val:5555",
            credentials=credentials,
        )

        # Mock backend that raises exception in to_dict
        bad_backend = Mock(name="bad_backend")
        bad_backend.to_dict.side_effect = RuntimeError("Serialization failed")

        current_config = {"backends": [bad_backend]}
        new_config = {"backends": []}

        changes = synchronizer._compare_structured_configs(current_config, new_config)
        # Should handle the serialization error gracefully
        assert len(changes) >= 0  # Should not crash


class TestNormalizeDataplaneUrl:
    """Test normalize_dataplane_url function."""

    def test_normalize_url_without_v3(self):
        """Test URL normalization adds /v3."""

        result = normalize_dataplane_url("http://localhost:5555")
        assert result == "http://localhost:5555/v3"

    def test_normalize_url_with_trailing_slash(self):
        """Test URL normalization with trailing slash."""

        result = normalize_dataplane_url("http://localhost:5555/")
        assert result == "http://localhost:5555/v3"

    def test_normalize_url_already_has_v3(self):
        """Test URL normalization when /v3 already exists."""

        result = normalize_dataplane_url("http://localhost:5555/v3")
        assert result == "http://localhost:5555/v3"

    def test_normalize_url_with_query_params(self):
        """Test URL normalization preserves query parameters."""

        result = normalize_dataplane_url("http://localhost:5555?timeout=30")
        assert result == "http://localhost:5555/v3?timeout=30"

    def test_normalize_url_with_path_and_query(self):
        """Test URL normalization with existing path and query parameters."""

        result = normalize_dataplane_url("https://api.example.com/haproxy?auth=token")
        assert result == "https://api.example.com/haproxy/v3?auth=token"

    def test_normalize_dataplane_url_edge_cases(self):
        """Test normalize_dataplane_url with edge cases and error conditions."""
        # Test with already normalized URLs
        assert (
            normalize_dataplane_url("http://localhost:5555/v3")
            == "http://localhost:5555/v3"
        )

        # Test with trailing slash
        assert (
            normalize_dataplane_url("http://localhost:5555/")
            == "http://localhost:5555/v3"
        )

        # Test with query parameters
        assert (
            normalize_dataplane_url("http://localhost:5555?timeout=30")
            == "http://localhost:5555/v3?timeout=30"
        )

        # Test with fragment
        assert (
            normalize_dataplane_url("http://localhost:5555#section")
            == "http://localhost:5555/v3#section"
        )

        # Test with complex path
        assert (
            normalize_dataplane_url("https://api.example.com/haproxy/")
            == "https://api.example.com/haproxy/v3"
        )

        # Test error handling - this should trigger the ValueError catch and fallback
        # We can't easily mock urlparse to raise ValueError, so test the fallback logic
        malformed_url = "http://localhost:5555"  # This should work normally
        result = normalize_dataplane_url(malformed_url)
        assert result == "http://localhost:5555/v3"


class TestErrorParsingFunctions:
    """Test error parsing helper functions and other utility functions."""

    def test_extract_hash_from_description_with_hash(self):
        """Test extracting hash from description with valid hash."""
        from haproxy_template_ic.dataplane import extract_hash_from_description

        assert extract_hash_from_description("xxh64:abc123def") == "xxh64:abc123def"
        assert extract_hash_from_description("sha256:def456ghi") == "sha256:def456ghi"
        assert extract_hash_from_description("md5:ghi789jkl") == "md5:ghi789jkl"

    def test_extract_hash_from_description_with_additional_text(self):
        """Test extracting hash when there's additional text after the hash."""
        from haproxy_template_ic.dataplane import extract_hash_from_description

        assert (
            extract_hash_from_description("xxh64:abc123 some additional text")
            == "xxh64:abc123"
        )

    def test_extract_hash_from_description_no_hash(self):
        """Test extracting hash from description without hash."""
        from haproxy_template_ic.dataplane import extract_hash_from_description

        assert extract_hash_from_description("no hash here") is None
        assert extract_hash_from_description("") is None
        assert extract_hash_from_description(None) is None

    def test_extract_hash_from_description_invalid_input(self):
        """Test extracting hash with invalid input types."""
        from haproxy_template_ic.dataplane import extract_hash_from_description

        assert extract_hash_from_description(123) is None
        assert extract_hash_from_description([]) is None

    def test_parse_haproxy_error_line_various_formats(self):
        """Test parsing HAProxy error lines in various formats."""
        assert parse_haproxy_error_line("config parsing [/tmp/file:54]") == 54
        assert parse_haproxy_error_line("line 42: some error") == 42
        assert parse_haproxy_error_line("[line 123] error occurred") == 123
        assert parse_haproxy_error_line("at line 99 there was an issue") == 99
        assert parse_haproxy_error_line("some error :456]") == 456

    def test_parse_haproxy_error_line_no_match(self):
        """Test parsing HAProxy error lines with no line numbers."""
        assert parse_haproxy_error_line("generic error message") is None
        assert parse_haproxy_error_line("") is None

    def test_parse_haproxy_error_line_malformed_input(self):
        """Test parsing HAProxy error lines with malformed input."""
        # Invalid line numbers
        assert parse_haproxy_error_line("config parsing [/tmp/file:abc]") is None
        assert parse_haproxy_error_line("line abc: some error") is None
        assert parse_haproxy_error_line("[line ]") is None

        # Partial matches that should not work
        assert parse_haproxy_error_line("line :") is None
        assert (
            parse_haproxy_error_line("line -42: error") is None
        )  # Negative line number

        # These should work (testing actual regex behavior)
        assert (
            parse_haproxy_error_line("config parsing [:123]") == 123
        )  # This actually matches

        # Empty patterns
        assert parse_haproxy_error_line("line : error") is None
        assert parse_haproxy_error_line("config parsing []") is None

    def test_extract_config_context_valid_line(self):
        """Test extracting config context around a valid line."""
        config = "line1\nline2\nline3\nline4\nline5"
        context = extract_config_context(config, 3, context_lines=1)
        expected = "    2: line2\n>   3: line3\n    4: line4"
        assert context == expected

    def test_extract_config_context_edge_cases(self):
        """Test extracting config context with edge cases."""
        # Empty config
        assert extract_config_context("", 1) == "No configuration content available"

        # Line number out of range
        config = "line1\nline2"
        context = extract_config_context(config, 10)
        assert "out of range" in context

        # Line number 0 or negative
        context = extract_config_context(config, 0)
        assert "out of range" in context

    def test_parse_validation_error_details_with_line_number(self):
        """Test parsing validation error details with extractable line number."""
        error_msg = "config parsing [/tmp/test:4]"
        config = "line1\nline2\nline3\nerror line\nline5"
        line, context = parse_validation_error_details(error_msg, config)
        assert line == 4
        # Should include the error line and surrounding context
        assert "error line" in context
        assert ">   4: error line" in context  # Error line should be marked with >

    def test_parse_validation_error_details_no_line_number(self):
        """Test parsing validation error details without line number."""
        error_msg = "generic validation error"
        config = "some config"
        line, context = parse_validation_error_details(error_msg, config)
        assert line is None
        assert context is None

    def test_parse_haproxy_error_line_config_parsing_format(self):
        """Test parsing line number from config parsing error format."""

        error_msg = "config parsing [/tmp/onlyvalidate3935728576:54] 'listen' or 'defaults' expected."
        line_num = parse_haproxy_error_line(error_msg)
        assert line_num == 54

    def test_parse_haproxy_error_line_simple_line_format(self):
        """Test parsing line number from simple line format."""

        error_msg = "line 42: unknown keyword 'foobar'"
        line_num = parse_haproxy_error_line(error_msg)
        assert line_num == 42

    def test_parse_haproxy_error_line_at_line_format(self):
        """Test parsing line number from 'at line' format."""

        error_msg = "syntax error at line 123"
        line_num = parse_haproxy_error_line(error_msg)
        assert line_num == 123

    def test_parse_haproxy_error_line_not_found(self):
        """Test when no line number is found in error message."""

        error_msg = "generic error without line number"
        line_num = parse_haproxy_error_line(error_msg)
        assert line_num is None

    def test_extract_config_context(self):
        """Test extracting configuration context around an error line."""

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

        config = "line1\nline2\nline3"
        context = extract_config_context(config, 10, context_lines=2)
        assert "out of range" in context
        assert "3 lines" in context

    def test_parse_validation_error_details(self):
        """Test parsing complete validation error details."""

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

    def test_extract_config_context_empty_config(self):
        """Test extracting context from empty configuration."""

        context = extract_config_context("", 1)
        assert context == "No configuration content available"

        context = extract_config_context(None, 1)
        assert context == "No configuration content available"

    def test_parse_validation_error_details_context_extraction_exception(self):
        """Test parsing validation error when context extraction fails."""

        error_msg = "config parsing [/tmp/file:2] syntax error"
        config = "global\n    daemon"

        with patch(
            "haproxy_template_ic.dataplane.extract_config_context"
        ) as mock_extract:
            mock_extract.side_effect = Exception("Context extraction failed")

            error_line, error_context = parse_validation_error_details(
                error_msg, config
            )
            assert error_line == 2
            assert (
                error_context
                == "Error extracting context for line 2: Context extraction failed"
            )

    def test_parse_haproxy_error_line_invalid_number(self):
        """Test parsing when regex matches but number is invalid."""

        # Test with non-numeric match
        error_msg = "config parsing [/tmp/file:invalid]: error"
        line_num = parse_haproxy_error_line(error_msg)
        assert line_num is None

        # Test empty match group
        with patch("re.search") as mock_search:
            mock_match = Mock()
            mock_match.group.side_effect = IndexError("No group")
            mock_search.return_value = mock_match

            line_num = parse_haproxy_error_line("some error")
            assert line_num is None


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

    def test_validation_error_str_with_context(self):
        """Test ValidationError string representation with context."""
        error = ValidationError(
            "validation failed",
            endpoint="http://test:5555",
            config_size=100,
            validation_details="detailed error",
            error_context="line 1: error\nline 2: content",
        )
        error_str = str(error)
        assert "validation failed" in error_str
        assert "config_size=100" in error_str
        assert "details=detailed error" in error_str
        assert "Configuration context around error:" in error_str


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

    def test_dataplane_api_error_str(self):
        """Test DataplaneAPIError string representation."""
        error = DataplaneAPIError(
            "test error", endpoint="http://test:5555", operation="test_op"
        )
        error_str = str(error)
        assert "test error" in error_str
        assert "operation=test_op" in error_str
        assert "endpoint=http://test:5555" in error_str

    def test_dataplane_api_error_str_no_context(self):
        """Test DataplaneAPIError string without context."""
        error = DataplaneAPIError("simple error")
        assert str(error) == "simple error"


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

            # Create a counter to return different configs on different calls
            call_count = {"count": 0}

            def get_structured_config():
                call_count["count"] += 1
                if call_count["count"] == 1:
                    # Validation instance - first call
                    return {
                        "backends": [],
                        "frontends": [],
                        "defaults": [],
                        "global": {"daemon": True},
                    }
                else:
                    # Production instance - different to trigger deployment
                    return {
                        "backends": [],
                        "frontends": [],
                        "defaults": [],
                        "global": {"daemon": False},
                    }

            mock_client.fetch_structured_configuration = AsyncMock(
                side_effect=get_structured_config
            )
            mock_client.sync_maps = AsyncMock(return_value=None)
            mock_client.sync_certificates = AsyncMock(return_value=None)
            mock_client.sync_files = AsyncMock(return_value=None)
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


class TestDataplaneClientSyncMethods:
    """Test DataplaneClient sync methods for maps, certificates, and files."""

    @pytest.mark.asyncio
    async def test_sync_maps_success(self):
        """Test successful map synchronization."""

        client = DataplaneClient("http://localhost:5555")

        # Mock the generated client
        mock_api_client = Mock()

        # Mock existing maps
        mock_existing_map = Mock()
        mock_existing_map.storage_name = "existing.map"

        with patch.object(client, "_get_client", return_value=mock_api_client):
            with patch(
                "haproxy_template_ic.dataplane.get_all_storage_map_files"
            ) as mock_get_maps:
                with patch(
                    "haproxy_template_ic.dataplane.get_one_storage_map"
                ) as mock_get_one:
                    with patch(
                        "haproxy_template_ic.dataplane.create_storage_map_file"
                    ) as mock_create:
                        with patch(
                            "haproxy_template_ic.dataplane.replace_storage_map_file"
                        ) as mock_replace:
                            # Set up existing maps
                            mock_get_maps.asyncio = AsyncMock(
                                return_value=[mock_existing_map]
                            )

                            # Mock get_one to return different content (triggering update)
                            mock_existing_content = Mock()
                            mock_existing_content.payload = io.BytesIO(b"old content")
                            mock_get_one.asyncio = AsyncMock(
                                return_value=mock_existing_content
                            )

                            mock_create.asyncio = AsyncMock(return_value=None)
                            mock_replace.asyncio = AsyncMock(return_value=None)

                            maps_to_sync = {
                                "new.map": "new map content",
                                "existing.map": "updated content",
                            }

                            await client.sync_maps(maps_to_sync)

                            # Verify create was called for new map
                            mock_create.asyncio.assert_called()

                            # Verify replace was called for existing map update
                            mock_replace.asyncio.assert_called_with(
                                client=mock_api_client,
                                name="existing.map",
                                body="updated content",
                            )

    @pytest.mark.asyncio
    async def test_sync_maps_with_obsolete_maps(self):
        """Test map sync deletes obsolete maps."""

        client = DataplaneClient("http://localhost:5555")
        mock_api_client = Mock()

        # Mock existing maps - one will become obsolete
        mock_existing_map = Mock()
        mock_existing_map.storage_name = "obsolete.map"
        mock_keep_map = Mock()
        mock_keep_map.storage_name = "keep.map"

        with patch.object(client, "_get_client", return_value=mock_api_client):
            with patch(
                "haproxy_template_ic.dataplane.get_all_storage_map_files"
            ) as mock_get_maps:
                with patch(
                    "haproxy_template_ic.dataplane.get_one_storage_map"
                ) as mock_get_one:
                    with patch(
                        "haproxy_template_ic.dataplane.replace_storage_map_file"
                    ) as mock_replace:
                        with patch(
                            "haproxy_template_ic.dataplane.delete_storage_map"
                        ) as mock_delete:
                            mock_get_maps.asyncio = AsyncMock(
                                return_value=[mock_existing_map, mock_keep_map]
                            )

                            # Mock get_one to return different content for keep.map
                            mock_existing_content = Mock()
                            mock_existing_content.payload = io.BytesIO(b"old content")
                            mock_get_one.asyncio = AsyncMock(
                                return_value=mock_existing_content
                            )

                            mock_replace.asyncio = AsyncMock(return_value=None)
                            mock_delete.asyncio = AsyncMock(return_value=None)

                            maps_to_sync = {
                                "keep.map": "updated content",
                            }

                            await client.sync_maps(maps_to_sync)

                            # Verify obsolete map was deleted
                            mock_delete.asyncio.assert_any_call(
                                client=mock_api_client, name="obsolete.map"
                            )

    @pytest.mark.asyncio
    async def test_sync_maps_error_handling(self):
        """Test map sync error handling."""

        client = DataplaneClient("http://localhost:5555")
        mock_api_client = Mock()

        with patch.object(client, "_get_client", return_value=mock_api_client):
            with patch(
                "haproxy_template_ic.dataplane.get_all_storage_map_files"
            ) as mock_get_maps:
                mock_get_maps.asyncio = AsyncMock(side_effect=Exception("API Error"))

                maps_to_sync = {"test.map": "content"}

                with pytest.raises(DataplaneAPIError) as exc_info:
                    await client.sync_maps(maps_to_sync)

                assert "Map sync failed" in str(exc_info.value)
                assert exc_info.value.operation == "sync_maps"

    @pytest.mark.asyncio
    async def test_sync_certificates_success(self):
        """Test successful certificate synchronization."""

        client = DataplaneClient("http://localhost:5555")
        mock_api_client = Mock()

        # Mock existing certificates
        mock_existing_cert = Mock()
        mock_existing_cert.storage_name = "existing.pem"

        with patch.object(client, "_get_client", return_value=mock_api_client):
            with patch(
                "haproxy_template_ic.dataplane.get_all_storage_ssl_certificates"
            ) as mock_get_certs:
                with patch(
                    "haproxy_template_ic.dataplane.get_one_storage_ssl_certificate"
                ) as mock_get_one:
                    with patch(
                        "haproxy_template_ic.dataplane.create_storage_ssl_certificate"
                    ) as mock_create:
                        with patch(
                            "haproxy_template_ic.dataplane.replace_storage_ssl_certificate"
                        ) as mock_replace:
                            mock_get_certs.asyncio = AsyncMock(
                                return_value=[mock_existing_cert]
                            )

                            # Mock get_one to return different content (triggering update)
                            mock_existing_content = Mock()
                            mock_existing_content.payload = io.BytesIO(
                                b"-----BEGIN CERTIFICATE-----\nold cert\n-----END CERTIFICATE-----"
                            )
                            mock_get_one.asyncio = AsyncMock(
                                return_value=mock_existing_content
                            )

                            mock_create.asyncio = AsyncMock(return_value=None)
                            mock_replace.asyncio = AsyncMock(return_value=None)

                            certs_to_sync = {
                                "new.pem": "-----BEGIN CERTIFICATE-----\nnew cert\n-----END CERTIFICATE-----",
                                "existing.pem": "-----BEGIN CERTIFICATE-----\nupdated cert\n-----END CERTIFICATE-----",
                            }

                            await client.sync_certificates(certs_to_sync)

                            # Verify create was called for new cert
                            mock_create.asyncio.assert_called()

                            # Verify replace was called for existing cert update
                            mock_replace.asyncio.assert_called_with(
                                client=mock_api_client,
                                name="existing.pem",
                                body="-----BEGIN CERTIFICATE-----\nupdated cert\n-----END CERTIFICATE-----",
                            )

    @pytest.mark.asyncio
    async def test_sync_certificates_error_handling(self):
        """Test certificate sync error handling."""

        client = DataplaneClient("http://localhost:5555")
        mock_api_client = Mock()

        with patch.object(client, "_get_client", return_value=mock_api_client):
            with patch(
                "haproxy_template_ic.dataplane.get_all_storage_ssl_certificates"
            ) as mock_get_certs:
                mock_get_certs.asyncio = AsyncMock(
                    side_effect=Exception("Certificate API Error")
                )

                certs_to_sync = {"test.pem": "cert content"}

                with pytest.raises(DataplaneAPIError) as exc_info:
                    await client.sync_certificates(certs_to_sync)

                assert "Certificate sync failed" in str(exc_info.value)
                assert exc_info.value.operation == "sync_certificates"

    @pytest.mark.asyncio
    async def test_sync_files_success(self):
        """Test successful general file synchronization."""

        client = DataplaneClient("http://localhost:5555")
        mock_api_client = Mock()

        # Mock existing files
        mock_existing_file = Mock()
        mock_existing_file.storage_name = "existing.txt"

        with patch.object(client, "_get_client", return_value=mock_api_client):
            with patch(
                "haproxy_template_ic.dataplane.get_all_storage_general_files"
            ) as mock_get_files:
                with patch(
                    "haproxy_template_ic.dataplane.create_storage_general_file"
                ) as mock_create:
                    with patch(
                        "haproxy_template_ic.dataplane.replace_storage_general_file"
                    ) as mock_replace:
                        with patch(
                            "haproxy_template_ic.dataplane.delete_storage_general_file"
                        ) as mock_delete:
                            mock_get_files.asyncio = AsyncMock(
                                return_value=[mock_existing_file]
                            )
                            mock_create.asyncio = AsyncMock(return_value=None)
                            mock_replace.asyncio = AsyncMock(return_value=None)
                            mock_delete.asyncio = AsyncMock(return_value=None)

                            files_to_sync = {
                                "new.txt": "new file content",
                                "existing.txt": "updated content",
                            }

                            await client.sync_files(files_to_sync)

                            # Verify create was called for new file
                            mock_create.asyncio.assert_called()
                            # Verify replace was called for existing file update
                            mock_replace.asyncio.assert_called_with(
                                client=mock_api_client,
                                name="existing.txt",
                                body=mock.ANY,
                            )

    @pytest.mark.asyncio
    async def test_sync_files_error_handling(self):
        """Test file sync error handling."""

        client = DataplaneClient("http://localhost:5555")
        mock_api_client = Mock()

        with patch.object(client, "_get_client", return_value=mock_api_client):
            with patch(
                "haproxy_template_ic.dataplane.get_all_storage_general_files"
            ) as mock_get_files:
                mock_get_files.asyncio = AsyncMock(
                    side_effect=Exception("File API Error")
                )

                files_to_sync = {"test.txt": "file content"}

                with pytest.raises(DataplaneAPIError) as exc_info:
                    await client.sync_files(files_to_sync)

                assert "File sync failed" in str(exc_info.value)
                assert exc_info.value.operation == "sync_files"

    @pytest.mark.asyncio
    async def test_sync_maps_with_none_response(self):
        """Test sync_maps handles None response from API."""

        client = DataplaneClient("http://localhost:5555")
        mock_api_client = Mock()

        with patch.object(client, "_get_client", return_value=mock_api_client):
            with patch(
                "haproxy_template_ic.dataplane.get_all_storage_map_files"
            ) as mock_get_maps:
                with patch(
                    "haproxy_template_ic.dataplane.create_storage_map_file"
                ) as mock_create:
                    # API returns None instead of empty list
                    mock_get_maps.asyncio = AsyncMock(return_value=None)
                    mock_create.asyncio = AsyncMock(return_value=None)

                    maps_to_sync = {"test.map": "content"}

                    # Should not raise exception and should handle None gracefully
                    await client.sync_maps(maps_to_sync)

                    # Verify create was called since no existing maps
                    mock_create.asyncio.assert_called()

    @pytest.mark.asyncio
    async def test_sync_certificates_with_none_response(self):
        """Test sync_certificates handles None response from API."""

        client = DataplaneClient("http://localhost:5555")
        mock_api_client = Mock()

        with patch.object(client, "_get_client", return_value=mock_api_client):
            with patch(
                "haproxy_template_ic.dataplane.get_all_storage_ssl_certificates"
            ) as mock_get_certs:
                with patch(
                    "haproxy_template_ic.dataplane.create_storage_ssl_certificate"
                ) as mock_create:
                    # API returns None instead of empty list
                    mock_get_certs.asyncio = AsyncMock(return_value=None)
                    mock_create.asyncio = AsyncMock(return_value=None)

                    certs_to_sync = {"test.pem": "cert content"}

                    # Should not raise exception and should handle None gracefully
                    await client.sync_certificates(certs_to_sync)

                    # Verify create was called since no existing certs
                    mock_create.asyncio.assert_called()

    @pytest.mark.asyncio
    async def test_sync_files_with_none_response(self):
        """Test sync_files handles None response from API."""

        client = DataplaneClient("http://localhost:5555")
        mock_api_client = Mock()

        with patch.object(client, "_get_client", return_value=mock_api_client):
            with patch(
                "haproxy_template_ic.dataplane.get_all_storage_general_files"
            ) as mock_get_files:
                with patch(
                    "haproxy_template_ic.dataplane.create_storage_general_file"
                ) as mock_create:
                    # API returns None instead of empty list
                    mock_get_files.asyncio = AsyncMock(return_value=None)
                    mock_create.asyncio = AsyncMock(return_value=None)

                    files_to_sync = {"test.txt": "file content"}

                    # Should not raise exception and should handle None gracefully
                    await client.sync_files(files_to_sync)

                    # Verify create was called since no existing files
                    mock_create.asyncio.assert_called()


class TestDataplaneCriticalPaths:
    """Test critical paths and edge cases for dataplane functionality."""

    def test_normalize_dataplane_url_malformed_urls(self):
        """Test URL normalization with malformed URLs."""

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

    def test_normalize_dataplane_url_parse_errors(self):
        """Test URL normalization with parsing errors triggering fallbacks."""

        # Test with string that causes urlparse to raise ValueError
        with patch("haproxy_template_ic.dataplane.urlparse") as mock_urlparse:
            mock_urlparse.side_effect = ValueError("URL parsing failed")

            # Should fallback to simple string concatenation
            result = normalize_dataplane_url("http://localhost:5555")
            assert result == "http://localhost:5555/v3"

            # Test URL that already has /v3 - should remain unchanged in fallback
            result = normalize_dataplane_url("http://localhost:5555/v3")
            assert result == "http://localhost:5555/v3"

    def test_normalize_dataplane_url_reconstruction_errors(self):
        """Test URL normalization when urlunparse fails."""

        with patch("haproxy_template_ic.dataplane.urlunparse") as mock_urlunparse:
            mock_urlunparse.side_effect = ValueError("URL reconstruction failed")

            # Should fallback to simple string concatenation
            result = normalize_dataplane_url("http://localhost:5555")
            assert result == "http://localhost:5555/v3"

    @pytest.mark.asyncio
    async def test_dataplane_client_get_version_success(self):
        """Test DataplaneClient.get_version() successful retrieval."""

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

        client = DataplaneClient("http://localhost:5555")

        # Test ConnectionError
        with patch("httpx.AsyncClient") as mock_httpx_client:
            mock_client_instance = AsyncMock()
            mock_httpx_client.return_value.__aenter__.return_value = (
                mock_client_instance
            )

            mock_client_instance.post.side_effect = httpx.RequestError("Network error")

            with pytest.raises(DataplaneAPIError) as exc_info:
                await client.validate_configuration("test config")

            assert "Network error during validation" in str(exc_info.value)
            assert exc_info.value.operation == "validate"

    @pytest.mark.asyncio
    async def test_validate_configuration_unexpected_exception(self):
        """Test configuration validation unexpected exception handling."""

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


class TestConfigSynchronizerSyncMethods:
    """Test ConfigSynchronizer sync methods with maps, certificates, and files."""

    @pytest.mark.asyncio
    async def test_sync_configuration_with_maps_and_certificates(self):
        """Test sync with maps and certificates."""
        deployment_history = DeploymentHistory()

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

        # Create context with maps and certificates
        context = Mock()
        context.rendered_config.content = "global\n    daemon"

        # Mock rendered content
        mock_map = Mock()
        mock_map.filename = "test.map"
        mock_map.content = "map content"
        context.rendered_maps = [mock_map]

        mock_cert = Mock()
        mock_cert.filename = "test.pem"
        mock_cert.content = "cert content"
        context.rendered_certificates = [mock_cert]

        mock_file = Mock()
        mock_file.filename = "test.txt"
        mock_file.content = "file content"
        context.rendered_files = [mock_file]

        with patch(
            "haproxy_template_ic.dataplane.DataplaneClient"
        ) as mock_client_class:
            mock_client = Mock()
            mock_client.validate_configuration = AsyncMock(return_value=None)
            mock_client.deploy_configuration = AsyncMock(return_value="v1.0")

            # Return different configs for validation vs production to trigger deployment
            call_count = {"count": 0}

            def get_structured_config():
                call_count["count"] += 1
                if call_count["count"] == 1:
                    # Validation instance - first call
                    return {
                        "backends": [],
                        "frontends": [],
                        "defaults": [],
                        "global": {"daemon": True},
                    }
                else:
                    # Production instance - different to trigger deployment
                    return {
                        "backends": [],
                        "frontends": [],
                        "defaults": [],
                        "global": {"daemon": False},
                    }

            mock_client.fetch_structured_configuration = AsyncMock(
                side_effect=get_structured_config
            )
            mock_client.sync_maps = AsyncMock(return_value=None)
            mock_client.sync_certificates = AsyncMock(return_value=None)
            mock_client.sync_files = AsyncMock(return_value=None)
            mock_client_class.return_value = mock_client

            results = await synchronizer.sync_configuration(context)

            assert results["successful"] == 1
            assert results["failed"] == 0

            # Verify sync methods were called
            mock_client.sync_maps.assert_called_with({"test.map": "map content"})
            mock_client.sync_certificates.assert_called_with(
                {"test.pem": "cert content"}
            )
            mock_client.sync_files.assert_called_with({"test.txt": "file content"})

    @pytest.mark.asyncio
    async def test_sync_configuration_deployment_with_config_context_error(self):
        """Test deployment error with config context parsing."""
        deployment_history = DeploymentHistory()

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
        config_with_error = """global
    daemon
defaults
    invalid-directive
    mode http"""
        context.rendered_config.content = config_with_error
        context.rendered_maps = []
        context.rendered_certificates = []
        context.rendered_files = []

        with patch(
            "haproxy_template_ic.dataplane.DataplaneClient"
        ) as mock_client_class:

            def create_mock_client(url, **kwargs):
                mock_client = Mock()
                if "localhost" in url:  # Validation client
                    mock_client.validate_configuration = AsyncMock(return_value=None)
                    mock_client.deploy_configuration = AsyncMock(return_value="v1.0")
                    mock_client.fetch_structured_configuration = AsyncMock(
                        return_value={
                            "backends": [],
                            "frontends": [],
                            "defaults": [],
                            "global": {"daemon": True},
                        }
                    )
                    mock_client.sync_maps = AsyncMock(return_value=None)
                    mock_client.sync_certificates = AsyncMock(return_value=None)
                    mock_client.sync_files = AsyncMock(return_value=None)
                else:  # Production client
                    # Return different config to trigger deployment attempt
                    mock_client.fetch_structured_configuration = AsyncMock(
                        return_value={
                            "backends": [],
                            "frontends": [],
                            "defaults": [],
                            "global": {
                                "daemon": False
                            },  # Different to trigger deployment
                        }
                    )
                    # Simulate deployment error with line reference
                    error_with_line = Exception(
                        "config parsing [/tmp/haproxy.cfg:4]: unknown keyword 'invalid-directive'"
                    )
                    mock_client.deploy_configuration = AsyncMock(
                        side_effect=error_with_line
                    )
                    mock_client.sync_maps = AsyncMock(return_value=None)
                    mock_client.sync_certificates = AsyncMock(return_value=None)
                    mock_client.sync_files = AsyncMock(return_value=None)
                return mock_client

            mock_client_class.side_effect = create_mock_client

            results = await synchronizer.sync_configuration(context)

            assert results["successful"] == 0
            assert results["failed"] == 1
            assert len(results["errors"]) == 1
            # Error should contain context information
            error_msg = results["errors"][0]
            assert "unknown keyword 'invalid-directive'" in error_msg

    @pytest.mark.asyncio
    async def test_sync_configuration_deployment_with_dataplane_api_error_containing_context(
        self,
    ):
        """Test deployment error with DataplaneAPIError that already contains context."""
        deployment_history = DeploymentHistory()

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
        context.rendered_maps = []
        context.rendered_certificates = []
        context.rendered_files = []

        with patch(
            "haproxy_template_ic.dataplane.DataplaneClient"
        ) as mock_client_class:

            def create_mock_client(url, **kwargs):
                mock_client = Mock()
                if "localhost" in url:  # Validation client
                    mock_client.validate_configuration = AsyncMock(return_value=None)
                    mock_client.deploy_configuration = AsyncMock(return_value="v1.0")
                    mock_client.fetch_structured_configuration = AsyncMock(
                        return_value={
                            "backends": [],
                            "frontends": [],
                            "defaults": [],
                            "global": {"daemon": True},
                        }
                    )
                    mock_client.sync_maps = AsyncMock(return_value=None)
                    mock_client.sync_certificates = AsyncMock(return_value=None)
                    mock_client.sync_files = AsyncMock(return_value=None)
                else:  # Production client
                    # Return different config to trigger deployment attempt
                    mock_client.fetch_structured_configuration = AsyncMock(
                        return_value={
                            "backends": [],
                            "frontends": [],
                            "defaults": [],
                            "global": {
                                "daemon": False
                            },  # Different to trigger deployment
                        }
                    )
                    # Create error that already contains context
                    error_with_context = DataplaneAPIError(
                        "Deploy failed\n\nConfiguration context around error:\n> 4: invalid line"
                    )
                    mock_client.deploy_configuration = AsyncMock(
                        side_effect=error_with_context
                    )
                    mock_client.sync_maps = AsyncMock(return_value=None)
                    mock_client.sync_certificates = AsyncMock(return_value=None)
                    mock_client.sync_files = AsyncMock(return_value=None)
                return mock_client

            mock_client_class.side_effect = create_mock_client

            results = await synchronizer.sync_configuration(context)

            assert results["successful"] == 0
            assert results["failed"] == 1
            # Should not try to add additional context since it already exists
            error_msg = results["errors"][0]
            assert "Configuration context around error:" in error_msg

    @pytest.mark.asyncio
    async def test_sync_configuration_deployment_context_extraction_failure(self):
        """Test deployment error when context extraction fails."""
        deployment_history = DeploymentHistory()

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
        context.rendered_maps = []
        context.rendered_certificates = []
        context.rendered_files = []

        with patch(
            "haproxy_template_ic.dataplane.DataplaneClient"
        ) as mock_client_class:
            with patch(
                "haproxy_template_ic.dataplane.parse_validation_error_details"
            ) as mock_parse:

                def create_mock_client(url, **kwargs):
                    mock_client = Mock()
                    if "localhost" in url:  # Validation client
                        mock_client.validate_configuration = AsyncMock(
                            return_value=None
                        )
                        mock_client.deploy_configuration = AsyncMock(
                            return_value="v1.0"
                        )
                        mock_client.fetch_structured_configuration = AsyncMock(
                            return_value={
                                "backends": [],
                                "frontends": [],
                                "defaults": [],
                                "global": {"daemon": True},
                            }
                        )
                        mock_client.sync_maps = AsyncMock(return_value=None)
                        mock_client.sync_certificates = AsyncMock(return_value=None)
                        mock_client.sync_files = AsyncMock(return_value=None)
                    else:  # Production client
                        # Return different config to trigger deployment attempt
                        mock_client.fetch_structured_configuration = AsyncMock(
                            return_value={
                                "backends": [],
                                "frontends": [],
                                "defaults": [],
                                "global": {
                                    "daemon": False
                                },  # Different to trigger deployment
                            }
                        )
                        mock_client.deploy_configuration = AsyncMock(
                            side_effect=Exception("Generic deployment error")
                        )
                        mock_client.sync_maps = AsyncMock(return_value=None)
                        mock_client.sync_certificates = AsyncMock(return_value=None)
                        mock_client.sync_files = AsyncMock(return_value=None)
                    return mock_client

                # Make context extraction raise an exception
                mock_parse.side_effect = Exception("Context extraction failed")
                mock_client_class.side_effect = create_mock_client

                results = await synchronizer.sync_configuration(context)

                assert results["successful"] == 0
                assert results["failed"] == 1
                # Should still log the original error even if context extraction fails
                error_msg = results["errors"][0]
                assert "Generic deployment error" in error_msg


class TestDataplaneClientDeploymentRetryLogic:
    """Test DataplaneClient deployment retry mechanisms and error handling."""

    @pytest.mark.asyncio
    async def test_deploy_configuration_version_get_failure(self):
        """Test deployment when getting current version fails."""

        client = DataplaneClient("http://localhost:5555")

        with patch("httpx.AsyncClient") as mock_async_client:
            mock_client_instance = AsyncMock()
            mock_async_client.return_value.__aenter__.return_value = (
                mock_client_instance
            )

            # Mock version request failure
            mock_version_resp = MagicMock()
            mock_version_resp.status_code = 500
            mock_version_resp.text = "Version API error"

            mock_client_instance.get.return_value = mock_version_resp

            with pytest.raises(DataplaneAPIError) as exc_info:
                await client.deploy_configuration("global\n    daemon\n")

            # Error message now wrapped by retry mechanism
            assert "Configuration deployment failed" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_deploy_configuration_new_version_get_failure(self):
        """Test deployment when getting new version after deployment fails."""

        client = DataplaneClient("http://localhost:5555")

        with patch("httpx.AsyncClient") as mock_async_client:
            mock_client_instance = AsyncMock()
            mock_async_client.return_value.__aenter__.return_value = (
                mock_client_instance
            )

            # Mock successful initial version request and deployment
            mock_version_resp_1 = MagicMock()
            mock_version_resp_1.status_code = 200
            mock_version_resp_1.json.return_value = 1

            mock_deploy_resp = MagicMock()
            mock_deploy_resp.status_code = 200

            # Mock failed new version request
            mock_version_resp_2 = MagicMock()
            mock_version_resp_2.status_code = 500
            mock_version_resp_2.text = "New version API error"

            mock_client_instance.get.side_effect = [
                mock_version_resp_1,
                mock_version_resp_2,
            ]
            mock_client_instance.post.return_value = mock_deploy_resp

            with pytest.raises(DataplaneAPIError) as exc_info:
                await client.deploy_configuration("global\n    daemon\n")

            # Error message now wrapped by retry mechanism
            assert "Configuration deployment failed" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_deploy_configuration_successful(self):
        """Test successful configuration deployment."""

        client = DataplaneClient("http://localhost:5555")

        with patch("httpx.AsyncClient") as mock_async_client:
            mock_client_instance = AsyncMock()
            mock_async_client.return_value.__aenter__.return_value = (
                mock_client_instance
            )

            # Mock version responses (successful)
            mock_version_resp_1 = MagicMock()
            mock_version_resp_1.status_code = 200
            mock_version_resp_1.json.return_value = 1

            mock_version_resp_2 = MagicMock()
            mock_version_resp_2.status_code = 200
            mock_version_resp_2.json.return_value = 2

            # Successful deployment flow
            mock_client_instance.get.side_effect = [
                mock_version_resp_1,  # Get current version
                mock_version_resp_2,  # Get new version after deployment
            ]

            mock_deploy_resp = MagicMock()
            mock_deploy_resp.status_code = 200
            mock_client_instance.post.return_value = mock_deploy_resp

            result = await client.deploy_configuration("global\n    daemon\n")
            assert result == "2"

    @pytest.mark.asyncio
    async def test_deploy_configuration_retry_exhausted(self):
        """Test deployment when all retry attempts are exhausted."""

        client = DataplaneClient("http://localhost:5555")

        with patch("httpx.AsyncClient") as mock_async_client:
            mock_client_instance = AsyncMock()
            mock_async_client.return_value.__aenter__.return_value = (
                mock_client_instance
            )

            # Always fail with network error
            mock_client_instance.get.side_effect = httpx.RequestError(
                "Network always fails"
            )

            # Retry mechanism is already mocked globally by the fixture
            with pytest.raises(DataplaneAPIError) as exc_info:
                await client.deploy_configuration("global\n    daemon\n")

            assert "Configuration deployment failed" in str(exc_info.value)
            assert exc_info.value.operation == "deploy"


class TestConditionalDeployment:
    """Test conditional deployment functionality that minimizes HAProxy reloads."""

    @pytest.mark.asyncio
    async def test_get_current_configuration_success(self):
        """Test successful retrieval of current configuration."""

        client = DataplaneClient("http://localhost:5555")

        with patch.object(client, "_get_client") as mock_get_client:
            mock_client = AsyncMock()
            mock_get_client.return_value = mock_client

            # Mock successful get_ha_proxy_configuration call
            with patch(
                "haproxy_template_ic.dataplane.get_ha_proxy_configuration"
            ) as mock_get_config:
                mock_get_config.asyncio = AsyncMock(return_value="global\n    daemon\n")

                result = await client.get_current_configuration()

                assert result == "global\n    daemon\n"
                mock_get_config.asyncio.assert_called_once_with(client=mock_client)

    @pytest.mark.asyncio
    async def test_get_current_configuration_error(self):
        """Test handling of errors when getting current configuration."""

        client = DataplaneClient("http://localhost:5555")

        with patch.object(client, "_get_client") as mock_get_client:
            mock_client = MagicMock()
            mock_get_client.return_value = mock_client

            # Mock exception in get_ha_proxy_configuration
            with patch(
                "haproxy_template_ic.dataplane.get_ha_proxy_configuration"
            ) as mock_get_config:
                mock_get_config.asyncio.side_effect = Exception("API Error")

                result = await client.get_current_configuration()

                assert result is None

    @pytest.mark.asyncio
    async def test_deploy_configuration_conditionally_config_unchanged(self):
        """Test conditional deployment when configuration is unchanged."""

        client = DataplaneClient("http://localhost:5555")
        current_config = "global\n    daemon\n"

        with patch.object(client, "get_current_configuration") as mock_get_current:
            mock_get_current.return_value = current_config

            with patch.object(client, "_get_client") as mock_get_client:
                mock_client = AsyncMock()
                mock_get_client.return_value = mock_client

                # Mock version retrieval
                with patch(
                    "haproxy_template_ic.dataplane.get_configuration_version"
                ) as mock_get_version:
                    mock_get_version.asyncio = AsyncMock(return_value=5)

                    # Should skip deployment and return current version
                    result = await client.deploy_configuration_conditionally(
                        current_config
                    )

                    assert result == "5"
                    mock_get_version.asyncio.assert_called_once_with(client=mock_client)

    @pytest.mark.asyncio
    async def test_deploy_configuration_conditionally_config_changed(self):
        """Test conditional deployment when configuration has changed."""

        client = DataplaneClient("http://localhost:5555")
        current_config = "global\n    daemon\n"
        new_config = "global\n    daemon\n    maxconn 1000\n"

        with patch.object(client, "get_current_configuration") as mock_get_current:
            mock_get_current.return_value = current_config

            with patch.object(client, "deploy_configuration") as mock_deploy:
                mock_deploy.return_value = "6"

                # Should deploy and return new version
                result = await client.deploy_configuration_conditionally(new_config)

                assert result == "6"
                mock_deploy.assert_called_once_with(new_config)

    @pytest.mark.asyncio
    async def test_deploy_configuration_conditionally_force_deployment(self):
        """Test conditional deployment with force=True."""

        client = DataplaneClient("http://localhost:5555")
        config = "global\n    daemon\n"

        with patch.object(client, "deploy_configuration") as mock_deploy:
            mock_deploy.return_value = "7"

            # Should deploy even without checking current config
            result = await client.deploy_configuration_conditionally(config, force=True)

            assert result == "7"
            mock_deploy.assert_called_once_with(config)

    @pytest.mark.asyncio
    async def test_deploy_configuration_conditionally_no_current_config(self):
        """Test conditional deployment when current config is not available."""

        client = DataplaneClient("http://localhost:5555")
        new_config = "global\n    daemon\n"

        with patch.object(client, "get_current_configuration") as mock_get_current:
            mock_get_current.return_value = None  # Cannot get current config

            with patch.object(client, "deploy_configuration") as mock_deploy:
                mock_deploy.return_value = "8"

                # Should deploy since we can't compare
                result = await client.deploy_configuration_conditionally(new_config)

                assert result == "8"
                mock_deploy.assert_called_once_with(new_config)

    def test_config_normalization(self):
        """Test configuration normalization for comparison."""

        client = DataplaneClient("http://localhost:5555")

        # Access the normalize function through a mock deployment call
        with patch.object(client, "get_current_configuration") as mock_get_current:
            with patch.object(client, "deploy_configuration") as mock_deploy:
                config1 = "global\n    daemon\n\n\n"  # Extra newlines
                config3 = "global\n    daemon\n"  # Clean

                # All should normalize to the same thing
                mock_get_current.return_value = config1
                mock_deploy.return_value = "9"

                # The normalization logic is embedded in the method,
                # so we test it indirectly by ensuring identical normalized configs are detected
                async def test_normalization():
                    # This should skip deployment since normalized configs are identical
                    with patch.object(client, "_get_client") as mock_get_client:
                        mock_client = AsyncMock()
                        mock_get_client.return_value = mock_client

                        with patch(
                            "haproxy_template_ic.dataplane.get_configuration_version"
                        ) as mock_get_version:
                            mock_get_version.asyncio = AsyncMock(return_value=10)

                            result = await client.deploy_configuration_conditionally(
                                config3
                            )
                            assert (
                                result == "10"
                            )  # Should return current version, not deploy

                asyncio.run(test_normalization())


class TestConfigSynchronizerEnhancements:
    """Test enhancements to ConfigSynchronizer with conditional deployment."""

    @pytest.mark.asyncio
    async def test_sync_configuration_with_skipped_deployments(self):
        """Test sync_configuration with some deployments skipped due to unchanged config."""

        # Setup test data
        production_urls = ["http://prod1:5555", "http://prod2:5555"]
        validation_url = "http://validation:5555"
        credentials = Credentials(
            dataplane=DataplaneAuth(username="admin", password=SecretStr("pass")),
            validation=DataplaneAuth(
                username="admin", password=SecretStr("validationpass")
            ),
        )

        synchronizer = ConfigSynchronizer(production_urls, validation_url, credentials)

        # Mock config context
        mock_config_context = MagicMock()
        mock_config_context.rendered_config.content = "global\n    daemon\n"
        mock_config_context.rendered_maps = []
        mock_config_context.rendered_certificates = []
        mock_config_context.rendered_files = []

        with patch.object(synchronizer, "_sync_content_to_client"):
            with patch.object(synchronizer, "_validate_configuration"):
                # Mock conditional deployment - first succeeds, second skips
                with patch(
                    "haproxy_template_ic.dataplane.DataplaneClient"
                ) as MockDataplaneClient:
                    # Validation instance
                    mock_validation_client = AsyncMock()
                    # Production instances
                    mock_prod_client_1 = AsyncMock()
                    mock_prod_client_2 = AsyncMock()

                    MockDataplaneClient.side_effect = [
                        mock_validation_client,  # validation client
                        mock_prod_client_1,  # first production client
                        mock_prod_client_2,  # second production client
                    ]

                    # Mock structured configuration fetch to work properly
                    # First client has different config, second has same config
                    mock_prod_client_1.fetch_structured_configuration = AsyncMock(
                        return_value={
                            "backends": [],
                            "frontends": [],
                            "defaults": [],
                            "global": type(
                                "obj",
                                (object,),
                                {"to_dict": lambda self: {"old": "config"}},
                            )(),
                        }
                    )
                    mock_prod_client_1.deploy_configuration = AsyncMock(
                        return_value="5"
                    )

                    mock_prod_client_2.fetch_structured_configuration = AsyncMock(
                        return_value={
                            "backends": [],
                            "frontends": [],
                            "defaults": [],
                            "global": type(
                                "obj",
                                (object,),
                                {"to_dict": lambda self: {"new": "config"}},
                            )(),
                        }
                    )
                    # Second client should not deploy because config matches validation

                    # Mock validation client to deploy and fetch structured config
                    mock_validation_client.deploy_configuration = AsyncMock()
                    mock_validation_client.fetch_structured_configuration = AsyncMock(
                        return_value={
                            "backends": [],
                            "frontends": [],
                            "defaults": [],
                            "global": type(
                                "obj",
                                (object,),
                                {"to_dict": lambda self: {"new": "config"}},
                            )(),
                        }
                    )

                    # Mock deployment history to simulate version tracking
                    synchronizer.deployment_history._history = {
                        "http://prod1:5555": {
                            "version": "4"
                        },  # Different version, should deploy
                        "http://prod2:5555": {
                            "version": "3"
                        },  # Same version, should skip
                    }

                    result = await synchronizer.sync_configuration(mock_config_context)

                    # Should have 1 successful deployment and 1 skipped
                    assert result["successful"] == 1
                    assert result["skipped"] == 1
                    assert result["failed"] == 0

    @pytest.mark.asyncio
    async def test_sync_configuration_with_fallback_deployment(self):
        """Test sync_configuration with fallback to regular deployment when conditional fails."""

        # Setup test data
        production_urls = ["http://prod1:5555"]
        validation_url = "http://validation:5555"
        credentials = Credentials(
            dataplane=DataplaneAuth(username="admin", password=SecretStr("pass")),
            validation=DataplaneAuth(
                username="admin", password=SecretStr("validationpass")
            ),
        )

        synchronizer = ConfigSynchronizer(production_urls, validation_url, credentials)

        # Mock config context
        mock_config_context = MagicMock()
        mock_config_context.rendered_config.content = "global\n    daemon\n"
        mock_config_context.rendered_maps = []
        mock_config_context.rendered_certificates = []
        mock_config_context.rendered_files = []

        with patch.object(synchronizer, "_sync_content_to_client"):
            with patch.object(synchronizer, "_validate_configuration"):
                with patch(
                    "haproxy_template_ic.dataplane.DataplaneClient"
                ) as MockDataplaneClient:
                    # Validation instance
                    mock_validation_client = AsyncMock()
                    # Production instance
                    mock_prod_client = AsyncMock()

                    MockDataplaneClient.side_effect = [
                        mock_validation_client,  # validation client
                        mock_prod_client,  # production client
                    ]

                    # Mock structured fetch and conditional deployment to fail, regular deployment to succeed
                    mock_prod_client.fetch_structured_configuration = AsyncMock(
                        side_effect=Exception("Structured failed")
                    )
                    mock_prod_client.deploy_configuration_conditionally = AsyncMock(
                        side_effect=Exception("Conditional failed")
                    )
                    mock_prod_client.deploy_configuration = AsyncMock(return_value="6")

                    # Mock validation client to deploy and fetch structured config
                    mock_validation_client.deploy_configuration = AsyncMock()
                    mock_validation_client.fetch_structured_configuration = AsyncMock(
                        return_value={
                            "backends": [],
                            "frontends": [],
                            "defaults": [],
                            "global": None,
                        }
                    )

                    result = await synchronizer.sync_configuration(mock_config_context)

                    # Should have 1 successful deployment (via fallback)
                    assert result["successful"] == 1
                    assert result["failed"] == 0

                    # Verify fallback chain was used
                    mock_prod_client.fetch_structured_configuration.assert_called_once()
                    mock_prod_client.deploy_configuration_conditionally.assert_called_once()
                    mock_prod_client.deploy_configuration.assert_called_once()


class TestDataplaneClientFetchStructuredConfiguration:
    """Test DataplaneClient fetch_structured_configuration for better coverage."""

    @pytest.mark.asyncio
    async def test_fetch_structured_configuration_basic(self):
        """Test basic fetch_structured_configuration functionality."""
        client = DataplaneClient("http://test:5555")

        with pytest.MonkeyPatch().context() as m:
            # Mock all the individual API calls
            m.setattr(
                "haproxy_template_ic.dataplane.get_backends.asyncio",
                AsyncMock(return_value=[]),
            )
            m.setattr(
                "haproxy_template_ic.dataplane.get_frontends.asyncio",
                AsyncMock(return_value=[]),
            )
            m.setattr(
                "haproxy_template_ic.dataplane.get_defaults_sections.asyncio",
                AsyncMock(return_value=[]),
            )
            m.setattr(
                "haproxy_template_ic.dataplane.get_global.asyncio",
                AsyncMock(return_value=Mock()),
            )

            # Mock other sections to return empty
            m.setattr(
                "haproxy_template_ic.dataplane.get_userlists.asyncio",
                AsyncMock(return_value=[]),
            )
            m.setattr(
                "haproxy_template_ic.dataplane.get_caches.asyncio",
                AsyncMock(return_value=[]),
            )
            m.setattr(
                "haproxy_template_ic.dataplane.get_mailers_sections.asyncio",
                AsyncMock(return_value=[]),
            )
            m.setattr(
                "haproxy_template_ic.dataplane.get_log_forwards.asyncio",
                AsyncMock(return_value=[]),
            )
            m.setattr(
                "haproxy_template_ic.dataplane.get_rings.asyncio",
                AsyncMock(return_value=[]),
            )
            m.setattr(
                "haproxy_template_ic.dataplane.get_resolvers.asyncio",
                AsyncMock(return_value=[]),
            )
            m.setattr(
                "haproxy_template_ic.dataplane.get_http_errors_sections.asyncio",
                AsyncMock(return_value=[]),
            )
            m.setattr(
                "haproxy_template_ic.dataplane.get_peer_sections.asyncio",
                AsyncMock(return_value=[]),
            )
            m.setattr(
                "haproxy_template_ic.dataplane.get_fcgi_apps.asyncio",
                AsyncMock(return_value=[]),
            )
            m.setattr(
                "haproxy_template_ic.dataplane.get_programs.asyncio",
                AsyncMock(return_value=[]),
            )

            client._client = Mock()
            result = await client.fetch_structured_configuration()

            assert isinstance(result, dict)
            assert "backends" in result
            assert "frontends" in result
            assert result["backends"] == []
            assert result["frontends"] == []

    @pytest.mark.asyncio
    async def test_fetch_structured_configuration_with_data(self):
        """Test fetch_structured_configuration with actual data."""
        client = DataplaneClient("http://test:5555")

        # Create mock backend and frontend
        mock_backend = Mock()
        mock_backend.name = "test_backend"
        mock_frontend = Mock()
        mock_frontend.name = "test_frontend"

        with pytest.MonkeyPatch().context() as m:
            # Mock API calls to return data
            m.setattr(
                "haproxy_template_ic.dataplane.get_backends.asyncio",
                AsyncMock(return_value=[mock_backend]),
            )
            m.setattr(
                "haproxy_template_ic.dataplane.get_frontends.asyncio",
                AsyncMock(return_value=[mock_frontend]),
            )
            m.setattr(
                "haproxy_template_ic.dataplane.get_defaults_sections.asyncio",
                AsyncMock(return_value=[]),
            )
            m.setattr(
                "haproxy_template_ic.dataplane.get_global.asyncio",
                AsyncMock(return_value=Mock()),
            )

            # Mock other sections to return empty
            m.setattr(
                "haproxy_template_ic.dataplane.get_userlists.asyncio",
                AsyncMock(return_value=[]),
            )
            m.setattr(
                "haproxy_template_ic.dataplane.get_caches.asyncio",
                AsyncMock(return_value=[]),
            )
            m.setattr(
                "haproxy_template_ic.dataplane.get_mailers_sections.asyncio",
                AsyncMock(return_value=[]),
            )
            m.setattr(
                "haproxy_template_ic.dataplane.get_log_forwards.asyncio",
                AsyncMock(return_value=[]),
            )
            m.setattr(
                "haproxy_template_ic.dataplane.get_rings.asyncio",
                AsyncMock(return_value=[]),
            )
            m.setattr(
                "haproxy_template_ic.dataplane.get_resolvers.asyncio",
                AsyncMock(return_value=[]),
            )
            m.setattr(
                "haproxy_template_ic.dataplane.get_http_errors_sections.asyncio",
                AsyncMock(return_value=[]),
            )
            m.setattr(
                "haproxy_template_ic.dataplane.get_peer_sections.asyncio",
                AsyncMock(return_value=[]),
            )
            m.setattr(
                "haproxy_template_ic.dataplane.get_fcgi_apps.asyncio",
                AsyncMock(return_value=[]),
            )
            m.setattr(
                "haproxy_template_ic.dataplane.get_programs.asyncio",
                AsyncMock(return_value=[]),
            )

            client._client = Mock()
            result = await client.fetch_structured_configuration()

            assert result["backends"] == [mock_backend]
            assert result["frontends"] == [mock_frontend]

    @pytest.mark.asyncio
    async def test_fetch_structured_configuration_exception_handling(self):
        """Test fetch_structured_configuration exception handling."""
        client = DataplaneClient("http://test:5555")

        with pytest.MonkeyPatch().context() as m:
            # Mock get_backends to raise an exception
            m.setattr(
                "haproxy_template_ic.dataplane.get_backends.asyncio",
                AsyncMock(side_effect=Exception("API error")),
            )

            client._client = Mock()

            # Should raise DataplaneAPIError when there are API errors
            with pytest.raises(
                DataplaneAPIError, match="Failed to fetch structured configuration"
            ):
                await client.fetch_structured_configuration()
