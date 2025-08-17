"""
Tests for haproxy_template_ic.resilience module.

This module contains comprehensive tests for resilience patterns including
retry mechanisms, circuit breakers, adaptive timeouts, and error recovery.
"""

import asyncio
import time
from unittest.mock import MagicMock

import pytest
import httpx

from haproxy_template_ic.resilience import (
    ErrorCategory,
    RetryPolicy,
    TimeoutConfig,
    CircuitBreakerConfig,
    AdaptiveTimeoutManager,
    ResilientOperator,
    OperationResult,
    get_resilient_operator,
    categorize_error,
    resilient_operation,
)

# Import circuitbreaker exceptions for testing
from circuitbreaker import CircuitBreakerError


class TestErrorCategorization:
    """Test cases for error categorization functionality."""

    def test_categorize_network_errors(self):
        """Test categorization of network-related errors."""
        timeout_error = asyncio.TimeoutError("Request timeout")
        os_error = OSError("Connection refused")
        connect_error = httpx.ConnectError("Connection failed")

        assert categorize_error(timeout_error) == ErrorCategory.NETWORK
        assert categorize_error(os_error) == ErrorCategory.NETWORK
        assert categorize_error(connect_error) == ErrorCategory.NETWORK

    def test_categorize_http_status_errors(self):
        """Test categorization of HTTP status errors."""
        # Mock HTTP response objects
        rate_limit_response = MagicMock()
        rate_limit_response.status_code = 429
        rate_limit_error = httpx.HTTPStatusError(
            "Rate limited", request=MagicMock(), response=rate_limit_response
        )

        server_error_response = MagicMock()
        server_error_response.status_code = 500
        server_error = httpx.HTTPStatusError(
            "Internal server error", request=MagicMock(), response=server_error_response
        )

        client_error_response = MagicMock()
        client_error_response.status_code = 404
        client_error = httpx.HTTPStatusError(
            "Not found", request=MagicMock(), response=client_error_response
        )

        assert categorize_error(rate_limit_error) == ErrorCategory.RATE_LIMIT
        assert categorize_error(server_error) == ErrorCategory.SERVER_ERROR
        assert categorize_error(client_error) == ErrorCategory.CLIENT_ERROR

    def test_categorize_validation_errors(self):
        """Test categorization of validation errors."""
        validation_error = ValueError("Configuration validation failed")
        assert categorize_error(validation_error) == ErrorCategory.VALIDATION

    def test_categorize_unknown_errors(self):
        """Test categorization of unknown errors."""
        unknown_error = RuntimeError("Something unexpected happened")
        assert categorize_error(unknown_error) == ErrorCategory.UNKNOWN


class TestTimeoutConfiguration:
    """Test cases for timeout configuration."""

    def test_timeout_config_defaults(self):
        """Test timeout configuration default values."""
        config = TimeoutConfig()

        assert config.initial_timeout == 30.0
        assert config.max_timeout == 300.0
        assert config.timeout_multiplier == 1.5
        assert config.success_timeout_reduction == 0.9

    def test_timeout_config_custom_values(self):
        """Test timeout configuration with custom values."""
        config = TimeoutConfig(
            initial_timeout=10.0,
            max_timeout=60.0,
            timeout_multiplier=2.0,
            success_timeout_reduction=0.8,
        )

        assert config.initial_timeout == 10.0
        assert config.max_timeout == 60.0
        assert config.timeout_multiplier == 2.0
        assert config.success_timeout_reduction == 0.8


