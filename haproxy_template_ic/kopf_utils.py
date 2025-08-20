"""
Utilities for handling Kopf Store and Body objects.

This module provides centralized functions for converting Kopf's internal
data structures (Store and Body objects) to regular Python dictionaries.
These utilities should only be used within IndexedResourceCollection.from_kopf_index().
"""

import logging
from typing import Any, Dict

logger = logging.getLogger(__name__)


def convert_kopf_body_to_dict(body: Any) -> Dict[str, Any]:
    """
    Convert a Kopf Body object to a regular dictionary.

    Args:
        body: A Kopf Body object or any dict-convertible object

    Returns:
        Dictionary representation of the Body object

    Raises:
        ValueError: If the Body object cannot be converted to a dictionary
    """
    try:
        # Try direct conversion first - works for most Body objects
        result = dict(body)
        if not isinstance(result, dict):
            raise ValueError(f"Conversion resulted in {type(result)}, not dict")
        return result
    except Exception as e:
        logger.warning(f"Failed to convert Body object to dict: {e}")
        raise ValueError(f"Cannot convert Body object to dict: {e}") from e


def normalize_kopf_resource(resource: Any) -> Dict[str, Any]:
    """
    Normalize a Kopf resource (Body object or dict) to a regular dictionary.

    Args:
        resource: A Kopf Body object, regular dict, or other dict-convertible object

    Returns:
        Dictionary representation of the resource

    Raises:
        ValueError: If the resource cannot be normalized to a dictionary
    """
    # If it's already a regular dict, return as-is
    if isinstance(resource, dict):
        return resource

    # Check if it's a Kopf Body object or similar dict-convertible object
    if hasattr(resource, "__getitem__") or hasattr(resource, "items"):
        try:
            return convert_kopf_body_to_dict(resource)
        except ValueError:
            # Fall through to error case
            pass

    # If we can't handle it, raise an error
    raise ValueError(
        f"Cannot normalize resource of type {type(resource)} to dictionary. "
        f"Expected dict or dict-convertible object."
    )


def is_valid_kubernetes_resource(resource_dict: Any) -> bool:
    """
    Check if a dictionary represents a valid Kubernetes resource.

    Args:
        resource_dict: Object to validate (should be a dictionary)

    Returns:
        True if the dictionary appears to be a valid Kubernetes resource
    """
    if not isinstance(resource_dict, dict):
        return False

    # Must have metadata
    metadata = resource_dict.get("metadata")
    if not isinstance(metadata, dict):
        return False

    # Must have a name
    name = metadata.get("name")
    if not isinstance(name, str) or not name.strip():
        return False

    return True
