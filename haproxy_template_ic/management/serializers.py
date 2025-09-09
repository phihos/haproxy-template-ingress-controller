"""
Serialization utilities for management socket data.

This module provides utilities for converting complex internal data structures
into JSON-serializable dictionaries for the management socket interface.
"""

import logging
from typing import Any, Callable, Dict, Iterator, List, Protocol, Tuple, Union

from haproxy_template_ic.core.validation import has_valid_attr

logger = logging.getLogger(__name__)


class KopfIndexData(Protocol):
    """Protocol for Kopf index data structures.

    This protocol defines the interface for Kopf index data structures
    that can be iterated over and support item access by key.
    """

    def __iter__(self) -> Iterator[Any]:
        """Iterate over the index keys."""
        ...

    def __getitem__(self, key: Any) -> Union[Dict[str, Any], List[Dict[str, Any]]]:
        """Get resources by index key."""
        ...


ResourceDict = Dict[str, Any]
SerializationErrors = List[str]


def _serialize_resource_collection(resources: Any) -> List[ResourceDict]:
    """Convert resource collection to serializable list of resources."""
    result = []
    try:
        # Check if this is a plain dict (single resource) vs a resource collection
        if isinstance(resources, dict) and not any(
            isinstance(v, (list, dict)) for v in resources.values()
        ):
            # This looks like a single resource dict, not a collection
            result.append({"data": resources})
        elif hasattr(resources, "items"):
            # This is a resource collection (dict of resources)
            for key, resource_data in resources.items():
                if isinstance(resource_data, list):
                    result.extend(resource_data)
                else:
                    try:
                        if hasattr(resource_data, "__dict__"):
                            result.append(resource_data.__dict__)
                        elif isinstance(resource_data, dict):
                            result.append(resource_data)
                        else:
                            result.append({"data": resource_data})
                    except Exception:
                        result.append({"data": str(resource_data)})  # type: ignore[dict-item]
        elif hasattr(resources, "__iter__") and not isinstance(resources, (str, bytes)):
            for item in resources:
                if isinstance(item, dict):
                    result.append(item)
                elif hasattr(item, "__dict__"):
                    result.append(item.__dict__)
                else:
                    result.append(item)
        else:
            # Non-iterable types
            result.append({"data": resources})
    except Exception as e:
        logger.warning(f"Failed to serialize resource collection: {e}")
        # Return empty list on error
    return result


def _format_index_key(key: Any) -> str:
    """Format index key for serialization.

    Converts tuple keys to colon-separated strings for better readability.

    Args:
        key: Index key (could be tuple, string, or other type)

    Returns:
        Formatted string representation of the key
    """
    if isinstance(key, tuple):
        return ":".join(str(k) for k in key)
    else:
        return str(key)


def _serialize_kopf_index(index_data: KopfIndexData) -> Dict[str, List[ResourceDict]]:
    """Serialize kopf index data to a dictionary of resource lists.

    Args:
        index_data: Kopf index data structure

    Returns:
        Dictionary mapping index keys to resource lists
    """
    serialized = {}
    try:
        for key in index_data:
            try:
                resources = index_data[key]
                formatted_key = _format_index_key(key)
                if isinstance(resources, list):
                    serialized[formatted_key] = [dict(r) for r in resources]
                elif isinstance(resources, dict):
                    serialized[formatted_key] = [dict(resources)]
                else:
                    logger.warning(
                        f"Unexpected resource type for key {key}: {type(resources)}"
                    )
            except Exception as e:
                logger.warning(f"Failed to serialize resource at key {key}: {e}")
                continue
    except Exception as e:
        logger.warning(f"Failed to iterate over index data: {e}")
    return serialized


def _safe_serialize_object(
    obj: Any, max_depth: int = 10, current_depth: int = 0
) -> Any:
    """Safely serialize an object, handling circular references and complex types.

    Args:
        obj: Object to serialize
        max_depth: Maximum recursion depth
        current_depth: Current recursion depth

    Returns:
        Serializable representation of the object
    """
    if current_depth >= max_depth:
        return f"<max_depth_reached: {type(obj).__name__}>"

    if isinstance(obj, (str, int, float, bool)) or obj is None:
        return obj
    elif isinstance(obj, dict):
        return {
            k: _safe_serialize_object(v, max_depth, current_depth + 1)
            for k, v in obj.items()
        }
    elif isinstance(obj, (list, tuple)):
        return [
            _safe_serialize_object(item, max_depth, current_depth + 1) for item in obj
        ]
    elif hasattr(obj, "__dict__"):
        return _safe_serialize_object(obj.__dict__, max_depth, current_depth + 1)
    else:
        return str(obj)


