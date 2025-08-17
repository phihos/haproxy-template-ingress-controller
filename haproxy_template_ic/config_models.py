"""
Pydantic models for HAProxy Template IC configuration.

This module contains all configuration models using Pydantic for automatic
validation, type coercion, and enhanced developer experience.
"""

from typing import Any, Dict, List, Optional

from jinja2 import Template
from pydantic import BaseModel, Field, validator


class ResourceFilter(BaseModel):
    """Filter for Kubernetes resources."""

    namespace_selector: Optional[Dict[str, str]] = Field(
        None, description="Namespace label selector"
    )
    label_selector: Optional[Dict[str, str]] = Field(
        None, description="Resource label selector"
    )

    @validator("namespace_selector", "label_selector")
    def validate_selector(cls, v):
        if v is not None and not isinstance(v, dict):
            raise ValueError("Selector must be a dictionary")
        return v

    class Config:
        frozen = True


class WatchResourceConfig(BaseModel):
    """Configuration for a Kubernetes resource to watch."""

    api_version: str = Field(
        ..., description="Kubernetes API version (e.g., 'v1', 'networking.k8s.io/v1')"
    )
    kind: str = Field(
        ..., description="Kubernetes resource kind (e.g., 'Service', 'Ingress')"
    )
    enable_validation_webhook: bool = Field(
        True, description="Enable webhook validation for this resource"
    )
    resource_filter: Optional[ResourceFilter] = Field(
        None, description="Optional resource filtering"
    )

    # Backward compatibility fields
    id: str = Field("", description="Resource ID (for backward compatibility)")
    group: Optional[str] = Field(None, description="Group (for backward compatibility)")
    version: Optional[str] = Field(
        None, description="Version (for backward compatibility)"
    )
    filter: Optional[ResourceFilter] = Field(
        None, description="Filter (for backward compatibility)"
    )

    def __init__(self, **data):
        # Handle backward compatibility: convert group/version to api_version
        if "api_version" not in data:
            group = data.get("group", "")
            version = data.get("version", "v1")
            if group:
                data["api_version"] = f"{group}/{version}"
            else:
                data["api_version"] = version

        # Handle filter -> resource_filter mapping
        if "filter" in data and "resource_filter" not in data:
            data["resource_filter"] = data["filter"]

        super().__init__(**data)

    @validator("api_version")
    def validate_api_version(cls, v):
        if not v or not isinstance(v, str):
            raise ValueError("api_version must be a non-empty string")
        # Basic format validation - should contain version info
        if "/" in v:
            group, version = v.rsplit("/", 1)
            if not group or not version:
                raise ValueError(
                    "api_version format should be 'group/version' or just 'version'"
                )
        return v

    @validator("kind")
    def validate_kind(cls, v):
        if not v or not isinstance(v, str):
            raise ValueError("kind must be a non-empty string")
        # Kind should be PascalCase
        if not v[0].isupper():
            raise ValueError("kind should start with uppercase letter (PascalCase)")
        return v

    class Config:
        # Allow arbitrary types for filters
        arbitrary_types_allowed = True


class MapConfig(BaseModel):
    """Configuration for HAProxy map files."""

    template: str = Field(..., description="Jinja2 template for the map content")
    compiled_template: Optional[Template] = Field(
        None, description="Compiled Jinja2 template (internal use)"
    )
    path: str = Field("", description="Map file path (for backward compatibility)")

    @validator("template", pre=True)
    def validate_template(cls, v):
        # Handle both string templates and Template objects for backward compatibility
        if isinstance(v, Template):
            # For tests that pass Template objects directly, extract template string
            # Template objects don't have source, so we create a dummy template string
            return "template from Template object"
        elif isinstance(v, str):
            if not v:
                raise ValueError("template must be a non-empty string")
            return v
        else:
            raise ValueError("template must be a string or Template object")

    def __init__(self, **data):
        # Handle Template objects passed directly
        if "template" in data and isinstance(data["template"], Template):
            template_obj = data["template"]
            data["template"] = "template from Template object"  # Store placeholder
            data["compiled_template"] = template_obj  # Store the actual template
        super().__init__(**data)

    class Config:
        # Allow Template objects (not JSON serializable but used internally)
        arbitrary_types_allowed = True


