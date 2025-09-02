"""
Rich UI panels for the dashboard.

Contains panel components for displaying different aspects of the
HAProxy Template IC status and metrics.
"""

from typing import Dict, Any
from rich.table import Table
from rich.panel import Panel
from rich.text import Text
from datetime import datetime, timezone
import logging

from .compatibility import CompatibilityLevel
from .formatters import create_sparkline, format_bytes, format_timestamp

logger = logging.getLogger(__name__)

__all__ = [
    "HeaderPanel",
    "PodsPanel",
    "TemplatesPanel",
    "ResourcesPanel",
    "PerformancePanel",
    "ActivityPanel",
]


def _format_duration(start_time_str: str) -> str:
    """Format duration from ISO timestamp to human readable format."""
    try:
        # Parse the ISO timestamp
        if start_time_str.endswith("Z"):
            start_time_str = start_time_str[:-1] + "+00:00"
        elif "+" not in start_time_str and "T" in start_time_str:
            start_time_str += "+00:00"

        start_time = datetime.fromisoformat(start_time_str)

        # Calculate duration
        now = datetime.now(timezone.utc)
        if start_time.tzinfo is None:
            start_time = start_time.replace(tzinfo=timezone.utc)

        duration = now - start_time
        total_seconds = int(duration.total_seconds())

        # Format as human readable
        if total_seconds < 60:
            return f"{total_seconds}s"
        elif total_seconds < 3600:  # Less than 1 hour
            minutes = total_seconds // 60
            seconds = total_seconds % 60
            if seconds == 0:
                return f"{minutes}m"
            return f"{minutes}m {seconds}s"
        elif total_seconds < 86400:  # Less than 1 day
            hours = total_seconds // 3600
            minutes = (total_seconds % 3600) // 60
            if minutes == 0:
                return f"{hours}h"
            return f"{hours}h {minutes}m"
        else:  # 1 day or more
            days = total_seconds // 86400
            hours = (total_seconds % 86400) // 3600
            if hours == 0:
                return f"{days}d"
            return f"{days}d {hours}h"
    except Exception as e:
        logger.debug(f"Failed to format duration from '{start_time_str}': {e}")
        return "unknown"


class HeaderPanel:
    """Header panel showing operator status and basic info."""

    def render(self, data: Dict[str, Any], compatibility: CompatibilityLevel) -> Panel:
        """Render the header panel."""
        operator = data.get("operator", {})

        # Status indicator
        status = operator.get("status", "UNKNOWN")
        status_color = {
            "RUNNING": "green",
            "STARTING": "yellow",
            "ERROR": "red",
            "UNKNOWN": "dim",
        }.get(status, "dim")

        # Build header content
        header_text = Text()

        # First line: operator status
        header_text.append("🚀 Operator Status: ", style="bold")
        header_text.append(status, style=f"bold {status_color}")
        header_text.append("  │  ", style="dim")
        header_text.append(
            f"Version: {operator.get('version', 'unknown')}", style="cyan"
        )
        header_text.append("  │  ", style="dim")
        header_text.append(
            f"Namespace: {operator.get('namespace', 'unknown')}", style="cyan"
        )
        header_text.append("  │  ", style="dim")
        header_text.append(
            f"Config: {operator.get('configmap_name', 'unknown')}", style="cyan"
        )

        # Add controller pod name to visible content
        controller_pod_name = operator.get("controller_pod_name")
        if controller_pod_name:
            header_text.append("  │  ", style="dim")
            header_text.append(f"Pod: {controller_pod_name}", style="cyan")

        # Add compatibility indicator
        if compatibility != CompatibilityLevel.FULL:
            header_text.append("  │  ", style="dim")
            compat_text = {
                CompatibilityLevel.ENHANCED: "Enhanced Mode",
                CompatibilityLevel.BASIC: "Basic Mode",
                CompatibilityLevel.LEGACY: "Legacy Mode",
            }.get(compatibility, "Unknown Mode")
            header_text.append(f"Mode: {compat_text}", style="yellow")

        header_text.append("\n")

        # Second line: compatibility status and controls
        if compatibility == CompatibilityLevel.FULL:
            header_text.append(
                "✅ Full dashboard functionality available", style="green"
            )
        elif compatibility == CompatibilityLevel.ENHANCED:
            header_text.append(
                "⚡ Enhanced dashboard mode (some features available)", style="yellow"
            )
        elif compatibility == CompatibilityLevel.BASIC:
            header_text.append(
                "📊 Basic dashboard mode (limited features)", style="yellow"
            )
        else:  # LEGACY
            header_text.append("⚠️  Legacy mode (minimal functionality)", style="red")

        header_text.append("  │  ", style="dim")
        header_text.append(
            "Press 'q' to quit, 'r' to refresh, 'h' for help, 'd' for debug, Ctrl+C to exit",
            style="dim",
        )

        # Build title with optional controller pod name, uptime, and last reload
        title_parts = ["HAProxy Template IC - Live Status"]

        controller_pod_name = operator.get("controller_pod_name")
        if controller_pod_name:
            title_parts.append(f"({controller_pod_name})")

        # Add uptime if available
        pod_start_time = operator.get("controller_pod_start_time")
        if pod_start_time:
            uptime = _format_duration(pod_start_time)
            title_parts.append(f"Up: {uptime}")

        # Add time since last reload if available
        last_deployment_time = operator.get("last_deployment_time")
        if last_deployment_time:
            reload_age = _format_duration(last_deployment_time)
            title_parts.append(f"Last reload: {reload_age} ago")

        title = " | ".join(title_parts)

        return Panel(header_text, title=title, border_style="blue", padding=(0, 1))


