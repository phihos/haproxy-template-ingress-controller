"""
HAProxy Dataplane API client for configuration management.

This module provides the DataplaneClient class that wraps the generated
HAProxy Dataplane API v3 client, offering a simplified interface for
common operations like validation, deployment, and storage synchronization.
"""

import base64
import io
import logging
import os
from typing import Any, Dict, List, Optional, Set

import httpx
from tenacity import (
    AsyncRetrying,
    retry_if_exception,
    stop_after_attempt,
    wait_exponential_jitter,
)


# HAProxy Dataplane API v3 client
from haproxy_dataplane_v3 import AuthenticatedClient

# Main configuration APIs
from haproxy_dataplane_v3.api.acl import (
    create_acl_backend,
    create_acl_frontend,
    delete_acl_backend,
    delete_acl_frontend,
    get_all_acl_backend,
    get_all_acl_frontend,
    replace_acl_backend,
    replace_acl_frontend,
)
from haproxy_dataplane_v3.api.backend import (
    create_backend,
    delete_backend,
    get_backends,
    replace_backend,
)
from haproxy_dataplane_v3.api.backend_switching_rule import (
    create_backend_switching_rule,
    delete_backend_switching_rule,
    get_backend_switching_rules,
    replace_backend_switching_rule,
)

# Core section APIs
from haproxy_dataplane_v3.api.bind import (
    create_bind_frontend,
    delete_bind_frontend,
    get_all_bind_frontend,
    replace_bind_frontend,
)
from haproxy_dataplane_v3.api.cache import (
    get_caches,
)
from haproxy_dataplane_v3.api.configuration import (
    get_ha_proxy_configuration,
)
from haproxy_dataplane_v3.api.defaults import (
    get_defaults_sections,
    replace_defaults_section,
)
from haproxy_dataplane_v3.api.fcgi_app import (
    get_fcgi_apps,
)
from haproxy_dataplane_v3.api.filter_ import (
    create_filter_backend,
    create_filter_frontend,
    delete_filter_backend,
    delete_filter_frontend,
    get_all_filter_backend,
    get_all_filter_frontend,
    replace_filter_backend,
    replace_filter_frontend,
)
from haproxy_dataplane_v3.api.frontend import (
    create_frontend,
    delete_frontend,
    get_frontends,
    replace_frontend,
)
from haproxy_dataplane_v3.api.global_ import get_global, replace_global
from haproxy_dataplane_v3.api.http_after_response_rule import (
    get_all_http_after_response_rule_backend,
    get_all_http_after_response_rule_frontend,
)
from haproxy_dataplane_v3.api.http_check import (
    get_all_http_check_backend,
)
from haproxy_dataplane_v3.api.http_error_rule import (
    get_all_http_error_rule_backend,
    get_all_http_error_rule_frontend,
)
from haproxy_dataplane_v3.api.http_errors import (
    get_http_errors_sections,
)
from haproxy_dataplane_v3.api.http_request_rule import (
    create_http_request_rule_backend,
    create_http_request_rule_frontend,
    delete_http_request_rule_backend,
    delete_http_request_rule_frontend,
    get_all_http_request_rule_backend,
    get_all_http_request_rule_frontend,
    replace_http_request_rule_backend,
    replace_http_request_rule_frontend,
)
from haproxy_dataplane_v3.api.http_response_rule import (
    create_http_response_rule_backend,
    create_http_response_rule_frontend,
    delete_http_response_rule_backend,
    delete_http_response_rule_frontend,
    get_all_http_response_rule_backend,
    get_all_http_response_rule_frontend,
    replace_http_response_rule_backend,
    replace_http_response_rule_frontend,
)
from haproxy_dataplane_v3.api.information import get_info

# Advanced section APIs
from haproxy_dataplane_v3.api.log_forward import (
    get_log_forwards,
)
from haproxy_dataplane_v3.api.log_target import (
    create_log_target_backend,
    create_log_target_frontend,
    delete_log_target_backend,
    delete_log_target_frontend,
    get_all_log_target_backend,
    get_all_log_target_frontend,
    get_all_log_target_global,
    replace_log_target_backend,
    replace_log_target_frontend,
)
from haproxy_dataplane_v3.api.mailers import (
    get_mailers_sections,
)
from haproxy_dataplane_v3.api.peer import (
    get_peer_sections,
)
from haproxy_dataplane_v3.api.process_manager import (
    get_programs,
)
from haproxy_dataplane_v3.api.quic_initial_rule import (
    get_all_quic_initial_rule_frontend,
)
from haproxy_dataplane_v3.api.resolver import (
    get_resolvers,
)
from haproxy_dataplane_v3.api.ring import (
    get_rings,
)
from haproxy_dataplane_v3.api.server import (
    create_server_backend,
    delete_server_backend,
    get_all_server_backend,
    replace_server_backend,
)

# Runtime APIs for reload-free operations
from haproxy_dataplane_v3.api.acl_runtime import (
    add_payload_runtime_acl,
    delete_services_haproxy_runtime_acls_parent_name_entries_id,
    post_services_haproxy_runtime_acls_parent_name_entries,
)
from haproxy_dataplane_v3.api.maps import (
    add_map_entry,
    delete_runtime_map_entry,
    replace_runtime_map_entry,
)
from haproxy_dataplane_v3.api.server_switching_rule import (
    create_server_switching_rule,
    delete_server_switching_rule,
    get_server_switching_rules,
    replace_server_switching_rule,
)
from haproxy_dataplane_v3.api.stick_rule import (
    create_stick_rule,
    delete_stick_rule,
    get_stick_rules,
    replace_stick_rule,
)
from haproxy_dataplane_v3.api.storage import (
    create_storage_general_file,
    create_storage_map_file,
    create_storage_ssl_certificate,
    delete_storage_general_file,
    delete_storage_map,
    delete_storage_ssl_certificate,
    get_all_storage_general_files,
    get_all_storage_map_files,
    get_all_storage_ssl_certificates,
    get_one_storage_general_file,
    get_one_storage_map,
    get_one_storage_ssl_certificate,
    replace_storage_general_file,
    replace_storage_map_file,
    replace_storage_ssl_certificate,
)
from haproxy_dataplane_v3.api.tcp_check import (
    get_all_tcp_check_backend,
)
from haproxy_dataplane_v3.api.tcp_request_rule import (
    create_tcp_request_rule_backend,
    create_tcp_request_rule_frontend,
    delete_tcp_request_rule_backend,
    delete_tcp_request_rule_frontend,
    get_all_tcp_request_rule_backend,
    get_all_tcp_request_rule_frontend,
    replace_tcp_request_rule_backend,
    replace_tcp_request_rule_frontend,
)
from haproxy_dataplane_v3.api.tcp_response_rule import (
    create_tcp_response_rule_backend,
    delete_tcp_response_rule_backend,
    get_all_tcp_response_rule_backend,
    replace_tcp_response_rule_backend,
)
from haproxy_dataplane_v3.api.transactions import (
    commit_transaction,
    delete_transaction,
    start_transaction,
)
from haproxy_dataplane_v3.api.userlist import (
    create_userlist,
    delete_userlist,
    get_userlists,
)
from haproxy_dataplane_v3.models.create_storage_general_file_body import (
    CreateStorageGeneralFileBody,
)
from haproxy_dataplane_v3.models.create_storage_map_file_body import (
    CreateStorageMapFileBody,
)
from haproxy_dataplane_v3.models.create_storage_ssl_certificate_body import (
    CreateStorageSSLCertificateBody,
)
from haproxy_dataplane_v3.models.replace_storage_general_file_body import (
    ReplaceStorageGeneralFileBody,
)
from haproxy_dataplane_v3.types import File
from haproxy_dataplane_v3.models.one_map_entry import OneMapEntry
from haproxy_dataplane_v3.models.one_acl_file_entry import OneACLFileEntry
from haproxy_dataplane_v3.models.server_params_maintenance import (
    ServerParamsMaintenance,
)

from haproxy_template_ic.constants import (
    DEFAULT_API_TIMEOUT,
    DEFAULT_DATAPLANE_PASSWORD,
    DEFAULT_DATAPLANE_USERNAME,
    INITIAL_RETRY_WAIT_SECONDS,
    MAX_RETRY_WAIT_SECONDS,
)
from .errors import DataplaneAPIError, ValidationError
from .models import ConfigChange, compute_content_hash
from .types import ConfigChangeType, ConfigElementType, ConfigSectionType
from .utils import (
    handle_dataplane_errors,
    normalize_dataplane_url,
    parse_validation_error_details,
    _fetch_with_metrics,
    _get_configuration_version,
    _log_fetch_error,
    _natural_sort_key,
)
from haproxy_template_ic.metrics import get_metrics_collector
from haproxy_template_ic.tracing import (
    add_span_attributes,
    record_span_event,
    set_span_error,
    trace_dataplane_operation,
)

logger = logging.getLogger(__name__)

# Section elements registry defining nested elements each section supports
_SECTION_ELEMENTS = {
    ConfigSectionType.BACKEND: [
        ("servers", ConfigElementType.SERVER, True),  # Named elements
        (
            "server_switching_rules",
            ConfigElementType.SERVER_SWITCHING_RULE,
            False,
        ),  # Ordered
        ("stick_rules", ConfigElementType.STICK_RULE, False),  # Ordered
        ("http_request_rules", ConfigElementType.HTTP_REQUEST_RULE, False),  # Ordered
        ("http_response_rules", ConfigElementType.HTTP_RESPONSE_RULE, False),  # Ordered
        ("tcp_request_rules", ConfigElementType.TCP_REQUEST_RULE, False),  # Ordered
        ("tcp_response_rules", ConfigElementType.TCP_RESPONSE_RULE, False),  # Ordered
        ("acls", ConfigElementType.ACL, True),  # Named
        ("filters", ConfigElementType.FILTER, False),  # Ordered
        ("log_targets", ConfigElementType.LOG_TARGET, False),  # Ordered
    ],
    ConfigSectionType.FRONTEND: [
        ("binds", ConfigElementType.BIND, True),  # Named elements
        (
            "backend_switching_rules",
            ConfigElementType.BACKEND_SWITCHING_RULE,
            False,
        ),  # Ordered
        ("http_request_rules", ConfigElementType.HTTP_REQUEST_RULE, False),  # Ordered
        ("http_response_rules", ConfigElementType.HTTP_RESPONSE_RULE, False),  # Ordered
        ("tcp_request_rules", ConfigElementType.TCP_REQUEST_RULE, False),  # Ordered
        ("acls", ConfigElementType.ACL, True),  # Named
        ("filters", ConfigElementType.FILTER, False),  # Ordered
        ("log_targets", ConfigElementType.LOG_TARGET, False),  # Ordered
    ],
    # Note: ConfigSectionType.DEFAULTS is not included here because the HAProxy
    # Dataplane API v3 doesn't support nested element endpoints for defaults
    # sections (returns HTTP 501 Not Implemented). Defaults are handled as
    # atomic units using full_section=true.
}


