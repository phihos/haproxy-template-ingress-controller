"""
Field filtering utilities for removing unwanted fields from resources (backward compatibility module).

This module re-exports all functionality from the haproxy_template_ic.k8s.field_filter
module to maintain backward compatibility with existing code.

The actual implementation has been moved to the k8s package for better organization.
"""

# Re-export everything from the k8s.field_filter module
from haproxy_template_ic.k8s.field_filter import (
    _compile_jsonpath_filter,
    _remove_field_at_path,
    remove_fields_from_resource,
    validate_ignore_fields,
)

__all__ = [
    "remove_fields_from_resource",
    "validate_ignore_fields",
    "_remove_field_at_path",  # Private function for tests
    "_compile_jsonpath_filter",  # Also needed for tests
]
