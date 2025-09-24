"""
Configuration types, enums, exceptions, and models for HAProxy Dataplane API operations.

Consolidated module containing all type definitions, error classes, and data models
for the HAProxy Dataplane API v3 integration.
"""

import logging
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, TypeVar, TYPE_CHECKING

import xxhash

from haproxy_template_ic.constants import DEFAULT_DATAPLANE_PORT
from haproxy_template_ic.k8s.kopf_utils import IndexedResourceCollection

from .endpoint import DataplaneEndpoint

if TYPE_CHECKING:
    from .adapter import ReloadInfo

__all__ = [
    "XXH64_PREFIX",
    "SHA256_PREFIX",
    "MD5_PREFIX",
    "MIME_TYPE_TEXT_PLAIN",
    "MIME_TYPE_PEM_FILE",
    "ConfigChangeType",
    "ConfigSectionType",
    "ConfigElementType",
    "DataplaneAPIError",
    "ValidationError",
    "ConfigChange",
    "MapChange",
    "StructuredDeploymentResult",
    "ValidationDeploymentResult",
    "TransactionCommitResult",
    "SynchronizationResult",
    "ValidateAndDeployResult",
    "ConfigSynchronizerResult",
    "ConfigChangeResult",
    "RuntimeOperationResult",
    "StorageOperationResult",
    "CreateOperationResult",
    "UpdateOperationResult",
    "DeleteOperationResult",
    "compute_content_hash",
    "extract_hash_from_description",
    "get_production_urls_from_index",
]

T = TypeVar("T")

XXH64_PREFIX = "xxh64:"
SHA256_PREFIX = "sha256:"
MD5_PREFIX = "md5:"

MIME_TYPE_TEXT_PLAIN = "text/plain"
MIME_TYPE_PEM_FILE = "application/x-pem-file"


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

    SERVER = "server"
    SERVER_TEMPLATE = "server_template"
    SERVER_SWITCHING_RULE = "server_switching_rule"
    STICK_RULE = "stick_rule"

    BIND = "bind"
    BACKEND_SWITCHING_RULE = "backend_switching_rule"

    ACL = "acl"
    HTTP_REQUEST_RULE = "http_request_rule"
    HTTP_RESPONSE_RULE = "http_response_rule"
    TCP_REQUEST_RULE = "tcp_request_rule"
    TCP_RESPONSE_RULE = "tcp_response_rule"
    FILTER = "filter"
    LOG_TARGET = "log_target"
    PEER_ENTRY = "peer_entry"
    CAPTURE = "capture"
    MAILER = "mailer"
    NAMESERVER = "nameserver"

    HTTP_CHECK = "http_check"
    TCP_CHECK = "tcp_check"
    ERROR_FILE = "error_file"


class DataplaneAPIError(Exception):
    """Base exception for Dataplane API errors.

    Attributes:
        endpoint: The dataplane endpoint where the error occurred
        operation: The operation that failed (e.g., 'validate', 'deploy', 'get_version')
        original_error: The original exception that caused this error, if any
    """

    def __init__(
        self,
        message: str,
        endpoint: str | DataplaneEndpoint | None = None,
        operation: str | None = None,
        original_error: Exception | None = None,
    ):
        super().__init__(message)
        self.endpoint = endpoint
        self.operation = operation
        self.original_error = original_error

    def __str__(self) -> str:
        """Return detailed error message with context."""
        base_message = super().__str__()
        context_parts = []

        if self.operation:
            context_parts.append(f"operation={self.operation}")
        if self.endpoint:
            context_parts.append(f"endpoint={self.endpoint}")

        if context_parts:
            return f"{base_message} [{', '.join(context_parts)}]"
        return base_message


class ValidationError(DataplaneAPIError):
    """Raised when HAProxy configuration validation fails.

    Attributes:
        config_size: Size of the configuration that failed validation
        validation_details: Detailed error message from HAProxy validation
        error_line: Line number where the error occurred (if extracted)
        config_content: Full configuration content that failed validation
        error_context: Configuration lines around the error (if available)
    """

    def __init__(
        self,
        message: str,
        endpoint: str | DataplaneEndpoint | None = None,
        config_size: int | None = None,
        validation_details: str | None = None,
        error_line: int | None = None,
        config_content: str | None = None,
        error_context: str | None = None,
        original_error: Exception | None = None,
    ):
        super().__init__(
            message,
            endpoint=endpoint,
            operation="validate",
            original_error=original_error,
        )
        self.config_size = config_size
        self.validation_details = validation_details
        self.error_line = error_line
        self.config_content = config_content
        self.error_context = error_context

    def __str__(self) -> str:
        """Return detailed validation error message with context."""
        base_message = super().__str__()
        detail_parts = []

        if self.config_size:
            detail_parts.append(f"config_size={self.config_size}")
        if self.validation_details:
            detail_parts.append(f"details={self.validation_details}")

        if detail_parts:
            result = f"{base_message} [{', '.join(detail_parts)}]"
        else:
            result = base_message

        # Add error context if available
        if self.error_context:
            result += f"\n\nConfiguration context around error:\n{self.error_context}"

        return result


