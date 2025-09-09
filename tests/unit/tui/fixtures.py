"""
Test fixtures for TUI components.

Provides mock data and helpers for testing Textual widgets and screens.
"""

from datetime import datetime

import pytest
from unittest.mock import AsyncMock, MagicMock

from haproxy_template_ic.tui.models import (
    OperatorInfo,
    PodInfo,
    TemplateInfo,
    ResourceInfo,
    PerformanceInfo,
    DashboardData,
    ErrorInfo,
)
from haproxy_template_ic.activity import ActivityEvent


@pytest.fixture
def mock_operator_info():
    """Mock OperatorInfo data."""
    return OperatorInfo(
        status="RUNNING",
        version="1.2.3",
        namespace="test-namespace",
        deployment_name="haproxy-template-ic",
        last_update=datetime.now(),
    )


@pytest.fixture
def mock_pods_data():
    """Mock pods data."""
    return [
        PodInfo(
            name="haproxy-pod-1",
            status="Running",
            ip="10.0.0.1",
            cpu="100m",
            memory="128Mi",
            synced="2m ago",
            last_sync=datetime.now(),
            sync_success=True,
        ),
        PodInfo(
            name="haproxy-pod-2",
            status="Running",
            ip="10.0.0.2",
            cpu="95m",
            memory="120Mi",
            synced="3m ago",
            last_sync=datetime.now(),
            sync_success=True,
        ),
    ]


@pytest.fixture
def mock_templates_data():
    """Mock templates data."""
    return {
        "haproxy.cfg": TemplateInfo(
            name="haproxy.cfg",
            type="config",
            size=1024,
            lines=45,
            status="valid",
            last_modified=datetime.now(),
        ),
        "host.map": TemplateInfo(
            name="host.map",
            type="map",
            size=512,
            lines=20,
            status="valid",
            last_modified=datetime.now(),
        ),
        "tls.pem": TemplateInfo(
            name="tls.pem",
            type="certificate",
            size=2048,
            lines=100,
            status="valid",
            last_modified=datetime.now(),
        ),
    }


@pytest.fixture
def mock_resources_data():
    """Mock resources data."""
    return ResourceInfo(
        resource_counts={
            "ingresses": 3,
            "services": 5,
            "secrets": 2,
            "configmaps": 1,
        },
        total=11,
        last_update=datetime.now(),
    )


@pytest.fixture
def mock_performance_data():
    """Mock performance data."""
    return PerformanceInfo(
        template_render_time=0.025,
        config_sync_time=0.150,
        last_sync_duration=0.180,
        total_syncs=150,
        failed_syncs=2,
        success_rate=0.987,
    )


@pytest.fixture
def mock_activity_data():
    """Mock activity data."""
    return [
        ActivityEvent(
            type="RELOAD",
            message="Template rendering completed successfully",
            timestamp=datetime.now().isoformat(),
            source="template-engine",
        ),
        ActivityEvent(
            type="SYNC",
            message="Configuration synchronized to HAProxy pods",
            timestamp=datetime.now().isoformat(),
            source="sync-manager",
        ),
        ActivityEvent(
            type="ERROR",
            message="Connection timeout to pod haproxy-pod-3",
            timestamp=datetime.now().isoformat(),
            source="health-checker",
        ),
    ]


@pytest.fixture
def mock_dashboard_data(
    mock_operator_info,
    mock_pods_data,
    mock_templates_data,
    mock_resources_data,
    mock_performance_data,
    mock_activity_data,
):
    """Complete mock dashboard data."""
    return DashboardData(
        operator=mock_operator_info,
        pods=mock_pods_data,
        templates=mock_templates_data,
        resources=mock_resources_data,
        performance=mock_performance_data,
        activity=mock_activity_data,
        last_update=datetime.now(),
    )


