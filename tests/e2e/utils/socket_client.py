"""
Simple socket client for management socket communication.
"""

import json
import socket
from typing import Any, Dict, Optional


def send_socket_command(socket_path: str, command: str) -> Optional[Dict[str, Any]]:
    """
    Send command to Unix socket using Python socket library.

    Args:
        socket_path: Path to Unix socket
        command: Command to send

    Returns:
        Parsed JSON response or None
    """
    try:
        # Create Unix socket client
        client = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        client.settimeout(5.0)

        # Connect to socket
        client.connect(socket_path)

        # Send command
        client.sendall(f"{command}\n".encode())

        # Receive response
        response = b""
        while True:
            data = client.recv(4096)
            if not data:
                break
            response += data
            # Check if we have a complete JSON response
            try:
                json.loads(response.decode())
                break
            except (json.JSONDecodeError, UnicodeDecodeError):
                continue

        client.close()

        # Parse response
        if response:
            return json.loads(response.decode())

    except Exception as e:
        print(f"Socket error: {e}")

    return None
