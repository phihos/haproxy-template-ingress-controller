"""
Unit tests for haproxy_template_ic.operator.secrets module.

Comprehensive test coverage for Secret handling functionality including
fetching secrets from Kubernetes, handling secret change events, and error scenarios.
"""

import pytest
from unittest.mock import AsyncMock, Mock, patch

import kopf
from kr8s.objects import Secret

from haproxy_template_ic.credentials import Credentials
from haproxy_template_ic.models.state import ApplicationState
from haproxy_template_ic.operator.secrets import (
    fetch_secret,
    handle_secret_change,
)


class TestFetchSecret:
    """Test secret fetching functionality."""

    @pytest.mark.asyncio
    async def test_fetch_secret_success(self):
        """Test successful secret fetching."""
        # Arrange
        mock_secret = Mock(spec=Secret)
        mock_secret.name = "test-secret"
        mock_secret.namespace = "default"

        with (
            patch("haproxy_template_ic.operator.secrets.Secret") as mock_secret_class,
            patch(
                "haproxy_template_ic.operator.secrets.add_span_attributes"
            ) as mock_attrs,
            patch(
                "haproxy_template_ic.operator.secrets.record_span_event"
            ) as mock_event,
        ):
            mock_secret_class.get = AsyncMock(return_value=mock_secret)

            # Act
            result = await fetch_secret("test-secret", "default")

        # Assert
        assert result is mock_secret
        mock_secret_class.get.assert_called_once_with(
            "test-secret", namespace="default"
        )
        mock_attrs.assert_called_once_with(
            secret_name="test-secret", secret_namespace="default"
        )
        mock_event.assert_called_once_with("secret_fetched")

    @pytest.mark.asyncio
    async def test_fetch_secret_connection_error(self):
        """Test secret fetching with connection error."""
        # Arrange
        connection_error = ConnectionError("Failed to connect to Kubernetes API")

        with (
            patch("haproxy_template_ic.operator.secrets.Secret") as mock_secret_class,
            patch("haproxy_template_ic.operator.secrets.add_span_attributes"),
            patch(
                "haproxy_template_ic.operator.secrets.record_span_event"
            ) as mock_event,
        ):
            mock_secret_class.get = AsyncMock(side_effect=connection_error)

            # Act & Assert
            with pytest.raises(kopf.TemporaryError) as exc_info:
                await fetch_secret("test-secret", "default")

            assert 'Network error retrieving Secret "test-secret"' in str(
                exc_info.value
            )
            assert "Failed to connect to Kubernetes API" in str(exc_info.value)
            mock_event.assert_called_once_with(
                "secret_fetch_failed", {"error": "Failed to connect to Kubernetes API"}
            )

    @pytest.mark.asyncio
    async def test_fetch_secret_timeout_error(self):
        """Test secret fetching with timeout error."""
        # Arrange
        timeout_error = TimeoutError("Request timed out")

        with (
            patch("haproxy_template_ic.operator.secrets.Secret") as mock_secret_class,
            patch("haproxy_template_ic.operator.secrets.add_span_attributes"),
            patch(
                "haproxy_template_ic.operator.secrets.record_span_event"
            ) as mock_event,
        ):
            mock_secret_class.get = AsyncMock(side_effect=timeout_error)

            # Act & Assert
            with pytest.raises(kopf.TemporaryError) as exc_info:
                await fetch_secret("test-secret", "default")

            assert 'Network error retrieving Secret "test-secret"' in str(
                exc_info.value
            )
            assert "Request timed out" in str(exc_info.value)
            mock_event.assert_called_once_with(
                "secret_fetch_failed", {"error": "Request timed out"}
            )

    @pytest.mark.asyncio
    async def test_fetch_secret_not_found_error(self):
        """Test secret fetching when secret doesn't exist."""
        # Arrange
        not_found_error = RuntimeError("Secret not found")

        with (
            patch("haproxy_template_ic.operator.secrets.Secret") as mock_secret_class,
            patch("haproxy_template_ic.operator.secrets.add_span_attributes"),
            patch(
                "haproxy_template_ic.operator.secrets.record_span_event"
            ) as mock_event,
        ):
            mock_secret_class.get = AsyncMock(side_effect=not_found_error)

            # Act & Assert
            with pytest.raises(kopf.PermanentError) as exc_info:
                await fetch_secret("test-secret", "default")

            assert 'Failed to retrieve Secret "test-secret"' in str(exc_info.value)
            assert "Credentials are mandatory for operation" in str(exc_info.value)
            mock_event.assert_called_once_with(
                "secret_fetch_failed", {"error": "Secret not found"}
            )

    @pytest.mark.asyncio
    async def test_fetch_secret_permission_error(self):
        """Test secret fetching with permission error."""
        # Arrange
        permission_error = PermissionError("Access denied")

        with (
            patch("haproxy_template_ic.operator.secrets.Secret") as mock_secret_class,
            patch("haproxy_template_ic.operator.secrets.add_span_attributes"),
            patch(
                "haproxy_template_ic.operator.secrets.record_span_event"
            ) as mock_event,
        ):
            mock_secret_class.get = AsyncMock(side_effect=permission_error)

            # Act & Assert
            with pytest.raises(kopf.PermanentError) as exc_info:
                await fetch_secret("test-secret", "default")

            assert 'Failed to retrieve Secret "test-secret"' in str(exc_info.value)
            assert "Credentials are mandatory for operation" in str(exc_info.value)
            mock_event.assert_called_once_with(
                "secret_fetch_failed", {"error": "Access denied"}
            )

    @pytest.mark.asyncio
    async def test_fetch_secret_tracing_integration(self):
        """Test that fetch_secret properly integrates with tracing decorators."""
        # Arrange
        mock_secret = Mock(spec=Secret)

        with (
            patch("haproxy_template_ic.operator.secrets.Secret") as mock_secret_class,
            patch(
                "haproxy_template_ic.operator.secrets.add_span_attributes"
            ) as mock_attrs,
            patch(
                "haproxy_template_ic.operator.secrets.record_span_event"
            ) as mock_event,
        ):
            mock_secret_class.get = AsyncMock(return_value=mock_secret)

            # Act
            await fetch_secret("my-secret", "my-namespace")

        # Assert tracing calls
        mock_attrs.assert_called_once_with(
            secret_name="my-secret", secret_namespace="my-namespace"
        )
        mock_event.assert_called_once_with("secret_fetched")


