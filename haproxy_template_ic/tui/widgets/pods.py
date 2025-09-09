"""
Pods widget for the TUI dashboard.

Shows HAProxy pods with status indicators using a DataTable.
"""

import logging

from textual.reactive import Reactive, reactive
from textual.widgets import DataTable

from haproxy_template_ic.tui.models import DashboardData
from ..utils import format_age

logger = logging.getLogger(__name__)

__all__ = ["PodsWidget"]


class PodsWidget(DataTable):
    """Widget displaying HAProxy pods in a table format."""

    # Reactive property for dashboard data
    dashboard_data: Reactive[DashboardData] = reactive(DashboardData())

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.border_title = "HAProxy Pods"
        self.cursor_type = "row"
        self.zebra_stripes = True

    def on_mount(self) -> None:
        """Initialize the table columns."""
        self.add_columns(
            "Pod Name",
            "IP Address",
            "Sync Status",
            "Last Update",
            "Uptime",
        )

    def watch_dashboard_data(self, dashboard_data: DashboardData) -> None:
        """Update table when dashboard data changes."""
        pods = dashboard_data.pods

        # Clear existing rows
        self.clear()

        if not pods:
            # Add a single row indicating no pods with helpful context
            self.add_row("No HAProxy pods found", "N/A", "⚫ Unknown", "N/A", "N/A")
            self.refresh()
            return

        # Add rows for each pod
        for pod in pods:
            # Sync status
            sync_success = pod.sync_success
            if sync_success is True:
                sync_status = "✅ Success"
            elif sync_success is False:
                sync_status = "❌ Failed"
            else:
                sync_status = "⚫ Unknown"

            # Format last update time with age
            if pod.last_sync:
                timestamp_iso = pod.last_sync.isoformat()
                last_update = format_age(timestamp_iso)
            else:
                last_update = "Never"

            # Use the uptime property from PodInfo
            uptime = pod.uptime

            self.add_row(
                pod.name,
                pod.ip,
                sync_status,
                str(last_update),
                str(uptime),
            )
        # Force a refresh of the DataTable widget
        self.refresh()

    def on_data_table_row_selected(self, event) -> None:
        """Handle row selection (for future enhancement)."""
        # Could show detailed pod information in a modal or side panel
        pass
