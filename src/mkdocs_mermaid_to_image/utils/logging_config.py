"""Structured logging configuration using structlog."""

import logging
import os
import sys
from collections.abc import Iterator
from contextlib import contextmanager
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Protocol

import structlog
from structlog import BoundLogger
from structlog.contextvars import (
    bind_contextvars,
    unbind_contextvars,
)

from ..types import LogFormat, LogLevel


class LoggerProtocol(Protocol):
    """Protocol for structured logger."""

    def bind(self, **kwargs: Any) -> "LoggerProtocol":
        """Bind context variables to the logger."""
        ...

    def unbind(self, *keys: str) -> "LoggerProtocol":
        """Unbind context variables from the logger."""
        ...

    def debug(self, event: str, **kwargs: Any) -> None:
        """Log a debug message."""
        ...

    def info(self, event: str, **kwargs: Any) -> None:
        """Log an info message."""
        ...

    def warning(self, event: str, **kwargs: Any) -> None:
        """Log a warning message."""
        ...

    def error(self, event: str, **kwargs: Any) -> None:
        """Log an error message."""
        ...

    def critical(self, event: str, **kwargs: Any) -> None:
        """Log a critical message."""
        ...


def add_timestamp(_: Any, __: Any, event_dict: dict[str, Any]) -> dict[str, Any]:
    """Add ISO timestamp to log entries."""
    event_dict["timestamp"] = datetime.now(UTC).isoformat()
    return event_dict


def add_caller_info(_: Any, __: Any, event_dict: dict[str, Any]) -> dict[str, Any]:
    """Add caller information (file, function, line) to log entries."""
    try:
        # Get the caller frame (skip structlog internals)
        import inspect

        frame = None
        stack = inspect.stack()

        # Skip the first few frames which are structlog internals
        for f in stack[4:12]:  # Limit search to avoid infinite loops
            if f.filename and f.function:
                module = inspect.getmodule(f.frame)
                if (
                    module
                    and not module.__name__.startswith("structlog")
                    and not module.__name__.startswith("logging")
                    and "site-packages" not in f.filename
                ):
                    frame = f
                    break

        if frame:
            event_dict["caller"] = {
                "filename": Path(frame.filename).name,
                "function": frame.function,
                "line": frame.lineno,
            }
    except Exception:  # nosec B110
        # If caller info extraction fails, silently continue
        # This is intentional to prevent logging infrastructure failures
        pass

    return event_dict


def add_log_level_upper(_: Any, __: Any, event_dict: dict[str, Any]) -> dict[str, Any]:
    """Convert log level to uppercase for consistency."""
    if "level" in event_dict:
        event_dict["level"] = event_dict["level"].upper()
    return event_dict


def setup_logging(  # noqa: PLR0913
    *,
    level: LogLevel | str = "INFO",
    format: LogFormat = "console",
    log_file: str | Path | None = None,
    include_timestamp: bool = True,
    include_caller_info: bool = True,
    force: bool = False,
) -> None:
    """Setup structured logging configuration.

    Parameters
    ----------
    level : LogLevel | str
        Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        Can also be set via LOG_LEVEL environment variable
    format : LogFormat
        Output format: "json", "console", or "plain"
        - json: Structured JSON output (best for production)
        - console: Colored, human-readable output (best for development)
        - plain: Simple key=value output
    log_file : str | Path | None
        Optional file path to write logs to
    include_timestamp : bool
        Whether to add ISO timestamps to logs
    include_caller_info : bool
        Whether to add caller information (file, function, line)
    force : bool
        Force reconfiguration even if already configured
    """
    # 環境変数からログレベルを取得
    env_level = os.environ.get("LOG_LEVEL", "").upper()
    if env_level in ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]:
        level = env_level

    # 環境変数からフォーマットを取得
    env_format = os.environ.get("LOG_FORMAT", "").lower()
    if env_format in ["json", "console", "plain"]:
        format = env_format  # type: ignore

    # プロセッサの設定
    processors: list[Any] = [
        structlog.contextvars.merge_contextvars,
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        add_log_level_upper,
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
    ]

    # Add timestamp processor if enabled
    if include_timestamp:
        processors.insert(3, add_timestamp)

    # Add caller info processor if enabled
    if include_caller_info:
        processors.insert(4, add_caller_info)

    # 開発環境判定
    is_development = (
        os.environ.get("PROJECT_ENV") == "development" or format == "console"
    )

    # レンダラーの選択
    if format == "json":
        processors.append(structlog.processors.JSONRenderer())
    elif format == "console" and is_development:
        try:
            # Rich ConsoleRendererを使用（カラフルな出力）
            processors.append(
                structlog.dev.ConsoleRenderer(
                    colors=True,
                )
            )
        except ImportError:
            # Richが利用できない場合は標準のコンソール出力
            processors.append(structlog.dev.ConsoleRenderer())
    else:
        # Plain text (key=value format)
        processors.append(structlog.processors.KeyValueRenderer())

    # structlogの設定
    structlog.configure(
        processors=processors,
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )

    # 標準ライブラリのloggingも設定
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=getattr(logging, level.upper() if isinstance(level, str) else level),
        force=force,
    )

    # ファイルハンドラーの追加
    if log_file:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)

        file_handler = logging.FileHandler(log_path, encoding="utf-8")
        file_handler.setLevel(
            getattr(logging, level.upper() if isinstance(level, str) else level)
        )

        # ファイルへの出力は既にstructlogで処理済みなので、そのまま出力
        file_handler.setFormatter(logging.Formatter("%(message)s"))

        logging.root.addHandler(file_handler)

    # サードパーティライブラリのログレベル調整
    if level != "DEBUG":
        for logger_name in ["urllib3", "asyncio", "filelock"]:
            logging.getLogger(logger_name).setLevel(logging.WARNING)