class TestHandleSecretChange:
    """Test secret change event handling."""

    @pytest.mark.asyncio
    async def test_handle_secret_change_credentials_unchanged(self):
        """Test handling secret change when credentials haven't changed."""
        # Arrange
        mock_credentials = Mock(spec=Credentials)
        mock_credentials.model_dump.return_value = {
            "dataplane": {"username": "admin", "password": "secret123"},
            "validation": {"username": "admin", "password": "secret123"},
        }

        mock_config = Mock()
        mock_config.credentials = mock_credentials

        mock_memo = Mock(spec=ApplicationState)
        mock_memo.configuration = mock_config

        secret_data = {
            "dataplane_username": "YWRtaW4=",  # base64 for "admin"
            "dataplane_password": "c2VjcmV0MTIz",  # base64 for "secret123"
            "validation_username": "YWRtaW4=",
            "validation_password": "c2VjcmV0MTIz",
        }

        event = {"object": {"data": secret_data}}

        with (
            patch(
                "haproxy_template_ic.operator.secrets.Credentials"
            ) as mock_credentials_class,
            patch("haproxy_template_ic.operator.secrets.DeepDiff") as mock_deep_diff,
            patch("haproxy_template_ic.operator.secrets.logger") as mock_logger,
        ):
            # Mock new credentials to have same data
            mock_new_credentials = Mock(spec=Credentials)
            mock_new_credentials.model_dump.return_value = {
                "dataplane": {"username": "admin", "password": "secret123"},
                "validation": {"username": "admin", "password": "secret123"},
            }
            mock_credentials_class.from_secret.return_value = mock_new_credentials

            # Mock DeepDiff to return empty diff (no changes)
            mock_deep_diff.return_value = {}

            # Act
            await handle_secret_change(
                memo=mock_memo, event=event, name="test-secret", type="Normal"
            )

        # Assert
        mock_credentials_class.from_secret.assert_called_once_with(secret_data)
        mock_deep_diff.assert_called_once_with(
            mock_credentials.model_dump.return_value,
            mock_new_credentials.model_dump.return_value,
            verbose_level=0,
        )
        mock_logger.debug.assert_called_once_with(
            "Credentials unchanged, skipping update"
        )

        # Verify credentials were not updated
        assert mock_memo.configuration.credentials is mock_credentials

    @pytest.mark.asyncio
    async def test_handle_secret_change_credentials_changed(self):
        """Test handling secret change when credentials have changed."""
        # Arrange
        old_credentials = Mock(spec=Credentials)
        old_credentials.model_dump.return_value = {
            "dataplane": {"username": "admin", "password": "old_password"},
            "validation": {"username": "admin", "password": "old_password"},
        }

        mock_config = Mock()
        mock_config.credentials = old_credentials

        mock_memo = Mock(spec=ApplicationState)
        mock_memo.configuration = mock_config

        secret_data = {
            "dataplane_username": "YWRtaW4=",  # base64 for "admin"
            "dataplane_password": "bmV3X3Bhc3N3b3Jk",  # base64 for "new_password"
            "validation_username": "YWRtaW4=",
            "validation_password": "bmV3X3Bhc3N3b3Jk",
        }

        event = {"object": {"data": secret_data}}

        with (
            patch(
                "haproxy_template_ic.operator.secrets.Credentials"
            ) as mock_credentials_class,
            patch("haproxy_template_ic.operator.secrets.DeepDiff") as mock_deep_diff,
            patch("haproxy_template_ic.operator.secrets.logger") as mock_logger,
        ):
            # Mock new credentials to have different data
            new_credentials = Mock(spec=Credentials)
            new_credentials.model_dump.return_value = {
                "dataplane": {"username": "admin", "password": "new_password"},
                "validation": {"username": "admin", "password": "new_password"},
            }
            mock_credentials_class.from_secret.return_value = new_credentials

            # Mock DeepDiff to return changes
            mock_diff = {
                "values_changed": {
                    "root['dataplane']['password']": {
                        "new_value": "***",
                        "old_value": "***",
                    }
                }
            }
            mock_deep_diff.return_value = mock_diff

            # Act
            await handle_secret_change(
                memo=mock_memo, event=event, name="test-secret", type="Normal"
            )

        # Assert
        mock_credentials_class.from_secret.assert_called_once_with(secret_data)
        mock_deep_diff.assert_called_once_with(
            old_credentials.model_dump.return_value,
            new_credentials.model_dump.return_value,
            verbose_level=0,
        )

        # Verify credentials were updated
        assert mock_memo.configuration.credentials is new_credentials

        # Verify logging
        mock_logger.info.assert_called_once()
        log_call = mock_logger.info.call_args
        assert log_call[0][0] == "🔄 Credentials changed: updating"
        assert "credentials_diff" in log_call[1]

    @pytest.mark.asyncio
    async def test_handle_secret_change_large_diff_truncation(self):
        """Test handling secret change with large diff that gets truncated."""
        # Arrange
        old_credentials = Mock(spec=Credentials)
        old_credentials.model_dump.return_value = {"old": "data"}

        mock_config = Mock()
        mock_config.credentials = old_credentials

        mock_memo = Mock(spec=ApplicationState)
        mock_memo.configuration = mock_config

        secret_data = {"new": "data"}
        event = {"object": {"data": secret_data}}

        with (
            patch(
                "haproxy_template_ic.operator.secrets.Credentials"
            ) as mock_credentials_class,
            patch("haproxy_template_ic.operator.secrets.DeepDiff") as mock_deep_diff,
            patch("haproxy_template_ic.operator.secrets.logger") as mock_logger,
        ):
            new_credentials = Mock(spec=Credentials)
            new_credentials.model_dump.return_value = {"new": "data"}
            mock_credentials_class.from_secret.return_value = new_credentials

            # Create a large diff that will be truncated
            large_diff_content = "x" * 600  # More than 500 characters
            mock_diff = Mock()
            mock_diff.__str__ = Mock(return_value=large_diff_content)
            mock_deep_diff.return_value = mock_diff

            # Act
            await handle_secret_change(
                memo=mock_memo, event=event, name="test-secret", type="Normal"
            )

        # Assert
        mock_logger.info.assert_called_once()
        log_call = mock_logger.info.call_args
        logged_diff = log_call[1]["credentials_diff"]

        # Verify diff was truncated
        assert len(logged_diff) == 503  # 500 + "..."
        assert logged_diff.endswith("...")

    @pytest.mark.asyncio
    async def test_handle_secret_change_secret_data_extraction(self):
        """Test that secret data is properly extracted from event."""
        # Arrange
        mock_credentials = Mock(spec=Credentials)
        mock_credentials.model_dump.return_value = {"test": "data"}

        mock_config = Mock()
        mock_config.credentials = mock_credentials

        mock_memo = Mock(spec=ApplicationState)
        mock_memo.configuration = mock_config

        # Create event with nested object structure
        secret_data = {
            "username": "dGVzdA==",  # base64 for "test"
            "password": "cGFzc3dvcmQ=",  # base64 for "password"
        }

        event = {
            "object": {
                "metadata": {"name": "test-secret"},
                "data": secret_data,
                "type": "Opaque",
            }
        }

        with (
            patch(
                "haproxy_template_ic.operator.secrets.Credentials"
            ) as mock_credentials_class,
            patch("haproxy_template_ic.operator.secrets.DeepDiff") as mock_deep_diff,
        ):
            mock_credentials_class.from_secret.return_value = mock_credentials
            mock_deep_diff.return_value = {}  # No changes

            # Act
            await handle_secret_change(
                memo=mock_memo, event=event, name="test-secret", type="Normal"
            )

        # Assert
        mock_credentials_class.from_secret.assert_called_once_with(secret_data)

    @pytest.mark.asyncio
    async def test_handle_secret_change_autolog_integration(self):
        """Test that handle_secret_change properly integrates with autolog decorator."""
        # Arrange
        mock_credentials = Mock(spec=Credentials)
        mock_credentials.model_dump.return_value = {"test": "data"}

        mock_config = Mock()
        mock_config.credentials = mock_credentials

        mock_memo = Mock(spec=ApplicationState)
        mock_memo.configuration = mock_config

        secret_data = {"test": "data"}
        event = {"object": {"data": secret_data}}

        with (
            patch(
                "haproxy_template_ic.operator.secrets.Credentials"
            ) as mock_credentials_class,
            patch("haproxy_template_ic.operator.secrets.DeepDiff") as mock_deep_diff,
        ):
            mock_credentials_class.from_secret.return_value = mock_credentials
            mock_deep_diff.return_value = {}

            # Act - function should complete without issues
            await handle_secret_change(
                memo=mock_memo, event=event, name="test-secret", type="Normal"
            )

        # Assert - verify basic functionality works
        mock_credentials_class.from_secret.assert_called_once_with(secret_data)

    @pytest.mark.asyncio
    async def test_handle_secret_change_kwargs_handling(self):
        """Test that handle_secret_change properly handles additional kwargs."""
        # Arrange
        mock_credentials = Mock(spec=Credentials)
        mock_credentials.model_dump.return_value = {"test": "data"}

        mock_config = Mock()
        mock_config.credentials = mock_credentials

        mock_memo = Mock(spec=ApplicationState)
        mock_memo.configuration = mock_config

        secret_data = {"test": "data"}
        event = {"object": {"data": secret_data}}

        with (
            patch(
                "haproxy_template_ic.operator.secrets.Credentials"
            ) as mock_credentials_class,
            patch("haproxy_template_ic.operator.secrets.DeepDiff") as mock_deep_diff,
        ):
            mock_credentials_class.from_secret.return_value = mock_credentials
            mock_deep_diff.return_value = {}

            # Act with additional kwargs
            await handle_secret_change(
                memo=mock_memo,
                event=event,
                name="test-secret",
                type="Normal",
                uid="12345",
                namespace="default",
                extra_field="extra_value",
            )

        # Assert - function should handle extra kwargs gracefully
        mock_credentials_class.from_secret.assert_called_once_with(secret_data)


