"""
Unit tests for TUI custom exceptions.

Tests exception construction, inheritance, error messages, and behavior.
"""

import pytest

from haproxy_template_ic.tui.exceptions import (
    DashboardError,
    ConnectionError,
    ResourceNotFoundError,
    MetricsUnavailableError,
    PodExecutionError,
)


class TestDashboardError:
    """Test base DashboardError exception."""

    def test_dashboard_error_basic(self):
        """Test basic DashboardError construction."""
        error = DashboardError("Test error")
        assert str(error) == "Test error"
        assert isinstance(error, Exception)

    def test_dashboard_error_inheritance(self):
        """Test that DashboardError inherits from Exception."""
        error = DashboardError("Test error")
        assert isinstance(error, Exception)
        assert isinstance(error, DashboardError)

    def test_dashboard_error_empty_message(self):
        """Test DashboardError with empty message."""
        error = DashboardError("")
        assert str(error) == ""

    def test_dashboard_error_none_message(self):
        """Test DashboardError with None message."""
        error = DashboardError(None)
        assert str(error) == "None"


class TestConnectionError:
    """Test ConnectionError exception."""

    def test_connection_error_basic(self):
        """Test basic ConnectionError construction."""
        error = ConnectionError("Connection failed")
        assert str(error) == "Connection failed"
        assert isinstance(error, DashboardError)
        assert isinstance(error, ConnectionError)

    def test_connection_error_with_original_error(self):
        """Test ConnectionError with original error."""
        original = Exception("Original error")
        error = ConnectionError("Connection failed", original)

        assert "Connection failed" in str(error)
        assert "Original error" in str(error)
        assert error.original_error == original

    def test_connection_error_without_original_error(self):
        """Test ConnectionError without original error."""
        error = ConnectionError("Connection failed")
        assert str(error) == "Connection failed"
        assert error.original_error is None

    def test_connection_error_str_formatting(self):
        """Test ConnectionError string formatting."""
        original = ValueError("Network unreachable")
        error = ConnectionError("Failed to connect", original)

        error_str = str(error)
        assert "Failed to connect" in error_str
        assert "caused by" in error_str
        assert "Network unreachable" in error_str

    def test_connection_error_inheritance_hierarchy(self):
        """Test ConnectionError inheritance."""
        error = ConnectionError("Test")
        assert isinstance(error, DashboardError)
        assert isinstance(error, Exception)
        assert type(error).__name__ == "ConnectionError"


class TestResourceNotFoundError:
    """Test ResourceNotFoundError exception."""

    def test_resource_not_found_basic(self):
        """Test basic ResourceNotFoundError construction."""
        error = ResourceNotFoundError("deployment", "test-deploy")

        assert "deployment 'test-deploy' not found" in str(error)
        assert error.resource_type == "deployment"
        assert error.name == "test-deploy"
        assert error.namespace is None

    def test_resource_not_found_with_namespace(self):
        """Test ResourceNotFoundError with namespace."""
        error = ResourceNotFoundError("pod", "test-pod", "test-namespace")

        error_str = str(error)
        assert "pod 'test-pod'" in error_str
        assert "namespace 'test-namespace'" in error_str
        assert error.namespace == "test-namespace"

    def test_resource_not_found_attributes(self):
        """Test ResourceNotFoundError attributes."""
        error = ResourceNotFoundError("service", "web-service", "production")

        assert error.resource_type == "service"
        assert error.name == "web-service"
        assert error.namespace == "production"
        assert isinstance(error, DashboardError)

    def test_resource_not_found_different_types(self):
        """Test ResourceNotFoundError with different resource types."""
        test_cases = [
            ("deployment", "haproxy", None),
            ("pod", "haproxy-1", "default"),
            ("configmap", "config", "kube-system"),
            ("secret", "tls-cert", "production"),
        ]

        for resource_type, name, namespace in test_cases:
            error = ResourceNotFoundError(resource_type, name, namespace)

            error_str = str(error)
            assert resource_type in error_str
            assert name in error_str
            if namespace:
                assert namespace in error_str

    def test_resource_not_found_message_formatting(self):
        """Test ResourceNotFoundError message formatting."""
        # Without namespace
        error1 = ResourceNotFoundError("deployment", "test")
        assert str(error1) == "deployment 'test' not found"

        # With namespace
        error2 = ResourceNotFoundError("deployment", "test", "default")
        assert str(error2) == "deployment 'test' in namespace 'default' not found"


class TestMetricsUnavailableError:
    """Test MetricsUnavailableError exception."""

    def test_metrics_unavailable_default(self):
        """Test MetricsUnavailableError with default message."""
        error = MetricsUnavailableError()
        assert str(error) == "Metrics server unavailable"
        assert isinstance(error, DashboardError)

    def test_metrics_unavailable_custom_message(self):
        """Test MetricsUnavailableError with custom message."""
        error = MetricsUnavailableError("Custom metrics error")
        assert str(error) == "Custom metrics error"

    def test_metrics_unavailable_inheritance(self):
        """Test MetricsUnavailableError inheritance."""
        error = MetricsUnavailableError()
        assert isinstance(error, DashboardError)
        assert isinstance(error, Exception)


