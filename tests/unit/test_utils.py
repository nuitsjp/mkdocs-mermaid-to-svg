"""
ユーティリティ関数のテスト
このファイルでは、mkdocs_mermaid_to_image.utilsモジュールの各種ユーティリティ関数が正しく動作するかをテストします。

Python未経験者へのヒント：
- pytestを使ってテストを書いています。
- 各テスト関数は「test_」で始まります。
- assert文で「期待する結果」かどうかを検証します。
"""

import contextlib
import logging
import tempfile
from pathlib import Path
from unittest.mock import patch

from mkdocs_mermaid_to_image.utils import (
    clean_temp_file,
    ensure_directory,
    generate_image_filename,
    get_relative_path,
    get_temp_file_path,
    is_command_available,
    setup_logger,
)


class TestUtilityFunctions:
    """ユーティリティ関数のテストクラス"""

    def test_setup_logger(self):
        """setup_logger関数がLoggerインスタンスを正しく返すかテスト"""
        logger = setup_logger("test_logger", "DEBUG")

        # Loggerの型・名前・レベル・ハンドラ数を確認
        assert isinstance(logger, logging.Logger)
        assert logger.name == "test_logger"
        assert logger.level == logging.DEBUG
        assert len(logger.handlers) > 0

    def test_setup_logger_default_level(self):
        """ログレベル省略時はINFOになるかテスト"""
        logger = setup_logger("test_logger_default")

        assert isinstance(logger, logging.Logger)
        assert logger.level == logging.INFO

    def test_setup_logger_existing_logger(self):
        """同じ名前のLoggerを2回作ってもハンドラが増えないかテスト"""
        # 1回目のLogger作成
        logger1 = setup_logger("existing_logger", "DEBUG")
        initial_handlers = len(logger1.handlers)

        # 2回目のLogger作成（ハンドラ数が増えないことを確認）
        logger2 = setup_logger("existing_logger", "INFO")

        assert logger1 is logger2
        assert len(logger2.handlers) == initial_handlers

    def test_generate_image_filename(self):
        """画像ファイル名が正しく生成されるかテスト"""
        filename = generate_image_filename(
            "test/page.md", 0, "graph TD\n A --> B", "png"
        )

        # ファイル名の形式を確認
        assert filename.startswith("page_mermaid_0_")
        assert filename.endswith(".png")
        assert len(filename.split("_")) == 4  # page_mermaid_0_hash.png

    def test_generate_image_filename_different_content(self):
        """内容が異なるとファイル名も異なるかテスト"""
        filename1 = generate_image_filename("test.md", 0, "graph TD\n A --> B", "png")
        filename2 = generate_image_filename("test.md", 0, "graph TD\n C --> D", "png")

        # 内容が違えばファイル名も違う
        assert filename1 != filename2

    def test_generate_image_filename_svg_format(self):
        """SVG形式のファイル名が正しく生成されるかテスト"""
        filename = generate_image_filename("test.md", 1, "graph TD\n A --> B", "svg")

        assert filename.endswith(".svg")
        assert "_mermaid_1_" in filename

    def test_ensure_directory_new_directory(self):
        """新しいディレクトリが作成されるかテスト"""
        with tempfile.TemporaryDirectory() as temp_dir:
            new_dir = Path(temp_dir) / "new" / "nested" / "directory"

            ensure_directory(str(new_dir))

            assert new_dir.exists()
            assert new_dir.is_dir()

    def test_ensure_directory_existing_directory(self):
        """既存ディレクトリでもエラーにならないかテスト"""
        with tempfile.TemporaryDirectory() as temp_dir:
            # 既存ディレクトリでエラーが出ないことを確認
            ensure_directory(temp_dir)
            assert Path(temp_dir).exists()

    def test_get_temp_file_path(self):
        """一時ファイルのパスが正しく取得できるかテスト"""
        temp_path = get_temp_file_path(".mmd")

        assert temp_path.endswith(".mmd")
        # tempfile.NamedTemporaryFileはデフォルトでファイルを作成します

        # ファイルが存在すれば削除
        with contextlib.suppress(OSError):
            Path(temp_path).unlink()

    def test_get_temp_file_path_default_suffix(self):
        """拡張子省略時は.mmdになるかテスト"""
        temp_path = get_temp_file_path()

        assert temp_path.endswith(".mmd")

    def test_clean_temp_file_existing_file(self):
        """既存の一時ファイルが削除できるかテスト"""
        with tempfile.NamedTemporaryFile(delete=False) as temp_file:
            temp_path = temp_file.name

        # ファイルが存在することを確認
        assert Path(temp_path).exists()

        # 削除
        clean_temp_file(temp_path)

        # ファイルが削除されたことを確認
        assert not Path(temp_path).exists()

    def test_clean_temp_file_nonexistent_file(self):
        """存在しないファイルでもエラーにならないかテスト"""
        # 存在しないファイルでもエラーにならない
        clean_temp_file("/nonexistent/file/path")

    def test_get_relative_path(self):
        """相対パスが正しく計算されるかテスト"""
        # 画像ファイルと基準ディレクトリを指定
        file_path = "/home/user/project/images/diagram.png"
        base_path = "/home/user/project/docs"

        relative = get_relative_path(file_path, base_path)
        assert relative == "../images/diagram.png"

    def test_get_relative_path_same_directory(self):
        """同じディレクトリの場合の相対パス計算をテスト"""
        file_path = "/home/user/project/image.png"
        base_path = "/home/user/project"

        relative = get_relative_path(file_path, base_path)
        assert relative == "image.png"

    def test_get_relative_path_absolute_fallback(self):
        """相対パス計算が失敗する場合のフォールバックをテスト"""
        # WindowsパスとLinuxパスの混在例
        file_path = "C:\\Windows\\image.png"
        base_path = "/home/user/project"

        relative = get_relative_path(file_path, base_path)
        # Linux環境では相対パス計算を試みるので、ファイル名が含まれていればOK
        assert "image.png" in relative

    @patch("mkdocs_mermaid_to_image.utils.which")
    def test_is_command_available_true(self, mock_which):
        """コマンドが存在する場合Trueを返すかテスト"""
        mock_which.return_value = "/usr/bin/mmdc"

        result = is_command_available("mmdc")
        assert result is True
        mock_which.assert_called_once_with("mmdc")

    @patch("mkdocs_mermaid_to_image.utils.which")
    def test_is_command_available_false(self, mock_which):
        """コマンドが存在しない場合Falseを返すかテスト"""
        mock_which.return_value = None

        result = is_command_available("nonexistent-command")
        assert result is False
        mock_which.assert_called_once_with("nonexistent-command")
