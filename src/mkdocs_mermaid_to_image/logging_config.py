"""Structured logging configuration for the MkDocs Mermaid to Image plugin."""

import logging
import os
import sys
from collections.abc import MutableMapping
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Union

from .types import LogContext


class StructuredFormatter(logging.Formatter):
    """Custom formatter for structured logging."""

    def __init__(self, include_caller: bool = True) -> None:
        """Initialize the formatter.

        Args:
            include_caller: Whether to include caller information in logs
        """
        super().__init__()
        self.include_caller = include_caller

    def format(self, record: logging.LogRecord) -> str:
        """Format a log record with structured information.

        Args:
            record: The log record to format

        Returns:
            Formatted log message
        """
        # Create base structured log entry
        log_entry: dict[str, Any] = {
            "timestamp": datetime.now(UTC).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }

        # Add caller information if enabled
        if self.include_caller and hasattr(record, "pathname"):
            log_entry["caller"] = {
                "filename": Path(record.pathname).name,
                "function": record.funcName,
                "line": record.lineno,
            }

        # Add any additional context from the record
        if hasattr(record, "context"):
            context = getattr(record, "context", None)
            if context:
                log_entry["context"] = context

        # Add exception information if present
        if record.exc_info:
            log_entry["exception"] = self.formatException(record.exc_info)

        # Format as key=value pairs for easier reading
        parts = [f"timestamp={log_entry['timestamp']}"]
        parts.append(f"level={log_entry['level']}")
        parts.append(f"logger={log_entry['logger']}")

        if "caller" in log_entry:
            caller = log_entry["caller"]
            if isinstance(caller, dict):
                filename = caller.get("filename", "")
                function = caller.get("function", "")
                line = caller.get("line", "")
                parts.append(f"caller={filename}:{function}:{line}")

        parts.append(f"message={log_entry['message']}")

        if "context" in log_entry:
            context = log_entry["context"]
            if isinstance(context, dict):
                for key, value in context.items():
                    parts.append(f"{key}={value}")

        if "exception" in log_entry:
            parts.append(f"exception={log_entry['exception']}")

        return " ".join(parts)


def setup_plugin_logging(
    *,
    level: str = "INFO",
    include_caller: bool = True,
    log_file: str | Path | None = None,
    force: bool = False,
) -> None:
    """Setup logging configuration for the plugin.

    Args:
        level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        include_caller: Whether to include caller information
        log_file: Optional file path to write logs to
        force: Force reconfiguration even if already configured
    """
    # Get log level from environment if set
    env_level = os.environ.get("MKDOCS_MERMAID_LOG_LEVEL", "").upper()
    if env_level in ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]:
        level = env_level

    # Configure root logger for the plugin
    logger = logging.getLogger("mkdocs_mermaid_to_image")

    # Only configure if not already configured or if forced
    if logger.handlers and not force:
        return

    # Clear existing handlers if forcing reconfiguration
    if force:
        logger.handlers.clear()

    # Set log level
    logger.setLevel(getattr(logging, level.upper()))

    # Create console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(getattr(logging, level.upper()))
    console_handler.setFormatter(StructuredFormatter(include_caller=include_caller))
    logger.addHandler(console_handler)

    # Create file handler if requested
    if log_file:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)

        file_handler = logging.FileHandler(log_path, encoding="utf-8")
        file_handler.setLevel(getattr(logging, level.upper()))
        file_handler.setFormatter(StructuredFormatter(include_caller=include_caller))
        logger.addHandler(file_handler)

    # Prevent propagation to avoid duplicate logs
    logger.propagate = False


def get_plugin_logger(
    name: str, **context: Any
) -> Union[logging.Logger, logging.LoggerAdapter[logging.Logger]]:
    """Get a logger instance for the plugin with optional context.

    Args:
        name: Name of the logger (typically __name__)
        **context: Additional context to include in logs

    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(name)

    # Add context to logger if provided
    if context:
        # Create a custom adapter to add context to all log records
        class ContextAdapter(logging.LoggerAdapter[logging.Logger]):
            def process(
                self, msg: str, kwargs: MutableMapping[str, Any]
            ) -> tuple[str, MutableMapping[str, Any]]:
                # Add context to extra if not already present
                if "extra" not in kwargs:
                    kwargs["extra"] = {}
                if "context" not in kwargs["extra"]:
                    kwargs["extra"]["context"] = {}
                kwargs["extra"]["context"].update(self.extra)
                return msg, kwargs

        return ContextAdapter(logger, context)

    return logger


def log_with_context(
    logger: logging.Logger, level: str, message: str, **context: Any
) -> None:
    """Log a message with additional context.

    Args:
        logger: Logger instance to use
        level: Log level (debug, info, warning, error, critical)
        message: Log message
        **context: Additional context to include
    """
    log_method = getattr(logger, level.lower())
    log_method(message, extra={"context": context})


def create_processing_context(
    page_file: str | None = None,
    block_index: int | None = None,
) -> LogContext:
    """Create a log context for processing operations."""
    return LogContext(page_file=page_file, block_index=block_index)


def create_error_context(
    error_type: str | None = None,
    processing_step: str | None = None,
) -> LogContext:
    """Create a log context for error reporting."""
    return LogContext(error_type=error_type, processing_step=processing_step)


def create_performance_context(
    execution_time_ms: float | None = None,
    image_format: str | None = None,
) -> LogContext:
    """Create a log context for performance tracking."""

    context: LogContext = {"execution_time_ms": execution_time_ms}
    if image_format is not None and image_format in ("png", "svg"):
        context["image_format"] = image_format  # type: ignore[typeddict-item]
    return context


# Initialize plugin logging when module is imported
setup_plugin_logging()
