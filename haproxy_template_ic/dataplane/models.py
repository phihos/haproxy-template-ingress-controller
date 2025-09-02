"""
Data models and classes for HAProxy Dataplane API operations.

Contains configuration change representations, deployment tracking,
and utility functions for content hashing and validation.
"""

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import TYPE_CHECKING, Any, Dict, List, Optional

import xxhash

from .types import ConfigChangeType, ConfigElementType, ConfigSectionType

if TYPE_CHECKING:
    from haproxy_template_ic.models import IndexedResourceCollection

__all__ = [
    "ConfigChange",
    "DeploymentHistory",
    "compute_content_hash",
    "extract_hash_from_description",
    "get_production_urls_from_index",
]

# Default dataplane port for HAProxy instances
DEFAULT_DATAPLANE_PORT = 5555


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


class DeploymentHistory:
    """Simple deployment tracking per endpoint with thread-safe operations."""

    def __init__(self) -> None:
        self._history: Dict[str, Dict[str, Any]] = {}

    def record(
        self,
        endpoint: str,
        version: str,
        success: bool,
        error: Optional[str] = None,
        template_hashes: Optional[Dict[str, str]] = None,
        reload_triggered: bool = False,
    ) -> None:
        """Record a deployment attempt."""
        # Keep current version only if this deployment succeeded
        current_version = (
            self._history.get(endpoint, {}).get("version") if not success else version
        )

        current_timestamp = datetime.now(UTC).isoformat()
        entry = {
            "version": current_version,  # What's actually running
            "timestamp": current_timestamp,
            "success": success,
            "last_attempt": version,  # What was attempted
            "error": error,
            "reload_triggered": reload_triggered,  # Whether this deployment triggered a HAProxy reload
        }

        # Track reload timestamp separately for successful deployments that triggered reloads
        previous_entry = self._history.get(endpoint, {})
        if success and reload_triggered:
            entry["last_reload_timestamp"] = current_timestamp
        else:
            # Keep previous reload timestamp if this deployment didn't trigger a reload
            entry["last_reload_timestamp"] = previous_entry.get("last_reload_timestamp")

        # Only add template hashes if deployment succeeded
        if success and template_hashes:
            # Get previous deployment info for this endpoint to compare hashes
            previous_entry = self._history.get(endpoint, {})
            previous_hashes = previous_entry.get("template_hashes", {})

            # Store all template hashes
            entry["template_hashes"] = template_hashes

            # Track which templates actually changed by comparing hashes
            changed_templates = {}
            previous_timestamps = previous_entry.get("template_change_timestamps", {})

            for template_name, template_hash in template_hashes.items():
                previous_hash = previous_hashes.get(template_name)
                # Template changed if it's new or hash is different
                if previous_hash is None or previous_hash != template_hash:
                    changed_templates[template_name] = current_timestamp
                else:
                    # Template didn't change, keep previous timestamp if available
                    # If no previous timestamp exists, use the earliest timestamp we have for this endpoint
                    if template_name in previous_timestamps:
                        changed_templates[template_name] = previous_timestamps[
                            template_name
                        ]
                    else:
                        # First time tracking this template, use deployment timestamp as baseline
                        # This ensures all templates have timestamps for consistent tracking
                        changed_templates[template_name] = previous_entry.get(
                            "timestamp", current_timestamp
                        )

            # Store individual template change timestamps
            entry["template_change_timestamps"] = changed_templates

        self._history[endpoint] = entry

    def to_dict(self) -> Dict[str, Any]:
        """Get deployment history as dict."""
        return {"deployment_history": self._history}


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
) -> List[str]:
    """Extract dataplane URLs from indexed HAProxy pods."""
    import logging

    logger = logging.getLogger(__name__)
    urls = []

    # IndexedResourceCollection has already converted all Kopf objects to regular dicts
    # We can iterate through all resources directly
    for pod_dict in indexed_pods.values():
        # Extract pod status information
        status = pod_dict.get("status", {})
        phase = status.get("phase") if isinstance(status, dict) else None
        pod_ip = status.get("podIP") if isinstance(status, dict) else None

        logger.debug(f"🔍 Pod phase: {phase}, IP: {pod_ip}")

        if phase == "Running" and pod_ip:
            metadata = pod_dict.get("metadata", {})
            annotations = (
                metadata.get("annotations", {}) if isinstance(metadata, dict) else {}
            )
            port = (
                annotations.get(
                    "haproxy-template-ic/dataplane-port", str(DEFAULT_DATAPLANE_PORT)
                )
                if isinstance(annotations, dict)
                else str(DEFAULT_DATAPLANE_PORT)
            )
            url = f"http://{pod_ip}:{port}"
            urls.append(url)
            logger.debug(f"🔍 Found production URL: {url}")

    logger.debug(f"🔍 Found {len(urls)} production URLs: {urls}")
    return urls
