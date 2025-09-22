"""
Unit tests for haproxy_template_ic.k8s.resource_utils module.

Comprehensive test coverage for Kubernetes resource utilities including
namespace detection, JSONPath compilation, field extraction, and resource validation.
"""

import os
import tempfile
import pytest
from unittest.mock import Mock, mock_open, patch

from jsonpath.exceptions import JSONPathError

from haproxy_template_ic.k8s.resource_utils import (
    _compile_jsonpath,
    _is_valid_dict_resource,
    _is_valid_resource,
    extract_nested_field,
    get_current_namespace,
)


class TestGetCurrentNamespace:
    """Test namespace detection functionality."""

    def test_get_current_namespace_from_environment(self):
        """Test namespace detection from environment variable."""
        # Arrange & Act & Assert
        with patch.dict(os.environ, {"KUBERNETES_NAMESPACE": "test-namespace"}):
            result = get_current_namespace()
            assert result == "test-namespace"

    def test_get_current_namespace_from_service_account_file(self):
        """Test namespace detection from service account file."""
        # Arrange
        namespace_content = "production-namespace"

        with (
            patch.dict(os.environ, {}, clear=True),
            patch("os.path.exists") as mock_exists,
            patch("builtins.open", mock_open(read_data=namespace_content)) as mock_file,
        ):
            mock_exists.return_value = True

            # Act
            result = get_current_namespace()

        # Assert
        assert result == "production-namespace"
        mock_exists.assert_called_once_with(
            "/var/run/secrets/kubernetes.io/serviceaccount/namespace"
        )
        mock_file.assert_called_once_with(
            "/var/run/secrets/kubernetes.io/serviceaccount/namespace", "r"
        )

    def test_get_current_namespace_service_account_file_with_whitespace(self):
        """Test namespace detection from service account file with whitespace."""
        # Arrange
        namespace_content = "  staging-namespace  \n"

        with (
            patch.dict(os.environ, {}, clear=True),
            patch("os.path.exists") as mock_exists,
            patch("builtins.open", mock_open(read_data=namespace_content)),
        ):
            mock_exists.return_value = True

            # Act
            result = get_current_namespace()

        # Assert
        assert result == "staging-namespace"

    def test_get_current_namespace_service_account_file_empty(self):
        """Test namespace detection when service account file is empty."""
        # Arrange
        namespace_content = ""

        with (
            patch.dict(os.environ, {}, clear=True),
            patch("os.path.exists") as mock_exists,
            patch("builtins.open", mock_open(read_data=namespace_content)),
        ):
            mock_exists.return_value = True

            # Act
            result = get_current_namespace()

        # Assert
        assert result == "default"

    def test_get_current_namespace_service_account_file_whitespace_only(self):
        """Test namespace detection when service account file contains only whitespace."""
        # Arrange
        namespace_content = "   \n\t  "

        with (
            patch.dict(os.environ, {}, clear=True),
            patch("os.path.exists") as mock_exists,
            patch("builtins.open", mock_open(read_data=namespace_content)),
        ):
            mock_exists.return_value = True

            # Act
            result = get_current_namespace()

        # Assert
        assert result == "default"

    def test_get_current_namespace_file_not_exists(self):
        """Test namespace detection when service account file doesn't exist."""
        # Arrange & Act & Assert
        with (
            patch.dict(os.environ, {}, clear=True),
            patch("os.path.exists") as mock_exists,
        ):
            mock_exists.return_value = False

            result = get_current_namespace()

        assert result == "default"
        mock_exists.assert_called_once_with(
            "/var/run/secrets/kubernetes.io/serviceaccount/namespace"
        )

    def test_get_current_namespace_file_read_error(self):
        """Test namespace detection when file read fails."""
        # Arrange
        with (
            patch.dict(os.environ, {}, clear=True),
            patch("os.path.exists") as mock_exists,
            patch("builtins.open") as mock_file,
            patch("haproxy_template_ic.k8s.resource_utils.logger") as mock_logger,
        ):
            mock_exists.return_value = True
            mock_file.side_effect = OSError("Permission denied")

            # Act
            result = get_current_namespace()

        # Assert
        assert result == "default"
        mock_logger.warning.assert_called_once_with(
            "Failed to read namespace from /var/run/secrets/kubernetes.io/serviceaccount/namespace: Permission denied"
        )

    def test_get_current_namespace_environment_takes_precedence(self):
        """Test that environment variable takes precedence over file."""
        # Arrange
        with (
            patch.dict(os.environ, {"KUBERNETES_NAMESPACE": "env-namespace"}),
            patch("os.path.exists") as mock_exists,
            patch("builtins.open", mock_open(read_data="file-namespace")),
        ):
            mock_exists.return_value = True

            # Act
            result = get_current_namespace()

        # Assert
        assert result == "env-namespace"
        # File should not be checked when env var is set
        mock_exists.assert_not_called()

    def test_get_current_namespace_unicode_handling(self):
        """Test namespace detection with unicode characters."""
        # Arrange
        namespace_content = "测试-namespace"

        with (
            patch.dict(os.environ, {}, clear=True),
            patch("os.path.exists") as mock_exists,
            patch("builtins.open", mock_open(read_data=namespace_content)),
        ):
            mock_exists.return_value = True

            # Act
            result = get_current_namespace()

        # Assert
        assert result == "测试-namespace"


