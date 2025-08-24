"""
Templating functionality for HAProxy Template IC.

This module provides Jinja2-based template compilation, rendering, and caching
functionality including support for template snippets and custom filters.
"""

import base64
import os
import unicodedata
import urllib.parse
from functools import lru_cache
from typing import Any, Callable, Dict, Optional

import jinja2
from jinja2 import (
    BaseLoader,
    Environment,
    Template,
    TemplateSyntaxError,
    TemplateNotFound,
)

# Import Pydantic models and collection type aliases
from .config_models import (
    TemplateSnippetCollection,
)
from .constants import (
    ERROR_TEMPLATE_COMPILATION,
    ERROR_TEMPLATE_GENERIC,
    ERROR_TEMPLATE_INVALID_SYNTAX,
    ERROR_TEMPLATE_RENDER,
    ERROR_TEMPLATE_SNIPPET_NOT_FOUND,
    ERROR_TEMPLATE_SYNTAX,
    TEMPLATE_CACHE_SIZE,
)

# -----------------------------------------------------------------------------
# Jinja2 setup and template functionality
# -----------------------------------------------------------------------------


def b64decode_filter(value: str) -> str:
    """Custom Jinja2 filter to decode base64 strings."""
    try:
        return base64.b64decode(value).decode("utf-8")
    except (ValueError, TypeError, UnicodeDecodeError) as e:
        raise ValueError(f"Failed to decode base64 value: {e}") from e


def get_path_filter(filename: str, content_type: str, config=None) -> str:
    """Custom Jinja2 filter to resolve full paths from filenames with security validation.

    Args:
        filename: The filename without path
        content_type: Type of content ("map", "certificate", or "file")
        config: Configuration object containing storage directories

    Returns:
        Full path to the file based on content type and configuration

    Example:
        {{ "500.http" | get_path("file") }} -> "/etc/haproxy/general/500.http"
        {{ "host.map" | get_path("map") }} -> "/etc/haproxy/maps/host.map"

    Raises:
        ValueError: If filename contains invalid characters or content_type is unknown
    """
    # Validate filename for security with comprehensive normalization
    if not filename or not isinstance(filename, str):
        raise ValueError(f"Invalid filename: {filename}")

    # Defense in depth: Multiple layers of validation

    # Layer 1: URL decode the filename to catch encoded attacks
    try:
        decoded_filename = urllib.parse.unquote(filename, errors="strict")
    except UnicodeDecodeError:
        raise ValueError(f"Invalid filename encoding: {filename}")

    # Layer 2: Normalize Unicode to catch Unicode variations
    normalized_filename = unicodedata.normalize("NFKC", decoded_filename)

    # Layer 3: Check if normalization/decoding revealed encoded sequences
    if "%" in normalized_filename:
        raise ValueError(
            f"Filename contains encoded sequences after normalization: {filename}"
        )

    # Layer 4: Check for path traversal attempts and dangerous characters
    # Apply checks to both original and normalized filenames for completeness
    for check_filename in [filename, normalized_filename]:
        if (
            ".." in check_filename
            or "/" in check_filename
            or "\\" in check_filename
            or "\x00" in check_filename
            or check_filename in (".", "..")
            # Additional checks for common path separator Unicode variants
            or "\u002f" in check_filename  # Unicode forward slash
            or "\u005c" in check_filename  # Unicode backslash
            or "\u2044" in check_filename  # Unicode fraction slash
            or "\u2215" in check_filename  # Unicode division slash
        ):
            raise ValueError(
                f"Invalid filename contains prohibited characters: {filename}"
            )

    # Layer 5: Final whitelist validation - only safe characters allowed
    import re

    if not re.match(r"^[a-zA-Z0-9][a-zA-Z0-9._-]*$", normalized_filename):
        raise ValueError(
            f"Filename contains unsafe characters (only alphanumeric, dots, hyphens, underscores allowed): {filename}"
        )

    # Use normalized filename for further processing
    filename = normalized_filename

    # Validate content_type
    valid_types = {"map", "certificate", "file"}
    if content_type not in valid_types:
        raise ValueError(
            f"Invalid content_type '{content_type}'. Must be one of: {valid_types}"
        )

    # Get base directory
    if config is None:
        # Fallback to defaults if no config provided
        base_dirs = {
            "map": "/etc/haproxy/maps",
            "certificate": "/etc/haproxy/ssl",
            "file": "/etc/haproxy/general",
        }
        base_dir = base_dirs[content_type]
    else:
        # Use config storage directories
        base_dirs = {
            "map": config.storage_maps_dir,
            "certificate": config.storage_ssl_dir,
            "file": config.storage_general_dir,
        }
        base_dir = base_dirs[content_type]

    # Construct and validate path
    full_path = os.path.join(base_dir, filename)
    normalized_path = os.path.normpath(full_path)
    normalized_base = os.path.normpath(base_dir)

    # Ensure path doesn't escape base directory
    if (
        not normalized_path.startswith(normalized_base + os.sep)
        and normalized_path != normalized_base
    ):
        raise ValueError(
            f"Path traversal detected for filename '{filename}' in {content_type}"
        )

    return normalized_path