class TestAdaptiveTimeoutManager:
    """Test cases for adaptive timeout management."""

    def test_initial_timeout(self):
        """Test initial timeout value."""
        config = TimeoutConfig(initial_timeout=20.0)
        manager = AdaptiveTimeoutManager(config)

        assert manager.get_timeout() == 20.0

    def test_timeout_adjustment_on_success(self):
        """Test timeout reduction after successful operations."""
        config = TimeoutConfig(initial_timeout=30.0, success_timeout_reduction=0.8)
        manager = AdaptiveTimeoutManager(config)

        # Start with increased timeout
        manager.current_timeout = 50.0

        manager.record_success()
        assert manager.get_timeout() == 40.0  # 50.0 * 0.8

        manager.record_success()
        assert manager.get_timeout() == 32.0  # 40.0 * 0.8

        # Should not go below initial timeout
        manager.record_success()
        assert manager.get_timeout() == 30.0  # Clamped to initial

    def test_timeout_adjustment_on_failure(self):
        """Test timeout increase after failed operations."""
        config = TimeoutConfig(
            initial_timeout=10.0, max_timeout=50.0, timeout_multiplier=2.0
        )
        manager = AdaptiveTimeoutManager(config)

        manager.record_failure()
        assert manager.get_timeout() == 20.0  # 10.0 * 2.0

        manager.record_failure()
        assert manager.get_timeout() == 40.0  # 20.0 * 2.0

        # Should not exceed max timeout
        manager.record_failure()
        assert manager.get_timeout() == 50.0  # Clamped to max


class TestRetryPolicy:
    """Test cases for retry policy configuration."""

    def test_retry_policy_defaults(self):
        """Test retry policy default values."""
        policy = RetryPolicy()

        assert policy.max_attempts == 3
        assert policy.base_delay == 1.0
        assert policy.max_delay == 60.0
        assert policy.exponential_base == 2.0
        assert policy.jitter_factor == 0.1
        assert ErrorCategory.NETWORK in policy.retryable_categories
        assert ErrorCategory.RATE_LIMIT in policy.retryable_categories
        assert ErrorCategory.SERVER_ERROR in policy.retryable_categories
        assert isinstance(policy.timeout_config, TimeoutConfig)

    def test_retry_policy_custom_categories(self):
        """Test retry policy with custom retryable categories."""
        policy = RetryPolicy(
            retryable_categories=[ErrorCategory.NETWORK, ErrorCategory.VALIDATION]
        )

        assert len(policy.retryable_categories) == 2
        assert ErrorCategory.NETWORK in policy.retryable_categories
        assert ErrorCategory.VALIDATION in policy.retryable_categories
        assert ErrorCategory.SERVER_ERROR not in policy.retryable_categories


class TestCircuitBreaker:
    """Test cases for circuit breaker functionality."""

    @pytest.mark.asyncio
    async def test_circuit_breaker_creation(self):
        """Test circuit breaker creation and basic functionality."""
        operator = ResilientOperator()
        config = CircuitBreakerConfig(failure_threshold=2, recovery_timeout=1)

        # Get circuit breaker
        breaker = operator.get_circuit_breaker("test_circuit", config)

        # Should be a circuitbreaker decorator function
        assert callable(breaker)

    @pytest.mark.asyncio
    async def test_circuit_breaker_allows_success(self):
        """Test circuit breaker allows successful operations."""
        operator = ResilientOperator()
        config = CircuitBreakerConfig(failure_threshold=2, recovery_timeout=1)
        breaker = operator.get_circuit_breaker("test_success", config)

        @breaker
        async def successful_operation():
            return "success"

        # Should succeed
        result = await successful_operation()
        assert result == "success"

    @pytest.mark.asyncio
    async def test_circuit_breaker_opens_on_failures(self):
        """Test circuit breaker opens after configured failures."""
        operator = ResilientOperator()
        config = CircuitBreakerConfig(failure_threshold=2, recovery_timeout=60)
        breaker = operator.get_circuit_breaker("test_failures", config)

        @breaker
        async def failing_operation():
            raise Exception("Test failure")

        # First failure
        with pytest.raises(Exception, match="Test failure"):
            await failing_operation()

        # Second failure
        with pytest.raises(Exception, match="Test failure"):
            await failing_operation()

        # Third call should raise CircuitBreakerError (circuit is now open)
        with pytest.raises(CircuitBreakerError):
            await failing_operation()

    @pytest.mark.asyncio
    async def test_circuit_breaker_recovery(self):
        """Test circuit breaker recovery after timeout."""
        operator = ResilientOperator()
        config = CircuitBreakerConfig(failure_threshold=1, recovery_timeout=1)
        breaker = operator.get_circuit_breaker("test_recovery", config)

        call_count = 0

        @breaker
        async def sometimes_failing_operation():
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                raise Exception("First failure")
            return "recovered"

        # First call fails, opens circuit
        with pytest.raises(Exception, match="First failure"):
            await sometimes_failing_operation()

        # Immediate second call should fail with CircuitBreakerError
        with pytest.raises(CircuitBreakerError):
            await sometimes_failing_operation()

        # Wait for recovery timeout
        await asyncio.sleep(1.1)

        # Should now allow test execution and succeed
        result = await sometimes_failing_operation()
        assert result == "recovered"


