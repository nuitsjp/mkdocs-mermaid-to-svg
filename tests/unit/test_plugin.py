"""
MermaidToImagePluginクラスのテスト
このファイルでは、プラグイン本体の動作を検証します。

Python未経験者へのヒント：
- pytestを使ってテストを書いています。
- patchやMockで外部依存を疑似的に置き換えています。
- assert文で「期待する結果」かどうかを検証します。
"""

import sys
from unittest.mock import Mock, patch

import pytest

from mkdocs_mermaid_to_image.exceptions import MermaidConfigError
from mkdocs_mermaid_to_image.plugin import MermaidToImagePlugin


class TestMermaidToImagePlugin:
    """MermaidToImagePluginクラスのテストクラス"""

    @pytest.fixture
    def plugin(self):
        """テスト用のプラグインインスタンスを返すfixture"""
        return MermaidToImagePlugin()

    @pytest.fixture
    def mock_config(self):
        """テスト用のモック設定を返すfixture"""
        config = Mock()
        config.__getitem__ = Mock(
            side_effect=lambda key: {
                "docs_dir": "/tmp/docs",
                "site_dir": "/tmp/site",
            }.get(key)
        )
        return config

    @pytest.fixture
    def mock_page(self):
        """テスト用のモックページを返すfixture"""
        page = Mock()
        page.file = Mock()
        page.file.src_path = "test.md"
        return page

    def test_plugin_initialization(self, plugin):
        """初期化時のプロパティが正しいかテスト"""
        assert plugin.processor is None
        assert plugin.logger is None
        assert plugin.generated_images == []

    def test_config_validation_success(self, plugin, mock_config):
        """有効な設定でon_configが成功するかテスト"""
        plugin.config = {
            "enabled": True,
            "output_dir": "assets/images",
            "image_format": "png",
            "mmdc_path": "mmdc",
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

        with (
            patch("mkdocs_mermaid_to_image.plugin.MermaidProcessor"),
            patch("mkdocs_mermaid_to_image.plugin.setup_logger") as mock_logger,
        ):
            mock_logger.return_value = Mock()
            result = plugin.on_config(mock_config)
            assert result == mock_config
            assert plugin.processor is not None

    def test_config_validation_disabled_plugin(self, plugin, mock_config):
        """プラグインが無効な場合にprocessorがNoneになるかテスト"""
        plugin.config = {
            "enabled": False,
            "output_dir": "assets/images",
            "image_format": "png",
            "mmdc_path": "mmdc",
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

        with patch("mkdocs_mermaid_to_image.plugin.setup_logger") as mock_logger:
            mock_logger.return_value = Mock()
            result = plugin.on_config(mock_config)
            assert result == mock_config
            assert plugin.processor is None

    def test_config_validation_invalid_dimensions(self, plugin, mock_config):
        """幅や高さが不正な場合に例外が発生するかテスト"""
        plugin.config = {
            "enabled": True,
            "width": -100,
            "height": 600,
            "scale": 1.0,
            "log_level": "INFO",
        }

        with pytest.raises(MermaidConfigError):
            plugin.on_config(mock_config)

    def test_on_files_disabled(self, plugin):
        """プラグイン無効時のon_filesの挙動をテスト"""
        plugin.config = {"enabled": False}
        files = ["file1.md", "file2.md"]

        result = plugin.on_files(files, config={})
        assert result == files
        assert plugin.generated_images == []

    def test_on_files_enabled(self, plugin):
        """プラグイン有効時のon_filesの挙動をテスト"""
        plugin.config = {"enabled": True}
        plugin.processor = Mock()
        files = ["file1.md", "file2.md"]

        result = plugin.on_files(files, config={})
        assert result == files
        assert plugin.generated_images == []

    @patch("mkdocs_mermaid_to_image.plugin.MermaidProcessor")
    def test_on_page_markdown_disabled(self, _mock_processor_class, plugin, mock_page):
        """プラグイン無効時は元のMarkdownが返るかテスト"""
        plugin.config = {"enabled": False}
        markdown = "# Test\n\nSome content"

        result = plugin.on_page_markdown(markdown, page=mock_page, config={}, files=[])
        assert result == markdown

    @patch("mkdocs_mermaid_to_image.plugin.MermaidProcessor")
    def test_on_page_markdown_success(
        self, _mock_processor_class, plugin, mock_page, mock_config
    ):
        """ページ内にMermaidブロックがある場合の処理をテスト"""
        plugin.config = {
            "enabled": True,
            "output_dir": "assets/images",
            "error_on_fail": False,
            "log_level": "INFO",
        }

        # processorをモック
        mock_processor = Mock()
        mock_processor.process_page.return_value = (
            "modified content",
            ["/path/to/image.png"],
        )
        plugin.processor = mock_processor
        plugin.logger = Mock()

        markdown = "# Test\n\n```mermaid\ngraph TD\n A --> B\n```"

        result = plugin.on_page_markdown(
            markdown, page=mock_page, config=mock_config, files=[]
        )

        assert result == "modified content"
        assert plugin.generated_images == ["/path/to/image.png"]
        mock_processor.process_page.assert_called_once()

    @patch("mkdocs_mermaid_to_image.plugin.MermaidProcessor")
    def test_on_page_markdown_error_handling(
        self, _mock_processor_class, plugin, mock_page, mock_config
    ):
        """画像生成時に例外が発生した場合のエラーハンドリングをテスト"""
        plugin.config = {
            "enabled": True,
            "output_dir": "assets/images",
            "error_on_fail": False,
            "log_level": "INFO",
        }

        # processorが例外を投げるようにモック
        mock_processor = Mock()
        mock_processor.process_page.side_effect = Exception("Test error")
        plugin.processor = mock_processor
        plugin.logger = Mock()

        markdown = "# Test\n\n```mermaid\ngraph TD\n A --> B\n```"

        result = plugin.on_page_markdown(
            markdown, page=mock_page, config=mock_config, files=[]
        )

        # error_on_fail=Falseなので元のMarkdownが返る
        assert result == markdown
        plugin.logger.error.assert_called()

    def test_on_post_build_disabled(self, plugin):
        """プラグイン無効時のon_post_buildの挙動をテスト"""
        plugin.config = {"enabled": False}
        plugin.on_post_build(config={})
        # 例外が発生しなければOK

    def test_on_post_build_with_images(self, plugin):
        """画像生成後のon_post_buildでログが出るかテスト"""
        plugin.config = {
            "enabled": True,
            "cache_enabled": True,
            "cache_dir": ".mermaid_cache",
        }
        plugin.generated_images = ["/path/to/image1.png", "/path/to/image2.png"]
        plugin.logger = Mock()

        plugin.on_post_build(config={})

        plugin.logger.info.assert_called_with("Generated 2 Mermaid images total")

    @patch("shutil.rmtree")
    @patch("pathlib.Path.exists")
    def test_on_post_build_cache_cleanup(self, mock_exists, mock_rmtree, plugin):
        """キャッシュ無効時にキャッシュディレクトリが削除されるかテスト"""
        plugin.config = {
            "enabled": True,
            "cache_enabled": False,
            "cache_dir": ".mermaid_cache",
        }
        plugin.generated_images = []
        plugin.logger = Mock()
        mock_exists.return_value = True

        plugin.on_post_build(config={})

        mock_rmtree.assert_called_once_with(".mermaid_cache")

    def test_on_serve_disabled(self, plugin):
        """プラグイン無効時のon_serveの挙動をテスト"""
        plugin.config = {"enabled": False}
        server = Mock()

        result = plugin.on_serve(server, config={}, builder=None)
        assert result == server

    def test_on_serve_enabled(self, plugin):
        """プラグイン有効時にキャッシュディレクトリの監視が追加されるかテスト"""
        plugin.config = {
            "enabled": True,
            "cache_enabled": True,
            "cache_dir": ".mermaid_cache",
        }
        server = Mock()

        with patch("pathlib.Path.exists", return_value=True):
            result = plugin.on_serve(server, config={}, builder=None)
            assert result == server
            server.watch.assert_called_once_with(".mermaid_cache")


class TestMermaidToImagePluginServeMode:
    """serve モード検出機能のテストクラス"""

    def test_正常系_ビルドモード検出(self):
        """ビルドモード時にis_serve_modeがFalseになることを確認"""
        with patch.object(sys, "argv", ["mkdocs", "build"]):
            plugin = MermaidToImagePlugin()
            assert not plugin.is_serve_mode

    def test_正常系_serveモード検出(self):
        """serveモード時にis_serve_modeがTrueになることを確認"""
        with patch.object(sys, "argv", ["mkdocs", "serve"]):
            plugin = MermaidToImagePlugin()
            assert plugin.is_serve_mode

    def test_正常系_serveモード_オプション付き(self):
        """serveモード（オプション付き）の検出を確認"""
        with patch.object(
            sys, "argv", ["mkdocs", "serve", "--dev-addr", "0.0.0.0:8000"]
        ):
            plugin = MermaidToImagePlugin()
            assert plugin.is_serve_mode

    def test_正常系_他のコマンド(self):
        """他のコマンド（gh-deploy）でis_serve_modeがFalseになることを確認"""
        with patch.object(sys, "argv", ["mkdocs", "gh-deploy"]):
            plugin = MermaidToImagePlugin()
            assert not plugin.is_serve_mode

    def test_正常系_空のargv(self):
        """空のargvでis_serve_modeがFalseになることを確認"""
        with patch.object(sys, "argv", []):
            plugin = MermaidToImagePlugin()
            assert not plugin.is_serve_mode

    @patch("mkdocs_mermaid_to_image.plugin.MermaidProcessor")
    def test_正常系_serveモード時のMarkdown処理スキップ(self, _mock_processor_class):
        """serveモード時にMermaid処理がスキップされることを確認"""
        with patch.object(sys, "argv", ["mkdocs", "serve"]):
            plugin = MermaidToImagePlugin()
            plugin.config = {"enabled": True}
            plugin.processor = Mock()  # プロセッサが設定されている状態
            plugin.logger = Mock()

            # Mock page and config
            mock_page = Mock()
            mock_page.file.src_path = "test.md"
            mock_config = {"docs_dir": "/tmp/docs"}

            markdown = "# Test\n\n```mermaid\ngraph TD\n A --> B\n```"

            result = plugin.on_page_markdown(
                markdown, page=mock_page, config=mock_config, files=[]
            )

            # serveモード時は元のMarkdownがそのまま返される
            assert result == markdown
            # プロセッサの処理メソッドが呼び出されていないことを確認
            plugin.processor.process_page.assert_not_called()
            # デバッグログが出力されていることを確認
            plugin.logger.debug.assert_called_once()

    @patch("mkdocs_mermaid_to_image.plugin.MermaidProcessor")
    def test_正常系_ビルドモード時のMarkdown処理実行(self, _mock_processor_class):
        """ビルドモード時にMermaid処理が実行されることを確認"""
        with patch.object(sys, "argv", ["mkdocs", "build"]):
            plugin = MermaidToImagePlugin()
            plugin.config = {"enabled": True, "output_dir": "assets/images"}

            # プロセッサをモック
            mock_processor = Mock()
            mock_processor.process_page.return_value = (
                "modified content with images",
                ["/path/to/image.png"],
            )
            plugin.processor = mock_processor
            plugin.logger = Mock()

            # Mock page and config
            mock_page = Mock()
            mock_page.file.src_path = "test.md"
            mock_config = {"docs_dir": "/tmp/docs"}

            markdown = "# Test\n\n```mermaid\ngraph TD\n A --> B\n```"

            result = plugin.on_page_markdown(
                markdown, page=mock_page, config=mock_config, files=[]
            )

            # ビルドモード時は処理されたMarkdownが返される
            assert result == "modified content with images"
            # プロセッサの処理メソッドが呼び出されていることを確認
            plugin.processor.process_page.assert_called_once()
            # 生成された画像パスが記録されていることを確認
            assert plugin.generated_images == ["/path/to/image.png"]

    def test_正常系_serveモード時のプラグイン無効(self):
        """serveモード時にプラグインが無効な場合の処理を確認"""
        with patch.object(sys, "argv", ["mkdocs", "serve"]):
            plugin = MermaidToImagePlugin()
            plugin.config = {"enabled": False}
            plugin.processor = None

            # Mock page and config
            mock_page = Mock()
            mock_page.file.src_path = "test.md"
            mock_config = {"docs_dir": "/tmp/docs"}

            markdown = "# Test\n\n```mermaid\ngraph TD\n A --> B\n```"

            result = plugin.on_page_markdown(
                markdown, page=mock_page, config=mock_config, files=[]
            )

            # プラグイン無効時は元のMarkdownが返される
            assert result == markdown

    def test_正常系_serveモード時のプロセッサ未初期化(self):
        """serveモード時にプロセッサが未初期化の場合の処理を確認"""
        with patch.object(sys, "argv", ["mkdocs", "serve"]):
            plugin = MermaidToImagePlugin()
            plugin.config = {"enabled": True}
            plugin.processor = None  # プロセッサが未初期化

            # Mock page and config
            mock_page = Mock()
            mock_page.file.src_path = "test.md"
            mock_config = {"docs_dir": "/tmp/docs"}

            markdown = "# Test\n\n```mermaid\ngraph TD\n A --> B\n```"

            result = plugin.on_page_markdown(
                markdown, page=mock_page, config=mock_config, files=[]
            )

            # プロセッサ未初期化時は元のMarkdownが返される
            assert result == markdown
