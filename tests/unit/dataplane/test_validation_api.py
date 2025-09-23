"""
Unit tests for ValidationAPI functionality.

Tests validation and deployment operations for HAProxy configuration.
"""

import pytest
from unittest.mock import Mock, patch

from haproxy_template_ic.dataplane.types import (
    ValidationDeploymentResult,
)
from tests.unit.conftest import (
    create_api_info_response,
    patch_dataplane_apis,
    create_haproxy_process_info_response,
    create_configuration_response,
    expect_validation_error,
    expect_dataplane_error,
)
from tests.unit.dataplane.conftest import (
    create_validation_api,
)


@pytest.fixture
def validation_api(test_endpoint):
    """Create ValidationAPI instance for testing."""
    return create_validation_api(test_endpoint)


@pytest.mark.asyncio
async def test_validate_configuration_success(
    validation_api, mock_client, mock_metrics
):
    """Test successful configuration validation."""
    config_content = "global\n    daemon\n\nfrontend web\n    bind *:80"

    with (
        patch(
            "haproxy_template_ic.dataplane.validation_api.post_haproxy_configuration"
        ) as mock_post_config,
        patch("haproxy_template_ic.dataplane.validation_api.record_span_event"),
    ):
        # Mock the response from post_haproxy_configuration
        mock_response = Mock()
        mock_response.reload_info = Mock()
        mock_response.reload_info.reload_triggered = False
        mock_response.reload_info.reload_id = None
        mock_post_config.return_value = mock_response

        # Execute
        await validation_api.validate_configuration(config_content)

        # Verify
        mock_post_config.assert_called_once_with(
            endpoint=validation_api.endpoint,
            body=config_content + "\n",  # Expect newline-terminated config
            skip_reload=True,
            only_validate=True,
        )


@pytest.mark.asyncio
async def test_validate_configuration_empty_content(validation_api):
    """Test validation with empty configuration content."""
    with expect_validation_error("Configuration content cannot be empty"):
        await validation_api.validate_configuration("")


@pytest.mark.asyncio
async def test_validate_configuration_error(validation_api, mock_metrics):
    """Test validation error handling."""
    config_content = "invalid config"

    with (
        patch_dataplane_apis(mock_metrics=mock_metrics) as mocks,
        patch(
            "haproxy_template_ic.dataplane.validation_api.set_span_error"
        ) as mock_set_error,
        patch(
            "haproxy_template_ic.dataplane.validation_api.parse_validation_error_details"
        ) as mock_parse_error,
    ):
        mocks["api_mocks"][
            "post_haproxy_configuration"
        ].asyncio_detailed.side_effect = Exception("Validation failed")
        mock_parse_error.return_value = ("Invalid syntax", 5, "line context")

        with expect_validation_error("Configuration validation failed"):
            await validation_api.validate_configuration(config_content)
        mock_set_error.assert_called_once()


@pytest.mark.asyncio
async def test_deploy_configuration_success(validation_api, mock_client, mock_metrics):
    """Test successful configuration deployment."""
    config_content = "global\n    daemon\n\nfrontend web\n    bind *:80"

    with (
        patch(
            "haproxy_template_ic.dataplane.validation_api.post_haproxy_configuration"
        ) as mock_post_config,
        patch(
            "haproxy_template_ic.dataplane.validation_api.get_configuration_version"
        ) as mock_get_version,
        patch("haproxy_template_ic.dataplane.validation_api.record_span_event"),
    ):
        # Setup mocks
        # Import adapter fixtures to create proper APIResponse mock
        from tests.unit.dataplane.adapter_fixtures import create_mock_api_response

        mock_get_version.return_value = create_mock_api_response(content=3)

        # Create proper APIResponse with ReloadInfo
        mock_response = create_mock_api_response(
            content="success",  # Deployment response content
            reload_id="reload-123",
        )
        mock_post_config.return_value = mock_response

        # Execute
        result = await validation_api.deploy_configuration(config_content)

        # Verify
        assert isinstance(result, ValidationDeploymentResult)
        assert result.size == len(config_content + "\n")  # Account for appended newline
        assert result.reload_info.reload_id == "reload-123"
        assert result.reload_info.reload_triggered
        assert result.status == "success"
        assert result.version == "3"

        mock_post_config.assert_called_once_with(
            endpoint=validation_api.endpoint,
            body=config_content + "\n",  # Expect newline-terminated config
            skip_reload=False,
            only_validate=False,
            version=3,
        )


