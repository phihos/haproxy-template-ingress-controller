"""
Templating functionality for HAProxy Template IC.

This module provides Jinja2-based template compilation, rendering, and caching
functionality including support for template snippets and custom filters.
"""

import base64
import os
import re
import sys
from functools import lru_cache
from typing import Any, Callable, Dict, Optional, Union, Union

from pathvalidate import ValidationError, is_valid_filename, sanitize_filename

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
    TemplateSnippet,
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
# Constants and patterns
# -----------------------------------------------------------------------------

# Regex pattern for extracting snippet names from include statements
INCLUDE_PATTERN = re.compile(r'{%\s*include\s+["\']([^"\']+)["\']\s*%}')

# Context lines to show around errors
CONTEXT_LINES_BEFORE = 2
CONTEXT_LINES_AFTER = 3

# -----------------------------------------------------------------------------
# Jinja2 setup and template functionality
# -----------------------------------------------------------------------------


def b64decode_filter(value: str) -> str:
    """Custom Jinja2 filter to decode base64 strings."""
    try:
        return base64.b64decode(value).decode("utf-8")
    except (ValueError, TypeError, UnicodeDecodeError) as e:
        raise ValueError(f"Failed to decode base64 value: {e}") from e


def get_path_filter(
    filename: str, content_type: str, config: Optional[Any] = None
) -> str:
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
    # Validate and sanitize filename for security using pathvalidate + additional restrictions
    if not filename or not isinstance(filename, str):
        raise ValueError(f"Invalid filename: {filename}")

    # First validate with pathvalidate - handles platform-specific and Unicode issues
    if not is_valid_filename(filename):
        raise ValueError(f"Invalid filename contains prohibited characters: {filename}")

    # Additional security checks for our specific use case (stricter than pathvalidate)
    # Block directory names and path components
    if filename in (".", ".."):
        raise ValueError(f"Invalid filename contains prohibited characters: {filename}")

    # Block files with spaces, special chars, or starting with dots/dashes/underscores
    if not re.match(r"^[a-zA-Z0-9][a-zA-Z0-9._-]*$", filename):
        raise ValueError(
            f"Filename contains unsafe characters (only alphanumeric, dots, hyphens, underscores allowed): {filename}"
        )

    try:
        # Then sanitize for additional safety (handles edge cases and normalization)
        safe_filename = sanitize_filename(filename, platform="auto")
        if not safe_filename:  # Empty result means entirely invalid
            raise ValueError(f"Invalid filename: {filename}")
    except ValidationError as e:
        raise ValueError(f"Invalid filename: {str(e)}") from e

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

    # Construct and validate path using pathlib for additional security
    full_path = os.path.join(base_dir, safe_filename)
    normalized_path = os.path.normpath(full_path)
    normalized_base = os.path.normpath(base_dir)

    # Ensure path doesn't escape base directory (additional defense)
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


def _extract_snippet_name(line_text: str) -> Optional[str]:
    """Extract snippet name from an include statement.

    Args:
        line_text: Line of template text that may contain an include statement

    Returns:
        The snippet name if found, None otherwise
    """
    if "include" in line_text:
        match = INCLUDE_PATTERN.search(line_text)
        if match:
            return match.group(1)
    return None


def _get_context_lines(
    lines: list[str],
    line_idx: int,
    error_line_no: int,
    context_before: int = CONTEXT_LINES_BEFORE,
    context_after: int = CONTEXT_LINES_AFTER,
) -> list[str]:
    """Get context lines around a specific line.

    Args:
        lines: List of lines from the template
        line_idx: Zero-based index of the target line
        error_line_no: One-based line number for display
        context_before: Number of lines to show before
        context_after: Number of lines to show after

    Returns:
        List of formatted context lines with line numbers and markers
    """
    if not lines or line_idx < 0 or line_idx >= len(lines):
        return []

    start = max(0, line_idx - context_before)
    end = min(len(lines), line_idx + context_after + 1)

    context_lines = []
    for i in range(start, end):
        prefix = ">>> " if i == line_idx else "    "
        context_lines.append(f"  {i + 1:4d}: {prefix}{lines[i]}")

    return context_lines


