"""
MermaidProcessorクラスのテスト
このファイルでは、MermaidProcessorクラスの動作を検証します。

Python未経験者へのヒント：
- pytestを使ってテストを書いています。
- Mockやpatchで外部依存を疑似的に置き換えています。
- assert文で「期待する結果」かどうかを検証します。
"""

from unittest.mock import Mock, patch

import pytest

from mkdocs_mermaid_to_image.exceptions import MermaidCLIError
from mkdocs_mermaid_to_image.mermaid_block import MermaidBlock
from mkdocs_mermaid_to_image.processor import MermaidProcessor


class TestMermaidProcessor:
    """MermaidProcessorクラスのテストクラス"""

    @pytest.fixture
    def basic_config(self):
        """テスト用の基本設定を返すfixture"""
        return {
            "mmdc_path": "mmdc",
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

    @patch("mkdocs_mermaid_to_image.image_generator.is_command_available")
    def test_processor_initialization(self, mock_command_available, basic_config):
        """MermaidProcessorの初期化が正しく行われるかテスト"""
        mock_command_available.return_value = True
        processor = MermaidProcessor(basic_config)
        assert processor.config == basic_config
        assert processor.logger is not None
        assert processor.markdown_processor is not None
        assert processor.image_generator is not None

    @patch("mkdocs_mermaid_to_image.image_generator.is_command_available")
    def test_processor_initialization_missing_cli(
        self, mock_command_available, basic_config
    ):
        """Mermaid CLIが見つからない場合に例外が発生するかテスト"""
        mock_command_available.return_value = False
        with pytest.raises(MermaidCLIError):
            MermaidProcessor(basic_config)

    @patch("mkdocs_mermaid_to_image.image_generator.is_command_available")
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
        mock_block.get_filename.assert_called_once_with("test.md", 0, "png")

    @patch("mkdocs_mermaid_to_image.image_generator.is_command_available")
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

    @patch("mkdocs_mermaid_to_image.image_generator.is_command_available")
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