@dataclass
class MapChange:
    """Represents a change in map file entries."""

    operation: str
    key: str
    value: str = ""


def _safe_dict_get(obj: Any, key: str, default: T | None = None) -> T | None:
    """Safely get value from dict-like object."""
    return obj.get(key, default) if isinstance(obj, dict) else default


@dataclass
class ConfigChange:
    """Represents a specific configuration change to be applied via dataplane API.

    This class encapsulates all information needed to apply a granular configuration
    change using the HAProxy Dataplane API's structured endpoints instead of the
    raw configuration endpoint.

    Attributes:
        change_type: The type of change (CREATE, UPDATE, DELETE)
        section_type: The type of configuration section being changed
        section_name: The name/identifier of the specific section
        new_config: The new configuration object (None for DELETE operations)
        old_config: The old configuration object (None for CREATE operations)
        section_index: For indexed sections like defaults, the section index (optional)
        element_type: For nested elements within sections (optional)
        element_index: For ordered elements like rules, the element index (optional)
        element_id: For named elements within sections (optional)
    """

    change_type: ConfigChangeType
    section_type: ConfigSectionType
    section_name: str
    new_config: Any | None = None
    old_config: Any | None = None
    section_index: int | None = None
    element_type: ConfigElementType | None = None
    element_index: int | None = None
    element_id: str | None = None

    def __str__(self) -> str:
        """Return a human-readable description of the change."""
        base_description = f"{self.section_type.value} {self.section_name}"

        if self.element_type:
            # This is a nested element change
            element_id = (
                self.element_id or f"[{self.element_index}]"
                if self.element_index is not None
                else ""
            )
            element_description = f"{self.element_type.value} {element_id}".strip()
            base_description = f"{base_description}/{element_description}"

        match self.change_type:
            case ConfigChangeType.CREATE:
                return f"create {base_description}"
            case ConfigChangeType.DELETE:
                return f"remove {base_description}"
            case ConfigChangeType.UPDATE:
                return f"modify {base_description}"
            case _:
                return f"{self.change_type.value} {base_description}"

    @classmethod
    def create_section_change(
        cls,
        change_type: ConfigChangeType,
        section_type: ConfigSectionType,
        section_name: str,
        new_config: Any | None = None,
        old_config: Any | None = None,
        section_index: int | None = None,
    ) -> "ConfigChange":
        """Factory method for creating section-level configuration changes."""
        return cls(
            change_type=change_type,
            section_type=section_type,
            section_name=section_name,
            new_config=new_config,
            old_config=old_config,
            section_index=section_index,
        )

    @classmethod
    def create_element_change(
        cls,
        change_type: ConfigChangeType,
        section_type: ConfigSectionType,
        section_name: str,
        element_type: ConfigElementType,
        new_config: Any | None = None,
        old_config: Any | None = None,
        element_id: str | None = None,
        element_index: int | None = None,
    ) -> "ConfigChange":
        """Factory method for creating element-level configuration changes."""
        return cls(
            change_type=change_type,
            section_type=section_type,
            section_name=section_name,
            element_type=element_type,
            new_config=new_config,
            old_config=old_config,
            element_id=element_id,
            element_index=element_index,
        )


@dataclass
class StructuredDeploymentResult:
    """Result from structured configuration deployment operations.

    Used by _deploy_with_transaction and _deploy_without_transaction methods.
    """

    changes_applied: int
    transaction_used: bool
    version: str
    reload_info: "ReloadInfo"
    transaction_id: str | None = None
    total_changes: int | None = None


@dataclass
class ValidationDeploymentResult:
    """Result from configuration validation and deployment operations.

    Used by deploy_configuration method in ValidationAPI.
    """

    size: int
    status: str
    version: str
    reload_info: "ReloadInfo"


@dataclass
class TransactionCommitResult:
    """Result from transaction commit operations.

    Used by commit method in TransactionAPI.
    """

    transaction_id: str
    status: str
    reload_info: "ReloadInfo"


@dataclass
class SynchronizationResult:
    """Result from configuration synchronization operations.

    Used by various deployment methods in synchronizer.
    """

    method: str
    version: str
    reload_info: "ReloadInfo"
    dataplane_errors: list[DataplaneAPIError] = field(default_factory=list)


