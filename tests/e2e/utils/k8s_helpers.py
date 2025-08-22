"""
Kubernetes interaction utilities for HAProxy Template IC tests.

This module contains utilities for interacting with Kubernetes resources,
pods, and the management socket during end-to-end tests.
"""

import json
import time

import pytest


def send_socket_command(pod, command, retries=3):
    """Send a command to the management socket using nc and return the response."""
    for attempt in range(retries):
        try:
            # Check if nc is available first
            pod.exec(["which", "nc"])

            # Use echo to pipe command to nc
            cmd = (
                f'echo "{command}" | nc local:/run/haproxy-template-ic/management.sock'
            )
            result = pod.exec(["sh", "-c", cmd])

            # Parse the response
            response_text = result.stdout.decode("utf-8").strip()
            if not response_text:
                raise ValueError("Empty response from management socket")
            return json.loads(response_text)
        except Exception as e:
            if attempt < retries - 1:
                time.sleep(2)  # Wait before retry
                continue
            pytest.fail(
                f"Failed to communicate with management socket after {retries} attempts: {e}"
            )
            return None
    return None
