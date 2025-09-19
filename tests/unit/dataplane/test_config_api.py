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
)
from haproxy_dataplane_v3.models import (
    Backend,
    Frontend,
    Defaults,
)
from tests.unit.conftest import (
    create_dataplane_endpoint_mock,
)


class TestConfigAPIInitialization:
    """Test ConfigAPI initialization and basic setup."""

    def test_config_api_init(self):
        """Test ConfigAPI initialization."""
        mock_get_client = Mock()
        endpoint = create_dataplane_endpoint_mock()

        config_api = ConfigAPI(mock_get_client, endpoint)

        assert config_api._get_client == mock_get_client
        assert config_api.endpoint == endpoint


class TestConfigAPIFetchOperations:
    """Test configuration fetching operations."""

    @pytest.mark.asyncio
    async def test_fetch_structured_configuration_success(self):
        """Test successful structured configuration fetching."""
        mock_get_client = Mock()
        mock_client = Mock()
        mock_get_client.return_value = mock_client
        endpoint = create_dataplane_endpoint_mock()

        config_api = ConfigAPI(mock_get_client, endpoint)

        # Mock API responses
        mock_backends = [Backend(name="api", balance="roundrobin")]
        mock_frontends = [Frontend(name="web", mode="http")]
        mock_defaults = [Defaults(mode="http")]

        with (
            patch(
                "haproxy_template_ic.dataplane.config_api.get_backends"
            ) as mock_get_backends,
            patch(
                "haproxy_template_ic.dataplane.config_api.get_frontends"
            ) as mock_get_frontends,
            patch(
                "haproxy_template_ic.dataplane.config_api.get_defaults_sections"
            ) as mock_get_defaults,
            patch(
                "haproxy_template_ic.dataplane.config_api.get_global"
            ) as mock_get_global,
            patch(
                "haproxy_template_ic.dataplane.config_api.get_userlists"
            ) as mock_get_userlists,
            patch(
                "haproxy_template_ic.dataplane.config_api.get_caches"
            ) as mock_get_caches,
            patch(
                "haproxy_template_ic.dataplane.config_api.get_fcgi_apps"
            ) as mock_get_fcgi_apps,
            patch(
                "haproxy_template_ic.dataplane.config_api.get_http_errors_sections"
            ) as mock_get_http_errors,
            patch(
                "haproxy_template_ic.dataplane.config_api.get_log_forwards"
            ) as mock_get_log_forwards,
            patch(
                "haproxy_template_ic.dataplane.config_api.get_mailers_sections"
            ) as mock_get_mailers,
            patch(
                "haproxy_template_ic.dataplane.config_api.get_resolvers"
            ) as mock_get_resolvers,
            patch(
                "haproxy_template_ic.dataplane.config_api.get_peer_sections"
            ) as mock_get_peers,
            patch(
                "haproxy_template_ic.dataplane.config_api.get_rings"
            ) as mock_get_rings,
            patch(
                "haproxy_template_ic.dataplane.config_api.get_programs"
            ) as mock_get_programs,
        ):
            # Mock the asyncio attribute (config API uses .asyncio for fetch operations)
            mock_get_backends.asyncio = AsyncMock(return_value=mock_backends)
            mock_get_frontends.asyncio = AsyncMock(return_value=mock_frontends)
            mock_get_defaults.asyncio = AsyncMock(return_value=mock_defaults)
            mock_get_global.asyncio = AsyncMock(return_value={})
            mock_get_userlists.asyncio = AsyncMock(return_value=[])
            mock_get_caches.asyncio = AsyncMock(return_value=[])
            mock_get_fcgi_apps.asyncio = AsyncMock(return_value=[])
            mock_get_http_errors.asyncio = AsyncMock(return_value=[])
            mock_get_log_forwards.asyncio = AsyncMock(return_value=[])
            mock_get_mailers.asyncio = AsyncMock(return_value=[])
            mock_get_resolvers.asyncio = AsyncMock(return_value=[])
            mock_get_peers.asyncio = AsyncMock(return_value=[])
            mock_get_rings.asyncio = AsyncMock(return_value=[])
            mock_get_programs.asyncio = AsyncMock(return_value=[])

            result = await config_api.fetch_structured_configuration()

            # Verify result structure
            assert "backends" in result
            assert "frontends" in result
            assert "defaults" in result


