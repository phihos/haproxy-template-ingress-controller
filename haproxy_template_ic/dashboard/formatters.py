"""
Data formatting utilities for the dashboard.

Provides helper functions for formatting various types of data
for display in the Rich UI components.
"""

from typing import Dict, List, Optional, Union
from datetime import datetime, timezone
import re

__all__ = [
    "format_bytes",
    "format_duration",
    "format_timestamp",
    "format_percentage",
    "truncate_text",
    "format_resource_name",
    "create_sparkline",
    "format_status",
]


def format_bytes(bytes_value: Union[int, str]) -> str:
    """Format bytes value into human readable format.

    Args:
        bytes_value: Number of bytes or string with unit

    Returns:
        Formatted string like "1.2KB", "3.4MB", etc.
    """
    if isinstance(bytes_value, str):
        # Try to parse if it's already a string with units
        match = re.match(r"^(\d+(?:\.\d+)?)\s*([KMGT]?i?[Bb]?)$", bytes_value.strip())
        if match:
            num, unit = match.groups()
            unit = unit.upper()

            # If it has a unit (not just B), format consistently for string inputs
            if unit and unit != "B":
                original = bytes_value.strip()
                # If it doesn't have a decimal point, add .0 for consistency
                if "." not in num:
                    return f"{float(num):.1f}{unit}"
                else:
                    return original

            # If it's just "B" or numeric only, convert to appropriate format
            num = float(num)

            # Handle case where it's like "1024B" - should stay as "1024B"
            if unit == "B":
                return bytes_value.strip()

            # Numeric only string - convert to bytes and format
            bytes_value = int(num)
        else:
            return str(bytes_value)  # Return as-is if we can't parse

    if not isinstance(bytes_value, (int, float)):
        return str(bytes_value)

    bytes_value = int(bytes_value)

    if bytes_value < 1024:
        return f"{bytes_value}B"
    elif bytes_value < 1024**2:
        return f"{bytes_value / 1024:.1f}KB"
    elif bytes_value < 1024**3:
        return f"{bytes_value / 1024**2:.1f}MB"
    elif bytes_value < 1024**4:
        return f"{bytes_value / 1024**3:.1f}GB"
    else:
        return f"{bytes_value / 1024**4:.1f}TB"


