"""
Management socket server for HAProxy Template IC.

This module provides the main server class and entry point for the
management socket interface that allows external tools to query the
operator's internal state via Unix socket commands.
"""

import asyncio
import json
import logging
from pathlib import Path
from typing import Any, Dict, Optional

from haproxy_template_ic.constants import SOCKET_BUFFER_SIZE
from haproxy_template_ic.metrics import get_metrics_collector
from haproxy_template_ic.management.handlers import CommandHandler

logger = logging.getLogger(__name__)


class ManagementSocketServer:
    """Management socket server for exposing internal state via commands."""

    def __init__(
        self,
        memo: Any,
        socket_path: str = "/run/haproxy-template-ic/management.sock",
    ) -> None:
        """Initialize the management socket server.

        Args:
            memo: Kopf memo object containing operator state
            socket_path: Path to the Unix socket file
        """
        self.memo = memo
        self.logger = logger
        self.socket_path = Path(socket_path)
        self.server: Optional[asyncio.Server] = None
        self.command_handler = CommandHandler(memo)

    async def run(self) -> None:
        """Run the management socket server."""
        try:
            # Ensure parent directory exists (needed for mirrord compatibility)
            socket_dir = self.socket_path.parent
            if not socket_dir.exists():
                try:
                    socket_dir.mkdir(parents=True, exist_ok=True)
                    self.logger.debug(f"🔌 Created socket directory: {socket_dir}")
                except (PermissionError, OSError) as e:
                    self.logger.warning(
                        f"Could not create socket directory {socket_dir}: {e}"
                    )
                    # Continue anyway - the socket creation will fail with a more specific error

            if self.socket_path.exists():
                self.socket_path.unlink()
            self.server = await asyncio.start_unix_server(
                self._handle_client,
                path=str(self.socket_path),
                limit=SOCKET_BUFFER_SIZE,
            )

            self.logger.info(
                f"🔌 Management socket server listening on {self.socket_path}"
            )

            async with self.server:
                try:
                    await self.server.serve_forever()
                except asyncio.CancelledError:
                    self.logger.info(
                        "🔌 Management socket server received cancellation signal"
                    )
                    raise

        except asyncio.CancelledError:
            self.logger.info("🔌 Management socket server was cancelled")
            raise
        except Exception as e:
            self.logger.error(
                f"❌ Management socket server (path {self.socket_path}) error: {e}"
            )
        finally:
            self._cleanup()

    async def _handle_client(
        self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter
    ) -> None:
        """Handle a client connection."""
        metrics = get_metrics_collector()

        try:
            metrics.record_management_socket_connection()
            self.logger.debug("🔌 New management socket client connected")

            command_data = await reader.read(SOCKET_BUFFER_SIZE)
            if not command_data:
                command_data = b"dump all"

            command_str = command_data.decode("utf-8").strip()
            self.logger.debug(f"📥 Received command: {command_str}")

            response_data = await self.command_handler.process_command(command_str)

            response = json.dumps(response_data, indent=2, default=str).encode("utf-8")
            writer.write(response)
            await writer.drain()

            self.logger.debug(f"📤 Sent response for command: {command_str}")

        except Exception as e:
            self.logger.error(f"❌ Error handling management socket client: {e}")
            error_response = json.dumps({"error": str(e)}, default=str).encode("utf-8")
            try:
                writer.write(error_response)
                await writer.drain()
            except Exception as send_error:
                self.logger.debug(f"Failed to send error response: {send_error}")
        finally:
            writer.close()
            await writer.wait_closed()

    async def _process_command(self, command: str) -> Dict[str, Any]:
        """Process a command string and return response data.

        This method delegates to the command handler for backward compatibility.

        Args:
            command: Command string to process

        Returns:
            Dictionary containing command response data
        """
        return await self.command_handler.process_command(command)

    # Backward compatibility methods for tests - delegate to data provider
    def _dump_indices(self) -> Dict[str, Any]:
        """Dump all indices from memo."""
        from haproxy_template_ic.management.data_providers import DataProvider

        data_provider = DataProvider(self.memo)
        return data_provider.dump_indices()

    def _dump_config(self) -> Dict[str, Any]:
        """Dump HAProxy configuration context and config."""
        from haproxy_template_ic.management.data_providers import DataProvider

        data_provider = DataProvider(self.memo)
        return data_provider.dump_config()

    def _dump_stats(self) -> Dict[str, Any]:
        """Dump dashboard-optimized statistics."""
        from haproxy_template_ic.management.data_providers import DataProvider

        data_provider = DataProvider(self.memo)
        return data_provider.dump_stats()

    def _cleanup(self) -> None:
        """Clean up server resources."""
        if self.server:
            self.server.close()
        if self.socket_path.exists():
            self.socket_path.unlink()
        self.logger.info("🔌 Management socket server stopped")


async def run_management_socket_server(
    memo: Any,
    socket_path: str = "/run/haproxy-template-ic/management.sock",
) -> None:
    """Run the management socket server to expose internal state via commands.

    Args:
        memo: Kopf memo object containing operator state
        socket_path: Path to the Unix socket file
    """
    server = ManagementSocketServer(memo, socket_path)
    try:
        await server.run()
    except Exception as e:
        logger.error(f"❌ Management socket server failed: {e}")
