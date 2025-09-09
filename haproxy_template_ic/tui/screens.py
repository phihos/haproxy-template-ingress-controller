"""
Textual screens for the TUI dashboard.

Contains screen definitions for Main, Help, Debug, and TemplateInspector views.
"""

import logging
from collections import deque
from typing import Optional, Dict, Any, Deque

from textual import on
from textual.app import ComposeResult
from textual.containers import Container, Vertical
from textual.screen import Screen
from textual.widgets import Log, Markdown, Select, Static

from haproxy_template_ic.constants import TUI_LOG_BUFFER_SIZE, LOG_SEPARATOR_WIDTH
from .widgets.inspector import TemplateInspectorWidget, TemplateContentChanged

logger = logging.getLogger(__name__)

__all__ = ["HelpScreen", "DebugScreen", "TemplateInspectorScreen", "TuiLogHandler"]


class TuiLogHandler(logging.Handler):
    """Custom logging handler that captures logs for the TUI debug screen."""

    def __init__(self) -> None:
        super().__init__()
        self.logs: Deque[str] = deque(
            maxlen=TUI_LOG_BUFFER_SIZE
        )  # Keep last N log entries
        self.log_records: Deque[logging.LogRecord] = deque(
            maxlen=TUI_LOG_BUFFER_SIZE
        )  # Keep raw log records for filtering
        self.debug_screen: Optional["DebugScreen"] = None
        self.min_log_level = logging.INFO  # Default to INFO level

        # Set up formatting
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s", datefmt="%H:%M:%S"
        )
        self.setFormatter(formatter)

    def emit(self, record: logging.LogRecord) -> None:
        """Emit a log record."""
        try:
            formatted_message = self.format(record)

            # Add smart stack trace for errors (not warnings)
            if record.levelno >= logging.ERROR:
                if record.exc_info:
                    # Format the exception traceback with filtering
                    stack_trace = self._format_filtered_traceback(record)
                    if stack_trace:
                        formatted_message += f"\n{stack_trace}"
                elif self._should_add_stack_trace(record):
                    # For errors without exc_info, add filtered current stack trace
                    stack_trace = self._get_filtered_stack_trace()
                    if stack_trace:
                        formatted_message += f"\n{stack_trace}"

            # Store both formatted message and raw record
            self.logs.append(formatted_message)
            self.log_records.append(record)

            # If debug screen is active, write to it (respect current filter level)
            if self.debug_screen and record.levelno >= self.min_log_level:
                self.debug_screen.add_log_line(formatted_message)

        except Exception as e:
            # Don't let logging errors break the application
            logger.debug(f"Log handler error (suppressed): {e}")

    def set_debug_screen(self, debug_screen: Optional["DebugScreen"]) -> None:
        """Set the active debug screen."""
        self.debug_screen = debug_screen

    def get_recent_logs(self, count: int = 100) -> list:
        """Get recent log entries."""
        return list(self.logs)[-count:]

    def get_filtered_logs(self, count: int = 100, min_level: int = None) -> list:
        """Get recent log entries filtered by minimum log level."""
        if min_level is None:
            min_level = self.min_log_level

        filtered_logs = []
        # Go through both logs and records in reverse order (most recent first)
        for log_msg, record in zip(reversed(self.logs), reversed(self.log_records)):
            if record.levelno >= min_level:
                filtered_logs.append(log_msg)
                if len(filtered_logs) >= count:
                    break

        # Reverse to get chronological order (oldest first)
        return list(reversed(filtered_logs))

    def set_min_log_level(self, level: int) -> None:
        """Set the minimum log level for filtering."""
        self.min_log_level = level

        # If debug screen is active, refresh its display
        if self.debug_screen:
            self.debug_screen.refresh_log_display()

    def _should_add_stack_trace(self, record: logging.LogRecord) -> bool:
        """Determine if we should add a stack trace for this error."""
        message = record.getMessage()

        # Skip stack traces for expected/network errors and operational messages
        expected_errors = [
            "Failed to execute socket command",
            "All connection attempts failed",
            "Connection refused",
            "Timeout",
            "DNS resolution failed",
            "No route to host",
            "Showing error toast",
            "No HAProxy pods found",
            "NO_RESOURCES",
            "DISCONNECTED",
            "CONNECTION_ERROR",
        ]

        return not any(expected in message for expected in expected_errors)

    def _get_filtered_stack_trace(self) -> str:
        """Get a filtered and compacted stack trace."""
        import traceback

        # Get current stack
        stack = traceback.format_stack()[:-1]  # Exclude current frame

        # Filter to relevant frames only
        filtered_frames = []
        project_root = "haproxy_template_ic"

        for frame in stack:
            # Keep frames from our project
            if project_root in frame:
                # Clean up the frame format
                lines = frame.strip().split("\n")
                if len(lines) >= 2:
                    file_line = lines[0].strip()
                    code_line = lines[1].strip()

                    # Shorten file paths
                    if project_root in file_line:
                        start_idx = file_line.find(project_root)
                        file_line = file_line[start_idx:]

                    filtered_frames.append(f"  {file_line} -> {code_line}")

        # Limit to last 5 frames to avoid overwhelming output
        if len(filtered_frames) > 5:
            filtered_frames = ["  ... (frames omitted)"] + filtered_frames[-4:]

        if filtered_frames:
            return "Stack (project code only):\n{}".format("\n".join(filtered_frames))

        return ""

    def _format_filtered_traceback(self, record: logging.LogRecord) -> str:
        """Format exception traceback with filtering and compact display."""
        import traceback

        if not record.exc_info:
            return ""

        # Get the full traceback
        tb_lines = traceback.format_exception(*record.exc_info)

        # Find relevant frames
        filtered_lines = []
        project_root = "haproxy_template_ic"

        for i, line in enumerate(tb_lines):
            # Keep exception message (last line)
            if i == len(tb_lines) - 1:
                filtered_lines.append(f"Exception: {line.strip()}")
            # Keep frames from our project
            elif project_root in line and "File " in line:
                # Next line should be the code
                if i + 1 < len(tb_lines):
                    file_line = line.strip()
                    code_line = tb_lines[i + 1].strip()

                    # Shorten file paths
                    if project_root in file_line:
                        start_idx = file_line.find(project_root)
                        file_line = file_line[start_idx:]

                    filtered_lines.append(f"  {file_line} -> {code_line}")

        # Limit frames
        if len(filtered_lines) > 6:  # 5 frames + exception
            exception_line = filtered_lines[-1]
            filtered_lines = (
                ["  ... (frames omitted)"] + filtered_lines[-5:-1] + [exception_line]
            )

        if len(filtered_lines) > 1:  # More than just exception
            return "Traceback (project code only):\n{}".format(
                "\n".join(filtered_lines)
            )
        elif filtered_lines:  # Just exception
            return filtered_lines[0]

        return ""


