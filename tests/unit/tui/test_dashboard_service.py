"""
Unit tests for DashboardService.

Tests the main service layer including data fetching, error handling,
and data transformation logic.
"""

import pytest
from unittest.mock import AsyncMock
from datetime import datetime

from haproxy_template_ic.tui.dashboard_service import DashboardService
from haproxy_template_ic.tui.models import (
    DashboardData,
    OperatorInfo,
    PodInfo,
    TemplateInfo,
    PerformanceInfo,
)
from haproxy_template_ic.tui.exceptions import (
    ConnectionError,
)
from haproxy_template_ic.activity import ActivityEvent


class TestDashboardService:
    """Test DashboardService class."""

    @pytest.fixture
    def dashboard_service(self):
        """Create a DashboardService instance."""
        return DashboardService(
            namespace="test-namespace",
            context="test-context",
            deployment_name="test-deployment",
        )

    @pytest.fixture
    def mock_socket_client(self):
        """Mock socket client."""
        mock = AsyncMock()
        return mock

    @pytest.fixture
    def sample_dashboard_data(self):
        """Sample dashboard data response."""
        return {
            "operator": {
                "status": "RUNNING",
                "namespace": "test-namespace",
                "version": "1.0.0",
            },
            "pods": [
                {
                    "name": "haproxy-pod-1",
                    "ip": "10.0.0.1",
                    "sync_success": True,
                    "last_sync": "2024-01-15T10:30:00Z",
                }
            ],
            "performance": {
                "template_render": {"p50": 50.0, "p95": 100.0, "p99": 200.0},
                "sync_success_rate": 0.95,
            },
        }

    def test_init(self):
        """Test DashboardService initialization."""
        service = DashboardService(
            namespace="test-ns",
            context="test-ctx",
            deployment_name="test-deploy",
            socket_path="/test/path",
        )
        assert service.namespace == "test-ns"
        assert service.context == "test-ctx"
        assert service.deployment_name == "test-deploy"
        assert service.socket_path == "/test/path"

    @pytest.mark.asyncio
    async def test_initialize(self, dashboard_service):
        """Test service initialization."""
        await dashboard_service.initialize()
        # Should not raise any errors

    @pytest.mark.asyncio
    async def test_fetch_all_data_success(
        self, dashboard_service, mock_socket_client, sample_dashboard_data
    ):
        """Test successful data fetching."""
        dashboard_service.socket_client = mock_socket_client

        # Mock successful socket responses
        mock_socket_client.execute_command.side_effect = [
            sample_dashboard_data,  # dump dashboard
            {},  # dump deployments
            {"activity": []},  # dump activity
            {"config": {}},  # dump config
        ]

        result = await dashboard_service.fetch_all_data()

        assert isinstance(result, DashboardData)
        assert result.operator.status == "RUNNING"
        assert len(result.pods) == 1
        assert result.pods[0].name == "haproxy-pod-1"

    @pytest.mark.asyncio
    async def test_fetch_all_data_connection_error(
        self, dashboard_service, mock_socket_client
    ):
        """Test data fetching with connection error."""
        dashboard_service.socket_client = mock_socket_client

        # Mock connection error
        connection_error = ConnectionError("connection error")
        mock_socket_client.execute_command.side_effect = connection_error

        result = await dashboard_service.fetch_all_data()

        assert isinstance(result, DashboardData)
        assert result.operator.status == "ERROR"
        assert len(result.error_infos) == 1
        assert result.error_infos[0].type == "CONNECTION_ERROR"

    @pytest.mark.asyncio
    async def test_get_template_content_success(
        self, dashboard_service, mock_socket_client
    ):
        """Test successful template content retrieval."""
        dashboard_service.socket_client = mock_socket_client

        # Mock successful responses
        mock_socket_client.execute_command.side_effect = [
            {
                "result": {
                    "source": "{% for item in items %}{{ item }}{% endfor %}",
                    "type": "config",
                }
            },
            {"result": {"content": "rendered content here", "type": "config"}},
        ]

        result = await dashboard_service.get_template_content("test.cfg")

        assert result is not None
        assert result["template_name"] == "test.cfg"
        assert result["source"] == "{% for item in items %}{{ item }}{% endfor %}"
        assert result["rendered"] == "rendered content here"
        assert result["type"] == "config"
        assert len(result["errors"]) == 0

    @pytest.mark.asyncio
    async def test_get_template_content_snippet_type(
        self, dashboard_service, mock_socket_client
    ):
        """Test template content retrieval for snippets (no rendered content)."""
        dashboard_service.socket_client = mock_socket_client

        # Mock source response for snippet
        mock_socket_client.execute_command.return_value = {
            "result": {"source": "snippet content", "type": "snippet"}
        }

        result = await dashboard_service.get_template_content("test-snippet")

        assert result is not None
        assert result["type"] == "snippet"
        assert result["source"] == "snippet content"
        assert result["rendered"] is None
        # Should only call socket once for snippet (no rendered content fetch)
        mock_socket_client.execute_command.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_template_content_error(
        self, dashboard_service, mock_socket_client
    ):
        """Test template content retrieval with error."""
        dashboard_service.socket_client = mock_socket_client

        # Mock error response
        mock_socket_client.execute_command.side_effect = Exception("Socket error")

        result = await dashboard_service.get_template_content("test.cfg")

        assert result is not None
        assert result["template_name"] == "test.cfg"
        assert result["source"] is None
        assert result["rendered"] is None
        assert len(result["errors"]) == 1
        assert "Exception: Socket error" in result["errors"][0]


