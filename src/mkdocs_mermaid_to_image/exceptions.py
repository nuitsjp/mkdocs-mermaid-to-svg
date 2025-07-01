from __future__ import annotations

from typing import Any


class MermaidPreprocessorError(Exception):
    def __init__(self, message: str, **context_params: Any) -> None:
        """Initialize the exception with a message and optional context parameters.

        Args:
            message: Human-readable error message
            **context_params: Arbitrary context parameters for error details
        """
        details = {k: v for k, v in context_params.items() if v is not None}

        # Truncate long mermaid content for readability
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
    def __init__(
        self,
        message: str,
        command: str | None = None,
        return_code: int | None = None,
        stderr: str | None = None,
    ) -> None:
        """Initialize CLI error with command details.

        Args:
            message: Human-readable error message
            command: The command that failed
            return_code: Exit code of the failed command
            stderr: Standard error output from the command
        """
        super().__init__(
            message, command=command, return_code=return_code, stderr=stderr
        )


class MermaidConfigError(MermaidPreprocessorError):
    def __init__(
        self,
        message: str,
        config_key: str | None = None,
        config_value: str | int | None = None,
        suggestion: str | None = None,
    ) -> None:
        """Initialize configuration error with context.

        Args:
            message: Human-readable error message
            config_key: The configuration key that caused the error
            config_value: The invalid configuration value
            suggestion: Suggested fix for the configuration error
        """
        super().__init__(
            message,
            config_key=config_key,
            config_value=config_value,
            suggestion=suggestion,
        )


class MermaidParsingError(MermaidPreprocessorError):
    def __init__(
        self,
        message: str,
        source_file: str | None = None,
        line_number: int | None = None,
        mermaid_code: str | None = None,
    ) -> None:
        """Initialize parsing error with source context.

        Args:
            message: Human-readable error message
            source_file: The file where the parsing error occurred
            line_number: Line number where the error was found
            mermaid_code: The problematic Mermaid code block
        """
        super().__init__(
            message,
            source_file=source_file,
            line_number=line_number,
            mermaid_code=mermaid_code,
        )


class MermaidFileError(MermaidPreprocessorError):
    def __init__(
        self,
        message: str,
        file_path: str | None = None,
        operation: str | None = None,
        suggestion: str | None = None,
    ) -> None:
        """Initialize file operation error with context.

        Args:
            message: Human-readable error message
            file_path: Path to the file that caused the error
            operation: The file operation that failed (read, write, create, etc.)
            suggestion: Suggested fix for the file error
        """
        super().__init__(
            message, file_path=file_path, operation=operation, suggestion=suggestion
        )


class MermaidValidationError(MermaidPreprocessorError):
    def __init__(
        self,
        message: str,
        validation_type: str | None = None,
        invalid_value: str | None = None,
        expected_format: str | None = None,
    ) -> None:
        """Initialize validation error with context.

        Args:
            message: Human-readable error message
            validation_type: Type of validation that failed
            invalid_value: The value that failed validation
            expected_format: Expected format or pattern
        """
        super().__init__(
            message,
            validation_type=validation_type,
            invalid_value=invalid_value,
            expected_format=expected_format,
        )


class MermaidImageError(MermaidPreprocessorError):
    def __init__(
        self,
        message: str,
        image_format: str | None = None,
        image_path: str | None = None,
        mermaid_content: str | None = None,
        suggestion: str | None = None,
    ) -> None:
        """Initialize image generation error with context.

        Args:
            message: Human-readable error message
            image_format: Target image format (png, svg, etc.)
            image_path: Path where image should be generated
            mermaid_content: Mermaid diagram content that failed to render
            suggestion: Suggested fix for the image generation error
        """
        super().__init__(
            message,
            image_format=image_format,
            image_path=image_path,
            mermaid_content=mermaid_content,
            suggestion=suggestion,
        )