class TestCompileJsonpath:
    """Test JSONPath compilation and caching."""

    def test_compile_jsonpath_valid_expression(self):
        """Test compilation of valid JSONPath expression."""
        # Arrange
        expression = "$.metadata.name"

        # Act
        compiled = _compile_jsonpath(expression)

        # Assert
        assert compiled is not None
        # Verify it's actually a compiled JSONPath object by checking it has expected methods
        assert hasattr(compiled, "findall")

    def test_compile_jsonpath_complex_expression(self):
        """Test compilation of complex JSONPath expression."""
        # Arrange
        expression = "$.items[*].metadata.labels['app']"

        # Act
        compiled = _compile_jsonpath(expression)

        # Assert
        assert compiled is not None
        assert hasattr(compiled, "findall")

    def test_compile_jsonpath_invalid_expression(self):
        """Test compilation of invalid JSONPath expression."""
        # Arrange
        expression = "$.invalid[syntax"

        with patch("haproxy_template_ic.k8s.resource_utils.logger") as mock_logger:
            # Act & Assert
            with pytest.raises(JSONPathError):
                _compile_jsonpath(expression)

            mock_logger.warning.assert_called_once()
            warning_call = mock_logger.warning.call_args[0][0]
            assert "Invalid JSONPath expression" in warning_call
            assert "$.invalid[syntax" in warning_call

    def test_compile_jsonpath_caching(self):
        """Test that JSONPath expressions are cached."""
        # Arrange
        expression = "$.metadata.namespace"

        # Act
        compiled1 = _compile_jsonpath(expression)
        compiled2 = _compile_jsonpath(expression)

        # Assert
        assert compiled1 is compiled2  # Should be the same object due to caching

    def test_compile_jsonpath_cache_different_expressions(self):
        """Test that different expressions get different cached objects."""
        # Arrange
        expression1 = "$.metadata.name"
        expression2 = "$.metadata.namespace"

        # Act
        compiled1 = _compile_jsonpath(expression1)
        compiled2 = _compile_jsonpath(expression2)

        # Assert
        assert compiled1 is not compiled2  # Should be different objects

    def test_compile_jsonpath_empty_expression(self):
        """Test compilation of empty JSONPath expression (treated as root)."""
        # Arrange
        expression = ""

        # Act
        compiled = _compile_jsonpath(expression)

        # Assert - empty string is treated as root selector
        assert compiled is not None
        assert hasattr(compiled, "findall")

    def test_compile_jsonpath_root_only_expression(self):
        """Test compilation of root-only JSONPath expression."""
        # Arrange
        expression = "$"

        # Act
        compiled = _compile_jsonpath(expression)

        # Assert
        assert compiled is not None
        assert hasattr(compiled, "findall")


