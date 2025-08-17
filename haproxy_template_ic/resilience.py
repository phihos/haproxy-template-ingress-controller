"""
Resilience and error recovery patterns for HAProxy Template IC using tenacity and aiobreaker.

This module provides resilient operation patterns including:
- Exponential backoff retry mechanisms (via tenacity)
- Circuit breaker pattern for failing services (via aiobreaker)
- Error categorization and recovery policies
- Backward compatibility with the original custom implementation
"""

import asyncio
import time
from dataclasses import dataclass
from enum import Enum
from typing import Any, Awaitable, Callable, Dict, List, Optional, TypeVar

import httpx
from aiobreaker import CircuitBreaker as AIOCircuitBreaker
from tenacity import (
    AsyncRetrying,
    RetryError,
    stop_after_attempt,
    wait_exponential_jitter,
    retry_if_exception,
)

from haproxy_template_ic.metrics import get_metrics_collector
from haproxy_template_ic.structured_logging import get_structured_logger

T = TypeVar("T")

logger = get_structured_logger(__name__)


class CircuitState(Enum):
    """States of the circuit breaker."""

    CLOSED = "closed"  # Normal operation
    OPEN = "open"  # Failing, blocking requests
    HALF_OPEN = "half_open"  # Testing if service recovered


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
    absolute_max_timeout: float = 600.0  # Absolute maximum timeout as safety net
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


@dataclass
class OperationResult:
    """Result of a resilient operation attempt."""

    success: bool
    result: Any = None
    error: Optional[Exception] = None
    attempt: int = 1
    total_duration: float = 0.0
    error_category: ErrorCategory = ErrorCategory.UNKNOWN


def categorize_error(error: Exception) -> ErrorCategory:
    """Categorize an error for appropriate retry handling."""
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


class CircuitBreakerWrapper:
    """Wrapper around aiobreaker to provide backward compatibility with our original API."""

    def __init__(
        self,
        aio_breaker: AIOCircuitBreaker,
        timeout_config: Optional[TimeoutConfig] = None,
        circuit_config: Optional[CircuitBreakerConfig] = None,
    ):
        self.aio_breaker = aio_breaker
        self.timeout_config = timeout_config or TimeoutConfig()
        self.circuit_config = circuit_config or CircuitBreakerConfig()
        self.current_timeout = self.timeout_config.initial_timeout

        # Test compatibility fields
        self._state = CircuitState.CLOSED
        self.failure_count = 0
        self.success_count = 0
        self.last_failure_time = 0.0

    @property
    def state(self) -> CircuitState:
        """Get current circuit breaker state."""
        return self._state

    @state.setter
    def state(self, value: CircuitState) -> None:
        """Set circuit breaker state (for test compatibility)."""
        self._state = value

    def can_execute(self) -> bool:
        """Check if operation can be executed based on circuit state."""
        if self._state == CircuitState.OPEN:
            # Check if recovery timeout has passed
            if (
                hasattr(self, "last_failure_time")
                and time.time() - self.last_failure_time > 60
            ):  # default recovery
                self._state = CircuitState.HALF_OPEN
                self.success_count = 0
                return True
            return False
        return True

    def record_success(self) -> None:
        """Record a successful operation."""
        if self._state == CircuitState.HALF_OPEN:
            self.success_count += 1
            if self.success_count >= self.circuit_config.success_threshold:
                self._state = CircuitState.CLOSED
                self.failure_count = 0

        if self._state == CircuitState.CLOSED:
            self.failure_count = 0  # Reset failure count on success

        # Adjust timeout downward on success
        self.current_timeout = max(
            self.timeout_config.initial_timeout,
            self.current_timeout * self.timeout_config.success_timeout_reduction,
        )

    def record_failure(self) -> None:
        """Record a failed operation."""
        self.failure_count += 1
        self.last_failure_time = time.time()

        # Adjust timeout upward on failure
        self.current_timeout = min(
            self.timeout_config.max_timeout,
            self.timeout_config.absolute_max_timeout,
            self.current_timeout * self.timeout_config.timeout_multiplier,
        )

        # Update internal state based on failure threshold
        if self._state == CircuitState.CLOSED:
            if self.failure_count >= self.circuit_config.failure_threshold:
                self._state = CircuitState.OPEN
        elif self._state == CircuitState.HALF_OPEN:
            self._state = CircuitState.OPEN

    def get_adaptive_timeout(self) -> Optional[float]:
        """Get the current adaptive timeout if available."""
        return self.current_timeout

    async def call(self, operation: Callable[[], Awaitable[T]]) -> T:
        """Call operation through the circuit breaker."""
        return await self.aio_breaker.call(operation)

    @property
    def current_state(self) -> str:
        """Get current circuit breaker state."""
        return self.aio_breaker.current_state


