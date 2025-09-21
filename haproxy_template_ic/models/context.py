"""
Template context and HAProxy configuration context models.

Contains models for template rendering context and complete
HAProxy configuration context with change detection capabilities.
"""

import asyncio
from typing import TYPE_CHECKING

import xxhash
from pydantic import BaseModel, ConfigDict, Field, PrivateAttr, computed_field

from haproxy_template_ic.k8s.kopf_utils import IndexedResourceCollection
from .templates import RenderedConfig, RenderedContent

if TYPE_CHECKING:
    pass


class TemplateContext(BaseModel):
    """Context for template rendering."""

    resources: dict[str, IndexedResourceCollection] = Field(
        default_factory=dict,
        description="Indexed resource collections organized by type",
    )

    model_config = ConfigDict(
        # Allow extra fields for extensibility
        extra="allow",
        # Make immutable as expected by tests
        frozen=True,
        # Allow IndexedResourceCollection (not JSON serializable but used internally)
        arbitrary_types_allowed=True,
    )


class HAProxyConfigContext(BaseModel):
    """Complete context for HAProxy configuration rendering."""

    template_context: TemplateContext = Field(
        ..., description="Template rendering context"
    )

    # Rendered artifacts (unified for all content types)
    rendered_content: list[RenderedContent] = Field(
        default_factory=list, description="All rendered content (maps, certs, files)"
    )
    rendered_config: RenderedConfig | None = Field(
        None, description="Rendered HAProxy config"
    )

    # Private attributes for caching filtered lists
    _cached_maps: list[RenderedContent] | None = PrivateAttr(default=None)
    _cached_certificates: list[RenderedContent] | None = PrivateAttr(default=None)
    _cached_acls: list[RenderedContent] | None = PrivateAttr(default=None)
    _cached_files: list[RenderedContent] | None = PrivateAttr(default=None)
    _cache_version: int = PrivateAttr(default=0)

    # Private attributes for change detection
    _last_content_hash: str | None = PrivateAttr(default=None)
    _last_haproxy_pods_hash: str | None = PrivateAttr(default=None)
    _hash_lock: asyncio.Lock = PrivateAttr(default_factory=asyncio.Lock)

    def get_content_by_filename(self, filename: str) -> RenderedContent | None:
        """Get any rendered content by its filename (maps, certificates, files)."""
        return next(
            (
                content
                for content in self.rendered_content
                if content.filename == filename
            ),
            None,
        )

    def _clear_cache(self) -> None:
        """Clear cached filtered lists when content changes."""
        self._cached_maps = None
        self._cached_certificates = None
        self._cached_acls = None
        self._cached_files = None
        self._cache_version += 1

    # Convenience properties for backward compatibility (filters by content type with caching)
    @computed_field  # type: ignore[misc]
    @property
    def rendered_maps(self) -> list[RenderedContent]:
        """Get rendered maps (cached)."""
        if self._cached_maps is None:
            self._cached_maps = [
                c for c in self.rendered_content if c.content_type == "map"
            ]
        return self._cached_maps

    @computed_field  # type: ignore[misc]
    @property
    def rendered_certificates(self) -> list[RenderedContent]:
        """Get rendered certificates (cached)."""
        if self._cached_certificates is None:
            self._cached_certificates = [
                c for c in self.rendered_content if c.content_type == "certificate"
            ]
        return self._cached_certificates

    @computed_field  # type: ignore[misc]
    @property
    def rendered_acls(self) -> list[RenderedContent]:
        """Get rendered ACLs (cached)."""
        if self._cached_acls is None:
            self._cached_acls = [
                c for c in self.rendered_content if c.content_type == "acl"
            ]
        return self._cached_acls

    @computed_field  # type: ignore[misc]
    @property
    def rendered_files(self) -> list[RenderedContent]:
        """Get rendered files (cached)."""
        if self._cached_files is None:
            self._cached_files = [
                c for c in self.rendered_content if c.content_type == "file"
            ]
        return self._cached_files

    def compute_all_content_hash(self) -> str:
        """Compute xxHash64 of all rendered content for change detection.

        Combines hashes of rendered config and all rendered content (maps, certificates, files).

        Returns:
            Hash string in format "xxh64:<hex_hash>"
        """
        # Collect all content to hash
        content_parts = []

        # Add rendered config content
        if self.rendered_config:
            content_parts.append(self.rendered_config.content)

        # Add all rendered content sorted by filename for deterministic hashing
        for content in sorted(
            self.rendered_content, key=lambda x: (x.content_type, x.filename)
        ):
            content_parts.append(
                f"{content.content_type}:{content.filename}:{content.content}"
            )

        # Combine all content with separator
        combined_content = "\n---\n".join(content_parts)

        # Compute hash
        hash_value = xxhash.xxh64(combined_content.encode("utf-8")).hexdigest()
        return f"xxh64:{hash_value}"

    def compute_haproxy_pods_hash(self, haproxy_pods_collection) -> str:
        """Compute xxHash64 of HAProxy pod state for change detection.

        Args:
            haproxy_pods_collection: IndexedResourceCollection of HAProxy pods

        Returns:
            Hash string in format "xxh64:<hex_hash>"
        """
        if not haproxy_pods_collection:
            return "xxh64:empty"

        # Collect pod identifiers (namespace, name, pod_ip)
        pod_identifiers = []
        for key, pod in haproxy_pods_collection.items():
            namespace = pod.get("metadata", {}).get("namespace", "")
            name = pod.get("metadata", {}).get("name", "")
            pod_ip = pod.get("status", {}).get("podIP", "")
            pod_identifiers.append(f"{namespace}:{name}:{pod_ip}")

        # Sort for deterministic hashing
        pod_identifiers.sort()

        # Combine and hash
        combined_pods = "\n".join(pod_identifiers)
        hash_value = xxhash.xxh64(combined_pods.encode("utf-8")).hexdigest()
        return f"xxh64:{hash_value}"

    async def has_content_changed(self) -> bool:
        """Check if rendered content has changed since last check (thread-safe).

        Returns:
            True if content changed or this is the first check
        """
        async with self._hash_lock:
            current_hash = self.compute_all_content_hash()
            if (
                self._last_content_hash is None
                or self._last_content_hash != current_hash
            ):
                self._last_content_hash = current_hash
                return True
            return False

    async def have_pods_changed(self, haproxy_pods_collection) -> bool:
        """Check if HAProxy pods have changed since last check (thread-safe).

        Args:
            haproxy_pods_collection: IndexedResourceCollection of HAProxy pods

        Returns:
            True if pods changed or this is the first check
        """
        async with self._hash_lock:
            current_hash = self.compute_haproxy_pods_hash(haproxy_pods_collection)
            if (
                self._last_haproxy_pods_hash is None
                or self._last_haproxy_pods_hash != current_hash
            ):
                self._last_haproxy_pods_hash = current_hash
                return True
            return False

    model_config = ConfigDict(
        # This is mutable during rendering process
        validate_assignment=True,
        # Allow forward references and arbitrary types
        arbitrary_types_allowed=True,
    )


# Note: model_rebuild() should be called after all models are defined


__all__ = [
    "TemplateContext",
    "HAProxyConfigContext",
]
