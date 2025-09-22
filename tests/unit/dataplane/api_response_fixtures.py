"""
Standardized API response mocking helpers for dataplane unit tests.

This module provides fixtures for creating consistent API response mocks
that handle the version parameter issues and common response patterns.
"""

import pytest
from typing import Any, Dict


class MockAPIResponse:
    """Mock API response that handles common response patterns."""

    def __init__(self, data: Any = None, status_code: int = 200):
        self.data = data
        self.status_code = status_code

    def json(self):
        """Return JSON representation of the data."""
        return self.data


@pytest.fixture
def mock_api_response_factory():
    """
    Factory for creating standardized API response mocks.

    Returns a function that creates MockAPIResponse instances with proper
    data structure and status codes.
    """

    def create_response(data: Any = None, status_code: int = 200) -> MockAPIResponse:
        return MockAPIResponse(data=data, status_code=status_code)

    return create_response


@pytest.fixture
def mock_empty_list_response(mock_api_response_factory):
    """Create a mock response with an empty list."""
    return mock_api_response_factory([])


@pytest.fixture
def mock_success_response(mock_api_response_factory):
    """Create a mock successful response with basic success data."""
    return mock_api_response_factory({"status": "success"})


@pytest.fixture
def mock_transaction_response(mock_api_response_factory):
    """Create a mock transaction response."""
    return mock_api_response_factory(
        {"id": "test-transaction-123", "status": "in_progress", "version": 1}
    )


@pytest.fixture
def mock_config_sections_response(mock_api_response_factory):
    """Create a mock response for configuration sections."""
    return mock_api_response_factory(
        [
            {"name": "frontend", "type": "frontend"},
            {"name": "backend", "type": "backend"},
        ]
    )


@pytest.fixture
def mock_storage_files_response(mock_api_response_factory):
    """Create a mock response for storage files."""
    return mock_api_response_factory(
        [
            {"storage_name": "test.map", "description": "Test map file"},
            {"storage_name": "test.crt", "description": "Test certificate"},
        ]
    )


class MockHTTPClient:
    """Mock HTTP client that returns consistent responses."""

    def __init__(self, default_response_data: Any = None):
        self.default_response_data = default_response_data or []
        self.responses = {}

    def set_response(self, url_pattern: str, response_data: Any):
        """Set a specific response for a URL pattern."""
        self.responses[url_pattern] = response_data

    async def get(self, url: str, **kwargs) -> MockAPIResponse:
        """Mock GET request that returns configured responses."""
        for pattern, data in self.responses.items():
            if pattern in url:
                return MockAPIResponse(data)
        return MockAPIResponse(self.default_response_data)

    async def post(self, url: str, **kwargs) -> MockAPIResponse:
        """Mock POST request."""
        return MockAPIResponse({"status": "created", "id": "test-id-123"}, 201)

    async def put(self, url: str, **kwargs) -> MockAPIResponse:
        """Mock PUT request."""
        return MockAPIResponse({"status": "updated"})

    async def delete(self, url: str, **kwargs) -> MockAPIResponse:
        """Mock DELETE request."""
        return MockAPIResponse({"status": "deleted"}, 204)


@pytest.fixture
def mock_http_client():
    """Create a mock HTTP client for API testing."""
    return MockHTTPClient()


@pytest.fixture
def mock_dataplane_responses():
    """
    Create a comprehensive set of mock responses for common dataplane operations.

    Returns a dictionary of mock responses that can be used across tests.
    """
    return {
        "empty_list": MockAPIResponse([]),
        "transaction": MockAPIResponse(
            {"id": "test-transaction-123", "status": "in_progress", "version": 1}
        ),
        "config_sections": MockAPIResponse(
            [
                {"name": "frontend", "type": "frontend"},
                {"name": "backend", "type": "backend"},
            ]
        ),
        "storage_files": MockAPIResponse(
            [
                {"storage_name": "test.map", "description": "Test map file"},
                {"storage_name": "test.crt", "description": "Test certificate"},
            ]
        ),
        "success": MockAPIResponse({"status": "success"}),
        "created": MockAPIResponse({"status": "created", "id": "new-id"}, 201),
        "updated": MockAPIResponse({"status": "updated"}),
        "deleted": MockAPIResponse({"status": "deleted"}, 204),
        "error": MockAPIResponse({"error": "Test error"}, 400),
        "not_found": MockAPIResponse({"error": "Not found"}, 404),
    }


def create_mock_client_with_responses(responses: Dict[str, Any]) -> MockHTTPClient:
    """
    Create a mock HTTP client with predefined responses.

    Args:
        responses: Dictionary mapping URL patterns to response data

    Returns:
        Configured MockHTTPClient instance
    """
    client = MockHTTPClient()
    for pattern, data in responses.items():
        client.set_response(pattern, data)
    return client


@pytest.fixture
def mock_version_handling():
    """
    Mock fixture that properly handles version parameters in API calls.

    This fixes the common issue where version parameters are passed as
    string representations instead of integers.
    """

    def normalize_version(version):
        """Normalize version parameter to proper type."""
        if isinstance(version, str):
            try:
                return int(version)
            except ValueError:
                return None
        return version

    return {
        "normalize_version": normalize_version,
        "default_version": 1,
        "test_versions": [1, 2, 3, "1", "2", "3"],
    }


class APIResponseBuilder:
    """Builder class for creating complex API responses."""

    def __init__(self):
        self.data = {}
        self.status_code = 200

    def with_data(self, data: Any):
        """Set response data."""
        self.data = data
        return self

    def with_status(self, status_code: int):
        """Set response status code."""
        self.status_code = status_code
        return self

    def with_success(self):
        """Add success status to response."""
        self.data["status"] = "success"
        return self

    def with_error(self, message: str):
        """Add error to response."""
        self.data["error"] = message
        self.status_code = 400
        return self

    def with_transaction_id(self, transaction_id: str = "test-transaction-123"):
        """Add transaction ID to response."""
        self.data["id"] = transaction_id
        return self

    def with_version(self, version: int = 1):
        """Add version to response."""
        self.data["version"] = version
        return self

    def build(self) -> MockAPIResponse:
        """Build the final response."""
        return MockAPIResponse(self.data, self.status_code)


@pytest.fixture
def api_response_builder():
    """Factory for API response builder."""

    def create_builder():
        return APIResponseBuilder()

    return create_builder
