"""
Template inspector widget for the TUI dashboard.

Provides template content viewing with syntax highlighting and navigation.
"""

import logging
from typing import Dict, Any, List, Union

from textual.widgets import Static, Tree
from textual.reactive import Reactive, reactive
from textual.containers import Horizontal, Vertical, ScrollableContainer
from textual.message import Message
from rich.syntax import Syntax
from rich.text import Text

from haproxy_template_ic.constants import INSPECTOR_SEPARATOR_WIDTH
from ..lexers import HAProxyLexer

logger = logging.getLogger(__name__)

__all__ = ["TemplateInspectorWidget", "TemplateContentChanged"]


class TemplateContentChanged(Message):
    """Message sent when template content should be displayed."""

    def __init__(self, template_name: str, template_type: str):
        super().__init__()
        self.template_name = template_name
        self.template_type = template_type


class TemplateInspectorWidget(Horizontal):
    """Widget for inspecting template content with syntax highlighting."""

    # Reactive properties
    templates_data: Reactive[Dict[str, Any]] = reactive({})
    template_content: Reactive[Dict[str, Any]] = reactive({})
    selected_template: Reactive[str] = reactive("")
    last_highlighted_template: Reactive[str] = reactive("")

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.border_title = "Template Inspector"

    def compose(self):
        """Create the inspector layout with template list and content view."""
        with Vertical(id="template-list-panel", classes="panel"):
            yield Static("Templates", classes="panel-header")
            yield Tree("Templates", id="template-tree")

        with Vertical(id="template-content-panel", classes="panel"):
            yield Static("Content", classes="panel-header")
            with ScrollableContainer(id="template-scroll"):
                yield Static(
                    "Hover over a template to view its content", id="template-content"
                )

    def on_mount(self) -> None:
        """Initialize the template inspector."""
        self._update_template_tree()

    def watch_templates_data(self, templates: Dict[str, Any]) -> None:
        """Update template tree when templates data changes."""
        self._update_template_tree()

    def watch_template_content(self, content: Dict[str, Any]) -> None:
        """Update template content display when content changes."""
        self._update_content_display()

    def watch_selected_template(self, template_name: str) -> None:
        """Watch selected_template and highlight the corresponding tree node."""
        if template_name and self.templates_data:
            # Defer highlighting until after the tree is fully rendered
            self.call_after_refresh(self._highlight_template_in_tree, template_name)

    def _update_template_tree(self) -> None:
        """Update the template tree with available templates."""
        try:
            tree = self.query_one("#template-tree", Tree)
            tree.clear()

            if not self.templates_data:
                tree.root.set_label("No templates available")
                return

            # Set proper root label when templates exist
            tree.root.set_label("Templates")

            # Group templates by type
            config_templates = {}
            map_templates = {}
            cert_templates = {}
            snippet_templates = {}

            for name, template_info in self.templates_data.items():
                if hasattr(template_info, "type"):
                    template_type = template_info.type
                else:
                    # Fallback type detection
                    template_type = self._detect_template_type(name)

                if template_type == "config":
                    config_templates[name] = template_info
                elif template_type == "map":
                    map_templates[name] = template_info
                elif template_type == "certificate":
                    cert_templates[name] = template_info
                elif template_type == "snippet":
                    snippet_templates[name] = template_info

            # Add nodes to tree
            if config_templates:
                config_node = tree.root.add("Configuration Files")
                for name in sorted(config_templates.keys()):
                    config_node.add_leaf(name)

            if map_templates:
                map_node = tree.root.add("Map Files")
                for name in sorted(map_templates.keys()):
                    map_node.add_leaf(name)

            if cert_templates:
                cert_node = tree.root.add("Certificates")
                for name in sorted(cert_templates.keys()):
                    cert_node.add_leaf(name)

            if snippet_templates:
                snippet_node = tree.root.add("Snippets")
                for name in sorted(snippet_templates.keys()):
                    snippet_node.add_leaf(name)

            # Expand all nodes by default
            tree.root.expand_all()

            # If there's a selected template, highlight it after the tree is built
            if self.selected_template:
                self._highlight_template_in_tree(self.selected_template)

        except Exception as e:
            logger.error(f"Error updating template tree: {e}", exc_info=True)

    def _highlight_template_in_tree(self, template_name: str) -> None:
        """Find and highlight the template node in the tree."""
        try:
            tree = self.query_one("#template-tree", Tree)

            # Search all leaf nodes for the matching template name
            def find_template_node(node):
                # If this is a leaf node (no children) and matches the template name
                if len(node.children) == 0 and str(node.label) == template_name:
                    return node

                # Recursively search children
                for child in node.children:
                    result = find_template_node(child)
                    if result:
                        return result
                return None

            # Find the matching node
            target_node = find_template_node(tree.root)

            if target_node:
                logger.debug(
                    f"Found template node for '{template_name}', highlighting it"
                )
                # Ensure the parent node is expanded so the target is visible
                if target_node.parent:
                    target_node.parent.expand()
                # Also ensure all nodes are expanded for full visibility
                tree.root.expand_all()
                # Move the cursor to the target node
                tree.select_node(target_node)
                # Trigger the selection/highlight event to load content
                tree.action_select_cursor()
            else:
                logger.warning(
                    f"Could not find tree node for template '{template_name}'"
                )

        except Exception as e:
            logger.error(f"Error highlighting template in tree: {e}", exc_info=True)

    def _detect_template_type(self, name: str) -> str:
        """Detect template type from filename."""
        name_lower = name.lower()
        if name_lower.endswith(".cfg") or name_lower == "haproxy.cfg":
            return "config"
        elif name_lower.endswith(".map"):
            return "map"
        elif (
            name_lower.endswith(".pem")
            or name_lower.endswith(".crt")
            or name_lower.endswith(".key")
        ):
            return "certificate"
        elif (
            name_lower.endswith(".snippet")
            or "-snippet" in name_lower
            or "snippet-" in name_lower
        ):
            return "snippet"
        else:
            return "config"  # Default to config

    def on_tree_node_highlighted(self, event: Tree.NodeHighlighted) -> None:
        """Handle template hover in the tree."""
        # Debug logging to understand node highlighting
        logger.debug(
            f"Tree node highlighted: label='{event.node.label}', is_root={event.node.is_root}, children_count={len(event.node.children)}"
        )
        logger.debug(f"Available templates: {list(self.templates_data.keys())}")

        if not event.node.is_root and len(event.node.children) == 0:
            # Get the template name (leaf node)
            template_name = str(event.node.label)
            logger.debug(f"Leaf node highlighted: {template_name}")

            # Check if this is actually a template (not a category label)
            if not self.templates_data:
                logger.debug("No templates data available")
                return

            # Avoid unnecessary updates if hovering over the same template
            if template_name == self.last_highlighted_template:
                return

            if template_name in self.templates_data:
                logger.debug(
                    f"Template found in data, requesting content for: {template_name}"
                )
                self.selected_template = template_name
                self.last_highlighted_template = template_name
                template_type = self._detect_template_type(template_name)

                # Post message to request template content
                self.post_message(TemplateContentChanged(template_name, template_type))
            else:
                logger.debug(
                    f"Template '{template_name}' not found in templates_data - likely a category node"
                )
        else:
            logger.debug(
                f"Node ignored: root={event.node.is_root}, children={len(event.node.children)}"
            )

    def _update_content_display(self) -> None:
        """Update the content display with syntax highlighting."""
        try:
            if not self.template_content or not self.selected_template:
                # Handle empty content case at the end with other logic
                scroll_container = self.query_one(
                    "#template-scroll", ScrollableContainer
                )
                scroll_container.remove_children()
                static_widget = Static("Hover over a template to view its content")
                scroll_container.mount(static_widget)
                return

            template_name = self.selected_template
            content_data = self.template_content

            # Get template content
            source_content = content_data.get("source", "")
            rendered_content = content_data.get("rendered", "")
            template_type = content_data.get("type", "unknown")
            errors = content_data.get("errors", [])

            # Build display content
            display_parts: List[Union[Text, Syntax]] = []

            # Show errors if any
            if errors:
                error_text = Text("❌ Template Errors:\n", style="bold red")
                for error in errors:
                    error_text.append(f"  • {error}\n", style="red")
                display_parts.append(error_text)
                display_parts.append(Text("\n"))

            # Show source content with syntax highlighting
            if source_content:
                display_parts.append(Text("📝 Source Template:\n", style="bold cyan"))
                try:
                    # Source templates are always Jinja2 templates
                    lexer = "jinja"
                    syntax = Syntax(
                        source_content,
                        lexer,
                        theme="monokai",
                        line_numbers=True,
                        word_wrap=True,
                    )
                    display_parts.append(syntax)
                except Exception as e:
                    logger.debug(f"Error creating syntax highlighting: {e}")
                    display_parts.append(Text(source_content))

                display_parts.append(
                    Text("\n" + "─" * INSPECTOR_SEPARATOR_WIDTH + "\n")
                )

            # Show rendered content or snippet information
            if template_type == "snippet":
                # Snippets are reusable template fragments - show informational message
                display_parts.append(
                    Text(
                        "ℹ️  Snippets are reusable template fragments\n",
                        style="italic cyan",
                    )
                )
                display_parts.append(
                    Text(
                        "They are included in other templates using {% include '"
                        + template_name
                        + "' %}",
                        style="dim",
                    )
                )
            elif rendered_content:
                display_parts.append(Text("🎯 Rendered Content:\n", style="bold green"))
                try:
                    # Use appropriate syntax highlighting for rendered content
                    if template_type == "config":
                        # Use custom HAProxy lexer for configuration files
                        haproxy_lexer = HAProxyLexer()
                        syntax = Syntax(
                            rendered_content,
                            haproxy_lexer,
                            theme="monokai",
                            line_numbers=True,
                            word_wrap=True,
                        )
                        display_parts.append(syntax)
                    else:
                        display_parts.append(Text(rendered_content))
                except Exception:
                    display_parts.append(Text(rendered_content))
            elif source_content and not errors:
                display_parts.append(
                    Text("⚠️ No rendered content available", style="yellow")
                )

            # Update the content display with multiple Static widgets
            scroll_container = self.query_one("#template-scroll", ScrollableContainer)
            scroll_container.remove_children()

            if display_parts:
                for i, part in enumerate(display_parts):
                    # Create a Static widget for each part to preserve rendering
                    static_widget = Static(part)
                    scroll_container.mount(static_widget)
            else:
                # Fallback if no parts
                static_widget = Static("Hover over a template to view its content")
                scroll_container.mount(static_widget)

        except Exception as e:
            logger.error(f"Error updating content display: {e}", exc_info=True)
            try:
                content_widget = self.query_one("#template-content", Static)
                content_widget.update(f"Error displaying template: {e}")
            except Exception as e:
                logger.debug(f"Error display fallback failed (suppressed): {e}")

    def _get_lexer_for_template(self, template_name: str, template_type: str) -> str:
        """Get the appropriate lexer for syntax highlighting."""
        name_lower = template_name.lower()

        if template_type == "config" or name_lower.endswith(".cfg"):
            return "haproxy"  # Custom HAProxy lexer
        elif template_type == "map" or name_lower.endswith(".map"):
            return "yaml"  # Simple key-value format
        elif template_type == "certificate" or any(
            name_lower.endswith(ext) for ext in [".pem", ".crt", ".key"]
        ):
            return "text"  # Plain text for certificates
        elif template_type == "snippet":
            return "jinja2"  # Snippets are Jinja2 templates
        elif any(ext in name_lower for ext in [".yaml", ".yml"]):
            return "yaml"
        elif any(ext in name_lower for ext in [".json"]):
            return "json"
        else:
            return "jinja2"  # Default for Jinja2 templates

    def set_template_content(self, content: Dict[str, Any]) -> None:
        """Set template content from external source."""
        self.template_content = content
