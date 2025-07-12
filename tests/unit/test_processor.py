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

from mkdocs_mermaid_to_svg.exceptions import MermaidCLIError
from mkdocs_mermaid_to_svg.mermaid_block import MermaidBlock
from mkdocs_mermaid_to_svg.processor import MermaidProcessor


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
