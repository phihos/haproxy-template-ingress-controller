"""
Utilities for handling Kopf Store and Body objects.

This module provides centralized functions for converting Kopf's internal
data structures (Store and Body objects) to regular Python dictionaries.
These utilities should only be used within IndexedResourceCollection.from_kopf_index().
"""

import logging
import unicodedata
from collections import defaultdict
from typing import Any, Iterator

from kopf._core.engines.indexing import OperatorIndices
from pydantic import BaseModel, PrivateAttr

from haproxy_template_ic.tracing import record_span_event

from .field_filter import remove_fields_from_resource

logger = logging.getLogger(__name__)


def convert_kopf_body_to_dict(body: Any) -> dict[str, Any]:
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
    resource: Any, ignore_fields: list[str] | None = None
) -> dict[str, Any]:
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


def get_resource_collection_from_indices(
    indices: OperatorIndices,
    resource_id: str,
    ignore_fields: list[str] | None = None,
) -> "IndexedResourceCollection":
    """
    Get an IndexedResourceCollection from a memo object for a specific resource type.

    This consolidates the common pattern of getting an index from indices
    and converting it to an IndexedResourceCollection.

    Args:
        resource_id: Resource identifier/type to retrieve
        ignore_fields: Optional list of JSONPath expressions for fields to remove

    Returns:
        IndexedResourceCollection for the specified resource type
    """

    if resource_id in indices:
        return IndexedResourceCollection.from_kopf_index(
            indices[resource_id], ignore_fields=ignore_fields
        )
    return IndexedResourceCollection()


class IndexedResourceCollection(BaseModel):
    """O(1) resource lookups by custom index keys."""

    _internal_dict: dict[tuple[str, ...], list[dict[str, Any]]] = PrivateAttr(
        default_factory=lambda: defaultdict(list)
    )
    _max_size: int = PrivateAttr(default=10000)

    @classmethod
    def from_kopf_index(
        cls, index: Any, ignore_fields: list[str] | None = None
    ) -> "IndexedResourceCollection":
        """Create from kopf Index with automatic Body/Store object conversion.

        Args:
            index: Kopf index object containing resources
            ignore_fields: Optional list of JSONPath expressions for fields to remove

        Returns:
            IndexedResourceCollection with filtered resources
        """
        collection = cls()
        if not (hasattr(index, "__getitem__") and hasattr(index, "__iter__")):
            return collection

        count = 0
        for key in index:
            if count >= collection._max_size:
                logger.warning(f"Size limit reached ({collection._max_size})")
                break
            try:
                normalized_key = collection._normalize_key(key)
                for resource in index[key]:
                    if count >= collection._max_size:
                        break

                    # Convert Kopf Body objects to regular dictionaries and apply field filtering
                    try:
                        normalized_resource = normalize_kopf_resource(
                            resource, ignore_fields
                        )
                    except ValueError as e:
                        logger.warning(
                            f"Failed to normalize resource with key {normalized_key}: {e}"
                        )
                        continue

                    if collection._validate_resource(normalized_resource):
                        collection._internal_dict[normalized_key].append(
                            normalized_resource
                        )
                        count += 1
                    else:
                        logger.warning(
                            f"Skipping invalid resource with key {normalized_key}"
                        )
            except Exception as e:
                logger.warning(f"Error with key {key}: {e}")
        return collection

    def get_indexed(self, *args: str) -> list[dict[str, Any]]:
        """Get resources by key."""
        key = self._normalize_key(*args)
        return self._internal_dict.get(key, [])

    def get_indexed_iter(self, *args: str) -> Iterator[dict[str, Any]]:
        yield from self.get_indexed(*args)

    def get_indexed_single(self, *args: str) -> dict[str, Any] | None:
        """Get single resource or raise if multiple found."""
        results = self.get_indexed(*args)
        if len(results) > 1:
            resource_ids = [self._extract_resource_id(r) for r in results[:3]]
            error_msg = (
                f"Multiple resources found for key {args}: {len(results)} matches"
            )
            if len(results) > 3:
                error_msg += f" (showing first 3: {', '.join(resource_ids)})"
            else:
                error_msg += f" [{', '.join(resource_ids)}]"
            logger.error(
                f"{error_msg}. This may indicate duplicate resources or incorrect indexing configuration."
            )
            try:
                record_span_event(
                    "multiple_resources_found",
                    {
                        "key": str(args),
                        "count": len(results),
                        "resources": resource_ids,
                    },
                )
            except ImportError:
                pass
            raise ValueError(error_msg)
        return results[0] if results else None

    def items(self) -> Iterator[tuple[tuple[str, ...], dict[str, Any]]]:
        for key, resources in self._internal_dict.items():
            for resource in resources:
                yield (key, resource)

    def values(self) -> Iterator[dict[str, Any]]:
        for resources in self._internal_dict.values():
            yield from resources

    def __len__(self) -> int:
        return sum(len(resources) for resources in self._internal_dict.values())

    def __bool__(self) -> bool:
        return bool(self._internal_dict)

    def __contains__(self, key: tuple[str, ...]) -> bool:
        if isinstance(key, tuple):
            normalized_key = self._normalize_key(*key)
        return normalized_key in self._internal_dict

    def keys(self) -> Iterator[tuple[str, ...]]:
        return iter(self._internal_dict.keys())

    def _normalize_key(self, *args: Any) -> tuple[str, ...]:
        components = (
            args[0] if len(args) == 1 and isinstance(args[0], (tuple, list)) else args
        )
        return tuple(
            unicodedata.normalize("NFC", str(arg or "").strip()) for arg in components
        )

    def _validate_resource(self, resource: Any) -> bool:
        try:
            return bool(resource.metadata.name)
        except AttributeError:
            return (
                isinstance(resource, dict)
                and isinstance(resource.get("metadata", {}), dict)
                and bool(resource.get("metadata", {}).get("name", "").strip())
            )

    def _extract_resource_id(self, resource: Any) -> str:
        try:
            # Try object-style access first
            try:
                return f"{getattr(resource, 'kind', 'unknown')}:{getattr(resource.metadata, 'namespace', 'unknown')}/{resource.metadata.name}"
            except AttributeError:
                # Fall back to dict-style access
                if isinstance(resource, dict) and "metadata" in resource:
                    metadata = resource["metadata"]
                    return f"{resource.get('kind', 'unknown')}:{metadata.get('namespace', 'unknown')}/{metadata.get('name', 'unknown')}"
                return "<unknown>"
        except Exception:
            return "<error>"
