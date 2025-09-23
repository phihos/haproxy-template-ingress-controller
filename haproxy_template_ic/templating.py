"""
Templating functionality for HAProxy Template IC.

This module provides Jinja2-based template compilation, rendering, and caching
functionality including support for template snippets and custom filters.
"""

import base64
import math
import re
import sys
from functools import lru_cache
from pathlib import Path
from typing import Any, Callable

import jinja2
from jinja2 import (
    BaseLoader,
    Environment,
    Template,
    TemplateNotFound,
    TemplateSyntaxError,
)
from pathvalidate import ValidationError, is_valid_filename, sanitize_filename

from .constants import (
    MAX_TEMPLATE_FRAMES,
    TEMPLATE_CACHE_SIZE,
)
from .models.config import TemplateSnippetCollection
from .models.templates import TemplateSnippet

# Regex pattern for extracting snippet names from include statements
INCLUDE_PATTERN = re.compile(r'{%\s*include\s+["\']([^"\']+)["\']\s*%}')

# Context lines to show around errors
CONTEXT_LINES_BEFORE = 2
CONTEXT_LINES_AFTER = 3


def b64decode_filter(value: str) -> str:
    """Custom Jinja2 filter to decode base64 strings."""
    try:
        return base64.b64decode(value).decode("utf-8")
    except (ValueError, TypeError, UnicodeDecodeError) as e:
        raise ValueError(f"Failed to decode base64 value: {e}") from e


def logarithm_filter(x, base=math.e) -> float:
    """Ansible-style logarithm filter."""
    try:
        if base == 10:
            return math.log10(x)
        else:
            return math.log(x, base)
    except TypeError as ex:
        raise ValueError("logarithm() can only be used on numbers") from ex


def get_path_filter(filename: str, content_type: str, config: Any | None = None) -> str:
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

    if config is None:
        # Fallback to defaults if no config provided
        base_dirs = {
            "map": "/etc/haproxy/maps",
            "certificate": "/etc/haproxy/ssl",
            "file": "/etc/haproxy/general",
        }
        base_dir = base_dirs[content_type]
    else:
        base_dirs = {
            "map": config.storage_maps_dir,
            "certificate": config.storage_ssl_dir,
            "file": config.storage_general_dir,
        }
        base_dir = base_dirs[content_type]

    # Construct and validate path using pathlib for additional security
    base_path = Path(base_dir).resolve()
    full_path = base_path / safe_filename
    resolved_path = full_path.resolve()

    # Ensure path doesn't escape base directory (additional defense)
    try:
        resolved_path.relative_to(base_path)
    except ValueError as e:
        raise ValueError(
            f"Path traversal detected for filename '{filename}' in {content_type}"
        ) from e

    return str(resolved_path)


class SnippetLoader(BaseLoader):
    """Custom Jinja2 loader that can resolve template snippets by name."""

    def __init__(self, snippets: TemplateSnippetCollection | None = None):
        self.snippets = snippets if snippets is not None else {}

    def get_source(
        self, environment: Environment, template: str
    ) -> tuple[str, str | None, Callable | None]:
        """Get template source for snippet name."""
        # Handle snippets dict (current format)
        snippet = self.snippets.get(template)

        if snippet is None:
            raise TemplateNotFound(template)

        source = snippet.template if hasattr(snippet, "template") else str(snippet)
        return source, None, lambda: True


def _extract_snippet_name(line_text: str) -> str | None:
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


def _format_snippet_context(
    snippet_name: str | None,
    line_no: int,
    lines: list[str],
    line_idx: int,
    is_error: bool = False,
    is_include: bool = False,
) -> list[str]:
    """Format context for a snippet or include location.

    Args:
        snippet_name: Name of the snippet (if known)
        line_no: Line number in the snippet/template
        lines: Lines of content
        line_idx: Zero-based line index
        is_error: Whether this is the error location
        is_include: Whether this is an include statement

    Returns:
        Formatted context lines with appropriate headers
    """
    context_parts: list[str] = []
    context_lines = _get_context_lines(lines, line_idx, line_no)

    if not context_lines:
        return context_parts

    if snippet_name:
        if is_error:
            header = f"\n  ↓ Snippet '{snippet_name}' (error at line {line_no}):\n"
        elif is_include:
            header = f"\n  ↓ Snippet '{snippet_name}' (include at line {line_no}):\n"
        else:
            header = f"\n  ↓ Snippet '{snippet_name}' (line {line_no}):\n"
    else:
        if is_error:
            header = f"\n  ↓ Error location (line {line_no}):\n"
        elif is_include:
            header = f"\n  ↓ Include at line {line_no}:\n"
        else:
            header = f"\n  Template context (line {line_no}):\n"

    context_parts.append(header + "\n".join(context_lines))
    return context_parts


