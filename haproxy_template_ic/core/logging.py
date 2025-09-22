"""
Structured logging functionality for HAProxy Template IC using structlog.

This module provides context-aware structured logging with automatic
metadata injection, operation correlation, and JSON output formatting
using the industry-standard structlog library.
"""

import functools
import inspect
import logging
from functools import lru_cache
from typing import Any, Callable, TypeVar, Awaitable, cast, TypedDict, NotRequired
from dataclasses import dataclass, field, asdict
from uuid import uuid4

import structlog
import structlog.contextvars
from structlog.types import EventDict, WrappedLogger, Processor


# Unicode constants for emoji detection
EMOJI_UNICODE_RANGES = [
    (
        "\U0001f300",
        "\U0001f9ff",
    ),  # Misc Symbols and Pictographs, Emoticons, Transport, etc.
    ("\U00002600", "\U000027bf"),  # Miscellaneous Symbols, Dingbats
]
SPECIAL_EMOJI_CHARS = "✅❌⚠️ℹ️⏰🔧📋☸️⚙️✓"


class LogEventDict(TypedDict, total=False):
    """Enhanced type definition for log event dictionaries with common fields."""

    event: str
    log_level: NotRequired[str]
    _json_mode: NotRequired[bool]
    _record: NotRequired[Any]  # LogRecord or dict


# Emoji mappings for different contexts
LIBRARY_EMOJIS = {
    "httpx": "🌐",
    "httpcore": "🌐",
    "kopf": "☸️",
    "kr8s": "☸️",
    "asyncio": "⚡",
    "uvloop": "⚡",
}

LEVEL_EMOJIS = {
    "critical": "💥",
    "error": "❌",
    "warning": "⚠️",
    "debug": "🔧",
}

INFO_MESSAGE_EMOJIS = {
    ("start", "begin", "init"): "🚀",
    ("success", "complete", "done", "finish"): "✅",
    ("sync", "update", "refresh"): "🔄",
    ("config", "setting"): "⚙️",
    ("metric", "measure", "count"): "📊",
    ("render", "template"): "📄",
    ("valid",): "✓",
}

DEBUG_MESSAGE_EMOJIS = {
    ("creat", "add", "new"): "➕",
    ("delet", "remov"): "➖",
    ("skip", "unchang", "same"): "⏭️",
    ("updat", "modif", "chang"): "📝",
    ("fetch", "get", "retriev"): "📥",
    ("send", "post", "deploy"): "📤",
}


# Type variables for decorators
F = TypeVar("F", bound=Callable[..., Any])
AsyncF = TypeVar("AsyncF", bound=Callable[..., Awaitable[Any]])


@lru_cache(maxsize=128)
def _get_function_signature(func: Callable) -> inspect.Signature:
    """Get cached function signature for performance."""
    return inspect.signature(func)


def _extract_context_from_parameters(
    func: Callable, args: tuple, kwargs: dict, decorator_kwargs: dict
) -> dict[str, Any]:
    """Extract logging context from function parameters using smart detection."""
    context = decorator_kwargs.copy()

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

    # Auto-detect dataplane API classes and extract endpoint information
    if args and hasattr(args[0], "endpoint"):
        endpoint = args[0].endpoint
        if hasattr(endpoint, "url") and hasattr(endpoint, "pod_name"):
            context.setdefault("dataplane_url", endpoint.url)
            if endpoint.pod_name:
                context.setdefault("pod_name", endpoint.pod_name)

    if "name" in bound_args.arguments:
        context.setdefault("resource_name", bound_args.arguments["name"])

    if "namespace" in bound_args.arguments:
        context.setdefault("resource_namespace", bound_args.arguments["namespace"])

    if "type" in bound_args.arguments and "event" in bound_args.arguments:
        # This looks like a kopf event handler
        context.setdefault("kubernetes_event", bound_args.arguments["type"])

    # Resource types should come from event objects or explicit decorator parameters

    # Auto-generate operation_id if not provided
    if "operation_id" not in context:
        context["operation_id"] = str(uuid4())[:8]

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

            return cast(F, async_wrapper)
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

            return cast(F, sync_wrapper)

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

            return cast(AsyncF, traced_func)
        except ImportError:
            # If tracing module is unavailable, return just the autolog version
            return cast(AsyncF, autolog_func)

    return decorator