class TestPodExecutionError:
    """Test PodExecutionError exception."""

    def test_pod_execution_error_basic(self):
        """Test basic PodExecutionError construction."""
        error = PodExecutionError("test-pod", "dump all")

        error_str = str(error)
        assert "Failed to execute 'dump all' in pod 'test-pod'" in error_str
        assert error.pod_name == "test-pod"
        assert error.command == "dump all"
        assert error.original_error is None

    def test_pod_execution_error_with_original_error(self):
        """Test PodExecutionError with original error."""
        original = Exception("JSON decode error")
        error = PodExecutionError("test-pod", "dump config", original)

        error_str = str(error)
        assert "Failed to execute 'dump config' in pod 'test-pod'" in error_str
        assert "JSON decode error" in error_str
        assert error.original_error == original

    def test_pod_execution_error_attributes(self):
        """Test PodExecutionError attributes."""
        original = ValueError("Invalid response")
        error = PodExecutionError("controller-1", "get status", original)

        assert error.pod_name == "controller-1"
        assert error.command == "get status"
        assert error.original_error == original
        assert isinstance(error, DashboardError)

    def test_pod_execution_error_different_scenarios(self):
        """Test PodExecutionError with different scenarios."""
        scenarios = [
            ("haproxy-pod-1", "dump all", None),
            ("controller", "get template", ConnectionError("Connection lost")),
            ("validator", "check config", ValueError("Invalid JSON")),
        ]

        for pod_name, command, original_error in scenarios:
            error = PodExecutionError(pod_name, command, original_error)

            error_str = str(error)
            assert pod_name in error_str
            assert command in error_str

            if original_error:
                assert str(original_error) in error_str

    def test_pod_execution_error_inheritance(self):
        """Test PodExecutionError inheritance."""
        error = PodExecutionError("test", "test")
        assert isinstance(error, DashboardError)
        assert isinstance(error, Exception)


class TestExceptionHierarchy:
    """Test exception hierarchy and relationships."""

    def test_all_exceptions_inherit_from_dashboard_error(self):
        """Test that all custom exceptions inherit from DashboardError."""
        exceptions_to_test = [
            ConnectionError("test"),
            ResourceNotFoundError("test", "test"),
            MetricsUnavailableError(),
            PodExecutionError("test", "test"),
        ]

        for exception in exceptions_to_test:
            assert isinstance(exception, DashboardError)
            assert isinstance(exception, Exception)

    def test_exception_type_checking(self):
        """Test exception type checking works correctly."""
        # Create instances
        connection_error = ConnectionError("test")
        resource_error = ResourceNotFoundError("pod", "test")
        metrics_error = MetricsUnavailableError()
        pod_error = PodExecutionError("test", "test")

        # Test type checking
        assert type(connection_error).__name__ == "ConnectionError"
        assert type(resource_error).__name__ == "ResourceNotFoundError"
        assert type(metrics_error).__name__ == "MetricsUnavailableError"
        assert type(pod_error).__name__ == "PodExecutionError"

        # Test isinstance checks
        assert isinstance(connection_error, ConnectionError)
        assert not isinstance(connection_error, ResourceNotFoundError)
        assert not isinstance(resource_error, ConnectionError)

    def test_exception_catching_hierarchy(self):
        """Test exception catching with hierarchy."""
        # Should be able to catch specific exceptions
        try:
            raise ConnectionError("test")
        except ConnectionError as e:
            assert str(e) == "test"
        except DashboardError:
            pytest.fail("Should have caught ConnectionError specifically")

        # Should be able to catch base exception
        try:
            raise ResourceNotFoundError("test", "test")
        except DashboardError as e:
            assert "test" in str(e)
        except Exception:
            pytest.fail("Should have caught DashboardError")


class TestExceptionUsagePatterns:
    """Test common exception usage patterns."""

    def test_exception_chaining(self):
        """Test exception chaining patterns."""
        try:
            # Simulate a chain of errors
            try:
                raise ValueError("Original network error")
            except ValueError as e:
                raise ConnectionError("Failed to connect to cluster", e)
        except ConnectionError as e:
            assert "Failed to connect" in str(e)
            assert "Original network error" in str(e)
            assert isinstance(e.original_error, ValueError)

    def test_exception_context_preservation(self):
        """Test that exception context is preserved."""
        original_error = OSError("Permission denied")
        wrapper_error = ConnectionError("Socket connection failed", original_error)

        # Context should be preserved
        assert wrapper_error.original_error == original_error
        assert str(original_error) in str(wrapper_error)

    def test_exception_serialization(self):
        """Test exception can be converted to string reliably."""
        exceptions_with_expected_content = [
            (ConnectionError("test connection"), "test connection"),
            (ResourceNotFoundError("pod", "test-pod"), "pod 'test-pod' not found"),
            (MetricsUnavailableError("metrics down"), "metrics down"),
            (
                PodExecutionError("pod-1", "cmd"),
                "Failed to execute 'cmd' in pod 'pod-1'",
            ),
        ]

        for exception, expected_content in exceptions_with_expected_content:
            error_str = str(exception)
            assert expected_content in error_str
            assert len(error_str) > 0
            assert isinstance(error_str, str)

    def test_exception_equality(self):
        """Test exception equality comparisons."""
        # Same type and message should be equal for string comparison
        error1 = ConnectionError("test")
        error2 = ConnectionError("test")

        # String representations should be equal
        assert str(error1) == str(error2)

        # But objects themselves are different instances
        assert error1 is not error2

    def test_exception_attributes_immutable(self):
        """Test that exception attributes are properly set."""
        resource_error = ResourceNotFoundError("deployment", "test-deploy", "test-ns")

        # Attributes should be immutable-like (can't easily change core properties)
        assert resource_error.resource_type == "deployment"
        assert resource_error.name == "test-deploy"
        assert resource_error.namespace == "test-ns"

        pod_error = PodExecutionError("pod", "command", ValueError("test"))
        assert pod_error.pod_name == "pod"
        assert pod_error.command == "command"
        assert isinstance(pod_error.original_error, ValueError)
