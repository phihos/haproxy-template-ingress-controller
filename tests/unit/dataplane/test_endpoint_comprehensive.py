"""
Comprehensive unit tests for DataplaneEndpoint functionality.

Tests endpoint creation, validation, and utility methods.
"""

import pytest

from haproxy_template_ic.dataplane.endpoint import (
    DataplaneEndpoint,
    DataplaneEndpointSet,
)
from haproxy_template_ic.credentials import DataplaneAuth


@pytest.fixture
def test_auth():
    """Create test authentication."""
    return DataplaneAuth(username="admin", password="test-password")


def test_endpoint_creation_basic(test_auth):
    """Test basic endpoint creation."""
    endpoint = DataplaneEndpoint(url="http://localhost:5555", dataplane_auth=test_auth)

    assert endpoint.url == "http://localhost:5555/v3"
    assert endpoint.dataplane_auth == test_auth
    assert endpoint.pod_name is None


def test_endpoint_creation_with_pod_name(test_auth):
    """Test endpoint creation with pod name."""
    endpoint = DataplaneEndpoint(
        url="http://localhost:5555", dataplane_auth=test_auth, pod_name="test-pod"
    )

    assert endpoint.pod_name == "test-pod"


def test_endpoint_url_normalization(test_auth):
    """Test URL normalization."""
    # URL without /v3 should get it added
    endpoint1 = DataplaneEndpoint(url="http://localhost:5555", dataplane_auth=test_auth)
    assert endpoint1.url == "http://localhost:5555/v3"

    # URL with /v3 should remain unchanged
    endpoint2 = DataplaneEndpoint(
        url="http://localhost:5555/v3", dataplane_auth=test_auth
    )
    assert endpoint2.url == "http://localhost:5555/v3"


def test_endpoint_validation_empty_url(test_auth):
    """Test endpoint validation with empty URL."""
    with pytest.raises(ValueError, match="URL cannot be empty"):
        DataplaneEndpoint(url="", dataplane_auth=test_auth)


def test_endpoint_validation_invalid_url(test_auth):
    """Test endpoint validation with invalid URL format."""
    with pytest.raises(ValueError, match="Invalid URL format"):
        DataplaneEndpoint(url="not-a-url", dataplane_auth=test_auth)


def test_endpoint_hostname_property(test_auth):
    """Test hostname property extraction."""
    endpoint = DataplaneEndpoint(
        url="http://192.168.1.10:5555", dataplane_auth=test_auth
    )
    assert endpoint.hostname == "192.168.1.10"


def test_endpoint_hostname_property_with_domain(test_auth):
    """Test hostname property with domain name."""
    endpoint = DataplaneEndpoint(
        url="https://haproxy.example.com:8080", dataplane_auth=test_auth
    )
    assert endpoint.hostname == "haproxy.example.com"


def test_endpoint_display_name_with_pod(test_auth):
    """Test display name with pod name."""
    endpoint = DataplaneEndpoint(
        url="http://localhost:5555", dataplane_auth=test_auth, pod_name="test-pod"
    )
    assert endpoint.display_name == "test-pod"


def test_endpoint_display_name_without_pod(test_auth):
    """Test display name without pod name."""
    endpoint = DataplaneEndpoint(url="http://localhost:5555", dataplane_auth=test_auth)
    assert endpoint.display_name == "localhost"


def test_endpoint_str_representation(test_auth):
    """Test string representation."""
    endpoint = DataplaneEndpoint(
        url="http://localhost:5555", dataplane_auth=test_auth, pod_name="test-pod"
    )
    str_repr = str(endpoint)
    assert "test-pod" in str_repr


def test_endpoint_immutability(test_auth):
    """Test that endpoints are immutable."""
    endpoint = DataplaneEndpoint(url="http://localhost:5555", dataplane_auth=test_auth)

    # Should not be able to modify attributes
    with pytest.raises(AttributeError):
        endpoint.url = "http://other:5555"


def test_endpoint_set_creation(test_auth):
    """Test DataplaneEndpointSet creation."""
    validation_endpoint = DataplaneEndpoint(
        url="http://localhost:5555", dataplane_auth=test_auth, pod_name="validation"
    )
    production_endpoint = DataplaneEndpoint(
        url="http://localhost:5556", dataplane_auth=test_auth, pod_name="prod-1"
    )

    endpoint_set = DataplaneEndpointSet(
        validation=validation_endpoint, production=[production_endpoint]
    )

    assert endpoint_set.validation == validation_endpoint
    assert len(endpoint_set.production) == 1
    assert endpoint_set.production[0] == production_endpoint


def test_endpoint_set_immutability(test_auth):
    """Test that endpoint sets are immutable."""
    validation_endpoint = DataplaneEndpoint(
        url="http://localhost:5555", dataplane_auth=test_auth
    )
    endpoint_set = DataplaneEndpointSet(validation=validation_endpoint, production=[])

    # Should not be able to modify validation endpoint
    with pytest.raises(AttributeError):
        endpoint_set.validation = validation_endpoint
