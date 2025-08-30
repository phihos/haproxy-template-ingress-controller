"""Telepresence connection management for acceptance tests."""

import logging
import subprocess
import time
from contextlib import contextmanager
from typing import Optional

logger = logging.getLogger(__name__)


class TelepresenceConnection:
    """Manages Telepresence lifecycle for test execution.

    Provides network bridge between local test environment and Kind cluster,
    enabling local operator execution with full cluster network access.
    """

    def __init__(
        self,
        cluster_name: str,
        namespace: str = "haproxy-template-ic",
        kubeconfig: Optional[str] = None,
    ):
        """Initialize Telepresence connection manager.

        Args:
            cluster_name: Name of the Kind cluster
            namespace: Namespace to connect to
            kubeconfig: Path to kubeconfig file (optional)
        """
        self.cluster_name = cluster_name
        self.namespace = namespace
        self.context = f"kind-{cluster_name}"
        self.kubeconfig = kubeconfig
        self._connected = False

    def connect(self) -> None:
        """Establish Telepresence connection to the cluster.

        Uses passwordless sudo configured for Telepresence.
        Connects to the specified namespace and context.
        Handles the case where Telepresence is already connected.
        """
        # Check if already connected
        if self._is_already_connected():
            logger.info(
                "Telepresence is already connected, reusing existing connection"
            )
            self._connected = True
            return

        if self._connected:
            logger.warning("Connection object already marked as connected")
            return

        logger.info(f"Connecting Telepresence to cluster {self.cluster_name}")

        # First, quit any existing connection
        try:
            subprocess.run(
                ["telepresence", "quit"], capture_output=True, text=True, timeout=10
            )
        except (subprocess.CalledProcessError, subprocess.TimeoutExpired):
            pass  # Ignore errors from quit if not connected

        # Wait a moment for cleanup
        time.sleep(2)

        # First install the traffic manager if needed
        install_cmd = ["telepresence", "helm", "install"]
        if self.kubeconfig:
            install_cmd.extend(["--kubeconfig", self.kubeconfig])

        try:
            logger.info("Installing Telepresence traffic manager...")
            subprocess.run(install_cmd, capture_output=True, text=True, timeout=60)
        except (subprocess.CalledProcessError, subprocess.TimeoutExpired):
            # It's okay if this fails - it might already be installed
            pass

        # Connect to the cluster
        cmd = [
            "telepresence",
            "connect",
            "--namespace",
            self.namespace,
            "--context",
            self.context,
            "--manager-namespace",
            "ambassador",  # Default manager namespace
        ]

        # Add kubeconfig if specified
        if self.kubeconfig:
            cmd.extend(["--kubeconfig", self.kubeconfig])

        try:
            result = subprocess.run(
                cmd, capture_output=True, text=True, check=True, timeout=30
            )
            logger.info(f"Telepresence connected: {result.stdout}")
            self._connected = True

            # Verify connection
            self._verify_connection()

        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to connect Telepresence: {e.stderr}")
            raise RuntimeError(f"Telepresence connection failed: {e.stderr}") from e
        except subprocess.TimeoutExpired:
            logger.error("Telepresence connection timed out")
            raise RuntimeError("Telepresence connection timed out")

    def _is_already_connected(self) -> bool:
        """Check if Telepresence is already connected to any cluster.

        Returns:
            True if Telepresence is connected, False otherwise
        """
        try:
            result = subprocess.run(
                ["telepresence", "status"], capture_output=True, text=True, timeout=5
            )
            # Check if the output indicates a connection
            if result.returncode == 0 and "Connected" in result.stdout:
                logger.info("Found existing Telepresence connection")
                return True
        except (
            subprocess.CalledProcessError,
            subprocess.TimeoutExpired,
            FileNotFoundError,
        ):
            pass
        return False

    def disconnect(self) -> None:
        """Disconnect Telepresence from the cluster."""
        if not self._connected:
            return

        logger.info("Disconnecting Telepresence")

        try:
            result = subprocess.run(
                ["telepresence", "quit"],
                capture_output=True,
                text=True,
                check=True,
                timeout=10,
            )
            logger.info(f"Telepresence disconnected: {result.stdout}")
            self._connected = False
        except subprocess.CalledProcessError as e:
            logger.warning(f"Error disconnecting Telepresence: {e.stderr}")
        except subprocess.TimeoutExpired:
            logger.warning("Telepresence disconnect timed out")

    def _verify_connection(self) -> None:
        """Verify that Telepresence connection is working."""
        try:
            result = subprocess.run(
                ["telepresence", "status"],
                capture_output=True,
                text=True,
                check=True,
                timeout=5,
            )

            if "Connected" not in result.stdout:
                raise RuntimeError("Telepresence status check failed")

            logger.info("Telepresence connection verified")

        except (subprocess.CalledProcessError, subprocess.TimeoutExpired) as e:
            raise RuntimeError(f"Telepresence verification failed: {e}") from e

    def get_service_url(
        self, service_name: str, port: int, namespace: Optional[str] = None
    ) -> str:
        """Get URL for a service accessible via Telepresence.

        Args:
            service_name: Name of the Kubernetes service
            port: Service port
            namespace: Service namespace (defaults to connection namespace)

        Returns:
            URL string for accessing the service
        """
        ns = namespace or self.namespace
        # Telepresence makes services available via their DNS names
        return f"http://{service_name}.{ns}.svc.cluster.local:{port}"

    @property
    def is_connected(self) -> bool:
        """Check if Telepresence is currently connected."""
        return self._connected

    @contextmanager
    def connection_context(self):
        """Context manager for Telepresence connection lifecycle."""
        try:
            self.connect()
            yield self
        finally:
            self.disconnect()


def ensure_telepresence_installed() -> bool:
    """Check if Telepresence is installed and accessible.

    Returns:
        True if Telepresence is installed, False otherwise
    """
    try:
        result = subprocess.run(
            ["telepresence", "version"], capture_output=True, text=True, timeout=5
        )
        logger.info(f"Telepresence version: {result.stdout.strip()}")
        return result.returncode == 0
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return False
