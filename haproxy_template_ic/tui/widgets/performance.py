"""
Performance widget for the TUI dashboard.

Shows performance metrics and sparklines (when available).
"""

import logging
from datetime import datetime, timezone
from typing import List, Optional

from textual.app import ComposeResult
from textual.containers import ScrollableContainer
from textual.widgets import Static
from textual.reactive import Reactive, reactive

from haproxy_template_ic.constants import SECONDS_PER_HOUR, SECONDS_PER_MINUTE
from haproxy_template_ic.tui.models import DashboardData, PerformanceMetric

logger = logging.getLogger(__name__)

__all__ = ["PerformanceWidget"]


class PerformanceWidget(ScrollableContainer):
    """Widget displaying performance metrics with sparkline visualizations."""

    # Reactive property
    dashboard_data: Reactive[DashboardData] = reactive(DashboardData())

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.border_title = "Performance Metrics"

    def compose(self) -> ComposeResult:
        """Create the child Static widget for content."""
        yield Static("", id="performance-content")

    def _generate_content(self) -> str:
        """Generate the performance metrics content with enhanced formatting."""

        performance_data = self.dashboard_data.performance

        # Check if we have any performance data
        has_template_data = (
            performance_data.template_render
            and performance_data.template_render.p50 is not None
        )
        has_api_data = (
            performance_data.dataplane_api
            and performance_data.dataplane_api.p50 is not None
        )
        has_sync_data = performance_data.total_syncs > 0

        if not (has_template_data or has_api_data or has_sync_data):
            return "❌ No performance data available\nℹ️  Check if HAProxy pods are running\n🔄 Use 'r' to refresh data"

        lines = []

        # Performance Overview Header
        lines.append("━━━ Performance Overview ━━━")

        # Overall status based on worst metric
        overall_status = "⚡ Excellent"
        if has_template_data and performance_data.template_render is not None:
            template_status = self._get_performance_status(
                performance_data.template_render, "template"
            )
            if "Slow" in template_status:
                overall_status = template_status
        if has_api_data and performance_data.dataplane_api is not None:
            api_status = self._get_performance_status(
                performance_data.dataplane_api, "api"
            )
            if "Very Slow" in api_status or (
                "Slow" in api_status and "Excellent" in overall_status
            ):
                overall_status = api_status

        lines.append(f"🎯 Current Status: {overall_status}")
        lines.append("")  # Separator

        # Template Rendering Section
        if has_template_data and performance_data.template_render is not None:
            template_metric = performance_data.template_render
            uptime = self._calculate_uptime()
            uptime_text = (
                f" (since startup: {uptime})" if uptime else " (since startup)"
            )

            lines.append(f"📊 Template Rendering{uptime_text}")
            lines.append(f"   {self._format_percentiles(template_metric)}")

            # Add throughput if we can estimate it
            throughput = self._calculate_throughput(template_metric)
            if throughput:
                lines.append(f"   Throughput: ~{throughput:.0f} ops/min")

            template_status = self._get_performance_status(template_metric, "template")
            lines.append(f"   Status: {template_status}")
            lines.append("")  # Separator

        # Dataplane API Section
        if has_api_data and performance_data.dataplane_api is not None:
            api_metric = performance_data.dataplane_api
            uptime = self._calculate_uptime()
            uptime_text = (
                f" (since startup: {uptime})" if uptime else " (since startup)"
            )

            lines.append(f"📡 Dataplane API{uptime_text}")
            lines.append(f"   {self._format_percentiles(api_metric)}")

            # Add throughput if we can estimate it
            throughput = self._calculate_throughput(api_metric)
            if throughput:
                lines.append(f"   Throughput: ~{throughput:.0f} ops/min")

            api_status = self._get_performance_status(api_metric, "api")
            lines.append(f"   Status: {api_status}")
            lines.append("")  # Separator

        # Sync Statistics Section
        if has_sync_data:
            lines.append("📈 Sync Statistics")
            lines.append(
                f"   Total: {performance_data.total_syncs}  Failed: {performance_data.failed_syncs}"
            )

            if performance_data.sync_success_rate is not None:
                success_rate = performance_data.sync_success_rate * 100
                if success_rate >= 95:
                    status_emoji = "✅"
                elif success_rate >= 80:
                    status_emoji = "⚠️"
                else:
                    status_emoji = "🚨"
                lines.append(f"   Success Rate: {status_emoji} {success_rate:.1f}%")
            lines.append("")  # Separator

        # Enhanced Sparklines Section
        sparklines = self._generate_sparklines()
        if sparklines:
            lines.append("━━━ Trends (recent activity) ━━━")
            lines.extend(sparklines)

        # Remove trailing separator
        while lines and lines[-1] == "":
            lines.pop()

        return "\n".join(lines)

    def watch_dashboard_data(self, dashboard_data: DashboardData) -> None:
        """Update when dashboard data changes."""
        try:
            content_widget = self.query_one("#performance-content", Static)
            content_widget.update(self._generate_content())
        except Exception as e:
            logger.debug(f"Error updating performance content: {e}")

    def on_mount(self) -> None:
        """Initialize the widget content when mounted."""
        try:
            content_widget = self.query_one("#performance-content", Static)
            content_widget.update(self._generate_content())
        except Exception as e:
            logger.debug(f"Error initializing performance content: {e}")

    def _generate_sparklines(self) -> List[str]:
        """Generate enhanced ASCII sparklines with value ranges."""
        sparklines = []
        performance_data = self.dashboard_data.performance

        try:
            # Template render sparkline from model data
            if (
                performance_data.template_render
                and performance_data.template_render.history
                and len(performance_data.template_render.history) >= 3
            ):
                history_ms = performance_data.template_render.history
                min_val = min(history_ms)
                max_val = max(history_ms)

                # Convert to seconds for sparkline creation
                history_seconds = [x / 1000 for x in history_ms]
                sparkline = self._create_sparkline(
                    history_seconds, "🎨 Templates", unit=""
                )
                if sparkline:
                    # Add range information
                    min_str = self._format_duration_from_ms(min_val)
                    max_str = self._format_duration_from_ms(max_val)
                    range_str = f"{min_str}-{max_str} range"
                    sparklines.append(f"{sparkline} ({range_str})")

            # Dataplane API sparkline from model data
            if (
                performance_data.dataplane_api
                and performance_data.dataplane_api.history
                and len(performance_data.dataplane_api.history) >= 3
            ):
                history_ms = performance_data.dataplane_api.history
                min_val = min(history_ms)
                max_val = max(history_ms)

                # Convert to seconds for sparkline creation
                history_seconds = [x / 1000 for x in history_ms]
                sparkline = self._create_sparkline(
                    history_seconds, "🔄 API Calls", unit=""
                )
                if sparkline:
                    # Add range information
                    min_str = self._format_duration_from_ms(min_val)
                    max_str = self._format_duration_from_ms(max_val)
                    range_str = f"{min_str}-{max_str} range"
                    sparklines.append(f"{sparkline} ({range_str})")

            # Success rate pattern from model data
            if performance_data.sync_pattern:
                sparklines.append(f"📊 Sync Pattern: {performance_data.sync_pattern}")

        except Exception as e:
            logger.debug(f"Error generating sparklines: {e}")

        return sparklines

    def _create_sparkline(
        self, values: List[float], label: str, unit: str = ""
    ) -> Optional[str]:
        """Create an ASCII sparkline from a list of values."""
        if len(values) < 2:
            return None

        try:
            # Sparkline characters from low to high
            chars = ["▁", "▂", "▃", "▄", "▅", "▆", "▇", "█"]

            # Handle edge case where all values are the same
            min_val = min(values)
            max_val = max(values)

            if max_val == min_val:
                # All values are the same - use middle character
                sparkline_chars = [chars[len(chars) // 2]] * len(values)
                trend_indicator = "→"
            else:
                # Normalize values to 0-7 range for sparkline characters
                range_val = max_val - min_val
                sparkline_chars = []

                for value in values:
                    normalized = (value - min_val) / range_val
                    char_index = min(int(normalized * (len(chars) - 1)), len(chars) - 1)
                    sparkline_chars.append(chars[char_index])

                # Determine trend (compare last 3 values to first 3)
                if len(values) >= 6:
                    first_avg = sum(values[:3]) / 3
                    last_avg = sum(values[-3:]) / 3
                    if last_avg > first_avg * 1.05:
                        trend_indicator = "↗️"
                    elif last_avg < first_avg * 0.95:
                        trend_indicator = "↘️"
                    else:
                        trend_indicator = "→"
                else:
                    # For shorter sequences, compare first and last
                    if values[-1] > values[0] * 1.1:
                        trend_indicator = "↗️"
                    elif values[-1] < values[0] * 0.9:
                        trend_indicator = "↘️"
                    else:
                        trend_indicator = "→"

            # Limit sparkline to reasonable width
            display_chars = (
                sparkline_chars[-15:] if len(sparkline_chars) > 15 else sparkline_chars
            )
            current_value = values[-1]

            # Format the sparkline
            sparkline_str = "".join(display_chars)

            if unit:
                return f"{label}: {sparkline_str} {trend_indicator} {current_value:.3f}{unit}"
            else:
                return f"{label}: {sparkline_str} {trend_indicator} {current_value:.3f}"

        except Exception as e:
            logger.debug(f"Error creating sparkline for {label}: {e}")
            return None

    def _format_duration(self, seconds: Optional[float]) -> str:
        """Format duration with appropriate units (μs, ms, s)."""
        if seconds is None:
            return "N/A"

        if seconds < 0.001:  # Less than 1ms
            microseconds = seconds * 1_000_000
            return f"{microseconds:.0f}μs"
        elif seconds < 1.0:  # Less than 1s
            milliseconds = seconds * 1000
            return f"{milliseconds:.1f}ms"
        else:
            return f"{seconds:.3f}s"

    def _format_duration_from_ms(self, milliseconds: Optional[float]) -> str:
        """Format duration from milliseconds value."""
        if milliseconds is None:
            return "N/A"

        if milliseconds < 1.0:
            microseconds = milliseconds * 1000
            return f"{microseconds:.0f}μs"
        elif milliseconds < 1000:
            return f"{milliseconds:.1f}ms"
        else:
            seconds = milliseconds / 1000
            return f"{seconds:.3f}s"

    def _get_performance_status(
        self, metric: "PerformanceMetric", metric_type: str
    ) -> str:
        """Get performance status emoji and text based on metric values."""
        if not metric or metric.p50 is None:
            return "❓ Unknown"

        p50_ms = metric.p50

        if metric_type == "template":
            # Template rendering thresholds (in ms)
            if p50_ms < 10:
                return "⚡ Excellent"
            elif p50_ms < 50:
                return "✅ Good"
            elif p50_ms < 100:
                return "⚠️ Slow"
            else:
                return "🐌 Very Slow"
        elif metric_type == "api":
            # API operation thresholds (in ms)
            if p50_ms < 100:
                return "⚡ Excellent"
            elif p50_ms < 500:
                return "✅ Good"
            elif p50_ms < 1000:
                return "⚠️ Slow"
            else:
                return "🐌 Very Slow"

        return "❓ Unknown"

    def _format_percentiles(self, metric: "PerformanceMetric") -> str:
        """Format percentiles nicely (P50/P95/P99)."""
        if not metric:
            return "N/A"

        p50 = (
            self._format_duration_from_ms(metric.p50)
            if metric.p50 is not None
            else "N/A"
        )
        p95 = (
            self._format_duration_from_ms(metric.p95)
            if metric.p95 is not None
            else "N/A"
        )
        p99 = (
            self._format_duration_from_ms(metric.p99)
            if metric.p99 is not None
            else "N/A"
        )

        return f"P50: {p50:<6} P95: {p95:<6} P99: {p99}"

    def _calculate_throughput(self, metric: "PerformanceMetric") -> Optional[float]:
        """Calculate approximate throughput (ops/min) from history data."""
        if not metric or not metric.history or len(metric.history) < 2:
            return None

        # Rough estimate: assume history represents operations over the last few minutes
        # This is a simplified calculation - in reality we'd need timestamps
        recent_operations = len(metric.history)
        # Assume history covers last 5 minutes
        estimated_time_minutes = 5
        throughput_per_minute = recent_operations * (
            SECONDS_PER_MINUTE / (estimated_time_minutes * SECONDS_PER_MINUTE)
        )

        return max(1.0, throughput_per_minute)  # At least 1 op/min

    def _calculate_uptime(self) -> Optional[str]:
        """Calculate uptime since controller pod started."""
        try:
            controller_start_time = (
                self.dashboard_data.operator.controller_pod_start_time
            )
            if not controller_start_time:
                return None

            # Parse the start time (ISO format)
            if controller_start_time.endswith("Z"):
                controller_start_time = controller_start_time[:-1] + "+00:00"

            start_dt = datetime.fromisoformat(controller_start_time)

            # Convert to UTC for calculation
            if start_dt.tzinfo is None:
                start_dt = start_dt.replace(tzinfo=timezone.utc)

            now = datetime.now(start_dt.tzinfo)
            uptime = now - start_dt

            # Format uptime
            days = uptime.days
            hours, remainder = divmod(uptime.seconds, SECONDS_PER_HOUR)
            minutes = remainder // SECONDS_PER_MINUTE

            if days > 0:
                return f"{days}d {hours}h {minutes}m"
            elif hours > 0:
                return f"{hours}h {minutes}m"
            else:
                return f"{minutes}m"

        except Exception as e:
            logger.debug(f"Error calculating uptime: {e}")
            return None
