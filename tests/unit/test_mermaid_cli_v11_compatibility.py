"""Test for mermaid-cli v11.6.0+ compatibility with correct format option."""

import tempfile
from pathlib import Path
from unittest.mock import patch

from mkdocs_mermaid_to_svg.image_generator import MermaidImageGenerator


class TestMermaidCliV11Compatibility:
    """Test mermaid-cli v11.6.0+ compatibility with updated format options."""

    def test_mmdc_command_uses_correct_format_option(self):
        """Test that mmdc command uses -e instead of -f for format specification."""
        config = {
            "mmdc_path": "mmdc",
            "theme": "default",
            "error_on_fail": False,
            "log_level": "INFO",
        }

        with tempfile.TemporaryDirectory() as temp_dir:
            input_file = Path(temp_dir) / "test.mmd"
            output_file = Path(temp_dir) / "test.svg"

            input_file.write_text("graph TD\n    A --> B")

            with patch(
                "mkdocs_mermaid_to_svg.image_generator.is_command_available"
            ) as mock_available:
                mock_available.return_value = True
                generator = MermaidImageGenerator(config)

                # _build_mmdc_command を直接テストして正しいオプションが使われる確認
                cmd, puppeteer_config_file, mermaid_config_file = (
                    generator._build_mmdc_command(
                        str(input_file), str(output_file), config
                    )
                )

                # コマンドに -e svg が含まれていることを確認（-f svg ではない）
                cmd_str = " ".join(cmd)
                assert (
                    "-e svg" in cmd_str
                ), f"Command should use '-e svg', got: {cmd_str}"
                assert (
                    "-f svg" not in cmd_str
                ), f"Command should not use '-f svg', got: {cmd_str}"

    def test_mmdc_command_format_generates_correct_arguments(self):
        """Test command line arguments formatting for mermaid-cli 11.6.0+."""
        config = {
            "mmdc_path": "mmdc",
            "theme": "default",
            "error_on_fail": False,
            "log_level": "INFO",
        }

        with tempfile.TemporaryDirectory() as temp_dir:
            input_file = str(Path(temp_dir) / "test.mmd")
            output_file = str(Path(temp_dir) / "test.svg")

            with patch(
                "mkdocs_mermaid_to_svg.image_generator.is_command_available"
            ) as mock_available:
                mock_available.return_value = True
                generator = MermaidImageGenerator(config)

                cmd, _, _ = generator._build_mmdc_command(
                    input_file, output_file, config
                )

                # 基本的なコマンド構造を確認
                expected_args = [
                    "mmdc",
                    "-i",
                    input_file,
                    "-o",
                    output_file,
                    "-e",
                    "svg",  # -f ではなく -e を使用
                ]

                # 基本引数の存在確認
                for i in range(0, len(expected_args), 2):
                    if i + 1 < len(expected_args):
                        assert (
                            expected_args[i] in cmd
                        ), f"Missing argument: {expected_args[i]}"
                        if expected_args[i] in ["-i", "-o", "-e"]:
                            arg_index = cmd.index(expected_args[i])
                            assert arg_index + 1 < len(
                                cmd
                            ), f"Missing value for {expected_args[i]}"
                            assert (
                                cmd[arg_index + 1] == expected_args[i + 1]
                            ), f"Wrong value for {expected_args[i]}"
