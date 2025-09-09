"""
Textual widgets for the TUI dashboard.

Contains custom widgets for displaying different aspects of the
HAProxy Template IC status and metrics.
"""

from .header import HeaderWidget
from .pods import PodsWidget
from .templates import TemplatesWidget
from .resources import ResourcesWidget
from .performance import PerformanceWidget
from .activity import ActivityWidget
from .inspector import TemplateInspectorWidget

__all__ = [
    "HeaderWidget",
    "PodsWidget",
    "TemplatesWidget",
    "ResourcesWidget",
    "PerformanceWidget",
    "ActivityWidget",
    "TemplateInspectorWidget",
]