class SnippetLoader(BaseLoader):
    """Custom Jinja2 loader that can resolve template snippets by name."""

    def __init__(self, snippets: Optional[TemplateSnippetCollection] = None):
        self.snippets = snippets if snippets is not None else {}

    def get_source(
        self, environment: Environment, template: str
    ) -> tuple[str, Optional[str], Optional[Callable]]:
        """Get template source for snippet name."""
        # Handle snippets dict (current format)
        snippet = self.snippets.get(template)

        if snippet is None:
            raise TemplateNotFound(template)

        # Get template content from snippet
        source = snippet.template if hasattr(snippet, "template") else str(snippet)
        return source, None, lambda: True


def get_template_environment(
    snippets: Optional[TemplateSnippetCollection] = None,
    config=None,
) -> Environment:
    """Get or create a Jinja2 environment with snippet support."""
    # Create snippet loader
    snippet_loader = SnippetLoader(snippets)

    # Create environment with custom loader and filters
    env = Environment(
        loader=snippet_loader,
        autoescape=False,  # HAProxy config shouldn't be HTML-escaped  # nosec B701
        trim_blocks=False,  # Rely on manual whitespace control to create fewer surprises
        lstrip_blocks=False,  # Rely on manual whitespace control to create fewer surprises
        extensions=["jinja2.ext.do"],  # Enable do extension for {% do %} statements
    )

    # Add custom filters
    env.filters["b64decode"] = b64decode_filter

    # Add get_path filter with config access
    def get_path_with_config(filename: str, content_type: str) -> str:
        return get_path_filter(filename, content_type, config)

    env.filters["get_path"] = get_path_with_config

    return env


class TemplateEnvironmentFactory:
    """Factory for creating Jinja2 environments with snippet support."""

    @staticmethod
    def create_environment(
        snippets: Optional[TemplateSnippetCollection] = None,
        config=None,
    ) -> Environment:
        """Create a Jinja2 environment with the given snippets."""
        return get_template_environment(snippets, config)


class TemplateCompiler:
    """Service for compiling Jinja2 templates with dependency injection."""

    def __init__(
        self, snippets: Optional[TemplateSnippetCollection] = None, config=None
    ):
        """Initialize the compiler with template snippets."""
        self.environment = TemplateEnvironmentFactory.create_environment(
            snippets, config
        )

    def compile_template(self, template_string: str) -> Template:
        """Compile a template string into a Jinja2 Template object."""
        return self.environment.from_string(template_string)


# -----------------------------------------------------------------------------
# Template compilation and caching
# -----------------------------------------------------------------------------


@lru_cache(maxsize=TEMPLATE_CACHE_SIZE)
def compile_template(
    template_str: str, snippets_tuple: Optional[tuple] = None
) -> Template:
    """Compile a template string with caching."""
    # Convert tuple back to dict for snippet environment
    snippets = dict(snippets_tuple) if snippets_tuple else None
    env = get_template_environment(snippets)

    try:
        return env.from_string(template_str)
    except TemplateSyntaxError as e:
        raise ValueError(ERROR_TEMPLATE_SYNTAX.format(error=e)) from e


def render_template(
    template_str: str,
    context: Dict[str, Any],
    snippets: Optional[TemplateSnippetCollection] = None,
) -> str:
    """Render a template with the given context and snippets."""
    # Convert snippets to tuple for caching
    snippets_tuple = tuple(snippets.items()) if snippets else None

    try:
        template = compile_template(template_str, snippets_tuple)
        return template.render(**context)
    except (jinja2.TemplateError, ValueError, TypeError) as e:
        raise ValueError(ERROR_TEMPLATE_RENDER.format(error=e)) from e


# -----------------------------------------------------------------------------
# Template Renderer with Caching
# -----------------------------------------------------------------------------


