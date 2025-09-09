"""
Main Textual TUI application for HAProxy Template IC dashboard.

Contains the primary TuiApp class that manages screens, navigation,
keyboard bindings, and reactive data updates.
"""

import logging
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from haproxy_template_ic.constants import SECONDS_PER_MINUTE

from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Container, Horizontal, Vertical
from textual.reactive import Reactive, reactive
from textual.widgets import Footer, Header

from haproxy_template_ic.activity import ActivityEvent
from haproxy_template_ic.tui.models import (
    OperatorInfo,
    PerformanceInfo,
    ResourceInfo,
    ErrorInfo,
    PodInfo,
    TemplateInfo,
)
from .dashboard_service import DashboardService
from .screens import (
    DebugScreen,
    HelpScreen,
    TemplateInspectorScreen,
    get_tui_log_handler,
)
from .widgets import (
    ActivityWidget,
    HeaderWidget,
    PerformanceWidget,
    PodsWidget,
    ResourcesWidget,
    TemplatesWidget,
)
from .widgets.templates import TemplateSelected

logger = logging.getLogger(__name__)

__all__ = ["TuiApp"]


class TuiApp(App):
    """HAProxy Template IC TUI Dashboard."""

    # CSS path relative to this module
    CSS_PATH = Path(__file__).parent / "styles.css"
    TITLE = "HAProxy Template IC Dashboard"
    SUB_TITLE = "Terminal User Interface"

    # Installed screens for proper screen management
    SCREENS = {
        "help": HelpScreen,
        "debug": DebugScreen,
        # TemplateInspectorScreen is instantiated dynamically with data
    }

    # Key bindings
    BINDINGS = [
        Binding("q", "quit", "Quit"),
        Binding("r", "refresh", "Refresh"),
        Binding("h", "help", "Help"),
        Binding("d", "debug", "Debug"),
        Binding("t", "template_inspector", "Templates"),
        Binding("escape", "back", "Back"),
    ]

    # Reactive properties for data
    operator_status: Reactive[OperatorInfo] = reactive(
        OperatorInfo(status="UNKNOWN", namespace="unknown")
    )
    pods: Reactive[List[PodInfo]] = reactive([])
    templates: Reactive[Dict[str, TemplateInfo]] = reactive({})
    resources: Reactive[ResourceInfo] = reactive(ResourceInfo())
    performance: Reactive[PerformanceInfo] = reactive(PerformanceInfo.empty())
    activity: Reactive[List[ActivityEvent]] = reactive([])

    # State management
    current_screen: Reactive[str] = reactive("main")
    loading: Reactive[bool] = reactive(True)
    last_update: Reactive[Optional[datetime]] = reactive(None, init=False)
    last_error_toast_time: Reactive[Optional[Tuple[str, float]]] = reactive(
        None, init=False
    )  # Track last toast message and timestamp

    def __init__(
        self,
        namespace: str,
        context: Optional[str] = None,
        refresh_interval: int = 5,
        deployment_name: str = "haproxy-template-ic",
        socket_path: Optional[str] = None,
    ):
        super().__init__()

        self.namespace = namespace
        self.context = context
        self.refresh_interval = refresh_interval
        self.deployment_name = deployment_name
        self.socket_path = socket_path

        # Initialize dashboard service
        self.data_provider = DashboardService(
            namespace=namespace,
            context=context,
            deployment_name=deployment_name,
            socket_path=socket_path,
        )

        # Ensure TUI log handler is set up after console handlers have been removed
        # This allows logs to be captured for the debug screen without polluting the terminal

        root_logger = logging.getLogger()
        # Remove any remaining console handlers to prevent terminal pollution
        for handler in root_logger.handlers[:]:
            if isinstance(handler, logging.StreamHandler):
                if handler.stream in (sys.stderr, sys.stdout):
                    root_logger.removeHandler(handler)

        # Initialize TUI logging handler for debug screen
        get_tui_log_handler()

    def compose(self) -> ComposeResult:
        """Create the UI layout."""
        yield Header()

        with Container(id="main-container"):
            with Vertical(id="dashboard"):
                yield HeaderWidget(id="header")
                with Horizontal(id="main-content"):
                    with Vertical(id="left-panel"):
                        # Pods and templates
                        yield PodsWidget(id="pods")
                        yield TemplatesWidget(id="templates")

                    with Vertical(id="right-panel"):
                        # Resources, performance, and activity
                        yield ResourcesWidget(id="resources")
                        yield PerformanceWidget(id="performance")
                        yield ActivityWidget(id="activity")

        yield Footer()

    async def on_mount(self) -> None:
        """Initialize the dashboard on mount."""
        # Start periodic data refresh
        self.set_interval(self.refresh_interval, self.refresh_data)

        # Initial data load
        await self._initialize()

    async def _initialize(self) -> None:
        """Initialize the dashboard data."""
        try:
            self.loading = True

            # Initialize data provider
            await self.data_provider.initialize()

            # Initial data fetch
            await self.refresh_data()

            self.loading = False

        except Exception as e:
            logger.error(f"Dashboard initialization error: {e}", exc_info=True)
            self.loading = False

    async def refresh_data(self) -> None:
        """Refresh dashboard data."""
        try:
            # Set connection status to connecting
            self._set_connection_status("CONNECTING")

            # Fetch all data from the data provider
            data = await self.data_provider.fetch_all_data()

            # Store complete dashboard data
            self.dashboard_data = data

            # Update reactive properties for backwards compatibility
            self.operator_status = data.operator
            self.pods = data.pods
            self.templates = data.templates
            self.resources = data.resources
            self.performance = data.performance
            self.activity = data.activity

            # Check for error information in the data
            error_infos = data.error_infos
            if error_infos:
                # Show each error as a toast notification
                for error_info in error_infos:
                    self._show_error_toast(error_info)
                self._set_connection_status("DISCONNECTED")
            else:
                # Connection successful
                self._set_connection_status("CONNECTED")

            # Update widgets with new data
            self._update_widgets()

            # Force a full screen refresh to ensure updated widgets are displayed
            self.refresh()

            self.last_update = datetime.now(timezone.utc)

        except Exception as e:
            logger.error(f"Data refresh error: {e}", exc_info=True)
            self._set_connection_status("DISCONNECTED")

            error_info = ErrorInfo(
                type="UNEXPECTED_ERROR",
                message=f"Unexpected error: {str(e)}",
                details=str(e),
                suggestions=[
                    "Try refreshing the dashboard",
                    "Check the debug log for more information",
                    "Restart the dashboard if the problem persists",
                ],
            )
            self._show_error_toast(error_info)

    def _update_widgets(self) -> None:
        """Update widgets with current data."""
        # Update each widget with complete dashboard data
        widget_ids = [
            "#header",
            "#pods",
            "#templates",
            "#resources",
            "#performance",
            "#activity",
        ]
        widget_types = [
            HeaderWidget,
            PodsWidget,
            TemplatesWidget,
            ResourcesWidget,
            PerformanceWidget,
            ActivityWidget,
        ]

        for widget_id, widget_type in zip(widget_ids, widget_types):
            try:
                widget = self.query_one(widget_id, expect_type=widget_type)
                setattr(widget, "dashboard_data", self.dashboard_data)
            except Exception as e:
                logger.warning(
                    f"Failed to update widget {widget_id}: {e}", exc_info=True
                )
                # Continue with other widgets

    # Action handlers for key bindings
    async def action_quit(self) -> None:
        """Quit the application."""
        self.exit()

    async def action_refresh(self) -> None:
        """Force refresh data."""
        await self.refresh_data()

    async def action_help(self) -> None:
        """Show help screen."""
        if self.current_screen == "help":
            await self.action_back()
        else:
            self.push_screen("help")
            self.current_screen = "help"

    async def action_debug(self) -> None:
        """Show debug screen."""
        if self.current_screen == "debug":
            await self.action_back()
        else:
            self.push_screen("debug")
            self.current_screen = "debug"

    async def action_template_inspector(self) -> None:
        """Show template inspector screen."""
        if self.current_screen == "template_inspector":
            await self.action_back()
        else:
            # Create TemplateInspectorScreen with current data
            inspector_screen = TemplateInspectorScreen(
                data_provider=self.data_provider, templates_data=self.templates
            )
            self.push_screen(inspector_screen)
            self.current_screen = "template_inspector"

    async def action_back(self) -> None:
        """Go back to previous screen."""
        if self.current_screen != "main":
            self.pop_screen()
            self.current_screen = "main"

    def on_screen_suspend(self, screen) -> None:
        """Handle screen being suspended."""
        pass

    def on_screen_resume(self, screen) -> None:
        """Handle screen being resumed."""
        # Update current screen tracking
        if hasattr(screen, "screen_name"):
            self.current_screen = screen.screen_name
        else:
            self.current_screen = "main"

    def on_template_selected(self, message: TemplateSelected) -> None:
        """Handle template selection for inspection."""
        logger.info(f"Template selected for inspection: {message.template_name}")
        # Create TemplateInspectorScreen with the selected template
        inspector_screen = TemplateInspectorScreen(
            data_provider=self.data_provider,
            templates_data=self.templates,
            selected_template=message.template_name,
        )
        self.push_screen(inspector_screen)
        self.current_screen = "template_inspector"

    def _show_error_toast(self, error_info) -> None:
        """Show error information as toast notification."""
        try:
            error_type = error_info.type
            message = error_info.message

            # Create notification message
            toast_message = f"⚠️ {error_type}: {message}"
            current_time = time.time()

            # Check if we should skip this toast due to recent duplicate
            if self.last_error_toast_time is not None:
                last_message, last_timestamp = self.last_error_toast_time
                time_elapsed = current_time - last_timestamp

                # Skip if same message and less than 60 seconds have passed
                if last_message == toast_message and time_elapsed < SECONDS_PER_MINUTE:
                    logger.debug(
                        f"Skipping duplicate error toast: {error_type} (shown {time_elapsed:.1f}s ago)"
                    )
                    return

            # Show toast with error styling and longer duration
            self.notify(
                toast_message,
                severity="error",
                timeout=10.0,  # Show for 10 seconds
            )

            # Track this toast with current timestamp
            self.last_error_toast_time = (toast_message, current_time)

            logger.info(f"Showing error toast: {error_type} - {message}")

        except Exception as e:
            logger.error(f"Failed to show error toast: {e}", exc_info=True)
            # Fallback to basic notification
            self.notify("An error occurred", severity="error")

    def _set_connection_status(self, status: str) -> None:
        """Update connection status in header widget."""
        try:
            # Update operator status to reflect connection state
            self.operator_status = self.operator_status.model_copy(
                update={"status": status}
            )

            # Update header widget data
            header = self.query_one("#header", HeaderWidget)
            header.dashboard_data = header.dashboard_data.model_copy(
                update={"operator": self.operator_status}
            )
        except Exception as e:
            logger.warning(f"Failed to update connection status: {e}", exc_info=True)