# Global log handler instance
_tui_log_handler: Optional[TuiLogHandler] = None


def get_tui_log_handler() -> TuiLogHandler:
    """Get or create the global TUI log handler."""
    global _tui_log_handler
    if _tui_log_handler is None:
        _tui_log_handler = TuiLogHandler()
        # Add to root logger to capture all logs
        root_logger = logging.getLogger()
        root_logger.addHandler(_tui_log_handler)
        # Set root logger level to DEBUG so all logs reach the handler
        root_logger.setLevel(logging.DEBUG)
        # Set handler level to capture DEBUG and above
        _tui_log_handler.setLevel(logging.DEBUG)
    return _tui_log_handler


class HelpScreen(Screen):
    """Help screen with keyboard shortcuts and usage information."""

    screen_name = "help"

    def compose(self) -> ComposeResult:
        """Create the help screen layout."""
        help_text = """
# HAProxy Template IC Dashboard Help

## Keyboard Commands

- **q** - Quit dashboard
- **r** - Force refresh data
- **h** - Toggle this help screen
- **d** - Toggle debug log overlay
- **t** - Toggle template inspector
- **ESC** - Back to main screen
- **Ctrl+C** - Emergency exit

## Template Inspector

- **↑/↓** - Navigate template list
- **Enter** - Inspect selected template
- **Tab** - Switch view modes (template/rendered/split)
- **ESC** - Back to list or main screen

## Dashboard Features

- Auto-refresh every 5 seconds
- Live HAProxy pod monitoring
- Template and resource tracking
- Template inspection with syntax highlighting
- Performance metrics (when available)
- Real-time activity feed

## Navigation

Use the keyboard shortcuts above to navigate between different views.
The dashboard automatically updates data every few seconds.

Press **ESC** or **h** to return to the main dashboard.
        """

        yield Markdown(help_text, id="help-content")


