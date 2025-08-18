"""
Resilience and error recovery patterns for HAProxy Template IC using tenacity and circuitbreaker.

This module provides resilient operation patterns including:
- Exponential backoff retry mechanisms (via tenacity)
- Circuit breaker pattern for failing services (via circuitbreaker)
- Error categorization and recovery policies
- Clean, maintainable implementation using well-tested libraries
"""

import asyncio
import time
from dataclasses import dataclass
from enum import Enum
from typing import Any, Awaitable, Callable, Dict, List, Optional, TypeVar

import httpx
from circuitbreaker import circuit
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
            return ErrorCategory.UNKNOWN

    if isinstance(error, httpx.ConnectError):
        return ErrorCategory.NETWORK

    if "validation" in str(error).lower():
        return ErrorCategory.VALIDATION

    return ErrorCategory.UNKNOWN


class AdaptiveTimeoutManager:
    """Manages adaptive timeout adjustment based on operation success/failure."""

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


class ResilientOperator:
    """Provides resilient operation execution with retry and circuit breaking using tenacity and circuitbreaker."""

    def __init__(self):
        self.circuit_breakers: Dict[str, Any] = {}
        self.timeout_managers: Dict[str, AdaptiveTimeoutManager] = {}
        self.default_retry_policy = RetryPolicy()

    def get_circuit_breaker(
        self,
        name: str,
        config: Optional[CircuitBreakerConfig] = None,
    ) -> Any:
        """Get or create a circuit breaker for a named operation."""
        if name not in self.circuit_breakers:
            if config is None:
                config = CircuitBreakerConfig()

            # Create circuit breaker using the circuitbreaker library
            self.circuit_breakers[name] = circuit(
                failure_threshold=config.failure_threshold,
                recovery_timeout=config.recovery_timeout,
                name=name,
            )

        return self.circuit_breakers[name]

    def get_timeout_manager(
        self,
        name: str,
        config: Optional[TimeoutConfig] = None,
    ) -> AdaptiveTimeoutManager:
        """Get or create a timeout manager for a named operation."""
        if name not in self.timeout_managers:
            if config is None:
                config = TimeoutConfig()
            self.timeout_managers[name] = AdaptiveTimeoutManager(config)
        return self.timeout_managers[name]

    async def execute_with_retry(
        self,
        operation: Callable[[], Awaitable[T]],
        operation_name: str,
        retry_policy: Optional[RetryPolicy] = None,
        circuit_breaker_name: Optional[str] = None,
        circuit_breaker_config: Optional[CircuitBreakerConfig] = None,
        **context,
    ) -> OperationResult:
        """Execute an operation with retry logic and optional circuit breaking using tenacity and circuitbreaker."""
        if retry_policy is None:
            retry_policy = self.default_retry_policy

        metrics = get_metrics_collector()
        start_time = time.time()
        last_error = None
        attempt_count = 0

        # Set up timeout management
        timeout_manager = self.get_timeout_manager(
            f"{operation_name}_timeout", retry_policy.timeout_config
        )

        # Apply circuit breaker if configured
        protected_operation = operation
        if circuit_breaker_name:
            circuit_breaker = self.get_circuit_breaker(
                circuit_breaker_name, circuit_breaker_config
            )
            protected_operation = circuit_breaker(operation)

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
                        timeout=timeout_manager.get_timeout(),
                        **context,
                    )

                    # Execute operation
                    result = await protected_operation()

                    # Success - record metrics and adjust timeout
                    duration = time.time() - start_time
                    timeout_manager.record_success()
                    metrics.record_dataplane_api_request(operation_name, "success")

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
            if hasattr(retry_error, "last_attempt") and retry_error.last_attempt:
                try:
                    raw_error = retry_error.last_attempt.exception()
                    if isinstance(raw_error, Exception):
                        last_error = raw_error
                    else:
                        last_error = Exception(f"Retry failed: {retry_error}")
                except Exception:
                    last_error = Exception(f"Retry failed: {retry_error}")
            else:
                last_error = Exception(f"Retry operation failed: {retry_error}")

        except Exception as error:
            # Direct exception (e.g., from circuit breaker)
            last_error = error

        # Failure path
        error_category = (
            categorize_error(last_error) if last_error else ErrorCategory.UNKNOWN
        )
        duration = time.time() - start_time

        # Record failure metrics and adjust timeout
        timeout_manager.record_failure()
        metrics.record_dataplane_api_request(operation_name, "error")
        metrics.record_error(f"{operation_name}_failed", "resilience")

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
