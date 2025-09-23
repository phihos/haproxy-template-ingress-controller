"""
Comprehensive unit tests for haproxy_template_ic.dataplane.synchronizer module.

Covers all major functionality including configuration comparison, deployment strategies,
error handling, and client management with thorough edge case testing.
"""

import pytest
from unittest.mock import AsyncMock, Mock, patch

from haproxy_template_ic.dataplane.client import DataplaneClient
from haproxy_template_ic.dataplane.endpoint import (
    DataplaneEndpoint,
    DataplaneEndpointSet,
)
from haproxy_template_ic.credentials import DataplaneAuth
from pydantic import SecretStr
from haproxy_template_ic.dataplane.synchronizer import (
    _SECTION_ELEMENTS,
)
from haproxy_template_ic.dataplane.types import (
    ConfigChangeType,
    ConfigElementType,
    ConfigSectionType,
    ConfigSynchronizerResult,
    DataplaneAPIError,
    ValidationDeploymentResult,
    ValidationError,
    compute_content_hash,
)
from haproxy_template_ic.dataplane.adapter import ReloadInfo
from haproxy_template_ic.models.context import HAProxyConfigContext, TemplateContext
from haproxy_template_ic.models.templates import (
    RenderedConfig,
    RenderedContent,
    ContentType,
)
from tests.unit.dataplane.conftest import create_config_synchronizer


def create_mock_endpoint(
    url: str = "http://test:5555",
    pod_name: str | None = None,
    display_name: str | None = None,
):
    """Helper to create properly mocked DataplaneEndpoint objects."""
    mock_auth = Mock(spec=DataplaneAuth)
    mock_auth.username = "admin"
    mock_auth.password = SecretStr("password")

    mock_endpoint = Mock(spec=DataplaneEndpoint)
    mock_endpoint.url = url
    mock_endpoint.dataplane_auth = mock_auth
    mock_endpoint.pod_name = pod_name
    mock_endpoint.display_name = (
        display_name or pod_name or url.split("//")[1].split(":")[0]
    )

    return mock_endpoint


class TestConfigSynchronizerInit:
    """Test ConfigSynchronizer initialization and basic methods."""

    def test_init_with_endpoints(self):
        """Test initialization with endpoint set."""
        # Arrange
        mock_endpoints = Mock(spec=DataplaneEndpointSet)

        # Act
        synchronizer = create_config_synchronizer(mock_endpoints)

        # Assert
        assert synchronizer.endpoints is mock_endpoints
        assert synchronizer._validation_client is None
        assert synchronizer._production_clients == {}

    def test_create_client(self):
        """Test client creation factory method."""
        # Arrange
        mock_endpoints = Mock(spec=DataplaneEndpointSet)
        synchronizer = create_config_synchronizer(mock_endpoints)
        mock_auth = Mock(spec=DataplaneAuth)
        mock_auth.username = "admin"
        mock_auth.password = SecretStr("password")
        mock_endpoint = create_mock_endpoint()
        mock_endpoint.url = "http://test:5555"
        mock_endpoint.dataplane_auth = mock_auth

        # Act
        client = synchronizer.create_client(mock_endpoint, timeout=45.0)

        # Assert
        assert isinstance(client, DataplaneClient)
        assert client.endpoint is mock_endpoint
        assert client.timeout == 45.0

    def test_create_client_for_url_success(self):
        """Test client creation by URL when endpoint exists."""
        # Arrange
        mock_endpoints = Mock(spec=DataplaneEndpointSet)
        mock_auth = Mock(spec=DataplaneAuth)
        mock_auth.username = "admin"
        mock_auth.password = SecretStr("password")
        mock_endpoint = create_mock_endpoint()
        mock_endpoint.url = "http://test:5555"
        mock_endpoint.dataplane_auth = mock_auth
        mock_endpoints.find_by_url.return_value = mock_endpoint

        synchronizer = create_config_synchronizer(mock_endpoints)

        # Act
        client = synchronizer.create_client_for_url("http://test:5555", timeout=60.0)

        # Assert
        mock_endpoints.find_by_url.assert_called_once_with("http://test:5555")
        assert isinstance(client, DataplaneClient)
        assert client.endpoint is mock_endpoint
        assert client.timeout == 60.0

    def test_create_client_for_url_not_found(self):
        """Test client creation by URL when endpoint doesn't exist."""
        # Arrange
        mock_endpoints = Mock(spec=DataplaneEndpointSet)
        mock_endpoints.find_by_url.return_value = None

        synchronizer = create_config_synchronizer(mock_endpoints)

        # Act & Assert
        with pytest.raises(ValueError, match="No endpoint found for URL"):
            synchronizer.create_client_for_url("http://unknown:5555")

    def test_get_validation_client_cached(self):
        """Test validation client creation and caching."""
        # Arrange
        mock_endpoints = Mock(spec=DataplaneEndpointSet)
        mock_auth = Mock(spec=DataplaneAuth)
        mock_auth.username = "admin"
        mock_auth.password = SecretStr("password")
        mock_validation_endpoint = create_mock_endpoint("http://validation:5555")
        mock_validation_endpoint.url = "http://validation:5555"
        mock_validation_endpoint.dataplane_auth = mock_auth
        mock_endpoints.validation = mock_validation_endpoint

        synchronizer = create_config_synchronizer(mock_endpoints)

        # Act
        client1 = synchronizer._get_validation_client()
        client2 = synchronizer._get_validation_client()

        # Assert
        assert client1 is client2  # Should be cached
        assert isinstance(client1, DataplaneClient)
        assert client1.endpoint is mock_validation_endpoint

    def test_get_production_client_cached(self):
        """Test production client creation and caching."""
        # Arrange
        mock_endpoints = Mock(spec=DataplaneEndpointSet)
        synchronizer = create_config_synchronizer(mock_endpoints)

        mock_auth = Mock(spec=DataplaneAuth)
        mock_auth.username = "admin"
        mock_auth.password = SecretStr("password")
        mock_endpoint = create_mock_endpoint()
        mock_endpoint.url = "http://test:5555"
        mock_endpoint.dataplane_auth = mock_auth
        mock_endpoint.url = "http://test:5555"

        # Act
        client1 = synchronizer._get_production_client(mock_endpoint)
        client2 = synchronizer._get_production_client(mock_endpoint)

        # Assert
        assert client1 is client2  # Should be cached
        assert isinstance(client1, DataplaneClient)
        assert client1.endpoint is mock_endpoint

    def test_get_endpoint_health(self):
        """Test endpoint health status collection."""
        # Arrange
        mock_endpoints = Mock(spec=DataplaneEndpointSet)
        mock_endpoint1 = create_mock_endpoint(
            "http://validation:5555", display_name="validation"
        )
        mock_endpoint2 = create_mock_endpoint(
            "http://prod-1:5555", display_name="prod-1"
        )
        mock_endpoints.all_endpoints.return_value = [mock_endpoint1, mock_endpoint2]

        synchronizer = create_config_synchronizer(mock_endpoints)

        # Act
        health = synchronizer.get_endpoint_health()

        # Assert
        assert health == {"validation": "unknown", "prod-1": "unknown"}


