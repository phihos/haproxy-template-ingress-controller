"""
Resilience and error recovery patterns for HAProxy Template IC.

This module provides resilient operation patterns including:
- Exponential backoff retry mechanisms
- Circuit breaker pattern for failing services
- Adaptive timeout strategies
- Error categorization and recovery policies
"""

import asyncio
import time
from dataclasses import dataclass
from enum import Enum
from typing import Any, Awaitable, Callable, Dict, List, Optional, TypeVar
from uuid import uuid4

from haproxy_template_ic.metrics import get_metrics_collector
from haproxy_template_ic.structured_logging import get_structured_logger

T = TypeVar("T")

logger = get_structured_logger(__name__)


class ErrorCategory(Enum):
    """Categories of errors for different retry strategies."""

    NETWORK = "network"  # Connection timeouts, DNS failures
    RATE_LIMIT = "rate_limit"  # HTTP 429, backpressure
    SERVER_ERROR = "server_error"  # HTTP 5xx responses
    CLIENT_ERROR = "client_error"  # HTTP 4xx responses
    VALIDATION = "validation"  # Configuration validation errors
    UNKNOWN = "unknown"  # Uncategorized errors


@dataclass
class TimeoutConfig:
    """Configuration for adaptive timeout behavior."""

    initial_timeout: float = 30.0  # Initial timeout in seconds
    max_timeout: float = 300.0  # Maximum timeout in seconds
    timeout_multiplier: float = 1.5  # Timeout increase factor on failure
    success_timeout_reduction: float = 0.9  # Timeout reduction on success


@dataclass
class RetryPolicy:
    """Configuration for retry behavior."""

    max_attempts: int = 3
    base_delay: float = 1.0  # Base delay in seconds
    max_delay: float = 60.0  # Maximum delay in seconds
    exponential_base: float = 2.0  # Exponential backoff base
    jitter_factor: float = 0.1  # Random jitter to avoid thundering herd
    timeout_config: Optional[TimeoutConfig] = None

    # Error categories that should be retried
    retryable_categories: Optional[List[ErrorCategory]] = None

    def __post_init__(self):
        if self.retryable_categories is None:
            self.retryable_categories = [
                ErrorCategory.NETWORK,
                ErrorCategory.RATE_LIMIT,
                ErrorCategory.SERVER_ERROR,
            ]
        if self.timeout_config is None:
            self.timeout_config = TimeoutConfig()


@dataclass
class CircuitBreakerConfig:
    """Configuration for circuit breaker pattern."""

    failure_threshold: int = 5  # Failures before opening circuit
    recovery_timeout: int = 60  # Seconds before attempting recovery
    success_threshold: int = 2  # Successes needed to close circuit


class CircuitState(Enum):
    """States of the circuit breaker."""

    CLOSED = "closed"  # Normal operation
    OPEN = "open"  # Failing, blocking requests
    HALF_OPEN = "half_open"  # Testing if service recovered


@dataclass
class OperationResult:
    """Result of a resilient operation attempt."""

    success: bool
    result: Any = None
    error: Optional[Exception] = None
    attempt: int = 1
    total_duration: float = 0.0
    error_category: ErrorCategory = ErrorCategory.UNKNOWN


class AdaptiveTimeoutManager:
    """Manages adaptive timeout adjustments based on operation success/failure."""

    def __init__(self, config: TimeoutConfig):
        self.config = config
        self.current_timeout = config.initial_timeout

    def get_timeout(self) -> float:
        """Get the current adaptive timeout value."""
        return self.current_timeout

    def record_success(self) -> None:
        """Adjust timeout downward after successful operation."""
        self.current_timeout = max(
            self.config.initial_timeout,
            self.current_timeout * self.config.success_timeout_reduction,
        )

    def record_failure(self) -> None:
        """Adjust timeout upward after failed operation."""
        self.current_timeout = min(
            self.config.max_timeout,
            self.current_timeout * self.config.timeout_multiplier,
        )


