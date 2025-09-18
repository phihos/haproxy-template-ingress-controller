"""
Unit tests for DataplaneEndpoint and DataplaneEndpointSet classes.

Tests endpoint creation, validation, URL normalization, and set operations.
"""

import pytest
from unittest.mock import patch

from haproxy_template_ic.dataplane.endpoint import (
    DataplaneEndpoint,
    DataplaneEndpointSet,
)
from haproxy_template_ic.credentials import DataplaneAuth
from pydantic import SecretStr
from tests.unit.conftest import (
    generate_endpoint_test_cases,
)


class TestDataplaneEndpoint:
    """Test DataplaneEndpoint dataclass."""

    def test_endpoint_creation_basic(self, test_auth):
        """Test basic endpoint creation."""
        endpoint = DataplaneEndpoint(
            url="http://localhost:5555",
            dataplane_auth=test_auth,
        )

        assert endpoint.url == "http://localhost:5555/v3"  # Normalized
        assert endpoint.dataplane_auth == test_auth
        assert endpoint.pod_name is None

    def test_endpoint_creation_with_pod_name(self, test_auth):
        """Test endpoint creation with pod name."""
        endpoint = DataplaneEndpoint(
            url="http://192.168.1.1:5555",
            dataplane_auth=test_auth,
            pod_name="haproxy-1",
        )

        assert endpoint.url == "http://192.168.1.1:5555/v3"
        assert endpoint.pod_name == "haproxy-1"

    def test_endpoint_creation_with_v3_path(self, test_auth):
        """Test endpoint creation with /v3 already in URL."""
        endpoint = DataplaneEndpoint(
            url="http://localhost:5555/v3",
            dataplane_auth=test_auth,
        )

        # Should not double-append /v3
        assert endpoint.url == "http://localhost:5555/v3"

    def test_endpoint_url_validation_empty(self, test_auth):
        """Test endpoint creation with empty URL."""
        with pytest.raises(ValueError, match="URL cannot be empty"):
            DataplaneEndpoint(
                url="",
                dataplane_auth=test_auth,
            )

    def test_endpoint_url_validation_invalid_format(self, test_auth):
        """Test endpoint creation with invalid URL format."""
        with pytest.raises(ValueError, match="Invalid URL format"):
            DataplaneEndpoint(
                url="not-a-url",
                dataplane_auth=test_auth,
            )

    def test_endpoint_url_validation_missing_scheme(self, test_auth):
        """Test endpoint creation with missing scheme."""
        with pytest.raises(ValueError, match="Invalid URL format"):
            DataplaneEndpoint(
                url="localhost:5555",
                dataplane_auth=test_auth,
            )

    def test_endpoint_immutability(self, test_auth):
        """Test that endpoint is immutable."""
        endpoint = DataplaneEndpoint(
            url="http://localhost:5555",
            dataplane_auth=test_auth,
        )

        # Should not be able to modify frozen dataclass
        with pytest.raises(AttributeError):
            endpoint.url = "http://other:5555"  # type: ignore

        with pytest.raises(AttributeError):
            endpoint.pod_name = "new-pod"  # type: ignore

    @pytest.mark.parametrize("input_url,expected_url", generate_endpoint_test_cases())
    def test_endpoint_url_normalization(self, test_auth, input_url, expected_url):
        """Test URL normalization with various input formats."""
        endpoint = DataplaneEndpoint(
            url=input_url,
            dataplane_auth=test_auth,
        )

        assert endpoint.url == expected_url


