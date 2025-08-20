"""
Unit tests for URL normalization utility function.

Tests edge cases and various input formats for the normalize_dataplane_url function.
"""

from haproxy_template_ic.dataplane import normalize_dataplane_url


class TestNormalizeDataplaneUrl:
    """Test cases for the normalize_dataplane_url utility function."""

    def test_normalize_url_without_v3(self):
        """Test normalization of URL without /v3 suffix."""
        result = normalize_dataplane_url("http://localhost:5555")
        assert result == "http://localhost:5555/v3"

    def test_normalize_url_with_trailing_slash(self):
        """Test normalization of URL with trailing slash."""
        result = normalize_dataplane_url("http://localhost:5555/")
        assert result == "http://localhost:5555/v3"

    def test_normalize_url_already_with_v3(self):
        """Test that URL already ending with /v3 is unchanged."""
        result = normalize_dataplane_url("http://localhost:5555/v3")
        assert result == "http://localhost:5555/v3"

    def test_normalize_url_with_v3_and_trailing_slash(self):
        """Test URL ending with /v3/ gets trailing slash removed."""
        result = normalize_dataplane_url("http://localhost:5555/v3/")
        assert result == "http://localhost:5555/v3"

    def test_normalize_https_url(self):
        """Test HTTPS URL normalization."""
        result = normalize_dataplane_url("https://haproxy.example.com:5555")
        assert result == "https://haproxy.example.com:5555/v3"

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

    def test_normalize_preserves_query_parameters(self):
        """Test that query parameters are preserved."""
        result = normalize_dataplane_url("http://localhost:5555?timeout=30")
        assert result == "http://localhost:5555?timeout=30/v3"

    def test_normalize_preserves_fragment(self):
        """Test that URL fragments are preserved."""
        result = normalize_dataplane_url("http://localhost:5555#section")
        assert result == "http://localhost:5555#section/v3"