class TestConfigSynchronizerContentMethods:
    """Test content preparation and synchronization methods."""

    def test_prepare_sync_content(self):
        """Test content preparation from HAProxy config context."""
        # Arrange
        mock_endpoints = Mock(spec=DataplaneEndpointSet)
        synchronizer = create_config_synchronizer(mock_endpoints)

        context = HAProxyConfigContext(template_context=TemplateContext())
        context.rendered_content = [
            RenderedContent(
                filename="hosts.map",
                content="host1 backend1",
                content_type=ContentType.MAP,
            ),
            RenderedContent(
                filename="ssl.pem",
                content="cert content",
                content_type=ContentType.CERTIFICATE,
            ),
            RenderedContent(
                filename="acl.lst", content="acl content", content_type=ContentType.ACL
            ),
            RenderedContent(
                filename="error.html",
                content="<html>Error</html>",
                content_type=ContentType.FILE,
            ),
        ]

        # Act
        maps, certs, acls, files = synchronizer._prepare_sync_content(context)

        # Assert
        assert maps == {"hosts.map": "host1 backend1"}
        assert certs == {"ssl.pem": "cert content"}
        assert acls == {"acl.lst": "acl content"}
        assert files == {"error.html": "<html>Error</html>"}

    def test_prepare_sync_content_empty(self):
        """Test content preparation with no rendered content."""
        # Arrange
        mock_endpoints = Mock(spec=DataplaneEndpointSet)
        synchronizer = create_config_synchronizer(mock_endpoints)

        context = HAProxyConfigContext(template_context=TemplateContext())
        context.rendered_content = []

        # Act
        maps, certs, acls, files = synchronizer._prepare_sync_content(context)

        # Assert
        assert maps == {}
        assert certs == {}
        assert acls == {}
        assert files == {}

    def test_compute_template_hashes(self):
        """Test template hash computation."""
        # Arrange
        mock_endpoints = Mock(spec=DataplaneEndpointSet)
        synchronizer = create_config_synchronizer(mock_endpoints)

        context = HAProxyConfigContext(template_context=TemplateContext())
        context.rendered_config = RenderedConfig(content="global\n    daemon")
        context.rendered_content = [
            RenderedContent(
                filename="hosts.map",
                content="host1 backend1",
                content_type=ContentType.MAP,
            ),
            RenderedContent(
                filename="ssl.pem",
                content="cert content",
                content_type=ContentType.CERTIFICATE,
            ),
        ]

        # Act
        hashes = synchronizer._compute_template_hashes(context)

        # Assert
        assert "haproxy.cfg" in hashes
        assert "hosts.map" in hashes
        assert "ssl.pem" in hashes

        # Verify hashes are consistent
        expected_config_hash = compute_content_hash("global\n    daemon")
        expected_map_hash = compute_content_hash("host1 backend1")
        expected_cert_hash = compute_content_hash("cert content")

        assert hashes["haproxy.cfg"] == expected_config_hash
        assert hashes["hosts.map"] == expected_map_hash
        assert hashes["ssl.pem"] == expected_cert_hash

    def test_compute_template_hashes_no_config(self):
        """Test template hash computation with no rendered config."""
        # Arrange
        mock_endpoints = Mock(spec=DataplaneEndpointSet)
        synchronizer = create_config_synchronizer(mock_endpoints)

        context = HAProxyConfigContext(template_context=TemplateContext())
        context.rendered_config = None
        context.rendered_content = [
            RenderedContent(
                filename="hosts.map",
                content="host1 backend1",
                content_type=ContentType.MAP,
            ),
        ]

        # Act
        hashes = synchronizer._compute_template_hashes(context)

        # Assert
        assert "haproxy.cfg" not in hashes
        assert "hosts.map" in hashes


