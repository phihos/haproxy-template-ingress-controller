"""
Advanced connection pool for HAProxy Dataplane API clients.

This module provides a sophisticated connection pool with reference counting,
TTL-based cleanup, and automatic idle connection management to ensure optimal
resource usage and persistent connections.
"""

import asyncio
import base64
import inspect
import logging
import time
from dataclasses import dataclass, field
from typing import Any, Dict, Optional, TYPE_CHECKING

import httpx
from haproxy_dataplane_v3 import AuthenticatedClient

if TYPE_CHECKING:
    from .endpoint import DataplaneEndpoint

logger = logging.getLogger(__name__)


@dataclass
class PooledClient:
    """Wrapper for pooled client with reference counting and TTL tracking."""

    client: AuthenticatedClient
    reference_count: int = 0
    last_used: float = field(default_factory=time.time)
    created_at: float = field(default_factory=time.time)

    def add_reference(self) -> None:
        """Add reference and update last used time."""
        self.reference_count += 1
        self.last_used = time.time()
        logger.debug(f"Client reference count increased to {self.reference_count}")

    def remove_reference(self) -> None:
        """Remove reference (safe decrement to 0)."""
        self.reference_count = max(0, self.reference_count - 1)
        logger.debug(f"Client reference count decreased to {self.reference_count}")

    def is_idle(self, idle_timeout: float) -> bool:
        """Check if client has been idle beyond timeout."""
        idle_time = time.time() - self.last_used
        return idle_time > idle_timeout

    def is_expired(self, max_age: float) -> bool:
        """Check if client has exceeded maximum age."""
        age = time.time() - self.created_at
        return age > max_age

    def get_age(self) -> float:
        """Get age of client in seconds."""
        return time.time() - self.created_at

    def get_idle_time(self) -> float:
        """Get idle time in seconds."""
        return time.time() - self.last_used