# Element handler registry for structured nested element deployment
_ELEMENT_HANDLERS = {
    ConfigElementType.SERVER: {
        "sections": {ConfigSectionType.BACKEND},
        "api": (create_server_backend, replace_server_backend, delete_server_backend),
        "id_type": "name",
    },
    ConfigElementType.BIND: {
        "sections": {ConfigSectionType.FRONTEND},
        "api": (create_bind_frontend, replace_bind_frontend, delete_bind_frontend),
        "id_type": "name",
    },
    ConfigElementType.HTTP_REQUEST_RULE: {
        "api_map": {
            ConfigSectionType.BACKEND: (
                create_http_request_rule_backend,
                replace_http_request_rule_backend,
                delete_http_request_rule_backend,
            ),
            ConfigSectionType.FRONTEND: (
                create_http_request_rule_frontend,
                replace_http_request_rule_frontend,
                delete_http_request_rule_frontend,
            ),
        },
        "id_type": "index",
    },
    ConfigElementType.ACL: {
        "api_map": {
            ConfigSectionType.BACKEND: (
                create_acl_backend,
                replace_acl_backend,
                delete_acl_backend,
            ),
            ConfigSectionType.FRONTEND: (
                create_acl_frontend,
                replace_acl_frontend,
                delete_acl_frontend,
            ),
        },
        "id_type": "index",
    },
    ConfigElementType.BACKEND_SWITCHING_RULE: {
        "sections": {ConfigSectionType.FRONTEND},
        "api": (
            create_backend_switching_rule,
            replace_backend_switching_rule,
            delete_backend_switching_rule,
        ),
        "id_type": "index",
    },
    ConfigElementType.HTTP_RESPONSE_RULE: {
        "api_map": {
            ConfigSectionType.BACKEND: (
                create_http_response_rule_backend,
                replace_http_response_rule_backend,
                delete_http_response_rule_backend,
            ),
            ConfigSectionType.FRONTEND: (
                create_http_response_rule_frontend,
                replace_http_response_rule_frontend,
                delete_http_response_rule_frontend,
            ),
        },
        "id_type": "index",
    },
    ConfigElementType.FILTER: {
        "api_map": {
            ConfigSectionType.BACKEND: (
                create_filter_backend,
                replace_filter_backend,
                delete_filter_backend,
            ),
            ConfigSectionType.FRONTEND: (
                create_filter_frontend,
                replace_filter_frontend,
                delete_filter_frontend,
            ),
        },
        "id_type": "index",
    },
    ConfigElementType.TCP_REQUEST_RULE: {
        "api_map": {
            ConfigSectionType.BACKEND: (
                create_tcp_request_rule_backend,
                replace_tcp_request_rule_backend,
                delete_tcp_request_rule_backend,
            ),
            ConfigSectionType.FRONTEND: (
                create_tcp_request_rule_frontend,
                replace_tcp_request_rule_frontend,
                delete_tcp_request_rule_frontend,
            ),
        },
        "id_type": "index",
    },
    ConfigElementType.STICK_RULE: {
        "sections": {ConfigSectionType.BACKEND},
        "api": (create_stick_rule, replace_stick_rule, delete_stick_rule),
        "id_type": "index",
    },
    ConfigElementType.SERVER_SWITCHING_RULE: {
        "sections": {ConfigSectionType.BACKEND},
        "api": (
            create_server_switching_rule,
            replace_server_switching_rule,
            delete_server_switching_rule,
        ),
        "id_type": "index",
    },
    ConfigElementType.TCP_RESPONSE_RULE: {
        "api_map": {
            ConfigSectionType.BACKEND: (
                create_tcp_response_rule_backend,
                replace_tcp_response_rule_backend,
                delete_tcp_response_rule_backend,
            ),
        },
        "id_type": "index",
    },
    ConfigElementType.LOG_TARGET: {
        "api_map": {
            ConfigSectionType.BACKEND: (
                create_log_target_backend,
                replace_log_target_backend,
                delete_log_target_backend,
            ),
            ConfigSectionType.FRONTEND: (
                create_log_target_frontend,
                replace_log_target_frontend,
                delete_log_target_frontend,
            ),
        },
        "id_type": "index",
    },
}


# Section handler registry for structured top-level section deployment
_SECTION_HANDLERS = {
    ConfigSectionType.BACKEND: {
        "create": create_backend.asyncio,
        "update": replace_backend.asyncio,
        "delete": delete_backend.asyncio,
        "id_field": "name",
        "supports_create": True,
        "supports_update": True,
        "supports_delete": True,
    },
    ConfigSectionType.FRONTEND: {
        "create": create_frontend.asyncio,
        "update": replace_frontend.asyncio,
        "delete": delete_frontend.asyncio,
        "id_field": "name",
        "supports_create": True,
        "supports_update": True,
        "supports_delete": True,
    },
    ConfigSectionType.DEFAULTS: {
        "update": replace_defaults_section.asyncio,
        "id_field": "name",
        "supports_create": False,
        "supports_update": True,
        "supports_delete": False,
        "full_section": True,  # Use full_section=True for defaults
    },
    ConfigSectionType.GLOBAL: {
        "update": replace_global.asyncio,
        "id_field": None,  # Global section doesn't have a name
        "supports_create": True,  # CREATE is treated as UPDATE
        "supports_update": True,
        "supports_delete": False,
    },
    ConfigSectionType.USERLIST: {
        "create": create_userlist.asyncio,
        "delete": delete_userlist.asyncio,
        "id_field": "name",
        "supports_create": True,
        "supports_update": True,  # UPDATE handled as DELETE+CREATE
        "supports_delete": True,
        "update_strategy": "delete_create",  # No replace endpoint
    },
}


# Section elements registry - defines which nested elements each section type supports
_SECTION_ELEMENTS = {
    ConfigSectionType.BACKEND: [
        ("servers", ConfigElementType.SERVER, True),  # Named elements
        (
            "server_switching_rules",
            ConfigElementType.SERVER_SWITCHING_RULE,
            False,
        ),  # Ordered
        ("stick_rules", ConfigElementType.STICK_RULE, False),  # Ordered
        ("http_request_rules", ConfigElementType.HTTP_REQUEST_RULE, False),  # Ordered
        ("http_response_rules", ConfigElementType.HTTP_RESPONSE_RULE, False),  # Ordered
        ("tcp_request_rules", ConfigElementType.TCP_REQUEST_RULE, False),  # Ordered
        ("tcp_response_rules", ConfigElementType.TCP_RESPONSE_RULE, False),  # Ordered
        ("acls", ConfigElementType.ACL, True),  # Named
        ("filters", ConfigElementType.FILTER, False),  # Ordered
        ("log_targets", ConfigElementType.LOG_TARGET, False),  # Ordered
    ],
    ConfigSectionType.FRONTEND: [
        ("binds", ConfigElementType.BIND, True),  # Named elements
        (
            "backend_switching_rules",
            ConfigElementType.BACKEND_SWITCHING_RULE,
            False,
        ),  # Ordered
        ("http_request_rules", ConfigElementType.HTTP_REQUEST_RULE, False),  # Ordered
        ("http_response_rules", ConfigElementType.HTTP_RESPONSE_RULE, False),  # Ordered
        ("tcp_request_rules", ConfigElementType.TCP_REQUEST_RULE, False),  # Ordered
        ("acls", ConfigElementType.ACL, True),  # Named
        ("filters", ConfigElementType.FILTER, False),  # Ordered
        ("log_targets", ConfigElementType.LOG_TARGET, False),  # Ordered
    ],
    # Note: ConfigSectionType.DEFAULTS is not included here because the HAProxy
    # Dataplane API v3 doesn't support nested element endpoints for defaults
    # sections (returns HTTP 501 Not Implemented). Defaults are handled as
    # atomic units using full_section=true.
}


# Element fetch API registry - maps element attribute names to their fetch functions
_ELEMENT_FETCH_APIS = {
    ConfigSectionType.BACKEND: {
        "servers": get_all_server_backend.asyncio,
        "server_switching_rules": get_server_switching_rules.asyncio,
        "http_request_rules": get_all_http_request_rule_backend.asyncio,
        "http_response_rules": get_all_http_response_rule_backend.asyncio,
        "http_after_response_rules": get_all_http_after_response_rule_backend.asyncio,
        "http_error_rules": get_all_http_error_rule_backend.asyncio,
        "http_checks": get_all_http_check_backend.asyncio,
        "tcp_checks": get_all_tcp_check_backend.asyncio,
        "acls": get_all_acl_backend.asyncio,
        "filters": get_all_filter_backend.asyncio,
        "tcp_request_rules": get_all_tcp_request_rule_backend.asyncio,
        "tcp_response_rules": get_all_tcp_response_rule_backend.asyncio,
        "log_targets": get_all_log_target_backend.asyncio,
        "stick_rules": get_stick_rules.asyncio,
    },
    ConfigSectionType.FRONTEND: {
        "binds": get_all_bind_frontend.asyncio,
        "backend_switching_rules": get_backend_switching_rules.asyncio,
        "http_request_rules": get_all_http_request_rule_frontend.asyncio,
        "http_response_rules": get_all_http_response_rule_frontend.asyncio,
        "http_after_response_rules": get_all_http_after_response_rule_frontend.asyncio,
        "http_error_rules": get_all_http_error_rule_frontend.asyncio,
        "acls": get_all_acl_frontend.asyncio,
        "filters": get_all_filter_frontend.asyncio,
        "tcp_request_rules": get_all_tcp_request_rule_frontend.asyncio,
        "tcp_response_rules": None,  # Not supported for frontends
        "log_targets": get_all_log_target_frontend.asyncio,
        "quic_initial_rules": get_all_quic_initial_rule_frontend.asyncio,
    },
    ConfigSectionType.GLOBAL: {
        "log_targets": get_all_log_target_global.asyncio,
    },
}