class TestConfigSynchronizerClientManagement:
    """Test client lifecycle management."""

    def test_update_production_clients_add_new(self):
        """Test adding new production clients."""
        # Arrange
        mock_auth = Mock(spec=DataplaneAuth)
        mock_auth.username = "admin"
        mock_auth.password = SecretStr("password")
        mock_validation_endpoint = create_mock_endpoint("http://validation:5555")
        mock_validation_endpoint.url = "http://validation:5555"
        mock_validation_endpoint.dataplane_auth = mock_auth
        mock_validation_endpoint.url = "http://validation:5555"

        mock_endpoints = Mock(spec=DataplaneEndpointSet)
        mock_endpoints.validation = mock_validation_endpoint
        mock_endpoints.production = []

        synchronizer = create_config_synchronizer(mock_endpoints)

        new_endpoint1 = Mock(spec=DataplaneEndpoint)
        new_endpoint1.url = "http://new-pod-1:5555"
        new_endpoint2 = Mock(spec=DataplaneEndpoint)
        new_endpoint2.url = "http://new-pod-2:5555"

        new_endpoints = [new_endpoint1, new_endpoint2]

        with patch(
            "haproxy_template_ic.dataplane.synchronizer.DataplaneClient"
        ) as mock_client_class:
            mock_client_instances = [Mock(), Mock()]
            mock_client_class.side_effect = mock_client_instances

            # Act
            synchronizer.update_production_clients(new_endpoints)

        # Assert
        assert len(synchronizer._production_clients) == 2
        assert "http://new-pod-1:5555" in synchronizer._production_clients
        assert "http://new-pod-2:5555" in synchronizer._production_clients

        # Verify endpoint set was updated
        assert synchronizer.endpoints.validation is mock_validation_endpoint
        assert synchronizer.endpoints.production == new_endpoints

    def test_update_production_clients_remove_old(self):
        """Test removing old production clients."""
        # Arrange
        mock_auth = Mock(spec=DataplaneAuth)
        mock_auth.username = "admin"
        mock_auth.password = SecretStr("password")
        mock_validation_endpoint = create_mock_endpoint("http://validation:5555")
        mock_validation_endpoint.url = "http://validation:5555"
        mock_validation_endpoint.dataplane_auth = mock_auth
        mock_endpoints = Mock(spec=DataplaneEndpointSet)
        mock_endpoints.validation = mock_validation_endpoint

        synchronizer = create_config_synchronizer(mock_endpoints)

        # Pre-populate with old clients
        synchronizer._production_clients = {
            "http://old-pod-1:5555": Mock(),
            "http://old-pod-2:5555": Mock(),
        }

        new_endpoint = Mock(spec=DataplaneEndpoint)
        new_endpoint.url = "http://new-pod:5555"
        new_endpoints = [new_endpoint]

        with patch("haproxy_template_ic.dataplane.synchronizer.DataplaneClient"):
            # Act
            synchronizer.update_production_clients(new_endpoints)

        # Assert
        assert len(synchronizer._production_clients) == 1
        assert "http://new-pod:5555" in synchronizer._production_clients
        assert "http://old-pod-1:5555" not in synchronizer._production_clients
        assert "http://old-pod-2:5555" not in synchronizer._production_clients

    def test_update_production_clients_partial_overlap(self):
        """Test updating clients with partial overlap."""
        # Arrange
        mock_auth = Mock(spec=DataplaneAuth)
        mock_auth.username = "admin"
        mock_auth.password = SecretStr("password")
        mock_validation_endpoint = create_mock_endpoint("http://validation:5555")
        mock_validation_endpoint.url = "http://validation:5555"
        mock_validation_endpoint.dataplane_auth = mock_auth
        mock_endpoints = Mock(spec=DataplaneEndpointSet)
        mock_endpoints.validation = mock_validation_endpoint

        synchronizer = create_config_synchronizer(mock_endpoints)

        # Pre-populate with existing clients
        existing_client = Mock()
        synchronizer._production_clients = {
            "http://existing-pod:5555": existing_client,
            "http://remove-pod:5555": Mock(),
        }

        existing_endpoint = Mock(spec=DataplaneEndpoint)
        existing_endpoint.url = "http://existing-pod:5555"
        new_endpoint = Mock(spec=DataplaneEndpoint)
        new_endpoint.url = "http://new-pod:5555"

        new_endpoints = [existing_endpoint, new_endpoint]

        with patch(
            "haproxy_template_ic.dataplane.synchronizer.DataplaneClient"
        ) as mock_client_class:
            mock_client_class.return_value = Mock()

            # Act
            synchronizer.update_production_clients(new_endpoints)

        # Assert
        assert len(synchronizer._production_clients) == 2
        assert "http://existing-pod:5555" in synchronizer._production_clients
        assert "http://new-pod:5555" in synchronizer._production_clients
        assert "http://remove-pod:5555" not in synchronizer._production_clients

        # Verify existing client was not replaced
        assert (
            synchronizer._production_clients["http://existing-pod:5555"]
            is existing_client
        )


