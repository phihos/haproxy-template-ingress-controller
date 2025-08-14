"""
Management socket functionality for HAProxy Template IC.

This module provides a simple command-based management socket interface that allows
external tools to query the operator's internal state via Unix socket commands.
"""

import asyncio
import json
import logging
from dataclasses import asdict, is_dataclass
from pathlib import Path
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)


class DataclassJSONEncoder(json.JSONEncoder):
    """Custom JSON encoder that handles dataclasses."""

    def default(self, obj):
        if is_dataclass(obj):
            return asdict(obj)
        return super().default(obj)


class StateSerializer:
    """Handles serialization of operator state for management socket responses."""

    def __init__(self, memo: Any) -> None:
        """Initialize serializer with memo object."""
        self.memo = memo

    def _get_configmap_name(self) -> Optional[str]:
        """Extract configmap name from memo's CLI options."""
        if hasattr(self.memo, "cli_options") and self.memo.cli_options:
            configmap_name = self.memo.cli_options.configmap_name
            return configmap_name if isinstance(configmap_name, str) else None
        return None

    def _serialize_cli_options(self) -> Dict[str, Any]:
        """Serialize CLI options from memo."""
        if not hasattr(self.memo, "cli_options") or not self.memo.cli_options:
            return {}

        return {
            "configmap_name": self.memo.cli_options.configmap_name,
            "healthz_port": self.memo.cli_options.healthz_port,
            "verbose": self.memo.cli_options.verbose,
            "socket_path": self.memo.cli_options.socket_path,
        }

    def _serialize_config(self) -> Dict[str, Any]:
        """Serialize configuration from memo."""
        config: Dict[str, Any] = {
            "pod_selector": None,
            "watch_resources": {},
            "maps": {},
        }

        if not hasattr(self.memo, "config") or not self.memo.config:
            return config

        # Serialize pod selector - convert dataclass to dict if needed
        pod_selector = self.memo.config.pod_selector
        if is_dataclass(pod_selector) and not isinstance(pod_selector, type):
            pod_selector = asdict(pod_selector)
        config["pod_selector"] = pod_selector

        # Serialize watch resources
        for watch_config in self.memo.config.watch_resources:
            config["watch_resources"][watch_config.id] = {
                "kind": watch_config.kind,
                "group": watch_config.group,
                "version": watch_config.version,
            }

        # Serialize maps
        for map_config in self.memo.config.maps:
            template_source = "unavailable"
            if hasattr(map_config.template, "source"):
                template_source = str(map_config.template.source)

            config["maps"][map_config.path] = {
                "path": map_config.path,
                "template_source": template_source,
            }

        return config

    def _serialize_haproxy_config_context(self) -> Dict[str, Any]:
        """Serialize HAProxy configuration context from memo."""
        context: Dict[str, Any] = {"rendered_maps": {}}

        if (
            not hasattr(self.memo, "haproxy_config_context")
            or not self.memo.haproxy_config_context
        ):
            return context

        for rendered_map in self.memo.haproxy_config_context.rendered_maps:
            context["rendered_maps"][rendered_map.path] = {
                "path": rendered_map.path,
                "content": rendered_map.content,
                "map_config_path": rendered_map.map_config.path,
            }

        return context

    def _serialize_indices(self) -> Dict[str, Any]:
        """Serialize indices from memo."""
        indices: Dict[str, Any] = {}

        for attr_name in dir(self.memo):
            if not attr_name.endswith("_index") or attr_name.startswith("_"):
                continue

            try:
                index_value = getattr(self.memo, attr_name)
                if hasattr(index_value, "items"):
                    indices[attr_name] = dict(index_value)
            except Exception:
                indices[attr_name] = "serialization_error"

        return indices

    def _serialize_metadata(self) -> Dict[str, Any]:
        """Serialize metadata from memo."""
        return {
            "configmap_name": self._get_configmap_name(),
            "has_config_reload_flag": hasattr(self.memo, "config_reload_flag"),
            "has_stop_flag": hasattr(self.memo, "stop_flag"),
        }

    def serialize(self) -> Dict[str, Any]:
        """Serialize the application's internal state to a JSON-serializable
        dictionary."""
        try:
            state = {
                "config": self._serialize_config(),
                "haproxy_config_context": self._serialize_haproxy_config_context(),
                "metadata": self._serialize_metadata(),
                "cli_options": self._serialize_cli_options(),
                "indices": self._serialize_indices(),
            }

            return state

        except Exception as e:
            return {
                "error": f"Failed to serialize state: {str(e)}",
                "metadata": {"configmap_name": self._get_configmap_name()},
            }