def _process_include_chain(
    template_frames: list[dict[str, Any]],
    template_content: str | None,
    snippets: TemplateSnippetCollection | None,
) -> list[str]:
    """Process a chain of includes to build error context.

    Args:
        template_frames: List of traceback frames from templates
        template_content: Main template content
        snippets: Collection of template snippets

    Returns:
        List of formatted error context parts
    """
    error_parts = []
    include_chain: list[dict[str, Any]] = []
    current_content = template_content

    for frame_idx in range(len(template_frames)):
        frame_dict = template_frames[frame_idx]
        frame_line_no: int = frame_dict["line"]
        is_last = frame_idx == len(template_frames) - 1

        content_to_analyze = current_content

        # For intermediate frames, get content from the previous snippet
        if (
            frame_idx > 0
            and include_chain
            and include_chain[-1].get("next_snippet_name")
        ):
            prev_snippet_name = include_chain[-1]["next_snippet_name"]
            if snippets and prev_snippet_name in snippets:
                snippet = snippets[prev_snippet_name]
                content_to_analyze = (
                    snippet.template if hasattr(snippet, "template") else str(snippet)
                )
            else:
                # Snippet not found
                content_to_analyze = None

        # Extract context and snippet name (with input validation)
        if not isinstance(content_to_analyze, str):
            content_to_analyze = str(content_to_analyze) if content_to_analyze else None
        lines = content_to_analyze.split("\n") if content_to_analyze else []
        line_idx = frame_line_no - 1

        snippet_name_for_next = None
        if 0 <= line_idx < len(lines) and not is_last:
            # Try to extract the snippet name from include statement
            snippet_name_for_next = _extract_snippet_name(lines[line_idx])

        include_chain.append(
            {
                "line_no": frame_line_no,
                "content": content_to_analyze,
                "is_last": is_last,
                "next_snippet_name": snippet_name_for_next,
                "frame_idx": frame_idx,
            }
        )

        current_content = content_to_analyze

    # Now display the chain
    for idx, chain_item in enumerate(include_chain):
        if not chain_item["content"]:
            # No content available for this frame
            if idx > 0 and include_chain[idx - 1].get("next_snippet_name"):
                snippet_name = include_chain[idx - 1]["next_snippet_name"]
                error_parts.append(
                    f"\n  ↓ Snippet '{snippet_name}' (not found in snippets collection)"
                )
            continue

        lines = chain_item["content"].split("\n")
        line_idx = chain_item["line_no"] - 1

        if 0 <= line_idx < len(lines):
            # Determine context type
            is_error = chain_item["is_last"]
            is_include = not is_error and idx < len(include_chain) - 1

            snippet_name = None
            if idx > 0 and include_chain[idx - 1].get("next_snippet_name"):
                snippet_name = include_chain[idx - 1]["next_snippet_name"]

            # Format the context
            if idx == 0:
                # Main template
                context_lines = _get_context_lines(
                    lines, line_idx, chain_item["line_no"]
                )
                if context_lines:
                    header = f"\n  Main template (include at line {chain_item['line_no']}):\n"
                    error_parts.append(header + "\n".join(context_lines))
            else:
                context = _format_snippet_context(
                    snippet_name,
                    chain_item["line_no"],
                    lines,
                    line_idx,
                    is_error=is_error,
                    is_include=is_include,
                )
                error_parts.extend(context)

    return error_parts


