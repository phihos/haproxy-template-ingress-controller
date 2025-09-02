"""
Resource metadata tracking models.

Contains dataclasses for tracking metadata about watched Kubernetes resources,
including change timestamps, counts, and memory usage.
"""

from dataclasses import dataclass, field
from typing import Any, Dict, Optional
from datetime import datetime, timezone

__all__ = [
    "ResourceTypeMetadata",
]


@dataclass
class ResourceTypeMetadata:
    """Tracks metadata for a watched resource type.

    This dataclass consolidates all metadata we track about a specific
    resource type (e.g., ingresses, services, secrets) including change
    timestamps, resource counts, and memory usage.
    """

    resource_type: str
    last_change: Optional[str] = None  # ISO timestamp string in UTC
    total_count: int = 0
    namespace_count: int = 0
    memory_size: int = 0
    namespaces: Dict[str, int] = field(default_factory=dict)

    def update_change_timestamp(self) -> None:
        """Update the last_change timestamp to current UTC time."""
        self.last_change = datetime.now(timezone.utc).isoformat()

    def update_statistics(
        self,
        total_count: int,
        namespace_count: int,
        memory_size: int,
        namespaces: Dict[str, int],
    ) -> None:
        """Update resource statistics."""
        self.total_count = total_count
        self.namespace_count = namespace_count
        self.memory_size = memory_size
        self.namespaces = namespaces.copy()

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "total": self.total_count,
            "namespace_count": self.namespace_count,
            "memory_size": self.memory_size,
            "namespaces": self.namespaces,
            "last_change": self.last_change,
        }
