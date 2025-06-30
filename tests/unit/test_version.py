"""Tests for version module."""

from __future__ import annotations


def test_version_imports() -> None:
    """Test that version module imports work correctly."""
    from mkdocs_mermaid_to_image import _version

    # Test that version attributes exist and are strings
    assert hasattr(_version, "__version__")
    assert hasattr(_version, "version")
    assert isinstance(_version.__version__, str)
    assert isinstance(_version.version, str)
    assert _version.__version__ == _version.version

    # Test that version tuple attributes exist
    assert hasattr(_version, "__version_tuple__")
    assert hasattr(_version, "version_tuple")
    assert _version.__version_tuple__ == _version.version_tuple

    # Test __all__ exports
    assert hasattr(_version, "__all__")
    expected_exports = ["__version__", "__version_tuple__", "version", "version_tuple"]
    assert _version.__all__ == expected_exports
