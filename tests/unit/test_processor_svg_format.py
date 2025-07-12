"""Test for SVG format usage in processor after image_format config removal."""

import tempfile
from pathlib import Path
from unittest.mock import patch

from mkdocs_mermaid_to_svg.processor import MermaidProcessor


class TestProcessorSvgFormat:
    """Test processor works without image_format in config."""

    def test_processor_works_without_image_format_config(self):
        """Test that processor works when image_format is not in config."""
        # image_formatを含まない設定（削除後の状態）
        config = {
            "mmdc_path": "mmdc",
            "theme": "default",
            "error_on_fail": False,
            "log_level": "INFO",
        }

        with tempfile.TemporaryDirectory() as temp_dir:
            output_dir = Path(temp_dir)

            # MermaidProcessorを作成（image_formatなしでもエラーが出ない）
            with patch(
                "mkdocs_mermaid_to_svg.image_generator.is_command_available"
            ) as mock_available:
                mock_available.return_value = True
                processor = MermaidProcessor(config)

                # Mermaid図を含むmarkdownを処理
                markdown_content = """
# Test

```mermaid
graph TD
    A --> B
```
"""

                # image_formatがなくてもprocess_pageが動作する
                result_content, image_paths = processor.process_page(
                    "test.md", markdown_content, output_dir
                )

                # 結果が正しく返される（エラーでない）
                assert result_content is not None
                assert isinstance(image_paths, list)

    def test_processor_uses_svg_format_by_default(self):
        """Test processor defaults to SVG format when image_format not configured."""
        config = {
            "mmdc_path": "mmdc",
            "theme": "default",
            "error_on_fail": False,
            "log_level": "INFO",
        }

        with tempfile.TemporaryDirectory() as temp_dir:
            output_dir = Path(temp_dir)

            with patch(
                "mkdocs_mermaid_to_svg.image_generator.is_command_available"
            ) as mock_available:
                mock_available.return_value = True

                with patch(
                    "mkdocs_mermaid_to_svg.mermaid_block.MermaidBlock.get_filename"
                ) as mock_get_filename:
                    mock_get_filename.return_value = "test_mermaid_0_hash.svg"

                    processor = MermaidProcessor(config)

                    markdown_content = """
```mermaid
graph TD
    A --> B
```
"""

                    processor.process_page("test.md", markdown_content, output_dir)

                    # get_filenameが"svg"で呼び出されることを確認
                    mock_get_filename.assert_called_with("test.md", 0, "svg")