class PodsPanel:
    """Panel showing HAProxy pod status and health."""

    def render(self, data: Dict[str, Any]) -> Panel:
        """Render the pods panel."""
        pods_data = data.get("pods", {})
        if isinstance(pods_data, dict):
            pods = pods_data.get("discovered", [])
        else:
            pods = pods_data if isinstance(pods_data, list) else []

        if not pods:
            return Panel(
                "[yellow]No HAProxy pods found or data unavailable[/yellow]",
                title="🏃 HAProxy Pods",
                border_style="yellow",
            )

        # Check if metrics are available (any pod has non-N/A CPU or memory)
        has_metrics = any(
            pod.get("cpu", "N/A") != "N/A" or pod.get("memory", "N/A") != "N/A"
            for pod in pods
        )

        # Create table
        table = Table(show_header=True, header_style="bold magenta", padding=(0, 1))
        table.add_column("Pod Name", style="cyan", no_wrap=True)
        table.add_column("Status", justify="center", min_width=8)
        table.add_column("IP", style="blue", no_wrap=True)
        table.add_column("Uptime", justify="right", no_wrap=True)

        # Only add CPU and Memory columns if metrics are available
        if has_metrics:
            table.add_column("CPU", justify="right", no_wrap=True)
            table.add_column("Memory", justify="right", no_wrap=True)

        table.add_column("Synced", justify="center", no_wrap=True)
        table.add_column("Last Reload", justify="right", no_wrap=True)

        ready_count = 0
        total_count = len(pods)

        for pod in pods:
            # Status with emoji
            status = pod.get("status", "Unknown")
            if status == "Running":
                status_text = "✅ Ready"
                ready_count += 1
            elif status == "Pending":
                status_text = "🟡 Pending"
            elif status == "Failed":
                status_text = "❌ Failed"
            else:
                status_text = f"⚪ {status}"

            # Format uptime from pod start time
            start_time = pod.get("start_time")
            if start_time:
                uptime_text = _format_duration(start_time)
            else:
                uptime_text = "N/A"

            # Format last reload time
            last_reload_timestamp = pod.get("last_reload_timestamp")
            if last_reload_timestamp:
                last_reload_text = f"{_format_duration(last_reload_timestamp)} ago"
            else:
                last_reload_text = "N/A"

            # Sync status with time-based information and emoji indicators
            synced = pod.get("synced", "Unknown")
            if synced == "Failed":
                sync_text = "❌ Failed"
            elif synced == "Unknown":
                sync_text = "⚠ Unknown"
            elif "ago" in synced:  # Time-based sync status (e.g., "5s ago", "2m ago")
                sync_text = f"✅ {synced}"
            else:
                # Fallback for any unexpected formats
                sync_text = f"⚠ {synced}"

            # Build row data based on available columns
            row_data = [
                pod.get("name", "unknown"),
                status_text,
                pod.get("ip", "N/A"),
                uptime_text,
            ]

            if has_metrics:
                row_data.extend([pod.get("cpu", "N/A"), pod.get("memory", "N/A")])

            row_data.extend([sync_text, last_reload_text])
            table.add_row(*row_data)

        # Build title with metrics indicator
        title = f"🏃 HAProxy Pods ({ready_count}/{total_count} Ready)"
        if not has_metrics:
            title += " [dim](metrics unavailable)[/dim]"

        border_color = "green" if ready_count == total_count else "yellow"

        return Panel(table, title=title, border_style=border_color)


