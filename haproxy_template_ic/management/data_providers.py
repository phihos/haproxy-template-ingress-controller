"""
Data providers for management socket interface.

This module provides data extraction and dumping capabilities for the
management socket server, allowing external tools to query the operator's
internal state.
"""

import logging
from datetime import datetime
from importlib import metadata
from typing import Any, Dict, List, Optional


from haproxy_template_ic.constants import (
    HAPROXY_PODS_INDEX,
    DEFAULT_ACTIVITY_QUERY_LIMIT,
)
from haproxy_template_ic.core.error_handling import handle_exceptions, safe_operation
from haproxy_template_ic.deployment_state import DeploymentStateTracker
from haproxy_template_ic.metrics import get_performance_metrics
from haproxy_template_ic.management.serializers import _serialize_kopf_index
from haproxy_template_ic.models import IndexedResourceCollection
from haproxy_template_ic.core.validation import has_valid_attr, has_valid_nested_attr
from haproxy_template_ic.tui.models import PodInfo

logger = logging.getLogger(__name__)


class DataProvider:
    """Provides data extraction and dumping capabilities for management socket."""

    def __init__(self, memo: Any):
        """Initialize data provider with memo object.

        Args:
            memo: Kopf memo object containing operator state
        """
        self.memo = memo

    def dump_indices(self) -> Dict[str, Any]:
        """Dump all indices from memo."""
        indices: Dict[str, Any] = {}

        if has_valid_attr(self.memo, "indices"):
            for name, index_data in self.memo.indices.items():

                @safe_operation("index serialization", logger)
                def serialize_index():
                    return _serialize_kopf_index(index_data)

                result = serialize_index()
                indices[name] = (
                    result if result is not None else {"error": "Failed to serialize"}
                )

        return {"indices": indices}

    def dump_config(self) -> Dict[str, Any]:
        """Dump HAProxy configuration context and config."""
        result = {}

        if has_valid_attr(self.memo, "config"):
            config_dict = self.memo.config.model_dump(mode="json")
            result["config"] = config_dict
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

    @handle_exceptions(
        default_return={"error": "Failed to get deployment history"},
        context="deployment_history",
    )
    def dump_deployments(self) -> Dict[str, Any]:
        """Dump all deployment history using DeploymentStateTracker."""
        if has_valid_attr(self.memo, "activity_buffer"):
            tracker = DeploymentStateTracker(self.memo.activity_buffer)
            # Use the synchronous version to avoid async complications
            return tracker.to_dict_sync()

        return {"deployment_history": {}}

    def dump_debouncer(self) -> Dict[str, Any]:
        """Dump template debouncer statistics."""
        if has_valid_attr(self.memo, "debouncer"):
            return {"debouncer": self.memo.debouncer.get_stats()}
        return {"debouncer": None}

    def dump_stats(self) -> Dict[str, Any]:
        """Dump dashboard-optimized statistics."""
        try:
            stats = {
                "operator": {
                    "status": "RUNNING"
                    if hasattr(self.memo, "config") and self.memo.config
                    else "UNKNOWN",
                    "config_loaded": hasattr(self.memo, "config")
                    and self.memo.config is not None,
                    "namespace": self._get_namespace(),
                }
            }

            self._enhance_operator_data(stats["operator"])

            pods_info = self.dump_pods()
            stats["pods"] = {
                "total": pods_info.get("total_count", 0),
                "ready": pods_info.get("ready_count", 0),
            }

            if has_valid_nested_attr(self.memo, "config", "watched_resources"):
                resource_counts: Dict[str, str] = {}
                for resource_type in self.memo.config.watched_resources:
                    count = 0
                    if (
                        hasattr(self.memo, "indices")
                        and resource_type in self.memo.indices
                        and self.memo.indices[resource_type]
                    ):
                        count = len(self.memo.indices[resource_type])
                    resource_counts[resource_type] = str(count)
                # Cast to ensure type compatibility
                stats["resources"] = dict(resource_counts)

            stats["performance"] = self._get_performance_stats()

            return stats

        except Exception as e:
            logger.exception("Failed to generate stats")
            return {"error": f"Failed to generate stats: {str(e)}"}

    def dump_activity(self) -> Dict[str, Any]:
        """Dump recent activity stream."""
        try:
            if has_valid_attr(self.memo, "activity_buffer"):
                recent_events = self.memo.activity_buffer.get_recent_sync(
                    count=DEFAULT_ACTIVITY_QUERY_LIMIT
                )
                return {"activity": recent_events}
            else:
                return {"activity": []}
        except Exception as e:
            logger.exception("Failed to get activity stream")
            return {"error": f"Failed to get activity stream: {str(e)}"}

    def dump_pods(self) -> Dict[str, Any]:
        """Dump HAProxy pod details with sync status."""
        try:
            pods_info = {"pods": [], "total_count": 0, "ready_count": 0}
            pod_data = []

            if (
                hasattr(self.memo, "indices")
                and HAPROXY_PODS_INDEX in self.memo.indices
            ):
                # Convert kopf index to IndexedResourceCollection for proper handling
                pods_collection = IndexedResourceCollection.from_kopf_index(
                    self.memo.indices[HAPROXY_PODS_INDEX]
                )
                logger.debug(
                    f"Found HAProxy pods collection with {len(pods_collection)} entries"
                )

                # Get deployment history for sync status enhancement
                deployment_history = {}
                if has_valid_attr(self.memo, "activity_buffer"):
                    tracker = DeploymentStateTracker(self.memo.activity_buffer)
                    deployment_data = tracker.to_dict_sync()
                    deployment_history = deployment_data.get("deployment_history", {})

                # Iterate over the collection properly
                for pod_key, pod_resource in pods_collection.items():
                    try:
                        pod_dict = self._process_pod_resource(pod_resource)

                        # Enhance with sync status from deployment history
                        pod_ip = pod_dict.get("ip", "N/A")
                        if pod_ip != "N/A":
                            self._enhance_pod_with_sync_status(
                                pod_dict, pod_ip, deployment_history
                            )

                        pod_data.append(pod_dict)
                    except Exception as e:
                        logger.warning(f"Failed to process pod at key {pod_key}: {e}")
                        continue
            else:
                # Add diagnostic information for empty pod index
                if not hasattr(self.memo, "indices"):
                    logger.debug(
                        "No indices available in memo - operator may be initializing"
                    )
                elif HAPROXY_PODS_INDEX not in self.memo.indices:
                    logger.debug(
                        f"HAProxy pods index '{HAPROXY_PODS_INDEX}' not found in indices"
                    )
                    if hasattr(self.memo, "config") and hasattr(
                        self.memo.config, "pod_selector"
                    ):
                        pod_selector = self.memo.config.pod_selector.match_labels
                        logger.debug(
                            f"Pod selector: {pod_selector}. Ensure HAProxy pods have matching labels and are in Running state"
                        )
                    else:
                        logger.debug("No pod_selector configuration found")

            pods_info["pods"] = pod_data
            pods_info["total_count"] = len(pod_data)
            pods_info["ready_count"] = sum(
                1
                for pod in pod_data
                if pod.get("sync_success", False)  # Use sync_success instead of ready
            )

            # Log summary for troubleshooting
            if len(pod_data) == 0:
                logger.debug(
                    "No HAProxy pods found - check that pods exist with correct labels and are Running"
                )
            else:
                logger.debug(
                    f"Found {len(pod_data)} HAProxy pods, {pods_info['ready_count']} synced"
                )

            return pods_info

        except Exception as e:
            logger.exception("Failed to get pods information")
            return {
                "error": f"Failed to get pods information: {str(e)}",
                "pods": [],
                "total_count": 0,
                "ready_count": 0,
            }

    def dump_dashboard(self) -> Dict[str, Any]:
        """Dump all dashboard data in optimized format."""
        try:
            dashboard_data: Dict[str, Any] = {
                "operator": {},
                "pods": [],
                "resources": {},
                "activity": [],
                "performance": {},
                "timestamp": datetime.now().isoformat(),
            }

            if has_valid_attr(self.memo, "config"):
                dashboard_data["operator"] = {
                    "status": "RUNNING",
                    "config_loaded": True,
                    "namespace": self._get_namespace(),
                }
                self._enhance_operator_data(dashboard_data["operator"])
            else:
                dashboard_data["operator"] = {
                    "status": "INITIALIZING",
                    "config_loaded": False,
                    "namespace": "unknown",
                }

            # Add config and haproxy_config_context data for TUI template extraction
            config_data = self.dump_config()
            dashboard_data["config"] = config_data.get("config", {})
            dashboard_data["haproxy_config_context"] = config_data.get(
                "haproxy_config_context", {}
            )

            pods_info = self.dump_pods()
            dashboard_data["pods"] = pods_info.get("pods", [])

            if has_valid_nested_attr(self.memo, "config", "watched_resources"):
                from haproxy_template_ic.metrics import get_metrics_collector

                metrics = get_metrics_collector()
                # Import locally to avoid circular imports
                from haproxy_template_ic.operator.k8s_resources import (
                    _collect_resource_indices,
                )

                resource_indices = _collect_resource_indices(self.memo, metrics)

                dashboard_data["resources"] = {}
                for resource_type, collection in resource_indices.items():
                    # Use 'total' instead of 'count' to match TUI expectations
                    resource_data = {
                        "total": len(collection),
                        "items": list(collection.items())[:10],
                    }

                    # Add memory_size if available
                    if hasattr(collection, "get_memory_size"):
                        try:
                            resource_data["memory_size"] = collection.get_memory_size()
                        except Exception as e:
                            logger.debug(
                                f"Failed to get memory size for {resource_type}: {e}"
                            )
                            resource_data["memory_size"] = 0
                    else:
                        resource_data["memory_size"] = 0

                    dashboard_data["resources"][resource_type] = resource_data

            activity_data = self.dump_activity()
            dashboard_data["activity"] = activity_data.get("activity", [])

            dashboard_data["performance"] = self._get_performance_stats()

            # Add deployment history for template timestamps
            deployment_data = self.dump_deployments()
            dashboard_data["deployment_history"] = deployment_data.get(
                "deployment_history", {}
            )

            return dashboard_data

        except Exception as e:
            logger.exception("Failed to generate dashboard data")
            return {
                "error": f"Failed to generate dashboard data: {str(e)}",
                "operator": {"status": "ERROR", "config_loaded": False},
                "pods": [],
                "resources": {},
                "activity": [],
                "performance": {},
                "timestamp": datetime.now().isoformat(),
            }

    def dump_all(self, metrics: Any) -> Dict[str, Any]:
        """Dump all available data."""
        return {
            "indices": self.dump_indices(),
            "config": self.dump_config(),
            "deployments": self.dump_deployments(),
            "debouncer": self.dump_debouncer(),
            "stats": self.dump_stats(),
            "activity": self.dump_activity(),
            "pods": self.dump_pods(),
            "dashboard": self.dump_dashboard(),
        }

    def get_deployment_history(self, endpoint_url: str) -> Dict[str, Any]:
        """Get deployment history for a specific endpoint from activity events."""
        # Get all deployment history
        deployment_data = self.dump_deployments().get("deployment_history", {})

        if endpoint_url in deployment_data:
            return {"result": deployment_data[endpoint_url]}
        else:
            return {
                "error": f"No deployment history found for endpoint: {endpoint_url}",
                "available_endpoints": list(deployment_data.keys()),
            }

    @safe_operation("template extraction")
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
            source = (
                template_obj.template
                if hasattr(template_obj, "template")
                else str(template_obj)
            )
            template_sources.append(
                {
                    "type": collection_type,
                    "name": template_name,
                    "source": source,
                }
            )

    @safe_operation("HAProxy config template extraction")
    def _extract_haproxy_config_template(
        self, template_sources: List[Dict[str, Any]]
    ) -> None:
        """Extract HAProxy config template source."""
        config_template = self.memo.config.haproxy_config
        source = (
            config_template.template
            if hasattr(config_template, "template")
            else str(config_template)
        )
        template_sources.append(
            {
                "type": "haproxy_config",
                "name": "haproxy_config",
                "source": source,
            }
        )

    def get_template_source(self, template_name: str) -> Dict[str, Any]:
        """Get the source template content (Jinja2) for a given template."""
        logger.debug(f"Getting template source for: {template_name}")

        if not hasattr(self.memo, "config") or not self.memo.config:
            logger.debug("Configuration not available in memo")
            return {"error": "Configuration not available"}

        # Parse template identifier (type:name or just name)
        if ":" in template_name:
            template_type, name = template_name.split(":", 1)
        else:
            template_type = "auto"
            name = template_name

        template_sources: List[Dict[str, Any]] = []

        try:
            if template_type == "map" or (
                template_type == "auto" and template_name == "maps"
            ):
                # Get map template
                if has_valid_attr(self.memo.config, "maps"):
                    if template_type == "map":
                        self._extract_template_from_collection(
                            self.memo.config.maps, "map", name, template_sources
                        )
                    else:
                        for map_name in self.memo.config.maps:
                            self._extract_template_from_collection(
                                self.memo.config.maps, "map", map_name, template_sources
                            )

            elif template_type == "snippet" or (
                template_type == "auto" and template_name == "template_snippets"
            ):
                # Get template snippet
                if has_valid_attr(self.memo.config, "template_snippets"):
                    if template_type == "snippet":
                        self._extract_template_from_collection(
                            self.memo.config.template_snippets,
                            "snippet",
                            name,
                            template_sources,
                        )
                    else:
                        for snippet_name in self.memo.config.template_snippets:
                            self._extract_template_from_collection(
                                self.memo.config.template_snippets,
                                "snippet",
                                snippet_name,
                                template_sources,
                            )

            elif template_type == "cert" or (
                template_type == "auto" and template_name == "certificates"
            ):
                # Get certificate template
                if has_valid_attr(self.memo.config, "certificates"):
                    if template_type == "cert":
                        self._extract_template_from_collection(
                            self.memo.config.certificates,
                            "certificate",
                            name,
                            template_sources,
                        )
                    else:
                        for cert_name in self.memo.config.certificates:
                            self._extract_template_from_collection(
                                self.memo.config.certificates,
                                "certificate",
                                cert_name,
                                template_sources,
                            )

            elif template_name == "haproxy_config":
                # Get HAProxy config template
                if has_valid_attr(self.memo.config, "haproxy_config"):
                    self._extract_haproxy_config_template(template_sources)

            if not template_sources:
                return {"error": f"Template '{template_name}' not found"}

            if len(template_sources) == 1:
                return {"template_source": template_sources[0]}
            else:
                return {"template_sources": template_sources}

        except Exception as e:
            logger.exception(f"Error getting template source for '{template_name}'")
            return {"error": f"Failed to get template source: {str(e)}"}

    def get_rendered_template(self, template_name: str) -> Dict[str, Any]:
        """Get the rendered content for a given template."""
        logger.debug(f"Getting rendered template for: {template_name}")

        if (
            not hasattr(self.memo, "haproxy_config_context")
            or not self.memo.haproxy_config_context
        ):
            return {"error": "Template rendering context not available"}

        context = self.memo.haproxy_config_context

        # Parse template identifier
        if ":" in template_name:
            template_type, name = template_name.split(":", 1)
        else:
            template_type = "auto"
            name = template_name

        try:
            if template_type == "map" or (
                template_type == "auto" and hasattr(context, "rendered_content")
            ):
                # Get rendered map content
                for content_item in context.rendered_content:
                    if content_item.content_type == "map" and (
                        template_type == "auto" or content_item.name == name
                    ):
                        return {
                            "rendered_content": {
                                "type": "map",
                                "name": content_item.name,
                                "content": content_item.content,
                                "size": len(content_item.content),
                            }
                        }

            elif template_name == "haproxy_config":
                # Get rendered HAProxy config
                if has_valid_attr(context, "rendered_config"):
                    return {
                        "rendered_content": {
                            "type": "haproxy_config",
                            "name": "haproxy_config",
                            "content": context.rendered_config,
                            "size": len(context.rendered_config),
                        }
                    }

            return {"error": f"Rendered template '{template_name}' not found"}

        except Exception as e:
            logger.exception(f"Error getting rendered template for '{template_name}'")
            return {"error": f"Failed to get rendered template: {str(e)}"}

    def get_version_info(self) -> Dict[str, Any]:
        """Get version information."""
        try:
            version = metadata.version("haproxy-template-ic")
        except metadata.PackageNotFoundError:
            version = "development"

        return {
            "version": {
                "haproxy_template_ic": version,
                "timestamp": datetime.now().isoformat(),
            }
        }

    def _get_namespace(self) -> str:
        """Get the current namespace from various sources."""
        if hasattr(self.memo, "namespace") and self.memo.namespace:
            return self.memo.namespace
        elif (
            hasattr(self.memo, "config")
            and self.memo.config
            and hasattr(self.memo.config, "namespace")
            and self.memo.config.namespace
        ):
            return self.memo.config.namespace
        elif hasattr(self.memo, "cli_options") and hasattr(
            self.memo.cli_options, "namespace"
        ):
            return self.memo.cli_options.namespace or "default"
        else:
            return "unknown"

    def _enhance_operator_data(self, operator_data: Dict[str, Any]) -> None:
        """Enhance operator data with additional details."""
        namespace = self._get_namespace()
        operator_data["namespace"] = namespace
        operator_data["configmap_name"] = (
            getattr(self.memo.cli_options, "configmap_name", "unknown")
            if hasattr(self.memo, "cli_options") and self.memo.cli_options
            else "unknown"
        )

        if has_valid_attr(self.memo, "config"):
            operator_data["watched_resources"] = list(
                self.memo.config.watched_resources.keys()
            )
            operator_data["has_pod_selector"] = bool(self.memo.config.pod_selector)

    def _get_performance_stats(self) -> Dict[str, Any]:
        """Get performance statistics for the dashboard."""
        try:
            performance = get_performance_metrics()

            # Calculate sync success rate from sync_stats
            sync_stats = self._get_sync_stats()
            total_syncs = sync_stats["success_count"] + sync_stats["failure_count"]
            success_rate = (
                (sync_stats["success_count"] / total_syncs * 100)
                if total_syncs > 0
                else 100.0
            )

            return {
                "sync_success_rate": round(success_rate, 1),
                "total_syncs": total_syncs,
                "last_sync": sync_stats.get("last_sync_time"),
                **performance,
            }
        except Exception as e:
            logger.exception("Failed to get performance stats")
            return {"error": f"Failed to get performance stats: {str(e)}"}

    def _get_sync_stats(self) -> Dict[str, Any]:
        """Get synchronization statistics from deployment history."""
        sync_stats: Dict[str, Any] = {
            "success_count": 0,
            "failure_count": 0,
            "last_sync_time": None,
        }

        try:
            # Get sync stats from deployment history
            history = self.dump_deployments().get("deployment_history", {})
            most_recent_time = None

            for endpoint, info in history.items():
                if info.get("success"):
                    sync_stats["success_count"] = (
                        sync_stats.get("success_count", 0) or 0
                    ) + 1
                else:
                    sync_stats["failure_count"] = (
                        sync_stats.get("failure_count", 0) or 0
                    ) + 1

                # Track most recent sync time
                timestamp_str = info.get("timestamp")
                if timestamp_str:
                    try:
                        timestamp = datetime.fromisoformat(
                            timestamp_str.replace("Z", "+00:00")
                        )
                        if most_recent_time is None or timestamp > most_recent_time:
                            most_recent_time = timestamp
                    except (ValueError, AttributeError):
                        pass

            # Set last_sync_time as string or None
            last_sync_time: Optional[str] = None
            if most_recent_time:
                last_sync_time = most_recent_time.isoformat()
            sync_stats["last_sync_time"] = last_sync_time

        except Exception:
            logger.exception("Failed to calculate sync stats")

        return sync_stats

    def _process_pod_resource(self, pod_resource: Dict[str, Any]) -> Dict[str, Any]:
        """Process a pod resource and return PodInfo-compatible data."""
        try:
            # Extract pod information from Kubernetes resource
            metadata = pod_resource.get("metadata", {})
            status = pod_resource.get("status", {})

            # Create PodInfo instance with proper field mapping
            pod_info = PodInfo(
                name=metadata.get("name", "unknown"),
                status=status.get("phase", "Unknown"),
                ip=status.get("podIP", "N/A"),
                start_time=metadata.get(
                    "creationTimestamp"
                ),  # Maps to start_time for uptime calculation
                sync_success=False,  # Default, will be updated from deployment history
                last_sync=None,  # Will be updated from deployment history
            )

            # Return as dict for serialization
            return pod_info.model_dump()

        except Exception as e:
            logger.warning(f"Failed to process pod resource: {e}")
            # Return minimal valid PodInfo data on error
            pod_info = PodInfo(
                name=pod_resource.get("metadata", {}).get("name", "unknown"),
                status="unknown",
                ip="N/A",
                start_time=None,
                sync_success=False,
                last_sync=None,
            )
            return pod_info.model_dump()

    def _enhance_pod_with_sync_status(
        self, pod_dict: Dict[str, Any], pod_ip: str, deployment_history: Dict[str, Any]
    ) -> None:
        """Enhance pod data with sync status and last_sync from deployment history."""
        try:
            # Find the most recent deployment for this pod IP
            most_recent_success = False
            most_recent_timestamp = None

            # Look through deployment history for entries matching this pod IP
            for endpoint_url, deployment_info in deployment_history.items():
                if pod_ip in endpoint_url:  # Match IP in the endpoint URL
                    success = deployment_info.get("success", False)
                    timestamp_str = deployment_info.get("timestamp")

                    if timestamp_str:
                        try:
                            from datetime import datetime

                            timestamp = datetime.fromisoformat(
                                timestamp_str.replace("Z", "+00:00")
                            )

                            # Track the most recent deployment
                            if (
                                most_recent_timestamp is None
                                or timestamp > most_recent_timestamp
                            ):
                                most_recent_timestamp = timestamp
                                most_recent_success = success
                        except Exception as e:
                            logger.debug(
                                f"Failed to parse timestamp for pod {pod_ip}: {e}"
                            )

            # Update pod data with sync information
            pod_dict["sync_success"] = most_recent_success
            if most_recent_timestamp:
                pod_dict["last_sync"] = most_recent_timestamp.isoformat()

            logger.debug(
                f"Enhanced pod {pod_ip} with sync_success={most_recent_success}, last_sync={most_recent_timestamp}"
            )

        except Exception as e:
            logger.warning(f"Failed to enhance pod {pod_ip} with sync status: {e}")