def get_logger(name: str, **context: Any) -> BoundLogger:
    """Get a structured logger instance with optional context.

    Parameters
    ----------
    name : str
        Name of the logger (typically __name__)
    **context : Any
        Initial context to bind to the logger

    Returns
    -------
    BoundLogger
        Configured structlog logger instance

    Example
    -------
    >>> logger = get_logger(__name__)
    >>> logger.info("Processing started", items_count=100)

    >>> logger = get_logger(__name__, module="data_processor", version="1.0")
    >>> logger.error("Processing failed", error_type="ValidationError")
    """
    logger: BoundLogger = structlog.get_logger(name)

    if context:
        logger = logger.bind(**context)

    return logger


@contextmanager
def log_context(**kwargs: Any) -> Iterator[None]:
    """Context manager to temporarily bind context variables.

    Parameters
    ----------
    **kwargs : Any
        Context variables to bind

    Example
    -------
    >>> logger = get_logger(__name__)
    >>> with log_context(user_id=123, request_id="abc"):
    ...     logger.info("Processing user request")
    ...     # All logs within this context will include user_id and request_id
    """
    bind_contextvars(**kwargs)
    try:
        yield
    finally:
        unbind_contextvars(*kwargs.keys())


def set_log_level(level: LogLevel | str, logger_name: str | None = None) -> None:
    """Dynamically change the log level.

    Parameters
    ----------
    level : LogLevel | str
        New logging level
    logger_name : str | None
        Name of the logger to update. If None, updates root logger
    """
    level_value = getattr(logging, level.upper() if isinstance(level, str) else level)

    if logger_name:
        logging.getLogger(logger_name).setLevel(level_value)
    else:
        logging.root.setLevel(level_value)
        # Update all handlers
        for handler in logging.root.handlers:
            handler.setLevel(level_value)


def log_performance(logger: BoundLogger) -> Any:
    """Decorator to log function performance metrics.

    Parameters
    ----------
    logger : BoundLogger
        Logger instance to use

    Example
    -------
    >>> logger = get_logger(__name__)
    >>> @log_performance(logger)
    ... def process_data(items):
    ...     return [item * 2 for item in items]
    """
    import functools
    import time

    def decorator(func: Any) -> Any:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            start_time = time.perf_counter()
            func_name = func.__name__

            # Log function call
            logger.debug(
                f"Function {func_name} started",
                function=func_name,
                args_count=len(args),
                kwargs_count=len(kwargs),
            )

            try:
                result = func(*args, **kwargs)
                duration_ms = (time.perf_counter() - start_time) * 1000

                # Log successful completion with duration
                logger.debug(
                    f"Function {func_name} completed",
                    function=func_name,
                    duration_ms=round(duration_ms, 2),
                    success=True,
                )

                return result

            except Exception as e:
                duration_ms = (time.perf_counter() - start_time) * 1000

                # Log error with duration
                logger.error(
                    f"Function {func_name} failed",
                    function=func_name,
                    duration_ms=round(duration_ms, 2),
                    success=False,
                    error_type=type(e).__name__,
                    error_message=str(e),
                    exc_info=True,
                )
                raise

        return wrapper

    return decorator
