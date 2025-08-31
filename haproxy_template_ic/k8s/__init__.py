# Kubernetes utilities package
# This package contains utilities specific to Kubernetes operations:
# field filtering, Kopf object handling, namespace detection, etc.

from .kopf_utils import (
    convert_kopf_body_to_dict,
    normalize_kopf_resource,
    is_valid_kubernetes_resource,
)

from .field_filter import (
    remove_fields_from_resource,
    validate_ignore_fields,
)

from .resource_utils import (
    get_current_namespace,
    extract_nested_field,
    _compile_jsonpath,
    _is_valid_resource,
    _is_valid_dict_resource,
    _is_valid_sequence_resource,
    _is_valid_object_resource,
)

__all__ = [
    # Kopf utilities
    "convert_kopf_body_to_dict",
    "normalize_kopf_resource",
    "is_valid_kubernetes_resource",
    
    # Field filtering
    "remove_fields_from_resource",
    "validate_ignore_fields",
    
    # Resource utilities
    "get_current_namespace",
    "extract_nested_field",
    "_compile_jsonpath",
    "_is_valid_resource",
    "_is_valid_dict_resource", 
    "_is_valid_sequence_resource",
    "_is_valid_object_resource",
]