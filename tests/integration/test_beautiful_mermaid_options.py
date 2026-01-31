"""beautiful-mermaidレンダリングオプションの統合テスト（T036）

グローバルオプション設定、テーマ指定、ブロック単位の上書きが
プラグインのパイプライン全体を通じて正しく動作することを検証する。
"""

from __future__ import annotations

import sys
from typing import TYPE_CHECKING, Any
from unittest.mock import MagicMock, patch

if TYPE_CHECKING:
    from pathlib import Path

import pytest

from mkdocs_mermaid_to_svg.image_generator import (
    AutoRenderer,
    BatchRenderItem,
    BatchRenderResult,
    BeautifulMermaidRenderer,
)
from mkdocs_mermaid_to_svg.plugin import MermaidSvgConverterPlugin


def _make_plugin_with_options(
    tmp_path: Path,
    *,
    theme: str = "default",
    extra_config: dict[str, Any] | None = None,
) -> tuple[MermaidSvgConverterPlugin, MagicMock]:
    """beautiful-mermaidオプション付きプラグインを構築して返す"""
    with patch.object(sys, "argv", ["mkdocs", "build"]):
        plugin = MermaidSvgConverterPlugin()

    config: dict[str, Any] = {
        "output_dir": "assets/images",
        "error_on_fail": True,
        "theme": theme,
        "enabled_if_env": None,
    }
    if extra_config:
        config.update(extra_config)
    plugin.config = config

    # AutoRendererをモック構築
    mock_beautiful = MagicMock(spec=BeautifulMermaidRenderer)
    mock_beautiful.is_available.return_value = True

    mock_renderer = MagicMock(spec=AutoRenderer)
    mock_renderer.beautiful_renderer = mock_beautiful

    mock_processor = MagicMock()
    mock_processor.image_generator.renderer = mock_renderer

    plugin.processor = mock_processor
    plugin.files = MagicMock()
    plugin.generated_images = []
    plugin.batch_items = []

    return plugin, mock_beautiful


