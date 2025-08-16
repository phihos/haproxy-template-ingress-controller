"""
Progress reporting utilities for integration tests.

This module provides tools for showing test progress, container status,
and debug information during integration test execution.
"""

import time
import sys
import os
import logging
from contextlib import contextmanager
from typing import Dict, List, Optional
from pathlib import Path

import pytest


class TestProgressReporter:
    """Reports test progress with visual indicators.

    Supports both serial execution (real-time output) and parallel execution
    with pytest-xdist (logging-based output after test completion).

    Usage:
    - Serial execution (-n 0): Full real-time progress with beautiful formatting
    - Parallel execution (-n auto): Progress messages after each test completes
    - With --verbose-docker and xdist: Creates detailed log files per worker
    """

    _xdist_message_shown: bool = False

    def __init__(self, show_container_logs: bool = False, verbose_docker: bool = False):
        """Initialize progress reporter with options."""
        self.show_container_logs = show_container_logs
        self.verbose_docker = verbose_docker
        self.current_test: Optional[str] = None
        self.start_time: Optional[float] = None
        self.logger: Optional[logging.Logger] = None

        # Detect pytest-xdist execution
        self.worker_id = os.environ.get("PYTEST_XDIST_WORKER")
        self.is_xdist = self.worker_id is not None

        # Configure logging for xdist mode
        if self.is_xdist:
            self.logger = logging.getLogger(f"integration.{self.worker_id}")

            # Set up file logging if verbose docker is enabled
            if self.verbose_docker:
                self._setup_file_logging()
        else:
            self.logger = None

        # Show xdist information message once
        if self.is_xdist and not hasattr(TestProgressReporter, "_xdist_message_shown"):
            TestProgressReporter._xdist_message_shown = True
            self._show_xdist_info()

    def _setup_file_logging(self) -> None:
        """Set up detailed file logging for xdist workers."""
        if self.logger is None:
            return

        log_file = f"integration_test_{self.worker_id}.log"

        # Remove existing handlers to avoid duplicates
        self.logger.handlers.clear()

        # Create file handler
        file_handler = logging.FileHandler(log_file, mode="w")
        file_handler.setLevel(logging.DEBUG)

        # Create formatter
        formatter = logging.Formatter(
            "%(asctime)s [%(levelname)s] %(message)s", datefmt="%H:%M:%S"
        )
        file_handler.setFormatter(formatter)

        self.logger.addHandler(file_handler)
        self.logger.setLevel(logging.DEBUG)

    def _show_xdist_info(self) -> None:
        """Show information about xdist limitations and capabilities."""
        if self.verbose_docker:
            self._log_message(
                f"ℹ️ Running with pytest-xdist worker {self.worker_id}. "
                f"Detailed logs: integration_test_{self.worker_id}.log"
            )
        else:
            self._log_message(
                "ℹ️ Running with pytest-xdist: Progress shown after test completion. "
                "Use --verbose-docker for detailed log files."
            )

    def start_test(self, test_name: str) -> None:
        """Start reporting for a test."""
        self.current_test = test_name
        self.start_time = time.time()
        self._print_header(f"🔄 Starting integration test: {test_name}")

    def end_test(self, success: bool = True) -> None:
        """End reporting for a test."""
        if self.current_test and self.start_time:
            duration = time.time() - self.start_time
            status = "✅ PASSED" if success else "❌ FAILED"
            self._print_footer(f"{status} {self.current_test} (took {duration:.1f}s)")
        self.current_test = None
        self.start_time = None

    def phase(self, phase_name: str, description: str = "") -> None:
        """Report test phase."""
        message = f"📋 PHASE: {phase_name}"
        if description:
            message += f" - {description}"
        self._print_status(message)

    def docker_operation(self, operation: str, details: str = "") -> None:
        """Report Docker operation."""
        message = f"🐳 DOCKER: {operation}"
        if details:
            message += f" - {details}"
        if self.verbose_docker:
            self._print_status(message)
        elif operation in [
            "Starting containers",
            "Stopping containers",
            "Building images",
        ]:
            self._print_status(message)

    def waiting_for_service(
        self, service: str, url: str, attempt: int = 0, max_attempts: int = 0
    ) -> None:
        """Report waiting for service to become ready."""
        if max_attempts > 0:
            message = (
                f"⏳ WAITING: {service} at {url} (attempt {attempt}/{max_attempts})"
            )
        else:
            message = f"⏳ WAITING: {service} at {url}"
        self._print_status(message)

    def service_ready(self, service: str, url: str, took_seconds: float) -> None:
        """Report service is ready."""
        self._print_status(f"✅ READY: {service} at {url} (took {took_seconds:.1f}s)")

    def service_failed(self, service: str, url: str, error: str) -> None:
        """Report service failed to start."""
        self._print_status(f"❌ FAILED: {service} at {url} - {error}")

    def container_logs(self, service: str, logs: str) -> None:
        """Report container logs if enabled."""
        if self.show_container_logs and logs.strip():
            self._print_section(f"📜 LOGS for {service}", logs)

    def port_allocation(self, ports: Dict[str, int]) -> None:
        """Report allocated ports for test."""
        port_list = [f"{name}:{port}" for name, port in ports.items()]
        self._print_status(f"🔌 PORTS: {', '.join(port_list)}")

    def compose_file(self, compose_file: Path) -> None:
        """Report docker-compose file being used."""
        if self.verbose_docker:
            self._print_status(f"📄 COMPOSE: {compose_file}")

    def error(self, message: str) -> None:
        """Report error message."""
        self._print_status(f"❌ ERROR: {message}")

    def warning(self, message: str) -> None:
        """Report warning message."""
        self._print_status(f"⚠️  WARNING: {message}")

    def debug(self, message: str) -> None:
        """Report debug message."""
        if self.verbose_docker:
            self._print_status(f"🔍 DEBUG: {message}")

    def _log_message(self, message: str) -> None:
        """Log message using appropriate method for execution mode."""
        if self.is_xdist and self.logger is not None:
            # Use logging for xdist (appears after test completion)
            worker_prefix = f"[{self.worker_id}] " if self.worker_id else ""
            self.logger.warning(f"{worker_prefix}{message}")
        else:
            # Use print for serial execution (real-time)
            timestamp = time.strftime("%H:%M:%S", time.localtime())
            print(f"[{timestamp}] {message}")
            sys.stdout.flush()

    def _print_header(self, message: str) -> None:
        """Print test header."""
        if self.is_xdist:
            self._log_message(f"{'=' * 80}")
            self._log_message(message)
            self._log_message(f"{'=' * 80}")
        else:
            print(f"\n{'=' * 80}")
            print(f"{message}")
            print(f"{'=' * 80}")

    def _print_footer(self, message: str) -> None:
        """Print test footer."""
        if self.is_xdist:
            self._log_message(f"{'=' * 80}")
            self._log_message(message)
            self._log_message(f"{'=' * 80}")
        else:
            print(f"{'=' * 80}")
            print(f"{message}")
            print(f"{'=' * 80}\n")

    def _print_status(self, message: str) -> None:
        """Print status message."""
        self._log_message(message)

    def _print_section(self, title: str, content: str) -> None:
        """Print content section."""
        if self.is_xdist:
            self._log_message(f"{'-' * 60}")
            self._log_message(title)
            self._log_message(f"{'-' * 60}")
            # Split content into lines for better logging
            for line in content.split("\n"):
                if line.strip():
                    self._log_message(line)
            self._log_message(f"{'-' * 60}")
        else:
            print(f"\n{'-' * 60}")
            print(f"{title}")
            print(f"{'-' * 60}")
            print(content)
            print(f"{'-' * 60}\n")
            sys.stdout.flush()


