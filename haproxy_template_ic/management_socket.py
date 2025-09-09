"""
Management socket functionality for HAProxy Template IC.

This module provides a simple command-based management socket interface that allows
external tools to query the operator's internal state via Unix socket commands.
"""

import asyncio
import json
import logging
import os
import traceback
from datetime import datetime
from importlib import metadata
from pathlib import Path
from typing import Any, Callable, Dict, Iterator, List, Optional, Protocol, Tuple, Union

from kr8s.objects import Pod

from haproxy_template_ic.constants import (
    HAPROXY_PODS_INDEX,
    SOCKET_BUFFER_SIZE,
    DEFAULT_ACTIVITY_QUERY_LIMIT,
)
from haproxy_template_ic.deployment_state import DeploymentStateTracker
from haproxy_template_ic.metrics import get_metrics_collector, get_performance_metrics
from haproxy_template_ic.models import IndexedResourceCollection
from haproxy_template_ic.tui.models import PodInfo

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
        try:
            return list(resources)
        except (TypeError, ValueError):
            return [resources]
    elif isinstance(resources, dict):
        return [resources]
    else:
        return [{"data": resources}]


def _serialize_kopf_index(index_data: KopfIndexData) -> Dict[str, List[ResourceDict]]:
    """Serialize a Kopf index to a dictionary format.

    Args:
        index_data: Kopf index data structure implementing KopfIndexData protocol

    Returns:
        Dictionary with string keys and resource lists as values
    """
    if not (
        hasattr(index_data, "__iter__")
        and hasattr(index_data, "__getitem__")
        and hasattr(index_data, "items")
    ):
        return {}

    serialized_index = {}
    try:
        for key in index_data:
            resources = index_data[key]
            serialized_key = (
                ":".join(str(k) for k in key) if isinstance(key, tuple) else str(key)
            )
            serialized_index[serialized_key] = _serialize_resource_collection(resources)
    except (TypeError, KeyError):
        return {}

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

    return indices, errors


def _safe_serialize(
    operation_name: str,
    serializer_func: Callable[[], Any],
    default_value: Any,
    errors: List[str],
    exception_types: Tuple = (AttributeError, TypeError, ValueError, RuntimeError),
) -> Any:
    """Safely serialize data with consistent error handling."""
    try:
        return serializer_func()
    except exception_types as e:
        errors.append(f"{operation_name} serialization: {e}")
        return default_value


