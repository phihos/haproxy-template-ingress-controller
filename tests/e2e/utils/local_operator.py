"""
Local operator runner for acceptance tests using Telepresence.

This module provides utilities to run the HAProxy Template IC operator
locally during tests while connected to a Kind cluster via Telepresence.
This approach dramatically improves test performance by eliminating
container build/deploy cycles.
"""

import os
import signal
import subprocess
import sys
import tempfile
import threading
import time
from queue import Queue, Empty
from typing import Any, Dict, List, Optional

import structlog

logger = structlog.get_logger(__name__)


class LocalOperatorRunner:
    """
    Context manager for running the operator locally during tests.

    This class manages:
    - Operator process lifecycle
    - Coverage data collection
    - Log capture and streaming
    - Environment variable injection
    - Graceful shutdown
    """

    def __init__(
        self,
        configmap_name: str,
        secret_name: str,
        namespace: str,
        socket_path: Optional[str] = None,
        verbose: int = 2,
        collect_coverage: bool = True,
        kubeconfig_path: Optional[str] = None,
    ):
        """
        Initialize the local operator runner.

        Args:
            configmap_name: Name of the ConfigMap containing operator config
            secret_name: Name of the Secret containing credentials
            namespace: Kubernetes namespace for the operator to use
            socket_path: Path for the management socket (auto-generated if None)
            verbose: Verbosity level (0=WARNING, 1=INFO, 2=DEBUG)
            collect_coverage: Whether to collect coverage data
        """
        self.configmap_name = configmap_name
        self.secret_name = secret_name
        self.namespace = namespace
        self.verbose = verbose
        self.collect_coverage = collect_coverage
        self.kubeconfig_path = kubeconfig_path

        # Create temporary directory for socket if not provided
        if socket_path:
            self.socket_path = socket_path
            self.temp_dir = None
        else:
            self.temp_dir = tempfile.mkdtemp(prefix="haproxy-test-")
            self.socket_path = os.path.join(self.temp_dir, "management.sock")

        self.process: Optional[subprocess.Popen] = None
        self.log_queue: Queue = Queue()
        self.log_thread: Optional[threading.Thread] = None
        self.logs: List[str] = []
        self.exit_code: Optional[int] = None
        self.exception: Optional[Exception] = None

    def __enter__(self):
        """Start the operator process."""
        self.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Stop the operator process and cleanup."""
        self.stop()

    def start(self):
        """Start the operator process with proper environment and coverage."""
        # Prepare environment variables
        env = os.environ.copy()
        env.update(
            {
                "CONFIGMAP_NAME": self.configmap_name,
                "SECRET_NAME": self.secret_name,
                "NAMESPACE": self.namespace,  # Pass namespace to operator
                "SOCKET_PATH": self.socket_path,
                "VERBOSE": str(self.verbose),
                # Disable buffering for real-time log capture
                "PYTHONUNBUFFERED": "1",
            }
        )

        # Set KUBECONFIG if provided
        if self.kubeconfig_path:
            env["KUBECONFIG"] = self.kubeconfig_path

        # Build command
        if self.collect_coverage:
            cmd = [
                sys.executable,
                "-m",
                "coverage",
                "run",
                "--parallel-mode",
                "--source",
                "haproxy_template_ic",
                "-m",
                "haproxy_template_ic",
                "run",
                "--configmap-name",
                self.configmap_name,
            ]
        else:
            cmd = [
                sys.executable,
                "-m",
                "haproxy_template_ic",
                "run",
                "--configmap-name",
                self.configmap_name,
            ]

        logger.info(
            "Starting operator locally",
            namespace=self.namespace,
            configmap=self.configmap_name,
            socket_path=self.socket_path,
        )

        # Start the process
        self.process = subprocess.Popen(
            cmd,
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,  # Line buffered
            preexec_fn=os.setsid if os.name != "nt" else None,  # Create process group
        )

        # Start log reader thread
        self.log_thread = threading.Thread(target=self._read_logs, daemon=True)
        self.log_thread.start()

        # Give operator time to start
        time.sleep(2)

        # Check if process is still running
        if self.process.poll() is not None:
            raise RuntimeError(
                f"Operator process exited immediately with code {self.process.returncode}. "
                f"Logs: {self.get_logs()}"
            )

    def stop(self):
        """Stop the operator process gracefully."""
        if not self.process:
            return

        logger.info("Stopping operator process")

        # Try graceful shutdown first
        try:
            if os.name != "nt":
                # Send SIGTERM to process group
                os.killpg(os.getpgid(self.process.pid), signal.SIGTERM)
            else:
                self.process.terminate()

            # Wait up to 10 seconds for graceful shutdown
            try:
                self.exit_code = self.process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                logger.warning("Operator did not stop gracefully, forcing kill")
                if os.name != "nt":
                    os.killpg(os.getpgid(self.process.pid), signal.SIGKILL)
                else:
                    self.process.kill()
                self.exit_code = self.process.wait()

        except ProcessLookupError:
            # Process already terminated
            pass

        # Clean up temporary directory
        if self.temp_dir and os.path.exists(self.temp_dir):
            import shutil

            shutil.rmtree(self.temp_dir)

    def _read_logs(self):
        """Read logs from the operator process in a separate thread."""
        try:
            for line in iter(self.process.stdout.readline, ""):
                if not line:
                    break
                line = line.rstrip()
                self.logs.append(line)
                self.log_queue.put(line)
                # Also print to console for debugging
                if self.verbose >= 2:
                    print(f"[OPERATOR] {line}")
        except Exception as e:
            self.exception = e
            logger.error(f"Error reading operator logs: {e}")

    def get_logs(self, since_index: int = 0) -> str:
        """
        Get operator logs.

        Args:
            since_index: Return logs starting from this index

        Returns:
            String containing log lines joined with newlines
        """
        return "\n".join(self.logs[since_index:])

    def wait_for_log(self, pattern: str, timeout: float = 30) -> bool:
        """
        Wait for a specific log pattern to appear.

        Args:
            pattern: String pattern to search for in logs
            timeout: Maximum time to wait in seconds

        Returns:
            True if pattern found, False if timeout
        """
        start_time = time.time()

        # Check existing logs first
        for log_line in self.logs:
            if pattern in log_line:
                return True

        # Wait for new logs
        while time.time() - start_time < timeout:
            try:
                log_line = self.log_queue.get(timeout=0.1)
                if pattern in log_line:
                    return True
            except Empty:
                # Check if process has exited
                if self.process and self.process.poll() is not None:
                    raise RuntimeError(
                        f"Operator process exited while waiting for '{pattern}'. "
                        f"Exit code: {self.process.returncode}"
                    )

        return False

    def is_running(self) -> bool:
        """Check if the operator process is still running."""
        return self.process is not None and self.process.poll() is None

    def send_socket_command(
        self, command: str, retries: int = 3
    ) -> Optional[Dict[str, Any]]:
        """
        Send a command to the management socket.

        Args:
            command: Socket command to send
            retries: Number of retry attempts

        Returns:
            Parsed JSON response or None on failure
        """
        from .socket_client import send_socket_command as send_cmd

        for attempt in range(retries):
            try:
                response = send_cmd(self.socket_path, command)
                if response:
                    return response

            except Exception as e:
                if attempt == retries - 1:
                    logger.error(
                        f"Failed to send socket command after {retries} attempts: {e}"
                    )
                else:
                    time.sleep(1)

        return None


def wait_for_operator_ready(runner: LocalOperatorRunner, timeout: int = 60) -> None:
    """
    Wait for the local operator to be fully initialized and ready.

    Args:
        runner: The LocalOperatorRunner instance
        timeout: Maximum time to wait in seconds

    Raises:
        TimeoutError: If operator doesn't become ready within timeout
        RuntimeError: If operator process exits unexpectedly
    """
    logger.info("Waiting for operator to become ready")

    # First, wait for socket to be available
    start_time = time.time()
    socket_ready = False

    while time.time() - start_time < timeout:
        if not runner.is_running():
            raise RuntimeError(
                f"Operator process exited unexpectedly. Logs:\n{runner.get_logs()}"
            )

        # Check if socket file exists
        if os.path.exists(runner.socket_path):
            # Try to connect to socket
            response = runner.send_socket_command("dump all", retries=1)
            if response and "config" in response:
                socket_ready = True
                break

        time.sleep(1)

    if not socket_ready:
        raise TimeoutError(
            f"Operator did not become ready within {timeout} seconds. "
            f"Logs:\n{runner.get_logs()}"
        )

    logger.info("Operator is ready")


def assert_log_line(
    runner: LocalOperatorRunner, expected_log_line: str, timeout: float = 5
) -> str:
    """
    Assert that a specific log line appears in the operator's logs.

    Args:
        runner: The LocalOperatorRunner instance
        expected_log_line: The log line text to search for
        timeout: Maximum time to wait

    Returns:
        The complete log output

    Raises:
        AssertionError: If the expected log line is not found
    """
    if not expected_log_line.strip():
        raise ValueError("Expected log line cannot be empty")

    found = runner.wait_for_log(expected_log_line, timeout)

    if not found:
        logs = runner.get_logs()
        raise AssertionError(
            f"Expected log line not found: '{expected_log_line}'\n"
            f"Timeout: {timeout}s\n"
            f"Complete logs:\n{logs}"
        )

    return runner.get_logs()