class TestDashboardServiceErrorHandling:
    """Test error handling methods in DashboardService."""

    def test_is_connection_error(self):
        """Test connection error detection."""
        service = DashboardService("test-ns")

        # Test connection error cases
        assert service._is_connection_error("connection refused") is True
        assert service._is_connection_error("connection timed out") is True
        assert service._is_connection_error("dial tcp: connection reset") is True
        assert service._is_connection_error("network is unreachable") is True
        assert service._is_connection_error("certificate error") is True

        # Test non-connection error cases
        assert service._is_connection_error("invalid json") is False
        assert service._is_connection_error("template not found") is False
        assert service._is_connection_error("random error") is False

    def test_extract_error_summary(self):
        """Test error summary extraction."""
        service = DashboardService("test-ns")

        # Test dial tcp pattern
        error = Exception("dial tcp 10.0.0.1:5555: connection refused")
        summary = service._extract_error_summary(error)
        assert "connection refused" in summary.lower()

        # Test couldn't get pattern
        error = Exception("couldn't get pods: network unreachable")
        summary = service._extract_error_summary(error)
        assert "network unreachable" in summary.lower()

        # Test GET request pattern
        error = Exception('Get "https://api.cluster.local": timeout')
        summary = service._extract_error_summary(error)
        assert "timeout" in summary.lower()

        # Test long error message
        long_error = Exception("a" * 100)
        summary = service._extract_error_summary(long_error)
        assert len(summary) <= 80
        assert summary.endswith("...")

    def test_categorize_error_connection(self):
        """Test error categorization for connection errors."""
        service = DashboardService("test-ns")

        error = Exception("dial tcp: connection refused")
        error_info = service._categorize_error(error)

        assert error_info.type == "CONNECTION_ERROR"
        assert "Cannot connect to Kubernetes cluster" in error_info.message
        assert "kind get clusters" in str(error_info.suggestions)

    def test_categorize_error_authentication(self):
        """Test error categorization for auth errors."""
        service = DashboardService("test-ns")

        error = Exception("401 unauthorized")
        error_info = service._categorize_error(error)

        assert (
            error_info.type == "CONNECTION_ERROR"
        )  # 401 unauthorized is in connection keywords
        assert "Cannot connect to Kubernetes cluster" in error_info.message
        assert "Check kubectl connectivity" in str(error_info.suggestions)

    def test_categorize_error_not_found(self):
        """Test error categorization for not found errors."""
        service = DashboardService("test-ns")

        error = Exception("deployment not found")
        error_info = service._categorize_error(error)

        assert error_info.type == "NO_RESOURCES"
        assert "Resources not found" in error_info.message
        assert "test-ns" in error_info.message

    def test_categorize_error_generic(self):
        """Test error categorization for generic API errors."""
        service = DashboardService("test-ns")

        error = Exception("some random api error")
        error_info = service._categorize_error(error)

        assert error_info.type == "API_ERROR"
        assert "Kubernetes API issue" in error_info.message


