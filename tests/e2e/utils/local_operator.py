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
from queue import Empty, Queue
from typing import List, Optional, Tuple

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
            verbose: Verbosity level (0=WARNING, 1=INFO, 2=DEBUG)
            collect_coverage: Whether to collect coverage data
        """
        self.configmap_name = configmap_name
        self.secret_name = secret_name
        self.namespace = namespace
        self.verbose = verbose
        self.collect_coverage = collect_coverage
        self.kubeconfig_path = kubeconfig_path

        # Create temporary directory for testing if coverage is enabled
        self.temp_dir: Optional[str]
        if collect_coverage:
            self.temp_dir = tempfile.mkdtemp(prefix="haproxy-test-")
        else:
            self.temp_dir = None

        self.process: Optional[subprocess.Popen] = None
        self.log_queue: Queue = Queue()
        self.log_thread: Optional[threading.Thread] = None
        self.logs: List[Tuple[float, str]] = []  # (timestamp, log_line) pairs
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
                "POD_NAMESPACE": self.namespace,  # Pass namespace to operator
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
        )

        # Determine project root directory
        import haproxy_template_ic

        project_root = os.path.dirname(os.path.dirname(haproxy_template_ic.__file__))

        # Start the process
        self.process = subprocess.Popen(
            cmd,
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,  # Line buffered
            preexec_fn=os.setsid if os.name != "nt" else None,  # Create process group
            cwd=project_root,  # Ensure correct working directory
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
                timestamp = time.time()
                self.logs.append((timestamp, line))
                self.log_queue.put((timestamp, line))
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
        # Extract just the log lines from the (timestamp, log_line) tuples
        log_lines = [log_line for _, log_line in self.logs[since_index:]]
        return "\n".join(log_lines)

    def get_log_position(self) -> int:
        """
        Get the current log position (number of log lines).

        Returns:
            Current number of log lines
        """
        return len(self.logs)

    def get_log_position_at_time(self, milliseconds_ago: float) -> int:
        """
        Get the log position N milliseconds ago.

        Args:
            milliseconds_ago: Number of milliseconds to look back

        Returns:
            Log position at the specified time ago
        """
        if milliseconds_ago <= 0:
            return len(self.logs)

        target_time = time.time() - (milliseconds_ago / 1000.0)

        # Find the first log entry at or after the target time
        for i, (timestamp, _) in enumerate(self.logs):
            if timestamp >= target_time:
                return i

        # If no logs found after target time, return current position
        return len(self.logs)

    def wait_for_log(
        self,
        pattern: str,
        timeout: float = 30,
        since_index: int = 0,
    ) -> bool:
        """
        Wait for a specific log pattern to appear.

        Args:
            pattern: String pattern to search for in logs
            timeout: Maximum time to wait in seconds
            since_index: Only check logs starting from this index (0 means check all existing logs)

        Returns:
            True if pattern found, False if timeout
        """
        start_time = time.time()

        # Check existing logs from the specified index
        for _, log_line in self.logs[since_index:]:
            if pattern in log_line:
                return True

        # Wait for new logs
        while time.time() - start_time < timeout:
            try:
                timestamp, log_line = self.log_queue.get(timeout=0.1)
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

    # Wait for operator to be ready by checking for successful initialization in logs
    start_time = time.time()
    ready = False

    while time.time() - start_time < timeout:
        if not runner.is_running():
            raise RuntimeError(
                f"Operator process exited unexpectedly. Logs:\n{runner.get_logs()}"
            )

        # Check for ready indicators in logs
        logs = runner.get_logs()
        if (
            "✅ Configuration and credentials loaded successfully." in logs
            and "📊 Metrics server started on port" in logs
        ):
            ready = True
            break

        time.sleep(1)

    if not ready:
        raise TimeoutError(
            f"Operator did not become ready within {timeout} seconds. "
            f"Logs:\n{runner.get_logs()}"
        )

    logger.info("Operator is ready")
