"""
MermaidProcessorクラスのテスト
このファイルでは、MermaidProcessorクラスの動作を検証します。

Python未経験者へのヒント：
- pytestを使ってテストを書いています。
- Mockやpatchで外部依存を疑似的に置き換えています。
- assert文で「期待する結果」かどうかを検証します。
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import TYPE_CHECKING
from unittest.mock import Mock, patch

import pytest

from mkdocs_mermaid_to_svg.exceptions import MermaidCLIError
from mkdocs_mermaid_to_svg.mermaid_block import MermaidBlock

if TYPE_CHECKING:
    from mkdocs_mermaid_to_svg.image_generator import BatchRenderItem
from mkdocs_mermaid_to_svg.processor import MermaidProcessor


class TestMermaidProcessor:
    """MermaidProcessorクラスのテストクラス"""

    @pytest.fixture
    def basic_config(self):
        """テスト用の基本設定を返すfixture"""
        return {
            "mmdc_path": "mmdc",
            "renderer": "mmdc",
            "output_dir": "assets/images",
            "image_format": "png",
            "theme": "default",
            "background_color": "white",
            "width": 800,
            "height": 600,
            "scale": 1.0,
            "css_file": None,
            "puppeteer_config": None,
            "mermaid_config": None,
            "cache_enabled": True,
            "cache_dir": ".mermaid_cache",
            "preserve_original": False,
            "error_on_fail": False,
            "log_level": "INFO",
        }

    @patch("mkdocs_mermaid_to_svg.image_generator.is_command_available")
    def test_processor_initialization(self, mock_command_available, basic_config):
        """MermaidProcessorの初期化が正しく行われるかテスト"""
        mock_command_available.return_value = True
        processor = MermaidProcessor(basic_config)
        assert processor.config == basic_config
        assert processor.logger is not None
        assert processor.markdown_processor is not None
        assert processor.image_generator is not None

    @patch("mkdocs_mermaid_to_svg.image_generator.is_command_available")
    def test_processor_initialization_missing_cli(
        self, mock_command_available, basic_config
    ):
        """Mermaid CLIが見つからない場合に例外が発生するかテスト"""
        # キャッシュをクリアして独立したテストにする
        from mkdocs_mermaid_to_svg.image_generator import MermaidImageGenerator

        MermaidImageGenerator.clear_command_cache()
        mock_command_available.return_value = False
        with pytest.raises(MermaidCLIError):
            MermaidProcessor(basic_config)

    @patch("mkdocs_mermaid_to_svg.image_generator.is_command_available")
    def test_process_page_with_blocks(self, mock_command_available, basic_config):
        """Mermaidブロックがある場合のページ処理をテスト"""
        mock_command_available.return_value = True
        processor = MermaidProcessor(basic_config)

        # MermaidBlockのモックを作成
        mock_block = Mock(spec=MermaidBlock)
        mock_block.get_filename.return_value = "test_0_abc123.png"
        mock_block.generate_image.return_value = True

        # markdown_processorのメソッドをモック化
        processor.markdown_processor.extract_mermaid_blocks = Mock(
            return_value=[mock_block]
        )
        processor.markdown_processor.replace_blocks_with_images = Mock(
            return_value="![Mermaid](test.png)"
        )

        markdown = """# Test

