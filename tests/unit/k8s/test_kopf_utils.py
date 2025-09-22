"""
Tests for kopf_utils module.
"""

import pytest

from haproxy_template_ic.k8s.kopf_utils import (
    normalize_kopf_resource,
    is_valid_kubernetes_resource,
)
from tests.unit.conftest import (
    create_k8s_pod_resource,
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


def test_mock_contains_method():
    """Test __contains__ method works correctly."""
    test_data = {"metadata": {"name": "test-pod"}, "status": {"phase": "Running"}}
    mock_body = MockKopfBody(test_data)

    assert "metadata" in mock_body
    assert "status" in mock_body
    assert "nonexistent" not in mock_body


def test_mock_get_method():
    """Test get method works correctly."""
    test_data = {"metadata": {"name": "test-pod"}, "status": {"phase": "Running"}}
    mock_body = MockKopfBody(test_data)

    assert mock_body.get("metadata") == {"name": "test-pod"}
    assert mock_body.get("status") == {"phase": "Running"}
    assert mock_body.get("nonexistent") is None
    assert mock_body.get("nonexistent", "default") == "default"


def test_normalize_regular_dict():
    """Test normalizing a regular dictionary."""
    test_dict = {"metadata": {"name": "test-pod"}, "status": {"phase": "Running"}}
    result = normalize_kopf_resource(test_dict)
    assert result == test_dict  # Should have the same content


def test_normalize_body_object():
    """Test normalizing a Body-like object."""
    test_data = {"metadata": {"name": "test-pod"}}
    mock_body = MockKopfBody(test_data)

    result = normalize_kopf_resource(mock_body)
    assert result == test_data


def test_normalize_object_with_items():
    """Test normalizing an object with items() method."""
    test_data = {"metadata": {"name": "test-pod"}}
    mock_body = MockKopfBody(test_data)

    result = normalize_kopf_resource(mock_body)
    assert result == test_data


def test_normalize_unsupported_object():
    """Test failure when object cannot be normalized."""
    unsupported = "just a string"

    with pytest.raises(ValueError):  # dict() will raise ValueError for string
        normalize_kopf_resource(unsupported)


def test_normalize_object_conversion_fails():
    """Test failure when Body object conversion fails."""

    # Create an object that appears convertible but fails
    class BadConvertible:
        def __getitem__(self, key):
            return None

        def keys(self):
            raise RuntimeError("Conversion failed")

    bad_obj = BadConvertible()
    with pytest.raises(RuntimeError, match="Conversion failed"):
        normalize_kopf_resource(bad_obj)


def test_valid_resource():
    """Test a valid Kubernetes resource."""
    resource = create_k8s_pod_resource(
        name="test-pod", namespace="default", phase="Running"
    )
    assert is_valid_kubernetes_resource(resource) is True


def test_valid_minimal_resource():
    """Test a minimal valid resource."""
    resource = create_k8s_pod_resource(name="test-pod", phase=None)
    assert is_valid_kubernetes_resource(resource) is True


def test_invalid_not_dict():
    """Test non-dict input."""
    assert is_valid_kubernetes_resource("not a dict") is False
    assert is_valid_kubernetes_resource(None) is False
    assert is_valid_kubernetes_resource([]) is False


def test_invalid_no_api_version():
    """Test resource without apiVersion."""
    resource = {"kind": "Pod", "metadata": {"name": "test-pod"}}
    assert is_valid_kubernetes_resource(resource) is False


def test_invalid_empty_api_version():
    """Test resource with empty apiVersion."""
    resource = {"apiVersion": "", "kind": "Pod", "metadata": {"name": "test-pod"}}
    assert is_valid_kubernetes_resource(resource) is False


def test_invalid_whitespace_api_version():
    """Test resource with whitespace-only apiVersion."""
    resource = {
        "apiVersion": "   ",
        "kind": "Pod",
        "metadata": {"name": "test-pod"},
    }
    assert is_valid_kubernetes_resource(resource) is False


def test_invalid_non_string_api_version():
    """Test resource with non-string apiVersion."""
    resource = {"apiVersion": 123, "kind": "Pod", "metadata": {"name": "test-pod"}}
    assert is_valid_kubernetes_resource(resource) is False


def test_invalid_no_kind():
    """Test resource without kind."""
    resource = {"apiVersion": "v1", "metadata": {"name": "test-pod"}}
    assert is_valid_kubernetes_resource(resource) is False


def test_invalid_empty_kind():
    """Test resource with empty kind."""
    resource = {"apiVersion": "v1", "kind": "", "metadata": {"name": "test-pod"}}
    assert is_valid_kubernetes_resource(resource) is False


def test_invalid_whitespace_kind():
    """Test resource with whitespace-only kind."""
    resource = {"apiVersion": "v1", "kind": "   ", "metadata": {"name": "test-pod"}}
    assert is_valid_kubernetes_resource(resource) is False


def test_invalid_non_string_kind():
    """Test resource with non-string kind."""
    resource = {"apiVersion": "v1", "kind": 123, "metadata": {"name": "test-pod"}}
    assert is_valid_kubernetes_resource(resource) is False


def test_invalid_no_metadata():
    """Test resource without metadata."""
    resource = {"apiVersion": "v1", "kind": "Pod", "status": {"phase": "Running"}}
    assert is_valid_kubernetes_resource(resource) is False


def test_invalid_metadata_not_dict():
    """Test resource with non-dict metadata."""
    resource = {"apiVersion": "v1", "kind": "Pod", "metadata": "not a dict"}
    assert is_valid_kubernetes_resource(resource) is False


def test_invalid_no_name():
    """Test resource without name."""
    resource = {
        "apiVersion": "v1",
        "kind": "Pod",
        "metadata": {"namespace": "default"},
    }
    assert is_valid_kubernetes_resource(resource) is False


def test_invalid_empty_name():
    """Test resource with empty name."""
    resource = {"apiVersion": "v1", "kind": "Pod", "metadata": {"name": ""}}
    assert is_valid_kubernetes_resource(resource) is False


def test_invalid_whitespace_name():
    """Test resource with whitespace-only name."""
    resource = {"apiVersion": "v1", "kind": "Pod", "metadata": {"name": "   "}}
    assert is_valid_kubernetes_resource(resource) is False


def test_invalid_non_string_name():
    """Test resource with non-string name."""
    resource = {"apiVersion": "v1", "kind": "Pod", "metadata": {"name": 123}}
    assert is_valid_kubernetes_resource(resource) is False
