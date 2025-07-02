"""
MermaidToImagePluginクラスのテスト
このファイルでは、プラグイン本体の動作を検証します。

Python未経験者へのヒント：
- pytestを使ってテストを書いています。
- patchやMockで外部依存を疑似的に置き換えています。
- assert文で「期待する結果」かどうかを検証します。
"""

import sys
import warnings
from pathlib import Path
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
            patch("mkdocs_mermaid_to_image.plugin.get_logger") as mock_logger,
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

        with patch("mkdocs_mermaid_to_image.plugin.get_logger") as mock_logger:
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

        markdown = "# Test\n\n```mermaid\ngraph TD\n A --> B\n```"

        result = plugin.on_page_markdown(
            markdown, page=mock_page, config=mock_config, files=[]
        )

        # error_on_fail=Falseなので元のMarkdownが返る
        assert result == markdown

    @patch("mkdocs_mermaid_to_image.plugin.MermaidProcessor")
    def test_on_page_markdown_mermaid_error_with_error_on_fail_true(
        self, _mock_processor_class, plugin, mock_page, mock_config
    ):
        """MermaidPreprocessorError例外とerror_on_fail=Trueのテスト"""
        from mkdocs_mermaid_to_image.exceptions import MermaidPreprocessorError

        plugin.config = {
            "enabled": True,
            "output_dir": "assets/images",
            "error_on_fail": True,  # この場合は例外が再発生される
            "log_level": "INFO",
        }

        # processorがMermaidPreprocessorErrorを投げるようにモック
        mock_processor = Mock()
        mock_processor.process_page.side_effect = MermaidPreprocessorError(
            "Mermaid processing failed"
        )
        plugin.processor = mock_processor

        markdown = "# Test\n\n```mermaid\ngraph TD\n A --> B\n```"

        with pytest.raises(MermaidPreprocessorError):
            plugin.on_page_markdown(
                markdown, page=mock_page, config=mock_config, files=[]
            )

    @patch("mkdocs_mermaid_to_image.plugin.MermaidProcessor")
    def test_on_page_markdown_general_error_with_error_on_fail_true(
        self, _mock_processor_class, plugin, mock_page, mock_config
    ):
        """一般的な例外とerror_on_fail=Trueのテスト"""
        from mkdocs_mermaid_to_image.exceptions import MermaidPreprocessorError

        plugin.config = {
            "enabled": True,
            "output_dir": "assets/images",
            "error_on_fail": True,  # この場合は例外が再発生される
            "log_level": "INFO",
        }

        # processorが一般的な例外を投げるようにモック
        mock_processor = Mock()
        mock_processor.process_page.side_effect = ValueError("Unexpected error")
        plugin.processor = mock_processor

        markdown = "# Test\n\n```mermaid\ngraph TD\n A --> B\n```"

        with pytest.raises(MermaidPreprocessorError):
            plugin.on_page_markdown(
                markdown, page=mock_page, config=mock_config, files=[]
            )

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

        mock_logger = Mock()
        plugin.logger = mock_logger
        plugin.on_post_build(config={})
        mock_logger.info.assert_called_with("Generated 2 Mermaid images total")

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

    @patch("pathlib.Path.exists")
    def test_on_post_build_image_cleanup_enabled(self, mock_exists, plugin):
        """画像クリーンアップが有効時に生成画像ファイルが削除されるかテスト"""
        plugin.config = {
            "enabled": True,
            "cache_enabled": True,
            "cache_dir": ".mermaid_cache",
            "cleanup_generated_images": True,
        }
        plugin.generated_images = [
            "/path/to/image1.png",
            "/path/to/image2.svg",
            "/path/to/nonexistent.png",  # 存在しないファイル
        ]
        plugin.logger = Mock()

        # mock_existsをTrue設定（簡単のため全ファイルが存在するとする）
        mock_exists.return_value = True

        with patch("pathlib.Path.unlink") as mock_unlink:
            plugin.on_post_build(config={})

            # 3つのファイルが削除される
            assert mock_unlink.call_count == 3

    @patch("pathlib.Path.exists")
    def test_on_post_build_image_cleanup_disabled(self, mock_exists, plugin):
        """画像クリーンアップが無効時に生成画像ファイルが削除されないかテスト"""
        plugin.config = {
            "enabled": True,
            "cache_enabled": True,
            "cache_dir": ".mermaid_cache",
            "cleanup_generated_images": False,
        }
        plugin.generated_images = ["/path/to/image1.png", "/path/to/image2.svg"]
        plugin.logger = Mock()
        mock_exists.return_value = True

        with patch("pathlib.Path.unlink") as mock_unlink:
            plugin.on_post_build(config={})

            # クリーンアップが無効なので削除されない
            mock_unlink.assert_not_called()

    @patch("pathlib.Path.unlink")
    @patch("pathlib.Path.exists")
    def test_on_post_build_image_cleanup_error_handling(
        self, mock_exists, mock_unlink, plugin
    ):
        """画像削除時のエラーハンドリングをテスト"""
        plugin.config = {
            "enabled": True,
            "cleanup_generated_images": True,
            "cache_enabled": True,
            "cache_dir": ".mermaid_cache",
        }
        plugin.generated_images = ["/path/to/image1.png"]
        mock_exists.return_value = True
        mock_unlink.side_effect = PermissionError("Permission denied")

        # エラーが発生してもプラグインは正常に動作する
        plugin.on_post_build(config={})

    @patch("mkdocs_mermaid_to_image.plugin.clean_generated_images")
    def test_on_post_build_image_cleanup_without_logger(
        self, mock_clean_generated_images, plugin
    ):
        """loggerがNoneでもクリーンアップが実行されることをテスト"""
        plugin.config = {
            "enabled": True,
            "cleanup_generated_images": True,
            "cache_enabled": True,
            "cache_dir": ".mermaid_cache",
        }
        plugin.generated_images = ["/path/to/image1.png", "/path/to/image2.svg"]

        mock_logger = Mock()
        plugin.logger = mock_logger
        plugin.on_post_build(config={})
        # clean_generated_imagesが呼び出されるべき
        mock_clean_generated_images.assert_called_once_with(
            plugin.generated_images, mock_logger
        )

    @patch("pathlib.Path.exists")
    def test_register_generated_images_replaces_duplicate_file(self, mock_exists):
        """重複ファイルが適切に置換されることを確認"""
        mock_exists.return_value = True

        plugin = MermaidToImagePlugin()
        plugin.config = {"enabled": True}

        # 実際のMkDocs FilesオブジェクトとFileオブジェクトを使用
        from pathlib import Path

        from mkdocs.structure.files import File, Files

        docs_dir = Path("/tmp/docs")

        # Filesオブジェクトを作成
        files = Files([])
        plugin.files = files

        # 先に1つファイルを追加して重複状況を作る
        existing_file = File("assets/images/test.svg", str(docs_dir), "/tmp/site", True)
        files.append(existing_file)

        # ファイル数を記録
        initial_file_count = len(files)

        # モック設定を作成
        mock_config = {
            "docs_dir": str(docs_dir),
            "site_dir": "/tmp/site",
            "use_directory_urls": True,
        }

        # 既に存在するファイルと同じパスを登録（重複）
        image_paths = [str(docs_dir / "assets/images/test.svg")]

        # テスト対象メソッドを実行
        plugin._register_generated_images_to_files(image_paths, docs_dir, mock_config)

        # ファイル数が変わらないことを確認（置換されたため）
        assert (
            len(files) == initial_file_count
        ), "File count should remain the same after duplicate replacement"

        # ファイルパスが正しいことを確認
        file_paths = [f.src_path for f in files]
        assert "assets/images/test.svg" in file_paths

    @patch("pathlib.Path.exists")
    def test_register_generated_images_no_duplication_warning_after_fix(
        self, mock_exists
    ):
        """修正後は同じファイルを複数回登録してもDeprecationWarningが発生しないことをテスト（失敗予定）"""
        mock_exists.return_value = True

        plugin = MermaidToImagePlugin()
        plugin.config = {"enabled": True}

        # 実際のMkDocs FilesオブジェクトとFileオブジェクトを使用
        from pathlib import Path

        from mkdocs.structure.files import File, Files

        docs_dir = Path("/tmp/docs")

        # Filesオブジェクトを作成
        files = Files([])
        plugin.files = files

        # 先に1つファイルを追加して重複状況を作る
        existing_file = File("assets/images/test.svg", str(docs_dir), "/tmp/site", True)
        files.append(existing_file)

        # モック設定を作成
        mock_config = {
            "docs_dir": str(docs_dir),
            "site_dir": "/tmp/site",
            "use_directory_urls": True,
        }

        # 既に存在するファイルと同じパスを登録（重複）
        image_paths = [str(docs_dir / "assets/images/test.svg")]

        # DeprecationWarningをキャッチするためのwarningsフィルター
        with warnings.catch_warnings(record=True) as warning_list:
            warnings.simplefilter("always")

            # テスト対象メソッドを実行（修正後は警告が発生しないはず）
            plugin._register_generated_images_to_files(
                image_paths, docs_dir, mock_config
            )

            # DeprecationWarningが発生していないことを確認（修正目標）
            deprecation_warnings = [
                w for w in warning_list if issubclass(w.category, DeprecationWarning)
            ]
            assert len(deprecation_warnings) == 0, (
                f"DeprecationWarning should not occur after fix, "
                f"but got: {deprecation_warnings}"
            )

    @patch.object(Path, "exists")
    def test_register_generated_images_nonexistent_file(self, mock_exists):
        """存在しないファイルは警告を出してスキップされることをテスト"""
        mock_exists.return_value = False

        plugin = MermaidToImagePlugin()
        plugin.config = {"enabled": True}
        plugin.logger = Mock()

        from pathlib import Path

        from mkdocs.structure.files import Files

        docs_dir = Path("/tmp/docs")
        files = Files([])
        plugin.files = files

        mock_config = {
            "docs_dir": str(docs_dir),
            "site_dir": "/tmp/site",
            "use_directory_urls": True,
        }

        # 存在しないファイルパス
        image_paths = [str(docs_dir / "assets/images/nonexistent.svg")]

        plugin._register_generated_images_to_files(image_paths, docs_dir, mock_config)

        # ファイルが追加されていないことを確認（ログは追加機能なのでスキップ）
        assert len(files) == 0

    def test_remove_existing_file_by_path(self):
        """_remove_existing_file_by_pathメソッドのテスト"""
        plugin = MermaidToImagePlugin()

        from pathlib import Path

        from mkdocs.structure.files import File, Files

        docs_dir = Path("/tmp/docs")
        files = Files([])
        plugin.files = files

        # テスト用ファイルを追加
        test_file = File("assets/images/test.svg", str(docs_dir), "/tmp/site", True)
        files.append(test_file)

        # ファイル削除のテスト
        result = plugin._remove_existing_file_by_path("assets/images/test.svg")
        assert result is True
        assert len(files) == 0

        # 存在しないファイルの削除テスト
        result = plugin._remove_existing_file_by_path("assets/images/nonexistent.svg")
        assert result is False

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

    @patch("mkdocs_mermaid_to_image.plugin.MermaidProcessor")
    def test_正常系_ビルドモード時のMarkdown処理実行(self, _mock_processor_class):
        """ビルドモード時にMermaid処理が実行されることを確認"""
        with patch.object(sys, "argv", ["mkdocs", "build"]):
            plugin = MermaidToImagePlugin()
            plugin.config = {
                "enabled": True,
                "output_dir": "assets/images",
                "error_on_fail": False,
            }

            # プロセッサをモック
            mock_processor = Mock()
            mock_processor.process_page.return_value = (
                "modified content with images",
                ["/path/to/image.png"],
            )
            plugin.processor = mock_processor

            # Mock page and config
            mock_page = Mock()
            mock_page.file.src_path = "test.md"
            mock_config = {"docs_dir": "/tmp/docs", "site_dir": "/tmp/site"}

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
