"""
Template and content models for HAProxy Template IC.

Contains models for template configuration, rendered content,
and template rendering context information.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any, TYPE_CHECKING

from pydantic import BaseModel, Field, field_validator, ConfigDict

from .types import Filename, NonEmptyStr, NonEmptyStrictStr, SnippetName

if TYPE_CHECKING:
    from ..models.config import Config
    from ..models.context import HAProxyConfigContext, TemplateContext
    from ..metrics import MetricsCollector
    from ..templating import TemplateRenderer


class TemplateConfig(BaseModel):
    """Base configuration for template-based content."""

    template: NonEmptyStrictStr = Field(..., description="Jinja2 template content")

    model_config = ConfigDict(
        # Allow Template objects (not JSON serializable but used internally)
        arbitrary_types_allowed=True,
        frozen=True,
    )


class TemplateSnippet(BaseModel):
    """Reusable template snippet."""

    name: SnippetName = Field(..., description="Snippet name for {% include %}")
    template: NonEmptyStrictStr = Field(..., description="Jinja2 template content")

    model_config = ConfigDict(
        # Allow Template objects (not JSON serializable but used internally)
        arbitrary_types_allowed=True,
        frozen=True,
    )


class ContentType(str, Enum):
    """Enum for HAProxy content types."""

    MAP = "map"
    CERTIFICATE = "certificate"
    ACL = "acl"
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


@dataclass(frozen=True)
class TemplateValidationIssue:
    """Validation issue encountered during template processing."""

    resource_type: str
    resource_uid: str
    error: str


@dataclass(frozen=True)
class TemplatePreparationResult:
    """Result of preparing template context and variables for rendering."""

    template_context: TemplateContext
    template_vars: dict[str, Any]
    validation_errors: list[TemplateValidationIssue]


@dataclass(frozen=True)
class TemplateRenderContext:
    """Bundled context for template rendering operations."""

    config: Config
    template_renderer: TemplateRenderer
    haproxy_config_context: HAProxyConfigContext
    template_vars: dict[str, Any]
    metrics: MetricsCollector


__all__ = [
    "TemplateConfig",
    "TemplateSnippet",
    "ContentType",
    "RenderedContent",
    "TriggerContext",
    "RenderedConfig",
    "TemplateValidationIssue",
    "TemplatePreparationResult",
    "TemplateRenderContext",
]
