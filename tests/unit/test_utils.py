"""
ユーティリティ関数のテスト
このファイルでは、mkdocs_mermaid_to_image.utilsモジュールの各種ユーティリティ関数が正しく動作するかをテストします。

Python未経験者へのヒント：
- pytestを使ってテストを書いています。
- 各テスト関数は「test_」で始まります。
- assert文で「期待する結果」かどうかを検証します。
"""

import contextlib
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

from mkdocs_mermaid_to_image.utils import (
    clean_temp_file,
    ensure_directory,
    generate_image_filename,
    get_relative_path,
    get_temp_file_path,
    is_command_available,
)


class TestUtilityFunctions:
    """ユーティリティ関数のテストクラス"""

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

    def test_clean_temp_file_empty_path(self):
        """空のパスが渡された場合の早期リターンをテスト"""
        # Line 53: if not file_path: return
        clean_temp_file("")
        clean_temp_file(None)
        # Should not raise any exception

    @patch("mkdocs_mermaid_to_image.utils.Path.unlink")
    def test_clean_temp_file_permission_error(self, mock_unlink):
        """PermissionErrorが発生した場合の処理をテスト"""
        mock_unlink.side_effect = PermissionError("Access denied")

        with tempfile.NamedTemporaryFile(delete=False) as temp_file:
            temp_path = temp_file.name

        # Should not raise exception, but log warning
        clean_temp_file(temp_path)

        # Clean up
        with contextlib.suppress(OSError):
            Path(temp_path).unlink()

    @patch("mkdocs_mermaid_to_image.utils.Path.unlink")
    def test_clean_temp_file_os_error(self, mock_unlink):
        """OSErrorが発生した場合の処理をテスト"""
        mock_unlink.side_effect = OSError("File locked")

        with tempfile.NamedTemporaryFile(delete=False) as temp_file:
            temp_path = temp_file.name

        # Should not raise exception, but log warning
        clean_temp_file(temp_path)

        # Clean up
        with contextlib.suppress(OSError):
            Path(temp_path).unlink()

    def test_get_relative_path_empty_inputs(self):
        """空の入力値での早期リターンをテスト"""
        # Line 93: if not file_path or not base_path: return file_path
        assert get_relative_path("", "base") == ""
        assert get_relative_path("file", "") == "file"
        assert get_relative_path("", "") == ""

    @patch("mkdocs_mermaid_to_image.utils.os.path.relpath")
    def test_get_relative_path_value_error(self, mock_relpath):
        """ValueErrorが発生した場合のフォールバックをテスト"""
        mock_relpath.side_effect = ValueError("Cross-drive paths not supported")

        file_path = "C:\\file.txt"
        base_path = "/home/user"

        result = get_relative_path(file_path, base_path)
        assert result == file_path  # Should return original file_path


class TestCleanGeneratedImages:
    """clean_generated_images関数のテストクラス"""

    @patch("pathlib.Path.exists")
    @patch("pathlib.Path.unlink")
    def test_clean_generated_images_success(self, mock_unlink, mock_exists):
        """正常なクリーンアップのテスト"""
        from mkdocs_mermaid_to_image.utils import clean_generated_images

        mock_logger = Mock()
        image_paths = ["/path/to/image1.png", "/path/to/image2.svg"]
        mock_exists.return_value = True

        clean_generated_images(image_paths, mock_logger)

        assert mock_unlink.call_count == 2
        mock_logger.info.assert_called_with("Image cleanup: 2 cleaned, 0 errors")

    @patch("pathlib.Path.exists")
    @patch("pathlib.Path.unlink")
    def test_clean_generated_images_permission_error(self, mock_unlink, mock_exists):
        """権限エラー時のテスト"""
        from mkdocs_mermaid_to_image.utils import clean_generated_images

        mock_logger = Mock()
        image_paths = ["/path/to/image1.png"]
        mock_exists.return_value = True
        mock_unlink.side_effect = PermissionError("Permission denied")

        clean_generated_images(image_paths, mock_logger)

        # warning が複数回呼ばれる（個別エラー + 全体サマリー）
        assert mock_logger.warning.call_count >= 1
        # 最初の呼び出しが権限エラーメッセージかチェック
        warning_calls = [str(call) for call in mock_logger.warning.call_args_list]
        assert any("Permission denied" in call for call in warning_calls)

    @patch("pathlib.Path.exists")
    @patch("pathlib.Path.unlink")
    def test_clean_generated_images_os_error(self, mock_unlink, mock_exists):
        """OSエラー時のテスト"""
        from mkdocs_mermaid_to_image.utils import clean_generated_images

        mock_logger = Mock()
        image_paths = ["/path/to/image1.png"]
        mock_exists.return_value = True
        mock_unlink.side_effect = OSError("File locked")

        clean_generated_images(image_paths, mock_logger)

        # warning が呼ばれることを確認
        assert mock_logger.warning.call_count >= 1
        # OSError メッセージがあることをチェック
        warning_calls = [str(call) for call in mock_logger.warning.call_args_list]
        assert any("OSError" in call for call in warning_calls)

    def test_clean_generated_images_empty_list(self):
        """空のリストの場合のテスト"""
        from mkdocs_mermaid_to_image.utils import clean_generated_images

        mock_logger = Mock()

        clean_generated_images([], mock_logger)

        # 何も実行されない
        mock_logger.info.assert_not_called()
        mock_logger.warning.assert_not_called()

    @patch("pathlib.Path.exists")
    def test_clean_generated_images_nonexistent_files(self, mock_exists):
        """存在しないファイルの場合のテスト"""
        from mkdocs_mermaid_to_image.utils import clean_generated_images

        mock_logger = Mock()
        image_paths = ["/path/to/nonexistent.png"]
        mock_exists.return_value = False

        clean_generated_images(image_paths, mock_logger)

        # 存在しないファイルは削除されない（エラーでもない）
        mock_logger.info.assert_not_called()
        mock_logger.warning.assert_not_called()

    def test_clean_generated_images_empty_string_paths(self):
        """空文字列のパスが含まれる場合のテスト"""
        from mkdocs_mermaid_to_image.utils import clean_generated_images

        mock_logger = Mock()
        image_paths = ["", "/path/to/image.png", None]

        # 例外が発生せず正常に実行される
        clean_generated_images(image_paths, mock_logger)

    @patch("pathlib.Path.exists")
    @patch("pathlib.Path.unlink")
    def test_clean_generated_images_with_none_logger(self, mock_unlink, mock_exists):
        """loggerがNoneの場合のテスト"""
        from mkdocs_mermaid_to_image.utils import clean_generated_images

        image_paths = ["/path/to/image1.png", "/path/to/image2.svg"]
        mock_exists.return_value = True

        # loggerがNoneでも例外が発生しない
        clean_generated_images(image_paths, None)
