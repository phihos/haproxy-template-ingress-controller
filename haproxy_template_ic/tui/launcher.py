"""
TUI launcher for the HAProxy Template IC dashboard.

Handles initialization and launching of the Textual TUI dashboard application.
"""

import asyncio
import logging
from typing import Optional

from .app import TuiApp

logger = logging.getLogger(__name__)

__all__ = ["TuiLauncher"]


class TuiLauncher:
    """Launcher for the Textual TUI dashboard application."""

    def __init__(
        self,
        namespace: str,
        context: Optional[str] = None,
        refresh_interval: int = 5,
        deployment_name: str = "haproxy-template-ic",
        socket_path: Optional[str] = None,
    ):
        self.namespace = namespace
        self.context = context
        self.refresh_interval = refresh_interval
        self.deployment_name = deployment_name
        self.socket_path = socket_path

    async def launch(self) -> None:
        """Launch the TUI dashboard application."""
        try:
            logger.info(f"Starting TUI dashboard for namespace '{self.namespace}'")

            # Create and configure the TUI app
            app = TuiApp(
                namespace=self.namespace,
                context=self.context,
                refresh_interval=self.refresh_interval,
                deployment_name=self.deployment_name,
                socket_path=self.socket_path,
            )

            # Run the app
            await app.run_async()

        except KeyboardInterrupt:
            logger.info("TUI dashboard stopped by user")
        except Exception as e:
            logger.error(f"TUI dashboard error: {e}", exc_info=True)
            # Removed traceback.print_exc() to avoid interfering with Textual rendering
            raise

    def run(self) -> None:
        """Run the TUI dashboard synchronously."""
        try:
            asyncio.run(self.launch())
        except KeyboardInterrupt:
            logger.info("TUI dashboard stopped by user")
        except Exception as e:
            logger.error(f"TUI dashboard error: {e}", exc_info=True)
            raise
