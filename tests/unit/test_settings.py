"""
Tests for application settings with environment variable support.
"""

import os
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest
from pydantic import ValidationError

from haproxy_template_ic.settings import (
    ApplicationSettings,
    TracingSettings,
    WebhookSettings,
    get_application_settings,
    export_settings_schema,
    validate_environment_config,
)


class TestTracingSettings:
    """Test tracing configuration settings."""

    def test_default_values(self):
        """Test default tracing settings."""
        settings = TracingSettings()

        assert settings.enabled is False
        assert settings.service_name == "haproxy-template-ic"
        assert settings.service_version == "1.0.0"
        assert settings.jaeger_endpoint is None
        assert settings.sample_rate == 1.0
        assert settings.console_export is False

    def test_environment_variables(self):
        """Test loading tracing settings from environment variables."""
        env_vars = {
            "TRACING_ENABLED": "true",
            "TRACING_SERVICE_NAME": "test-service",
            "TRACING_SERVICE_VERSION": "2.0.0",
            "TRACING_JAEGER_ENDPOINT": "jaeger:14268",
            "TRACING_SAMPLE_RATE": "0.5",
            "TRACING_CONSOLE_EXPORT": "true",
        }

        with patch.dict(os.environ, env_vars):
            settings = TracingSettings()

            assert settings.enabled is True
            assert settings.service_name == "test-service"
            assert settings.service_version == "2.0.0"
            assert settings.jaeger_endpoint == "jaeger:14268"
            assert settings.sample_rate == 0.5
            assert settings.console_export is True

    def test_sample_rate_validation(self):
        """Test sample rate validation."""
        # Valid range
        settings = TracingSettings(sample_rate=0.0)
        assert settings.sample_rate == 0.0

        settings = TracingSettings(sample_rate=1.0)
        assert settings.sample_rate == 1.0

        # Invalid range
        with pytest.raises(ValidationError) as exc_info:
            TracingSettings(sample_rate=-0.1)
        assert "greater than or equal to 0" in str(exc_info.value)

        with pytest.raises(ValidationError) as exc_info:
            TracingSettings(sample_rate=1.1)
        assert "less than or equal to 1" in str(exc_info.value)


class TestWebhookSettings:
    """Test webhook configuration settings."""

    def test_default_values(self):
        """Test default webhook settings."""
        settings = WebhookSettings()

        assert settings.enabled is False
        assert settings.port == 9443
        assert settings.cert_dir == Path("/tmp/webhook-certs")

    def test_environment_variables(self):
        """Test loading webhook settings from environment variables."""
        env_vars = {
            "WEBHOOK_ENABLED": "true",
            "WEBHOOK_PORT": "8443",
            "WEBHOOK_CERT_DIR": "/etc/certs",
        }

        with patch.dict(os.environ, env_vars):
            settings = WebhookSettings()

            assert settings.enabled is True
            assert settings.port == 8443
            assert settings.cert_dir == Path("/etc/certs")

    def test_port_validation(self):
        """Test webhook port validation."""
        # Valid port
        settings = WebhookSettings(port=8443)
        assert settings.port == 8443

        # Invalid ports
        with pytest.raises(ValidationError) as exc_info:
            WebhookSettings(port=80)  # Below 1024
        assert "greater than or equal to 1024" in str(exc_info.value)

        with pytest.raises(ValidationError) as exc_info:
            WebhookSettings(port=70000)  # Above 65535
        assert "less than or equal to 65535" in str(exc_info.value)


