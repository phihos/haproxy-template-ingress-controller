"""
Header widget for the TUI dashboard.

Shows operator status, version, namespace, and compatibility information.
"""

import logging
from datetime import datetime

from textual.reactive import Reactive, reactive
from textual.widgets import Static

from haproxy_template_ic.tui.models import DashboardData
from haproxy_template_ic.tui.utils import format_age

logger = logging.getLogger(__name__)

__all__ = ["HeaderWidget"]


class HeaderWidget(Static):
    """Header widget showing operator status and basic info."""

    # Reactive property
    dashboard_data: Reactive[DashboardData] = reactive(DashboardData())

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.border_title = "HAProxy Template IC Dashboard"

    def render(self) -> str:
        """Render the header content."""
        operator = self.dashboard_data.operator

        # Status indicator
        status = operator.status
        status_emoji = {
            "RUNNING": "🟢",
            "STARTING": "🟡",
            "ERROR": "🔴",
            "DISCONNECTED": "🔴",
            "UNKNOWN": "⚫",
        }.get(status, "⚫")

        # Build first line: operator status
        line1_parts = [
            f"{status_emoji} Status: {status}",
            f"Version: {operator.version or 'unknown'}",
            f"Namespace: {operator.namespace}",
            f"Config: {operator.configmap_name or 'unknown'}",
        ]
        last_update = self.dashboard_data.last_update
        if last_update:
            if isinstance(last_update, datetime):
                age_str = format_age(last_update)
                line1_parts.append(f"Updated: {age_str}")

        # Add controller pod name if available
        if operator.controller_pod_name:
            line1_parts.append(f"Pod: {operator.controller_pod_name}")

        line1 = " │ ".join(line1_parts)

        return line1

    def watch_dashboard_data(self, dashboard_data: DashboardData) -> None:
        """Update when dashboard data changes."""
        self.refresh()
