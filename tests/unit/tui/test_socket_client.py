"""
Unit tests for SocketClient.

Tests socket communication, retry logic, and error handling.
"""

import json
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from haproxy_template_ic.tui.socket_client import SocketClient
from haproxy_template_ic.tui.models import SocketInfo
from haproxy_template_ic.tui.exceptions import (
    ConnectionError,
    PodExecutionError,
)


class TestSocketClient:
    """Test SocketClient class."""

    @pytest.fixture
    def socket_client(self):
        """Create a SocketClient instance."""
        return SocketClient(
            namespace="test-namespace",
            context="test-context",
            deployment_name="test-deployment",
        )

    @pytest.fixture
    def socket_client_with_local_path(self):
        """Create a SocketClient with local socket path."""
        with patch("os.path.exists", return_value=True):
            return SocketClient(
                namespace="test-namespace", socket_path="/test/socket/path"
            )

    def test_init_without_socket_path(self):
        """Test SocketClient initialization without socket path."""
        with patch("os.path.exists", return_value=False):
            client = SocketClient(
                namespace="test-ns", context="test-ctx", deployment_name="test-deploy"
            )
        assert client.namespace == "test-ns"
        assert client.context == "test-ctx"
        assert client.deployment_name == "test-deploy"
        assert client.socket_path is None

    def test_init_with_auto_detected_socket(self):
        """Test SocketClient initialization with auto-detected socket."""
        with patch("os.path.exists", return_value=True):
            client = SocketClient(namespace="test-ns")
        assert client.socket_path == "/run/haproxy-template-ic/management.sock"

    def test_init_with_explicit_socket_path(self):
        """Test SocketClient initialization with explicit socket path."""
        client = SocketClient(namespace="test-ns", socket_path="/custom/socket/path")
        assert client.socket_path == "/custom/socket/path"

    def test_controller_pod_properties(self, socket_client):
        """Test controller pod name and start time properties."""
        assert socket_client.controller_pod_name is None
        assert socket_client.controller_pod_start_time is None

        # Set values
        socket_client._controller_pod_name = "test-pod"
        socket_client._controller_pod_start_time = "2024-01-15T10:30:00Z"

        assert socket_client.controller_pod_name == "test-pod"
        assert socket_client.controller_pod_start_time == "2024-01-15T10:30:00Z"


class TestSocketClientLocalExecution:
    """Test local socket execution."""

    @pytest.fixture
    def local_socket_client(self):
        """Create a SocketClient with local socket."""
        with patch("os.path.exists", return_value=True):
            return SocketClient(namespace="test-namespace", socket_path="/test/socket")

    @pytest.mark.asyncio
    async def test_execute_command_local_success(self, local_socket_client):
        """Test successful local socket command execution."""
        mock_response = {"result": "success", "data": [1, 2, 3]}
        mock_response_bytes = json.dumps(mock_response).encode()

        mock_reader = AsyncMock()
        mock_writer = AsyncMock()

        # Mock reader to return response data then EOF
        mock_reader.read.side_effect = [mock_response_bytes, b""]

        with patch(
            "asyncio.open_unix_connection", return_value=(mock_reader, mock_writer)
        ):
            result = await local_socket_client.execute_command("dump all")

        assert result == mock_response
        mock_writer.write.assert_called_once_with(b"dump all\n")
        mock_writer.drain.assert_called_once()
        mock_writer.close.assert_called_once()

    @pytest.mark.asyncio
    async def test_execute_command_local_chunked_response(self, local_socket_client):
        """Test local socket command with chunked response."""
        mock_response = {"large": "data" * 1000}
        mock_response_bytes = json.dumps(mock_response).encode()

        # Split response into chunks
        chunk_size = len(mock_response_bytes) // 3
        chunks = [
            mock_response_bytes[:chunk_size],
            mock_response_bytes[chunk_size : chunk_size * 2],
            mock_response_bytes[chunk_size * 2 :],
            b"",  # EOF
        ]

        mock_reader = AsyncMock()
        mock_writer = AsyncMock()
        mock_reader.read.side_effect = chunks

        with patch(
            "asyncio.open_unix_connection", return_value=(mock_reader, mock_writer)
        ):
            result = await local_socket_client.execute_command("dump config")

        assert result == mock_response

    @pytest.mark.asyncio
    async def test_execute_command_local_connection_error(self, local_socket_client):
        """Test local socket connection error."""
        with patch(
            "asyncio.open_unix_connection", side_effect=OSError("Connection failed")
        ):
            with pytest.raises(ConnectionError) as exc_info:
                await local_socket_client.execute_command("dump all")

        assert "Failed to connect to socket" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_execute_command_local_json_decode_error(self, local_socket_client):
        """Test local socket JSON decode error."""
        mock_reader = AsyncMock()
        mock_writer = AsyncMock()
        mock_reader.read.side_effect = [b"invalid json", b""]

        with patch(
            "asyncio.open_unix_connection", return_value=(mock_reader, mock_writer)
        ):
            with pytest.raises(PodExecutionError) as exc_info:
                await local_socket_client.execute_command("dump all")

        assert exc_info.value.pod_name == "local"
        assert exc_info.value.command == "dump all"


