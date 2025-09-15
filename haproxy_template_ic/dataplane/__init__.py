# HAProxy Dataplane API integration
# This package handles communication with HAProxy Dataplane API,
# configuration synchronization, and deployment management

# Export public API
from .errors import DataplaneAPIError, ValidationError
from .models import ConfigChange, get_production_urls_from_index
from .client import DataplaneClient
from .synchronizer import ConfigSynchronizer
from .utils import normalize_dataplane_url

__all__ = [
    # Error classes
    "DataplaneAPIError",
    "ValidationError",
    # Client classes
    "DataplaneClient",
    "ConfigSynchronizer",
    # Model classes and utilities
    "ConfigChange",
    "get_production_urls_from_index",
    "normalize_dataplane_url",
]