class TestDashboardServiceDataExtraction:
    """Test data extraction methods in DashboardService."""

    def test_extract_operator_info(self):
        """Test operator info extraction."""
        service = DashboardService("test-ns")

        data = {
            "operator": {
                "status": "RUNNING",
                "namespace": "test-ns",
                "version": "1.0.0",
            }
        }

        operator_info = service._extract_operator_info(data)

        assert isinstance(operator_info, OperatorInfo)
        assert operator_info.status == "RUNNING"
        assert operator_info.namespace == "test-ns"
        assert operator_info.version == "1.0.0"

    def test_extract_operator_info_empty(self):
        """Test operator info extraction with empty data."""
        service = DashboardService("test-ns")

        operator_info = service._extract_operator_info({})

        assert isinstance(operator_info, OperatorInfo)
        # Should use default values

    def test_process_socket_pods(self):
        """Test socket pod processing."""
        service = DashboardService("test-ns")

        dashboard_pods = [
            {
                "name": "pod-1",
                "ip": "10.0.0.1",
                "sync_success": True,
                "last_sync": "2024-01-15T10:30:00Z",
            },
            {
                "name": "pod-2",
                "ip": "10.0.0.2",
                "sync_success": False,
                "last_sync": None,
            },
        ]

        activity_events = [
            ActivityEvent(
                type="SYNC",
                message="Sync completed",
                timestamp=datetime.now().isoformat(),
                source="dataplane",
                metadata={"pod_ip": "10.0.0.1", "config_changed": True},
            )
        ]

        result = service._process_socket_pods(dashboard_pods, activity_events)

        assert len(result) == 2
        assert all(isinstance(pod, PodInfo) for pod in result)
        assert result[0].name == "pod-1"
        assert result[0].sync_success is True
        assert result[1].name == "pod-2"
        assert result[1].sync_success is False

    def test_process_socket_pods_empty(self):
        """Test socket pod processing with empty data."""
        service = DashboardService("test-ns")

        result = service._process_socket_pods([], None)

        assert result == []

    def test_extract_performance_info(self):
        """Test performance info extraction."""
        service = DashboardService("test-ns")

        data = {
            "performance": {
                "template_render": {"p50": 50.0, "p95": 100.0, "p99": 200.0},
                "dataplane_api": {
                    "p50": 25.0,
                    "p95": "N/A",  # Test N/A handling
                    "p99": None,
                },
                "sync_success_rate": 0.95,
                "total_syncs": 100,
                "failed_syncs": 5,
            }
        }

        performance_info = service._extract_performance_info(data)

        assert isinstance(performance_info, PerformanceInfo)
        assert performance_info.template_render.p50 == 50.0
        assert performance_info.template_render.p95 == 100.0
        assert performance_info.dataplane_api.p50 == 25.0
        assert performance_info.dataplane_api.p95 is None  # N/A converted to None
        assert performance_info.sync_success_rate == 0.95
        assert performance_info.total_syncs == 100
        assert performance_info.failed_syncs == 5

    def test_extract_activity_events(self):
        """Test activity events extraction."""
        service = DashboardService("test-ns")

        activity_data = {
            "activity": [
                {
                    "timestamp": "2024-01-15T10:30:00Z",
                    "type": "RELOAD",
                    "source": "dataplane",
                    "message": "Configuration reloaded",
                },
                {
                    "timestamp": "2024-01-15T10:29:00Z",
                    "type": "SYNC",
                    "source": "operator",
                    "message": "Resource synchronized",
                },
            ]
        }

        result = service._extract_activity_events(activity_data)

        assert len(result) == 2
        assert all(isinstance(event, ActivityEvent) for event in result)
        assert result[0].type == "RELOAD"
        assert result[1].type == "SYNC"

    def test_extract_activity_events_with_error(self):
        """Test activity events extraction with error."""
        service = DashboardService("test-ns")

        activity_data = {"error": "Failed to get activity"}

        result = service._extract_activity_events(activity_data)

        assert result == []

    def test_calculate_sync_status(self):
        """Test sync status calculation."""
        service = DashboardService("test-ns")

        # Test successful sync
        pod_data = {"sync_success": True, "last_sync": "2024-01-15T10:30:00Z"}
        status = service._calculate_sync_status(pod_data)
        assert "ago" in status  # Should show time ago

        # Test failed sync
        pod_data = {"sync_success": False, "last_sync": "2024-01-15T10:30:00Z"}
        status = service._calculate_sync_status(pod_data)
        assert status == "Failed"

        # Test no sync data
        pod_data = {"sync_success": True, "last_sync": None}
        status = service._calculate_sync_status(pod_data)
        assert status == "Unknown"


