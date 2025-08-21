"""
Tests for kopf_utils module.
"""

import pytest
from unittest.mock import MagicMock, patch

from haproxy_template_ic.kopf_utils import (
    convert_kopf_body_to_dict,
    normalize_kopf_resource,
    is_valid_kubernetes_resource,
)


class MockKopfBody:
    """Mock Kopf Body object for testing."""

    def __init__(self, data):
        self._data = data

    def __getitem__(self, key):
        return self._data[key]

    def __iter__(self):
        return iter(self._data)

    def __contains__(self, key):
        return key in self._data

    def keys(self):
        return self._data.keys()

    def items(self):
        return self._data.items()

    def get(self, key, default=None):
        return self._data.get(key, default)


class TestMockKopfBody:
    """Test MockKopfBody functionality."""

    def test_mock_contains_method(self):
        """Test __contains__ method works correctly."""
        test_data = {"metadata": {"name": "test-pod"}, "status": {"phase": "Running"}}
        mock_body = MockKopfBody(test_data)

        assert "metadata" in mock_body
        assert "status" in mock_body
        assert "nonexistent" not in mock_body

    def test_mock_get_method(self):
        """Test get method works correctly."""
        test_data = {"metadata": {"name": "test-pod"}, "status": {"phase": "Running"}}
        mock_body = MockKopfBody(test_data)

        assert mock_body.get("metadata") == {"name": "test-pod"}
        assert mock_body.get("status") == {"phase": "Running"}
        assert mock_body.get("nonexistent") is None
        assert mock_body.get("nonexistent", "default") == "default"


class TestConvertKopfBodyToDict:
    """Test convert_kopf_body_to_dict function."""

    def test_convert_dict_convertible_object(self):
        """Test converting an object that supports dict() conversion."""
        test_data = {"metadata": {"name": "test-pod"}, "status": {"phase": "Running"}}
        mock_body = MockKopfBody(test_data)

        result = convert_kopf_body_to_dict(mock_body)
        assert result == test_data

    def test_convert_regular_dict(self):
        """Test converting a regular dictionary."""
        test_dict = {"metadata": {"name": "test-pod"}}
        result = convert_kopf_body_to_dict(test_dict)
        assert result == test_dict

    def test_convert_failure(self):
        """Test failure when object cannot be converted."""
        mock_body = MagicMock()

        # Mock dict() to raise an exception
        with patch("builtins.dict", side_effect=TypeError("Cannot convert")):
            with pytest.raises(ValueError, match="Cannot convert Body object to dict"):
                convert_kopf_body_to_dict(mock_body)

    def test_convert_non_dict_result(self):
        """Test failure when dict() returns non-dict."""

        # Create an object that dict() can call but doesn't produce a dict
        class BadDictConvertible:
            def keys(self):
                return "not iterable"  # This will cause dict() to fail

        bad_obj = BadDictConvertible()
        with pytest.raises(ValueError, match="Cannot convert Body object to dict"):
            convert_kopf_body_to_dict(bad_obj)


class TestNormalizeKopfResource:
    """Test normalize_kopf_resource function."""

    def test_normalize_regular_dict(self):
        """Test normalizing a regular dictionary passes through unchanged."""
        test_dict = {"metadata": {"name": "test-pod"}, "status": {"phase": "Running"}}
        result = normalize_kopf_resource(test_dict)
        assert result is test_dict  # Should be the same object

    def test_normalize_body_object(self):
        """Test normalizing a Body-like object."""
        test_data = {"metadata": {"name": "test-pod"}}
        mock_body = MockKopfBody(test_data)

        result = normalize_kopf_resource(mock_body)
        assert result == test_data

    def test_normalize_object_with_items(self):
        """Test normalizing an object with items() method."""
        test_data = {"metadata": {"name": "test-pod"}}
        mock_body = MockKopfBody(test_data)

        result = normalize_kopf_resource(mock_body)
        assert result == test_data

    def test_normalize_unsupported_object(self):
        """Test failure when object cannot be normalized."""
        unsupported = "just a string"

        with pytest.raises(
            ValueError, match="Cannot normalize resource of type.*to dictionary"
        ):
            normalize_kopf_resource(unsupported)

    def test_normalize_object_conversion_fails(self):
        """Test failure when Body object conversion fails."""

        # Create an object that appears convertible but fails
        class BadConvertible:
            def __getitem__(self, key):
                return None

            def keys(self):
                raise RuntimeError("Conversion failed")

        bad_obj = BadConvertible()
        with pytest.raises(
            ValueError, match="Cannot normalize resource of type.*to dictionary"
        ):
            normalize_kopf_resource(bad_obj)


