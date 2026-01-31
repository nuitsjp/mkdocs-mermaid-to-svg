"""SVGゴールデンテスト（生成結果の完全一致比較）。"""

from __future__ import annotations

import os
from pathlib import Path

import pytest

from mkdocs_mermaid_to_svg.image_generator import MermaidImageGenerator

FIXTURES_DIR = Path(__file__).resolve().parent.parent / "fixtures"
# CI環境ではmmdc/Puppeteerのバージョン差異によりSVG出力が一致しないためスキップ
_CI = os.environ.get("CI", "") != ""
SKIP_GOLDEN = os.environ.get("SKIP_SVG_GOLDEN") == "1" or _CI
REGENERATE = os.environ.get("REGENERATE_SVG_GOLDENS") == "1"

pytestmark = pytest.mark.skipif(
    SKIP_GOLDEN,
    reason="CI環境またはSKIP_SVG_GOLDEN=1のためSVGゴールデンをスキップ",
)


def _read_fixture(name: str) -> str:
    return (FIXTURES_DIR / name).read_text(encoding="utf-8")


def _assert_svg_matches(expected_path: Path, actual_path: Path) -> None:
    actual_raw = actual_path.read_text(encoding="utf-8")
    if REGENERATE:
        # end-of-file-fixer対応: 末尾改行を付与して書き出す
        content = actual_raw.rstrip() + "\n"
        expected_path.write_text(content, encoding="utf-8")

    if not expected_path.exists():
        raise AssertionError(
            f"期待SVGが存在しません: {expected_path}. "
            "REGENERATE_SVG_GOLDENS=1 で生成してください。"
        )

    expected = expected_path.read_text(encoding="utf-8").rstrip()
    actual = actual_raw.rstrip()
    assert actual == expected


@pytest.mark.parametrize(
    ("source_name", "expected_name"),
    [
        ("sample_basic.mmd", "output_basic.svg"),
        ("sample_sequence.mmd", "output_sequence.svg"),
    ],
)
def test_svg_golden_matches(
    tmp_path: Path, source_name: str, expected_name: str
) -> None:
    config = {
        "mmdc_path": "mmdc",
        "renderer": "mmdc",
        "theme": "default",
        "error_on_fail": True,
        "log_level": "INFO",
    }

    code = _read_fixture(source_name)
    output_path = tmp_path / expected_name

    generator = MermaidImageGenerator(config)
    success = generator.generate(code, str(output_path), config)

    assert success is True
    _assert_svg_matches(FIXTURES_DIR / expected_name, output_path)
