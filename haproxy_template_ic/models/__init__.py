# Configuration and data models package
# This package contains all configuration models split by concern:
# types, config, templates, resources, and context

import logging

logger = logging.getLogger(__name__)

from .types import (
    NonEmptyStr,
    NonEmptyStrictStr,
    AbsolutePath,
    Filename,
    KubernetesKind,
    ApiVersion,
    SnippetName,
)

from .config import (
    ResourceFilter,
    WatchResourceConfig,
    PodSelector,
    TemplateRenderingConfig,
    OperatorConfig,
    LoggingConfig,
    TracingConfig,
    ValidationConfig,
    Config,
    config_from_dict,
    # Type aliases for collections
    WatchResourceCollection,
    MapCollection,
    TemplateSnippetCollection,
    CertificateCollection,
)

from .templates import (
    TemplateConfig,
    TemplateSnippet,
    ContentType,
    RenderedContent,
    TriggerContext,
    RenderedConfig,
)

from .resources import (
    IndexedResourceCollection,
)

from .context import (
    TemplateContext,
    HAProxyConfigContext,
)

# Rebuild models with forward references after all imports are complete
try:
    HAProxyConfigContext.model_rebuild()
except Exception as e:  # nosec B110 - Exception is logged and safe to ignore for backward compatibility
    # If rebuilding fails, continue anyway for backward compatibility during development
    # This can happen when Config import is not available or circular dependencies exist
    logger.debug(f"Model rebuild failed (safe to ignore): {e}")

__all__ = [
    # Type aliases and validation
    "NonEmptyStr",
    "NonEmptyStrictStr", 
    "AbsolutePath",
    "Filename",
    "KubernetesKind",
    "ApiVersion",
    "SnippetName",
    
    # Configuration models
    "ResourceFilter",
    "WatchResourceConfig",
    "PodSelector",
    "TemplateRenderingConfig",
    "OperatorConfig",
    "LoggingConfig",
    "TracingConfig",
    "ValidationConfig",
    "Config",
    "config_from_dict",
    
    # Template models
    "TemplateConfig",
    "TemplateSnippet",
    "ContentType",
    "RenderedContent",
    "TriggerContext",
    "RenderedConfig",
    
    # Resource models
    "IndexedResourceCollection",
    
    # Context models
    "TemplateContext",
    "HAProxyConfigContext",
    
    # Type aliases for collections
    "WatchResourceCollection",
    "MapCollection",
    "TemplateSnippetCollection",
    "CertificateCollection",
]