class TestIsValidKubernetesResource:
    """Test is_valid_kubernetes_resource function."""

    def test_valid_resource(self):
        """Test a valid Kubernetes resource."""
        resource = {
            "apiVersion": "v1",
            "kind": "Pod",
            "metadata": {"name": "test-pod", "namespace": "default"},
            "status": {"phase": "Running"},
        }
        assert is_valid_kubernetes_resource(resource) is True

    def test_valid_minimal_resource(self):
        """Test a minimal valid resource."""
        resource = {"apiVersion": "v1", "kind": "Pod", "metadata": {"name": "test-pod"}}
        assert is_valid_kubernetes_resource(resource) is True

    def test_invalid_not_dict(self):
        """Test non-dict input."""
        assert is_valid_kubernetes_resource("not a dict") is False
        assert is_valid_kubernetes_resource(None) is False
        assert is_valid_kubernetes_resource([]) is False

    def test_invalid_no_api_version(self):
        """Test resource without apiVersion."""
        resource = {"kind": "Pod", "metadata": {"name": "test-pod"}}
        assert is_valid_kubernetes_resource(resource) is False

    def test_invalid_empty_api_version(self):
        """Test resource with empty apiVersion."""
        resource = {"apiVersion": "", "kind": "Pod", "metadata": {"name": "test-pod"}}
        assert is_valid_kubernetes_resource(resource) is False

    def test_invalid_whitespace_api_version(self):
        """Test resource with whitespace-only apiVersion."""
        resource = {
            "apiVersion": "   ",
            "kind": "Pod",
            "metadata": {"name": "test-pod"},
        }
        assert is_valid_kubernetes_resource(resource) is False

    def test_invalid_non_string_api_version(self):
        """Test resource with non-string apiVersion."""
        resource = {"apiVersion": 123, "kind": "Pod", "metadata": {"name": "test-pod"}}
        assert is_valid_kubernetes_resource(resource) is False

    def test_invalid_no_kind(self):
        """Test resource without kind."""
        resource = {"apiVersion": "v1", "metadata": {"name": "test-pod"}}
        assert is_valid_kubernetes_resource(resource) is False

    def test_invalid_empty_kind(self):
        """Test resource with empty kind."""
        resource = {"apiVersion": "v1", "kind": "", "metadata": {"name": "test-pod"}}
        assert is_valid_kubernetes_resource(resource) is False

    def test_invalid_whitespace_kind(self):
        """Test resource with whitespace-only kind."""
        resource = {"apiVersion": "v1", "kind": "   ", "metadata": {"name": "test-pod"}}
        assert is_valid_kubernetes_resource(resource) is False

    def test_invalid_non_string_kind(self):
        """Test resource with non-string kind."""
        resource = {"apiVersion": "v1", "kind": 123, "metadata": {"name": "test-pod"}}
        assert is_valid_kubernetes_resource(resource) is False

    def test_invalid_no_metadata(self):
        """Test resource without metadata."""
        resource = {"apiVersion": "v1", "kind": "Pod", "status": {"phase": "Running"}}
        assert is_valid_kubernetes_resource(resource) is False

    def test_invalid_metadata_not_dict(self):
        """Test resource with non-dict metadata."""
        resource = {"apiVersion": "v1", "kind": "Pod", "metadata": "not a dict"}
        assert is_valid_kubernetes_resource(resource) is False

    def test_invalid_no_name(self):
        """Test resource without name."""
        resource = {
            "apiVersion": "v1",
            "kind": "Pod",
            "metadata": {"namespace": "default"},
        }
        assert is_valid_kubernetes_resource(resource) is False

    def test_invalid_empty_name(self):
        """Test resource with empty name."""
        resource = {"apiVersion": "v1", "kind": "Pod", "metadata": {"name": ""}}
        assert is_valid_kubernetes_resource(resource) is False

    def test_invalid_whitespace_name(self):
        """Test resource with whitespace-only name."""
        resource = {"apiVersion": "v1", "kind": "Pod", "metadata": {"name": "   "}}
        assert is_valid_kubernetes_resource(resource) is False

    def test_invalid_non_string_name(self):
        """Test resource with non-string name."""
        resource = {"apiVersion": "v1", "kind": "Pod", "metadata": {"name": 123}}
        assert is_valid_kubernetes_resource(resource) is False
