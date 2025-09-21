"""
Core configuration models for HAProxy Template IC.

Contains all configuration classes including Config, WatchResourceConfig,
and other settings models with validation and parsing logic.
"""

import logging
import os
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, PrivateAttr, field_validator

from haproxy_template_ic.constants import (
    CLIENT_TIMEOUT,
    CONNECT_TIMEOUT,
    DEFAULT_HEALTH_PORT,
    SERVER_TIMEOUT,
)

from ..k8s.field_filter import validate_ignore_fields
from .templates import TemplateConfig, TemplateSnippet
from .types import ApiVersion, Filename, KubernetesKind

logger = logging.getLogger(__name__)


class ResourceFilter(BaseModel):
    """Filter for Kubernetes resources."""

    namespace_selector: dict[str, str | None] | None = Field(
        None, description="Namespace label selector"
    )
    label_selector: dict[str, str | None] | None = Field(
        None, description="Resource label selector"
    )

    model_config = ConfigDict(
        frozen=True,
        json_schema_extra={
            "examples": [
                {
                    "namespace_selector": {"environment": "production"},
                    "label_selector": {"app": "my-app", "version": "v1.0.0"},
                }
            ]
        },
    )


class WatchResourceConfig(BaseModel):
    """Configuration for a Kubernetes resource to watch."""

    api_version: ApiVersion = Field(
        ..., description="Kubernetes API version (e.g., 'v1', 'networking.k8s.io/v1')"
    )
    kind: KubernetesKind = Field(
        ..., description="Kubernetes resource kind (e.g., 'Service', 'Ingress')"
    )
    enable_validation_webhook: bool = Field(
        True, description="Enable webhook validation for this resource"
    )
    resource_filter: ResourceFilter | None = Field(
        None, description="Optional resource filtering"
    )
    index_by: list[str] = Field(
        default_factory=lambda: ["metadata.namespace", "metadata.name"],
        description="Field paths for index key (dot notation for nested access)",
    )

    @property
    def group(self) -> str:
        """Extract group from api_version."""
        if "/" in self.api_version:
            return self.api_version.rsplit("/", 1)[0]
        return ""

    @property
    def version(self) -> str:
        """Extract version from api_version."""
        if "/" in self.api_version:
            return self.api_version.rsplit("/", 1)[1]
        return self.api_version

    model_config = ConfigDict(
        # Allow arbitrary types for filters
        arbitrary_types_allowed=True,
        frozen=True,
    )


class PodSelector(BaseModel):
    """Selector for HAProxy pods."""

    match_labels: dict[str, str] = Field(
        ..., description="Labels to match HAProxy pods", min_length=1
    )

    model_config = ConfigDict(frozen=True)


class TemplateRenderingConfig(BaseModel):
    """Configuration for template rendering behavior."""

    min_render_interval: int = Field(
        default=5,
        ge=1,
        le=3600,
        description="Minimum seconds between template renders (default: 5)",
    )
    max_render_interval: int = Field(
        default=60,
        ge=1,
        le=3600,
        description="Maximum seconds without render for guaranteed refresh (default: 60)",
    )

    @field_validator("max_render_interval")
    @classmethod
    def validate_intervals(cls, v: int, info) -> int:
        """Ensure max_render_interval >= min_render_interval."""
        if "min_render_interval" in info.data:
            min_interval = info.data["min_render_interval"]
            if v < min_interval:
                raise ValueError(
                    f"max_render_interval ({v}) must be >= min_render_interval ({min_interval})"
                )
        return v

    model_config = ConfigDict(frozen=True, extra="forbid")


class OperatorConfig(BaseModel):
    """Operator runtime configuration."""

    healthz_port: int = Field(
        default=8080, ge=1, le=65535, description="Port for health check endpoint"
    )
    metrics_port: int = Field(
        default=9090, ge=1, le=65535, description="Port for Prometheus metrics endpoint"
    )
    index_initialization_timeout: int = Field(
        default=5,
        ge=1,
        le=300,
        description="Seconds to wait before considering index initialized (zero-resource case)",
    )

    model_config = ConfigDict(frozen=True, extra="forbid")


class LoggingConfig(BaseModel):
    """Logging configuration."""

    verbose: int = Field(
        default=0, ge=0, le=2, description="Log level: 0=WARNING, 1=INFO, 2=DEBUG"
    )
    structured: bool = Field(
        default=False, description="Enable structured JSON logging output"
    )

    model_config = ConfigDict(frozen=True, extra="forbid")


class TracingConfig(BaseModel):
    """Distributed tracing configuration."""

    enabled: bool = Field(
        default=False, description="Enable distributed tracing with OpenTelemetry"
    )
    service_name: str = Field(
        default="haproxy-template-ic", description="Service name for tracing"
    )
    service_version: str = Field(
        default="",
        description="Service version for tracing (empty uses application version)",
    )
    jaeger_endpoint: str = Field(
        default="",
        description="Jaeger collector endpoint (e.g., 'jaeger-collector:14268')",
    )
    sample_rate: float = Field(
        default=1.0, ge=0.0, le=1.0, description="Tracing sample rate (0.0 to 1.0)"
    )
    console_export: bool = Field(
        default=False, description="Export traces to console for debugging"
    )

    model_config = ConfigDict(frozen=True, extra="forbid")


