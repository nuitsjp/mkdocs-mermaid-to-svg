"""Utility helper functions."""

import json
from collections.abc import Mapping
from pathlib import Path
from typing import Any, TypeVar

from ..types import JSONObject, JSONValue

T = TypeVar("T")


# ロガーを遅延初期化で循環インポートを回避
def _get_logger() -> Any:
    try:
        from ..utils.logging_config import get_logger

        return get_logger(__name__, module="helpers")
    except ImportError:
        import logging

        return logging.getLogger(__name__)


logger: Any = _get_logger()


def load_json_file(filepath: str | Path) -> JSONObject:
    """Load JSON data from a file.

    Parameters
    ----------
    filepath : str | Path
        Path to JSON file

    Returns
    -------
    JSONObject
        Loaded JSON data as a dictionary

    Raises
    ------
    FileNotFoundError
        If file doesn't exist
    ValueError
        If file contains invalid JSON
    """
    path = Path(filepath)
    logger.debug(
        "Loading JSON file",
        file_path=str(path),
        file_exists=path.exists(),
        file_size=path.stat().st_size if path.exists() else None,
    )

    if not path.exists():
        logger.error(
            "File not found",
            file_path=str(path),
            absolute_path=str(path.absolute()),
        )
        raise FileNotFoundError(f"File not found: {path}")

    try:
        logger.debug("Opening file", file_path=str(path))
        with path.open("r", encoding="utf-8") as f:
            result = json.load(f)
            logger.debug(
                "Successfully loaded JSON data",
                file_path=str(path),
                data_type=type(result).__name__,
            )

            # json.load returns Any, but we expect dict[str, Any]
            if not isinstance(result, dict):
                type_name = type(result).__name__
                logger.error(
                    "Invalid JSON structure",
                    file_path=str(path),
                    expected_type="object",
                    actual_type=type_name,
                )
                raise ValueError(f"Expected JSON object in {path}, got {type_name}")

            logger.debug(
                "JSON object loaded",
                file_path=str(path),
                key_count=len(result),
                keys=list(result.keys())[:5],  # 最初の5キーのみ
            )
            return result
    except json.JSONDecodeError as e:
        logger.error(
            "Failed to parse JSON",
            file_path=str(path),
            error_type=type(e).__name__,
            error_message=str(e),
            line_number=e.lineno if hasattr(e, "lineno") else None,
            column_number=e.colno if hasattr(e, "colno") else None,
        )
        raise ValueError(f"Invalid JSON in {path}: {e}") from e


def save_json_file(
    data: JSONObject,
    filepath: str | Path,
    *,
    indent: int = 2,
    ensure_ascii: bool = False,
) -> None:
    """Save data to a JSON file.

    Parameters
    ----------
    data : JSONObject
        JSON-compatible dictionary to save
    filepath : str | Path
        Path to save to
    indent : int
        JSON indentation level
    ensure_ascii : bool
        Whether to escape non-ASCII characters
    """
    path = Path(filepath)
    logger.debug(
        "Saving JSON data",
        file_path=str(path),
        indent=indent,
        ensure_ascii=ensure_ascii,
        key_count=len(data),
    )

    # ディレクトリが存在しない場合は作成
    if not path.parent.exists():
        logger.debug(
            "Creating directory",
            directory_path=str(path.parent),
            directory_exists=path.parent.exists(),
        )
    path.parent.mkdir(parents=True, exist_ok=True)

    logger.debug(
        "Writing JSON data",
        file_path=str(path),
        key_count=len(data),
        data_size_estimate=len(str(data)),
    )
    with path.open("w", encoding="utf-8") as f:
        json.dump(data, f, indent=indent, ensure_ascii=ensure_ascii)
    logger.info(
        "JSON file saved successfully",
        file_path=str(path),
        file_size=path.stat().st_size if path.exists() else None,
        key_count=len(data),
    )


def chunk_list(items: list[T], chunk_size: int) -> list[list[T]]:
    """Split a list into chunks of specified size.

    Parameters
    ----------
    items : list[T]
        Items to chunk
    chunk_size : int
        Size of each chunk

    Returns
    -------
    list[list[T]]
        List of chunks

    Raises
    ------
    ValueError
        If chunk_size is not positive

    Examples
    --------
    >>> chunk_list([1, 2, 3, 4, 5], 2)
    [[1, 2], [3, 4], [5]]
    """
    if chunk_size <= 0:
        logger.error(
            "Invalid chunk_size",
            chunk_size=chunk_size,
            error="chunk_size must be positive",
        )
        raise ValueError(f"chunk_size must be positive, got {chunk_size}")

    logger.debug(
        "Chunking list",
        item_count=len(items),
        chunk_size=chunk_size,
        expected_chunks=(len(items) + chunk_size - 1) // chunk_size if items else 0,
    )

    chunks = [items[i : i + chunk_size] for i in range(0, len(items), chunk_size)]
    logger.debug(
        "Chunking completed",
        input_count=len(items),
        chunk_count=len(chunks),
        chunk_size=chunk_size,
        last_chunk_size=len(chunks[-1]) if chunks else 0,
    )

    return chunks


def flatten_dict(
    nested_dict: Mapping[str, JSONValue],
    *,
    separator: str = ".",
    prefix: str = "",
) -> Mapping[str, JSONValue]:
    """Flatten a nested dictionary.

    Parameters
    ----------
    nested_dict : dict[str, JSONValue]
        Dictionary with JSON-compatible values to flatten
    separator : str
        Separator for keys
    prefix : str
        Prefix for all keys

    Returns
    -------
    Mapping[str, JSONValue]
        Flattened dictionary with dot-notation keys

    Examples
    --------
    >>> flatten_dict({"a": {"b": 1, "c": 2}})
    {"a.b": 1, "a.c": 2}
    """
    logger.debug(
        "Flattening dictionary",
        input_keys=len(nested_dict),
        separator=separator,
        has_prefix=bool(prefix),
        prefix=prefix if prefix else None,
    )

    items: list[tuple[str, JSONValue]] = []

    for key, value in nested_dict.items():
        new_key = f"{prefix}{separator}{key}" if prefix else key
        logger.debug(
            "Processing dictionary key",
            original_key=key,
            new_key=new_key,
            value_type=type(value).__name__,
            is_nested=isinstance(value, dict),
        )

        if isinstance(value, dict):
            logger.debug(
                "Found nested dictionary",
                key=key,
                nested_key_count=len(value),
                nesting_level=prefix.count(separator) + 1 if prefix else 1,
            )
            items.extend(
                flatten_dict(value, separator=separator, prefix=new_key).items()
            )
        else:
            items.append((new_key, value))

    result = dict(items)
    logger.debug(
        "Dictionary flattening completed",
        input_key_count=len(nested_dict),
        output_key_count=len(result),
        keys_expanded=len(result) - len(nested_dict),
        flattening_ratio=round(len(result) / len(nested_dict), 2) if nested_dict else 0,
    )

    return result
