"""
Structured logging functionality for HAProxy Template IC using structlog.

This module provides context-aware structured logging with automatic
metadata injection, operation correlation, and JSON output formatting
using the industry-standard structlog library.
"""

import logging
import functools
import inspect
from functools import lru_cache
from typing import Any, List, Callable, TypeVar, Awaitable, Dict
from uuid import uuid4

import structlog
import structlog.contextvars


# Type variables for decorators
F = TypeVar("F", bound=Callable[..., Any])
AsyncF = TypeVar("AsyncF", bound=Callable[..., Awaitable[Any]])


@lru_cache(maxsize=128)
def _get_function_signature(func: Callable) -> inspect.Signature:
    """Get cached function signature for performance."""
    return inspect.signature(func)


def _extract_context_from_parameters(
    func: Callable, args: tuple, kwargs: dict, decorator_kwargs: dict
) -> Dict[str, Any]:
    """Extract logging context from function parameters using smart detection."""
    context = decorator_kwargs.copy()

    # Get function signature with error handling
    try:
        sig = _get_function_signature(func)
        bound_args = sig.bind_partial(*args, **kwargs)
        bound_args.apply_defaults()
    except (TypeError, ValueError):
        # If signature binding fails, return minimal context with operation_id
        context.setdefault("operation_id", str(uuid4())[:8])
        return {k: v for k, v in context.items() if v is not None}

    # Smart parameter detection for kopf event handlers
    if "event" in bound_args.arguments:
        event = bound_args.arguments["event"]
        if isinstance(event, dict) and "object" in event:
            metadata = event.get("object", {}).get("metadata", {})
            context.setdefault("resource_namespace", metadata.get("namespace"))

            # Infer resource_type from event structure
            if "kind" in event.get("object", {}):
                context.setdefault("resource_type", event["object"]["kind"])

    # Use function parameter values as context
    if "name" in bound_args.arguments:
        context.setdefault("resource_name", bound_args.arguments["name"])

    if "namespace" in bound_args.arguments:
        context.setdefault("resource_namespace", bound_args.arguments["namespace"])

    if "type" in bound_args.arguments and "event" in bound_args.arguments:
        # This looks like a kopf event handler
        context.setdefault("kubernetes_event", bound_args.arguments["type"])

    # Note: Removed fragile function name inference as per code review
    # Resource types should come from event objects or explicit decorator parameters

    # Auto-generate operation_id if not provided
    if "operation_id" not in context:
        context["operation_id"] = str(uuid4())[:8]

    # Remove None values to avoid cluttering logs
    return {k: v for k, v in context.items() if v is not None}


def autolog(**decorator_kwargs: Any) -> Callable[[F], F]:
    """Decorator for automatic logging context injection.

    Automatically extracts context from function parameters and provides
    structured logging without boilerplate. Detects kopf event handlers,
    resource operations, and more.

    Args:
        **decorator_kwargs: Override context values (component, etc.)
    """

    def decorator(func: F) -> F:
        if inspect.iscoroutinefunction(func):

            @functools.wraps(func)
            async def async_wrapper(*args: Any, **kwargs: Any) -> Any:
                context = _extract_context_from_parameters(
                    func, args, kwargs, decorator_kwargs
                )
                bound_keys = list(context.keys())

                # Context ready for structured logging

                if bound_keys:
                    structlog.contextvars.bind_contextvars(**context)

                try:
                    # Call the original function - it now has clean business logic
                    return await func(*args, **kwargs)
                finally:
                    if bound_keys:
                        structlog.contextvars.unbind_contextvars(*bound_keys)

            return async_wrapper  # type: ignore[return-value]
        else:

            @functools.wraps(func)
            def sync_wrapper(*args: Any, **kwargs: Any) -> Any:
                context = _extract_context_from_parameters(
                    func, args, kwargs, decorator_kwargs
                )
                bound_keys = list(context.keys())

                # Context ready for structured logging

                if bound_keys:
                    structlog.contextvars.bind_contextvars(**context)

                try:
                    # Call the original function - it now has clean business logic
                    return func(*args, **kwargs)
                finally:
                    if bound_keys:
                        structlog.contextvars.unbind_contextvars(*bound_keys)

            return sync_wrapper  # type: ignore[return-value]

    return decorator


def observe(**decorator_kwargs: Any) -> Callable[[AsyncF], AsyncF]:
    """Decorator combining autolog + tracing for complete observability.

    Provides both structured logging context and distributed tracing
    in a single decorator. Perfect for functions that need full observability.

    Args:
        **decorator_kwargs: Context overrides and tracing attributes
    """

    def decorator(func: AsyncF) -> AsyncF:
        # Apply autolog first
        autolog_func = autolog(**decorator_kwargs)(func)

        # Then apply tracing with error handling
        try:
            from haproxy_template_ic.tracing import trace_async_function

            # Extract tracing-specific args
            span_name = decorator_kwargs.get("span_name")
            trace_attrs = decorator_kwargs.get("trace_attributes", {})

            traced_func = trace_async_function(
                span_name=span_name, attributes=trace_attrs
            )(autolog_func)

            return traced_func  # type: ignore[return-value]
        except ImportError:
            # If tracing module is unavailable, return just the autolog version
            return autolog_func  # type: ignore[return-value]

    return decorator


def setup_structured_logging(verbose_level: int, use_json: bool = False) -> None:
    """Configure structured logging with optional JSON output using structlog."""
    log_levels = {0: logging.WARNING, 1: logging.INFO, 2: logging.DEBUG}
    level = log_levels.get(verbose_level, logging.DEBUG)

    # Configure the standard library logging first
    logging.basicConfig(
        level=level,
        format="%(message)s",  # structlog will handle all formatting
        force=True,
    )

    # Configure structlog processors
    processors: List[Any] = [
        structlog.contextvars.merge_contextvars,  # Merge context variables
        structlog.processors.add_log_level,  # Add log level
        structlog.processors.StackInfoRenderer(),  # Add stack info if requested
    ]

    if use_json:
        # Add timestamp and JSON renderer for JSON output
        processors.extend(
            [
                structlog.processors.TimeStamper(fmt="iso"),
                structlog.processors.JSONRenderer(),
            ]
        )
    else:
        # Use structlog's built-in processors for traditional format
        processors.extend(
            [
                structlog.processors.TimeStamper(fmt="iso"),
                structlog.processors.KeyValueRenderer(
                    key_order=["timestamp", "level", "logger"]
                ),
            ]
        )

    # Configure structlog
    structlog.configure(
        processors=processors,
        wrapper_class=structlog.make_filtering_bound_logger(level),
        context_class=dict,
        logger_factory=structlog.PrintLoggerFactory(),
        cache_logger_on_first_use=True,
    )