@contextmanager
def progress_context(test_name: str, reporter: TestProgressReporter):
    """Context manager for test progress reporting."""
    reporter.start_test(test_name)
    try:
        yield reporter
        reporter.end_test(success=True)
    except Exception:
        reporter.end_test(success=False)
        raise


class ContainerWaitReporter:
    """Reports progress while waiting for containers to become ready."""

    def __init__(self, reporter: TestProgressReporter):
        self.reporter = reporter
        self.start_time = time.time()
        self.last_update = 0.0

    def update(self, service: str, url: str, attempt: int, max_attempts: int) -> None:
        """Update wait progress."""
        current_time = time.time()

        # Only update every 2 seconds to avoid spam
        if current_time - self.last_update >= 2.0:
            self.reporter.waiting_for_service(service, url, attempt, max_attempts)
            self.last_update = current_time

    def success(self, service: str, url: str) -> None:
        """Report successful wait."""
        elapsed = time.time() - self.start_time
        self.reporter.service_ready(service, url, elapsed)

    def failure(self, service: str, url: str, error: str) -> None:
        """Report failed wait."""
        self.reporter.service_failed(service, url, error)


def get_test_reporter() -> TestProgressReporter:
    """Get test reporter based on pytest options."""
    config = getattr(pytest, "current_config", None)

    show_logs = False
    verbose_docker = False

    if config:
        show_logs = config.getoption("--show-container-logs", False)
        verbose_docker = config.getoption("--verbose-docker", False)

    return TestProgressReporter(
        show_container_logs=show_logs, verbose_docker=verbose_docker
    )


def format_troubleshooting_info(
    compose_file: Path,
    ports: Dict[str, int],
    failed_services: List[str],
    container_logs: Dict[str, str],
) -> str:
    """Format troubleshooting information for failed tests."""
    lines = [
        "\n" + "=" * 80,
        "🚨 INTEGRATION TEST FAILURE - TROUBLESHOOTING INFO",
        "=" * 80,
        "",
        f"📄 Docker Compose File: {compose_file}",
        "",
        "🔌 Port Allocations:",
    ]

    for name, port in ports.items():
        lines.append(f"  - {name}: {port}")

    if failed_services:
        lines.extend(
            [
                "",
                "❌ Failed Services:",
            ]
        )
        for service in failed_services:
            lines.append(f"  - {service}")

    lines.extend(
        [
            "",
            "🛠️  Debugging Commands:",
            f"  docker compose -f {compose_file} ps",
            f"  docker compose -f {compose_file} logs",
            f"  docker compose -f {compose_file} down -v",
            "",
            "🔍 Manual Service Testing:",
        ]
    )

    for name, port in ports.items():
        if "dataplane" in name or "api" in name:
            lines.append(f"  curl -u admin:adminpass http://localhost:{port}/v3/info")
        elif "health" in name:
            lines.append(f"  curl http://localhost:{port}/healthz")

    if container_logs:
        lines.extend(
            [
                "",
                "📜 Container Logs:",
                "",
            ]
        )
        for service, logs in container_logs.items():
            lines.extend(
                [
                    f"--- {service} ---",
                    logs[:1000] + ("..." if len(logs) > 1000 else ""),
                    "",
                ]
            )

    lines.extend(["=" * 80, ""])

    return "\n".join(lines)
