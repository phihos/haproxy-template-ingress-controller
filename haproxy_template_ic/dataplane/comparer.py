"""
HAProxy Configuration Comparer.

This module provides the ConfigComparer class for detailed comparison of HAProxy
configurations and generating structured change lists for deployment.
"""

import logging
from typing import Any

from .types import (
    ConfigChange,
    ConfigChangeType,
    ConfigElementType,
    ConfigSectionType,
)
from .utils import _to_dict_safe, natural_sort_key

# Section elements registry defining nested elements each section supports
_SECTION_ELEMENTS = {
    ConfigSectionType.BACKEND: [
        ("servers", ConfigElementType.SERVER, True),  # Named elements
        ("http_request_rules", ConfigElementType.HTTP_REQUEST_RULE, False),  # Ordered
        ("http_response_rules", ConfigElementType.HTTP_RESPONSE_RULE, False),  # Ordered
        ("acls", ConfigElementType.ACL, False),  # Ordered
        ("filters", ConfigElementType.FILTER, False),  # Ordered
        ("log_targets", ConfigElementType.LOG_TARGET, False),  # Ordered
    ],
    ConfigSectionType.FRONTEND: [
        ("binds", ConfigElementType.BIND, True),  # Named elements
        ("http_request_rules", ConfigElementType.HTTP_REQUEST_RULE, False),  # Ordered
        ("http_response_rules", ConfigElementType.HTTP_RESPONSE_RULE, False),  # Ordered
        (
            "backend_switching_rules",
            ConfigElementType.BACKEND_SWITCHING_RULE,
            False,
        ),  # Ordered
        ("acls", ConfigElementType.ACL, False),  # Ordered
        ("filters", ConfigElementType.FILTER, False),  # Ordered
        ("log_targets", ConfigElementType.LOG_TARGET, False),  # Ordered
    ],
    ConfigSectionType.GLOBAL: [
        ("log_targets", ConfigElementType.LOG_TARGET, False),  # Ordered
    ],
}

logger = logging.getLogger(__name__)