@pytest.mark.asyncio
async def test_deploy_configuration_no_version(
    validation_api, mock_client, mock_metrics
):
    """Test deployment when version is None (fallback to version 1)."""
    config_content = "global\n    daemon"

    with (
        patch(
            "haproxy_template_ic.dataplane.validation_api.post_haproxy_configuration"
        ) as mock_post_config,
        patch(
            "haproxy_template_ic.dataplane.validation_api.get_configuration_version"
        ) as mock_get_version,
        patch("haproxy_template_ic.dataplane.validation_api.record_span_event"),
    ):
        # Setup mocks - version is None
        # Import adapter fixtures to create proper APIResponse mock
        from tests.unit.dataplane.adapter_fixtures import create_mock_api_response

        mock_get_version.return_value = create_mock_api_response(content=None)

        # Create proper APIResponse with ReloadInfo
        mock_response = create_mock_api_response(
            content="success",  # Deployment response content
            reload_id="reload-456",
        )
        mock_post_config.return_value = mock_response

        # Execute
        result = await validation_api.deploy_configuration(config_content)

        # Verify fallback to version 1
        mock_post_config.assert_called_once_with(
            endpoint=validation_api.endpoint,
            body=config_content + "\n",  # Expect newline-terminated config
            skip_reload=False,
            only_validate=False,
            version=1,
        )
        assert result.version == "1"


@pytest.mark.asyncio
async def test_get_version_success(validation_api, mock_client, mock_metrics):
    """Test successful version retrieval."""
    mock_info = create_api_info_response()
    mock_process_info = create_haproxy_process_info_response()

    with patch_dataplane_apis(mock_client, mock_metrics) as mocks:
        # Setup mocks - create APIResponse objects with the mock data
        from tests.unit.dataplane.adapter_fixtures import create_mock_api_response

        mocks["api_mocks"]["get_info"].asyncio.return_value = create_mock_api_response(
            content=mock_info
        )
        mocks["api_mocks"][
            "get_haproxy_process_info"
        ].asyncio.return_value = create_mock_api_response(content=mock_process_info)

        # Execute
        result = await validation_api.get_version()

        # Verify
        expected = {
            "api_version": "3.0",
            "build_date": "2023-01-01",
            "version": "dataplane-2.8.0",
            "haproxy": {
                "version": "3.1.0",
                "release_date": "2023-12-01",
                "uptime": "5d 3h 42m",
            },
        }
        assert result == expected


@pytest.mark.asyncio
async def test_get_current_configuration_success(
    validation_api, mock_client, mock_metrics
):
    """Test successful configuration retrieval."""
    config_data = b"global\n    daemon\n\nfrontend web\n    bind *:80"
    mock_config = create_configuration_response(config_data)

    with patch_dataplane_apis(mock_client, mock_metrics) as mocks:
        # Setup mocks - use the asyncio method return_value
        from tests.unit.dataplane.adapter_fixtures import create_mock_api_response

        mocks["api_mocks"][
            "get_ha_proxy_configuration"
        ].asyncio.return_value = create_mock_api_response(content=mock_config)

        # Execute
        result = await validation_api.get_current_configuration()

        # Verify
        assert result == config_data.decode("utf-8")


@pytest.mark.asyncio
async def test_get_current_configuration_no_data(
    validation_api, mock_client, mock_metrics
):
    """Test configuration retrieval when no data is available."""
    mock_config = create_configuration_response()  # No data attribute

    with patch_dataplane_apis(mock_client, mock_metrics) as mocks:
        # Setup mocks - use the asyncio method return_value
        from tests.unit.dataplane.adapter_fixtures import create_mock_api_response

        mocks["api_mocks"][
            "get_ha_proxy_configuration"
        ].asyncio.return_value = create_mock_api_response(content=mock_config)

        # Execute
        result = await validation_api.get_current_configuration()

        # Verify
        assert result is None