class TestDashboardServiceTemplates:
    """Test template-related methods in DashboardService."""

    def test_extract_templates_info_with_rendered_content(self):
        """Test template extraction with rendered content."""
        service = DashboardService("test-ns")

        config_data = {
            "haproxy_config_context": {
                "rendered_config": {"content": "global\n    daemon\n"},
                "rendered_content": [
                    {
                        "filename": "host.map",
                        "content": "example.com backend1\n",
                        "content_type": "map",
                    },
                    {
                        "filename": "tls.pem",
                        "content": "-----BEGIN CERTIFICATE-----\n",
                        "content_type": "certificate",
                    },
                ],
            },
            "config": {
                "template_snippets": {
                    "backend-name": {"template": "backend_{{ name }}"}
                }
            },
        }

        deployment_data = {
            "deployment_history": {
                "http://10.0.0.1:5555": {
                    "success": True,
                    "template_change_timestamps": {
                        "haproxy.cfg": "2024-01-15T10:30:00Z",
                        "host.map": "2024-01-15T10:31:00Z",
                    },
                }
            }
        }

        result = service._extract_templates_info(config_data, deployment_data)

        assert len(result) >= 3  # haproxy.cfg, host.map, backend-name snippet
        assert "haproxy.cfg" in result
        assert "host.map" in result
        assert "backend-name" in result

        # Check haproxy.cfg
        haproxy_template = result["haproxy.cfg"]
        assert haproxy_template.type == "config"
        assert haproxy_template.status == "valid"
        assert haproxy_template.size > 0

        # Check map file
        host_map = result["host.map"]
        assert host_map.type == "map"
        assert host_map.status == "valid"

        # Check snippet
        snippet = result["backend-name"]
        assert snippet.type == "snippet"
        assert snippet.status == "valid"

    def test_extract_templates_info_configured_only(self):
        """Test template extraction with only configured templates."""
        service = DashboardService("test-ns")

        config_data = {
            "config": {
                "haproxy_config": {"template": "global\n    daemon\n"},
                "maps": {"host.map": {"template": "{{ hosts }}"}},
                "certificates": {"tls.pem": {"template": "{{ cert_data }}"}},
            }
        }

        result = service._extract_templates_info(config_data)

        assert len(result) == 3
        assert all(template.status == "configured" for template in result.values())
        assert all(template.size == 0 for template in result.values())

    def test_add_template_timestamps_from_deployment_history(self):
        """Test adding timestamps from deployment history."""
        service = DashboardService("test-ns")

        templates = {
            "haproxy.cfg": TemplateInfo(name="haproxy.cfg", type="config"),
            "host.map": TemplateInfo(name="host.map", type="map"),
        }

        deployment_data = {
            "deployment_history": {
                "http://10.0.0.1:5555": {
                    "success": True,
                    "template_change_timestamps": {
                        "haproxy.cfg": "2024-01-15T10:30:00Z",
                        "host.map": "2024-01-15T10:31:00Z",
                    },
                },
                "http://10.0.0.2:5555": {
                    "success": True,
                    "template_change_timestamps": {
                        "haproxy.cfg": "2024-01-15T10:32:00Z"  # More recent
                    },
                },
            }
        }

        service._add_template_timestamps_from_deployment_history(
            templates, deployment_data
        )

        # Should use most recent timestamp
        assert templates["haproxy.cfg"].last_modified is not None
        assert templates["host.map"].last_modified is not None


