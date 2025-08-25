"""Application constants for HAProxy Template IC.

This module centralizes magic numbers, strings, and configuration values
used throughout the application to improve maintainability and reduce
duplication.
"""

from typing import Final

# Port Numbers
DEFAULT_DATAPLANE_PORT: Final[int] = 5555
DEFAULT_HEALTH_PORT: Final[int] = 8404
DEFAULT_METRICS_PORT: Final[int] = 9090
DEFAULT_WEBHOOK_PORT: Final[int] = 9443
DEFAULT_HEALTHZ_PORT: Final[int] = 8080

# Timeouts (in seconds)
DEFAULT_API_TIMEOUT: Final[float] = 30.0
CONNECT_TIMEOUT_MS: Final[int] = 5000
CLIENT_TIMEOUT_MS: Final[int] = 50000
SERVER_TIMEOUT_MS: Final[int] = 50000

# Retry Configuration
MAX_RETRY_WAIT_SECONDS: Final[int] = 30
INITIAL_RETRY_WAIT_SECONDS: Final[int] = 2
DEFAULT_RETRY_JITTER: Final[bool] = True

# Index Names (used for kopf indexing)
HAPROXY_PODS_INDEX: Final[str] = "haproxy_pods"

# Instance Types (for metrics)
INSTANCE_TYPE_PRODUCTION: Final[str] = "production"
INSTANCE_TYPE_VALIDATION: Final[str] = "validation"

# Content Types (for template rendering)
CONTENT_TYPE_MAP: Final[str] = "map"
CONTENT_TYPE_CERTIFICATE: Final[str] = "certificate"
CONTENT_TYPE_FILE: Final[str] = "file"
CONTENT_TYPE_HAPROXY_CONFIG: Final[str] = "haproxy_config"

# Authentication Defaults
DEFAULT_DATAPLANE_USERNAME: Final[str] = "admin"
DEFAULT_DATAPLANE_PASSWORD: Final[str] = "adminpass"
DEFAULT_VALIDATION_USERNAME: Final[str] = "admin"
DEFAULT_VALIDATION_PASSWORD: Final[str] = "validationpass"

# Path Constants
NAMESPACE_FILE_PATH: Final[str] = (
    "/var/run/secrets/kubernetes.io/serviceaccount/namespace"
)
DEFAULT_SOCKET_PATH: Final[str] = "/run/haproxy-template-ic/management.sock"

# Kubernetes Resource Limits
MAX_K8S_NAME_LENGTH: Final[int] = 253

# HAProxy Version API Path
DATAPLANE_API_VERSION: Final[str] = "v3"

# Error Severity Levels
ERROR_LEVEL_CRITICAL: Final[str] = "critical"
ERROR_LEVEL_WARNING: Final[str] = "warning"
ERROR_LEVEL_INFO: Final[str] = "info"

# Configuration Template Types
TEMPLATE_TYPE_HAPROXY: Final[str] = "haproxy"
TEMPLATE_TYPE_MAP: Final[str] = "map"
TEMPLATE_TYPE_CERTIFICATE: Final[str] = "certificate"
TEMPLATE_TYPE_FILE: Final[str] = "file"

# Cache Configuration
TEMPLATE_CACHE_SIZE: Final[int] = 256
LOGGING_CACHE_SIZE: Final[int] = 128

# Buffer Sizes
SOCKET_BUFFER_SIZE: Final[int] = 1024

# Error Message Templates
ERROR_TEMPLATE_SYNTAX: Final[str] = "Template syntax error: {error}"
ERROR_TEMPLATE_RENDER: Final[str] = "Template rendering failed: {error}"
ERROR_TEMPLATE_COMPILATION: Final[str] = "Template compilation failed: {error}"
ERROR_TEMPLATE_SNIPPET_NOT_FOUND: Final[str] = "Template snippet not found: {error}"
ERROR_TEMPLATE_INVALID_SYNTAX: Final[str] = "Invalid template syntax: {error}"
ERROR_TEMPLATE_GENERIC: Final[str] = "Template error: {error}"
ERROR_MISSING_CREDENTIALS: Final[str] = "Missing/invalid credential fields: {fields}"
