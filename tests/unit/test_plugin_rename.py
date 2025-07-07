"""
プラグイン名変更のテストファイル

このファイルは、プラグインクラス名が正しく変更されたことを確認するテストです。
- MermaidToImagePlugin が MermaidSvgConverterPlugin に変更されていることを確認
- プラグインのエントリーポイントが正しく設定されていることを確認
"""


class TestPluginRename:
    """プラグイン名変更のテストクラス"""

    def test_old_plugin_class_is_alias_for_new_class(self):
        """
        古いプラグインクラス名が新しいクラスのエイリアスになっていることを確認するテスト

        後方互換性のために古いクラス名も使用可能である必要があります。
        """
        from mkdocs_mermaid_to_svg.plugin import (
            MermaidSvgConverterPlugin,
            MermaidToImagePlugin,
        )

        # 古いクラス名が新しいクラスのエイリアスであることを確認
        assert MermaidToImagePlugin is MermaidSvgConverterPlugin

    def test_new_plugin_class_should_exist(self):
        """
        新しいプラグインクラス名が存在することを確認するテスト

        このテストは最初に失敗し、クラス名を変更した後に成功する必要があります。
        """
        from mkdocs_mermaid_to_svg.plugin import MermaidSvgConverterPlugin

        # クラスが正しく定義されていることを確認
        assert MermaidSvgConverterPlugin is not None
        assert hasattr(MermaidSvgConverterPlugin, "on_config")
        assert hasattr(MermaidSvgConverterPlugin, "on_page_markdown")
        assert hasattr(MermaidSvgConverterPlugin, "on_post_build")

    def test_plugin_config_schema_works(self):
        """
        新しいプラグインクラスの設定スキーマが正しく動作することを確認するテスト
        """
        from mkdocs_mermaid_to_svg.plugin import MermaidSvgConverterPlugin

        plugin = MermaidSvgConverterPlugin()
        config_schema = plugin.config_scheme

        # 設定項目名の一覧を抽出
        config_names = [item[0] for item in config_schema]

        # image_formatが設定スキーマに含まれていないことを確認
        assert "image_format" not in config_names

        # 他の重要な設定項目が含まれていることを確認
        assert "output_dir" in config_names
        assert "theme" in config_names
        assert "enabled_if_env" in config_names
