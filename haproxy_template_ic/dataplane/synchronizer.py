"""
HAProxy Configuration Synchronizer.

This module provides the ConfigSynchronizer class for synchronizing HAProxy configurations
across multiple instances with validation-first deployment and structured comparison.
"""

import asyncio
import logging
import time
from typing import Any, Callable, Dict, List, Optional, Tuple

from haproxy_template_ic.metrics import get_metrics_collector
from haproxy_template_ic.models.context import HAProxyConfigContext

from .client import DataplaneClient
from .client_pool import DataplaneClientPool
from .endpoint import DataplaneEndpoint, DataplaneEndpointSet
from .types import (
    ConfigChange,
    ConfigChangeType,
    ConfigElementType,
    ConfigSectionType,
    DataplaneAPIError,
    ValidationError,
    SynchronizationResult,
    ValidationDeploymentResult,
    compute_content_hash,
)
from .utils import (
    _check_early_exit_condition,
    extract_exception_origin,
    natural_sort_key,
    _to_dict_safe,
    extract_hostname_from_url,
    parse_validation_error_details,
)


logger = logging.getLogger(__name__)


class ConfigSynchronizer:
    """Configuration synchronizer owning persistent client pool and using endpoint bundling."""

    def __init__(self, endpoints: DataplaneEndpointSet):
        self.endpoints = endpoints

        # ConfigSynchronizer owns the client pool - single responsibility
        self.client_pool = DataplaneClientPool()

        # Lazy-initialized clients using owned pool
        self._validation_client: Optional[DataplaneClient] = None
        self._production_clients: Dict[str, DataplaneClient] = {}

    def create_client(
        self, endpoint: DataplaneEndpoint, timeout: float = 30.0
    ) -> DataplaneClient:
        """Factory method for creating clients with shared pool."""
        return DataplaneClient(endpoint=endpoint, timeout=timeout)

    def create_client_for_url(self, url: str, timeout: float = 30.0) -> DataplaneClient:
        """Factory method for creating clients by URL (convenience method)."""
        endpoint = self.endpoints.find_by_url(url)
        if not endpoint:
            raise ValueError(f"No endpoint found for URL: {url}")
        return self.create_client(endpoint, timeout)

    def get_client_pool(self) -> DataplaneClientPool:
        """Access to the persistent client pool for external clients."""
        return self.client_pool

    async def close_all_connections(self) -> None:
        """Close all persistent connections owned by this synchronizer."""
        await self.client_pool.close_all()

    def _get_validation_client(self) -> DataplaneClient:
        """Get validation client using owned pool."""
        if self._validation_client is None:
            self._validation_client = self.create_client(self.endpoints.validation)
        return self._validation_client

    def _get_production_client(self, endpoint: DataplaneEndpoint) -> DataplaneClient:
        """Get production client using owned pool."""
        if endpoint.url not in self._production_clients:
            self._production_clients[endpoint.url] = self.create_client(endpoint)
        return self._production_clients[endpoint.url]

    def get_pool_metrics(self) -> Dict[str, Any]:
        """Get connection pool metrics for monitoring."""
        return self.client_pool.get_pool_stats()

    def get_endpoint_health(self) -> Dict[str, str]:
        """Get health status of all endpoints."""
        health = {}
        for endpoint in self.endpoints.all_endpoints():
            # Could add health check logic here in the future
            health[endpoint.display_name] = "unknown"
        return health

    def _record_pool_metrics(self) -> None:
        """Record connection pool metrics for monitoring."""
        try:
            pool_stats = self.get_pool_metrics()
            metrics = get_metrics_collector()
            metrics.record_pool_statistics(pool_stats)

            # Log pool health for debugging
            logger.debug(
                f"📊 Pool stats: {pool_stats['active_connections']} active, "
                f"{pool_stats['total_references']} refs, "
                f"{pool_stats['statistics']['clients_created']} created, "
                f"{pool_stats['statistics']['clients_cleaned']} cleaned"
            )
        except Exception as e:
            logger.debug(f"Failed to record pool metrics: {e}")

    def _prepare_sync_content(
        self, config_context: HAProxyConfigContext
    ) -> Tuple[Dict[str, str], Dict[str, str], Dict[str, str], Dict[str, str]]:
        """Prepare content for synchronization."""
        return (
            {rc.filename: rc.content for rc in config_context.rendered_maps},
            {rc.filename: rc.content for rc in config_context.rendered_certificates},
            {rc.filename: rc.content for rc in config_context.rendered_acls},
            {rc.filename: rc.content for rc in config_context.rendered_files},
        )

    def _compute_template_hashes(
        self, config_context: HAProxyConfigContext
    ) -> Dict[str, str]:
        """Compute hashes for all rendered templates."""

        template_hashes = {}

        if config_context.rendered_config:
            template_hashes["haproxy.cfg"] = compute_content_hash(
                config_context.rendered_config.content
            )

        # Add all rendered content (maps, certificates, ACLs, files)
        for content in config_context.rendered_content:
            template_hashes[content.filename] = compute_content_hash(content.content)

        return template_hashes

    def update_production_clients(self, new_endpoints: List[DataplaneEndpoint]) -> None:
        """Update production clients based on current endpoints.

        This method handles dynamic HAProxy pod lifecycle by:
        - Creating clients for newly discovered endpoints
        - Removing clients for endpoints that are no longer present
        - Preserving existing clients for stable endpoints to maintain connection pooling

        Args:
            new_endpoints: Current list of production HAProxy endpoints
        """
        new_urls = [ep.url for ep in new_endpoints]

        # Remove clients for URLs that are no longer present
        removed_urls = set(self._production_clients.keys()) - set(new_urls)
        for url in removed_urls:
            # Simply remove the client - the underlying httpx client will be cleaned up
            # when the DataplaneClient is garbage collected
            del self._production_clients[url]
            logger.debug(f"Removed cached client for {url}")

        # Create clients for new URLs
        new_urls_set = set(new_urls)
        existing_urls = set(self._production_clients.keys())
        newly_added_urls = new_urls_set - existing_urls

        for url in newly_added_urls:
            # Find endpoint with auth from new_endpoints list
            endpoint = next(ep for ep in new_endpoints if ep.url == url)
            self._production_clients[url] = DataplaneClient(endpoint)
            logger.debug(f"Created cached client for {url}")

        # Update the endpoint set with new endpoints
        self.endpoints = DataplaneEndpointSet(
            validation=self.endpoints.validation,  # Keep the existing validation endpoint
            production=new_endpoints,
        )

    async def _sync_content_to_client(
        self,
        client: DataplaneClient,
        maps: Dict[str, str],
        certificates: Dict[str, str],
        acls: Dict[str, str],
        files: Dict[str, str],
        url: str,
    ) -> None:
        """Sync all content types to a single client."""
        if maps:
            logger.debug(f"Syncing {len(maps)} maps to {url}")
            await client.sync_maps(maps)

        if certificates:
            logger.debug(f"Syncing {len(certificates)} certificates to {url}")
            await client.sync_certificates(certificates)

        if acls:
            logger.debug(f"Syncing {len(acls)} ACLs to {url}")
            await client.sync_acls(acls)

        if files:
            logger.debug(f"Syncing {len(files)} files to {url}")
            await client.sync_files(files)

    async def _validate_configuration(self, config: str) -> None:
        """Validate configuration using the validation instance."""
        logger.debug(f"Validating configuration at {self.endpoints.validation.url}")
        try:
            validation_client = self._get_validation_client()
            await validation_client.validate_configuration(config)
        except Exception as e:
            raise ValidationError(f"Configuration validation failed: {e}") from e

    def _compare_nested_elements(
        self,
        current_nested: Dict[str, Any],
        new_nested: Dict[str, Any],
        section_type: ConfigSectionType,
        section_name: str,
        changes: List[ConfigChange],
    ) -> None:
        """Compare all nested elements within a section.

        This method compares nested configuration elements like servers, ACLs,
        HTTP request rules, etc. within backends, frontends, and defaults sections.

        Args:
            current_nested: Current nested elements for this section
            new_nested: New nested elements for this section
            section_type: Type of the parent section
            section_name: Name of the parent section
            changes: List to append detected changes to
        """
        # Define elements to compare for this section type
        elements_to_compare: list = []

        # Compare each type of nested element
        for attr_name, element_type, is_named in elements_to_compare:
            # Get nested element lists from the nested storage
            current_items = current_nested.get(attr_name, []) or []
            new_items = new_nested.get(attr_name, []) or []

            if not isinstance(current_items, list):
                current_items = []
            if not isinstance(new_items, list):
                new_items = []

            self._compare_element_list(
                current_items,
                new_items,
                element_type,
                section_type,
                section_name,
                changes,
                is_named,
            )

    def _compare_element_list(
        self,
        current_items: List[Any],
        new_items: List[Any],
        element_type: ConfigElementType,
        section_type: ConfigSectionType,
        section_name: str,
        changes: List[ConfigChange],
        is_named: bool,
    ) -> None:
        """Compare element lists using either named or ordered strategy.

        Args:
            current_items: Current list of elements
            new_items: New list of elements
            element_type: Type of the nested element
            section_type: Type of the parent section
            section_name: Name of the parent section
            changes: List to append detected changes to
            is_named: If True, use named comparison; if False, use ordered comparison
        """
        if is_named:
            self._compare_by_name(
                current_items,
                new_items,
                element_type,
                section_type,
                section_name,
                changes,
            )
        else:
            self._compare_by_order(
                current_items,
                new_items,
                element_type,
                section_type,
                section_name,
                changes,
            )

    def _compare_by_name(
        self,
        current_items: List[Any],
        new_items: List[Any],
        element_type: ConfigElementType,
        section_type: ConfigSectionType,
        section_name: str,
        changes: List[ConfigChange],
    ) -> None:
        """Compare named nested elements like servers or ACLs."""
        # Build dictionaries by name for efficient comparison
        current_dict = {}
        for item in current_items:
            if item.name:
                current_dict[item.name] = item
            elif item.id:
                current_dict[item.id] = item

        new_dict = {}
        for item in new_items:
            if item.name:
                new_dict[item.name] = item
            elif item.id:
                new_dict[item.id] = item

        current_names = set(current_dict.keys())
        new_names = set(new_dict.keys())

        # Deletions
        for name in sorted(current_names - new_names, key=natural_sort_key):
            changes.append(
                ConfigChange.create_element_change(
                    change_type=ConfigChangeType.DELETE,
                    section_type=section_type,
                    section_name=section_name,
                    element_type=element_type,
                    element_id=name,
                    old_config=current_dict[name],
                )
            )

        for name in sorted(new_names - current_names, key=natural_sort_key):
            changes.append(
                ConfigChange.create_element_change(
                    change_type=ConfigChangeType.CREATE,
                    section_type=section_type,
                    section_name=section_name,
                    element_type=element_type,
                    element_id=name,
                    new_config=new_dict[name],
                )
            )

        # Modifications
        for name in sorted(current_names & new_names, key=natural_sort_key):
            if _to_dict_safe(current_dict[name]) != _to_dict_safe(new_dict[name]):
                changes.append(
                    ConfigChange.create_element_change(
                        change_type=ConfigChangeType.UPDATE,
                        section_type=section_type,
                        section_name=section_name,
                        element_type=element_type,
                        element_id=name,
                        old_config=current_dict[name],
                        new_config=new_dict[name],
                    )
                )

    def _compare_by_order(
        self,
        current_items: List[Any],
        new_items: List[Any],
        element_type: ConfigElementType,
        section_type: ConfigSectionType,
        section_name: str,
        changes: List[ConfigChange],
    ) -> None:
        """Compare ordered nested elements like HTTP request rules."""
        # Compare lists element by element
        max_len = max(len(current_items), len(new_items))

        for i in range(max_len):
            if i < len(current_items) and i < len(new_items):
                # Both exist - check for modifications
                if _to_dict_safe(current_items[i]) != _to_dict_safe(new_items[i]):
                    changes.append(
                        ConfigChange(
                            change_type=ConfigChangeType.UPDATE,
                            section_type=section_type,
                            section_name=section_name,
                            element_type=element_type,
                            element_index=i,
                            old_config=current_items[i],
                            new_config=new_items[i],
                        )
                    )
            elif i < len(new_items):
                # New element added
                changes.append(
                    ConfigChange(
                        change_type=ConfigChangeType.CREATE,
                        section_type=section_type,
                        section_name=section_name,
                        element_type=element_type,
                        element_index=i,
                        new_config=new_items[i],
                    )
                )
            else:
                # Element removed (current has more elements than new)
                changes.append(
                    ConfigChange(
                        change_type=ConfigChangeType.DELETE,
                        section_type=section_type,
                        section_name=section_name,
                        element_type=element_type,
                        element_index=i,
                        old_config=current_items[i],
                    )
                )

    def _compare_section_configs(
        self,
        current: Dict[str, Any],
        new: Dict[str, Any],
        section_key: str,
        section_type: ConfigSectionType,
        changes: List[ConfigChange],
    ) -> None:
        """Compare configuration sections and append changes to the changes list.

        Args:
            current: Current configuration
            new: New configuration
            section_key: Key in the config dict (e.g., "backends", "frontends")
            section_type: ConfigSectionType for this section
            changes: List to append changes to
        """
        # Build name-indexed dictionaries
        current_items = {
            item.name: item
            for item in current.get(section_key, [])
            if hasattr(item, "name")
        }
        new_items = {
            item.name: item
            for item in new.get(section_key, [])
            if hasattr(item, "name")
        }

        current_names = set(current_items.keys())
        new_names = set(new_items.keys())

        # Deletions
        for name in current_names - new_names:
            changes.append(
                ConfigChange(
                    change_type=ConfigChangeType.DELETE,
                    section_type=section_type,
                    section_name=name,
                    old_config=current_items[name],
                )
            )

        for name in new_names - current_names:
            changes.append(
                ConfigChange(
                    change_type=ConfigChangeType.CREATE,
                    section_type=section_type,
                    section_name=name,
                    new_config=new_items[name],
                )
            )

        # Modifications
        for name in current_names & new_names:
            if _to_dict_safe(current_items[name]) != _to_dict_safe(new_items[name]):
                changes.append(
                    ConfigChange(
                        change_type=ConfigChangeType.UPDATE,
                        section_type=section_type,
                        section_name=name,
                        new_config=new_items[name],
                        old_config=current_items[name],
                    )
                )

            # Compare nested elements within existing sections
            current_nested = (
                current.get("nested_elements", {}).get(section_key, {}).get(name, {})
            )
            new_nested = (
                new.get("nested_elements", {}).get(section_key, {}).get(name, {})
            )
            self._compare_nested_elements(
                current_nested, new_nested, section_type, name, changes
            )

    def _analyze_config_changes(
        self, current: Dict[str, Any], new: Dict[str, Any]
    ) -> List[ConfigChange]:
        """Analyze two structured configurations and return list of actionable changes.

        This method compares HAProxy configuration sections and returns a list of
        ConfigChange objects that can be applied using granular dataplane API endpoints.

        Args:
            current: Current structured configuration
            new: New structured configuration

        Returns:
            List of ConfigChange objects representing the required changes
        """
        changes: List[ConfigChange] = []

        # Compare backends
        self._compare_section_configs(
            current, new, "backends", ConfigSectionType.BACKEND, changes
        )

        # Compare frontends
        self._compare_section_configs(
            current, new, "frontends", ConfigSectionType.FRONTEND, changes
        )

        # Compare defaults sections
        current_defaults = current.get("defaults", [])
        new_defaults = new.get("defaults", [])

        # For defaults sections, we compare by name (if available) or fallback to index
        for i, new_def in enumerate(new_defaults):
            if i < len(current_defaults):
                # Use the name from the new defaults object if available, otherwise fallback to index-based name
                section_name = getattr(new_def, "name", None) or f"defaults-{i}"

                # Existing defaults section - check if it needs updating
                if _to_dict_safe(current_defaults[i]) != _to_dict_safe(new_def):
                    changes.append(
                        ConfigChange(
                            change_type=ConfigChangeType.UPDATE,
                            section_type=ConfigSectionType.DEFAULTS,
                            section_name=section_name,
                            new_config=new_def,
                            old_config=current_defaults[i],
                        )
                    )

                # Skip nested element comparison for defaults sections
                # HAProxy Dataplane API v3 limitation: defaults sections don't support nested
                # element endpoints (they return HTTP 501). Defaults are handled as atomic units
                # and any changes trigger a full section update using full_section=true.

        # Compare global section
        current_global = current.get("global")
        new_global = new.get("global")

        if current_global and new_global:
            if _to_dict_safe(current_global) != _to_dict_safe(new_global):
                changes.append(
                    ConfigChange(
                        change_type=ConfigChangeType.UPDATE,
                        section_type=ConfigSectionType.GLOBAL,
                        section_name="global",
                        new_config=new_global,
                        old_config=current_global,
                    )
                )
        elif new_global and not current_global:
            changes.append(
                ConfigChange(
                    change_type=ConfigChangeType.CREATE,
                    section_type=ConfigSectionType.GLOBAL,
                    section_name="global",
                    new_config=new_global,
                )
            )
        elif current_global and not new_global:
            changes.append(
                ConfigChange(
                    change_type=ConfigChangeType.DELETE,
                    section_type=ConfigSectionType.GLOBAL,
                    section_name="global",
                    old_config=current_global,
                )
            )

        # Helper function for named sections
        def analyze_named_sections(section_key: str, section_type: ConfigSectionType):
            """Analyze named configuration sections for changes."""
            current_sections = {
                s.name: s
                for s in current.get(section_key, [])
                if hasattr(s, "name") and s.name
            }
            new_sections = {
                s.name: s
                for s in new.get(section_key, [])
                if hasattr(s, "name") and s.name
            }

            current_names = set(current_sections.keys())
            new_names = set(new_sections.keys())

            # Deletions
            for name in current_names - new_names:
                changes.append(
                    ConfigChange(
                        change_type=ConfigChangeType.DELETE,
                        section_type=section_type,
                        section_name=name,
                        old_config=current_sections[name],
                    )
                )

                for name in new_names - current_names:
                    changes.append(
                        ConfigChange(
                            change_type=ConfigChangeType.CREATE,
                            section_type=section_type,
                            section_name=name,
                            new_config=new_sections[name],
                        )
                    )

            # Modifications
            for name in current_names & new_names:
                if _to_dict_safe(current_sections[name]) != _to_dict_safe(
                    new_sections[name]
                ):
                    changes.append(
                        ConfigChange(
                            change_type=ConfigChangeType.UPDATE,
                            section_type=section_type,
                            section_name=name,
                            new_config=new_sections[name],
                            old_config=current_sections[name],
                        )
                    )

        # Analyze all named sections
        analyze_named_sections("userlists", ConfigSectionType.USERLIST)
        analyze_named_sections("caches", ConfigSectionType.CACHE)
        analyze_named_sections("mailers", ConfigSectionType.MAILERS)
        analyze_named_sections("resolvers", ConfigSectionType.RESOLVER)
        analyze_named_sections("peers", ConfigSectionType.PEER)
        analyze_named_sections("fcgi_apps", ConfigSectionType.FCGI_APP)
        analyze_named_sections("http_errors", ConfigSectionType.HTTP_ERRORS)
        analyze_named_sections("rings", ConfigSectionType.RING)
        analyze_named_sections("log_forwards", ConfigSectionType.LOG_FORWARD)
        analyze_named_sections("programs", ConfigSectionType.PROGRAM)

        return changes

    def _safe_compare_sections(
        self,
        section_name: str,
        current: Dict[str, Any],
        new: Dict[str, Any],
        changes: List[str],
        max_changes: int,
        comparison_func: Callable[
            [str, Dict[str, Any], Dict[str, Any], List[str]], bool
        ],
    ) -> bool:
        """Safely compare configuration sections with error handling."""
        try:
            return comparison_func(section_name, current, new, changes)
        except Exception as e:
            logger.debug(f"Error comparing {section_name}: {type(e).__name__}: {e}")
            changes.append(f"error comparing {section_name}: {type(e).__name__}")
            return _check_early_exit_condition(changes, max_changes)

    def _compare_named_sections_impl(
        self,
        section_name: str,
        current: Dict[str, Any],
        new: Dict[str, Any],
        changes: List[str],
    ) -> bool:
        """Implementation for comparing named configuration sections."""
        current_sections = {
            s.name: _to_dict_safe(s)
            for s in current.get(section_name, [])
            if hasattr(s, "name") and s.name
        }
        new_sections = {
            s.name: _to_dict_safe(s)
            for s in new.get(section_name, [])
            if hasattr(s, "name") and s.name
        }

        current_names = set(current_sections.keys())
        new_names = set(new_sections.keys())
        section_type = section_name[:-1]  # Remove 's' from plural

        changes.extend(
            f"remove {section_type} {name}" for name in current_names - new_names
        )
        changes.extend(
            f"add {section_type} {name}" for name in new_names - current_names
        )
        changes.extend(
            f"modify {section_type} {name}"
            for name in current_names & new_names
            if current_sections[name] != new_sections[name]
        )
        return False  # Never early exit from implementation

    def _compare_list_sections_impl(
        self,
        section_name: str,
        current: Dict[str, Any],
        new: Dict[str, Any],
        changes: List[str],
    ) -> bool:
        """Implementation for comparing list configuration sections."""
        current_list = [_to_dict_safe(s) for s in current.get(section_name, [])]
        new_list = [_to_dict_safe(s) for s in new.get(section_name, [])]

        if len(current_list) != len(new_list):
            changes.append(
                f"{section_name} count changed from {len(current_list)} to {len(new_list)}"
            )
        else:
            changes.extend(
                f"modify {section_name} section {i}"
                for i, (curr, new_item) in enumerate(zip(current_list, new_list))
                if curr != new_item
            )
        return False  # Never early exit from implementation

    def _compare_named_config_sections(
        self,
        section_name: str,
        current: Dict[str, Any],
        new: Dict[str, Any],
        changes: List[str],
        max_changes: int,
    ) -> bool:
        """Compare named configuration sections and return True if early exit needed."""
        if self._safe_compare_sections(
            section_name,
            current,
            new,
            changes,
            max_changes,
            self._compare_named_sections_impl,
        ):
            return True
        return _check_early_exit_condition(changes, max_changes)

    def _compare_list_config_sections(
        self,
        section_name: str,
        current: Dict[str, Any],
        new: Dict[str, Any],
        changes: List[str],
        max_changes: int,
    ) -> bool:
        """Compare list configuration sections and return True if early exit needed."""
        if self._safe_compare_sections(
            section_name,
            current,
            new,
            changes,
            max_changes,
            self._compare_list_sections_impl,
        ):
            return True
        return _check_early_exit_condition(changes, max_changes)

    def _compare_global_section(
        self, current: Dict[str, Any], new: Dict[str, Any], changes: List[str]
    ) -> None:
        """Compare global configuration section."""
        current_global = _to_dict_safe(current.get("global"))
        new_global = _to_dict_safe(new.get("global"))

        if current_global and new_global:
            if current_global != new_global:
                changes.append("modify global")
        elif new_global and not current_global:
            changes.append("add global")
        elif current_global and not new_global:
            changes.append("remove global")

    def _compare_structured_configs(
        self, current: Dict[str, Any], new: Dict[str, Any]
    ) -> List[str]:
        """Compare two structured configurations and return list of changes.

        This method performs an optimized comparison of HAProxy configuration sections
        including backends, frontends, defaults, global, and all other sections.

        Performance considerations:
        - For large configurations (>100 backends/frontends), this method may consume
          significant memory as it loads all configuration sections into memory
        - Early exit after a maximum number of changes to avoid expensive
          deep comparisons when many changes are detected
        - Uses xxHash-based serialization with defensive error handling

        Args:
            current: Current structured configuration
            new: New structured configuration

        Returns:
            List of change descriptions, empty if configs are identical
        """
        start_time = time.time()
        changes: List[str] = []
        max_changes_before_exit = 10  # Stop comparison after finding this many changes

        # Compare main configuration sections
        if self._compare_backends_and_frontends(
            current, new, changes, max_changes_before_exit
        ):
            return changes

        # Compare defaults sections
        self._compare_defaults_sections(current, new, changes)

        # Compare all named sections
        named_sections = [
            "userlists",
            "caches",
            "mailers",
            "resolvers",
            "peers",
            "fcgi_apps",
            "http_errors",
            "rings",
            "log_forwards",
            "programs",
        ]

        for section_name in named_sections:
            if self._compare_named_config_sections(
                section_name, current, new, changes, max_changes_before_exit
            ):
                return changes

        # Compare global section
        self._compare_global_section(current, new, changes)

        # Record performance metrics
        self._record_comparison_metrics(start_time, len(changes))

        return changes

    def _compare_backends_and_frontends(
        self,
        current: Dict[str, Any],
        new: Dict[str, Any],
        changes: List[str],
        max_changes: int,
    ) -> bool:
        """Compare backends and frontends sections. Returns True if early exit needed."""
        # Compare backends
        if self._compare_named_section_type(
            current, new, "backends", "backend", changes, max_changes
        ):
            return True

        # Compare frontends
        if self._compare_named_section_type(
            current, new, "frontends", "frontend", changes, max_changes
        ):
            return True

        return False

    def _compare_named_section_type(
        self,
        current: Dict[str, Any],
        new: Dict[str, Any],
        section_key: str,
        section_label: str,
        changes: List[str],
        max_changes: int,
    ) -> bool:
        """Compare a named section type (like backends or frontends). Returns True if early exit needed."""
        # Build name-indexed dictionaries
        current_sections = {
            item.name: _to_dict_safe(item)
            for item in current.get(section_key, [])
            if hasattr(item, "name")
        }
        new_sections = {
            item.name: _to_dict_safe(item)
            for item in new.get(section_key, [])
            if hasattr(item, "name")
        }

        current_names = set(current_sections.keys())
        new_names = set(new_sections.keys())

        changes.extend(
            f"remove {section_label} {name}" for name in current_names - new_names
        )
        if _check_early_exit_condition(changes, max_changes):
            return True

        # Check for additions
        changes.extend(
            f"add {section_label} {name}" for name in new_names - current_names
        )
        if _check_early_exit_condition(changes, max_changes):
            return True

        # Check for modifications
        changes.extend(
            f"modify {section_label} {name}"
            for name in current_names & new_names
            if current_sections[name] != new_sections[name]
        )
        return _check_early_exit_condition(changes, max_changes)

    def _compare_defaults_sections(
        self, current: Dict[str, Any], new: Dict[str, Any], changes: List[str]
    ) -> None:
        """Compare defaults sections."""
        current_defaults = [_to_dict_safe(d) for d in current.get("defaults", [])]
        new_defaults = [_to_dict_safe(d) for d in new.get("defaults", [])]

        if len(current_defaults) != len(new_defaults):
            changes.append(
                f"defaults count changed from {len(current_defaults)} to {len(new_defaults)}"
            )
        else:
            changes.extend(
                f"modify defaults section {i}"
                for i, (curr, new_def) in enumerate(zip(current_defaults, new_defaults))
                if curr != new_def
            )

    def _record_comparison_metrics(self, start_time: float, changes_count: int) -> None:
        """Record performance metrics for the comparison operation."""
        elapsed = time.time() - start_time
        logger.debug(
            f"⏱️ Structured config comparison took {elapsed:.3f}s, found {changes_count} changes"
        )

        # Record metrics
        metrics = get_metrics_collector()
        if hasattr(metrics, "record_custom_metric"):
            metrics.record_custom_metric("structured_comparison_time", elapsed)
            metrics.record_custom_metric("structured_changes_count", changes_count)

    async def _deploy_to_single_instance(
        self,
        url: str,
        config: str,
        maps_to_sync: Dict[str, str],
        certificates_to_sync: Dict[str, str],
        acls_to_sync: Dict[str, str],
        files_to_sync: Dict[str, str],
        validation_structured: Dict[str, Any],
    ) -> SynchronizationResult:
        """Deploy to a single production instance with structured comparison.

        Returns:
            Dict with keys: method, version
        """

        client = self._production_clients[url]

        # Sync auxiliary content first (maps, certs, files)
        await self._sync_content_to_client(
            client, maps_to_sync, certificates_to_sync, acls_to_sync, files_to_sync, url
        )

        # Fetch current structured config from production instance
        try:
            production_structured = await client.fetch_structured_configuration()

            # Analyze structured configurations to get actionable changes
            config_changes = self._analyze_config_changes(
                production_structured, validation_structured
            )

            if not config_changes:
                # No changes needed - skip deployment
                logger.debug(f"⏭️  No structural changes for {url}, skipping deployment")
                return SynchronizationResult(
                    method="skipped",
                    version="unchanged",
                    reload_triggered=False,
                    reload_id=None,
                )
            else:
                # Changes detected - use structured deployment
                change_descriptions = [str(change) for change in config_changes]
                logger.debug(
                    f"📝 {len(config_changes)} changes detected for {url}: {', '.join(change_descriptions[:5])}"
                )

                try:
                    deploy_result = await client.deploy_structured_configuration(
                        config_changes
                    )
                    return SynchronizationResult(
                        method="structured",
                        version=deploy_result.version,
                        reload_triggered=False,  # StructuredDeploymentResult doesn't have reload_triggered
                        reload_id=None,  # StructuredDeploymentResult doesn't have reload_id
                    )
                except DataplaneAPIError as structured_error:
                    # If structured deployment fails, fall back to raw deployment
                    # Extract origin details from the original error if available
                    origin_details = ""
                    if structured_error.original_error:
                        origin_details = f"\n{extract_exception_origin(structured_error.original_error)}"

                    logger.warning(
                        f"⚠️  Structured deployment failed for {url}, falling back to raw: {structured_error}{origin_details}"
                    )

                    # Record structured deployment failure metrics
                    metrics = get_metrics_collector()
                    metrics.increment_dataplane_fallback("structured_to_raw")

                    fallback_result: ValidationDeploymentResult = (
                        await client.deploy_configuration(config)
                    )
                    return SynchronizationResult(
                        method="raw_fallback",
                        version=fallback_result.version,
                        reload_triggered=fallback_result.reload_id
                        is not None,  # ValidationDeploymentResult has reload_id
                        reload_id=fallback_result.reload_id,
                    )

        except Exception as fetch_error:
            # Fallback to conditional deployment if structured comparison fails
            logger.warning(
                f"⚠️  Structured comparison failed for {url}, falling back to conditional: {fetch_error}"
            )

            # Record fallback metrics
            metrics = get_metrics_collector()
            metrics.increment_dataplane_fallback("structured_to_conditional")

            try:
                conditional_result: ValidationDeploymentResult = (
                    await client.deploy_configuration(config)
                )
                return SynchronizationResult(
                    method="conditional",
                    version=conditional_result.version,
                    reload_triggered=conditional_result.reload_id is not None,
                    reload_id=conditional_result.reload_id,
                )
            except Exception as conditional_error:
                # Final fallback to regular deployment
                # Extract origin details for debugging
                origin_details = f"\n{extract_exception_origin(conditional_error)}"

                logger.warning(
                    f"⚠️  Conditional deployment also failed for {url}, using regular deployment: {conditional_error}{origin_details}"
                )

                # Record double fallback metrics
                metrics.increment_dataplane_fallback("conditional_to_regular")

                final_result: ValidationDeploymentResult = (
                    await client.deploy_configuration(config)
                )
                return SynchronizationResult(
                    method="fallback",
                    version=final_result.version,
                    reload_triggered=final_result.reload_id is not None,
                    reload_id=final_result.reload_id,
                )

    def _handle_deployment_error(
        self, url: str, error: Exception, config: str, results: Dict[str, Any]
    ) -> None:
        """Handle deployment error with enhanced logging."""
        results["failed"] += 1
        results["errors"].append(f"{url}: {error}")

        error_msg = f"❌ Failed to deploy to {url}: {error}"
        if isinstance(
            error, DataplaneAPIError
        ) and "Configuration context around error:" in str(error):
            logger.error(error_msg)
        else:
            try:
                parsed_error_msg, error_line, error_context = (
                    parse_validation_error_details(str(error), config)
                )
                if error_context:
                    error_msg += (
                        f"\n\nConfiguration context around error:\n{error_context}"
                    )
            except Exception as parse_error:
                # Broad exception catch is necessary here because parse_validation_error_details
                # calls extract_config_context which performs string operations on user-provided
                # configuration content that may contain unexpected characters or formats that
                # could raise various exceptions (UnicodeError, IndexError, etc.). We must ensure
                # that error parsing failure doesn't mask the original deployment error.
                logger.debug(
                    f"Could not parse validation error details: {type(parse_error).__name__}: {parse_error}"
                )
            logger.error(error_msg)

    async def sync_configuration(
        self, config_context: HAProxyConfigContext
    ) -> Dict[str, Any]:
        """Synchronize configuration to all endpoints with validation-first deployment.

        This method implements an improved approach that minimizes HAProxy reloads:
        1. Sync maps/certs/files to validation instance and validate config
        2. Deploy to production instances only if configuration changed
        3. Use structured deployment with automatic fallbacks to avoid unnecessary reloads

        Args:
            config_context: The rendered configuration context
        """
        if not config_context.rendered_config:
            raise DataplaneAPIError(
                "No rendered HAProxy configuration available",
                operation="sync_configuration",
            )

        # Prepare configuration content
        config = config_context.rendered_config.content
        sync_content = self._prepare_sync_content(config_context)

        # Compute template hashes for deployment history tracking
        _ = self._compute_template_hashes(config_context)

        # Update production clients to handle dynamic URL changes
        self.update_production_clients(self.endpoints.production)

        # Validate configuration using validation instance
        validation_structured = await self._validate_and_prepare_config(
            config, sync_content
        )

        # Deploy to production instances
        results = await self._deploy_to_production_instances(
            config, sync_content, validation_structured
        )

        # Record pool metrics after deployment operations
        self._record_pool_metrics()

        # Log final results
        self._log_sync_results(results)

        return results

    async def _validate_and_prepare_config(
        self,
        config: str,
        sync_content: Tuple[
            Dict[str, str], Dict[str, str], Dict[str, str], Dict[str, str]
        ],
    ) -> Dict[str, Any]:
        """Validate configuration and prepare structured config for deployment."""
        maps_to_sync, certificates_to_sync, acls_to_sync, files_to_sync = sync_content

        # Step 1: Sync content to validation instance and validate
        logger.debug("🔍 Validating configuration and syncing auxiliary content")
        validation_client = self._get_validation_client()
        await self._sync_content_to_client(
            validation_client,
            maps_to_sync,
            certificates_to_sync,
            acls_to_sync,
            files_to_sync,
            "validation instance",
        )
        await self._validate_configuration(config)

        # Step 2: Deploy config to validation instance and fetch structured components
        logger.debug(
            "📤 Deploying config to validation instance for structured comparison"
        )
        await validation_client.deploy_configuration(config)

        # Fetch structured config from validation instance
        logger.debug("🔍 Fetching structured configuration from validation instance")
        return await validation_client.fetch_structured_configuration()

    async def _deploy_to_production_instances(
        self,
        config: str,
        sync_content: Tuple[
            Dict[str, str], Dict[str, str], Dict[str, str], Dict[str, str]
        ],
        validation_structured: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Deploy configuration to production instances in parallel."""
        maps_to_sync, certificates_to_sync, acls_to_sync, files_to_sync = sync_content

        # Initialize results tracking
        results: Dict[str, Any] = {
            "successful": 0,
            "failed": 0,
            "skipped": 0,
            "errors": [],
        }

        logger.debug(
            f"🚀 Deploying to {len(self.endpoints.production)} production instances"
        )

        # Create deployment tasks for parallel execution
        deployment_tasks = []
        for endpoint in self.endpoints.production:
            task = self._deploy_to_single_instance(
                endpoint.url,
                config,
                maps_to_sync,
                certificates_to_sync,
                acls_to_sync,
                files_to_sync,
                validation_structured,
            )
            deployment_tasks.append(task)

        # Execute all deployments in parallel
        deployment_results = await asyncio.gather(
            *deployment_tasks, return_exceptions=True
        )

        # Process deployment results
        self._process_deployment_results(deployment_results, config, results)

        return results

    def _process_deployment_results(
        self, deployment_results: List[Any], config: str, results: Dict[str, Any]
    ) -> None:
        """Process the results from parallel deployment tasks."""
        for endpoint, result in zip(self.endpoints.production, deployment_results):
            if isinstance(result, Exception):
                # Task failed with exception
                self._handle_deployment_error(endpoint.url, result, config, results)
            elif isinstance(result, SynchronizationResult):
                # Process successful result
                self._process_successful_deployment(endpoint.url, result, results)
            else:
                # Unexpected result type
                error_msg = f"Unexpected result type from deployment: {type(result)}"
                self._handle_deployment_error(
                    endpoint.url, Exception(error_msg), config, results
                )

    def _process_successful_deployment(
        self, url: str, result: SynchronizationResult, results: Dict[str, Any]
    ) -> None:
        """Process a successful deployment result."""
        if result.method == "skipped":
            results["skipped"] += 1
        else:
            results["successful"] += 1
            self._log_successful_deployment(url, result)

        # Log detailed deployment information
        self._log_deployment_details(url, result)

    def _log_successful_deployment(
        self, url: str, result: SynchronizationResult
    ) -> None:
        """Log information about successful deployment."""
        method_emojis = {
            "structured": "🏗️",
            "conditional": "✅",
            "raw_fallback": "🔄",
            "fallback": "🔄",
        }
        method_emoji = method_emojis.get(result.method, "✅")
        pod_info = self._extract_pod_info_from_url(url)
        logger.info(
            f"{method_emoji} Deployed to {pod_info['pod_name']} ({url}) ({result.method}), version: {result.version}"
        )

    def _log_deployment_details(self, url: str, result: SynchronizationResult) -> None:
        """Log detailed deployment information for debugging."""
        reload_triggered = result.reload_triggered
        reload_id = result.reload_id

        logger.debug(
            f"🔍 Processing deployment result for {url}: reload_triggered={reload_triggered}, "
            f"reload_id={reload_id}, method={result.method}, version={result.version}"
        )

        pod_info = self._extract_pod_info_from_url(url)
        if result.method == "skipped":
            logger.debug(
                f"ℹ️  Configuration unchanged on {pod_info['pod_name']} ({url})"
            )
        else:
            logger.debug(
                f"🔄 Configuration updated on {pod_info['pod_name']} ({url}) using {result.method}"
            )

    def _log_sync_results(self, results: Dict[str, Any]) -> None:
        """Log the final synchronization results."""
        total_instances = len(self.endpoints.production)
        if results["successful"] > 0:
            # Log at INFO when we actually deployed something
            logger.info(
                f"🎯 Sync complete: {results['successful']} deployed, "
                f"{results['skipped']} skipped (unchanged), "
                f"{results['failed']} failed out of {total_instances} instances"
            )
        elif results["failed"] > 0:
            # Log at INFO when there were failures (important to know)
            logger.info(
                f"Sync complete: {results['successful']} successful, {results['failed']} failed"
            )
        else:
            # Log at DEBUG when nothing changed (all skipped)
            logger.debug(
                f"🎯 Sync complete: {results['successful']} deployed, "
                f"{results['skipped']} skipped (unchanged), "
                f"{results['failed']} failed out of {total_instances} instances"
            )

    def _extract_pod_info_from_url(self, url: str) -> Dict[str, str]:
        """Extract pod information from dataplane URL.

        Args:
            url: Dataplane URL in format http://pod_ip:port

        Returns:
            Dictionary with 'pod_ip' and 'pod_name' keys
        """
        try:
            # Parse URL to extract IP address
            pod_ip = extract_hostname_from_url(url)

            if not pod_ip:
                return {"pod_ip": "unknown", "pod_name": "unknown"}

            # Use actual pod name from endpoint if available, otherwise fallback to IP-based name
            endpoint = self.endpoints.find_by_url(url)
            pod_name = (
                endpoint.pod_name
                if endpoint and endpoint.pod_name
                else f"pod-{pod_ip.replace('.', '-')}"
            )

            return {"pod_ip": pod_ip, "pod_name": pod_name}

        except Exception as e:
            logger.debug(f"Error extracting pod info from URL {url}: {e}")
            return {"pod_ip": "unknown", "pod_name": "unknown"}
