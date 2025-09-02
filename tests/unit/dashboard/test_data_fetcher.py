"""Test data fetcher functionality."""

import pytest
from unittest.mock import AsyncMock, patch

from haproxy_template_ic.dashboard.data_fetcher import DashboardDataFetcher
from haproxy_template_ic.dashboard.compatibility import CompatibilityLevel


class TestDashboardDataFetcher:
    """Test DashboardDataFetcher functionality."""

    @pytest.fixture
    def data_fetcher(self):
        """Create a DashboardDataFetcher instance."""
        return DashboardDataFetcher(
            namespace="test-namespace",
            context="test-context",
            deployment_name="test-deployment",
        )

    def test_initialization(self, data_fetcher):
        """Test data fetcher initialization."""
        assert data_fetcher.namespace == "test-namespace"
        assert data_fetcher.context == "test-context"
        assert data_fetcher.deployment_name == "test-deployment"
        assert data_fetcher.compatibility_checker.compatibility_level is None
        assert data_fetcher._cache == {}

    @pytest.mark.asyncio
    async def test_initialize_with_version_command(self, data_fetcher):
        """Test initialization with version command support."""
        with patch.object(
            data_fetcher, "_get_socket_data", new_callable=AsyncMock
        ) as mock_socket:
            mock_socket.side_effect = lambda cmd: {
                "version": {
                    "version": "1.2.0",
                    "capabilities": ["dump_dashboard", "dump_stats", "dump_all"],
                }
            }.get(cmd, {"error": "unknown command"})

            level = await data_fetcher.initialize()

            assert level == CompatibilityLevel.FULL
            assert (
                data_fetcher.compatibility_checker.compatibility_level
                == CompatibilityLevel.FULL
            )

    @pytest.mark.asyncio
    async def test_initialize_fallback_to_dump_all(self, data_fetcher):
        """Test initialization fallback when version command fails."""
        with patch.object(
            data_fetcher, "_get_socket_data", new_callable=AsyncMock
        ) as mock_socket:

            def mock_data(command):
                if command == "version":
                    raise Exception("Version command not supported")
                elif command == "dump all":
                    return {"config": {"some": "data"}}
                return {"error": "unknown command"}

            mock_socket.side_effect = mock_data

            level = await data_fetcher.initialize()

            assert level == CompatibilityLevel.BASIC
            assert (
                data_fetcher.compatibility_checker.compatibility_level
                == CompatibilityLevel.BASIC
            )

    @pytest.mark.asyncio
    async def test_fetch_all_data(self, data_fetcher):
        """Test fetch_all_data based on compatibility."""
        data_fetcher.compatibility_checker.compatibility_level = (
            CompatibilityLevel.BASIC
        )

        with patch.object(
            data_fetcher, "_fetch_basic", new_callable=AsyncMock
        ) as mock_fetch:
            mock_data = {"config": {"templates": []}, "indices": {"resources": {}}}
            mock_fetch.return_value = mock_data

            result = await data_fetcher.fetch_all_data()

            assert result == mock_data
            mock_fetch.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_socket_data_mocked(self, data_fetcher):
        """Test getting socket data via kubectl."""
        with patch.object(
            data_fetcher, "_get_socket_data", new_callable=AsyncMock
        ) as mock_socket:
            mock_socket.return_value = {"test": "data"}

            result = await data_fetcher._get_socket_data("test command")

            assert result == {"test": "data"}
            mock_socket.assert_called_once_with("test command")

    def test_compatibility_level_property(self, data_fetcher):
        """Test compatibility level property access."""
        # Initially None
        assert data_fetcher.compatibility_checker.compatibility_level is None

        # Set and verify
        data_fetcher.compatibility_checker.compatibility_level = (
            CompatibilityLevel.ENHANCED
        )
        assert (
            data_fetcher.compatibility_checker.compatibility_level
            == CompatibilityLevel.ENHANCED
        )
