"""
Unit tests for enhanced exception types in dataplane module.

Tests the enhanced DataplaneAPIError and ValidationError with context information.
"""

from haproxy_template_ic.dataplane import DataplaneAPIError, ValidationError


class TestDataplaneAPIError:
    """Test cases for DataplaneAPIError with enhanced context."""

    def test_basic_error_creation(self):
        """Test creating basic DataplaneAPIError."""
        error = DataplaneAPIError("Test error")
        assert str(error) == "Test error"
        assert error.endpoint is None
        assert error.operation is None
        assert error.original_error is None

    def test_error_with_context(self):
        """Test DataplaneAPIError with endpoint and operation context."""
        error = DataplaneAPIError(
            "Connection failed",
            endpoint="http://localhost:5555/v3",
            operation="get_version",
        )
        expected_str = "Connection failed [operation=get_version, endpoint=http://localhost:5555/v3]"
        assert str(error) == expected_str
        assert error.endpoint == "http://localhost:5555/v3"
        assert error.operation == "get_version"

    def test_error_with_original_exception(self):
        """Test DataplaneAPIError with original exception context."""
        original = ConnectionError("Network unreachable")
        error = DataplaneAPIError(
            "Failed to connect",
            endpoint="http://localhost:5555/v3",
            operation="deploy",
            original_error=original,
        )
        assert error.original_error is original
        assert "operation=deploy" in str(error)
        assert "endpoint=http://localhost:5555/v3" in str(error)

    def test_error_with_partial_context(self):
        """Test DataplaneAPIError with only some context fields."""
        error = DataplaneAPIError("Timeout", operation="validate")
        assert str(error) == "Timeout [operation=validate]"
        assert error.operation == "validate"
        assert error.endpoint is None


class TestValidationError:
    """Test cases for ValidationError with enhanced validation context."""

    def test_basic_validation_error(self):
        """Test creating basic ValidationError."""
        error = ValidationError("Config validation failed")
        assert "Config validation failed" in str(error)
        assert error.operation == "validate"  # Automatically set
        assert error.config_size is None
        assert error.validation_details is None

    def test_validation_error_with_context(self):
        """Test ValidationError with full validation context."""
        error = ValidationError(
            "Invalid HAProxy config",
            endpoint="http://localhost:5555/v3",
            config_size=1024,
            validation_details="line 15: unknown keyword 'invalid_option'",
        )
        error_str = str(error)
        assert "Invalid HAProxy config" in error_str
        assert "operation=validate" in error_str
        assert "endpoint=http://localhost:5555/v3" in error_str
        assert "config_size=1024" in error_str
        assert "details=line 15: unknown keyword 'invalid_option'" in error_str

    def test_validation_error_inheritance(self):
        """Test that ValidationError inherits from DataplaneAPIError."""
        error = ValidationError("Test validation error")
        assert isinstance(error, DataplaneAPIError)
        assert isinstance(error, ValidationError)

    def test_validation_error_with_original_exception(self):
        """Test ValidationError with original exception context."""
        original = RuntimeError("HAProxy validation process failed")
        error = ValidationError(
            "Validation process error",
            endpoint="http://localhost:5555/v3",
            config_size=512,
            original_error=original,
        )
        assert error.original_error is original
        assert error.config_size == 512
        assert "config_size=512" in str(error)

    def test_validation_error_empty_details(self):
        """Test ValidationError with empty validation details."""
        error = ValidationError(
            "Config failed validation", config_size=256, validation_details=""
        )
        # Empty details should not appear in string representation
        error_str = str(error)
        assert "config_size=256" in error_str
        assert "details=" not in error_str

    def test_validation_error_none_details(self):
        """Test ValidationError with None validation details."""
        error = ValidationError(
            "Config failed validation", config_size=256, validation_details=None
        )
        # None details should not appear in string representation
        error_str = str(error)
        assert "config_size=256" in error_str
        assert "details=" not in error_str
