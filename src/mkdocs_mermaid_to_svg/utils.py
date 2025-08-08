import hashlib
import logging
import os
import platform
import subprocess  # nosec B404
import tempfile
from pathlib import Path

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


def clean_temp_file(file_path: str) -> None:
    """一時ファイルをクリーンアップする"""
    logger = get_logger(__name__)
    clean_file_with_error_handling(file_path, logger, "temp_cleanup")


def _get_cleanup_suggestion(error_type: str) -> str:
    """Get contextual suggestion based on error type."""
    suggestions = {
        "PermissionError": "Check file permissions or run with privileges",
        "OSError": "File may be locked by another process",
    }
    return suggestions.get(error_type, "Try again or check system logs for details")


def clean_file_with_error_handling(
    file_path: str,
    logger: logging.Logger | None = None,
    operation_type: str = "cleanup",
) -> tuple[bool, bool]:
    """ファイル削除の共通処理（エラーハンドリング付き）"""
    if not file_path:
        return False, False

    file_obj = Path(file_path)

    try:
        if file_obj.exists():
            file_obj.unlink()
            if logger:
                logger.debug(f"Successfully cleaned file: {file_path}")
            return True, False
        return False, False
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
        return False, True


def get_relative_path(file_path: str, base_path: str) -> str:
    if not file_path or not base_path:
        return file_path

    logger = get_logger(__name__)

    try:
        rel_path = os.path.relpath(file_path, base_path)
        return rel_path.replace(os.sep, "/")
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
    """Check if a command is available and working by executing version check"""
    if not command:
        return False

    command_parts = command.split()
    if not command_parts:
        return False

    logger = get_logger(__name__)
    logger.debug(f"Checking if command '{command}' is working...")

    return _verify_command_execution(command_parts, command, logger)


def _verify_command_execution(
    command_parts: list[str], command: str, logger: logging.Logger
) -> bool:
    """Verify that a command can be executed successfully"""
    version_flags = ["--version", "-v", "--help"]

    for flag in version_flags:
        try:
            use_shell = platform.system() == "Windows"

            if use_shell:
                version_cmd_str = " ".join([*command_parts, flag])
                result = subprocess.run(  # nosec B603,B602,B607
                    ["cmd", "/c", version_cmd_str],
                    capture_output=True,
                    text=True,
                    timeout=5,
                    check=False,
                    shell=False,  # nosec B603
                )
            else:
                version_cmd = [*command_parts, flag]
                result = subprocess.run(  # nosec B603
                    version_cmd,
                    capture_output=True,
                    text=True,
                    timeout=5,
                    check=False,
                    shell=False,
                )

            if result.returncode in [0, 1]:
                logger.debug(
                    f"Command '{command}' is available and working "
                    f"(verified with '{flag}', exit code: {result.returncode})"
                )
                return True

        except (subprocess.TimeoutExpired, FileNotFoundError, OSError, Exception) as e:
            logger.debug(f"Command '{command}' check failed with '{flag}': {e}")
            continue

    logger.debug(f"Command '{command}' exists but is not working properly")
    return False


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
