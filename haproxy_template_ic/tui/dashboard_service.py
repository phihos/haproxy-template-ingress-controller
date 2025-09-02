"""
Dashboard service that orchestrates data collection and processing.

Uses management socket to provide complete dashboard data.
"""

import logging
import re
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from haproxy_template_ic.constants import SECONDS_PER_HOUR, SECONDS_PER_MINUTE
from haproxy_template_ic.tui.models import (
    ActivityEvent,
    DashboardData,
    ErrorInfo,
    OperatorInfo,
    PerformanceInfo,
    PerformanceMetric,
    PodInfo,
    ResourceInfo,
    TemplateInfo,
)
from haproxy_template_ic.tui.socket_client import SocketClient
from haproxy_template_ic.tui.utils import parse_iso_timestamp

logger = logging.getLogger(__name__)

__all__ = ["DashboardService"]


class DashboardService:
    """Main service for dashboard data collection and processing."""

    def __init__(
        self,
        namespace: str,
        context: Optional[str] = None,
        deployment_name: str = "haproxy-template-ic",
        socket_path: Optional[str] = None,
    ):
        self.namespace = namespace
        self.context = context
        self.deployment_name = deployment_name
        self.socket_path = socket_path

        # Initialize socket client
        self.socket_client = SocketClient(
            namespace, context, deployment_name, socket_path
        )

    async def initialize(self) -> None:
        """Initialize the service."""
        # Service is ready to use immediately without compatibility checking
        pass

    async def fetch_all_data(self) -> DashboardData:
        """Fetch all dashboard data with enhanced error handling."""
        try:
            return await self._fetch()
        except Exception as e:
            logger.error(f"Failed to fetch dashboard data: {e}")
            error_info = self._categorize_error(e)

            return DashboardData(
                operator=OperatorInfo(status="ERROR", namespace=self.namespace),
                pods=[],
                templates={},
                resources=ResourceInfo(),
                performance=PerformanceInfo.empty(),
                activity=[],
                error_infos=[error_info],
            )

    async def get_template_content(
        self, template_name: str
    ) -> Optional[Dict[str, Any]]:
        """Get template content for inspection."""
        try:
            # Fetch source content first
            source_result = await self.socket_client.execute_command(
                f"get template_source {template_name}"
            )

            response: Dict[str, Any] = {
                "template_name": template_name,
                "source": None,
                "rendered": None,
                "type": "unknown",
                "errors": [],
            }

            # Process source result
            if source_result and not source_result.get("error"):
                source_data = source_result.get("result", {})
                response["source"] = source_data.get("source")
                response["type"] = source_data.get("type", "unknown")
            else:
                response["errors"].append(
                    f"Source: {source_result.get('error', 'Unknown error')}"
                )

            # Skip fetching rendered content for snippets since they don't have rendered versions
            if response["type"] != "snippet":
                # Fetch rendered content only for non-snippet templates
                rendered_result = await self.socket_client.execute_command(
                    f"get rendered_template {template_name}"
                )

                # Process rendered result
                if rendered_result and not rendered_result.get("error"):
                    rendered_data = rendered_result.get("result", {})
                    response["rendered"] = rendered_data.get("content")
                    if response["type"] == "unknown":
                        response["type"] = rendered_data.get("type", "unknown")
                else:
                    response["errors"].append(
                        f"Rendered: {rendered_result.get('error', 'Unknown error')}"
                    )

            return response

        except Exception as e:
            logger.error(f"Failed to get template content for {template_name}: {e}")
            return {
                "template_name": template_name,
                "source": None,
                "rendered": None,
                "type": "unknown",
                "errors": [f"Exception: {e}"],
            }

    def _is_connection_error(self, error_msg: str) -> bool:
        """Check if an error message indicates a connection/API problem."""
        connection_keywords = [
            "connection refused",
            "connection timed out",
            "connection reset",
            "no route to host",
            "network is unreachable",
            "name or service not known",
            "api server",
            "cluster unreachable",
            "unable to connect",
            "dial tcp",
            "context deadline exceeded",
            "client: etcd cluster unavailable",
            "the server could not find the requested resource",
            "401 unauthorized",
            "403 forbidden",
            "certificate",
            "tls handshake",
            "couldn't get current server api group list",
            "the connection to the server",
            "connection error",
            "connection failure",
            "server unreachable",
            "host unreachable",
            "timeout error",
            "request timeout",
        ]

        error_lower = error_msg.lower()
        return any(keyword in error_lower for keyword in connection_keywords)

    def _extract_error_summary(self, exception: Exception) -> str:
        """Extract a concise, useful error summary from an exception."""

        error_str = str(exception)

        # Common patterns to extract meaningful parts
        patterns = [
            # Extract the main error after "dial tcp"
            r"dial tcp[^:]*:\s*(.+)",
            # Extract error after "couldn't get"
            r"couldn't get[^:]*:\s*(.+)",
            # Extract error after "Get" request
            r'Get\s+"[^"]+": (.+)',
            # Extract error after colon
            r":\s*(.+?)(?:\s*-\s*did you specify|$)",
        ]

        for pattern in patterns:
            match = re.search(pattern, error_str, re.IGNORECASE)
            if match:
                extracted = match.group(1).strip()
                # Clean up common redundant phrases
                extracted = re.sub(
                    r"\s*-\s*did you specify.*$", "", extracted, flags=re.IGNORECASE
                )
                extracted = re.sub(
                    r"\s*\(.*?\)$", "", extracted
                )  # Remove parenthetical notes
                return extracted

        # Fallback: return first sentence or up to first major punctuation
        sentences = error_str.split(".")
        if sentences and len(sentences[0]) < 100:
            return sentences[0].strip()

        # If still too long, take first 80 chars
        return f"{error_str[:77]}..." if len(error_str) > 80 else error_str

    def _categorize_error(self, exception: Exception) -> ErrorInfo:
        """Categorize an exception into a structured error info."""
        error_str = str(exception).lower()

        # Connection/API errors - use the helper method for consistency
        if self._is_connection_error(error_str):
            return ErrorInfo(
                type="CONNECTION_ERROR",
                message="Cannot connect to Kubernetes cluster",
                details=str(exception),
                suggestions=[
                    "Check if the cluster is running: kind get clusters",
                    "Check kubectl connectivity: kubectl cluster-info",
                    "Verify your kubeconfig is correctly configured",
                    "Check network connectivity to the cluster",
                ],
            )

        # Authentication errors
        elif any(
            term in error_str
            for term in ["forbidden", "unauthorized", "authentication", "permission"]
        ):
            return ErrorInfo(
                type="AUTH_ERROR",
                message="Authentication or authorization failed",
                details=str(exception),
                suggestions=[
                    "Check your kubeconfig credentials",
                    "Verify you have permissions to access the namespace",
                    f"Try: kubectl auth can-i get pods --namespace={self.namespace}",
                    "Contact your cluster administrator if needed",
                ],
            )

        # Not found errors
        elif any(term in error_str for term in ["not found", "404"]):
            return ErrorInfo(
                type="NO_RESOURCES",
                message=f"Resources not found in namespace '{self.namespace}'",
                details=str(exception),
                suggestions=[
                    f"Verify the namespace exists: kubectl get namespace {self.namespace}",
                    f"Check if the deployment exists: kubectl get deployment {self.deployment_name} -n {self.namespace}",
                    "Verify the deployment and namespace names are correct",
                ],
            )

        # Generic API errors - try to provide better context
        else:
            error_summary = self._extract_error_summary(exception)

            # Try to categorize based on the extracted summary
            if any(
                keyword in error_summary.lower()
                for keyword in ["connection", "timeout", "refused"]
            ):
                return ErrorInfo(
                    type="CONNECTION_ERROR",
                    message=f"Connection error: {error_summary}",
                    details=str(exception),
                    suggestions=[
                        "Check if the cluster is running: kind get clusters",
                        "Check kubectl connectivity: kubectl cluster-info",
                        "Verify your kubeconfig is correctly configured",
                        "Check network connectivity to the cluster",
                    ],
                )
            elif any(
                keyword in error_summary.lower()
                for keyword in ["permission", "forbidden", "unauthorized"]
            ):
                return ErrorInfo(
                    type="AUTH_ERROR",
                    message=f"Authentication error: {error_summary}",
                    details=str(exception),
                    suggestions=[
                        "Check your kubeconfig credentials",
                        f"Verify you have permissions to access namespace '{self.namespace}'",
                        f"Try: kubectl auth can-i get pods --namespace={self.namespace}",
                        "Contact your cluster administrator if needed",
                    ],
                )
            else:
                return ErrorInfo(
                    type="API_ERROR",
                    message=f"Kubernetes API issue: {error_summary}",
                    details=str(exception),
                    suggestions=[
                        "Check cluster health and availability",
                        "Verify the namespace and resource names are correct",
                        "Try refreshing or restarting the dashboard",
                        "Review the full error details above for more information",
                    ],
                )

    async def _fetch(self) -> DashboardData:
        """Fetch data using optimized dashboard commands."""
        logger.debug("Starting optimized fetch with dump dashboard command")

        # Fetch core data - this includes all data from dump deployments, activity, and config
        dashboard_data = await self.socket_client.execute_command("dump dashboard")

        # dashboard_data is now a dict - no exception was raised

        dashboard_data_args: Dict[str, Any] = {
            "operator": self._extract_operator_info(dashboard_data),
            "error_infos": [],
        }

        # Extract activity events first so we can use them for pod sync times
        activity_events = self._extract_activity_events(dashboard_data)
        dashboard_data_args["activity"] = activity_events
        dashboard_data_args["resources"] = self._extract_resources_info(
            dashboard_data, activity_events
        )

        # Process pod data from socket only
        dashboard_pods = dashboard_data.get("pods", [])
        dashboard_data_args["pods"] = self._process_socket_pods(
            dashboard_pods, activity_events
        )

        # Extract templates info using config and deployment data from dashboard dump
        # Note: deployment_history might be missing from dashboard dump due to async issues in management socket
        deployment_history = dashboard_data.get("deployment_history")
        if not deployment_history:
            logger.debug(
                "No deployment history found in dashboard data, template timestamps may be incomplete"
            )
        dashboard_data_args["templates"] = self._extract_templates_info(
            dashboard_data,
            deployment_history,
        )
        dashboard_data_args["performance"] = self._extract_performance_info(
            dashboard_data
        )

        return DashboardData(
            **dashboard_data_args,
        )

    def _extract_operator_info(self, data: Dict[str, Any]) -> OperatorInfo:
        """Extract operator information from data."""

        return OperatorInfo(**data.get("operator", {}))

    def _process_socket_pods(
        self,
        dashboard_pods: List[Dict[str, Any]],
        activity_events: Optional[List[ActivityEvent]] = None,
    ) -> List[PodInfo]:
        """Process dashboard pod data using only socket data."""
        if not dashboard_pods:
            return []

        enhanced_pods = []

        # Extract update times from activity events
        pod_update_times = {}
        if activity_events:
            pod_update_times = self._extract_pod_update_times_from_activity(
                activity_events
            )

        for pod_data in dashboard_pods:
            pod_name = pod_data.get("name", "unknown")
            pod_ip = pod_data.get("ip", "N/A")

            # Get last update time from activity events
            last_update_time = None
            if pod_ip != "N/A" and pod_ip in pod_update_times:
                last_update_time = pod_update_times[pod_ip]
                logger.debug(
                    f"Using activity-based update time for pod {pod_name} ({pod_ip}): {last_update_time}"
                )

            # Use dictionary unpacking pattern for clean initialization
            pod_info_data = {
                **pod_data,
                "last_sync": last_update_time,
                "synced": self._calculate_sync_status(pod_data),
                "cpu": "N/A",  # No metrics without K8s
                "memory": "N/A",  # No metrics without K8s
            }
            pod_info = PodInfo(**pod_info_data)

            enhanced_pods.append(pod_info)

        return enhanced_pods

    def _extract_templates_info(
        self, dashboard_data: Dict[str, Any], deployment_history: Dict[str, Any] = None
    ) -> Dict[str, TemplateInfo]:
        """Extract template information from dashboard data."""
        logger.debug(
            f"_extract_templates_info called with dashboard_data keys: {list(dashboard_data.keys())}"
        )
        templates = {}

        # Extract from haproxy_config_context (rendered templates)
        config_context = dashboard_data.get("haproxy_config_context", {})
        logger.debug(
            f"Config context keys: {list(config_context.keys()) if config_context else 'None'}"
        )

        # Process main config
        rendered_config = config_context.get("rendered_config", {})
        if rendered_config and rendered_config.get("content"):
            templates["haproxy.cfg"] = TemplateInfo(
                name="haproxy.cfg",
                type="config",
                size=len(rendered_config["content"]),
                lines=len(rendered_config["content"].splitlines()),
                status="valid" if rendered_config["content"] else "empty",
                last_modified=datetime.now(timezone.utc),
            )

        # Process rendered content (unified list containing maps, certificates, and files)
        rendered_content = config_context.get("rendered_content", [])
        logger.debug(f"Found {len(rendered_content)} rendered content items")
        for content_data in rendered_content:
            if isinstance(content_data, dict):
                filename = content_data.get("filename", "unknown.file")
                content = content_data.get("content", "")
                content_type = content_data.get("content_type", "file")

                # Map content_type to template type
                template_type = content_type  # "map", "certificate", "file"

                templates[filename] = TemplateInfo(
                    name=filename,
                    type=template_type,
                    size=len(content),
                    lines=len(content.splitlines()),
                    status="valid" if content else "empty",
                    last_modified=datetime.now(timezone.utc),
                )

        # Process template snippets (always from configuration, snippets are not rendered separately)
        config_data = dashboard_data.get("config", {})
        snippets_config = config_data.get("template_snippets", {})
        logger.debug(f"Found {len(snippets_config)} template snippets")
        for snippet_name, snippet_template in snippets_config.items():
            # Get snippet content if it's a dict with template key
            if isinstance(snippet_template, dict):
                content = snippet_template.get("template", "")
            else:
                content = str(snippet_template) if snippet_template else ""

            templates[snippet_name] = TemplateInfo(
                name=snippet_name,
                type="snippet",
                size=len(content) if content else 0,
                lines=len(content.splitlines()) if content else 0,
                status="valid" if content else "empty",
                last_modified=None,
            )

        # If no rendered templates found, look at configuration to show what's configured
        # This helps when the operator hasn't rendered templates yet
        if not templates:
            config_data = dashboard_data.get("config", {})

            # Add main haproxy config if configured
            if config_data.get("haproxy_config"):
                templates["haproxy.cfg"] = TemplateInfo(
                    name="haproxy.cfg",
                    type="config",
                    size=0,  # Not rendered yet
                    lines=0,
                    status="configured",  # Different status to indicate it's not rendered
                    last_modified=None,
                )

            # Add configured maps
            maps_config = config_data.get("maps", {})
            for map_name in maps_config.keys():
                templates[map_name] = TemplateInfo(
                    name=map_name,
                    type="map",
                    size=0,
                    lines=0,
                    status="configured",
                    last_modified=None,
                )

            # Add configured certificates
            certificates_config = config_data.get("certificates", {})
            for cert_name in certificates_config.keys():
                templates[cert_name] = TemplateInfo(
                    name=cert_name,
                    type="certificate",
                    size=0,
                    lines=0,
                    status="configured",
                    last_modified=None,
                )

            # Add configured files
            files_config = config_data.get("files", {})
            for file_name in files_config.keys():
                templates[file_name] = TemplateInfo(
                    name=file_name,
                    type="file",
                    size=0,
                    lines=0,
                    status="configured",
                    last_modified=None,
                )

        logger.debug(f"Extracted {len(templates)} templates: {list(templates.keys())}")

        # Add template change timestamps from deployment history if available
        if deployment_history:
            self._add_template_timestamps_from_deployment_history(
                templates, {"deployment_history": deployment_history}
            )

        return templates

    def _add_template_timestamps_from_deployment_history(
        self, templates: Dict[str, TemplateInfo], deployment_data: Dict[str, Any]
    ) -> None:
        """Add actual change timestamps to templates from deployment history."""
        history_data = deployment_data.get("deployment_history", {})

        # Find the most recent actual change timestamp for each template across all endpoints
        template_timestamps: Dict[str, str] = {}

        for endpoint, deployment_info in history_data.items():
            if deployment_info.get("success"):
                # Use template_change_timestamps if available (new format)
                change_timestamps = deployment_info.get(
                    "template_change_timestamps", {}
                )
                if change_timestamps:
                    for template_name, change_timestamp in change_timestamps.items():
                        if (
                            template_name not in template_timestamps
                            or change_timestamp > template_timestamps[template_name]
                        ):
                            template_timestamps[template_name] = change_timestamp

        # Update last_modified for templates that have change timestamps
        for template_name, template_info in templates.items():
            change_timestamp_str = template_timestamps.get(template_name)
            if change_timestamp_str:
                try:
                    # Parse ISO timestamp and create datetime object
                    change_timestamp = datetime.fromisoformat(
                        change_timestamp_str.replace("Z", "+00:00")
                    )
                    # Convert to local time
                    template_info.last_modified = change_timestamp.astimezone()
                except Exception as e:
                    logger.warning(
                        f"Failed to parse timestamp '{change_timestamp_str}' for template '{template_name}': {e}"
                    )
                    # Keep the existing last_modified (datetime.now() or None)

    def _calculate_resource_timestamps(
        self, activity_events: List[ActivityEvent]
    ) -> Dict[str, datetime]:
        """Calculate last update timestamp for each resource type from activity events."""
        resource_timestamps = {}

        # Process activity events in reverse order to get most recent first
        for event in reversed(activity_events):
            if event.metadata and isinstance(event.metadata, dict):
                resource_type = event.metadata.get("resource_type")
                if resource_type and resource_type not in resource_timestamps:
                    # Parse timestamp from string to datetime
                    try:
                        if isinstance(event.timestamp, str):
                            timestamp = datetime.fromisoformat(
                                event.timestamp.replace("Z", "+00:00")
                            )
                        else:
                            timestamp = event.timestamp
                        resource_timestamps[resource_type] = timestamp
                    except Exception as e:
                        logger.debug(
                            f"Failed to parse timestamp for {resource_type}: {e}"
                        )

        return resource_timestamps

    def _extract_resources_info(
        self,
        data: Dict[str, Any],
        activity_events: Optional[List[ActivityEvent]] = None,
    ) -> ResourceInfo:
        """Extract resource information."""
        # Try to get from pre-calculated resources
        if "resources" in data:
            stats = data["resources"]
            resource_counts = {}
            resource_last_updates = {}
            resource_memory_sizes = {}
            total = 0
            current_time = datetime.now(timezone.utc)

            # Calculate resource timestamps from activity events if available
            if activity_events:
                calculated_timestamps = self._calculate_resource_timestamps(
                    activity_events
                )
            else:
                calculated_timestamps = {}

            for res_type, res_data in stats.items():
                if isinstance(res_data, dict) and "total" in res_data:
                    count = res_data["total"]
                    resource_counts[res_type] = count
                    total += count

                    # Extract memory size if available
                    memory_size = res_data.get("memory_size", 0)
                    resource_memory_sizes[res_type] = memory_size

                    # Use calculated timestamp from activity events or fallback to current time
                    resource_last_updates[res_type] = calculated_timestamps.get(
                        res_type, current_time
                    )

            return ResourceInfo(
                resource_counts=resource_counts,
                total=total,
                last_update=current_time,
                resource_last_updates=resource_last_updates,
                resource_memory_sizes=resource_memory_sizes,
            )

        # Fallback: calculate from indices
        return self._calculate_resource_stats(data, activity_events)

    def _calculate_resource_stats(
        self,
        data: Dict[str, Any],
        activity_events: Optional[List[ActivityEvent]] = None,
    ) -> ResourceInfo:
        """Calculate resource statistics from indices."""
        indices = data.get("indices", {})

        resource_counts = {}
        resource_last_updates = {}
        resource_memory_sizes = {}
        total = 0
        current_time = datetime.now(timezone.utc)

        # Calculate resource timestamps from activity events if available
        if activity_events:
            calculated_timestamps = self._calculate_resource_timestamps(activity_events)
        else:
            calculated_timestamps = {}

        # Dynamically calculate counts for all resource types in indices
        for res_type, resource_index in indices.items():
            count = self._count_resources(resource_index)
            resource_counts[res_type] = count
            total += count

            # Try to get memory size if the resource_index has the get_memory_size method
            memory_size = 0
            if hasattr(resource_index, "get_memory_size"):
                try:
                    memory_size = resource_index.get_memory_size()
                except Exception as e:
                    logger.debug(f"Failed to get memory size for {res_type}: {e}")
            resource_memory_sizes[res_type] = memory_size

            # Use calculated timestamp from activity events or fallback to current time
            resource_last_updates[res_type] = calculated_timestamps.get(
                res_type, current_time
            )

        return ResourceInfo(
            resource_counts=resource_counts,
            total=total,
            last_update=current_time,
            resource_last_updates=resource_last_updates,
            resource_memory_sizes=resource_memory_sizes,
        )

    def _count_resources(self, resource_index: Dict[str, Any]) -> int:
        """Count resources in an index."""
        if not resource_index:
            return 0

        try:
            total_count = 0
            for key in resource_index:
                resources = resource_index[key]
                if isinstance(resources, list):
                    total_count += len(resources)
                else:
                    total_count += 1
            return total_count
        except Exception as e:
            logger.debug(f"Error counting resources: {e}")
            return 0

    def _extract_performance_info(self, data: Dict[str, Any]) -> PerformanceInfo:
        """Extract performance information."""

        performance_data = data.get("performance", {})

        # Create PerformanceMetric objects from nested data
        template_render = None
        if "template_render" in performance_data:
            template_render_data = performance_data["template_render"].copy()
            # Convert "N/A" strings to None for Pydantic validation
            for key in ["p50", "p95", "p99"]:
                if template_render_data.get(key) == "N/A":
                    template_render_data[key] = None
            template_render = PerformanceMetric(**template_render_data)

        dataplane_api = None
        if "dataplane_api" in performance_data:
            dataplane_api_data = performance_data["dataplane_api"].copy()
            # Convert "N/A" strings to None for Pydantic validation
            for key in ["p50", "p95", "p99"]:
                if dataplane_api_data.get(key) == "N/A":
                    dataplane_api_data[key] = None
            dataplane_api = PerformanceMetric(**dataplane_api_data)

        # Extract other fields directly
        return PerformanceInfo(
            template_render=template_render,
            dataplane_api=dataplane_api,
            sync_success_rate=performance_data.get("sync_success_rate"),
            recent_sync_success_rate=performance_data.get("recent_sync_success_rate"),
            sync_pattern=performance_data.get("sync_pattern"),
            total_syncs=performance_data.get("total_syncs", 0),
            failed_syncs=performance_data.get("failed_syncs", 0),
        )

    def _extract_activity_events(
        self, dashboard_data: Dict[str, Any]
    ) -> List[ActivityEvent]:
        """Extract activity events from dashboard data."""

        if dashboard_data.get("error"):
            return []

        events = []
        raw_events = dashboard_data.get("activity", [])

        for event_data in raw_events:
            if isinstance(event_data, dict):
                try:
                    event = ActivityEvent(**event_data)
                    events.append(event)
                except Exception as e:
                    logger.debug(f"Failed to parse activity event: {e}")
                    continue

        return events

    def _calculate_sync_status(self, pod_data: Dict[str, Any]) -> str:
        """Calculate sync status for a pod."""
        sync_success = pod_data.get("sync_success")
        last_sync = pod_data.get("last_sync")

        if not sync_success:
            return "Failed"
        elif last_sync:
            try:
                sync_time = parse_iso_timestamp(last_sync)
                if sync_time is None:
                    return "Invalid timestamp"
                now = datetime.now(timezone.utc)
                time_diff = now - sync_time

                if time_diff.total_seconds() < SECONDS_PER_MINUTE:
                    return f"{int(time_diff.total_seconds())}s ago"
                elif time_diff.total_seconds() < SECONDS_PER_HOUR:
                    return f"{int(time_diff.total_seconds() / SECONDS_PER_MINUTE)}m ago"
                elif time_diff.total_seconds() < 86400:
                    return f"{int(time_diff.total_seconds() / SECONDS_PER_HOUR)}h ago"
                else:
                    return f"{int(time_diff.total_seconds() / 86400)}d ago"
            except Exception:
                return "Unknown"
        else:
            return "Unknown"

    def _create_error_response(self, error_message: str) -> DashboardData:
        """Create an error response."""
        return DashboardData(
            operator=OperatorInfo(status="ERROR", namespace=self.namespace),
            pods=[],
            templates={},
            resources=ResourceInfo(),
            performance=PerformanceInfo.empty(),
            activity=[],
            error_infos=[
                ErrorInfo(
                    type="FETCH_ERROR",
                    message="Failed to fetch dashboard data",
                    details=error_message,
                    suggestions=[
                        "Check if the operator is running",
                        "Verify socket connectivity",
                        "Check Kubernetes API access",
                    ],
                )
            ],
        )

    def _extract_pod_update_times_from_activity(
        self, activity_events: List[ActivityEvent]
    ) -> Dict[str, datetime]:
        """Extract the last configuration update time for each pod from activity events.

        Only considers events where configuration was actually changed (not skipped).

        Args:
            activity_events: List of activity events to analyze

        Returns:
            Dictionary mapping pod IP addresses to their last config update datetime
        """
        pod_update_times = {}

        # Process events in reverse chronological order to get most recent update times
        for event in reversed(activity_events):
            if (
                event.source == "dataplane"
                and event.type in ["RELOAD", "SYNC"]
                and event.metadata
                and isinstance(event.metadata, dict)
            ):
                # Only consider events where configuration actually changed
                config_changed = event.metadata.get(
                    "config_changed", True
                )  # Default True for backward compatibility
                if not config_changed:
                    continue

                pod_ip = event.metadata.get("pod_ip")

                if pod_ip and pod_ip != "unknown" and pod_ip not in pod_update_times:
                    # Parse timestamp from string to datetime if needed
                    try:
                        if isinstance(event.timestamp, str):
                            timestamp = datetime.fromisoformat(
                                event.timestamp.replace("Z", "+00:00")
                            )
                        else:
                            timestamp = event.timestamp

                        pod_update_times[pod_ip] = timestamp
                        logger.debug(
                            f"Found config update time for pod IP {pod_ip}: {timestamp}"
                        )

                    except Exception as e:
                        logger.debug(
                            f"Failed to parse update timestamp for {pod_ip}: {e}"
                        )

        logger.debug(f"Extracted update times for {len(pod_update_times)} pods")
        return pod_update_times
