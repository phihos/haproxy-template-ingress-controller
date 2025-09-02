# HAProxy Dataplane API integration
# This package handles communication with HAProxy Dataplane API,
# configuration synchronization, and deployment management

from .types import ConfigChangeType, ConfigSectionType, ConfigElementType
from .models import (
    ConfigChange,
    compute_content_hash,
    extract_hash_from_description,
    get_production_urls_from_index,
)
from .errors import DataplaneAPIError, ValidationError
from .client import DataplaneClient
from .synchronizer import ConfigSynchronizer

from .utils import (
    extract_config_context,
    normalize_dataplane_url,
    parse_haproxy_error_line,
    parse_validation_error_details,
    MAX_CONFIG_COMPARISON_CHANGES,
)

__all__ = [
    # Types and enums
    "ConfigChangeType",
    "ConfigSectionType",
    "ConfigElementType",
    # Data models
    "ConfigChange",
    # Exceptions
    "DataplaneAPIError",
    "ValidationError",
    # Main classes
    "DataplaneClient",
    "ConfigSynchronizer",
    # Utility functions
    "compute_content_hash",
    "extract_hash_from_description",
    "get_production_urls_from_index",
    "extract_config_context",
    "normalize_dataplane_url",
    "parse_haproxy_error_line",
    "parse_validation_error_details",
    "MAX_CONFIG_COMPARISON_CHANGES",
]
