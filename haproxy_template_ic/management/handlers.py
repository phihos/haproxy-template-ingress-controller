"""
Command handlers for management socket interface.

This module provides command parsing and handling logic for the
management socket server, delegating to appropriate data providers.
"""

import logging
from typing import Any, Dict, List

logger = logging.getLogger(__name__)


class CommandHandler:
    """Handles command parsing and routing for management socket."""

    def __init__(self, memo: Any):
        """Initialize command handler with memo object.

        Args:
            memo: Kopf memo object containing operator state
        """
        self.memo = memo

    def handle_dump_command(self, parts: List[str], metrics: Any) -> Dict[str, Any]:
        """Handle 'dump' commands.

        Args:
            parts: Command parts (e.g., ['dump', 'all'])
            metrics: Metrics collector instance

        Returns:
            Dictionary containing requested dump data
        """
        from haproxy_template_ic.management.data_providers import DataProvider

        data_provider = DataProvider(self.memo)

        if len(parts) < 2:
            return {"error": "Missing dump target"}

        dump_target = parts[1]

        if dump_target == "all":
            return data_provider.dump_all(metrics)
        elif dump_target == "indices":
            return data_provider.dump_indices()
        elif dump_target == "config":
            return data_provider.dump_config()
        elif dump_target == "deployments":
            return data_provider.dump_deployments()
        elif dump_target == "debouncer":
            return data_provider.dump_debouncer()
        elif dump_target == "stats":
            return data_provider.dump_stats()
        elif dump_target == "activity":
            return data_provider.dump_activity()
        elif dump_target == "pods":
            return data_provider.dump_pods()
        elif dump_target == "dashboard":
            return data_provider.dump_dashboard()
        else:
            return {"error": f"Unknown dump target: {dump_target}"}

    def handle_get_command(self, parts: List[str]) -> Dict[str, Any]:
        """Handle 'get' commands.

        Args:
            parts: Command parts (e.g., ['get', 'maps', 'host.map'])

        Returns:
            Dictionary containing requested data
        """
        from haproxy_template_ic.management.data_providers import DataProvider

        data_provider = DataProvider(self.memo)

        if len(parts) < 2:
            return {"error": "Missing get target"}

        get_target = parts[1]

        if get_target == "maps" and len(parts) >= 3:
            map_name = parts[2]
            return data_provider.get_template_source(f"map:{map_name}")
        elif get_target == "template_snippets" and len(parts) >= 3:
            snippet_name = parts[2]
            return data_provider.get_template_source(f"snippet:{snippet_name}")
        elif get_target == "haproxy_config":
            return data_provider.get_template_source("haproxy_config")
        elif get_target == "certificates" and len(parts) >= 3:
            cert_name = parts[2]
            return data_provider.get_template_source(f"cert:{cert_name}")
        elif get_target == "deployments" and len(parts) >= 3:
            endpoint_url = " ".join(parts[2:])
            return data_provider.get_deployment_history(endpoint_url)
        else:
            return {"error": f"Invalid get command: {' '.join(parts)}"}

    def handle_version_command(self) -> Dict[str, Any]:
        """Handle 'version' command.

        Returns:
            Dictionary containing version information
        """
        from haproxy_template_ic.management.data_providers import DataProvider

        data_provider = DataProvider(self.memo)
        return data_provider.get_version_info()

    async def process_command(self, command: str) -> Dict[str, Any]:
        """Process a command string and return response data.

        Args:
            command: Command string to process

        Returns:
            Dictionary containing command response data
        """
        try:
            parts = command.strip().split()
            if not parts:
                return {"error": "Empty command"}

            command_type = parts[0].lower()

            # Import metrics here to avoid circular imports
            from haproxy_template_ic.metrics import get_metrics_collector

            metrics = get_metrics_collector()

            if command_type == "dump":
                return self.handle_dump_command(parts, metrics)
            elif command_type == "get":
                return self.handle_get_command(parts)
            elif command_type == "version":
                return self.handle_version_command()
            else:
                return {"error": f"Unknown command: {command_type}"}

        except Exception as e:
            logger.exception(f"Error processing command '{command}'")
            return {"error": f"Command processing failed: {str(e)}"}
