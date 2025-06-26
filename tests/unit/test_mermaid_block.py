"""
MermaidBlockクラスのテスト
このファイルでは、MermaidBlockクラスの動作を検証します。

Python未経験者へのヒント：
- pytestを使ってテストを書いています。
- Mockやpatchで外部依存を疑似的に置き換えています。
- assert文で「期待する結果」かどうかを検証します。
"""

from unittest.mock import Mock, patch

from mkdocs_mermaid_to_image.mermaid_block import MermaidBlock


class TestMermaidBlock:
    """MermaidBlockクラスのテストクラス"""

    def test_basic_block_creation(self):
        """基本的なブロック生成のテスト"""
        block = MermaidBlock("graph TD\n A --> B", 0, 20)
        assert block.code == "graph TD\n A --> B"
        assert block.start_pos == 0
        assert block.end_pos == 20
        assert block.attributes == {}

    def test_block_with_attributes(self):
        """属性付きブロックの生成テスト"""
        attributes = {"theme": "dark", "background": "black"}
        block = MermaidBlock("graph TD\n A --> B", 0, 20, attributes)
        assert block.attributes == attributes

    def test_block_repr(self):
        """__repr__の出力テスト"""
        block = MermaidBlock("graph TD\n A --> B", 0, 20)
        repr_str = repr(block)
        assert "MermaidBlock" in repr_str
        assert "start=0" in repr_str
        assert "end=20" in repr_str

    def test_code_stripping(self):
        """コードの前後空白除去のテスト"""
        block = MermaidBlock("  \n  graph TD\n A --> B  \n  ", 0, 20)
        assert block.code == "graph TD\n A --> B"

    def test_generate_image_with_mock_generator(self):
        """画像生成メソッドのテスト（モック使用）"""
        block = MermaidBlock("graph TD\n A --> B", 0, 20)
        mock_generator = Mock()
        mock_generator.generate.return_value = True

        config = {
            "theme": "default",
            "background_color": "white",
            "width": 800,
            "height": 600,
        }

        result = block.generate_image("/path/to/output.png", mock_generator, config)

        assert result is True
        mock_generator.generate.assert_called_once()
        args = mock_generator.generate.call_args[0]
        assert args[0] == "graph TD\n A --> B"  # mermaid_code
        assert args[1] == "/path/to/output.png"  # output_path

    def test_generate_image_with_block_attributes(self):
        """ブロック属性が画像生成設定に反映されるかテスト"""
        attributes = {"theme": "dark", "background": "black", "width": "1000"}
        block = MermaidBlock("graph TD\n A --> B", 0, 20, attributes)
        mock_generator = Mock()
        mock_generator.generate.return_value = True

        config = {
            "theme": "default",
            "background_color": "white",
            "width": 800,
            "height": 600,
        }

        result = block.generate_image("/path/to/output.png", mock_generator, config)

        assert result is True
        # 呼び出された設定を確認
        args = mock_generator.generate.call_args[0]
        merged_config = args[2]
        assert merged_config["theme"] == "dark"
        assert merged_config["background_color"] == "black"
        assert merged_config["width"] == 1000
        assert merged_config["height"] == 600  # 元の設定のまま

    def test_get_image_markdown_basic(self):
        """画像Markdown生成の基本テスト"""
        block = MermaidBlock("graph TD\n A --> B", 0, 20)

        # ルートレベルのページの場合
        result = block.get_image_markdown(
            "/home/user/docs/assets/images/test.png", "index.md"
        )

        assert result == "![Mermaid Diagram](assets/images/test.png)"

    def test_get_image_markdown_preserve_original(self):
        """元のMermaidコードも残す場合のMarkdown生成テスト"""
        block = MermaidBlock("graph TD\n A --> B", 0, 20)

        result = block.get_image_markdown(
            "/home/user/docs/assets/images/test.png", "index.md", preserve_original=True
        )

        expected = (
            "![Mermaid Diagram](assets/images/test.png)\n\n"
            "```mermaid\ngraph TD\n A --> B\n```"
        )
        assert result == expected

    def test_get_image_markdown_preserve_original_with_attributes(self):
        """属性付きで元のコードも残す場合のMarkdown生成テスト"""
        attributes = {"theme": "dark", "background": "black"}
        block = MermaidBlock("graph TD\n A --> B", 0, 20, attributes)

        result = block.get_image_markdown(
            "/home/user/docs/assets/images/test.png", "index.md", preserve_original=True
        )

        assert "![Mermaid Diagram](assets/images/test.png)" in result
        assert "```mermaid {theme: dark, background: black}" in result
        assert "graph TD\n A --> B" in result

    def test_get_image_markdown_subdirectory(self):
        """サブディレクトリのページでの画像Markdown生成テスト"""
        block = MermaidBlock("graph TD\n A --> B", 0, 20)

        # development/page.md のようなサブディレクトリのページの場合
        result = block.get_image_markdown(
            "/home/user/docs/assets/images/test.png", "development/page.md"
        )

        assert result == "![Mermaid Diagram](../assets/images/test.png)"

    def test_get_filename(self):
        """ファイル名生成のテスト"""
        block = MermaidBlock("graph TD\n A --> B", 0, 20)

        with patch(
            "mkdocs_mermaid_to_image.mermaid_block.generate_image_filename"
        ) as mock_gen_filename:
            mock_gen_filename.return_value = "test_0_abc123.png"

            result = block.get_filename("/path/to/page.md", 0, "png")

            assert result == "test_0_abc123.png"
            mock_gen_filename.assert_called_once_with(
                "/path/to/page.md", 0, "graph TD\n A --> B", "png"
            )

    def test_invalid_width_height_attributes(self):
        """幅・高さ属性が不正な場合は無視されるかテスト"""
        attributes = {"width": "invalid", "height": "also_invalid"}
        block = MermaidBlock("graph TD\n A --> B", 0, 20, attributes)
        mock_generator = Mock()
        mock_generator.generate.return_value = True

        config = {"theme": "default", "width": 800, "height": 600}

        block.generate_image("/path/to/output.png", mock_generator, config)

        # 呼び出された設定を確認（無効な値は無視されるべき）
        args = mock_generator.generate.call_args[0]
        merged_config = args[2]
        assert merged_config["width"] == 800  # 元の設定のまま
        assert merged_config["height"] == 600  # 元の設定のまま
