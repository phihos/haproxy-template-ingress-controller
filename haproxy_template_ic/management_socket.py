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

from haproxy_template_ic.constants import SOCKET_BUFFER_SIZE
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
    # Check if it's a dict-like object (not just iterable like strings)
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
            # Convert tuple keys to structured strings with ':' separator
            # e.g., ('namespace', 'name') becomes 'namespace:name'
            if isinstance(key, tuple):
                serialized_key = ":".join(str(k) for k in key)
            else:
                serialized_key = str(key)
            serialized_index[serialized_key] = _serialize_resource_collection(resources)
    except (TypeError, KeyError):
        # Handle cases where index_data doesn't behave like a dict
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

    # Serialize CLI options (bootstrap parameters only)
    try:
        if hasattr(memo, "cli_options") and memo.cli_options:
            state["cli_options"] = {
                "configmap_name": memo.cli_options.configmap_name,
                "secret_name": memo.cli_options.secret_name,
            }
        else:
            state["cli_options"] = {}
    except (AttributeError, TypeError) as e:
        errors.append(f"cli_options serialization: {e}")
        state["cli_options"] = {}

    # Serialize operator configuration (runtime settings)
    try:
        if hasattr(memo, "config") and memo.config:
            state["operator_config"] = {
                "healthz_port": memo.config.operator.healthz_port,
                "metrics_port": memo.config.operator.metrics_port,
                "socket_path": memo.config.operator.socket_path,
                "verbose": memo.config.logging.verbose,
                "structured_logging": memo.config.logging.structured,
                "tracing_enabled": memo.config.tracing.enabled,
                "validation_dataplane_host": memo.config.validation.dataplane_host,
                "validation_dataplane_port": memo.config.validation.dataplane_port,
            }
        else:
            state["operator_config"] = {}
    except (AttributeError, TypeError) as e:
        errors.append(f"operator_config serialization: {e}")
        state["operator_config"] = {}

    # Serialize indices with specific error handling
    try:
        indices, index_errors = _serialize_memo_indices(memo)
        state["indices"] = indices
        errors.extend(index_errors)
    except (AttributeError, TypeError) as e:
        errors.append(f"indices serialization: {e}")
        state["indices"] = {}

    # Serialize debouncer stats with specific error handling
    try:
        if hasattr(memo, "debouncer") and memo.debouncer:
            state["debouncer"] = memo.debouncer.get_stats()
        else:
            state["debouncer"] = None
    except (AttributeError, TypeError) as e:
        errors.append(f"debouncer serialization: {e}")
        state["debouncer"] = None

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

        # Also check for old-style _index attributes for backward compatibility
        for name in dir(self.memo):
            if (
                name.endswith("_index")
                and not name.startswith("_")
                and hasattr(getattr(self.memo, name), "items")
            ):
                if name not in indices:  # Don't override new-style indices
                    try:
                        indices[name] = dict(getattr(self.memo, name))
                    except Exception as e:
                        indices[name] = {"error": f"Failed to serialize: {e}"}

        return {"indices": indices}

    def _dump_config(self) -> Dict[str, Any]:
        """Dump HAProxy configuration context."""
        if (
            hasattr(self.memo, "haproxy_config_context")
            and self.memo.haproxy_config_context
        ):
            context_dict = self.memo.haproxy_config_context.model_dump(mode="json")
            # Add convenience properties for backward compatibility
            rendered_content = context_dict.get("rendered_content", [])
            context_dict["rendered_maps"] = [
                c for c in rendered_content if c.get("content_type") == "map"
            ]
            context_dict["rendered_certificates"] = [
                c for c in rendered_content if c.get("content_type") == "certificate"
            ]
            context_dict["rendered_files"] = [
                c for c in rendered_content if c.get("content_type") == "file"
            ]
            return {"haproxy_config_context": context_dict}
        return {
            "haproxy_config_context": {
                "rendered_content": [],
                "rendered_maps": [],
                "rendered_certificates": [],
                "rendered_files": [],
                "rendered_config": None,
            }
        }

    def _dump_deployments(self) -> Dict[str, Any]:
        """Dump all deployment history."""
        if hasattr(self.memo, "deployment_history") and self.memo.deployment_history:
            return self.memo.deployment_history.to_dict()
        return {"deployment_history": {}}

    def _dump_debouncer(self) -> Dict[str, Any]:
        """Dump template debouncer statistics."""
        if hasattr(self.memo, "debouncer") and self.memo.debouncer:
            return {"debouncer": self.memo.debouncer.get_stats()}
        return {"debouncer": None}

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

    def _get_template_source(self, template_name: str) -> Dict[str, Any]:
        """Get the source template content (Jinja2) for a given template."""
        logger.debug(f"Getting template source for: {template_name}")

        if not hasattr(self.memo, "config") or not self.memo.config:
            logger.debug("Configuration not available in memo")
            return {"error": "Configuration not available"}

        # Check different template sources
        template_sources = []

        # Maps
        if template_name in self.memo.config.maps:
            map_template = self.memo.config.maps[template_name]
            logger.debug(
                f"Found map template for {template_name}, type: {type(map_template)}"
            )
            try:
                source = (
                    map_template.template
                    if hasattr(map_template, "template")
                    else str(map_template)
                )
                template_sources.append(
                    {"type": "map", "source": source, "filename": template_name}
                )
                logger.debug(
                    f"Successfully extracted map template source for {template_name}: {len(source)} chars"
                )
            except Exception as e:
                logger.error(
                    f"Failed to extract map template source for {template_name}: {e}"
                )

        # Files
        if template_name in self.memo.config.files:
            file_template = self.memo.config.files[template_name]
            logger.debug(
                f"Found file template for {template_name}, type: {type(file_template)}"
            )
            try:
                source = (
                    file_template.template
                    if hasattr(file_template, "template")
                    else str(file_template)
                )
                template_sources.append(
                    {"type": "file", "source": source, "filename": template_name}
                )
                logger.debug(
                    f"Successfully extracted file template source for {template_name}: {len(source)} chars"
                )
            except Exception as e:
                logger.error(
                    f"Failed to extract file template source for {template_name}: {e}"
                )

        # Certificates
        if template_name in self.memo.config.certificates:
            cert_template = self.memo.config.certificates[template_name]
            logger.debug(
                f"Found certificate template for {template_name}, type: {type(cert_template)}"
            )
            try:
                source = (
                    cert_template.template
                    if hasattr(cert_template, "template")
                    else str(cert_template)
                )
                template_sources.append(
                    {"type": "certificate", "source": source, "filename": template_name}
                )
                logger.debug(
                    f"Successfully extracted certificate template source for {template_name}: {len(source)} chars"
                )
            except Exception as e:
                logger.error(
                    f"Failed to extract certificate template source for {template_name}: {e}"
                )

        # Template snippets
        if template_name in self.memo.config.template_snippets:
            snippet_template = self.memo.config.template_snippets[template_name]
            logger.debug(
                f"Found snippet template for {template_name}, type: {type(snippet_template)}"
            )
            try:
                source = (
                    snippet_template.template
                    if hasattr(snippet_template, "template")
                    else str(snippet_template)
                )
                template_sources.append(
                    {"type": "snippet", "source": source, "filename": template_name}
                )
                logger.debug(
                    f"Successfully extracted snippet template source for {template_name}: {len(source)} chars"
                )
            except Exception as e:
                logger.error(
                    f"Failed to extract snippet template source for {template_name}: {e}"
                )

        # HAProxy config template
        if template_name == "haproxy.cfg":
            if hasattr(self.memo.config, "haproxy_config"):
                config_template = self.memo.config.haproxy_config
                logger.debug(
                    f"Found haproxy_config template, type: {type(config_template)}"
                )
                logger.debug(
                    f"haproxy_config has template attribute: {hasattr(config_template, 'template')}"
                )

                try:
                    if hasattr(config_template, "template"):
                        source = config_template.template
                        logger.debug(
                            f"Extracted template attribute, type: {type(source)}, length: {len(source) if isinstance(source, str) else 'N/A'}"
                        )
                    else:
                        source = str(config_template)
                        logger.debug(f"Used str() fallback, length: {len(source)}")

                    template_sources.append(
                        {"type": "config", "source": source, "filename": "haproxy.cfg"}
                    )
                    logger.debug(
                        f"Successfully added haproxy.cfg template source: {len(source)} chars"
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
        """Handle version command for compatibility checking."""
        try:
            from importlib import metadata

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
            if (
                hasattr(self.memo, "deployment_history")
                and self.memo.deployment_history
            ):
                history_dict = self.memo.deployment_history.to_dict()
                deployment_data = history_dict.get("deployment_history", {})

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
                        if timestamp and (
                            not last_sync_time or timestamp > last_sync_time
                        ):
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
                recent_events = self.memo.activity_buffer.get_recent_sync(count=1000)

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

            # This would typically get pod information from Kubernetes
            # For now, we can only provide what's available from deployment history
            if (
                hasattr(self.memo, "deployment_history")
                and self.memo.deployment_history
            ):
                history_dict = self.memo.deployment_history.to_dict()
                deployment_data = history_dict.get("deployment_history", {})

                pod_data = []
                for endpoint, data in deployment_data.items():
                    if isinstance(data, dict):
                        # Extract IP from endpoint URL if possible
                        pod_ip = (
                            endpoint.split("://")[1].split(":")[0]
                            if "://" in endpoint
                            else endpoint
                        )

                        pod_data.append(
                            {
                                "name": f"haproxy-{pod_ip.replace('.', '-')}",
                                "ip": pod_ip,
                                "endpoint": endpoint,
                                "last_sync": data.get("timestamp"),
                                "sync_success": data.get("success", False),
                                "sync_version": data.get("version"),
                                "last_error": data.get("error"),
                            }
                        )

                pods_info["pods"] = pod_data
                pods_info["total_count"] = len(pod_data)
                pods_info["ready_count"] = len(
                    [p for p in pod_data if p["sync_success"]]
                )

            return pods_info

        except Exception as e:
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
                    import os

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
                    import os

                    pod_name = os.environ.get(
                        "HOSTNAME"
                    )  # Pod name is the hostname in Kubernetes
                    if pod_name:
                        operator_data["controller_pod_name"] = pod_name

                        # Try to get pod start time
                        try:
                            # Use kr8s to get pod start time
                            from kr8s.objects import Pod

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
            from haproxy_template_ic.metrics import get_performance_metrics

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
        """Get synchronization statistics."""
        sync_stats = {"success_count": 0, "failure_count": 0, "last_sync_time": None}

        try:
            # Try to get sync stats from deployment history
            if (
                hasattr(self.memo, "dataplane_deployment_history")
                and self.memo.dataplane_deployment_history
            ):
                history = self.memo.dataplane_deployment_history
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
            import traceback

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
