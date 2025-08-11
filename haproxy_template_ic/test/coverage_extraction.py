"""
Coverage extraction utilities for Kubernetes pods.

This module provides functionality to extract coverage data from pods running
instrumented Python code with coverage.py.
"""

import os
import time
from typing import Optional


def find_coverage_process(pod) -> Optional[str]:
    """Find the PID of the Python coverage process in the pod.

    Args:
        pod: The Kubernetes pod object with exec capability

    Returns:
        The PID as a string, or None if not found
    """
    result = pod.exec(
        [
            "sh",
            "-c",
            "for pid in /proc/[0-9]*; do if grep -q coverage_wrapper.py $pid/cmdline 2>/dev/null; then basename $pid; break; fi; done",
        ],
        capture_output=True,
    )
    if result.stdout:
        return result.stdout.decode().strip().split("\n")[0]
    return None


def trigger_coverage_save(pod) -> bool:
    """Send SIGUSR1 signal to trigger coverage data save.

    Args:
        pod: The Kubernetes pod object with exec capability

    Returns:
        True if signal was sent successfully, False otherwise
    """
    python_pid = find_coverage_process(pod)
    if python_pid:
        print(f"Found Python coverage process at PID: {python_pid}")
        result = pod.exec(["sh", "-c", f"kill -USR1 {python_pid}"], capture_output=True)
        success = result.returncode == 0
        print(f"USR1 signal sent to Python process: {success}")
        return success
    else:
        print("Python coverage process not found, signaling via dumb-init")
        result = pod.exec(["sh", "-c", "kill -USR1 1"], capture_output=True)
        success = result.returncode == 0
        print(f"USR1 signal sent to PID 1: {success}")
        return success


def wait_and_copy_coverage(pod, max_wait_time: float = 4.0) -> Optional[bytes]:
    """Wait for coverage file to appear and copy it.

    Args:
        pod: The Kubernetes pod object with exec capability
        max_wait_time: Maximum time to wait in seconds

    Returns:
        Coverage data as bytes, or None if not found within timeout
    """
    max_iterations = int(max_wait_time / 0.2)
    for i in range(max_iterations):
        time.sleep(0.2)
        result = pod.exec(["test", "-f", "/app/.coverage"], capture_output=True)
        if result.returncode == 0:  # File exists
            print(f"Coverage file found after {i * 0.2:.1f}s")
            try:
                result = pod.exec(["cat", "/app/.coverage"], capture_output=True)
                if result.stdout and len(result.stdout) > 100:
                    print(
                        f"Successfully copied coverage data ({len(result.stdout)} bytes)"
                    )
                    return result.stdout
            except Exception as e:
                print(f"Failed to copy coverage file: {e}")
                continue

    print("Coverage file not found within timeout")
    return None


def try_fallback_coverage_paths(pod) -> Optional[bytes]:
    """Try to find coverage data in fallback locations.

    Args:
        pod: The Kubernetes pod object with exec capability

    Returns:
        Coverage data as bytes, or None if not found
    """
    coverage_paths = ["/app/.coverage", "/tmp/.coverage", "/.coverage"]

    for path in coverage_paths:
        try:
            result = pod.exec(["cat", path], capture_output=True)
            if result.stdout and len(result.stdout) > 100:
                print(f"Found coverage data at {path} ({len(result.stdout)} bytes)")
                return result.stdout
        except Exception as e:
            print(f"Failed to read {path}: {e}")
            continue

    return None


def save_coverage_data(coverage_data: bytes, test_name: str, project_root: str) -> str:
    """Save coverage data to a file for later combining.

    Args:
        coverage_data: The coverage data as bytes
        test_name: Name of the test (used in filename)
        project_root: Path to the project root directory

    Returns:
        Path to the saved coverage file
    """
    coverage_file = os.path.join(project_root, f".coverage.acceptance.{test_name}")
    with open(coverage_file, "wb") as f:
        f.write(coverage_data)

    print(f"Saved coverage data to {coverage_file}")
    return coverage_file


def extract_coverage_from_pod(pod, test_name: str, project_root: str) -> Optional[str]:
    """Extract coverage data from a pod and save it to a file.

    This is the main entry point that orchestrates the coverage extraction process.

    Args:
        pod: The Kubernetes pod object with exec capability
        test_name: Name of the test (used in filename)
        project_root: Path to the project root directory

    Returns:
        Path to the saved coverage file, or None if extraction failed
    """
    try:
        print("Collecting coverage data from container...")

        # Trigger coverage save via signal
        trigger_coverage_save(pod)

        # Wait for coverage file and copy it
        coverage_data = wait_and_copy_coverage(pod)

        # Try fallback locations if the primary method failed
        if not coverage_data:
            coverage_data = try_fallback_coverage_paths(pod)

        # Save the coverage data for later combining
        if coverage_data:
            return save_coverage_data(coverage_data, test_name, project_root)
        else:
            print("No coverage data found in container")
            return None

    except Exception as e:
        print(f"Failed to collect coverage: {e}")
        return None