@pytest.mark.integration
class TestBeautifulMermaidOptionsIntegration:
    """beautiful-mermaidオプションのパイプライン統合テスト"""

    def test_グローバルオプションがバッチペイロードに含まれる(
        self, tmp_path: Path
    ) -> None:
        """グローバル設定のbeautiful-mermaidオプションがbatch_renderに渡される"""
        plugin, mock_beautiful = _make_plugin_with_options(
            tmp_path,
            extra_config={
                "beautiful_mermaid_bg": "#1a1b26",
                "beautiful_mermaid_fg": "#c0caf5",
            },
        )

        docs_dir = tmp_path / "docs"
        docs_dir.mkdir()
        output_dir = docs_dir / "assets" / "images"
        output_dir.mkdir(parents=True)

        item = BatchRenderItem(
            id="index_mermaid_0_abc12345",
            code="graph TD\n  A-->B",
            theme="default",
            output_path=str(output_dir / "index_mermaid_0_abc12345.svg"),
            page_file="index.md",
            options={"bg": "#1a1b26", "fg": "#c0caf5"},
        )
        plugin.batch_items = [item]

        mock_beautiful.batch_render.return_value = [
            BatchRenderResult(
                id="index_mermaid_0_abc12345",
                success=True,
                svg="<svg>styled</svg>",
            ),
        ]

        mock_config: dict[str, Any] = {
            "docs_dir": str(docs_dir),
            "site_dir": str(tmp_path / "site"),
        }
        plugin.on_post_build(config=mock_config)

        # batch_renderに渡されたアイテムにoptionsが含まれることを確認
        mock_beautiful.batch_render.assert_called_once()
        called_items = mock_beautiful.batch_render.call_args[0][0]
        assert called_items[0].options == {
            "bg": "#1a1b26",
            "fg": "#c0caf5",
        }

        # SVGファイルが正しく書き出される
        svg_path = output_dir / "index_mermaid_0_abc12345.svg"
        assert svg_path.read_text(encoding="utf-8") == "<svg>styled</svg>"

    def test_名前付きテーマがバッチペイロードに渡される(self, tmp_path: Path) -> None:
        """theme: tokyo-nightが設定された場合にbatch_renderに渡される"""
        plugin, mock_beautiful = _make_plugin_with_options(
            tmp_path,
            theme="tokyo-night",
        )

        docs_dir = tmp_path / "docs"
        docs_dir.mkdir()
        output_dir = docs_dir / "assets" / "images"
        output_dir.mkdir(parents=True)

        item = BatchRenderItem(
            id="page_mermaid_0_abc12345",
            code="graph TD\n  A-->B",
            theme="tokyo-night",
            output_path=str(output_dir / "page_mermaid_0_abc12345.svg"),
            page_file="page.md",
        )
        plugin.batch_items = [item]

        mock_beautiful.batch_render.return_value = [
            BatchRenderResult(
                id="page_mermaid_0_abc12345",
                success=True,
                svg="<svg>tokyo-night-themed</svg>",
            ),
        ]

        mock_config: dict[str, Any] = {
            "docs_dir": str(docs_dir),
            "site_dir": str(tmp_path / "site"),
        }
        plugin.on_post_build(config=mock_config)

        called_items = mock_beautiful.batch_render.call_args[0][0]
        assert called_items[0].theme == "tokyo-night"

    def test_ブロック単位のオプション上書きが個別に反映される(
        self, tmp_path: Path
    ) -> None:
        """各ブロックが異なるoptionsを持ち、バッチ処理で個別に反映される"""
        plugin, mock_beautiful = _make_plugin_with_options(
            tmp_path,
            extra_config={
                "beautiful_mermaid_bg": "#1a1b26",
            },
        )

        docs_dir = tmp_path / "docs"
        docs_dir.mkdir()
        output_dir = docs_dir / "assets" / "images"
        output_dir.mkdir(parents=True)

        # ブロック1: グローバルbgを上書き
        item1 = BatchRenderItem(
            id="page_mermaid_0_aaa",
            code="graph TD\n  A-->B",
            theme="default",
            output_path=str(output_dir / "page_mermaid_0_aaa.svg"),
            page_file="page.md",
            options={"bg": "#ff0000", "fg": "#ffffff"},
        )
        # ブロック2: グローバル設定のまま
        item2 = BatchRenderItem(
            id="page_mermaid_1_bbb",
            code="graph LR\n  C-->D",
            theme="default",
            output_path=str(output_dir / "page_mermaid_1_bbb.svg"),
            page_file="page.md",
            options={"bg": "#1a1b26"},
        )
        plugin.batch_items = [item1, item2]

        mock_beautiful.batch_render.return_value = [
            BatchRenderResult(
                id="page_mermaid_0_aaa",
                success=True,
                svg="<svg>red-bg</svg>",
            ),
            BatchRenderResult(
                id="page_mermaid_1_bbb",
                success=True,
                svg="<svg>default-bg</svg>",
            ),
        ]

        mock_config: dict[str, Any] = {
            "docs_dir": str(docs_dir),
            "site_dir": str(tmp_path / "site"),
        }
        plugin.on_post_build(config=mock_config)

        called_items = mock_beautiful.batch_render.call_args[0][0]
        # ブロック1: 上書きされたオプション
        assert called_items[0].options == {
            "bg": "#ff0000",
            "fg": "#ffffff",
        }
        # ブロック2: グローバル設定のまま
        assert called_items[1].options == {"bg": "#1a1b26"}

        # 両方のSVGファイルが書き出される
        svg1 = output_dir / "page_mermaid_0_aaa.svg"
        svg2 = output_dir / "page_mermaid_1_bbb.svg"
        assert svg1.read_text(encoding="utf-8") == "<svg>red-bg</svg>"
        assert svg2.read_text(encoding="utf-8") == "<svg>default-bg</svg>"

    def test_オプション未設定時は従来動作と同一(self, tmp_path: Path) -> None:
        """beautiful-mermaidオプション未設定時は既存動作と変わらない"""
        plugin, mock_beautiful = _make_plugin_with_options(tmp_path)

        docs_dir = tmp_path / "docs"
        docs_dir.mkdir()
        output_dir = docs_dir / "assets" / "images"
        output_dir.mkdir(parents=True)

        item = BatchRenderItem(
            id="page_mermaid_0_abc",
            code="graph TD\n  A-->B",
            theme="default",
            output_path=str(output_dir / "page_mermaid_0_abc.svg"),
            page_file="page.md",
        )
        plugin.batch_items = [item]

        mock_beautiful.batch_render.return_value = [
            BatchRenderResult(
                id="page_mermaid_0_abc",
                success=True,
                svg="<svg>plain</svg>",
            ),
        ]

        mock_config: dict[str, Any] = {
            "docs_dir": str(docs_dir),
            "site_dir": str(tmp_path / "site"),
        }
        plugin.on_post_build(config=mock_config)

        called_items = mock_beautiful.batch_render.call_args[0][0]
        # optionsはNone（未設定）
        assert called_items[0].options is None