class TemplatesPanel:
    """Panel showing template rendering status."""

    def render(self, data: Dict[str, Any]) -> Panel:
        """Render the templates panel."""
        templates = data.get("templates", {})

        if not templates:
            return Panel(
                "[yellow]No template data available[/yellow]",
                title="📋 Template Status",
                border_style="yellow",
            )

        # Create table
        table = Table(show_header=True, header_style="bold magenta", padding=(0, 1))
        table.add_column("Template", style="cyan", no_wrap=True)
        table.add_column("Type", style="blue", no_wrap=True)
        table.add_column("Size", justify="right", no_wrap=True)
        table.add_column("Status", justify="center", no_wrap=True)
        table.add_column("Last Change", justify="center", no_wrap=True)

        valid_count = 0
        total_count = len(templates)

        for template_name, template_info in templates.items():
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
                valid_count += 1
            elif status == "empty":
                status_text = "⚪ Empty"
            else:
                status_text = f"❌ {status}"

            # Format last change timestamp
            last_change = template_info.get("last_change")
            if last_change:
                # Use format_timestamp function to convert to local timezone
                last_change_text = format_timestamp(last_change)
            else:
                last_change_text = "—"

            table.add_row(
                template_name,
                template_info.get("type", "unknown"),
                size_text,
                status_text,
                last_change_text,
            )

        title = f"📋 Template Status ({valid_count}/{total_count} Valid)"
        border_color = "green" if valid_count == total_count else "yellow"

        return Panel(table, title=title, border_style=border_color)


class ResourcesPanel:
    """Panel showing watched resources statistics."""

    def render(self, data: Dict[str, Any]) -> Panel:
        """Render the resources panel."""
        resources = data.get("resources", {})

        if not resources:
            return Panel(
                "[yellow]No resource data available[/yellow]",
                title="🎯 Watched Resources",
                border_style="yellow",
            )

        # Create table
        table = Table(show_header=True, header_style="bold magenta", padding=(0, 1))
        table.add_column("Resource Type", style="cyan", no_wrap=True)
        table.add_column("Total", justify="right", no_wrap=True)
        table.add_column("Namespaces", justify="right", no_wrap=True)
        table.add_column("Size", justify="right", no_wrap=True)
        table.add_column("Last Change", justify="center", no_wrap=True)
        table.add_column("Top Namespaces", style="blue", no_wrap=False)

        for resource_type, stats in resources.items():
            # Format resource type (remove _index suffix if present)
            display_type = resource_type.replace("_index", "").title()

            total = stats.get("total", 0)
            namespace_count = stats.get("namespace_count", 0)
            memory_size = stats.get("memory_size", 0)
            last_change = stats.get("last_change")
            top_namespaces = stats.get("namespaces", {})

            # Format memory size
            if memory_size > 0:
                size_text = format_bytes(memory_size)
            else:
                size_text = "N/A"

            # Format last change timestamp
            if last_change:
                # Use format_timestamp function to convert to local timezone
                last_change_text = format_timestamp(last_change)
            else:
                last_change_text = "—"

            # Format top namespaces
            if top_namespaces:
                ns_items = list(top_namespaces.items())[:3]  # Top 3
                ns_text = ", ".join([f"{ns}({count})" for ns, count in ns_items])
                if len(top_namespaces) > 3:
                    ns_text += f" +{len(top_namespaces) - 3} more"
            else:
                ns_text = "N/A"

            table.add_row(
                display_type,
                str(total),
                f"{namespace_count} ns",
                size_text,
                last_change_text,
                ns_text,
            )

        return Panel(table, title="🎯 Watched Resources", border_style="cyan")


