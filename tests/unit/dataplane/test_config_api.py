"""
Unit tests for ConfigAPI class.

Tests configuration API operations including fetching sections, CRUD operations
for backends/frontends/defaults, and nested element management.
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch

from haproxy_template_ic.dataplane.config_api import ConfigAPI
from haproxy_template_ic.dataplane.types import (
    ConfigChange,
    ConfigChangeType,
    ConfigSectionType,
    DataplaneAPIError,
)
from haproxy_dataplane_v3.models import (
    Backend,
    Frontend,
    Defaults,
    Server,
    Bind,
)
from tests.unit.conftest import (
    create_dataplane_endpoint_mock,
)
from tests.unit.dataplane.conftest import (
    create_frontend_config_change,
)


class TestConfigAPIInitialization:
    """Test ConfigAPI initialization and basic setup."""

    def test_config_api_init(self):
        """Test ConfigAPI initialization."""
        endpoint = create_dataplane_endpoint_mock()
        config_api = ConfigAPI(endpoint)
        assert config_api.endpoint == endpoint


class TestConfigAPIFetchOperations:
    """Test configuration fetching operations."""

    @pytest.mark.asyncio
    async def test_fetch_structured_configuration_success(self, mock_metrics):
        """Test successful structured configuration fetching with all sections."""
        endpoint = create_dataplane_endpoint_mock()
        config_api = ConfigAPI(endpoint)

        mock_backends = [Backend(name="api", balance="roundrobin")]
        mock_frontends = [Frontend(name="web", mode="http")]
        mock_defaults = [Defaults(mode="http")]

        from unittest.mock import AsyncMock
        from contextlib import ExitStack

        with ExitStack() as stack:
            # Top-level section mocks
            mock_get_backends = stack.enter_context(
                patch(
                    "haproxy_template_ic.dataplane.config_api.get_backends",
                    new_callable=AsyncMock,
                )
            )
            mock_get_frontends = stack.enter_context(
                patch(
                    "haproxy_template_ic.dataplane.config_api.get_frontends",
                    new_callable=AsyncMock,
                )
            )
            mock_get_defaults = stack.enter_context(
                patch(
                    "haproxy_template_ic.dataplane.config_api.get_defaults_sections",
                    new_callable=AsyncMock,
                )
            )
            mock_get_global = stack.enter_context(
                patch(
                    "haproxy_template_ic.dataplane.config_api.get_global",
                    new_callable=AsyncMock,
                )
            )
            mock_get_userlists = stack.enter_context(
                patch(
                    "haproxy_template_ic.dataplane.config_api.get_userlists",
                    new_callable=AsyncMock,
                )
            )
            mock_get_caches = stack.enter_context(
                patch(
                    "haproxy_template_ic.dataplane.config_api.get_caches",
                    new_callable=AsyncMock,
                )
            )
            mock_get_fcgi_apps = stack.enter_context(
                patch(
                    "haproxy_template_ic.dataplane.config_api.get_fcgi_apps",
                    new_callable=AsyncMock,
                )
            )
            mock_get_http_errors = stack.enter_context(
                patch(
                    "haproxy_template_ic.dataplane.config_api.get_http_errors_sections",
                    new_callable=AsyncMock,
                )
            )
            mock_get_log_forwards = stack.enter_context(
                patch(
                    "haproxy_template_ic.dataplane.config_api.get_log_forwards",
                    new_callable=AsyncMock,
                )
            )
            mock_get_mailers = stack.enter_context(
                patch(
                    "haproxy_template_ic.dataplane.config_api.get_mailers_sections",
                    new_callable=AsyncMock,
                )
            )
            mock_get_resolvers = stack.enter_context(
                patch(
                    "haproxy_template_ic.dataplane.config_api.get_resolvers",
                    new_callable=AsyncMock,
                )
            )
            mock_get_peers = stack.enter_context(
                patch(
                    "haproxy_template_ic.dataplane.config_api.get_peer_sections",
                    new_callable=AsyncMock,
                )
            )
            mock_get_rings = stack.enter_context(
                patch(
                    "haproxy_template_ic.dataplane.config_api.get_rings",
                    new_callable=AsyncMock,
                )
            )
            mock_get_programs = stack.enter_context(
                patch(
                    "haproxy_template_ic.dataplane.config_api.get_programs",
                    new_callable=AsyncMock,
                )
            )

            # Nested element mocks (critical for performance)
            mock_get_servers = stack.enter_context(
                patch(
                    "haproxy_template_ic.dataplane.config_api.get_all_server_backend",
                    new_callable=AsyncMock,
                )
            )
            mock_get_backend_acls = stack.enter_context(
                patch(
                    "haproxy_template_ic.dataplane.config_api.get_all_acl_backend",
                    new_callable=AsyncMock,
                )
            )
            mock_get_backend_request_rules = stack.enter_context(
                patch(
                    "haproxy_template_ic.dataplane.config_api.get_all_http_request_rule_backend",
                    new_callable=AsyncMock,
                )
            )
            mock_get_backend_response_rules = stack.enter_context(
                patch(
                    "haproxy_template_ic.dataplane.config_api.get_all_http_response_rule_backend",
                    new_callable=AsyncMock,
                )
            )
            mock_get_backend_filters = stack.enter_context(
                patch(
                    "haproxy_template_ic.dataplane.config_api.get_all_filter_backend",
                    new_callable=AsyncMock,
                )
            )
            mock_get_backend_logs = stack.enter_context(
                patch(
                    "haproxy_template_ic.dataplane.config_api.get_all_log_target_backend",
                    new_callable=AsyncMock,
                )
            )
            mock_get_binds = stack.enter_context(
                patch(
                    "haproxy_template_ic.dataplane.config_api.get_all_bind_frontend",
                    new_callable=AsyncMock,
                )
            )
            mock_get_frontend_acls = stack.enter_context(
                patch(
                    "haproxy_template_ic.dataplane.config_api.get_all_acl_frontend",
                    new_callable=AsyncMock,
                )
            )
            mock_get_frontend_request_rules = stack.enter_context(
                patch(
                    "haproxy_template_ic.dataplane.config_api.get_all_http_request_rule_frontend",
                    new_callable=AsyncMock,
                )
            )
            mock_get_frontend_response_rules = stack.enter_context(
                patch(
                    "haproxy_template_ic.dataplane.config_api.get_all_http_response_rule_frontend",
                    new_callable=AsyncMock,
                )
            )
            mock_get_frontend_filters = stack.enter_context(
                patch(
                    "haproxy_template_ic.dataplane.config_api.get_all_filter_frontend",
                    new_callable=AsyncMock,
                )
            )
            mock_get_frontend_logs = stack.enter_context(
                patch(
                    "haproxy_template_ic.dataplane.config_api.get_all_log_target_frontend",
                    new_callable=AsyncMock,
                )
            )
            mock_get_global_logs = stack.enter_context(
                patch(
                    "haproxy_template_ic.dataplane.config_api.get_all_log_target_global",
                    new_callable=AsyncMock,
                )
            )
            stack.enter_context(
                patch(
                    "haproxy_template_ic.dataplane.config_api.get_metrics_collector",
                    return_value=mock_metrics,
                )
            )
            # Setup APIResponse return values using proper adapter fixtures
            from tests.unit.dataplane.adapter_fixtures import create_mock_api_response

            mock_get_backends.return_value = create_mock_api_response(
                content=mock_backends
            )
            mock_get_frontends.return_value = create_mock_api_response(
                content=mock_frontends
            )
            mock_get_defaults.return_value = create_mock_api_response(
                content=mock_defaults
            )
            mock_get_global.return_value = create_mock_api_response(
                content=Mock(mode="http")
            )
            mock_get_userlists.return_value = create_mock_api_response(content=[])
            mock_get_caches.return_value = create_mock_api_response(content=[])
            mock_get_fcgi_apps.return_value = create_mock_api_response(content=[])
            mock_get_http_errors.return_value = create_mock_api_response(content=[])
            mock_get_log_forwards.return_value = create_mock_api_response(content=[])
            mock_get_mailers.return_value = create_mock_api_response(content=[])
            mock_get_resolvers.return_value = create_mock_api_response(content=[])
            mock_get_peers.return_value = create_mock_api_response(content=[])
            mock_get_rings.return_value = create_mock_api_response(content=[])
            mock_get_programs.return_value = create_mock_api_response(content=[])

            # Setup nested element mocks with empty content (prevents HTTP timeout calls!)
            for mock_func in [
                mock_get_servers,
                mock_get_backend_acls,
                mock_get_backend_request_rules,
                mock_get_backend_response_rules,
                mock_get_backend_filters,
                mock_get_backend_logs,
                mock_get_binds,
                mock_get_frontend_acls,
                mock_get_frontend_request_rules,
                mock_get_frontend_response_rules,
                mock_get_frontend_filters,
                mock_get_frontend_logs,
                mock_get_global_logs,
            ]:
                mock_func.return_value = create_mock_api_response(content=[])

            result = await config_api.fetch_structured_configuration()

            # Verify result structure
            assert "backends" in result
            assert "frontends" in result
            assert "defaults" in result
            assert len(result["backends"]) == 1
            assert len(result["frontends"]) == 1
            assert result["backends"][0].name == "api"
            assert result["frontends"][0].name == "web"

    @pytest.mark.asyncio
    async def test_fetch_structured_configuration_api_error(self, mock_metrics):
        """Test structured configuration fetching with API error."""
        endpoint = create_dataplane_endpoint_mock()
        config_api = ConfigAPI(endpoint)

        with (
            patch(
                "haproxy_template_ic.dataplane.config_api.get_backends"
            ) as mock_get_backends,
            patch(
                "haproxy_template_ic.dataplane.config_api.get_metrics_collector",
                return_value=mock_metrics,
            ),
        ):
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
        config_api = ConfigAPI(endpoint)

        frontend_config = {"name": "test-frontend", "mode": "http"}
        change = ConfigChange(
            change_type=ConfigChangeType.CREATE,
            section_type=ConfigSectionType.FRONTEND,
            section_name="test-frontend",
            new_config=frontend_config,
        )

        with (
            patch(
                "haproxy_template_ic.dataplane.config_api.create_frontend",
                new_callable=AsyncMock,
            ) as mock_create,
            patch(
                "haproxy_template_ic.dataplane.config_api.get_metrics_collector",
                return_value=mock_metrics,
            ),
        ):
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
        config_api = ConfigAPI(endpoint)

        backend_config = {"name": "test-backend", "balance": "leastconn"}
        change = ConfigChange(
            change_type=ConfigChangeType.UPDATE,
            section_type=ConfigSectionType.BACKEND,
            section_name="test-backend",
            new_config=backend_config,
        )

        with (
            patch(
                "haproxy_template_ic.dataplane.config_api.replace_backend"
            ) as mock_replace,
            patch(
                "haproxy_template_ic.dataplane.config_api.get_metrics_collector",
                return_value=mock_metrics,
            ),
        ):
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
        config_api = ConfigAPI(endpoint)

        change = ConfigChange(
            change_type=ConfigChangeType.DELETE,
            section_type=ConfigSectionType.FRONTEND,
            section_name="test-frontend",
        )

        with (
            patch(
                "haproxy_template_ic.dataplane.config_api.delete_frontend"
            ) as mock_delete,
            patch(
                "haproxy_template_ic.dataplane.config_api.get_metrics_collector",
                return_value=mock_metrics,
            ),
        ):
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
        config_api = ConfigAPI(endpoint)

        change = ConfigChange(
            change_type=ConfigChangeType.CREATE,
            section_type=ConfigSectionType.BACKEND,
            section_name="test-backend",
            new_config={"name": "test-backend"},
        )

        with (
            patch(
                "haproxy_template_ic.dataplane.config_api.create_backend"
            ) as mock_create,
            patch(
                "haproxy_template_ic.dataplane.config_api.get_metrics_collector",
                return_value=mock_metrics,
            ),
        ):
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
        config_api = ConfigAPI(endpoint)

        change = ConfigChange(
            change_type=ConfigChangeType.CREATE,
            section_type=ConfigSectionType.BACKEND,
            section_name="test-backend",
            new_config={"name": "test-backend"},
        )

        with (
            patch(
                "haproxy_template_ic.dataplane.config_api.create_backend"
            ) as mock_create,
            patch(
                "haproxy_template_ic.dataplane.config_api.get_metrics_collector",
                return_value=mock_metrics,
            ),
        ):
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
        config_api = ConfigAPI(endpoint)

        # Use factory pattern similar to existing ones
        change = ConfigChange(
            change_type=ConfigChangeType.UPDATE,
            section_type=ConfigSectionType.DEFAULTS,
            section_name="defaults",
            new_config={"mode": "tcp", "timeout": {"connect": "5s"}},
        )

        with (
            patch(
                "haproxy_template_ic.dataplane.config_api.replace_defaults_section"
            ) as mock_replace,
            patch(
                "haproxy_template_ic.dataplane.config_api.get_metrics_collector",
                return_value=mock_metrics,
            ),
        ):
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
        config_api = ConfigAPI(endpoint)

        change = ConfigChange(
            change_type=ConfigChangeType.CREATE,
            section_type="unsupported_section",
            section_name="test",
            new_config={"test": "value"},
        )

        with patch(
            "haproxy_template_ic.dataplane.config_api.get_metrics_collector",
            return_value=mock_metrics,
        ):
            with pytest.raises(DataplaneAPIError) as exc_info:
                await config_api.apply_config_change(change, version=1)

            assert "Unsupported section type" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_apply_config_change_with_transaction(self, mock_metrics):
        """Test applying config change within a transaction."""
        endpoint = create_dataplane_endpoint_mock()
        config_api = ConfigAPI(endpoint)

        # Use existing factory function
        change = create_frontend_config_change(section_name="test-frontend")

        with (
            patch(
                "haproxy_template_ic.dataplane.config_api.create_frontend"
            ) as mock_create,
            patch(
                "haproxy_template_ic.dataplane.config_api.get_metrics_collector",
                return_value=mock_metrics,
            ),
        ):
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
        config_api = ConfigAPI(endpoint)

        mock_servers = [Server(name="server1", address="10.0.0.1:8080")]

        with (
            patch(
                "haproxy_template_ic.dataplane.config_api.get_all_server_backend"
            ) as mock_get_servers,
            patch(
                "haproxy_template_ic.dataplane.config_api.get_metrics_collector",
                return_value=mock_metrics,
            ),
        ):
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
        config_api = ConfigAPI(endpoint)

        mock_binds = [Bind(name="bind1", address="*:80")]

        with (
            patch(
                "haproxy_template_ic.dataplane.config_api.get_all_bind_frontend"
            ) as mock_get_binds,
            patch(
                "haproxy_template_ic.dataplane.config_api.get_metrics_collector",
                return_value=mock_metrics,
            ),
        ):
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
        config_api = ConfigAPI(endpoint)

        # Use factory function for cleaner test
        changes = [
            create_frontend_config_change(section_name=f"frontend-{i}")
            for i in range(3)
        ]

        with (
            patch(
                "haproxy_template_ic.dataplane.config_api.create_frontend"
            ) as mock_create,
            patch(
                "haproxy_template_ic.dataplane.config_api.get_metrics_collector",
                return_value=mock_metrics,
            ),
        ):
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
    async def test_large_configuration_fetch(self, mock_metrics):
        """Test fetching large configuration efficiently."""
        endpoint = create_dataplane_endpoint_mock()
        config_api = ConfigAPI(endpoint)

        # Create large mock data sets
        large_backend_list = [Backend(name=f"backend-{i}") for i in range(100)]
        large_frontend_list = [Frontend(name=f"frontend-{i}") for i in range(50)]

        from unittest.mock import AsyncMock
        from contextlib import ExitStack

        with ExitStack() as stack:
            # Top-level section mocks
            mock_get_backends = stack.enter_context(
                patch(
                    "haproxy_template_ic.dataplane.config_api.get_backends",
                    new_callable=AsyncMock,
                )
            )
            mock_get_frontends = stack.enter_context(
                patch(
                    "haproxy_template_ic.dataplane.config_api.get_frontends",
                    new_callable=AsyncMock,
                )
            )
            mock_get_defaults = stack.enter_context(
                patch(
                    "haproxy_template_ic.dataplane.config_api.get_defaults_sections",
                    new_callable=AsyncMock,
                )
            )
            mock_get_global = stack.enter_context(
                patch(
                    "haproxy_template_ic.dataplane.config_api.get_global",
                    new_callable=AsyncMock,
                )
            )
            mock_get_userlists = stack.enter_context(
                patch(
                    "haproxy_template_ic.dataplane.config_api.get_userlists",
                    new_callable=AsyncMock,
                )
            )
            mock_get_caches = stack.enter_context(
                patch(
                    "haproxy_template_ic.dataplane.config_api.get_caches",
                    new_callable=AsyncMock,
                )
            )
            mock_get_fcgi_apps = stack.enter_context(
                patch(
                    "haproxy_template_ic.dataplane.config_api.get_fcgi_apps",
                    new_callable=AsyncMock,
                )
            )
            mock_get_http_errors = stack.enter_context(
                patch(
                    "haproxy_template_ic.dataplane.config_api.get_http_errors_sections",
                    new_callable=AsyncMock,
                )
            )
            mock_get_log_forwards = stack.enter_context(
                patch(
                    "haproxy_template_ic.dataplane.config_api.get_log_forwards",
                    new_callable=AsyncMock,
                )
            )
            mock_get_mailers = stack.enter_context(
                patch(
                    "haproxy_template_ic.dataplane.config_api.get_mailers_sections",
                    new_callable=AsyncMock,
                )
            )
            mock_get_resolvers = stack.enter_context(
                patch(
                    "haproxy_template_ic.dataplane.config_api.get_resolvers",
                    new_callable=AsyncMock,
                )
            )
            mock_get_peers = stack.enter_context(
                patch(
                    "haproxy_template_ic.dataplane.config_api.get_peer_sections",
                    new_callable=AsyncMock,
                )
            )
            mock_get_rings = stack.enter_context(
                patch(
                    "haproxy_template_ic.dataplane.config_api.get_rings",
                    new_callable=AsyncMock,
                )
            )
            mock_get_programs = stack.enter_context(
                patch(
                    "haproxy_template_ic.dataplane.config_api.get_programs",
                    new_callable=AsyncMock,
                )
            )

            # Nested element mocks (critical for performance) - these were missing!
            mock_get_servers = stack.enter_context(
                patch(
                    "haproxy_template_ic.dataplane.config_api.get_all_server_backend",
                    new_callable=AsyncMock,
                )
            )
            mock_get_backend_acls = stack.enter_context(
                patch(
                    "haproxy_template_ic.dataplane.config_api.get_all_acl_backend",
                    new_callable=AsyncMock,
                )
            )
            mock_get_backend_request_rules = stack.enter_context(
                patch(
                    "haproxy_template_ic.dataplane.config_api.get_all_http_request_rule_backend",
                    new_callable=AsyncMock,
                )
            )
            mock_get_backend_response_rules = stack.enter_context(
                patch(
                    "haproxy_template_ic.dataplane.config_api.get_all_http_response_rule_backend",
                    new_callable=AsyncMock,
                )
            )
            mock_get_backend_filters = stack.enter_context(
                patch(
                    "haproxy_template_ic.dataplane.config_api.get_all_filter_backend",
                    new_callable=AsyncMock,
                )
            )
            mock_get_backend_logs = stack.enter_context(
                patch(
                    "haproxy_template_ic.dataplane.config_api.get_all_log_target_backend",
                    new_callable=AsyncMock,
                )
            )
            mock_get_binds = stack.enter_context(
                patch(
                    "haproxy_template_ic.dataplane.config_api.get_all_bind_frontend",
                    new_callable=AsyncMock,
                )
            )
            mock_get_frontend_acls = stack.enter_context(
                patch(
                    "haproxy_template_ic.dataplane.config_api.get_all_acl_frontend",
                    new_callable=AsyncMock,
                )
            )
            mock_get_frontend_request_rules = stack.enter_context(
                patch(
                    "haproxy_template_ic.dataplane.config_api.get_all_http_request_rule_frontend",
                    new_callable=AsyncMock,
                )
            )
            mock_get_frontend_response_rules = stack.enter_context(
                patch(
                    "haproxy_template_ic.dataplane.config_api.get_all_http_response_rule_frontend",
                    new_callable=AsyncMock,
                )
            )
            mock_get_frontend_filters = stack.enter_context(
                patch(
                    "haproxy_template_ic.dataplane.config_api.get_all_filter_frontend",
                    new_callable=AsyncMock,
                )
            )
            mock_get_frontend_logs = stack.enter_context(
                patch(
                    "haproxy_template_ic.dataplane.config_api.get_all_log_target_frontend",
                    new_callable=AsyncMock,
                )
            )
            mock_get_global_logs = stack.enter_context(
                patch(
                    "haproxy_template_ic.dataplane.config_api.get_all_log_target_global",
                    new_callable=AsyncMock,
                )
            )
            stack.enter_context(
                patch(
                    "haproxy_template_ic.dataplane.config_api.get_metrics_collector",
                    return_value=mock_metrics,
                )
            )
            # Setup async mocks properly - these functions are already AsyncMock due to patch
            # They should return APIResponse objects directly
            from tests.unit.dataplane.adapter_fixtures import create_mock_api_response

            # Top-level section mocks
            mock_get_backends.return_value = create_mock_api_response(
                content=large_backend_list
            )
            mock_get_frontends.return_value = create_mock_api_response(
                content=large_frontend_list
            )

            # Setup other top-level mocks with empty content
            for mock_func in [
                mock_get_defaults,
                mock_get_userlists,
                mock_get_caches,
                mock_get_fcgi_apps,
                mock_get_http_errors,
                mock_get_log_forwards,
                mock_get_mailers,
                mock_get_resolvers,
                mock_get_peers,
                mock_get_rings,
                mock_get_programs,
            ]:
                mock_func.return_value = create_mock_api_response(content=[])
            mock_get_global.return_value = create_mock_api_response(content=None)

            # Setup nested element mocks with empty content (this prevents 900+ HTTP timeout calls!)
            for mock_func in [
                mock_get_servers,
                mock_get_backend_acls,
                mock_get_backend_request_rules,
                mock_get_backend_response_rules,
                mock_get_backend_filters,
                mock_get_backend_logs,
                mock_get_binds,
                mock_get_frontend_acls,
                mock_get_frontend_request_rules,
                mock_get_frontend_response_rules,
                mock_get_frontend_filters,
                mock_get_frontend_logs,
                mock_get_global_logs,
            ]:
                mock_func.return_value = create_mock_api_response(content=[])

            result = await config_api.fetch_structured_configuration()

            assert len(result["backends"]) == 100
            assert len(result["frontends"]) == 50
