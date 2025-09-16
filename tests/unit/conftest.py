"""
Unit test configuration with global network request prevention.

This module provides pytest configuration specifically for unit tests,
including an autouse fixture that prevents any network requests from
being made during unit test execution.
"""

import pytest


@pytest.fixture(autouse=True)
def no_network_requests(monkeypatch):
    """
    Remove network request capabilities for all unit tests.

    This autouse fixture automatically runs for every unit test and removes
    the ability to make HTTP requests, ensuring true unit test isolation.

    Following pytest documentation pattern:
    https://docs.pytest.org/en/7.1.x/how-to/monkeypatch.html#global-patch-example-preventing-requests-from-remote-operations

    Any attempt to make network requests will result in AttributeError,
    forcing tests to properly mock their dependencies.
    """
    # Remove httpx.AsyncClient HTTP methods to prevent async HTTP requests
    # These are used directly in DataplaneClient for text/plain requests
    monkeypatch.delattr("httpx.AsyncClient.post")
    monkeypatch.delattr("httpx.AsyncClient.get")
    monkeypatch.delattr("httpx.AsyncClient.put")
    monkeypatch.delattr("httpx.AsyncClient.delete")
    monkeypatch.delattr("httpx.AsyncClient.patch")
    monkeypatch.delattr("httpx.AsyncClient.head")
    monkeypatch.delattr("httpx.AsyncClient.options")

    # Remove AuthenticatedClient constructor to prevent dataplane API client creation
    # This is used by the generated haproxy-dataplane-v3 client
    monkeypatch.delattr("haproxy_dataplane_v3.AuthenticatedClient.__init__")
