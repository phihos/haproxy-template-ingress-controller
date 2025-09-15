# Configuration and data models package
# This package contains all configuration models split by concern:
# types, config, templates, resources, and context

# Export public API
from .context import HAProxyConfigContext, TemplateContext
from .templates import (
    TemplateSnippet,
    TriggerContext,
    RenderedConfig,
    RenderedContent,
    ContentType,
    TemplateConfig,
)
from .config import (
    Config,
    PodSelector,
    ResourceFilter,
    WatchResourceConfig,
    config_from_dict,
)
from ..k8s.kopf_utils import IndexedResourceCollection

__all__ = [
    # Context models
    "HAProxyConfigContext",
    "TemplateContext",
    # Template models
    "TemplateSnippet",
    "TriggerContext",
    "RenderedConfig",
    "RenderedContent",
    "ContentType",
    "TemplateConfig",
    # Config models
    "Config",
    "PodSelector",
    "ResourceFilter",
    "WatchResourceConfig",
    "config_from_dict",
    # K8s utilities (commonly used with models)
    "IndexedResourceCollection",
]
