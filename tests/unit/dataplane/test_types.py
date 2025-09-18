"""
Unit tests for dataplane types, error classes, and utility functions.

Tests DataplaneAPIError, ValidationError, and type-related functionality.
"""

from haproxy_template_ic.dataplane import DataplaneAPIError, ValidationError


def test_basic_error_creation():
    """Test creating basic DataplaneAPIError."""
    error = DataplaneAPIError("Test error")
    assert str(error) == "Test error"
    assert error.endpoint is None
    assert error.operation is None
    assert error.original_error is None


def test_error_with_context():
    """Test DataplaneAPIError with endpoint and operation context."""
    error = DataplaneAPIError(
        "Connection failed",
        endpoint="http://localhost:5555/v3",
        operation="get_version",
    )
    expected_str = (
        "Connection failed [operation=get_version, endpoint=http://localhost:5555/v3]"
    )
    assert str(error) == expected_str
    assert error.endpoint == "http://localhost:5555/v3"
    assert error.operation == "get_version"


def test_error_with_partial_context():
    """Test DataplaneAPIError with only some context fields."""
    error = DataplaneAPIError(
        "Timeout occurred",
        endpoint="http://localhost:5555/v3",
    )
    expected_str = "Timeout occurred [endpoint=http://localhost:5555/v3]"
    assert str(error) == expected_str
    assert error.endpoint == "http://localhost:5555/v3"
    assert error.operation is None


def test_error_with_original_exception():
    """Test DataplaneAPIError with original exception context."""
    original = ValueError("Invalid input")
    error = DataplaneAPIError(
        "Processing failed",
        endpoint="http://localhost:5555/v3",
        operation="validate",
        original_error=original,
    )
    expected_str = (
        "Processing failed [operation=validate, endpoint=http://localhost:5555/v3]"
    )
    assert str(error) == expected_str
    assert error.original_error is original


def test_validation_error_inheritance():
    """Test ValidationError inherits from DataplaneAPIError."""
    error = ValidationError("Validation failed")
    assert isinstance(error, DataplaneAPIError)


def test_basic_validation_error():
    """Test basic ValidationError functionality."""
    error = ValidationError("Config validation failed")
    assert isinstance(error, DataplaneAPIError)
    assert "Config validation failed" in str(error)


def test_validation_error_with_context():
    """Test ValidationError with endpoint context."""
    error = ValidationError(
        "Invalid backend configuration",
        endpoint="http://localhost:5555/v3",
    )
    expected_str = "Invalid backend configuration [operation=validate, endpoint=http://localhost:5555/v3]"
    assert str(error) == expected_str
    assert error.endpoint == "http://localhost:5555/v3"


def test_validation_error_with_original_exception():
    """Test ValidationError with original exception."""
    original = KeyError("missing_key")
    error = ValidationError(
        "Configuration key missing",
        endpoint="http://localhost:5555/v3",
        original_error=original,
    )
    assert error.original_error is original


def test_validation_error_none_details():
    """Test ValidationError with None validation details."""
    error = ValidationError(
        "Validation failed",
        endpoint="http://localhost:5555/v3",
        validation_details=None,
    )
    assert "Validation failed" in str(error)


def test_validation_error_empty_details():
    """Test ValidationError with empty validation details."""
    error = ValidationError(
        "Validation failed",
        endpoint="http://localhost:5555/v3",
        validation_details="",
    )
    assert "Validation failed" in str(error)
