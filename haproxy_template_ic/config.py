"""
Configuration management for HAProxy Template IC using Pydantic models.

This module handles template rendering, snippet management, and provides
enhanced collection classes for working with configuration data.
"""

import base64
from functools import lru_cache
from typing import Any, Callable, Dict, List, Optional

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
    WatchResourceCollection as WatchResourceCollectionType,
    MapCollection as MapCollectionType,
    TemplateSnippetCollection as TemplateSnippetCollectionType,
    CertificateCollection as CertificateCollectionType,
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

    def __init__(self, snippets: Optional[TemplateSnippetCollectionType] = None):
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
    snippets: Optional[TemplateSnippetCollectionType] = None,
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
    snippets: Optional[TemplateSnippetCollectionType] = None,
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
# Enhanced collection classes with improved functionality
# -----------------------------------------------------------------------------


# Enhanced collection classes with backward compatibility for list initialization
class WatchResourceCollection(WatchResourceCollectionType):
    """Enhanced collection with backward compatibility."""

    def __init__(self, data=None):
        if data is None:
            super().__init__()
        elif isinstance(data, list):
            # Convert list to dict using id as key for backward compatibility
            dict_data = {}
            for item in data:
                key = (
                    item.id if hasattr(item, "id") and item.id else str(len(dict_data))
                )
                dict_data[key] = item
            super().__init__(dict_data)
        elif isinstance(data, dict):
            super().__init__(data)
        else:
            super().__init__()

    def by_id(self, resource_id: str) -> Optional[WatchResourceConfig]:
        """Get watch resource by ID."""
        return self.get(resource_id)

    def with_validation_enabled(self) -> List[WatchResourceConfig]:
        """Get all resources with validation webhook enabled."""
        return [config for config in self.values() if config.enable_validation_webhook]

    def by_api_version(self, api_version: str) -> List[WatchResourceConfig]:
        """Get all resources with specific API version."""
        return [config for config in self.values() if config.api_version == api_version]


# Use the type aliases from config_models.py as the base types
MapCollection = MapCollectionType
TemplateSnippetCollection = TemplateSnippetCollectionType
CertificateCollection = CertificateCollectionType


# All models are now imported from config_models.py - no duplicate definitions needed

# All models are now imported from config_models.py - type aliases are imported above
