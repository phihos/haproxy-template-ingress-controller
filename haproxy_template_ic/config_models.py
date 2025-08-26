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
import logging
import os
import unicodedata
from collections import defaultdict
from enum import Enum

from pydantic import BaseModel, ConfigDict, Field, PrivateAttr, field_validator
from pydantic.types import StringConstraints

from haproxy_template_ic.constants import DEFAULT_DATAPLANE_PORT, DEFAULT_HEALTH_PORT
from haproxy_template_ic.field_filter import validate_ignore_fields
from haproxy_template_ic.kopf_utils import normalize_kopf_resource

if TYPE_CHECKING:
    pass


# =============================================================================
# Type Aliases for Common Validation Patterns
# =============================================================================

# Non-empty string validation
NonEmptyStr = Annotated[str, StringConstraints(min_length=1)]

# Non-empty strict string for template validation (prevents Template objects)
NonEmptyStrictStr = Annotated[str, StringConstraints(min_length=1, strict=True)]

# Absolute path validation (deprecated - use storage_*_dir fields instead)
AbsolutePath = Annotated[str, StringConstraints(pattern="^/")]

# Filename validation (secure against path traversal and filesystem issues)
Filename = Annotated[
    str,
    StringConstraints(
        min_length=1,
        max_length=255,  # Common filesystem limit
        # Whitelist approach: Only allow safe characters
        # - Must start with alphanumeric character
        # - Can contain alphanumeric, dots, hyphens, underscores
        # - No encoded sequences, path separators, or special characters
        pattern=r"^[a-zA-Z0-9][a-zA-Z0-9._-]*$",
    ),
]

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


# Removed type aliases - use TemplateConfig directly for clarity


class PodSelector(BaseModel):
    """Selector for HAProxy pods."""

    match_labels: Dict[str, str] = Field(
        ..., description="Labels to match HAProxy pods", min_length=1
    )

    class Config:
        frozen = True


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


class Config(BaseModel):
    """Root configuration for HAProxy Template IC."""

    # Required fields
    pod_selector: PodSelector = Field(..., description="Selector for HAProxy pods")
    haproxy_config: TemplateConfig = Field(
        ..., description="Main HAProxy configuration"
    )

    # Optional collections
    watched_resources: Dict[str, WatchResourceConfig] = Field(
        default_factory=dict, description="Kubernetes resources to watch"
    )
    maps: Dict[Filename, TemplateConfig] = Field(
        default_factory=dict, description="HAProxy map files (by filename)"
    )
    template_snippets: Dict[str, TemplateSnippet] = Field(
        default_factory=dict, description="Reusable template snippets"
    )
    certificates: Dict[Filename, TemplateConfig] = Field(
        default_factory=dict, description="TLS certificates (by filename)"
    )
    files: Dict[Filename, TemplateConfig] = Field(
        default_factory=dict, description="General-purpose files (by filename)"
    )

    # Field filtering configuration
    watched_resources_ignore_fields: List[str] = Field(
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
    validation_dataplane_url: str = Field(
        default=f"http://localhost:{DEFAULT_DATAPLANE_PORT}",
        description="URL for validation sidecar Dataplane API",
    )

    # Template rendering configuration
    template_rendering: TemplateRenderingConfig = Field(
        default_factory=TemplateRenderingConfig,
        description="Template rendering timing configuration",
    )

    @field_validator("template_snippets")
    @classmethod
    def validate_snippet_names(cls, v: Dict[str, Any]) -> Dict[str, Any]:
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
    def validate_ignore_fields(cls, v: List[str]) -> List[str]:
        """Validate JSONPath expressions for field filtering."""
        validated = validate_ignore_fields(v)
        if len(validated) < len(v):
            logger = logging.getLogger(__name__)
            logger.warning(
                f"Some ignore field expressions were invalid and removed. "
                f"Original: {len(v)}, Valid: {len(validated)}"
            )
        return validated

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
                        "template": f'global\n    daemon\n\ndefaults\n    mode http\n    timeout connect 5000ms\n    timeout client 50000ms\n    timeout server 50000ms\n\nfrontend health\n    bind *:{DEFAULT_HEALTH_PORT}\n    http-request return status 200 content-type text/plain string "OK" if {{ path /healthz }}\n\nfrontend main\n    bind *:80\n    # Add your routing logic here'
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


class RenderedConfig(BaseModel):
    """Rendered HAProxy configuration."""

    content: NonEmptyStr = Field(..., description="Rendered configuration content")

    class Config:
        frozen = True


# Removed type aliases - use RenderedContent directly for clarity


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

                    # Convert Kopf Body objects to regular dictionaries and apply field filtering
                    try:
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

    # Rendered artifacts (unified for all content types)
    rendered_content: List[RenderedContent] = Field(
        default_factory=list, description="All rendered content (maps, certs, files)"
    )
    rendered_config: Optional[RenderedConfig] = Field(
        None, description="Rendered HAProxy config"
    )

    # Private attributes for caching filtered lists
    _cached_maps: Optional[List[RenderedContent]] = PrivateAttr(default=None)
    _cached_certificates: Optional[List[RenderedContent]] = PrivateAttr(default=None)
    _cached_files: Optional[List[RenderedContent]] = PrivateAttr(default=None)
    _cache_version: int = PrivateAttr(default=0)

    def get_content_by_filename(self, filename: str) -> Optional[RenderedContent]:
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
        self._cached_files = None
        self._cache_version += 1

    # Convenience properties for backward compatibility (filters by content type with caching)
    @property
    def rendered_maps(self) -> List[RenderedContent]:
        """Get rendered maps (cached)."""
        if self._cached_maps is None:
            self._cached_maps = [
                c for c in self.rendered_content if c.content_type == "map"
            ]
        return self._cached_maps

    @property
    def rendered_certificates(self) -> List[RenderedContent]:
        """Get rendered certificates (cached)."""
        if self._cached_certificates is None:
            self._cached_certificates = [
                c for c in self.rendered_content if c.content_type == "certificate"
            ]
        return self._cached_certificates

    @property
    def rendered_files(self) -> List[RenderedContent]:
        """Get rendered files (cached)."""
        if self._cached_files is None:
            self._cached_files = [
                c for c in self.rendered_content if c.content_type == "file"
            ]
        return self._cached_files

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
        elif "dataplane_auth" in error_str or "validation_auth" in error_str:
            error_msg += "\n\n🔧 CREDENTIALS MOVED TO SECRET:\nAuthentication fields are no longer supported in ConfigMaps. You must provide credentials via a Kubernetes Secret using --secret-name parameter.\n\n"

        error_msg += f"\nDETAILED ERROR:\n{e}"

        raise ValueError(error_msg) from e


WatchResourceCollection = Dict[str, WatchResourceConfig]
MapCollection = Dict[str, TemplateConfig]
TemplateSnippetCollection = Dict[str, TemplateSnippet]
CertificateCollection = Dict[str, TemplateConfig]
