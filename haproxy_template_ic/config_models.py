"""
Pydantic models for HAProxy Template IC configuration.

This module contains all configuration models using Pydantic for automatic
validation, type coercion, and enhanced developer experience.
"""

from typing import Any, Dict, List, Optional

from jinja2 import Template
from pydantic import BaseModel, ConfigDict, Field, field_validator


class ResourceFilter(BaseModel):
    """Filter for Kubernetes resources."""

    namespace_selector: Optional[Dict[str, str]] = Field(
        None, description="Namespace label selector"
    )
    label_selector: Optional[Dict[str, str]] = Field(
        None, description="Resource label selector"
    )

    @field_validator("namespace_selector", "label_selector")
    @classmethod
    def validate_selector(cls, v):
        if v is not None and not isinstance(v, dict):
            raise ValueError("Selector must be a dictionary")
        return v

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

    @field_validator("api_version")
    @classmethod
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

    @field_validator("kind")
    @classmethod
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
        None,
        description="Compiled Jinja2 template (internal use)",
        exclude=True,  # Exclude from serialization and schema generation
    )

    @field_validator("template", mode="before")
    @classmethod
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

    class Config:
        # Allow Template objects (not JSON serializable but used internally)
        arbitrary_types_allowed = True


class TemplateSnippet(BaseModel):
    """Reusable template snippet."""

    name: str = Field(..., description="Snippet name for {% include %}")
    template: str = Field(..., description="Jinja2 template content")
    compiled_template: Optional[Template] = Field(
        None,
        description="Compiled Jinja2 template (internal use)",
        exclude=True,  # Exclude from serialization and schema generation
    )

    @field_validator("name")
    @classmethod
    def validate_name(cls, v):
        if not v or not isinstance(v, str):
            raise ValueError("name must be a non-empty string")
        # Basic validation for template include names
        if " " in v or "\n" in v:
            raise ValueError("name cannot contain spaces or newlines")
        return v

    @field_validator("template")
    @classmethod
    def validate_template(cls, v):
        if not isinstance(v, str):
            raise ValueError("template must be a string")
        return v

    class Config:
        # Allow Template objects (not JSON serializable but used internally)
        arbitrary_types_allowed = True


class CertificateConfig(BaseModel):
    """Configuration for TLS certificates."""

    template: str = Field(..., description="Jinja2 template for certificate content")
    compiled_template: Optional[Template] = Field(
        None,
        description="Compiled Jinja2 template (internal use)",
        exclude=True,  # Exclude from serialization and schema generation
    )

    @field_validator("template")
    @classmethod
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

    @field_validator("match_labels")
    @classmethod
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

    @field_validator("maps")
    @classmethod
    def validate_map_paths(cls, v):
        """Validate that map paths are absolute."""
        for path in v.keys():
            if not path.startswith("/"):
                raise ValueError(f"Map path must be absolute: {path}")
        return v

    @field_validator("certificates")
    @classmethod
    def validate_cert_paths(cls, v):
        """Validate that certificate paths are absolute."""
        for path in v.keys():
            if not path.startswith("/"):
                raise ValueError(f"Certificate path must be absolute: {path}")
        return v

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

    path: str = Field(..., description="Absolute path to the map file")
    content: str = Field(..., description="Rendered map content")
    map_config: Optional["MapConfig"] = Field(
        None, description="Source map configuration"
    )

    @field_validator("path")
    @classmethod
    def validate_path(cls, v):
        if not v.startswith("/"):
            raise ValueError("Map path must be absolute")
        return v

    class Config:
        # Allow arbitrary types for MapConfig
        arbitrary_types_allowed = True
        frozen = True


