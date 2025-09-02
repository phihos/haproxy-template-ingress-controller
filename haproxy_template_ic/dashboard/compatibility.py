"""
Version compatibility management for dashboard and operator.

Handles different versions of the operator gracefully by detecting capabilities
and adapting the dashboard functionality accordingly.
"""

from enum import Enum
from typing import Set, Optional
import logging

logger = logging.getLogger(__name__)

__all__ = ["CompatibilityLevel", "check_compatibility", "CompatibilityChecker"]


class CompatibilityLevel(Enum):
    """Different levels of compatibility between dashboard and operator."""

    FULL = "full"  # All dashboard features available
    ENHANCED = "enhanced"  # Some new commands available
    BASIC = "basic"  # Only core commands (dump all, etc.)
    LEGACY = "legacy"  # Very old operator, minimal support


class CompatibilityChecker:
    """Manages version compatibility checking and feature availability."""

    def __init__(self):
        self.server_version: Optional[str] = None
        self.server_capabilities: Set[str] = set()
        self.compatibility_level: Optional[CompatibilityLevel] = None

    async def check_compatibility(self, socket_data_func) -> CompatibilityLevel:
        """Check server version and determine compatibility mode.

        Args:
            socket_data_func: Async function to fetch data from management socket

        Returns:
            CompatibilityLevel indicating what features are available
        """
        try:
            # Try new version command first
            logger.debug("Checking compatibility: trying 'version' command")
            response = await socket_data_func("version")

            if isinstance(response, dict) and not response.get("error"):
                self.server_version = response.get("version", "unknown")
                self.server_capabilities = set(response.get("capabilities", []))
                logger.debug(
                    f"Version command succeeded: version={self.server_version}, capabilities={list(self.server_capabilities)}"
                )

                # Determine compatibility based on capabilities
                if "dump_dashboard" in self.server_capabilities:
                    self.compatibility_level = CompatibilityLevel.FULL
                    logger.debug("Detected FULL compatibility (has dump_dashboard)")
                elif "dump_stats" in self.server_capabilities:
                    self.compatibility_level = CompatibilityLevel.ENHANCED
                    logger.debug("Detected ENHANCED compatibility (has dump_stats)")
                else:
                    self.compatibility_level = CompatibilityLevel.BASIC
                    logger.debug("Detected BASIC compatibility (no advanced commands)")

                logger.info(
                    f"Detected operator version {self.server_version} with {len(self.server_capabilities)} capabilities"
                )
                return self.compatibility_level
            else:
                logger.debug(
                    f"Version command returned error or invalid response: {response}"
                )

        except Exception as e:
            logger.debug(f"Version command failed: {e}")

        # Fallback: try basic commands to see what's available
        try:
            logger.debug("Compatibility fallback: trying 'dump all' command")
            response = await socket_data_func("dump all")
            if isinstance(response, dict) and not response.get("error"):
                # Old operator but working
                self.compatibility_level = CompatibilityLevel.BASIC
                logger.debug("dump all command succeeded - using BASIC compatibility")
                logger.info(
                    "Detected older operator without version command - using basic compatibility mode"
                )
                return self.compatibility_level
            else:
                logger.debug(
                    f"dump all command returned error or invalid response: {response}"
                )
        except Exception as e:
            logger.debug(f"Basic command test failed: {e}")

        # Very old or broken operator
        self.compatibility_level = CompatibilityLevel.LEGACY
        logger.debug("All compatibility checks failed - falling back to LEGACY mode")
        logger.warning(
            "Operator compatibility check failed - using legacy mode with minimal features"
        )
        return self.compatibility_level

    def has_feature(self, feature: str) -> bool:
        """Check if a specific feature is available based on compatibility level."""
        if self.compatibility_level is None:
            return False

        # Feature availability matrix
        feature_matrix = {
            CompatibilityLevel.FULL: {
                "operator_status",
                "pod_details",
                "resource_stats",
                "performance_metrics",
                "activity_feed",
                "dataplane_status",
                "template_stats",
                "enhanced_commands",
            },
            CompatibilityLevel.ENHANCED: {
                "operator_status",
                "pod_details",
                "resource_stats",
                "template_stats",
                "partial_enhanced_commands",
            },
            CompatibilityLevel.BASIC: {
                "operator_status",
                "pod_details",
                "resource_stats",
                "template_stats",
            },
            CompatibilityLevel.LEGACY: {
                "operator_status"  # Minimal functionality
            },
        }

        return feature in feature_matrix.get(self.compatibility_level, set())

    def get_available_commands(self) -> Set[str]:
        """Get list of available management socket commands."""
        if self.server_capabilities:
            return self.server_capabilities.copy()

        # Fallback based on compatibility level
        if self.compatibility_level == CompatibilityLevel.FULL:
            return {
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
        elif self.compatibility_level == CompatibilityLevel.ENHANCED:
            return {
                "dump_all",
                "dump_indices",
                "dump_config",
                "dump_deployments",
                "dump_debouncer",
                "dump_stats",
                "get",
            }
        elif self.compatibility_level == CompatibilityLevel.BASIC:
            return {
                "dump_all",
                "dump_indices",
                "dump_config",
                "dump_deployments",
                "dump_debouncer",
                "get",
            }
        else:  # LEGACY
            return {"dump_all"}


# Convenience function for simple compatibility checking
async def check_compatibility(socket_data_func) -> CompatibilityLevel:
    """Simple convenience function to check compatibility.

    Args:
        socket_data_func: Async function to fetch data from management socket

    Returns:
        CompatibilityLevel indicating what features are available
    """
    checker = CompatibilityChecker()
    return await checker.check_compatibility(socket_data_func)
