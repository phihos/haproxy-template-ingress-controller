"""
Kubernetes resource utilities for namespace detection and resource validation.

Contains utilities for working with Kubernetes resources including
namespace detection, JSONPath compilation, and resource validation.
"""

import logging
import os
from functools import lru_cache
from typing import Any, Dict, Optional

import jsonpath
from jsonpath.exceptions import JSONPathError

logger = logging.getLogger(__name__)


def get_current_namespace() -> str:
    """
    Get the current Kubernetes namespace from the service account token.

    Returns:
        Current namespace name, or "default" if not found
    """
    # First check environment variable for local development/testing
    env_namespace = os.environ.get("KUBERNETES_NAMESPACE")
    if env_namespace:
        return env_namespace

    # Then check service account namespace file for in-cluster operation
    namespace_path = "/var/run/secrets/kubernetes.io/serviceaccount/namespace"

    if os.path.exists(namespace_path):
        try:
            with open(namespace_path, "r") as f:
                namespace = f.read().strip()
                if namespace:
                    return namespace
        except Exception as e:
            logger.warning(f"Failed to read namespace from {namespace_path}: {e}")

    # Final fallback to default
    return "default"


@lru_cache(maxsize=256)
def _compile_jsonpath(expression: str) -> Any:
    """Compile and cache JSONPath expressions for performance."""
    try:
        return jsonpath.compile(expression)
    except JSONPathError as e:
        logger.warning(f"Invalid JSONPath expression '{expression}': {e}")
        raise


def extract_nested_field(resource: Dict[str, Any], field_path: str) -> Optional[Any]:
    """
    Extract a nested field from a resource using dot notation.

    Args:
        resource: The resource dictionary
        field_path: Dot-separated field path (e.g., "metadata.name")

    Returns:
        The field value or None if not found
    """
    try:
        # Convert dot notation to JSONPath and use cached compilation
        jsonpath_expr = f"$.{field_path}"
        compiled_path = _compile_jsonpath(jsonpath_expr)

        # Extract the value
        matches = compiled_path.findall(resource)
        return matches[0] if matches else None

    except Exception as e:
        logger.debug(f"Failed to extract field '{field_path}': {e}")
        return None


def _is_valid_resource(resource: Any) -> bool:
    """Check if a resource is valid (has required Kubernetes fields)."""
    try:
        return bool(resource.metadata.name)
    except AttributeError:
        return _is_valid_dict_resource(resource)


def _is_valid_dict_resource(resource: Any) -> bool:
    """Check if a dictionary resource is valid."""
    if not isinstance(resource, dict):
        return False

    metadata = resource.get("metadata", {})
    if not isinstance(metadata, dict):
        return False

    name = metadata.get("name", "")
    return bool(name.strip()) if isinstance(name, str) else False


def _is_valid_sequence_resource(resources: Any) -> bool:
    """Check if a sequence of resources contains valid items."""
    if not isinstance(resources, (list, tuple)):
        return False

    # At least one resource must be valid
    return any(_is_valid_resource(resource) for resource in resources)


def _is_valid_object_resource(resource: Any) -> bool:
    """Check if an object resource (with attributes) is valid."""
    try:
        # Check if it has kubernetes-like attributes
        return bool(
            resource.metadata and resource.kind and _is_valid_resource(resource)
        )
    except AttributeError:
        return False