class TemplateSnippet(BaseModel):
    """Reusable template snippet."""

    name: str = Field(..., description="Snippet name for {% include %}")
    template: str = Field(..., description="Jinja2 template content")
    compiled_template: Optional[Template] = Field(
        None, description="Compiled Jinja2 template (internal use)"
    )
    source: str = Field(
        "", description="Source template string (for backward compatibility)"
    )

    @validator("name")
    def validate_name(cls, v):
        if not v or not isinstance(v, str):
            raise ValueError("name must be a non-empty string")
        # Basic validation for template include names
        if " " in v or "\n" in v:
            raise ValueError("name cannot contain spaces or newlines")
        return v

    @validator("template")
    def validate_template(cls, v):
        if not isinstance(v, str):
            raise ValueError("template must be a string")
        return v

    @validator("source", pre=True, always=True)
    def set_source_from_template(cls, v, values):
        # If source is not explicitly set, use template value
        if not v and "template" in values:
            return values["template"]
        return v

    class Config:
        # Allow Template objects (not JSON serializable but used internally)
        arbitrary_types_allowed = True


class CertificateConfig(BaseModel):
    """Configuration for TLS certificates."""

    template: str = Field(..., description="Jinja2 template for certificate content")
    compiled_template: Optional[Template] = Field(
        None, description="Compiled Jinja2 template (internal use)"
    )
    name: str = Field("", description="Certificate name (for backward compatibility)")

    @validator("template")
    def validate_template(cls, v):
        if not v or not isinstance(v, str):
            raise ValueError("template must be a non-empty string")
        return v

    class Config:
        # Allow Template objects (not JSON serializable but used internally)
        arbitrary_types_allowed = True


class PodSelector(BaseModel):
    """Selector for HAProxy pods."""

    match_labels: Dict[str, str] = Field(
        ..., description="Labels to match HAProxy pods"
    )

    @validator("match_labels")
    def validate_labels(cls, v):
        if not v:
            raise ValueError("match_labels cannot be empty")
        for key, value in v.items():
            if not isinstance(key, str) or not isinstance(value, str):
                raise ValueError("All label keys and values must be strings")
        return v

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
    maps: Dict[str, MapConfig] = Field(
        default_factory=dict, description="HAProxy map files"
    )
    template_snippets: Dict[str, TemplateSnippet] = Field(
        default_factory=dict, description="Reusable template snippets"
    )
    certificates: Dict[str, CertificateConfig] = Field(
        default_factory=dict, description="TLS certificates"
    )

    # Raw configuration for backward compatibility
    raw: Optional[Dict[str, Any]] = Field(
        None, description="Raw configuration dictionary"
    )

    @validator("maps")
    def validate_map_paths(cls, v):
        """Validate that map paths are absolute."""
        for path in v.keys():
            if not path.startswith("/"):
                raise ValueError(f"Map path must be absolute: {path}")
        return v

    @validator("certificates")
    def validate_cert_paths(cls, v):
        """Validate that certificate paths are absolute."""
        for path in v.keys():
            if not path.startswith("/"):
                raise ValueError(f"Certificate path must be absolute: {path}")
        return v

    @validator("template_snippets")
    def validate_snippet_names(cls, v):
        """Validate snippet names for template inclusion."""
        for name, snippet in v.items():
            if name != snippet.name:
                raise ValueError(
                    f"Snippet key '{name}' must match snippet.name '{snippet.name}'"
                )
        return v

    class Config:
        # Allow extra fields for future extensibility
        extra = "forbid"
        # Validate assignment to catch errors early
        validate_assignment = True
        # Allow Template objects (not JSON serializable but used internally)
        arbitrary_types_allowed = True


