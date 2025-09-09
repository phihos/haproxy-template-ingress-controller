"""
Data models and classes for HAProxy Dataplane API operations.

Contains configuration change representations, deployment tracking,
and utility functions for content hashing and validation.
"""

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Dict, List, Optional, Tuple, TypeVar

import xxhash

from .types import ConfigChangeType, ConfigElementType, ConfigSectionType

if TYPE_CHECKING:
    from haproxy_template_ic.models import IndexedResourceCollection

__all__ = [
    "ConfigChange",
    "compute_content_hash",
    "extract_hash_from_description",
    "get_production_urls_from_index",
]

DEFAULT_DATAPLANE_PORT = 5555

T = TypeVar("T")


def _safe_dict_get(obj: Any, key: str, default: Optional[T] = None) -> Optional[T]:
    """Safely get value from dict-like object."""
    return obj.get(key, default) if isinstance(obj, dict) else default


@dataclass
class ConfigChange:
    """Represents a specific configuration change to be applied via dataplane API.

    This class encapsulates all information needed to apply a granular configuration
    change using the HAProxy Dataplane API's structured endpoints instead of the
    raw configuration endpoint.

    Attributes:
        change_type: The type of change (CREATE, UPDATE, DELETE)
        section_type: The type of configuration section being changed
        section_name: The name/identifier of the specific section
        new_config: The new configuration object (None for DELETE operations)
        old_config: The old configuration object (None for CREATE operations)
        section_index: For indexed sections like defaults, the section index (optional)
        element_type: For nested elements within sections (optional)
        element_index: For ordered elements like rules, the element index (optional)
        element_id: For named elements within sections (optional)
    """

    change_type: ConfigChangeType
    section_type: ConfigSectionType
    section_name: str
    new_config: Optional[Any] = None
    old_config: Optional[Any] = None
    section_index: Optional[int] = None
    element_type: Optional[ConfigElementType] = None
    element_index: Optional[int] = None
    element_id: Optional[str] = None

    def __str__(self) -> str:
        """Return a human-readable description of the change."""
        base_description = f"{self.section_type.value} {self.section_name}"

        if self.element_type:
            # This is a nested element change
            element_id = (
                self.element_id or f"[{self.element_index}]"
                if self.element_index is not None
                else ""
            )
            element_description = f"{self.element_type.value} {element_id}".strip()
            base_description = f"{base_description}/{element_description}"

        if self.change_type == ConfigChangeType.CREATE:
            return f"create {base_description}"
        elif self.change_type == ConfigChangeType.DELETE:
            return f"remove {base_description}"
        else:  # UPDATE
            return f"modify {base_description}"

    @classmethod
    def create_section_change(
        cls,
        change_type: ConfigChangeType,
        section_type: ConfigSectionType,
        section_name: str,
        new_config: Optional[Any] = None,
        old_config: Optional[Any] = None,
        section_index: Optional[int] = None,
    ) -> "ConfigChange":
        """Factory method for creating section-level configuration changes."""
        return cls(
            change_type=change_type,
            section_type=section_type,
            section_name=section_name,
            new_config=new_config,
            old_config=old_config,
            section_index=section_index,
        )

    @classmethod
    def create_element_change(
        cls,
        change_type: ConfigChangeType,
        section_type: ConfigSectionType,
        section_name: str,
        element_type: ConfigElementType,
        new_config: Optional[Any] = None,
        old_config: Optional[Any] = None,
        element_id: Optional[str] = None,
        element_index: Optional[int] = None,
    ) -> "ConfigChange":
        """Factory method for creating element-level configuration changes."""
        return cls(
            change_type=change_type,
            section_type=section_type,
            section_name=section_name,
            element_type=element_type,
            new_config=new_config,
            old_config=old_config,
            element_id=element_id,
            element_index=element_index,
        )


def compute_content_hash(content: str) -> str:
    """Compute xxHash64 of content for fast change detection.

    Uses xxHash64 for its excellent performance (5GB/s+) and sufficient
    collision resistance for non-cryptographic change detection.

    Args:
        content: The text content to hash

    Returns:
        Hash string in format "xxh64:<hex_hash>"
    """
    return f"xxh64:{xxhash.xxh64(content.encode('utf-8')).hexdigest()}"


def extract_hash_from_description(description: Optional[str]) -> Optional[str]:
    """Extract content hash from description field if present.

    Args:
        description: Description field that may contain a hash

    Returns:
        The hash string if found (e.g., "xxh64:abc123..."), None otherwise
    """
    if not description or not isinstance(description, str):
        return None

    # Check if description starts with a known hash format
    if description.startswith(("xxh64:", "sha256:", "md5:")):
        # Return just the hash part (before any additional description)
        return description.split(" ", 1)[0]

    return None


def get_production_urls_from_index(
    indexed_pods: "IndexedResourceCollection",
) -> Tuple[List[str], Dict[str, str]]:
    """Extract dataplane URLs and pod names from indexed HAProxy pods.

    Returns:
        Tuple of (urls, url_to_pod_name_mapping) where:
        - urls: List of dataplane URLs
        - url_to_pod_name_mapping: Dict mapping URLs to pod names
    """
    import logging

    logger = logging.getLogger(__name__)
    urls: List[str] = []
    url_to_pod_name: Dict[str, str] = {}

    for pod_dict in indexed_pods.values():
        status: Dict[str, Any] = _safe_dict_get(pod_dict, "status", {}) or {}
        phase = _safe_dict_get(status, "phase")
        pod_ip = _safe_dict_get(status, "podIP")

        logger.debug(f"🔍 Pod phase: {phase}, IP: {pod_ip}")

        if phase == "Running" and pod_ip:
            metadata = _safe_dict_get(pod_dict, "metadata", {})
            pod_name = _safe_dict_get(
                metadata, "name", f"pod-{pod_ip.replace('.', '-')}"
            )

            annotations = _safe_dict_get(metadata, "annotations", {})
            port = _safe_dict_get(
                annotations,
                "haproxy-template-ic/dataplane-port",
                str(DEFAULT_DATAPLANE_PORT),
            )

            url = f"http://{pod_ip}:{port}"
            urls.append(url)
            url_to_pod_name[url] = pod_name
            logger.debug(f"🔍 Found production URL: {url} for pod: {pod_name}")

    logger.debug(f"🔍 Found {len(urls)} production URLs: {urls}")
    return urls, url_to_pod_name