```mermaid
graph TD
    A --> B
```
"""
        # ページ処理を実行
        result_content, result_paths = processor.process_page(
            "test.md", markdown, "/output"
        )

        assert result_content == "![Mermaid](test.png)"
        assert len(result_paths) == 1
        mock_block.generate_image.assert_called_once()
        mock_block.get_filename.assert_called_once_with("test.md", 0, "svg")

    @patch("mkdocs_mermaid_to_svg.image_generator.is_command_available")
    def test_process_page_assigns_image_id_when_enabled(
        self, mock_command_available, basic_config
    ):
        """image_id_enabled=True のときに set_render_context が呼ばれることをテスト"""
        mock_command_available.return_value = True
        basic_config["image_id_enabled"] = True
        processor = MermaidProcessor(basic_config)

        mock_block = Mock(spec=MermaidBlock)
        mock_block.get_filename.return_value = "guide_0_abc123.svg"
        mock_block.generate_image.return_value = True
        mock_block.attributes = {}
        mock_block.set_render_context = Mock()

        processor.markdown_processor.extract_mermaid_blocks = Mock(
            return_value=[mock_block]
        )
        processor.markdown_processor.replace_blocks_with_images = Mock(
            return_value="![Mermaid](test.png){#mermaid-diagram-page-1}"
        )

        markdown = "```mermaid\ngraph TD\n  A --> B\n```"

        processor.process_page(
            "docs/guide/page.md", markdown, "/output", docs_dir="docs"
        )

        mock_block.set_render_context.assert_called_once_with(
            image_id="mermaid-diagram-page-1"
        )

    @patch("mkdocs_mermaid_to_svg.image_generator.is_command_available")
    def test_process_page_respects_custom_image_id_prefix(
        self, mock_command_available, basic_config
    ):
        """image_id_prefix がカスタム指定された場合の動作をテスト"""
        mock_command_available.return_value = True
        basic_config["image_id_enabled"] = True
        basic_config["image_id_prefix"] = "diagram"
        processor = MermaidProcessor(basic_config)

        mock_block = Mock(spec=MermaidBlock)
        mock_block.get_filename.return_value = "guide_1_def456.svg"
        mock_block.generate_image.return_value = True
        mock_block.attributes = {}
        mock_block.set_render_context = Mock()

        processor.markdown_processor.extract_mermaid_blocks = Mock(
            return_value=[mock_block]
        )
        processor.markdown_processor.replace_blocks_with_images = Mock(
            return_value="![Mermaid](test.png){#diagram-page-1}"
        )

        processor.process_page(
            "docs/guide/page.md",
            "```mermaid\ngraph TD\n  A --> B\n```",
            "/output",
        )

        mock_block.set_render_context.assert_called_once_with(image_id="diagram-page-1")

    @patch("mkdocs_mermaid_to_svg.image_generator.is_command_available")
    def test_process_page_prefers_block_defined_id(
        self, mock_command_available, basic_config
    ):
        """Mermaidコードブロックに id 属性があればそれを優先することをテスト"""
        mock_command_available.return_value = True
        basic_config["image_id_enabled"] = True
        processor = MermaidProcessor(basic_config)

        mock_block = Mock(spec=MermaidBlock)
        mock_block.get_filename.return_value = "guide_2_ghi789.svg"
        mock_block.generate_image.return_value = True
        mock_block.attributes = {"id": "Custom Diagram!"}
        mock_block.set_render_context = Mock()

        processor.markdown_processor.extract_mermaid_blocks = Mock(
            return_value=[mock_block]
        )
        processor.markdown_processor.replace_blocks_with_images = Mock(
            return_value="![Mermaid](test.png){#custom-diagram}"
        )

        processor.process_page(
            "docs/guide/page.md",
            "```mermaid\ngraph TD\n  A --> B\n```",
            "/output",
        )

        mock_block.set_render_context.assert_called_once_with(image_id="custom-diagram")

    @pytest.mark.skipif(os.name == "nt", reason="POSIX環境のみ対象")
    @patch("mkdocs_mermaid_to_svg.image_generator.is_command_available")
    def test_process_page_injects_docs_dir_posix(
        self, mock_command_available, basic_config
    ):
        """process_page 呼び出し時に docs_dir を渡しているかをテスト（POSIX）"""
        mock_command_available.return_value = True
        processor = MermaidProcessor(basic_config)

        mock_block = Mock(spec=MermaidBlock)
        mock_block.get_filename.return_value = "test_0_abc123.png"
        mock_block.generate_image.return_value = True

        processor.markdown_processor.extract_mermaid_blocks = Mock(
            return_value=[mock_block]
        )

        replacement = "![Mermaid](../assets/images/test.svg)"
        processor.markdown_processor.replace_blocks_with_images = Mock(
            return_value=replacement
        )

        markdown = """```mermaid
graph TD
    A --> B
```"""

        docs_dir = "/home/user/project/docs"
        output_dir = "/home/user/project/docs/assets/images"

        result_content, result_paths = processor.process_page(
            "guide/page.md",
            markdown,
            output_dir,
            docs_dir=docs_dir,
        )

        assert result_content == replacement
        assert result_paths == [f"{output_dir}/test_0_abc123.png"]
        processor.markdown_processor.replace_blocks_with_images.assert_called_once()
        _, kwargs = processor.markdown_processor.replace_blocks_with_images.call_args
        assert kwargs["docs_dir"] == str(Path(docs_dir))

    @pytest.mark.skipif(os.name != "nt", reason="Windows環境のみ対象")
    @patch("mkdocs_mermaid_to_svg.image_generator.is_command_available")
    def test_process_page_injects_docs_dir_windows(
        self, mock_command_available, basic_config
    ):
        """process_page 呼び出し時に docs_dir を渡しているかをテスト（Windows）"""
        mock_command_available.return_value = True
        processor = MermaidProcessor(basic_config)

        mock_block = Mock(spec=MermaidBlock)
        mock_block.get_filename.return_value = "test_0_abc123.png"
        mock_block.generate_image.return_value = True

        processor.markdown_processor.extract_mermaid_blocks = Mock(
            return_value=[mock_block]
        )

        replacement = "![Mermaid](../assets/images/test.svg)"
        processor.markdown_processor.replace_blocks_with_images = Mock(
            return_value=replacement
        )

        markdown = """```mermaid
graph TD
    A --> B
```"""

        docs_dir = "/home/user/project/docs"
        output_dir = "/home/user/project/docs/assets/images"

        result_content, result_paths = processor.process_page(
            "guide/page.md",
            markdown,
            output_dir,
            docs_dir=docs_dir,
        )

        expected_path = str(Path(output_dir) / "test_0_abc123.png")
        assert result_content == replacement
        assert result_paths == [expected_path]
        processor.markdown_processor.replace_blocks_with_images.assert_called_once()
        _, kwargs = processor.markdown_processor.replace_blocks_with_images.call_args
        assert kwargs["docs_dir"] == str(Path(docs_dir))

    @patch("mkdocs_mermaid_to_svg.image_generator.is_command_available")
    def test_process_page_no_blocks(self, mock_command_available, basic_config):
        """Mermaidブロックがない場合は元の内容が返るかテスト"""
        mock_command_available.return_value = True
        processor = MermaidProcessor(basic_config)

        # ブロック抽出が空リストを返すようにモック
        processor.markdown_processor.extract_mermaid_blocks = Mock(return_value=[])

        markdown = """# Test

