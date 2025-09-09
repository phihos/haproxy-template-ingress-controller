"""
Utilities for handling Kopf Store and Body objects.

This module provides centralized functions for converting Kopf's internal
data structures (Store and Body objects) to regular Python dictionaries.
These utilities should only be used within IndexedResourceCollection.from_kopf_index().
"""

import logging
from typing import Any, Dict, List, Optional, TYPE_CHECKING

from .field_filter import remove_fields_from_resource

if TYPE_CHECKING:
    from haproxy_template_ic.models import IndexedResourceCollection

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


def normalize_kopf_resource(
    resource: Any, ignore_fields: Optional[List[str]] = None
) -> Dict[str, Any]:
    """
    Normalize a Kopf resource (Body object or dict) to a regular dictionary.

    Args:
        resource: A Kopf Body object, regular dict, or other dict-convertible object
        ignore_fields: Optional list of JSONPath expressions for fields to remove

    Returns:
        Dictionary representation of the resource with specified fields removed

    Raises:
        ValueError: If the resource cannot be normalized to a dictionary
    """
    # If it's already a regular dict, use it directly
    if isinstance(resource, dict):
        result = resource
    # Check if it's a Kopf Body object or similar dict-convertible object
    elif hasattr(resource, "__getitem__") or hasattr(resource, "items"):
        try:
            result = convert_kopf_body_to_dict(resource)
        except ValueError:
            # Fall through to error case
            raise ValueError(
                f"Cannot normalize resource of type {type(resource)} to dictionary. "
                f"Expected dict or dict-convertible object."
            )
    else:
        # If we can't handle it, raise an error
        raise ValueError(
            f"Cannot normalize resource of type {type(resource)} to dictionary. "
            f"Expected dict or dict-convertible object."
        )

    # Apply field filtering if specified
    if ignore_fields:
        result = remove_fields_from_resource(result, ignore_fields)

    return result


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

    # Must have apiVersion
    api_version = resource_dict.get("apiVersion")
    if not isinstance(api_version, str) or not api_version.strip():
        return False

    # Must have kind
    kind = resource_dict.get("kind")
    if not isinstance(kind, str) or not kind.strip():
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


def get_resource_collection_from_memo(
    memo: Any, resource_id: str, ignore_fields: Optional[List[str]] = None
) -> "IndexedResourceCollection":
    """
    Get an IndexedResourceCollection from a memo object for a specific resource type.

    This consolidates the common pattern of getting an index from memo.indices
    and converting it to an IndexedResourceCollection.

    Args:
        memo: Memo object containing indices
        resource_id: Resource identifier/type to retrieve
        ignore_fields: Optional list of JSONPath expressions for fields to remove

    Returns:
        IndexedResourceCollection for the specified resource type
    """
    from haproxy_template_ic.models import IndexedResourceCollection

    if hasattr(memo, "indices") and resource_id in memo.indices:
        return IndexedResourceCollection.from_kopf_index(
            memo.indices[resource_id], ignore_fields=ignore_fields
        )
    return IndexedResourceCollection()