class ConfigComparer:
    """Configuration comparer for generating structured change lists."""

    def compare_structured_configs(
        self, current: dict[str, Any], new: dict[str, Any]
    ) -> list[ConfigChange]:
        """Compare two structured configurations and return a list of changes.

        Args:
            current: Current configuration dictionary
            new: New configuration dictionary

        Returns:
            List of ConfigChange objects representing differences
        """
        changes: list[ConfigChange] = []

        # Compare backends and frontends (named sections)
        if self._compare_backends_and_frontends(current, new, changes):
            # At least one backend or frontend changed
            logger.debug("📊 Found changes in backends or frontends")

        # Compare flat ACL structures that come from fetch_structured_configuration
        self._compare_flat_acl_structures(current, new, changes)

        # Compare defaults sections (list of sections)
        self._compare_defaults_sections(current, new, changes)

        # Compare other named section types
        other_named_sections = [
            (ConfigSectionType.USERLIST, "userlists"),
            (ConfigSectionType.CACHE, "caches"),
            (ConfigSectionType.MAILERS, "mailers"),
            (ConfigSectionType.RESOLVER, "resolvers"),
            (ConfigSectionType.PEER, "peers"),
            (ConfigSectionType.FCGI_APP, "fcgi_apps"),
            (ConfigSectionType.HTTP_ERRORS, "http_errors"),
            (ConfigSectionType.RING, "rings"),
            (ConfigSectionType.LOG_FORWARD, "log_forwards"),
            (ConfigSectionType.PROGRAM, "programs"),
        ]

        for section_type, config_key in other_named_sections:
            # Handle both list and dict formats
            current_sections = current.get(config_key, [])
            new_sections = new.get(config_key, [])

            # Convert to dict format if they're lists
            if isinstance(current_sections, list):
                current_sections = self._list_to_dict_by_name(current_sections)
            if isinstance(new_sections, list):
                new_sections = self._list_to_dict_by_name(new_sections)

            if self._compare_named_config_sections(
                current_sections,
                new_sections,
                section_type,
                changes,
            ):
                logger.debug(f"📊 Found changes in {config_key}")

        # Compare global section
        self._compare_global_section(current, new, changes)

        logger.debug(f"📊 Total configuration changes found: {len(changes)}")
        return changes

    def _compare_flat_acl_structures(
        self, current: dict[str, Any], new: dict[str, Any], changes: list[ConfigChange]
    ) -> None:
        """Compare flat ACL structures returned by fetch_structured_configuration.

        The system returns ACLs in flat structures like:
        - frontend_acls: {frontend_name: [acl_objects]}
        - backend_acls: {backend_name: [acl_objects]}
        """
        # Compare frontend ACLs
        current_frontend_acls = current.get("frontend_acls", {})
        new_frontend_acls = new.get("frontend_acls", {})
        self._compare_flat_acls_for_section_type(
            current_frontend_acls,
            new_frontend_acls,
            ConfigSectionType.FRONTEND,
            changes,
        )

        # Compare backend ACLs
        current_backend_acls = current.get("backend_acls", {})
        new_backend_acls = new.get("backend_acls", {})
        self._compare_flat_acls_for_section_type(
            current_backend_acls, new_backend_acls, ConfigSectionType.BACKEND, changes
        )

    def _compare_flat_acls_for_section_type(
        self,
        current_acls: dict[str, Any],
        new_acls: dict[str, Any],
        section_type: ConfigSectionType,
        changes: list[ConfigChange],
    ) -> None:
        """Compare flat ACL structures for a specific section type."""
        all_section_names = set(current_acls.keys()) | set(new_acls.keys())

        for section_name in sorted(all_section_names, key=natural_sort_key):
            current_section_acls = current_acls.get(section_name, [])
            new_section_acls = new_acls.get(section_name, [])

            # Compare the ACL lists using ordered comparison (since ACLs have order significance)
            self._compare_by_order(
                current_section_acls,
                new_section_acls,
                section_type,
                section_name,
                ConfigElementType.ACL,
                changes,
            )

    def _compare_backends_and_frontends(
        self, current: dict[str, Any], new: dict[str, Any], changes: list[ConfigChange]
    ) -> bool:
        """Compare backends and frontends sections."""
        changes_found = False

        # Convert list format to dict format for comparison
        current_backends = self._list_to_dict_by_name(current.get("backends", []))
        new_backends = self._list_to_dict_by_name(new.get("backends", []))

        current_frontends = self._list_to_dict_by_name(current.get("frontends", []))
        new_frontends = self._list_to_dict_by_name(new.get("frontends", []))

        if self._compare_named_section_type(
            current_backends,
            new_backends,
            ConfigSectionType.BACKEND,
            changes,
        ):
            changes_found = True

        if self._compare_named_section_type(
            current_frontends,
            new_frontends,
            ConfigSectionType.FRONTEND,
            changes,
        ):
            changes_found = True

        return changes_found

    def _list_to_dict_by_name(self, items: list[Any]) -> dict[str, Any]:
        """Convert a list of objects with 'name' attribute to a dict keyed by name."""
        result = {}
        for item in items:
            if hasattr(item, "name") and item.name:
                result[item.name] = item
        return result

    def _compare_named_section_type(
        self,
        current_sections: dict[str, Any],
        new_sections: dict[str, Any],
        section_type: ConfigSectionType,
        changes: list[ConfigChange],
    ) -> bool:
        """Compare sections of a specific type by name."""
        changes_found = False

        # Get all section names from both configs
        all_section_names = set(current_sections.keys()) | set(new_sections.keys())

        for section_name in sorted(all_section_names, key=natural_sort_key):
            current_section = current_sections.get(section_name)
            new_section = new_sections.get(section_name)

            # Determine change type and apply
            if current_section is None:
                # New section
                changes.append(
                    ConfigChange.create_section_change(
                        ConfigChangeType.CREATE,
                        section_type,
                        section_name,
                        new_config=new_section,
                    )
                )
                changes_found = True
            elif new_section is None:
                # Deleted section
                changes.append(
                    ConfigChange.create_section_change(
                        ConfigChangeType.DELETE,
                        section_type,
                        section_name,
                        old_config=current_section,
                    )
                )
                changes_found = True
            else:
                # Potentially modified section - delegate to section comparison
                section_changed = self._compare_section_configs(
                    current_section,
                    new_section,
                    section_type,
                    section_name,
                    changes,
                )
                if section_changed:
                    changes_found = True

        return changes_found

    def _compare_defaults_sections(
        self,
        current: dict[str, Any],
        new: dict[str, Any],
        changes: list[ConfigChange],
    ) -> None:
        """Compare defaults sections (which are indexed by order)."""
        current_defaults = current.get("defaults", [])
        new_defaults = new.get("defaults", [])

        # Handle case where current is empty (fresh deployment)
        if len(current_defaults) == 0 and len(new_defaults) > 0:
            # Create all new defaults sections
            for idx, defaults_config in enumerate(new_defaults):
                changes.append(
                    ConfigChange.create_section_change(
                        ConfigChangeType.CREATE,
                        ConfigSectionType.DEFAULTS,
                        f"defaults_{idx}",
                        new_config=defaults_config,
                        section_index=idx,
                    )
                )
        # Handle case where we're removing all defaults sections
        elif len(current_defaults) > 0 and len(new_defaults) == 0:
            # Delete all old defaults sections (in reverse order)
            for idx in range(len(current_defaults) - 1, -1, -1):
                changes.append(
                    ConfigChange.create_section_change(
                        ConfigChangeType.DELETE,
                        ConfigSectionType.DEFAULTS,
                        f"defaults_{idx}",
                        old_config=current_defaults[idx],
                        section_index=idx,
                    )
                )
        # Handle case where counts are different (need to replace all)
        elif len(current_defaults) != len(new_defaults):
            # Delete all old defaults sections (in reverse order)
            for idx in range(len(current_defaults) - 1, -1, -1):
                changes.append(
                    ConfigChange.create_section_change(
                        ConfigChangeType.DELETE,
                        ConfigSectionType.DEFAULTS,
                        f"defaults_{idx}",
                        old_config=current_defaults[idx],
                        section_index=idx,
                    )
                )

            # Create all new defaults sections
            for idx, defaults_config in enumerate(new_defaults):
                changes.append(
                    ConfigChange.create_section_change(
                        ConfigChangeType.CREATE,
                        ConfigSectionType.DEFAULTS,
                        f"defaults_{idx}",
                        new_config=defaults_config,
                        section_index=idx,
                    )
                )
        else:
            # Same count - compare each defaults section
            # For defaults sections, we need to be careful about CREATE vs UPDATE
            # If the current section is "empty" (indicating it doesn't really exist),
            # use CREATE instead of UPDATE
            for idx, (current_defaults_section, new_defaults_section) in enumerate(
                zip(current_defaults, new_defaults)
            ):
                current_dict = _to_dict_safe(current_defaults_section)

                # Check if current section is effectively empty (doesn't really exist)
                # This can happen when fetch_structured_configuration returns placeholder data
                is_current_empty = (
                    not current_dict
                    or len(current_dict) == 0
                    or (
                        len(current_dict) == 1 and "name" in current_dict
                    )  # Only has name field
                )

                if is_current_empty:
                    # Current section doesn't really exist, use CREATE
                    changes.append(
                        ConfigChange.create_section_change(
                            ConfigChangeType.CREATE,
                            ConfigSectionType.DEFAULTS,
                            f"defaults_{idx}",
                            new_config=new_defaults_section,
                            section_index=idx,
                        )
                    )
                    logger.debug(
                        f"📊 Creating defaults section {idx} (current was empty)"
                    )
                else:
                    # Normal comparison for existing sections
                    section_changed = self._compare_section_configs(
                        current_defaults_section,
                        new_defaults_section,
                        ConfigSectionType.DEFAULTS,
                        f"defaults_{idx}",
                        changes,
                        section_index=idx,
                    )

                    if section_changed:
                        logger.debug(f"📊 Found changes in defaults section {idx}")

    def _compare_section_configs(
        self,
        current_section: dict[str, Any],
        new_section: dict[str, Any],
        section_type: ConfigSectionType,
        section_name: str,
        changes: list[ConfigChange],
        section_index: int | None = None,
    ) -> bool:
        """Compare two section configurations and detect changes.

        Returns True if changes were found, False otherwise.
        """
        changes_before = len(changes)

        # Convert to dict format if needed
        current_dict = _to_dict_safe(current_section)
        new_dict = _to_dict_safe(new_section)

        # Ensure we have dictionaries for nested element comparison
        if not isinstance(current_dict, dict):
            current_dict = {}
        if not isinstance(new_dict, dict):
            new_dict = {}

        # Compare nested elements first
        if section_type in _SECTION_ELEMENTS:
            self._compare_nested_elements(
                current_dict, new_dict, section_type, section_name, changes
            )

        # Check if main section properties changed (excluding nested elements)
        main_props_changed = self._section_main_properties_changed(
            current_dict, new_dict, section_type
        )

        if main_props_changed:
            # Update the section itself
            changes.append(
                ConfigChange.create_section_change(
                    ConfigChangeType.UPDATE,
                    section_type,
                    section_name,
                    new_config=new_section,
                    old_config=current_section,
                    section_index=section_index,
                )
            )

        return len(changes) > changes_before

    def _section_main_properties_changed(
        self,
        current_dict: dict[str, Any],
        new_dict: dict[str, Any],
        section_type: ConfigSectionType,
    ) -> bool:
        """Check if main section properties changed (excluding nested elements)."""
        # Get list of nested element keys to exclude from main comparison
        nested_keys = set()
        if section_type in _SECTION_ELEMENTS:
            for element_key, _, _ in _SECTION_ELEMENTS[section_type]:
                nested_keys.add(element_key)

        # Compare only non-nested properties
        for key in set(current_dict.keys()) | set(new_dict.keys()):
            if key in nested_keys:
                continue  # Skip nested elements

            current_value = current_dict.get(key)
            new_value = new_dict.get(key)

            if current_value != new_value:
                return True

        return False

    def _compare_nested_elements(
        self,
        current_nested: dict[str, Any],
        new_nested: dict[str, Any],
        section_type: ConfigSectionType,
        section_name: str,
        changes: list[ConfigChange],
    ) -> None:
        """Compare all nested elements within a section.

        This method compares nested configuration elements like servers, ACLs,
        HTTP request rules, etc. within backends, frontends, and defaults sections.

        Args:
            current_nested: Current section configuration as dict
            new_nested: New section configuration as dict
            section_type: Type of the parent section
            section_name: Name of the parent section
            changes: List to append ConfigChange objects to
        """
        if section_type not in _SECTION_ELEMENTS:
            return

        for element_key, element_type, is_named in _SECTION_ELEMENTS[section_type]:
            current_elements = current_nested.get(
                element_key, [] if not is_named else {}
            )
            new_elements = new_nested.get(element_key, [] if not is_named else {})

            self._compare_element_list(
                current_elements,
                new_elements,
                section_type,
                section_name,
                element_type,
                is_named,
                changes,
            )

    def _compare_element_list(
        self,
        current_elements: list[Any] | dict[str, Any],
        new_elements: list[Any] | dict[str, Any],
        section_type: ConfigSectionType,
        section_name: str,
        element_type: ConfigElementType,
        is_named: bool,
        changes: list[ConfigChange],
    ) -> None:
        """Compare a list or dict of elements and generate appropriate changes."""
        if is_named:
            # Named elements (like servers, binds) - use dict comparison
            self._compare_by_name(
                current_elements if isinstance(current_elements, dict) else {},
                new_elements if isinstance(new_elements, dict) else {},
                section_type,
                section_name,
                element_type,
                changes,
            )
        else:
            # Ordered elements (like rules, ACLs) - use list comparison
            self._compare_by_order(
                current_elements if isinstance(current_elements, list) else [],
                new_elements if isinstance(new_elements, list) else [],
                section_type,
                section_name,
                element_type,
                changes,
            )

    def _compare_by_name(
        self,
        current_elements: dict[str, Any],
        new_elements: dict[str, Any],
        section_type: ConfigSectionType,
        section_name: str,
        element_type: ConfigElementType,
        changes: list[ConfigChange],
    ) -> None:
        """Compare named elements and generate appropriate changes."""
        all_element_names = set(current_elements.keys()) | set(new_elements.keys())

        for element_name in sorted(all_element_names, key=natural_sort_key):
            current_element = current_elements.get(element_name)
            new_element = new_elements.get(element_name)

            if current_element is None:
                # New element
                changes.append(
                    ConfigChange.create_element_change(
                        ConfigChangeType.CREATE,
                        section_type,
                        section_name,
                        element_type,
                        new_config=new_element,
                        element_id=element_name,
                    )
                )
            elif new_element is None:
                # Deleted element
                changes.append(
                    ConfigChange.create_element_change(
                        ConfigChangeType.DELETE,
                        section_type,
                        section_name,
                        element_type,
                        old_config=current_element,
                        element_id=element_name,
                    )
                )
            elif current_element != new_element:
                # Modified element
                changes.append(
                    ConfigChange.create_element_change(
                        ConfigChangeType.UPDATE,
                        section_type,
                        section_name,
                        element_type,
                        new_config=new_element,
                        old_config=current_element,
                        element_id=element_name,
                    )
                )

    def _compare_by_order(
        self,
        current_elements: list[Any],
        new_elements: list[Any],
        section_type: ConfigSectionType,
        section_name: str,
        element_type: ConfigElementType,
        changes: list[ConfigChange],
    ) -> None:
        """Compare ordered elements and generate appropriate changes.

        For ordered elements like HTTP rules and ACLs, we need to consider
        both element content and position. The strategy is:
        1. Delete all old elements (in reverse order to avoid index shifts)
        2. Create all new elements (in forward order)

        This ensures that the final order matches exactly without complex
        position tracking.
        """
        # If lists are identical, no changes needed
        if current_elements == new_elements:
            return

        # Delete all current elements (in reverse order to avoid index issues)
        for idx in range(len(current_elements) - 1, -1, -1):
            changes.append(
                ConfigChange.create_element_change(
                    ConfigChangeType.DELETE,
                    section_type,
                    section_name,
                    element_type,
                    old_config=current_elements[idx],
                    element_index=idx,
                )
            )

        # Create all new elements (in forward order)
        for idx, element in enumerate(new_elements):
            changes.append(
                ConfigChange.create_element_change(
                    ConfigChangeType.CREATE,
                    section_type,
                    section_name,
                    element_type,
                    new_config=element,
                    element_index=idx,
                )
            )

    def _safe_compare_sections(
        self,
        current_sections: Any,
        new_sections: Any,
        section_type: ConfigSectionType,
        changes: list[ConfigChange],
        compare_impl: Any,
    ) -> bool:
        """Safely compare sections with error handling."""
        try:
            return compare_impl(current_sections, new_sections, section_type, changes)
        except Exception as e:
            logger.warning(
                f"Error comparing {section_type.value} sections: {e}. "
                "Skipping comparison for this section type."
            )
            return False

    def _compare_named_sections_impl(
        self,
        current_sections: dict[str, Any],
        new_sections: dict[str, Any],
        section_type: ConfigSectionType,
        changes: list[ConfigChange],
    ) -> bool:
        """Implementation for comparing named sections."""
        return self._compare_named_section_type(
            current_sections, new_sections, section_type, changes
        )

    def _compare_list_sections_impl(
        self,
        current_sections: list[Any],
        new_sections: list[Any],
        section_type: ConfigSectionType,
        changes: list[ConfigChange],
    ) -> bool:
        """Implementation for comparing list-based sections."""
        # This could be expanded for other list-based sections if needed
        return False

    def _compare_named_config_sections(
        self,
        current_sections: dict[str, Any],
        new_sections: dict[str, Any],
        section_type: ConfigSectionType,
        changes: list[ConfigChange],
    ) -> bool:
        """Compare named configuration sections with error handling."""
        if self._safe_compare_sections(
            current_sections,
            new_sections,
            section_type,
            changes,
            self._compare_named_sections_impl,
        ):
            return True
        return False

    def _compare_list_config_sections(
        self,
        current_sections: list[Any],
        new_sections: list[Any],
        section_type: ConfigSectionType,
        changes: list[ConfigChange],
    ) -> bool:
        """Compare list-based configuration sections with error handling."""
        if self._safe_compare_sections(
            current_sections,
            new_sections,
            section_type,
            changes,
            self._compare_list_sections_impl,
        ):
            return True
        return False

    def _compare_global_section(
        self,
        current: dict[str, Any],
        new: dict[str, Any],
        changes: list[ConfigChange],
    ) -> None:
        """Compare global section configuration."""
        current_global = current.get("global", {})
        new_global = new.get("global", {})

        if current_global != new_global:
            self._compare_section_configs(
                current_global,
                new_global,
                ConfigSectionType.GLOBAL,
                "global",
                changes,
            )