class TestValidationAPIAdvancedValidation:
    """Test advanced validation scenarios and edge cases."""

    @pytest.mark.asyncio
    async def test_validate_configuration_complex_config(
        self, validation_api, mock_metrics
    ):
        """Test validation with complex HAProxy configuration."""
        complex_config = """global
    daemon
    chroot /var/lib/haproxy
    stats socket /var/run/haproxy/admin.sock mode 660 level admin
    stats timeout 30s
    user haproxy
    group haproxy

defaults
    mode http
    timeout connect 5s
    timeout client 30s
    timeout server 30s
    option httplog
    option dontlognull

frontend web
    bind *:80
    bind *:443 ssl crt /etc/ssl/certs/
    redirect scheme https if !{ ssl_fc }
    use_backend api if { path_beg /api }
    default_backend web

backend web
    balance roundrobin
    server web1 192.168.1.10:8080 check
    server web2 192.168.1.11:8080 check

backend api
    balance leastconn
    server api1 192.168.1.20:8080 check
    server api2 192.168.1.21:8080 check"""

        with (
            patch(
                "haproxy_template_ic.dataplane.validation_api.post_haproxy_configuration"
            ) as mock_post_config,
            patch("haproxy_template_ic.dataplane.validation_api.record_span_event"),
        ):
            mock_response = Mock()
            mock_response.reload_info = Mock()
            mock_response.reload_info.reload_triggered = False
            mock_response.reload_info.reload_id = None
            mock_post_config.return_value = mock_response

            await validation_api.validate_configuration(complex_config)

            # Verify the complex config was processed correctly
            mock_post_config.assert_called_once_with(
                endpoint=validation_api.endpoint,
                body=complex_config + "\n",
                skip_reload=True,
                only_validate=True,
            )

    @pytest.mark.asyncio
    async def test_validate_configuration_with_syntax_errors(
        self, validation_api, mock_metrics
    ):
        """Test validation with configuration syntax errors."""
        invalid_config = """global
    daemon
    invalid_directive

frontend web
    bind *:80
    missing_backend_reference unknown_backend"""

        with (
            patch_dataplane_apis(mock_metrics=mock_metrics) as mocks,
            patch(
                "haproxy_template_ic.dataplane.validation_api.parse_validation_error_details"
            ) as mock_parse_error,
        ):
            mocks["api_mocks"][
                "post_haproxy_configuration"
            ].asyncio_detailed.side_effect = Exception("Configuration syntax error")
            mock_parse_error.return_value = (
                "Invalid directive 'invalid_directive'",
                3,
                "invalid_directive",
            )

            with expect_validation_error("Configuration validation failed"):
                await validation_api.validate_configuration(invalid_config)

            # Verify error parsing was called
            mock_parse_error.assert_called_once()

    @pytest.mark.asyncio
    async def test_validate_configuration_whitespace_handling(
        self, validation_api, mock_metrics
    ):
        """Test validation handles whitespace correctly."""
        config_with_whitespace = (
            "   \n\nglobal\n    daemon\n\n\nfrontend web\n    bind *:80\n   \n"
        )

        with (
            patch(
                "haproxy_template_ic.dataplane.validation_api.post_haproxy_configuration"
            ) as mock_post_config,
            patch("haproxy_template_ic.dataplane.validation_api.record_span_event"),
        ):
            mock_response = Mock()
            mock_response.reload_info = Mock()
            mock_response.reload_info.reload_triggered = False
            mock_response.reload_info.reload_id = None
            mock_post_config.return_value = mock_response

            await validation_api.validate_configuration(config_with_whitespace)

            # Verify whitespace is preserved, no extra newline needed since it already ends with \n
            mock_post_config.assert_called_once_with(
                endpoint=validation_api.endpoint,
                body=config_with_whitespace,  # No extra newline since it already ends with \n
                skip_reload=True,
                only_validate=True,
            )