class PerformancePanel:
    """Panel showing performance metrics and statistics."""

    def render(self, data: Dict[str, Any], compatibility: CompatibilityLevel) -> Panel:
        """Render the performance panel with visual graphs and sparklines."""
        performance = data.get("performance", {})

        if not performance or compatibility not in [
            CompatibilityLevel.FULL,
            CompatibilityLevel.ENHANCED,
        ]:
            # Show placeholder for unavailable performance data
            content = Text()
            content.append("📊 Performance metrics not available\n", style="yellow")
            content.append("(requires operator with enhanced features)\n", style="dim")

            if compatibility == CompatibilityLevel.BASIC:
                content.append(
                    "\nUpgrade operator for performance monitoring", style="dim"
                )

            return Panel(content, title="📊 Performance & Health", border_style="dim")

        # Create enhanced performance display with sparklines
        content = Text()

        # Template render metrics with sparkline
        template_metrics = performance.get("template_render", {})
        if template_metrics:
            p50 = template_metrics.get("p50", "N/A")
            p95 = template_metrics.get("p95", "N/A")
            p99 = template_metrics.get("p99", "N/A")
            history = template_metrics.get("history", [])

            # Create sparkline from historical data
            sparkline = create_sparkline(history, 16) if history else "▁" * 16

            # Color sparkline based on performance (green=fast, yellow=moderate, red=slow)
            if isinstance(p50, (int, float)) and p50 != "N/A":
                sparkline_color = (
                    "green" if p50 < 5 else "yellow" if p50 < 20 else "red"
                )
            else:
                sparkline_color = "dim"

            content.append("Template Render:  ", style="bold")
            content.append(sparkline, style=sparkline_color)
            content.append(f"  {p50}ms\n", style="cyan")
            content.append("                  └─ Last 16 renders ─┘  ", style="dim")
            content.append(f"P50/P95/P99: {p50}/{p95}/{p99}ms", style="cyan")
            content.append("\n\n")

        # Dataplane API metrics with sparkline
        api_metrics = performance.get("dataplane_api", {})
        if api_metrics:
            p50 = api_metrics.get("p50", "N/A")
            p95 = api_metrics.get("p95", "N/A")
            p99 = api_metrics.get("p99", "N/A")
            history = api_metrics.get("history", [])

            # Create sparkline from historical data
            sparkline = create_sparkline(history, 16) if history else "▁" * 16

            # Color sparkline based on performance
            if isinstance(p50, (int, float)) and p50 != "N/A":
                sparkline_color = (
                    "green" if p50 < 50 else "yellow" if p50 < 200 else "red"
                )
            else:
                sparkline_color = "dim"

            content.append("Dataplane API:    ", style="bold")
            content.append(sparkline, style=sparkline_color)
            content.append(f"  {p50}ms\n", style="cyan")
            content.append("                  └─ Last 16 calls ───┘  ", style="dim")
            content.append(f"P50/P95/P99: {p50}/{p95}/{p99}ms", style="cyan")
            content.append("\n\n")

        # Enhanced sync success display with pattern and progress bar
        success_rate = performance.get("sync_success_rate", 0)
        recent_rate = performance.get("recent_sync_success_rate", 0)
        sync_pattern = performance.get("sync_pattern", "")

        if success_rate or sync_pattern:
            # Use recent rate if available, otherwise fallback to overall rate
            display_rate = recent_rate if recent_rate > 0 else success_rate
            rate_percent = (
                int(display_rate * 100)
                if isinstance(display_rate, float)
                else display_rate
            )

            # Create visual progress bar
            bar_length = 20
            filled = int(bar_length * rate_percent / 100)
            bar = "█" * filled + "░" * (bar_length - filled)

            rate_color = (
                "green"
                if rate_percent >= 90
                else "yellow"
                if rate_percent >= 75
                else "red"
            )

            content.append("Sync Success:     ", style="bold")
            content.append(f"{bar} {rate_percent}%", style=rate_color)
            content.append("\n")

            # Show success/failure pattern if available
            if sync_pattern:
                # Truncate pattern to fit nicely
                display_pattern = (
                    sync_pattern[-18:] if len(sync_pattern) > 18 else sync_pattern
                )
                content.append("                  ", style="dim")
                content.append(display_pattern, style="cyan")
                content.append(
                    "\n                  └─ Recent syncs (▲=success ▼=fail) ─┘",
                    style="dim",
                )
                content.append("\n")

        # If no metrics are available
        if not content.plain:
            content.append("No performance data available", style="dim")
            content.append("\n")
            content.append(
                "Metrics will appear after some template rendering and API calls",
                style="dim",
            )

        return Panel(content, title="📊 Performance & Health", border_style="green")


