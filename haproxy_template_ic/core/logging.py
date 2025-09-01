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
from typing import Any, Callable, TypeVar, Awaitable, Dict, Union
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


def add_emoji_prefix(
    logger: Any, method_name: str, event_dict: Dict[str, Any]
) -> Dict[str, Any]:
    """Add emoji prefix to log messages based on level and content.

    This processor ensures all log messages have a consistent emoji prefix,
    making logs easier to scan visually. It checks if a message already has
    an emoji and adds an appropriate one if not.
    """
    # Check if we're in JSON mode (no emojis needed for JSON output)
    if event_dict.get("_json_mode", False):
        return event_dict

    # Get the log message
    msg = event_dict.get("event", "")
    if not msg:
        return event_dict

    # Check if message already starts with an emoji (Unicode range for emojis)
    # Common emoji ranges:
    # - Emoticons: U+1F600 to U+1F64F
    # - Symbols: U+1F300 to U+1F5FF, U+1F680 to U+1F6FF, U+1F900 to U+1F9FF
    # - Other: U+2600 to U+26FF, U+2700 to U+27BF
    if msg and len(msg) > 0:
        first_char = msg[0]
        if (
            "\U0001f300" <= first_char <= "\U0001f9ff"
            or "\U00002600" <= first_char <= "\U000027bf"
            or first_char in "✅❌⚠️ℹ️⏰🔧📋☸️⚙️✓"
        ):
            return event_dict

    # Get log level
    # For structlog messages, level is in 'log_level'
    # For stdlib messages, level is in '_record.levelname' (uppercase)
    level = event_dict.get("log_level")
    if not level:
        # Try to get from LogRecord for stdlib logging
        record = event_dict.get("_record")
        if record and hasattr(record, "levelname"):
            level = record.levelname.lower()
        else:
            level = "info"  # Default if we can't determine

    # Get logger name to identify external libraries
    # Handle both dict (structlog) and LogRecord (stdlib) formats
    record = event_dict.get("_record")
    if record and hasattr(record, "name"):
        # Standard library LogRecord
        logger_name = record.name
    elif isinstance(record, dict):
        # Structlog dict format
        logger_name = record.get("name", "")
    else:
        logger_name = ""

    # Determine appropriate emoji based on level and logger
    emoji = ""

    # Special handling for known libraries (override level-based emoji)
    if any(lib in logger_name for lib in ["httpx", "httpcore"]):
        emoji = "🌐"  # Network/HTTP requests
    elif "kopf" in logger_name:
        emoji = "☸️"  # Kubernetes operator
    elif "kr8s" in logger_name:
        emoji = "☸️"  # Kubernetes client
    elif "asyncio" in logger_name or "uvloop" in logger_name:
        emoji = "⚡"  # Async operations

    # If no library-specific emoji, use level-based
    if not emoji:
        # Default emojis by log level
        if level == "critical":
            emoji = "💥"
        elif level == "error":
            emoji = "❌"
        elif level == "warning":
            emoji = "⚠️"
        elif level == "info":
            # Try to be smart about info messages
            if any(word in msg.lower() for word in ["start", "begin", "init"]):
                emoji = "🚀"
            elif any(
                word in msg.lower()
                for word in ["success", "complete", "done", "finish"]
            ):
                emoji = "✅"
            elif any(word in msg.lower() for word in ["sync", "update", "refresh"]):
                emoji = "🔄"
            elif any(word in msg.lower() for word in ["config", "setting"]):
                emoji = "⚙️"
            elif any(word in msg.lower() for word in ["metric", "measure", "count"]):
                emoji = "📊"
            elif any(word in msg.lower() for word in ["render", "template"]):
                emoji = "📄"
            elif any(word in msg.lower() for word in ["valid"]):
                emoji = "✓"
            else:
                emoji = "ℹ️"
        elif level == "debug":
            # Smart debug emojis
            msg_lower = msg.lower()
            if any(word in msg_lower for word in ["creat", "add", "new"]):
                emoji = "➕"
            elif any(word in msg_lower for word in ["delet", "remov"]):
                emoji = "➖"
            elif any(word in msg_lower for word in ["skip", "unchang", "same"]):
                emoji = "⏭️"
            elif any(word in msg_lower for word in ["updat", "modif", "chang"]):
                emoji = "📝"
            elif any(word in msg_lower for word in ["fetch", "get", "retriev"]):
                emoji = "📥"
            elif any(word in msg_lower for word in ["send", "post", "deploy"]):
                emoji = "📤"
            else:
                emoji = "🔧"

    # Add emoji to the message
    if emoji:
        event_dict["event"] = f"{emoji} {msg}"

    return event_dict


def setup_structured_logging(verbose_level: int, use_json: bool = False) -> None:
    """Configure structured logging with optional JSON or colored console output."""
    level = {0: logging.WARNING, 1: logging.INFO, 2: logging.DEBUG}.get(
        verbose_level, logging.DEBUG
    )

    # Build shared processors for both structlog and stdlib
    # Note: Order matters! add_log_level must run before add_emoji_prefix
    shared_processors = [
        structlog.contextvars.merge_contextvars,
        structlog.processors.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
    ]

    # Choose renderer based on output format
    renderer: Union[structlog.processors.JSONRenderer, structlog.dev.ConsoleRenderer]
    if use_json:
        # For JSON mode, mark it so emoji processor knows not to add emojis
        shared_processors.append(
            lambda _, __, event_dict: {**event_dict, "_json_mode": True}
        )
        renderer = structlog.processors.JSONRenderer(ensure_ascii=False)
    else:
        # Add emoji processor AFTER add_log_level so it can see the level
        shared_processors.append(add_emoji_prefix)

        # Get default styles and customize debug to gray
        level_styles = structlog.dev.ConsoleRenderer.get_default_level_styles()
        level_styles["debug"] = "\x1b[90m"  # Bright black (gray)

        renderer = structlog.dev.ConsoleRenderer(
            colors=True,
            force_colors=True,  # Force colors even without TTY (Kubernetes)
            level_styles=level_styles,
        )

    # Configure structlog
    processors = shared_processors + [renderer]
    structlog.configure(
        processors=processors,  # type: ignore[arg-type]
        wrapper_class=structlog.make_filtering_bound_logger(level),
        context_class=dict,
        logger_factory=structlog.PrintLoggerFactory(),
        cache_logger_on_first_use=True,
    )

    # Configure standard library logging to use structlog formatting
    # This ensures ALL logs (including from kopf, kr8s, uvloop) use our formatting
    formatter = structlog.stdlib.ProcessorFormatter(
        processor=renderer,
        foreign_pre_chain=shared_processors,  # type: ignore[arg-type]
    )

    handler = logging.StreamHandler()
    handler.setFormatter(formatter)

    root_logger = logging.getLogger()
    root_logger.handlers.clear()  # Remove existing handlers
    root_logger.addHandler(handler)
    root_logger.setLevel(level)

    # Suppress noisy HTTP libraries
    for logger_name in [
        "httpx",
        "httpcore",
        "httpcore.connection",
        "httpcore.http11",
    ]:
        logging.getLogger(logger_name).setLevel(logging.WARNING)


__all__ = [
    "setup_structured_logging",
    "autolog",
    "observe",
    "add_emoji_prefix",
    "_extract_context_from_parameters",  # Private function for tests
    "_get_function_signature",  # Private function for tests
]