class TestApplicationSettings:
    """Test main application settings."""

    def test_required_configmap_name(self):
        """Test that configmap_name is required."""
        with pytest.raises(ValidationError) as exc_info:
            ApplicationSettings()
        assert "configmap_name" in str(exc_info.value)

    def test_default_values(self):
        """Test default application settings."""
        settings = ApplicationSettings(configmap_name="test-config")

        assert settings.configmap_name == "test-config"
        assert settings.healthz_port == 8080
        assert settings.metrics_port == 9090
        assert settings.verbose == 0
        assert settings.structured_logging is False
        assert settings.socket_path == Path("/run/haproxy-template-ic/management.sock")
        assert settings.development_mode is False
        assert settings.api_key is None

    def test_environment_variables(self):
        """Test loading settings from environment variables."""
        env_vars = {
            "CONFIGMAP_NAME": "my-config",
            "HEALTHZ_PORT": "8081",
            "METRICS_PORT": "9091",
            "VERBOSE": "2",
            "STRUCTURED_LOGGING": "true",
            "SOCKET_PATH": "/tmp/test.sock",
            "DEVELOPMENT_MODE": "true",
            "API_KEY": "secret-key",
        }

        with patch.dict(os.environ, env_vars):
            settings = ApplicationSettings()

            assert settings.configmap_name == "my-config"
            assert settings.healthz_port == 8081
            assert settings.metrics_port == 9091
            assert settings.verbose == 2
            assert settings.structured_logging is True
            assert settings.socket_path == Path("/tmp/test.sock")
            assert settings.development_mode is True
            assert settings.api_key.get_secret_value() == "secret-key"

    def test_nested_settings(self):
        """Test nested settings configuration."""
        env_vars = {
            "CONFIGMAP_NAME": "test-config",
            "TRACING_ENABLED": "true",
            "TRACING_SERVICE_NAME": "test-service",
            "WEBHOOK_ENABLED": "true",
            "WEBHOOK_PORT": "8443",
        }

        with patch.dict(os.environ, env_vars):
            settings = ApplicationSettings()

            assert settings.tracing.enabled is True
            assert settings.tracing.service_name == "test-service"
            assert settings.webhook.enabled is True
            assert settings.webhook.port == 8443

    def test_configmap_name_validation(self):
        """Test ConfigMap name validation."""
        # Valid names
        valid_names = [
            "test-config",
            "my.config",
            "config123",
            "a",
            "a" * 253,  # Max length
        ]

        for name in valid_names:
            settings = ApplicationSettings(configmap_name=name)
            assert settings.configmap_name == name

        # Invalid names
        invalid_names = [
            "",  # Empty
            "Test-Config",  # Uppercase
            "-config",  # Starts with hyphen
            "config-",  # Ends with hyphen
            ".config",  # Starts with dot
            "config.",  # Ends with dot
            "a" * 254,  # Too long
            "config_name",  # Underscore not allowed
        ]

        for name in invalid_names:
            with pytest.raises(ValidationError):
                ApplicationSettings(configmap_name=name)

    def test_port_validation(self):
        """Test port number validation."""
        # Valid ports
        settings = ApplicationSettings(
            configmap_name="test", healthz_port=8080, metrics_port=9090
        )
        assert settings.healthz_port == 8080
        assert settings.metrics_port == 9090

        # Invalid ports
        with pytest.raises(ValidationError):
            ApplicationSettings(
                configmap_name="test",
                healthz_port=80,  # Below 1024
            )

        with pytest.raises(ValidationError):
            ApplicationSettings(
                configmap_name="test",
                metrics_port=70000,  # Above 65535
            )

    def test_verbose_level_validation(self):
        """Test verbose level validation."""
        # Valid levels
        for level in [0, 1, 2]:
            settings = ApplicationSettings(configmap_name="test", verbose=level)
            assert settings.verbose == level

        # Invalid levels
        for level in [-1, 3, 10]:
            with pytest.raises(ValidationError):
                ApplicationSettings(configmap_name="test", verbose=level)

    def test_socket_path_validation(self):
        """Test socket path validation and directory creation."""
        with tempfile.TemporaryDirectory() as temp_dir:
            socket_path = Path(temp_dir) / "subdir" / "test.sock"

            settings = ApplicationSettings(
                configmap_name="test", socket_path=socket_path
            )

            assert settings.socket_path == socket_path
            # Parent directory should be created
            assert socket_path.parent.exists()


