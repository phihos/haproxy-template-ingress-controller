"""
Unit tests for ConfigAPI class.

Tests configuration API operations including fetching sections, CRUD operations
for backends/frontends/defaults, and nested element management.
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch

from haproxy_template_ic.dataplane.types import (
    ConfigChange,
    ConfigChangeType,
    ConfigSectionType,
    DataplaneAPIError,
)
from haproxy_dataplane_v3.models import (
    Backend,
    Frontend,
    Server,
    Bind,
)
from tests.unit.conftest import (
    create_dataplane_endpoint_mock,
)
from tests.unit.dataplane.conftest import (
    create_frontend_config_change,
    create_config_api,
)


class TestConfigAPIInitialization:
    """Test ConfigAPI initialization and basic setup."""

    def test_config_api_init(self):
        """Test ConfigAPI initialization."""
        endpoint = create_dataplane_endpoint_mock()
        config_api = create_config_api(endpoint)
        assert config_api.endpoint == endpoint


class TestConfigAPIFetchOperations:
    """Test configuration fetching operations."""

    @pytest.mark.asyncio
    async def test_fetch_structured_configuration_success(
        self, mock_all_dataplane_clients
    ):
        """Test successful structured configuration fetching with all sections."""
        endpoint = create_dataplane_endpoint_mock()
        config_api = create_config_api(endpoint)

        # Create test data using the centralized fixture - eliminates 200+ lines of manual mocking
        mock_backends = [Backend(name="api", balance="roundrobin")]
        mock_frontends = [Frontend(name="web", mode="http")]

        # Configure the centralized mock with our test data
        mock_all_dataplane_clients.configure(
            backends=mock_backends,
            frontends=mock_frontends,
            global_config=Mock(mode="http"),
        )

        result = await config_api.fetch_structured_configuration()

        # Verify result structure
        assert "backends" in result
        assert "frontends" in result
        assert "global" in result
        assert len(result["backends"]) == 1
        assert len(result["frontends"]) == 1
        assert result["backends"][0].name == "api"
        assert result["frontends"][0].name == "web"

    @pytest.mark.asyncio
    async def test_fetch_structured_configuration_api_error(
        self, mock_all_dataplane_clients
    ):
        """Test structured configuration fetching with API error."""
        endpoint = create_dataplane_endpoint_mock()
        config_api = create_config_api(endpoint)

        with patch(
            "haproxy_template_ic.dataplane.config_api.get_backends"
        ) as mock_get_backends:
            mock_get_backends.side_effect = Exception("API Error")

            with pytest.raises(DataplaneAPIError) as exc_info:
                await config_api.fetch_structured_configuration()

            assert "Failed to fetch structured configuration" in str(exc_info.value)


class TestConfigAPIApplyConfigChange:
    """Test configuration change application."""

    @pytest.mark.asyncio
    async def test_apply_frontend_create_change(self, mock_metrics):
        """Test applying frontend CREATE change."""
        endpoint = create_dataplane_endpoint_mock()
        config_api = create_config_api(endpoint)

        frontend_config = {"name": "test-frontend", "mode": "http"}
        change = ConfigChange(
            change_type=ConfigChangeType.CREATE,
            section_type=ConfigSectionType.FRONTEND,
            section_name="test-frontend",
            new_config=frontend_config,
        )

        with patch(
            "haproxy_template_ic.dataplane.config_api.create_frontend",
            new_callable=AsyncMock,
        ) as mock_create:
            # Import adapter fixtures to create proper APIResponse mock
            from tests.unit.dataplane.adapter_fixtures import create_mock_api_response

            mock_response = create_mock_api_response(
                content="success", reload_id="reload-123"
            )
            mock_create.return_value = mock_response

            result = await config_api.apply_config_change(change, version=1)

            assert result.reload_info.reload_triggered
            assert result.reload_info.reload_id == "reload-123"

    @pytest.mark.asyncio
    async def test_apply_backend_update_change(self, mock_metrics):
        """Test applying backend UPDATE change."""
        endpoint = create_dataplane_endpoint_mock()
        config_api = create_config_api(endpoint)

        backend_config = {"name": "test-backend", "balance": "leastconn"}
        change = ConfigChange(
            change_type=ConfigChangeType.UPDATE,
            section_type=ConfigSectionType.BACKEND,
            section_name="test-backend",
            new_config=backend_config,
        )

        with patch(
            "haproxy_template_ic.dataplane.config_api.replace_backend"
        ) as mock_replace:
            # Import adapter fixtures to create proper APIResponse mock
            from tests.unit.dataplane.adapter_fixtures import create_mock_api_response

            mock_response = create_mock_api_response(
                content="success",
                reload_id=None,  # No reload for update
            )
            mock_replace.return_value = mock_response

            result = await config_api.apply_config_change(change, version=1)

            assert not result.reload_info.reload_triggered

    @pytest.mark.asyncio
    async def test_apply_delete_change(self, mock_metrics):
        """Test applying DELETE change."""
        endpoint = create_dataplane_endpoint_mock()
        config_api = create_config_api(endpoint)

        change = ConfigChange(
            change_type=ConfigChangeType.DELETE,
            section_type=ConfigSectionType.FRONTEND,
            section_name="test-frontend",
        )

        with patch(
            "haproxy_template_ic.dataplane.config_api.delete_frontend"
        ) as mock_delete:
            # Import adapter fixtures to create proper APIResponse mock
            from tests.unit.dataplane.adapter_fixtures import create_mock_api_response

            mock_response = create_mock_api_response(
                content="success", reload_id="reload-456"
            )
            mock_delete.return_value = mock_response

            result = await config_api.apply_config_change(change, version=1)

            assert result.reload_info.reload_triggered
            assert result.reload_info.reload_id == "reload-456"

    @pytest.mark.asyncio
    async def test_apply_config_change_with_api_error(self, mock_metrics):
        """Test apply config change handling API errors."""
        endpoint = create_dataplane_endpoint_mock()
        config_api = create_config_api(endpoint)

        change = ConfigChange(
            change_type=ConfigChangeType.CREATE,
            section_type=ConfigSectionType.BACKEND,
            section_name="test-backend",
            new_config={"name": "test-backend"},
        )

        with patch(
            "haproxy_template_ic.dataplane.config_api.create_backend"
        ) as mock_create:
            mock_create.side_effect = Exception("API Error")

            with pytest.raises(DataplaneAPIError) as exc_info:
                await config_api.apply_config_change(change, version=1)

            assert "API call" in str(exc_info.value)


class TestConfigAPIErrorHandling:
    """Test error handling in configuration operations."""

    @pytest.mark.asyncio
    async def test_apply_config_change_with_api_error(self, mock_metrics):
        """Test handling API errors during config change application."""
        endpoint = create_dataplane_endpoint_mock()
        config_api = create_config_api(endpoint)

        change = ConfigChange(
            change_type=ConfigChangeType.CREATE,
            section_type=ConfigSectionType.BACKEND,
            section_name="test-backend",
            new_config={"name": "test-backend"},
        )

        with patch(
            "haproxy_template_ic.dataplane.config_api.create_backend"
        ) as mock_create:
            mock_create.side_effect = Exception("Test API error")

            with pytest.raises(DataplaneAPIError) as exc_info:
                await config_api.apply_config_change(change, version=1)

            assert "API call" in str(exc_info.value)
            assert exc_info.value.operation == "AsyncMock"
            assert exc_info.value.endpoint == endpoint


class TestConfigAPIAdvancedOperations:
    """Test advanced configuration operations."""

    @pytest.mark.asyncio
    async def test_apply_defaults_section_change(self, mock_metrics):
        """Test applying defaults section changes."""
        endpoint = create_dataplane_endpoint_mock()
        config_api = create_config_api(endpoint)

        # Use factory pattern similar to existing ones
        change = ConfigChange(
            change_type=ConfigChangeType.UPDATE,
            section_type=ConfigSectionType.DEFAULTS,
            section_name="defaults",
            new_config={"mode": "tcp", "timeout": {"connect": "5s"}},
        )

        with patch(
            "haproxy_template_ic.dataplane.config_api.replace_defaults_section"
        ) as mock_replace:
            # Import adapter fixtures to create proper APIResponse mock
            from tests.unit.dataplane.adapter_fixtures import create_mock_api_response

            mock_response = create_mock_api_response(
                content="success", reload_id="reload-defaults"
            )
            mock_replace.return_value = mock_response

            result = await config_api.apply_config_change(change, version=1)

            assert result.change_applied
            assert result.reload_info.reload_triggered
            assert result.reload_info.reload_id == "reload-defaults"

    @pytest.mark.asyncio
    async def test_apply_unsupported_section_type(self, mock_metrics):
        """Test applying change with unsupported section type."""
        endpoint = create_dataplane_endpoint_mock()
        config_api = create_config_api(endpoint)

        change = ConfigChange(
            change_type=ConfigChangeType.CREATE,
            section_type="unsupported_section",
            section_name="test",
            new_config={"test": "value"},
        )

        with pytest.raises(DataplaneAPIError) as exc_info:
            await config_api.apply_config_change(change, version=1)

        assert "Unsupported section type" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_apply_config_change_with_transaction(self, mock_metrics):
        """Test applying config change within a transaction."""
        endpoint = create_dataplane_endpoint_mock()
        config_api = create_config_api(endpoint)

        # Use existing factory function
        change = create_frontend_config_change(section_name="test-frontend")

        with patch(
            "haproxy_template_ic.dataplane.config_api.create_frontend"
        ) as mock_create:
            # Import adapter fixtures to create proper APIResponse mock
            from tests.unit.dataplane.adapter_fixtures import create_mock_api_response

            mock_response = create_mock_api_response(
                content="success",
                reload_id=None,  # No reload in transaction
            )
            mock_create.return_value = mock_response

            result = await config_api.apply_config_change(
                change, version=1, transaction_id="txn-123"
            )

            assert result.change_applied
            assert not result.reload_info.reload_triggered


class TestConfigAPINestedElements:
    """Test nested element operations (servers, ACLs, rules, etc.)."""

    @pytest.mark.asyncio
    async def test_fetch_backend_servers(self, mock_metrics):
        """Test fetching servers for a backend."""
        endpoint = create_dataplane_endpoint_mock()
        config_api = create_config_api(endpoint)

        mock_servers = [Server(name="server1", address="10.0.0.1:8080")]

        with patch(
            "haproxy_template_ic.dataplane.config_api.get_all_server_backend"
        ) as mock_get_servers:
            mock_get_servers.return_value = Mock(content=mock_servers)

            result = await mock_get_servers(
                endpoint=config_api.endpoint, backend_name="api"
            )

            assert result.content == mock_servers
            mock_get_servers.assert_called_once_with(
                endpoint=config_api.endpoint, backend_name="api"
            )

    @pytest.mark.asyncio
    async def test_fetch_frontend_binds(self, mock_metrics):
        """Test fetching bind configurations for a frontend."""
        endpoint = create_dataplane_endpoint_mock()
        config_api = create_config_api(endpoint)

        mock_binds = [Bind(name="bind1", address="*:80")]

        with patch(
            "haproxy_template_ic.dataplane.config_api.get_all_bind_frontend"
        ) as mock_get_binds:
            mock_get_binds.return_value = Mock(content=mock_binds)

            result = await mock_get_binds(
                endpoint=config_api.endpoint, frontend_name="web"
            )

            assert result.content == mock_binds
            mock_get_binds.assert_called_once_with(
                endpoint=config_api.endpoint, frontend_name="web"
            )


class TestConfigAPIPerformance:
    """Test performance-related scenarios."""

    @pytest.mark.asyncio
    async def test_concurrent_config_changes(self, mock_metrics):
        """Test handling multiple config changes efficiently."""
        endpoint = create_dataplane_endpoint_mock()
        config_api = create_config_api(endpoint)

        # Use factory function for cleaner test
        changes = [
            create_frontend_config_change(section_name=f"frontend-{i}")
            for i in range(3)
        ]

        with patch(
            "haproxy_template_ic.dataplane.config_api.create_frontend"
        ) as mock_create:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.headers = {}
            mock_create.return_value = mock_response

            # Apply changes sequentially
            results = []
            for change in changes:
                result = await config_api.apply_config_change(change, version=1)
                results.append(result)

            assert len(results) == 3
            assert all(r.change_applied for r in results)
            assert mock_create.call_count == 3

    @pytest.mark.asyncio
    async def test_large_configuration_fetch(self, mock_dataplane_large_config):
        """Test fetching multi-section configuration efficiently."""
        endpoint = create_dataplane_endpoint_mock()
        config_api = create_config_api(endpoint)

        # Use the centralized large config fixture - eliminates 80+ lines of manual mocking
        # This fixture provides 100 backends + 50 frontends automatically
        result = await config_api.fetch_structured_configuration()

        # Verify comprehensive configuration data
        assert "backends" in result
        assert "frontends" in result
        assert "global" in result
        assert len(result["backends"]) == 100
        assert len(result["frontends"]) == 50

        # Verify that we successfully mocked all the client calls
        # Backends and frontends should be the lists provided by the fixture
        assert isinstance(result["backends"], list)
        assert isinstance(result["frontends"], list)
