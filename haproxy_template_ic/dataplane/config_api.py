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

import logging
from collections.abc import Callable
from typing import Any, Dict, Optional, Tuple, TYPE_CHECKING
from typing_extensions import TypedDict

from haproxy_dataplane_v3 import AuthenticatedClient

if TYPE_CHECKING:
    from .endpoint import DataplaneEndpoint

# Configuration APIs
from haproxy_dataplane_v3.api.acl import (
    create_acl_backend,
    create_acl_frontend,
    delete_acl_backend,
    delete_acl_frontend,
    get_all_acl_backend,
    get_all_acl_frontend,
    replace_acl_backend,
    replace_acl_frontend,
)
from haproxy_dataplane_v3.api.backend import (
    create_backend,
    delete_backend,
    get_backends,
    replace_backend,
)
from haproxy_dataplane_v3.api.bind import (
    create_bind_frontend,
    delete_bind_frontend,
    get_all_bind_frontend,
    replace_bind_frontend,
)
from haproxy_dataplane_v3.api.cache import get_caches
from haproxy_dataplane_v3.api.defaults import (
    get_defaults_sections,
    replace_defaults_section,
)
from haproxy_dataplane_v3.api.fcgi_app import get_fcgi_apps
from haproxy_dataplane_v3.api.http_errors import get_http_errors_sections
from haproxy_dataplane_v3.api.filter_ import (
    create_filter_backend,
    create_filter_frontend,
    delete_filter_backend,
    delete_filter_frontend,
    get_all_filter_backend,
    get_all_filter_frontend,
    replace_filter_backend,
    replace_filter_frontend,
)
from haproxy_dataplane_v3.api.frontend import (
    create_frontend,
    delete_frontend,
    get_frontends,
    replace_frontend,
)
from haproxy_dataplane_v3.api.global_ import get_global, replace_global
from haproxy_dataplane_v3.api.http_request_rule import (
    create_http_request_rule_backend,
    create_http_request_rule_frontend,
    delete_http_request_rule_backend,
    delete_http_request_rule_frontend,
    get_all_http_request_rule_backend,
    get_all_http_request_rule_frontend,
    replace_http_request_rule_backend,
    replace_http_request_rule_frontend,
)
from haproxy_dataplane_v3.api.http_response_rule import (
    create_http_response_rule_backend,
    create_http_response_rule_frontend,
    delete_http_response_rule_backend,
    delete_http_response_rule_frontend,
    get_all_http_response_rule_backend,
    get_all_http_response_rule_frontend,
    replace_http_response_rule_backend,
    replace_http_response_rule_frontend,
)
from haproxy_dataplane_v3.api.log_forward import get_log_forwards
from haproxy_dataplane_v3.api.log_target import (
    create_log_target_backend,
    create_log_target_frontend,
    delete_log_target_backend,
    delete_log_target_frontend,
    get_all_log_target_backend,
    get_all_log_target_frontend,
    get_all_log_target_global,
    replace_log_target_backend,
    replace_log_target_frontend,
)
from haproxy_dataplane_v3.api.mailers import get_mailers_sections
from haproxy_dataplane_v3.api.peer import get_peer_sections
from haproxy_dataplane_v3.api.process_manager import get_programs
from haproxy_dataplane_v3.api.resolver import get_resolvers
from haproxy_dataplane_v3.api.ring import get_rings
from haproxy_dataplane_v3.api.server import (
    create_server_backend,
    delete_server_backend,
    get_all_server_backend,
    replace_server_backend,
)
from haproxy_dataplane_v3.api.userlist import get_userlists

from haproxy_template_ic.metrics import get_metrics_collector
from .types import (
    ConfigChange,
    ConfigChangeType,
    ConfigElementType,
    ConfigSectionType,
    DataplaneAPIError,
)
from .utils import fetch_with_metrics, _log_fetch_error, check_dataplane_response