def _get_library_emoji(logger_name: str) -> str:
    """Get emoji for library-specific loggers."""
    for lib, emoji in LIBRARY_EMOJIS.items():
        if lib in logger_name:
            return emoji
    return ""


def _get_message_based_emoji(message: str, level: str) -> str:
    """Get emoji based on message content and level."""
    msg_lower = message.lower()

    if level == "info":
        for keywords, emoji in INFO_MESSAGE_EMOJIS.items():
            if any(word in msg_lower for word in keywords):
                return emoji
        return "ℹ️"  # Default info emoji

    elif level == "debug":
        for keywords, emoji in DEBUG_MESSAGE_EMOJIS.items():
            if any(word in msg_lower for word in keywords):
                return emoji
        return "🔧"  # Default debug emoji

    return ""


def _get_emoji_for_log(level: str, logger_name: str, message: str) -> str:
    """Determine appropriate emoji for log entry."""
    # Check for library-specific emojis first (overrides level-based)
    library_emoji = _get_library_emoji(logger_name)
    if library_emoji:
        return library_emoji

    # Check level-specific emojis
    level_emoji = LEVEL_EMOJIS.get(level)
    if level_emoji:
        return level_emoji

    # For info and debug levels, analyze message content
    return _get_message_based_emoji(message, level)


def add_emoji_prefix(
    logger: WrappedLogger, method_name: str, event_dict: EventDict
) -> EventDict:
    """Add emoji prefix to log messages based on level and content.

    This processor ensures all log messages have a consistent emoji prefix,
    making logs easier to scan visually. It checks if a message already has
    an emoji and adds an appropriate one if not.

    Args:
        logger: The wrapped logger instance
        method_name: The name of the logging method called
        event_dict: The log event dictionary

    Returns:
        Updated event dictionary with emoji prefix
    """
    # Check if we're in JSON mode (no emojis needed for JSON output)
    if event_dict.get("_json_mode", False):
        return event_dict

    # Get the log message
    msg = event_dict.get("event", "")
    if not msg:
        return event_dict

    if msg and len(msg) > 0:
        first_char = msg[0]
        # Check if message already has an emoji prefix
        if (
            any(start <= first_char <= end for start, end in EMOJI_UNICODE_RANGES)
            or first_char in SPECIAL_EMOJI_CHARS
        ):
            return event_dict

    level = event_dict.get("log_level")
    if not level:
        # Try to get from LogRecord for stdlib logging
        record = event_dict.get("_record")
        if record and hasattr(record, "levelname"):
            level = record.levelname.lower()
        else:
            level = "info"  # Default if we can't determine

    record = event_dict.get("_record")
    if record and hasattr(record, "name"):
        # Standard library LogRecord
        logger_name = record.name
    elif isinstance(record, dict):
        # Structlog dict format
        logger_name = record.get("name", "")
    else:
        logger_name = ""

    # Get appropriate emoji using helper function
    emoji = _get_emoji_for_log(level, logger_name, msg)

    # Add emoji to the message
    if emoji:
        event_dict["event"] = f"{emoji} {msg}"

    return event_dict