def serialize_state(memo: Any) -> Dict[str, Any]:
    """Serialize the application's internal state to a JSON-serializable dictionary."""
    serializer = StateSerializer(memo)
    return serializer.serialize()


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
        parts = command.strip().split()

        if not parts:
            return {"error": "Empty command"}

        if parts[0] == "dump":
            if len(parts) < 2:
                return {
                    "error": "Missing command name. Usage: dump <all|indices|config>"
                }

            if parts[1] == "all":
                return serialize_state(self.memo)

            elif parts[1] == "indices":
                return self._dump_indices()

            elif parts[1] == "config":
                return self._dump_config()

            else:
                return {
                    "error": f"Unknown dump command: {parts[1]}. "
                    f"Available: all, indices, config"
                }

        elif parts[0] == "get":
            if len(parts) < 3:
                return {
                    "error": "Missing arguments. Usage: get <maps|watch_resources|template_snippets|certificates> <identifier>"
                }

            collection_type = parts[1]
            identifier = parts[2]

            if collection_type == "maps":
                map_config = self.memo.config.maps.by_path(identifier)
                if map_config:
                    return {
                        "result": {
                            "path": map_config.path,
                            "template_source": getattr(
                                map_config.template, "source", "unavailable"
                            ),
                        }
                    }
                return {"error": f"Map not found: {identifier}"}

            elif collection_type == "watch_resources":
                watch_config = self.memo.config.watch_resources.by_id(identifier)
                if watch_config:
                    return {
                        "result": {
                            "id": watch_config.id,
                            "kind": watch_config.kind,
                            "group": watch_config.group,
                            "version": watch_config.version,
                        }
                    }
                return {"error": f"Watch resource not found: {identifier}"}

            elif collection_type == "template_snippets":
                snippet = self.memo.config.template_snippets.by_name(identifier)
                if snippet:
                    return {
                        "result": {
                            "name": snippet.name,
                            "template_source": getattr(
                                snippet.template, "source", "unavailable"
                            ),
                        }
                    }
                return {"error": f"Template snippet not found: {identifier}"}

            elif collection_type == "certificates":
                cert_config = self.memo.config.certificates.by_name(identifier)
                if cert_config:
                    return {
                        "result": {
                            "name": cert_config.name,
                            "template_source": getattr(
                                cert_config.template, "source", "unavailable"
                            ),
                        }
                    }
                return {"error": f"Certificate not found: {identifier}"}

            else:
                return {
                    "error": f"Unknown collection type: {collection_type}. "
                    f"Available: maps, watch_resources, template_snippets, certificates"
                }

        else:
            return {"error": f"Unknown command: {parts[0]}. Available: dump, get"}

    def _dump_indices(self) -> Dict[str, Any]:
        """Dump all indices from memo."""
        indices: Dict[str, Any] = {}
        for attr_name in dir(self.memo):
            if attr_name.endswith("_index") and not attr_name.startswith("_"):
                try:
                    index_value = getattr(self.memo, attr_name)
                    if hasattr(index_value, "items"):
                        indices[attr_name] = dict(index_value)
                except Exception as e:
                    indices[attr_name] = f"error: {str(e)}"
        return {"indices": indices}

    def _dump_config(self) -> Dict[str, Any]:
        """Dump HAProxy configuration context."""
        if (
            hasattr(self.memo, "haproxy_config_context")
            and self.memo.haproxy_config_context
        ):
            rendered_maps: Dict[str, Any] = {}
            for rendered_map in self.memo.haproxy_config_context.rendered_maps:
                rendered_maps[rendered_map.path] = {
                    "path": rendered_map.path,
                    "content": rendered_map.content,
                    "map_config_path": rendered_map.map_config.path,
                }
            return {"haproxy_config_context": {"rendered_maps": rendered_maps}}
        else:
            return {"haproxy_config_context": {"rendered_maps": {}}}

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
        try:
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
            response = json.dumps(
                response_data, indent=2, cls=DataclassJSONEncoder
            ).encode("utf-8")
            writer.write(response)
            await writer.drain()

            self.logger.debug(f"📤 Sent response for command: {command_str}")

        except Exception as e:
            self.logger.error(f"❌ Error handling management socket client: {e}")
            error_response = json.dumps(
                {"error": str(e)}, cls=DataclassJSONEncoder
            ).encode("utf-8")
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