class TestSocketClientRemoteExecution:
    """Test remote (Kubernetes) socket execution."""

    @pytest.fixture
    def remote_socket_client(self):
        """Create a SocketClient for remote execution."""
        return SocketClient(
            namespace="test-namespace", deployment_name="test-deployment"
        )

    @pytest.fixture
    def mock_deployment(self):
        """Mock Kubernetes deployment."""
        mock_deployment = MagicMock()

        # Mock pod
        mock_pod = MagicMock()
        mock_pod.metadata.name = "controller-pod-1"
        mock_pod.status = {"startTime": "2024-01-15T10:30:00Z"}

        # Mock exec result
        mock_exec_result = MagicMock()
        mock_exec_result.stdout = json.dumps({"result": "success"})
        mock_pod.exec = AsyncMock(return_value=mock_exec_result)

        mock_deployment.pods = AsyncMock(return_value=[mock_pod])
        return mock_deployment, mock_pod

    @pytest.mark.asyncio
    async def test_execute_command_remote_success(
        self, remote_socket_client, mock_deployment
    ):
        """Test successful remote socket command execution."""
        deployment, pod = mock_deployment

        with patch("kr8s.asyncio.objects.Deployment.get", return_value=deployment):
            with patch.object(deployment, "pods", AsyncMock(return_value=[pod])):
                result = await remote_socket_client.execute_command("dump all")

        assert result == {"result": "success"}
        assert remote_socket_client.controller_pod_name == "controller-pod-1"
        assert remote_socket_client.controller_pod_start_time == "2024-01-15T10:30:00Z"

        # Verify exec command
        expected_cmd = [
            "sh",
            "-c",
            "echo 'dump all' | socat - UNIX-CONNECT:/run/haproxy-template-ic/management.sock",
        ]
        pod.exec.assert_called_once_with(command=expected_cmd, container="controller")

    @pytest.mark.asyncio
    async def test_execute_command_remote_no_pods(self, remote_socket_client):
        """Test remote execution with no pods found."""
        mock_deployment = MagicMock()
        mock_deployment.pods = AsyncMock(return_value=[])

        with patch("kr8s.asyncio.objects.Deployment.get", return_value=mock_deployment):
            with pytest.raises(PodExecutionError) as exc_info:
                await remote_socket_client.execute_command("dump all")

        # The ResourceNotFoundError is wrapped in PodExecutionError
        assert "deployment 'test-deployment'" in str(exc_info.value)
        assert "test-namespace" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_execute_command_remote_json_decode_error(
        self, remote_socket_client, mock_deployment
    ):
        """Test remote execution with JSON decode error."""
        deployment, pod = mock_deployment

        # Mock invalid JSON response
        mock_exec_result = MagicMock()
        mock_exec_result.stdout = "invalid json"
        pod.exec = AsyncMock(return_value=mock_exec_result)

        with patch("kr8s.asyncio.objects.Deployment.get", return_value=deployment):
            with pytest.raises(PodExecutionError) as exc_info:
                await remote_socket_client.execute_command("dump all")

        assert exc_info.value.pod_name == "controller-pod-1"
        assert exc_info.value.command == "dump all"

    @pytest.mark.asyncio
    async def test_execute_command_remote_connection_error(self, remote_socket_client):
        """Test remote execution with connection error."""
        with patch(
            "kr8s.asyncio.objects.Deployment.get",
            side_effect=Exception("Connection refused"),
        ):
            with pytest.raises(ConnectionError) as exc_info:
                await remote_socket_client.execute_command("dump all")

        assert "Failed to connect to cluster or pods" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_execute_command_remote_with_context(self):
        """Test remote execution with Kubernetes context."""
        client = SocketClient(
            namespace="test-ns", context="test-context", deployment_name="test-deploy"
        )

        mock_api = AsyncMock()
        mock_deployment = MagicMock()
        mock_pod = MagicMock()
        mock_pod.metadata.name = "test-pod"
        mock_pod.status = {}
        mock_exec_result = MagicMock()
        mock_exec_result.stdout = json.dumps({"result": "ok"})
        mock_pod.exec = AsyncMock(return_value=mock_exec_result)
        mock_deployment.pods = AsyncMock(return_value=[mock_pod])

        with patch("kr8s.asyncio.api", return_value=mock_api):
            with patch(
                "kr8s.asyncio.objects.Deployment.get", return_value=mock_deployment
            ):
                result = await client.execute_command("test command")

        # Should call kr8s.api with context
        assert result == {"result": "ok"}