class TestExtractNestedField:
    """Test nested field extraction functionality."""

    def test_extract_nested_field_simple_path(self):
        """Test extraction of simple nested field."""
        # Arrange
        resource = {"metadata": {"name": "test-pod", "namespace": "default"}}
        field_path = "metadata.name"

        # Act
        result = extract_nested_field(resource, field_path)

        # Assert
        assert result == "test-pod"

    def test_extract_nested_field_deep_path(self):
        """Test extraction of deeply nested field."""
        # Arrange
        resource = {
            "spec": {
                "containers": [
                    {
                        "name": "app",
                        "image": "nginx:latest",
                        "ports": [{"containerPort": 80}],
                    }
                ]
            }
        }
        field_path = "spec.containers[0].ports[0].containerPort"

        # Act
        result = extract_nested_field(resource, field_path)

        # Assert
        assert result == 80

    def test_extract_nested_field_nonexistent_path(self):
        """Test extraction of non-existent field."""
        # Arrange
        resource = {"metadata": {"name": "test-pod"}}
        field_path = "metadata.labels.app"

        # Act
        result = extract_nested_field(resource, field_path)

        # Assert
        assert result is None

    def test_extract_nested_field_array_index(self):
        """Test extraction from array using index."""
        # Arrange
        resource = {"items": [{"name": "first"}, {"name": "second"}, {"name": "third"}]}
        field_path = "items[1].name"

        # Act
        result = extract_nested_field(resource, field_path)

        # Assert
        assert result == "second"

    def test_extract_nested_field_array_out_of_bounds(self):
        """Test extraction from array with out-of-bounds index."""
        # Arrange
        resource = {"items": [{"name": "first"}, {"name": "second"}]}
        field_path = "items[5].name"

        # Act
        result = extract_nested_field(resource, field_path)

        # Assert
        assert result is None

    def test_extract_nested_field_empty_resource(self):
        """Test extraction from empty resource."""
        # Arrange
        resource = {}
        field_path = "metadata.name"

        # Act
        result = extract_nested_field(resource, field_path)

        # Assert
        assert result is None

    def test_extract_nested_field_null_values(self):
        """Test extraction when field contains null values."""
        # Arrange
        resource = {"metadata": {"name": "test-pod", "labels": None}}
        field_path = "metadata.labels"

        # Act
        result = extract_nested_field(resource, field_path)

        # Assert
        assert result is None

    def test_extract_nested_field_invalid_path_syntax(self):
        """Test extraction with invalid JSONPath syntax."""
        # Arrange
        resource = {"metadata": {"name": "test"}}
        field_path = "invalid[syntax"

        with patch("haproxy_template_ic.k8s.resource_utils.logger") as mock_logger:
            # Act
            result = extract_nested_field(resource, field_path)

        # Assert
        assert result is None
        mock_logger.debug.assert_called_once()
        debug_call = mock_logger.debug.call_args[0][0]
        assert "Failed to extract field" in debug_call

    def test_extract_nested_field_type_error(self):
        """Test extraction when resource structure has unexpected types."""
        # Arrange
        resource = {
            "metadata": "not-a-dict"  # Should be a dict
        }
        field_path = "metadata.name"

        with patch("haproxy_template_ic.k8s.resource_utils.logger") as mock_logger:
            # Act
            result = extract_nested_field(resource, field_path)

        # Assert - JSONPath handles this gracefully without raising exceptions
        assert result is None
        mock_logger.debug.assert_not_called()  # No exception means no debug logging

    def test_extract_nested_field_complex_data_types(self):
        """Test extraction of complex data types."""
        # Arrange
        resource = {
            "data": {
                "config.yaml": "apiVersion: v1\nkind: ConfigMap",
                "numbers": [1, 2, 3, 4, 5],
                "nested": {"deep": {"value": {"key": "complex"}}},
            }
        }

        # Act & Assert
        assert extract_nested_field(resource, "data.numbers") == [1, 2, 3, 4, 5]
        assert extract_nested_field(resource, "data.nested.deep.value") == {
            "key": "complex"
        }
        assert extract_nested_field(resource, "data.nested.deep.value.key") == "complex"


