"""
Structured logging functionality for HAProxy Template IC using structlog.

This module provides context-aware structured logging with automatic
metadata injection, operation correlation, and JSON output formatting
using the industry-standard structlog library.
"""

import logging
from contextlib import contextmanager
from typing import Any, Optional, Iterator, List
from uuid import uuid4

import structlog
import structlog.contextvars


# LogContext dataclass removed - using contextvars directly for context management


@contextmanager
def logging_context(**kwargs: Any) -> Iterator[Optional[str]]:
    """Universal context manager for structured logging.

    Supports all context types:
    - operation_id (generates UUID if None)
    - component
    - resource_type, resource_namespace, resource_name
    - Any additional fields
    """
    # Handle special case for operation_id generation
    if "operation_id" in kwargs and kwargs["operation_id"] is None:
        kwargs["operation_id"] = str(uuid4())[:8]

    # Remove None/empty values to avoid cluttering logs
    context = {k: v for k, v in kwargs.items() if v is not None}
    bound_keys = list(context.keys())

    if bound_keys:
        structlog.contextvars.bind_contextvars(**context)
    try:
        # Return operation_id for backward compatibility with operation_context
        yield context.get("operation_id")
    finally:
        if bound_keys:
            structlog.contextvars.unbind_contextvars(*bound_keys)


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