@dataclass
class ValidateAndDeployResult:
    """Result from combined validation and deployment operations.

    Used by validate_and_deploy method.
    """

    validation: str
    deployment: ValidationDeploymentResult


@dataclass
class ConfigSynchronizerResult:
    """Result from configuration synchronizer operations.

    Used by sync_configuration method in ConfigSynchronizer.
    """

    successful: int
    failed: int
    skipped: int
    errors: list[str]
    reload_info: "ReloadInfo"


@dataclass
class ConfigChangeResult:
    """Result from applying a single configuration change.

    Used by ConfigAPI operations that may trigger reloads.
    """

    change_applied: bool
    reload_info: "ReloadInfo"


@dataclass
class RuntimeOperationResult:
    """Result from runtime API operations.

    Used by RuntimeAPI operations like map updates, ACL updates.
    """

    operation_applied: bool
    reload_info: "ReloadInfo"


@dataclass
class StorageOperationResult:
    """Result from storage API operations.

    Used by StorageAPI operations like map sync, certificate sync.
    """

    operation_applied: bool
    reload_info: "ReloadInfo"


@dataclass
class CreateOperationResult:
    """Result from storage create operations.

    Used by storage helper methods for creating resources.
    """

    reload_info: "ReloadInfo"


@dataclass
class UpdateOperationResult:
    """Result from storage update operations.

    Used by storage helper methods for updating resources.
    """

    content_changed: bool
    reload_info: "ReloadInfo"


@dataclass
class DeleteOperationResult:
    """Result from storage delete operations.

    Used by storage helper methods for deleting resources.
    """

    reload_info: "ReloadInfo"


def compute_content_hash(content: str) -> str:
    """Compute xxHash64 of content for fast change detection.

    Uses xxHash64 for its excellent performance (5GB/s+) and sufficient
    collision resistance for non-cryptographic change detection.

    Args:
        content: The text content to hash

    Returns:
        Hash string in format "xxh64:<hex_hash>"
    """
    return f"{XXH64_PREFIX}{xxhash.xxh64(content.encode('utf-8')).hexdigest()}"


def extract_hash_from_description(description: str | None) -> str | None:
    """Extract content hash from description field if present.

    Args:
        description: Description field that may contain a hash

    Returns:
        The hash string if found (e.g., "xxh64:abc123..."), None otherwise
    """
    if not description or not isinstance(description, str):
        return None

    # Check if description starts with a known hash format
    if description.startswith((XXH64_PREFIX, SHA256_PREFIX, MD5_PREFIX)):
        # Return just the hash part (before any additional description)
        return description.split(" ", 1)[0]

    return None


def get_production_urls_from_index(
    indexed_pods: "IndexedResourceCollection",
) -> tuple[list[str], dict[str, str]]:
    """Extract dataplane URLs and pod names from indexed HAProxy pods.

    Returns:
        Tuple of (urls, url_to_pod_name_mapping) where:
        - urls: List of dataplane URLs
        - url_to_pod_name_mapping: Dict mapping URLs to pod names
    """

    logger = logging.getLogger(__name__)
    urls: list[str] = []
    url_to_pod_name: dict[str, str] = {}

    for pod_dict in indexed_pods.values():
        status: dict[str, Any] = _safe_dict_get(pod_dict, "status", {}) or {}
        phase = _safe_dict_get(status, "phase")
        pod_ip = _safe_dict_get(status, "podIP")

        logger.debug(f"🔍 Pod phase: {phase}, IP: {pod_ip}")

        if phase != "Running" or not pod_ip:
            continue

        metadata = _safe_dict_get(pod_dict, "metadata", {})
        pod_name = _safe_dict_get(metadata, "name", f"pod-{pod_ip.replace('.', '-')}")

        annotations = _safe_dict_get(metadata, "annotations", {})
        port_str = _safe_dict_get(
            annotations,
            "haproxy-template-ic/dataplane-port",
            str(DEFAULT_DATAPLANE_PORT),
        )

        # Validate port is a valid number, fallback to default if not
        try:
            port_num = (
                int(port_str)
                if port_str and port_str.strip()
                else DEFAULT_DATAPLANE_PORT
            )
            if not (1 <= port_num <= 65535):  # Valid port range
                port_num = DEFAULT_DATAPLANE_PORT
            port = str(port_num)
        except (ValueError, TypeError):
            port = str(DEFAULT_DATAPLANE_PORT)

        url = f"http://{pod_ip}:{port}"
        urls.append(url)
        url_to_pod_name[url] = pod_name
        logger.debug(f"🔍 Found production URL: {url} for pod: {pod_name}")

    logger.debug(f"🔍 Found {len(urls)} production URLs: {urls}")
    return urls, url_to_pod_name
