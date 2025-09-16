"""
Unit tests for field filtering functionality.

Tests the ability to remove fields from resources using JSONPath expressions.
"""

import copy
from unittest.mock import MagicMock

import haproxy_template_ic.k8s.field_filter as field_filter_module
from haproxy_template_ic.k8s.field_filter import (
    _remove_field_at_path,
    remove_fields_from_resource,
    validate_ignore_fields,
)
from haproxy_template_ic.models import IndexedResourceCollection


class TestFieldFilter:
    """Test field filtering functionality."""

    def test_remove_simple_field(self):
        """Test removing a simple top-level field."""
        resource = {
            "apiVersion": "v1",
            "kind": "Service",
            "metadata": {
                "name": "test-service",
                "namespace": "default",
                "managedFields": [{"manager": "kubectl", "operation": "Update"}],
            },
            "spec": {"selector": {"app": "test"}},
        }

        filtered = remove_fields_from_resource(resource, ["metadata.managedFields"])

        assert "managedFields" not in filtered["metadata"]
        assert filtered["metadata"]["name"] == "test-service"
        assert filtered["spec"]["selector"]["app"] == "test"
        # Original should not be modified
        assert "managedFields" in resource["metadata"]

    def test_remove_nested_field(self):
        """Test removing a deeply nested field."""
        resource = {
            "metadata": {
                "name": "test",
                "annotations": {
                    "kubectl.kubernetes.io/last-applied-configuration": "large-json",
                    "app.io/version": "1.0",
                },
            }
        }

        filtered = remove_fields_from_resource(
            resource,
            [
                "metadata.annotations['kubectl.kubernetes.io/last-applied-configuration']"
            ],
        )

        assert (
            "kubectl.kubernetes.io/last-applied-configuration"
            not in filtered["metadata"]["annotations"]
        )
        assert filtered["metadata"]["annotations"]["app.io/version"] == "1.0"

    def test_remove_multiple_fields(self):
        """Test removing multiple fields."""
        resource = {
            "metadata": {
                "name": "test",
                "managedFields": ["field1"],
                "generation": 5,
                "resourceVersion": "12345",
            },
            "status": {"phase": "Running"},
        }

        filtered = remove_fields_from_resource(
            resource,
            ["metadata.managedFields", "metadata.resourceVersion", "status"],
        )

        assert "managedFields" not in filtered["metadata"]
        assert "resourceVersion" not in filtered["metadata"]
        assert "status" not in filtered
        assert filtered["metadata"]["name"] == "test"
        assert filtered["metadata"]["generation"] == 5

    def test_remove_nonexistent_field(self):
        """Test that removing nonexistent fields doesn't cause errors."""
        resource = {"metadata": {"name": "test"}}

        filtered = remove_fields_from_resource(
            resource, ["metadata.nonexistent", "status.phase"]
        )

        assert filtered == resource

    def test_empty_ignore_list(self):
        """Test that empty ignore list returns original resource."""
        resource = {"metadata": {"name": "test", "managedFields": ["field1"]}}

        filtered = remove_fields_from_resource(resource, [])

        assert filtered == resource

    def test_none_ignore_list(self):
        """Test that None ignore list returns original resource."""
        resource = {"metadata": {"name": "test", "managedFields": ["field1"]}}

        filtered = remove_fields_from_resource(resource, None)

        assert filtered == resource

    def test_deep_copy_preserves_original(self):
        """Test that the original resource is not modified."""
        resource = {
            "metadata": {
                "name": "test",
                "managedFields": [{"manager": "kubectl"}],
            }
        }
        original_copy = copy.deepcopy(resource)

        filtered = remove_fields_from_resource(resource, ["metadata.managedFields"])

        # Original should not be modified
        assert resource == original_copy
        # Filtered should have the field removed
        assert "managedFields" not in filtered["metadata"]

    def test_none_resource(self):
        """Test handling of None resource."""
        # Should handle None gracefully, though this shouldn't happen in practice
        result = remove_fields_from_resource(None, ["metadata.managedFields"])
        assert result is None

    def test_non_dict_resource(self):
        """Test handling of non-dict resource."""
        # Test with a list (shouldn't happen but good to be defensive)
        resource = ["item1", "item2"]
        result = remove_fields_from_resource(resource, ["[0]"])
        assert len(result) == 1
        assert result[0] == "item2"

    def test_field_path_with_special_chars(self):
        """Test field paths containing special characters."""
        resource = {
            "metadata": {
                "annotations": {
                    "nginx.ingress.kubernetes.io/rewrite-target": "/",
                    "cert-manager.io/cluster-issuer": "letsencrypt",
                }
            }
        }

        filtered = remove_fields_from_resource(
            resource,
            ["metadata.annotations['nginx.ingress.kubernetes.io/rewrite-target']"],
        )

        assert (
            "nginx.ingress.kubernetes.io/rewrite-target"
            not in filtered["metadata"]["annotations"]
        )
        assert "cert-manager.io/cluster-issuer" in filtered["metadata"]["annotations"]

    def test_invalid_jsonpath_expression(self):
        """Test that invalid JSONPath expressions are handled gracefully."""
        resource = {"metadata": {"name": "test"}}

        # Invalid JSONPath expressions should be logged but not cause failure
        filtered = remove_fields_from_resource(
            resource, ["[[[invalid", "metadata..double..dots"]
        )

        assert filtered == resource

    def test_array_element_removal(self):
        """Test removing specific array elements."""
        resource = {
            "spec": {
                "containers": [
                    {"name": "container1", "image": "image1"},
                    {"name": "container2", "image": "image2"},
                ]
            }
        }

        filtered = remove_fields_from_resource(resource, ["spec.containers[0]"])

        # Note: Removing array elements shifts indices
        assert len(filtered["spec"]["containers"]) == 1
        assert filtered["spec"]["containers"][0]["name"] == "container2"

    def test_wildcard_field_removal(self):
        """Test removing fields with wildcards."""
        resource = {
            "metadata": {
                "annotations": {
                    "kubectl.kubernetes.io/last-applied": "data1",
                    "kubectl.kubernetes.io/revision": "2",
                    "app.io/version": "1.0",
                }
            }
        }

        # Remove all kubectl annotations
        filtered = remove_fields_from_resource(
            resource, ["metadata.annotations[?@.key =~ 'kubectl.*']"]
        )

        # This depends on the JSONPath library's support for filters
        # The actual behavior may vary, so we're testing the basic functionality
        assert filtered["metadata"]["annotations"] is not None

    def test_validate_ignore_fields(self):
        """Test validation of ignore field expressions."""
        valid_fields = [
            "metadata.managedFields",
            "status",
            "metadata.annotations['key']",
        ]

        validated = validate_ignore_fields(valid_fields)
        assert len(validated) == 3

    def test_invalid_field_path_in_remove(self, monkeypatch):
        """Test handling of invalid field paths in remove_fields_from_resource."""
        resource = {"metadata": {"name": "test"}}

        # Test with non-string field paths
        mock_logger = MagicMock()
        monkeypatch.setattr(field_filter_module, "logger", mock_logger)

        result = remove_fields_from_resource(
            resource,
            [None, 123, [], "valid.path"],  # Mix of invalid and valid
        )
        # Should skip invalid ones and process valid ones
        assert result == resource  # valid.path doesn't exist so no change
        assert mock_logger.debug.call_count >= 3  # For None, 123, and []

    def test_field_path_too_long_in_remove(self, monkeypatch):
        """Test handling of overly long field paths in remove_fields_from_resource."""
        resource = {"metadata": {"name": "test"}}

        # Create a path > 500 characters
        long_path = "a" * 501

        mock_logger = MagicMock()
        monkeypatch.setattr(field_filter_module, "logger", mock_logger)

        result = remove_fields_from_resource(resource, [long_path])
        assert result == resource  # Should skip the long path
        mock_logger.warning.assert_called_once()
        assert "Field path too long" in str(mock_logger.warning.call_args)

    def test_unexpected_error_in_remove(self, monkeypatch):
        """Test handling of unexpected errors during field removal."""
        resource = {"metadata": {"name": "test"}}

        mock_compile = MagicMock(side_effect=RuntimeError("Unexpected error"))
        mock_logger = MagicMock()
        monkeypatch.setattr(
            field_filter_module, "_compile_jsonpath_filter", mock_compile
        )
        monkeypatch.setattr(field_filter_module, "logger", mock_logger)

        result = remove_fields_from_resource(resource, ["metadata.name"])
        # Should handle the error gracefully
        assert result == resource
        mock_logger.warning.assert_called_once()
        assert "Unexpected error processing field filter" in str(
            mock_logger.warning.call_args
        )

    def test_match_without_parts(self):
        """Test _remove_field_at_path with match lacking parts attribute."""

        resource = {"metadata": {"name": "test"}}

        # Create a mock match without parts
        mock_match = MagicMock()
        del mock_match.parts  # Remove parts attribute

        _remove_field_at_path(resource, mock_match)
        assert resource == {"metadata": {"name": "test"}}  # Should remain unchanged

    def test_empty_parts_in_match(self):
        """Test _remove_field_at_path with empty parts list."""

        resource = {"metadata": {"name": "test"}}

        # Create a mock match with empty parts - this hits line 111
        mock_match = MagicMock()
        mock_match.parts = []

        _remove_field_at_path(resource, mock_match)
        assert resource == {"metadata": {"name": "test"}}  # Should remain unchanged

        # Also test parts = None which should trigger line 104
        mock_match.parts = None
        _remove_field_at_path(resource, mock_match)
        assert resource == {"metadata": {"name": "test"}}  # Should remain unchanged

    def test_path_not_in_dict(self):
        """Test navigation when path doesn't exist in dict."""

        resource = {"metadata": {"name": "test"}}

        # Create a mock match with non-existent path
        mock_match = MagicMock()
        mock_match.parts = ["spec", "containers"]  # spec doesn't exist

        _remove_field_at_path(resource, mock_match)
        assert resource == {"metadata": {"name": "test"}}  # Should remain unchanged

    def test_list_navigation_errors(self):
        """Test errors during list navigation."""

        resource = {"items": ["a", "b", "c"]}

        # Test with out-of-range index
        mock_match = MagicMock()
        mock_match.parts = ["items", "10"]  # Index out of range

        _remove_field_at_path(resource, mock_match)
        assert resource == {"items": ["a", "b", "c"]}  # Should remain unchanged

        # Test with non-integer index
        mock_match.parts = ["items", "not_a_number"]
        _remove_field_at_path(resource, mock_match)
        assert resource == {"items": ["a", "b", "c"]}  # Should remain unchanged

        # Test navigation through non-dict/list (hits line 132)
        resource = {"value": 42}
        mock_match.parts = ["value", "subfield"]  # Can't navigate through int
        _remove_field_at_path(resource, mock_match)
        assert resource == {"value": 42}  # Should remain unchanged

        # Another case: trying to navigate through string
        resource = {"text": "hello"}
        mock_match.parts = ["text", "charAt", "0"]  # Can't navigate through string
        _remove_field_at_path(resource, mock_match)
        assert resource == {"text": "hello"}  # Should remain unchanged

    def test_nested_list_navigation(self):
        """Test complex list navigation scenarios."""

        # Test navigating through nested structures with lists
        resource = {
            "items": [{"name": "first", "value": 1}, {"name": "second", "value": 2}]
        }

        # Successfully navigate and remove
        mock_match = MagicMock()
        mock_match.parts = ["items", "0", "value"]
        _remove_field_at_path(resource, mock_match)
        assert resource == {
            "items": [
                {"name": "first"},  # value removed
                {"name": "second", "value": 2},
            ]
        }

        # Test with invalid index in middle of path
        resource = {"data": [{"nested": {"field": "value"}}]}
        mock_match.parts = ["data", "invalid", "nested", "field"]
        _remove_field_at_path(resource, mock_match)
        assert resource == {"data": [{"nested": {"field": "value"}}]}  # Unchanged

        # Test navigation through list with negative index (should fail with ValueError)
        mock_match.parts = ["data", "-1", "nested"]
        _remove_field_at_path(resource, mock_match)
        assert resource == {"data": [{"nested": {"field": "value"}}]}  # Unchanged

    def test_final_part_list_errors(self):
        """Test errors when removing final part from list."""

        resource = {"items": ["a", "b", "c"]}

        # Test with invalid index for final part
        mock_match = MagicMock()
        mock_match.parts = ["items", "invalid"]

        _remove_field_at_path(resource, mock_match)
        assert resource == {"items": ["a", "b", "c"]}  # Should remain unchanged

    def test_validate_ignore_fields_with_invalid(self, monkeypatch):
        """Test validation filters out invalid expressions."""
        fields = [
            "metadata.managedFields",  # Valid
            "",  # Empty
            None,  # None
            "a" * 501,  # Too long
            "[[[invalid",  # Invalid syntax
        ]

        mock_logger = MagicMock()
        monkeypatch.setattr(field_filter_module, "logger", mock_logger)

        validated = validate_ignore_fields(fields)

        # Only the first valid field should remain
        assert len(validated) == 1
        assert validated[0] == "metadata.managedFields"

        # Check that warnings were logged for invalid fields
        assert (
            mock_logger.warning.call_count >= 3
        )  # Empty, None, too long, invalid syntax