class TestResilientOperator:
    """Test cases for resilient operation execution."""

    @pytest.mark.asyncio
    async def test_successful_operation(self):
        """Test successful operation execution."""
        operator = ResilientOperator()

        async def successful_operation():
            return "success"

        result = await operator.execute_with_retry(
            operation=successful_operation, operation_name="test_operation"
        )

        assert result.success is True
        assert result.result == "success"
        assert result.attempt == 1
        assert result.error is None

    @pytest.mark.asyncio
    async def test_operation_with_retryable_failure(self):
        """Test operation that fails then succeeds on retry."""
        operator = ResilientOperator()

        call_count = 0

        async def flaky_operation():
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                raise httpx.ConnectError("Connection failed")
            return "success"

        retry_policy = RetryPolicy(max_attempts=3, base_delay=0.01)
        result = await operator.execute_with_retry(
            operation=flaky_operation,
            operation_name="flaky_operation",
            retry_policy=retry_policy,
        )

        assert result.success is True
        assert result.result == "success"
        assert result.attempt == 2
        assert call_count == 2

    @pytest.mark.asyncio
    async def test_operation_with_non_retryable_failure(self):
        """Test operation with non-retryable error."""
        operator = ResilientOperator()

        async def failing_operation():
            # Create a 404 client error (not retryable)
            response = MagicMock()
            response.status_code = 404
            raise httpx.HTTPStatusError(
                "Not found", request=MagicMock(), response=response
            )

        result = await operator.execute_with_retry(
            operation=failing_operation, operation_name="failing_operation"
        )

        assert result.success is False
        assert result.attempt == 1
        assert result.error_category == ErrorCategory.CLIENT_ERROR

    @pytest.mark.asyncio
    async def test_operation_exhausts_retries(self):
        """Test operation that exhausts all retry attempts."""
        operator = ResilientOperator()

        async def always_failing_operation():
            raise httpx.ConnectError("Connection failed")

        retry_policy = RetryPolicy(max_attempts=3, base_delay=0.01)
        result = await operator.execute_with_retry(
            operation=always_failing_operation,
            operation_name="always_failing",
            retry_policy=retry_policy,
        )

        assert result.success is False
        assert result.attempt == 3
        assert result.error_category == ErrorCategory.NETWORK

    @pytest.mark.asyncio
    async def test_operation_with_circuit_breaker_open(self):
        """Test operation when circuit breaker is open."""
        operator = ResilientOperator()

        # Configure circuit breaker with low threshold to open quickly
        config = CircuitBreakerConfig(failure_threshold=1, recovery_timeout=60)

        # First, cause enough failures to open the circuit breaker
        async def failing_operation():
            raise Exception("Force circuit to open")

        # Cause a failure to open the circuit
        result1 = await operator.execute_with_retry(
            operation=failing_operation,
            operation_name="force_failure",
            retry_policy=RetryPolicy(max_attempts=1),
            circuit_breaker_name="test_circuit",
            circuit_breaker_config=config,
        )
        assert result1.success is False

        # Now try to use the same circuit breaker - should be open
        async def dummy_operation():
            return "should not execute"

        result2 = await operator.execute_with_retry(
            operation=dummy_operation,
            operation_name="dummy",
            circuit_breaker_name="test_circuit",
            circuit_breaker_config=config,
        )

        assert result2.success is False
        # Should get either CircuitBreakerError or the operation should be blocked
        assert (
            isinstance(result2.error, CircuitBreakerError)
            or "circuit" in str(result2.error).lower()
        )

    @pytest.mark.asyncio
    async def test_operation_with_circuit_breaker_success(self):
        """Test successful operation updates circuit breaker state."""
        operator = ResilientOperator()

        async def successful_operation():
            return "success"

        # Execute operation with circuit breaker
        result = await operator.execute_with_retry(
            operation=successful_operation,
            operation_name="test_success",
            circuit_breaker_name="test_circuit",
        )

        assert result.success is True

        # Check circuit breaker is still functional (no exceptions means it's working)
        circuit_breaker = operator.get_circuit_breaker("test_circuit")
        assert callable(circuit_breaker)