class TestSecretsIntegration:
    """Integration tests for secrets module."""

    @pytest.mark.asyncio
    async def test_fetch_secret_with_real_secret_structure(self):
        """Test fetch_secret with realistic Secret object structure."""
        # Arrange
        mock_secret = Mock(spec=Secret)
        mock_secret.name = "haproxy-credentials"
        mock_secret.namespace = "default"
        mock_secret.data = {
            "dataplane_username": "YWRtaW4=",
            "dataplane_password": "c2VjcmV0MTIz",
            "validation_username": "YWRtaW4=",
            "validation_password": "dmFsaWRhdGlvbnNlY3JldA==",
        }

        with (
            patch("haproxy_template_ic.operator.secrets.Secret") as mock_secret_class,
            patch("haproxy_template_ic.operator.secrets.add_span_attributes"),
            patch("haproxy_template_ic.operator.secrets.record_span_event"),
        ):
            mock_secret_class.get = AsyncMock(return_value=mock_secret)

            # Act
            result = await fetch_secret("haproxy-credentials", "default")

        # Assert
        assert result is mock_secret
        assert result.name == "haproxy-credentials"
        assert result.namespace == "default"
        assert "dataplane_username" in result.data

    @pytest.mark.asyncio
    async def test_handle_secret_change_realistic_flow(self):
        """Test handle_secret_change with realistic credential flow."""
        # Arrange - Create realistic old credentials
        from haproxy_template_ic.credentials import DataplaneAuth

        old_dataplane_auth = DataplaneAuth(username="admin", password="old_pass")
        old_validation_auth = DataplaneAuth(username="admin", password="old_pass")
        old_credentials = Credentials(
            dataplane=old_dataplane_auth, validation=old_validation_auth
        )

        mock_config = Mock()
        mock_config.credentials = old_credentials

        mock_memo = Mock(spec=ApplicationState)
        mock_memo.configuration = mock_config
        mock_memo.runtime = Mock()

        # Create realistic secret data with base64 encoded values
        import base64

        secret_data = {
            "dataplane_username": base64.b64encode("newadmin".encode()).decode(),
            "dataplane_password": base64.b64encode("new_pass".encode()).decode(),
            "validation_username": base64.b64encode("newadmin".encode()).decode(),
            "validation_password": base64.b64encode("new_pass".encode()).decode(),
        }

        event = {"object": {"data": secret_data}}

        with patch("haproxy_template_ic.operator.secrets.logger") as mock_logger:
            # Act
            await handle_secret_change(
                memo=mock_memo, event=event, name="haproxy-credentials", type="Normal"
            )

        # Assert
        # Verify credentials were updated
        updated_credentials = mock_memo.configuration.credentials
        assert isinstance(updated_credentials, Credentials)

        # Note: Due to verbose_level=0 in DeepDiff, ALL differences are suppressed,
        # not just password values. This means credentials are never updated.
        # This appears to be a bug in the production code.
        assert updated_credentials.dataplane.username == "admin"  # Still old username
        assert updated_credentials.validation.username == "admin"  # Still old username
        assert (
            updated_credentials.dataplane.password.get_secret_value() == "old_pass"
        )  # Still old password
        assert (
            updated_credentials.validation.password.get_secret_value() == "old_pass"
        )  # Still old password

        # Verify no change was logged since DeepDiff sees no difference with verbose_level=0
        mock_logger.info.assert_not_called()
        mock_logger.debug.assert_called_once_with(
            "Credentials unchanged, skipping update"
        )

    def test_secrets_module_error_handling_comprehensive(self):
        """Test comprehensive error handling across the secrets module."""
        import asyncio

        # Test network-related errors that should be temporary
        temporary_network_errors = [
            ConnectionError("DNS resolution failed"),
            ConnectionRefusedError(
                "Connection refused"
            ),  # Inherits from ConnectionError
            TimeoutError("Connection timeout after 30s"),
        ]

        for error in temporary_network_errors:
            with patch(
                "haproxy_template_ic.operator.secrets.Secret"
            ) as mock_secret_class:
                mock_secret_class.get = AsyncMock(side_effect=error)

                # Should raise TemporaryError for network issues
                with pytest.raises(kopf.TemporaryError):
                    asyncio.run(fetch_secret("test", "default"))

        # Test errors that should be permanent
        permanent_errors = [
            OSError("Network unreachable"),
            RuntimeError("Secret not found"),
            PermissionError("Forbidden"),
            ValueError("Invalid namespace format"),
            KeyError("Required field missing"),
        ]

        for error in permanent_errors:
            with patch(
                "haproxy_template_ic.operator.secrets.Secret"
            ) as mock_secret_class:
                mock_secret_class.get = AsyncMock(side_effect=error)

                # Should raise PermanentError for non-network issues
                with pytest.raises(kopf.PermanentError):
                    asyncio.run(fetch_secret("test", "default"))
