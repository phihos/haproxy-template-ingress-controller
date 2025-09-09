"""
Socket client for connecting to HAProxy Template IC management socket.

Handles socket communication, caching, and retry logic.
"""

import asyncio
import json
import logging
import os
from datetime import datetime, timezone
from typing import Any, Dict, Optional

import kr8s.asyncio as kr8s
from kr8s.asyncio.objects import Deployment

from haproxy_template_ic.tui.models import SocketInfo
from haproxy_template_ic.tui.exceptions import (
    ConnectionError,
    ResourceNotFoundError,
    PodExecutionError,
)

logger = logging.getLogger(__name__)

__all__ = ["SocketClient"]


class SocketClient:
    """Client for HAProxy Template IC management socket communication."""

    def __init__(
        self,
        namespace: str,
        context: Optional[str] = None,
        deployment_name: str = "haproxy-template-ic",
        socket_path: Optional[str] = None,
    ):
        self.namespace = namespace
        self.context = context
        self.deployment_name = deployment_name
        self.socket_path = socket_path

        # Auto-detect socket path if not provided
        if not self.socket_path:
            default_socket = "/run/haproxy-template-ic/management.sock"
            if os.path.exists(default_socket):
                self.socket_path = default_socket
                logger.info(f"Auto-detected local socket at {default_socket}")

        # Controller pod info
        self._controller_pod_name: Optional[str] = None
        self._controller_pod_start_time: Optional[str] = None

    @property
    def controller_pod_name(self) -> Optional[str]:
        """Get the current controller pod name."""
        return self._controller_pod_name

    @property
    def controller_pod_start_time(self) -> Optional[str]:
        """Get the current controller pod start time."""
        return self._controller_pod_start_time

    async def execute_command(self, command: str) -> Dict[str, Any]:
        """Execute a command on the management socket."""
        return await self._execute_with_retry(command, max_retries=1)

    async def _get_fresh_api_client(self):
        """Get a fresh kr8s API client, bypassing any cached connections."""
        try:
            # Force kr8s to create a new API client by closing any existing ones
            import kr8s.asyncio as kr8s_async

            # Create API client with explicit context to ensure fresh connection
            if self.context:
                return await kr8s_async.api(context=self.context)
            else:
                return await kr8s_async.api()
        except Exception as e:
            logger.debug(f"Failed to create fresh API client: {e}")
            return None

    async def _execute_with_retry(
        self, command: str, max_retries: int = 1
    ) -> Dict[str, Any]:
        """Execute socket command with retry logic."""
        logger.debug(
            f"Starting socket command '{command}' with max_retries={max_retries}"
        )

        if self.socket_path:
            # Direct local socket connection
            return await self._execute_command_local(command)
        else:
            # Use kubectl exec with retry logic
            last_error = None

            for attempt in range(max_retries + 1):
                try:
                    logger.debug(
                        f"Attempt {attempt + 1}/{max_retries + 1} for command '{command}'"
                    )
                    # On retry attempts, try to use a fresh API client if the previous attempt
                    # failed due to connection issues
                    use_fresh_client = attempt > 0
                    result = await self._execute_command_remote(
                        command, use_fresh_client=use_fresh_client
                    )
                    logger.debug(
                        f"Socket command '{command}' succeeded on attempt {attempt + 1}"
                    )
                    return result
                except Exception as e:
                    last_error = e
                    if attempt < max_retries:
                        logger.debug(
                            f"Attempt {attempt + 1} failed: {e}, retrying in 0.1s with fresh connection..."
                        )
                        await asyncio.sleep(0.1)
                        continue
                    else:
                        logger.debug(f"Final attempt {attempt + 1} failed: {e}")
                    break

            # If all retries failed, raise the last error
            logger.debug(
                f"All {max_retries + 1} attempts failed for command '{command}', raising: {last_error}"
            )
            if last_error:
                raise last_error
            else:
                raise Exception(
                    f"Failed to execute command '{command}' after {max_retries + 1} attempts"
                )

    async def _execute_command_local(self, command: str) -> Dict[str, Any]:
        """Execute command directly on local management socket."""
        logger.debug(
            f"Executing socket command '{command}' on local socket {self.socket_path}"
        )

        try:
            reader, writer = await asyncio.open_unix_connection(self.socket_path)
            writer.write(f"{command}\n".encode())
            await writer.drain()

            # Read complete response by accumulating chunks until EOF
            response_chunks = []
            while True:
                chunk = await reader.read(8192)  # Read in 8KB chunks
                if not chunk:
                    break
                response_chunks.append(chunk)

            writer.close()
            await writer.wait_closed()

            response = b"".join(response_chunks)

            # Parse the JSON response
            data = json.loads(response.decode())
            logger.debug(
                f"Local socket command '{command}' succeeded, result keys: {list(data.keys()) if isinstance(data, dict) else 'non-dict'}"
            )
            return data

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON response for command '{command}': {e}")
            logger.debug(
                f"Raw response that failed parsing: {response.decode() if 'response' in locals() else 'N/A'}"
            )
            raise PodExecutionError("local", command, e)
        except Exception as e:
            logger.error(f"Failed to connect to local socket {self.socket_path}: {e}")
            raise ConnectionError(
                f"Failed to connect to socket {self.socket_path}: {e}"
            )

    async def _execute_command_remote(
        self, command: str, use_fresh_client: bool = False
    ) -> Dict[str, Any]:
        """Execute a single command on the management socket via kubectl exec."""
        logger.debug(
            f"Executing socket command '{command}' (fresh_client={use_fresh_client})"
        )

        try:
            logger.debug(
                f"Fetching pods for deployment '{self.namespace}/{self.deployment_name}'"
            )
            # Get the deployment and its pods
            if use_fresh_client:
                api = await self._get_fresh_api_client()
                if api:
                    deployment = await Deployment.get(
                        self.deployment_name, namespace=self.namespace, api=api
                    )
                else:
                    # Fallback if fresh client creation failed
                    deployment = await Deployment.get(
                        self.deployment_name, namespace=self.namespace
                    )
            elif self.context:
                api = await kr8s.api(context=self.context)
                deployment = await Deployment.get(
                    self.deployment_name, namespace=self.namespace, api=api
                )
            else:
                deployment = await Deployment.get(
                    self.deployment_name, namespace=self.namespace
                )
            pods = await deployment.pods()

            if not pods:
                logger.error(
                    f"No pods found for deployment '{self.deployment_name}' in namespace '{self.namespace}'"
                )
                raise ResourceNotFoundError(
                    "deployment", self.deployment_name, self.namespace
                )

            # Use the first available pod (they should all be equivalent)
            pod = pods[0]
            pod_name = pod.metadata.name

            logger.debug(f"Using pod '{self.namespace}/{pod_name}'")

            # Store the controller pod name and start time
            if self._controller_pod_name != pod_name:
                self._controller_pod_name = pod_name
                logger.debug(f"Controller pod name updated to: {pod_name}")

            # Extract and store pod start time
            pod_start_time = pod.status.get("startTime") if pod.status else None
            if pod_start_time and self._controller_pod_start_time != pod_start_time:
                self._controller_pod_start_time = pod_start_time
                logger.debug(f"Controller pod start time updated to: {pod_start_time}")

            logger.debug(f"Using pod '{pod_name}' for socket command '{command}'")

            # Execute the socat command to connect to management socket
            exec_command = f"echo '{command}' | socat - UNIX-CONNECT:/run/haproxy-template-ic/management.sock"
            logger.debug(f"Executing: {exec_command}")

            exec_result = await pod.exec(
                command=["sh", "-c", exec_command], container="controller"
            )

            # Log raw response info
            response_size = len(exec_result.stdout)
            logger.debug(
                f"Received {response_size} bytes from socket for command '{command}'"
            )
            if response_size > 0:
                # Log first few chars for debugging
                preview = str(exec_result.stdout[:100])
                if len(exec_result.stdout) > 100:
                    preview += "..."
                logger.debug(f"Response preview: {preview}")

            # Parse the JSON response
            data = json.loads(exec_result.stdout)
            logger.debug(
                f"Socket command '{command}' succeeded, result keys: {list(data.keys()) if isinstance(data, dict) else 'non-dict'}"
            )

            return data

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON response for command '{command}': {e}")
            logger.debug(
                f"Raw response that failed parsing: {exec_result.stdout if 'exec_result' in locals() else 'N/A'}"
            )
            pod_name = locals().get("pod_name", "unknown")
            raise PodExecutionError(pod_name, command, e)
        except Exception as e:
            # Use warning for expected connection failures to avoid verbose stack traces
            error_str = str(e).lower()
            connection_errors = [
                "connection refused",
                "all connection attempts failed",
                "no such file",
                "no route to host",
                "network is unreachable",
                "name or service not known",
                "context deadline exceeded",
                "client: etcd cluster unavailable",
                "the server could not find the requested resource",
                "unauthorized",
                "forbidden",
                "certificate",
                "tls handshake",
                "couldn't get current server api group list",
                "the connection to the server",
            ]

            if any(keyword in error_str for keyword in connection_errors):
                logger.warning(
                    f"Socket command '{command}' failed (connection issue): {e}"
                )
                # Raise ConnectionError to trigger reconnection logic
                raise ConnectionError("Failed to connect to cluster or pods", e)
            else:
                logger.error(f"Failed to execute socket command '{command}': {e}")
                pod_name = locals().get("pod_name", "unknown")
                raise PodExecutionError(pod_name, command, e)

    def get_socket_info(self) -> SocketInfo:
        """Get current socket connection information."""
        return SocketInfo(
            pod_name=self._controller_pod_name or "unknown",
            socket_path="/run/haproxy-template-ic/management.sock",
            accessible=self._controller_pod_name is not None,
            last_check=datetime.now(timezone.utc)
            if self._controller_pod_name
            else None,
        )
