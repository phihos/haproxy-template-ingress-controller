"""
Pydantic models for HAProxy Template IC configuration.

This module contains all configuration models using Pydantic for automatic
validation, type coercion, and enhanced developer experience.

## Type Aliases and Validation

This module leverages Pydantic's built-in features for validation instead of
custom validators, providing better maintainability and standardized error messages:

- NonEmptyStr: Non-empty string validation using StringConstraints(min_length=1)
- NonEmptyStrictStr: Strict string validation preventing type coercion
- AbsolutePath: Path validation using regex pattern "^/"
- KubernetesKind: Kubernetes resource kind validation (PascalCase)
- ApiVersion: API version format validation (supports "v1" and "group/version")
- SnippetName: Template snippet name validation (no spaces/newlines)

## Benefits of Built-in Validation

- Reduced code complexity (~100+ lines of custom validators removed)
- Standardized error messages from Pydantic
- Better type safety through Annotated types
- Improved performance using optimized built-in validators
- Enhanced maintainability using library features
"""

from typing import Annotated, Any, Dict, List, Optional, TYPE_CHECKING

from pydantic import BaseModel, ConfigDict, Field, field_validator
from pydantic.types import StringConstraints

if TYPE_CHECKING:
    pass


# =============================================================================
# Type Aliases for Common Validation Patterns
# =============================================================================

# Non-empty string validation
NonEmptyStr = Annotated[str, StringConstraints(min_length=1)]

# Non-empty strict string for template validation (prevents Template objects)
NonEmptyStrictStr = Annotated[str, StringConstraints(min_length=1, strict=True)]

# Absolute path validation
AbsolutePath = Annotated[str, StringConstraints(pattern="^/")]

# Kubernetes kind validation (PascalCase starting with uppercase)
KubernetesKind = Annotated[
    str, StringConstraints(min_length=1, pattern="^[A-Z][a-zA-Z0-9]*$")
]

# API version validation (supports both 'v1' and 'group/version' formats)
ApiVersion = Annotated[
    str,
    StringConstraints(
        min_length=1, pattern="^([a-z0-9.-]+/)?v[0-9]+([a-z][a-z0-9]*)?$"
    ),
]

# Template snippet name (no spaces or newlines)
SnippetName = Annotated[str, StringConstraints(min_length=1, pattern="^[^\\s\\n]+$")]