class TestIsValidResource:
    """Test resource validation functionality."""

    def test_is_valid_resource_kubernetes_object_with_name(self):
        """Test validation of Kubernetes object with valid name."""
        # Arrange
        mock_resource = Mock()
        mock_resource.metadata.name = "test-pod"

        # Act
        result = _is_valid_resource(mock_resource)

        # Assert
        assert result is True

    def test_is_valid_resource_kubernetes_object_empty_name(self):
        """Test validation of Kubernetes object with empty name."""
        # Arrange
        mock_resource = Mock()
        mock_resource.metadata.name = ""

        # Act
        result = _is_valid_resource(mock_resource)

        # Assert
        assert result is False

    def test_is_valid_resource_kubernetes_object_none_name(self):
        """Test validation of Kubernetes object with None name."""
        # Arrange
        mock_resource = Mock()
        mock_resource.metadata.name = None

        # Act
        result = _is_valid_resource(mock_resource)

        # Assert
        assert result is False

    def test_is_valid_resource_kubernetes_object_no_metadata(self):
        """Test validation of Kubernetes object without metadata."""
        # Arrange
        mock_resource = Mock()
        del mock_resource.metadata

        # Act
        result = _is_valid_resource(mock_resource)

        # Assert
        assert result is False

    def test_is_valid_resource_dict_resource_valid(self):
        """Test validation of valid dictionary resource."""
        # Arrange
        resource = {"metadata": {"name": "test-service", "namespace": "default"}}

        # Act
        result = _is_valid_resource(resource)

        # Assert
        assert result is True

    def test_is_valid_resource_dict_resource_empty_name(self):
        """Test validation of dictionary resource with empty name."""
        # Arrange
        resource = {"metadata": {"name": "", "namespace": "default"}}

        # Act
        result = _is_valid_resource(resource)

        # Assert
        assert result is False

    def test_is_valid_resource_dict_resource_whitespace_name(self):
        """Test validation of dictionary resource with whitespace-only name."""
        # Arrange
        resource = {"metadata": {"name": "   \n\t  ", "namespace": "default"}}

        # Act
        result = _is_valid_resource(resource)

        # Assert
        assert result is False

    def test_is_valid_resource_dict_resource_no_metadata(self):
        """Test validation of dictionary resource without metadata."""
        # Arrange
        resource = {"spec": {"replicas": 3}}

        # Act
        result = _is_valid_resource(resource)

        # Assert
        assert result is False

    def test_is_valid_resource_dict_resource_invalid_metadata(self):
        """Test validation of dictionary resource with invalid metadata."""
        # Arrange
        resource = {"metadata": "not-a-dict"}

        # Act
        result = _is_valid_resource(resource)

        # Assert
        assert result is False

    def test_is_valid_resource_non_dict_non_object(self):
        """Test validation of non-dictionary, non-object resource."""
        # Arrange
        resource = "not-a-resource"

        # Act
        result = _is_valid_resource(resource)

        # Assert
        assert result is False

    def test_is_valid_resource_none(self):
        """Test validation of None resource."""
        # Arrange
        resource = None

        # Act
        result = _is_valid_resource(resource)

        # Assert
        assert result is False

    def test_is_valid_resource_empty_dict(self):
        """Test validation of empty dictionary."""
        # Arrange
        resource = {}

        # Act
        result = _is_valid_resource(resource)

        # Assert
        assert result is False


class TestIsValidDictResource:
    """Test dictionary resource validation functionality."""

    def test_is_valid_dict_resource_valid(self):
        """Test validation of valid dictionary resource."""
        # Arrange
        resource = {"metadata": {"name": "valid-resource", "namespace": "test"}}

        # Act
        result = _is_valid_dict_resource(resource)

        # Assert
        assert result is True

    def test_is_valid_dict_resource_not_dict(self):
        """Test validation of non-dictionary resource."""
        # Arrange
        resource = ["not", "a", "dict"]

        # Act
        result = _is_valid_dict_resource(resource)

        # Assert
        assert result is False

    def test_is_valid_dict_resource_no_metadata(self):
        """Test validation of dictionary resource without metadata."""
        # Arrange
        resource = {"spec": {"replicas": 1}}

        # Act
        result = _is_valid_dict_resource(resource)

        # Assert
        assert result is False

    def test_is_valid_dict_resource_metadata_not_dict(self):
        """Test validation of resource with non-dict metadata."""
        # Arrange
        resource = {"metadata": "invalid-metadata-type"}

        # Act
        result = _is_valid_dict_resource(resource)

        # Assert
        assert result is False

    def test_is_valid_dict_resource_no_name(self):
        """Test validation of resource without name in metadata."""
        # Arrange
        resource = {"metadata": {"namespace": "test"}}

        # Act
        result = _is_valid_dict_resource(resource)

        # Assert
        assert result is False

    def test_is_valid_dict_resource_empty_name(self):
        """Test validation of resource with empty name."""
        # Arrange
        resource = {"metadata": {"name": "", "namespace": "test"}}

        # Act
        result = _is_valid_dict_resource(resource)

        # Assert
        assert result is False

    def test_is_valid_dict_resource_whitespace_name(self):
        """Test validation of resource with whitespace-only name."""
        # Arrange
        resource = {"metadata": {"name": "   ", "namespace": "test"}}

        # Act
        result = _is_valid_dict_resource(resource)

        # Assert
        assert result is False

    def test_is_valid_dict_resource_name_not_string(self):
        """Test validation of resource with non-string name."""
        # Arrange
        resource = {
            "metadata": {
                "name": 123,  # Should be string
                "namespace": "test",
            }
        }

        # Act
        result = _is_valid_dict_resource(resource)

        # Assert
        assert result is False

    def test_is_valid_dict_resource_name_none(self):
        """Test validation of resource with None name."""
        # Arrange
        resource = {"metadata": {"name": None, "namespace": "test"}}

        # Act
        result = _is_valid_dict_resource(resource)

        # Assert
        assert result is False

    def test_is_valid_dict_resource_valid_with_extra_fields(self):
        """Test validation of valid resource with additional fields."""
        # Arrange
        resource = {
            "apiVersion": "v1",
            "kind": "Pod",
            "metadata": {
                "name": "test-pod",
                "namespace": "production",
                "labels": {"app": "web"},
                "annotations": {"key": "value"},
            },
            "spec": {"containers": [{"name": "app", "image": "nginx"}]},
        }

        # Act
        result = _is_valid_dict_resource(resource)

        # Assert
        assert result is True


