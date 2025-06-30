"""Tests for version module."""

from __future__ import annotations


def test_version_imports() -> None:
    """Test that version module imports work correctly."""
    from mkdocs_mermaid_to_image import __version__

    # Test that version attribute exists and is a string
    assert isinstance(__version__, str)
    assert len(__version__) > 0