class ResourceFilter(BaseModel):
    """Filter for Kubernetes resources."""

    namespace_selector: Optional[Dict[str, str]] = Field(
        None, description="Namespace label selector"
    )
    label_selector: Optional[Dict[str, str]] = Field(
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
    resource_filter: Optional[ResourceFilter] = Field(
        None, description="Optional resource filtering"
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

    class Config:
        # Allow arbitrary types for filters
        arbitrary_types_allowed = True


class MapConfig(BaseModel):
    """Configuration for HAProxy map files."""

    template: NonEmptyStrictStr = Field(
        ..., description="Jinja2 template for the map content"
    )

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


class CertificateConfig(BaseModel):
    """Configuration for TLS certificates."""

    template: NonEmptyStrictStr = Field(
        ..., description="Jinja2 template for certificate content"
    )

    class Config:
        # Allow Template objects (not JSON serializable but used internally)
        arbitrary_types_allowed = True


class PodSelector(BaseModel):
    """Selector for HAProxy pods."""

    match_labels: Dict[str, str] = Field(
        ..., description="Labels to match HAProxy pods", min_length=1
    )

    class Config:
        frozen = True


class DataplaneAuth(BaseModel):
    """Authentication configuration for HAProxy Dataplane API."""

    username: NonEmptyStr = Field(
        default="admin", description="Username for Dataplane API"
    )
    password: NonEmptyStr = Field(
        default="adminpass", description="Password for Dataplane API"
    )

    class Config:
        frozen = True


class Config(BaseModel):
    """Root configuration for HAProxy Template IC."""

    # Required fields
    pod_selector: PodSelector = Field(..., description="Selector for HAProxy pods")
    haproxy_config: MapConfig = Field(..., description="Main HAProxy configuration")

    # Optional collections
    watched_resources: Dict[str, WatchResourceConfig] = Field(
        default_factory=dict, description="Kubernetes resources to watch"
    )
    maps: Dict[AbsolutePath, MapConfig] = Field(
        default_factory=dict, description="HAProxy map files"
    )
    template_snippets: Dict[str, TemplateSnippet] = Field(
        default_factory=dict, description="Reusable template snippets"
    )
    certificates: Dict[AbsolutePath, CertificateConfig] = Field(
        default_factory=dict, description="TLS certificates"
    )
    dataplane_auth: DataplaneAuth = Field(
        default_factory=DataplaneAuth,
        description="Authentication for HAProxy Dataplane API",
    )

    @field_validator("template_snippets")
    @classmethod
    def validate_snippet_names(cls, v):
        """Validate snippet names for template inclusion."""
        for name, snippet in v.items():
            if name != snippet.name:
                raise ValueError(
                    f"Snippet key '{name}' must match snippet.name '{snippet.name}'"
                )
        return v

    model_config = ConfigDict(
        # Forbid extra fields for strict validation
        extra="forbid",
        # Validate assignment to catch errors early
        validate_assignment=True,
        # Allow Template objects (not JSON serializable but used internally)
        arbitrary_types_allowed=True,
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
                        "template": 'global\n    daemon\n\ndefaults\n    mode http\n    timeout connect 5000ms\n    timeout client 50000ms\n    timeout server 50000ms\n\nfrontend health\n    bind *:8404\n    http-request return status 200 content-type text/plain string "OK" if { path /healthz }\n\nfrontend main\n    bind *:80\n    # Add your routing logic here'
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
                        "/etc/haproxy/maps/host.map": {
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


class RenderedMap(BaseModel):
    """Rendered HAProxy map file."""

    path: AbsolutePath = Field(..., description="Absolute path to the map file")
    content: str = Field(..., description="Rendered map content")
    map_config: Optional["MapConfig"] = Field(
        None, description="Source map configuration"
    )

    class Config:
        # Allow arbitrary types for MapConfig
        arbitrary_types_allowed = True
        frozen = True


class RenderedConfig(BaseModel):
    """Rendered HAProxy configuration."""

    content: NonEmptyStr = Field(..., description="Rendered configuration content")

    class Config:
        frozen = True


class RenderedCertificate(BaseModel):
    """Rendered TLS certificate."""

    path: AbsolutePath = Field(..., description="Absolute path to the certificate file")
    content: str = Field(..., description="Rendered certificate content")

    class Config:
        frozen = True


class TemplateContext(BaseModel):
    """Context for template rendering."""

    resources: Dict[str, Dict[str, Any]] = Field(
        default_factory=dict, description="Kubernetes resources organized by type"
    )
    namespace: Optional[str] = Field(None, description="Current namespace")

    model_config = ConfigDict(
        # Allow extra fields for extensibility
        extra="allow",
        # Make immutable as expected by tests
        frozen=True,
    )


class HAProxyConfigContext(BaseModel):
    """Complete context for HAProxy configuration rendering."""

    # Core configuration
    config: Config = Field(..., description="Configuration object")
    template_context: TemplateContext = Field(
        ..., description="Template rendering context"
    )

    # Rendered artifacts (optional, populated during rendering)
    rendered_maps: List[RenderedMap] = Field(
        default_factory=list, description="Rendered map files"
    )
    rendered_config: Optional[RenderedConfig] = Field(
        None, description="Rendered HAProxy config"
    )
    rendered_certificates: List[RenderedCertificate] = Field(
        default_factory=list, description="Rendered certificates"
    )

    def get_rendered_map_by_path(self, path: str) -> Optional[RenderedMap]:
        """Get a rendered map by its path."""
        for rendered_map in self.rendered_maps:
            if rendered_map.path == path:
                return rendered_map
        return None

    def get_rendered_certificate_by_path(
        self, path: str
    ) -> Optional[RenderedCertificate]:
        """Get a rendered certificate by its path."""
        for cert in self.rendered_certificates:
            if cert.path == path:
                return cert
        return None

    class Config:
        # This is mutable during rendering process
        validate_assignment = True


# Main parsing function to replace config_from_dict
def config_from_dict(data: Dict[str, Any]) -> Config:
    """
    Create Config object from dictionary with automatic validation.
    """
    try:
        # Use Pydantic parsing for validation
        config = Config.model_validate(data)
        return config
    except Exception as e:
        # Re-raise with more context for debugging
        raise ValueError(f"Configuration validation failed: {e}") from e


# =============================================================================
# JSON Schema Generation and Export
# =============================================================================


def export_config_schema(include_examples: bool = True) -> Dict[str, Any]:
    """Export the JSON schema for the main Config model."""
    return Config.model_json_schema(mode="serialization")


def export_all_schemas() -> Dict[str, Any]:
    """Export JSON schemas for all configuration models."""
    models = [
        Config,
        WatchResourceConfig,
        MapConfig,
        TemplateSnippet,
        CertificateConfig,
        PodSelector,
        ResourceFilter,
        RenderedMap,
        RenderedConfig,
        RenderedCertificate,
        TemplateContext,
        HAProxyConfigContext,
    ]
    return {
        model.__name__: model.model_json_schema(mode="serialization")  # type: ignore[attr-defined]
        for model in models
    }


def validate_config_against_schema(config_data: Dict[str, Any]) -> List[str]:
    """
    Validate configuration data against the schema and return validation errors.

    Args:
        config_data: Configuration data to validate

    Returns:
        list: List of validation error messages (empty if valid)
    """
    try:
        # This will raise ValidationError if invalid
        Config.model_validate(config_data)
        return []
    except Exception as e:
        # Parse validation errors into readable messages
        errors = []
        if hasattr(e, "errors"):
            for error in e.errors():
                loc = " -> ".join(str(x) for x in error["loc"])
                msg = error["msg"]
                errors.append(f"{loc}: {msg}")
        else:
            errors.append(str(e))
        return errors


def get_schema_version() -> str:
    """
    Get the schema version for configuration compatibility checking.

    Returns:
        str: Schema version string
    """
    # This can be used for schema migration and compatibility checking
    return "1.0.0"


WatchResourceCollection = Dict[str, WatchResourceConfig]
MapCollection = Dict[str, MapConfig]
TemplateSnippetCollection = Dict[str, TemplateSnippet]
CertificateCollection = Dict[str, CertificateConfig]
