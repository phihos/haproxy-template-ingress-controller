"""
Deployment state tracking using activity events.

This module provides the DeploymentStateTracker which uses ActivityEvents
to track deployment state, replacing the old DeploymentHistory system.
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Dict, Optional, Any

from haproxy_template_ic.activity import ActivityBuffer, EventType
from haproxy_template_ic.constants import DEFAULT_ACTIVITY_QUERY_LIMIT
from haproxy_template_ic.tui.utils import parse_iso_timestamp


@dataclass
class DeploymentInfo:
    """Information about deployment state for an endpoint."""

    endpoint: str
    version: Optional[str] = None
    success: bool = False
    error: Optional[str] = None
    last_attempt: Optional[str] = None
    pod_name: Optional[str] = None
    timestamp: Optional[datetime] = None


class DeploymentStateTracker:
    """Track deployment state using activity events."""

    def __init__(self, activity_buffer: ActivityBuffer):
        self.activity_buffer = activity_buffer

    # Use utility function for timestamp parsing

    async def to_dict(self) -> Dict[str, Any]:
        """Convert deployment state to dictionary format."""
        deployment_history = {}

        # Get recent events and filter for deployment events
        all_events = await self.activity_buffer.get_recent(
            count=DEFAULT_ACTIVITY_QUERY_LIMIT
        )
        events = [
            event
            for event in all_events
            if isinstance(event, dict)
            and event.get("type")
            in [EventType.DEPLOYMENT_SUCCESS, EventType.DEPLOYMENT_FAILED]
        ]

        # Group events by endpoint and track latest state
        endpoint_info: Dict[str, Dict[str, Any]] = {}

        for event_data in events:
            if isinstance(event_data, dict):
                metadata = event_data.get("metadata", {})
                endpoint = metadata.get("endpoint")
                if not endpoint:
                    continue

                event_type = event_data.get("type")

                if endpoint not in endpoint_info:
                    endpoint_info[endpoint] = {}

                info = endpoint_info[endpoint]

                if event_type == EventType.DEPLOYMENT_SUCCESS:
                    info.update(
                        {
                            "success": True,
                            "version": metadata.get("version"),
                            "pod_name": metadata.get("pod_name"),
                            "timestamp": event_data.get("timestamp"),
                            "error": None,
                        }
                    )
                elif event_type == EventType.DEPLOYMENT_FAILED:
                    if not info.get("success"):  # Only update if no success yet
                        info.update(
                            {
                                "success": False,
                                "error": metadata.get("error"),
                                "last_attempt": metadata.get("version"),
                                "pod_name": metadata.get("pod_name"),
                                "timestamp": event_data.get("timestamp"),
                            }
                        )

        # Convert to deployment history format
        for endpoint, info in endpoint_info.items():
            deployment_history[endpoint] = info

        return {"deployment_history": deployment_history}

    def to_dict_sync(self) -> Dict[str, Any]:
        """Convert deployment state to dictionary format synchronously."""
        deployment_history = {}

        try:
            # Get recent events and filter for deployment events using sync method
            all_events = self.activity_buffer.get_recent_sync(
                count=DEFAULT_ACTIVITY_QUERY_LIMIT
            )
            events = [
                event
                for event in all_events
                if isinstance(event, dict)
                and event.get("type")
                in [EventType.DEPLOYMENT_SUCCESS, EventType.DEPLOYMENT_FAILED]
            ]
        except (AttributeError, TypeError):
            # ActivityBuffer might not have get_recent_sync method (e.g., in tests)
            # or might not be iterable - return empty deployment history
            return {"deployment_history": {}}

        # Group events by endpoint and track latest state
        endpoint_info: Dict[str, Dict[str, Any]] = {}

        for event_data in events:
            if isinstance(event_data, dict):
                metadata = event_data.get("metadata", {})
                endpoint = metadata.get("endpoint")
                if not endpoint:
                    continue

                event_type = event_data.get("type")

                if endpoint not in endpoint_info:
                    endpoint_info[endpoint] = {}

                info = endpoint_info[endpoint]

                if event_type == EventType.DEPLOYMENT_SUCCESS:
                    info.update(
                        {
                            "success": True,
                            "version": metadata.get("version"),
                            "pod_name": metadata.get("pod_name"),
                            "timestamp": event_data.get("timestamp"),
                            "error": None,
                        }
                    )
                elif event_type == EventType.DEPLOYMENT_FAILED:
                    if not info.get("success"):  # Only update if no success yet
                        info.update(
                            {
                                "success": False,
                                "error": metadata.get("error"),
                                "last_attempt": metadata.get("version"),
                                "pod_name": metadata.get("pod_name"),
                                "timestamp": event_data.get("timestamp"),
                            }
                        )

        # Convert to deployment history format
        for endpoint, info in endpoint_info.items():
            deployment_history[endpoint] = info

        return {"deployment_history": deployment_history}

    async def get_deployment_info(self, endpoint: str) -> Optional[DeploymentInfo]:
        """Get deployment information for a specific endpoint."""
        state = await self.to_dict()
        deployment_history = state.get("deployment_history", {})

        info_data = deployment_history.get(endpoint)
        if not info_data:
            return None

        return DeploymentInfo(
            endpoint=endpoint,
            version=info_data.get("version"),
            success=info_data.get("success", False),
            error=info_data.get("error"),
            last_attempt=info_data.get("last_attempt"),
            pod_name=info_data.get("pod_name"),
            timestamp=parse_iso_timestamp(info_data.get("timestamp")),
        )

    async def get_all_deployment_info(self) -> Dict[str, DeploymentInfo]:
        """Get deployment information for all endpoints."""
        state = await self.to_dict()
        deployment_history = state.get("deployment_history", {})

        result = {}
        for endpoint, info_data in deployment_history.items():
            result[endpoint] = DeploymentInfo(
                endpoint=endpoint,
                version=info_data.get("version"),
                success=info_data.get("success", False),
                error=info_data.get("error"),
                last_attempt=info_data.get("last_attempt"),
                pod_name=info_data.get("pod_name"),
                timestamp=parse_iso_timestamp(info_data.get("timestamp")),
            )

        return result