class TestValidationAPIAdvancedDeployment:
    """Test advanced deployment scenarios and edge cases."""

    @pytest.mark.asyncio
    async def test_deploy_configuration_large_config(
        self, validation_api, mock_client, mock_metrics
    ):
        """Test deployment with large configuration."""
        # Generate large configuration
        large_config = "global\n    daemon\n\n"
        for i in range(100):
            large_config += f"backend backend_{i}\n"
            large_config += "    balance roundrobin\n"
            for j in range(5):
                large_config += (
                    f"    server server_{j} 192.168.{i}.{j + 10}:8080 check\n"
                )
            large_config += "\n"

        with (
            patch(
                "haproxy_template_ic.dataplane.validation_api.post_haproxy_configuration"
            ) as mock_post_config,
            patch(
                "haproxy_template_ic.dataplane.validation_api.get_configuration_version"
            ) as mock_get_version,
            patch("haproxy_template_ic.dataplane.validation_api.record_span_event"),
        ):
            # Import adapter fixtures to create proper APIResponse mock
            from tests.unit.dataplane.adapter_fixtures import create_mock_api_response

            mock_get_version.return_value = create_mock_api_response(content=5)

            # Create proper APIResponse with ReloadInfo
            mock_response = create_mock_api_response(
                content="success",  # Deployment response content
                reload_id="reload-large-config",
            )
            mock_post_config.return_value = mock_response

            result = await validation_api.deploy_configuration(large_config)

            # Verify large config deployment
            assert isinstance(result, ValidationDeploymentResult)
            # Large config already ends with newline, so no additional newline is added
            expected_size = (
                len(large_config)
                if large_config.endswith("\n")
                else len(large_config + "\n")
            )
            assert result.size == expected_size
            assert result.reload_info.reload_id == "reload-large-config"
            assert result.status == "success"

    @pytest.mark.asyncio
    async def test_deploy_configuration_with_ssl_certs(
        self, validation_api, mock_client, mock_metrics
    ):
        """Test deployment with SSL certificate references."""
        ssl_config = """global
    daemon

defaults
    mode http
    timeout connect 5s
    timeout client 30s
    timeout server 30s

frontend https
    bind *:443 ssl crt /etc/ssl/certs/server.pem
    bind *:443 ssl crt /etc/ssl/certs/wildcard.pem
    redirect scheme https if !{ ssl_fc }
    default_backend web

backend web
    balance roundrobin
    server web1 192.168.1.10:8080 check ssl verify none"""

        with (
            patch(
                "haproxy_template_ic.dataplane.validation_api.post_haproxy_configuration"
            ) as mock_post_config,
            patch(
                "haproxy_template_ic.dataplane.validation_api.get_configuration_version"
            ) as mock_get_version,
            patch("haproxy_template_ic.dataplane.validation_api.record_span_event"),
        ):
            # Import adapter fixtures to create proper APIResponse mock
            from tests.unit.dataplane.adapter_fixtures import create_mock_api_response

            mock_get_version.return_value = create_mock_api_response(content=2)

            # Create proper APIResponse with ReloadInfo
            mock_response = create_mock_api_response(
                content="success",  # Deployment response content
                reload_id="reload-ssl",
            )
            mock_post_config.return_value = mock_response

            result = await validation_api.deploy_configuration(ssl_config)

            # Verify SSL config deployment
            assert result.reload_info.reload_id == "reload-ssl"
            assert result.status == "success"

    @pytest.mark.asyncio
    async def test_deploy_configuration_deployment_failure(
        self, validation_api, mock_client, mock_metrics
    ):
        """Test deployment failure handling."""
        config_content = "global\n    daemon"

        with (
            patch_dataplane_apis(mock_client, mock_metrics) as mocks,
            patch(
                "haproxy_template_ic.dataplane.validation_api.get_configuration_version"
            ) as mock_get_version,
            patch(
                "haproxy_template_ic.dataplane.validation_api.set_span_error"
            ) as mock_set_error,
        ):
            # Import adapter fixtures to create proper APIResponse mock
            from tests.unit.dataplane.adapter_fixtures import create_mock_api_response

            mock_get_version.return_value = create_mock_api_response(content=3)
            mocks["api_mocks"][
                "post_haproxy_configuration"
            ].asyncio_detailed.side_effect = Exception("Deployment failed")

            with expect_validation_error("Configuration deployment failed"):
                await validation_api.deploy_configuration(config_content)

            mock_set_error.assert_called_once()

    @pytest.mark.asyncio
    async def test_deploy_configuration_partial_reload(
        self, validation_api, mock_client, mock_metrics
    ):
        """Test deployment with partial reload (202 response but no reload ID)."""
        config_content = "global\n    daemon\n\nfrontend web\n    bind *:80"

        with (
            patch(
                "haproxy_template_ic.dataplane.validation_api.post_haproxy_configuration"
            ) as mock_post_config,
            patch(
                "haproxy_template_ic.dataplane.validation_api.get_configuration_version"
            ) as mock_get_version,
            patch("haproxy_template_ic.dataplane.validation_api.record_span_event"),
        ):
            # Import adapter fixtures to create proper APIResponse mock
            from tests.unit.dataplane.adapter_fixtures import create_mock_api_response

            mock_get_version.return_value = create_mock_api_response(content=4)

            # Create proper APIResponse with no reload ID (None)
            mock_response = create_mock_api_response(
                content="success",  # Deployment response content
                reload_id=None,  # No reload ID for partial reload test
            )
            mock_post_config.return_value = mock_response

            result = await validation_api.deploy_configuration(config_content)

            # Verify partial reload handling
            assert result.reload_info.reload_triggered is False
            assert result.reload_info.reload_id is None
            assert result.status == "success"


