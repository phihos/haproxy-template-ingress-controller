"""
Resources widget for the TUI dashboard.

Shows watched Kubernetes resources using a DataTable.
"""

import logging

from textual.widgets import DataTable
from textual.reactive import Reactive, reactive

from haproxy_template_ic.tui.models import DashboardData
from haproxy_template_ic.tui.utils import format_size, format_age

logger = logging.getLogger(__name__)

__all__ = ["ResourcesWidget"]


class ResourcesWidget(DataTable):
    """Widget displaying watched Kubernetes resources in a table format."""

    # Reactive property for dashboard data
    dashboard_data: Reactive[DashboardData] = reactive(DashboardData())

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.border_title = "Watched Resources"
        self.cursor_type = "row"
        self.zebra_stripes = True
        self.show_cursor = False  # Don't show cursor for this table

    def on_mount(self) -> None:
        """Initialize the table columns."""
        self.add_columns(
            "Resource Type",
            "Count",
            "Size",
            "Last Update",
        )

    def watch_dashboard_data(self, dashboard_data: DashboardData) -> None:
        """Update table when dashboard data changes."""
        resources = dashboard_data.resources

        # Clear existing rows
        self.clear()

        # Check if we have any resources
        if resources.total == 0:
            # Add a single row indicating no resources with helpful context
            self.add_row("❌", "No watched resources", "—", "—")
            return

        # Add rows for each resource type dynamically
        for resource_type, count in resources.resource_counts.items():
            if count > 0:
                # Format resource type name (e.g., "ingresses" → "Ingresses")
                display_name = resource_type.replace("_", " ").title()

                # Get memory size for this resource type
                memory_size = resources.resource_memory_sizes.get(resource_type, 0)
                memory_size_str = format_size(memory_size)

                # Use individual resource timestamp or fallback to global
                resource_timestamp = resources.resource_last_updates.get(
                    resource_type, resources.last_update
                )
                if resource_timestamp:
                    timestamp_iso = resource_timestamp.isoformat()
                    resource_last_update_display = format_age(timestamp_iso)
                else:
                    resource_last_update_display = "—"

                self.add_row(
                    display_name,
                    str(count),
                    memory_size_str,
                    str(resource_last_update_display),
                )

        # Add total row if we have multiple resource types
        if len(resources.resource_counts) > 1:
            # Find the most recent timestamp among all resource types
            max_timestamp = None
            if resources.resource_last_updates:
                max_timestamp = max(resources.resource_last_updates.values())

            # Fallback to global timestamp if no individual timestamps
            if max_timestamp is None:
                max_timestamp = resources.last_update

            # Calculate total memory size across all resource types
            total_memory_size = sum(resources.resource_memory_sizes.values())
            total_memory_size_str = format_size(total_memory_size)

            if max_timestamp:
                timestamp_iso = max_timestamp.isoformat()
                max_timestamp_display = format_age(timestamp_iso)
            else:
                max_timestamp_display = "—"

            self.add_row(
                "Total",
                str(resources.total),
                total_memory_size_str,
                str(max_timestamp_display),
            )