class TestConfigSynchronizerContentSync:
    """Test content synchronization methods."""

    @pytest.mark.asyncio
    async def test_sync_content_to_client(self):
        """Test synchronizing all content types to a client."""
        # Arrange
        mock_endpoints = Mock(spec=DataplaneEndpointSet)
        synchronizer = create_config_synchronizer(mock_endpoints)

        mock_client = Mock(spec=DataplaneClient)
        mock_client.sync_maps = AsyncMock()
        mock_client.sync_certificates = AsyncMock()
        mock_client.sync_acls = AsyncMock()
        mock_client.sync_files = AsyncMock()

        maps = {"hosts.map": "host1 backend1"}
        certificates = {"ssl.pem": "cert content"}
        acls = {"acl.lst": "acl content"}
        files = {"error.html": "<html>Error</html>"}
        url = "http://test:5555"

        # Act
        await synchronizer._sync_content_to_client(
            mock_client, maps, certificates, acls, files, url
        )

        # Assert
        mock_client.sync_maps.assert_called_once_with(maps)
        mock_client.sync_certificates.assert_called_once_with(certificates)
        mock_client.sync_acls.assert_called_once_with(acls)
        mock_client.sync_files.assert_called_once_with(files)

    @pytest.mark.asyncio
    async def test_sync_content_pre_deployment(self):
        """Test pre-deployment content synchronization."""
        # Arrange
        mock_endpoints = Mock(spec=DataplaneEndpointSet)
        synchronizer = create_config_synchronizer(mock_endpoints)

        mock_client = Mock(spec=DataplaneClient)
        mock_client.sync_maps = AsyncMock()
        mock_client.sync_certificates = AsyncMock()
        mock_client.sync_acls = AsyncMock()
        mock_client.sync_files = AsyncMock()

        maps = {"hosts.map": "content"}
        certificates = {"ssl.pem": "content"}
        acls = {"acl.lst": "content"}
        files = {"error.html": "content"}
        url = "http://test:5555"

        # Act
        await synchronizer._sync_content_pre_deployment(
            mock_client, maps, certificates, acls, files, url
        )

        # Assert
        operations = {"create", "update"}
        mock_client.sync_maps.assert_called_once_with(maps, operations=operations)
        mock_client.sync_certificates.assert_called_once_with(
            certificates, operations=operations
        )
        mock_client.sync_acls.assert_called_once_with(acls, operations=operations)
        mock_client.sync_files.assert_called_once_with(files, operations=operations)

    @pytest.mark.asyncio
    async def test_sync_content_pre_deployment_empty_content(self):
        """Test pre-deployment sync with empty content collections."""
        # Arrange
        mock_endpoints = Mock(spec=DataplaneEndpointSet)
        synchronizer = create_config_synchronizer(mock_endpoints)

        mock_client = Mock(spec=DataplaneClient)
        mock_client.sync_maps = AsyncMock()
        mock_client.sync_certificates = AsyncMock()
        mock_client.sync_acls = AsyncMock()
        mock_client.sync_files = AsyncMock()

        # Act
        await synchronizer._sync_content_pre_deployment(
            mock_client, {}, {}, {}, {}, "http://test:5555"
        )

        # Assert - no operations should be called for empty content
        mock_client.sync_maps.assert_not_called()
        mock_client.sync_certificates.assert_not_called()
        mock_client.sync_acls.assert_not_called()
        mock_client.sync_files.assert_not_called()

    @pytest.mark.asyncio
    async def test_sync_content_post_deployment(self):
        """Test post-deployment content synchronization."""
        # Arrange
        mock_endpoints = Mock(spec=DataplaneEndpointSet)
        synchronizer = create_config_synchronizer(mock_endpoints)

        mock_client = Mock(spec=DataplaneClient)
        mock_client.sync_maps = AsyncMock()
        mock_client.sync_certificates = AsyncMock()
        mock_client.sync_acls = AsyncMock()
        mock_client.sync_files = AsyncMock()

        maps = {"hosts.map": "content"}
        certificates = {"ssl.pem": "content"}
        acls = {"acl.lst": "content"}
        files = {"error.html": "content"}
        url = "http://test:5555"

        # Act
        await synchronizer._sync_content_post_deployment(
            mock_client, maps, certificates, acls, files, url
        )

        # Assert
        operations = {"delete"}
        mock_client.sync_maps.assert_called_once_with(maps, operations=operations)
        mock_client.sync_certificates.assert_called_once_with(
            certificates, operations=operations
        )
        mock_client.sync_acls.assert_called_once_with(acls, operations=operations)
        mock_client.sync_files.assert_called_once_with(files, operations=operations)


