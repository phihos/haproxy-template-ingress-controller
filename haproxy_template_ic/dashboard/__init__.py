"""
Live status dashboard for HAProxy Template IC.

This package provides a real-time terminal UI for monitoring HAProxy Template IC
operator status, pod health, template rendering, and resource synchronization.
"""

from .launcher import DashboardLauncher
from .compatibility import CompatibilityLevel, check_compatibility

__all__ = ["DashboardLauncher", "CompatibilityLevel", "check_compatibility"]
