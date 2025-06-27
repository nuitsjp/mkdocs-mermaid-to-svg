"""Type definitions for the MkDocs Mermaid to Image plugin."""

from __future__ import annotations

from typing import TYPE_CHECKING, Literal, TypedDict

if TYPE_CHECKING:
    from collections.abc import Mapping

# Plugin status types
PluginStatus = Literal["success", "error", "pending"]
ValidationStatus = Literal["valid", "invalid", "skipped"]
ProcessingStatus = Literal["processing", "completed", "failed"]

# Image format and configuration types
ImageFormat = Literal["png", "svg"]
MermaidTheme = Literal["default", "dark", "forest", "neutral"]


# Configuration structures
class PluginConfigDict(TypedDict, total=False):
    """Plugin configuration dictionary with optional fields."""

    image_format: ImageFormat
    theme: MermaidTheme
    cache_enabled: bool
    output_dir: str
    image_width: int
    image_height: int
    background_color: str
    puppeteer_config: str
    css_file: str
    scale: float
    timeout: int


class MermaidBlockDict(TypedDict):
    """Structure representing a Mermaid code block."""

    code: str
    language: str
    start_line: int
    end_line: int
    block_index: int


class MermaidBlockWithMetadata(MermaidBlockDict):
    """Extended Mermaid block with processing metadata."""

    image_filename: str
    image_path: str
    processed: bool
    processing_status: ProcessingStatus


class ProcessingResultDict(TypedDict):
    """Result of a Mermaid processing operation."""

    status: PluginStatus
    processed_blocks: list[MermaidBlockWithMetadata]
    errors: list[str]
    warnings: list[str]
    processing_time_ms: float


class ValidationResultDict(TypedDict):
    """Result of a validation operation."""

    is_valid: bool
    errors: list[str]
    warnings: list[str]
    validation_status: ValidationStatus


class ImageGenerationResult(TypedDict):
    """Result of image generation operation."""

    success: bool
    image_path: str
    error_message: str | None
    generation_time_ms: float


# Error information types
class ErrorInfo(TypedDict):
    """Structured error information."""

    code: str
    message: str
    details: Mapping[str, str | int | None]
    source_file: str | None
    line_number: int | None


# Log context types for structured logging
class LogContext(TypedDict, total=False):
    """Context information for structured logging."""

    page_file: str | None
    block_index: int | None
    image_format: ImageFormat | None
    processing_step: str | None
    execution_time_ms: float | None
    error_type: str | None


# Command execution types
CommandResult = tuple[int, str, str]  # (return_code, stdout, stderr)

# File operation types
FileOperation = Literal["read", "write", "create", "delete"]
CacheOperation = Literal["hit", "miss", "invalidate", "store"]

# Plugin lifecycle types
PluginHook = Literal["on_config", "on_page_markdown", "on_post_build"]


# Statistics and metrics
class ProcessingStats(TypedDict):
    """Statistics from processing operation."""

    total_blocks: int
    processed_blocks: int
    failed_blocks: int
    cache_hits: int
    cache_misses: int
    total_processing_time_ms: float
    average_processing_time_ms: float


class CacheInfo(TypedDict):
    """Cache information for a processed block."""

    cache_key: str
    cache_hit: bool
    cache_timestamp: str
    file_hash: str