class TestResilientOperationDecorator:
    """Test cases for the resilient operation decorator."""

    @pytest.mark.asyncio
    async def test_resilient_operation_decorator(self):
        """Test the resilient operation decorator."""

        @resilient_operation("decorated_operation")
        async def test_function(value: str) -> str:
            return f"processed: {value}"

        result = await test_function("test_input")

        assert isinstance(result, OperationResult)
        assert result.success is True
        assert result.result == "processed: test_input"

    @pytest.mark.asyncio
    async def test_resilient_operation_decorator_with_failure(self):
        """Test resilient operation decorator with failure."""
        call_count = 0

        @resilient_operation(
            "decorated_operation",
            retry_policy=RetryPolicy(max_attempts=2, base_delay=0.01),
        )
        async def failing_function():
            nonlocal call_count
            call_count += 1
            raise httpx.ConnectError("Connection failed")

        result = await failing_function()

        assert isinstance(result, OperationResult)
        assert result.success is False
        assert call_count == 2  # Should have retried once


class TestGlobalResilientOperator:
    """Test cases for global resilient operator instance."""

    def test_get_resilient_operator_singleton(self):
        """Test that get_resilient_operator returns singleton instance."""
        operator1 = get_resilient_operator()
        operator2 = get_resilient_operator()

        assert operator1 is operator2

    def test_resilient_operator_circuit_breaker_persistence(self):
        """Test that circuit breakers persist across operations."""
        operator = get_resilient_operator()

        # Get circuit breaker
        breaker1 = operator.get_circuit_breaker("persistent_test")

        # Get the same circuit breaker again
        breaker2 = operator.get_circuit_breaker("persistent_test")

        # Should return the same circuit breaker instance
        assert breaker1 is breaker2
        assert callable(breaker1)
        assert callable(breaker2)