# Storage resource sync registry for unified resource management
_STORAGE_SYNC_CONFIGS = {
    "maps": {
        "get_all_func": get_all_storage_map_files.asyncio,
        "get_one_func": get_one_storage_map.asyncio,
        "create_func": create_storage_map_file.asyncio,
        "delete_func": delete_storage_map.asyncio,
        "replace_func": replace_storage_map_file.asyncio,
        "create_body_class": CreateStorageMapFileBody,
        "mime_type": "text/plain",
    },
    "certificates": {
        "get_all_func": get_all_storage_ssl_certificates.asyncio,
        "get_one_func": get_one_storage_ssl_certificate.asyncio,
        "create_func": create_storage_ssl_certificate.asyncio,
        "delete_func": delete_storage_ssl_certificate.asyncio,
        "replace_func": replace_storage_ssl_certificate.asyncio,
        "create_body_class": CreateStorageSSLCertificateBody,
        "mime_type": "application/x-pem-file",
    },
}


# Runtime-compatible server fields (these don't cause reload when changed via API)
RUNTIME_COMPATIBLE_FIELDS = {
    "name",
    "address",
    "port",  # Basic identification
    "weight",  # Weight changes
    "maintenance",  # Maps to enable/disable
    "agent_addr",
    "agent_port",
    "agent_send",  # Agent parameters
    "health_check_address",
    "health_check_port",  # Health check location
    # Note: 'ssl' was supported in 2.4 but deprecated after 2.5
}


def has_non_runtime_fields(server_config):
    """Check if server config has fields that require reload."""
    if not hasattr(server_config, "to_dict"):
        return []

    config_dict = server_config.to_dict()
    non_runtime_fields = []

    for field_name, field_value in config_dict.items():
        # Skip unset fields, empty lists, and runtime-compatible fields
        if (
            field_value is not None
            and field_value != []
            and field_name not in RUNTIME_COMPATIBLE_FIELDS
        ):
            non_runtime_fields.append(field_name)

    return non_runtime_fields


