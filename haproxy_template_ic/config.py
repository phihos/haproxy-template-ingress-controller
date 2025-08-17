"""
Configuration management for HAProxy Template IC using Pydantic models.

This module handles template rendering, snippet management, and provides
enhanced collection classes for working with configuration data.
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

# Import all Pydantic models and the main parsing function
from .config_models import (
    WatchResourceConfig,
    MapConfig,
    CertificateConfig,
    TemplateSnippet,
)

# -----------------------------------------------------------------------------
# Collection type aliases (plain dictionaries)
# -----------------------------------------------------------------------------

# Collections are now just plain dictionaries for simplicity
WatchResourceCollection = Dict[str, WatchResourceConfig]
MapCollection = Dict[str, MapConfig]
TemplateSnippetCollection = Dict[str, TemplateSnippet]
CertificateCollection = Dict[str, CertificateConfig]

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