class CircuitBreaker:
    """Circuit breaker implementation for failing operations."""

    def __init__(
        self,
        name: str,
        config: CircuitBreakerConfig,
        timeout_config: Optional[TimeoutConfig] = None,
    ):
        self.name = name
        self.config = config
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.success_count = 0
        self.last_failure_time = 0.0
        self.operation_id = str(uuid4())[:8]

        # Add adaptive timeout management
        self.timeout_manager = None
        if timeout_config:
            self.timeout_manager = AdaptiveTimeoutManager(timeout_config)

    def can_execute(self) -> bool:
        """Check if operation can be executed based on circuit state."""
        metrics = get_metrics_collector()

        if self.state == CircuitState.CLOSED:
            return True

        if self.state == CircuitState.OPEN:
            # Check if recovery timeout has passed
            if time.time() - self.last_failure_time > self.config.recovery_timeout:
                logger.info(
                    f"Circuit breaker {self.name} attempting recovery",
                    circuit_state=self.state.value,
                    operation_id=self.operation_id,
                )
                self.state = CircuitState.HALF_OPEN
                self.success_count = 0
                return True

            metrics.record_error("circuit_breaker_blocked", "resilience")
            return False

        # HALF_OPEN state
        return True

    def record_success(self) -> None:
        """Record a successful operation."""
        if self.state == CircuitState.HALF_OPEN:
            self.success_count += 1
            if self.success_count >= self.config.success_threshold:
                logger.info(
                    f"Circuit breaker {self.name} closing after recovery",
                    success_count=self.success_count,
                    operation_id=self.operation_id,
                )
                self.state = CircuitState.CLOSED
                self.failure_count = 0

        if self.state == CircuitState.CLOSED:
            self.failure_count = 0  # Reset failure count on success

        # Adjust timeout downward on success
        if self.timeout_manager:
            self.timeout_manager.record_success()

    def record_failure(self) -> None:
        """Record a failed operation."""
        self.failure_count += 1
        self.last_failure_time = time.time()

        # Adjust timeout upward on failure
        if self.timeout_manager:
            self.timeout_manager.record_failure()

        if self.state == CircuitState.CLOSED:
            if self.failure_count >= self.config.failure_threshold:
                logger.warning(
                    f"Circuit breaker {self.name} opening due to failures",
                    failure_count=self.failure_count,
                    threshold=self.config.failure_threshold,
                    current_timeout=self.timeout_manager.get_timeout()
                    if self.timeout_manager
                    else None,
                    operation_id=self.operation_id,
                )
                self.state = CircuitState.OPEN

        elif self.state == CircuitState.HALF_OPEN:
            logger.warning(
                f"Circuit breaker {self.name} re-opening after failed recovery",
                operation_id=self.operation_id,
            )
            self.state = CircuitState.OPEN

    def get_adaptive_timeout(self) -> Optional[float]:
        """Get the current adaptive timeout if available."""
        if self.timeout_manager:
            return self.timeout_manager.get_timeout()
        return None


def categorize_error(error: Exception) -> ErrorCategory:
    """Categorize an error for appropriate retry handling."""
    import httpx

    if isinstance(error, (asyncio.TimeoutError, OSError)):
        return ErrorCategory.NETWORK

    if isinstance(error, httpx.HTTPStatusError):
        try:
            status_code = error.response.status_code
            if status_code == 429:
                return ErrorCategory.RATE_LIMIT
            elif 500 <= status_code < 600:
                return ErrorCategory.SERVER_ERROR
            elif 400 <= status_code < 500:
                return ErrorCategory.CLIENT_ERROR
        except (AttributeError, TypeError):
            # Handle cases where response mock doesn't have proper status_code
            return ErrorCategory.SERVER_ERROR

    if isinstance(error, httpx.ConnectError):
        return ErrorCategory.NETWORK

    if "validation" in str(error).lower():
        return ErrorCategory.VALIDATION

    return ErrorCategory.UNKNOWN


