from __future__ import annotations

from typing import TYPE_CHECKING, Literal, TypedDict

if TYPE_CHECKING:
    from collections.abc import Mapping

PluginStatus = Literal["success", "error", "pending"]
ValidationStatus = Literal["valid", "invalid", "skipped"]
ProcessingStatus = Literal["processing", "completed", "failed"]

MermaidTheme = Literal["default", "dark", "forest", "neutral"]


class PluginConfigDict(TypedDict, total=False):
    theme: MermaidTheme
    output_dir: str
    puppeteer_config: str
    css_file: str
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
    processing_step: str | None
    execution_time_ms: float | None
    error_type: str | None


CommandResult = tuple[int, str, str]

FileOperation = Literal["read", "write", "create", "delete"]

PluginHook = Literal["on_config", "on_page_markdown", "on_post_build"]


class ProcessingStats(TypedDict):
    total_blocks: int
    processed_blocks: int
    failed_blocks: int
    total_processing_time_ms: float
    average_processing_time_ms: float
