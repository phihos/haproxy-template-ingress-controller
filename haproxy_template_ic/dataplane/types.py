"""
Configuration types and enums for HAProxy Dataplane API operations.

Defines the various types of configuration sections, elements, and changes
supported by the HAProxy Dataplane API v3.
"""

from enum import Enum

__all__ = [
    "ConfigChangeType",
    "ConfigSectionType", 
    "ConfigElementType",
]


class ConfigChangeType(Enum):
    """Types of configuration changes that can be applied."""

    CREATE = "create"
    UPDATE = "update"
    DELETE = "delete"


class ConfigSectionType(Enum):
    """Types of configuration sections supported for structured updates."""

    BACKEND = "backend"
    FRONTEND = "frontend"
    DEFAULTS = "defaults"
    GLOBAL = "global"
    USERLIST = "userlist"
    CACHE = "cache"
    MAILERS = "mailers"
    RESOLVER = "resolver"
    PEER = "peer"
    FCGI_APP = "fcgi_app"
    HTTP_ERRORS = "http_errors"
    RING = "ring"
    LOG_FORWARD = "log_forward"
    PROGRAM = "program"


class ConfigElementType(Enum):
    """Types of nested configuration elements within sections."""

    # Backend-specific elements
    SERVER = "server"
    SERVER_SWITCHING_RULE = "server_switching_rule"
    STICK_RULE = "stick_rule"

    # Frontend-specific elements
    BIND = "bind"
    BACKEND_SWITCHING_RULE = "backend_switching_rule"

    # Common elements for frontends, backends, defaults
    ACL = "acl"
    HTTP_REQUEST_RULE = "http_request_rule"
    HTTP_RESPONSE_RULE = "http_response_rule"
    TCP_REQUEST_RULE = "tcp_request_rule"
    TCP_RESPONSE_RULE = "tcp_response_rule"
    FILTER = "filter"
    LOG_TARGET = "log_target"

    # Defaults-specific elements
    ERROR_FILE = "error_file"