"""Helper functions for common operations."""

import json
from pathlib import Path
from typing import Any

from .logging_config import get_logger

logger = get_logger(__name__)


def chunk_list(items: list[Any], chunk_size: int) -> list[list[Any]]:
    """Split a list into chunks of specified size.

    Parameters
    ----------
    items : list[Any]
        List to be chunked
    chunk_size : int
        Size of each chunk (must be positive)

    Returns
    -------
    list[list[Any]]
        List of chunks

    Raises
    ------
    ValueError
        If chunk_size is not positive
    """
    logger.debug("Chunking list", item_count=len(items), chunk_size=chunk_size)

    if chunk_size <= 0:
        raise ValueError("Chunk size must be positive")

    if not items:
        logger.debug("Empty list provided, returning empty result")
        return []

    chunks = []
    for i in range(0, len(items), chunk_size):
        chunk = items[i : i + chunk_size]
        chunks.append(chunk)

    logger.debug("Created chunks", chunk_count=len(chunks), item_count=len(items))
    return chunks


def flatten_dict(
    nested_dict: dict[str, Any], separator: str = ".", prefix: str = ""
) -> dict[str, Any]:
    """Flatten a nested dictionary.

    Parameters
    ----------
    nested_dict : dict[str, Any]
        Dictionary to flatten
    separator : str, default="."
        Separator to use between nested keys
    prefix : str, default=""
        Prefix to add to all keys

    Returns
    -------
    dict[str, Any]
        Flattened dictionary
    """
    logger.debug(
        "Flattening dictionary",
        top_level_keys=len(nested_dict),
        separator=separator,
    )

    result = {}

    for key, value in nested_dict.items():
        new_key = f"{prefix}{separator}{key}" if prefix else key

        if isinstance(value, dict):
            # Recursively flatten nested dictionaries
            result.update(flatten_dict(value, separator, new_key))
        else:
            result[new_key] = value

    logger.debug(
        "Dictionary flattened",
        original_keys=len(nested_dict),
        flattened_keys=len(result),
    )
    return result


def save_json_file(data: Any, file_path: str | Path, indent: int | None = 2) -> None:
    """Save data to a JSON file.

    Parameters
    ----------
    data : Any
        Data to save (must be JSON serializable)
    file_path : str | Path
        Path to save the file
    indent : int | None, default=2
        JSON indentation level

    Raises
    ------
    ValueError
        If data is not JSON serializable
    """
    path = Path(file_path)
    logger.debug("Saving JSON data", file_path=str(path), indent=indent)

    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("w", encoding="utf-8") as f:
            json.dump(data, f, indent=indent, ensure_ascii=False)
        logger.debug("Successfully saved JSON", file_path=str(path))
    except (TypeError, ValueError) as e:
        raise ValueError(f"Data is not JSON serializable: {e}") from e


def load_json_file(file_path: str | Path) -> Any:
    """Load data from a JSON file.

    Parameters
    ----------
    file_path : str | Path
        Path to the JSON file

    Returns
    -------
    Any
        Loaded data

    Raises
    ------
    FileNotFoundError
        If file does not exist
    ValueError
        If file contains invalid JSON
    """
    path = Path(file_path)
    logger.debug("Loading JSON data", file_path=str(path))

    if not path.exists():
        raise FileNotFoundError(f"JSON file not found: {path}")

    try:
        with path.open("r", encoding="utf-8") as f:
            data = json.load(f)
        logger.debug("Successfully loaded JSON", file_path=str(path))
        return data
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON in file {path}: {e}") from e