class TestDashboardServiceEnhanced:
    """Enhanced tests for DashboardService coverage improvement."""

    @pytest.fixture
    def dashboard_service(self):
        """Create a DashboardService instance."""
        return DashboardService(
            namespace="test-namespace",
            context="test-context",
            deployment_name="test-deployment",
        )

    @pytest.fixture
    def mock_socket_client(self):
        """Mock socket client."""
        return AsyncMock()

    @pytest.mark.asyncio
    async def test_get_template_content_error_handling(
        self, dashboard_service, mock_socket_client
    ):
        """Test template content retrieval with various error conditions."""
        dashboard_service.socket_client = mock_socket_client

        # Test source error
        mock_socket_client.execute_command.side_effect = [
            {"error": "Source not found"},  # Source command fails
            {"result": {"content": "rendered content"}},  # Rendered succeeds
        ]

        result = await dashboard_service.get_template_content("test.cfg")

        assert result is not None
        assert "Source: Source not found" in result["errors"]
        assert result["rendered"] == "rendered content"

    @pytest.mark.asyncio
    async def test_get_template_content_rendered_error(
        self, dashboard_service, mock_socket_client
    ):
        """Test template content retrieval when rendered content fails."""
        dashboard_service.socket_client = mock_socket_client

        mock_socket_client.execute_command.side_effect = [
            {
                "result": {"source": "source content", "type": "haproxy_config"}
            },  # Source succeeds
            {"error": "Rendering failed"},  # Rendered fails
        ]

        result = await dashboard_service.get_template_content("test.cfg")

        assert result is not None
        assert result["source"] == "source content"
        assert "Rendered: Rendering failed" in result["errors"]

    @pytest.mark.asyncio
    async def test_get_template_content_snippet_type(
        self, dashboard_service, mock_socket_client
    ):
        """Test template content retrieval for snippet templates."""
        dashboard_service.socket_client = mock_socket_client

        mock_socket_client.execute_command.side_effect = [
            {
                "result": {"source": "snippet content", "type": "snippet"}
            },  # Source succeeds with snippet type
        ]

        result = await dashboard_service.get_template_content("test-snippet")

        assert result is not None
        assert result["source"] == "snippet content"
        assert result["type"] == "snippet"
        # Should not have called for rendered content (snippets don't have rendered versions)
        assert mock_socket_client.execute_command.call_count == 1

    @pytest.mark.asyncio
    async def test_get_template_content_unknown_type_from_rendered(
        self, dashboard_service, mock_socket_client
    ):
        """Test template content type determination from rendered result."""
        dashboard_service.socket_client = mock_socket_client

        mock_socket_client.execute_command.side_effect = [
            {"result": {"source": "source content"}},  # Source without type
            {
                "result": {"content": "rendered content", "type": "map"}
            },  # Rendered with type
        ]

        result = await dashboard_service.get_template_content("test.map")

        assert result is not None
        assert result["type"] == "map"  # Should get type from rendered result

    def test_service_initialization_parameters(self, dashboard_service):
        """Test service initialization with parameters."""
        # Test that service can be initialized with correct parameters
        assert dashboard_service.namespace == "test-namespace"
        assert dashboard_service.context == "test-context"
        assert dashboard_service.deployment_name == "test-deployment"

    @pytest.mark.asyncio
    async def test_socket_client_error_handling(
        self, dashboard_service, mock_socket_client
    ):
        """Test socket client error handling."""
        dashboard_service.socket_client = mock_socket_client
        mock_socket_client.execute_command.side_effect = Exception("Socket error")

        # Should handle socket errors gracefully in get_template_content
        result = await dashboard_service.get_template_content("test.cfg")
        assert result is not None
        assert len(result["errors"]) > 0
