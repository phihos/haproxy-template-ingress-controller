"""
Configuration API operations for HAProxy Dataplane API.

This module provides the ConfigAPI class for managing HAProxy configuration
sections (backends, frontends, defaults, global) and their nested elements
(servers, ACLs, rules, binds, filters, etc.).

Key features:
- Structured configuration fetching with proper API signatures
- Section-level and element-level CRUD operations
- Support for both named elements (servers) and indexed elements (rules)
- Proper handling of different API call patterns (positional vs keyword args)
"""

import asyncio
import logging
from typing import Any, Callable

from typing_extensions import TypedDict

from haproxy_template_ic.metrics import get_metrics_collector
from .endpoint import DataplaneEndpoint
from .adapter import (
    ReloadInfo,
    create_acl_backend,
    create_acl_frontend,
    create_backend,
    create_bind_frontend,
    create_cache,
    create_defaults_section,
    create_fcgi_app,
    create_filter_backend,
    create_filter_frontend,
    create_frontend,
    create_http_errors_section,
    create_http_request_rule_backend,
    create_http_request_rule_frontend,
    create_http_response_rule_backend,
    create_http_response_rule_frontend,
    create_log_forward,
    create_log_target_backend,
    create_log_target_frontend,
    create_log_target_global,
    create_log_target_log_forward,
    create_log_target_peer,
    create_mailers_section,
    create_peer,
    create_program,
    create_resolver,
    create_ring,
    create_server_backend,
    create_userlist,
    delete_acl_backend,
    delete_acl_frontend,
    delete_backend,
    delete_bind_frontend,
    delete_cache,
    delete_defaults_section,
    delete_fcgi_app,
    delete_filter_backend,
    delete_filter_frontend,
    delete_frontend,
    delete_http_errors_section,
    delete_http_request_rule_backend,
    delete_http_request_rule_frontend,
    delete_http_response_rule_backend,
    delete_http_response_rule_frontend,
    delete_log_forward,
    delete_log_target_backend,
    delete_log_target_frontend,
    delete_log_target_global,
    delete_log_target_log_forward,
    delete_log_target_peer,
    delete_mailers_section,
    delete_peer,
    delete_program,
    delete_resolver,
    delete_ring,
    delete_server_backend,
    delete_userlist,
    edit_mailers_section,
    get_all_acl_backend,
    get_all_acl_frontend,
    get_all_backend_switching_rule_frontend,
    get_all_bind_frontend,
    get_all_filter_backend,
    get_all_filter_frontend,
    get_all_http_request_rule_backend,
    get_all_http_request_rule_frontend,
    get_all_http_response_rule_backend,
    get_all_http_response_rule_frontend,
    get_all_log_target_backend,
    get_all_log_target_frontend,
    get_all_log_target_global,
    get_all_log_target_log_forward,
    get_all_log_target_peer,
    get_all_server_backend,
    get_backends,
    get_caches,
    get_defaults_sections,
    get_fcgi_apps,
    get_frontends,
    get_global,
    get_http_errors_sections,
    get_log_forwards,
    get_mailers_sections,
    get_peer_sections,
    get_programs,
    get_resolvers,
    get_rings,
    get_userlists,
    replace_acl_backend,
    replace_acl_frontend,
    replace_backend,
    replace_bind_frontend,
    replace_cache,
    replace_defaults_section,
    replace_fcgi_app,
    replace_filter_backend,
    replace_filter_frontend,
    replace_frontend,
    replace_global,
    replace_http_errors_section,
    replace_http_request_rule_backend,
    replace_http_request_rule_frontend,
    replace_http_response_rule_backend,
    replace_http_response_rule_frontend,
    replace_log_forward,
    replace_log_target_backend,
    replace_log_target_frontend,
    replace_log_target_global,
    replace_log_target_log_forward,
    replace_log_target_peer,
    replace_program,
    replace_resolver,
    replace_ring,
    replace_server_backend,
    APIResponse,
)
from .types import (
    ConfigChange,
    ConfigChangeResult,
    ConfigChangeType,
    ConfigElementType,
    ConfigSectionType,
    DataplaneAPIError,
)
from .utils import _log_fetch_error


# TypedDict classes for handler configurations
class SectionHandlerConfig(TypedDict, total=False):
    """Type definition for section handler configuration."""

    create: Callable[..., Any] | None
    update: Callable[..., Any] | None
    delete: Callable[..., Any] | None
    id_field: str | None


class ElementHandlerConfig(TypedDict, total=False):
    """Type definition for element handler configuration."""

    create: Callable[..., Any]
    update: Callable[..., Any]
    delete: Callable[..., Any]
    parent_field: str
    id_field: str


__all__ = [
    "ConfigAPI",
]

logger = logging.getLogger(__name__)


