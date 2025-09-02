"""
Main dashboard launcher with Rich UI integration.

Handles the main dashboard loop, user input, and coordinates all components.
"""

import asyncio
import logging
import signal
import sys
import time
from collections import deque
from datetime import datetime, timezone
from typing import Any, Dict, Optional, Deque

from prompt_toolkit.input import create_input
from prompt_toolkit.keys import Keys
from rich.console import Console
from rich.layout import Layout
from rich.live import Live
from rich.panel import Panel
from rich.text import Text

from .compatibility import CompatibilityLevel
from .data_fetcher import DashboardDataFetcher
from .template_inspector import TemplateInspectorPanel
from .ui_panels import (
    ActivityPanel,
    HeaderPanel,
    PerformancePanel,
    PodsPanel,
    ResourcesPanel,
    TemplatesPanel,
)

logger = logging.getLogger(__name__)

__all__ = ["DashboardLauncher"]


class DashboardLauncher:
    """Main dashboard application launcher."""

    def __init__(
        self,
        namespace: str,
        context: Optional[str] = None,
        refresh_interval: int = 5,
        deployment_name: str = "haproxy-template-ic",
    ):
        self.namespace = namespace
        self.context = context
        self.refresh_interval = refresh_interval
        self.deployment_name = deployment_name

        self.console = Console()
        self.data_fetcher = DashboardDataFetcher(
            namespace=namespace, context=context, deployment_name=deployment_name
        )

        # UI components
        self.header_panel = HeaderPanel()
        self.pods_panel = PodsPanel()
        self.templates_panel = TemplatesPanel()
        self.resources_panel = ResourcesPanel()
        self.performance_panel = PerformancePanel()
        self.activity_panel = ActivityPanel()
        self.template_inspector = TemplateInspectorPanel(self.console)

        # State
        self.compatibility_level = CompatibilityLevel.BASIC
        self.running = False
        self.last_update: Optional[datetime] = None
        self.manual_refresh = False
        self.show_help = False
        self.show_debug = False

        # Template inspection state
        self.show_template_inspector = False
        self.template_inspector_mode = "list"  # "list", "inspect"
        self.current_template_data: Optional[Dict[str, Any]] = None

        # Loading state
        self.loading = True
        self.loading_message = "Initializing dashboard..."
        self.has_error = False
        self.error_message = ""

        # Debug overlay scroll state
        self.debug_scroll_position = 0
        self.debug_logs_per_page = 20
        self.debug_total_logs = 0

        # Scroll acceleration and debouncing
        self.last_scroll_time: float = 0.0
        self.scroll_velocity: int = 0
        self.active_scrolling = False

        # Keyboard input handling
        self.key_queue: asyncio.Queue[str] = asyncio.Queue()
        self.input_handler = None  # prompt-toolkit input handler
        self.input_thread = None  # Thread for input handling
        self._stop_input = False  # Flag to stop input thread
        self.previous_help_state = False
        self.previous_debug_state = False
        self.previous_template_inspector_state = False
        self.previous_loading_state = True  # Track loading state changes
        self._event_loop = None

        # Debug logging infrastructure
        self.debug_logs: Deque[Dict[str, Any]] = deque(maxlen=200)
        self._setup_debug_logging()

        # Set up signal handler for clean exit
        signal.signal(signal.SIGINT, self._signal_handler)

    def _setup_debug_logging(self):
        """Set up debug logging handler to capture logs."""

        class DebugLogHandler(logging.Handler):
            def __init__(self, launcher):
                super().__init__()
                self.launcher = launcher
                self.setLevel(logging.DEBUG)

            def emit(self, record):
                # Only capture dashboard-related logs
                if (
                    "dashboard" in record.name.lower()
                    or "haproxy_template_ic.dashboard" in record.name
                ):
                    try:
                        timestamp = datetime.now(timezone.utc)
                        self.launcher.debug_logs.append(
                            {
                                "timestamp": timestamp,
                                "level": record.levelname,
                                "logger": record.name.split(".")[
                                    -1
                                ],  # Just the module name
                                "message": record.getMessage(),
                            }
                        )
                    except Exception as e:
                        # Don't let logging errors crash the dashboard
                        logger.debug(f"Non-critical error in debug log handler: {e}")

        # Set up logging configuration to ensure DEBUG logs are captured
        root_logger = logging.getLogger()

        # Store original handlers for restoration later
        self.original_handlers = root_logger.handlers.copy()

        # Remove all StreamHandlers to prevent console output conflicts with Rich
        for handler in root_logger.handlers[
            :
        ]:  # Use slice copy to avoid modification during iteration
            if isinstance(handler, logging.StreamHandler):
                root_logger.removeHandler(handler)

        # Add our debug handler
        self.debug_handler = DebugLogHandler(self)
        root_logger.addHandler(self.debug_handler)

        # Ensure root logger level allows DEBUG messages
        if root_logger.level > logging.DEBUG:
            root_logger.setLevel(logging.DEBUG)

        # Explicitly set dashboard loggers to DEBUG level
        dashboard_loggers = [
            "haproxy_template_ic.dashboard",
            "haproxy_template_ic.dashboard.data_fetcher",
            "haproxy_template_ic.dashboard.compatibility",
            "haproxy_template_ic.dashboard.launcher",
            "haproxy_template_ic.dashboard.ui_panels",
        ]

        for logger_name in dashboard_loggers:
            logger_obj = logging.getLogger(logger_name)
            logger_obj.setLevel(logging.DEBUG)

        # Test that debug logging is working
        logger.debug("Debug log handler initialized successfully")

    def _cleanup_debug_logging(self):
        """Clean up debug logging and restore original handlers."""
        root_logger = logging.getLogger()

        # Remove our debug handler
        if (
            hasattr(self, "debug_handler")
            and self.debug_handler in root_logger.handlers
        ):
            root_logger.removeHandler(self.debug_handler)

        # Restore original handlers
        if hasattr(self, "original_handlers"):
            # Clear current handlers and restore originals
            root_logger.handlers.clear()
            for handler in self.original_handlers:
                root_logger.addHandler(handler)

    def _signal_handler(self, signum, frame):
        """Handle signals for clean exit."""
        self.running = False

    async def launch(self) -> None:
        """Launch the dashboard application."""
        try:
            # Start the dashboard immediately with loading state
            self.running = True

            # Start initialization in background (fire and forget)
            initialization_task = asyncio.create_task(self._initialize())

            # Run the dashboard (this will block until user quits or error occurs)
            await self._run_dashboard()

            # Dashboard has exited, cancel initialization if still running
            if not initialization_task.done():
                initialization_task.cancel()
                try:
                    await initialization_task
                except asyncio.CancelledError:
                    pass

        except KeyboardInterrupt:
            self.console.print("\n[yellow]Dashboard stopped by user[/yellow]")
        except Exception as e:
            logger.error(f"Dashboard error: {e}")
            import traceback

            traceback.print_exc()
            self.console.print(f"[red]Dashboard error: {e}[/red]")
            self.console.print(
                "[red]Please check your configuration and try again.[/red]"
            )
        finally:
            self.running = False
            # Clean up debug logging handler and restore original handlers
            self._cleanup_debug_logging()

    async def _initialize(self) -> None:
        """Initialize dashboard data in background while UI is shown."""
        try:
            self.loading_message = "Checking prerequisites..."

            # Pre-flight checks
            if not await self._verify_prerequisites():
                self.has_error = True
                # Keep loading=True so we show the error in the loading panel
                # Don't set running=False to keep dashboard UI active
                return

            self.loading_message = "Initializing data fetcher..."

            # Initialize data fetcher and check compatibility
            self.compatibility_level = await self.data_fetcher.initialize()

            # Initialization complete
            self.loading = False

        except Exception as e:
            logger.error(f"Initialization error: {e}")
            self.has_error = True
            self.error_message = f"Initialization failed: {e}"
            # Keep loading=True so we show the error in the loading panel
            # Don't set running=False to keep dashboard UI active

    async def _verify_prerequisites(self) -> bool:
        """Verify that required tools and connectivity are available."""
        # Import kr8s here to avoid circular imports
        from kr8s.objects import Deployment

        # Check cluster connectivity and deployment existence with kr8s
        try:
            # Check if operator deployment exists (this also verifies cluster connectivity)
            deployment = await Deployment.get(
                self.deployment_name, namespace=self.namespace
            )
            if deployment is None:
                self.error_message = f"Operator deployment '{self.deployment_name}' not found in namespace '{self.namespace}'"
                return False
        except Exception as e:
            # This could be a connectivity issue or deployment not found
            error_str = str(e).lower()
            if "not found" in error_str or "404" in error_str:
                self.error_message = f"Operator deployment '{self.deployment_name}' not found in namespace '{self.namespace}'"
            else:
                self.error_message = f"Cannot connect to Kubernetes cluster: {e}"
            return False

        return True

    def _show_compatibility_info(self) -> None:
        """Show compatibility information to user."""
        if self.compatibility_level == CompatibilityLevel.FULL:
            self.console.print(
                "[green]✅ Full dashboard functionality available[/green]"
            )
        elif self.compatibility_level == CompatibilityLevel.ENHANCED:
            self.console.print(
                "[yellow]⚡ Enhanced dashboard mode (some features available)[/yellow]"
            )
        elif self.compatibility_level == CompatibilityLevel.BASIC:
            self.console.print(
                "[yellow]📊 Basic dashboard mode (limited features)[/yellow]"
            )
            self.console.print(
                "[dim]   Upgrade operator to get performance metrics and activity feed[/dim]"
            )
        else:  # LEGACY
            self.console.print("[red]⚠️  Legacy mode (minimal functionality)[/red]")
            self.console.print(
                "[dim]   Consider upgrading the operator for better dashboard experience[/dim]"
            )

        self.console.print()

        # Show keyboard instructions
        self.console.print(
            "[dim]Press 'q' to quit, 'r' to refresh, 'h' for help, or Ctrl+C to exit[/dim]"
        )
        self.console.print()

    def _setup_keyboard_input(self):
        """Set up async keyboard input handling with prompt-toolkit."""
        try:
            if not sys.stdin.isatty():
                logger.info("No TTY available, keyboard input disabled")
                return False

            self.input = create_input()

            def keys_ready():
                """Handle keyboard input when available."""
                try:
                    for key_press in self.input.read_keys():
                        # Map prompt-toolkit keys to our key names
                        key_name = None
                        if key_press.key == Keys.Up:
                            key_name = "UP"
                        elif key_press.key == Keys.Down:
                            key_name = "DOWN"
                        elif key_press.key == Keys.Left:
                            key_name = "LEFT"
                        elif key_press.key == Keys.Right:
                            key_name = "RIGHT"
                        elif key_press.key == Keys.PageUp:
                            key_name = "PAGEUP"
                        elif key_press.key == Keys.PageDown:
                            key_name = "PAGEDOWN"
                        elif key_press.key == Keys.Home:
                            key_name = "HOME"
                        elif key_press.key == Keys.End:
                            key_name = "END"
                        elif key_press.key == Keys.Escape:
                            key_name = "\x1b"
                        elif (
                            key_press.key == Keys.Enter
                            or key_press.key == Keys.ControlM
                        ):
                            key_name = "\r"
                        elif (
                            key_press.key == Keys.Tab or key_press.key == Keys.ControlI
                        ):
                            key_name = "\t"
                        elif (
                            hasattr(key_press.key, "value")
                            and len(key_press.key.value) == 1
                        ):
                            # Single character keys
                            key_name = key_press.key.value
                        elif isinstance(key_press.key, str) and len(key_press.key) == 1:
                            # String character keys
                            key_name = key_press.key

                        if key_name:
                            # Queue the key asynchronously
                            asyncio.create_task(self.key_queue.put(key_name))
                except Exception as e:
                    logger.error(f"[INPUT] Error processing keys: {e}")

            # Set up the input handler in raw mode
            self.input_context = self.input.raw_mode()
            self.input_context.__enter__()

            self.input_reader_context = self.input.attach(keys_ready)
            self.input_reader_context.__enter__()

            logger.info("Keyboard input handler set up successfully")
            return True

        except Exception as e:
            logger.error(f"Error setting up keyboard input: {e}")
            return False

    def _cleanup_keyboard_input(self):
        """Clean up keyboard input resources."""
        try:
            if hasattr(self, "input_reader_context"):
                self.input_reader_context.__exit__(None, None, None)
            if hasattr(self, "input_context"):
                self.input_context.__exit__(None, None, None)
            logger.debug("Keyboard input cleaned up")
        except Exception as e:
            logger.error(f"Error cleaning up keyboard input: {e}")

    async def _run_dashboard(self) -> None:
        """Run the main dashboard loop with Rich Live."""
        try:
            # Clear screen for clean dashboard display
            self.console.clear()

            # Set up keyboard input with prompt-toolkit
            keyboard_enabled = self._setup_keyboard_input()
            layout = self._create_layout()

            try:
                with (
                    Live(
                        layout,
                        console=self.console,
                        refresh_per_second=2,  # Slightly faster refresh for better responsiveness
                        screen=True,
                        transient=False,  # Keep output after exit for debugging
                    ) as live
                ):
                    last_refresh = 0.0
                    loop_count = 0
                    max_loops_without_tty = 50  # For non-TTY environments, limit loops

                    while self.running:
                        try:
                            # Check for keyboard input from queue (only if keyboard enabled)
                            if keyboard_enabled:
                                # Process keys directly without debouncing
                                try:
                                    key = self.key_queue.get_nowait()
                                    if key:
                                        # Handle debug navigation keys directly
                                        navigation_keys = {
                                            "UP",
                                            "DOWN",
                                            "PAGEUP",
                                            "PAGEDOWN",
                                            "HOME",
                                            "END",
                                            "LEFT",
                                            "RIGHT",
                                        }
                                        is_navigation = key in navigation_keys

                                        if self.show_debug and is_navigation:
                                            nav_result = self._handle_debug_navigation(
                                                key
                                            )

                                            if nav_result:
                                                # Debug navigation handled, refresh the display
                                                self.manual_refresh = True
                                        # Handle template inspector navigation
                                        elif (
                                            self.show_template_inspector
                                            and await self._handle_template_inspector_navigation(
                                                key,
                                                getattr(
                                                    self, "_last_dashboard_data", None
                                                ),
                                            )
                                        ):
                                            # Template inspector navigation handled, refresh the display
                                            self.manual_refresh = True
                                        # Handle special keys that don't have .lower() method
                                        elif key in ("q", "\x03"):  # 'q' or Ctrl+C
                                            self.running = False
                                            break
                                        # Handle single character keys (safe to call .lower())
                                        elif len(key) == 1:
                                            if key.lower() == "r":  # Force refresh
                                                self.manual_refresh = True
                                            elif key.lower() == "h":  # Toggle help
                                                self.show_help = not self.show_help
                                                self.manual_refresh = True
                                            elif key.lower() == "d":  # Toggle debug
                                                if self.show_debug:
                                                    # Reset scroll position and velocity when closing debug
                                                    self.debug_scroll_position = 0
                                                    self.scroll_velocity = 0
                                                    self.active_scrolling = False
                                                self.show_debug = not self.show_debug
                                                self.manual_refresh = True
                                            elif (
                                                key.lower() == "t"
                                            ):  # Toggle template inspector
                                                self.show_template_inspector = (
                                                    not self.show_template_inspector
                                                )
                                                if self.show_template_inspector:
                                                    # Reset to template list mode
                                                    self.template_inspector_mode = (
                                                        "list"
                                                    )
                                                    self.template_inspector.reset_state()
                                                else:
                                                    # Clear template data when closing
                                                    self.current_template_data = None
                                                self.manual_refresh = True
                                except asyncio.QueueEmpty:
                                    # No key pressed, continue
                                    pass
                            else:
                                # No stdin reader, auto-exit after some loops to prevent hanging
                                loop_count += 1
                                if loop_count > max_loops_without_tty:
                                    logger.info(
                                        "Dashboard running in non-interactive mode, exiting after displaying data"
                                    )
                                    break

                            # Check if it's time to refresh or if layout needs to change
                            current_time = asyncio.get_event_loop().time()
                            time_based_refresh = (
                                current_time - last_refresh >= self.refresh_interval
                            )
                            needs_refresh = time_based_refresh or self.manual_refresh

                            help_state_changed = (
                                self.show_help != self.previous_help_state
                            )
                            debug_state_changed = (
                                self.show_debug != self.previous_debug_state
                            )
                            template_inspector_state_changed = (
                                self.show_template_inspector
                                != self.previous_template_inspector_state
                            )
                            loading_state_changed = (
                                self.loading != self.previous_loading_state
                            )

                            if (
                                needs_refresh
                                or help_state_changed
                                or debug_state_changed
                                or template_inspector_state_changed
                                or loading_state_changed
                            ):
                                # Handle layout updates efficiently
                                if (
                                    help_state_changed
                                    or debug_state_changed
                                    or template_inspector_state_changed
                                    or loading_state_changed
                                ):
                                    # State change - recreate entire layout
                                    new_layout = self._create_layout()
                                    live.update(new_layout)
                                    layout = new_layout
                                    self.previous_help_state = self.show_help
                                    self.previous_debug_state = self.show_debug
                                    self.previous_template_inspector_state = (
                                        self.show_template_inspector
                                    )
                                    self.previous_loading_state = self.loading
                                elif needs_refresh and self.show_debug:
                                    # Only debug panel visible and needs refresh - update the live display
                                    live.update(self._create_debug_panel())
                                elif needs_refresh and self.show_template_inspector:
                                    # Only template inspector visible and needs refresh - update the live display
                                    live.update(self._create_template_inspector_panel())

                                # Fetch and update data if not showing overlays and refresh is needed
                                if (
                                    needs_refresh
                                    and not self.show_help
                                    and not self.show_debug
                                    and not self.show_template_inspector
                                ):
                                    logger.debug(
                                        "Starting dashboard data refresh cycle"
                                    )
                                    try:
                                        data = await self.data_fetcher.fetch_all_data()
                                        self.last_update = datetime.now()
                                        logger.debug(
                                            "Dashboard data refresh completed, updating UI"
                                        )
                                        self._update_layout(layout, data)
                                    except Exception as e:
                                        logger.error(f"Data fetch error: {e}")
                                        # Show error in dashboard but don't exit
                                        self.has_error = True
                                        self.error_message = f"Data fetch failed: {e}"
                                elif (
                                    needs_refresh or debug_state_changed
                                ) and self.show_debug:
                                    # Refresh debug panel content even without fetching new data
                                    if debug_state_changed:
                                        pass  # Layout already updated above

                                # Reset refresh timing and flags
                                if needs_refresh:
                                    last_refresh = current_time
                                    self.manual_refresh = False

                            # Variable sleep to prevent busy waiting - shorter during active scrolling
                            if self.active_scrolling:
                                # Check if we're still actively scrolling based on time
                                if time.time() - self.last_scroll_time > 0.3:
                                    self.active_scrolling = False
                                    self.scroll_velocity = 0
                                    # Use normal sleep when no longer actively scrolling
                                    await asyncio.sleep(0.05)
                                else:
                                    # Very short sleep during active scrolling for responsiveness
                                    # Remove continue to allow refresh logic to run
                                    await asyncio.sleep(0.01)
                            else:
                                # Normal sleep when not actively scrolling
                                await asyncio.sleep(0.05)

                        except KeyboardInterrupt:
                            self.running = False
                            break
                        except Exception as e:
                            logger.error(f"Dashboard loop error: {e}")
                            # Don't exit on individual loop errors, just log and continue
                            await asyncio.sleep(0.5)
            finally:
                # Clean up keyboard input
                self._cleanup_keyboard_input()
        except Exception as e:
            logger.error(f"Dashboard setup error: {e}")
            import traceback

            traceback.print_exc()
            self.console.print(f"[red]Dashboard setup failed: {e}[/red]")
            raise

    def _create_help_panel(self) -> Panel:
        """Create help panel as a layout overlay."""
        help_text = Text()
        help_text.append("Dashboard Help\n\n", style="bold cyan")
        help_text.append("Keyboard Commands:\n", style="bold white")
        help_text.append("  q, Q - Quit dashboard\n", style="white")
        help_text.append("  r, R - Force refresh data\n", style="white")
        help_text.append("  h, H - Toggle this help\n", style="white")
        help_text.append("  d, D - Toggle debug log overlay\n", style="white")
        help_text.append("  t, T - Toggle template inspector\n", style="white")
        help_text.append("  Ctrl+C - Emergency exit\n", style="white")
        help_text.append("\nTemplate Inspector:\n", style="bold white")
        help_text.append("  ↑↓ - Navigate template list\n", style="white")
        help_text.append("  Enter - Inspect selected template\n", style="white")
        help_text.append(
            "  Tab - Switch view modes (template/rendered/split)\n", style="white"
        )
        help_text.append("  ESC - Back to list or exit inspector\n", style="white")
        help_text.append("\nDashboard Features:\n", style="bold white")
        help_text.append("  • Auto-refresh every 5 seconds\n", style="dim")
        help_text.append("  • Live HAProxy pod monitoring\n", style="dim")
        help_text.append("  • Template and resource tracking\n", style="dim")
        help_text.append(
            "  • Template inspection with syntax highlighting\n", style="dim"
        )
        help_text.append("  • Performance metrics (when available)\n", style="dim")
        help_text.append(
            "\nPress 'h' again to return to dashboard", style="bold yellow"
        )

        return Panel(
            help_text,
            title="🔧 HAProxy Template IC - Dashboard Help",
            border_style="cyan",
            padding=(1, 2),
        )

    def _create_loading_panel(self) -> Panel:
        """Create loading panel as a layout overlay."""
        loading_text = Text()
        loading_text.append("HAProxy Template IC Dashboard\n\n", style="bold cyan")

        if self.has_error:
            # Show error state
            loading_text.append("❌ ", style="bold red")
            loading_text.append("Initialization Failed\n\n", style="bold red")
            loading_text.append(f"{self.error_message}\n\n", style="white")
            loading_text.append(
                "Please check your configuration and try again.\n", style="dim"
            )
            loading_text.append("Press 'q' to exit", style="bold yellow")

            return Panel(
                loading_text,
                title="⚠️  Dashboard Error",
                border_style="red",
                padding=(2, 4),
            )
        else:
            # Show loading state
            loading_text.append("🔄 ", style="bold yellow")
            loading_text.append(f"{self.loading_message}\n\n", style="white")
            loading_text.append(
                "Please wait while the dashboard initializes...\n", style="dim"
            )
            loading_text.append("Press 'q' to cancel", style="bold yellow")

            return Panel(
                loading_text,
                title="🚀 Dashboard Starting",
                border_style="yellow",
                padding=(2, 4),
            )

    def _handle_debug_navigation(self, key: str) -> bool:
        """Handle navigation keys when debug overlay is active with acceleration.

        Returns:
            True if the key was handled, False otherwise
        """
        old_position = self.debug_scroll_position

        current_time = time.time()

        # Calculate scroll acceleration based on key repeat timing
        time_since_last_scroll = current_time - self.last_scroll_time
        if time_since_last_scroll < 0.15:  # Fast repeated keys
            self.scroll_velocity = min(5, self.scroll_velocity + 1)
        else:
            self.scroll_velocity = 1

        self.last_scroll_time = current_time
        scroll_amount = self.scroll_velocity

        if key == "UP":
            self.debug_scroll_position = max(
                0, self.debug_scroll_position - scroll_amount
            )
        elif key == "DOWN":
            max_scroll = max(0, self.debug_total_logs - self.debug_logs_per_page)
            self.debug_scroll_position = min(
                max_scroll, self.debug_scroll_position + scroll_amount
            )
        elif key == "PAGEUP":
            page_amount = self.debug_logs_per_page
            self.debug_scroll_position = max(
                0, self.debug_scroll_position - page_amount
            )
        elif key == "PAGEDOWN":
            max_scroll = max(0, self.debug_total_logs - self.debug_logs_per_page)
            page_amount = self.debug_logs_per_page
            self.debug_scroll_position = min(
                max_scroll, self.debug_scroll_position + page_amount
            )
        elif key == "HOME":
            self.debug_scroll_position = 0
            self.scroll_velocity = 0
        elif key == "END":
            max_scroll = max(0, self.debug_total_logs - self.debug_logs_per_page)
            self.debug_scroll_position = max_scroll
            self.scroll_velocity = 0
        else:
            # Reset active scrolling if key wasn't a navigation key
            self.active_scrolling = False
            return False  # Key not handled

        position_changed = old_position != self.debug_scroll_position
        return position_changed

    async def _handle_template_inspector_navigation(
        self, key: str, dashboard_data: Optional[Dict[str, Any]]
    ) -> bool:
        """Handle navigation keys when template inspector is active.

        Returns:
            True if the key was handled, False otherwise
        """
        if not dashboard_data:
            return False

        templates = dashboard_data.get("templates", {})

        if self.template_inspector_mode == "list":
            # Template list navigation
            if key == "\x1b":  # ESC key - exit template inspector
                self.show_template_inspector = False
                return True
            elif key == "\r" or key == "\n":  # Enter key - inspect selected template
                selected_template = self.template_inspector.get_selected_template_name(
                    templates
                )
                if selected_template:
                    # Fetch template content and switch to inspect mode
                    self.current_template_data = (
                        await self.data_fetcher.get_template_content(selected_template)
                    )
                    self.template_inspector_mode = "inspect"
                return True
            else:
                # Handle navigation within template list
                return self.template_inspector.handle_navigation(key, templates)

        elif self.template_inspector_mode == "inspect":
            # Template content inspection navigation
            if key == "\x1b":  # ESC key - back to template list
                self.template_inspector_mode = "list"
                self.current_template_data = None
                return True
            elif key == "\t":  # Tab key - cycle view modes
                self.template_inspector.cycle_view_mode()
                return True
            else:
                # Handle content navigation (scrolling, etc.)
                content = None
                if self.current_template_data:
                    if self.template_inspector.view_mode == "template":
                        content = self.current_template_data.get("source")
                    elif self.template_inspector.view_mode == "rendered":
                        content = self.current_template_data.get("rendered")
                    else:  # split mode doesn't need scrolling, handled separately
                        content = self.current_template_data.get("rendered")
                return self.template_inspector.handle_content_navigation(key, content)

        return False

    def _create_debug_panel(self) -> Panel:
        """Create scrollable debug log panel as a layout overlay."""
        debug_text = Text()

        # Calculate available terminal space and adjust page size dynamically
        terminal_height = self.console.size.height
        # Reserve space for: title (1), borders (2), navigation instructions (2), padding (2) = 7 lines
        available_lines = max(10, terminal_height - 7)
        self.debug_logs_per_page = available_lines

        # Update total logs count
        self.debug_total_logs = len(self.debug_logs)

        if not self.debug_logs:
            debug_text.append("No debug logs captured yet...\n\n", style="dim")
            scroll_info = ""
        else:
            # Calculate visible window based on scroll position
            all_logs = list(self.debug_logs)
            start_idx = self.debug_scroll_position
            end_idx = min(start_idx + self.debug_logs_per_page, len(all_logs))
            visible_logs = all_logs[start_idx:end_idx]

            # Create scroll position info with progress indicator
            if len(all_logs) <= self.debug_logs_per_page:
                scroll_info = f"Showing all {len(all_logs)} logs"
            else:
                # Calculate scroll percentage for progress bar
                scroll_percentage = int(
                    (start_idx / max(1, len(all_logs) - self.debug_logs_per_page)) * 100
                )

                scroll_info = f"Lines {start_idx + 1}-{end_idx} of {len(all_logs)} logs ({scroll_percentage}%)"
                if start_idx > 0:
                    scroll_info += " ↑ More above"
                if end_idx < len(all_logs):
                    scroll_info += " ↓ More below"

            # Display visible logs
            for log_entry in visible_logs:
                # Format absolute timestamp with millisecond precision in local timezone
                local_timestamp = log_entry["timestamp"].astimezone()
                time_str = local_timestamp.strftime("%H:%M:%S.%f")[
                    :-3
                ]  # Remove last 3 digits for milliseconds

                # Color code by level
                level_colors = {
                    "DEBUG": "dim",
                    "INFO": "white",
                    "WARNING": "yellow",
                    "ERROR": "red",
                    "CRITICAL": "bold red",
                }
                level_color = level_colors.get(log_entry["level"], "white")

                # Format log line
                debug_text.append(f"[{time_str}] ", style="dim")
                debug_text.append(f"{log_entry['level']:<7} ", style=level_color)
                debug_text.append(f"{log_entry['logger']:<12} ", style="cyan")
                debug_text.append(
                    f"{log_entry['message']}\n",
                    style=level_color if log_entry["level"] == "ERROR" else "white",
                )

        # Add navigation instructions
        debug_text.append(f"\n{scroll_info}\n", style="dim")
        debug_text.append(
            "Navigation: ↑↓ Line | PgUp/PgDn Page | Home/End Jump | 'd' Return",
            style="bold yellow",
        )

        return Panel(
            debug_text,
            title="🐛 Dashboard Debug Logs",
            border_style="magenta",
            padding=(1, 2),
            height=terminal_height,
            expand=True,
        )

    def _create_template_inspector_panel(self) -> Panel:
        """Create template inspector panel as a layout overlay."""
        # Get templates from the current dashboard data or use empty dict
        templates = {}
        if hasattr(self, "_last_dashboard_data") and self._last_dashboard_data:
            templates = self._last_dashboard_data.get("templates", {})

        if self.template_inspector_mode == "list":
            # Show template list for selection
            return self.template_inspector.render_template_list(
                templates, self.template_inspector.selected_template
            )
        elif self.template_inspector_mode == "inspect" and self.current_template_data:
            # Show template content inspection
            selected_template = self.template_inspector.get_selected_template_name(
                templates
            )
            if selected_template:
                template_info = templates.get(selected_template, {})
                template_type = template_info.get("type", "unknown")

                return self.template_inspector.render_template_content(
                    template_name=selected_template,
                    template_source=self.current_template_data.get("source"),
                    rendered_content=self.current_template_data.get("rendered"),
                    template_type=template_type,
                )

        # Fallback - show empty template inspector
        return Panel(
            "[yellow]Template inspector not available[/yellow]\n\nPress 't' to return to dashboard",
            title="📋 Template Inspector",
            border_style="yellow",
            padding=(2, 4),
        )

    def _create_layout(self) -> Layout:
        """Create the Rich layout structure."""
        # Create main layout
        layout = Layout()

        if self.show_help:
            # Show help overlay - take over entire screen
            layout.update(self._create_help_panel())
        elif self.show_debug:
            # Show debug overlay - take over entire screen
            layout.update(self._create_debug_panel())
        elif self.show_template_inspector:
            # Show template inspector overlay - take over entire screen
            layout.update(self._create_template_inspector_panel())
        elif self.loading:
            # Show loading screen - take over entire screen
            layout.update(self._create_loading_panel())
        else:
            # Normal dashboard layout
            # Split into header and body
            layout.split_column(
                Layout(name="header", size=4),  # Increased size for 2-line header
                Layout(name="body"),
            )

            # Split body into left and right columns
            layout["body"].split_row(Layout(name="left"), Layout(name="right", ratio=1))

            # Split left column
            layout["left"].split_column(Layout(name="pods"), Layout(name="templates"))

            # Split right column
            layout["right"].split_column(
                Layout(name="resources", ratio=4),  # More space for resource table
                Layout(name="performance", ratio=2),  # Better space for sparklines
                Layout(name="activity", ratio=4),  # Balanced space for activity feed
            )

        return layout

    def _update_layout(self, layout: Layout, data: dict) -> None:
        """Update the layout with fresh data."""
        try:
            # Store data for template inspector access
            self._last_dashboard_data = data

            # Skip updates if showing overlays or loading
            if (
                self.show_help
                or self.show_debug
                or self.loading
                or self.show_template_inspector
            ):
                return

            # Header
            layout["header"].update(
                self.header_panel.render(data, self.compatibility_level)
            )

            # Pods panel
            layout["pods"].update(self.pods_panel.render(data))

            # Templates panel
            layout["templates"].update(self.templates_panel.render(data))

            # Resources panel
            layout["resources"].update(self.resources_panel.render(data))

            # Performance panel
            layout["performance"].update(
                self.performance_panel.render(data, self.compatibility_level)
            )

            # Activity panel
            layout["activity"].update(
                self.activity_panel.render(data, self.compatibility_level)
            )

            # Add footer with controls and last update time
            for panel_name in ["activity"]:  # Add footer to activity panel
                if hasattr(layout[panel_name], "renderable") and hasattr(
                    layout[panel_name].renderable, "renderable"
                ):
                    # This is a bit hacky but works for adding footer info
                    pass

        except Exception as e:
            logger.error(f"Layout update error: {e}")
            # Show error in header if layout update fails
            try:
                layout["header"].update(
                    Panel(
                        f"[red]Dashboard error: {e}[/red]",
                        title="Error",
                        border_style="red",
                    )
                )
            except Exception as e:
                # If even error display fails, just continue
                logger.debug(f"Non-critical error in fallback error display: {e}")

    def _create_footer_text(self) -> str:
        """Create footer text with controls and status."""
        controls = "Ctrl+C to exit | Auto-refresh: ON"

        if self.last_update:
            update_time = self.last_update.strftime("%H:%M:%S")
            status = f"Last update: {update_time} | Refresh: {self.refresh_interval}s"
        else:
            status = "Initializing..."

        return f"{controls} | {status}"

    async def stop(self) -> None:
        """Stop the dashboard gracefully."""
        self.running = False
        # Clean up event loop reference
        self._event_loop = None
        # Clean up debug logging handler and restore original handlers
        self._cleanup_debug_logging()
