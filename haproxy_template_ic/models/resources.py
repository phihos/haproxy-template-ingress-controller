"""
Resource indexing and collection models for HAProxy Template IC.

Contains IndexedResourceCollection for O(1) resource lookups
with support for custom indexing patterns.
"""

import logging
import unicodedata
from typing import Any, Dict, Iterator, List, Optional, Tuple
from collections import defaultdict

from pydantic import BaseModel, PrivateAttr

logger = logging.getLogger(__name__)


class IndexedResourceCollection(BaseModel):
    """O(1) resource lookups by custom index keys."""

    _internal_dict: Dict[Tuple[str, ...], List[Dict[str, Any]]] = PrivateAttr(
        default_factory=lambda: defaultdict(list)
    )
    _max_size: int = PrivateAttr(default=10000)

    @classmethod
    def from_kopf_index(
        cls, index: Any, ignore_fields: Optional[List[str]] = None
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
                        from haproxy_template_ic.k8s import normalize_kopf_resource

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

    def get_indexed(self, *args: str) -> List[Dict[str, Any]]:
        """Get resources by key."""
        key = self._normalize_key(*args)
        return self._internal_dict.get(key, [])

    def get_indexed_iter(self, *args: str) -> Iterator[Dict[str, Any]]:
        yield from self.get_indexed(*args)

    def get_indexed_single(self, *args: str) -> Optional[Dict[str, Any]]:
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
                from haproxy_template_ic.tracing import record_span_event

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

    def items(self) -> Iterator[Tuple[Tuple[str, ...], Dict[str, Any]]]:
        for key, resources in self._internal_dict.items():
            for resource in resources:
                yield (key, resource)

    def values(self) -> Iterator[Dict[str, Any]]:
        for resources in self._internal_dict.values():
            yield from resources

    def __len__(self) -> int:
        return sum(len(resources) for resources in self._internal_dict.values())

    def __bool__(self) -> bool:
        return bool(self._internal_dict)

    def __contains__(self, key: Tuple[str, ...]) -> bool:
        if isinstance(key, tuple):
            normalized_key = self._normalize_key(*key)
        return normalized_key in self._internal_dict

    def keys(self) -> Iterator[Tuple[str, ...]]:
        return iter(self._internal_dict.keys())

    def _normalize_key(self, *args: Any) -> Tuple[str, ...]:
        components = (
            args[0] if len(args) == 1 and isinstance(args[0], (tuple, list)) else args
        )
        return tuple(
            unicodedata.normalize("NFC", str(arg or "").strip()) for arg in components
        )

    def _validate_resource(self, resource: Any) -> bool:
        if hasattr(resource, "metadata") and hasattr(resource.metadata, "name"):
            return bool(getattr(resource.metadata, "name", None))
        return (
            isinstance(resource, dict)
            and isinstance(resource.get("metadata", {}), dict)
            and bool(resource.get("metadata", {}).get("name", "").strip())
        )

    def _extract_resource_id(self, resource: Dict[str, Any]) -> str:
        try:
            if hasattr(resource, "metadata"):
                return f"{getattr(resource, 'kind', 'unknown')}:{getattr(resource.metadata, 'namespace', 'unknown')}/{resource.metadata.name}"
            if isinstance(resource, dict) and "metadata" in resource:
                metadata = resource["metadata"]
                return f"{resource.get('kind', 'unknown')}:{metadata.get('namespace', 'unknown')}/{metadata.get('name', 'unknown')}"
            return "<unknown>"
        except Exception:
            return "<error>"


__all__ = [
    "IndexedResourceCollection",
]
