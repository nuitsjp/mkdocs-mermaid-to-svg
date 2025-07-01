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


def clean_temp_file(file_path: str) -> None:
    if not file_path:
        return

    logger = get_logger(__name__)
    file_path_obj = Path(file_path)

    try:
        if file_path_obj.exists():
            file_path_obj.unlink()
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
    return which(command) is not None


def clean_generated_images(
    image_paths: list[str], logger: logging.Logger | None
) -> None:
    """生成された画像ファイルをクリーンアップする"""
    if not image_paths:
        return

    cleaned_count = 0
    error_count = 0

    for image_path in image_paths:
        if not image_path:
            continue

        image_file = Path(image_path)

        try:
            if image_file.exists():
                image_file.unlink()
                cleaned_count += 1
                if logger:
                    logger.debug(
                        f"Cleaned generated image: {image_path}",
                        extra={
                            "context": {"file_path": image_path, "operation": "delete"}
                        },
                    )
        except PermissionError as e:
            error_count += 1
            if logger:
                logger.warning(
                    f"Permission denied when cleaning generated image: {image_path}",
                    extra={
                        "context": {
                            "file_path": image_path,
                            "error_type": "PermissionError",
                            "error_message": str(e),
                            "suggestion": (
                                "Check file permissions or run with privileges"
                            ),
                        }
                    },
                )
        except OSError as e:
            error_count += 1
            if logger:
                logger.warning(
                    f"OS error when cleaning generated image: {image_path}",
                    extra={
                        "context": {
                            "file_path": image_path,
                            "error_type": "OSError",
                            "error_message": str(e),
                            "suggestion": "File may be locked by another process",
                        }
                    },
                )

    if (cleaned_count > 0 or error_count > 0) and logger:
        logger.info(f"Image cleanup: {cleaned_count} cleaned, {error_count} errors")
