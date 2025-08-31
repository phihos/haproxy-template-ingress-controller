"""
Utilities for handling Kopf Store and Body objects (backward compatibility module).

This module re-exports all functionality from the haproxy_template_ic.k8s.kopf_utils
module to maintain backward compatibility with existing code.

The actual implementation has been moved to the k8s package for better organization.
"""

# Re-export everything from the k8s.kopf_utils module
from haproxy_template_ic.k8s.kopf_utils import (
    convert_kopf_body_to_dict,
    is_valid_kubernetes_resource,
    normalize_kopf_resource,
)

__all__ = [
    "convert_kopf_body_to_dict",
    "normalize_kopf_resource",
    "is_valid_kubernetes_resource",
]