def extract_stdlib_extra_fields(
    logger: WrappedLogger, method_name: str, event_dict: EventDict
) -> EventDict:
    """Extract extra fields from stdlib logging LogRecord objects.

    When stdlib logging uses logger.info("msg", extra={"key": "value"}),
    this processor extracts those extra fields and adds them to the
    structured log event dict so they appear in the output.

    For kopf loggers, filters out verbose fields like complete OperatorSettings
    and resource UIDs while preserving essential information.

    Args:
        logger: The wrapped logger instance
        method_name: The name of the logging method called
        event_dict: The log event dictionary

    Returns:
        Updated event dictionary with extracted extra fields
    """
    # Check if we have a stdlib LogRecord
    record = event_dict.get("_record")
    if not record or not hasattr(record, "__dict__"):
        return event_dict

    # Standard LogRecord attributes that we should NOT include as extra fields
    standard_attrs = {
        "name",
        "msg",
        "args",
        "levelname",
        "levelno",
        "pathname",
        "filename",
        "module",
        "lineno",
        "funcName",
        "created",
        "msecs",
        "relativeCreated",
        "thread",
        "threadName",
        "processName",
        "process",
        "getMessage",
        "exc_info",
        "exc_text",
        "stack_info",
        "message",
    }

    # Check if this is a kopf logger
    logger_name = getattr(record, "name", "")
    is_kopf_logger = "kopf" in logger_name

    # Extract any attributes that were added via 'extra' parameter
    extra_fields = {}
    for key, value in record.__dict__.items():
        if key not in standard_attrs and not key.startswith("_"):
            # Filter verbose kopf-specific fields
            if is_kopf_logger:
                if key == "settings":
                    # Skip the verbose OperatorSettings object entirely
                    continue
                elif key == "taskName":
                    # Only skip taskName for pure kopf internal loggers
                    # Our application loggers should keep taskName for correlation
                    if logger_name.startswith("kopf."):
                        continue
                    # Otherwise preserve taskName
                elif key == "k8s_ref" and isinstance(value, dict):
                    # For k8s_ref, extract only essential fields (skip uid)
                    filtered_ref = {}
                    for ref_key, ref_value in value.items():
                        if ref_key in ("name", "namespace", "kind", "apiVersion"):
                            filtered_ref[ref_key] = ref_value
                        # Skip 'uid' and other verbose fields
                    if filtered_ref:
                        extra_fields[key] = filtered_ref
                    continue
                elif key == "k8s_skip":
                    # Skip k8s_skip as it's not very useful for operators
                    continue

            # For non-kopf loggers or non-filtered kopf fields, include as-is
            extra_fields[key] = value

    # Add extra fields to event_dict
    if extra_fields:
        event_dict.update(extra_fields)

    # Remove redundant operation_id when taskName is present (kopf context)
    if "taskName" in event_dict and "operation_id" in event_dict:
        # taskName provides better correlation than generic operation_id
        del event_dict["operation_id"]

    return event_dict


# Configuration Classes


@dataclass(frozen=True)
class LoggingConfig:
    """Configuration for structured logging setup.

    This dataclass provides a type-safe way to configure logging behavior
    and can be easily serialized/deserialized from configuration files.
    """

    # Basic settings
    verbose_level: int = 1  # 0=WARNING, 1=INFO, 2=DEBUG
    use_json: bool = False
    use_utc: bool = True

    # Performance settings
    fast_json_serialization: bool = True
    enable_early_filtering: bool = True
    cache_loggers: bool = True

    # Feature settings
    enable_emojis: bool = True
    emoji_disabled_for_json: bool = True
    enable_logger_names: bool = True

    # Kopf filtering settings
    filter_kopf_settings: bool = True
    filter_kopf_task_names: bool = True
    filter_kopf_uids: bool = True

    # Suppressed loggers
    suppressed_loggers: list[str] = field(
        default_factory=lambda: [
            "httpx",
            "httpcore",
            "httpcore.connection",
            "httpcore.http11",
        ]
    )

    @classmethod
    def from_dict(cls, config_dict: dict[str, Any]) -> "LoggingConfig":
        """Create LoggingConfig from dictionary (e.g., from YAML/JSON config)."""
        return cls(**config_dict)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        return asdict(self)


# Processor Factory Functions


