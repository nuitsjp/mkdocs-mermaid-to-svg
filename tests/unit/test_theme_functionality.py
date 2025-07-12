"""
テーマ機能のテスト
t_wada式TDDでテーマ機能を実装するためのテストファイル
"""

from unittest.mock import Mock, patch

import pytest

from mkdocs_mermaid_to_svg.image_generator import MermaidImageGenerator


class TestThemeFunctionality:
    """テーマ機能のテストクラス"""

    @pytest.fixture
    def basic_config(self):
        """テスト用の基本設定"""
        return {
            "mmdc_path": "mmdc",
            "output_dir": "assets/images",
            "theme": "default",
            "image_format": "svg",
            "error_on_fail": False,
            "log_level": "INFO",
            "css_file": None,
            "puppeteer_config": None,
            "mermaid_config": None,
        }

    @patch("mkdocs_mermaid_to_svg.image_generator.is_command_available")
    @patch("subprocess.run")
    def test_default_theme_not_passed_to_cli(
        self, mock_subprocess, mock_command_available, basic_config
    ):
        """デフォルトテーマの場合、-tオプションが渡されないことを確認"""
        mock_command_available.return_value = True
        mock_subprocess.return_value = Mock(returncode=0, stderr="")

        config = basic_config.copy()
        config["theme"] = "default"

        generator = MermaidImageGenerator(config)

        with (
            patch("tempfile.NamedTemporaryFile"),
            patch("builtins.open"),
            patch("os.path.exists", return_value=True),
        ):
            generator.generate("graph TD\n A --> B", "output.svg", config)

            # subprocessが呼ばれたことを確認
            mock_subprocess.assert_called_once()
            # 実際に呼ばれたコマンドを取得
        called_args = mock_subprocess.call_args[0][0]
        # print(f"DEBUG: Called command: {called_args}")  # デバッグ用（コメントアウト）

        # デフォルトテーマの場合、-tオプションが含まれないことを確認
        if "-t" in called_args:
            theme_index = called_args.index("-t")
            theme_value = called_args[theme_index + 1]
            # デフォルトテーマの場合は省略されるべき
            assert (
                theme_value != "default"
            ), f"Default theme should be omitted, but got: {theme_value}"

    @patch("mkdocs_mermaid_to_svg.image_generator.is_command_available")
    @patch("subprocess.run")
    def test_non_default_theme_passed_to_cli(
        self, mock_subprocess, mock_command_available, basic_config
    ):
        """非デフォルトテーマの場合、-tオプションが正しく渡されることを確認"""
        mock_command_available.return_value = True
        mock_subprocess.return_value = Mock(returncode=0, stderr="")

        config = basic_config.copy()
        config["theme"] = "dark"

        generator = MermaidImageGenerator(config)

        with (
            patch("tempfile.NamedTemporaryFile"),
            patch("builtins.open"),
            patch("os.path.exists", return_value=True),
        ):
            generator.generate("graph TD\n A --> B", "output.svg", config)

            # subprocessが呼ばれたことを確認
            mock_subprocess.assert_called_once()

            # 実際に呼ばれたコマンドを取得
            called_args = mock_subprocess.call_args[0][0]

            # -tオプションが含まれることを確認
            assert (
                "-t" in called_args
            ), f"Theme option not found in command: {called_args}"

            # テーマ値が正しく設定されていることを確認
            theme_index = called_args.index("-t")
            theme_value = called_args[theme_index + 1]
            assert theme_value == "dark", f"Expected 'dark' theme, got: {theme_value}"

    @pytest.mark.parametrize("theme", ["default", "dark", "forest", "neutral"])
    @patch("mkdocs_mermaid_to_svg.image_generator.is_command_available")
    @patch("subprocess.run")
    def test_all_themes_handled_correctly(
        self, mock_subprocess, mock_command_available, basic_config, theme
    ):
        """全テーマが正しく処理されることを確認"""
        mock_command_available.return_value = True
        mock_subprocess.return_value = Mock(returncode=0, stderr="")

        config = basic_config.copy()
        config["theme"] = theme

        generator = MermaidImageGenerator(config)

        with (
            patch("tempfile.NamedTemporaryFile"),
            patch("builtins.open"),
            patch("os.path.exists", return_value=True),
        ):
            generator.generate("graph TD\n A --> B", "output.svg", config)

            # subprocessが呼ばれたことを確認
            mock_subprocess.assert_called_once()

            # 実際に呼ばれたコマンドを取得
            called_args = mock_subprocess.call_args[0][0]

            if theme == "default":
                # デフォルトテーマの場合は-tオプションが省略されるべき
                if "-t" in called_args:
                    theme_index = called_args.index("-t")
                    theme_value = called_args[theme_index + 1]
                    assert theme_value != "default", "Default theme should be omitted"
            else:
                # 非デフォルトテーマの場合は-tオプションが含まれるべき
                assert "-t" in called_args, f"Theme option not found for {theme}"
                theme_index = called_args.index("-t")
                theme_value = called_args[theme_index + 1]
                assert (
                    theme_value == theme
                ), f"Expected '{theme}' theme, got: {theme_value}"

    @patch("mkdocs_mermaid_to_svg.image_generator.is_command_available")
    @patch("subprocess.run")
    def test_theme_parameter_precedence(
        self, mock_subprocess, mock_command_available, basic_config
    ):
        """個別設定のテーマが全体設定より優先されることを確認"""
        mock_command_available.return_value = True
        mock_subprocess.return_value = Mock(returncode=0, stderr="")

        # 全体設定ではdefault、個別設定ではdark
        config = basic_config.copy()
        config["theme"] = "default"

        individual_config = {"theme": "dark"}

        generator = MermaidImageGenerator(config)

        with (
            patch("tempfile.NamedTemporaryFile"),
            patch("builtins.open"),
            patch("os.path.exists", return_value=True),
        ):
            generator.generate("graph TD\n A --> B", "output.svg", individual_config)

            # subprocessが呼ばれたことを確認
            mock_subprocess.assert_called_once()

            # 実際に呼ばれたコマンドを取得
            called_args = mock_subprocess.call_args[0][0]

            # 個別設定のdarkテーマが使われることを確認
            assert (
                "-t" in called_args
            ), f"Theme option not found in command: {called_args}"
            theme_index = called_args.index("-t")
            theme_value = called_args[theme_index + 1]
            assert (
                theme_value == "dark"
            ), f"Expected 'dark' theme from individual config, got: {theme_value}"
