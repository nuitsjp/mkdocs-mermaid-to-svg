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
    """Mermaidプラグイン向けに簡潔な構造化ログを整形するフォーマッタ"""

    def __init__(self, include_caller: bool = True) -> None:
        """必要に応じて呼び出し元情報を含める設定で初期化する"""
        super().__init__()
        self.include_caller = include_caller

    def format(self, record: logging.LogRecord) -> str:
        """ログレコードを統一プレフィックス付き文字列へ整形する"""
        logger_name = "mkdocs-mermaid-to-svg"
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
    """プラグイン専用ロガーへハンドラーとレベル設定を適用する"""
    # 環境変数が設定されていれば優先してログレベルを上書き
    env_level = os.environ.get("MKDOCS_MERMAID_LOG_LEVEL", "").upper()
    if env_level in ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]:
        level = env_level

    logger = logging.getLogger("mkdocs_mermaid_to_image")

    if logger.handlers and not force:
        return

    if force:
        logger.handlers.clear()

    logger.setLevel(getattr(logging, level.upper()))

    formatter = StructuredFormatter(include_caller=include_caller)

    # コンソールハンドラーで標準出力へログを書き出す
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(getattr(logging, level.upper()))
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # ファイルハンドラーを指定された場合のみ追加する
    if log_file:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)

        file_handler = logging.FileHandler(log_path, encoding="utf-8")
        file_handler.setLevel(getattr(logging, level.upper()))
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    logger.propagate = False


def get_plugin_logger(
    name: str, **context: Any
) -> logging.Logger | logging.LoggerAdapter[logging.Logger]:
    """追加コンテキスト付きロガーを取得し、なければ生ロガーを返す"""
    logger = logging.getLogger(name)

    if context:

        class ContextAdapter(logging.LoggerAdapter[logging.Logger]):
            """ログ毎にコンテキスト情報を注入するアダプター"""

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
    """任意のコンテキスト情報を付与してログ出力するヘルパー"""
    log_method = getattr(logger, level.lower())
    log_method(message, extra={"context": context})


def create_processing_context(
    page_file: str | None = None,
    block_index: int | None = None,
) -> LogContext:
    """ページ情報やブロック番号を含むログ用コンテキストを生成する"""
    return LogContext(page_file=page_file, block_index=block_index)


def create_error_context(
    error_type: str | None = None,
    processing_step: str | None = None,
) -> LogContext:
    """エラー種別や処理ステップを伝えるログ用コンテキストを生成する"""
    return LogContext(error_type=error_type, processing_step=processing_step)


def create_performance_context(
    execution_time_ms: float | None = None,
) -> LogContext:
    """実行時間を記録するパフォーマンス用コンテキストを生成する"""
    return LogContext(execution_time_ms=execution_time_ms)


def get_logger(name: str) -> logging.Logger:
    """統一ロガーファクトリー - 全モジュールが使用する標準ロガー取得関数"""
    root_logger = logging.getLogger("mkdocs_mermaid_to_image")
    if not root_logger.handlers:
        setup_plugin_logging()

    return logging.getLogger(name)
