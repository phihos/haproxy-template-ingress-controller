"""
Core validation utilities for HAProxy Template IC.

This module provides reusable validation functions that are used across
different parts of the application to reduce duplication and ensure
consistent validation behavior.
"""

from typing import Any


def has_valid_attr(obj: Any, attr_name: str) -> bool:
    """Check if object has a non-None attribute that evaluates to True.

    This consolidates the common pattern of checking both attribute existence
    and truthiness: `hasattr(obj, attr_name) and getattr(obj, attr_name)`

    Args:
        obj: Object to check
        attr_name: Attribute name to check

    Returns:
        True if object has the attribute and it's truthy, False otherwise
    """
    return hasattr(obj, attr_name) and bool(getattr(obj, attr_name, None))


def has_valid_nested_attr(obj: Any, *attr_path: str) -> bool:
    """Check if object has valid nested attributes following a path.

    This consolidates patterns like:
    `hasattr(obj, "config") and obj.config and hasattr(obj.config, "watched_resources")`

    Args:
        obj: Object to check
        *attr_path: Sequence of attribute names to traverse

    Returns:
        True if all attributes in the path exist and are truthy, False otherwise

    Example:
        >>> has_valid_nested_attr(memo, "config", "watched_resources")
        # Equivalent to: hasattr(memo, "config") and memo.config and hasattr(memo.config, "watched_resources")
    """
    current_obj = obj
    for attr_name in attr_path:
        if not has_valid_attr(current_obj, attr_name):
            return False
        current_obj = getattr(current_obj, attr_name)
    return True


def get_safe_attr(obj: Any, attr_name: str, default: Any = None) -> Any:
    """Safely get an attribute with a default fallback.

    This consolidates patterns where we check for attribute existence
    before getting its value.

    Args:
        obj: Object to get attribute from
        attr_name: Attribute name to get
        default: Default value if attribute doesn't exist or is None

    Returns:
        Attribute value or default
    """
    if has_valid_attr(obj, attr_name):
        return getattr(obj, attr_name)
    return default


def get_safe_nested_attr(obj: Any, *attr_path: str, default: Any = None) -> Any:
    """Safely get a nested attribute with a default fallback.

    This consolidates patterns where we traverse a chain of attributes
    with safety checks at each level.

    Args:
        obj: Object to start traversal from
        *attr_path: Sequence of attribute names to traverse
        default: Default value if any attribute in the path fails

    Returns:
        Final attribute value or default

    Example:
        >>> get_safe_nested_attr(memo, "config", "watched_resources", default={})
        # Equivalent to safe traversal of memo.config.watched_resources
    """
    current_obj = obj
    for attr_name in attr_path:
        if not has_valid_attr(current_obj, attr_name):
            return default
        current_obj = getattr(current_obj, attr_name)
    return current_obj


def is_non_empty_dict(obj: Any) -> bool:
    """Check if object is a non-empty dictionary.

    Args:
        obj: Object to check

    Returns:
        True if object is a dict with at least one key, False otherwise
    """
    return isinstance(obj, dict) and len(obj) > 0


def is_non_empty_list(obj: Any) -> bool:
    """Check if object is a non-empty list.

    Args:
        obj: Object to check

    Returns:
        True if object is a list with at least one item, False otherwise
    """
    return isinstance(obj, list) and len(obj) > 0
