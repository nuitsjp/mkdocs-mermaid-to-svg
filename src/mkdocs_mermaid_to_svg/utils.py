import hashlib
import logging
import os
import platform
import shlex
import subprocess  # nosec B404
import tempfile
from collections.abc import Iterable
from pathlib import Path

from .logging_config import get_logger


def generate_image_filename(
    page_file: str,
    block_index: int,
    mermaid_code: str,
    image_format: str,
    options: dict[str, object] | None = None,
) -> str:
    """ページ名とコードハッシュから衝突しにくい画像ファイル名を生成する。

    ``options`` が指定された場合、ハッシュ入力に含めることで
    同一コードでも異なるオプションなら別ファイル名を生成する。
    """
    page_name = Path(page_file).stem

    # オプションが空でない場合はキーソート済みJSONをハッシュに含める
    options_str = ""
    if options:
        import json

        options_str = json.dumps(options, sort_keys=True)

    hash_input = mermaid_code + options_str
    code_hash = hashlib.md5(
        hash_input.encode("utf-8"), usedforsecurity=False
    ).hexdigest()[:8]  # nosec B324

    return f"{page_name}_mermaid_{block_index}_{code_hash}.{image_format}"


def ensure_directory(directory: str) -> None:
    """出力先ディレクトリが存在しなければ再帰的に作成する"""
    Path(directory).mkdir(parents=True, exist_ok=True)


def get_temp_file_path(suffix: str = ".mmd") -> str:
    """安全に作成した一時ファイルパスを返しハンドルはすぐ閉じる"""
    fd, path = tempfile.mkstemp(suffix=suffix)
    os.close(fd)
    return path


def clean_temp_file(file_path: str) -> None:
    """一時ファイルをクリーンアップする"""
    logger = get_logger(__name__)
    clean_file_with_error_handling(file_path, logger, "temp_cleanup")


def _get_cleanup_suggestion(error_type: str) -> str:
    """エラー種別に応じた復旧策をメッセージとして返す"""
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
    """基準パスからの相対パスを計算しPOSIX形式に揃える"""
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
    """バージョン確認等を走らせてコマンドが利用可能か判定する"""
    if not command:
        return False

    logger = get_logger(__name__)
    logger.debug(f"Checking if command '{command}' is working...")
    command_parts = split_command(command)
    if not command_parts:
        return False

    return _verify_command_execution(command_parts, command, logger)


def split_command(command: str) -> list[str]:
    """引用符を保持しながらコマンド文字列を安全に分割する"""
    trimmed = command.strip()
    if not trimmed:
        return []

    posix_mode = os.name != "nt"
    try:
        parts = shlex.split(trimmed, posix=posix_mode)
    except ValueError:
        return [_strip_wrapping_quotes(trimmed)]

    if not parts:
        return [_strip_wrapping_quotes(trimmed)]

    parts = [_strip_wrapping_quotes(part) for part in parts]

    if _should_treat_as_single_path(trimmed, parts):
        return [_strip_wrapping_quotes(trimmed)]

    return parts


def _should_treat_as_single_path(command: str, parts: list[str]) -> bool:
    """バックスラッシュ等を含むパスを1要素のコマンドとして扱うべきか判定する"""
    if len(parts) <= 1:
        return False

    has_space = " " in command
    if not has_space:
        return False

    # On Windows os.sep is "\"; commands may also include "/" (MSYS).
    # Include "\\" to account for escaped separators.
    path_separators = [os.sep]
    if os.sep != "/":
        path_separators.append("/")
    if os.sep != "\\":
        path_separators.append("\\")

    if not any(sep in command for sep in path_separators):
        return False

    lowered = command.lower()
    known_prefixes = (
        "npx ",
        "npm ",
        "pnpm ",
        "yarn ",
        "node ",
        "python ",
        "pip ",
        "uv ",
        "cmd ",
        "powershell ",
        "pwsh ",
    )

    return not any(lowered.startswith(prefix) for prefix in known_prefixes)


def _strip_wrapping_quotes(value: str) -> str:
    """単一引数として囲まれた引用符を取り除く"""
    if len(value) >= 2 and value[0] == value[-1] and value[0] in {'"', "'"}:
        return value[1:-1]
    return value


def _verify_command_execution(
    command_parts: Iterable[str], command: str, logger: logging.Logger
) -> bool:
    """コマンドが実際に実行できるかバージョンオプションで確認する"""
    parts_list: list[str] = list(command_parts)
    version_flags = ["--version", "-v", "--help"]

    for flag in version_flags:
        try:
            use_shell = platform.system() == "Windows"

            if use_shell:
                version_cmd_str = subprocess.list2cmdline([*parts_list, flag])
                result = subprocess.run(  # nosec B603,B602,B607
                    ["cmd", "/c", version_cmd_str],
                    capture_output=True,
                    text=True,
                    timeout=5,
                    check=False,
                    shell=False,  # nosec B603
                    encoding="utf-8",
                )
            else:
                version_cmd = [*parts_list, flag]
                result = subprocess.run(  # nosec B603
                    version_cmd,
                    capture_output=True,
                    text=True,
                    timeout=5,
                    check=False,
                    shell=False,
                    encoding="utf-8",
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