def create_emoji_processor(
    disabled_for_json: bool = True,
) -> Callable[[WrappedLogger, str, EventDict], EventDict]:
    """Create an emoji prefix processor with configurable options.

    Args:
        disabled_for_json: Whether to disable emojis for JSON output mode

    Returns:
        Configured emoji processor function
    """

    def emoji_processor(
        logger: WrappedLogger, method_name: str, event_dict: EventDict
    ) -> EventDict:
        if disabled_for_json and event_dict.get("_json_mode", False):
            return event_dict
        return add_emoji_prefix(logger, method_name, event_dict)

    return emoji_processor


def _safe_filter_by_level(
    logger: WrappedLogger, method_name: str, event_dict: EventDict
) -> EventDict:
    """Async-safe level filtering that doesn't access logger.disabled attribute.

    This replaces structlog.stdlib.filter_by_level which can fail in thread pools
    when the logger object is None or doesn't have expected attributes.
    """
    # For async logging in thread pools, we can't safely access logger attributes
    # So we just pass through all events and let the stdlib logger handle filtering
    return event_dict


def create_kopf_filter_processor(
    filter_settings: bool = True,
    filter_task_names: bool = True,
    filter_uids: bool = True,
) -> Callable[[WrappedLogger, str, EventDict], EventDict]:
    """Create a kopf field filtering processor with configurable options.

    Args:
        filter_settings: Whether to filter verbose OperatorSettings objects
        filter_task_names: Whether to filter taskName for pure kopf loggers
        filter_uids: Whether to filter resource UIDs from k8s_ref

    Returns:
        Configured kopf filtering processor function
    """

    def kopf_filter_processor(
        logger: WrappedLogger, method_name: str, event_dict: EventDict
    ) -> EventDict:
        return extract_stdlib_extra_fields(logger, method_name, event_dict)

    return kopf_filter_processor


def create_base_processor_chain(level: int, use_json: bool = False) -> list[Processor]:
    """Create the base processor chain with performance optimizations.

    Args:
        level: Logging level for filtering
        use_json: Whether to use JSON output format

    Returns:
        List of configured processors
    """
    processors: list[Processor] = [
        _safe_filter_by_level,  # Async-safe early filtering
        structlog.contextvars.merge_contextvars,
        create_kopf_filter_processor(),  # Configurable kopf filtering
        structlog.stdlib.add_logger_name,  # Better stdlib integration
        structlog.processors.add_log_level,
        structlog.processors.TimeStamper(fmt="iso", utc=True),  # UTC for consistency
    ]

    if not use_json:
        processors.append(create_emoji_processor())

    return processors


def create_json_renderer(
    fast_serialization: bool = True,
) -> structlog.processors.JSONRenderer:
    """Create a JSON renderer with optional fast serialization.

    Args:
        fast_serialization: Whether to use orjson for faster serialization

    Returns:
        Configured JSON renderer
    """
    if fast_serialization:
        try:
            import orjson  # type: ignore[import-untyped]

            def orjson_serializer(obj, **kwargs):
                # orjson doesn't support the same keyword arguments as json.dumps
                # but it's much faster, so we ignore the kwargs
                return orjson.dumps(obj).decode("utf-8")

            return structlog.processors.JSONRenderer(serializer=orjson_serializer)
        except ImportError:
            pass  # Fall through to standard JSON

    return structlog.processors.JSONRenderer(ensure_ascii=False)