def _serialize_memo_indices(
    memo: Any,
) -> Tuple[Dict[str, Dict[str, List[ResourceDict]]], SerializationErrors]:
    """Serialize all indices from a memo object.

    Args:
        memo: The memo object containing indices

    Returns:
        Tuple of (indices_dict, error_list)
    """
    indices = {}
    errors = []

    if has_valid_attr(memo, "indices"):
        for name, index_data in memo.indices.items():
            try:
                indices[name] = _serialize_kopf_index(index_data)
            except (TypeError, ValueError, AttributeError) as e:
                errors.append(f"index '{name}' serialization: {e}")

    return indices, errors


def _safe_serialize(
    operation_name: str,
    serializer_func: Callable[[], Any],
    default_value: Any,
    errors: List[str],
    exception_types: Tuple = (AttributeError, TypeError, ValueError, RuntimeError),
) -> Any:
    """Safely serialize data with consistent error handling.

    Args:
        operation_name: Name of the operation for error reporting
        serializer_func: Function that performs the serialization
        default_value: Value to return if serialization fails
        errors: List to append error messages to
        exception_types: Tuple of exception types to catch

    Returns:
        Serialized data or default value if serialization fails
    """
    try:
        return serializer_func()
    except exception_types as e:
        errors.append(f"{operation_name} serialization: {e}")
        return default_value


def serialize_state(memo: Any) -> Dict[str, Any]:
    """Serialize the application's internal state to a JSON-serializable dictionary.

    Args:
        memo: Kopf memo object containing operator state

    Returns:
        Dictionary containing serialized state
    """
    state = {}
    errors: List[str] = []

    def serialize_config():
        if has_valid_attr(memo, "config"):
            return memo.config.model_dump(mode="json")
        return {}

    state["config"] = _safe_serialize("config", serialize_config, {}, errors)

    def serialize_config_context():
        if has_valid_attr(memo, "haproxy_config_context"):
            return memo.haproxy_config_context.model_dump(mode="json")
        return {}

    state["haproxy_config_context"] = _safe_serialize(
        "haproxy_config_context", serialize_config_context, {}, errors
    )

    def serialize_metadata():
        return {
            "configmap_name": getattr(memo.cli_options, "configmap_name", None)
            if hasattr(memo, "cli_options")
            else None,
            "has_config_reload_flag": hasattr(memo, "config_reload_flag"),
            "has_stop_flag": hasattr(memo, "stop_flag"),
        }

    state["metadata"] = _safe_serialize(
        "metadata", serialize_metadata, {"configmap_name": None}, errors
    )

    def serialize_cli_options():
        if has_valid_attr(memo, "cli_options"):
            return {
                "configmap_name": memo.cli_options.configmap_name,
                "secret_name": memo.cli_options.secret_name,
            }
        return {}

    state["cli_options"] = _safe_serialize(
        "cli_options", serialize_cli_options, {}, errors
    )

    def serialize_operator_config():
        if has_valid_attr(memo, "config"):
            return {
                "healthz_port": memo.config.operator.healthz_port,
                "metrics_port": memo.config.operator.metrics_port,
                "socket_path": memo.config.operator.socket_path,
                "verbose": memo.config.logging.verbose,
                "structured_logging": memo.config.logging.structured,
                "tracing_enabled": memo.config.tracing.enabled,
                "validation_dataplane_host": memo.config.validation.dataplane_host,
                "validation_dataplane_port": memo.config.validation.dataplane_port,
            }
        return {}

    state["operator_config"] = _safe_serialize(
        "operator_config", serialize_operator_config, {}, errors
    )

    def serialize_indices():
        indices, index_errors = _serialize_memo_indices(memo)
        errors.extend(index_errors)
        return indices

    state["indices"] = _safe_serialize("indices", serialize_indices, {}, errors)

    def serialize_debouncer():
        if has_valid_attr(memo, "debouncer"):
            return memo.debouncer.get_stats()
        return None

    state["debouncer"] = _safe_serialize("debouncer", serialize_debouncer, None, errors)

    if errors:
        state["serialization_errors"] = errors
        logger.warning(
            f"State serialization encountered {len(errors)} errors: {errors}"
        )

    return state
