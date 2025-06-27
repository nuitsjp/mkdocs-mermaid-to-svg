from __future__ import annotations

from typing import TYPE_CHECKING, Literal, TypedDict

if TYPE_CHECKING:
    from collections.abc import Mapping

PluginStatus = Literal["success", "error", "pending"]
ValidationStatus = Literal["valid", "invalid", "skipped"]
ProcessingStatus = Literal["processing", "completed", "failed"]

ImageFormat = Literal["png", "svg"]
MermaidTheme = Literal["default", "dark", "forest", "neutral"]


class PluginConfigDict(TypedDict, total=False):
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
    code: str
    language: str
    start_line: int
    end_line: int
    block_index: int


class MermaidBlockWithMetadata(MermaidBlockDict):
    image_filename: str
    image_path: str
    processed: bool
    processing_status: ProcessingStatus


class ProcessingResultDict(TypedDict):
    status: PluginStatus
    processed_blocks: list[MermaidBlockWithMetadata]
    errors: list[str]
    warnings: list[str]
    processing_time_ms: float


class ValidationResultDict(TypedDict):
    is_valid: bool
    errors: list[str]
    warnings: list[str]
    validation_status: ValidationStatus


class ImageGenerationResult(TypedDict):
    success: bool
    image_path: str
    error_message: str | None
    generation_time_ms: float


class ErrorInfo(TypedDict):
    code: str
    message: str
    details: Mapping[str, str | int | None]
    source_file: str | None
    line_number: int | None


class LogContext(TypedDict, total=False):
    page_file: str | None
    block_index: int | None
    image_format: ImageFormat | None
    processing_step: str | None
    execution_time_ms: float | None
    error_type: str | None


CommandResult = tuple[int, str, str]

FileOperation = Literal["read", "write", "create", "delete"]
CacheOperation = Literal["hit", "miss", "invalidate", "store"]

PluginHook = Literal["on_config", "on_page_markdown", "on_post_build"]


class ProcessingStats(TypedDict):
    total_blocks: int
    processed_blocks: int
    failed_blocks: int
    cache_hits: int
    cache_misses: int
    total_processing_time_ms: float
    average_processing_time_ms: float


class CacheInfo(TypedDict):
    cache_key: str
    cache_hit: bool
    cache_timestamp: str
    file_hash: str