class TestConfigSynchronizerValidation:
    """Test configuration validation methods."""

    @pytest.mark.asyncio
    async def test_validate_configuration_success(self):
        """Test successful configuration validation."""
        # Arrange
        mock_auth = Mock(spec=DataplaneAuth)
        mock_auth.username = "admin"
        mock_auth.password = SecretStr("password")
        mock_validation_endpoint = create_mock_endpoint("http://validation:5555")
        mock_validation_endpoint.url = "http://validation:5555"
        mock_validation_endpoint.dataplane_auth = mock_auth
        mock_endpoints = Mock(spec=DataplaneEndpointSet)
        mock_endpoints.validation = mock_validation_endpoint
        mock_endpoints.validation.url = "http://validation:5555"

        synchronizer = create_config_synchronizer(mock_endpoints)

        mock_client = Mock(spec=DataplaneClient)
        mock_client.validate_configuration = AsyncMock()
        synchronizer._validation_client = mock_client

        config = "global\n    daemon\ndefaults\n    mode http"

        # Act
        await synchronizer._validate_configuration(config)

        # Assert
        mock_client.validate_configuration.assert_called_once_with(config)

    @pytest.mark.asyncio
    async def test_validate_configuration_failure(self):
        """Test configuration validation failure."""
        # Arrange
        mock_auth = Mock(spec=DataplaneAuth)
        mock_auth.username = "admin"
        mock_auth.password = SecretStr("password")
        mock_validation_endpoint = create_mock_endpoint("http://validation:5555")
        mock_validation_endpoint.url = "http://validation:5555"
        mock_validation_endpoint.dataplane_auth = mock_auth
        mock_endpoints = Mock(spec=DataplaneEndpointSet)
        mock_endpoints.validation = mock_validation_endpoint

        synchronizer = create_config_synchronizer(mock_endpoints)

        mock_client = Mock(spec=DataplaneClient)
        mock_client.validate_configuration = AsyncMock(
            side_effect=RuntimeError("Invalid bind directive")
        )
        synchronizer._validation_client = mock_client

        config = "invalid config"

        # Act & Assert
        with pytest.raises(ValidationError, match="Configuration validation failed"):
            await synchronizer._validate_configuration(config)


class TestConfigSynchronizerElementComparison:
    """Test configuration element comparison methods."""

    def test_get_element_identifier_acl(self):
        """Test element identifier extraction for ACL objects."""
        # Arrange
        mock_endpoints = Mock(spec=DataplaneEndpointSet)
        synchronizer = create_config_synchronizer(mock_endpoints)

        mock_item = Mock()
        mock_item.acl_name = "test_acl"

        # Act
        identifier = synchronizer._get_element_identifier(
            mock_item, ConfigElementType.ACL
        )

        # Assert
        assert identifier == "test_acl"

    def test_get_element_identifier_server(self):
        """Test element identifier extraction for server objects."""
        # Arrange
        mock_endpoints = Mock(spec=DataplaneEndpointSet)
        synchronizer = create_config_synchronizer(mock_endpoints)

        mock_item = Mock()
        mock_item.name = "web_server"

        # Act
        identifier = synchronizer._get_element_identifier(
            mock_item, ConfigElementType.SERVER
        )

        # Assert
        assert identifier == "web_server"

    def test_get_element_identifier_fallback_to_id(self):
        """Test element identifier extraction falling back to id attribute."""
        # Arrange
        mock_endpoints = Mock(spec=DataplaneEndpointSet)
        synchronizer = create_config_synchronizer(mock_endpoints)

        mock_item = Mock()
        mock_item.name = None
        mock_item.id = "123"

        # Act
        identifier = synchronizer._get_element_identifier(
            mock_item, ConfigElementType.SERVER
        )

        # Assert
        assert identifier == "123"

    def test_get_element_identifier_none(self):
        """Test element identifier extraction when no identifier found."""
        # Arrange
        mock_endpoints = Mock(spec=DataplaneEndpointSet)
        synchronizer = create_config_synchronizer(mock_endpoints)

        mock_item = Mock()
        del mock_item.name
        del mock_item.id
        del mock_item.acl_name

        # Act
        identifier = synchronizer._get_element_identifier(
            mock_item, ConfigElementType.SERVER
        )

        # Assert
        assert identifier is None

    def test_compare_by_name_additions(self):
        """Test named element comparison for additions."""
        # Arrange
        mock_endpoints = Mock(spec=DataplaneEndpointSet)
        synchronizer = create_config_synchronizer(mock_endpoints)

        current_items = []

        new_server = Mock()
        new_server.name = "web1"
        new_items = [new_server]

        changes = []

        # Act
        synchronizer._compare_by_name(
            current_items,
            new_items,
            ConfigElementType.SERVER,
            ConfigSectionType.BACKEND,
            "web_backend",
            changes,
        )

        # Assert
        assert len(changes) == 1
        change = changes[0]
        assert change.change_type == ConfigChangeType.CREATE
        assert change.section_type == ConfigSectionType.BACKEND
        assert change.section_name == "web_backend"
        assert change.element_type == ConfigElementType.SERVER
        assert change.element_id == "web1"
        assert change.new_config is new_server

    def test_compare_by_name_deletions(self):
        """Test named element comparison for deletions."""
        # Arrange
        mock_endpoints = Mock(spec=DataplaneEndpointSet)
        synchronizer = create_config_synchronizer(mock_endpoints)

        old_server = Mock()
        old_server.name = "web1"
        current_items = [old_server]

        new_items = []
        changes = []

        # Act
        synchronizer._compare_by_name(
            current_items,
            new_items,
            ConfigElementType.SERVER,
            ConfigSectionType.BACKEND,
            "web_backend",
            changes,
        )

        # Assert
        assert len(changes) == 1
        change = changes[0]
        assert change.change_type == ConfigChangeType.DELETE
        assert change.element_id == "web1"
        assert change.old_config is old_server

    def test_compare_by_name_modifications(self):
        """Test named element comparison for modifications."""
        # Arrange
        mock_endpoints = Mock(spec=DataplaneEndpointSet)
        synchronizer = create_config_synchronizer(mock_endpoints)

        old_server = Mock()
        old_server.name = "web1"
        old_server.address = "192.168.1.1"

        new_server = Mock()
        new_server.name = "web1"
        new_server.address = "192.168.1.2"  # Changed address

        current_items = [old_server]
        new_items = [new_server]
        changes = []

        with patch(
            "haproxy_template_ic.dataplane.synchronizer._to_dict_safe"
        ) as mock_to_dict:
            # Mock different dictionary representations for servers
            mock_to_dict.side_effect = lambda x: {"name": x.name, "address": x.address}

            # Act
            synchronizer._compare_by_name(
                current_items,
                new_items,
                ConfigElementType.SERVER,
                ConfigSectionType.BACKEND,
                "web_backend",
                changes,
            )

        # Assert
        assert len(changes) == 1
        change = changes[0]
        assert change.change_type == ConfigChangeType.UPDATE
        assert change.element_id == "web1"
        assert change.old_config is old_server
        assert change.new_config is new_server

    def test_compare_by_order_additions(self):
        """Test ordered element comparison for additions."""
        # Arrange
        mock_endpoints = Mock(spec=DataplaneEndpointSet)
        synchronizer = create_config_synchronizer(mock_endpoints)

        current_items = []

        new_rule = Mock()
        new_items = [new_rule]
        changes = []

        # Act
        synchronizer._compare_by_order(
            current_items,
            new_items,
            ConfigElementType.HTTP_REQUEST_RULE,
            ConfigSectionType.FRONTEND,
            "web_frontend",
            changes,
        )

        # Assert
        assert len(changes) == 1
        change = changes[0]
        assert change.change_type == ConfigChangeType.CREATE
        assert change.element_index == 0
        assert change.new_config is new_rule

    def test_compare_by_order_deletions(self):
        """Test ordered element comparison for deletions."""
        # Arrange
        mock_endpoints = Mock(spec=DataplaneEndpointSet)
        synchronizer = create_config_synchronizer(mock_endpoints)

        old_rule = Mock()
        current_items = [old_rule]
        new_items = []
        changes = []

        # Act
        synchronizer._compare_by_order(
            current_items,
            new_items,
            ConfigElementType.HTTP_REQUEST_RULE,
            ConfigSectionType.FRONTEND,
            "web_frontend",
            changes,
        )

        # Assert
        assert len(changes) == 1
        change = changes[0]
        assert change.change_type == ConfigChangeType.DELETE
        assert change.element_index == 0
        assert change.old_config is old_rule

    def test_compare_by_order_modifications(self):
        """Test ordered element comparison for modifications."""
        # Arrange
        mock_endpoints = Mock(spec=DataplaneEndpointSet)
        synchronizer = create_config_synchronizer(mock_endpoints)

        old_rule = Mock()
        old_rule.condition = "if path_beg /api"

        new_rule = Mock()
        new_rule.condition = "if path_beg /v2/api"  # Changed condition

        current_items = [old_rule]
        new_items = [new_rule]
        changes = []

        with patch(
            "haproxy_template_ic.dataplane.synchronizer._to_dict_safe"
        ) as mock_to_dict:
            # Mock different dictionary representations
            mock_to_dict.side_effect = lambda x: {"condition": x.condition}

            # Act
            synchronizer._compare_by_order(
                current_items,
                new_items,
                ConfigElementType.HTTP_REQUEST_RULE,
                ConfigSectionType.FRONTEND,
                "web_frontend",
                changes,
            )

        # Assert
        assert len(changes) == 1
        change = changes[0]
        assert change.change_type == ConfigChangeType.UPDATE
        assert change.element_index == 0
        assert change.old_config is old_rule
        assert change.new_config is new_rule