```python
print("Hello")
```
"""
        result_content, result_paths = processor.process_page(
            "test.md", markdown, "/output"
        )

        assert result_content == markdown
        assert len(result_paths) == 0

    @patch("mkdocs_mermaid_to_svg.image_generator.is_command_available")
    def test_process_page_with_generation_failure(
        self, mock_command_available, basic_config
    ):
        """画像生成が失敗した場合の挙動をテスト"""
        mock_command_available.return_value = True
        processor = MermaidProcessor(basic_config)

        # 画像生成が失敗するブロックをモック
        mock_block = Mock(spec=MermaidBlock)
        mock_block.get_filename.return_value = "test_0_abc123.png"
        mock_block.generate_image.return_value = False  # 生成失敗

        processor.markdown_processor.extract_mermaid_blocks = Mock(
            return_value=[mock_block]
        )

        markdown = """```mermaid
graph TD
    A --> B
```"""
        result_content, result_paths = processor.process_page(
            "test.md", markdown, "/output"
        )

        # error_on_fail=Falseなので元の内容が返る
        assert result_content == markdown
        assert len(result_paths) == 0

    @patch("mkdocs_mermaid_to_svg.image_generator.is_command_available")
    def test_process_page_with_generation_failure_error_on_fail(
        self, mock_command_available, basic_config
    ):
        """error_on_fail=Trueで画像生成が失敗した場合に例外が発生するかテスト"""
        mock_command_available.return_value = True
        # error_on_fail=Trueに設定
        config_with_error_on_fail = basic_config.copy()
        config_with_error_on_fail["error_on_fail"] = True
        processor = MermaidProcessor(config_with_error_on_fail)

        # 画像生成が失敗するブロックをモック
        mock_block = Mock(spec=MermaidBlock)
        mock_block.get_filename.return_value = "test_0_abc123.png"
        mock_block.generate_image.return_value = False  # 生成失敗

        processor.markdown_processor.extract_mermaid_blocks = Mock(
            return_value=[mock_block]
        )

        markdown = """```mermaid
graph TD
    A --> B
```"""

        # MermaidImageError例外が発生することを期待
        from mkdocs_mermaid_to_svg.exceptions import MermaidImageError

        with pytest.raises(MermaidImageError) as exc_info:
            processor.process_page("test.md", markdown, "/output")

        assert "Image generation failed for block 0 in test.md" in str(exc_info.value)

    @patch("mkdocs_mermaid_to_svg.image_generator.is_command_available")
    def test_process_page_with_filesystem_error_error_on_fail(
        self, mock_command_available, basic_config
    ):
        """error_on_fail=Trueでファイルシステムエラーが発生した場合に例外が発生するかテスト"""
        mock_command_available.return_value = True
        # error_on_fail=Trueに設定
        config_with_error_on_fail = basic_config.copy()
        config_with_error_on_fail["error_on_fail"] = True
        processor = MermaidProcessor(config_with_error_on_fail)

        # ファイルシステムエラーが発生するブロックをモック
        mock_block = Mock(spec=MermaidBlock)
        mock_block.get_filename.return_value = "test_0_abc123.png"
        mock_block.generate_image.side_effect = PermissionError("Permission denied")

        processor.markdown_processor.extract_mermaid_blocks = Mock(
            return_value=[mock_block]
        )

        markdown = """```mermaid
graph TD
    A --> B
```"""

        # MermaidFileError例外が発生することを期待
        from mkdocs_mermaid_to_svg.exceptions import MermaidFileError

        with pytest.raises(MermaidFileError) as exc_info:
            processor.process_page("test.md", markdown, "/output")

        assert "File system error processing block 0 in test.md" in str(exc_info.value)
        assert "Permission denied" in str(exc_info.value)

    @patch("mkdocs_mermaid_to_svg.image_generator.is_command_available")
    def test_process_page_with_filesystem_error_no_error_on_fail(
        self, mock_command_available, basic_config
    ):
        """error_on_fail=Falseでファイルシステムエラーが発生した場合はcontinueするかテスト"""
        mock_command_available.return_value = True
        # error_on_fail=Falseに設定（デフォルト）
        processor = MermaidProcessor(basic_config)

        # ファイルシステムエラーが発生するブロックをモック
        mock_block = Mock(spec=MermaidBlock)
        mock_block.get_filename.return_value = "test_0_abc123.png"
        mock_block.generate_image.side_effect = FileNotFoundError("File not found")

        processor.markdown_processor.extract_mermaid_blocks = Mock(
            return_value=[mock_block]
        )

        markdown = """```mermaid
graph TD
    A --> B
```"""

        # 例外は発生せず、元のmarkdownが返る
        result_content, result_paths = processor.process_page(
            "test.md", markdown, "/output"
        )

        assert result_content == markdown
        assert len(result_paths) == 0

    @patch("mkdocs_mermaid_to_svg.image_generator.is_command_available")
    def test_process_page_with_unexpected_error_error_on_fail(
        self, mock_command_available, basic_config
    ):
        """error_on_fail=Trueで予期しないエラーが発生した場合に例外が発生するかテスト"""
        mock_command_available.return_value = True
        # error_on_fail=Trueに設定
        config_with_error_on_fail = basic_config.copy()
        config_with_error_on_fail["error_on_fail"] = True
        processor = MermaidProcessor(config_with_error_on_fail)

        # 予期しないエラーが発生するブロックをモック
        mock_block = Mock(spec=MermaidBlock)
        mock_block.get_filename.return_value = "test_0_abc123.png"
        mock_block.generate_image.side_effect = RuntimeError("Unexpected error")

        processor.markdown_processor.extract_mermaid_blocks = Mock(
            return_value=[mock_block]
        )

        markdown = """```mermaid
graph TD
    A --> B
```"""

        # MermaidPreprocessorError例外が発生することを期待
        from mkdocs_mermaid_to_svg.exceptions import MermaidPreprocessorError

        with pytest.raises(MermaidPreprocessorError) as exc_info:
            processor.process_page("test.md", markdown, "/output")

        assert "Unexpected error processing block 0 in test.md" in str(exc_info.value)
        assert "Unexpected error" in str(exc_info.value)

    @patch("mkdocs_mermaid_to_svg.image_generator.is_command_available")
    def test_process_page_with_unexpected_error_no_error_on_fail(
        self, mock_command_available, basic_config
    ):
        """error_on_fail=Falseで予期しないエラーが発生した場合はcontinueするかテスト"""
        mock_command_available.return_value = True
        # error_on_fail=Falseに設定（デフォルト）
        processor = MermaidProcessor(basic_config)

        # 予期しないエラーが発生するブロックをモック
        mock_block = Mock(spec=MermaidBlock)
        mock_block.get_filename.return_value = "test_0_abc123.png"
        mock_block.generate_image.side_effect = ValueError("Unexpected value error")

        processor.markdown_processor.extract_mermaid_blocks = Mock(
            return_value=[mock_block]
        )

        markdown = """```mermaid
graph TD
    A --> B
```"""

        # 例外は発生せず、元のmarkdownが返る
        result_content, result_paths = processor.process_page(
            "test.md", markdown, "/output"
        )

        assert result_content == markdown
        assert len(result_paths) == 0


# ---------------------------------------------------------------------------
# T008: プロセッサの収集モードの単体テスト（batch_items指定時の動作）
# ---------------------------------------------------------------------------


class TestProcessorCollectMode:
    """プロセッサの収集モード（batch_items指定時）のテスト（T008）"""

    @pytest.fixture
    def auto_config(self):
        """auto rendererを使うテスト用設定"""
        return {
            "mmdc_path": "mmdc",
            "renderer": "auto",
            "output_dir": "assets/images",
            "image_format": "png",
            "theme": "default",
            "background_color": "white",
            "width": 800,
            "height": 600,
            "scale": 1.0,
            "css_file": None,
            "puppeteer_config": None,
            "mermaid_config": None,
            "cache_enabled": True,
            "cache_dir": ".mermaid_cache",
            "preserve_original": False,
            "error_on_fail": False,
            "log_level": "INFO",
        }

    @patch("mkdocs_mermaid_to_svg.image_generator.is_command_available")
    def test_beautiful対応ブロックがBatchRenderItemとして収集される(
        self, mock_command_available, auto_config, tmp_path
    ):
        """beautiful-mermaid対応ブロック（flowchart）がbatch_itemsに追加される"""
        mock_command_available.return_value = True
        processor = MermaidProcessor(auto_config)

        # flowchartブロック（beautiful-mermaid対応）
        mock_block = Mock(spec=MermaidBlock)
        mock_block.code = "graph TD\n  A-->B"
        mock_block.get_filename.return_value = "test_0_abc123.svg"
        mock_block.attributes = {}

        processor.markdown_processor.extract_mermaid_blocks = Mock(
            return_value=[mock_block]
        )
        processor.markdown_processor.replace_blocks_with_images = Mock(
            return_value="![Mermaid Diagram](assets/images/test_0_abc123.svg)"
        )

        # beautiful-mermaid対応を判定するためのモック
        with patch.object(
            processor.image_generator.renderer.beautiful_renderer,
            "is_available",
            return_value=True,
        ):
            batch_items: list[BatchRenderItem] = []
            result_content, result_paths = processor.process_page(
                "test.md",
                "```mermaid\ngraph TD\n  A-->B\n```",
                str(tmp_path / "output"),
                batch_items=batch_items,
            )

        # batch_itemsに追加されていること
        assert len(batch_items) == 1
        assert batch_items[0].code == "graph TD\n  A-->B"
        assert batch_items[0].page_file == "test.md"
        assert batch_items[0].theme == "default"
        # SVGファイルはこの段階では生成されないこと（generate_image未呼出）
        mock_block.generate_image.assert_not_called()
        # ただしMarkdown書き換え用のimage_pathsには追加される
        assert len(result_paths) == 1

    @patch("mkdocs_mermaid_to_svg.image_generator.is_command_available")
    def test_非対応ブロックは従来どおり即時処理される(
        self, mock_command_available, auto_config
    ):
        """beautiful-mermaid非対応ブロック（pie等）は従来どおり即時処理される"""
        mock_command_available.return_value = True
        processor = MermaidProcessor(auto_config)

        # pieブロック（beautiful-mermaid非対応）
        mock_block = Mock(spec=MermaidBlock)
        mock_block.code = 'pie\n  title Pets\n  "Dogs" : 40'
        mock_block.get_filename.return_value = "test_0_def456.svg"
        mock_block.generate_image.return_value = True
        mock_block.attributes = {}

        processor.markdown_processor.extract_mermaid_blocks = Mock(
            return_value=[mock_block]
        )
        processor.markdown_processor.replace_blocks_with_images = Mock(
            return_value="![Mermaid Diagram](test_0_def456.svg)"
        )

        # beautiful-mermaid非対応
        with patch.object(
            processor.image_generator.renderer.beautiful_renderer,
            "is_available",
            return_value=False,
        ):
            batch_items: list[BatchRenderItem] = []
            result_content, result_paths = processor.process_page(
                "test.md",
                "```mermaid\npie\n  title Pets\n```",
                "/output",
                batch_items=batch_items,
            )

        # batch_itemsには追加されないこと
        assert len(batch_items) == 0
        # 即時処理されること
        assert len(result_paths) == 1
        mock_block.generate_image.assert_called_once()

    @patch("mkdocs_mermaid_to_svg.image_generator.is_command_available")
    def test_Markdownが画像参照に書き換えられる(
        self, mock_command_available, auto_config, tmp_path
    ):
        """収集モードでもMarkdownが画像参照に書き換えられる"""
        mock_command_available.return_value = True
        processor = MermaidProcessor(auto_config)

        mock_block = Mock(spec=MermaidBlock)
        mock_block.code = "graph TD\n  A-->B"
        mock_block.get_filename.return_value = "test_0_abc123.svg"
        mock_block.attributes = {}

        processor.markdown_processor.extract_mermaid_blocks = Mock(
            return_value=[mock_block]
        )
        expected_markdown = "![Mermaid Diagram](assets/images/test_0_abc123.svg)"
        processor.markdown_processor.replace_blocks_with_images = Mock(
            return_value=expected_markdown
        )

        with patch.object(
            processor.image_generator.renderer.beautiful_renderer,
            "is_available",
            return_value=True,
        ):
            batch_items: list[BatchRenderItem] = []
            result_content, result_paths = processor.process_page(
                "test.md",
                "```mermaid\ngraph TD\n  A-->B\n```",
                str(tmp_path / "output"),
                batch_items=batch_items,
            )

        assert result_content == expected_markdown

    @patch("mkdocs_mermaid_to_svg.image_generator.is_command_available")
    def test_batch_items未指定時は従来動作(self, mock_command_available, auto_config):
        """batch_items=Noneの場合は従来どおりの動作"""
        mock_command_available.return_value = True
        processor = MermaidProcessor(auto_config)

        mock_block = Mock(spec=MermaidBlock)
        mock_block.code = "graph TD\n  A-->B"
        mock_block.get_filename.return_value = "test_0_abc123.svg"
        mock_block.generate_image.return_value = True
        mock_block.attributes = {}

        processor.markdown_processor.extract_mermaid_blocks = Mock(
            return_value=[mock_block]
        )
        processor.markdown_processor.replace_blocks_with_images = Mock(
            return_value="![Mermaid](test.svg)"
        )

        # batch_itemsを渡さない（従来動作）
        result_content, result_paths = processor.process_page(
            "test.md", "```mermaid\ngraph TD\n  A-->B\n```", "/output"
        )

        # 従来どおり即時処理される
        assert len(result_paths) == 1
        mock_block.generate_image.assert_called_once()


# ---------------------------------------------------------------------------
# Phase 5 (US3): ブロックレベルオプションオーバーライドのテスト
# ---------------------------------------------------------------------------


class TestBlockLevelOptionOverride:
    """ブロック属性によるbeautiful-mermaidオプション上書きのテスト（T026, T027）"""

    @pytest.fixture
    def auto_config_with_global_options(self):
        """グローバルbeautiful-mermaidオプション付きのauto renderer設定"""
        return {
            "mmdc_path": "mmdc",
            "renderer": "auto",
            "output_dir": "assets/images",
            "image_format": "png",
            "theme": "default",
            "background_color": "white",
            "width": 800,
            "height": 600,
            "scale": 1.0,
            "css_file": None,
            "puppeteer_config": None,
            "mermaid_config": None,
            "cache_enabled": True,
            "cache_dir": ".mermaid_cache",
            "preserve_original": False,
            "error_on_fail": False,
            "log_level": "INFO",
            "beautiful_mermaid_bg": "#1a1b26",
            "beautiful_mermaid_fg": "#c0caf5",
            "beautiful_mermaid_font": None,
        }

    @patch("mkdocs_mermaid_to_svg.image_generator.is_command_available")
    def test_ブロック属性がグローバル設定を上書きする(
        self, mock_command_available, auto_config_with_global_options, tmp_path
    ):
        """ブロック属性のbgがグローバル設定のbgを上書きすることを検証（T026）"""
        mock_command_available.return_value = True
        processor = MermaidProcessor(auto_config_with_global_options)

        mock_block = Mock(spec=MermaidBlock)
        mock_block.code = "graph TD\n  A-->B"
        mock_block.get_filename.return_value = "test_0_abc123.svg"
        # ブロック属性でbgを上書き
        mock_block.attributes = {"bg": "#000000", "font": "Inter"}

        processor.markdown_processor.extract_mermaid_blocks = Mock(
            return_value=[mock_block]
        )
        processor.markdown_processor.replace_blocks_with_images = Mock(
            return_value="![Mermaid](test.svg)"
        )

        with patch.object(
            processor.image_generator.renderer.beautiful_renderer,
            "is_available",
            return_value=True,
        ):
            batch_items: list[BatchRenderItem] = []
            processor.process_page(
                "test.md",
                "```mermaid\ngraph TD\n  A-->B\n```",
                str(tmp_path / "output"),
                batch_items=batch_items,
            )

        assert len(batch_items) == 1
        options = batch_items[0].options
        assert options is not None
        # ブロック属性のbgがグローバル設定を上書き
        assert options["bg"] == "#000000"
        # グローバル設定のfgはそのまま残る
        assert options["fg"] == "#c0caf5"
        # ブロック属性のfontが追加される
        assert options["font"] == "Inter"

    @patch("mkdocs_mermaid_to_svg.image_generator.is_command_available")
    def test_各ブロックが個別のオプションを持てる(
        self, mock_command_available, auto_config_with_global_options, tmp_path
    ):
        """バッチレンダリング時に各ブロックが個別のオプションを持てることを検証（T027）"""
        mock_command_available.return_value = True
        processor = MermaidProcessor(auto_config_with_global_options)

        # ブロック1: bgを上書き
        mock_block1 = Mock(spec=MermaidBlock)
        mock_block1.code = "graph TD\n  A-->B"
        mock_block1.get_filename.return_value = "test_0_abc123.svg"
        mock_block1.attributes = {"bg": "#ff0000"}

        # ブロック2: 上書きなし（グローバル設定のまま）
        mock_block2 = Mock(spec=MermaidBlock)
        mock_block2.code = "graph LR\n  C-->D"
        mock_block2.get_filename.return_value = "test_1_def456.svg"
        mock_block2.attributes = {}

        processor.markdown_processor.extract_mermaid_blocks = Mock(
            return_value=[mock_block1, mock_block2]
        )
        processor.markdown_processor.replace_blocks_with_images = Mock(
            return_value="![Mermaid](test.svg)"
        )

        with patch.object(
            processor.image_generator.renderer.beautiful_renderer,
            "is_available",
            return_value=True,
        ):
            batch_items: list[BatchRenderItem] = []
            processor.process_page(
                "test.md",
                "```mermaid\ngraph TD\n  A-->B\n```\n"
                "```mermaid\ngraph LR\n  C-->D\n```",
                str(tmp_path / "output"),
                batch_items=batch_items,
            )

        assert len(batch_items) == 2
        # ブロック1: bgが上書きされている
        assert batch_items[0].options is not None
        assert batch_items[0].options["bg"] == "#ff0000"
        assert batch_items[0].options["fg"] == "#c0caf5"  # グローバルから
        # ブロック2: グローバル設定のまま
        assert batch_items[1].options is not None
        assert batch_items[1].options["bg"] == "#1a1b26"  # グローバルから
        assert batch_items[1].options["fg"] == "#c0caf5"  # グローバルから
