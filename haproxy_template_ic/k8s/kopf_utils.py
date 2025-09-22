"""
Utilities for handling Kopf Store and Body objects.

This module provides centralized functions for converting Kopf's internal
data structures (Store and Body objects) to regular Python dictionaries.
These utilities should only be used within IndexedResourceCollection.from_kopf_index().
"""

import logging
import unicodedata
from collections import defaultdict
from collections.abc import Mapping
from typing import Any, Iterator, Protocol, runtime_checkable

from kopf._core.engines.indexing import OperatorIndices
from pydantic import BaseModel, PrivateAttr

from haproxy_template_ic.tracing import record_span_event

from .field_filter import remove_fields_from_resource

logger = logging.getLogger(__name__)


@runtime_checkable
class KubernetesMetadata(Protocol):
    """Protocol for Kubernetes resource metadata."""

    name: str
    namespace: str | None = None


@runtime_checkable
class KubernetesResource(Protocol):
    """Protocol for Kubernetes resource objects."""

    apiVersion: str
    kind: str
    metadata: KubernetesMetadata


def normalize_kopf_resource(
    resource: Mapping[str, Any] | dict[str, Any], ignore_fields: list[str] | None = None
) -> dict[str, Any]:
    """
    Normalize a Kopf resource (Body object or dict) to a regular dictionary.

    Args:
        resource: A Kopf Body object, regular dict, or other Mapping-compatible object
        ignore_fields: Optional list of JSONPath expressions for fields to remove

    Returns:
        Dictionary representation of the resource with specified fields removed
    """
    # Convert any Mapping to dict (works for kopf Body objects and regular dicts)
    result = dict(resource)

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
        cls,
        index: Any,
        ignore_fields: list[str] | None = None,
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

        # Early exit for empty results
        if not results:
            return None

        # Early exit for single result (common case)
        if len(results) == 1:
            return results[0]

        # Handle multiple results error
        self._handle_multiple_resources_error(results, args)

    def _handle_multiple_resources_error(
        self, results: list[dict[str, Any]], key_args: tuple[str, ...]
    ) -> None:
        """Handle error case when multiple resources are found for a single lookup."""
        resource_ids = [self._extract_resource_id(r) for r in results[:3]]
        error_msg = (
            f"Multiple resources found for key {key_args}: {len(results)} matches"
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
                    "key": str(key_args),
                    "count": len(results),
                    "resources": resource_ids,
                },
            )
        except ImportError:
            pass

        raise ValueError(error_msg)

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
        """Validate that a resource has the required Kubernetes structure."""
        try:
            return bool(str(resource.metadata.name or "").strip())
        except AttributeError:
            metadata = resource.get("metadata", {})
            return isinstance(metadata, dict) and bool(
                str(metadata.get("name", "")).strip()
            )

    def _extract_resource_id(self, resource: Any) -> str:
        """Extract a human-readable resource identifier."""
        try:
            kind = getattr(resource, "kind", "unknown")
            namespace = getattr(resource.metadata, "namespace", "unknown")
            name = getattr(resource.metadata, "name", "unknown")
            return f"{kind}:{namespace}/{name}"
        except Exception:
            try:
                metadata = resource.get("metadata", {})
                kind = resource.get("kind", "unknown")
                namespace = metadata.get("namespace", "unknown")
                name = metadata.get("name", "unknown")
                return f"{kind}:{namespace}/{name}"
            except Exception:
                return "<error>"
