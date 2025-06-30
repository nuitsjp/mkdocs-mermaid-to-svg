import hashlib
import logging
import os
import tempfile
from pathlib import Path
from shutil import which

from .logging_config import get_plugin_logger


def setup_logger(name: str, log_level: str = "INFO") -> logging.Logger:
    """プラグイン用のロガーを設定する"""
    # メインロガーを取得
    logger = logging.getLogger(name)

    # 既存のハンドラをクリア
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)

    # ハンドラを追加
    handler = logging.StreamHandler()
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    handler.setFormatter(formatter)
    logger.addHandler(handler)

    # ログレベルを設定
    level = getattr(logging, log_level.upper())
    logger.setLevel(level)
    handler.setLevel(level)

    # 親ロガーへの伝播を無効にして重複を避ける
    logger.propagate = False

    return logger


def generate_image_filename(
    page_file: str, block_index: int, mermaid_code: str, image_format: str
) -> str:
    page_name = Path(page_file).stem

    code_hash = hashlib.md5(
        mermaid_code.encode("utf-8"), usedforsecurity=False
    ).hexdigest()[:8]  # nosec B324

    return f"{page_name}_mermaid_{block_index}_{code_hash}.{image_format}"


def ensure_directory(directory: str) -> None:
    Path(directory).mkdir(parents=True, exist_ok=True)


def get_temp_file_path(suffix: str = ".mmd") -> str:
    fd, path = tempfile.mkstemp(suffix=suffix)

    os.close(fd)

    return path


def clean_temp_file(file_path: str) -> None:
    if not file_path:
        return

    logger = get_plugin_logger(__name__)
    file_path_obj = Path(file_path)

    try:
        if file_path_obj.exists():
            file_path_obj.unlink()
            logger.debug(
                "Temporary file cleaned successfully",
                extra={"context": {"file_path": file_path, "operation": "delete"}},
            )
    except PermissionError as e:
        logger.warning(
            f"Permission denied when cleaning temporary file: {file_path}",
            extra={
                "context": {
                    "file_path": file_path,
                    "error_type": "PermissionError",
                    "error_message": str(e),
                    "suggestion": "Check file permissions or run with privileges",
                }
            },
        )
    except OSError as e:
        logger.warning(
            f"OS error when cleaning temporary file: {file_path}",
            extra={
                "context": {
                    "file_path": file_path,
                    "error_type": "OSError",
                    "error_message": str(e),
                    "suggestion": "File may be locked by another process",
                }
            },
        )


def get_relative_path(file_path: str, base_path: str) -> str:
    if not file_path or not base_path:
        return file_path

    logger = get_plugin_logger(__name__)

    try:
        rel_path = os.path.relpath(file_path, base_path)
        logger.debug(
            "Relative path calculated successfully",
            extra={
                "context": {
                    "file_path": file_path,
                    "base_path": base_path,
                    "relative_path": rel_path,
                }
            },
        )
        return rel_path
    except ValueError as e:
        logger.warning(
            f"Cannot calculate relative path from {base_path} to {file_path}",
            extra={
                "context": {
                    "file_path": file_path,
                    "base_path": base_path,
                    "error_type": "ValueError",
                    "error_message": str(e),
                    "fallback": "Using absolute path",
                    "suggestion": "Often happens with cross-drive paths on Windows",
                }
            },
        )
        return file_path


def is_command_available(command: str) -> bool:
    return which(command) is not None