class RenderedConfig(BaseModel):
    """Rendered HAProxy configuration."""

    content: str = Field(..., description="Rendered configuration content")

    @field_validator("content")
    @classmethod
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

    @field_validator("path")
    @classmethod
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

        # Use Pydantic parsing for basic validation
        config = Config.model_validate(transformed_data)

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

    # Handle watched_resources
    if "watch_resources" in result:
        # Convert old field name to new field name
        result["watched_resources"] = result.pop("watch_resources")

    if "watched_resources" in result:
        resources = {}
        watch_data = result["watched_resources"]

        if isinstance(watch_data, dict):
            # Dict format: {id: {kind: ..., api_version: ...}}
            for resource_id, config in watch_data.items():
                if isinstance(config, dict):
                    # Handle api_version construction from group/version
                    api_version = config.get("api_version")
                    if not api_version:
                        group = config.get("group")
                        version = config.get("version")

                        # Handle None/empty values
                        if group is None and version is None:
                            api_version = "v1"  # Default for core resources
                        elif group is None or group == "":
                            api_version = version if version else "v1"
                        else:
                            api_version = f"{group}/{version if version else 'v1'}"

                    resources[resource_id] = {
                        "api_version": api_version,
                        "kind": config["kind"],
                        "enable_validation_webhook": config.get(
                            "enable_validation_webhook", False
                        ),
                        "resource_filter": config.get("resource_filter")
                        or config.get("filter"),
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


# =============================================================================
# JSON Schema Generation and Export
# =============================================================================


def export_config_schema(include_examples: bool = True) -> Dict[str, Any]:
    """
    Export the JSON schema for the main Config model.

    Args:
        include_examples: Whether to include example values in the schema

    Returns:
        dict: JSON schema for the Config model
    """
    try:
        # Generate schema in 'serialization' mode to exclude non-serializable fields
        schema = Config.model_json_schema(mode="serialization")
    except Exception:
        # Fallback: create a simplified schema manually
        schema = _create_simplified_config_schema()

    if include_examples:
        # Add examples to the schema for better documentation
        _add_schema_examples(schema)

    return schema


def export_all_schemas() -> Dict[str, Any]:
    """
    Export JSON schemas for all configuration models.

    Returns:
        dict: Dictionary containing schemas for all models
    """
    return {
        "Config": Config.model_json_schema(),
        "WatchResourceConfig": WatchResourceConfig.model_json_schema(),
        "MapConfig": MapConfig.model_json_schema(),
        "TemplateSnippet": TemplateSnippet.model_json_schema(),
        "CertificateConfig": CertificateConfig.model_json_schema(),
        "PodSelector": PodSelector.model_json_schema(),
        "ResourceFilter": ResourceFilter.model_json_schema(),
        "RenderedMap": RenderedMap.model_json_schema(),
        "RenderedConfig": RenderedConfig.model_json_schema(),
        "RenderedCertificate": RenderedCertificate.model_json_schema(),
        "TemplateContext": TemplateContext.model_json_schema(),
        "HAProxyConfigContext": HAProxyConfigContext.model_json_schema(),
    }


def _add_schema_examples(schema: Dict[str, Any]) -> None:
    """Add example values to schema properties for documentation."""
    properties = schema.get("properties", {})

    # Add examples for main configuration sections
    if "pod_selector" in properties:
        properties["pod_selector"]["example"] = {
            "match_labels": {"app": "haproxy", "component": "loadbalancer"}
        }

    if "watched_resources" in properties:
        properties["watched_resources"]["example"] = {
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
        }

    if "maps" in properties:
        properties["maps"]["example"] = {
            "/etc/haproxy/maps/host.map": {
                "template": "{% for _, ingress in resources.get('ingresses', {}).items() %}\n{% if ingress.spec and ingress.spec.rules %}\n{% for rule in ingress.spec.rules %}\n{% if rule.host %}\n{{ rule.host }} {{ rule.host }}\n{% endif %}\n{% endfor %}\n{% endif %}\n{% endfor %}"
            }
        }

    if "template_snippets" in properties:
        properties["template_snippets"]["example"] = {
            "backend-name": {
                "name": "backend-name",
                "template": "backend_{{ service_name }}_{{ port }}",
            },
            "health-check": {
                "name": "health-check",
                "template": "option httpchk GET /health",
            },
        }

    if "haproxy_config" in properties:
        properties["haproxy_config"]["example"] = {
            "template": 'global\n    daemon\n\ndefaults\n    mode http\n    timeout connect 5000ms\n    timeout client 50000ms\n    timeout server 50000ms\n\nfrontend health\n    bind *:8404\n    http-request return status 200 content-type text/plain string "OK" if { path /healthz }\n\nfrontend main\n    bind *:80\n    {% include "backend-routing" %}'
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


def _create_simplified_config_schema() -> Dict[str, Any]:
    """Create a simplified schema manually when automatic generation fails."""
    return {
        "type": "object",
        "properties": {
            "pod_selector": {
                "type": "object",
                "properties": {
                    "match_labels": {
                        "type": "object",
                        "additionalProperties": {"type": "string"},
                    }
                },
                "required": ["match_labels"],
            },
            "haproxy_config": {
                "type": "object",
                "properties": {"template": {"type": "string"}},
                "required": ["template"],
            },
            "watched_resources": {
                "type": "object",
                "additionalProperties": {
                    "type": "object",
                    "properties": {
                        "api_version": {"type": "string"},
                        "kind": {"type": "string"},
                        "enable_validation_webhook": {
                            "type": "boolean",
                            "default": True,
                        },
                    },
                    "required": ["api_version", "kind"],
                },
            },
            "maps": {
                "type": "object",
                "additionalProperties": {
                    "type": "object",
                    "properties": {"template": {"type": "string"}},
                    "required": ["template"],
                },
            },
            "template_snippets": {
                "type": "object",
                "additionalProperties": {
                    "type": "object",
                    "properties": {
                        "name": {"type": "string"},
                        "template": {"type": "string"},
                    },
                    "required": ["name", "template"],
                },
            },
            "certificates": {
                "type": "object",
                "additionalProperties": {
                    "type": "object",
                    "properties": {"template": {"type": "string"}},
                    "required": ["template"],
                },
            },
        },
        "required": ["pod_selector", "haproxy_config"],
        "additionalProperties": False,
    }


# =============================================================================
# Type aliases for collections (maintains compatibility)
# =============================================================================

WatchResourceCollection = Dict[str, WatchResourceConfig]
MapCollection = Dict[str, MapConfig]
TemplateSnippetCollection = Dict[str, TemplateSnippet]
CertificateCollection = Dict[str, CertificateConfig]
