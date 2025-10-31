from __future__ import annotations

from typing import Any


class MermaidPreprocessorError(Exception):
    """Mermaidプラグイン全体の基底例外として文脈情報を保持する"""

    def __init__(self, message: str, **context_params: Any) -> None:
        """エラーメッセージと任意の文脈情報を保持する基本例外クラス"""
        details = {k: v for k, v in context_params.items() if v is not None}

        # Mermaidコードが長すぎる場合は頭出しのみ残して読みやすくする
        for key in ["mermaid_content", "mermaid_code"]:
            if (
                key in details
                and isinstance(details[key], str)
                and len(details[key]) > 200
            ):
                details[key] = details[key][:200] + "..."

        super().__init__(message)
        self.details = details


class MermaidCLIError(MermaidPreprocessorError):
    """Mermaid CLI実行時の異常を表す派生例外"""

    def __init__(
        self,
        message: str,
        command: str | None = None,
        return_code: int | None = None,
        stderr: str | None = None,
    ) -> None:
        """Mermaid CLI実行時の失敗情報を保持する例外"""
        super().__init__(
            message, command=command, return_code=return_code, stderr=stderr
        )


class MermaidConfigError(MermaidPreprocessorError):
    """設定値の異常を通知する派生例外"""

    def __init__(
        self,
        message: str,
        config_key: str | None = None,
        config_value: str | int | None = None,
        suggestion: str | None = None,
    ) -> None:
        """設定値の誤りを報告する例外"""
        super().__init__(
            message,
            config_key=config_key,
            config_value=config_value,
            suggestion=suggestion,
        )


class MermaidParsingError(MermaidPreprocessorError):
    """Mermaidコード解析時の失敗を通知する派生例外"""

    def __init__(
        self,
        message: str,
        source_file: str | None = None,
        line_number: int | None = None,
        mermaid_code: str | None = None,
    ) -> None:
        """Mermaidコードの解析段階で発生した問題を表す例外"""
        super().__init__(
            message,
            source_file=source_file,
            line_number=line_number,
            mermaid_code=mermaid_code,
        )


class MermaidFileError(MermaidPreprocessorError):
    """ファイルI/Oに関する問題を通知する派生例外"""

    def __init__(
        self,
        message: str,
        file_path: str | None = None,
        operation: str | None = None,
        suggestion: str | None = None,
    ) -> None:
        """ファイル入出力に関する失敗を表す例外"""
        super().__init__(
            message, file_path=file_path, operation=operation, suggestion=suggestion
        )


class MermaidValidationError(MermaidPreprocessorError):
    """入力検証の失敗を通知する派生例外"""

    def __init__(
        self,
        message: str,
        validation_type: str | None = None,
        invalid_value: str | None = None,
        expected_format: str | None = None,
    ) -> None:
        """入力値の検証に失敗した際の例外"""
        super().__init__(
            message,
            validation_type=validation_type,
            invalid_value=invalid_value,
            expected_format=expected_format,
        )


class MermaidImageError(MermaidPreprocessorError):
    """画像生成処理の失敗を通知する派生例外"""

    def __init__(
        self,
        message: str,
        image_format: str | None = None,
        image_path: str | None = None,
        mermaid_content: str | None = None,
        suggestion: str | None = None,
    ) -> None:
        """画像生成プロセスでの失敗を表す例外"""
        super().__init__(
            message,
            image_format=image_format,
            image_path=image_path,
            mermaid_content=mermaid_content,
            suggestion=suggestion,
        )
