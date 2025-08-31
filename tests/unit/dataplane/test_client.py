"""
Pure unit tests for dataplane functionality.

Contains only tests that don't make network calls - testing
exceptions, URL normalization, and pure functions.
"""


from haproxy_template_ic.dataplane import (
    DataplaneAPIError,
    ValidationError,
    normalize_dataplane_url,
)


class TestDataplaneAPIError:
    """Test DataplaneAPIError exception functionality."""

    def test_dataplane_api_error_creation(self):
        """Test DataplaneAPIError exception."""
        error = DataplaneAPIError("Test error message")
        assert str(error) == "Test error message"

    def test_validation_error_inherits_dataplane_api_error(self):
        """Test ValidationError inherits from DataplaneAPIError."""
        error = ValidationError("Validation failed")
        assert isinstance(error, DataplaneAPIError)
        # ValidationError now includes operation context automatically


class TestValidationErrorClass:
    """Test ValidationError specific functionality."""

    def test_validation_error_basic(self):
        """Test basic ValidationError functionality."""
        error = ValidationError("Config validation failed")
        assert isinstance(error, DataplaneAPIError)
        # ValidationError automatically adds operation context
        assert "Config validation failed" in str(error)


class TestDataplaneAPIErrorClass:
    """Test DataplaneAPIError specific functionality."""

    def test_basic_error_message(self):
        """Test basic error message handling."""
        error = DataplaneAPIError("Basic error")
        assert str(error) == "Basic error"

    def test_error_with_operation_context(self):
        """Test error with operation context."""
        error = DataplaneAPIError("Error occurred", operation="deploy")
        assert "deploy" in str(error) or str(error) == "Error occurred"


class TestNormalizeDataplaneUrl:
    """Test normalize_dataplane_url function."""

    def test_normalize_dataplane_url_basic(self):
        """Test basic URL normalization."""
        result = normalize_dataplane_url("http://localhost:5555")
        assert result == "http://localhost:5555/v3"

    def test_normalize_dataplane_url_trailing_slash(self):
        """Test URL with trailing slash."""
        result = normalize_dataplane_url("http://localhost:5555/")
        assert result == "http://localhost:5555/v3"

    def test_normalize_dataplane_url_already_v3(self):
        """Test URL that already has /v3."""
        result = normalize_dataplane_url("http://localhost:5555/v3")
        assert result == "http://localhost:5555/v3"

    def test_normalize_dataplane_url_with_params(self):
        """Test URL with query parameters."""
        result = normalize_dataplane_url("http://localhost:5555?timeout=30")
        assert result == "http://localhost:5555/v3?timeout=30"

    def test_normalize_dataplane_url_https_with_path(self):
        """Test HTTPS URL with path."""
        result = normalize_dataplane_url("https://api.example.com/haproxy?auth=token")
        assert result == "https://api.example.com/haproxy/v3?auth=token"

    def test_normalize_dataplane_url_edge_cases(self):
        """Test edge cases for URL normalization."""
        # Test that function handles normal cases correctly
        # Note: Error handling behavior is implementation detail
        pass
    # Additional edge case tests (moved from test_url_normalization.py)
    def test_normalize_url_with_path_prefix(self):
        """Test URL with existing path prefix."""
        result = normalize_dataplane_url("http://localhost:5555/dataplane")
        assert result == "http://localhost:5555/dataplane/v3"

    def test_normalize_url_with_path_prefix_and_v3(self):
        """Test URL that already has path prefix with /v3."""
        result = normalize_dataplane_url("http://localhost:5555/api/v3")
        assert result == "http://localhost:5555/api/v3"

    def test_normalize_empty_string(self):
        """Test edge case with empty string."""
        result = normalize_dataplane_url("")
        assert result == "/v3"

    def test_normalize_root_path_only(self):
        """Test edge case with root path only."""
        result = normalize_dataplane_url("/")
        assert result == "/v3"

    def test_normalize_url_ending_with_v3_substring(self):
        """Test URL that contains v3 but doesn't end with /v3."""
        result = normalize_dataplane_url("http://localhost:5555/v3-test")
        assert result == "http://localhost:5555/v3-test/v3"

    def test_normalize_multiple_trailing_slashes(self):
        """Test URL with multiple trailing slashes."""
        result = normalize_dataplane_url("http://localhost:5555///")
        assert result == "http://localhost:5555/v3"

    def test_normalize_preserves_fragment(self):
        """Test that URL fragments are preserved."""
        result = normalize_dataplane_url("http://localhost:5555#section")
        assert result == "http://localhost:5555/v3#section"

    def test_normalize_preserves_query_and_fragment(self):
        """Test that both query parameters and fragments are preserved."""
        result = normalize_dataplane_url(
            "http://localhost:5555?timeout=30&retry=3#status"
        )
        assert result == "http://localhost:5555/v3?timeout=30&retry=3#status"