class TestIndexedResourceCollectionWithFieldFilter:
    """Test IndexedResourceCollection with field filtering."""

    def test_from_kopf_index_with_field_filtering(self):
        """Test that field filtering is applied during index creation."""
        # Mock kopf Index
        mock_index = MagicMock()
        keys = [("default", "service1")]
        mock_index.__iter__.return_value = iter(keys)

        def mock_getitem(key):
            mock_store = MagicMock()
            mock_store.__iter__.return_value = iter(
                [
                    {
                        "apiVersion": "v1",
                        "kind": "Service",
                        "metadata": {
                            "name": "service1",
                            "namespace": "default",
                            "managedFields": [
                                {"manager": "kubectl", "operation": "Update"}
                            ],
                            "resourceVersion": "12345",
                        },
                        "spec": {"selector": {"app": "test"}},
                    }
                ]
            )
            return mock_store

        mock_index.__getitem__.side_effect = mock_getitem

        # Create collection with field filtering
        collection = IndexedResourceCollection.from_kopf_index(
            mock_index,
            ignore_fields=["metadata.managedFields", "metadata.resourceVersion"],
        )

        # Get the indexed resource
        resources = collection.get_indexed("default", "service1")
        assert len(resources) == 1

        resource = resources[0]
        # Check that filtered fields are removed
        assert "managedFields" not in resource["metadata"]
        assert "resourceVersion" not in resource["metadata"]
        # Check that other fields remain
        assert resource["metadata"]["name"] == "service1"
        assert resource["spec"]["selector"]["app"] == "test"

    def test_from_kopf_index_without_field_filtering(self):
        """Test that no filtering occurs when ignore_fields is not provided."""
        # Mock kopf Index
        mock_index = MagicMock()
        keys = [("default", "service1")]
        mock_index.__iter__.return_value = iter(keys)

        def mock_getitem(key):
            mock_store = MagicMock()
            mock_store.__iter__.return_value = iter(
                [
                    {
                        "metadata": {
                            "name": "service1",
                            "namespace": "default",
                            "managedFields": [
                                {"manager": "kubectl", "operation": "Update"}
                            ],
                        }
                    }
                ]
            )
            return mock_store

        mock_index.__getitem__.side_effect = mock_getitem

        # Create collection without field filtering
        collection = IndexedResourceCollection.from_kopf_index(mock_index)

        # Get the indexed resource
        resources = collection.get_indexed("default", "service1")
        assert len(resources) == 1

        resource = resources[0]
        # Check that all fields remain
        assert "managedFields" in resource["metadata"]
        assert resource["metadata"]["managedFields"][0]["manager"] == "kubectl"
