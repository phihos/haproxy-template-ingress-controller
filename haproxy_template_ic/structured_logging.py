"""
Structured logging functionality for HAProxy Template IC.

This module provides context-aware structured logging with automatic
metadata injection, operation correlation, and JSON output formatting.
"""

import logging
import json
import time
from contextlib import contextmanager
from contextvars import ContextVar
from dataclasses import dataclass
from typing import Dict, Any, Optional, Iterator
from uuid import uuid4

# Context variables for structured logging
operation_id_context: ContextVar[Optional[str]] = ContextVar(
    "operation_id", default=None
)
component_context: ContextVar[Optional[str]] = ContextVar("component", default=None)
resource_context: ContextVar[Optional[Dict[str, Any]]] = ContextVar(
    "resource", default=None
)


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


class StructuredFormatter(logging.Formatter):
    """JSON formatter for structured logging with context injection."""

    def format(self, record: logging.LogRecord) -> str:
        """Format log record as structured JSON with context."""
        # Build base log entry
        log_entry = {
            "timestamp": time.strftime(
                "%Y-%m-%dT%H:%M:%S.%fZ", time.gmtime(record.created)
            ),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }

        # Add operation correlation
        operation_id = operation_id_context.get()
        if operation_id:
            log_entry["operation_id"] = operation_id

        # Add component context
        component = component_context.get()
        if component:
            log_entry["component"] = component

        # Add resource context
        resource = resource_context.get()
        if resource:
            log_entry.update(resource)

        # Add exception information if present
        if record.exc_info:
            log_entry["exception"] = self.formatException(record.exc_info)

        # Add any extra fields from the log record
        for key, value in record.__dict__.items():
            if key not in {
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
                "exc_info",
                "exc_text",
                "stack_info",
            }:
                log_entry[key] = value

        return json.dumps(log_entry, default=str)


class StructuredLogger:
    """Wrapper for enhanced structured logging with context management."""

    def __init__(self, logger: logging.Logger) -> None:
        """Initialize with base logger."""
        self.logger = logger

    def _log_with_context(self, level: int, msg: str, **kwargs: Any) -> None:
        """Log message with current context and additional fields."""
        # Create a copy of kwargs to avoid modifying the original
        extra = kwargs.copy()

        # Add context information
        operation_id = operation_id_context.get()
        if operation_id:
            extra["operation_id"] = operation_id

        component = component_context.get()
        if component:
            extra["component"] = component

        resource = resource_context.get()
        if resource:
            extra.update(resource)

        self.logger.log(level, msg, extra=extra)

    def debug(self, msg: str, **kwargs: Any) -> None:
        """Log debug message with context."""
        self._log_with_context(logging.DEBUG, msg, **kwargs)

    def info(self, msg: str, **kwargs: Any) -> None:
        """Log info message with context."""
        self._log_with_context(logging.INFO, msg, **kwargs)

    def warning(self, msg: str, **kwargs: Any) -> None:
        """Log warning message with context."""
        self._log_with_context(logging.WARNING, msg, **kwargs)

    def error(self, msg: str, **kwargs: Any) -> None:
        """Log error message with context."""
        self._log_with_context(logging.ERROR, msg, **kwargs)

    def critical(self, msg: str, **kwargs: Any) -> None:
        """Log critical message with context."""
        self._log_with_context(logging.CRITICAL, msg, **kwargs)


@contextmanager
def operation_context(operation_id: Optional[str] = None) -> Iterator[str]:
    """Context manager for operation correlation."""
    if operation_id is None:
        operation_id = str(uuid4())[:8]  # Short UUID for readability

    token = operation_id_context.set(operation_id)
    try:
        yield operation_id
    finally:
        operation_id_context.reset(token)


@contextmanager
def component_context_manager(component: str) -> Iterator[None]:
    """Context manager for component identification."""
    token = component_context.set(component)
    try:
        yield
    finally:
        component_context.reset(token)


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

    token = resource_context.set(context)
    try:
        yield
    finally:
        resource_context.reset(token)


def get_structured_logger(name: str) -> StructuredLogger:
    """Get a structured logger for the given name."""
    base_logger = logging.getLogger(name)
    return StructuredLogger(base_logger)


def setup_structured_logging(verbose_level: int, use_json: bool = False) -> None:
    """Configure structured logging with optional JSON output."""
    log_levels = {0: logging.WARNING, 1: logging.INFO, 2: logging.DEBUG}
    level = log_levels.get(verbose_level, logging.DEBUG)

    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(level)

    # Remove existing handlers
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)

    # Create console handler
    handler = logging.StreamHandler()
    handler.setLevel(level)

    if use_json:
        # Use structured JSON formatter
        formatter: logging.Formatter = StructuredFormatter()
    else:
        # Use traditional formatter with some structure
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )

    handler.setFormatter(formatter)
    root_logger.addHandler(handler)


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
