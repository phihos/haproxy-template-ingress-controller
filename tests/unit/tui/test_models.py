"""
Unit tests for TUI Pydantic models.

Tests model validation, field validators, properties, and edge cases.
"""

import pytest
from datetime import datetime, timezone, timedelta
from pydantic import ValidationError

from haproxy_template_ic.tui.models import (
    PodInfo,
    OperatorInfo,
    TemplateInfo,
    ResourceInfo,
    PerformanceMetric,
    PerformanceInfo,
    ErrorInfo,
    DashboardData,
)
from haproxy_template_ic.activity import ActivityEvent


class TestPodInfo:
    """Test PodInfo model."""

    def test_basic_creation(self):
        """Test basic PodInfo creation."""
        pod = PodInfo(name="test-pod", status="Running", ip="10.0.0.1")
        assert pod.name == "test-pod"
        assert pod.status == "Running"
        assert pod.ip == "10.0.0.1"
        assert pod.cpu is None
        assert pod.memory is None
        assert pod.synced == "Unknown"
        assert pod.sync_success is False

    def test_start_time_validation_with_iso_string(self):
        """Test start_time validation with ISO string."""
        iso_string = "2024-01-15T10:30:00Z"
        pod = PodInfo(name="test-pod", start_time=iso_string)
        assert isinstance(pod.start_time, datetime)
        assert pod.start_time.tzinfo is not None

    def test_start_time_validation_with_datetime(self):
        """Test start_time validation with datetime object."""
        dt = datetime.now(timezone.utc)
        pod = PodInfo(name="test-pod", start_time=dt)
        assert pod.start_time == dt

    def test_start_time_validation_with_invalid_string(self):
        """Test start_time validation with invalid string."""
        pod = PodInfo(name="test-pod", start_time="invalid-date")
        assert pod.start_time is None

    def test_start_time_validation_with_none(self):
        """Test start_time validation with None."""
        pod = PodInfo(name="test-pod", start_time=None)
        assert pod.start_time is None

    def test_uptime_calculation_with_timezone_aware_start_time(self):
        """Test uptime calculation with timezone-aware start_time."""
        # 2 hours and 30 minutes ago
        import datetime as dt

        start_time = datetime.now(timezone.utc) - dt.timedelta(hours=2, minutes=30)
        pod = PodInfo(name="test-pod", start_time=start_time)
        uptime = pod.uptime
        # Just verify format is reasonable (actual time calculation may vary)
        assert "h" in uptime and "m" in uptime

    def test_uptime_calculation_with_naive_datetime(self):
        """Test uptime calculation with naive datetime."""
        # 45 minutes ago
        import datetime as dt

        start_time = datetime.now() - dt.timedelta(minutes=45)
        pod = PodInfo(name="test-pod", start_time=start_time)
        uptime = pod.uptime
        assert "45m" in uptime or "m" in uptime

    def test_uptime_calculation_with_days(self):
        """Test uptime calculation spanning days."""
        # 2 days, 3 hours, 15 minutes ago
        import datetime as dt

        start_time = datetime.now(timezone.utc) - dt.timedelta(
            days=2, hours=3, minutes=15
        )
        pod = PodInfo(name="test-pod", start_time=start_time)
        uptime = pod.uptime
        assert "2d" in uptime and "h" in uptime and "m" in uptime

    def test_uptime_with_no_start_time(self):
        """Test uptime when start_time is None."""
        pod = PodInfo(name="test-pod", start_time=None)
        assert pod.uptime == "Unknown"

    def test_full_pod_creation(self):
        """Test PodInfo with all fields."""
        import datetime as dt

        pod = PodInfo(
            name="haproxy-pod-1",
            status="Running",
            ip="10.0.0.1",
            cpu="100m",
            memory="128Mi",
            synced="2m ago",
            last_sync=datetime.now(),
            sync_success=True,
            start_time=datetime.now() - dt.timedelta(hours=2),
        )
        assert pod.name == "haproxy-pod-1"
        assert pod.sync_success is True
        assert pod.cpu == "100m"
        assert pod.memory == "128Mi"