class ResilientOperator:
    """Provides resilient operation execution with retry and circuit breaking using tenacity and aiobreaker."""

    def __init__(self):
        self.circuit_breakers: Dict[str, CircuitBreakerWrapper] = {}
        self.default_retry_policy = RetryPolicy()

    def get_circuit_breaker(
        self,
        name: str,
        config: Optional[CircuitBreakerConfig] = None,
        timeout_config: Optional[TimeoutConfig] = None,
    ) -> CircuitBreakerWrapper:
        """Get or create a circuit breaker for a named operation."""
        if name not in self.circuit_breakers:
            if config is None:
                config = CircuitBreakerConfig()

            # Create aiobreaker circuit breaker with wrapper for backward compatibility
            aio_breaker = AIOCircuitBreaker(
                fail_max=config.failure_threshold,
                timeout_duration=config.recovery_timeout,
                name=name,
            )
            self.circuit_breakers[name] = CircuitBreakerWrapper(
                aio_breaker, timeout_config, config
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
        """Execute an operation with retry logic and optional circuit breaking using tenacity and aiobreaker."""
        if retry_policy is None:
            retry_policy = self.default_retry_policy

        metrics = get_metrics_collector()
        circuit_breaker = None

        if circuit_breaker_name:
            circuit_breaker = self.get_circuit_breaker(circuit_breaker_name)

            # Check if circuit breaker is open
            if not circuit_breaker.can_execute():
                return OperationResult(
                    success=False,
                    error=Exception(f"Circuit breaker {circuit_breaker_name} is open"),
                    error_category=ErrorCategory.NETWORK,
                )

        start_time = time.time()
        last_error = None
        attempt_count = 0

        # Define retry condition based on error categories
        def should_retry(exception):
            error_category = categorize_error(exception)
            retryable_categories = retry_policy.retryable_categories or []
            return error_category in retryable_categories

        try:
            # Use tenacity for retry logic
            async for attempt in AsyncRetrying(
                stop=stop_after_attempt(retry_policy.max_attempts),
                wait=wait_exponential_jitter(
                    initial=retry_policy.base_delay,
                    max=retry_policy.max_delay,
                    exp_base=retry_policy.exponential_base,
                    jitter=retry_policy.jitter_factor,
                ),
                retry=retry_if_exception(should_retry),
                reraise=True,
            ):
                with attempt:
                    attempt_count += 1
                    logger.debug(
                        f"Attempting {operation_name}",
                        attempt=attempt_count,
                        max_attempts=retry_policy.max_attempts,
                        **context,
                    )

                    # Execute operation with circuit breaker if configured
                    if circuit_breaker:
                        result = await circuit_breaker.call(operation)
                    else:
                        result = await operation()

                    # Success - record metrics and circuit breaker state
                    duration = time.time() - start_time
                    metrics.record_dataplane_api_request(operation_name, "success")

                    if circuit_breaker:
                        circuit_breaker.record_success()

                    logger.info(
                        f"Operation {operation_name} succeeded",
                        attempt=attempt_count,
                        duration=duration,
                        **context,
                    )

                    return OperationResult(
                        success=True,
                        result=result,
                        attempt=attempt_count,
                        total_duration=duration,
                    )

        except RetryError as retry_error:
            # Extract the last exception from the retry error
            raw_error = retry_error.last_attempt.exception()
            # Ensure we have an Exception (not BaseException) for type safety
            last_error = (
                raw_error
                if isinstance(raw_error, Exception)
                else Exception(str(raw_error))
            )

        except Exception as error:
            # Direct exception (e.g., from circuit breaker)
            last_error = error

        # Failure path
        error_category = (
            categorize_error(last_error) if last_error else ErrorCategory.UNKNOWN
        )
        duration = time.time() - start_time

        # Record failure metrics and circuit breaker state
        metrics.record_dataplane_api_request(operation_name, "error")
        metrics.record_error(f"{operation_name}_failed", "resilience")

        if circuit_breaker:
            circuit_breaker.record_failure()

        logger.error(
            f"Operation {operation_name} exhausted retries",
            final_attempt=attempt_count,
            error=str(last_error) if last_error else "Unknown error",
            error_category=error_category.value,
            total_duration=duration,
            **context,
        )

        return OperationResult(
            success=False,
            error=last_error or Exception("Unknown error"),
            attempt=attempt_count,
            total_duration=duration,
            error_category=error_category,
        )


# Global resilient operator instance
_resilient_operator: Optional[ResilientOperator] = None


def get_resilient_operator() -> ResilientOperator:
    """Get the global resilient operator instance."""
    global _resilient_operator
    if _resilient_operator is None:
        _resilient_operator = ResilientOperator()
    return _resilient_operator


# Backward compatibility aliases for classes that were removed


# Create proper CircuitBreaker for backward compatibility
class CircuitBreaker:
    """Circuit breaker implementation for backward compatibility with tests."""

    def __init__(
        self,
        name: str,
        config: CircuitBreakerConfig,
        timeout_config: Optional[TimeoutConfig] = None,
    ):
        self.name = name
        self.config = config
        self.timeout_config = timeout_config or TimeoutConfig()

        # Create underlying aiobreaker instance for production use
        self.aio_breaker = AIOCircuitBreaker(
            fail_max=config.failure_threshold,
            timeout_duration=config.recovery_timeout,
            name=name,
        )

        # Manual state tracking for test compatibility
        self._state = CircuitState.CLOSED
        self.failure_count = 0
        self.success_count = 0
        self.last_failure_time = 0.0
        self.current_timeout = self.timeout_config.initial_timeout

    @property
    def state(self) -> CircuitState:
        """Get current circuit breaker state."""
        return self._state

    @state.setter
    def state(self, value: CircuitState) -> None:
        """Set circuit breaker state (for test compatibility)."""
        self._state = value

    def can_execute(self) -> bool:
        """Check if operation can be executed based on circuit state."""
        if self._state == CircuitState.OPEN:
            # Check if recovery timeout has passed
            if time.time() - self.last_failure_time > self.config.recovery_timeout:
                self._state = CircuitState.HALF_OPEN
                self.success_count = 0
                return True
            return False
        return True

    def record_success(self) -> None:
        """Record a successful operation."""
        if self._state == CircuitState.HALF_OPEN:
            self.success_count += 1
            if self.success_count >= self.config.success_threshold:
                self._state = CircuitState.CLOSED
                self.failure_count = 0

        if self._state == CircuitState.CLOSED:
            self.failure_count = 0  # Reset failure count on success

        # Adjust timeout downward on success
        self.current_timeout = max(
            self.timeout_config.initial_timeout,
            self.current_timeout * self.timeout_config.success_timeout_reduction,
        )

    def record_failure(self) -> None:
        """Record a failed operation."""
        self.failure_count += 1
        self.last_failure_time = time.time()

        # Adjust timeout upward on failure
        self.current_timeout = min(
            self.timeout_config.max_timeout,
            self.timeout_config.absolute_max_timeout,
            self.current_timeout * self.timeout_config.timeout_multiplier,
        )

        if self._state == CircuitState.CLOSED:
            if self.failure_count >= self.config.failure_threshold:
                self._state = CircuitState.OPEN
        elif self._state == CircuitState.HALF_OPEN:
            self._state = CircuitState.OPEN

    def get_adaptive_timeout(self) -> Optional[float]:
        """Get the current adaptive timeout if available."""
        return self.current_timeout

    async def call(self, operation: Callable[[], Awaitable[T]]) -> T:
        """Call operation through the circuit breaker."""
        # For production use, delegate to aiobreaker
        return await self.aio_breaker.call(operation)


class AdaptiveTimeoutManager:
    """Simplified adaptive timeout manager for backward compatibility."""

    def __init__(self, config: TimeoutConfig):
        self.config = config
        self.current_timeout = config.initial_timeout

    def get_timeout(self) -> float:
        return self.current_timeout

    def record_success(self) -> None:
        self.current_timeout = max(
            self.config.initial_timeout,
            self.current_timeout * self.config.success_timeout_reduction,
        )

    def record_failure(self) -> None:
        self.current_timeout = min(
            self.config.max_timeout,
            self.config.absolute_max_timeout,
            self.current_timeout * self.config.timeout_multiplier,
        )


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
