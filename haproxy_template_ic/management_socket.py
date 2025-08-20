"""
Management socket functionality for HAProxy Template IC.

This module provides a simple command-based management socket interface that allows
external tools to query the operator's internal state via Unix socket commands.
"""

import asyncio
import json
import logging
from pathlib import Path
from typing import Any, Dict, Iterator, List, Optional, Protocol, Tuple, Union

from haproxy_template_ic.metrics import get_metrics_collector

logger = logging.getLogger(__name__)


class KopfIndexData(Protocol):
    """Protocol for Kopf index data structures.

    This protocol defines the interface for Kopf index data structures
    that can be iterated over and support item access by key.
    """

    def __iter__(self) -> Iterator[Any]:
        """Iterate over the index keys."""
        ...

    def __getitem__(self, key: Any) -> Union[Dict[str, Any], List[Dict[str, Any]]]:
        """Get resources by index key."""
        ...


# Type aliases for better readability
ResourceDict = Dict[str, Any]
SerializationErrors = List[str]


def _serialize_resource_collection(resources: Any) -> List[ResourceDict]:
    """Serialize a resource collection to a list format.

    Args:
        resources: A resource or collection of resources

    Returns:
        List representation of the resources
    """
    if hasattr(resources, "__iter__") and not isinstance(resources, (str, bytes)):
        # Convert to list if it's iterable but not a string
        try:
            return list(resources)
        except (TypeError, ValueError):
            # Fallback for non-listable iterables
            return [resources]
    elif isinstance(resources, dict):
        # Wrap single resource dict in a list
        return [resources]
    else:
        # Fallback for other types - convert to dict-like structure
        return [{"data": resources}]


def _serialize_kopf_index(index_data: KopfIndexData) -> Dict[str, List[ResourceDict]]:
    """Serialize a Kopf index to a dictionary format.

    Args:
        index_data: Kopf index data structure implementing KopfIndexData protocol

    Returns:
        Dictionary with string keys and resource lists as values

    Raises:
        TypeError: If index_data cannot be serialized
    """
    if not (hasattr(index_data, "__iter__") and hasattr(index_data, "__getitem__")):
        return {}

    serialized_index = {}
    for key in index_data:
        resources = index_data[key]
        serialized_index[str(key)] = _serialize_resource_collection(resources)

    return serialized_index


def _serialize_memo_indices(
    memo: Any,
) -> Tuple[Dict[str, Dict[str, List[ResourceDict]]], SerializationErrors]:
    """Serialize all indices from a memo object.

    Args:
        memo: The memo object containing indices

    Returns:
        Tuple of (indices_dict, error_list)
    """
    indices = {}
    errors = []

    # Handle new memo.indices dictionary structure
    if hasattr(memo, "indices") and memo.indices:
        for name, index_data in memo.indices.items():
            try:
                indices[name] = _serialize_kopf_index(index_data)
            except (TypeError, ValueError, AttributeError) as e:
                errors.append(f"index '{name}' serialization: {e}")
                indices[name] = {}

    # Handle legacy _index attributes (backward compatibility)
    for name in dir(memo):
        if (
            name.endswith("_index")
            and not name.startswith("_")
            and hasattr(getattr(memo, name), "items")
        ):
            try:
                indices[name] = dict(getattr(memo, name))
            except (TypeError, ValueError) as e:
                errors.append(f"legacy index '{name}' serialization: {e}")
                indices[name] = {}

    return indices, errors