def format_template_error(
    e: Exception,
    template_name: str = "template",
    template_content: Optional[str] = None,
    snippets: Optional[TemplateSnippetCollection] = None,
) -> str:
    """Format a template error with detailed context for debugging.

    Args:
        e: The exception that occurred
        template_name: Name of the template that failed
        template_content: Optional template content to show context
        snippets: Optional collection of template snippets for resolving includes

    Returns:
        Formatted error message with context
    """
    error_parts = [f"Template '{template_name}' rendering failed"]

    # Collect all template frames from traceback
    template_frames: list[dict[str, Any]] = []
    exc_type, exc_value, tb = sys.exc_info()

    if tb:
        # Traverse entire traceback to find all template frames
        while tb:
            frame = tb.tb_frame
            # Jinja2 templates have special filenames
            if frame.f_code.co_filename and (
                "<template>" in frame.f_code.co_filename
                or "memory:" in frame.f_code.co_filename
            ):
                # Store the frame's filename for snippet detection
                template_frames.append(
                    {
                        "line": tb.tb_lineno,
                        "frame": frame,
                        "filename": frame.f_code.co_filename,
                    }
                )
            tb = tb.tb_next

    # For syntax errors, use the lineno attribute
    if hasattr(e, "lineno") and e.lineno:
        template_frames = [{"line": e.lineno, "frame": None, "filename": "<template>"}]

    # Determine if this is an include error (multiple template frames)
    # When there are multiple frames, it usually means we have an include
    is_include_error = len(template_frames) > 1

    if template_frames:
        if is_include_error and len(template_frames) >= 2:
            error_parts.append(f": {str(e)}")

            # Handle multiple levels of includes
            if len(template_frames) > 2:
                # Deep nesting - show the full chain
                error_parts.append("\n\n  Error occurred through nested includes:")

                # Build the include chain
                include_chain: list[dict[str, Any]] = []
                current_content = template_content

                for frame_idx in range(len(template_frames)):
                    frame_dict = template_frames[frame_idx]
                    frame_line_no: int = frame_dict["line"]
                    is_last = frame_idx == len(template_frames) - 1

                    # Get the content to analyze
                    content_to_analyze = current_content

                    # For intermediate frames, we need the content from the previous snippet
                    if (
                        frame_idx > 0
                        and include_chain
                        and include_chain[-1].get("next_snippet_name")
                    ):
                        prev_snippet_name = include_chain[-1]["next_snippet_name"]
                        if snippets and prev_snippet_name in snippets:
                            snippet = snippets[prev_snippet_name]
                            content_to_analyze = (
                                snippet.template
                                if hasattr(snippet, "template")
                                else str(snippet)
                            )
                        else:
                            # Snippet not found - log this but continue
                            content_to_analyze = None

                    # Extract context and snippet name
                    lines = content_to_analyze.split("\n") if content_to_analyze else []
                    line_idx = frame_line_no - 1

                    snippet_name_for_next = None
                    if 0 <= line_idx < len(lines) and not is_last:
                        # Try to extract the snippet name from include statement
                        snippet_name_for_next = _extract_snippet_name(lines[line_idx])

                    # Store frame info
                    include_chain.append(
                        {
                            "line_no": frame_line_no,
                            "content": content_to_analyze,
                            "is_last": is_last,
                            "next_snippet_name": snippet_name_for_next,
                            "frame_idx": frame_idx,
                        }
                    )

                    # Update current content for next iteration
                    current_content = content_to_analyze

                # Now display the chain
                for idx, chain_item in enumerate(include_chain):
                    if not chain_item["content"]:
                        # No content available for this frame (e.g., missing snippet)
                        if idx > 0 and include_chain[idx - 1].get("next_snippet_name"):
                            snippet_name = include_chain[idx - 1]["next_snippet_name"]
                            error_parts.append(
                                f"\n  ↓ Snippet '{snippet_name}' (not found in snippets collection)"
                            )
                        continue

                    lines = chain_item["content"].split("\n")
                    line_idx = chain_item["line_no"] - 1

                    if 0 <= line_idx < len(lines):
                        # Show context
                        line_number: int = chain_item["line_no"]
                        context_lines = _get_context_lines(lines, line_idx, line_number)

                        if context_lines:
                            if idx == 0:
                                # Main template
                                error_parts.append(
                                    f"\n  Main template (include at line {chain_item['line_no']}):\n"
                                    + "\n".join(context_lines)
                                )
                            elif chain_item["is_last"]:
                                # Error location - get the snippet name from previous item
                                snippet_name = None
                                if idx > 0 and include_chain[idx - 1].get(
                                    "next_snippet_name"
                                ):
                                    snippet_name = include_chain[idx - 1][
                                        "next_snippet_name"
                                    ]

                                if snippet_name:
                                    error_parts.append(
                                        f"\n  ↓ Snippet '{snippet_name}' (error at line {chain_item['line_no']}):\n"
                                        + "\n".join(context_lines)
                                    )
                                else:
                                    error_parts.append(
                                        f"\n  ↓ Error location (line {chain_item['line_no']}):\n"
                                        + "\n".join(context_lines)
                                    )
                            else:
                                # Intermediate include - get snippet name from previous
                                snippet_name = None
                                if idx > 0 and include_chain[idx - 1].get(
                                    "next_snippet_name"
                                ):
                                    snippet_name = include_chain[idx - 1][
                                        "next_snippet_name"
                                    ]

                                if snippet_name:
                                    error_parts.append(
                                        f"\n  ↓ Snippet '{snippet_name}' (include at line {chain_item['line_no']}):\n"
                                        + "\n".join(context_lines)
                                    )
                                else:
                                    error_parts.append(
                                        f"\n  ↓ Include at line {chain_item['line_no']}:\n"
                                        + "\n".join(context_lines)
                                    )
            else:
                # Simple two-level include (existing logic)
                include_frame = template_frames[0]
                error_frame = template_frames[-1]
                include_line: int = include_frame["line"]
                error_line: int = error_frame["line"]

                # Show main template context (include statement)
                snippet_name = None
                if template_content:
                    lines = template_content.split("\n")
                    line_idx = include_line - 1

                    if 0 <= line_idx < len(lines):
                        # Try to extract snippet name from include statement first
                        snippet_name = _extract_snippet_name(lines[line_idx])

                        # Show main template context
                        context_lines = _get_context_lines(
                            lines, line_idx, include_line
                        )

                        if context_lines:
                            error_parts.append(
                                "\n\n  Error occurred in included snippet"
                            )
                            error_parts.append(
                                "\n  Main template (include at line "
                                + str(include_line)
                                + "):\n"
                                + "\n".join(context_lines)
                            )

                        # Show snippet context if we have the snippet
                        if snippet_name and snippets and snippet_name in snippets:
                            snippet = snippets[snippet_name]
                            snippet_content = (
                                snippet.template
                                if hasattr(snippet, "template")
                                else str(snippet)
                            )
                            snippet_lines = snippet_content.split("\n")

                            # The error_line here is the line number within the snippet
                            snippet_line_idx = error_line - 1

                            if 0 <= snippet_line_idx < len(snippet_lines):
                                snippet_context = _get_context_lines(
                                    snippet_lines, snippet_line_idx, error_line
                                )

                                if snippet_context:
                                    error_parts.append(
                                        f"\n  Snippet '{snippet_name}' (error at line "
                                        + str(error_line)
                                        + "):\n"
                                        + "\n".join(snippet_context)
                                    )
        else:
            # Single frame - regular error
            line_no: int = template_frames[0]["line"]
            error_parts.append(f"at line {line_no}")
            error_parts.append(f": {str(e)}")

            # Show context
            if template_content and line_no:
                lines = template_content.split("\n")
                line_idx = line_no - 1

                context_lines = _get_context_lines(lines, line_idx, line_no)
                if context_lines:
                    error_parts.append(
                        "\n\n  Template context:\n" + "\n".join(context_lines)
                    )
    else:
        # No line number available
        error_parts.append(f": {str(e)}")

    # Add specific guidance for common errors
    error_str = str(e).lower()
    if "nonetype" in error_str and "is not iterable" in error_str:
        error_parts.append(
            "\n  💡 Hint: Check if the resource collection exists before iterating. Use: {% for _, item in resources.get('type', {}).items() %}"
        )
    elif "undefined" in error_str:
        error_parts.append(
            "\n  💡 Hint: A variable is not defined. Check your template variables and resource names."
        )
    elif "no filter named" in error_str:
        error_parts.append(
            "\n  💡 Hint: Unknown filter. Available filters: b64decode, get_path"
        )
    elif "has no attribute" in error_str:
        error_parts.append(
            "\n  💡 Hint: Check if the object exists and has the attribute you're trying to access. Consider using default values or conditional checks."
        )

    return " ".join(error_parts)


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

    def render(
        self, template_str: str, template_name: Optional[str] = None, **context: Any
    ) -> str:
        """Compile (with caching) and render a template.

        Args:
            template_str: Template string to compile and render
            template_name: Optional name of the template for error reporting
            **context: Template variables for rendering

        Returns:
            Rendered template content

        Raises:
            ValueError: If template compilation or rendering fails
        """
        template_name = template_name or "unnamed"
        try:
            template = self.get_compiled(template_str)
            return template.render(**context)
        except Exception as e:
            # Format detailed error with context, including snippets
            snippets_to_use = None
            if self._compiler.environment.loader and hasattr(
                self._compiler.environment.loader, "snippets"
            ):
                snippets_to_use = self._compiler.environment.loader.snippets  # type: ignore[attr-defined]
            detailed_error = format_template_error(
                e,
                template_name,
                template_str,
                snippets_to_use,
            )
            raise ValueError(detailed_error) from e

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
