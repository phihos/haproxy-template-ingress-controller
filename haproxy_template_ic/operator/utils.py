"""
Utility functions for the Kubernetes operator.

This module provides operator-specific utilities for namespace detection,
memo object handling, and configuration management.
"""

import logging
import os

from kubernetes import config

from haproxy_template_ic.constants import NAMESPACE_FILE_PATH
from haproxy_template_ic.models.state import ApplicationState

logger = logging.getLogger(__name__)

__all__ = [
    "get_current_namespace",
    "trigger_reload",
]


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


def trigger_reload(memo: ApplicationState) -> None:
    """Trigger configuration reload by setting flags on the memo object.

    This function sets the reload flags that signal the operator to reload
    the configuration. It's typically called when ConfigMap changes are detected.

    Args:
        memo: The kopf memo object containing config_reload_flag and stop_flag
    """
    logger.debug("Triggering configuration reload")

    # Set the reload flag
    memo.runtime.config_reload_flag.set_result(None)
    logger.debug("Set config_reload_flag")

    # Set the stop flag
    memo.runtime.stop_flag.set_result(None)
    logger.debug("Set stop_flag")