def format_duration(milliseconds: Union[int, float, str]) -> str:
    """Format duration in milliseconds to human readable format.

    Args:
        milliseconds: Duration in milliseconds

    Returns:
        Formatted string like "123ms", "1.2s", "2m 30s", etc.
    """
    if isinstance(milliseconds, str):
        # Try to parse if it's already formatted
        if milliseconds.endswith("ms"):
            return milliseconds
        elif milliseconds.endswith("s"):
            return milliseconds
        else:
            try:
                milliseconds = float(milliseconds)
            except ValueError:
                return str(milliseconds)

    if not isinstance(milliseconds, (int, float)):
        return str(milliseconds)

    ms = float(milliseconds)

    if ms < 1000:
        return f"{ms:.0f}ms"
    elif ms < 60000:  # Less than 1 minute
        return f"{ms / 1000:.1f}s"
    elif ms < 3600000:  # Less than 1 hour
        minutes = int(ms // 60000)
        seconds = int((ms % 60000) // 1000)
        return f"{minutes}m {seconds}s"
    else:
        hours = int(ms // 3600000)
        minutes = int((ms % 3600000) // 60000)
        return f"{hours}h {minutes}m"


def format_timestamp(timestamp: Union[str, datetime]) -> str:
    """Format timestamp for display.

    Args:
        timestamp: ISO timestamp string or datetime object

    Returns:
        Formatted time string like "14:32:45" or "2h ago" in local timezone
    """
    if isinstance(timestamp, str):
        try:
            # Handle various timestamp formats
            if timestamp.endswith("Z"):
                dt = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
            elif "+" in timestamp or timestamp.endswith("+00:00"):
                dt = datetime.fromisoformat(timestamp)
            else:
                # Assume UTC if no timezone info
                dt = datetime.fromisoformat(timestamp).replace(tzinfo=timezone.utc)
        except ValueError:
            return timestamp  # Return as-is if we can't parse
    elif isinstance(timestamp, datetime):
        dt = timestamp
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
    else:
        return str(timestamp)

    # Convert to local timezone for display
    local_dt = dt.astimezone()

    now = datetime.now(timezone.utc)
    diff = now - dt

    # If within last minute, show seconds ago
    if diff.total_seconds() < 60:
        return f"{int(diff.total_seconds())}s ago"
    # If within last hour, show minutes ago
    elif diff.total_seconds() < 3600:
        return f"{int(diff.total_seconds() // 60)}m ago"
    # If today, show local time
    elif diff.days == 0:
        return local_dt.strftime("%H:%M:%S")
    # If within last week, show day and local time
    elif diff.days < 7:
        return local_dt.strftime("%a %H:%M")
    # Otherwise show date and local time
    else:
        return local_dt.strftime("%m/%d %H:%M")


def format_percentage(value: Union[int, float, str], decimal_places: int = 1) -> str:
    """Format percentage value.

    Args:
        value: Percentage value (0-100 or 0-1)
        decimal_places: Number of decimal places

    Returns:
        Formatted percentage string like "85.0%"
    """
    if isinstance(value, str):
        if value.endswith("%"):
            return value
        try:
            value = float(value)
        except ValueError:
            return str(value)

    if not isinstance(value, (int, float)):
        return str(value)

    # Assume 0-1 range if value is <= 1
    if value <= 1:
        value = value * 100

    return f"{value:.{decimal_places}f}%"


def truncate_text(text: str, max_length: int, suffix: str = "...") -> str:
    """Truncate text to maximum length with optional suffix.

    Args:
        text: Text to truncate
        max_length: Maximum length including suffix
        suffix: Suffix to add if truncated

    Returns:
        Truncated text
    """
    if len(text) <= max_length:
        return text

    if len(suffix) >= max_length:
        return text[:max_length]

    return text[: max_length - len(suffix)] + suffix


def format_resource_name(name: str, max_length: int = 20) -> str:
    """Format Kubernetes resource name for display.

    Args:
        name: Resource name
        max_length: Maximum display length

    Returns:
        Formatted name, possibly truncated
    """
    if len(name) <= max_length:
        return name

    # For long names, try to keep meaningful parts
    # e.g., "haproxy-template-ic-7d9f8b6-x2kt9" -> "haproxy-ic-x2kt9"
    parts = name.split("-")

    if len(parts) >= 3:
        # Try to use first and last parts
        first = parts[0]
        last = parts[-1]

        # Add middle parts if they fit
        result = first
        for i in range(1, len(parts) - 1):
            candidate = result + "-" + parts[i]
            if len(candidate) + len(last) + 1 <= max_length:
                result = candidate
            else:
                break

        result = result + "-" + last

        if len(result) <= max_length:
            return result

    # Fallback to simple truncation
    return truncate_text(name, max_length)


def create_sparkline(values: List[Union[int, float]], width: int = 16) -> str:
    """Create a simple sparkline from numeric values.

    Args:
        values: List of numeric values
        width: Width of sparkline in characters

    Returns:
        Sparkline string using Unicode block characters
    """
    if not values or width <= 0:
        return ""

    # Normalize values to 0-7 range (8 levels for block characters)
    try:
        numeric_values = [float(v) for v in values if isinstance(v, (int, float, str))]
        if not numeric_values:
            return "▁" * width

        min_val = min(numeric_values)
        max_val = max(numeric_values)

        if min_val == max_val:
            return "▄" * width

        # Map to sparkline characters
        chars = "▁▂▃▄▅▆▇█"

        # Sample values to fit width
        if len(numeric_values) > width:
            # Take evenly spaced samples
            step = len(numeric_values) / width
            sampled = [numeric_values[int(i * step)] for i in range(width)]
        else:
            # Pad with last value if needed
            sampled = numeric_values + [numeric_values[-1]] * (
                width - len(numeric_values)
            )
            sampled = sampled[:width]

        # Convert to sparkline
        result = ""
        for val in sampled:
            normalized = (val - min_val) / (max_val - min_val)
            char_index = min(7, int(normalized * 7.99))  # 0-7 range
            result += chars[char_index]

        return result

    except (ValueError, TypeError, ZeroDivisionError):
        return "▁" * width


def format_status(status: str, status_map: Optional[Dict[str, tuple]] = None) -> tuple:
    """Format status with appropriate emoji and color.

    Args:
        status: Status string
        status_map: Optional custom status mapping

    Returns:
        Tuple of (formatted_text, color_style)
    """
    if status_map is None:
        status_map = {
            # Kubernetes pod phases
            "Running": ("✅ Running", "green"),
            "Pending": ("🟡 Pending", "yellow"),
            "Succeeded": ("✅ Succeeded", "green"),
            "Failed": ("❌ Failed", "red"),
            "Unknown": ("⚪ Unknown", "dim"),
            # HAProxy status
            "UP": ("🟢 UP", "green"),
            "DOWN": ("🔴 DOWN", "red"),
            "MAINT": ("🟡 MAINT", "yellow"),
            "DRAIN": ("🟠 DRAIN", "orange"),
            # General status
            "RUNNING": ("🚀 RUNNING", "green"),
            "STARTING": ("🟡 STARTING", "yellow"),
            "ERROR": ("❌ ERROR", "red"),
            "HEALTHY": ("✅ HEALTHY", "green"),
            "UNHEALTHY": ("❌ UNHEALTHY", "red"),
            # Sync status
            "SYNCED": ("✓ SYNCED", "green"),
            "PENDING_SYNC": ("🔄 PENDING", "yellow"),
            "SYNC_ERROR": ("❌ SYNC ERROR", "red"),
        }

    # Try exact case first
    if status in status_map:
        return status_map[status]

    # Try case-insensitive lookup, preferring proper case over uppercase
    status_lower = status.lower()
    for key in status_map:
        if key.lower() == status_lower:
            return status_map[key]

    # Default formatting
    return (f"⚪ {status}", "dim")
