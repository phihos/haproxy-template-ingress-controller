"""Telepresence connection management for acceptance tests."""

import logging
import subprocess
import time
from contextlib import contextmanager
from typing import Optional, Dict, Any

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

        # Try to install traffic manager, but continue if it fails
        try:
            self._install_traffic_manager()
        except RuntimeError as e:
            logger.warning(f"Traffic manager installation failed: {e}")
            logger.info(
                "Continuing without traffic manager - some features may be limited"
            )

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

        # Retry connection with traffic manager startup time
        max_retries = 3
        retry_delay = 10

        for attempt in range(max_retries):
            try:
                logger.info(
                    f"Attempting to connect to Telepresence (attempt {attempt + 1}/{max_retries})..."
                )
                result = subprocess.run(
                    cmd, capture_output=True, text=True, check=True, timeout=30
                )
                logger.info(f"Telepresence connected: {result.stdout}")
                self._connected = True

                # Verify connection
                self._verify_connection()
                return

            except subprocess.CalledProcessError as e:
                logger.warning(f"Connection attempt {attempt + 1} failed: {e.stderr}")
                if attempt < max_retries - 1:
                    logger.info(f"Waiting {retry_delay} seconds before retry...")
                    time.sleep(retry_delay)
                else:
                    logger.error(
                        f"Failed to connect Telepresence after {max_retries} attempts"
                    )
                    raise RuntimeError(
                        f"Telepresence connection failed: {e.stderr}"
                    ) from e
            except subprocess.TimeoutExpired:
                logger.warning(f"Connection attempt {attempt + 1} timed out")
                if attempt < max_retries - 1:
                    logger.info(f"Waiting {retry_delay} seconds before retry...")
                    time.sleep(retry_delay)
                else:
                    logger.error("Telepresence connection timed out after all retries")
                    raise RuntimeError("Telepresence connection timed out")

    def _install_traffic_manager(self) -> None:
        """Install Telepresence traffic manager in the cluster."""
        # Check if traffic manager is already running
        if self._is_traffic_manager_ready():
            logger.info("Traffic manager is already running")
            return

        # Create ambassador namespace if it doesn't exist
        logger.info("Ensuring ambassador namespace exists...")
        try:
            create_cmd = ["kubectl", "create", "namespace", "ambassador"]
            if self.kubeconfig:
                create_cmd.extend(["--kubeconfig", self.kubeconfig])
            subprocess.run(create_cmd, capture_output=True, text=True, timeout=10)
        except (subprocess.CalledProcessError, subprocess.TimeoutExpired):
            pass  # Namespace might already exist

        # Configure Telepresence timeouts
        self._configure_telepresence_timeout()

        # Install traffic manager
        logger.info("Installing Telepresence traffic manager...")
        install_cmd = [
            "telepresence",
            "helm",
            "install",
            "--manager-namespace",
            "ambassador",
        ]
        if self.kubeconfig:
            install_cmd.extend(["--kubeconfig", self.kubeconfig])

        try:
            result = subprocess.run(
                install_cmd, capture_output=True, text=True, timeout=120
            )
            if result.returncode != 0:
                logger.warning(f"Traffic manager installation failed: {result.stderr}")
                # Check if it's already installed
                if "already exists" in result.stderr.lower():
                    logger.info("Traffic manager already exists")
                else:
                    raise RuntimeError(
                        f"Failed to install traffic manager: {result.stderr}"
                    )
            else:
                logger.info("Traffic manager installed successfully")
        except subprocess.TimeoutExpired:
            raise RuntimeError(
                "Traffic manager installation timed out after 60 seconds"
            )

        # Wait for traffic manager to be ready
        self._wait_for_traffic_manager()

    def _configure_telepresence_timeout(self) -> None:
        """Configure Telepresence timeout settings."""
        import os
        import yaml

        config_dir = os.path.expanduser("~/.config/telepresence")
        config_file = os.path.join(config_dir, "config.yml")

        # Ensure config directory exists
        os.makedirs(config_dir, exist_ok=True)

        # Load existing config or create new one
        config: Dict[str, Any] = {}
        if os.path.exists(config_file):
            try:
                with open(config_file, "r") as f:
                    config = yaml.safe_load(f) or {}
            except Exception:
                config = {}

        # Set longer timeout for helm operations
        config.setdefault("timeouts", {})["helm"] = "120s"

        # Write config back
        try:
            with open(config_file, "w") as f:
                yaml.dump(config, f)
            logger.info("Updated Telepresence timeout configuration")
        except Exception as e:
            logger.warning(f"Failed to update Telepresence config: {e}")

    def _is_traffic_manager_ready(self) -> bool:
        """Check if traffic manager is ready."""
        try:
            cmd = [
                "kubectl",
                "get",
                "deployment",
                "traffic-manager",
                "-n",
                "ambassador",
            ]
            if self.kubeconfig:
                cmd.extend(["--kubeconfig", self.kubeconfig])
            cmd.extend(["-o", "jsonpath={.status.readyReplicas}"])

            result = subprocess.run(cmd, capture_output=True, text=True, timeout=5)
            if result.returncode == 0 and result.stdout.strip():
                ready_replicas = int(result.stdout.strip() or "0")
                return ready_replicas > 0
        except (subprocess.TimeoutExpired, ValueError):
            pass
        return False

    def _wait_for_traffic_manager(self) -> None:
        """Wait for traffic manager to be ready."""
        logger.info("Waiting for traffic manager to be ready...")
        max_wait = 30
        start_time = time.time()

        while time.time() - start_time < max_wait:
            if self._is_traffic_manager_ready():
                logger.info("Traffic manager is ready")
                return
            time.sleep(2)

        raise RuntimeError("Traffic manager did not become ready in 30 seconds")

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
