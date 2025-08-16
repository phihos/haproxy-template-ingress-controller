"""
Structured logging functionality for HAProxy Template IC using structlog.

This module provides context-aware structured logging with automatic
metadata injection, operation correlation, and JSON output formatting
using the industry-standard structlog library.
"""

import logging
import time
from contextlib import contextmanager
from dataclasses import dataclass
from typing import Any, Optional, Iterator, List
from uuid import uuid4

import structlog
import structlog.contextvars


@dataclass
class LogContext:
    """Container for structured logging context."""

    operation_id: Optional[str] = None
    component: Optional[str] = None
    resource_type: Optional[str] = None
    resource_namespace: Optional[str] = None
    resource_name: Optional[str] = None
    template_type: Optional[str] = None
    pod_name: Optional[str] = None


def custom_logfmt_renderer(_, __, event_dict):
    """Custom renderer that appends context fields in logfmt format to traditional log messages."""
    # Extract standard log fields
    timestamp = event_dict.pop("timestamp", "")
    level = event_dict.pop("level", "")
    logger = event_dict.pop("logger", "")
    event = event_dict.pop("event", "")

    # Format the base message traditionally
    base_message = f"{timestamp} - {logger} - {level} - {event}"

    # Format remaining context fields as logfmt and append
    if event_dict:
        logfmt_parts = []
        for key, value in event_dict.items():
            # Quote values that contain spaces or special characters
            if isinstance(value, str) and (
                " " in value or '"' in value or "=" in value
            ):
                # Escape quotes in the value
                escaped_value = value.replace('"', '\\"')
                logfmt_parts.append(f'{key}="{escaped_value}"')
            else:
                logfmt_parts.append(f"{key}={value}")

        logfmt_string = " ".join(logfmt_parts)
        return f"{base_message} {logfmt_string}"

    return base_message


def custom_timestamp_processor(_, __, event_dict):
    """Custom timestamp processor that formats timestamps to match original format."""
    # Use the same timestamp format as the original implementation
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime())
    # Add milliseconds
    timestamp += f",{int((time.time() % 1) * 1000):03d}"
    event_dict["timestamp"] = timestamp
    return event_dict


class StructuredLogger:
    """Wrapper for enhanced structured logging with context management using structlog."""

    def __init__(self, logger: structlog.BoundLogger) -> None:
        """Initialize with structlog bound logger."""
        self.logger = logger

    def debug(self, msg: str, **kwargs: Any) -> None:
        """Log debug message with context."""
        self.logger.debug(msg, **kwargs)

    def info(self, msg: str, **kwargs: Any) -> None:
        """Log info message with context."""
        self.logger.info(msg, **kwargs)

    def warning(self, msg: str, **kwargs: Any) -> None:
        """Log warning message with context."""
        self.logger.warning(msg, **kwargs)

    def error(self, msg: str, **kwargs: Any) -> None:
        """Log error message with context."""
        self.logger.error(msg, **kwargs)

    def critical(self, msg: str, **kwargs: Any) -> None:
        """Log critical message with context."""
        self.logger.critical(msg, **kwargs)


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

    structlog.contextvars.bind_contextvars(**context)
    try:
        yield
    finally:
        # Unbind all the context fields we set
        structlog.contextvars.unbind_contextvars(*context.keys())


def get_structured_logger(name: str) -> StructuredLogger:
    """Get a structured logger for the given name."""
    # Create a structlog logger bound to the name
    bound_logger = structlog.get_logger(name)
    return StructuredLogger(bound_logger)


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


# Convenience functions for common operations
def log_template_operation(
    logger: StructuredLogger, template_type: str, operation: str, **kwargs: Any
) -> None:
    """Log a template operation with structured context."""
    with resource_context_manager(template_type=template_type):
        logger.info(f"Template {operation}", template_operation=operation, **kwargs)


def log_dataplane_operation(
    logger: StructuredLogger, operation: str, pod_name: str, **kwargs: Any
) -> None:
    """Log a Dataplane API operation with structured context."""
    with resource_context_manager(pod_name=pod_name):
        logger.info(
            f"Dataplane API {operation}", dataplane_operation=operation, **kwargs
        )


def log_kubernetes_event(
    logger: StructuredLogger,
    event_type: str,
    resource_type: str,
    namespace: str,
    name: str,
    **kwargs: Any,
) -> None:
    """Log a Kubernetes event with structured context."""
    with resource_context_manager(
        resource_type=resource_type, resource_namespace=namespace, resource_name=name
    ):
        logger.info(f"Kubernetes {event_type}", kubernetes_event=event_type, **kwargs)