# TypedDict classes for handler configurations
class SectionHandlerConfig(TypedDict, total=False):
    """Type definition for section handler configuration."""

    create: Optional[Callable[..., Any]]
    update: Optional[Callable[..., Any]]
    delete: Optional[Callable[..., Any]]
    id_field: Optional[str]


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
        get_client: Callable[[], AuthenticatedClient],
        endpoint: "DataplaneEndpoint",
    ):
        """Initialize configuration API.

        Args:
            get_client: Factory function that returns an authenticated client
            endpoint: Dataplane endpoint for error context
        """
        self._get_client = get_client
        self.endpoint = endpoint

    async def fetch_structured_configuration(self) -> Dict[str, Any]:
        """Fetch complete structured configuration components from HAProxy instance.

        Returns:
            Dictionary containing all configuration sections and their nested elements

        Raises:
            DataplaneAPIError: If fetching configuration fails
        """
        metrics = get_metrics_collector()

        with metrics.time_dataplane_api_operation("fetch_structured"):
            client = self._get_client()

            try:
                # Fetch all top-level configuration sections
                config_sections = await self._fetch_top_level_sections(client, metrics)

                # Fetch nested elements for sections that support them
                nested_elements = await self._fetch_nested_elements(
                    client, config_sections
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

    async def _fetch_top_level_sections(
        self, client: Any, metrics: Any
    ) -> Dict[str, Any]:
        """Fetch all top-level configuration sections."""
        return {
            "backends": await fetch_with_metrics(
                "fetch_backends",
                get_backends.asyncio,
                client,
                metrics,
                [],
                self.endpoint,
            ),
            "frontends": await fetch_with_metrics(
                "fetch_frontends",
                get_frontends.asyncio,
                client,
                metrics,
                [],
                self.endpoint,
            ),
            "defaults": await fetch_with_metrics(
                "fetch_defaults",
                get_defaults_sections.asyncio,
                client,
                metrics,
                [],
                self.endpoint,
            ),
            "global": await fetch_with_metrics(
                "fetch_global", get_global.asyncio, client, metrics, None, self.endpoint
            ),
            "userlists": await fetch_with_metrics(
                "fetch_userlists",
                get_userlists.asyncio,
                client,
                metrics,
                [],
                self.endpoint,
            ),
            "caches": await fetch_with_metrics(
                "fetch_caches", get_caches.asyncio, client, metrics, [], self.endpoint
            ),
            "mailers": await fetch_with_metrics(
                "fetch_mailers",
                get_mailers_sections.asyncio,
                client,
                metrics,
                [],
                self.endpoint,
            ),
            "resolvers": await fetch_with_metrics(
                "fetch_resolvers",
                get_resolvers.asyncio,
                client,
                metrics,
                [],
                self.endpoint,
            ),
            "peers": await fetch_with_metrics(
                "fetch_peers",
                get_peer_sections.asyncio,
                client,
                metrics,
                [],
                self.endpoint,
            ),
            "fcgi_apps": await fetch_with_metrics(
                "fetch_fcgi_apps",
                get_fcgi_apps.asyncio,
                client,
                metrics,
                [],
                self.endpoint,
            ),
            "http_errors": await fetch_with_metrics(
                "fetch_http_errors",
                get_http_errors_sections.asyncio,
                client,
                metrics,
                [],
                self.endpoint,
            ),
            "rings": await fetch_with_metrics(
                "fetch_rings", get_rings.asyncio, client, metrics, [], self.endpoint
            ),
            "log_forwards": await fetch_with_metrics(
                "fetch_log_forwards",
                get_log_forwards.asyncio,
                client,
                metrics,
                [],
                self.endpoint,
            ),
            "programs": await fetch_with_metrics(
                "fetch_programs",
                get_programs.asyncio,
                client,
                metrics,
                [],
                self.endpoint,
            ),
        }

    async def _fetch_nested_elements(
        self, client: Any, config_sections: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Fetch nested elements for configuration sections."""
        nested: Dict[str, Any] = {}

        # Fetch nested elements for backends
        if config_sections.get("backends"):
            nested["backend_servers"] = {}
            nested["backend_acls"] = {}
            nested["backend_http_request_rules"] = {}
            nested["backend_http_response_rules"] = {}
            nested["backend_filters"] = {}
            nested["backend_log_targets"] = {}

            for backend in config_sections["backends"]:
                backend_name = backend.name
                try:
                    nested["backend_servers"][backend_name] = (
                        check_dataplane_response(
                            await get_all_server_backend.asyncio(
                                backend_name, client=client
                            ),
                            f"fetch_backend_servers_{backend_name}",
                            self.endpoint,
                        )
                        or []
                    )

                    nested["backend_acls"][backend_name] = (
                        check_dataplane_response(
                            await get_all_acl_backend.asyncio(
                                backend_name, client=client
                            ),
                            f"fetch_backend_acls_{backend_name}",
                            self.endpoint,
                        )
                        or []
                    )

                    nested["backend_http_request_rules"][backend_name] = (
                        check_dataplane_response(
                            await get_all_http_request_rule_backend.asyncio(
                                backend_name, client=client
                            ),
                            f"fetch_backend_http_request_rules_{backend_name}",
                            self.endpoint,
                        )
                        or []
                    )

                    nested["backend_http_response_rules"][backend_name] = (
                        check_dataplane_response(
                            await get_all_http_response_rule_backend.asyncio(
                                backend_name, client=client
                            ),
                            f"fetch_backend_http_response_rules_{backend_name}",
                            self.endpoint,
                        )
                        or []
                    )

                    nested["backend_filters"][backend_name] = (
                        check_dataplane_response(
                            await get_all_filter_backend.asyncio(
                                backend_name, client=client
                            ),
                            f"fetch_backend_filters_{backend_name}",
                            self.endpoint,
                        )
                        or []
                    )

                    nested["backend_log_targets"][backend_name] = (
                        check_dataplane_response(
                            await get_all_log_target_backend.asyncio(
                                backend_name, client=client
                            ),
                            f"fetch_backend_log_targets_{backend_name}",
                            self.endpoint,
                        )
                        or []
                    )
                except Exception as e:
                    _log_fetch_error(f"backend {backend_name} nested elements", "", e)

        # Fetch nested elements for frontends
        if config_sections.get("frontends"):
            nested["frontend_binds"] = {}
            nested["frontend_acls"] = {}
            nested["frontend_http_request_rules"] = {}
            nested["frontend_http_response_rules"] = {}
            nested["frontend_filters"] = {}
            nested["frontend_log_targets"] = {}

            for frontend in config_sections["frontends"]:
                frontend_name = frontend.name
                try:
                    nested["frontend_binds"][frontend_name] = (
                        check_dataplane_response(
                            await get_all_bind_frontend.asyncio(
                                frontend_name, client=client
                            ),
                            f"fetch_frontend_binds_{frontend_name}",
                            self.endpoint,
                        )
                        or []
                    )

                    nested["frontend_acls"][frontend_name] = (
                        check_dataplane_response(
                            await get_all_acl_frontend.asyncio(
                                frontend_name, client=client
                            ),
                            f"fetch_frontend_acls_{frontend_name}",
                            self.endpoint,
                        )
                        or []
                    )

                    nested["frontend_http_request_rules"][frontend_name] = (
                        check_dataplane_response(
                            await get_all_http_request_rule_frontend.asyncio(
                                frontend_name, client=client
                            ),
                            f"fetch_frontend_http_request_rules_{frontend_name}",
                            self.endpoint,
                        )
                        or []
                    )

                    nested["frontend_http_response_rules"][frontend_name] = (
                        check_dataplane_response(
                            await get_all_http_response_rule_frontend.asyncio(
                                frontend_name, client=client
                            ),
                            f"fetch_frontend_http_response_rules_{frontend_name}",
                            self.endpoint,
                        )
                        or []
                    )

                    nested["frontend_filters"][frontend_name] = (
                        check_dataplane_response(
                            await get_all_filter_frontend.asyncio(
                                frontend_name, client=client
                            ),
                            f"fetch_frontend_filters_{frontend_name}",
                            self.endpoint,
                        )
                        or []
                    )

                    nested["frontend_log_targets"][frontend_name] = (
                        check_dataplane_response(
                            await get_all_log_target_frontend.asyncio(
                                frontend_name, client=client
                            ),
                            f"fetch_frontend_log_targets_{frontend_name}",
                            self.endpoint,
                        )
                        or []
                    )
                except Exception as e:
                    _log_fetch_error(f"frontend {frontend_name} nested elements", "", e)

        # Fetch global log targets
        try:
            nested["global_log_targets"] = (
                check_dataplane_response(
                    await get_all_log_target_global.asyncio(client=client),
                    "fetch_global_log_targets",
                    self.endpoint,
                )
                or []
            )
        except Exception as e:
            _log_fetch_error("global log targets", "", e)

        return nested

    def _build_configuration_result(
        self,
        config_sections: Dict[str, Any],
        nested_elements: Dict[str, Any],
        metrics: Any,
    ) -> Dict[str, Any]:
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
        self, change: ConfigChange, version: int, transaction_id: Optional[str] = None
    ) -> None:
        """Apply a single configuration change via structured API.

        Args:
            change: The configuration change to apply
            version: Configuration version for the transaction
            transaction_id: Optional transaction ID to use for atomic changes

        Raises:
            DataplaneAPIError: If the change cannot be applied
        """
        client = self._get_client()

        if change.element_type:
            await self._apply_nested_element_change(
                client, change, version, transaction_id
            )
        else:
            await self._apply_section_change(client, change, version, transaction_id)

    async def _apply_section_change(
        self,
        client: Any,
        change: ConfigChange,
        version: int,
        transaction_id: Optional[str] = None,
    ) -> None:
        """Apply a section-level configuration change."""
        # Configuration for each section type
        section_handlers: Dict[ConfigSectionType, SectionHandlerConfig] = {
            ConfigSectionType.BACKEND: {
                "create": create_backend.asyncio,
                "update": replace_backend.asyncio,
                "delete": delete_backend.asyncio,
                "id_field": "name",
            },
            ConfigSectionType.FRONTEND: {
                "create": create_frontend.asyncio,
                "update": replace_frontend.asyncio,
                "delete": delete_frontend.asyncio,
                "id_field": "name",
            },
            ConfigSectionType.GLOBAL: {
                "create": None,  # Global cannot be created
                "update": replace_global.asyncio,
                "delete": None,  # Global cannot be deleted
                "id_field": None,
            },
            ConfigSectionType.DEFAULTS: {
                "create": None,  # Use replace to create/update defaults
                "update": replace_defaults_section.asyncio,
                "delete": None,  # Defaults cannot be deleted
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
            base_params = {"client": client, "transaction_id": transaction_id}
        else:
            base_params = {"client": client, "version": version}

        if change.change_type == ConfigChangeType.CREATE:
            if not handler_config["create"]:
                raise DataplaneAPIError(
                    f"CREATE not supported for {change.section_type}",
                    endpoint=self.endpoint,
                    operation="apply_section_change",
                )
            await handler_config["create"](body=change.new_config, **base_params)

        elif change.change_type == ConfigChangeType.UPDATE:
            if not handler_config["update"]:
                raise DataplaneAPIError(
                    f"UPDATE not supported for {change.section_type}",
                    endpoint=self.endpoint,
                    operation="apply_section_change",
                )
            params = {**base_params, "body": change.new_config}
            if handler_config["id_field"] == "name":
                # For APIs that expect name as positional argument (backends, frontends, defaults)
                await handler_config["update"](change.section_name, **params)
            elif handler_config["id_field"]:
                # For other APIs that expect the id as keyword argument
                params[handler_config["id_field"]] = change.section_name
                await handler_config["update"](**params)
            else:
                await handler_config["update"](**params)

        elif change.change_type == ConfigChangeType.DELETE:
            if not handler_config["delete"]:
                raise DataplaneAPIError(
                    f"DELETE not supported for {change.section_type}",
                    endpoint=self.endpoint,
                    operation="apply_section_change",
                )
            params = {**base_params}
            if handler_config["id_field"] == "name":
                # For APIs that expect name as positional argument (backends, frontends, defaults)
                await handler_config["delete"](change.section_name, **params)
            elif handler_config["id_field"]:
                # For other APIs that expect the id as keyword argument
                params[handler_config["id_field"]] = change.section_name
                await handler_config["delete"](**params)
            else:
                await handler_config["delete"](**params)

    async def _apply_nested_element_change(
        self,
        client: Any,
        change: ConfigChange,
        version: int,
        transaction_id: Optional[str] = None,
    ) -> None:
        """Apply a nested element configuration change."""
        # Configuration for nested elements
        element_handlers: Dict[
            Tuple[ConfigSectionType, ConfigElementType], ElementHandlerConfig
        ] = {
            (ConfigSectionType.BACKEND, ConfigElementType.SERVER): {
                "create": create_server_backend.asyncio,
                "update": replace_server_backend.asyncio,
                "delete": delete_server_backend.asyncio,
                "parent_field": "backend",
                "id_field": "name",
            },
            (ConfigSectionType.BACKEND, ConfigElementType.ACL): {
                "create": create_acl_backend.asyncio,
                "update": replace_acl_backend.asyncio,
                "delete": delete_acl_backend.asyncio,
                "parent_field": "backend",
                "id_field": "index",
            },
            (ConfigSectionType.BACKEND, ConfigElementType.HTTP_REQUEST_RULE): {
                "create": create_http_request_rule_backend.asyncio,
                "update": replace_http_request_rule_backend.asyncio,
                "delete": delete_http_request_rule_backend.asyncio,
                "parent_field": "backend",
                "id_field": "index",
            },
            (ConfigSectionType.BACKEND, ConfigElementType.HTTP_RESPONSE_RULE): {
                "create": create_http_response_rule_backend.asyncio,
                "update": replace_http_response_rule_backend.asyncio,
                "delete": delete_http_response_rule_backend.asyncio,
                "parent_field": "backend",
                "id_field": "index",
            },
            (ConfigSectionType.BACKEND, ConfigElementType.FILTER): {
                "create": create_filter_backend.asyncio,
                "update": replace_filter_backend.asyncio,
                "delete": delete_filter_backend.asyncio,
                "parent_field": "backend",
                "id_field": "index",
            },
            (ConfigSectionType.BACKEND, ConfigElementType.LOG_TARGET): {
                "create": create_log_target_backend.asyncio,
                "update": replace_log_target_backend.asyncio,
                "delete": delete_log_target_backend.asyncio,
                "parent_field": "backend",
                "id_field": "index",
            },
            (ConfigSectionType.FRONTEND, ConfigElementType.BIND): {
                "create": create_bind_frontend.asyncio,
                "update": replace_bind_frontend.asyncio,
                "delete": delete_bind_frontend.asyncio,
                "parent_field": "frontend",
                "id_field": "name",
            },
            (ConfigSectionType.FRONTEND, ConfigElementType.ACL): {
                "create": create_acl_frontend.asyncio,
                "update": replace_acl_frontend.asyncio,
                "delete": delete_acl_frontend.asyncio,
                "parent_field": "frontend",
                "id_field": "index",
            },
            (ConfigSectionType.FRONTEND, ConfigElementType.HTTP_REQUEST_RULE): {
                "create": create_http_request_rule_frontend.asyncio,
                "update": replace_http_request_rule_frontend.asyncio,
                "delete": delete_http_request_rule_frontend.asyncio,
                "parent_field": "frontend",
                "id_field": "index",
            },
            (ConfigSectionType.FRONTEND, ConfigElementType.HTTP_RESPONSE_RULE): {
                "create": create_http_response_rule_frontend.asyncio,
                "update": replace_http_response_rule_frontend.asyncio,
                "delete": delete_http_response_rule_frontend.asyncio,
                "parent_field": "frontend",
                "id_field": "index",
            },
            (ConfigSectionType.FRONTEND, ConfigElementType.FILTER): {
                "create": create_filter_frontend.asyncio,
                "update": replace_filter_frontend.asyncio,
                "delete": delete_filter_frontend.asyncio,
                "parent_field": "frontend",
                "id_field": "index",
            },
            (ConfigSectionType.FRONTEND, ConfigElementType.LOG_TARGET): {
                "create": create_log_target_frontend.asyncio,
                "update": replace_log_target_frontend.asyncio,
                "delete": delete_log_target_frontend.asyncio,
                "parent_field": "frontend",
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
                "client": client,
                "transaction_id": transaction_id,
                handler_config["parent_field"]: change.section_name,
            }
        else:
            base_params = {
                "client": client,
                "version": version,
                handler_config["parent_field"]: change.section_name,
            }

        if change.change_type == ConfigChangeType.CREATE:
            if handler_config["id_field"] == "index":
                # For APIs that expect parent_name and index as positional arguments
                parent_name = change.section_name
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
                # Pass parent_name and index as positional, other params as keyword
                if transaction_id:
                    await handler_config["create"](
                        parent_name,
                        element_index,
                        client=client,
                        body=change.new_config,
                        transaction_id=transaction_id,
                    )
                else:
                    await handler_config["create"](
                        parent_name,
                        element_index,
                        client=client,
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
                # For APIs that expect index as positional argument
                parent_name = change.section_name
                await handler_config["update"](
                    parent_name,
                    element_id,
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
                # For APIs that expect index as positional argument
                parent_name = change.section_name
                await handler_config["delete"](
                    parent_name,
                    element_id,
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