class DebugScreen(Screen):
    """Debug screen showing application logs."""

    screen_name = "debug"

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self.log_widget: Optional[Log] = None
        self.log_level_select: Optional[Select] = None
        self.current_log_level = (
            logging.INFO
        )  # Store current log level for state preservation

        # Log level options with display name and logging constant
        self.log_level_options = [
            ("DEBUG", logging.DEBUG),
            ("INFO", logging.INFO),
            ("WARNING", logging.WARNING),
            ("ERROR", logging.ERROR),
        ]

    def compose(self) -> ComposeResult:
        """Create the debug screen layout."""
        with Container(id="debug-container"):
            # Header with log level selector
            yield Static("Debug Log Viewer - Live Application Logs", id="debug-header")
            with Vertical(id="debug-content"):
                yield Static("Min Level:", classes="debug-label")
                yield Select(
                    options=self.log_level_options,
                    value=self.current_log_level,
                    id="log-level-select",
                )
                yield Log(id="debug-log", auto_scroll=True)

    def on_mount(self) -> None:
        """Initialize debug screen."""
        self.log_widget = self.query_one("#debug-log", Log)
        self.log_level_select = self.query_one("#log-level-select", Select)

        # Register with the log handler
        handler = get_tui_log_handler()
        handler.set_debug_screen(self)

        # Set initial filter level to current level
        handler.set_min_log_level(self.current_log_level)

        # Ensure the Select widget shows the correct value
        self.log_level_select.value = self.current_log_level

        # Load initial display
        self.refresh_log_display()

    def refresh_log_display(self) -> None:
        """Refresh the log display with current filter settings."""
        handler = get_tui_log_handler()

        # Clear the log widget
        if not self.log_widget:
            return

        # At this point log_widget is guaranteed to be not None
        self.log_widget.clear()

        # Show header info
        level_name = logging.getLevelName(handler.min_log_level)
        self.log_widget.write_line(f"🔍 Debug Log Viewer - Showing {level_name}+ logs")
        self.log_widget.write_line("─" * LOG_SEPARATOR_WIDTH)

        # Load filtered recent logs
        recent_logs = handler.get_filtered_logs(
            500
        )  # Show last 500 filtered logs for better context
        if recent_logs:
            self.log_widget.write_line("📋 Recent log entries:")
            for log_line in recent_logs:
                self.log_widget.write_line(log_line)
        else:
            self.log_widget.write_line(
                f"ℹ️  No recent {level_name}+ log entries available"
            )

        self.log_widget.write_line("─" * LOG_SEPARATOR_WIDTH)
        self.log_widget.write_line("📡 Live logs will appear below:")

    @on(Select.Changed, "#log-level-select")
    def on_log_level_changed(self, event: Select.Changed) -> None:
        """Handle log level selection change."""
        if event.value != Select.BLANK and isinstance(event.value, int):
            # Save the current log level
            self.current_log_level = event.value
            handler = get_tui_log_handler()
            handler.set_min_log_level(event.value)
            # refresh_log_display is called automatically by set_min_log_level

    def on_screen_suspend(self) -> None:
        """Called when screen is being suspended."""
        # Save current log level before suspension
        handler = get_tui_log_handler()
        self.current_log_level = handler.min_log_level
        # Unregister from log handler
        handler.set_debug_screen(None)

    def on_screen_resume(self, screen) -> None:
        """Called when screen is resumed - re-establish connections."""
        # Re-register with the log handler
        handler = get_tui_log_handler()
        handler.set_debug_screen(self)

        # Restore the log level and update the select widget
        handler.set_min_log_level(self.current_log_level)
        if self.log_level_select:
            self.log_level_select.value = self.current_log_level

        # Refresh the display with current settings
        self.refresh_log_display()

    def add_log_line(self, log_line: str) -> None:
        """Add a log line to the debug screen (called by log handler)."""
        if self.log_widget:
            try:
                self.log_widget.write_line(log_line)
            except Exception as e:
                # Don't let logging errors break the screen
                logger.debug(f"Log widget write error (suppressed): {e}")


