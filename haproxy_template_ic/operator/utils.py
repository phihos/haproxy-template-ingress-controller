"""
Utility functions for the Kubernetes operator.

This module re-exports utilities from the k8s package while maintaining
operator-specific behavior and error handling.
"""

import logging
import os
from typing import Any, Dict

from haproxy_template_ic.constants import NAMESPACE_FILE_PATH
from haproxy_template_ic.k8s import (
    _compile_jsonpath as k8s_compile_jsonpath,
    _is_valid_dict_resource as k8s_is_valid_dict_resource,
    _is_valid_sequence_resource as k8s_is_valid_sequence_resource,
    _is_valid_object_resource as k8s_is_valid_object_resource,
    _is_valid_resource as k8s_is_valid_resource,
    extract_nested_field as k8s_extract_nested_field,
)

logger = logging.getLogger(__name__)

__all__ = [
    "get_current_namespace",
    "extract_nested_field",
    "trigger_reload",
    "_compile_jsonpath",
    "_is_valid_resource",
    "_is_valid_dict_resource",
    "_is_valid_sequence_resource",
    "_is_valid_object_resource",
]


def get_current_namespace() -> str:
    """Get the current Kubernetes namespace.

    Returns:
        The current namespace string, defaulting to "default" if not determinable
    """
    # Try mounted service account token first
    try:
        with open(NAMESPACE_FILE_PATH, "r", encoding="utf-8") as f:
            namespace = f.read().strip()
            if namespace:
                logger.debug(f"🏷️ Current namespace: {namespace}")
                return namespace
    except (FileNotFoundError, IOError) as e:
        logger.debug(f"Could not read namespace from {NAMESPACE_FILE_PATH}: {e}")

    # Fallback to environment variable
    namespace = os.environ.get("POD_NAMESPACE", "").strip()
    if namespace:
        logger.debug(f"🏷️ Current namespace from env: {namespace}")
        return namespace

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


def extract_nested_field(obj: Dict[str, Any], path: str) -> str:
    """Extract nested field from object using JSONPath with error handling.

    This operator-specific version provides detailed logging and string conversion
    that differs slightly from the k8s package version.

    Args:
        obj: The object to extract from (typically a Kubernetes resource)
        path: JSONPath expression (e.g., "metadata.name", "spec.rules[0].host")

    Returns:
        String representation of the extracted value, or empty string if not found

    Example:
        >>> resource = {"metadata": {"name": "test"}, "spec": {"port": 80}}
        >>> extract_nested_field(resource, "metadata.name")
        'test'
        >>> extract_nested_field(resource, "spec.port")
        '80'
        >>> extract_nested_field(resource, "missing.field")
        ''
    """
    if not obj or not isinstance(obj, dict):
        logger.debug(f"Invalid object for field extraction: {type(obj)}")
        return ""

    if not path:
        logger.debug("Empty path provided for field extraction")
        return ""

    try:
        # Use the k8s package implementation but convert result to string
        result = k8s_extract_nested_field(obj, path)

        # Ensure we return string (k8s version may return Any)
        if result is None:
            return ""
        elif isinstance(result, (str, int, float, bool)):
            return str(result)
        else:
            logger.debug(f"Complex value extracted for path '{path}': {type(result)}")
            return str(result)

    except Exception as e:
        logger.warning(f"Unexpected error extracting field '{path}': {e}")
        return ""


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


# Re-export the k8s package functions directly for these
_compile_jsonpath = k8s_compile_jsonpath
_is_valid_dict_resource = k8s_is_valid_dict_resource
_is_valid_sequence_resource = k8s_is_valid_sequence_resource
_is_valid_object_resource = k8s_is_valid_object_resource
_is_valid_resource = k8s_is_valid_resource
