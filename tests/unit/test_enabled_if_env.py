import os
import unittest.mock

from mkdocs_mermaid_to_svg.plugin import MermaidToImagePlugin


class TestEnabledIfEnv:
    def test_enabled_if_env_when_env_var_is_set(self):
        """環境変数が設定されている場合、プラグインが有効化されることをテスト"""
        with unittest.mock.patch.dict(os.environ, {"ENABLE_PDF_EXPORT": "1"}):
            plugin = MermaidToImagePlugin()
            config = {"enabled_if_env": "ENABLE_PDF_EXPORT"}

            # プラグインが有効化されることを確認
            assert plugin._should_be_enabled(config) is True

    def test_enabled_if_env_when_env_var_is_not_set(self):
        """環境変数が設定されていない場合、プラグインが無効化されることをテスト"""
        with unittest.mock.patch.dict(os.environ, {}, clear=True):
            plugin = MermaidToImagePlugin()
            config = {"enabled_if_env": "ENABLE_PDF_EXPORT"}

            # プラグインが無効化されることを確認
            assert plugin._should_be_enabled(config) is False

    def test_enabled_if_env_when_env_var_is_empty_string(self):
        """環境変数が空文字列の場合、プラグインが無効化されることをテスト"""
        with unittest.mock.patch.dict(os.environ, {"ENABLE_PDF_EXPORT": ""}):
            plugin = MermaidToImagePlugin()
            config = {"enabled_if_env": "ENABLE_PDF_EXPORT"}

            # プラグインが無効化されることを確認
            assert plugin._should_be_enabled(config) is False

    def test_enabled_if_env_default_behavior_when_not_specified(self):
        """enabled_if_envが指定されていない場合、プラグインが有効化されることをテスト"""
        plugin = MermaidToImagePlugin()
        config = {}

        # enabled_if_envが未設定の場合、プラグインが有効化されることを確認
        assert plugin._should_be_enabled(config) is True

    def test_enabled_if_env_overrides_default_behavior(self):
        """enabled_if_envが設定されている場合、デフォルトの有効化動作を上書きすることをテスト"""
        with unittest.mock.patch.dict(os.environ, {}, clear=True):
            plugin = MermaidToImagePlugin()
            config = {"enabled_if_env": "ENABLE_PDF_EXPORT"}

            # 環境変数が未設定の場合、プラグインが無効化される
            assert plugin._should_be_enabled(config) is False

    def test_config_scheme_includes_enabled_if_env(self):
        """設定スキーマにenabled_if_envが含まれることをテスト"""
        plugin = MermaidToImagePlugin()
        config_scheme_dict = dict(plugin.config_scheme)

        # enabled_if_envが設定スキーマに含まれることを確認
        assert "enabled_if_env" in config_scheme_dict

    def test_enabled_if_env_accepts_none_as_default(self):
        """enabled_if_envのデフォルト値がNoneであることをテスト"""
        config = {}

        # デフォルト値がNoneであることを確認
        assert config.get("enabled_if_env") is None
