from __future__ import annotations

import logging
import os
import sys
from pathlib import Path
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from collections.abc import MutableMapping

from .types import LogContext


class StructuredFormatter(logging.Formatter):
    def __init__(self, include_caller: bool = True) -> None:
        super().__init__()
        self.include_caller = include_caller

    def format(self, record: logging.LogRecord) -> str:
        logger_name = "mkdocs-mermaid-to-image"
        level_name = record.levelname
        message = record.getMessage()

        log_string = f"[{logger_name}] {level_name}: {message}"

        if hasattr(record, "context"):
            context = getattr(record, "context", None)
            if context and isinstance(context, dict):
                context_str = " ".join([f"{k}={v}" for k, v in context.items()])
                log_string += f" ({context_str})"

        if record.exc_info:
            log_string += "\n" + self.formatException(record.exc_info)

        return log_string


def setup_plugin_logging(
    *,
    level: str = "INFO",
    include_caller: bool = True,
    log_file: str | Path | None = None,
    force: bool = False,
) -> None:
    env_level = os.environ.get("MKDOCS_MERMAID_LOG_LEVEL", "").upper()
    if env_level in ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]:
        level = env_level

    logger = logging.getLogger("mkdocs_mermaid_to_image")

    if logger.handlers and not force:
        return

    if force:
        logger.handlers.clear()

    logger.setLevel(getattr(logging, level.upper()))

    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(getattr(logging, level.upper()))
    console_handler.setFormatter(StructuredFormatter(include_caller=include_caller))
    logger.addHandler(console_handler)

    if log_file:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)

        file_handler = logging.FileHandler(log_path, encoding="utf-8")
        file_handler.setLevel(getattr(logging, level.upper()))
        file_handler.setFormatter(StructuredFormatter(include_caller=include_caller))
        logger.addHandler(file_handler)

    logger.propagate = False


def get_plugin_logger(
    name: str, **context: Any
) -> logging.Logger | logging.LoggerAdapter[logging.Logger]:
    logger = logging.getLogger(name)

    if context:

        class ContextAdapter(logging.LoggerAdapter[logging.Logger]):
            def process(
                self, msg: str, kwargs: MutableMapping[str, Any]
            ) -> tuple[str, MutableMapping[str, Any]]:
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
    log_method = getattr(logger, level.lower())
    log_method(message, extra={"context": context})


def create_processing_context(
    page_file: str | None = None,
    block_index: int | None = None,
) -> LogContext:
    return LogContext(page_file=page_file, block_index=block_index)


def create_error_context(
    error_type: str | None = None,
    processing_step: str | None = None,
) -> LogContext:
    return LogContext(error_type=error_type, processing_step=processing_step)


def create_performance_context(
    execution_time_ms: float | None = None,
    image_format: str | None = None,
) -> LogContext:
    context: LogContext = {"execution_time_ms": execution_time_ms}
    if image_format is not None and image_format in ("png", "svg"):
        context["image_format"] = image_format  # type: ignore[typeddict-item]
    return context


# setup_plugin_logging()を削除して自動初期化を無効化


def get_logger(name: str) -> logging.Logger:
    """統一ロガーファクトリー - 全モジュールが使用する標準ロガー取得関数

    Args:
        name: ロガー名（通常は__name__を使用）

    Returns:
        設定済みのロガーインスタンス
    """
    # プラグインロギングがセットアップされていない場合は初期化
    root_logger = logging.getLogger("mkdocs_mermaid_to_image")
    if not root_logger.handlers:
        setup_plugin_logging()

    return logging.getLogger(name)