class ConfigAPI:
    """Configuration API operations for HAProxy Dataplane API."""

    def __init__(
        self,
        endpoint: DataplaneEndpoint,
    ):
        """Initialize configuration API.

        Args:
            endpoint: Dataplane endpoint for error context
        """
        self.endpoint = endpoint

    async def _call_api_with_reload_info(
        self,
        api_function: Callable,
        *args,
        **kwargs,
    ) -> ReloadInfo:
        """Call an API function and extract reload information from the response.

        This helper method wraps dataplane API calls to extract ReloadInfo from
        HTTP 202 responses with Reload-ID headers.

        Args:
            api_function: The API function to call (should be asyncio_detailed variant)
            *args: Positional arguments to pass to the API function
            **kwargs: Keyword arguments to pass to the API function

        Returns:
            ReloadInfo instance with reload_id if reload was triggered

        Raises:
            DataplaneAPIError: If the API call fails
        """
        try:
            response = await api_function(*args, **kwargs)

            # APIResponse objects from @api_function() decorated functions already have error handling
            # No need for additional error checking

            # Extract reload information from APIResponse
            return response.reload_info

        except Exception as e:
            raise DataplaneAPIError(
                f"API call {getattr(api_function, '__name__', 'unknown')} failed: {e}",
                endpoint=self.endpoint,
                operation=getattr(api_function, "__name__", "unknown"),
                original_error=e,
            ) from e

    async def fetch_structured_configuration(self) -> dict[str, Any]:
        """Fetch complete structured configuration components from HAProxy instance.

        Returns:
            Dictionary containing all configuration sections and their nested elements

        Raises:
            DataplaneAPIError: If fetching configuration fails
        """
        metrics = get_metrics_collector()

        with metrics.time_dataplane_api_operation("fetch_structured"):
            try:
                # Fetch all top-level configuration sections
                config_sections = await self._fetch_top_level_sections(metrics)

                # Fetch nested elements for sections that support them
                nested_elements = await self._fetch_nested_elements(
                    config_sections, metrics
                )

                # Record success metrics and return combined result
                return self._build_configuration_result(
                    config_sections, nested_elements, metrics
                )

            except Exception as e:
                metrics.record_dataplane_api_request("fetch_structured", "error")
                _log_fetch_error("structured configuration", "all", e)
                raise DataplaneAPIError(
                    f"Failed to fetch structured configuration: {e}",
                    endpoint=self.endpoint,
                    operation="fetch_structured",
                    original_error=e,
                ) from e

    async def _fetch_top_level_sections(self, metrics: Any) -> dict[str, Any]:
        """Fetch all top-level configuration sections."""

        async def _fetch_with_timing(operation_name: str, adapter_func, default_value):
            with metrics.time_dataplane_api_operation(operation_name):
                result: APIResponse = await adapter_func(endpoint=self.endpoint)
                return result.content or default_value

        return {
            "backends": await _fetch_with_timing("fetch_backends", get_backends, []),
            "frontends": await _fetch_with_timing("fetch_frontends", get_frontends, []),
            "defaults": await _fetch_with_timing(
                "fetch_defaults", get_defaults_sections, []
            ),
            "global": await _fetch_with_timing("fetch_global", get_global, None),
            "userlists": await _fetch_with_timing("fetch_userlists", get_userlists, []),
            "caches": await _fetch_with_timing("fetch_caches", get_caches, []),
            "mailers": await _fetch_with_timing(
                "fetch_mailers", get_mailers_sections, []
            ),
            "resolvers": await _fetch_with_timing("fetch_resolvers", get_resolvers, []),
            "peers": await _fetch_with_timing("fetch_peers", get_peer_sections, []),
            "fcgi_apps": await _fetch_with_timing("fetch_fcgi_apps", get_fcgi_apps, []),
            "http_errors": await _fetch_with_timing(
                "fetch_http_errors", get_http_errors_sections, []
            ),
            "rings": await _fetch_with_timing("fetch_rings", get_rings, []),
            "log_forwards": await _fetch_with_timing(
                "fetch_log_forwards", get_log_forwards, []
            ),
            "programs": await _fetch_with_timing("fetch_programs", get_programs, []),
        }

    def _create_backend_tasks(
        self, backend_name: str, metrics: Any
    ) -> list[tuple[str, Any]]:
        """Create concurrent tasks for fetching all nested elements of a backend.

        Returns:
            List of (nested_key, task) tuples for concurrent execution
        """

        async def _fetch_with_timing(
            operation_name: str, adapter_func, *args, **kwargs
        ):
            with metrics.time_dataplane_api_operation(operation_name):
                result: APIResponse = await adapter_func(
                    *args, endpoint=self.endpoint, **kwargs
                )
                return result.content or []

        return [
            (
                "backend_servers",
                _fetch_with_timing(
                    f"fetch_backend_servers_{backend_name}",
                    get_all_server_backend,
                    parent_name=backend_name,
                ),
            ),
            (
                "backend_acls",
                _fetch_with_timing(
                    f"fetch_backend_acls_{backend_name}",
                    get_all_acl_backend,
                    parent_name=backend_name,
                ),
            ),
            (
                "backend_http_request_rules",
                _fetch_with_timing(
                    f"fetch_backend_http_request_rules_{backend_name}",
                    get_all_http_request_rule_backend,
                    parent_name=backend_name,
                ),
            ),
            (
                "backend_http_response_rules",
                _fetch_with_timing(
                    f"fetch_backend_http_response_rules_{backend_name}",
                    get_all_http_response_rule_backend,
                    parent_name=backend_name,
                ),
            ),
            (
                "backend_filters",
                _fetch_with_timing(
                    f"fetch_backend_filters_{backend_name}",
                    get_all_filter_backend,
                    parent_name=backend_name,
                ),
            ),
            (
                "backend_log_targets",
                _fetch_with_timing(
                    f"fetch_backend_log_targets_{backend_name}",
                    get_all_log_target_backend,
                    parent_name=backend_name,
                ),
            ),
        ]

    def _create_frontend_tasks(
        self, frontend_name: str, metrics: Any
    ) -> list[tuple[str, Any]]:
        """Create concurrent tasks for fetching all nested elements of a frontend.

        Returns:
            List of (nested_key, task) tuples for concurrent execution
        """

        async def _fetch_with_timing(
            operation_name: str, adapter_func, *args, **kwargs
        ):
            with metrics.time_dataplane_api_operation(operation_name):
                result: APIResponse = await adapter_func(
                    *args, endpoint=self.endpoint, **kwargs
                )
                return result.content or []

        return [
            (
                "frontend_binds",
                _fetch_with_timing(
                    f"fetch_frontend_binds_{frontend_name}",
                    get_all_bind_frontend,
                    parent_name=frontend_name,
                ),
            ),
            (
                "frontend_acls",
                _fetch_with_timing(
                    f"fetch_frontend_acls_{frontend_name}",
                    get_all_acl_frontend,
                    parent_name=frontend_name,
                ),
            ),
            (
                "frontend_http_request_rules",
                _fetch_with_timing(
                    f"fetch_frontend_http_request_rules_{frontend_name}",
                    get_all_http_request_rule_frontend,
                    parent_name=frontend_name,
                ),
            ),
            (
                "frontend_http_response_rules",
                _fetch_with_timing(
                    f"fetch_frontend_http_response_rules_{frontend_name}",
                    get_all_http_response_rule_frontend,
                    parent_name=frontend_name,
                ),
            ),
            (
                "frontend_backend_switching_rules",
                _fetch_with_timing(
                    f"fetch_frontend_backend_switching_rules_{frontend_name}",
                    get_all_backend_switching_rule_frontend,
                    parent_name=frontend_name,
                ),
            ),
            (
                "frontend_filters",
                _fetch_with_timing(
                    f"fetch_frontend_filters_{frontend_name}",
                    get_all_filter_frontend,
                    parent_name=frontend_name,
                ),
            ),
            (
                "frontend_log_targets",
                _fetch_with_timing(
                    f"fetch_frontend_log_targets_{frontend_name}",
                    get_all_log_target_frontend,
                    parent_name=frontend_name,
                ),
            ),
        ]

    async def _process_backend_results(
        self, backend_name: str, results: list[Any], nested: dict[str, Any]
    ) -> None:
        """Process results from concurrent backend nested element fetching."""
        nested_keys = [
            "backend_servers",
            "backend_acls",
            "backend_http_request_rules",
            "backend_http_response_rules",
            "backend_filters",
            "backend_log_targets",
        ]

        for i, (nested_key, result) in enumerate(zip(nested_keys, results)):
            if nested_key not in nested:
                nested[nested_key] = {}
            nested[nested_key][backend_name] = result or []

    async def _process_frontend_results(
        self, frontend_name: str, results: list[Any], nested: dict[str, Any]
    ) -> None:
        """Process results from concurrent frontend nested element fetching."""
        nested_keys = [
            "frontend_binds",
            "frontend_acls",
            "frontend_http_request_rules",
            "frontend_http_response_rules",
            "frontend_filters",
            "frontend_log_targets",
        ]

        for i, (nested_key, result) in enumerate(zip(nested_keys, results)):
            if nested_key not in nested:
                nested[nested_key] = {}
            nested[nested_key][frontend_name] = result or []

    async def _fetch_nested_elements(
        self, config_sections: dict[str, Any], metrics: Any
    ) -> dict[str, Any]:
        """Fetch nested elements for configuration sections using concurrent execution.

        This method uses asyncio.gather to fetch nested elements concurrently,
        providing significant performance improvements for large configurations.
        """
        nested: dict[str, Any] = {}

        # Initialize nested element dictionaries
        nested_keys = [
            "backend_servers",
            "backend_acls",
            "backend_http_request_rules",
            "backend_http_response_rules",
            "backend_filters",
            "backend_log_targets",
            "frontend_binds",
            "frontend_acls",
            "frontend_http_request_rules",
            "frontend_http_response_rules",
            "frontend_backend_switching_rules",
            "frontend_filters",
            "frontend_log_targets",
        ]
        for key in nested_keys:
            nested[key] = {}

        # Concurrent backend processing
        if config_sections.get("backends"):
            backend_tasks = []
            backend_names = []

            for backend in config_sections["backends"]:
                backend_name = backend.name
                backend_names.append(backend_name)

                # Create concurrent tasks for this backend
                tasks = self._create_backend_tasks(backend_name, metrics)
                # Extract just the tasks (second element of each tuple)
                task_coroutines = [task for _, task in tasks]
                backend_tasks.append(
                    asyncio.gather(*task_coroutines, return_exceptions=True)
                )

            if backend_tasks:
                try:
                    # Execute all backend tasks concurrently
                    all_backend_results = await asyncio.gather(
                        *backend_tasks, return_exceptions=True
                    )

                    # Process results for each backend
                    for i, (backend_name, results) in enumerate(
                        zip(backend_names, all_backend_results)
                    ):
                        if isinstance(results, Exception):
                            _log_fetch_error(
                                f"backend {backend_name} nested elements", "", results
                            )
                            # Initialize with empty lists for failed backend
                            for key in [
                                "backend_servers",
                                "backend_acls",
                                "backend_http_request_rules",
                                "backend_http_response_rules",
                                "backend_filters",
                                "backend_log_targets",
                            ]:
                                nested[key][backend_name] = []
                        else:
                            await self._process_backend_results(
                                backend_name, results, nested
                            )

                except Exception as e:
                    _log_fetch_error("backend concurrent processing", "", e)
                    # Initialize all backends with empty lists on total failure
                    for backend in config_sections["backends"]:
                        backend_name = backend.name
                        for key in [
                            "backend_servers",
                            "backend_acls",
                            "backend_http_request_rules",
                            "backend_http_response_rules",
                            "backend_filters",
                            "backend_log_targets",
                        ]:
                            nested[key][backend_name] = []

        # Concurrent frontend processing
        if config_sections.get("frontends"):
            frontend_tasks = []
            frontend_names = []

            for frontend in config_sections["frontends"]:
                frontend_name = frontend.name
                frontend_names.append(frontend_name)

                # Create concurrent tasks for this frontend
                tasks = self._create_frontend_tasks(frontend_name, metrics)
                # Extract just the tasks (second element of each tuple)
                task_coroutines = [task for _, task in tasks]
                frontend_tasks.append(
                    asyncio.gather(*task_coroutines, return_exceptions=True)
                )

            if frontend_tasks:
                try:
                    # Execute all frontend tasks concurrently
                    all_frontend_results = await asyncio.gather(
                        *frontend_tasks, return_exceptions=True
                    )

                    # Process results for each frontend
                    for i, (frontend_name, results) in enumerate(
                        zip(frontend_names, all_frontend_results)
                    ):
                        if isinstance(results, Exception):
                            _log_fetch_error(
                                f"frontend {frontend_name} nested elements", "", results
                            )
                            # Initialize with empty lists for failed frontend
                            for key in [
                                "frontend_binds",
                                "frontend_acls",
                                "frontend_http_request_rules",
                                "frontend_http_response_rules",
                                "frontend_filters",
                                "frontend_log_targets",
                            ]:
                                nested[key][frontend_name] = []
                        else:
                            await self._process_frontend_results(
                                frontend_name, results, nested
                            )

                except Exception as e:
                    _log_fetch_error("frontend concurrent processing", "", e)
                    # Initialize all frontends with empty lists on total failure
                    for frontend in config_sections["frontends"]:
                        frontend_name = frontend.name
                        for key in [
                            "frontend_binds",
                            "frontend_acls",
                            "frontend_http_request_rules",
                            "frontend_http_response_rules",
                            "frontend_filters",
                            "frontend_log_targets",
                        ]:
                            nested[key][frontend_name] = []

        # Fetch global log targets (single call, no concurrency needed)
        try:

            async def _fetch_global_logs():
                with metrics.time_dataplane_api_operation("fetch_global_log_targets"):
                    result: APIResponse = await get_all_log_target_global(
                        endpoint=self.endpoint
                    )
                    return result.content or []

            nested["global_log_targets"] = await _fetch_global_logs()
        except Exception as e:
            _log_fetch_error("global log targets", "", e)
            nested["global_log_targets"] = []

        # Fetch peer log targets
        nested["peer_log_targets"] = {}
        if config_sections.get("peers"):
            for peer_section in config_sections["peers"]:
                peer_name = peer_section.name
                try:

                    async def _fetch_peer_logs(name):
                        with metrics.time_dataplane_api_operation(
                            f"fetch_peer_log_targets_{name}"
                        ):
                            result: APIResponse = await get_all_log_target_peer(
                                parent_name=name, endpoint=self.endpoint
                            )
                            return result.content or []

                    nested["peer_log_targets"][peer_name] = await _fetch_peer_logs(
                        peer_name
                    )
                except Exception as e:
                    _log_fetch_error(f"peer {peer_name} log targets", "", e)
                    nested["peer_log_targets"][peer_name] = []

        # Fetch log_forward log targets
        nested["log_forward_log_targets"] = {}
        if config_sections.get("log_forwards"):
            for log_forward_section in config_sections["log_forwards"]:
                log_forward_name = log_forward_section.name
                try:

                    async def _fetch_log_forward_logs(name):
                        with metrics.time_dataplane_api_operation(
                            f"fetch_log_forward_log_targets_{name}"
                        ):
                            result: APIResponse = await get_all_log_target_log_forward(
                                parent_name=name, endpoint=self.endpoint
                            )
                            return result.content or []

                    nested["log_forward_log_targets"][
                        log_forward_name
                    ] = await _fetch_log_forward_logs(log_forward_name)
                except Exception as e:
                    _log_fetch_error(
                        f"log_forward {log_forward_name} log targets", "", e
                    )
                    nested["log_forward_log_targets"][log_forward_name] = []

        return nested

    def _build_configuration_result(
        self,
        config_sections: dict[str, Any],
        nested_elements: dict[str, Any],
        metrics: Any,
    ) -> dict[str, Any]:
        """Build final configuration result combining sections and nested elements."""
        metrics.record_dataplane_api_request("fetch_structured", "success")

        # Combine all sections and nested elements
        result = {**config_sections, **nested_elements}

        # Log configuration summary
        section_counts = {
            section: len(items) if isinstance(items, list) else 1
            for section, items in config_sections.items()
            if items
        }
        logger.debug(f"Fetched configuration sections: {section_counts}")

        return result

    async def apply_config_change(
        self, change: ConfigChange, version: int, transaction_id: str | None = None
    ) -> ConfigChangeResult:
        """Apply a single configuration change via structured API.

        Args:
            change: The configuration change to apply
            version: Configuration version for the transaction
            transaction_id: Optional transaction ID to use for atomic changes

        Returns:
            ConfigChangeResult containing operation status and reload information

        Raises:
            DataplaneAPIError: If the change cannot be applied
        """

        if change.element_type:
            reload_info = await self._apply_nested_element_change(
                change, version, transaction_id
            )
        else:
            reload_info = await self._apply_section_change(
                change, version, transaction_id
            )

        return ConfigChangeResult(
            change_applied=True,
            reload_info=reload_info,
        )

    async def _apply_section_change(
        self,
        change: ConfigChange,
        version: int,
        transaction_id: str | None = None,
    ) -> ReloadInfo:
        """Apply a section-level configuration change.

        Returns:
            ReloadInfo indicating if a reload was triggered
        """
        # Configuration for each section type
        section_handlers: dict[ConfigSectionType, SectionHandlerConfig] = {
            ConfigSectionType.BACKEND: {
                "create": create_backend,
                "update": replace_backend,
                "delete": delete_backend,
                "id_field": "name",
            },
            ConfigSectionType.FRONTEND: {
                "create": create_frontend,
                "update": replace_frontend,
                "delete": delete_frontend,
                "id_field": "name",
            },
            ConfigSectionType.GLOBAL: {
                "create": None,  # Global cannot be created
                "update": replace_global,
                "delete": None,  # Global cannot be deleted
                "id_field": None,
            },
            ConfigSectionType.DEFAULTS: {
                "create": create_defaults_section,
                "update": replace_defaults_section,
                "delete": delete_defaults_section,
                "id_field": "name",
            },
            ConfigSectionType.USERLIST: {
                "create": create_userlist,
                "update": None,  # No replace API - will use delete+create pattern
                "delete": delete_userlist,
                "id_field": "name",
            },
            ConfigSectionType.CACHE: {
                "create": create_cache,
                "update": replace_cache,
                "delete": delete_cache,
                "id_field": "name",
            },
            ConfigSectionType.MAILERS: {
                "create": create_mailers_section,
                "update": edit_mailers_section,
                "delete": delete_mailers_section,
                "id_field": "name",
            },
            ConfigSectionType.RESOLVER: {
                "create": create_resolver,
                "update": replace_resolver,
                "delete": delete_resolver,
                "id_field": "name",
            },
            ConfigSectionType.PEER: {
                "create": create_peer,
                "update": None,  # No replace API - will use delete+create pattern
                "delete": delete_peer,
                "id_field": "name",
            },
            ConfigSectionType.FCGI_APP: {
                "create": create_fcgi_app,
                "update": replace_fcgi_app,
                "delete": delete_fcgi_app,
                "id_field": "name",
            },
            ConfigSectionType.HTTP_ERRORS: {
                "create": create_http_errors_section,
                "update": replace_http_errors_section,
                "delete": delete_http_errors_section,
                "id_field": "name",
            },
            ConfigSectionType.RING: {
                "create": create_ring,
                "update": replace_ring,
                "delete": delete_ring,
                "id_field": "name",
            },
            ConfigSectionType.LOG_FORWARD: {
                "create": create_log_forward,
                "update": replace_log_forward,
                "delete": delete_log_forward,
                "id_field": "name",
            },
            ConfigSectionType.PROGRAM: {
                "create": create_program,
                "update": replace_program,
                "delete": delete_program,
                "id_field": "name",
            },
        }

        handler_config = section_handlers.get(change.section_type)
        if not handler_config:
            raise DataplaneAPIError(
                f"Unsupported section type: {change.section_type}",
                endpoint=self.endpoint,
                operation="apply_section_change",
            )

        # Use transaction_id if provided, otherwise use version
        if transaction_id:
            base_params = {"endpoint": self.endpoint, "transaction_id": transaction_id}
        else:
            base_params = {"endpoint": self.endpoint, "version": version}

        if change.change_type == ConfigChangeType.CREATE:
            if not handler_config["create"]:
                raise DataplaneAPIError(
                    f"CREATE not supported for {change.section_type}",
                    endpoint=self.endpoint,
                    operation="apply_section_change",
                )
            reload_info = await self._call_api_with_reload_info(
                handler_config["create"], body=change.new_config, **base_params
            )
            return reload_info

        elif change.change_type == ConfigChangeType.UPDATE:
            if not handler_config["update"]:
                # For sections without replace API (USERLIST, PEER), use delete+create pattern
                if handler_config["delete"] and handler_config["create"]:
                    # First try to delete existing section (ignore errors if it doesn't exist)
                    reload_infos = []
                    try:
                        delete_params = {**base_params}
                        if handler_config["id_field"] == "name":
                            delete_reload_info = await self._call_api_with_reload_info(
                                handler_config["delete"],
                                change.section_name,
                                **delete_params,
                            )
                        elif handler_config["id_field"]:
                            delete_params[handler_config["id_field"]] = (
                                change.section_name
                            )
                            delete_reload_info = await self._call_api_with_reload_info(
                                handler_config["delete"], **delete_params
                            )
                        else:
                            delete_reload_info = await self._call_api_with_reload_info(
                                handler_config["delete"], **delete_params
                            )
                        reload_infos.append(delete_reload_info)
                    except DataplaneAPIError as e:
                        # Ignore delete errors - section might not exist
                        logger.debug(
                            f"Delete section {change.section_name} failed (ignoring): {e}"
                        )

                    # Then create the new section
                    create_reload_info = await self._call_api_with_reload_info(
                        handler_config["create"], body=change.new_config, **base_params
                    )
                    reload_infos.append(create_reload_info)
                    return ReloadInfo.combine(*reload_infos)
                else:
                    raise DataplaneAPIError(
                        f"UPDATE not supported for {change.section_type}",
                        endpoint=self.endpoint,
                        operation="apply_section_change",
                    )
            else:
                params = {**base_params, "body": change.new_config}
                if handler_config["id_field"] == "name":
                    # For APIs that expect name as keyword argument to avoid @api_function conflicts
                    reload_info = await self._call_api_with_reload_info(
                        handler_config["update"], name=change.section_name, **params
                    )
                elif handler_config["id_field"]:
                    # For other APIs that expect the id as keyword argument
                    params[handler_config["id_field"]] = change.section_name
                    reload_info = await self._call_api_with_reload_info(
                        handler_config["update"], **params
                    )
                else:
                    reload_info = await self._call_api_with_reload_info(
                        handler_config["update"], **params
                    )
                return reload_info

        elif change.change_type == ConfigChangeType.DELETE:
            if not handler_config["delete"]:
                raise DataplaneAPIError(
                    f"DELETE not supported for {change.section_type}",
                    endpoint=self.endpoint,
                    operation="apply_section_change",
                )
            params = {**base_params}
            if handler_config["id_field"] == "name":
                # For APIs that expect name as keyword argument to avoid @api_function conflicts
                reload_info = await self._call_api_with_reload_info(
                    handler_config["delete"], name=change.section_name, **params
                )
            elif handler_config["id_field"]:
                # For other APIs that expect the id as keyword argument
                params[handler_config["id_field"]] = change.section_name
                reload_info = await self._call_api_with_reload_info(
                    handler_config["delete"], **params
                )
            else:
                reload_info = await self._call_api_with_reload_info(
                    handler_config["delete"], **params
                )
            return reload_info

        # This should never be reached, but add a fallback
        return ReloadInfo()

    async def _apply_nested_element_change(
        self,
        change: ConfigChange,
        version: int,
        transaction_id: str | None = None,
    ) -> ReloadInfo:
        """Apply a nested element configuration change.

        Returns:
            ReloadInfo indicating if a reload was triggered
        """
        # Configuration for nested elements
        element_handlers: dict[
            tuple[ConfigSectionType, ConfigElementType], ElementHandlerConfig
        ] = {
            (ConfigSectionType.BACKEND, ConfigElementType.SERVER): {
                "create": create_server_backend,
                "update": replace_server_backend,
                "delete": delete_server_backend,
                "parent_field": "parent_name",
                "id_field": "name",
            },
            (ConfigSectionType.BACKEND, ConfigElementType.ACL): {
                "create": create_acl_backend,
                "update": replace_acl_backend,
                "delete": delete_acl_backend,
                "parent_field": "parent_name",
                "id_field": "index",
            },
            (ConfigSectionType.BACKEND, ConfigElementType.HTTP_REQUEST_RULE): {
                "create": create_http_request_rule_backend,
                "update": replace_http_request_rule_backend,
                "delete": delete_http_request_rule_backend,
                "parent_field": "parent_name",
                "id_field": "index",
            },
            (ConfigSectionType.BACKEND, ConfigElementType.HTTP_RESPONSE_RULE): {
                "create": create_http_response_rule_backend,
                "update": replace_http_response_rule_backend,
                "delete": delete_http_response_rule_backend,
                "parent_field": "parent_name",
                "id_field": "index",
            },
            (ConfigSectionType.BACKEND, ConfigElementType.FILTER): {
                "create": create_filter_backend,
                "update": replace_filter_backend,
                "delete": delete_filter_backend,
                "parent_field": "parent_name",
                "id_field": "index",
            },
            (ConfigSectionType.BACKEND, ConfigElementType.LOG_TARGET): {
                "create": create_log_target_backend,
                "update": replace_log_target_backend,
                "delete": delete_log_target_backend,
                "parent_field": "parent_name",
                "id_field": "index",
            },
            (ConfigSectionType.FRONTEND, ConfigElementType.BIND): {
                "create": create_bind_frontend,
                "update": replace_bind_frontend,
                "delete": delete_bind_frontend,
                "parent_field": "parent_name",
                "id_field": "name",
            },
            (ConfigSectionType.FRONTEND, ConfigElementType.ACL): {
                "create": create_acl_frontend,
                "update": replace_acl_frontend,
                "delete": delete_acl_frontend,
                "parent_field": "parent_name",
                "id_field": "index",
            },
            (ConfigSectionType.FRONTEND, ConfigElementType.HTTP_REQUEST_RULE): {
                "create": create_http_request_rule_frontend,
                "update": replace_http_request_rule_frontend,
                "delete": delete_http_request_rule_frontend,
                "parent_field": "parent_name",
                "id_field": "index",
            },
            (ConfigSectionType.FRONTEND, ConfigElementType.HTTP_RESPONSE_RULE): {
                "create": create_http_response_rule_frontend,
                "update": replace_http_response_rule_frontend,
                "delete": delete_http_response_rule_frontend,
                "parent_field": "parent_name",
                "id_field": "index",
            },
            (ConfigSectionType.FRONTEND, ConfigElementType.FILTER): {
                "create": create_filter_frontend,
                "update": replace_filter_frontend,
                "delete": delete_filter_frontend,
                "parent_field": "parent_name",
                "id_field": "index",
            },
            (ConfigSectionType.FRONTEND, ConfigElementType.LOG_TARGET): {
                "create": create_log_target_frontend,
                "update": replace_log_target_frontend,
                "delete": delete_log_target_frontend,
                "parent_field": "parent_name",
                "id_field": "index",
            },
            (ConfigSectionType.GLOBAL, ConfigElementType.LOG_TARGET): {
                "create": create_log_target_global,
                "update": replace_log_target_global,
                "delete": delete_log_target_global,
                "parent_field": None,  # Global log targets don't have a parent
                "id_field": "index",
            },
            (ConfigSectionType.PEER, ConfigElementType.LOG_TARGET): {
                "create": create_log_target_peer,
                "update": replace_log_target_peer,
                "delete": delete_log_target_peer,
                "parent_field": "parent_name",
                "id_field": "index",
            },
            (ConfigSectionType.LOG_FORWARD, ConfigElementType.LOG_TARGET): {
                "create": create_log_target_log_forward,
                "update": replace_log_target_log_forward,
                "delete": delete_log_target_log_forward,
                "parent_field": "parent_name",
                "id_field": "index",
            },
        }

        # element_type must be non-None when this method is called
        if change.element_type is None:
            raise ValueError("element_type must be provided for nested element changes")
        key = (change.section_type, change.element_type)
        handler_config = element_handlers.get(key)
        if not handler_config:
            raise DataplaneAPIError(
                f"Unsupported element type: {change.element_type} for {change.section_type}",
                endpoint=self.endpoint,
                operation="apply_nested_element_change",
            )

        # Use transaction_id if provided, otherwise use version
        if transaction_id:
            base_params = {
                "endpoint": self.endpoint,
                "transaction_id": transaction_id,
            }
            # Add parent_field only if it's not None (global sections don't have parents)
            if handler_config["parent_field"] is not None:
                base_params[handler_config["parent_field"]] = change.section_name
        else:
            base_params = {
                "endpoint": self.endpoint,
                "version": version,
            }
            # Add parent_field only if it's not None (global sections don't have parents)
            if handler_config["parent_field"] is not None:
                base_params[handler_config["parent_field"]] = change.section_name

        if change.change_type == ConfigChangeType.CREATE:
            if handler_config["id_field"] == "index":
                element_index = (
                    change.element_index
                    if change.element_index is not None
                    else change.element_id
                )
                if element_index is None:
                    raise DataplaneAPIError(
                        "CREATE operation for index-based element requires element_index or element_id",
                        endpoint=self.endpoint,
                        operation="apply_nested_element_change",
                    )

                # Handle global elements (no parent) vs section elements (with parent)
                if handler_config["parent_field"] is None:
                    # Global elements (like global log targets) - no parent_name parameter
                    if transaction_id:
                        await handler_config["create"](
                            index=element_index,
                            endpoint=self.endpoint,
                            body=change.new_config,
                            transaction_id=transaction_id,
                        )
                    else:
                        await handler_config["create"](
                            index=element_index,
                            endpoint=self.endpoint,
                            body=change.new_config,
                            version=version,
                        )
                else:
                    # Section elements (like backend/frontend log targets) - with parent_name
                    parent_name = change.section_name
                    if transaction_id:
                        await handler_config["create"](
                            parent_name=parent_name,
                            index=element_index,
                            endpoint=self.endpoint,
                            body=change.new_config,
                            transaction_id=transaction_id,
                        )
                    else:
                        await handler_config["create"](
                            parent_name=parent_name,
                            index=element_index,
                            endpoint=self.endpoint,
                            body=change.new_config,
                            version=version,
                        )
            else:
                # For other APIs that expect all parameters as keyword arguments
                await handler_config["create"](body=change.new_config, **base_params)

        elif change.change_type == ConfigChangeType.UPDATE:
            params = {**base_params, "body": change.new_config}
            element_id = change.element_id or change.element_index
            if element_id is not None and handler_config["id_field"] == "index":
                # Handle global elements (no parent) vs section elements (with parent)
                if handler_config["parent_field"] is None:
                    # Global elements (like global log targets) - no parent_name parameter
                    await handler_config["update"](
                        index=element_id,
                        **{
                            k: v
                            for k, v in params.items()
                            if k != handler_config["parent_field"]
                        },
                    )
                else:
                    # Section elements (like backend/frontend log targets) - with parent_name
                    parent_name = change.section_name
                    await handler_config["update"](
                        parent_name=parent_name,
                        index=element_id,
                        **{
                            k: v
                            for k, v in params.items()
                            if k != handler_config["parent_field"]
                        },
                    )
            elif element_id is not None:
                # For other APIs that expect the id as keyword argument
                params[handler_config["id_field"]] = element_id
                await handler_config["update"](**params)
            else:
                await handler_config["update"](**params)

        elif change.change_type == ConfigChangeType.DELETE:
            params = {**base_params}
            element_id = change.element_id or change.element_index
            if element_id is not None and handler_config["id_field"] == "index":
                # Handle global elements (no parent) vs section elements (with parent)
                if handler_config["parent_field"] is None:
                    # Global elements (like global log targets) - no parent_name parameter
                    await handler_config["delete"](
                        index=element_id,
                        **{
                            k: v
                            for k, v in params.items()
                            if k != handler_config["parent_field"]
                        },
                    )
                else:
                    # Section elements (like backend/frontend log targets) - with parent_name
                    parent_name = change.section_name
                    await handler_config["delete"](
                        parent_name=parent_name,
                        index=element_id,
                        **{
                            k: v
                            for k, v in params.items()
                            if k != handler_config["parent_field"]
                        },
                    )
            elif element_id is not None:
                # For other APIs that expect the id as keyword argument
                params[handler_config["id_field"]] = element_id
                await handler_config["delete"](**params)
            else:
                await handler_config["delete"](**params)

        # Nested element operations within transactions typically don't trigger reloads
        return ReloadInfo()