class TestSocketClientRetryLogic:
    """Test retry logic."""

    @pytest.fixture
    def socket_client(self):
        """Create a SocketClient for retry testing."""
        return SocketClient(namespace="test-ns")

    @pytest.mark.asyncio
    async def test_execute_with_retry_success_first_attempt(self, socket_client):
        """Test successful execution on first attempt."""
        expected_result = {"result": "success"}

        with patch.object(
            socket_client,
            "_execute_command_remote",
            new_callable=AsyncMock,
            return_value=expected_result,
        ):
            result = await socket_client._execute_with_retry(
                "test command", max_retries=2
            )

        assert result == expected_result

    @pytest.mark.asyncio
    async def test_execute_with_retry_success_after_failure(self, socket_client):
        """Test successful execution after initial failure."""
        expected_result = {"result": "success"}

        with patch.object(
            socket_client, "_execute_command_remote", new_callable=AsyncMock
        ) as mock_exec:
            mock_exec.side_effect = [Exception("Connection failed"), expected_result]

            result = await socket_client._execute_with_retry(
                "test command", max_retries=1
            )

        assert result == expected_result
        assert mock_exec.call_count == 2

    @pytest.mark.asyncio
    async def test_execute_with_retry_all_attempts_fail(self, socket_client):
        """Test failure after all retry attempts."""
        with patch.object(
            socket_client,
            "_execute_command_remote",
            new_callable=AsyncMock,
            side_effect=Exception("Persistent error"),
        ):
            with pytest.raises(Exception) as exc_info:
                await socket_client._execute_with_retry("test command", max_retries=2)

        assert "Persistent error" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_execute_with_retry_sleep_between_attempts(self, socket_client):
        """Test retry delay between attempts."""
        with patch.object(
            socket_client,
            "_execute_command_remote",
            new_callable=AsyncMock,
            side_effect=Exception("Error"),
        ):
            with patch("asyncio.sleep") as mock_sleep:
                with pytest.raises(Exception):
                    await socket_client._execute_with_retry(
                        "test command", max_retries=1
                    )

                mock_sleep.assert_called_once_with(0.1)

    @pytest.mark.asyncio
    async def test_get_fresh_api_client(self, socket_client):
        """Test fresh API client creation."""
        mock_api = AsyncMock()

        with patch("kr8s.asyncio.api", return_value=mock_api) as mock_kr8s_api:
            result = await socket_client._get_fresh_api_client()

        assert result == mock_api
        mock_kr8s_api.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_fresh_api_client_with_context(self):
        """Test fresh API client creation with context."""
        client = SocketClient(namespace="test-ns", context="test-context")
        mock_api = AsyncMock()

        with patch("kr8s.asyncio.api", return_value=mock_api) as mock_kr8s_api:
            result = await client._get_fresh_api_client()

        assert result == mock_api
        mock_kr8s_api.assert_called_once_with(context="test-context")

    @pytest.mark.asyncio
    async def test_get_fresh_api_client_error(self, socket_client):
        """Test fresh API client creation error handling."""
        with patch("kr8s.asyncio.api", side_effect=Exception("API error")):
            result = await socket_client._get_fresh_api_client()

        assert result is None


