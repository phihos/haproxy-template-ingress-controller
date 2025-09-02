"""Test compatibility checking functionality."""

import pytest

from haproxy_template_ic.dashboard.compatibility import (
    CompatibilityLevel,
    check_compatibility,
    CompatibilityChecker,
)


class TestCompatibilityLevel:
    """Test CompatibilityLevel enum."""

    def test_compatibility_levels_exist(self):
        """Test that all compatibility levels are defined."""
        assert CompatibilityLevel.FULL
        assert CompatibilityLevel.ENHANCED
        assert CompatibilityLevel.BASIC
        assert CompatibilityLevel.LEGACY

        # Test values
        assert CompatibilityLevel.FULL.value == "full"
        assert CompatibilityLevel.ENHANCED.value == "enhanced"
        assert CompatibilityLevel.BASIC.value == "basic"
        assert CompatibilityLevel.LEGACY.value == "legacy"


class TestCheckCompatibility:
    """Test compatibility checking logic."""

    @pytest.mark.asyncio
    async def test_full_compatibility(self):
        """Test full compatibility detection via version command."""

        async def mock_socket_func(command):
            if command == "version":
                return {
                    "version": "1.2.0",
                    "capabilities": ["dump_dashboard", "dump_stats", "dump_all"],
                }
            return {"error": "unknown command"}

        level = await check_compatibility(mock_socket_func)
        assert level == CompatibilityLevel.FULL

    @pytest.mark.asyncio
    async def test_enhanced_compatibility(self):
        """Test enhanced compatibility detection."""

        async def mock_socket_func(command):
            if command == "version":
                return {"version": "1.1.0", "capabilities": ["dump_stats", "dump_all"]}
            return {"error": "unknown command"}

        level = await check_compatibility(mock_socket_func)
        assert level == CompatibilityLevel.ENHANCED

    @pytest.mark.asyncio
    async def test_basic_compatibility_via_version(self):
        """Test basic compatibility detection via version command."""

        async def mock_socket_func(command):
            if command == "version":
                return {"version": "1.0.0", "capabilities": ["dump_all"]}
            return {"error": "unknown command"}

        level = await check_compatibility(mock_socket_func)
        assert level == CompatibilityLevel.BASIC

    @pytest.mark.asyncio
    async def test_basic_compatibility_fallback(self):
        """Test basic compatibility detection via fallback."""

        async def mock_socket_func(command):
            if command == "version":
                raise Exception("Version command not supported")
            elif command == "dump all":
                return {"config": "data", "indices": "data"}
            return {"error": "unknown command"}

        level = await check_compatibility(mock_socket_func)
        assert level == CompatibilityLevel.BASIC

    @pytest.mark.asyncio
    async def test_legacy_compatibility(self):
        """Test legacy compatibility when all commands fail."""

        async def mock_socket_func(command):
            raise Exception(f"Command {command} failed")

        level = await check_compatibility(mock_socket_func)
        assert level == CompatibilityLevel.LEGACY


class TestCompatibilityChecker:
    """Test CompatibilityChecker functionality."""

    def test_has_feature_full(self):
        """Test feature availability at full compatibility level."""
        checker = CompatibilityChecker()
        checker.compatibility_level = CompatibilityLevel.FULL

        assert checker.has_feature("operator_status")
        assert checker.has_feature("performance_metrics")
        assert checker.has_feature("activity_feed")
        assert not checker.has_feature("unknown_feature")

    def test_has_feature_enhanced(self):
        """Test feature availability at enhanced compatibility level."""
        checker = CompatibilityChecker()
        checker.compatibility_level = CompatibilityLevel.ENHANCED

        assert checker.has_feature("operator_status")
        assert checker.has_feature("resource_stats")
        assert not checker.has_feature("activity_feed")
        assert not checker.has_feature("performance_metrics")

    def test_has_feature_basic(self):
        """Test feature availability at basic compatibility level."""
        checker = CompatibilityChecker()
        checker.compatibility_level = CompatibilityLevel.BASIC

        assert checker.has_feature("operator_status")
        assert checker.has_feature("template_stats")
        assert not checker.has_feature("performance_metrics")
        assert not checker.has_feature("activity_feed")

    def test_has_feature_legacy(self):
        """Test feature availability at legacy compatibility level."""
        checker = CompatibilityChecker()
        checker.compatibility_level = CompatibilityLevel.LEGACY

        assert checker.has_feature("operator_status")
        assert not checker.has_feature("template_stats")
        assert not checker.has_feature("resource_stats")

    def test_has_feature_no_compatibility_set(self):
        """Test feature availability when compatibility level is not set."""
        checker = CompatibilityChecker()

        assert not checker.has_feature("operator_status")
        assert not checker.has_feature("any_feature")

    def test_get_available_commands_with_capabilities(self):
        """Test getting available commands when server capabilities are known."""
        checker = CompatibilityChecker()
        checker.server_capabilities = {"dump_all", "dump_stats", "version"}

        commands = checker.get_available_commands()
        assert commands == {"dump_all", "dump_stats", "version"}

    def test_get_available_commands_full_fallback(self):
        """Test getting available commands for full compatibility fallback."""
        checker = CompatibilityChecker()
        checker.compatibility_level = CompatibilityLevel.FULL
        checker.server_capabilities = set()  # Empty capabilities

        commands = checker.get_available_commands()
        expected = {
            "dump_all",
            "dump_indices",
            "dump_config",
            "dump_deployments",
            "dump_debouncer",
            "dump_dashboard",
            "dump_stats",
            "dump_activity",
            "dump_pods",
            "get",
            "version",
        }
        assert commands == expected

    def test_get_available_commands_basic_fallback(self):
        """Test getting available commands for basic compatibility fallback."""
        checker = CompatibilityChecker()
        checker.compatibility_level = CompatibilityLevel.BASIC
        checker.server_capabilities = set()

        commands = checker.get_available_commands()
        expected = {
            "dump_all",
            "dump_indices",
            "dump_config",
            "dump_deployments",
            "dump_debouncer",
            "get",
        }
        assert commands == expected

    def test_get_available_commands_legacy_fallback(self):
        """Test getting available commands for legacy compatibility fallback."""
        checker = CompatibilityChecker()
        checker.compatibility_level = CompatibilityLevel.LEGACY
        checker.server_capabilities = set()

        commands = checker.get_available_commands()
        assert commands == {"dump_all"}