class DataplaneClient:
    """Wrapper around the generated HAProxy Dataplane API v3 client.

    This client provides a simplified interface for common Dataplane API operations
    including configuration validation and deployment. All operations raise
    structured exceptions with detailed context information.

    Example:
        Basic usage with error handling:

        >>> client = DataplaneClient("http://localhost:5555", auth=("admin", "password"))
        >>> try:
        ...     await client.validate_configuration(config_text)
        ...     version = await client.deploy_configuration(config_text)
        ... except ValidationError as e:
        ...     print(f"Config validation failed: {e}")
        ...     print(f"Config size: {e.config_size}, Details: {e.validation_details}")
        ... except DataplaneAPIError as e:
        ...     print(f"API error: {e}")
        ...     print(f"Endpoint: {e.endpoint}, Operation: {e.operation}")

    Raises:
        DataplaneAPIError: For general API communication errors
        ValidationError: For HAProxy configuration validation failures
    """

    def __init__(
        self,
        base_url: str,
        timeout: float = DEFAULT_API_TIMEOUT,
        auth: tuple[str, str] = (
            DEFAULT_DATAPLANE_USERNAME,
            DEFAULT_DATAPLANE_PASSWORD,
        ),
    ):
        """
        Initialize the client.

        Args:
            base_url: The base URL of the Dataplane API (with or without /v3)
            timeout: Request timeout in seconds
            auth: Tuple of (username, password) for basic auth
        """
        # Normalize the base URL to ensure it ends with /v3
        self.base_url = normalize_dataplane_url(base_url)
        self.timeout = timeout
        self.auth = auth

        # Defer client creation until first use
        self._client = None

    def _get_client(self) -> Any:
        """Lazy initialization of AuthenticatedClient object."""
        if self._client is None:
            logger.debug(f"Creating dataplane client for {self.base_url}")
            # Create basic auth token from username and password
            auth_string = f"{self.auth[0]}:{self.auth[1]}"
            auth_token = base64.b64encode(auth_string.encode()).decode("ascii")
            self._client = AuthenticatedClient(
                base_url=self.base_url,
                token=auth_token,
                prefix="Basic",
                timeout=httpx.Timeout(self.timeout),
            )
        return self._client

    @handle_dataplane_errors()
    async def get_version(self) -> Dict[str, Any]:
        """Get HAProxy version information using the generated client."""
        client = self._get_client()
        info_response = await get_info.asyncio(client=client)

        # Convert the generated model to dict format expected by existing code
        result = {}
        if hasattr(info_response, "haproxy") and info_response.haproxy:
            result.update(info_response.haproxy.to_dict())
        if hasattr(info_response, "api") and info_response.api:
            result.update(info_response.api.to_dict())
        if hasattr(info_response, "system") and info_response.system:
            result.update(info_response.system.to_dict())

        return result

    async def validate_configuration(self, config_content: str) -> None:
        """Validate HAProxy configuration without applying it.

        Uses direct httpx calls since openapi-python-client doesn't support
        text/plain content type for configuration endpoints.

        Raises:
            ValidationError: If configuration validation fails
            DataplaneAPIError: If API communication fails
        """
        with trace_dataplane_operation("validate", self.base_url):
            add_span_attributes(
                config_size=len(config_content), dataplane_url=self.base_url
            )

            metrics = get_metrics_collector()

            with metrics.time_dataplane_api_operation("validate"):
                try:
                    # Ensure config ends with newline to avoid HAProxy truncation errors
                    config_data = config_content.rstrip() + "\n"

                    # Use httpx directly for text/plain content
                    async with httpx.AsyncClient(timeout=self.timeout) as client:
                        response = await client.post(
                            f"{self.base_url}/services/haproxy/configuration/raw",
                            content=config_data,
                            headers={"Content-Type": "text/plain"},
                            params={"only_validate": "true", "skip_version": "true"},
                            auth=(self.auth[0], self.auth[1]),
                        )

                        if response.status_code >= 400:
                            validation_details = response.text
                            record_span_event(
                                "validation_failed", {"error": "validation_failed"}
                            )
                            set_span_error(
                                Exception(validation_details),
                                "Configuration validation failed",
                            )

                            # Extract error line and context for better debugging
                            error_msg, error_line, error_context = (
                                parse_validation_error_details(
                                    validation_details, config_data
                                )
                            )

                            raise ValidationError(
                                f"Configuration validation failed: {response.status_code} {validation_details}",
                                endpoint=self.base_url,
                                config_size=len(config_content),
                                validation_details=validation_details,
                                error_line=error_line,
                                config_content=config_data,
                                error_context=error_context,
                            )

                        record_span_event("validation_successful")

                except ValidationError:
                    # Re-raise ValidationError without wrapping
                    raise
                except httpx.RequestError as e:
                    # Handle network-related exceptions
                    record_span_event("validation_failed", {"error": str(e)})
                    set_span_error(e, "Configuration validation failed")
                    raise DataplaneAPIError(
                        f"Network error during validation: {e}",
                        endpoint=self.base_url,
                        operation="validate",
                        original_error=e,
                    ) from e
                except Exception as e:
                    # Handle all other unexpected exceptions
                    record_span_event("validation_failed", {"error": str(e)})
                    set_span_error(e, "Configuration validation failed")
                    raise DataplaneAPIError(
                        f"Configuration validation failed: {e}",
                        endpoint=self.base_url,
                        operation="validate",
                        original_error=e,
                    ) from e

    async def deploy_configuration(self, config_content: str) -> Dict[str, Any]:
        """Deploy HAProxy configuration.

        Uses direct httpx calls since openapi-python-client doesn't support
        text/plain content type for configuration endpoints.

        This method includes retry logic for transient failures (network issues,
        temporary dataplane unavailability), but excludes validation errors
        from retries since retrying won't fix config errors.
        """
        with trace_dataplane_operation("deploy", self.base_url):
            add_span_attributes(
                config_size=len(config_content), dataplane_url=self.base_url
            )

            metrics = get_metrics_collector()

            async def deployment_operation():
                with metrics.time_dataplane_api_operation("deploy"):
                    async with httpx.AsyncClient(timeout=self.timeout) as client:
                        # Get current configuration version first
                        version_response = await client.get(
                            f"{self.base_url}/services/haproxy/configuration/version",
                            auth=(self.auth[0], self.auth[1]),
                        )
                        if version_response.status_code >= 400:
                            raise DataplaneAPIError(
                                f"Failed to get configuration version: {version_response.text}"
                            )

                        current_version = version_response.json()

                        # Deploy configuration with reload using httpx
                        # Ensure config ends with newline to avoid HAProxy truncation errors
                        config_data = config_content.rstrip() + "\n"

                        deploy_response = await client.post(
                            f"{self.base_url}/services/haproxy/configuration/raw",
                            content=config_data,
                            headers={"Content-Type": "text/plain"},
                            params={
                                "version": str(current_version),
                            },
                            auth=(self.auth[0], self.auth[1]),
                        )

                        if deploy_response.status_code >= 400:
                            error_details = deploy_response.text
                            # Parse error details to extract line number and context
                            error_line, error_context = parse_validation_error_details(
                                error_details, config_data
                            )

                            # Create enhanced error with config context
                            error_msg = f"Configuration deployment failed: {deploy_response.status_code} {error_details}"
                            if error_context:
                                error_msg += f"\n\nConfiguration context around error:\n{error_context}"

                            raise DataplaneAPIError(error_msg)

                        # Get the new configuration version
                        new_version_response = await client.get(
                            f"{self.base_url}/services/haproxy/configuration/version",
                            auth=(self.auth[0], self.auth[1]),
                        )
                        if new_version_response.status_code >= 400:
                            raise DataplaneAPIError(
                                f"Failed to get new configuration version: {new_version_response.text}"
                            )

                        new_version = new_version_response.json()

                        # Check if deployment triggered a reload based on HTTP 202 status and Reload-ID header
                        reload_triggered = deploy_response.status_code == 202
                        # Try different cases for Reload-ID header (HTTP headers are case-insensitive)
                        reload_id = None
                        if reload_triggered:
                            for header_name in [
                                "Reload-ID",
                                "reload-id",
                                "RELOAD-ID",
                                "reload_id",
                            ]:
                                reload_id = deploy_response.headers.get(header_name)
                                if reload_id:
                                    break

                        logger.debug(
                            f"🔍 Raw deployment response: status={deploy_response.status_code}, "
                            f"reload_triggered={reload_triggered}, reload_id={reload_id}, "
                            f"headers={dict(deploy_response.headers)}"
                        )

                        return {
                            "version": str(new_version),
                            "reload_triggered": reload_triggered,
                            "reload_id": reload_id,
                        }

            try:
                # Simple retry with tenacity
                async for attempt in AsyncRetrying(
                    stop=stop_after_attempt(5),
                    wait=wait_exponential_jitter(
                        initial=INITIAL_RETRY_WAIT_SECONDS, max=MAX_RETRY_WAIT_SECONDS
                    ),
                    retry=retry_if_exception(
                        lambda e: (
                            isinstance(e, httpx.RequestError)  # Network errors only
                            or (
                                isinstance(e, DataplaneAPIError)
                                and not isinstance(e, ValidationError)
                                and "400" not in str(e)  # Don't retry validation errors
                            )
                        )
                    ),
                ):
                    with attempt:
                        version = await deployment_operation()
                        add_span_attributes(config_version=version)
                        record_span_event("deployment_successful", {"version": version})
                        return version

                # This should never be reached, but satisfies mypy
                raise DataplaneAPIError(
                    "Retry loop completed without success or failure"
                )
            except Exception as e:
                record_span_event("deployment_failed", {"error": str(e)})
                set_span_error(e, "Configuration deployment failed")
                raise DataplaneAPIError(
                    f"Configuration deployment failed: {e}",
                    endpoint=self.base_url,
                    operation="deploy",
                    original_error=e,
                ) from e

    def _extract_storage_content(self, storage_item: Optional[Any]) -> Optional[str]:
        """Extract content from HAProxy storage API response.

        Args:
            storage_item: Response from get_one_storage_* API calls

        Returns:
            Decoded content string or None if extraction fails
        """
        if not storage_item or not hasattr(storage_item, "payload"):
            return None
        try:
            content = storage_item.payload.read()
            if hasattr(storage_item.payload, "seek"):
                storage_item.payload.seek(0)
            return content.decode("utf-8")
        except Exception:
            return None

    @handle_dataplane_errors()
    async def _sync_storage_resources(
        self,
        resource_type: str,
        new_resources: Dict[str, str],
        get_all_func,
        get_one_func,
        create_func,
        delete_func,
        create_body_class,
        mime_type: str = "text/plain",
        replace_func=None,
    ) -> None:
        """Generic method to sync storage resources with content comparison.

        Args:
            resource_type: Type of resource ("map", "certificate", or "file")
            new_resources: Dict of resource name to content
            get_all_func: Async function to get all existing resources
            get_one_func: Async function to get a single resource
            create_func: Async function to create a resource
            delete_func: Async function to delete a resource
            create_body_class: Class to create request body
            mime_type: MIME type for the resource
            replace_func: Optional async function to replace resource content
        """
        metrics = get_metrics_collector()
        operation = f"sync_{resource_type}s"

        with metrics.time_dataplane_api_operation(operation):
            client = self._get_client()

            # Get existing resources
            existing = await get_all_func(client=client)
            existing_dict = {
                f.storage_name: f for f in (existing or []) if f.storage_name
            }

            target_names = set(new_resources.keys())
            existing_names = set(existing_dict.keys())

            created_count = 0
            updated_count = 0
            skipped_count = 0

            # Create new resources
            for name in target_names - existing_names:
                body = create_body_class(
                    file_upload=File(
                        payload=io.BytesIO(new_resources[name].encode("utf-8")),
                        file_name=name,
                        mime_type=mime_type,
                    )
                )
                body["description"] = compute_content_hash(new_resources[name])
                await create_func(client=client, body=body)
                created_count += 1
                logger.debug(f"Created {resource_type} {name}")

            # Update or skip existing resources
            for name in target_names & existing_names:
                new_content = new_resources[name]

                # Check if content changed
                try:
                    existing_resource = await get_one_func(client=client, name=name)
                    existing_content = self._extract_storage_content(existing_resource)

                    if existing_content == new_content:
                        skipped_count += 1
                        logger.debug(f"Skipped {resource_type} {name} (unchanged)")
                        continue
                except Exception as e:
                    _log_fetch_error(resource_type, name, e)

                # Content changed - use replace if available, otherwise delete+create
                if replace_func:
                    # Use generated replace function for maps/certificates
                    # The generated functions expect: client, name, body (string content)
                    await replace_func(client=client, name=name, body=new_content)
                else:
                    # Fallback to delete+create (shouldn't happen with proper replace_func)
                    await delete_func(client=client, name=name)
                    body = create_body_class(
                        file_upload=File(
                            payload=io.BytesIO(new_content.encode("utf-8")),
                            file_name=name,
                            mime_type=mime_type,
                        )
                    )
                    body["description"] = compute_content_hash(new_content)
                    await create_func(client=client, body=body)

                updated_count += 1
                logger.debug(f"Updated {resource_type} {name}")

            # Delete obsolete resources
            for name in existing_names - target_names:
                await delete_func(client=client, name=name)
                logger.debug(f"Deleted {resource_type} {name}")

            # Log summary - only use INFO if something changed
            if created_count or updated_count:
                logger.info(
                    f"{resource_type.capitalize()}s: "
                    f"{created_count} created, {updated_count} updated, {skipped_count} unchanged"
                )
            elif skipped_count:
                logger.debug(
                    f"{resource_type.capitalize()}s: "
                    f"{created_count} created, {updated_count} updated, {skipped_count} unchanged"
                )

            metrics.record_dataplane_api_request(operation, "success")

    async def sync_maps(self, maps: Dict[str, str]) -> None:
        """Synchronize HAProxy map files to storage with runtime entry updates."""
        await self._sync_maps_with_runtime(maps)

    def _parse_map_entries(self, content: str) -> Dict[str, str]:
        """Parse map file content into key-value pairs.

        Args:
            content: Map file content as string

        Returns:
            Dict mapping keys to values
        """
        entries = {}
        for line in content.splitlines():
            line = line.strip()
            if line and not line.startswith("#"):
                # Split on first whitespace
                parts = line.split(None, 1)
                if len(parts) == 2:
                    key, value = parts
                    entries[key] = value
                elif len(parts) == 1:
                    # Key without value
                    entries[parts[0]] = ""
        return entries

    def _detect_map_entry_changes(
        self, old_entries: Dict[str, str], new_entries: Dict[str, str]
    ) -> List[Any]:
        """Detect entry-level changes between old and new map content.

        Returns:
            List of change objects with operation, key, and data attributes
        """
        from dataclasses import dataclass

        @dataclass
        class MapChange:
            operation: str
            key: str
            value: str = ""
            data: str = ""  # Keep for backward compatibility

        changes = []
        old_keys = set(old_entries.keys())
        new_keys = set(new_entries.keys())

        # Deletions
        for key in old_keys - new_keys:
            changes.append(MapChange(operation="delete", key=key))

        # Additions
        for key in new_keys - old_keys:
            changes.append(
                MapChange(
                    operation="add",
                    key=key,
                    value=new_entries[key],
                    data=f"{key} {new_entries[key]}".strip(),
                )
            )

        # Modifications
        for key in old_keys & new_keys:
            if old_entries[key] != new_entries[key]:
                changes.append(
                    MapChange(
                        operation="replace",
                        key=key,
                        value=new_entries[key],
                        data=f"{key} {new_entries[key]}".strip(),
                    )
                )

        return changes

    @handle_dataplane_errors()
    async def _sync_maps_with_runtime(self, maps: Dict[str, str]) -> None:
        """Advanced map synchronization with runtime API for entry changes."""
        metrics = get_metrics_collector()
        operation = "sync_maps_runtime"

        with metrics.time_dataplane_api_operation(operation):
            client = self._get_client()
            config = _STORAGE_SYNC_CONFIGS["maps"]

            # Get existing map files
            existing = await config["get_all_func"](client=client)
            existing_dict = {
                f.storage_name: f for f in (existing or []) if f.storage_name
            }

            target_names = set(maps.keys())
            existing_names = set(existing_dict.keys())

            created_count = 0
            updated_count = 0
            skipped_count = 0
            runtime_updates = 0

            # Create new map files (these require full sync)
            for name in target_names - existing_names:
                body = config["create_body_class"](
                    file_upload=File(
                        payload=io.BytesIO(maps[name].encode("utf-8")),
                        file_name=name,
                        mime_type=config["mime_type"],
                    )
                )
                await config["create_func"](client=client, body=body)
                created_count += 1
                logger.info(f"🗺️  Created new map file: {name}")

            # Handle existing map files with smart entry-level updates
            for name in target_names & existing_names:
                new_content = maps[name]

                # Get current content
                try:
                    existing_resource = await config["get_one_func"](
                        client=client, name=name
                    )
                    existing_content = self._extract_storage_content(existing_resource)

                    if existing_content == new_content:
                        skipped_count += 1
                        logger.debug(f"🗺️  Skipped map {name} (unchanged)")
                        continue

                    # Parse entries and detect changes
                    old_entries = self._parse_map_entries(existing_content or "")
                    new_entries = self._parse_map_entries(new_content)
                    entry_changes = self._detect_map_entry_changes(
                        old_entries, new_entries
                    )

                    if (
                        entry_changes and len(entry_changes) <= 20
                    ):  # Limit runtime operations
                        try:
                            # Try runtime API for entry changes
                            map_path = f"/etc/haproxy/maps/{name}"
                            await self._apply_runtime_map_operations(
                                client, map_path, entry_changes
                            )
                            runtime_updates += len(entry_changes)
                            logger.info(
                                f"🗺️  Updated map {name} via runtime API: {len(entry_changes)} changes"
                            )
                            updated_count += 1
                            continue
                        except Exception as runtime_error:
                            logger.warning(
                                f"⚠️  Runtime update failed for map {name}, falling back to file replacement: {runtime_error}"
                            )

                    # Fallback to full file replacement
                    await config["replace_func"](
                        client=client, name=name, body=new_content
                    )
                    updated_count += 1
                    logger.info(f"🗺️  Updated map {name} via file replacement")

                except Exception as e:
                    logger.warning(
                        f"⚠️  Error processing map {name}: {e}, using file replacement"
                    )
                    await config["replace_func"](
                        client=client, name=name, body=new_content
                    )
                    updated_count += 1

            # Delete obsolete map files
            for name in existing_names - target_names:
                await config["delete_func"](client=client, name=name)
                logger.info(f"🗺️  Deleted obsolete map file: {name}")

            # Enhanced logging with runtime statistics
            if created_count or updated_count or runtime_updates:
                logger.info(
                    f"🗺️  Maps sync complete: {created_count} created, {updated_count} updated "
                    f"({runtime_updates} runtime entries), {skipped_count} unchanged"
                )
            elif skipped_count:
                logger.debug(f"🗺️  Maps sync: {skipped_count} maps unchanged")

            metrics.record_dataplane_api_request(operation, "success")

    def _parse_acl_entries(self, content: str) -> Set[str]:
        """Parse ACL file content into individual entries.

        Args:
            content: ACL file content as string

        Returns:
            Set of ACL entries (lines)
        """
        entries = set()
        for line in content.splitlines():
            line = line.strip()
            if line and not line.startswith("#"):
                entries.add(line)
        return entries

    async def sync_certificates(self, certificates: Dict[str, str]) -> None:
        """Synchronize SSL certificates to storage."""
        config = _STORAGE_SYNC_CONFIGS["certificates"]
        await self._sync_storage_resources(
            resource_type="certificate", new_resources=certificates, **config
        )

    async def sync_acls(self, acls: Dict[str, str]) -> None:
        """Synchronize HAProxy ACL entries using runtime API only.

        Note: ACL files are not stored in HAProxy storage, only runtime entries are updated.
        """
        if not acls:
            return

        logger.debug(f"📋 Processing {len(acls)} ACL files for runtime updates")
        client = self._get_client()

        for acl_name, acl_content in acls.items():
            entries = self._parse_acl_entries(acl_content)
            if entries:
                # For runtime API, we add entries directly
                changes = [{"operation": "add", "data": entry} for entry in entries]
                try:
                    await self._apply_runtime_acl_operations(client, acl_name, changes)
                    logger.debug(
                        f"📋 Updated ACL {acl_name} via runtime API ({len(entries)} entries)"
                    )
                except Exception as e:
                    logger.warning(
                        f"📋 Failed to update ACL {acl_name} via runtime API: {e}"
                    )

    @handle_dataplane_errors()
    async def sync_files(self, files: Dict[str, str]) -> None:
        """Synchronize general-purpose files to HAProxy storage.

        Note: Files use replace instead of delete+create for updates.
        """
        metrics = get_metrics_collector()
        operation = "sync_files"

        with metrics.time_dataplane_api_operation(operation):
            client = self._get_client()

            # Get existing resources
            existing = await get_all_storage_general_files.asyncio(client=client)
            existing_dict = {
                f.storage_name: f for f in (existing or []) if f.storage_name
            }

            target_names = set(files.keys())
            existing_names = set(existing_dict.keys())

            created_count = 0
            updated_count = 0
            skipped_count = 0

            # Create new files
            for name in target_names - existing_names:
                body = CreateStorageGeneralFileBody(
                    file_upload=File(
                        payload=io.BytesIO(files[name].encode("utf-8")),
                        file_name=name,
                        mime_type="text/plain",
                    )
                )
                body["description"] = compute_content_hash(files[name])
                await create_storage_general_file.asyncio(client=client, body=body)
                created_count += 1
                logger.debug(f"Created file {name}")

            # Update or skip existing files
            for name in target_names & existing_names:
                new_content = files[name]

                # Check if content changed
                try:
                    existing_file = await get_one_storage_general_file.asyncio(
                        client=client, name=name
                    )
                    existing_content = self._extract_storage_content(existing_file)

                    if existing_content == new_content:
                        skipped_count += 1
                        logger.debug(f"Skipped file {name} (unchanged)")
                        continue
                except Exception as e:
                    _log_fetch_error("file", name, e)

                # Content changed - use replace for files
                body = ReplaceStorageGeneralFileBody(
                    file_upload=File(
                        payload=io.BytesIO(new_content.encode("utf-8")),
                        file_name=name,
                        mime_type="text/plain",
                    )
                )
                body["description"] = compute_content_hash(new_content)
                await replace_storage_general_file.asyncio(
                    client=client, name=name, body=body
                )
                updated_count += 1
                logger.debug(f"Updated file {name}")

            # Delete obsolete files
            for name in existing_names - target_names:
                await delete_storage_general_file.asyncio(client=client, name=name)
                logger.debug(f"Deleted file {name}")

            # Log summary - only use INFO if something changed
            if created_count or updated_count:
                logger.info(
                    f"Files: "
                    f"{created_count} created, {updated_count} updated, {skipped_count} unchanged"
                )
            elif skipped_count:
                logger.debug(
                    f"Files: "
                    f"{created_count} created, {updated_count} updated, {skipped_count} unchanged"
                )

            metrics.record_dataplane_api_request(operation, "success")

    async def get_current_configuration(self) -> Optional[str]:
        """Get current raw HAProxy configuration.

        Returns:
            Current HAProxy configuration as string, or None if not available
        """
        try:
            client = self._get_client()
            config = await get_ha_proxy_configuration.asyncio(client=client)
            return config
        except Exception as e:
            _log_fetch_error("configuration", "current", e)
            return None

    async def deploy_configuration_conditionally(
        self, config_content: str, force: bool = False
    ) -> Dict[str, Any]:
        """Deploy HAProxy configuration only if it differs from current config.

        This method compares the new configuration with the current one and only
        deploys if they differ or if force=True. This helps minimize unnecessary
        HAProxy reloads.

        Args:
            config_content: New configuration to deploy
            force: If True, deploy even if configs are identical

        Returns:
            Dict containing version, reload_triggered status, and reload_id

        Raises:
            ValidationError: If configuration validation fails
            DataplaneAPIError: If deployment fails
        """

        with trace_dataplane_operation("deploy_conditional", self.base_url):
            add_span_attributes(
                config_size=len(config_content),
                dataplane_url=self.base_url,
                force_deployment=force,
            )

            # Get current configuration for comparison
            current_config = None
            if not force:
                current_config = await self.get_current_configuration()

            # Normalize both configs for comparison (remove extra whitespace, etc.)
            def normalize_config(config: str) -> str:
                if not config:
                    return ""
                # Remove trailing whitespace from each line and normalize line endings
                lines = [line.rstrip() for line in config.splitlines()]
                # Remove empty lines at the end
                while lines and not lines[-1]:
                    lines.pop()
                return "\n".join(lines) + "\n" if lines else ""

            new_config_normalized = normalize_config(config_content)
            current_config_normalized = (
                normalize_config(current_config) if current_config else ""
            )

            # Skip deployment if configs are identical
            if not force and new_config_normalized == current_config_normalized:
                logger.info(
                    f"⏭️  Configuration unchanged, skipping deployment to {self.base_url}"
                )
                add_span_attributes(deployment_skipped=True)
                record_span_event("deployment_skipped", {"reason": "config_unchanged"})

                # Get current version
                try:
                    client = self._get_client()
                    version_response = await _get_configuration_version(client)
                    version = str(version_response) if version_response else "unknown"
                    return {
                        "version": version,
                        "reload_triggered": False,
                        "reload_id": None,
                    }
                except Exception:
                    return {
                        "version": "unknown",
                        "reload_triggered": False,
                        "reload_id": None,
                    }

            # Deploy the configuration (it's different or forced)
            logger.info(
                f"📤 Deploying configuration to {self.base_url} (changed: {current_config is not None})"
            )
            add_span_attributes(
                deployment_skipped=False, config_changed=current_config is not None
            )
            result = await self.deploy_configuration(new_config_normalized)
            return result

    async def deploy_structured_configuration(
        self, changes: List[ConfigChange]
    ) -> Dict[str, Any]:
        """Deploy HAProxy configuration changes using granular dataplane API endpoints.

        This method applies a list of ConfigChange objects using HAProxy's structured
        API endpoints within a transaction, which minimizes reloads by only changing
        what's actually different.

        Args:
            changes: List of ConfigChange objects to apply

        Returns:
            Dict containing version, reload_triggered status, and reload_id

        Raises:
            DataplaneAPIError: If deployment fails
        """
        if not changes:
            logger.debug("⏭️  No changes to deploy")
            return {
                "version": "unchanged",
                "reload_triggered": False,
                "reload_id": None,
            }

        with trace_dataplane_operation("deploy_structured", self.base_url):
            add_span_attributes(
                dataplane_url=self.base_url,
                changes_count=len(changes),
                change_types=[str(c.change_type.value) for c in changes],
            )

            metrics = get_metrics_collector()
            client = self._get_client()

            # Separate server changes from other changes for runtime API optimization
            server_changes = [
                c
                for c in changes
                if c.element_type == ConfigElementType.SERVER
                and c.section_type == ConfigSectionType.BACKEND
            ]
            other_changes = [c for c in changes if c not in server_changes]

            # Sort server changes by name for consistent ordering (SRV_1, SRV_2, ..., SRV_10)
            server_changes.sort(key=lambda c: _natural_sort_key(c.element_id or ""))

            logger.debug(
                f"🔄 Separated changes: {len(server_changes)} server changes (runtime-eligible), "
                f"{len(other_changes)} other changes (transaction-required)"
            )

            # Apply server changes first WITHOUT transaction to enable runtime API
            runtime_failed_servers = []
            if server_changes:
                logger.info(
                    f"🏃 Applying {len(server_changes)} server changes via runtime-eligible path"
                )
                for i, change in enumerate(server_changes):
                    logger.debug(
                        f"🏃 Applying server change {i + 1}/{len(server_changes)}: {change}"
                    )
                    try:
                        await self._apply_server_without_transaction(client, change)
                    except Exception as server_error:
                        logger.warning(
                            f"⚠️  Runtime API failed for server {change.element_id}, will retry via transaction: {server_error}"
                        )
                        runtime_failed_servers.append(change)

                # If some servers failed runtime API, add them to other_changes for transaction
                if runtime_failed_servers:
                    logger.info(
                        f"🔄 {len(runtime_failed_servers)} server changes failed runtime API, will retry via transaction"
                    )
                    other_changes.extend(runtime_failed_servers)

                # Update success count
                successful_runtime_servers = len(server_changes) - len(
                    runtime_failed_servers
                )
                if successful_runtime_servers > 0:
                    logger.info(
                        f"✅ {successful_runtime_servers} server changes applied via runtime API"
                    )

            # Only use transaction if there are non-server changes
            if not other_changes:
                logger.info(
                    "✅ All changes were server changes applied via runtime API - no transaction needed"
                )
                # Get current version for return
                try:
                    version_response = await _get_configuration_version(client)
                    new_version = (
                        str(version_response) if version_response else "runtime-only"
                    )
                    record_span_event(
                        "runtime_only_deployment_successful",
                        {
                            "server_changes_count": len(server_changes),
                            "version": new_version,
                        },
                    )

                    # Runtime-only deployments don't trigger reloads
                    return {
                        "version": new_version,
                        "reload_triggered": False,
                        "reload_id": None,
                    }
                except Exception:
                    # Runtime-only fallback - no reload
                    return {
                        "version": "runtime-only",
                        "reload_triggered": False,
                        "reload_id": None,
                    }

            # Sort other_changes to ensure consistent ordering, especially for initial server creation
            other_changes.sort(
                key=lambda c: (
                    c.section_type.value if c.section_type else "",
                    c.section_name or "",
                    c.element_type.value if c.element_type else "",
                    _natural_sort_key(c.element_id or ""),
                )
            )

            # Start a transaction to batch remaining changes atomically
            try:
                # Get current configuration version for transaction consistency
                current_version = await _get_configuration_version(client)
                if current_version is None:
                    raise DataplaneAPIError(
                        "Failed to get current configuration version for transaction",
                        endpoint=self.base_url,
                        operation="get_configuration_version",
                    )

                # Start transaction with version
                with metrics.time_dataplane_api_operation("start_transaction"):
                    transaction = await start_transaction.asyncio(
                        client=client, version=current_version
                    )
                    transaction_id = transaction.id if transaction else None

                logger.debug(
                    f"📦 Started transaction {transaction_id} for {len(other_changes)} remaining changes"
                )

                try:
                    # Apply remaining changes within the transaction
                    for i, change in enumerate(other_changes):
                        logger.debug(
                            f"📝 Applying change {i + 1}/{len(other_changes)}: {change}"
                        )
                        await self._apply_config_change(
                            client, change, transaction_id or ""
                        )

                    # Commit the transaction
                    with metrics.time_dataplane_api_operation("commit_transaction"):
                        commit_response = await commit_transaction.asyncio_detailed(
                            client=client, id=transaction_id
                        )

                    logger.info(
                        f"✅ Successfully deployed {len(other_changes)} structured changes in transaction {transaction_id}"
                    )

                    # Get the new configuration version
                    version_response = await _get_configuration_version(client)
                    new_version = (
                        str(version_response) if version_response else "unknown"
                    )

                    record_span_event(
                        "structured_deployment_successful",
                        {
                            "transaction_id": transaction_id,
                            "changes_count": len(changes),
                            "server_changes_runtime": len(server_changes)
                            - len(runtime_failed_servers),
                            "server_changes_transaction": len(runtime_failed_servers),
                            "other_changes": len(other_changes)
                            - len(runtime_failed_servers),
                            "version": new_version,
                        },
                    )

                    # Check if transaction commit triggered a reload based on HTTP 202 status and Reload-ID header
                    reload_triggered = commit_response.status_code == 202
                    # Try different cases for Reload-ID header (HTTP headers are case-insensitive)
                    reload_id = None
                    if reload_triggered:
                        for header_name in [
                            "Reload-ID",
                            "reload-id",
                            "RELOAD-ID",
                            "reload_id",
                        ]:
                            reload_id = commit_response.headers.get(header_name)
                            if reload_id:
                                break

                    logger.debug(
                        f"🔍 Transaction commit response: status={commit_response.status_code}, "
                        f"reload_triggered={reload_triggered}, reload_id={reload_id}, "
                        f"headers={dict(commit_response.headers)}"
                    )

                    return {
                        "version": new_version,
                        "reload_triggered": reload_triggered,
                        "reload_id": reload_id,
                    }

                except Exception as apply_error:
                    # Rollback transaction on failure
                    try:
                        logger.warning(
                            f"⚠️  Rolling back transaction {transaction_id} due to error: {apply_error}"
                        )
                        await delete_transaction.asyncio(
                            client=client, id=transaction_id
                        )
                    except Exception as rollback_error:
                        logger.error(
                            f"❌ Failed to rollback transaction {transaction_id}: {rollback_error}"
                        )

                    record_span_event(
                        "structured_deployment_failed",
                        {"transaction_id": transaction_id, "error": str(apply_error)},
                    )
                    set_span_error(apply_error, "Structured deployment failed")

                    raise DataplaneAPIError(
                        f"Structured deployment failed in transaction {transaction_id}: {apply_error}",
                        endpoint=self.base_url,
                        operation="deploy_structured",
                        original_error=apply_error,
                    ) from apply_error

            except Exception as transaction_error:
                record_span_event(
                    "transaction_start_failed", {"error": str(transaction_error)}
                )
                set_span_error(transaction_error, "Failed to start transaction")

                raise DataplaneAPIError(
                    f"Failed to start transaction for structured deployment: {transaction_error}",
                    endpoint=self.base_url,
                    operation="deploy_structured",
                    original_error=transaction_error,
                ) from transaction_error

    async def _apply_server_without_transaction(
        self, client: Any, change: ConfigChange
    ) -> None:
        """Apply server changes directly without transaction to enable runtime API usage.

        This method calls the configuration API endpoints for servers without
        wrapping them in a transaction. This allows the Go dataplane API to
        automatically use the runtime API when possible (no default_server, etc.)
        which avoids HAProxy reloads.

        Args:
            client: The authenticated dataplane API client
            change: The server configuration change to apply
        """
        try:
            section_name = change.section_name

            # Get current configuration version for non-transactional operations
            # The DataPlane API requires EITHER transaction_id OR version parameter
            current_version = await _get_configuration_version(client)
            if current_version is None:
                raise DataplaneAPIError(
                    "Failed to get configuration version for runtime operation",
                    endpoint=self.base_url,
                    operation="get_version",
                    original_error=None,
                )

            # Prepare base parameters with version (not transaction_id)
            base_params = {
                "client": client,
                "parent_name": section_name,
                "version": current_version,
                # Note: Using version parameter enables runtime API usage
            }

            # Execute the appropriate server operation
            if change.change_type == ConfigChangeType.CREATE:
                clean_config = self._get_clean_config_object(change.new_config)
                # Ensure the server name is properly set from element_id
                if hasattr(clean_config, "name"):
                    clean_config.name = change.element_id
                logger.debug(
                    f"🏃 Sending server config: name={getattr(clean_config, 'name', None)}, address={getattr(clean_config, 'address', None)}"
                )
                params = {**base_params, "body": clean_config}

                # Use detailed response to check for HTTP errors
                response = await create_server_backend.asyncio_detailed(**params)
                if response.status_code >= 400:
                    error_content = (
                        response.content.decode()
                        if response.content
                        else "No error details"
                    )
                    raise DataplaneAPIError(
                        f"Server creation failed: {error_content}",
                        endpoint=self.base_url,
                        operation="create_server",
                        original_error=None,
                    )

            elif change.change_type == ConfigChangeType.UPDATE:
                clean_config = self._get_clean_config_object(change.new_config)
                if hasattr(clean_config, "name"):
                    clean_config.name = change.element_id

                # Check for non-runtime fields and warn user
                non_runtime_fields = has_non_runtime_fields(clean_config)
                if non_runtime_fields:
                    logger.warning(
                        f"⚠️ Server '{change.element_id}' update includes non-runtime parameters {non_runtime_fields} "
                        f"which will cause HAProxy reload. Consider using 'default-server' for parameters like 'check'."
                    )

                # Handle maintenance field for disabled servers
                # Check if server has 'disabled' field set
                if (
                    hasattr(clean_config, "disabled")
                    and clean_config.disabled is not None
                ):
                    # Server is disabled, set maintenance to enabled
                    clean_config.maintenance = ServerParamsMaintenance.ENABLED
                    logger.debug(
                        f"🔧 Converting disabled server '{change.element_id}' to maintenance mode"
                    )
                    # Remove the 'disabled' field as it's not runtime-compatible
                    clean_config.disabled = None

                params = {
                    **base_params,
                    "name": change.element_id,
                    "body": clean_config,
                }

                response = await replace_server_backend.asyncio_detailed(**params)
                if response.status_code >= 400:
                    error_content = (
                        response.content.decode()
                        if response.content
                        else "No error details"
                    )
                    raise DataplaneAPIError(
                        f"Server update failed: {error_content}",
                        endpoint=self.base_url,
                        operation="update_server",
                        original_error=None,
                    )

            elif change.change_type == ConfigChangeType.DELETE:
                params = {**base_params, "name": change.element_id}

                response = await delete_server_backend.asyncio_detailed(**params)
                if response.status_code >= 400:
                    error_content = (
                        response.content.decode()
                        if response.content
                        else "No error details"
                    )
                    raise DataplaneAPIError(
                        f"Server deletion failed: {error_content}",
                        endpoint=self.base_url,
                        operation="delete_server",
                        original_error=None,
                    )

            logger.debug(
                f"✅ Server {change.change_type.value} applied via runtime-eligible path: {change.element_id}"
            )

        except Exception as e:
            logger.debug(f"⚠️ Runtime API failed for server {change.element_id}: {e}")
            # Re-raise so deploy_structured_configuration can handle fallback
            raise

    async def _apply_runtime_map_operations(
        self, client: Any, map_file_path: str, map_changes: List[Any]
    ) -> None:
        """Apply map file changes using runtime API (no reload required).

        This method uses HAProxy's runtime map API to add, update, or delete
        map entries without requiring a configuration reload.

        Args:
            client: The authenticated dataplane API client
            map_file_path: Path to the map file (e.g., "/etc/haproxy/maps/host.map")
            map_changes: List of map entry changes to apply
        """
        try:
            # Extract just the filename from the full path for the API
            map_filename = os.path.basename(map_file_path)

            # The API endpoints automatically use runtime operations
            for change in map_changes:
                if hasattr(change, "operation"):
                    if change.operation == "add":
                        # Create OneMapEntry object for the API
                        entry = OneMapEntry(
                            key=change.key, value=getattr(change, "value", "")
                        )
                        await add_map_entry.asyncio(
                            client=client, parent_name=map_filename, body=entry
                        )
                        logger.debug(
                            f"🗺️  Added map entry to {map_filename}: {change.key}"
                        )
                    elif change.operation == "delete":
                        await delete_runtime_map_entry.asyncio(
                            client=client, parent_name=map_filename, id=change.key
                        )
                        logger.debug(
                            f"🗺️  Deleted map entry from {map_filename}: {change.key}"
                        )
                    elif change.operation == "replace":
                        # Create OneMapEntry object for replacement
                        entry = OneMapEntry(
                            key=change.key, value=getattr(change, "value", "")
                        )
                        await replace_runtime_map_entry.asyncio(
                            client=client,
                            parent_name=map_filename,
                            id=change.key,
                            body=entry,
                        )
                        logger.debug(
                            f"🗺️  Replaced map entry in {map_filename}: {change.key}"
                        )

        except Exception as e:
            logger.error(
                f"❌ Failed to apply runtime map operations to {map_file_path}"
            )
            raise DataplaneAPIError(
                f"Failed to apply runtime map operations to {map_file_path}: {e}",
                endpoint=self.base_url,
                operation="apply_runtime_map_operations",
                original_error=e,
            ) from e

    async def _apply_runtime_acl_operations(
        self, client: Any, acl_file_name: str, acl_changes: List[Any]
    ) -> None:
        """Apply ACL file changes using runtime API (no reload required).

        This method uses HAProxy's runtime ACL API to add or delete
        ACL entries without requiring a configuration reload.

        Args:
            client: The authenticated dataplane API client
            acl_file_name: Name of the ACL file
            acl_changes: List of ACL entry changes to apply
        """
        try:
            for change in acl_changes:
                if hasattr(change, "operation"):
                    if change.operation == "add":
                        # Create OneACLFileEntry object for the API
                        entry = OneACLFileEntry(value=change.data)
                        await post_services_haproxy_runtime_acls_parent_name_entries.asyncio(
                            client=client, parent_name=acl_file_name, body=entry
                        )
                        logger.debug(
                            f"🛡️  Added ACL entry to {acl_file_name}: {change.data}"
                        )
                    elif change.operation == "delete":
                        await delete_services_haproxy_runtime_acls_parent_name_entries_id.asyncio(
                            client=client, parent_name=acl_file_name, id=change.data
                        )
                        logger.debug(
                            f"🛡️  Deleted ACL entry from {acl_file_name}: {change.data}"
                        )
                    elif change.operation == "bulk_add":
                        # For bulk operations, use the payload endpoint
                        await add_payload_runtime_acl.asyncio(
                            client=client,
                            parent_name=acl_file_name,
                            body=change.payload,
                        )
                        logger.debug(f"🛡️  Bulk added ACL entries to {acl_file_name}")

        except Exception as e:
            logger.error(
                f"❌ Failed to apply runtime ACL operations to {acl_file_name}"
            )
            raise DataplaneAPIError(
                f"Failed to apply runtime ACL operations to {acl_file_name}: {e}",
                endpoint=self.base_url,
                operation="apply_runtime_acl_operations",
                original_error=e,
            ) from e

    async def _apply_nested_element_change(
        self, client: Any, change: ConfigChange, transaction_id: str
    ) -> None:
        """Apply a nested element change using the appropriate dataplane API endpoint.

        Args:
            client: The authenticated dataplane API client
            change: The nested element change to apply
            transaction_id: The transaction ID to use for the change
        """
        element_type = change.element_type
        section_type = change.section_type
        section_name = change.section_name

        try:
            # Look up handler configuration from registry
            if element_type is None:
                logger.warning(
                    "⚠️  Element type is None - skipping nested element change"
                )
                return

            handler_config = _ELEMENT_HANDLERS.get(element_type)
            if not handler_config:
                logger.warning(
                    f"⚠️  Unsupported nested element type for structured deployment: {element_type}"
                )
                return

            id_type = handler_config["id_type"]

            # Handle both registry formats: api_map (multiple sections) vs sections + api (single section type)
            if "api_map" in handler_config:
                # Multiple sections format
                api_map = dict(handler_config["api_map"])
                if section_type not in api_map:
                    logger.debug(
                        f"Element type {element_type} not supported for section type {section_type}"
                    )
                    return
                api_tuple = api_map[section_type]
                if not isinstance(api_tuple, (list, tuple)) or len(api_tuple) != 3:
                    logger.error(
                        f"Invalid API tuple for {element_type.value}/{section_type.value}"
                    )
                    return
                create_fn, replace_fn, delete_fn = (
                    api_tuple[0],
                    api_tuple[1],
                    api_tuple[2],
                )
            elif "sections" in handler_config and "api" in handler_config:
                # Single section type format
                if section_type not in handler_config["sections"]:
                    logger.debug(
                        f"Element type {element_type} not supported for section type {section_type}"
                    )
                    return
                create_fn, replace_fn, delete_fn = handler_config["api"]
            else:
                logger.error(
                    f"Invalid handler configuration for element type {element_type}"
                )
                return

            # Prepare common parameters
            base_params = {
                "client": client,
                "parent_name": section_name,
                "transaction_id": transaction_id,
            }

            # Execute the appropriate operation
            if change.change_type == ConfigChangeType.CREATE:
                clean_config = self._get_clean_config_object(change.new_config)
                params = {**base_params, "body": clean_config}
                if id_type == "index":
                    params["index"] = change.element_index
                await create_fn.asyncio(**params)

            elif change.change_type == ConfigChangeType.UPDATE:
                clean_config = self._get_clean_config_object(change.new_config)
                params = {**base_params, "body": clean_config}
                if id_type == "index":
                    params["index"] = change.element_index
                else:  # name
                    params["name"] = change.element_id
                await replace_fn.asyncio(**params)

            elif change.change_type == ConfigChangeType.DELETE:
                params = base_params.copy()
                if id_type == "index":
                    params["index"] = change.element_index
                else:  # name
                    params["name"] = change.element_id
                await delete_fn.asyncio(**params)

        except Exception as e:
            raise DataplaneAPIError(
                f"Failed to apply nested element change {change}: {e}",
                endpoint=self.base_url,
                operation=f"apply_{change.change_type.value}_{element_type.value if element_type else 'unknown'}",
                original_error=e,
            ) from e

    def _get_clean_config_object(self, config_obj: Any) -> Any:
        """Remove dynamically added attributes from config objects.

        This method ensures that only original model attributes are present
        when passing objects to the API, avoiding JSON serialization errors
        with dynamically added nested elements.

        Args:
            config_obj: The config object that may have extra attributes

        Returns:
            A clean config object suitable for API calls
        """
        if config_obj is None:
            return None

        # If it's a model object with to_dict/from_dict methods, use them
        # to create a clean copy with only the original schema attributes
        if hasattr(config_obj, "to_dict") and hasattr(config_obj, "from_dict"):
            try:
                # Get the clean dictionary representation (only original attributes)
                clean_dict = config_obj.to_dict()
                # Recreate the object from the dictionary
                return config_obj.__class__.from_dict(clean_dict)
            except Exception as e:
                logger.debug(
                    f"Failed to clean config object {type(config_obj).__name__}: {e}"
                )
                return config_obj

        # For non-model objects, return as-is
        return config_obj

    async def _apply_config_change(
        self, client: Any, change: ConfigChange, transaction_id: str
    ) -> None:
        """Apply a single configuration change using the appropriate dataplane API endpoint.

        Args:
            client: The authenticated dataplane API client
            change: The configuration change to apply
            transaction_id: The transaction ID to use for the change
        """
        try:
            # Handle nested element changes
            if change.element_type:
                await self._apply_nested_element_change(client, change, transaction_id)
                return

            # Handle top-level section changes using registry
            handler_config = _SECTION_HANDLERS.get(change.section_type)
            if not handler_config:
                logger.warning(
                    f"⚠️  Unsupported section type for structured deployment: {change.section_type}"
                )
                return

            # Prepare base parameters
            base_params = {
                "client": client,
                "transaction_id": transaction_id,
            }

            # Handle different change types
            if change.change_type == ConfigChangeType.CREATE:
                if not handler_config.get("supports_create", False):
                    if change.section_type == ConfigSectionType.GLOBAL:
                        # Global CREATE is treated as UPDATE
                        change.change_type = ConfigChangeType.UPDATE
                    else:
                        logger.debug(
                            f"Section type {change.section_type} doesn't support CREATE"
                        )
                        return

                if (
                    change.change_type == ConfigChangeType.CREATE
                ):  # Still CREATE after potential conversion
                    clean_config = self._get_clean_config_object(change.new_config)
                    params = {**base_params, "body": clean_config}
                    await handler_config["create"](**params)
                else:
                    # Fall through to UPDATE handling for converted GLOBAL operations
                    pass

            if change.change_type == ConfigChangeType.UPDATE:
                if not handler_config.get("supports_update", False):
                    logger.debug(
                        f"Section type {change.section_type} doesn't support UPDATE"
                    )
                    return

                # Handle different update strategies
                if handler_config.get("update_strategy") == "delete_create":
                    # Userlist: delete then create
                    if handler_config.get("supports_delete", False):
                        params = {**base_params}
                        if handler_config["id_field"]:
                            params[handler_config["id_field"]] = change.section_name
                        await handler_config["delete"](**params)

                    clean_config = self._get_clean_config_object(change.new_config)
                    params = {**base_params, "body": clean_config}
                    await handler_config["create"](**params)
                else:
                    # Standard update
                    clean_config = self._get_clean_config_object(change.new_config)
                    params = {**base_params, "body": clean_config}
                    if handler_config["id_field"]:
                        params[handler_config["id_field"]] = change.section_name
                    if handler_config.get("full_section"):
                        params["full_section"] = True
                    await handler_config["update"](**params)

            elif change.change_type == ConfigChangeType.DELETE:
                if not handler_config.get("supports_delete", False):
                    logger.debug(
                        f"Section type {change.section_type} doesn't support DELETE"
                    )
                    return

                params = {**base_params}
                if handler_config["id_field"]:
                    params[handler_config["id_field"]] = change.section_name
                await handler_config["delete"](**params)

        except Exception as e:
            raise DataplaneAPIError(
                f"Failed to apply {change}: {e}",
                endpoint=self.base_url,
                operation=f"apply_{change.change_type.value}_{change.section_type.value}",
                original_error=e,
            ) from e

    async def fetch_structured_configuration(self) -> Dict[str, Any]:
        """Fetch complete structured configuration components from this HAProxy instance.

        This method fetches both top-level configuration sections and all their detailed
        nested configurations using specialized endpoints, ensuring complete configuration
        comparison and deployment.

        Returns:
            Dictionary containing:
            - backends: List of backend configurations with nested details
            - frontends: List of frontend configurations with nested details
            - defaults: List of defaults sections with nested details
            - global: Global configuration section with nested details
            - userlists: List of userlist sections
            - caches: List of cache sections
            - mailers: List of mailers sections
            - resolvers: List of resolvers sections
            - peers: List of peer sections
            - fcgi_apps: List of fcgi-app sections with nested details
            - http_errors: List of http-errors sections
            - rings: List of ring sections
            - log_forwards: List of log-forward sections
            - programs: List of program sections

        Raises:
            DataplaneAPIError: If fetching configuration fails
        """
        metrics = get_metrics_collector()

        with metrics.time_dataplane_api_operation("fetch_structured"):
            client = self._get_client()

            try:
                # Fetch all top-level components with timing using helper
                backends = await _fetch_with_metrics(
                    "fetch_backends", get_backends.asyncio, client, metrics, []
                )
                frontends = await _fetch_with_metrics(
                    "fetch_frontends", get_frontends.asyncio, client, metrics, []
                )
                defaults = await _fetch_with_metrics(
                    "fetch_defaults", get_defaults_sections.asyncio, client, metrics, []
                )
                global_config = await _fetch_with_metrics(
                    "fetch_global", get_global.asyncio, client, metrics
                )
                userlists = await _fetch_with_metrics(
                    "fetch_userlists", get_userlists.asyncio, client, metrics, []
                )
                caches = await _fetch_with_metrics(
                    "fetch_caches", get_caches.asyncio, client, metrics, []
                )
                mailers = await _fetch_with_metrics(
                    "fetch_mailers", get_mailers_sections.asyncio, client, metrics, []
                )
                resolvers = await _fetch_with_metrics(
                    "fetch_resolvers", get_resolvers.asyncio, client, metrics, []
                )
                peers = await _fetch_with_metrics(
                    "fetch_peers", get_peer_sections.asyncio, client, metrics, []
                )
                fcgi_apps = await _fetch_with_metrics(
                    "fetch_fcgi_apps", get_fcgi_apps.asyncio, client, metrics, []
                )
                http_errors = await _fetch_with_metrics(
                    "fetch_http_errors",
                    get_http_errors_sections.asyncio,
                    client,
                    metrics,
                    [],
                )
                rings = await _fetch_with_metrics(
                    "fetch_rings", get_rings.asyncio, client, metrics, []
                )
                log_forwards = await _fetch_with_metrics(
                    "fetch_log_forwards", get_log_forwards.asyncio, client, metrics, []
                )
                programs = await _fetch_with_metrics(
                    "fetch_programs", get_programs.asyncio, client, metrics, []
                )

                # Create storage for nested elements to avoid modifying frozen models
                nested_elements: Dict[str, Dict[str, Dict[str, Any]]] = {
                    "backends": {},
                    "frontends": {},
                    "defaults": {},
                    "global": {},
                }

                # Now fetch detailed configurations for each section using registry-based approach
                section_configs = [
                    (ConfigSectionType.BACKEND, backends, "backends"),
                    (ConfigSectionType.FRONTEND, frontends, "frontends"),
                ]

                for section_type, sections, section_key in section_configs:
                    fetch_apis = _ELEMENT_FETCH_APIS.get(section_type, {})

                    for section in sections:
                        if hasattr(section, "name") and section.name:
                            section_name = section.name
                            nested_elements[section_key][section_name] = {}

                            try:
                                # Fetch all element types for this section
                                for attr_name, fetch_func in fetch_apis.items():
                                    if fetch_func is None:
                                        # Handle unsupported operations (like tcp_response_rules for frontends)
                                        nested_elements[section_key][section_name][
                                            attr_name
                                        ] = []
                                    else:
                                        nested_elements[section_key][section_name][
                                            attr_name
                                        ] = (
                                            await fetch_func(
                                                client=client, parent_name=section_name
                                            )
                                            or []
                                        )
                            except Exception as e:
                                logger.debug(
                                    f"Failed to fetch details for {section_type.value} {section_name}: {e}"
                                )
                                # Continue with other sections even if one fails

                # Skip nested element fetching for defaults sections
                # HAProxy Dataplane API v3 limitation: nested element endpoints for defaults sections
                # return HTTP 501 Not Implemented. Instead, defaults are handled as atomic units
                # using full_section=true in deployment operations.
                # The main defaults configuration already includes all nested elements.

                # Fetch nested elements for global configuration
                if global_config:
                    nested_elements["global"] = {}
                    global_fetch_apis = _ELEMENT_FETCH_APIS.get(
                        ConfigSectionType.GLOBAL, {}
                    )

                    try:
                        for attr_name, fetch_func in global_fetch_apis.items():
                            result = await fetch_func(client=client) or []
                            if isinstance(result, list):
                                nested_elements["global"][attr_name] = {}
                                for idx, item in enumerate(result):
                                    nested_elements["global"][attr_name][str(idx)] = (
                                        item
                                    )
                            else:
                                nested_elements["global"][attr_name] = {}
                    except Exception as e:
                        logger.debug(f"Failed to fetch global configuration: {e}")

                # Skip fcgi_apps nested elements for now - they have minimal nested configuration
                # and are not commonly used in most HAProxy setups

                # Record successful fetch
                metrics.record_dataplane_api_request("fetch_structured", "success")

                # Record component counts
                add_span_attributes(
                    backends_count=len(backends),
                    frontends_count=len(frontends),
                    defaults_count=len(defaults),
                    has_global=global_config is not None,
                    userlists_count=len(userlists),
                    caches_count=len(caches),
                    mailers_count=len(mailers),
                    resolvers_count=len(resolvers),
                    peers_count=len(peers),
                    fcgi_apps_count=len(fcgi_apps),
                    http_errors_count=len(http_errors),
                    rings_count=len(rings),
                    log_forwards_count=len(log_forwards),
                    programs_count=len(programs),
                )

                return {
                    "backends": backends,
                    "frontends": frontends,
                    "defaults": defaults,
                    "global": global_config,
                    "userlists": userlists,
                    "caches": caches,
                    "mailers": mailers,
                    "resolvers": resolvers,
                    "peers": peers,
                    "fcgi_apps": fcgi_apps,
                    "http_errors": http_errors,
                    "rings": rings,
                    "log_forwards": log_forwards,
                    "programs": programs,
                    "nested_elements": nested_elements,
                }
            except Exception as e:
                metrics.record_dataplane_api_request("fetch_structured", "error")
                _log_fetch_error("structured configuration", "all", e)
                raise DataplaneAPIError(
                    f"Failed to fetch structured configuration: {e}",
                    endpoint=self.base_url,
                    operation="fetch_structured",
                    original_error=e,
                ) from e