class TestConfigAPIApplyConfigChange:
    """Test configuration change application."""

    @pytest.mark.asyncio
    async def test_apply_frontend_create_change(self):
        """Test applying frontend CREATE change."""
        mock_get_client = Mock()
        mock_client = Mock()
        mock_get_client.return_value = mock_client
        endpoint = create_dataplane_endpoint_mock()

        config_api = ConfigAPI(mock_get_client, endpoint)

        # Create test change
        config_change = ConfigChange(
            change_type=ConfigChangeType.CREATE,
            section_type=ConfigSectionType.FRONTEND,
            section_name="web",
            new_config={"mode": "http", "bind": "*:80"},
        )

        mock_frontend = Frontend(name="web", mode="http")

        with patch(
            "haproxy_template_ic.dataplane.config_api.create_frontend"
        ) as mock_create:
            mock_create.asyncio_detailed = AsyncMock(
                return_value=Mock(parsed=mock_frontend)
            )
            mock_create.asyncio_detailed.__name__ = "create_frontend_asyncio_detailed"

            await config_api.apply_config_change(config_change, version=1)

            # Verify the mock was called (method returns None)
            mock_create.asyncio_detailed.assert_called_once()

    @pytest.mark.asyncio
    async def test_apply_backend_update_change(self):
        """Test applying backend UPDATE change."""
        mock_get_client = Mock()
        mock_client = Mock()
        mock_get_client.return_value = mock_client
        endpoint = create_dataplane_endpoint_mock()

        config_api = ConfigAPI(mock_get_client, endpoint)

        config_change = ConfigChange(
            change_type=ConfigChangeType.UPDATE,
            section_type=ConfigSectionType.BACKEND,
            section_name="api",
            new_config={"balance": "leastconn"},
        )

        mock_backend = Backend(name="api", balance="leastconn")

        with patch(
            "haproxy_template_ic.dataplane.config_api.replace_backend"
        ) as mock_replace:
            mock_replace.asyncio_detailed = AsyncMock(
                return_value=Mock(parsed=mock_backend)
            )
            mock_replace.asyncio_detailed.__name__ = "replace_backend_asyncio_detailed"

            await config_api.apply_config_change(config_change, version=1)

            # Verify the mock was called (method returns None)
            mock_replace.asyncio_detailed.assert_called_once()

    @pytest.mark.asyncio
    async def test_apply_delete_change(self):
        """Test applying DELETE change."""
        mock_get_client = Mock()
        mock_client = Mock()
        mock_get_client.return_value = mock_client
        endpoint = create_dataplane_endpoint_mock()

        config_api = ConfigAPI(mock_get_client, endpoint)

        config_change = ConfigChange(
            change_type=ConfigChangeType.DELETE,
            section_type=ConfigSectionType.BACKEND,
            section_name="old_api",
        )

        with patch(
            "haproxy_template_ic.dataplane.config_api.delete_backend"
        ) as mock_delete:
            mock_response = Mock(status_code=200, headers={})
            mock_delete.asyncio_detailed = AsyncMock(return_value=mock_response)
            mock_delete.asyncio_detailed.__name__ = "delete_backend_asyncio_detailed"

            await config_api.apply_config_change(config_change, version=1)

            # Verify the mock was called (method returns None)
            mock_delete.asyncio_detailed.assert_called_once()


class TestConfigAPIErrorHandling:
    """Test error handling and edge cases."""

    @pytest.mark.asyncio
    async def test_apply_config_change_with_api_error(self):
        """Test config change application with API error."""
        mock_get_client = Mock()
        mock_client = Mock()
        mock_get_client.return_value = mock_client
        endpoint = create_dataplane_endpoint_mock()

        config_api = ConfigAPI(mock_get_client, endpoint)

        config_change = ConfigChange(
            change_type=ConfigChangeType.CREATE,
            section_type=ConfigSectionType.BACKEND,
            section_name="api",
            new_config={"balance": "roundrobin"},
        )

        with patch(
            "haproxy_template_ic.dataplane.config_api.create_backend"
        ) as mock_create:
            mock_create.asyncio_detailed = AsyncMock(
                side_effect=Exception("Backend creation failed")
            )
            mock_create.asyncio_detailed.__name__ = "create_backend_asyncio_detailed"

            with pytest.raises(Exception, match="Backend creation failed"):
                await config_api.apply_config_change(config_change, version=1)
