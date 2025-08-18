"""
Application settings with environment variable support using Pydantic BaseSettings.

This module provides runtime configuration management with automatic environment
variable loading, validation, and type coercion.
"""

from typing import Optional, Union
from pathlib import Path

from pydantic import Field, field_validator, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class TracingSettings(BaseSettings):
    """Distributed tracing configuration settings."""

    model_config = SettingsConfigDict(env_prefix="TRACING_", env_file_encoding="utf-8")

    enabled: bool = Field(
        False, description="Enable distributed tracing with OpenTelemetry"
    )
    service_name: str = Field(
        "haproxy-template-ic", description="Service name for distributed tracing"
    )
    service_version: str = Field(
        "1.0.0", description="Service version for distributed tracing"
    )
    jaeger_endpoint: Optional[str] = Field(
        None, description="Jaeger collector endpoint (e.g., 'jaeger:14268')"
    )
    sample_rate: float = Field(
        1.0, ge=0.0, le=1.0, description="Sampling rate from 0.0 to 1.0"
    )
    console_export: bool = Field(
        False, description="Enable console trace export for development"
    )


class WebhookSettings(BaseSettings):
    """Webhook server configuration settings."""

    model_config = SettingsConfigDict(env_prefix="WEBHOOK_", env_file_encoding="utf-8")

    enabled: bool = Field(False, description="Enable validating admission webhooks")
    port: int = Field(9443, ge=1024, le=65535, description="Webhook server port")
    cert_dir: Path = Field(
        Path("/tmp/webhook-certs"),  # nosec B108 - Standard K8s volume mount path
        description="Directory containing webhook TLS certificates",
    )


class ApplicationSettings(BaseSettings):
    """Main application settings with environment variable support."""

    model_config = SettingsConfigDict(
        env_file_encoding="utf-8",
        case_sensitive=False,
        env_nested_delimiter="__",
    )

    # Core configuration - using env in model_config
    configmap_name: str = Field(
        description="Name of the Kubernetes ConfigMap used for configuration"
    )

    # Server ports
    healthz_port: int = Field(
        8080,
        ge=1024,
        le=65535,
        description="Port for health check endpoint",
    )
    metrics_port: int = Field(
        9090,
        ge=1024,
        le=65535,
        description="Port for Prometheus metrics endpoint",
    )

    # Logging and debugging
    verbose: int = Field(
        0,
        ge=0,
        le=2,
        description="Verbosity level: 0=WARNING, 1=INFO, 2=DEBUG",
    )
    structured_logging: bool = Field(
        False,
        description="Enable structured JSON logging output",
    )

    # File paths
    socket_path: Path = Field(
        Path("/run/haproxy-template-ic/management.sock"),
        description="Path for management socket to expose internal state",
    )

    # Feature flags
    development_mode: bool = Field(
        False,
        description="Enable development mode with additional debugging",
    )

    # Nested settings
    tracing: TracingSettings = Field(
        default_factory=lambda: TracingSettings(),  # type: ignore[call-arg]
        description="Distributed tracing configuration",
    )
    webhook: WebhookSettings = Field(
        default_factory=lambda: WebhookSettings(),  # type: ignore[call-arg]
        description="Webhook server configuration",
    )

    # Security
    api_key: Optional[SecretStr] = Field(
        None, description="API key for secure operations (if required)"
    )

    @field_validator("socket_path")
    @classmethod
    def validate_socket_path(cls, v: Union[str, Path]) -> Path:
        """Validate that socket path directory exists or can be created."""
        if isinstance(v, str):
            v = Path(v)

        # Ensure parent directory exists for socket creation
        if not v.parent.exists():
            try:
                v.parent.mkdir(parents=True, exist_ok=True)
            except PermissionError:
                # In production, the directory should already exist
                # This is mainly for development environments
                pass

        return v

    @field_validator("configmap_name")
    @classmethod
    def validate_configmap_name(cls, v: str) -> str:
        """Validate ConfigMap name follows Kubernetes naming conventions."""
        if not v:
            raise ValueError("ConfigMap name cannot be empty")

        # Basic Kubernetes resource name validation
        if len(v) > 253:
            raise ValueError("ConfigMap name too long (max 253 characters)")

        # Allow alphanumeric, hyphens, and dots
        import re

        if not re.match(r"^[a-z0-9]([a-z0-9\-\.]*[a-z0-9])?$", v):
            raise ValueError(
                "ConfigMap name must be lowercase alphanumeric with hyphens and dots"
            )

        return v

    model_config = SettingsConfigDict(
        # Enable validation on assignment for runtime changes
        validate_assignment=True,
        # Use enum values for better serialization
        use_enum_values=True,
        # Configure environment variable loading
        env_file=".env",
        env_file_encoding="utf-8",
        env_nested_delimiter="__",
        case_sensitive=False,
        # Allow extra environment variables for extensibility
        extra="ignore",
    )


def get_application_settings() -> ApplicationSettings:
    """
    Load application settings from environment variables.

    This is a convenience function that creates and returns the application
    settings, loading values from environment variables and .env files.

    Returns:
        ApplicationSettings: Configured application settings

    Raises:
        ValidationError: If configuration validation fails
    """
    return ApplicationSettings()  # type: ignore[call-arg]


def export_settings_schema() -> dict:
    """
    Export the JSON schema for application settings.

    This can be used for documentation generation, configuration validation,
    or IDE support.

    Returns:
        dict: JSON schema for ApplicationSettings
    """
    return ApplicationSettings.model_json_schema()


def validate_environment_config() -> tuple[ApplicationSettings, list[str]]:
    """
    Validate environment configuration and return warnings.

    Returns:
        tuple: (settings, warnings) where warnings is a list of validation warnings
    """
    warnings = []

    try:
        settings = ApplicationSettings()  # type: ignore[call-arg]

        # Check for common configuration issues
        if settings.webhook.enabled and not settings.webhook.cert_dir.exists():
            warnings.append(
                f"Webhook enabled but cert directory doesn't exist: {settings.webhook.cert_dir}"
            )

        if settings.tracing.enabled and not settings.tracing.jaeger_endpoint:
            warnings.append("Tracing enabled but no Jaeger endpoint configured")

        if settings.development_mode and settings.verbose < 1:
            warnings.append("Development mode enabled but verbose logging disabled")

        return settings, warnings

    except Exception as e:
        # Re-raise validation errors with context
        raise ValueError(f"Environment configuration validation failed: {e}") from e