class TestResourceUtilsIntegration:
    """Integration tests for resource utils module."""

    def test_full_namespace_detection_flow(self):
        """Test complete namespace detection flow."""
        # Test environment variable case
        with patch.dict(os.environ, {"KUBERNETES_NAMESPACE": "test-env"}):
            assert get_current_namespace() == "test-env"

        # Test service account file case
        with patch.dict(os.environ, {}, clear=True):
            with tempfile.NamedTemporaryFile(mode="w", delete=False) as temp_file:
                temp_file.write("test-file-namespace")
                temp_file_path = temp_file.name

            try:
                with (
                    patch(
                        "haproxy_template_ic.k8s.resource_utils.os.path.exists"
                    ) as mock_exists,
                    patch(
                        "haproxy_template_ic.k8s.resource_utils.open",
                        mock_open(read_data="test-file-namespace"),
                    ),
                ):
                    mock_exists.return_value = True
                    assert get_current_namespace() == "test-file-namespace"
            finally:
                os.unlink(temp_file_path)

        # Test fallback case
        with (
            patch.dict(os.environ, {}, clear=True),
            patch("os.path.exists", return_value=False),
        ):
            assert get_current_namespace() == "default"

    def test_jsonpath_extraction_with_caching(self):
        """Test JSONPath extraction with caching behavior."""
        # Arrange
        resource = {
            "metadata": {
                "name": "test-resource",
                "namespace": "default",
                "labels": {"app": "web", "version": "v1.0"},
            },
            "spec": {"replicas": 3, "selector": {"matchLabels": {"app": "web"}}},
        }

        # Act & Assert - Multiple extractions should use cached JSONPath
        assert extract_nested_field(resource, "metadata.name") == "test-resource"
        assert extract_nested_field(resource, "metadata.namespace") == "default"
        assert extract_nested_field(resource, "metadata.labels.app") == "web"
        assert extract_nested_field(resource, "spec.replicas") == 3

        # Test that the same path uses cached compilation
        assert extract_nested_field(resource, "metadata.name") == "test-resource"

    def test_resource_validation_comprehensive(self):
        """Test comprehensive resource validation scenarios."""
        # Valid Kubernetes object
        mock_k8s_obj = Mock()
        mock_k8s_obj.metadata.name = "valid-k8s-resource"
        assert _is_valid_resource(mock_k8s_obj) is True

        # Valid dictionary resource
        valid_dict = {"metadata": {"name": "valid-dict-resource", "namespace": "test"}}
        assert _is_valid_resource(valid_dict) is True

        # Invalid resources
        invalid_cases = [
            None,
            {},
            {"metadata": {}},
            {"metadata": {"name": ""}},
            {"metadata": {"name": "   "}},
            {"metadata": {"name": None}},
            {"metadata": "not-a-dict"},
            "not-a-resource",
            123,
            [],
        ]

        for invalid_resource in invalid_cases:
            assert _is_valid_resource(invalid_resource) is False

    def test_error_handling_robustness(self):
        """Test error handling across all utility functions."""
        # Test namespace detection with various error conditions
        with (
            patch.dict(os.environ, {}, clear=True),
            patch("os.path.exists", return_value=True),
            patch("builtins.open", side_effect=PermissionError("Access denied")),
            patch("haproxy_template_ic.k8s.resource_utils.logger") as mock_logger,
        ):
            result = get_current_namespace()
            assert result == "default"
            mock_logger.warning.assert_called_once()

        # Test JSONPath compilation with malformed expressions
        with pytest.raises(JSONPathError):
            _compile_jsonpath("$.[invalid")

        # Test field extraction with problematic data
        problematic_resource = {
            "metadata": {"name": "test", "deeply": {"nested": {"circular": None}}}
        }

        # Should handle gracefully
        result = extract_nested_field(
            problematic_resource, "metadata.deeply.nested.nonexistent"
        )
        assert result is None
