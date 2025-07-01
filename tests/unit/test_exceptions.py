"""Tests for exception classes."""

from __future__ import annotations

import pytest

from mkdocs_mermaid_to_image.exceptions import (
    MermaidCLIError,
    MermaidConfigError,
    MermaidParsingError,
    MermaidPreprocessorError,
)


class TestMermaidParsingError:
    """Test MermaidParsingError exception."""

    def test_mermaid_parsing_error_with_all_details(self) -> None:
        """Test MermaidParsingError with all detail parameters."""
        source_file = "test.md"
        line_number = 10
        mermaid_code = "graph TD\n    A --> B"

        error = MermaidParsingError(
            "Parse error occurred",
            source_file=source_file,
            line_number=line_number,
            mermaid_code=mermaid_code,
        )

        assert str(error) == "Parse error occurred"
        assert error.details["source_file"] == source_file
        assert error.details["line_number"] == line_number
        assert error.details["mermaid_code"] == mermaid_code

    def test_mermaid_parsing_error_with_long_code(self) -> None:
        """Test MermaidParsingError with code longer than 200 characters."""
        source_file = "test.md"
        line_number = 5
        # Create a long mermaid code string (over 200 chars)
        mermaid_code = "graph TD\n" + "    A --> B\n" * 20  # Much longer than 200 chars

        error = MermaidParsingError(
            "Parse error occurred",
            source_file=source_file,
            line_number=line_number,
            mermaid_code=mermaid_code,
        )

        # Should be truncated with "..." appended
        assert error.details["mermaid_code"].endswith("...")
        assert len(error.details["mermaid_code"]) == 203  # 200 + "..."

    def test_mermaid_parsing_error_with_empty_code(self) -> None:
        """Test MermaidParsingError with empty mermaid code."""
        error = MermaidParsingError(
            "Parse error occurred",
            source_file="test.md",
            line_number=1,
            mermaid_code="",
        )

        assert error.details["mermaid_code"] == ""

    def test_mermaid_parsing_error_with_none_code(self) -> None:
        """Test MermaidParsingError with None mermaid code."""
        error = MermaidParsingError(
            "Parse error occurred",
            source_file="test.md",
            line_number=1,
            mermaid_code=None,
        )

        # None values are now filtered out
        assert "mermaid_code" not in error.details
        assert error.details["source_file"] == "test.md"
        assert error.details["line_number"] == 1

    def test_mermaid_parsing_error_with_exactly_200_chars(self) -> None:
        """Test MermaidParsingError with exactly 200 character code."""
        mermaid_code = "A" * 200  # Exactly 200 characters

        error = MermaidParsingError(
            "Parse error occurred",
            source_file="test.md",
            line_number=1,
            mermaid_code=mermaid_code,
        )

        # Should not be truncated
        assert error.details["mermaid_code"] == mermaid_code
        assert not error.details["mermaid_code"].endswith("...")


class TestOtherExceptions:
    """Test other exception classes."""

    def test_mermaid_preprocessor_error(self) -> None:
        """Test MermaidPreprocessorError creation."""
        error = MermaidPreprocessorError("Preprocessor failed")
        assert str(error) == "Preprocessor failed"
        assert error.details == {}

    def test_mermaid_cli_error(self) -> None:
        """Test MermaidCLIError creation."""
        error = MermaidCLIError("CLI command failed")
        assert str(error) == "CLI command failed"
        # None values are now filtered out
        assert error.details == {}

    def test_mermaid_config_error(self) -> None:
        """Test MermaidConfigError creation."""
        error = MermaidConfigError("Configuration invalid")
        assert str(error) == "Configuration invalid"
        # None values are now filtered out
        assert error.details == {}

    def test_exception_inheritance(self) -> None:
        """Test that all exceptions inherit from MermaidPreprocessorError."""
        assert issubclass(MermaidParsingError, MermaidPreprocessorError)
        assert issubclass(MermaidCLIError, MermaidPreprocessorError)
        assert issubclass(MermaidConfigError, MermaidPreprocessorError)

        # Test that they can be caught as base exception
        try:
            raise MermaidParsingError("test", "file.md", 1, "code")
        except MermaidPreprocessorError:
            pass  # Should be caught
        else:
            pytest.fail(
                "MermaidParsingError should be caught as MermaidPreprocessorError"
            )