class DataplaneClientPool:
    """
    Advanced connection pool with reference counting and TTL cleanup.

    Features:
    - Reference counting for active clients
    - TTL-based cleanup of idle connections
    - Maximum age limits for connections
    - Background cleanup task
    - Connection statistics and monitoring
    """

    def __init__(
        self,
        idle_timeout: float = 300.0,  # 5 minutes
        max_age: float = 3600.0,  # 1 hour
        cleanup_interval: float = 60.0,  # 1 minute
    ):
        """
        Initialize client pool with configurable timeouts.

        Args:
            idle_timeout: Seconds before idle connections are cleaned up
            max_age: Maximum age in seconds before connections are recycled
            cleanup_interval: Seconds between cleanup runs
        """
        self._clients: Dict[str, PooledClient] = {}
        self._client_lock: Optional[asyncio.Lock] = None
        self._idle_timeout = idle_timeout
        self._max_age = max_age
        self._cleanup_interval = cleanup_interval
        self._cleanup_task: Optional[asyncio.Task] = None
        self._is_closed = False

        # Statistics tracking
        self._stats = {
            "clients_created": 0,
            "clients_reused": 0,
            "clients_cleaned": 0,
            "cleanup_runs": 0,
        }

        # Cleanup task will be started lazily when first needed

    def _start_cleanup_task(self) -> None:
        """Start background cleanup of idle/expired connections."""
        if not self._is_closed and (
            self._cleanup_task is None or self._cleanup_task.done()
        ):
            self._cleanup_task = asyncio.create_task(self._cleanup_loop())
            logger.debug("Started client pool cleanup task")

    async def _cleanup_loop(self) -> None:
        """Background cleanup of idle/expired connections."""
        logger.debug(
            f"Client pool cleanup loop started (interval: {self._cleanup_interval}s)"
        )

        while not self._is_closed:
            try:
                await asyncio.sleep(self._cleanup_interval)
                if not self._is_closed:
                    await self._cleanup_idle_connections()
            except asyncio.CancelledError:
                logger.debug("Client pool cleanup task cancelled")
                break
            except Exception as e:
                logger.warning(f"Client pool cleanup error: {e}")

        logger.debug("Client pool cleanup loop stopped")

    async def _cleanup_idle_connections(self) -> None:
        """Remove idle/expired connections with no references."""
        if self._client_lock is None:
            raise RuntimeError("Client lock not initialized")
        async with self._client_lock:
            if self._is_closed:
                return

            to_remove = []

            for key, pooled_client in self._clients.items():
                should_remove = pooled_client.reference_count == 0 and (
                    pooled_client.is_idle(self._idle_timeout)
                    or pooled_client.is_expired(self._max_age)
                )

                if should_remove:
                    to_remove.append(key)
                    logger.debug(
                        f"Marking client for cleanup: {key} "
                        f"(age: {pooled_client.get_age():.1f}s, "
                        f"idle: {pooled_client.get_idle_time():.1f}s, "
                        f"refs: {pooled_client.reference_count})"
                    )

            # Remove and close clients
            for key in to_remove:
                pooled_client = self._clients.pop(key)
                try:
                    # Close the underlying httpx client if available
                    try:
                        if (
                            hasattr(pooled_client.client, "_client")
                            and pooled_client.client._client is not None
                            and hasattr(pooled_client.client._client, "close")
                        ):
                            close_method = pooled_client.client._client.close
                            if inspect.iscoroutinefunction(close_method):
                                await close_method()
                            else:
                                close_method()
                        elif hasattr(pooled_client.client, "close"):
                            close_method = pooled_client.client.close
                            if inspect.iscoroutinefunction(close_method):
                                await close_method()
                            else:
                                close_method()
                    except Exception as e:
                        logger.debug(f"Failed to close client: {e}")

                    self._stats["clients_cleaned"] += 1
                    logger.debug(f"Cleaned up idle client: {key}")
                except Exception as e:
                    logger.warning(f"Error closing client {key}: {e}")

            if to_remove:
                self._stats["cleanup_runs"] += 1
                logger.info(f"Cleaned up {len(to_remove)} idle clients")

    async def get_client(
        self, endpoint: "DataplaneEndpoint", timeout: float
    ) -> AuthenticatedClient:
        """
        Get or create persistent client with reference counting.

        Args:
            endpoint: DataplaneEndpoint containing URL, auth, and pod context
            timeout: Request timeout in seconds

        Returns:
            AuthenticatedClient instance (persistent across calls)

        Raises:
            ValueError: If pool is closed or parameters are invalid
        """
        if self._is_closed:
            raise ValueError("Client pool is closed")

        if not endpoint or not endpoint.url:
            raise ValueError("endpoint cannot be empty")

        # Initialize lock and start cleanup task on first use
        if self._client_lock is None:
            self._client_lock = asyncio.Lock()
        self._start_cleanup_task()

        auth = (
            endpoint.dataplane_auth.username,
            endpoint.dataplane_auth.password.get_secret_value(),
        )

        client_key = f"{endpoint.url}:{timeout}:{auth[0]}:{auth[1]}"

        if self._client_lock is None:
            raise RuntimeError("Client lock not initialized")
        async with self._client_lock:
            if client_key in self._clients:
                # Reuse existing client
                pooled_client = self._clients[client_key]
                pooled_client.add_reference()
                self._stats["clients_reused"] += 1

                logger.debug(f"Reused existing client for {endpoint.url}")
                return pooled_client.client

            # Create new client
            auth_string = f"{auth[0]}:{auth[1]}"
            auth_token = base64.b64encode(auth_string.encode()).decode("ascii")

            client = AuthenticatedClient(
                base_url=endpoint.url,
                token=auth_token,
                prefix="Basic",
                timeout=httpx.Timeout(timeout),
            )

            # Wrap in pooled client and track it
            pooled_client = PooledClient(client=client)
            pooled_client.add_reference()
            self._clients[client_key] = pooled_client

            self._stats["clients_created"] += 1
            logger.debug(f"Created new persistent client for {endpoint.url}")

            return client

    async def release_client(
        self, endpoint: "DataplaneEndpoint", timeout: float
    ) -> None:
        """
        Release reference to a client (for manual reference management).

        Note: This is optional - cleanup will happen automatically based on TTL.
        """
        auth = (
            endpoint.dataplane_auth.username,
            endpoint.dataplane_auth.password.get_secret_value(),
        )
        client_key = f"{endpoint.url}:{timeout}:{auth[0]}:{auth[1]}"

        if self._client_lock is None:
            raise RuntimeError("Client lock not initialized")
        async with self._client_lock:
            if client_key in self._clients:
                self._clients[client_key].remove_reference()
                logger.debug(f"Released reference to client: {endpoint.url}")

    async def close_all(self) -> None:
        """Close all persistent connections and stop cleanup tasks."""
        logger.info("Closing all persistent connections")
        self._is_closed = True

        # Stop cleanup task
        if self._cleanup_task:
            self._cleanup_task.cancel()
            try:
                await self._cleanup_task
            except asyncio.CancelledError:
                pass

        # Close all clients
        if self._client_lock is None:
            raise RuntimeError("Client lock not initialized")
        async with self._client_lock:
            for key, pooled_client in self._clients.items():
                try:
                    # Close the underlying httpx client if available
                    try:
                        if (
                            hasattr(pooled_client.client, "_client")
                            and pooled_client.client._client is not None
                            and hasattr(pooled_client.client._client, "close")
                        ):
                            close_method = pooled_client.client._client.close
                            if inspect.iscoroutinefunction(close_method):
                                await close_method()
                            else:
                                close_method()
                        elif hasattr(pooled_client.client, "close"):
                            close_method = pooled_client.client.close
                            if inspect.iscoroutinefunction(close_method):
                                await close_method()
                            else:
                                close_method()
                    except Exception as e:
                        logger.debug(f"Failed to close client: {e}")
                    logger.debug(f"Closed client: {key}")
                except Exception as e:
                    logger.warning(f"Error closing client {key}: {e}")

            self._clients.clear()

        logger.info("All persistent connections closed")

    def get_pool_stats(self) -> Dict[str, Any]:
        """
        Get comprehensive pool statistics for monitoring.

        Returns:
            Dictionary with pool statistics and client information
        """
        active_clients = []

        for key, pooled_client in self._clients.items():
            active_clients.append(
                {
                    "key": key,
                    "reference_count": pooled_client.reference_count,
                    "age_seconds": pooled_client.get_age(),
                    "idle_seconds": pooled_client.get_idle_time(),
                    "created_at": pooled_client.created_at,
                    "last_used": pooled_client.last_used,
                }
            )

        return {
            "pool_config": {
                "idle_timeout": self._idle_timeout,
                "max_age": self._max_age,
                "cleanup_interval": self._cleanup_interval,
                "is_closed": self._is_closed,
            },
            "statistics": dict(self._stats),
            "active_connections": len(self._clients),
            "total_references": sum(
                pc.reference_count for pc in self._clients.values()
            ),
            "clients": active_clients,
        }

    def __del__(self):
        """Cleanup on deletion (best effort)."""
        if not self._is_closed and self._cleanup_task:
            logger.warning("DataplaneClientPool deleted without proper cleanup")
