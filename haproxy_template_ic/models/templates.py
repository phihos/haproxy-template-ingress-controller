"""
Template and content models for HAProxy Template IC.

Contains models for template configuration, rendered content,
and template rendering context information.
"""

from enum import Enum
from pydantic import BaseModel, Field, field_validator

from .types import Filename, NonEmptyStr, NonEmptyStrictStr, SnippetName


class TemplateConfig(BaseModel):
    """Base configuration for template-based content."""

    template: NonEmptyStrictStr = Field(..., description="Jinja2 template content")

    class Config:
        # Allow Template objects (not JSON serializable but used internally)
        arbitrary_types_allowed = True


class TemplateSnippet(BaseModel):
    """Reusable template snippet."""

    name: SnippetName = Field(..., description="Snippet name for {% include %}")
    template: NonEmptyStrictStr = Field(..., description="Jinja2 template content")

    class Config:
        # Allow Template objects (not JSON serializable but used internally)
        arbitrary_types_allowed = True


class ContentType(str, Enum):
    """Enum for HAProxy content types."""

    MAP = "map"
    CERTIFICATE = "certificate"
    FILE = "file"


class RenderedContent(BaseModel):
    """Unified model for all rendered HAProxy content (maps, certificates, files)."""

    filename: Filename = Field(..., description="Filename without path")
    content: str = Field(..., description="Rendered content")
    content_type: ContentType = Field(
        default=ContentType.FILE, description="Type of rendered content"
    )

    @field_validator("filename")
    @classmethod
    def validate_filename_not_directory(cls, v: str) -> str:
        """Additional validation to block directory names like '.' and '..'."""
        if v in (".", ".."):
            raise ValueError(f"Filename cannot be a directory name: {v}")
        return v

    class Config:
        frozen = True


class TriggerContext(BaseModel):
    """Context information for template rendering triggers."""

    trigger_type: str = Field(
        ...,
        description="Type of trigger: 'resource_changes', 'pod_changes', or 'periodic_refresh'",
    )
    pod_changed: bool = Field(
        default=False, description="Whether HAProxy pod changes triggered this render"
    )

    @property
    def force_sync(self) -> bool:
        """Whether this trigger should force synchronization regardless of content changes."""
        return (
            self.trigger_type in ("pod_changes", "periodic_refresh") or self.pod_changed
        )

    class Config:
        frozen = True


class RenderedConfig(BaseModel):
    """Rendered HAProxy configuration."""

    content: NonEmptyStr = Field(..., description="Rendered configuration content")

    class Config:
        frozen = True


__all__ = [
    "TemplateConfig",
    "TemplateSnippet",
    "ContentType",
    "RenderedContent",
    "TriggerContext",
    "RenderedConfig",
]
