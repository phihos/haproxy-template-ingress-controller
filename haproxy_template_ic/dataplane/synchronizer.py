"""
HAProxy Configuration Synchronizer.

This module provides the ConfigSynchronizer class for synchronizing HAProxy configurations
across multiple instances with validation-first deployment and structured comparison.
"""

import asyncio
import logging
import time
from typing import TYPE_CHECKING, Any, Callable, Dict, List, Optional, Tuple

if TYPE_CHECKING:
    from haproxy_template_ic.credentials import Credentials

from haproxy_template_ic.models import HAProxyConfigContext
from .client import DataplaneClient, _SECTION_ELEMENTS
from .errors import DataplaneAPIError, ValidationError
from .models import ConfigChange
from .types import ConfigChangeType, ConfigElementType, ConfigSectionType
from .utils import (
    parse_validation_error_details,
    extract_hostname_from_url,
    _check_early_exit_condition,
    _to_dict_safe,
    _natural_sort_key,
    MAX_CONFIG_COMPARISON_CHANGES,
)
from haproxy_template_ic.metrics import get_metrics_collector
from haproxy_template_ic.activity import (
    EventType,
    get_activity_buffer,
    ActivityBuffer,
    ActivityEventMetadata,
)

logger = logging.getLogger(__name__)


class ConfigSynchronizer:
    """Simple configuration synchronizer for HAProxy instances."""

    def __init__(
        self,
        production_urls: List[str],
        validation_url: str,
        credentials: "Credentials",
        activity_buffer: Optional[ActivityBuffer] = None,
        url_to_pod_name: Optional[Dict[str, str]] = None,
    ):
        self.production_urls = production_urls
        self.validation_url = validation_url
        self.credentials = credentials
        self.activity_buffer = activity_buffer or get_activity_buffer()
        self.url_to_pod_name = url_to_pod_name or {}

        self._validation_client: Optional[DataplaneClient] = None
        self._production_clients: Dict[str, DataplaneClient] = {}

    def _get_validation_client(self) -> DataplaneClient:
        """Get validation client, creating it if needed (lazy initialization)."""
        if self._validation_client is None:
            self._validation_client = DataplaneClient(
                self.validation_url,
                auth=(
                    self.credentials.validation.username,
                    self.credentials.validation.password.get_secret_value(),
                ),
            )
        return self._validation_client

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
        from .models import compute_content_hash

        template_hashes = {}

        # Add main HAProxy config
        if config_context.rendered_config:
            template_hashes["haproxy.cfg"] = compute_content_hash(
                config_context.rendered_config.content
            )

        # Add all rendered content (maps, certificates, ACLs, files)
        for content in config_context.rendered_content:
            template_hashes[content.filename] = compute_content_hash(content.content)

        return template_hashes

    def _update_production_clients(
        self, new_urls: List[str], url_to_pod_name: Optional[Dict[str, str]] = None
    ) -> None:
        """Update production clients based on current URLs.

        This method handles dynamic HAProxy pod lifecycle by:
        - Creating clients for newly discovered URLs
        - Removing clients for URLs that are no longer present
        - Preserving existing clients for stable URLs to maintain connection pooling

        Args:
            new_urls: Current list of production HAProxy URLs
            url_to_pod_name: Optional mapping from URLs to pod names
        """
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
            self._production_clients[url] = DataplaneClient(
                url,
                auth=(
                    self.credentials.dataplane.username,
                    self.credentials.dataplane.password.get_secret_value(),
                ),
            )
            logger.debug(f"Created cached client for {url}")

        # Update the production URLs list
        self.production_urls = new_urls

        # Update pod name mapping if provided
        if url_to_pod_name is not None:
            self.url_to_pod_name = url_to_pod_name

    def add_production_url(self, url: str) -> None:
        """Add a single production URL and create its client.

        Args:
            url: The production HAProxy dataplane URL to add
        """
        if url not in self._production_clients:
            self._production_clients[url] = DataplaneClient(
                url,
                auth=(
                    self.credentials.dataplane.username,
                    self.credentials.dataplane.password.get_secret_value(),
                ),
            )
            logger.debug(f"➕ Added production client for {url}")

            # Update the URLs list
            if url not in self.production_urls:
                self.production_urls.append(url)

    def remove_production_url(self, url: str) -> None:
        """Remove a single production URL and cleanup its client.

        Args:
            url: The production HAProxy dataplane URL to remove
        """
        if url in self._production_clients:
            # Remove the client
            del self._production_clients[url]
            logger.debug(f"➖ Removed production client for {url}")

            # Update the URLs list
            if url in self.production_urls:
                self.production_urls.remove(url)

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
        logger.debug(f"Validating configuration at {self.validation_url}")
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
        # Get element mappings from registry
        elements_to_compare = _SECTION_ELEMENTS.get(section_type, [])

        # Compare each type of nested element
        for attr_name, element_type, is_named in elements_to_compare:
            # Get nested element lists from the nested storage
            current_items = current_nested.get(attr_name, []) or []
            new_items = new_nested.get(attr_name, []) or []

            # Ensure we have lists
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
            if hasattr(item, "name") and item.name:
                current_dict[item.name] = item
            elif hasattr(item, "id") and item.id:
                current_dict[item.id] = item

        new_dict = {}
        for item in new_items:
            if hasattr(item, "name") and item.name:
                new_dict[item.name] = item
            elif hasattr(item, "id") and item.id:
                new_dict[item.id] = item

        current_names = set(current_dict.keys())
        new_names = set(new_dict.keys())

        # Deletions
        for name in sorted(current_names - new_names, key=_natural_sort_key):
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

        # Additions
        for name in sorted(new_names - current_names, key=_natural_sort_key):
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
        for name in sorted(current_names & new_names, key=_natural_sort_key):
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

        # Additions
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

            # Additions
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
        - Early exit after MAX_CONFIG_COMPARISON_CHANGES changes to avoid expensive
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
        max_changes_before_exit = MAX_CONFIG_COMPARISON_CHANGES

        # Compare backends - optimized with dict comprehensions
        current_backends = {
            b.name: _to_dict_safe(b)
            for b in current.get("backends", [])
            if hasattr(b, "name")
        }
        new_backends = {
            b.name: _to_dict_safe(b)
            for b in new.get("backends", [])
            if hasattr(b, "name")
        }

        # Find changes in backends efficiently
        current_names = set(current_backends.keys())
        new_names = set(new_backends.keys())

        changes.extend(f"remove backend {name}" for name in current_names - new_names)
        if _check_early_exit_condition(changes, max_changes_before_exit):
            return changes

        changes.extend(f"add backend {name}" for name in new_names - current_names)
        if _check_early_exit_condition(changes, max_changes_before_exit):
            return changes

        changes.extend(
            f"modify backend {name}"
            for name in current_names & new_names
            if current_backends[name] != new_backends[name]
        )
        if _check_early_exit_condition(changes, max_changes_before_exit):
            return changes

        # Compare frontends - same optimization
        current_frontends = {
            f.name: _to_dict_safe(f)
            for f in current.get("frontends", [])
            if hasattr(f, "name")
        }
        new_frontends = {
            f.name: _to_dict_safe(f)
            for f in new.get("frontends", [])
            if hasattr(f, "name")
        }

        current_names = set(current_frontends.keys())
        new_names = set(new_frontends.keys())

        changes.extend(f"remove frontend {name}" for name in current_names - new_names)
        if _check_early_exit_condition(changes, max_changes_before_exit):
            return changes

        changes.extend(f"add frontend {name}" for name in new_names - current_names)
        if _check_early_exit_condition(changes, max_changes_before_exit):
            return changes

        changes.extend(
            f"modify frontend {name}"
            for name in current_names & new_names
            if current_frontends[name] != new_frontends[name]
        )
        if _check_early_exit_condition(changes, max_changes_before_exit):
            return changes

        # Compare defaults sections
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

        # Helper function to compare named sections (similar to backends/frontends)
        def compare_named_sections(section_name: str) -> bool:
            """Compare named configuration sections and return True if early exit needed."""
            nonlocal changes
            try:
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

                changes.extend(
                    f"remove {section_name[:-1]} {name}"
                    for name in current_names - new_names
                )
                if _check_early_exit_condition(changes, max_changes_before_exit):
                    return True

                changes.extend(
                    f"add {section_name[:-1]} {name}"
                    for name in new_names - current_names
                )
                if _check_early_exit_condition(changes, max_changes_before_exit):
                    return True

                changes.extend(
                    f"modify {section_name[:-1]} {name}"
                    for name in current_names & new_names
                    if current_sections[name] != new_sections[name]
                )
                return _check_early_exit_condition(changes, max_changes_before_exit)
            except Exception as e:
                logger.debug(f"Error comparing {section_name}: {type(e).__name__}: {e}")
                changes.append(f"error comparing {section_name}: {type(e).__name__}")
                return _check_early_exit_condition(changes, max_changes_before_exit)

        # Helper function to compare list sections (similar to defaults)
        def compare_list_sections(section_name: str) -> bool:
            """Compare list configuration sections and return True if early exit needed."""
            nonlocal changes
            try:
                current_list = [_to_dict_safe(s) for s in current.get(section_name, [])]
                new_list = [_to_dict_safe(s) for s in new.get(section_name, [])]

                if len(current_list) != len(new_list):
                    changes.append(
                        f"{section_name} count changed from {len(current_list)} to {len(new_list)}"
                    )
                    return _check_early_exit_condition(changes, max_changes_before_exit)
                else:
                    changes.extend(
                        f"modify {section_name} section {i}"
                        for i, (curr, new_item) in enumerate(
                            zip(current_list, new_list)
                        )
                        if curr != new_item
                    )
                    return _check_early_exit_condition(changes, max_changes_before_exit)
            except Exception as e:
                logger.debug(f"Error comparing {section_name}: {type(e).__name__}: {e}")
                changes.append(f"error comparing {section_name}: {type(e).__name__}")
                return _check_early_exit_condition(changes, max_changes_before_exit)

        # Compare all named sections
        if compare_named_sections("userlists"):
            return changes

        if compare_named_sections("caches"):
            return changes

        if compare_named_sections("mailers"):
            return changes

        if compare_named_sections("resolvers"):
            return changes

        if compare_named_sections("peers"):
            return changes

        if compare_named_sections("fcgi_apps"):
            return changes

        if compare_named_sections("http_errors"):
            return changes

        if compare_named_sections("rings"):
            return changes

        if compare_named_sections("log_forwards"):
            return changes

        if compare_named_sections("programs"):
            return changes

        # Compare global section
        current_global = _to_dict_safe(current.get("global"))
        new_global = _to_dict_safe(new.get("global"))

        if current_global and new_global:
            if current_global != new_global:
                changes.append("modify global")
        elif new_global and not current_global:
            changes.append("add global")
        elif current_global and not new_global:
            changes.append("remove global")

        # Log comparison performance
        elapsed = time.time() - start_time
        logger.debug(
            f"⏱️ Structured config comparison took {elapsed:.3f}s, found {len(changes)} changes"
        )

        # Record metrics
        metrics = get_metrics_collector()
        if hasattr(metrics, "record_custom_metric"):
            metrics.record_custom_metric("structured_comparison_time", elapsed)
            metrics.record_custom_metric("structured_changes_count", len(changes))

        return changes

    async def _deploy_to_single_instance(
        self,
        url: str,
        config: str,
        maps_to_sync: Dict[str, str],
        certificates_to_sync: Dict[str, str],
        acls_to_sync: Dict[str, str],
        files_to_sync: Dict[str, str],
        validation_structured: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Deploy to a single production instance with structured comparison.

        Returns:
            Dict with keys: method, version
        """
        # Record deployment start event
        pod_name = self.url_to_pod_name.get(url)
        self.activity_buffer.add_event_sync(
            EventType.DEPLOYMENT_START,
            f"Starting deployment to {url}",
            source="synchronizer",
            metadata=ActivityEventMetadata(
                endpoint=url,
                pod_name=pod_name,
            ),
        )

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
                return {
                    "method": "skipped",
                    "version": "unchanged",
                    "reload_triggered": False,
                    "reload_id": None,
                }
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
                    return {
                        "method": "structured",
                        "version": deploy_result["version"],
                        "reload_triggered": deploy_result["reload_triggered"],
                        "reload_id": deploy_result.get("reload_id"),
                    }
                except DataplaneAPIError as structured_error:
                    # If structured deployment fails, fall back to raw deployment
                    logger.warning(
                        f"⚠️  Structured deployment failed for {url}, falling back to raw: {structured_error}"
                    )

                    # Record structured deployment failure metrics
                    metrics = get_metrics_collector()
                    metrics.increment_dataplane_fallback("structured_to_raw")

                    deploy_result = await client.deploy_configuration(config)
                    return {
                        "method": "raw_fallback",
                        "version": deploy_result["version"],
                        "reload_triggered": deploy_result["reload_triggered"],
                        "reload_id": deploy_result.get("reload_id"),
                    }

        except Exception as fetch_error:
            # Fallback to conditional deployment if structured comparison fails
            logger.warning(
                f"⚠️  Structured comparison failed for {url}, falling back to conditional: {fetch_error}"
            )

            # Record fallback metrics
            metrics = get_metrics_collector()
            metrics.increment_dataplane_fallback("structured_to_conditional")

            try:
                deploy_result = await client.deploy_configuration_conditionally(config)
                return {
                    "method": "conditional",
                    "version": deploy_result["version"],
                    "reload_triggered": deploy_result["reload_triggered"],
                    "reload_id": deploy_result.get("reload_id"),
                }
            except Exception as conditional_error:
                # Final fallback to regular deployment
                logger.warning(
                    f"⚠️  Conditional deployment also failed for {url}, using regular deployment: {conditional_error}"
                )

                # Record double fallback metrics
                metrics.increment_dataplane_fallback("conditional_to_regular")

                deploy_result = await client.deploy_configuration(config)
                return {
                    "method": "fallback",
                    "version": deploy_result["version"],
                    "reload_triggered": deploy_result["reload_triggered"],
                    "reload_id": deploy_result.get("reload_id"),
                }

    def _handle_deployment_error(
        self, url: str, error: Exception, config: str, results: Dict[str, Any]
    ) -> None:
        """Handle deployment error with enhanced logging."""
        # Get pod name for this URL
        pod_name = self.url_to_pod_name.get(url)

        # Record deployment failure event
        self.activity_buffer.add_event_sync(
            EventType.DEPLOYMENT_FAILED,
            f"Deployment failed to {url}: {str(error)[:100]}",
            source="synchronizer",
            metadata=ActivityEventMetadata(
                endpoint=url,
                version="unknown",
                error=str(error),
                pod_name=pod_name,
            ),
        )
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
            raise DataplaneAPIError("No rendered HAProxy configuration available")

        config = config_context.rendered_config.content
        maps_to_sync, certificates_to_sync, acls_to_sync, files_to_sync = (
            self._prepare_sync_content(config_context)
        )

        # Compute template hashes for deployment history tracking
        _ = self._compute_template_hashes(config_context)

        # Update production clients to handle dynamic URL changes
        self._update_production_clients(self.production_urls)

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
        validation_structured = await validation_client.fetch_structured_configuration()

        # Step 3: Deploy to production instances using structured comparison
        results: Dict[str, Any] = {
            "successful": 0,
            "failed": 0,
            "skipped": 0,
            "errors": [],
        }

        logger.debug(
            f"🚀 Deploying to {len(self.production_urls)} production instances"
        )

        # Create deployment tasks for parallel execution
        deployment_tasks = []
        for url in self.production_urls:
            task = self._deploy_to_single_instance(
                url,
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

        # Process results
        for url, result in zip(self.production_urls, deployment_results):
            if isinstance(result, Exception):
                # Task failed with exception
                self._handle_deployment_error(url, result, config, results)
            elif isinstance(result, dict):
                # Successful result
                if result["method"] == "skipped":
                    results["skipped"] += 1
                else:
                    results["successful"] += 1

                    method_emojis = {
                        "structured": "🏗️",
                        "conditional": "✅",
                        "raw_fallback": "🔄",
                        "fallback": "🔄",
                    }
                    method_emoji = method_emojis.get(result["method"], "✅")
                    pod_info = self._extract_pod_info_from_url(url)
                    logger.info(
                        f"{method_emoji} Deployed to {pod_info['pod_name']} ({url}) ({result['method']}), version: {result['version']}"
                    )

                # Use actual reload information from dataplane API response
                reload_triggered = result.get("reload_triggered", False)
                reload_id = result.get("reload_id")

                logger.debug(
                    f"🔍 Processing deployment result for {url}: reload_triggered={reload_triggered}, "
                    f"reload_id={reload_id}, method={result.get('method')}, version={result.get('version')}"
                )

                # Get activity buffer and pod info for all deployment events
                activity_buffer = get_activity_buffer()
                pod_info = self._extract_pod_info_from_url(url)

                # Emit activity events for all deployment types
                if result["method"] == "skipped":
                    # Configuration unchanged - emit INFO event (no last_update change)
                    activity_buffer.add_event_sync(
                        EventType.INFO,
                        f"Configuration unchanged on {pod_info['pod_name']} ({url})",
                        source="dataplane",
                        metadata=ActivityEventMetadata(
                            endpoint=url,
                            pod_ip=pod_info["pod_ip"],
                            pod_name=pod_info["pod_name"],
                            version=result["version"],
                        ),
                    )
                    logger.debug(
                        f"ℹ️  Configuration unchanged on {pod_info['pod_name']} ({url})"
                    )
                else:
                    # Configuration was deployed - emit SYNC event (updates last_update)
                    activity_buffer.add_event_sync(
                        EventType.SYNC,
                        f"Configuration updated on {pod_info['pod_name']} ({url}) ({result['method']})",
                        source="dataplane",
                        metadata=ActivityEventMetadata(
                            endpoint=url,
                            pod_ip=pod_info["pod_ip"],
                            pod_name=pod_info["pod_name"],
                            version=result["version"],
                        ),
                    )
                    logger.debug(
                        f"🔄 Configuration updated on {pod_info['pod_name']} ({url}) using {result['method']}"
                    )

                # Additionally emit RELOAD event for reloads (provides extra detail)
                if reload_triggered:
                    logger.debug(
                        f"🚀 Emitting additional RELOAD activity event for {pod_info['pod_name']} ({url}) with reload_id={reload_id}"
                    )

                    activity_buffer.add_event_sync(
                        EventType.RELOAD,
                        f"HAProxy process reloaded on {pod_info['pod_name']} ({url})",
                        source="dataplane",
                        metadata=ActivityEventMetadata(
                            endpoint=url,
                            pod_ip=pod_info["pod_ip"],
                            pod_name=pod_info["pod_name"],
                            version=result["version"],
                        ),
                    )
                    logger.debug(
                        f"✅ Successfully emitted RELOAD activity event for {pod_info['pod_name']} ({url})"
                    )

                # Get pod name for this URL
                pod_name = self.url_to_pod_name.get(url)

                # Record deployment success event
                self.activity_buffer.add_event_sync(
                    EventType.DEPLOYMENT_SUCCESS,
                    f"Deployment successful to {url} (version: {result['version']})",
                    source="synchronizer",
                    metadata=ActivityEventMetadata(
                        endpoint=url,
                        version=result["version"],
                        pod_name=pod_name,
                    ),
                )
            else:
                # Unexpected result type
                error_msg = f"Unexpected result type from deployment: {type(result)}"
                self._handle_deployment_error(
                    url, Exception(error_msg), config, results
                )

        # Enhanced logging with skip information
        total_instances = len(self.production_urls)
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

        return results

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

            # Use actual pod name from mapping if available, otherwise fallback to IP-based name
            pod_name = self.url_to_pod_name.get(url, f"pod-{pod_ip.replace('.', '-')}")

            return {"pod_ip": pod_ip, "pod_name": pod_name}

        except Exception as e:
            logger.debug(f"Error extracting pod info from URL {url}: {e}")
            return {"pod_ip": "unknown", "pod_name": "unknown"}
