import hashlib
import logging
import os
import tempfile
from pathlib import Path
from shutil import which

from .logging_config import get_logger


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


def _get_cleanup_suggestion(error_type: str) -> str:
    """Get contextual suggestion based on error type."""
    if error_type == "PermissionError":
        return "Check file permissions or run with privileges"
    elif error_type == "OSError":
        return "File may be locked by another process"
    else:
        return "Try again or check system logs for details"


def clean_file_with_error_handling(
    file_path: str,
    logger: logging.Logger | None = None,
    operation_type: str = "cleanup",
) -> tuple[bool, bool]:
    """ファイル削除の共通処理（エラーハンドリング付き）

    Args:
        file_path: 削除するファイルのパス
        logger: ロガーインスタンス（Noneの場合はログ出力なし）
        operation_type: 操作の種類（ログ出力用）

    Returns:
        Tuple of (success, had_error) where:
        - success: True if file was successfully deleted
        - had_error: True if there was an actual error (not just non-existence)
    """
    if not file_path:
        return False, False

    file_obj = Path(file_path)

    try:
        if file_obj.exists():
            file_obj.unlink()
            if logger:
                logger.debug(f"Successfully cleaned file: {file_path}")
            return True, False
        return False, False  # File doesn't exist, not an error
    except (PermissionError, OSError) as e:
        error_type = type(e).__name__
        if logger:
            logger.warning(
                f"{error_type} when cleaning file: {file_path}",
                extra={
                    "context": {
                        "file_path": file_path,
                        "operation_type": operation_type,
                        "error_type": error_type,
                        "error_message": str(e),
                        "suggestion": _get_cleanup_suggestion(error_type),
                    }
                },
            )
        return False, True  # Actual error occurred


def clean_temp_file(file_path: str) -> None:
    """一時ファイルをクリーンアップする"""
    logger = get_logger(__name__)
    clean_file_with_error_handling(file_path, logger, "temp_cleanup")


def get_relative_path(file_path: str, base_path: str) -> str:
    if not file_path or not base_path:
        return file_path

    logger = get_logger(__name__)

    try:
        rel_path = os.path.relpath(file_path, base_path)
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
    """Check if a command is available, handling complex commands like 'npx mmdc'"""
    if not command:
        return False

    # Split command to get the first part (actual executable)
    command_parts = command.split()
    if not command_parts:
        return False

    # For commands like "npx mmdc", check if "npx" is available
    base_command = command_parts[0]
    return which(base_command) is not None


def clean_generated_images(
    image_paths: list[str], logger: logging.Logger | None
) -> None:
    """生成された画像ファイルをクリーンアップする"""
    if not image_paths:
        return

    results = [
        clean_file_with_error_handling(path, logger, "image_cleanup")
        for path in image_paths
        if path
    ]

    cleaned_count = sum(success for success, _ in results)
    error_count = sum(had_error for _, had_error in results)

    if (cleaned_count > 0 or error_count > 0) and logger:
        logger.info(f"Image cleanup: {cleaned_count} cleaned, {error_count} errors")