class ResilientOperator:
    """Provides resilient operation execution with retry and circuit breaking."""

    def __init__(self):
        self.circuit_breakers: Dict[str, CircuitBreaker] = {}
        self.default_retry_policy = RetryPolicy()

    def get_circuit_breaker(
        self,
        name: str,
        config: Optional[CircuitBreakerConfig] = None,
        timeout_config: Optional[TimeoutConfig] = None,
    ) -> CircuitBreaker:
        """Get or create a circuit breaker for a named operation."""
        if name not in self.circuit_breakers:
            if config is None:
                config = CircuitBreakerConfig()
            self.circuit_breakers[name] = CircuitBreaker(name, config, timeout_config)
        else:
            # Update existing circuit breaker with new timeout config if provided
            if timeout_config and not self.circuit_breakers[name].timeout_manager:
                self.circuit_breakers[name].timeout_manager = AdaptiveTimeoutManager(
                    timeout_config
                )
        return self.circuit_breakers[name]

    async def execute_with_retry(
        self,
        operation: Callable[[], Awaitable[T]],
        operation_name: str,
        retry_policy: Optional[RetryPolicy] = None,
        circuit_breaker_name: Optional[str] = None,
        **context,
    ) -> OperationResult:
        """Execute an operation with retry logic and optional circuit breaking."""
        if retry_policy is None:
            retry_policy = self.default_retry_policy

        metrics = get_metrics_collector()
        circuit_breaker = None

        if circuit_breaker_name:
            circuit_breaker = self.get_circuit_breaker(circuit_breaker_name)
            if not circuit_breaker.can_execute():
                return OperationResult(
                    success=False,
                    error=Exception(f"Circuit breaker {circuit_breaker_name} is open"),
                    error_category=ErrorCategory.NETWORK,
                )

        start_time = time.time()
        last_error = None

        for attempt in range(1, retry_policy.max_attempts + 1):
            try:
                logger.debug(
                    f"Attempting {operation_name}",
                    attempt=attempt,
                    max_attempts=retry_policy.max_attempts,
                    **context,
                )

                result = await operation()

                # Success - record metrics and circuit breaker state
                duration = time.time() - start_time
                metrics.record_dataplane_api_request(operation_name, "success")

                if circuit_breaker:
                    circuit_breaker.record_success()

                logger.info(
                    f"Operation {operation_name} succeeded",
                    attempt=attempt,
                    duration=duration,
                    **context,
                )

                return OperationResult(
                    success=True,
                    result=result,
                    attempt=attempt,
                    total_duration=duration,
                )

            except Exception as error:
                last_error = error
                error_category = categorize_error(error)
                duration = time.time() - start_time

                # Record failure metrics
                metrics.record_dataplane_api_request(operation_name, "error")
                metrics.record_error(f"{operation_name}_failed", "resilience")

                if circuit_breaker:
                    circuit_breaker.record_failure()

                logger.warning(
                    f"Operation {operation_name} failed",
                    attempt=attempt,
                    error=str(error),
                    error_category=error_category.value,
                    duration=duration,
                    **context,
                )

                # Check if error should be retried
                retryable_categories = retry_policy.retryable_categories or []
                if (
                    attempt >= retry_policy.max_attempts
                    or error_category not in retryable_categories
                ):
                    logger.error(
                        f"Operation {operation_name} exhausted retries",
                        final_attempt=attempt,
                        error_category=error_category.value,
                        total_duration=duration,
                        **context,
                    )

                    return OperationResult(
                        success=False,
                        error=error,
                        attempt=attempt,
                        total_duration=duration,
                        error_category=error_category,
                    )

                # Calculate delay with exponential backoff and jitter
                if attempt < retry_policy.max_attempts:
                    delay = min(
                        retry_policy.base_delay
                        * (retry_policy.exponential_base ** (attempt - 1)),
                        retry_policy.max_delay,
                    )

                    # Add random jitter to avoid thundering herd
                    import random

                    jitter = (
                        delay * retry_policy.jitter_factor * (random.random() - 0.5)  # nosec B311
                    )
                    final_delay = max(0, delay + jitter)

                    logger.debug(
                        f"Retrying {operation_name} after delay",
                        delay=final_delay,
                        next_attempt=attempt + 1,
                        **context,
                    )

                    await asyncio.sleep(final_delay)

        # Should not reach here, but handle gracefully
        return OperationResult(
            success=False,
            error=last_error or Exception("Unknown error"),
            attempt=retry_policy.max_attempts,
            total_duration=time.time() - start_time,
            error_category=ErrorCategory.UNKNOWN,
        )


# Global resilient operator instance
_resilient_operator: Optional[ResilientOperator] = None


def get_resilient_operator() -> ResilientOperator:
    """Get the global resilient operator instance."""
    global _resilient_operator
    if _resilient_operator is None:
        _resilient_operator = ResilientOperator()
    return _resilient_operator


# Convenience decorator for resilient operations
def resilient_operation(
    operation_name: str,
    retry_policy: Optional[RetryPolicy] = None,
    circuit_breaker_name: Optional[str] = None,
):
    """Decorator to make a function resilient with retry and circuit breaking."""

    def decorator(
        func: Callable[..., Awaitable[T]],
    ) -> Callable[..., Awaitable[OperationResult]]:
        async def wrapper(*args, **kwargs) -> OperationResult:
            operator = get_resilient_operator()

            async def operation():
                return await func(*args, **kwargs)

            return await operator.execute_with_retry(
                operation=operation,
                operation_name=operation_name,
                retry_policy=retry_policy,
                circuit_breaker_name=circuit_breaker_name,
            )

        return wrapper

    return decorator
