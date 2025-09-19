"""
Unit tests for dataplane types, error classes, and utility functions.

Tests DataplaneAPIError, ValidationError, result types, and type-related functionality.
"""

from haproxy_template_ic.dataplane import DataplaneAPIError, ValidationError
from haproxy_template_ic.dataplane.types import (
    CreateOperationResult,
    UpdateOperationResult,
    DeleteOperationResult,
    ReloadInfo,
)


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


# ===== OPERATION RESULT TYPES TESTS =====


def test_create_operation_result_basic():
    """Test CreateOperationResult with empty ReloadInfo."""
    reload_info = ReloadInfo()
    result = CreateOperationResult(reload_info=reload_info)

    assert result.reload_info is reload_info
    assert not result.reload_info.reload_triggered


def test_create_operation_result_with_reload():
    """Test CreateOperationResult with reload information."""
    reload_info = ReloadInfo(reload_id="reload-123")
    result = CreateOperationResult(reload_info=reload_info)

    assert result.reload_info is reload_info
    assert result.reload_info.reload_triggered
    assert result.reload_info.reload_id == "reload-123"


def test_update_operation_result_no_change():
    """Test UpdateOperationResult with no content change."""
    reload_info = ReloadInfo()
    result = UpdateOperationResult(content_changed=False, reload_info=reload_info)

    assert not result.content_changed
    assert result.reload_info is reload_info
    assert not result.reload_info.reload_triggered


def test_update_operation_result_with_change():
    """Test UpdateOperationResult with content change and reload."""
    reload_info = ReloadInfo(reload_id="reload-456")
    result = UpdateOperationResult(content_changed=True, reload_info=reload_info)

    assert result.content_changed
    assert result.reload_info is reload_info
    assert result.reload_info.reload_triggered
    assert result.reload_info.reload_id == "reload-456"


def test_delete_operation_result_basic():
    """Test DeleteOperationResult with empty ReloadInfo."""
    reload_info = ReloadInfo()
    result = DeleteOperationResult(reload_info=reload_info)

    assert result.reload_info is reload_info
    assert not result.reload_info.reload_triggered


def test_delete_operation_result_with_reload():
    """Test DeleteOperationResult with reload information."""
    reload_info = ReloadInfo(reload_id="reload-789")
    result = DeleteOperationResult(reload_info=reload_info)

    assert result.reload_info is reload_info
    assert result.reload_info.reload_triggered
    assert result.reload_info.reload_id == "reload-789"


def test_result_types_are_dataclasses():
    """Test that all result types are properly defined as dataclasses."""
    reload_info = ReloadInfo()

    # Test that they can be created with keyword arguments
    create_result = CreateOperationResult(reload_info=reload_info)
    update_result = UpdateOperationResult(content_changed=True, reload_info=reload_info)
    delete_result = DeleteOperationResult(reload_info=reload_info)

    # Test that they have the expected attributes
    assert hasattr(create_result, "reload_info")
    assert hasattr(update_result, "content_changed")
    assert hasattr(update_result, "reload_info")
    assert hasattr(delete_result, "reload_info")

    # Test equality (dataclass generates __eq__ automatically)
    create_result2 = CreateOperationResult(reload_info=reload_info)
    assert create_result == create_result2
