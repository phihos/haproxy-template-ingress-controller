"""
Activity widget for the TUI dashboard.

Shows activity feed and log entries using a Log widget.
"""

import logging
from datetime import datetime

from textual.widgets import RichLog
from textual.reactive import Reactive, reactive
from rich.text import Text

from haproxy_template_ic.tui.models import DashboardData
from haproxy_template_ic.activity import ActivityEvent

logger = logging.getLogger(__name__)

__all__ = ["ActivityWidget"]


class ActivityWidget(RichLog):
    """Widget displaying activity feed and log entries."""

    # Reactive property
    dashboard_data: Reactive[DashboardData] = reactive(DashboardData())

    def __init__(self, **kwargs):
        super().__init__(auto_scroll=True, highlight=True, **kwargs)
        self.border_title = "Activity Feed"
        self._last_activity_count = 0
        self._showing_welcome = True

    def watch_dashboard_data(self, dashboard_data: DashboardData) -> None:
        """Update when dashboard data changes."""
        activity_data = dashboard_data.activity

        # Only add new activity entries to avoid duplicate entries
        current_count = len(activity_data)
        if current_count <= self._last_activity_count:
            return

        # If this is the first activity arriving and we're showing welcome, clear it
        if self._showing_welcome and current_count > 0:
            self.clear()
            self._showing_welcome = False

        # Add new entries
        new_entries = activity_data[self._last_activity_count :]
        for entry in new_entries:
            self._add_activity_entry(entry)

        self._last_activity_count = current_count

    def _add_activity_entry(self, entry: ActivityEvent) -> None:
        """Add a single activity entry to the log."""
        try:
            # Extract entry information from ActivityEvent model
            timestamp_str = entry.timestamp  # This is an ISO string
            event_type = entry.type  # This is an EventType enum
            message = entry.message
            source = entry.source or "system"

            # Format timestamp - convert ISO string to local time
            time_str = ""
            if timestamp_str:
                try:
                    # Parse ISO timestamp and convert to local time
                    utc_dt = datetime.fromisoformat(
                        timestamp_str.replace("Z", "+00:00")
                    )
                    local_dt = utc_dt.astimezone()
                    time_str = local_dt.strftime("%H:%M:%S")
                except Exception:
                    # Fallback - just show first 8 chars if parsing fails
                    time_str = str(timestamp_str)[:8]

            # Choose color/style based on event type
            event_type_str = str(event_type) if event_type else "INFO"
            if event_type_str == "ERROR":
                style = "[red]"
                icon = "❌"
            elif event_type_str in ["CREATE", "SUCCESS"]:
                style = "[green]"
                icon = "✅" if event_type_str == "SUCCESS" else "➕"
            elif event_type_str in ["UPDATE", "SYNC"]:
                style = "[blue]"
                icon = "🔄" if event_type_str == "SYNC" else "📝"
            elif event_type_str == "DELETE":
                style = "[yellow]"
                icon = "➖"
            elif event_type_str == "RELOAD":
                style = "[cyan]"
                icon = "🔄"
            else:  # INFO or unknown
                style = "[white]"
                icon = "ℹ️"

            # Format source
            source_str = f"[{source}]" if source and source != "system" else ""

            # Build the log line
            if time_str:
                log_line = f"{style}{time_str} {icon} {source_str} {message}[/]"
            else:
                log_line = f"{style}{icon} {source_str} {message}[/]"

            # Write to log with Rich markup processing
            self.write(Text.from_markup(log_line))

        except Exception as e:
            logger.error(f"Error adding activity entry: {e}", exc_info=True)
            # Fallback: write raw message
            self.write(f"📝 {entry.message}")

    def on_mount(self) -> None:
        """Initialize the activity widget."""
        # Show welcome message regardless of initial activity_data state
        # since data may arrive after mounting via reactive properties
        self.write("🚀 HAProxy Template IC Activity Feed")
        self.write("📝 Real-time operator and pod events will appear here")
        self._showing_welcome = True
