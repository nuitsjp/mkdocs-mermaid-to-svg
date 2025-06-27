class MermaidPreprocessorError(Exception):
    def __init__(
        self, message: str, details: dict[str, str | int | None] | None = None
    ) -> None:
        """Initialize the exception with a message and optional details.

        Args:
            message: Human-readable error message
            details: Optional dictionary with additional error context
        """
        super().__init__(message)
        self.details = details or {}


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
        details = {
            "command": command,
            "return_code": return_code,
            "stderr": stderr,
        }
        super().__init__(message, details)


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
        details = {
            "config_key": config_key,
            "config_value": config_value,
            "suggestion": suggestion,
        }
        super().__init__(message, details)


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
        details = {
            "source_file": source_file,
            "line_number": line_number,
            "mermaid_code": mermaid_code[:200] + "..."
            if mermaid_code and len(mermaid_code) > 200
            else mermaid_code,
        }
        super().__init__(message, details)
