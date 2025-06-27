"""Test minimal configuration functionality."""

from mkdocs_mermaid_to_image.plugin import MermaidToImagePlugin


class TestMinimalConfig:
    """Test plugin behavior with minimal configuration."""

    def test_最小構成での初期化成功(self):
        """プラグインが最小構成で初期化できることを確認。"""
        plugin = MermaidToImagePlugin()

        # MkDocsのconfig_optionsを使って設定を検証
        # 実際の設定値がデフォルト値で補完されることを確認
        for config_name, config_option in plugin.config_scheme:
            if hasattr(config_option, "default"):
                # デフォルト値が設定されている
                assert config_option.default is not None or config_name in [
                    "mermaid_config",
                    "css_file",
                    "puppeteer_config",
                    "temp_dir",
                ], f"{config_name} should have a default value"

    def test_enabled_デフォルトTrue_で動作(self):
        """enabled オプション未指定時にTrueになることを確認。"""
        plugin = MermaidToImagePlugin()

        # enabled設定を確認
        enabled_config = None
        for config_name, config_option in plugin.config_scheme:
            if config_name == "enabled":
                enabled_config = config_option
                break

        assert enabled_config is not None
        assert enabled_config.default is True

    def test_必須設定項目以外は全てデフォルト値を持つ(self):
        """必須設定項目以外は全てデフォルト値を持ち、最小構成で動作することを確認。"""
        plugin = MermaidToImagePlugin()

        # 各設定項目がデフォルト値を持つかチェック
        has_defaults = {}

        for config_name, config_option in plugin.config_scheme:
            has_defaults[config_name] = hasattr(config_option, "default")

        # 期待される最小構成で動作に必要な項目
        essential_with_defaults = [
            "enabled",  # プラグインの有効化
            "output_dir",  # 画像出力先
            "image_format",  # 画像形式
            "mmdc_path",  # Mermaid CLIパス
            "theme",  # テーマ
            "background_color",  # 背景色
            "width",  # 画像幅
            "height",  # 画像高さ
            "scale",  # 拡大率
            "cache_enabled",  # キャッシュ有効化
            "cache_dir",  # キャッシュディレクトリ
            "preserve_original",  # 元コード保持
            "error_on_fail",  # エラー時動作
            "log_level",  # ログレベル
        ]

        for essential in essential_with_defaults:
            assert has_defaults.get(
                essential, False
            ), f"{essential} should have a default value for minimal configuration"

    def test_オプショナル設定はデフォルトNoneまたは空文字(self):
        """オプショナルな設定項目はデフォルトでNoneまたは空文字で問題なく動作することを確認。"""
        plugin = MermaidToImagePlugin()

        # オプショナル設定項目
        optional_settings = [
            "mermaid_config",  # Mermaid設定ファイル
            "css_file",  # カスタムCSS
            "puppeteer_config",  # Puppeteer設定
            "temp_dir",  # 一時ディレクトリ
        ]

        for config_name, config_option in plugin.config_scheme:
            if config_name in optional_settings:
                # オプショナル設定はOptional wrapper または空文字/Noneデフォルト
                is_optional = str(type(config_option)).find("Optional") != -1 or (
                    hasattr(config_option, "default")
                    and config_option.default in [None, ""]
                )
                assert (
                    is_optional
                ), f"{config_name} should be optional or have None/empty default"

    def test_最小設定での設定検証通過(self):
        """最小設定で設定検証が通過することを確認。"""
        from mkdocs_mermaid_to_image.config import ConfigManager

        # 最小設定（必須項目のみデフォルト値）
        minimal_config = {
            "width": 800,
            "height": 600,
            "scale": 1.0,
            "css_file": None,
            "puppeteer_config": None,
        }

        # 設定検証が成功することを確認
        result = ConfigManager.validate_config(minimal_config)
        assert result is True
