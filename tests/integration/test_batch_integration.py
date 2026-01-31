"""一括レンダリングの統合テスト（T021）

複数ページにまたがるMermaidダイアグラムの一括処理E2Eテスト。
"""

from __future__ import annotations

import sys
from typing import TYPE_CHECKING, Any
from unittest.mock import MagicMock, Mock, patch

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


def _make_plugin_with_auto_renderer(
    tmp_path: Path,
) -> tuple[MermaidSvgConverterPlugin, MagicMock]:
    """AutoRenderer付きプラグインを構築して返す"""
    with patch.object(sys, "argv", ["mkdocs", "build"]):
        plugin = MermaidSvgConverterPlugin()

    # 設定を注入
    plugin.config = {
        "output_dir": "assets/images",
        "error_on_fail": True,
        "theme": "default",
        "enabled_if_env": None,
    }

    # AutoRendererをモック構築
    mock_beautiful = MagicMock(spec=BeautifulMermaidRenderer)
    mock_beautiful.is_available.return_value = True

    mock_renderer = MagicMock(spec=AutoRenderer)
    mock_renderer.beautiful_renderer = mock_beautiful

    mock_processor = MagicMock()
    mock_processor.image_generator.renderer = mock_renderer

    plugin.processor = mock_processor

    # on_files相当の初期化
    plugin.files = MagicMock()
    plugin.generated_images = []
    plugin.batch_items = []

    return plugin, mock_beautiful


@pytest.mark.integration
class TestBatchIntegrationMultiPage:
    """複数ページにまたがる一括処理の統合テスト"""

    def test_複数ページの収集とバッチレンダリング(self, tmp_path: Path) -> None:
        """複数ページからbatch_itemsが収集され、on_post_buildで一括処理されること"""
        plugin, mock_beautiful = _make_plugin_with_auto_renderer(tmp_path)

        docs_dir = tmp_path / "docs"
        docs_dir.mkdir()
        output_dir = docs_dir / "assets" / "images"
        output_dir.mkdir(parents=True)

        # ページ1のダイアグラム収集をシミュレート
        item1 = BatchRenderItem(
            id="index_mermaid_0_abc12345",
            code="graph TD\n  A-->B",
            theme="default",
            output_path=str(output_dir / "index_mermaid_0_abc12345.svg"),
            page_file="index.md",
        )
        # ページ2のダイアグラム収集をシミュレート
        item2 = BatchRenderItem(
            id="guide_mermaid_0_def67890",
            code="sequenceDiagram\n  Alice->>Bob: Hello",
            theme="dark",
            output_path=str(output_dir / "guide_mermaid_0_def67890.svg"),
            page_file="guide.md",
        )
        plugin.batch_items = [item1, item2]

        # batch_renderの戻り値を設定
        mock_beautiful.batch_render.return_value = [
            BatchRenderResult(
                id="index_mermaid_0_abc12345",
                success=True,
                svg="<svg>page1</svg>",
            ),
            BatchRenderResult(
                id="guide_mermaid_0_def67890",
                success=True,
                svg="<svg>page2</svg>",
            ),
        ]

        # on_post_build実行
        mock_config: dict[str, Any] = {
            "docs_dir": str(docs_dir),
            "site_dir": str(tmp_path / "site"),
        }
        plugin.on_post_build(config=mock_config)

        # batch_renderが1回だけ呼ばれたことを確認
        mock_beautiful.batch_render.assert_called_once_with([item1, item2])

        # SVGファイルが書き出されたことを確認
        svg1 = output_dir / "index_mermaid_0_abc12345.svg"
        svg2 = output_dir / "guide_mermaid_0_def67890.svg"
        assert svg1.read_text(encoding="utf-8") == "<svg>page1</svg>"
        assert svg2.read_text(encoding="utf-8") == "<svg>page2</svg>"

        # generated_imagesに登録されたことを確認
        assert len(plugin.generated_images) == 2

    def test_空のbatch_itemsではNode起動しない(self, tmp_path: Path) -> None:
        """ダイアグラムが0件の場合、batch_renderは呼ばれないこと"""
        plugin, mock_beautiful = _make_plugin_with_auto_renderer(tmp_path)
        plugin.batch_items = []

        mock_config: dict[str, Any] = {
            "docs_dir": str(tmp_path),
            "site_dir": str(tmp_path / "site"),
        }
        plugin.on_post_build(config=mock_config)

        mock_beautiful.batch_render.assert_not_called()
        assert len(plugin.generated_images) == 0

    def test_部分失敗時にmmdcフォールバックが動作する(self, tmp_path: Path) -> None:
        """一括処理で失敗したダイアグラムがmmdcフォールバックで再処理されること"""
        plugin, mock_beautiful = _make_plugin_with_auto_renderer(tmp_path)

        docs_dir = tmp_path / "docs"
        docs_dir.mkdir()
        output_dir = docs_dir / "assets" / "images"
        output_dir.mkdir(parents=True)

        item_ok = BatchRenderItem(
            id="ok_diagram",
            code="graph TD\n  A-->B",
            theme="default",
            output_path=str(output_dir / "ok_diagram.svg"),
            page_file="page.md",
        )
        item_ng = BatchRenderItem(
            id="ng_diagram",
            code="pie\n  title Distribution",
            theme="default",
            output_path=str(output_dir / "ng_diagram.svg"),
            page_file="page.md",
        )
        plugin.batch_items = [item_ok, item_ng]

        # batch_renderは部分成功を返す
        mock_beautiful.batch_render.return_value = [
            BatchRenderResult(id="ok_diagram", success=True, svg="<svg>ok</svg>"),
            BatchRenderResult(id="ng_diagram", success=False, error="Parse error"),
        ]

        # mmdcフォールバック用のモック
        mock_mmdc = MagicMock()
        mock_mmdc.render_svg.return_value = True
        renderer = plugin.processor.image_generator.renderer
        renderer.mmdc_renderer = mock_mmdc

        mock_config: dict[str, Any] = {
            "docs_dir": str(docs_dir),
            "site_dir": str(tmp_path / "site"),
        }
        plugin.on_post_build(config=mock_config)

        # 成功分はSVGが書き出される
        svg_ok = output_dir / "ok_diagram.svg"
        assert svg_ok.read_text(encoding="utf-8") == "<svg>ok</svg>"

        # 失敗分はmmdcフォールバックで処理される
        mock_mmdc.render_svg.assert_called_once()
        call_args = mock_mmdc.render_svg.call_args
        assert call_args[0][0] == "pie\n  title Distribution"  # code
        assert str(output_dir / "ng_diagram.svg") in call_args[0][1]  # output_path

    def test_serve時はbatch処理がスキップされる(self, tmp_path: Path) -> None:
        """serve時はon_page_markdownが元Markdownをそのまま返すこと"""
        with patch.object(sys, "argv", ["mkdocs", "serve"]):
            plugin = MermaidSvgConverterPlugin()

        plugin.config = {
            "output_dir": "assets/images",
            "error_on_fail": False,
            "enabled_if_env": None,
        }
        plugin.processor = MagicMock()

        mock_page = Mock()
        mock_page.file.src_path = "test.md"
        mock_config: dict[str, Any] = {"docs_dir": str(tmp_path)}

        markdown = "# Test\n\n```mermaid\ngraph TD\n  A-->B\n```\n"
        result = plugin.on_page_markdown(
            markdown, page=mock_page, config=mock_config, files=[]
        )

        assert result == markdown
        plugin.processor.process_page.assert_not_called()
