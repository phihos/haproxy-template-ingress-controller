"""
Management socket functionality for HAProxy Template IC.

This module provides a simple command-based management socket interface that allows
external tools to query the operator's internal state via Unix socket commands.

Note: This module has been refactored into the `management` package for better
organization. The main functionality is now split across multiple modules:
- server: ManagementSocketServer class and main server logic
- handlers: Command parsing and routing
- data_providers: Data extraction and dumping capabilities
- serializers: Data serialization utilities
"""

# Re-export the main functionality for backward compatibility
from haproxy_template_ic.management import (
    ManagementSocketServer,
    run_management_socket_server,
    serialize_state,
    _serialize_resource_collection,
    _serialize_kopf_index,
    _serialize_memo_indices,
    _safe_serialize,
)

__all__ = [
    "ManagementSocketServer",
    "run_management_socket_server",
    "serialize_state",
    "_serialize_resource_collection",
    "_serialize_kopf_index",
    "_serialize_memo_indices",
    "_safe_serialize",
]