class TestDataplaneEndpointProperties:
    """Test DataplaneEndpoint properties."""

    def test_hostname_property_with_ip(self, test_auth):
        """Test hostname extraction from IP address."""
        endpoint = DataplaneEndpoint(
            url="http://192.168.1.1:5555",
            dataplane_auth=test_auth,
        )

        assert endpoint.hostname == "192.168.1.1"

    def test_hostname_property_with_domain(self, test_auth):
        """Test hostname extraction from domain name."""
        endpoint = DataplaneEndpoint(
            url="https://haproxy.example.com:8080",
            dataplane_auth=test_auth,
        )

        assert endpoint.hostname == "haproxy.example.com"

    def test_hostname_property_fallback(self, test_auth):
        """Test hostname property fallback for malformed URLs."""
        with patch(
            "haproxy_template_ic.dataplane.endpoint.extract_hostname_from_url"
        ) as mock_extract:
            mock_extract.return_value = None

            endpoint = DataplaneEndpoint(
                url="http://localhost:5555",
                dataplane_auth=test_auth,
            )

            assert endpoint.hostname == "unknown"

    def test_display_name_with_pod_name(self, test_auth):
        """Test display_name property with pod name."""
        endpoint = DataplaneEndpoint(
            url="http://192.168.1.1:5555",
            dataplane_auth=test_auth,
            pod_name="haproxy-production-1",
        )

        assert endpoint.display_name == "haproxy-production-1"

    def test_display_name_without_pod_name(self, test_auth):
        """Test display_name property without pod name."""
        endpoint = DataplaneEndpoint(
            url="http://192.168.1.1:5555",
            dataplane_auth=test_auth,
        )

        assert endpoint.display_name == "192.168.1.1"

    def test_str_representation(self, test_auth):
        """Test string representation of endpoint."""
        endpoint = DataplaneEndpoint(
            url="http://localhost:5555",
            dataplane_auth=test_auth,
            pod_name="test-pod",
        )

        str_repr = str(endpoint)
        assert "localhost:5555" in str_repr
        assert "test-pod" in str_repr

    def test_repr_representation(self, test_auth):
        """Test repr representation of endpoint."""
        endpoint = DataplaneEndpoint(
            url="http://localhost:5555",
            dataplane_auth=test_auth,
        )

        repr_str = repr(endpoint)
        assert "DataplaneEndpoint" in repr_str
        assert "localhost:5555" in repr_str


class TestDataplaneEndpointSet:
    """Test DataplaneEndpointSet collection."""

    def test_endpoint_set_creation(self):
        """Test basic endpoint set creation."""
        auth = DataplaneAuth(username="admin", password=SecretStr("password"))

        validation_endpoint = DataplaneEndpoint(
            url="http://localhost:5555",
            dataplane_auth=auth,
            pod_name="validation",
        )

        production_endpoints = [
            DataplaneEndpoint(
                url="http://192.168.1.1:5555",
                dataplane_auth=auth,
                pod_name="haproxy-1",
            ),
            DataplaneEndpoint(
                url="http://192.168.1.2:5555",
                dataplane_auth=auth,
                pod_name="haproxy-2",
            ),
        ]

        endpoint_set = DataplaneEndpointSet(
            validation=validation_endpoint,
            production=production_endpoints,
        )

        assert endpoint_set.validation == validation_endpoint
        assert endpoint_set.production == production_endpoints
        assert len(endpoint_set.production) == 2

    def test_endpoint_set_immutability(self):
        """Test that endpoint set is immutable."""
        auth = DataplaneAuth(username="admin", password=SecretStr("password"))

        validation_endpoint = DataplaneEndpoint(
            url="http://localhost:5555",
            dataplane_auth=auth,
        )

        endpoint_set = DataplaneEndpointSet(
            validation=validation_endpoint,
            production=[],
        )

        # Should not be able to modify frozen dataclass
        with pytest.raises(AttributeError):
            endpoint_set.validation = validation_endpoint  # type: ignore

        with pytest.raises(AttributeError):
            endpoint_set.production = []  # type: ignore

    def test_endpoint_set_all_endpoints_property(self):
        """Test all_endpoints property."""
        auth = DataplaneAuth(username="admin", password=SecretStr("password"))

        validation_endpoint = DataplaneEndpoint(
            url="http://localhost:5555",
            dataplane_auth=auth,
        )

        production_endpoints = [
            DataplaneEndpoint(
                url="http://192.168.1.1:5555",
                dataplane_auth=auth,
            ),
            DataplaneEndpoint(
                url="http://192.168.1.2:5555",
                dataplane_auth=auth,
            ),
        ]

        endpoint_set = DataplaneEndpointSet(
            validation=validation_endpoint,
            production=production_endpoints,
        )

        all_endpoints = endpoint_set.all_endpoints()
        assert len(all_endpoints) == 3
        assert validation_endpoint in all_endpoints
        assert all(ep in all_endpoints for ep in production_endpoints)

    def test_endpoint_set_production_count_property(self):
        """Test production_count property."""
        auth = DataplaneAuth(username="admin", password=SecretStr("password"))

        validation_endpoint = DataplaneEndpoint(
            url="http://localhost:5555",
            dataplane_auth=auth,
        )

        endpoint_set = DataplaneEndpointSet(
            validation=validation_endpoint,
            production=[
                DataplaneEndpoint(url="http://192.168.1.1:5555", dataplane_auth=auth),
                DataplaneEndpoint(url="http://192.168.1.2:5555", dataplane_auth=auth),
                DataplaneEndpoint(url="http://192.168.1.3:5555", dataplane_auth=auth),
            ],
        )

        assert len(endpoint_set.production) == 3

    def test_endpoint_set_empty_production(self):
        """Test endpoint set with empty production list."""
        auth = DataplaneAuth(username="admin", password=SecretStr("password"))

        validation_endpoint = DataplaneEndpoint(
            url="http://localhost:5555",
            dataplane_auth=auth,
        )

        endpoint_set = DataplaneEndpointSet(
            validation=validation_endpoint,
            production=[],
        )

        assert len(endpoint_set.production) == 0
        assert len(endpoint_set.all_endpoints()) == 1  # Only validation

    def test_endpoint_set_str_representation(self):
        """Test string representation of endpoint set."""
        auth = DataplaneAuth(username="admin", password=SecretStr("password"))

        validation_endpoint = DataplaneEndpoint(
            url="http://localhost:5555",
            dataplane_auth=auth,
            pod_name="validation",
        )

        production_endpoints = [
            DataplaneEndpoint(
                url="http://192.168.1.1:5555",
                dataplane_auth=auth,
                pod_name="haproxy-1",
            ),
        ]

        endpoint_set = DataplaneEndpointSet(
            validation=validation_endpoint,
            production=production_endpoints,
        )

        str_repr = str(endpoint_set)
        assert "validation" in str_repr
        assert "1 production" in str_repr

    def test_endpoint_set_repr_representation(self):
        """Test repr representation of endpoint set."""
        auth = DataplaneAuth(username="admin", password=SecretStr("password"))

        validation_endpoint = DataplaneEndpoint(
            url="http://localhost:5555",
            dataplane_auth=auth,
        )

        endpoint_set = DataplaneEndpointSet(
            validation=validation_endpoint,
            production=[],
        )

        repr_str = repr(endpoint_set)
        assert "DataplaneEndpointSet" in repr_str


