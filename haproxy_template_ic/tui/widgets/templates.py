"""
Templates widget for the TUI dashboard.

Shows template information using a DataTable.
"""

import logging

from textual.message import Message
from textual.reactive import Reactive, reactive
from textual.widgets import DataTable

from haproxy_template_ic.tui.models import DashboardData
from haproxy_template_ic.tui.utils import format_size, format_age

logger = logging.getLogger(__name__)

__all__ = ["TemplatesWidget", "TemplateSelected"]


class TemplatesWidget(DataTable):
    """Widget displaying template information in a table format."""

    # Reactive property for dashboard data
    dashboard_data: Reactive[DashboardData] = reactive(DashboardData())

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.border_title = "Templates"
        self.cursor_type = "row"
        self.zebra_stripes = True

    def on_mount(self) -> None:
        """Initialize the table columns."""
        self.add_columns(
            "Status",
            "Template Name",
            "Type",
            "Size",
            "Last Modified",
        )

    def watch_dashboard_data(self, dashboard_data: DashboardData) -> None:
        """Update table when dashboard data changes."""
        templates = dashboard_data.templates

        # Clear existing rows
        self.clear()

        if not templates:
            # Add rows with helpful context about why no templates are shown
            self.add_row(
                "ℹ️",
                "No templates found",
                "Check ConfigMap",
                "0B",
                "N/A",
            )
            self.add_row(
                "💡",
                "Operator may be starting up",
                "Wait for initialization",
                "0B",
                "N/A",
            )
            return

        # Add rows for each template
        for template_name, template_info in templates.items():
            # Status indicator
            status = template_info.status
            template_type = template_info.type

            # Special handling for snippets
            if template_type == "snippet":
                if status == "valid":
                    status_indicator = "📝"  # Snippet with content
                elif status == "empty":
                    status_indicator = "📄"  # Empty snippet
                elif status == "configured":
                    status_indicator = "🔸"  # Configured snippet
                else:
                    status_indicator = "❌"  # Error in snippet
            else:
                # Standard template status indicators
                if status == "valid":
                    status_indicator = "✅"
                elif status == "configured":
                    status_indicator = "⏳"  # Configured but not yet rendered
                elif status == "empty":
                    status_indicator = "⚪"
                elif status == "error":
                    status_indicator = "❌"
                else:
                    status_indicator = "⚫"

            # Format size
            size_text = format_size(template_info.size)

            # Format last modified with age
            if template_info.last_modified:
                timestamp_iso = template_info.last_modified.isoformat()
                last_modified = format_age(timestamp_iso)
            else:
                last_modified = "—"

            self.add_row(
                status_indicator,
                template_name,
                template_info.type,
                size_text,
                str(last_modified),
            )

    def on_data_table_row_selected(self, event) -> None:
        """Handle row selection for template inspection."""
        # This will be enhanced when we implement the template inspector
        row_key = event.row_key
        if row_key is not None:
            # Get the template name from the selected row
            try:
                row_data = self.get_row(row_key)
                template_name = row_data[1]  # Template name is in second column
                if template_name != "No templates found":
                    # Post a message to the app to show template inspector
                    self.post_message(TemplateSelected(template_name))
            except Exception as e:
                logger.error(f"Error handling template selection: {e}", exc_info=True)


class TemplateSelected(Message):
    """Message posted when a template is selected for inspection."""

    def __init__(self, template_name: str):
        super().__init__()
        self.template_name = template_name
