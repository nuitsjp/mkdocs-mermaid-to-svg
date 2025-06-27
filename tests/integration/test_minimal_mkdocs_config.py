"""Integration test for minimal mkdocs.yml configuration."""

import tempfile
from unittest.mock import patch


class TestMinimalMkDocsConfig:
    """Test plugin functionality with minimal mkdocs.yml configuration."""

    def test_最小構成mkdocs_yml_でプラグイン動作(self):
        """plugins: [mermaid-to-image] だけの設定でプラグインが動作することを確認。"""
        from mkdocs_mermaid_to_image.plugin import MermaidToImagePlugin

        # プラグインインスタンスを作成
        plugin = MermaidToImagePlugin()

        # プラグインconfig にデフォルト値が設定されることをシミュレート
        # これは実際にはMkDocsが config_scheme を元に自動設定する
        plugin.config = {}
        for config_name, config_option in plugin.config_scheme:
            if hasattr(config_option, "default"):
                plugin.config[config_name] = config_option.default

        # 必須設定項目がデフォルト値で設定されていることを確認
        assert plugin.config["enabled"] is True
        assert plugin.config["output_dir"] == "assets/images"
        assert plugin.config["image_format"] == "png"
        assert plugin.config["mmdc_path"] == "mmdc"
        assert plugin.config["theme"] == "default"
        assert plugin.config["background_color"] == "white"
        assert plugin.config["width"] == 800
        assert plugin.config["height"] == 600
        assert plugin.config["scale"] == 1.0
        assert plugin.config["cache_enabled"] is True
        assert plugin.config["cache_dir"] == ".mermaid_cache"
        assert plugin.config["preserve_original"] is False
        assert plugin.config["error_on_fail"] is False
        assert plugin.config["log_level"] == "INFO"

        # オプショナル設定項目はNoneになっていることを確認
        assert plugin.config["mermaid_config"] is None
        assert plugin.config["css_file"] is None
        assert plugin.config["puppeteer_config"] is None
        assert plugin.config["temp_dir"] is None

    def test_最小構成でon_config_が成功する(self):
        """最小構成でon_configフックが成功することを確認。"""
        from mkdocs_mermaid_to_image.plugin import MermaidToImagePlugin

        plugin = MermaidToImagePlugin()

        # デフォルト設定を適用
        plugin.config = {}
        for config_name, config_option in plugin.config_scheme:
            if hasattr(config_option, "default"):
                plugin.config[config_name] = config_option.default

        # mock config
        mock_mkdocs_config = {
            "docs_dir": "/tmp/docs",
            "site_dir": "/tmp/site",
        }

        with tempfile.TemporaryDirectory() as temp_dir:
            mock_mkdocs_config["docs_dir"] = temp_dir

            # ディレクトリ作成とプロセッサ初期化をモック
            with (
                patch("mkdocs_mermaid_to_image.plugin.ensure_directory"),
                patch("mkdocs_mermaid_to_image.plugin.MermaidProcessor"),
                patch("mkdocs_mermaid_to_image.plugin.setup_logger"),
            ):
                # on_config が正常に実行されることを確認
                result = plugin.on_config(mock_mkdocs_config)

                # 設定が返されることを確認
                assert result is not None

    def test_デフォルト値でconfig_validation_が通過する(self):
        """デフォルト値で設定検証が通過することを確認。"""
        from mkdocs_mermaid_to_image.config import ConfigManager
        from mkdocs_mermaid_to_image.plugin import MermaidToImagePlugin

        plugin = MermaidToImagePlugin()

        # デフォルト設定を適用
        plugin.config = {}
        for config_name, config_option in plugin.config_scheme:
            if hasattr(config_option, "default"):
                plugin.config[config_name] = config_option.default

        # 設定検証が通過することを確認
        result = ConfigManager.validate_config(dict(plugin.config))
        assert result is True

    def test_最小構成yaml_パース(self):
        """最小構成のYAMLが正しくパースされることを確認。"""
        import yaml

        # 最小構成のmkdocs.yml内容
        minimal_yaml = """
plugins:
  - mermaid-to-image
"""

        # YAMLがパースできることを確認
        config_data = yaml.safe_load(minimal_yaml)
        assert "plugins" in config_data
        assert "mermaid-to-image" in config_data["plugins"]

        # より具体的な形式もテスト
        detailed_minimal_yaml = """
plugins:
  - mermaid-to-image: {}
"""

        config_data2 = yaml.safe_load(detailed_minimal_yaml)
        assert "plugins" in config_data2
        assert config_data2["plugins"][0]["mermaid-to-image"] == {}

    def test_全てのオプションにデフォルト値またはオプショナル設定(self):
        """全ての設定項目がデフォルト値を持つかオプショナル設定であることを確認。"""
        from mkdocs_mermaid_to_image.plugin import MermaidToImagePlugin

        plugin = MermaidToImagePlugin()

        missing_defaults = []

        for config_name, config_option in plugin.config_scheme:
            if not hasattr(config_option, "default"):
                missing_defaults.append(config_name)

        # 全ての設定項目がデフォルト値を持つことを確認
        assert (
            len(missing_defaults) == 0
        ), f"These config options lack default values: {missing_defaults}"
