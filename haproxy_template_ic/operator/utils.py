"""
Utility functions for the Kubernetes operator.

This module provides operator-specific utilities for namespace detection,
memo object handling, and configuration management.
"""

import logging
import os
from typing import Any, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from haproxy_template_ic.activity import ActivityBuffer

from haproxy_template_ic.constants import NAMESPACE_FILE_PATH

logger = logging.getLogger(__name__)

__all__ = [
    "get_current_namespace",
    "trigger_reload",
    "get_memo_activity_buffer",
    "get_memo_attr_safe",
    "has_memo_attr",
    "get_effective_namespace",
]


def get_memo_activity_buffer(memo: Any) -> Optional["ActivityBuffer"]:
    """Get activity buffer from memo if available.

    Args:
        memo: Kopf memo object

    Returns:
        ActivityBuffer if available and valid, None otherwise
    """
    if hasattr(memo, "activity_buffer") and memo.activity_buffer:
        return memo.activity_buffer
    return None


def get_current_namespace() -> str:
    """Get the current Kubernetes namespace.

    Returns:
        The current namespace string, defaulting to "default" if not determinable
    """
    namespace = os.environ.get("POD_NAMESPACE", "").strip()
    if namespace:
        logger.debug(f"🏷️ Current namespace from env: {namespace}")
        return namespace

    try:
        with open(NAMESPACE_FILE_PATH, "r", encoding="utf-8") as f:
            namespace = f.read().strip()
            if namespace:
                logger.debug(f"🏷️ Current namespace: {namespace}")
                return namespace
    except (FileNotFoundError, IOError) as e:
        logger.debug(f"Could not read namespace from {NAMESPACE_FILE_PATH}: {e}")

    # Fallback to environment variable

    # Try kubeconfig context
    try:
        from kubernetes import config

        contexts, active_context = config.list_kube_config_contexts()
        namespace = active_context["context"].get("namespace", "default")
        if isinstance(namespace, str) and namespace:
            logger.debug(f"🏷️ Current namespace from kubeconfig: {namespace}")
            return namespace
    except (KeyError, TypeError, Exception) as e:
        logger.debug(f"Could not get namespace from kubeconfig: {e}")

    # Default fallback
    logger.debug("🏷️ Using default namespace")
    return "default"


def trigger_reload(memo: Any) -> None:
    """Trigger configuration reload by setting flags on the memo object.

    This function sets the reload flags that signal the operator to reload
    the configuration. It's typically called when ConfigMap changes are detected.

    Args:
        memo: The kopf memo object containing config_reload_flag and stop_flag
    """
    logger.debug("Triggering configuration reload")

    # Set the reload flag if it exists
    if hasattr(memo, "config_reload_flag"):
        memo.config_reload_flag.set_result(None)
        logger.debug("Set config_reload_flag")

    # Set the stop flag if it exists
    if hasattr(memo, "stop_flag"):
        memo.stop_flag.set_result(None)
        logger.debug("Set stop_flag")


# Memo utility functions for common patterns
def get_memo_attr_safe(memo: Any, attr_name: str, default: Any = None) -> Any:
    """
    Safely get an attribute from memo with default fallback.

    Args:
        memo: Memo object to check
        attr_name: Attribute name to retrieve
        default: Default value if attribute doesn't exist or is None/falsy

    Returns:
        Attribute value or default
    """
    if hasattr(memo, attr_name):
        value = getattr(memo, attr_name)
        if value is not None:
            return value
    return default


def has_memo_attr(memo: Any, attr_name: str) -> bool:
    """
    Check if memo has a non-None attribute.

    Args:
        memo: Memo object to check
        attr_name: Attribute name to check

    Returns:
        True if attribute exists and is not None
    """
    return hasattr(memo, attr_name) and getattr(memo, attr_name) is not None


def get_effective_namespace(memo: Any = None) -> str:
    """
    Get the effective namespace from various sources with proper fallback chain.

    This consolidates the common pattern of namespace detection from:
    1. Memo object (if provided)
    2. Environment variables (POD_NAMESPACE)
    3. Service account namespace file
    4. Default fallback

    Args:
        memo: Optional memo object to check for namespace

    Returns:
        Effective namespace string
    """
    # Try memo first if provided
    if memo:
        if hasattr(memo, "namespace") and memo.namespace:
            return memo.namespace
        if (
            hasattr(memo, "config")
            and memo.config
            and hasattr(memo.config, "namespace")
            and memo.config.namespace
        ):
            return memo.config.namespace

    # Try environment variable
    namespace = os.environ.get("POD_NAMESPACE")
    if namespace:
        return namespace

    # Try service account namespace file
    try:
        with open("/var/run/secrets/kubernetes.io/serviceaccount/namespace", "r") as f:
            namespace = f.read().strip()
            if namespace:
                return namespace
    except Exception as e:
        logger.debug(f"Failed to read namespace from service account: {e}")

    return "unknown"