class TemplateInspectorScreen(Screen):
    """Template inspector screen for viewing template content with syntax highlighting."""

    screen_name = "template_inspector"

    def __init__(
        self,
        data_provider: Any = None,
        templates_data: Optional[Dict[str, Any]] = None,
        selected_template: Optional[str] = None,
        **kwargs: Any,
    ) -> None:
        super().__init__(**kwargs)
        self.data_provider = data_provider
        self.templates_data = templates_data or {}
        self.selected_template = selected_template

    def compose(self) -> ComposeResult:
        """Create the template inspector layout."""
        with Container(id="inspector-container"):
            yield Static(
                "🔍 Template Inspector", id="inspector-header", classes="header"
            )
            yield TemplateInspectorWidget(id="template-inspector")

    def on_mount(self) -> None:
        """Initialize template inspector with current templates data."""
        try:
            inspector = self.query_one("#template-inspector", TemplateInspectorWidget)

            # Set templates data if available
            if self.templates_data:
                inspector.templates_data = self.templates_data

            # Pre-select template if specified
            if self.selected_template:
                inspector.selected_template = self.selected_template
                # Schedule async content loading after mount is complete
                self.call_after_refresh(self._load_selected_template_content)

        except Exception as e:
            logger.error(f"Error initializing template inspector: {e}", exc_info=True)

    async def _load_selected_template_content(self) -> None:
        """Load content for the pre-selected template."""
        if self.selected_template:
            await self._load_template_content(self.selected_template)

    async def on_template_content_changed(
        self, message: TemplateContentChanged
    ) -> None:
        """Handle template content change requests."""
        await self._load_template_content(message.template_name)

    async def _load_template_content(self, template_name: str) -> None:
        """Load template content from the data provider."""
        logger.debug(f"Loading template content for: {template_name}")

        if not self.data_provider:
            logger.warning("No data provider available for template content")
            return

        try:
            # Show loading state
            inspector = self.query_one("#template-inspector", TemplateInspectorWidget)
            logger.debug("Found inspector widget, fetching content...")

            # Fetch template content
            content = await self.data_provider.get_template_content(template_name)
            logger.debug(
                f"Content fetched: {content is not None}, keys: {list(content.keys()) if content else None}"
            )

            if content:
                logger.debug("Setting template content on inspector widget")
                inspector.set_template_content(content)
                logger.debug("Template content set successfully")
            else:
                # Show error state
                error_content = {
                    "template_name": template_name,
                    "source": None,
                    "rendered": None,
                    "type": "unknown",
                    "errors": ["Failed to fetch template content"],
                }
                inspector.set_template_content(error_content)

        except Exception as e:
            logger.error(
                f"Error loading template content for {template_name}: {e}",
                exc_info=True,
            )

            # Show error in inspector
            try:
                inspector = self.query_one(
                    "#template-inspector", TemplateInspectorWidget
                )
                error_content = {
                    "template_name": template_name,
                    "source": None,
                    "rendered": None,
                    "type": "unknown",
                    "errors": [f"Error loading template: {e}"],
                }
                inspector.set_template_content(error_content)
            except Exception as e:
                logger.debug(f"Template content setting error (suppressed): {e}")

    def update_templates_data(self, templates_data: Dict[str, Any]) -> None:
        """Update the templates data in the inspector."""
        self.templates_data = templates_data
        try:
            inspector = self.query_one("#template-inspector", TemplateInspectorWidget)
            inspector.templates_data = templates_data
        except Exception as e:
            logger.debug(f"Error updating templates data in inspector: {e}")

    def set_data_provider(self, data_provider) -> None:
        """Set the data provider for fetching template content."""
        self.data_provider = data_provider
