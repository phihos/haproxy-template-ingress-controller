"""
Templating functionality for HAProxy Template IC.

This module provides Jinja2-based template compilation, rendering, and caching
functionality including support for template snippets and custom filters.
"""

import base64
from functools import lru_cache
from typing import Any, Callable, Dict, Optional

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

# -----------------------------------------------------------------------------
# Jinja2 setup and template functionality
# -----------------------------------------------------------------------------


def b64decode_filter(value: str) -> str:
    """Custom Jinja2 filter to decode base64 strings."""
    try:
        return base64.b64decode(value).decode("utf-8")
    except Exception as e:
        raise ValueError(f"Failed to decode base64 value: {e}") from e


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
) -> Environment:
    """Get or create a Jinja2 environment with snippet support."""
    # Create snippet loader
    snippet_loader = SnippetLoader(snippets)

    # Create environment with custom loader and filters
    env = Environment(
        loader=snippet_loader,
        autoescape=False,  # HAProxy config shouldn't be HTML-escaped  # nosec B701
        trim_blocks=True,
        lstrip_blocks=True,
    )

    # Add custom filters
    env.filters["b64decode"] = b64decode_filter

    return env


class TemplateEnvironmentFactory:
    """Factory for creating Jinja2 environments with snippet support."""

    @staticmethod
    def create_environment(
        snippets: Optional[TemplateSnippetCollection] = None,
    ) -> Environment:
        """Create a Jinja2 environment with the given snippets."""
        return get_template_environment(snippets)


class TemplateCompiler:
    """Service for compiling Jinja2 templates with dependency injection."""

    def __init__(self, snippets: Optional[TemplateSnippetCollection] = None):
        """Initialize the compiler with template snippets."""
        self.environment = TemplateEnvironmentFactory.create_environment(snippets)

    def compile_template(self, template_string: str) -> Template:
        """Compile a template string into a Jinja2 Template object."""
        return self.environment.from_string(template_string)


# -----------------------------------------------------------------------------
# Template compilation and caching
# -----------------------------------------------------------------------------


@lru_cache(maxsize=256)
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
        raise ValueError(f"Template syntax error: {e}") from e


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
    except Exception as e:
        raise ValueError(f"Template rendering failed: {e}") from e


# -----------------------------------------------------------------------------
# Template Renderer with Caching
# -----------------------------------------------------------------------------


class TemplateRenderer:
    """Manages template compilation and rendering with caching.

    This class encapsulates all template operations and caches compiled templates
    for efficient reuse. Templates are compiled once and cached by their content.
    """

    def __init__(self, template_snippets: Optional[TemplateSnippetCollection] = None):
        """Initialize the renderer with template snippets.

        Args:
            template_snippets: Collection of reusable template snippets
        """
        self._compiler = TemplateCompiler(template_snippets)
        self._compiled_templates: Dict[str, Template] = {}

    @classmethod
    def from_config(cls, config) -> "TemplateRenderer":
        """Create a TemplateRenderer from a Config object.

        Args:
            config: Config object containing template snippets

        Returns:
            TemplateRenderer instance configured with the config's snippets
        """
        return cls(template_snippets=config.template_snippets)

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
            raise ValueError(f"Template rendering failed: {e}") from e

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
                raise ValueError(f"Template compilation failed: {e}") from e

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
            self.get_compiled(template_str)
        except TemplateSyntaxError as e:
            warnings.append(f"Invalid template syntax: {e}")
        except TemplateNotFound as e:
            warnings.append(f"Template snippet not found: {e}")
        except Exception as e:
            warnings.append(f"Template error: {e}")
        return warnings


def validate_config_templates(config_dict: dict) -> list[str]:
    """Validate all templates in a configuration dictionary.

    Args:
        config_dict: Configuration dictionary to validate

    Returns:
        List of warning messages (empty if all valid)
    """
    warnings = []

    # Extract snippets for validation environment
    snippets = {}
    snippets_raw = config_dict.get("template_snippets", {})
    for snippet_name, snippet_data in snippets_raw.items():
        if isinstance(snippet_data, dict) and "template" in snippet_data:
            snippets[snippet_name] = snippet_data["template"]
        elif isinstance(snippet_data, str):
            snippets[snippet_name] = snippet_data
        else:
            try:
                snippets[snippet_name] = getattr(
                    snippet_data, "template", str(snippet_data)
                )
            except Exception:
                snippets[snippet_name] = str(snippet_data)

    renderer = TemplateRenderer(snippets)

    # Validate template snippets
    for snippet_name, snippet_template in snippets.items():
        snippet_warnings = renderer.validate_template(snippet_template)
        for warning in snippet_warnings:
            warnings.append(f"Snippet '{snippet_name}': {warning}")

    # Validate maps
    maps = config_dict.get("maps", {})
    for map_path, map_config in maps.items():
        if isinstance(map_config, dict) and "template" in map_config:
            map_warnings = renderer.validate_template(map_config["template"])
            for warning in map_warnings:
                warnings.append(f"Map '{map_path}': {warning}")

    # Validate HAProxy config
    haproxy_config = config_dict.get("haproxy_config", {})
    if isinstance(haproxy_config, dict) and "template" in haproxy_config:
        haproxy_warnings = renderer.validate_template(haproxy_config["template"])
        for warning in haproxy_warnings:
            warnings.append(f"HAProxy config: {warning}")

    # Validate certificates
    certificates = config_dict.get("certificates", {})
    for cert_path, cert_config in certificates.items():
        if isinstance(cert_config, dict) and "template" in cert_config:
            cert_warnings = renderer.validate_template(cert_config["template"])
            for warning in cert_warnings:
                warnings.append(f"Certificate '{cert_path}': {warning}")

    return warnings