class TestConfigSynchronizerSectionComparison:
    """Test configuration section comparison methods."""

    def test_extract_nested_elements_for_frontend(self):
        """Test nested element extraction for frontend sections."""
        # Arrange
        mock_endpoints = Mock(spec=DataplaneEndpointSet)
        synchronizer = create_config_synchronizer(mock_endpoints)

        config = {
            "frontend_acls": {
                "web_frontend": [{"acl_name": "is_api", "criterion": "path_beg /api"}]
            },
            "frontend_binds": {
                "web_frontend": [{"name": "bind1", "address": "*", "port": "80"}]
            },
            "frontend_http_request_rules": {
                "web_frontend": [{"condition": "if is_api"}]
            },
        }

        # Act
        nested = synchronizer._extract_nested_elements_for_section(
            config, ConfigSectionType.FRONTEND, "web_frontend"
        )

        # Assert
        assert "acls" in nested
        assert "binds" in nested
        assert "http_request_rules" in nested
        assert len(nested["acls"]) == 1
        assert len(nested["binds"]) == 1
        assert len(nested["http_request_rules"]) == 1

    def test_extract_nested_elements_for_backend(self):
        """Test nested element extraction for backend sections."""
        # Arrange
        mock_endpoints = Mock(spec=DataplaneEndpointSet)
        synchronizer = create_config_synchronizer(mock_endpoints)

        config = {
            "backend_servers": {
                "web_backend": [{"name": "web1", "address": "192.168.1.1"}]
            },
            "backend_acls": {"web_backend": [{"acl_name": "is_healthy"}]},
        }

        # Act
        nested = synchronizer._extract_nested_elements_for_section(
            config, ConfigSectionType.BACKEND, "web_backend"
        )

        # Assert
        assert "servers" in nested
        assert "acls" in nested
        assert len(nested["servers"]) == 1
        assert len(nested["acls"]) == 1

    def test_extract_nested_elements_for_global(self):
        """Test nested element extraction for global section."""
        # Arrange
        mock_endpoints = Mock(spec=DataplaneEndpointSet)
        synchronizer = create_config_synchronizer(mock_endpoints)

        config = {
            "global_log_targets": [{"address": "stdout", "facility": "local0"}],
        }

        # Act
        nested = synchronizer._extract_nested_elements_for_section(
            config, ConfigSectionType.GLOBAL, "global"
        )

        # Assert
        assert "log_targets" in nested
        assert len(nested["log_targets"]) == 1

    def test_extract_nested_elements_unknown_section(self):
        """Test nested element extraction for unknown section types."""
        # Arrange
        mock_endpoints = Mock(spec=DataplaneEndpointSet)
        synchronizer = create_config_synchronizer(mock_endpoints)

        config = {"some_data": "value"}

        # Act
        nested = synchronizer._extract_nested_elements_for_section(
            config, ConfigSectionType.DEFAULTS, "defaults"
        )

        # Assert
        assert nested == {}


