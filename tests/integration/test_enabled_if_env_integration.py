import os
import unittest.mock

from mkdocs_mermaid_to_image.plugin import MermaidToImagePlugin


class TestEnabledIfEnvIntegration:
    """enabled_if_env機能の統合テスト（実際のプラグイン設定を使用）"""

    def test_plugin_lifecycle_with_env_var_enabled(self):
        """環境変数が設定されている場合のプラグインライフサイクルテスト"""
        with unittest.mock.patch.dict(os.environ, {"ENABLE_PDF_EXPORT": "1"}):
            plugin = MermaidToImagePlugin()
            config = {
                "enabled_if_env": "ENABLE_PDF_EXPORT",
                "log_level": "ERROR",  # ログ出力を抑制
                "width": 800,
                "height": 600,
                "scale": 1.0,
                "output_dir": "assets/images",
                "image_format": "png",
                "mmdc_path": "mmdc",
                "theme": "default",
                "background_color": "white",
                "cache_enabled": True,
                "cache_dir": ".mermaid_cache",
                "preserve_original": False,
                "error_on_fail": False,
                "cleanup_generated_images": False,
            }

            # プラグインが有効化されることを確認
            assert plugin._should_be_enabled(config) is True

            # on_configメソッドでも適切に処理されることを確認
            mock_mkdocs_config = {"site_dir": "/tmp/test"}
            plugin.config = config
            result = plugin.on_config(mock_mkdocs_config)

            # 設定が正常に処理されることを確認
            assert result == mock_mkdocs_config

    def test_plugin_lifecycle_with_env_var_disabled(self):
        """環境変数が設定されていない場合のプラグインライフサイクルテスト"""
        with unittest.mock.patch.dict(os.environ, {}, clear=True):
            plugin = MermaidToImagePlugin()
            config = {
                "enabled_if_env": "ENABLE_PDF_EXPORT",
                "log_level": "ERROR",  # ログ出力を抑制
                "width": 800,
                "height": 600,
                "scale": 1.0,
                "output_dir": "assets/images",
                "image_format": "png",
                "mmdc_path": "mmdc",
                "theme": "default",
                "background_color": "white",
                "cache_enabled": True,
                "cache_dir": ".mermaid_cache",
                "preserve_original": False,
                "error_on_fail": False,
                "cleanup_generated_images": False,
            }

            # プラグインが無効化されることを確認
            assert plugin._should_be_enabled(config) is False

            # on_configメソッドで早期リターンされることを確認
            mock_mkdocs_config = {"site_dir": "/tmp/test"}
            plugin.config = config
            result = plugin.on_config(mock_mkdocs_config)

            # プロセッサが初期化されないことを確認
            assert plugin.processor is None
            assert result == mock_mkdocs_config

    def test_plugin_markdown_processing_with_env_var_enabled(self):
        """環境変数有効時のMarkdown処理テスト"""
        with unittest.mock.patch.dict(os.environ, {"ENABLE_PDF_EXPORT": "1"}):
            plugin = MermaidToImagePlugin()
            config = {
                "enabled_if_env": "ENABLE_PDF_EXPORT",
                "log_level": "ERROR",
                "width": 800,
                "height": 600,
                "scale": 1.0,
                "output_dir": "assets/images",
                "image_format": "png",
                "mmdc_path": "mmdc",
                "theme": "default",
                "background_color": "white",
                "cache_enabled": True,
                "cache_dir": ".mermaid_cache",
                "preserve_original": False,
                "error_on_fail": False,
                "cleanup_generated_images": False,
            }
            plugin.config = config

            # serve モードでない場合のテスト
            plugin.is_serve_mode = False

            test_markdown = """
# Test

```mermaid
graph TD
    A --> B
```
"""

            # プロセッサが未初期化の場合、Markdownが変更されずに返される
            mock_page = type(
                "MockPage",
                (),
                {
                    "file": type("MockFile", (), {"src_path": "test.md"})(),
                    "url": "test/",
                },
            )()
            mock_config = {"site_dir": "/tmp/test"}
            mock_files = []

            result = plugin.on_page_markdown(
                test_markdown, page=mock_page, config=mock_config, files=mock_files
            )

            # プロセッサが未初期化なので元のMarkdownが返される
            assert result == test_markdown

    def test_plugin_markdown_processing_with_env_var_disabled(self):
        """環境変数無効時のMarkdown処理テスト"""
        with unittest.mock.patch.dict(os.environ, {}, clear=True):
            plugin = MermaidToImagePlugin()
            config = {
                "enabled_if_env": "ENABLE_PDF_EXPORT",
                "log_level": "ERROR",
                "width": 800,
                "height": 600,
                "scale": 1.0,
                "output_dir": "assets/images",
                "image_format": "png",
                "mmdc_path": "mmdc",
                "theme": "default",
                "background_color": "white",
                "cache_enabled": True,
                "cache_dir": ".mermaid_cache",
                "preserve_original": False,
                "error_on_fail": False,
                "cleanup_generated_images": False,
            }
            plugin.config = config

            test_markdown = """
# Test

```mermaid
graph TD
    A --> B
```
"""

            mock_page = type(
                "MockPage",
                (),
                {
                    "file": type("MockFile", (), {"src_path": "test.md"})(),
                    "url": "test/",
                },
            )()
            mock_config = {"site_dir": "/tmp/test"}
            mock_files = []

            result = plugin.on_page_markdown(
                test_markdown, page=mock_page, config=mock_config, files=mock_files
            )

            # プラグインが無効化されているため、元のMarkdownがそのまま返される
            assert result == test_markdown

    def test_plugin_post_build_with_env_var_disabled(self):
        """環境変数無効時のpost_build処理テスト"""
        with unittest.mock.patch.dict(os.environ, {}, clear=True):
            plugin = MermaidToImagePlugin()
            config = {
                "enabled_if_env": "ENABLE_PDF_EXPORT",
                "log_level": "ERROR",
                "width": 800,
                "height": 600,
                "scale": 1.0,
                "output_dir": "assets/images",
                "image_format": "png",
                "mmdc_path": "mmdc",
                "theme": "default",
                "background_color": "white",
                "cache_enabled": True,
                "cache_dir": ".mermaid_cache",
                "preserve_original": False,
                "error_on_fail": False,
                "cleanup_generated_images": False,
            }
            plugin.config = config

            mock_config = {"site_dir": "/tmp/test"}

            # post_buildが例外なく実行されることを確認
            result = plugin.on_post_build(config=mock_config)
            assert result is None  # on_post_buildは戻り値なし
