from __future__ import annotations

from typing import TypedDict


class LogContext(TypedDict, total=False):
    """ログ出力に添える任意情報をまとめるTypedDict"""

    page_file: str | None
    block_index: int | None
    processing_step: str | None
    execution_time_ms: float | None
    error_type: str | None