class TestConfigSynchronizerErrorHandling:
    """Test error handling and logging methods."""

    def test_handle_deployment_error_basic(self):
        """Test basic deployment error handling."""
        # Arrange
        mock_endpoints = Mock(spec=DataplaneEndpointSet)
        synchronizer = create_config_synchronizer(mock_endpoints)

        results = {"failed": 0, "errors": []}
        error = RuntimeError("Connection failed")
        url = "http://test:5555"
        config = "test config"

        with patch("haproxy_template_ic.dataplane.synchronizer.logger") as mock_logger:
            # Act
            synchronizer._handle_deployment_error(url, error, config, results)

        # Assert
        assert results["failed"] == 1
        assert results["errors"] == ["http://test:5555: Connection failed"]
        mock_logger.error.assert_called()

    def test_handle_deployment_error_with_context(self):
        """Test deployment error handling with configuration context parsing."""
        # Arrange
        mock_endpoints = Mock(spec=DataplaneEndpointSet)
        synchronizer = create_config_synchronizer(mock_endpoints)

        results = {"failed": 0, "errors": []}
        error = RuntimeError("Parsing error at line 5")
        url = "http://test:5555"
        config = "line1\nline2\nline3\nline4\nline5\nline6"

        with (
            patch("haproxy_template_ic.dataplane.synchronizer.logger") as mock_logger,
            patch(
                "haproxy_template_ic.dataplane.synchronizer.parse_validation_error_details"
            ) as mock_parse,
        ):
            mock_parse.return_value = ("Parsed error", 5, "Context around line 5")

            # Act
            synchronizer._handle_deployment_error(url, error, config, results)

        # Assert
        assert results["failed"] == 1
        mock_logger.error.assert_called()
        # Verify context was included in error message
        error_call = mock_logger.error.call_args[0][0]
        assert "Configuration context around error:" in error_call

    def test_handle_deployment_error_parse_failure(self):
        """Test deployment error handling when context parsing fails."""
        # Arrange
        mock_endpoints = Mock(spec=DataplaneEndpointSet)
        synchronizer = create_config_synchronizer(mock_endpoints)

        results = {"failed": 0, "errors": []}
        error = RuntimeError("Some error")
        url = "http://test:5555"
        config = "test config"

        with (
            patch("haproxy_template_ic.dataplane.synchronizer.logger") as mock_logger,
            patch(
                "haproxy_template_ic.dataplane.synchronizer.parse_validation_error_details"
            ) as mock_parse,
        ):
            mock_parse.side_effect = ValueError("Parse failed")

            # Act
            synchronizer._handle_deployment_error(url, error, config, results)

        # Assert
        assert results["failed"] == 1
        mock_logger.error.assert_called()
        mock_logger.debug.assert_called_with(
            "Could not parse validation error details: ValueError: Parse failed"
        )

    def test_extract_pod_info_from_url_success(self):
        """Test pod information extraction from URL."""
        # Arrange
        mock_auth = Mock(spec=DataplaneAuth)
        mock_auth.username = "admin"
        mock_auth.password = SecretStr("password")
        mock_validation_endpoint = create_mock_endpoint("http://validation:5555")
        mock_validation_endpoint.url = "http://validation:5555"
        mock_validation_endpoint.dataplane_auth = mock_auth
        mock_production_endpoint = Mock(spec=DataplaneEndpoint)
        mock_production_endpoint.pod_name = "haproxy-pod-1"

        mock_endpoints = Mock(spec=DataplaneEndpointSet)
        mock_endpoints.validation = mock_validation_endpoint
        mock_endpoints.production = [mock_production_endpoint]
        mock_endpoints.find_by_url.return_value = mock_production_endpoint

        synchronizer = create_config_synchronizer(mock_endpoints)

        # Act
        endpoint = synchronizer._extract_pod_info_from_url("http://192.168.1.5:5555")

        # Assert
        assert endpoint is mock_production_endpoint
        assert endpoint.pod_name == "haproxy-pod-1"

    def test_extract_pod_info_from_url_no_endpoint(self):
        """Test pod information extraction when endpoint not found."""
        # Arrange
        mock_endpoints = Mock(spec=DataplaneEndpointSet)
        mock_endpoints.find_by_url.return_value = None

        synchronizer = create_config_synchronizer(mock_endpoints)

        # Act
        endpoint = synchronizer._extract_pod_info_from_url("http://192.168.1.5:5555")

        # Assert
        assert endpoint is None

    def test_extract_pod_info_from_url_error(self):
        """Test pod information extraction when parsing fails."""
        # Arrange
        mock_endpoints = Mock(spec=DataplaneEndpointSet)
        mock_endpoints.find_by_url.return_value = None
        synchronizer = create_config_synchronizer(mock_endpoints)

        # Act
        endpoint = synchronizer._extract_pod_info_from_url("invalid-url")

        # Assert
        assert endpoint is None