class ActivityPanel:
    """Panel showing recent activity and events."""

    def render(self, data: Dict[str, Any], compatibility: CompatibilityLevel) -> Panel:
        """Render the activity panel."""
        activity_data = data.get("activity", [])

        # Handle different activity data formats
        if isinstance(activity_data, dict):
            # Legacy test format: {"recent_events": [...]}
            activity = activity_data.get("recent_events", [])
        elif isinstance(activity_data, list):
            # New format: directly a list of events
            activity = activity_data
        else:
            activity = []

        errors = data.get("errors", [])

        if compatibility not in [CompatibilityLevel.FULL, CompatibilityLevel.ENHANCED]:
            content = Text()
            content.append(
                "🔄 Activity feed not available in this mode\n", style="yellow"
            )

            # Show any errors that occurred
            if errors:
                content.append("\nData collection errors:\n", style="red")
                for error in errors[:3]:  # Show first 3 errors
                    content.append(f"• {error}\n", style="red")

            return Panel(content, title="🔄 Recent Activity", border_style="dim")

        content = Text()

        if not activity:
            content.append("No recent activity available", style="dim")
        else:
            # Ensure we have a list of events
            if isinstance(activity, list):
                activity_list = activity
            elif hasattr(activity, "values"):  # IndexedResourceCollection or similar
                activity_list = list(activity.values())
            else:
                activity_list = []

            # Show recent events (last 20)
            recent_events = activity_list[-20:] if activity_list else []
            for event in recent_events:
                timestamp = event.get("timestamp", "unknown")
                event_type = event.get("type", "INFO")
                message = event.get("message", "No message")

                # Format timestamp using local timezone
                if timestamp != "unknown":
                    try:
                        time_str = format_timestamp(timestamp)
                    except Exception:
                        time_str = "??:??:??"
                else:
                    time_str = "??:??:??"

                # Event type emoji
                emoji = {
                    "CREATE": "➕",
                    "UPDATE": "📝",
                    "DELETE": "➖",
                    "SYNC": "🔄",
                    "ERROR": "❌",
                    "SUCCESS": "✅",
                }.get(event_type, "ℹ️")

                content.append(f"[{time_str:>8}] {emoji} {message}\n", style="dim")

        # Show errors if any
        if errors:
            content.append("\nData collection errors:\n", style="red")
            for error in errors[:3]:
                content.append(f"• {error}\n", style="red")

        return Panel(content, title="🔄 Recent Activity", border_style="blue")