class RenderedMap(BaseModel):
    """Rendered HAProxy map file."""

    path: str = Field(..., description="Absolute path to the map file")
    content: str = Field(..., description="Rendered map content")
    map_config: Optional["MapConfig"] = Field(
        None, description="Source map configuration"
    )

    @validator("path")
    def validate_path(cls, v):
        if not v.startswith("/"):
            raise ValueError("Map path must be absolute")
        return v

    class Config:
        # Allow arbitrary types for MapConfig
        arbitrary_types_allowed = True


class RenderedConfig(BaseModel):
    """Rendered HAProxy configuration."""

    content: str = Field(..., description="Rendered configuration content")

    @validator("content")
    def validate_content(cls, v):
        if not v or not isinstance(v, str):
            raise ValueError("content must be a non-empty string")
        return v

    class Config:
        frozen = True


class RenderedCertificate(BaseModel):
    """Rendered TLS certificate."""

    path: str = Field(..., description="Absolute path to the certificate file")
    content: str = Field(..., description="Rendered certificate content")

    @validator("path")
    def validate_path(cls, v):
        if not v.startswith("/"):
            raise ValueError("Certificate path must be absolute")
        return v

    class Config:
        frozen = True


class TemplateContext(BaseModel):
    """Context for template rendering."""

    resources: Dict[str, Dict[str, Any]] = Field(
        default_factory=dict, description="Kubernetes resources organized by type"
    )
    namespace: Optional[str] = Field(None, description="Current namespace")

    # Helper methods that return typed collections
    def get_watched_resources(self) -> Dict[str, WatchResourceConfig]:
        """Get watched resources as a typed collection."""
        return getattr(self, "watched_resources", {})

    def get_maps(self) -> Dict[str, MapConfig]:
        """Get maps as a typed collection."""
        return getattr(self, "maps", {})

    def get_template_snippets(self) -> Dict[str, TemplateSnippet]:
        """Get template snippets as a typed collection."""
        return getattr(self, "template_snippets", {})

    def get_certificates(self) -> Dict[str, CertificateConfig]:
        """Get certificates as a typed collection."""
        return getattr(self, "certificates", {})

    class Config:
        # Allow extra fields for extensibility
        extra = "allow"


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

    This replaces the manual parsing logic with Pydantic's automatic validation.
    """
    try:
        # Transform old config format to new Pydantic format
        transformed_data = _transform_legacy_config(data)

        # Store raw data for backward compatibility
        transformed_data["raw"] = data

        # Use Pydantic parsing for basic validation
        config = Config.parse_obj(transformed_data)

        # Now compile templates - this is done post-validation to handle includes
        _compile_templates_in_config(config)

        return config
    except Exception as e:
        # Re-raise with more context for debugging
        raise ValueError(f"Configuration validation failed: {e}") from e


def _transform_legacy_config(data: Dict[str, Any]) -> Dict[str, Any]:
    """Transform legacy config format to new Pydantic format."""
    result = data.copy()

    # Transform template_snippets from dict of name->string to dict of name->TemplateSnippet
    if "template_snippets" in result:
        snippets = {}
        for name, template_str in result["template_snippets"].items():
            snippets[name] = {
                "name": name,
                "template": template_str,
                "source": template_str,
            }
        result["template_snippets"] = snippets

    # Transform maps from dict of path->{template: str} to dict of path->MapConfig
    if "maps" in result:
        maps = {}
        for path, config in result["maps"].items():
            if isinstance(config, dict) and "template" in config:
                maps[path] = {"template": config["template"], "path": path}
            else:
                maps[path] = {"template": str(config), "path": path}
        result["maps"] = maps

    # Transform certificates from dict of name->{template: str} to dict of name->CertificateConfig
    if "certificates" in result:
        certificates = {}
        for name, config in result["certificates"].items():
            if isinstance(config, dict) and "template" in config:
                certificates[name] = {"template": config["template"], "name": name}
            else:
                certificates[name] = {"template": str(config), "name": name}
        result["certificates"] = certificates

    # Transform haproxy_config from {template: str} to MapConfig format
    if "haproxy_config" in result:
        config = result["haproxy_config"]
        if isinstance(config, dict) and "template" in config:
            result["haproxy_config"] = {
                "template": config["template"],
                "path": "/etc/haproxy/haproxy.cfg",  # Default path
            }
        else:
            result["haproxy_config"] = {
                "template": str(config),
                "path": "/etc/haproxy/haproxy.cfg",
            }

    # Transform watched_resources from legacy format to new format
    if "watched_resources" in result:
        resources = {}
        watch_data = result["watched_resources"]

        if isinstance(watch_data, dict):
            # New dict format: {id: {kind: ..., api_version: ...}}
            for resource_id, config in watch_data.items():
                if isinstance(config, dict):
                    # Handle different formats for api_version/group/version
                    api_version = config.get("api_version")
                    if not api_version:
                        # Legacy format with separate group/version
                        group = config.get("group", "")
                        version = config.get("version", "v1")
                        if group:
                            api_version = f"{group}/{version}"
                        else:
                            api_version = version

                    resources[resource_id] = {
                        "api_version": api_version,
                        "kind": config["kind"],
                        "enable_validation_webhook": config.get(
                            "enable_validation_webhook", False
                        ),
                        "resource_filter": config.get("filter"),
                    }
        elif isinstance(watch_data, list):
            # Legacy list format: [{id: ..., kind: ...}]
            for i, config in enumerate(watch_data):
                resource_id = config.get("id", str(i))
                api_version = config.get("api_version")
                if not api_version:
                    group = config.get("group", "")
                    version = config.get("version", "v1")
                    if group:
                        api_version = f"{group}/{version}"
                    else:
                        api_version = version

                resources[resource_id] = {
                    "api_version": api_version,
                    "kind": config["kind"],
                    "enable_validation_webhook": config.get(
                        "enable_validation_webhook", False
                    ),
                    "resource_filter": config.get("filter"),
                }

        result["watched_resources"] = resources

    return result


def _compile_templates_in_config(config: Config) -> None:
    """Compile all templates in the configuration with snippet support."""
    from jinja2 import TemplateSyntaxError
    from .config import get_template_environment

    try:
        # First compile template snippets (they don't depend on other snippets)
        env = get_template_environment()
        for snippet in config.template_snippets.values():
            if not snippet.compiled_template:
                # Use object.__setattr__ to bypass Pydantic immutability
                object.__setattr__(
                    snippet, "compiled_template", env.from_string(snippet.template)
                )

        # Now compile other templates with snippet support
        env_with_snippets = get_template_environment(config.template_snippets)

        # Compile haproxy_config template
        if not config.haproxy_config.compiled_template:
            object.__setattr__(
                config.haproxy_config,
                "compiled_template",
                env_with_snippets.from_string(config.haproxy_config.template),
            )

        # Compile map templates
        for map_config in config.maps.values():
            if not map_config.compiled_template:
                object.__setattr__(
                    map_config,
                    "compiled_template",
                    env_with_snippets.from_string(map_config.template),
                )

        # Compile certificate templates
        for cert_config in config.certificates.values():
            if not cert_config.compiled_template:
                object.__setattr__(
                    cert_config,
                    "compiled_template",
                    env_with_snippets.from_string(cert_config.template),
                )

    except TemplateSyntaxError as e:
        raise ValueError(f"Template compilation failed: {e}") from e


# Type aliases for collections (maintains compatibility)
WatchResourceCollection = Dict[str, WatchResourceConfig]
MapCollection = Dict[str, MapConfig]
TemplateSnippetCollection = Dict[str, TemplateSnippet]
CertificateCollection = Dict[str, CertificateConfig]
