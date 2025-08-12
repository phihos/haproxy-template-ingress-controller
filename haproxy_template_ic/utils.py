import os
from typing import Optional

from kubernetes import config


def get_current_namespace(context: Optional[str] = None) -> Optional[str]:
    ns_path = "/var/run/secrets/kubernetes.io/serviceaccount/namespace"
    if os.path.exists(ns_path):
        with open(ns_path) as f:
            return f.read().strip()
    try:
        contexts, active_context = config.list_kube_config_contexts()
        if context is None:
            namespace = active_context["context"].get("namespace", "default")
            return namespace if isinstance(namespace, str) else "default"
        selected_context = next(
            (ctx for ctx in contexts if ctx["name"] == context), None
        )
        if selected_context is None:
            return "default"
        namespace = selected_context["context"].get("namespace", "default")
        return namespace if isinstance(namespace, str) else "default"
    except (KeyError, StopIteration, TypeError):
        return "default"