class ValidationConfig(BaseModel):
    """Validation sidecar configuration."""

    dataplane_host: str = Field(
        default="localhost", description="Host for validation dataplane API endpoint"
    )
    dataplane_port: int = Field(
        default=5555,
        ge=1,
        le=65535,
        description="Port for validation dataplane API endpoint",
    )

    model_config = ConfigDict(frozen=True, extra="forbid")


class Config(BaseModel):
    """Root configuration for HAProxy Template IC."""

    # Required fields
    pod_selector: PodSelector = Field(..., description="Selector for HAProxy pods")
    haproxy_config: TemplateConfig = Field(
        ..., description="Main HAProxy configuration"
    )

    # Optional collections
    watched_resources: dict[str, WatchResourceConfig] = Field(
        default_factory=dict, description="Kubernetes resources to watch"
    )
    maps: dict[Filename, TemplateConfig] = Field(
        default_factory=dict, description="HAProxy map files (by filename)"
    )
    template_snippets: dict[str, TemplateSnippet] = Field(
        default_factory=dict, description="Reusable template snippets"
    )
    certificates: dict[Filename, TemplateConfig] = Field(
        default_factory=dict, description="TLS certificates (by filename)"
    )
    files: dict[Filename, TemplateConfig] = Field(
        default_factory=dict, description="General-purpose files (by filename)"
    )

    # Field filtering configuration
    watched_resources_ignore_fields: list[str] = Field(
        default_factory=lambda: ["metadata.managedFields"],
        description="JSONPath expressions for fields to omit from indexed resources (e.g., 'metadata.managedFields')",
    )

    # Storage directory configuration for HAProxy Dataplane API
    storage_maps_dir: str = Field(
        default="/etc/haproxy/maps",
        description="Directory for HAProxy map files in Dataplane API",
    )
    storage_ssl_dir: str = Field(
        default="/etc/haproxy/ssl",
        description="Directory for SSL certificates in Dataplane API",
    )
    storage_general_dir: str = Field(
        default="/etc/haproxy/general",
        description="Directory for general files in Dataplane API",
    )

    # Template rendering configuration
    template_rendering: TemplateRenderingConfig = Field(
        default_factory=TemplateRenderingConfig,
        description="Template rendering timing configuration",
    )

    # Grouped operator configuration
    operator: OperatorConfig = Field(
        default_factory=OperatorConfig,
        description="Operator runtime configuration",
    )
    logging: LoggingConfig = Field(
        default_factory=LoggingConfig,
        description="Logging configuration",
    )
    tracing: TracingConfig = Field(
        default_factory=TracingConfig,
        description="Distributed tracing configuration",
    )
    validation: ValidationConfig = Field(
        default_factory=ValidationConfig,
        description="Validation sidecar configuration",
    )

    @field_validator("template_snippets")
    @classmethod
    def validate_snippet_names(cls, v: dict[str, Any]) -> dict[str, Any]:
        """Validate snippet names for template inclusion."""
        for name, snippet in v.items():
            if name != snippet.name:
                raise ValueError(
                    f"Snippet key '{name}' must match snippet.name '{snippet.name}'"
                )
        return v

    @field_validator("storage_maps_dir", "storage_ssl_dir", "storage_general_dir")
    @classmethod
    def validate_storage_dir(cls, v: str) -> str:
        """Validate storage directories are absolute paths."""
        if not os.path.isabs(v):
            raise ValueError(f"Storage directory must be absolute path: {v}")
        return v.rstrip("/")  # Remove trailing slash for consistency

    @field_validator("watched_resources_ignore_fields")
    @classmethod
    def validate_ignore_fields(cls, v: list[str]) -> list[str]:
        """Validate JSONPath expressions for field filtering."""
        validated = validate_ignore_fields(v)
        if len(validated) < len(v):
            logger.warning(
                f"Some ignore field expressions were invalid and removed. "
                f"Original: {len(v)}, Valid: {len(validated)}"
            )
        return validated

    # Private attribute to store raw configuration dictionary for diff comparison
    _raw_dict: dict[str, Any] = PrivateAttr(default_factory=dict)

    @property
    def raw(self) -> dict[str, Any]:
        """Access to the raw configuration dictionary for comparison purposes."""
        return self._raw_dict

    model_config = ConfigDict(
        # Forbid extra fields for strict validation
        extra="forbid",
        # Validate assignment to catch errors early
        validate_assignment=True,
        # Allow Template objects (not JSON serializable but used internally)
        arbitrary_types_allowed=True,
        # Freeze the model after creation
        frozen=True,
        # Add title and description for better schema generation
        title="HAProxy Template IC Configuration",
        # Custom JSON schema modifications
        json_schema_extra={
            "examples": [
                {
                    "pod_selector": {
                        "match_labels": {"app": "haproxy", "component": "loadbalancer"}
                    },
                    "haproxy_config": {
                        "template": f'global\n    daemon\n\ndefaults\n    mode http\n    timeout connect {int(CONNECT_TIMEOUT.total_seconds() * 1000)}ms\n    timeout client {int(CLIENT_TIMEOUT.total_seconds() * 1000)}ms\n    timeout server {int(SERVER_TIMEOUT.total_seconds() * 1000)}ms\n\nfrontend health\n    bind *:{DEFAULT_HEALTH_PORT}\n    http-request return status 200 content-type text/plain string "OK" if {{ path /healthz }}\n\nfrontend main\n    bind *:80\n    # Add your routing logic here'
                    },
                    "watched_resources": {
                        "ingresses": {
                            "api_version": "networking.k8s.io/v1",
                            "kind": "Ingress",
                            "enable_validation_webhook": True,
                        },
                        "services": {
                            "api_version": "v1",
                            "kind": "Service",
                            "enable_validation_webhook": False,
                        },
                    },
                    "maps": {
                        "host.map": {
                            "template": "{% for _, ingress in resources.get('ingresses', {}).items() %}\n{% if ingress.spec and ingress.spec.rules %}\n{% for rule in ingress.spec.rules %}\n{% if rule.host %}\n{{ rule.host }} {{ rule.host }}\n{% endif %}\n{% endfor %}\n{% endif %}\n{% endfor %}"
                        }
                    },
                    "template_snippets": {
                        "backend-name": {
                            "name": "backend-name",
                            "template": "backend_{{ service_name }}_{{ port }}",
                        }
                    },
                }
            ],
            "additionalProperties": False,
            "$schema": "https://json-schema.org/draft/2020-12/schema",
        },
    )