class TestValidationAPIVersionAndInfo:
    """Test version and information retrieval functionality."""

    @pytest.mark.asyncio
    async def test_get_version_with_detailed_info(
        self, validation_api, mock_client, mock_metrics
    ):
        """Test version retrieval with detailed API and HAProxy info."""
        mock_info = create_api_info_response(
            api_version="3.1", build_date="2024-01-15", version="dataplane-3.0.1"
        )
        mock_process_info = create_haproxy_process_info_response(
            version="3.1.2", release_date="2024-02-01", uptime="30d 12h 15m"
        )

        with patch_dataplane_apis(mock_client, mock_metrics) as mocks:
            # Setup mocks - create APIResponse objects with the mock data
            from tests.unit.dataplane.adapter_fixtures import create_mock_api_response

            mocks["api_mocks"][
                "get_info"
            ].asyncio.return_value = create_mock_api_response(content=mock_info)
            mocks["api_mocks"][
                "get_haproxy_process_info"
            ].asyncio.return_value = create_mock_api_response(content=mock_process_info)

            result = await validation_api.get_version()

            expected = {
                "api_version": "3.1",
                "build_date": "2024-01-15",
                "version": "dataplane-3.0.1",
                "haproxy": {
                    "version": "3.1.2",
                    "release_date": "2024-02-01",
                    "uptime": "30d 12h 15m",
                },
            }
            assert result == expected

    @pytest.mark.asyncio
    async def test_get_version_api_error(
        self, validation_api, mock_client, mock_metrics
    ):
        """Test version retrieval with API errors."""
        with (
            patch_dataplane_apis(mock_client, mock_metrics) as mocks,
            expect_dataplane_error("Failed to get version"),
        ):
            mocks["api_mocks"]["get_info"].asyncio.side_effect = Exception("API Error")

            await validation_api.get_version()

    @pytest.mark.asyncio
    async def test_get_current_configuration_large_config(
        self, validation_api, mock_client, mock_metrics
    ):
        """Test retrieving large configuration content."""
        # Generate large configuration data
        large_config_data = "global\n    daemon\n\n"
        for i in range(200):
            large_config_data += f"backend backend_{i}\n    balance roundrobin\n\n"

        mock_config = create_configuration_response(large_config_data.encode("utf-8"))

        with patch_dataplane_apis(mock_client, mock_metrics) as mocks:
            from tests.unit.dataplane.adapter_fixtures import create_mock_api_response

            mocks["api_mocks"][
                "get_ha_proxy_configuration"
            ].asyncio.return_value = create_mock_api_response(content=mock_config)

            result = await validation_api.get_current_configuration()

            # Verify large config retrieval
            assert result == large_config_data
            assert len(result) > 8000  # Verify it's actually large

    @pytest.mark.asyncio
    async def test_get_current_configuration_with_unicode(
        self, validation_api, mock_client, mock_metrics
    ):
        """Test configuration retrieval with Unicode content."""
        unicode_config = """# Configuration with émojis and ünïcødé characters
global
    daemon
    # Comment with special chars: 🚀 💻 🔧

frontend web_ünïcødé
    bind *:80
    # Backend with special naming
    default_backend wéb_béckénd

backend wéb_béckénd
    balance roundrobin
    server sérver1 192.168.1.10:8080 check"""

        mock_config = create_configuration_response(unicode_config.encode("utf-8"))

        with patch_dataplane_apis(mock_client, mock_metrics) as mocks:
            from tests.unit.dataplane.adapter_fixtures import create_mock_api_response

            mocks["api_mocks"][
                "get_ha_proxy_configuration"
            ].asyncio.return_value = create_mock_api_response(content=mock_config)

            result = await validation_api.get_current_configuration()

            # Verify Unicode handling
            assert result == unicode_config
            assert "émojis" in result
            assert "ünïcødé" in result
            assert "🚀" in result


