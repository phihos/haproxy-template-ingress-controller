"""
Structured logging functionality for HAProxy Template IC using structlog.

This module provides context-aware structured logging with automatic
metadata injection, operation correlation, and JSON output formatting
using the industry-standard structlog library.
"""

import logging
import time
from contextlib import contextmanager
from typing import Any, Optional, Iterator, List
from uuid import uuid4

import structlog
import structlog.contextvars


# LogContext dataclass removed - using contextvars directly for context management


# Pre-compiled format string for better performance
_BASE_MESSAGE_FORMAT = "{timestamp} - {logger} - {level} - {event}"


def custom_logfmt_renderer(_, __, event_dict):
    """Custom renderer that appends context fields in logfmt format to traditional log messages."""
    # Extract standard log fields
    timestamp = event_dict.pop("timestamp", "")
    level = event_dict.pop("level", "")
    logger = event_dict.pop("logger", "")
    event = event_dict.pop("event", "")

    # Format the base message using pre-compiled format string
    base_message = _BASE_MESSAGE_FORMAT.format(
        timestamp=timestamp, logger=logger, level=level, event=event
    )

    # Format remaining context fields as logfmt and append
    if event_dict:
        logfmt_parts = []
        for key, value in event_dict.items():
            # Quote values that contain spaces, tabs, newlines, or special characters
            if isinstance(value, str) and any(
                char in value for char in (" ", "\t", "\n", "\r", '"', "=", "\\")
            ):
                # Escape special characters in the value
                escaped_value = (
                    value.replace("\\", "\\\\")
                    .replace('"', '\\"')
                    .replace("\n", "\\n")
                    .replace("\r", "\\r")
                    .replace("\t", "\\t")
                )
                logfmt_parts.append(f'{key}="{escaped_value}"')
            else:
                logfmt_parts.append(f"{key}={value}")

        logfmt_string = " ".join(logfmt_parts)
        return f"{base_message} {logfmt_string}"

    return base_message


def custom_timestamp_processor(_, __, event_dict):
    """Custom timestamp processor that formats timestamps to match original format."""
    # Capture time once to ensure thread safety
    current_time = time.time()
    # Format timestamp with milliseconds from the same time capture
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime(current_time))
    # Add milliseconds from the same time capture
    timestamp += f",{int((current_time % 1) * 1000):03d}"
    event_dict["timestamp"] = timestamp
    return event_dict


@contextmanager
def operation_context(operation_id: Optional[str] = None) -> Iterator[str]:
    """Context manager for operation correlation."""
    if operation_id is None:
        operation_id = str(uuid4())[:8]  # Short UUID for readability

    structlog.contextvars.bind_contextvars(operation_id=operation_id)
    try:
        yield operation_id
    finally:
        structlog.contextvars.unbind_contextvars("operation_id")


@contextmanager
def component_context_manager(component: str) -> Iterator[None]:
    """Context manager for component identification."""
    structlog.contextvars.bind_contextvars(component=component)
    try:
        yield
    finally:
        structlog.contextvars.unbind_contextvars("component")


@contextmanager
def resource_context_manager(
    resource_type: Optional[str] = None,
    resource_namespace: Optional[str] = None,
    resource_name: Optional[str] = None,
    **extra_fields: Any,
) -> Iterator[None]:
    """Context manager for resource identification."""
    context = {}
    if resource_type:
        context["resource_type"] = resource_type
    if resource_namespace:
        context["resource_namespace"] = resource_namespace
    if resource_name:
        context["resource_name"] = resource_name

    # Add any additional context fields
    context.update(extra_fields)

    # Track which keys we actually bind to ensure proper cleanup
    bound_keys = list(context.keys())

    if bound_keys:
        structlog.contextvars.bind_contextvars(**context)
    try:
        yield
    finally:
        # Unbind only the context fields we actually set
        if bound_keys:
            structlog.contextvars.unbind_contextvars(*bound_keys)


def get_structured_logger(name: str):
    """Get a structured logger for the given name."""
    return structlog.get_logger(name)


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
        # Add custom timestamp and logfmt renderer for traditional format
        processors.extend([custom_timestamp_processor, custom_logfmt_renderer])

    # Configure structlog
    structlog.configure(
        processors=processors,
        wrapper_class=structlog.make_filtering_bound_logger(level),
        context_class=dict,
        logger_factory=structlog.PrintLoggerFactory(),
        cache_logger_on_first_use=True,
    )