def serialize_state(memo: Any) -> Dict[str, Any]:
    """Serialize the application's internal state to a JSON-serializable dictionary."""
    state = {}
    errors: List[str] = []

    # Serialize config with specific error handling
    def serialize_config():
        if hasattr(memo, "config") and memo.config:
            return memo.config.model_dump(mode="json")
        return {}

    state["config"] = _safe_serialize("config", serialize_config, {}, errors)

    # Serialize HAProxy config context with specific error handling
    def serialize_config_context():
        if hasattr(memo, "haproxy_config_context") and memo.haproxy_config_context:
            return memo.haproxy_config_context.model_dump(mode="json")
        return {}

    state["haproxy_config_context"] = _safe_serialize(
        "haproxy_config_context", serialize_config_context, {}, errors
    )

    # Serialize metadata with specific error handling
    def serialize_metadata():
        return {
            "configmap_name": getattr(memo.cli_options, "configmap_name", None)
            if hasattr(memo, "cli_options")
            else None,
            "has_config_reload_flag": hasattr(memo, "config_reload_flag"),
            "has_stop_flag": hasattr(memo, "stop_flag"),
        }

    state["metadata"] = _safe_serialize(
        "metadata", serialize_metadata, {"configmap_name": None}, errors
    )

    # Serialize CLI options (bootstrap parameters only)
    def serialize_cli_options():
        if hasattr(memo, "cli_options") and memo.cli_options:
            return {
                "configmap_name": memo.cli_options.configmap_name,
                "secret_name": memo.cli_options.secret_name,
            }
        return {}

    state["cli_options"] = _safe_serialize(
        "cli_options", serialize_cli_options, {}, errors
    )

    # Serialize operator configuration (runtime settings)
    def serialize_operator_config():
        if hasattr(memo, "config") and memo.config:
            return {
                "healthz_port": memo.config.operator.healthz_port,
                "metrics_port": memo.config.operator.metrics_port,
                "socket_path": memo.config.operator.socket_path,
                "verbose": memo.config.logging.verbose,
                "structured_logging": memo.config.logging.structured,
                "tracing_enabled": memo.config.tracing.enabled,
                "validation_dataplane_host": memo.config.validation.dataplane_host,
                "validation_dataplane_port": memo.config.validation.dataplane_port,
            }
        return {}

    state["operator_config"] = _safe_serialize(
        "operator_config", serialize_operator_config, {}, errors
    )

    # Serialize indices with specific error handling
    def serialize_indices():
        indices, index_errors = _serialize_memo_indices(memo)
        errors.extend(index_errors)
        return indices

    state["indices"] = _safe_serialize("indices", serialize_indices, {}, errors)

    # Serialize debouncer stats with specific error handling
    def serialize_debouncer():
        if hasattr(memo, "debouncer") and memo.debouncer:
            return memo.debouncer.get_stats()
        return None

    state["debouncer"] = _safe_serialize("debouncer", serialize_debouncer, None, errors)

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

    def _handle_dump_command(self, parts: List[str], metrics: Any) -> Dict[str, Any]:
        """Handle dump subcommands."""
        if len(parts) < 2:
            return {
                "error": "Missing command name. Usage: dump <all|indices|config|deployments|debouncer|stats|activity|pods|dashboard>"
            }

        command_name = parts[1]

        # Handle each command explicitly to ensure proper handler invocation
        if command_name == "all":
            metrics.record_management_socket_command("dump_all", "success")
            return serialize_state(self.memo)
        elif command_name == "indices":
            metrics.record_management_socket_command("dump_indices", "success")
            return self._dump_indices()
        elif command_name == "config":
            metrics.record_management_socket_command("dump_config", "success")
            return self._dump_config()
        elif command_name == "deployments":
            metrics.record_management_socket_command("dump_deployments", "success")
            return self._dump_deployments()
        elif command_name == "debouncer":
            metrics.record_management_socket_command("dump_debouncer", "success")
            return self._dump_debouncer()
        elif command_name == "stats":
            metrics.record_management_socket_command("dump_stats", "success")
            return self._dump_stats()
        elif command_name == "activity":
            metrics.record_management_socket_command("dump_activity", "success")
            return self._dump_activity()
        elif command_name == "pods":
            metrics.record_management_socket_command("dump_pods", "success")
            return self._dump_pods()
        elif command_name == "dashboard":
            metrics.record_management_socket_command("dump_dashboard", "success")
            return self._dump_dashboard()
        elif command_name == "debug":
            # Debug handler to test function dispatch
            metrics.record_management_socket_command("dump_debug", "success")
            return {
                "debug": "handler working",
                "available_methods": [m for m in dir(self) if m.startswith("_dump")],
                "command_name": command_name,
            }
        else:
            metrics.record_management_socket_command("dump_unknown", "error")
            return {
                "error": f"Unknown dump command: {command_name}. "
                f"Available: all, indices, config, deployments, debouncer, stats, activity, pods, dashboard, debug"
            }

    def _handle_get_command(self, parts: List[str]) -> Dict[str, Any]:
        """Handle get subcommands."""
        if len(parts) < 3:
            return {
                "error": "Missing arguments. Usage: get <maps|watched_resources|template_snippets|certificates|deployment|template_source|rendered_template> <identifier>"
            }

        collection_type = parts[1]
        identifier = parts[2]

        if collection_type == "deployment":
            return self._get_deployment_history(identifier)
        elif collection_type == "template_source":
            return self._get_template_source(identifier)
        elif collection_type == "rendered_template":
            return self._get_rendered_template(identifier)

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

        return {
            "error": f"Unknown collection type: {collection_type}. "
            f"Available: maps, watched_resources, template_snippets, certificates, deployment, template_source, rendered_template"
        }

    async def _process_command(self, command: str) -> Dict[str, Any]:
        """Process a management socket command and return response data."""
        metrics = get_metrics_collector()
        parts = command.strip().split()

        if not parts:
            metrics.record_management_socket_command("empty", "error")
            return {"error": "Empty command"}

        command_name = parts[0]

        if command_name == "dump":
            return self._handle_dump_command(parts, metrics)
        elif command_name == "get":
            return self._handle_get_command(parts)
        elif command_name == "version":
            return self._handle_version_command()
        else:
            return {
                "error": f"Unknown command: {command_name}. Available: dump, get, version"
            }

    def _dump_indices(self) -> Dict[str, Any]:
        """Dump all indices from memo."""
        indices: Dict[str, Any] = {}

        # Handle new memo.indices dictionary structure
        if hasattr(self.memo, "indices") and self.memo.indices:
            for name, index_data in self.memo.indices.items():
                try:
                    indices[name] = _serialize_kopf_index(index_data)
                except Exception as e:
                    indices[name] = {"error": f"Failed to serialize: {e}"}

        return {"indices": indices}

    def _dump_config(self) -> Dict[str, Any]:
        """Dump HAProxy configuration context and config."""
        result = {}

        # Include the actual config (contains template_snippets, maps, etc.)
        if hasattr(self.memo, "config") and self.memo.config:
            config_dict = self.memo.config.model_dump(mode="json")
            result["config"] = config_dict

        # Include the rendered context
        if (
            hasattr(self.memo, "haproxy_config_context")
            and self.memo.haproxy_config_context
        ):
            context_dict = self.memo.haproxy_config_context.model_dump(mode="json")
            result["haproxy_config_context"] = context_dict
        else:
            result["haproxy_config_context"] = {
                "rendered_content": [],
                "rendered_config": None,
            }

        return result

    def _dump_deployments(self) -> Dict[str, Any]:
        """Dump all deployment history using DeploymentStateTracker."""
        # Use DeploymentStateTracker with activity_buffer
        if hasattr(self.memo, "activity_buffer") and self.memo.activity_buffer:
            tracker = DeploymentStateTracker(self.memo.activity_buffer)
            try:
                try:
                    loop = asyncio.get_running_loop()
                    loop.create_task(tracker.to_dict())
                    return {"deployment_history": {}}
                except RuntimeError:
                    return asyncio.run(tracker.to_dict())
            except Exception as e:
                logger.error(f"Failed to get deployment history: {e}")
                return {"error": f"Failed to get deployment history: {e}"}

        return {"deployment_history": {}}

    def _dump_debouncer(self) -> Dict[str, Any]:
        """Dump template debouncer statistics."""
        if hasattr(self.memo, "debouncer") and self.memo.debouncer:
            return {"debouncer": self.memo.debouncer.get_stats()}
        return {"debouncer": None}

    def _get_deployment_history(self, endpoint_url: str) -> Dict[str, Any]:
        """Get deployment history for a specific endpoint from activity events."""
        # Get all deployment history
        deployment_data = self._dump_deployments().get("deployment_history", {})

        if endpoint_url in deployment_data:
            return {"result": deployment_data[endpoint_url]}
        else:
            return {
                "error": f"No deployment history found for endpoint: {endpoint_url}",
                "available_endpoints": list(deployment_data.keys()),
            }

    def _extract_template_from_collection(
        self,
        collection,
        collection_type: str,
        template_name: str,
        template_sources: List[Dict[str, Any]],
    ) -> None:
        """Extract template source from a configuration collection."""
        if template_name in collection:
            template_obj = collection[template_name]
            try:
                source = (
                    template_obj.template
                    if hasattr(template_obj, "template")
                    else str(template_obj)
                )
                template_sources.append(
                    {
                        "type": collection_type,
                        "source": source,
                        "filename": template_name,
                    }
                )
            except Exception as e:
                logger.error(
                    f"Failed to extract {collection_type} template source for {template_name}: {e}"
                )

    def _get_template_source(self, template_name: str) -> Dict[str, Any]:
        """Get the source template content (Jinja2) for a given template."""
        logger.debug(f"Getting template source for: {template_name}")

        if not hasattr(self.memo, "config") or not self.memo.config:
            logger.debug("Configuration not available in memo")
            return {"error": "Configuration not available"}

        template_sources: List[Dict[str, Any]] = []

        # Check all template collections
        collections = [
            (self.memo.config.maps, "map"),
            (self.memo.config.files, "file"),
            (self.memo.config.certificates, "certificate"),
            (self.memo.config.template_snippets, "snippet"),
        ]

        for collection, collection_type in collections:
            self._extract_template_from_collection(
                collection, collection_type, template_name, template_sources
            )

        # HAProxy config template
        if template_name == "haproxy.cfg":
            if hasattr(self.memo.config, "haproxy_config"):
                config_template = self.memo.config.haproxy_config
                try:
                    source = (
                        config_template.template
                        if hasattr(config_template, "template")
                        else str(config_template)
                    )
                    template_sources.append(
                        {"type": "config", "source": source, "filename": "haproxy.cfg"}
                    )
                except Exception as e:
                    logger.error(
                        f"Failed to extract haproxy_config template source: {e}"
                    )
                    logger.error(f"config_template attributes: {dir(config_template)}")
            else:
                logger.debug("haproxy_config not found in memo.config")
                logger.debug(f"memo.config attributes: {dir(self.memo.config)}")

        if template_sources:
            # Return the first matching template (there should only be one per name)
            template_info = template_sources[0]
            logger.debug(
                f"Returning template source for {template_name}: type={template_info['type']}, source_length={len(template_info['source'])}"
            )
            return {
                "result": {
                    "template_name": template_name,
                    "type": template_info["type"],
                    "source": template_info["source"],
                    "filename": template_info["filename"],
                }
            }

        # Debug: List available templates
        available_templates = []
        if hasattr(self.memo.config, "maps") and self.memo.config.maps:
            available_templates.extend(self.memo.config.maps.keys())
        if hasattr(self.memo.config, "files") and self.memo.config.files:
            available_templates.extend(self.memo.config.files.keys())
        if hasattr(self.memo.config, "certificates") and self.memo.config.certificates:
            available_templates.extend(self.memo.config.certificates.keys())
        if (
            hasattr(self.memo.config, "template_snippets")
            and self.memo.config.template_snippets
        ):
            available_templates.extend(self.memo.config.template_snippets.keys())
        if hasattr(self.memo.config, "haproxy_config"):
            available_templates.append("haproxy.cfg")

        logger.debug(f"Available templates: {available_templates}")
        return {
            "error": f"Template source not found: {template_name}. Available: {available_templates}"
        }

    def _get_rendered_template(self, template_name: str) -> Dict[str, Any]:
        """Get the rendered content for a given template."""
        logger.debug(f"Getting rendered template for: {template_name}")

        if (
            not hasattr(self.memo, "haproxy_config_context")
            or not self.memo.haproxy_config_context
        ):
            logger.debug("HAProxy config context not available in memo")
            return {"error": "HAProxy config context not available"}

        context = self.memo.haproxy_config_context
        logger.debug(f"Found haproxy_config_context, type: {type(context)}")

        # Check rendered HAProxy config
        if template_name == "haproxy.cfg":
            logger.debug("Checking for rendered HAProxy config")
            rendered_config = getattr(context, "rendered_config", None)
            logger.debug(
                f"rendered_config found: {rendered_config is not None}, type: {type(rendered_config)}"
            )

            if rendered_config:
                if hasattr(rendered_config, "content"):
                    content = rendered_config.content
                    logger.debug(
                        f"Found rendered_config.content, length: {len(content) if content else 0}"
                    )
                    if content:
                        return {
                            "result": {
                                "template_name": template_name,
                                "type": "config",
                                "content": content,
                                "filename": "haproxy.cfg",
                            }
                        }
                    else:
                        logger.debug("rendered_config.content is empty")
                else:
                    logger.debug("rendered_config does not have content attribute")
                    logger.debug(f"rendered_config attributes: {dir(rendered_config)}")
            else:
                logger.debug("rendered_config is None or False")

        # Check rendered content (maps, certificates, files)
        rendered_content = getattr(context, "rendered_content", None) or []
        logger.debug(
            f"rendered_content found: {rendered_content is not None}, length: {len(rendered_content) if rendered_content else 0}"
        )

        if rendered_content:
            available_filenames = []
            for content_item in rendered_content:
                if hasattr(content_item, "filename"):
                    filename = content_item.filename
                    available_filenames.append(filename)
                    logger.debug(f"Found rendered content item: {filename}")

                    if filename == template_name:
                        content = getattr(content_item, "content", "")
                        content_type = getattr(content_item, "content_type", "unknown")
                        logger.debug(
                            f"Match found for {template_name}: type={content_type}, content_length={len(content)}"
                        )

                        return {
                            "result": {
                                "template_name": template_name,
                                "type": content_type,
                                "content": content,
                                "filename": filename,
                            }
                        }
                else:
                    logger.debug(
                        f"Rendered content item missing filename attribute: {dir(content_item)}"
                    )

            logger.debug(f"Available rendered content filenames: {available_filenames}")

        # Debug: List all available rendered templates
        available_rendered = []
        if hasattr(context, "rendered_config") and context.rendered_config:
            available_rendered.append("haproxy.cfg")
        if rendered_content:
            for item in rendered_content:
                if hasattr(item, "filename"):
                    available_rendered.append(item.filename)

        logger.debug(f"Available rendered templates: {available_rendered}")
        return {
            "error": f"Rendered template content not found: {template_name}. Available: {available_rendered}"
        }

    def _handle_version_command(self) -> Dict[str, Any]:
        """Handle version command."""
        try:
            app_version = metadata.version("haproxy-template-ic")
        except Exception:
            app_version = "development"

        return {
            "version": app_version,
            "api_version": "v1",
            "capabilities": [
                "dump_all",
                "dump_indices",
                "dump_config",
                "dump_deployments",
                "dump_debouncer",
                "dump_stats",
                "dump_activity",
                "dump_pods",
                "dump_dashboard",
                "get",
                "get_template_source",
                "get_rendered_template",
                "version",
            ],
            "dashboard_api": {"min_supported": "1.0.0", "recommended": "1.2.0"},
        }

    def _dump_stats(self) -> Dict[str, Any]:
        """Dump dashboard-optimized statistics."""
        try:
            # Start with basic operator info
            stats = {
                "operator": {
                    "status": "RUNNING"
                    if hasattr(self.memo, "config") and self.memo.config
                    else "UNKNOWN",
                    "uptime_seconds": 0,  # Would need startup tracking to implement
                    "version": self._handle_version_command().get("version", "unknown"),
                },
                "resources": {},
                "templates": {},
                "performance": self._get_performance_stats(),
                "sync_stats": self._get_sync_stats(),
            }

            # Extract resource counts from resource metadata
            if hasattr(self.memo, "indices") and self.memo.indices:
                from haproxy_template_ic.operator.k8s_resources import (
                    _collect_resource_indices,
                )

                # Collect normalized resource indices (same method used by operator)
                # This updates the resource_metadata with current statistics
                try:
                    metrics = getattr(self.memo, "metrics", None)
                    _collect_resource_indices(
                        self.memo, metrics
                    )  # Updates resource_metadata
                    resource_counts = {}

                    # Use the populated resource metadata instead of recalculating
                    if (
                        hasattr(self.memo, "resource_metadata")
                        and self.memo.resource_metadata
                    ):
                        for (
                            resource_type,
                            metadata,
                        ) in self.memo.resource_metadata.items():
                            # Only include resource types that have data
                            if metadata.total_count > 0:
                                # Format top 5 namespaces for display
                                top_namespaces = dict(
                                    sorted(
                                        metadata.namespaces.items(),
                                        key=lambda x: x[1],
                                        reverse=True,
                                    )[:5]
                                )
                                resource_counts[resource_type] = metadata.to_dict()
                                # Override namespaces with top 5 for display
                                resource_counts[resource_type]["namespaces"] = (
                                    top_namespaces
                                )

                    stats["resources"] = resource_counts
                except Exception as e:
                    logger.warning(f"Failed to collect resource statistics: {e}")
                    stats["resources"] = {}

            # Extract template stats
            if (
                hasattr(self.memo, "haproxy_config_context")
                and self.memo.haproxy_config_context
            ):
                template_stats = {}
                rendered_content = getattr(
                    self.memo.haproxy_config_context, "rendered_content", []
                )

                # Handle both list and dict formats of rendered_content
                if isinstance(rendered_content, list):
                    for content in rendered_content:
                        if isinstance(content, dict):
                            filename = content.get(
                                "filename", content.get("name", "unknown")
                            )
                            content_data = content.get("content", "")
                            template_stats[filename] = {
                                "name": filename,
                                "type": content.get("content_type", "unknown"),
                                "size": len(content_data),
                                "status": "valid" if content_data else "empty",
                            }
                elif isinstance(rendered_content, dict):
                    # If it's a dict, iterate over values
                    for content in rendered_content.values():
                        if isinstance(content, dict):
                            filename = content.get(
                                "filename", content.get("name", "unknown")
                            )
                            content_data = content.get("content", "")
                            template_stats[filename] = {
                                "name": filename,
                                "type": content.get("content_type", "unknown"),
                                "size": len(content_data),
                                "status": "valid" if content_data else "empty",
                            }

                # Add main haproxy.cfg if it exists
                rendered_config = getattr(
                    self.memo.haproxy_config_context, "rendered_config", None
                )
                if (
                    rendered_config
                    and hasattr(rendered_config, "content")
                    and rendered_config.content
                ):
                    template_stats["haproxy.cfg"] = {
                        "name": "haproxy.cfg",
                        "type": "config",
                        "size": len(rendered_config.content),
                        "status": "valid",
                    }

                # Ensure template_stats only has string keys by filtering out None keys
                filtered_template_stats: Dict[str, Any] = {
                    k: v for k, v in template_stats.items() if k is not None
                }
                stats["templates"] = filtered_template_stats

            # Extract sync stats from deployment history
            deployment_data = self._dump_deployments().get("deployment_history", {})

            success_count = 0
            failure_count = 0
            last_sync_time = None

            for endpoint_data in deployment_data.values():
                if isinstance(endpoint_data, dict):
                    if endpoint_data.get("success"):
                        success_count += 1
                    else:
                        failure_count += 1

                    # Track most recent sync
                    timestamp = endpoint_data.get("timestamp")
                    if timestamp and (not last_sync_time or timestamp > last_sync_time):
                        last_sync_time = timestamp

            stats["sync_stats"] = {
                "success_count": success_count,
                "failure_count": failure_count,
                "last_sync_time": last_sync_time,
            }

            return stats

        except Exception as e:
            return {"error": f"Failed to generate stats: {e}"}

    def _dump_activity(self) -> Dict[str, Any]:
        """Dump recent activity stream."""
        try:
            # Get activity buffer from memo
            if hasattr(self.memo, "activity_buffer") and self.memo.activity_buffer:
                # Get recent events (increased from 50 to 1000 for better history)
                recent_events = self.memo.activity_buffer.get_recent_sync(
                    count=DEFAULT_ACTIVITY_QUERY_LIMIT
                )

                return {
                    "activity": recent_events,
                    "total_events": self.memo.activity_buffer.total_count,
                    "current_count": self.memo.activity_buffer.current_count,
                    "max_size": self.memo.activity_buffer.max_size,
                    "message": f"Retrieved {len(recent_events)} recent activity events",
                }
            else:
                return {"activity": [], "message": "Activity buffer not initialized"}
        except Exception as e:
            logger.error(f"Failed to dump activity: {e}")
            return {"activity": [], "error": f"Failed to retrieve activity data: {e}"}

    def _dump_pods(self) -> Dict[str, Any]:
        """Dump HAProxy pod details with sync status."""
        try:
            pods_info = {"pods": [], "total_count": 0, "ready_count": 0}
            pod_data = []

            # Get ALL discovered HAProxy pods from Kopf index
            if (
                hasattr(self.memo, "indices")
                and HAPROXY_PODS_INDEX in self.memo.indices
            ):
                logger.debug(
                    f"Found HAProxy pod index with {len(self.memo.indices[HAPROXY_PODS_INDEX])} entries"
                )

                # Convert Kopf index to serializable format
                pod_collection = IndexedResourceCollection.from_kopf_index(
                    self.memo.indices[HAPROXY_PODS_INDEX]
                )

                # Extract pod info from each discovered pod
                for (namespace, name), pod_data_dict in pod_collection.items():
                    status = pod_data_dict.get("status", {})
                    metadata = pod_data_dict.get("metadata", {})

                    pod_ip = status.get("podIP", "N/A")
                    pod_phase = status.get("phase", "Unknown")
                    creation_timestamp = metadata.get("creationTimestamp")

                    # Store creation timestamp for PodInfo start_time
                    start_time = creation_timestamp

                    # Create PodInfo object with proper start_time datetime
                    start_time_dt = None
                    if start_time:
                        try:
                            start_time_dt = datetime.fromisoformat(
                                start_time.replace("Z", "+00:00")
                            )
                        except Exception:
                            start_time_dt = None

                    pod_info = PodInfo(
                        name=name,
                        ip=pod_ip,
                        status=pod_phase,
                        start_time=start_time_dt,
                        # Default sync status - will be enhanced below
                        last_sync=None,
                        sync_success=False,
                    )

                    pod_data.append(pod_info)
                    logger.debug(f"Added pod {namespace}/{name} with IP {pod_ip}")

            # Enhance pods with sync status from activity events
            if hasattr(self.memo, "activity_buffer") and self.memo.activity_buffer:
                logger.debug("Enhancing pods with sync status from activity events")
                recent_events = self.memo.activity_buffer.get_recent_sync(
                    count=DEFAULT_ACTIVITY_QUERY_LIMIT
                )

                # Create mapping of pod IP to latest sync status
                pod_sync_status = {}
                for event_data in recent_events:
                    if isinstance(event_data, dict):
                        event_type = event_data.get("type")
                        metadata = event_data.get("metadata", {})

                        # Try to get pod_ip from metadata, or extract from endpoint
                        pod_ip = metadata.get("pod_ip")
                        if not pod_ip:
                            endpoint = metadata.get("endpoint")
                            if endpoint and "://" in endpoint:
                                # Extract IP from endpoint URL like "http://10.244.0.8:5555"
                                pod_ip = endpoint.split("://")[1].split(":")[0]

                        if pod_ip and event_type in [
                            "DEPLOYMENT_SUCCESS",
                            "DEPLOYMENT_FAILED",
                            "SYNC",
                            "RELOAD",
                        ]:
                            # Use the most recent event for each pod IP
                            if pod_ip not in pod_sync_status:
                                is_success = event_type in [
                                    "DEPLOYMENT_SUCCESS",
                                    "SYNC",
                                ]
                                pod_sync_status[pod_ip] = {
                                    "last_sync": event_data.get("timestamp"),
                                    "sync_success": is_success,
                                    "sync_version": metadata.get("version"),
                                    "last_error": None
                                    if is_success
                                    else metadata.get("error"),
                                }

                # Apply sync status to pods
                for pod_info in pod_data:
                    pod_ip = pod_info.ip
                    if pod_ip in pod_sync_status:
                        sync_info = pod_sync_status[pod_ip]
                        # Parse last_sync timestamp if it's a string
                        last_sync = sync_info.get("last_sync")
                        if isinstance(last_sync, str):
                            try:
                                last_sync = datetime.fromisoformat(
                                    last_sync.replace("Z", "+00:00")
                                )
                            except Exception:
                                last_sync = None

                        # Update the PodInfo object with sync status
                        pod_info.last_sync = last_sync
                        pod_info.sync_success = sync_info.get("sync_success", False)
                        logger.debug(
                            f"Enhanced pod {pod_info.name} with sync status: success={sync_info['sync_success']}"
                        )

            # Serialize PodInfo objects to dictionaries for JSON compatibility
            pods_info["pods"] = [pod.model_dump(mode="json") for pod in pod_data]
            pods_info["total_count"] = len(pod_data)
            pods_info["ready_count"] = len([p for p in pod_data if p.sync_success])

            logger.debug(
                f"Returning {len(pod_data)} pods, {pods_info['ready_count']} synced"
            )
            return pods_info

        except Exception as e:
            logger.error(f"Failed to generate pod info: {e}", exc_info=True)
            return {"error": f"Failed to generate pod info: {e}"}

    def _dump_dashboard(self) -> Dict[str, Any]:
        """Dump all dashboard data in optimized format."""
        try:
            # Combine all dashboard-relevant data
            dashboard_data: Dict[str, Any] = {
                "operator": {},
                "pods": [],
                "resources": {},
                "templates": {},
                "performance": {},
                "activity": [],
                "errors": [],
            }

            # Get stats data
            stats = self._dump_stats()
            if "error" not in stats:
                dashboard_data["operator"] = stats.get("operator", {})
                dashboard_data["resources"] = stats.get("resources", {})
                dashboard_data["templates"] = stats.get("templates", {})
                dashboard_data["performance"] = stats.get("performance", {})

                # Enhance operator info with additional details
                operator_data = dashboard_data["operator"]
                # Try to get namespace from various sources
                namespace = "unknown"
                if hasattr(self.memo, "namespace") and self.memo.namespace:
                    namespace = self.memo.namespace
                elif (
                    hasattr(self.memo, "config")
                    and self.memo.config
                    and hasattr(self.memo.config, "namespace")
                ):
                    namespace = self.memo.config.namespace
                else:
                    # Try to detect from environment or use service account namespace
                    namespace = os.environ.get("POD_NAMESPACE") or "unknown"
                    if namespace == "unknown":
                        try:
                            # Read namespace from service account token
                            with open(
                                "/var/run/secrets/kubernetes.io/serviceaccount/namespace",
                                "r",
                            ) as f:
                                namespace = f.read().strip()
                        except Exception:
                            namespace = "unknown"

                operator_data["namespace"] = namespace
                operator_data["configmap_name"] = (
                    getattr(self.memo.cli_options, "configmap_name", "unknown")
                    if hasattr(self.memo, "cli_options") and self.memo.cli_options
                    else "unknown"
                )

                # Add timing information for dashboard title bar
                try:
                    # Get pod start time from Kubernetes
                    pod_name = os.environ.get(
                        "HOSTNAME"
                    )  # Pod name is the hostname in Kubernetes
                    if pod_name:
                        operator_data["controller_pod_name"] = pod_name

                        # Try to get pod start time
                        try:
                            # Use kr8s to get pod start time

                            pod = Pod.get(pod_name, namespace=namespace)
                            if pod and pod.status and pod.status.get("startTime"):
                                operator_data["controller_pod_start_time"] = pod.status[
                                    "startTime"
                                ]
                        except Exception as e:
                            # Silently continue if pod info unavailable
                            logger.debug(
                                f"Non-critical error fetching controller pod info: {e}"
                            )

                    # Get last deployment time from deployment history
                    try:
                        deployments_data = self._dump_deployments()
                        if "deployment_history" in deployments_data:
                            most_recent_timestamp = None
                            for endpoint, deployment_info in deployments_data[
                                "deployment_history"
                            ].items():
                                if deployment_info.get("success"):
                                    timestamp = deployment_info.get("timestamp")
                                    if timestamp and (
                                        not most_recent_timestamp
                                        or timestamp > most_recent_timestamp
                                    ):
                                        most_recent_timestamp = timestamp

                            if most_recent_timestamp:
                                operator_data["last_deployment_time"] = (
                                    most_recent_timestamp
                                )
                    except Exception as e:
                        # Silently continue if deployment history unavailable
                        logger.debug(
                            f"Non-critical error fetching deployment history: {e}"
                        )

                except Exception as e:
                    # Silently continue if timing info unavailable
                    logger.debug(f"Non-critical error fetching timing info: {e}")

            # Get pod data
            pods = self._dump_pods()
            if "error" not in pods:
                dashboard_data["pods"] = pods.get("pods", [])

            # Get activity data
            activity = self._dump_activity()
            if "error" not in activity:
                dashboard_data["activity"] = activity.get("activity", [])

            # Get config data (includes both actual config and rendered context)
            config_data = self._dump_config()
            if "error" not in config_data:
                dashboard_data.update(
                    config_data
                )  # This adds both "config" and "haproxy_config_context"

            # Add metadata
            dashboard_data["metadata"] = {
                "generated_at": __import__("datetime")
                .datetime.now(__import__("datetime").timezone.utc)
                .isoformat(),
                "version": self._handle_version_command().get("version", "unknown"),
            }

            return dashboard_data

        except Exception as e:
            return {"error": f"Failed to generate dashboard data: {e}"}

    def _get_performance_stats(self) -> Dict[str, Any]:
        """Get performance statistics for the dashboard."""
        try:
            performance = get_performance_metrics()

            # Calculate sync success rate from sync_stats
            sync_stats = self._get_sync_stats()
            success_count = sync_stats.get("success_count", 0)
            failure_count = sync_stats.get("failure_count", 0)
            total_syncs = success_count + failure_count

            if total_syncs > 0:
                success_rate = success_count / total_syncs
                performance["sync_success_rate"] = success_rate
            elif success_count > 0:
                # If we have successful syncs but no recorded failures, assume 100% success
                performance["sync_success_rate"] = 1.0

            return performance
        except Exception as e:
            logger.debug(f"Error getting performance stats: {e}")
            return {}

    def _get_sync_stats(self) -> Dict[str, Any]:
        """Get synchronization statistics from deployment history."""
        sync_stats = {"success_count": 0, "failure_count": 0, "last_sync_time": None}

        try:
            # Get sync stats from deployment history
            history = self._dump_deployments().get("deployment_history", {})
            success_count = 0
            failure_count = 0
            latest_time = None

            for endpoint_history in history.values():
                if isinstance(endpoint_history, dict):
                    if endpoint_history.get("success"):
                        success_count += 1
                    else:
                        failure_count += 1

                    timestamp = endpoint_history.get("timestamp")
                    if timestamp and (not latest_time or timestamp > latest_time):
                        latest_time = timestamp

            sync_stats.update(
                {
                    "success_count": success_count,
                    "failure_count": failure_count,
                    "last_sync_time": latest_time,
                }
            )

        except Exception as e:
            logger.debug(f"Error getting sync stats: {e}")

        return sync_stats

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

            # Remove existing socket file if it exists
            if self.socket_path.exists():
                self.socket_path.unlink()

            # Start the Unix server
            self.server = await asyncio.start_unix_server(
                self._handle_client,
                path=str(self.socket_path),
                limit=SOCKET_BUFFER_SIZE,
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
            self.logger.error(
                f"❌ Management socket server (path {self.socket_path}) error: {e}"
            )

            logger.error(traceback.format_exc())
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
            command_data = await reader.read(SOCKET_BUFFER_SIZE)
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
