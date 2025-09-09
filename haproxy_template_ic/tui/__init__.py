"""
Textual TUI dashboard for HAProxy Template IC.

This package provides a modern Terminal User Interface (TUI) dashboard
built with the Textual framework for monitoring HAProxy Template IC
operator status, pod health, template rendering, and resource synchronization.
"""

from .launcher import TuiLauncher

__all__ = ["TuiLauncher"]
