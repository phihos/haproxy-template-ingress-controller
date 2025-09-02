"""
Template inspector panel for the dashboard.

Provides detailed template inspection with syntax highlighting for both
Jinja2 templates and their rendered content.
"""

from typing import Dict, Any, Optional
from rich.panel import Panel
from rich.syntax import Syntax
from rich.text import Text
from rich.layout import Layout
from rich.table import Table
from rich.console import Console
import logging

logger = logging.getLogger(__name__)

__all__ = ["TemplateInspectorPanel"]


class TemplateInspectorPanel:
    """Panel for inspecting templates with syntax highlighting."""

    def __init__(self, console: Optional[Console] = None):
        self.selected_template = 0
        self.view_mode = "template"  # "template", "rendered", or "split"
        self.show_line_numbers = True
        self.theme = "monokai"
        self.scroll_position = 0
        self.lines_per_page = 20  # Default, will be recalculated dynamically
        self.console = console

    def render_template_list(self, templates: Dict[str, Any], selected: int) -> Panel:
        """Render a list of available templates for selection."""
        if not templates:
            return Panel(
                "[yellow]No templates available for inspection[/yellow]",
                title="📋 Template Inspector",
                border_style="yellow",
            )

        # Create table for template list
        table = Table(show_header=True, header_style="bold magenta", padding=(0, 1))
        table.add_column("", width=2)  # Selection indicator
        table.add_column("Template", style="cyan", no_wrap=True)
        table.add_column("Type", style="blue", no_wrap=True)
        table.add_column("Size", justify="right", no_wrap=True)
        table.add_column("Status", justify="center", no_wrap=True)

        template_names = list(templates.keys())
        for idx, (template_name, template_info) in enumerate(templates.items()):
            # Selection indicator
            indicator = "▶" if idx == selected else " "

            # Format size
            size = template_info.get("size", 0)
            if size > 1024:
                size_text = f"{size // 1024:.1f}KB"
            else:
                size_text = f"{size}B"

            # Status with emoji
            status = template_info.get("status", "unknown")
            if status == "valid":
                status_text = "✅ Valid"
            elif status == "empty":
                status_text = "⚪ Empty"
            else:
                status_text = f"❌ {status}"

            table.add_row(
                indicator,
                template_name,
                template_info.get("type", "unknown"),
                size_text,
                status_text,
            )

        return Panel(
            table,
            title="📋 Template Inspector - Select Template",
            subtitle=f"[dim]↑↓ Navigate | Enter to inspect | ESC to return | {len(template_names)} templates[/dim]",
            border_style="cyan",
        )

    def render_template_content(
        self,
        template_name: str,
        template_source: Optional[str] = None,
        rendered_content: Optional[str] = None,
        template_type: str = "unknown",
    ) -> Panel:
        """Render template content with syntax highlighting."""
        if self.view_mode == "split":
            return self._render_split_view(
                template_name, template_source, rendered_content, template_type
            )
        elif self.view_mode == "rendered":
            return self._render_single_view(
                template_name, rendered_content, "rendered", template_type
            )
        else:  # template
            return self._render_single_view(
                template_name, template_source, "template", template_type
            )

    def _render_split_view(
        self,
        template_name: str,
        template_source: Optional[str],
        rendered_content: Optional[str],
        template_type: str,
    ) -> Panel:
        """Render split view showing both template and rendered content."""
        layout = Layout()
        layout.split_row(Layout(name="template"), Layout(name="rendered"))

        # Template source on the left
        if template_source:
            template_syntax = self._create_syntax_panel(
                template_source, "jinja", f"Template Source ({template_type})"
            )
            layout["template"].update(template_syntax)
        else:
            layout["template"].update(
                Panel(
                    "[dim]Template source not available[/dim]",
                    title=f"Template Source ({template_type})",
                    border_style="dim",
                )
            )

        # Rendered content on the right
        if rendered_content:
            lexer = self._get_lexer_for_type(template_type)
            rendered_syntax = self._create_syntax_panel(
                rendered_content, lexer, f"Rendered Content ({template_type})"
            )
            layout["rendered"].update(rendered_syntax)
        else:
            layout["rendered"].update(
                Panel(
                    "[dim]Rendered content not available[/dim]",
                    title=f"Rendered Content ({template_type})",
                    border_style="dim",
                )
            )

        return Panel(
            layout,
            title=f"📋 {template_name} - Split View",
            subtitle="[dim]Tab to switch views | ↑↓ scroll | ESC to return[/dim]",
            border_style="blue",
            expand=True,
        )

    def _render_single_view(
        self,
        template_name: str,
        content: Optional[str],
        view_type: str,
        template_type: str,
    ) -> Panel:
        """Render single view of template or rendered content."""
        if not content:
            content_text = f"[dim]{view_type.title()} content not available[/dim]"
            return Panel(
                content_text,
                title=f"📋 {template_name} - {view_type.title()} View",
                subtitle="[dim]Tab to switch views | ESC to return[/dim]",
                border_style="dim",
                expand=True,
            )

        # Determine lexer based on view type
        if view_type == "template":
            lexer = "jinja"
        else:
            lexer = self._get_lexer_for_type(template_type)

        # Calculate lines per page and extract visible content
        lines_per_page = self._calculate_lines_per_page()
        visible_content, start_line_num = self._extract_visible_content(
            content, lines_per_page
        )
        total_lines = len(content.splitlines())

        # Create syntax highlighted content
        try:
            syntax = Syntax(
                visible_content,
                lexer=lexer,
                theme=self.theme,
                line_numbers=self.show_line_numbers,
                word_wrap=False,
                code_width=None,
                tab_size=2,
                start_line=start_line_num,  # Adjust line numbers for scrolled content
            )

            # Create scroll info for subtitle
            if total_lines <= lines_per_page:
                scroll_info = f"Lines: {total_lines}"
            else:
                end_line_num = min(
                    start_line_num + len(visible_content.splitlines()) - 1, total_lines
                )
                scroll_info = f"Lines: {start_line_num}-{end_line_num} of {total_lines}"

            content_panel = Panel(
                syntax,
                title=f"📋 {template_name} - {view_type.title()} View ({template_type})",
                subtitle=f"[dim]Tab to switch views | ↑↓ scroll | {scroll_info} | ESC to return[/dim]",
                border_style="blue",
                expand=True,
            )
        except Exception as e:
            logger.warning(
                f"Failed to create syntax highlighting for {template_name}: {e}"
            )
            # Fallback to plain text
            content_panel = Panel(
                Text(visible_content, style="white"),
                title=f"📋 {template_name} - {view_type.title()} View ({template_type})",
                subtitle=f"[dim]Tab to switch views | ↑↓ scroll | Lines: {len(visible_content.splitlines())} | ESC to return[/dim]",
                border_style="blue",
                expand=True,
            )

        return content_panel

    def _create_syntax_panel(self, content: str, lexer: str, title: str) -> Panel:
        """Create a syntax highlighted panel."""
        try:
            syntax = Syntax(
                content,
                lexer=lexer,
                theme=self.theme,
                line_numbers=self.show_line_numbers,
                word_wrap=False,
                code_width=None,
                tab_size=2,
            )
            return Panel(syntax, title=title, border_style="green")
        except Exception as e:
            logger.warning(f"Failed to create syntax panel: {e}")
            return Panel(
                Text(content, style="white"),
                title=f"{title} (Plain Text)",
                border_style="yellow",
            )

    def _get_lexer_for_type(self, template_type: str) -> str:
        """Get appropriate lexer for template type."""
        lexer_map = {
            "config": "nginx",  # HAProxy config similar to nginx
            "map": "properties",  # Key-value pairs
            "certificate": "text",  # PEM format
            "file": "text",  # Generic files
            "snippet": "jinja",  # Template snippets
        }
        return lexer_map.get(template_type, "text")

    def handle_navigation(self, key: str, templates: Dict[str, Any]) -> bool:
        """Handle navigation keys for template selection and scrolling.

        Returns:
            True if the key was handled, False otherwise
        """
        if not templates:
            return False

        template_count = len(templates)

        if key == "UP":
            self.selected_template = max(0, self.selected_template - 1)
            return True
        elif key == "DOWN":
            self.selected_template = min(template_count - 1, self.selected_template + 1)
            return True
        elif key == "PAGEUP":
            self.selected_template = max(0, self.selected_template - 5)
            return True
        elif key == "PAGEDOWN":
            self.selected_template = min(template_count - 1, self.selected_template + 5)
            return True
        elif key == "HOME":
            self.selected_template = 0
            return True
        elif key == "END":
            self.selected_template = template_count - 1
            return True

        return False

    def handle_content_navigation(self, key: str, content: Optional[str]) -> bool:
        """Handle navigation keys within template content.

        Returns:
            True if the key was handled, False otherwise
        """
        if not content:
            return False

        total_lines = len(content.splitlines())
        lines_per_page = self._calculate_lines_per_page()
        max_scroll = max(0, total_lines - lines_per_page)

        if key == "UP":
            self.scroll_position = max(0, self.scroll_position - 1)
            return True
        elif key == "DOWN":
            self.scroll_position = min(max_scroll, self.scroll_position + 1)
            return True
        elif key == "PAGEUP":
            self.scroll_position = max(0, self.scroll_position - lines_per_page)
            return True
        elif key == "PAGEDOWN":
            self.scroll_position = min(
                max_scroll, self.scroll_position + lines_per_page
            )
            return True
        elif key == "HOME":
            self.scroll_position = 0
            return True
        elif key == "END":
            self.scroll_position = max_scroll
            return True

        return False

    def get_selected_template_name(self, templates: Dict[str, Any]) -> Optional[str]:
        """Get the name of the currently selected template."""
        if not templates:
            return None

        template_names = list(templates.keys())
        if 0 <= self.selected_template < len(template_names):
            return template_names[self.selected_template]

        return None

    def cycle_view_mode(self) -> None:
        """Cycle through view modes: template -> rendered -> split."""
        modes = ["template", "rendered", "split"]
        current_index = modes.index(self.view_mode)
        self.view_mode = modes[(current_index + 1) % len(modes)]
        # Reset scroll position when changing view mode
        self.scroll_position = 0

    def toggle_line_numbers(self) -> None:
        """Toggle line number display."""
        self.show_line_numbers = not self.show_line_numbers

    def set_theme(self, theme: str) -> None:
        """Set syntax highlighting theme."""
        self.theme = theme

    def _calculate_lines_per_page(self) -> int:
        """Calculate available lines for content based on terminal height."""
        if not self.console:
            return 20  # Default fallback

        terminal_height = self.console.size.height
        # Reserve space for: title (1), borders (2), subtitle (1), padding (2) = 6 lines
        available_lines = max(10, terminal_height - 6)
        return available_lines

    def _extract_visible_content(
        self, content: str, lines_per_page: int
    ) -> tuple[str, int]:
        """Extract the visible portion of content based on scroll position.

        Args:
            content: Full content string
            lines_per_page: Number of lines to show per page

        Returns:
            Tuple of (visible_content_string, starting_line_number)
        """
        lines = content.splitlines()
        total_lines = len(lines)

        if total_lines == 0:
            return "", 1

        # Calculate start and end indices
        start_idx = self.scroll_position
        end_idx = min(start_idx + lines_per_page, total_lines)

        # Extract visible lines
        visible_lines = lines[start_idx:end_idx]

        # Join back into string with newlines
        visible_content = "\n".join(visible_lines)

        # Calculate starting line number (1-based)
        start_line_num = start_idx + 1

        return visible_content, start_line_num

    def reset_state(self) -> None:
        """Reset inspector state when exiting."""
        self.selected_template = 0
        self.scroll_position = 0
        self.view_mode = "template"