class TestUtilityFunctions:
    """Test utility functions for settings management."""

    def test_get_application_settings(self):
        """Test get_application_settings function."""
        with patch.dict(os.environ, {"CONFIGMAP_NAME": "test-config"}):
            settings = get_application_settings()
            assert isinstance(settings, ApplicationSettings)
            assert settings.configmap_name == "test-config"

    def test_export_settings_schema(self):
        """Test schema export function."""
        schema = export_settings_schema()

        assert isinstance(schema, dict)
        assert "properties" in schema
        assert "configmap_name" in schema["properties"]
        assert "healthz_port" in schema["properties"]
        assert "tracing" in schema["properties"]
        assert "webhook" in schema["properties"]

    def test_validate_environment_config(self):
        """Test environment configuration validation."""
        with patch.dict(os.environ, {"CONFIGMAP_NAME": "test-config"}):
            settings, warnings = validate_environment_config()

            assert isinstance(settings, ApplicationSettings)
            assert isinstance(warnings, list)
            assert settings.configmap_name == "test-config"

    def test_validate_environment_config_warnings(self):
        """Test configuration warnings generation."""
        env_vars = {
            "CONFIGMAP_NAME": "test-config",
            "WEBHOOK_ENABLED": "true",  # Webhook enabled but no cert dir
            "TRACING_ENABLED": "true",  # Tracing enabled but no jaeger endpoint
            "DEVELOPMENT_MODE": "true",  # Dev mode but verbose=0
        }

        with patch.dict(os.environ, env_vars):
            settings, warnings = validate_environment_config()

            assert len(warnings) >= 2  # Should have warnings
            warning_text = " ".join(warnings)
            assert "cert directory" in warning_text or "Jaeger endpoint" in warning_text

    def test_validate_environment_config_error(self):
        """Test configuration validation with errors."""
        # Missing required field
        with pytest.raises(ValueError) as exc_info:
            validate_environment_config()
        assert "validation failed" in str(exc_info.value)


class TestEnvironmentVariableOverrides:
    """Test environment variable override behavior."""

    def test_case_insensitive_env_vars(self):
        """Test that environment variables are case insensitive."""
        env_vars = {
            "configmap_name": "test-config",  # lowercase
            "HEALTHZ_PORT": "8081",  # uppercase
            "Metrics_Port": "9091",  # mixed case
        }

        with patch.dict(os.environ, env_vars):
            settings = ApplicationSettings()

            assert settings.configmap_name == "test-config"
            assert settings.healthz_port == 8081
            # Note: Mixed case might not work depending on OS

    def test_nested_environment_variables(self):
        """Test nested configuration with delimiters."""
        env_vars = {
            "CONFIGMAP_NAME": "test-config",
            "TRACING__ENABLED": "true",
            "TRACING__SERVICE_NAME": "nested-service",
            "WEBHOOK__PORT": "8443",
        }

        with patch.dict(os.environ, env_vars):
            settings = ApplicationSettings()

            assert settings.tracing.enabled is True
            assert settings.tracing.service_name == "nested-service"
            assert settings.webhook.port == 8443

    def test_type_coercion(self):
        """Test automatic type coercion from environment variables."""
        env_vars = {
            "CONFIGMAP_NAME": "test-config",
            "HEALTHZ_PORT": "8080",  # String to int
            "STRUCTURED_LOGGING": "true",  # String to bool
            "VERBOSE": "2",  # String to int
            "TRACING__SAMPLE_RATE": "0.5",  # String to float
        }

        with patch.dict(os.environ, env_vars):
            settings = ApplicationSettings()

            assert isinstance(settings.healthz_port, int)
            assert settings.healthz_port == 8080
            assert isinstance(settings.structured_logging, bool)
            assert settings.structured_logging is True
            assert isinstance(settings.verbose, int)
            assert settings.verbose == 2
            assert isinstance(settings.tracing.sample_rate, float)
            assert settings.tracing.sample_rate == 0.5
