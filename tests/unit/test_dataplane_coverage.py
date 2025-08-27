"""
Additional tests to improve coverage for dataplane.py module.

These tests focus on utility functions and edge cases that may not be covered
by the main integration tests.
"""

import pytest
from unittest.mock import Mock
from haproxy_template_ic.dataplane import (
    extract_hash_from_description,
    parse_haproxy_error_line,
    extract_config_context,
    parse_validation_error_details,
    DataplaneClient,
    ValidationError,
    DataplaneAPIError,
)


class TestUtilityFunctions:
    """Test utility functions for better coverage."""

    def test_extract_hash_from_description_with_hash(self):
        """Test extracting hash from description with valid hash."""
        assert extract_hash_from_description("xxh64:abc123def") == "xxh64:abc123def"
        assert extract_hash_from_description("sha256:def456ghi") == "sha256:def456ghi"
        assert extract_hash_from_description("md5:ghi789jkl") == "md5:ghi789jkl"

    def test_extract_hash_from_description_with_additional_text(self):
        """Test extracting hash when there's additional text after the hash."""
        assert (
            extract_hash_from_description("xxh64:abc123 some additional text")
            == "xxh64:abc123"
        )

    def test_extract_hash_from_description_no_hash(self):
        """Test extracting hash from description without hash."""
        assert extract_hash_from_description("no hash here") is None
        assert extract_hash_from_description("") is None
        assert extract_hash_from_description(None) is None

    def test_extract_hash_from_description_invalid_input(self):
        """Test extracting hash with invalid input types."""
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


class TestDataplaneClientAdvanced:
    """Test DataplaneClient advanced functionality."""

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


class TestExceptionClasses:
    """Test custom exception classes."""

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