def format_template_error(
    e: Exception,
    template_name: str = "template",
    template_content: str | None = None,
    snippets: TemplateSnippetCollection | None = None,
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

    # Collect all template frames from traceback (with early termination)
    template_frames: list[dict[str, Any]] = []
    exc_type, exc_value, tb = sys.exc_info()

    # Performance optimization: limit traceback depth to avoid excessive processing
    if tb:
        # Traverse traceback to find template frames (with early termination)
        frame_count = 0
        while tb and frame_count < MAX_TEMPLATE_FRAMES:
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
            frame_count += 1

    # For syntax errors, use the lineno attribute only if we don't have frames
    lineno = getattr(e, "lineno", None)
    if not template_frames and lineno:
        template_frames = [{"line": lineno, "frame": None, "filename": "<template>"}]

    # Determine if this is an include error (multiple template frames)
    # When there are multiple frames, it usually means we have an include
    is_include_error = len(template_frames) > 1

    if template_frames:
        if is_include_error and len(template_frames) >= 2:
            # Handle multiple levels of includes
            if len(template_frames) > 2:
                # Deep nesting - show the full chain
                error_parts.append("\n\n  Error occurred through nested includes:")
                error_parts.append(f"\n  Error: {str(e)}\n")

                chain_context = _process_include_chain(
                    template_frames, template_content, snippets
                )
                error_parts.extend(chain_context)
            else:
                # Simple two-level include
                error_parts.append("\n\n  Error occurred in included snippet:")
                error_parts.append(f"\n  Error: {str(e)}\n")

                chain_context = _process_include_chain(
                    template_frames, template_content, snippets
                )
                error_parts.extend(chain_context)
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
                        f"\n\n  Template context:\n{'\n'.join(context_lines)}"
                    )
    else:
        # No line number available
        error_parts.append(f": {str(e)}")

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
    snippets: TemplateSnippetCollection | None = None,
    config=None,
) -> Environment:
    """Get or create a Jinja2 environment with snippet support."""
    snippet_loader = SnippetLoader(snippets)

    env = Environment(
        loader=snippet_loader,
        autoescape=False,  # HAProxy config shouldn't be HTML-escaped  # nosec B701
        trim_blocks=False,  # Rely on manual whitespace control to create fewer surprises
        lstrip_blocks=False,  # Rely on manual whitespace control to create fewer surprises
        keep_trailing_newline=True,  # HAProxy requires configs to end with newline
        extensions=["jinja2.ext.do"],  # Enable do extension for {% do %} statements
    )

    env.filters["b64decode"] = b64decode_filter

    env.filters["log"] = logarithm_filter

    def get_path_with_config(filename: str, content_type: str) -> str:
        return get_path_filter(filename, content_type, config)

    env.filters["get_path"] = get_path_with_config

    return env


class TemplateEnvironmentFactory:
    """Factory for creating Jinja2 environments with snippet support."""

    @staticmethod
    def create_environment(
        snippets: TemplateSnippetCollection | None = None,
        config=None,
    ) -> Environment:
        """Create a Jinja2 environment with the given snippets."""
        return get_template_environment(snippets, config)


class TemplateCompiler:
    """Service for compiling Jinja2 templates with dependency injection."""

    def __init__(self, snippets: TemplateSnippetCollection | None = None, config=None):
        """Initialize the compiler with template snippets."""
        self.environment = TemplateEnvironmentFactory.create_environment(
            snippets, config
        )

    def compile_template(self, template_string: str) -> Template:
        """Compile a template string into a Jinja2 Template object."""
        return self.environment.from_string(template_string)


@lru_cache(maxsize=TEMPLATE_CACHE_SIZE)
def compile_template(
    template_str: str, snippets_tuple: tuple | None = None
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
    context: dict[str, Any],
    snippets: TemplateSnippetCollection | None = None,
) -> str:
    """Render a template with the given context and snippets."""
    # Convert snippets to tuple for caching
    snippets_tuple = tuple(snippets.items()) if snippets else None

    try:
        template = compile_template(template_str, snippets_tuple)
        return template.render(**context)
    except (jinja2.TemplateError, ValueError, TypeError) as e:
        raise ValueError(f"Template rendering failed: {e}") from e


class TemplateRenderer:
    """Manages template compilation and rendering with caching.

    This class encapsulates all template operations and caches compiled templates
    for efficient reuse. Templates are compiled once and cached by their content.
    """

    def __init__(
        self, template_snippets: TemplateSnippetCollection | None = None, config=None
    ):
        """Initialize the renderer with template snippets.

        Args:
            template_snippets: Collection of reusable template snippets
            config: Configuration object for get_path filter
        """
        self._compiler = TemplateCompiler(template_snippets, config)
        self._compiled_templates: dict[str, Template] = {}

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
        self, template_str: str, template_name: str | None = None, **context: Any
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
            # Compile the template first
            compiled_template = self.get_compiled(template_str)
            # Try to render with empty context to catch TemplateNotFound errors
            compiled_template.render({})
        except TemplateSyntaxError as e:
            warnings.append(f"Invalid template syntax: {e}")
        except TemplateNotFound as e:
            warnings.append(f"Template snippet not found: {e}")
        except Exception as e:
            warnings.append(f"Template error: {e}")
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
