"""
Unit tests for ValidationAPI functionality.

Tests validation and deployment operations for HAProxy configuration.
"""

import pytest
from unittest.mock import Mock, patch

from haproxy_template_ic.dataplane.validation_api import ValidationAPI
from haproxy_template_ic.dataplane.types import (
    ValidationDeploymentResult,
)
from tests.unit.conftest import (
    create_deployment_response,
    create_api_info_response,
    patch_dataplane_apis,
    create_haproxy_process_info_response,
    create_configuration_response,
    create_async_mock_with_return_value,
    expect_validation_error,
)


@pytest.fixture
def validation_api(mock_get_client):
    """Create ValidationAPI instance for testing."""
    from haproxy_template_ic.dataplane.endpoint import DataplaneEndpoint
    from haproxy_template_ic.credentials import DataplaneAuth

    auth = DataplaneAuth(username="admin", password="test")
    endpoint = DataplaneEndpoint(
        url="http://localhost:5555/v3", dataplane_auth=auth, pod_name="test-pod"
    )
    return ValidationAPI(mock_get_client, endpoint)


@pytest.mark.asyncio
async def test_validate_configuration_success(
    validation_api, mock_client, mock_metrics
):
    """Test successful configuration validation."""
    config_content = "global\n    daemon\n\nfrontend web\n    bind *:80"

    with (
        patch(
            "haproxy_template_ic.dataplane.validation_api.post_ha_proxy_configuration"
        ) as mock_post_config,
        patch(
            "haproxy_template_ic.dataplane.validation_api.get_metrics_collector",
            return_value=mock_metrics,
        ),
        patch("haproxy_template_ic.dataplane.validation_api.check_dataplane_response"),
        patch("haproxy_template_ic.dataplane.validation_api.record_span_event"),
    ):
        mock_post_config.asyncio_detailed = create_async_mock_with_return_value(
            Mock(parsed=Mock())
        )

        # Execute
        await validation_api.validate_configuration(config_content)

        # Verify
        mock_post_config.asyncio_detailed.assert_called_once_with(
            client=mock_client,
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
            "post_ha_proxy_configuration"
        ].asyncio_detailed.side_effect = Exception("Validation failed")
        mock_parse_error.return_value = ("Invalid syntax", 5, "line context")

        with expect_validation_error("Configuration validation failed"):
            await validation_api.validate_configuration(config_content)
        mock_set_error.assert_called_once()


@pytest.mark.asyncio
async def test_deploy_configuration_success(validation_api, mock_client, mock_metrics):
    """Test successful configuration deployment."""
    config_content = "global\n    daemon\n\nfrontend web\n    bind *:80"

    mock_result = create_deployment_response("reload-123", "success")

    with (
        patch_dataplane_apis(mock_client, mock_metrics) as mocks,
        patch(
            "haproxy_template_ic.dataplane.validation_api.get_configuration_version"
        ) as mock_get_version,
    ):
        # Setup mocks
        mock_get_version.return_value = 3
        mocks["api_mocks"][
            "post_ha_proxy_configuration"
        ].asyncio_detailed.return_value = Mock(
            parsed=mock_result, status_code=202, headers={"Reload-ID": "reload-123"}
        )

        # Execute
        result = await validation_api.deploy_configuration(config_content)

        # Verify
        assert isinstance(result, ValidationDeploymentResult)
        assert result.size == len(config_content + "\n")  # Account for appended newline
        assert result.reload_info.reload_id == "reload-123"
        assert result.reload_info.reload_triggered
        assert result.status == "success"
        assert result.version == "3"

        mocks["api_mocks"][
            "post_ha_proxy_configuration"
        ].asyncio_detailed.assert_called_once_with(
            client=mock_client,
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

    mock_result = create_deployment_response("reload-456", "success")

    with (
        patch_dataplane_apis(mock_client, mock_metrics) as mocks,
        patch(
            "haproxy_template_ic.dataplane.validation_api.get_configuration_version"
        ) as mock_get_version,
    ):
        # Setup mocks - version is None
        mock_get_version.return_value = None
        mocks["api_mocks"][
            "post_ha_proxy_configuration"
        ].asyncio_detailed.return_value = Mock(
            parsed=mock_result, status_code=202, headers={"Reload-ID": "reload-456"}
        )

        # Execute
        result = await validation_api.deploy_configuration(config_content)

        # Verify fallback to version 1
        mocks["api_mocks"][
            "post_ha_proxy_configuration"
        ].asyncio_detailed.assert_called_once_with(
            client=mock_client,
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
        # Setup mocks - use the asyncio method return_value
        mocks["api_mocks"]["get_info"].asyncio.return_value = mock_info
        mocks["api_mocks"][
            "get_haproxy_process_info"
        ].asyncio.return_value = mock_process_info

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
        mocks["api_mocks"][
            "get_ha_proxy_configuration"
        ].asyncio.return_value = mock_config

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
        mocks["api_mocks"][
            "get_ha_proxy_configuration"
        ].asyncio.return_value = mock_config

        # Execute
        result = await validation_api.get_current_configuration()

        # Verify
        assert result is None