class TemplateRenderer:
    """Manages template compilation and rendering with caching.

    This class encapsulates all template operations and caches compiled templates
    for efficient reuse. Templates are compiled once and cached by their content.
    """

    def __init__(
        self, template_snippets: Optional[TemplateSnippetCollection] = None, config=None
    ):
        """Initialize the renderer with template snippets.

        Args:
            template_snippets: Collection of reusable template snippets
            config: Configuration object for get_path filter
        """
        self._compiler = TemplateCompiler(template_snippets, config)
        self._compiled_templates: Dict[str, Template] = {}

    @classmethod
    def from_config(cls, config) -> "TemplateRenderer":
        """Create a TemplateRenderer from a Config object.

        Args:
            config: Config object containing template snippets

        Returns:
            TemplateRenderer instance configured with the config's snippets
        """
        return cls(template_snippets=config.template_snippets, config=config)

    def render(self, template_str: str, **context: Any) -> str:
        """Compile (with caching) and render a template.

        Args:
            template_str: Template string to compile and render
            **context: Template variables for rendering

        Returns:
            Rendered template content

        Raises:
            ValueError: If template compilation or rendering fails
        """
        try:
            template = self.get_compiled(template_str)
            return template.render(**context)
        except Exception as e:
            raise ValueError(ERROR_TEMPLATE_RENDER.format(error=e)) from e

    def get_compiled(self, template_str: str) -> Template:
        """Get compiled template (for cases where render is called separately).

        Templates are compiled once and cached for subsequent use.

        Args:
            template_str: Template string to compile

        Returns:
            Compiled Jinja2 Template object

        Raises:
            ValueError: If template compilation fails
        """
        if template_str not in self._compiled_templates:
            try:
                self._compiled_templates[template_str] = (
                    self._compiler.compile_template(template_str)
                )
            except Exception as e:
                raise ValueError(ERROR_TEMPLATE_COMPILATION.format(error=e)) from e

        return self._compiled_templates[template_str]

    def clear_cache(self) -> None:
        """Clear the compiled template cache.

        Useful when template snippets change and templates need recompilation.
        """
        self._compiled_templates.clear()

    @property
    def cache_size(self) -> int:
        """Get the number of cached compiled templates."""
        return len(self._compiled_templates)

    def validate_template(self, template_str: str) -> list[str]:
        """Validate a template string and return any warnings.

        Args:
            template_str: Template string to validate

        Returns:
            List of warning messages (empty if valid)
        """
        warnings = []
        try:
            # Compile the template first
            compiled_template = self.get_compiled(template_str)
            # Try to render with empty context to catch TemplateNotFound errors
            compiled_template.render({})
        except TemplateSyntaxError as e:
            warnings.append(ERROR_TEMPLATE_INVALID_SYNTAX.format(error=e))
        except TemplateNotFound as e:
            warnings.append(ERROR_TEMPLATE_SNIPPET_NOT_FOUND.format(error=e))
        except Exception as e:
            warnings.append(ERROR_TEMPLATE_GENERIC.format(error=e))
        return warnings


def _extract_snippet_templates(config_dict: dict) -> TemplateSnippetCollection:
    """Extract snippet templates from config dictionary."""
    from .config_models import TemplateSnippet

    snippets = {}
    snippets_raw = config_dict.get("template_snippets", {})

    for snippet_name, snippet_data in snippets_raw.items():
        template_content = None
        if isinstance(snippet_data, dict) and "template" in snippet_data:
            template_content = snippet_data["template"]
        elif isinstance(snippet_data, str):
            template_content = snippet_data
        else:
            try:
                template_content = getattr(snippet_data, "template", str(snippet_data))
            except Exception:
                template_content = str(snippet_data)

        if template_content:
            snippets[snippet_name] = TemplateSnippet(
                name=snippet_name, template=template_content
            )

    return snippets


def _validate_snippets(
    snippets: TemplateSnippetCollection, renderer: TemplateRenderer
) -> list[str]:
    """Validate template snippets."""
    warnings = []
    for snippet_name, snippet_obj in snippets.items():
        snippet_warnings = renderer.validate_template(snippet_obj.template)
        for warning in snippet_warnings:
            warnings.append(f"Snippet '{snippet_name}': {warning}")
    return warnings


def _validate_template_collection(
    collection: dict, renderer: TemplateRenderer, collection_type: str
) -> list[str]:
    """Validate a collection of templates (maps, certificates, etc.)."""
    warnings = []
    for item_name, item_config in collection.items():
        if isinstance(item_config, dict) and "template" in item_config:
            item_warnings = renderer.validate_template(item_config["template"])
            for warning in item_warnings:
                warnings.append(f"{collection_type} '{item_name}': {warning}")
    return warnings


def _validate_haproxy_config(
    config_dict: dict, renderer: TemplateRenderer
) -> list[str]:
    """Validate HAProxy main configuration template."""
    warnings = []
    haproxy_config = config_dict.get("haproxy_config", {})
    if isinstance(haproxy_config, dict) and "template" in haproxy_config:
        haproxy_warnings = renderer.validate_template(haproxy_config["template"])
        for warning in haproxy_warnings:
            warnings.append(f"HAProxy config: {warning}")
    return warnings


def validate_config_templates(config_dict: dict) -> list[str]:
    """Validate all templates in a configuration dictionary."""
    snippets = _extract_snippet_templates(config_dict)
    renderer = TemplateRenderer(snippets)

    warnings = []
    warnings.extend(_validate_snippets(snippets, renderer))
    warnings.extend(
        _validate_template_collection(config_dict.get("maps", {}), renderer, "Map")
    )
    warnings.extend(_validate_haproxy_config(config_dict, renderer))
    warnings.extend(
        _validate_template_collection(
            config_dict.get("certificates", {}), renderer, "Certificate"
        )
    )

    return warnings
