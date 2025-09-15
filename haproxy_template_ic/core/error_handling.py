"""
Centralized error handling utilities for HAProxy Template IC.

This module provides standardized error handling patterns, logging,
and recovery mechanisms to reduce code duplication across the codebase.
"""

import asyncio
import functools
import logging
from typing import Any, Callable, TypeVar, Optional, Union, cast

import structlog

# Type variables for decorators
F = TypeVar("F", bound=Callable[..., Any])


def handle_exceptions(
    logger: Optional[Union[logging.Logger, structlog.BoundLogger]] = None,
    default_return: Any = None,
    reraise: bool = False,
    context: Optional[str] = None,
) -> Callable[[F], F]:
    """
    Decorator for standardized exception handling with logging.

    Args:
        logger: Logger instance to use. If None, uses module logger
        default_return: Value to return on exception if not re-raising
        reraise: Whether to re-raise the exception after logging
        context: Additional context to include in error messages

    Returns:
        Decorated function with centralized error handling
    """

    def decorator(func: F) -> F:
        if asyncio.iscoroutinefunction(func):

            @functools.wraps(func)
            async def async_wrapper(*args, **kwargs):
                try:
                    return await func(*args, **kwargs)
                except Exception as e:
                    # Use provided logger or fall back to module logger
                    error_logger = logger or structlog.get_logger(func.__module__)

                    # Build error context
                    error_context = {
                        "function": func.__name__,
                        "exception_type": type(e).__name__,
                        "exception_message": str(e),
                    }
                    if context:
                        error_context["context"] = context

                    # Log the error with context
                    # Check if this is a structlog logger vs standard logger
                    try:
                        # Try structlog style first
                        error_logger.error("Exception in function", **error_context)
                    except TypeError:
                        # Fallback for standard logger
                        error_logger.error(
                            f"Exception in {func.__name__}: {e}", extra=error_context
                        )

                    if reraise:
                        raise

                    return default_return

            return cast(F, async_wrapper)
        else:

            @functools.wraps(func)
            def wrapper(*args, **kwargs):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    # Use provided logger or fall back to module logger
                    error_logger = logger or structlog.get_logger(func.__module__)

                    # Build error context
                    error_context = {
                        "function": func.__name__,
                        "error_type": type(e).__name__,
                        "error_message": str(e),
                    }
                    if context:
                        error_context["context"] = context

                    # Log the error with context
                    # Check if this is a structlog logger vs standard logger
                    try:
                        # Try structlog style first
                        error_logger.error("Exception in function", **error_context)
                    except TypeError:
                        # Fallback for standard logger
                        error_logger.error(
                            f"Exception in {func.__name__}: {e}", extra=error_context
                        )

                    if reraise:
                        raise

                    return default_return

            return cast(F, wrapper)

    return decorator


def log_and_ignore_errors(
    logger: Optional[Union[logging.Logger, structlog.BoundLogger]] = None,
    message: str = "Ignoring non-critical error",
) -> Callable[[F], F]:
    """
    Decorator to log and ignore non-critical errors.

    Args:
        logger: Logger instance to use
        message: Custom message for the log entry

    Returns:
        Decorated function that ignores exceptions
    """
    return handle_exceptions(logger=logger, default_return=None, context=message)


def safe_operation(
    default: Any = None,
    logger: Optional[Union[logging.Logger, structlog.BoundLogger]] = None,
) -> Callable[[F], F]:
    """
    Decorator for operations that should never crash the application.

    Args:
        default: Default value to return on exception
        logger: Logger to use for error logging

    Returns:
        Decorated function that returns default on exception
    """
    return handle_exceptions(logger=logger, default_return=default)
