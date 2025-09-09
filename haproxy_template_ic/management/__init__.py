"""
Management socket functionality for HAProxy Template IC.

This package provides a command-based management socket interface that allows
external tools to query the operator's internal state via Unix socket commands.
"""

from .server import ManagementSocketServer, run_management_socket_server
from .handlers import CommandHandler
from .data_providers import DataProvider
from .serializers import (
    _serialize_resource_collection,
    _serialize_kopf_index,
    _safe_serialize,
    serialize_state,
    _serialize_memo_indices,
)

__all__ = [
    "ManagementSocketServer",
    "run_management_socket_server",
    "CommandHandler",
    "DataProvider",
    "_serialize_resource_collection",
    "_serialize_kopf_index",
    "_safe_serialize",
    "serialize_state",
    "_serialize_memo_indices",
]
