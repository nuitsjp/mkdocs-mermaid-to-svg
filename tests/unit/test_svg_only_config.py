"""
SVG固定化のテストファイル

このファイルは、プラグインがSVG専用になったことを確認するテストです。
- image_formatが設定スキーマから削除されていることを確認
- 画像生成がSVG固定であることを確認
"""

from mkdocs_mermaid_to_svg.config import ConfigManager


class TestSvgOnlyConfig:
    """SVG固定化のテストクラス"""

    def test_image_format_not_in_config_scheme(self):
        """
        image_formatが設定スキーマから削除されていることを確認するテスト

        このテストは最初に失敗し、image_formatを削除した後に成功する必要があります。
        """
        scheme = ConfigManager.get_config_scheme()
        config_names = [item[0] for item in scheme]

        # image_formatが設定スキーマに含まれていないことを確認
        assert (
            "image_format" not in config_names
        ), "image_format should be removed from config scheme"

    def test_svg_only_generation(self):
        """
        画像生成がSVG固定であることを確認するテスト

        このテストは最初に失敗し、SVG固定化を実装した後に成功する必要があります。
        """
        from mkdocs_mermaid_to_svg.image_generator import MermaidImageGenerator

        # 最小限の設定でジェネレーターを作成
        config = {
            "mmdc_path": "mmdc",
            "width": 800,
            "height": 600,
            "scale": 1.0,
            "background_color": "white",
            "theme": "default",
            "output_dir": "assets/images",
            "error_on_fail": False,
        }

        generator = MermaidImageGenerator(config)

        # _build_mmdc_commandメソッドでSVGが使用されることを確認
        # この実装はimage_generator.pyの修正後に成功します
        command, _, _ = generator._build_mmdc_command("test.mmd", "output.svg", config)

        # コマンドにSVGフォーマットが含まれていることを確認
        command_str = " ".join(command)
        assert (
            "-e svg" in command_str or "--outputFormat svg" in command_str
        ), f"Generated command should use SVG format, but got: {command}"
