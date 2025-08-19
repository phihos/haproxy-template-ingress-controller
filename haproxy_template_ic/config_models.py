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

from typing import Annotated, Any, Dict, Iterator, List, Optional, Tuple, TYPE_CHECKING
import unicodedata
from collections import defaultdict

from pydantic import BaseModel, ConfigDict, Field, PrivateAttr, field_validator
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
    index_by: List[str] = Field(
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


class IndexedResourceCollection(BaseModel):
    """O(1) resource lookups by custom index keys."""

    _internal_dict: Dict[Tuple[str, ...], List[Dict[str, Any]]] = PrivateAttr(
        default_factory=lambda: defaultdict(list)
    )
    _max_size: int = PrivateAttr(default=10000)

    @classmethod
    def from_kopf_index(cls, index: Any) -> "IndexedResourceCollection":
        """Create from kopf Index."""
        import logging

        logger = logging.getLogger(__name__)

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
                    if collection._validate_resource(resource):
                        collection._internal_dict[normalized_key].append(resource)
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
            import logging

            resource_ids = [self._extract_resource_id(r) for r in results[:3]]
            error_msg = (
                f"Multiple resources found for key {args}: {len(results)} matches"
            )
            if len(results) > 3:
                error_msg += f" (showing first 3: {', '.join(resource_ids)})"
            else:
                error_msg += f" [{', '.join(resource_ids)}]"
            logging.getLogger(__name__).error(
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


class TemplateContext(BaseModel):
    """Context for template rendering."""

    resources: Dict[str, IndexedResourceCollection] = Field(
        default_factory=dict,
        description="Indexed resource collections organized by type",
    )
    namespace: Optional[str] = Field(None, description="Current namespace")

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

        error_msg += f"\nDETAILED ERROR:\n{e}"

        raise ValueError(error_msg) from e


WatchResourceCollection = Dict[str, WatchResourceConfig]
MapCollection = Dict[str, MapConfig]
TemplateSnippetCollection = Dict[str, TemplateSnippet]
CertificateCollection = Dict[str, CertificateConfig]
