"""
Shared data models for the dashboard package.

These Pydantic models provide clear type definitions and validation
for all dashboard data structures, eliminating type confusion bugs.
"""

from datetime import datetime, timezone
from typing import Dict, List, Optional

from pydantic import BaseModel, Field, field_validator

from haproxy_template_ic.activity import ActivityEvent
from haproxy_template_ic.constants import SECONDS_PER_HOUR, SECONDS_PER_MINUTE
from haproxy_template_ic.tui.utils import parse_iso_timestamp


class PodInfo(BaseModel):
    """Information about an HAProxy pod."""

    name: str
    status: str = "Unknown"
    ip: str = "N/A"
    cpu: Optional[str] = None
    memory: Optional[str] = None
    synced: str = "Unknown"
    last_sync: Optional[datetime] = None
    sync_success: bool = False
    start_time: Optional[datetime] = None

    @field_validator("start_time", mode="before")
    @classmethod
    def validate_start_time(cls, v):
        """Validate and parse start_time from various formats."""
        if v is None or isinstance(v, datetime):
            return v
        if isinstance(v, str):
            return parse_iso_timestamp(v)
        return None

    @property
    def uptime(self) -> str:
        """Calculate uptime from start_time."""
        if not self.start_time:
            return "Unknown"

        # Use UTC for consistent timezone handling
        now = datetime.now(timezone.utc)
        start_time = self.start_time

        # Ensure start_time is timezone-aware
        if start_time.tzinfo is None:
            start_time = start_time.replace(tzinfo=timezone.utc)

        delta = now - start_time

        # Format uptime in human-readable format
        days = delta.days
        hours, remainder = divmod(delta.seconds, SECONDS_PER_HOUR)
        minutes, _ = divmod(remainder, SECONDS_PER_MINUTE)

        if days > 0:
            return f"{days}d {hours}h {minutes}m"
        elif hours > 0:
            return f"{hours}h {minutes}m"
        else:
            return f"{minutes}m"


class OperatorInfo(BaseModel):
    """Information about the operator status."""

    status: str = "Unknown"
    version: Optional[str] = None
    namespace: str = "unknown"
    deployment_name: Optional[str] = None
    last_update: Optional[datetime] = None
    configmap_name: Optional[str] = None
    controller_pod_name: Optional[str] = None
    controller_pod_start_time: Optional[str] = None
    last_deployment_time: Optional[str] = None


class TemplateInfo(BaseModel):
    """Information about a template."""

    name: str
    type: str  # "map", "config", "certificate"
    size: int = 0
    lines: int = 0
    status: str = "unknown"  # "valid", "empty", "error", "unknown"
    last_modified: Optional[datetime] = None
    source_template: Optional[str] = None
    rendered_content: Optional[str] = None


class ResourceInfo(BaseModel):
    """Information about Kubernetes resources."""

    resource_counts: Dict[str, int] = Field(
        default_factory=dict, description="Count of each resource type"
    )
    total: int = 0
    last_update: Optional[datetime] = None
    resource_last_updates: Dict[str, datetime] = Field(
        default_factory=dict, description="Last update time per resource type"
    )
    resource_memory_sizes: Dict[str, int] = Field(
        default_factory=dict, description="Memory size in bytes for each resource type"
    )


class PerformanceMetric(BaseModel):
    """Single performance metric with percentiles and history."""

    p50: Optional[float] = Field(
        None, description="50th percentile (median) in milliseconds"
    )
    p95: Optional[float] = Field(None, description="95th percentile in milliseconds")
    p99: Optional[float] = Field(None, description="99th percentile in milliseconds")
    history: List[float] = Field(
        default_factory=list,
        description="Rolling window of recent values for sparklines",
    )


class PerformanceInfo(BaseModel):
    """Performance and metrics information."""

    template_render: Optional[PerformanceMetric] = Field(
        None, description="Template rendering performance"
    )
    dataplane_api: Optional[PerformanceMetric] = Field(
        None, description="Dataplane API operation performance"
    )
    sync_success_rate: Optional[float] = Field(
        None, description="Overall sync success rate (0.0-1.0)"
    )
    recent_sync_success_rate: Optional[float] = Field(
        None, description="Recent sync success rate (0.0-1.0)"
    )
    sync_pattern: Optional[str] = Field(
        None, description="Visual pattern of recent sync results"
    )
    total_syncs: int = Field(0, description="Total number of synchronizations")
    failed_syncs: int = Field(0, description="Number of failed synchronizations")

    @classmethod
    def empty(cls) -> "PerformanceInfo":
        """Create empty PerformanceInfo with default values."""
        return cls(
            template_render=None,
            dataplane_api=None,
            sync_success_rate=None,
            recent_sync_success_rate=None,
            sync_pattern=None,
            total_syncs=0,
            failed_syncs=0,
        )


class ErrorInfo(BaseModel):
    """Structured error information."""

    type: str  # CONNECTION_ERROR, NO_RESOURCES, AUTH_ERROR, etc.
    message: str
    details: Optional[str] = None
    suggestions: List[str] = Field(default_factory=list)


class DashboardData(BaseModel):
    """Complete dashboard data structure."""

    operator: OperatorInfo = OperatorInfo()
    pods: List[PodInfo] = Field(default=[])
    templates: Dict[str, TemplateInfo] = Field(default={})
    resources: ResourceInfo = Field(default=ResourceInfo())
    performance: PerformanceInfo = Field(default_factory=PerformanceInfo.empty)
    activity: List[ActivityEvent] = Field(default=[])
    error_infos: List[ErrorInfo] = Field(default=[])
    last_update: datetime = Field(default_factory=datetime.now)


class SocketInfo(BaseModel):
    """Information about HAProxy management socket."""

    pod_name: str
    socket_path: str
    accessible: bool = False
    last_check: Optional[datetime] = None
    error: Optional[str] = None


class DataplaneInfo(BaseModel):
    """Information about HAProxy Dataplane API."""

    pod_name: str
    endpoint: str
    accessible: bool = False
    version: Optional[str] = None
    last_check: Optional[datetime] = None
    error: Optional[str] = None