class TestOperatorInfo:
    """Test OperatorInfo model."""

    def test_basic_creation(self):
        """Test basic OperatorInfo creation."""
        operator = OperatorInfo(status="RUNNING", namespace="test-namespace")
        assert operator.status == "RUNNING"
        assert operator.namespace == "test-namespace"
        assert operator.version is None

    def test_full_creation(self):
        """Test OperatorInfo with all fields."""
        operator = OperatorInfo(
            status="RUNNING",
            version="1.2.3",
            namespace="test-namespace",
            deployment_name="haproxy-template-ic",
            last_update=datetime.now(),
            configmap_name="test-config",
            controller_pod_name="controller-pod-1",
            controller_pod_start_time="2024-01-15T10:30:00Z",
            last_deployment_time="2024-01-15T11:00:00Z",
        )
        assert operator.version == "1.2.3"
        assert operator.deployment_name == "haproxy-template-ic"
        assert operator.configmap_name == "test-config"


class TestTemplateInfo:
    """Test TemplateInfo model."""

    def test_basic_creation(self):
        """Test basic TemplateInfo creation."""
        template = TemplateInfo(name="haproxy.cfg", type="config")
        assert template.name == "haproxy.cfg"
        assert template.type == "config"
        assert template.size == 0
        assert template.lines == 0
        assert template.status == "unknown"

    def test_full_creation(self):
        """Test TemplateInfo with all fields."""
        template = TemplateInfo(
            name="host.map",
            type="map",
            size=1024,
            lines=50,
            status="valid",
            last_modified=datetime.now(),
            source_template="{% for host in hosts %}{{ host }}{% endfor %}",
            rendered_content="example.com\ntest.com",
        )
        assert template.size == 1024
        assert template.lines == 50
        assert template.status == "valid"
        assert template.source_template is not None
        assert template.rendered_content is not None


class TestResourceInfo:
    """Test ResourceInfo model."""

    def test_empty_creation(self):
        """Test ResourceInfo creation with defaults."""
        resources = ResourceInfo()
        assert resources.resource_counts == {}
        assert resources.total == 0
        assert resources.last_update is None

    def test_with_data(self):
        """Test ResourceInfo with data."""
        resources = ResourceInfo(
            resource_counts={"ingresses": 3, "services": 5},
            total=8,
            last_update=datetime.now(),
        )
        assert resources.resource_counts["ingresses"] == 3
        assert resources.resource_counts["services"] == 5
        assert resources.total == 8

    def test_with_memory_sizes(self):
        """Test ResourceInfo with memory sizes."""
        resources = ResourceInfo(
            resource_counts={"ingresses": 2}, resource_memory_sizes={"ingresses": 1024}
        )
        assert resources.resource_memory_sizes["ingresses"] == 1024


class TestPerformanceMetric:
    """Test PerformanceMetric model."""

    def test_basic_creation(self):
        """Test basic PerformanceMetric creation."""
        metric = PerformanceMetric()
        assert metric.p50 is None
        assert metric.p95 is None
        assert metric.p99 is None
        assert metric.history == []

    def test_with_values(self):
        """Test PerformanceMetric with values."""
        metric = PerformanceMetric(
            p50=100.5, p95=250.0, p99=500.0, history=[100, 110, 120, 130]
        )
        assert metric.p50 == 100.5
        assert metric.p95 == 250.0
        assert metric.p99 == 500.0
        assert len(metric.history) == 4


class TestPerformanceInfo:
    """Test PerformanceInfo model."""

    def test_empty_creation(self):
        """Test PerformanceInfo creation with defaults."""
        performance = PerformanceInfo()
        assert performance.template_render is None
        assert performance.dataplane_api is None
        assert performance.sync_success_rate is None
        assert performance.total_syncs == 0
        assert performance.failed_syncs == 0

    def test_with_metrics(self):
        """Test PerformanceInfo with metrics."""
        template_metric = PerformanceMetric(p50=50.0, p95=100.0)
        dataplane_metric = PerformanceMetric(p50=25.0, p95=50.0)

        performance = PerformanceInfo(
            template_render=template_metric,
            dataplane_api=dataplane_metric,
            sync_success_rate=0.95,
            recent_sync_success_rate=0.98,
            total_syncs=100,
            failed_syncs=5,
        )
        assert performance.template_render.p50 == 50.0
        assert performance.dataplane_api.p50 == 25.0
        assert performance.sync_success_rate == 0.95
        assert performance.total_syncs == 100