def setup_structured_logging(verbose_level: int, use_json: bool = False) -> None:
    """Configure structured logging with optional JSON or colored console output.

    This function sets up a high-performance structured logging system using
    the factory pattern for better maintainability and configurability.

    Args:
        verbose_level: Logging verbosity (0=WARNING, 1=INFO, 2=DEBUG)
        use_json: Whether to use JSON output format instead of colored console
    """
    level = {0: logging.WARNING, 1: logging.INFO, 2: logging.DEBUG}.get(
        verbose_level, logging.DEBUG
    )

    # Use factory functions for modular processor creation
    shared_processors = create_base_processor_chain(level, use_json)

    # Choose renderer based on output format
    renderer: structlog.processors.JSONRenderer | structlog.dev.ConsoleRenderer
    if use_json:
        # Mark for JSON mode so processors can adapt behavior
        shared_processors.append(
            lambda _, __, event_dict: {**event_dict, "_json_mode": True}
        )
        renderer = create_json_renderer(fast_serialization=True)
    else:
        # Console renderer with custom styling
        level_styles = structlog.dev.ConsoleRenderer.get_default_level_styles()
        level_styles["debug"] = "\x1b[90m"  # Bright black (gray)

        renderer = structlog.dev.ConsoleRenderer(
            colors=True,
            force_colors=True,  # Force colors even without TTY (Kubernetes)
            level_styles=level_styles,
        )

    # Configure structlog with optimized settings
    processors = shared_processors + [renderer]
    structlog.configure(
        processors=processors,  # type: ignore[arg-type]
        wrapper_class=structlog.stdlib.BoundLogger,  # Better stdlib integration
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),  # Use stdlib loggers
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


def setup_structured_logging_from_config(config: LoggingConfig) -> None:
    """Configure structured logging using a LoggingConfig object.

    This is the recommended way to configure logging as it provides
    type safety and better configuration management.

    Args:
        config: LoggingConfig instance with all logging settings
    """
    level = {0: logging.WARNING, 1: logging.INFO, 2: logging.DEBUG}.get(
        config.verbose_level, logging.DEBUG
    )

    # Build processors using configuration
    processors: list[Processor] = []

    if config.enable_early_filtering:
        processors.append(_safe_filter_by_level)

    processors.extend(
        [
            structlog.contextvars.merge_contextvars,
            create_kopf_filter_processor(
                filter_settings=config.filter_kopf_settings,
                filter_task_names=config.filter_kopf_task_names,
                filter_uids=config.filter_kopf_uids,
            ),
        ]
    )

    if config.enable_logger_names:
        processors.append(structlog.stdlib.add_logger_name)

    processors.extend(
        [
            structlog.processors.add_log_level,
            structlog.processors.TimeStamper(fmt="iso", utc=config.use_utc),
        ]
    )

    # Add emoji processor for console output
    if config.enable_emojis and not config.use_json:
        processors.append(create_emoji_processor(config.emoji_disabled_for_json))

    # Choose renderer
    renderer: structlog.processors.JSONRenderer | structlog.dev.ConsoleRenderer
    if config.use_json:
        processors.append(lambda _, __, event_dict: {**event_dict, "_json_mode": True})
        renderer = create_json_renderer(config.fast_json_serialization)
    else:
        level_styles = structlog.dev.ConsoleRenderer.get_default_level_styles()
        level_styles["debug"] = "\x1b[90m"  # Bright black (gray)
        renderer = structlog.dev.ConsoleRenderer(
            colors=True, force_colors=True, level_styles=level_styles
        )

    # Configure structlog
    processors.append(renderer)
    structlog.configure(
        processors=processors,  # type: ignore[arg-type]
        wrapper_class=structlog.stdlib.BoundLogger,
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=config.cache_loggers,
    )

    # Configure stdlib logging
    formatter = structlog.stdlib.ProcessorFormatter(
        processor=renderer,
        foreign_pre_chain=processors[:-1],  # type: ignore[arg-type]
    )

    handler = logging.StreamHandler()
    handler.setFormatter(formatter)

    root_logger = logging.getLogger()
    root_logger.handlers.clear()
    root_logger.addHandler(handler)
    root_logger.setLevel(level)

    # Suppress configured loggers
    for logger_name in config.suppressed_loggers:
        logging.getLogger(logger_name).setLevel(logging.WARNING)


