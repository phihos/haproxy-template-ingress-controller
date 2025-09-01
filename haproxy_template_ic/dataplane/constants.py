"""
Constants for HAProxy Dataplane API operations.

Re-exports relevant constants from the main constants module
and defines dataplane-specific constants.
"""

from haproxy_template_ic.constants import (
    DEFAULT_API_TIMEOUT,
    DEFAULT_DATAPLANE_PASSWORD,
    DEFAULT_DATAPLANE_PORT,
    DEFAULT_DATAPLANE_USERNAME,
)

__all__ = [
    "DEFAULT_API_TIMEOUT",
    "DEFAULT_DATAPLANE_PASSWORD",
    "DEFAULT_DATAPLANE_PORT",
    "DEFAULT_DATAPLANE_USERNAME",
]
