# Kubernetes Operator Core Logic
# This package contains the main operator functionality split by concern:
# resource watching, template rendering, pod management, and synchronization

from kubernetes import config
from kr8s.objects import Secret, ConfigMap
from kr8s.objects import Pod

from .k8s_resources import (
    update_resource_index,
    setup_resource_watchers,
    _collect_resource_indices,
    _record_resource_metrics,
)

from .configmap import (
    load_config_from_configmap,
    fetch_configmap,
    handle_configmap_change,
)

from .secrets import (
    fetch_secret,
    handle_secret_change,
)

from .pod_management import (
    haproxy_pods_index,
    handle_haproxy_pod_create,
    handle_haproxy_pod_delete,
    handle_haproxy_pod_update,
    setup_haproxy_pod_indexing,
)

from .template_renderer import (
    render_haproxy_templates,
    trigger_template_rendering,
    _prepare_template_context,
    _render_haproxy_config,
    _render_content_templates,
    _validate_template_errors,
)

from .synchronization import (
    synchronize_with_haproxy_instances,
    _validate_sync_prerequisites,
    _get_haproxy_pod_collection,
    _record_sync_metrics,
    _log_haproxy_error_hints,
)

from .initialization import (
    initialize_configuration,
    init_watch_configmap,
    init_management_socket,
    init_template_debouncer,
    init_metrics_server,
    cleanup_template_debouncer,
    cleanup_tracing,
    cleanup_metrics_server,
    configure_webhook_server,
    create_event_loop,
    run_operator_loop,
)

from .utils import (
    get_current_namespace,
    extract_nested_field,
    trigger_reload,
    _compile_jsonpath,
    _is_valid_resource,
    _is_valid_dict_resource,
    _is_valid_sequence_resource,
    _is_valid_object_resource,
)

__all__ = [
    # Test compatibility re-exports
    "config",
    "Secret",
    "ConfigMap",
    "Pod",
    # Resource management
    "update_resource_index",
    "setup_resource_watchers",
    "_collect_resource_indices",
    "_record_resource_metrics",
    # ConfigMap handling
    "load_config_from_configmap",
    "fetch_configmap",
    "handle_configmap_change",
    # Secret handling
    "fetch_secret",
    "handle_secret_change",
    # Pod management
    "haproxy_pods_index",
    "handle_haproxy_pod_create",
    "handle_haproxy_pod_delete",
    "handle_haproxy_pod_update",
    "setup_haproxy_pod_indexing",
    # Template rendering
    "render_haproxy_templates",
    "trigger_template_rendering",
    "_prepare_template_context",
    "_render_haproxy_config",
    "_render_content_templates",
    "_validate_template_errors",
    # Synchronization
    "synchronize_with_haproxy_instances",
    "_validate_sync_prerequisites",
    "_get_haproxy_pod_collection",
    "_record_sync_metrics",
    "_log_haproxy_error_hints",
    # Initialization
    "initialize_configuration",
    "init_watch_configmap",
    "init_management_socket",
    "init_template_debouncer",
    "init_metrics_server",
    "cleanup_template_debouncer",
    "cleanup_tracing",
    "cleanup_metrics_server",
    "configure_webhook_server",
    "create_event_loop",
    "run_operator_loop",
    # Utilities
    "get_current_namespace",
    "extract_nested_field",
    "trigger_reload",
    "_compile_jsonpath",
    "_is_valid_resource",
    "_is_valid_dict_resource",
    "_is_valid_sequence_resource",
    "_is_valid_object_resource",
]
