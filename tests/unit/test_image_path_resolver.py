"""
ImagePathResolver のテスト
MermaidBlock から切り出したパス計算責務を検証します。

Python未経験者へのヒント：
- pathlib.Path でパス操作を行うと OS に依存しないテストが書けます。
- pytest の tmp_path fixture を使うと、一時ディレクトリが簡単に扱えます。
"""

from pathlib import Path

import pytest


@pytest.fixture
def resolver():
    from mkdocs_mermaid_to_svg.mermaid_block import ImagePathResolver

    return ImagePathResolver()


def test_resolver_uses_docs_dir_when_available(resolver, tmp_path):
    docs_dir = tmp_path / "docs"
    docs_dir.mkdir()
    output_dir = docs_dir / "assets" / "images"
    output_dir.mkdir(parents=True)

    image_path = output_dir / "diagram.svg"
    image_path.write_text("<svg></svg>", encoding="utf-8")

    result = resolver.to_markdown_path(
        image_path=image_path,
        page_file="guide/page.md",
        output_dir="assets/images",
        docs_dir=docs_dir,
    )

    assert result == "../assets/images/diagram.svg"


def test_resolver_falls_back_to_output_dir_when_outside_docs(resolver, tmp_path):
    docs_dir = tmp_path / "docs"
    docs_dir.mkdir()

    external_dir = tmp_path / "build"
    external_dir.mkdir()
    image_path = external_dir / "diagram.svg"
    image_path.write_text("<svg></svg>", encoding="utf-8")

    result = resolver.to_markdown_path(
        image_path=image_path,
        page_file="index.md",
        output_dir="assets/images",
        docs_dir=docs_dir,
    )

    # docs_dir から外れているため output_dir + ファイル名でリンクする
    assert result == "assets/images/diagram.svg"


def test_resolver_normalizes_output_dir_slashes(resolver, tmp_path):
    image_path = tmp_path / "assets" / "images" / "diagram.svg"
    image_path.parent.mkdir(parents=True)
    image_path.write_text("<svg></svg>", encoding="utf-8")

    result = resolver.to_markdown_path(
        image_path=image_path,
        page_file="page.md",
        output_dir="./assets/images/",
        docs_dir=None,
    )

    assert result == "assets/images/diagram.svg"
