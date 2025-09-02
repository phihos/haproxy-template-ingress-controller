"""
Custom exceptions for dashboard components.

Provides specific exception types for better error handling and reconnection logic.
"""

__all__ = [
    "DashboardError",
    "ConnectionError",
    "ResourceNotFoundError",
    "MetricsUnavailableError",
    "PodExecutionError",
]


class DashboardError(Exception):
    """Base exception for dashboard-related errors."""

    pass


class ConnectionError(DashboardError):
    """Raised when unable to connect to Kubernetes cluster or components."""

    def __init__(self, message: str, original_error: Exception = None):
        super().__init__(message)
        self.original_error = original_error

    def __str__(self) -> str:
        if self.original_error:
            return f"{super().__str__()} (caused by: {self.original_error})"
        return super().__str__()


class ResourceNotFoundError(DashboardError):
    """Raised when a required Kubernetes resource is not found."""

    def __init__(self, resource_type: str, name: str, namespace: str = None):
        self.resource_type = resource_type
        self.name = name
        self.namespace = namespace

        location = f" in namespace '{namespace}'" if namespace else ""
        super().__init__(f"{resource_type} '{name}'{location} not found")


class MetricsUnavailableError(DashboardError):
    """Raised when pod metrics cannot be retrieved from metrics-server."""

    def __init__(self, message: str = "Metrics server unavailable"):
        super().__init__(message)


class PodExecutionError(DashboardError):
    """Raised when unable to execute commands in pods."""

    def __init__(self, pod_name: str, command: str, original_error: Exception = None):
        self.pod_name = pod_name
        self.command = command
        self.original_error = original_error

        message = f"Failed to execute '{command}' in pod '{pod_name}'"
        if original_error:
            message += f": {original_error}"
        super().__init__(message)