class TestDataplaneEndpointAuthentication:
    """Test authentication handling in endpoints."""

    def test_endpoint_auth_integration(self):
        """Test endpoint with DataplaneAuth integration."""
        auth = DataplaneAuth(
            username="test_user",
            password=SecretStr("test_password"),
        )

        endpoint = DataplaneEndpoint(
            url="http://localhost:5555",
            dataplane_auth=auth,
        )

        assert endpoint.dataplane_auth.username == "test_user"
        assert endpoint.dataplane_auth.password.get_secret_value() == "test_password"

    def test_endpoint_auth_immutability(self):
        """Test that auth credentials are protected."""
        auth = DataplaneAuth(
            username="admin",
            password=SecretStr("secret"),
        )

        endpoint = DataplaneEndpoint(
            url="http://localhost:5555",
            dataplane_auth=auth,
        )

        # Cannot modify the auth object directly through endpoint
        with pytest.raises(AttributeError):
            endpoint.dataplane_auth = auth  # type: ignore


class TestDataplaneEndpointEdgeCases:
    """Test edge cases and error conditions."""

    def test_endpoint_with_special_characters_in_url(self, test_auth):
        """Test endpoint with special characters in URL."""
        endpoint = DataplaneEndpoint(
            url="http://test-host.example.com:5555",
            dataplane_auth=test_auth,
        )

        assert "test-host.example.com" in endpoint.url

    def test_endpoint_with_https_scheme(self, test_auth):
        """Test endpoint with HTTPS scheme."""
        endpoint = DataplaneEndpoint(
            url="https://secure.example.com:8443",
            dataplane_auth=test_auth,
        )

        assert endpoint.url.startswith("https://")
        assert "8443" in endpoint.url

    def test_endpoint_url_normalization_edge_cases(self, test_auth):
        """Test URL normalization with edge cases."""
        # URL with trailing slash
        endpoint1 = DataplaneEndpoint(
            url="http://localhost:5555/",
            dataplane_auth=test_auth,
        )
        assert endpoint1.url == "http://localhost:5555/v3"

        # URL with path components
        endpoint2 = DataplaneEndpoint(
            url="http://localhost:5555/some/path",
            dataplane_auth=test_auth,
        )
        # Normalization should handle this appropriately
        assert "/v3" in endpoint2.url