@pytest.fixture
def mock_error_dashboard_data():
    """Mock dashboard data with error state."""
    return DashboardData(
        operator=OperatorInfo(status="ERROR", namespace="test-namespace"),
        pods=[],
        templates={},
        resources=ResourceInfo(),
        performance=PerformanceInfo(),
        activity=[],
        error_infos=[
            ErrorInfo(
                type="CONNECTION_ERROR",
                message="Cannot connect to Kubernetes cluster",
                details="Connection timeout after 30 seconds",
                suggestions=[
                    "Check if the cluster is running",
                    "Verify network connectivity",
                    "Check kubeconfig settings",
                ],
            )
        ],
        last_update=datetime.now(),
    )


@pytest.fixture
def mock_data_provider(mock_dashboard_data):
    """Mock DataProvider for testing."""
    provider = MagicMock()
    provider.fetch_all_data = AsyncMock(return_value=mock_dashboard_data)
    provider.get_template_content = AsyncMock(
        return_value={
            "template_name": "haproxy.cfg",
            "source": "global\\n    daemon\\ndefaults\\n    mode http",
            "rendered": "global\\n    daemon\\ndefaults\\n    mode http\\n    timeout connect 5000ms",
            "type": "config",
            "errors": [],
        }
    )
    provider.initialize = AsyncMock(return_value=None)
    provider.check_connection = AsyncMock(return_value=True)
    return provider


@pytest.fixture
def mock_error_data_provider():
    """Mock DataProvider that returns errors."""
    provider = MagicMock()
    provider.fetch_all_data = AsyncMock(side_effect=Exception("Connection failed"))
    provider.get_template_content = AsyncMock(return_value=None)
    provider.initialize = AsyncMock(return_value=None)
    provider.check_connection = AsyncMock(return_value=False)
    return provider


@pytest.fixture
def mock_template_content():
    """Mock template content for inspector testing."""
    return {
        "template_name": "haproxy.cfg",
        "source": """global
    daemon
    maxconn 2000

defaults
    mode http
    timeout connect 5000ms
    timeout client 50000ms
    timeout server 50000ms

frontend main
    bind *:80
    {% for _, ingress in resources.get('ingresses', {}).items() %}
    {% for rule in ingress.spec.rules %}
    use_backend {{ rule.host }}_backend if { hdr(host) -i {{ rule.host }} }
    {% endfor %}
    {% endfor %}
""",
        "rendered": """global
    daemon
    maxconn 2000

defaults
    mode http
    timeout connect 5000ms
    timeout client 50000ms
    timeout server 50000ms

frontend main
    bind *:80
    use_backend example.com_backend if { hdr(host) -i example.com }
    use_backend api.example.com_backend if { hdr(host) -i api.example.com }
""",
        "type": "config",
        "errors": [],
    }


class MockTextualApp:
    """Mock Textual app for widget testing."""

    def __init__(self):
        self.messages = []
        self.screens = []
        self.current_screen = "main"

    def post_message(self, message):
        """Mock message posting."""
        self.messages.append(message)

    def push_screen(self, screen):
        """Mock screen pushing."""
        self.screens.append(screen)

    def pop_screen(self):
        """Mock screen popping."""
        if self.screens:
            return self.screens.pop()
        return None


@pytest.fixture
def mock_textual_app():
    """Mock Textual application."""
    return MockTextualApp()


# Helper functions for testing


def create_empty_resources_data():
    """Create empty resources data for testing empty states."""
    return ResourceInfo(
        resource_counts={},
        total=0,
        last_update=datetime.now(),
    )


def create_large_templates_data():
    """Create a large set of templates for testing performance."""
    templates = {}
    for i in range(50):
        templates[f"template_{i}.cfg"] = TemplateInfo(
            name=f"template_{i}.cfg",
            type="config" if i % 3 == 0 else ("map" if i % 3 == 1 else "certificate"),
            size=1024 + i * 10,
            lines=20 + i,
            status="valid",
            last_modified=datetime.now(),
        )
    return templates


def create_error_template_content():
    """Create template content with errors for testing error handling."""
    return {
        "template_name": "broken.cfg",
        "source": "invalid jinja2 template {{ unclosed",
        "rendered": None,
        "type": "config",
        "errors": [
            "Template syntax error: unexpected end of template",
            "Jinja2 parsing failed at line 1",
        ],
    }