class TestErrorInfo:
    """Test ErrorInfo model."""

    def test_basic_creation(self):
        """Test basic ErrorInfo creation."""
        error = ErrorInfo(type="CONNECTION_ERROR", message="Failed to connect")
        assert error.type == "CONNECTION_ERROR"
        assert error.message == "Failed to connect"
        assert error.details is None
        assert error.suggestions == []

    def test_with_details_and_suggestions(self):
        """Test ErrorInfo with full data."""
        error = ErrorInfo(
            type="NO_RESOURCES",
            message="No pods found",
            details="Deployment 'haproxy-template-ic' not found in namespace 'test'",
            suggestions=["Check if deployment exists", "Verify namespace is correct"],
        )
        assert error.details is not None
        assert len(error.suggestions) == 2
        assert "Check if deployment exists" in error.suggestions


class TestDashboardData:
    """Test DashboardData model."""

    def test_empty_creation(self):
        """Test DashboardData creation with defaults."""
        data = DashboardData()
        assert isinstance(data.operator, OperatorInfo)
        assert data.pods == []
        assert data.templates == {}
        assert isinstance(data.resources, ResourceInfo)
        assert isinstance(data.performance, PerformanceInfo)
        assert data.activity == []
        assert data.error_infos == []
        assert isinstance(data.last_update, datetime)

    def test_full_creation(self):
        """Test DashboardData with full valid data."""

        operator_info = OperatorInfo(status="RUNNING", namespace="test")
        pod_info = PodInfo(name="test-pod", sync_success=True)
        template_info = TemplateInfo(name="test.cfg", type="config", status="valid")

        activity_events = [
            ActivityEvent(
                timestamp=datetime.now(),
                type="RELOAD",
                source="dataplane",
                message="Configuration reloaded",
            )
        ]

        error_infos = [ErrorInfo(type="CONNECTION_ERROR", message="Connection failed")]

        data = DashboardData(
            operator=operator_info,
            pods=[pod_info],
            templates={"test.cfg": template_info},
            activity=activity_events,
            error_infos=error_infos,
        )
        assert data.operator.status == "RUNNING"
        assert len(data.pods) == 1
        assert len(data.templates) == 1
        assert len(data.activity) == 1
        assert len(data.error_infos) == 1

    def test_validation_with_invalid_data(self):
        """Test DashboardData validation with invalid data."""
        # Test that invalid data types are properly rejected
        with pytest.raises(ValidationError):
            DashboardData(
                pods="invalid",  # Should be list, will raise ValidationError
            )

    def test_model_serialization(self):
        """Test model can be serialized to dict."""
        data = DashboardData()
        dict_data = data.model_dump()
        assert isinstance(dict_data, dict)
        assert "operator" in dict_data
        assert "pods" in dict_data
        assert "templates" in dict_data

    def test_pod_info_edge_cases(self):
        """Test PodInfo edge cases to reach 100% coverage."""
        # Test start_time validator with invalid input (line 39)
        pod = PodInfo(
            name="test-pod", start_time=123
        )  # Invalid type, should return None
        assert pod.start_time is None

        # Test uptime calculation with minutes only (line 67)
        now = datetime.now(timezone.utc)
        start_time_minutes_ago = now - timedelta(minutes=30)
        pod = PodInfo(name="test-pod", start_time=start_time_minutes_ago)
        uptime = pod.uptime
        assert "30m" in uptime  # Should show only minutes
        assert "h" not in uptime  # No hours
        assert "d" not in uptime  # No days