class TestSocketClientErrorHandling:
    """Test error handling and categorization."""

    @pytest.fixture
    def socket_client(self):
        """Create a SocketClient for error testing."""
        return SocketClient(namespace="test-ns")

    @pytest.mark.asyncio
    async def test_connection_error_detection(self, socket_client):
        """Test detection of various connection errors."""
        connection_errors = [
            "connection refused",
            "all connection attempts failed",
            "no such file",
            "no route to host",
            "network is unreachable",
            "name or service not known",
            "context deadline exceeded",
            "unauthorized",
            "forbidden",
            "certificate error",
            "tls handshake failed",
        ]

        for error_msg in connection_errors:
            with patch.object(
                socket_client,
                "_execute_command_remote",
                side_effect=Exception(error_msg),
            ):
                with pytest.raises(Exception) as exc_info:
                    await socket_client._execute_with_retry(
                        "test command", max_retries=0
                    )
                assert error_msg in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_non_connection_error_handling(self, socket_client):
        """Test handling of non-connection errors."""
        with patch.object(
            socket_client,
            "_execute_command_remote",
            side_effect=Exception("JSON parse error"),
        ):
            with pytest.raises(Exception) as exc_info:
                await socket_client._execute_with_retry("test command", max_retries=0)
            assert "JSON parse error" in str(exc_info.value)

    def test_get_socket_info_with_pod_name(self, socket_client):
        """Test socket info when pod name is available."""
        socket_client._controller_pod_name = "test-pod"

        info = socket_client.get_socket_info()

        assert isinstance(info, SocketInfo)
        assert info.pod_name == "test-pod"
        assert info.socket_path == "/run/haproxy-template-ic/management.sock"
        assert info.accessible is True
        assert info.last_check is not None

    def test_get_socket_info_without_pod_name(self, socket_client):
        """Test socket info when no pod name is available."""
        info = socket_client.get_socket_info()

        assert isinstance(info, SocketInfo)
        assert info.pod_name == "unknown"
        assert info.accessible is False
        assert info.last_check is None


class TestSocketClientIntegration:
    """Integration-style tests for SocketClient."""

    @pytest.mark.asyncio
    async def test_full_remote_execution_flow(self):
        """Test complete remote execution flow."""
        client = SocketClient(
            namespace="test-namespace", deployment_name="test-deployment"
        )

        # Mock the entire Kubernetes interaction chain
        mock_deployment = MagicMock()
        mock_pod = MagicMock()
        mock_pod.metadata.name = "controller-pod-1"
        mock_pod.status = {"startTime": "2024-01-15T10:30:00Z"}

        expected_response = {
            "operator": {"status": "RUNNING"},
            "pods": [{"name": "haproxy-1", "ip": "10.0.0.1"}],
        }

        mock_exec_result = MagicMock()
        mock_exec_result.stdout = json.dumps(expected_response)
        mock_pod.exec = AsyncMock(return_value=mock_exec_result)
        mock_deployment.pods = AsyncMock(return_value=[mock_pod])

        with patch("kr8s.asyncio.objects.Deployment.get", return_value=mock_deployment):
            result = await client.execute_command("dump dashboard")

        assert result == expected_response
        assert client.controller_pod_name == "controller-pod-1"

    @pytest.mark.asyncio
    async def test_retry_with_fresh_client(self):
        """Test retry mechanism with fresh API client."""
        client = SocketClient(namespace="test-ns")

        mock_deployment = MagicMock()
        mock_pod = MagicMock()
        mock_pod.metadata.name = "test-pod"
        mock_pod.status = {}
        mock_exec_result = MagicMock()
        mock_exec_result.stdout = json.dumps({"result": "success"})
        mock_pod.exec = AsyncMock(return_value=mock_exec_result)
        mock_deployment.pods = AsyncMock(return_value=[mock_pod])

        with patch("kr8s.asyncio.objects.Deployment.get") as mock_get:
            # First attempt fails, second succeeds
            mock_get.side_effect = [Exception("Connection error"), mock_deployment]

            with patch.object(
                client, "_get_fresh_api_client", return_value=AsyncMock()
            ):
                result = await client._execute_with_retry("test command", max_retries=1)

        assert result == {"result": "success"}
        assert mock_get.call_count == 2

    @pytest.mark.asyncio
    async def test_local_vs_remote_execution_paths(self):
        """Test that local and remote execution paths are chosen correctly."""
        # Test local path
        with patch("os.path.exists", return_value=True):
            local_client = SocketClient(
                namespace="test-ns", socket_path="/local/socket"
            )

        mock_response = {"local": True}
        with patch.object(
            local_client, "_execute_command_local", return_value=mock_response
        ) as mock_local:
            result = await local_client.execute_command("test")

        assert result == mock_response
        mock_local.assert_called_once_with("test")

        # Test remote path
        remote_client = SocketClient(namespace="test-ns")  # No socket path

        with patch.object(
            remote_client, "_execute_with_retry", return_value={"remote": True}
        ) as mock_remote:
            result = await remote_client.execute_command("test")

        assert result == {"remote": True}
        mock_remote.assert_called_once_with("test", max_retries=1)