def serialize_state(memo: Any) -> Dict[str, Any]:
    """Serialize the application's internal state to a JSON-serializable dictionary."""
    state = {}
    errors = []

    # Serialize config with specific error handling
    try:
        if hasattr(memo, "config") and memo.config:
            state["config"] = memo.config.model_dump(mode="json")
        else:
            state["config"] = {}
    except (AttributeError, TypeError, ValueError, RuntimeError) as e:
        errors.append(f"config serialization: {e}")
        state["config"] = {}

    # Serialize HAProxy config context with specific error handling
    try:
        if hasattr(memo, "haproxy_config_context") and memo.haproxy_config_context:
            state["haproxy_config_context"] = memo.haproxy_config_context.model_dump(
                mode="json"
            )
        else:
            state["haproxy_config_context"] = {}
    except (AttributeError, TypeError, ValueError, RuntimeError) as e:
        errors.append(f"haproxy_config_context serialization: {e}")
        state["haproxy_config_context"] = {}

    # Serialize metadata with specific error handling
    try:
        state["metadata"] = {
            "configmap_name": getattr(memo.cli_options, "configmap_name", None)
            if hasattr(memo, "cli_options")
            else None,
            "has_config_reload_flag": hasattr(memo, "config_reload_flag"),
            "has_stop_flag": hasattr(memo, "stop_flag"),
        }
    except (AttributeError, TypeError) as e:
        errors.append(f"metadata serialization: {e}")
        state["metadata"] = {"configmap_name": None}

    # Serialize CLI options with specific error handling
    try:
        if hasattr(memo, "cli_options") and memo.cli_options:
            state["cli_options"] = {
                "configmap_name": memo.cli_options.configmap_name,
                "healthz_port": memo.cli_options.healthz_port,
                "verbose": memo.cli_options.verbose,
                "socket_path": memo.cli_options.socket_path,
            }
        else:
            state["cli_options"] = {}
    except (AttributeError, TypeError) as e:
        errors.append(f"cli_options serialization: {e}")
        state["cli_options"] = {}

    # Serialize indices with specific error handling
    try:
        indices, index_errors = _serialize_memo_indices(memo)
        state["indices"] = indices
        errors.extend(index_errors)
    except (AttributeError, TypeError) as e:
        errors.append(f"indices serialization: {e}")
        state["indices"] = {}

    # Add any serialization errors to the response
    if errors:
        state["serialization_errors"] = errors
        logger.warning(
            f"State serialization encountered {len(errors)} errors: {errors}"
        )

    return state


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
                    "error": "Missing command name. Usage: dump <all|indices|config|deployments>"
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

            elif parts[1] == "deployments":
                metrics.record_management_socket_command("dump_deployments", "success")
                return self._dump_deployments()

            else:
                metrics.record_management_socket_command("dump_unknown", "error")
                return {
                    "error": f"Unknown dump command: {parts[1]}. "
                    f"Available: all, indices, config, deployments"
                }

        elif parts[0] == "get":
            if len(parts) < 3:
                return {
                    "error": "Missing arguments. Usage: get <maps|watched_resources|template_snippets|certificates|deployment> <identifier>"
                }

            collection_type = parts[1]
            identifier = parts[2]

            collections = {
                "maps": self.memo.config.maps,
                "watched_resources": self.memo.config.watched_resources,
                "template_snippets": self.memo.config.template_snippets,
                "certificates": self.memo.config.certificates,
            }

            if collection_type == "deployment":
                # Handle deployment history lookup
                return self._get_deployment_history(identifier)
            elif collection_type in collections:
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
                    f"Available: maps, watched_resources, template_snippets, certificates, deployment"
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

    def _dump_deployments(self) -> Dict[str, Any]:
        """Dump all deployment history."""
        if hasattr(self.memo, "deployment_history") and self.memo.deployment_history:
            return self.memo.deployment_history.to_dict()
        return {"deployment_history": {}}

    def _get_deployment_history(self, endpoint_url: str) -> Dict[str, Any]:
        """Get deployment history for a specific endpoint."""
        if hasattr(self.memo, "deployment_history") and self.memo.deployment_history:
            history_dict = self.memo.deployment_history.to_dict()
            deployment_data = history_dict.get("deployment_history", {})

            if endpoint_url in deployment_data:
                return {"result": deployment_data[endpoint_url]}
            else:
                return {
                    "error": f"No deployment history found for endpoint: {endpoint_url}",
                    "available_endpoints": list(deployment_data.keys()),
                }
        return {"error": "No deployment history available"}

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
