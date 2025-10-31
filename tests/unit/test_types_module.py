from typing import Any

from mkdocs_mermaid_to_svg import types as types_module


def _is_typed_dict(candidate: Any) -> bool:
    return isinstance(candidate, type) and getattr(candidate, "__total__", None) is not None


def test_types_module_exposes_only_log_context_typed_dict() -> None:
    typed_dict_names = [
        name
        for name, value in vars(types_module).items()
        if _is_typed_dict(value)
    ]

    assert typed_dict_names == ["LogContext"]