# Main parsing function to replace config_from_dict
def config_from_dict(data: dict[str, Any]) -> Config:
    """
    Create Config object from dictionary with automatic validation.
    """

    try:
        # Use Pydantic parsing for validation
        config = Config.model_validate(data)
        # Store the raw dictionary for diff comparison (after env overrides applied)
        config._raw_dict = data.copy()
        return config
    except Exception as e:
        # Provide detailed error context for common configuration issues
        error_msg = "Configuration validation failed"

        # Check for specific validation error patterns and provide helpful guidance
        error_str = str(e)
        if "template_snippets" in error_str and "model_type" in error_str:
            error_msg += "\n\n🔧 TEMPLATE SNIPPETS FORMAT ERROR:\nYour template_snippets are using the wrong format. Each snippet must be a dictionary with 'name' and 'template' fields.\n\n"
            error_msg += "❌ INCORRECT FORMAT:\n"
            error_msg += "template_snippets:\n"
            error_msg += "  snippet-name: |\n"
            error_msg += "    template content\n\n"
            error_msg += "✅ CORRECT FORMAT:\n"
            error_msg += "template_snippets:\n"
            error_msg += "  snippet-name:\n"
            error_msg += "    name: snippet-name\n"
            error_msg += "    template: |\n"
            error_msg += "      template content\n\n"
        elif "watched_resources" in error_str:
            error_msg += "\n\n🔧 WATCHED RESOURCES ERROR:\nThere's an issue with your watched_resources configuration. Check api_version, kind, and other required fields.\n\n"
        elif "pod_selector" in error_str:
            error_msg += "\n\n🔧 POD SELECTOR ERROR:\nYour pod_selector configuration is invalid. Ensure match_labels is a non-empty dictionary.\n\n"
        elif "haproxy_config" in error_str:
            error_msg += "\n\n🔧 HAPROXY CONFIG ERROR:\nYour haproxy_config template is invalid. Ensure it contains a valid Jinja2 template string.\n\n"
        elif "dataplane_auth" in error_str or "validation_auth" in error_str:
            error_msg += "\n\n🔧 CREDENTIALS MOVED TO SECRET:\nAuthentication fields are no longer supported in ConfigMaps. You must provide credentials via a Kubernetes Secret using --secret-name parameter.\n\n"

        error_msg += f"\nDETAILED ERROR:\n{e}"

        raise ValueError(error_msg) from e


# Type aliases for collections
WatchResourceCollection = dict[str, WatchResourceConfig]
MapCollection = dict[str, TemplateConfig]
TemplateSnippetCollection = dict[str, TemplateSnippet]
CertificateCollection = dict[str, TemplateConfig]

__all__ = [
    "ResourceFilter",
    "WatchResourceConfig",
    "PodSelector",
    "TemplateRenderingConfig",
    "OperatorConfig",
    "LoggingConfig",
    "TracingConfig",
    "ValidationConfig",
    "Config",
    "config_from_dict",
    # Type aliases for collections
    "WatchResourceCollection",
    "MapCollection",
    "TemplateSnippetCollection",
    "CertificateCollection",
]