class TestValidationAPIIntegrationScenarios:
    """Test validation API in realistic integration scenarios."""

    @pytest.mark.asyncio
    async def test_complete_configuration_lifecycle(
        self, validation_api, mock_client, mock_metrics
    ):
        """Test complete configuration validation and deployment lifecycle."""
        config_content = """global
    daemon
    chroot /var/lib/haproxy

defaults
    mode http
    timeout connect 5s
    timeout client 30s
    timeout server 30s

frontend api
    bind *:80
    use_backend api_v1 if { path_beg /v1 }
    use_backend api_v2 if { path_beg /v2 }
    default_backend api_v1

backend api_v1
    balance roundrobin
    server api1_v1 192.168.1.10:8080 check
    server api2_v1 192.168.1.11:8080 check

backend api_v2
    balance leastconn
    server api1_v2 192.168.1.20:8080 check
    server api2_v2 192.168.1.21:8080 check"""

        with (
            patch(
                "haproxy_template_ic.dataplane.validation_api.post_haproxy_configuration"
            ) as mock_post_config,
            patch(
                "haproxy_template_ic.dataplane.validation_api.get_configuration_version"
            ) as mock_get_version,
            patch("haproxy_template_ic.dataplane.validation_api.record_span_event"),
        ):
            # Import adapter fixtures to create proper APIResponse mocks
            from tests.unit.dataplane.adapter_fixtures import create_mock_api_response

            # Setup validation mock (no reload for validation-only)
            mock_validation_response = create_mock_api_response(
                content="validation_success",
                reload_id=None,  # No reload for validation
            )

            # Setup deployment mock
            mock_get_version.return_value = create_mock_api_response(content=6)
            mock_deployment_response = create_mock_api_response(
                content="success", reload_id="lifecycle-reload"
            )

            # Configure side_effect to return validation response first, then deployment response
            mock_post_config.side_effect = [
                mock_validation_response,
                mock_deployment_response,
            ]

            # First validate
            await validation_api.validate_configuration(config_content)

            # Then deploy
            result = await validation_api.deploy_configuration(config_content)

            # Verify both operations
            assert (
                mock_post_config.call_count == 2
            )  # One validation call + one deployment call

            assert isinstance(result, ValidationDeploymentResult)
            assert result.reload_info.reload_id == "lifecycle-reload"
            assert result.status == "success"

    @pytest.mark.asyncio
    async def test_validation_api_performance_scenario(
        self, validation_api, mock_client, mock_metrics
    ):
        """Test validation API performance with multiple rapid operations."""
        configs = [
            f"global\n    daemon\n\nfrontend web_{i}\n    bind *:{8080 + i}\n    default_backend backend_{i}\n\nbackend backend_{i}\n    server server1 192.168.1.{10 + i}:8080 check"
            for i in range(10)
        ]

        with (
            patch(
                "haproxy_template_ic.dataplane.validation_api.post_haproxy_configuration"
            ) as mock_post_config,
            patch(
                "haproxy_template_ic.dataplane.validation_api.get_configuration_version"
            ) as mock_get_version,
            patch("haproxy_template_ic.dataplane.validation_api.record_span_event"),
        ):
            # Import adapter fixtures to create proper APIResponse mock
            from tests.unit.dataplane.adapter_fixtures import create_mock_api_response

            mock_get_version.return_value = create_mock_api_response(content=1)

            # Create proper APIResponse with ReloadInfo
            mock_response = create_mock_api_response(
                content="success",  # Deployment response content
                reload_id="perf-reload",
            )
            mock_post_config.return_value = mock_response

            # Deploy all configurations rapidly
            results = []
            for config in configs:
                result = await validation_api.deploy_configuration(config)
                results.append(result)

            # Verify all deployments succeeded
            assert len(results) == 10
            for result in results:
                assert isinstance(result, ValidationDeploymentResult)
                assert result.status == "success"

            # Verify all API calls were made
            assert mock_post_config.call_count == 10
