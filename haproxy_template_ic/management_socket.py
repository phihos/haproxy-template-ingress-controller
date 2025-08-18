"""
Management socket functionality for HAProxy Template IC.

This module provides a simple command-based management socket interface that allows
external tools to query the operator's internal state via Unix socket commands.
"""

import asyncio
import json
import logging
from pathlib import Path
from typing import Any, Dict, Optional

from haproxy_template_ic.metrics import get_metrics_collector

logger = logging.getLogger(__name__)


def serialize_state(memo: Any) -> Dict[str, Any]:
    """Serialize the application's internal state to a JSON-serializable dictionary."""
    try:
        state = {
            "config": memo.config.model_dump(mode="json")
            if hasattr(memo, "config") and memo.config
            else {},
            "haproxy_config_context": memo.haproxy_config_context.model_dump(
                mode="json"
            )
            if hasattr(memo, "haproxy_config_context") and memo.haproxy_config_context
            else {},
            "metadata": {
                "configmap_name": getattr(memo.cli_options, "configmap_name", None)
                if hasattr(memo, "cli_options")
                else None,
                "has_config_reload_flag": hasattr(memo, "config_reload_flag"),
                "has_stop_flag": hasattr(memo, "stop_flag"),
            },
            "cli_options": {
                "configmap_name": memo.cli_options.configmap_name,
                "healthz_port": memo.cli_options.healthz_port,
                "verbose": memo.cli_options.verbose,
                "socket_path": memo.cli_options.socket_path,
            }
            if hasattr(memo, "cli_options") and memo.cli_options
            else {},
            "indices": {
                name: dict(getattr(memo, name))
                for name in dir(memo)
                if name.endswith("_index")
                and not name.startswith("_")
                and hasattr(getattr(memo, name), "items")
            },
        }
        return state
    except Exception as e:
        return {
            "error": f"Failed to serialize state: {str(e)}",
            "metadata": {
                "configmap_name": getattr(memo.cli_options, "configmap_name", None)
                if hasattr(memo, "cli_options")
                else None
            },
        }


class ManagementSocketServer:
    """Management socket server for exposing internal state via commands."""

    def __init__(
        self,
        memo: Any,
        socket_path: str = "/run/haproxy-template-ic/management.sock",
    ) -> None:
        self.memo = memo
        self.logger = logger
        self.socket_path = Path(socket_path)
        self.server: Optional[asyncio.Server] = None

    async def _process_command(self, command: str) -> Dict[str, Any]:
        """Process a management socket command and return response data."""
        metrics = get_metrics_collector()
        parts = command.strip().split()

        if not parts:
            metrics.record_management_socket_command("empty", "error")
            return {"error": "Empty command"}

        if parts[0] == "dump":
            if len(parts) < 2:
                return {
                    "error": "Missing command name. Usage: dump <all|indices|config>"
                }

            if parts[1] == "all":
                metrics.record_management_socket_command("dump_all", "success")
                return serialize_state(self.memo)

            elif parts[1] == "indices":
                metrics.record_management_socket_command("dump_indices", "success")
                return self._dump_indices()

            elif parts[1] == "config":
                metrics.record_management_socket_command("dump_config", "success")
                return self._dump_config()

            else:
                metrics.record_management_socket_command("dump_unknown", "error")
                return {
                    "error": f"Unknown dump command: {parts[1]}. "
                    f"Available: all, indices, config"
                }

        elif parts[0] == "get":
            if len(parts) < 3:
                return {
                    "error": "Missing arguments. Usage: get <maps|watched_resources|template_snippets|certificates> <identifier>"
                }

            collection_type = parts[1]
            identifier = parts[2]

            collections = {
                "maps": self.memo.config.maps,
                "watched_resources": self.memo.config.watched_resources,
                "template_snippets": self.memo.config.template_snippets,
                "certificates": self.memo.config.certificates,
            }

            if collection_type in collections:
                item = collections[collection_type].get(identifier)
                if item:
                    return {
                        "result": item.model_dump(mode="json")
                        if hasattr(item, "model_dump")
                        else {"id": identifier, "data": str(item)}
                    }
                return {
                    "error": f"{collection_type.rstrip('s').title()} not found: {identifier}"
                }

            else:
                return {
                    "error": f"Unknown collection type: {collection_type}. "
                    f"Available: maps, watched_resources, template_snippets, certificates"
                }

        else:
            return {"error": f"Unknown command: {parts[0]}. Available: dump, get"}

    def _dump_indices(self) -> Dict[str, Any]:
        """Dump all indices from memo."""
        return {
            "indices": {
                name: dict(getattr(self.memo, name))
                for name in dir(self.memo)
                if name.endswith("_index")
                and not name.startswith("_")
                and hasattr(getattr(self.memo, name), "items")
            }
        }

    def _dump_config(self) -> Dict[str, Any]:
        """Dump HAProxy configuration context."""
        if (
            hasattr(self.memo, "haproxy_config_context")
            and self.memo.haproxy_config_context
        ):
            return {
                "haproxy_config_context": self.memo.haproxy_config_context.model_dump(
                    mode="json"
                )
            }
        return {
            "haproxy_config_context": {
                "rendered_maps": {},
                "rendered_config": None,
                "rendered_certificates": {},
            }
        }

    async def run(self) -> None:
        """Run the management socket server."""
        try:
            # Remove existing socket file if it exists
            if self.socket_path.exists():
                self.socket_path.unlink()

            # Start the Unix server
            self.server = await asyncio.start_unix_server(
                self._handle_client,
                path=str(self.socket_path),
                limit=1024,
            )

            self.logger.info(
                f"🔌 Management socket server listening on {self.socket_path}"
            )

            # Keep the server running indefinitely
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
            self.logger.error(f"❌ Management socket server error: {e}")
            # Don't re-raise other exceptions to avoid crashing the operator
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

            # Read command from client
            command_data = await reader.read(1024)
            if not command_data:
                command_data = b"dump all"  # Default command

            command_str = command_data.decode("utf-8").strip()
            self.logger.debug(f"📥 Received command: {command_str}")

            # Process command
            response_data = await self._process_command(command_str)

            # Send response
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
                # Client may have disconnected, log but don't crash
                self.logger.debug(f"Failed to send error response: {send_error}")
        finally:
            writer.close()
            await writer.wait_closed()

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
    """Run the management socket server to expose internal state via commands."""
    server = ManagementSocketServer(memo, socket_path)
    try:
        await server.run()
    except Exception as e:
        logger.error(f"❌ Management socket server failed: {e}")
        # Don't re-raise to avoid crashing the operator
