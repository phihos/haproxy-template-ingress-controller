"""
Utility functions for the TUI dashboard.

Contains common formatting and helper functions used across TUI widgets.
"""

import logging
from datetime import datetime, timezone
from typing import Any, Optional

from haproxy_template_ic.constants import (
    BYTES_PER_KB,
    BYTES_PER_MB,
    BYTES_PER_GB,
    SECONDS_PER_MINUTE,
    SECONDS_PER_HOUR,
)

logger = logging.getLogger(__name__)

__all__ = ["format_size", "format_timestamp", "format_age", "parse_iso_timestamp"]


def parse_iso_timestamp(timestamp_value: Any) -> Optional[datetime]:
    """Parse ISO timestamp from string or return existing datetime.

    Handles common ISO timestamp formats including Z suffix.

    Args:
        timestamp_value: String or datetime object to parse

    Returns:
        Parsed datetime object or None if parsing fails
    """
    if isinstance(timestamp_value, datetime):
        return timestamp_value
    if isinstance(timestamp_value, str):
        try:
            # Handle Z suffix and other ISO formats
            return datetime.fromisoformat(timestamp_value.replace("Z", "+00:00"))
        except (ValueError, TypeError):
            return None
    return None


def format_size(size: Any) -> str:
    """
    Format file size in human readable format.

    Args:
        size: Size in bytes (int, float, or string)

    Returns:
        Formatted size string (e.g., "1.2KB", "512B")
    """
    try:
        if isinstance(size, str):
            size = int(size)

        if not isinstance(size, (int, float)):
            return "0B"

        if size <= 0:
            return "0B"
        elif size < BYTES_PER_KB:
            return f"{size}B"
        elif size < BYTES_PER_MB:
            return f"{size / BYTES_PER_KB:.1f}KB"
        elif size < BYTES_PER_GB:
            return f"{size / BYTES_PER_MB:.1f}MB"
        else:
            return f"{size / BYTES_PER_GB:.1f}GB"

    except Exception as e:
        logger.debug(f"Error formatting size {size}: {e}")
        return "0B"


def format_timestamp(timestamp: Any, format_str: str = "%H:%M:%S") -> str:
    """
    Format timestamp to human readable string.

    Args:
        timestamp: ISO timestamp string, datetime object, or other
        format_str: strftime format string

    Returns:
        Formatted timestamp string
    """
    try:
        if not timestamp:
            return "-"

        if isinstance(timestamp, str):
            # Handle ISO timestamp
            if "T" in timestamp:
                if timestamp.endswith("Z"):
                    timestamp = f"{timestamp[:-1]}+00:00"
                dt = datetime.fromisoformat(timestamp)
                # Convert to local time before formatting
                return dt.astimezone().strftime(format_str)
            else:
                return timestamp  # Already formatted

        elif isinstance(timestamp, datetime):
            # Convert to local time before formatting if it has timezone info
            if timestamp.tzinfo is not None:
                return timestamp.astimezone().strftime(format_str)
            else:
                return timestamp.strftime(format_str)
        else:
            return str(timestamp)

    except Exception as e:
        logger.debug(f"Error formatting timestamp {timestamp}: {e}")
        return str(timestamp) if timestamp else "Unknown"


def format_age(created_timestamp: Any) -> str:
    """
    Calculate and format age from creation timestamp.

    Args:
        created_timestamp: Creation timestamp (ISO string or datetime)

    Returns:
        Formatted age string (e.g., "2h", "30m", "<1m")
    """
    try:
        if not created_timestamp:
            return "Unknown"

        if isinstance(created_timestamp, str):
            if created_timestamp.endswith("Z"):
                created_timestamp = f"{created_timestamp[:-1]}+00:00"
            elif "+" not in created_timestamp and "T" in created_timestamp:
                created_timestamp += "+00:00"
            dt = datetime.fromisoformat(created_timestamp)
        elif isinstance(created_timestamp, datetime):
            dt = created_timestamp
        else:
            return "Unknown"

        # Ensure timezone info
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)

        # Calculate age
        now = datetime.now(timezone.utc)
        delta = now - dt

        days = delta.days
        hours = delta.seconds // 3600
        minutes = (delta.seconds % SECONDS_PER_HOUR) // SECONDS_PER_MINUTE

        if days > 0:
            return f"{days}d"
        elif hours > 0:
            return f"{hours}h"
        elif minutes > 0:
            return f"{minutes}m"
        else:
            return "<1m"

    except Exception as e:
        logger.debug(f"Error calculating age from {created_timestamp}: {e}")
        return "Unknown"