class TestConfigSynchronizerMainFlow:
    """Test the main synchronization flow."""

    @pytest.mark.asyncio
    async def test_sync_configuration_no_rendered_config(self):
        """Test sync_configuration with no rendered config."""
        # Arrange
        mock_endpoints = Mock(spec=DataplaneEndpointSet)
        synchronizer = create_config_synchronizer(mock_endpoints)

        context = HAProxyConfigContext(template_context=TemplateContext())
        context.rendered_config = None

        # Act & Assert
        with pytest.raises(
            DataplaneAPIError, match="No rendered HAProxy configuration available"
        ):
            await synchronizer.sync_configuration(context)

    @pytest.mark.asyncio
    async def test_sync_configuration_basic_flow(self):
        """Test basic synchronization flow."""
        # Arrange
        mock_endpoints = Mock(spec=DataplaneEndpointSet)
        mock_endpoints.production = [Mock(url="http://prod1:5555")]

        synchronizer = create_config_synchronizer(mock_endpoints)

        context = HAProxyConfigContext(template_context=TemplateContext())
        context.rendered_config = RenderedConfig(content="global\n    daemon")
        context.rendered_content = []

        # Mock the main methods
        synchronizer.update_production_clients = Mock()
        synchronizer._validate_and_prepare_config = AsyncMock(
            return_value={"backends": []}
        )
        synchronizer._deploy_to_production_instances = AsyncMock(
            return_value=ConfigSynchronizerResult(
                successful=1, failed=0, skipped=0, errors=[], reload_info=ReloadInfo()
            )
        )

        # Act
        result = await synchronizer.sync_configuration(context)

        # Assert
        assert isinstance(result, ConfigSynchronizerResult)
        synchronizer.update_production_clients.assert_called_once()
        synchronizer._validate_and_prepare_config.assert_called_once()
        synchronizer._deploy_to_production_instances.assert_called_once()

    @pytest.mark.asyncio
    async def test_validate_and_prepare_config(self):
        """Test configuration validation and preparation."""
        # Arrange
        mock_endpoints = Mock(spec=DataplaneEndpointSet)
        mock_endpoints.validation = Mock(url="http://validation:5555")

        synchronizer = create_config_synchronizer(mock_endpoints)

        mock_client = Mock(spec=DataplaneClient)
        mock_client.validate_configuration = AsyncMock()
        mock_client.deploy_configuration = AsyncMock(
            return_value=ValidationDeploymentResult(
                size=1024,
                status="success",
                version="v1",
                reload_info=ReloadInfo(reload_id="reload-123"),
            )
        )
        mock_client.fetch_structured_configuration = AsyncMock(
            return_value={"backends": [], "frontends": []}
        )

        synchronizer._get_validation_client = Mock(return_value=mock_client)
        synchronizer._sync_content_pre_deployment = AsyncMock()

        config = "global\n    daemon"
        sync_content = ({}, {}, {}, {})

        # Act
        result = await synchronizer._validate_and_prepare_config(config, sync_content)

        # Assert
        assert result == {"backends": [], "frontends": []}
        mock_client.validate_configuration.assert_called_once_with(config)
        mock_client.deploy_configuration.assert_called_once_with(config)
        mock_client.fetch_structured_configuration.assert_called_once()


class TestSectionElementsRegistry:
    """Test the section elements registry configuration."""

    def test_section_elements_registry_structure(self):
        """Test that section elements registry has expected structure."""
        # Assert registry exists and has expected sections
        assert ConfigSectionType.BACKEND in _SECTION_ELEMENTS
        assert ConfigSectionType.FRONTEND in _SECTION_ELEMENTS
        assert ConfigSectionType.GLOBAL in _SECTION_ELEMENTS

        # Test backend elements
        backend_elements = _SECTION_ELEMENTS[ConfigSectionType.BACKEND]
        element_names = [elem[0] for elem in backend_elements]
        assert "servers" in element_names
        assert "http_request_rules" in element_names
        assert "acls" in element_names

        # Test that servers are named elements (not ordered)
        servers_elem = next(elem for elem in backend_elements if elem[0] == "servers")
        assert servers_elem[1] == ConfigElementType.SERVER
        assert servers_elem[2] is True  # is_named

        # Test that HTTP rules are ordered elements (not named)
        rules_elem = next(
            elem for elem in backend_elements if elem[0] == "http_request_rules"
        )
        assert rules_elem[1] == ConfigElementType.HTTP_REQUEST_RULE
        assert rules_elem[2] is False  # not named, ordered

    def test_section_elements_registry_completeness(self):
        """Test that registry covers all necessary section types."""
        # Test frontend elements
        frontend_elements = _SECTION_ELEMENTS[ConfigSectionType.FRONTEND]
        frontend_element_names = [elem[0] for elem in frontend_elements]
        assert "binds" in frontend_element_names
        assert "http_request_rules" in frontend_element_names
        assert "acls" in frontend_element_names

        # Test global elements
        global_elements = _SECTION_ELEMENTS[ConfigSectionType.GLOBAL]
        global_element_names = [elem[0] for elem in global_elements]
        assert "log_targets" in global_element_names