async def log_resource_operation(
    operation: str,
    resource_type: str,
    resource_name: str,
    details: str = "",
    reload_triggered: bool = False,
) -> None:
    """Log resource operations with structured context using async logging.

    This helper function provides unified logging for all dataplane resource
    operations (create, update, delete) with consistent formatting and context.
    Uses async logging for better performance in async contexts.

    Args:
        operation: Operation type (e.g., "Created", "Updated", "Deleted")
        resource_type: Type of resource (e.g., "file", "map", "certificate", "ACL")
        resource_name: Name/identifier of the resource
        details: Additional details (e.g., file size, change description)
        reload_triggered: Whether this operation triggered an HAProxy reload
    """
    logger = structlog.get_logger(__name__)

    # Build the log message with consistent format
    msg_parts = [operation, f"{resource_type}:", resource_name]
    if details:
        msg_parts.append(f"({details})")

    message = " ".join(msg_parts)

    # Use async structured logging with extra context
    await logger.ainfo(
        message,
        operation=operation.lower(),
        resource_type=resource_type,
        resource_name=resource_name,
        reload_triggered=reload_triggered,
        **({"details": details} if details else {}),
    )


# Testing Utilities


def create_test_logger_config() -> dict[str, Any]:
    """Create a logging configuration optimized for testing.

    This configuration disables caching, uses simpler processors,
    and provides better test isolation.

    Returns:
        Dictionary of structlog configuration parameters for testing
    """
    return {
        "processors": [
            structlog.contextvars.merge_contextvars,
            structlog.processors.add_log_level,
            structlog.processors.TimeStamper(fmt="iso", utc=True),
            structlog.testing.LogCapture(),
        ],
        "wrapper_class": structlog.stdlib.BoundLogger,
        "context_class": dict,
        "logger_factory": structlog.stdlib.LoggerFactory(),
        "cache_logger_on_first_use": False,  # Disable for test isolation
    }


def setup_test_logging() -> None:
    """Configure structlog for testing with log capture capabilities.

    This should be called in test setup to ensure consistent
    logging behavior during tests.
    """
    structlog.configure(**create_test_logger_config())


def capture_logs() -> structlog.testing.LogCapture:
    """Create a log capture instance for testing log output.

    Returns:
        LogCapture instance that can be used to assert log messages

    Example:
        with capture_logs() as cap_logs:
            logger = structlog.get_logger()
            logger.info("test message", key="value")
            assert len(cap_logs.entries) == 1
            assert cap_logs.entries[0]["event"] == "test message"
    """
    return structlog.testing.LogCapture()


def assert_log_contains(
    log_entries: list[dict[str, Any]],
    message: str,
    level: str = "info",
    **expected_fields: Any,
) -> bool:
    """Assert that log entries contain a message with expected fields.

    Args:
        log_entries: List of log entry dictionaries
        message: Expected log message
        level: Expected log level
        **expected_fields: Expected key-value pairs in log entry

    Returns:
        True if assertion passes

    Raises:
        AssertionError: If expected log entry is not found
    """
    for entry in log_entries:
        if (
            entry.get("event") == message
            and entry.get("log_level") == level
            and all(entry.get(k) == v for k, v in expected_fields.items())
        ):
            return True

    # Build helpful error message
    available_messages = [entry.get("event", "NO_EVENT") for entry in log_entries]
    raise AssertionError(
        f"Log entry not found. Expected message='{message}' level='{level}' "
        f"fields={expected_fields}. Available messages: {available_messages}"
    )


__all__ = [
    # Main setup functions
    "setup_structured_logging",
    "setup_structured_logging_from_config",
    # Configuration
    "LoggingConfig",
    # Decorators
    "autolog",
    "observe",
    # Core processors
    "add_emoji_prefix",
    "extract_stdlib_extra_fields",
    # Utility functions
    "log_resource_operation",
    "_extract_context_from_parameters",
    "_get_function_signature",
    # Processor factories
    "create_emoji_processor",
    "create_kopf_filter_processor",
    "create_base_processor_chain",
    "create_json_renderer",
    # Testing utilities
    "create_test_logger_config",
    "setup_test_logging",
    "capture_logs",
    "assert_log_contains",
]
