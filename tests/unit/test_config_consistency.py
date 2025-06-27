"""Test configuration consistency between config.py and plugin.py."""

from mkdocs_mermaid_to_image.config import ConfigManager
from mkdocs_mermaid_to_image.plugin import MermaidToImagePlugin


class TestConfigConsistency:
    """Test consistency between ConfigManager and Plugin config schemes."""

    def test_config_schemeの一貫性確認(self):
        """ConfigManagerとMermaidToImagePluginの設定スキーマが一貫していることを確認。"""
        # ConfigManagerから設定スキーマを取得
        config_manager_scheme = ConfigManager.get_config_scheme()

        # プラグインから設定スキーマを取得
        plugin = MermaidToImagePlugin()
        plugin_scheme = plugin.config_scheme

        # 設定項目名を抽出
        config_manager_names = set(item[0] for item in config_manager_scheme)
        plugin_names = set(item[0] for item in plugin_scheme)

        # 設定項目名の違いを検出
        manager_only = config_manager_names - plugin_names
        plugin_only = plugin_names - config_manager_names

        # 互いに異なる設定項目があることを報告（重要な発見）
        if manager_only:
            print(f"ConfigManager only: {manager_only}")
        if plugin_only:
            print(f"Plugin only: {plugin_only}")

        # 共通設定項目のデフォルト値一貫性をチェック
        common_names = config_manager_names & plugin_names

        # 両方の設定スキーマを辞書形式に変換
        config_manager_dict = dict(config_manager_scheme)
        plugin_dict = dict(plugin_scheme)

        for name in common_names:
            manager_option = config_manager_dict[name]
            plugin_option = plugin_dict[name]

            # 両方にdefault属性がある場合、値が同じであることを確認
            if hasattr(manager_option, "default") and hasattr(plugin_option, "default"):
                assert manager_option.default == plugin_option.default, (
                    f"Default value mismatch for '{name}': "
                    f"ConfigManager={manager_option.default}, "
                    f"Plugin={plugin_option.default}"
                )

    def test_デフォルト値の妥当性確認(self):
        """各設定項目のデフォルト値が妥当であることを確認。"""
        plugin = MermaidToImagePlugin()

        # 期待される型とデフォルト値のマッピング
        expected_types_and_defaults = {
            "enabled": (bool, True),
            "output_dir": (str, "assets/images"),
            "image_format": (str, "png"),
            "mmdc_path": (str, "mmdc"),
            "theme": (str, "default"),
            "background_color": (str, "white"),
            "width": (int, 800),
            "height": (int, 600),
            "scale": (float, 1.0),
            "cache_enabled": (bool, True),
            "cache_dir": (str, ".mermaid_cache"),
            "preserve_original": (bool, False),
            "error_on_fail": (bool, False),
            "log_level": (str, "INFO"),
        }

        for config_item in plugin.config_scheme:
            config_name = config_item[0]
            config_option = config_item[1]

            if config_name in expected_types_and_defaults:
                expected_type, expected_default = expected_types_and_defaults[
                    config_name
                ]

                # デフォルト値の型チェック
                if hasattr(config_option, "default"):
                    actual_default = config_option.default
                    assert isinstance(actual_default, expected_type), (
                        f"{config_name} default should be "
                        f"{expected_type.__name__}, got "
                        f"{type(actual_default).__name__}"
                    )
                    assert actual_default == expected_default, (
                        f"{config_name} default should be "
                        f"{expected_default}, got {actual_default}"
                    )
