"""
Unit tests for dataplane utility functions.

Tests URL normalization and other utility functions from the utils module.
"""

from haproxy_template_ic.dataplane import normalize_dataplane_url


def test_normalize_dataplane_url_basic():
    """Test basic URL normalization."""
    result = normalize_dataplane_url("http://localhost:5555")
    assert result == "http://localhost:5555/v3"


def test_normalize_dataplane_url_trailing_slash():
    """Test URL with trailing slash."""
    result = normalize_dataplane_url("http://localhost:5555/")
    assert result == "http://localhost:5555/v3"


def test_normalize_dataplane_url_already_v3():
    """Test URL that already has /v3."""
    result = normalize_dataplane_url("http://localhost:5555/v3")
    assert result == "http://localhost:5555/v3"


def test_normalize_dataplane_url_https_with_path():
    """Test HTTPS URL with existing path."""
    result = normalize_dataplane_url("https://api.example.com/haproxy")
    assert result == "https://api.example.com/haproxy/v3"


def test_normalize_dataplane_url_with_params():
    """Test URL with query parameters."""
    result = normalize_dataplane_url("http://localhost:5555?timeout=30")
    assert result == "http://localhost:5555/v3?timeout=30"


def test_normalize_url_with_path_prefix():
    """Test URL with path prefix."""
    result = normalize_dataplane_url("http://api.example.com/dataplane")
    assert result == "http://api.example.com/dataplane/v3"


def test_normalize_url_with_path_prefix_and_v3():
    """Test URL with path prefix that already has v3."""
    result = normalize_dataplane_url("http://api.example.com/dataplane/v3")
    assert result == "http://api.example.com/dataplane/v3"


def test_normalize_url_ending_with_v3_substring():
    """Test URL ending with v3 as substring (not path segment)."""
    result = normalize_dataplane_url("http://api.example.com/apiv3")
    assert result == "http://api.example.com/apiv3/v3"


def test_normalize_preserves_fragment():
    """Test that fragment is preserved."""
    result = normalize_dataplane_url("http://localhost:5555#section")
    assert result == "http://localhost:5555/v3#section"


def test_normalize_preserves_query_and_fragment():
    """Test that both query and fragment are preserved."""
    result = normalize_dataplane_url("http://localhost:5555?timeout=30#section")
    assert result == "http://localhost:5555/v3?timeout=30#section"


def test_normalize_multiple_trailing_slashes():
    """Test URL with multiple trailing slashes."""
    result = normalize_dataplane_url("http://localhost:5555///")
    assert result == "http://localhost:5555/v3"


def test_normalize_root_path_only():
    """Test URL with only root path."""
    result = normalize_dataplane_url("http://localhost:5555/")
    assert result == "http://localhost:5555/v3"


def test_normalize_empty_string():
    """Test empty string normalization."""
    result = normalize_dataplane_url("")
    assert result == "/v3"


def test_normalize_dataplane_url_edge_cases():
    """Test edge cases for URL normalization."""
    # Test with port
    result = normalize_dataplane_url("http://localhost:8080")
    assert result == "http://localhost:8080/v3"

    # Test with subdomain
    result = normalize_dataplane_url("https://haproxy.example.com")
    assert result == "https://haproxy.example.com/v3"


def test_normalize_basic_url():
    """Test basic URL normalization."""
    result = normalize_dataplane_url("http://localhost:5555")
    assert result == "http://localhost:5555/v3"


def test_normalize_url_with_trailing_slash():
    """Test URL with trailing slash."""
    result = normalize_dataplane_url("http://localhost:5555/")
    assert result == "http://localhost:5555/v3"


def test_normalize_url_already_has_v3():
    """Test URL that already has /v3."""
    result = normalize_dataplane_url("http://localhost:5555/v3")
    assert result == "http://localhost:5555/v3"


def test_normalize_url_with_path():
    """Test URL with existing path."""
    result = normalize_dataplane_url("https://api.example.com/haproxy")
    assert result == "https://api.example.com/haproxy/v3"


def test_normalize_url_with_query_params():
    """Test URL with query parameters."""
    result = normalize_dataplane_url("http://localhost:5555?timeout=30")
    assert result == "http://localhost:5555/v3?timeout=30"


def test_normalize_url_with_path_and_query():
    """Test URL with both path and query parameters."""
    result = normalize_dataplane_url("https://api.example.com/haproxy?debug=true")
    assert result == "https://api.example.com/haproxy/v3?debug=true"