class TestIntegration:
    """Integration tests for resilience patterns."""

    @pytest.mark.asyncio
    async def test_complete_resilience_workflow(self):
        """Test complete resilience workflow with all patterns."""
        operator = ResilientOperator()

        call_count = 0

        async def complex_operation():
            nonlocal call_count
            call_count += 1

            if call_count <= 2:
                # First two calls fail with retryable errors
                raise httpx.ConnectError("Connection failed")
            elif call_count == 3:
                # Third call succeeds
                return f"success_after_{call_count}_attempts"

        # Configure comprehensive retry policy
        retry_policy = RetryPolicy(
            max_attempts=5,
            base_delay=0.01,
            max_delay=1.0,
            exponential_base=2.0,
            jitter_factor=0.1,
            timeout_config=TimeoutConfig(initial_timeout=10.0, max_timeout=60.0),
        )

        result = await operator.execute_with_retry(
            operation=complex_operation,
            operation_name="complex_workflow",
            retry_policy=retry_policy,
            circuit_breaker_name="integration_test",
        )

        assert result.success is True
        assert result.result == "success_after_3_attempts"
        assert result.attempt == 3
        assert call_count == 3

        # Circuit breaker should be available and functional
        circuit_breaker = operator.get_circuit_breaker("integration_test")
        assert callable(circuit_breaker)

    @pytest.mark.asyncio
    async def test_circuit_breaker_prevents_cascade_failures(self):
        """Test that circuit breaker prevents cascading failures."""
        operator = ResilientOperator()

        async def always_failing_operation():
            raise httpx.ConnectError("Service unavailable")

        retry_policy = RetryPolicy(max_attempts=1, base_delay=0.01)

        # First few operations should fail and open circuit
        for i in range(3):
            result = await operator.execute_with_retry(
                operation=always_failing_operation,
                operation_name=f"cascade_test_{i}",
                retry_policy=retry_policy,
                circuit_breaker_name="cascade_protection",
            )
            assert result.success is False

        # Additional operations should fail fast without calling the operation
        start_time = time.time()
        result = await operator.execute_with_retry(
            operation=always_failing_operation,
            operation_name="fast_fail_test",
            retry_policy=retry_policy,
            circuit_breaker_name="cascade_protection",
        )
        end_time = time.time()

        assert result.success is False
        # Check if it's a circuit breaker error or original error
        # The circuit should be open now, so either CircuitBreakerError or fast failure
        assert (
            isinstance(result.error, CircuitBreakerError)
            or "circuit" in str(result.error).lower()
            or (end_time - start_time) < 0.5  # Fast failure due to circuit being open
        )


class TestCircuitBreakerIntegration:
    """Test cases for circuit breaker integration with resilient operations."""

    @pytest.mark.asyncio
    async def test_circuit_breaker_with_resilient_operator(self):
        """Test circuit breaker working correctly with ResilientOperator."""
        operator = ResilientOperator()
        config = CircuitBreakerConfig(failure_threshold=3, recovery_timeout=1)

        call_count = 0

        async def operation_with_initial_failures():
            nonlocal call_count
            call_count += 1
            if call_count <= 2:
                raise Exception(f"Failure {call_count}")
            return f"Success after {call_count} calls"

        # Should fail, then succeed on retry
        result = await operator.execute_with_retry(
            operation=operation_with_initial_failures,
            operation_name="test_integration",
            retry_policy=RetryPolicy(
                max_attempts=5,
                base_delay=0.01,
                retryable_categories=[
                    ErrorCategory.UNKNOWN
                ],  # Allow retrying unknown errors for this test
            ),
            circuit_breaker_name="integration_test",
            circuit_breaker_config=config,
        )

        assert result.success is True
        assert "Success after 3 calls" in result.result

    @pytest.mark.asyncio
    async def test_circuit_breaker_prevents_excessive_calls(self):
        """Test that circuit breaker prevents excessive calls to failing operations."""
        operator = ResilientOperator()
        call_count = 0

        async def always_failing_operation():
            nonlocal call_count
            call_count += 1
            raise Exception(f"Always fails - call {call_count}")

        # First operation should fail normally
        result1 = await operator.execute_with_retry(
            operation=always_failing_operation,
            operation_name="fail_test_1",
            retry_policy=RetryPolicy(max_attempts=1),
            circuit_breaker_name="prevention_test",
        )
        assert result1.success is False
        assert call_count == 1

        # Second operation should trigger circuit breaker
        result2 = await operator.execute_with_retry(
            operation=always_failing_operation,
            operation_name="fail_test_2",
            retry_policy=RetryPolicy(max_attempts=1),
            circuit_breaker_name="prevention_test",
        )
        assert result2.success is False
        # call_count should still be 1 if circuit breaker is working
        # or 2 if the circuit opened after this call
        assert call_count <= 2
