"""Common type definitions for the project."""

from collections.abc import Mapping
from typing import Literal, TypedDict

# Status types
type ProcessorStatus = Literal["success", "error", "pending"]
type ValidationStatus = Literal["valid", "invalid", "skipped"]


# Common data structures
class ItemDict(TypedDict):
    """Typed dictionary for item data."""

    id: int
    name: str
    value: int


class ItemDictWithStatus(ItemDict):
    """Extended item dictionary with status."""

    status: ProcessorStatus
    processed: bool


class ConfigDict(TypedDict, total=False):
    """Typed dictionary for configuration data."""

    name: str
    max_items: int
    enable_validation: bool
    debug: bool
    timeout: float


class ErrorInfo(TypedDict):
    """Typed dictionary for error information."""

    code: str
    message: str
    details: Mapping[str, str | int | None]


# Result types
class ProcessingResult(TypedDict):
    """Result of a processing operation."""

    status: ProcessorStatus
    data: list[ItemDict]
    errors: list[ErrorInfo]
    processed_count: int
    skipped_count: int


class ValidationResult(TypedDict):
    """Result of a validation operation."""

    is_valid: bool
    errors: list[str]
    warnings: list[str]


# JSON types
type JSONPrimitive = str | int | float | bool | None
type JSONValue = JSONPrimitive | Mapping[str, "JSONValue"] | list["JSONValue"]
type JSONObject = Mapping[str, JSONValue]

# File operation types
type FileOperation = Literal["read", "write", "append", "delete"]
type FileFormat = Literal["json", "yaml", "csv", "txt"]

# Sorting and filtering
type SortOrder = Literal["asc", "desc"]
type FilterOperator = Literal["eq", "ne", "gt", "lt", "gte", "lte", "in", "contains"]


# Structured logging types
class LogContext(TypedDict, total=False):
    """Context information for structured logging."""

    user_id: str | int | None
    request_id: str | None
    session_id: str | None
    trace_id: str | None
    module: str | None
    function: str | None
    line_number: int | None
    extra: Mapping[str, JSONValue]


class LogEvent(TypedDict):
    """Structured log event."""

    event: str
    level: Literal["debug", "info", "warning", "error", "critical"]
    timestamp: str
    logger: str
    context: LogContext | None
    exception: str | None
    duration_ms: float | None


# Log formatting types
type LogFormat = Literal["json", "console", "plain"]
type LogLevel = Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
