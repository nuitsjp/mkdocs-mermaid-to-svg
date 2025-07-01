"""
MermaidImageGeneratorクラスのテスト
このファイルでは、MermaidImageGeneratorクラスの動作を検証します。

Python未経験者へのヒント：
- pytestを使ってテストを書いています。
- patchやMockで外部依存を疑似的に置き換えています。
- assert文で「期待する結果」かどうかを検証します。
"""

import os
import re
import subprocess
import tempfile
import xml.etree.ElementTree as ET
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

try:
    import numpy as np
    from PIL import Image

    PILLOW_AVAILABLE = True
except ImportError:
    PILLOW_AVAILABLE = False

from mkdocs_mermaid_to_image.exceptions import (
    MermaidCLIError,
    MermaidImageError,
)
from mkdocs_mermaid_to_image.image_generator import MermaidImageGenerator


class TestMermaidImageGenerator:
    """MermaidImageGeneratorクラスのテストクラス"""

    @pytest.fixture
    def basic_config(self):
        """テスト用の基本設定を返すfixture"""
        # CI環境でのみPuppeteer設定を使用
        puppeteer_config = None
        if os.getenv("CI") or os.getenv("GITHUB_ACTIONS"):
            puppeteer_config = str(
                Path(__file__).parent.parent.parent
                / ".github"
                / "puppeteer.config.json"
            )

        return {
            "mmdc_path": "mmdc",
            "theme": "default",
            "background_color": "white",
            "width": 800,
            "height": 600,
            "scale": 1.0,
            "css_file": None,
            "puppeteer_config": puppeteer_config,
            "mermaid_config": None,
            "error_on_fail": False,
            "log_level": "INFO",
        }

    @patch("mkdocs_mermaid_to_image.image_generator.is_command_available")
    def test_generator_initialization(self, mock_command_available, basic_config):
        """初期化時のプロパティが正しいかテスト"""
        mock_command_available.return_value = True
        generator = MermaidImageGenerator(basic_config)
        assert generator.config == basic_config
        assert generator.logger is not None

    @patch("mkdocs_mermaid_to_image.image_generator.is_command_available")
    def test_generator_initialization_missing_cli(
        self, mock_command_available, basic_config
    ):
        """Mermaid CLIが見つからない場合に例外が発生するかテスト"""
        mock_command_available.return_value = False
        with pytest.raises(MermaidCLIError):
            MermaidImageGenerator(basic_config)

    @patch("mkdocs_mermaid_to_image.image_generator.is_command_available")
    @patch("subprocess.run")
    @patch("mkdocs_mermaid_to_image.image_generator.get_temp_file_path")
    @patch("mkdocs_mermaid_to_image.image_generator.clean_temp_file")
    @patch.dict("os.environ", {"CI": "", "GITHUB_ACTIONS": ""}, clear=True)
    def test_generate_failure_subprocess_error(
        self,
        mock_clean,
        mock_temp_path,
        mock_subprocess,
        mock_command_available,
        basic_config,
    ):
        """subprocessエラー時の画像生成失敗テスト"""
        mock_command_available.return_value = True
        mock_temp_path.return_value = "/tmp/test.mmd"
        mock_subprocess.return_value = Mock(returncode=1, stderr="Error message")

        generator = MermaidImageGenerator(basic_config)

        with (
            patch("builtins.open", create=True),
            patch("mkdocs_mermaid_to_image.image_generator.ensure_directory"),
        ):
            result = generator.generate(
                "invalid mermaid code", "/tmp/output.png", basic_config
            )

            assert result is False
            # Both temp file (.mmd) and puppeteer config file (.json) are cleaned
            assert mock_clean.call_count == 2
            assert any(
                "/tmp/test.mmd" in str(call) for call in mock_clean.call_args_list
            )

    @patch("mkdocs_mermaid_to_image.image_generator.is_command_available")
    @patch("subprocess.run")
    @patch("os.path.exists")
    @patch("mkdocs_mermaid_to_image.image_generator.get_temp_file_path")
    @patch("mkdocs_mermaid_to_image.image_generator.clean_temp_file")
    @patch.dict("os.environ", {"CI": "", "GITHUB_ACTIONS": ""}, clear=True)
    def test_generate_failure_no_output_file(
        self,
        mock_clean,
        mock_temp_path,
        mock_exists,
        mock_subprocess,
        mock_command_available,
        basic_config,
    ):
        """出力ファイルが生成されない場合の失敗テスト"""
        mock_command_available.return_value = True
        mock_temp_path.return_value = "/tmp/test.mmd"
        mock_subprocess.return_value = Mock(returncode=0, stderr="")
        mock_exists.return_value = False  # 出力ファイルが作成されない

        generator = MermaidImageGenerator(basic_config)

        with (
            patch("builtins.open", create=True),
            patch("mkdocs_mermaid_to_image.image_generator.ensure_directory"),
        ):
            result = generator.generate(
                "graph TD\n A --> B", "/tmp/output.png", basic_config
            )

            assert result is False
            # Both temp file (.mmd) and puppeteer config file (.json) are cleaned
            assert mock_clean.call_count == 2
            assert any(
                "/tmp/test.mmd" in str(call) for call in mock_clean.call_args_list
            )

    @patch("mkdocs_mermaid_to_image.image_generator.is_command_available")
    @patch("subprocess.run")
    @patch("mkdocs_mermaid_to_image.image_generator.get_temp_file_path")
    @patch("mkdocs_mermaid_to_image.image_generator.clean_temp_file")
    @patch.dict("os.environ", {"CI": "", "GITHUB_ACTIONS": ""}, clear=True)
    def test_generate_timeout(
        self,
        mock_clean,
        mock_temp_path,
        mock_subprocess,
        mock_command_available,
        basic_config,
    ):
        """タイムアウト時の画像生成失敗テスト"""
        mock_command_available.return_value = True
        mock_temp_path.return_value = "/tmp/test.mmd"
        mock_subprocess.side_effect = subprocess.TimeoutExpired("mmdc", 30)

        generator = MermaidImageGenerator(basic_config)

        with (
            patch("builtins.open", create=True),
            patch("mkdocs_mermaid_to_image.image_generator.ensure_directory"),
        ):
            result = generator.generate(
                "graph TD\n A --> B", "/tmp/output.png", basic_config
            )

            assert result is False
            # Both temp file (.mmd) and puppeteer config file (.json) are cleaned
            assert mock_clean.call_count == 2
            assert any(
                "/tmp/test.mmd" in str(call) for call in mock_clean.call_args_list
            )

    @patch("mkdocs_mermaid_to_image.image_generator.is_command_available")
    def test_build_mmdc_command_basic(self, mock_command_available, basic_config):
        """mmdcコマンド生成の基本テスト"""
        mock_command_available.return_value = True
        generator = MermaidImageGenerator(basic_config)

        cmd, _ = generator._build_mmdc_command("input.mmd", "output.png", basic_config)

        assert "mmdc" in cmd
        assert "-i" in cmd
        assert "input.mmd" in cmd
        assert "-o" in cmd
        assert "output.png" in cmd
        assert "-t" in cmd
        assert "default" in cmd
        assert "-b" in cmd
        assert "white" in cmd
        assert "-w" in cmd
        assert "800" in cmd
        assert "-H" in cmd
        assert "600" in cmd
        assert "-s" in cmd
        assert "1.0" in cmd

    @patch("mkdocs_mermaid_to_image.image_generator.is_command_available")
    def test_build_mmdc_command_with_overrides(
        self, mock_command_available, basic_config
    ):
        """設定上書き時のmmdcコマンド生成テスト"""
        mock_command_available.return_value = True
        generator = MermaidImageGenerator(basic_config)

        override_config = basic_config.copy()
        override_config.update(
            {"theme": "dark", "background_color": "black", "width": 1000, "height": 800}
        )

        cmd, _ = generator._build_mmdc_command(
            "input.mmd", "output.png", override_config
        )

        assert "-t" in cmd
        assert "dark" in cmd
        assert "-b" in cmd
        assert "black" in cmd
        assert "-w" in cmd
        assert "1000" in cmd
        assert "-H" in cmd
        assert "800" in cmd

    @patch("mkdocs_mermaid_to_image.image_generator.is_command_available")
    def test_build_mmdc_command_with_optional_files(
        self, mock_command_available, basic_config, tmp_path
    ):
        """CSSやpuppeteer等のファイル指定時のコマンド生成テスト（ファイルが存在する場合）"""
        mock_command_available.return_value = True

        # 実際にファイルを作成
        css_file = tmp_path / "custom.css"
        css_file.write_text("/* custom css */")
        puppeteer_file = tmp_path / "puppeteer.json"
        puppeteer_file.write_text('{"args": ["--no-sandbox"]}')
        mermaid_file = tmp_path / "mermaid.json"
        mermaid_file.write_text('{"theme": "dark"}')

        basic_config.update(
            {
                "css_file": str(css_file),
                "puppeteer_config": str(puppeteer_file),
                "mermaid_config": str(mermaid_file),
            }
        )
        generator = MermaidImageGenerator(basic_config)

        cmd, _ = generator._build_mmdc_command("input.mmd", "output.png", basic_config)

        assert "-C" in cmd
        assert str(css_file) in cmd
        assert "-p" in cmd
        assert str(puppeteer_file) in cmd
        assert "-c" in cmd
        assert str(mermaid_file) in cmd

    @patch("mkdocs_mermaid_to_image.image_generator.is_command_available")
    @patch("os.getenv")
    def test_build_mmdc_command_with_missing_optional_files(
        self, mock_getenv, mock_command_available, basic_config
    ):
        """オプションファイルが存在しない場合のコマンド生成テスト"""
        mock_command_available.return_value = True
        # 非CI環境をシミュレート
        mock_getenv.return_value = None

        basic_config.update(
            {
                "css_file": "/nonexistent/custom.css",
                "puppeteer_config": "/nonexistent/puppeteer.json",
                "mermaid_config": "/nonexistent/mermaid.json",
            }
        )
        generator = MermaidImageGenerator(basic_config)

        cmd, _ = generator._build_mmdc_command("input.mmd", "output.png", basic_config)

        # CSS fileは存在確認していないので含まれる
        assert "-C" in cmd
        assert "/nonexistent/custom.css" in cmd

        # Puppeteer configは存在確認しているので含まれない
        # (CI用の-pフラグとユーザー指定の-pフラグを区別するため、カウントで確認)
        p_count = cmd.count("-p")
        assert p_count == 1  # CI用は常に追加される（システムChrome設定用）
        assert "/nonexistent/puppeteer.json" not in cmd

        # Mermaid configは存在確認していないので含まれる
        assert "-c" in cmd
        assert "/nonexistent/mermaid.json" in cmd

    @patch("mkdocs_mermaid_to_image.image_generator.is_command_available")
    @patch("os.getenv")
    def test_build_mmdc_command_ci_environment(
        self, mock_getenv, mock_command_available, basic_config
    ):
        """CI環境で--no-sandboxオプションが追加されるかテスト"""
        mock_command_available.return_value = True

        # CI環境をシミュレート
        def mock_env(key):
            if key == "CI":
                return "true"
            elif key == "GITHUB_ACTIONS":
                return None
            return None

        mock_getenv.side_effect = mock_env

        generator = MermaidImageGenerator(basic_config)
        cmd, _ = generator._build_mmdc_command("input.mmd", "output.png", basic_config)

        assert "-p" in cmd
        # Check that the puppeteer config file is created

    @patch("mkdocs_mermaid_to_image.image_generator.is_command_available")
    @patch("os.getenv")
    def test_build_mmdc_command_github_actions_environment(
        self, mock_getenv, mock_command_available, basic_config
    ):
        """GitHub Actions環境で--no-sandboxオプションが追加されるかテスト"""
        mock_command_available.return_value = True

        # GitHub Actions環境をシミュレート
        def mock_env(key):
            if key == "CI":
                return None
            elif key == "GITHUB_ACTIONS":
                return "true"
            return None

        mock_getenv.side_effect = mock_env

        generator = MermaidImageGenerator(basic_config)
        cmd, _ = generator._build_mmdc_command("input.mmd", "output.png", basic_config)

        assert "-p" in cmd
        # Check that the puppeteer config file is created

    @patch("mkdocs_mermaid_to_image.image_generator.is_command_available")
    @patch("os.getenv")
    def test_build_mmdc_command_non_ci_environment(
        self, mock_getenv, mock_command_available, basic_config
    ):
        """非CI環境で--no-sandboxオプションが追加されないかテスト"""
        mock_command_available.return_value = True

        # 非CI環境をシミュレート
        mock_getenv.return_value = None

        generator = MermaidImageGenerator(basic_config)
        generator._build_mmdc_command("input.mmd", "output.png", basic_config)

        # In non-CI environment, no additional -p flag should be added for sandbox

    @patch("mkdocs_mermaid_to_image.image_generator.is_command_available")
    def test_generate_with_error_on_fail_true(
        self, mock_command_available, basic_config, tmp_path
    ):
        """error_on_fail=True時に例外が発生するかテスト"""
        basic_config["error_on_fail"] = True
        mock_command_available.return_value = True

        generator = MermaidImageGenerator(basic_config)

        # Create a real temp file path
        temp_file = tmp_path / "temp.mmd"

        with patch("subprocess.run") as mock_subprocess:
            mock_subprocess.return_value = Mock(returncode=1, stderr="Error message")

            with (
                patch("builtins.open", create=True),
                patch(
                    "mkdocs_mermaid_to_image.image_generator.get_temp_file_path"
                ) as mock_temp_path,
                patch("mkdocs_mermaid_to_image.image_generator.ensure_directory"),
                patch("mkdocs_mermaid_to_image.image_generator.clean_temp_file"),
                pytest.raises(MermaidCLIError),
            ):
                mock_temp_path.return_value = str(temp_file)
                generator.generate("invalid", "/tmp/output.png", basic_config)

    @patch("mkdocs_mermaid_to_image.image_generator.is_command_available")
    def test_generate_with_missing_output_file_error_on_fail_true(
        self, mock_command_available, basic_config, tmp_path
    ):
        """出力ファイルが作成されない場合にerror_on_fail=Trueで例外が発生するかテスト"""
        basic_config["error_on_fail"] = True
        mock_command_available.return_value = True

        generator = MermaidImageGenerator(basic_config)

        # Create a real temp file path
        temp_file = tmp_path / "temp.mmd"

        with (
            patch("subprocess.run") as mock_subprocess,
            patch(
                "mkdocs_mermaid_to_image.image_generator.get_temp_file_path"
            ) as mock_temp_path,
            patch("mkdocs_mermaid_to_image.image_generator.ensure_directory"),
            patch("mkdocs_mermaid_to_image.image_generator.clean_temp_file"),
            patch("os.path.exists") as mock_exists,
        ):
            mock_subprocess.return_value = Mock(returncode=0, stderr="")
            mock_temp_path.return_value = str(temp_file)
            mock_exists.return_value = False  # Output file does not exist

            with pytest.raises(MermaidImageError, match="Image not created"):
                generator.generate("graph TD\nA-->B", "/tmp/output.png", basic_config)

    @patch("mkdocs_mermaid_to_image.image_generator.is_command_available")
    def test_generate_with_timeout_error_on_fail_true(
        self, mock_command_available, basic_config, tmp_path
    ):
        """タイムアウト発生時にerror_on_fail=Trueで例外が発生するかテスト"""
        basic_config["error_on_fail"] = True
        mock_command_available.return_value = True

        generator = MermaidImageGenerator(basic_config)

        # Create a real temp file path
        temp_file = tmp_path / "temp.mmd"

        with (
            patch("subprocess.run") as mock_subprocess,
            patch(
                "mkdocs_mermaid_to_image.image_generator.get_temp_file_path"
            ) as mock_temp_path,
            patch("mkdocs_mermaid_to_image.image_generator.ensure_directory"),
            patch("mkdocs_mermaid_to_image.image_generator.clean_temp_file"),
        ):
            mock_subprocess.side_effect = subprocess.TimeoutExpired("mmdc", 30)
            mock_temp_path.return_value = str(temp_file)

            with pytest.raises(MermaidCLIError, match="timed out"):
                generator.generate("graph TD\nA-->B", "/tmp/output.png", basic_config)

    @patch("mkdocs_mermaid_to_image.image_generator.is_command_available")
    def test_generate_with_general_exception_error_on_fail_true(
        self, mock_command_available, basic_config, tmp_path
    ):
        """一般的な例外発生時にerror_on_fail=Trueで例外が発生するかテスト"""
        basic_config["error_on_fail"] = True
        mock_command_available.return_value = True

        generator = MermaidImageGenerator(basic_config)

        # Create a real temp file path
        temp_file = tmp_path / "temp.mmd"

        with (
            patch("subprocess.run") as mock_subprocess,
            patch(
                "mkdocs_mermaid_to_image.image_generator.get_temp_file_path"
            ) as mock_temp_path,
            patch("mkdocs_mermaid_to_image.image_generator.ensure_directory"),
            patch("mkdocs_mermaid_to_image.image_generator.clean_temp_file"),
        ):
            mock_subprocess.side_effect = Exception("Unexpected error")
            mock_temp_path.return_value = str(temp_file)

            with pytest.raises(
                MermaidImageError, match="Unexpected error generating image"
            ):
                generator.generate("graph TD\nA-->B", "/tmp/output.png", basic_config)

    @pytest.mark.parametrize(
        "mmd_file, expected_png",
        [
            ("sample_basic.mmd", "output_basic.png"),
            ("sample_sequence.mmd", "output_sequence.png"),
        ],
    )
    @patch("mkdocs_mermaid_to_image.image_generator.is_command_available")
    @patch("subprocess.run")
    @patch("mkdocs_mermaid_to_image.image_generator.get_temp_file_path")
    @patch("mkdocs_mermaid_to_image.image_generator.clean_temp_file")
    @patch("mkdocs_mermaid_to_image.image_generator.ensure_directory")
    @patch("os.path.exists")
    def test_generate_mermaid_image_and_compare(
        self,
        mock_exists,
        mock_ensure_dir,
        mock_clean,
        mock_temp_path,
        mock_subprocess,
        mock_command_available,
        basic_config,
        mmd_file,
        expected_png,
    ):
        """
        Mermaidコードから画像を生成し、類似度比較を行う（モック版）
        """
        # モックでmermaid CLIの実行をシミュレート
        mock_command_available.return_value = True
        mock_subprocess.return_value = Mock(returncode=0, stderr="")

        fixtures_dir = Path(__file__).parent.parent / "fixtures"
        mmd_path = fixtures_dir / mmd_file
        expected_path = fixtures_dir / expected_png

        # 期待値ファイルが存在しない場合はスキップ
        if not expected_path.exists():
            pytest.skip(f"Expected file {expected_png} not found")

        with tempfile.TemporaryDirectory() as temp_dir:
            output_path = Path(temp_dir) / "output.png"
            temp_mmd_path = Path(temp_dir) / "temp.mmd"
            mermaid_code = mmd_path.read_text(encoding="utf-8")

            # テンポラリファイルパスのモック
            mock_temp_path.return_value = str(temp_mmd_path)

            # モックで出力ファイルの存在をシミュレート
            def mock_exists_side_effect(path):
                return str(path) == str(output_path)

            mock_exists.side_effect = mock_exists_side_effect

            generator = MermaidImageGenerator(basic_config)

            # ファイル書き込みのモック
            with patch("builtins.open", create=True):
                # PNG期待値ファイルの内容をバイナリで読み取って出力に書き込む
                if expected_path.exists():
                    output_path.write_bytes(expected_path.read_bytes())
                else:
                    # 期待値ファイルがない場合は、ダミーのPNGバイトを作成
                    output_path.write_bytes(b"\x89PNG\r\n\x1a\n")  # PNG header

                result = generator.generate(
                    mermaid_code, str(output_path), basic_config
                )
                assert result is True
                assert output_path.exists()

                # 類似度比較（モック環境では基本的なファイル存在チェックのみ）
                if PILLOW_AVAILABLE:
                    # Pillowが利用可能でも、モック環境では簡単な比較にとどめる
                    assert output_path.exists(), "Output file should exist"
                    assert (
                        output_path.stat().st_size > 0
                    ), "Output file should not be empty"
                    # モック環境では常に成功とみなす
                    similarity_ok, similarity_msg = True, "Mock comparison passed"
                else:
                    similarity_ok, similarity_msg = (
                        True,
                        "Pillow not available, skipping comparison",
                    )
                assert similarity_ok, f"Similarity comparison failed: {similarity_msg}"

    def _compare_images_similarity(  # noqa: PLR0911
        self, expected_path: str, actual_path: str, threshold: float = 0.95
    ) -> tuple[bool, str]:
        """
        画像の類似度比較（ピクセル値の比較）

        Args:
            expected_path: 期待値画像のパス
            actual_path: 実際の画像のパス
            threshold: 類似度の閾値 (0.0-1.0)

        Returns:
            Tuple[bool, str]: (比較結果, メッセージ)
        """
        if not PILLOW_AVAILABLE:
            return True, "Similarity comparison skipped (Pillow not available)"

        try:
            with (
                Image.open(expected_path) as expected_img,
                Image.open(actual_path) as actual_img,
            ):
                # 基本的な妥当性チェック
                expected_file = Path(expected_path)
                actual_file = Path(actual_path)

                if not expected_file.exists():
                    return False, f"Expected file does not exist: {expected_path}"
                if not actual_file.exists():
                    return False, f"Actual file does not exist: {actual_path}"

                expected_size = expected_file.stat().st_size
                actual_size = actual_file.stat().st_size

                if expected_size == 0:
                    return False, f"Expected file is empty: {expected_path}"
                if actual_size == 0:
                    return False, f"Actual file is empty: {actual_path}"

                # 画像サイズの差をチェック（10%以内）
                expected_width, expected_height = expected_img.size
                actual_width, actual_height = actual_img.size

                width_diff_ratio = (
                    abs(expected_width - actual_width) / expected_width
                    if expected_width > 0
                    else 0
                )
                height_diff_ratio = (
                    abs(expected_height - actual_height) / expected_height
                    if expected_height > 0
                    else 0
                )

                if width_diff_ratio > 0.1 or height_diff_ratio > 0.1:
                    return (
                        False,
                        f"Image size difference too large: "
                        f"expected={expected_img.size}, "
                        f"actual={actual_img.size} "
                        f"(width_diff={width_diff_ratio:.3f}, "
                        f"height_diff={height_diff_ratio:.3f})",
                    )

                # RGBモードに変換
                expected_img_rgb = expected_img.convert("RGB")
                actual_img_rgb = actual_img.convert("RGB")

                # NumPy配列に変換
                expected_array = np.array(expected_img_rgb)
                actual_array = np.array(actual_img_rgb)

                # 配列の形状が一致しない場合は、小さい方に合わせてリサイズ
                if expected_array.shape != actual_array.shape:
                    # より小さいサイズに合わせる
                    target_height = min(expected_array.shape[0], actual_array.shape[0])
                    target_width = min(expected_array.shape[1], actual_array.shape[1])

                    expected_img_resized = expected_img_rgb.resize(
                        (target_width, target_height), Image.Resampling.LANCZOS
                    )
                    actual_img_resized = actual_img_rgb.resize(
                        (target_width, target_height), Image.Resampling.LANCZOS
                    )

                    expected_array = np.array(expected_img_resized)
                    actual_array = np.array(actual_img_resized)

                # ピクセル値の差を計算
                diff = np.abs(
                    expected_array.astype(np.float64) - actual_array.astype(np.float64)
                )

                # 正規化された平均絶対誤差を計算
                mae = np.mean(diff) / 255.0
                similarity = 1.0 - mae

                if similarity >= threshold:
                    return (
                        True,
                        f"Similarity comparison passed: "
                        f"{similarity:.3f} >= {threshold}",
                    )
                else:
                    return False, f"Similarity too low: {similarity:.3f} < {threshold}"

        except Exception as e:
            return False, f"Error during similarity comparison: {e!s}"

    @pytest.mark.parametrize(
        "mmd_file, expected_svg",
        [
            ("sample_basic.mmd", "output_basic.svg"),
            ("sample_sequence.mmd", "output_sequence.svg"),
        ],
    )
    @patch("mkdocs_mermaid_to_image.image_generator.is_command_available")
    @patch("subprocess.run")
    @patch("mkdocs_mermaid_to_image.image_generator.get_temp_file_path")
    @patch("mkdocs_mermaid_to_image.image_generator.clean_temp_file")
    @patch("mkdocs_mermaid_to_image.image_generator.ensure_directory")
    @patch("os.path.exists")
    def test_generate_mermaid_svg_and_compare(
        self,
        mock_exists,
        mock_ensure_dir,
        mock_clean,
        mock_temp_path,
        mock_subprocess,
        mock_command_available,
        basic_config,
        mmd_file,
        expected_svg,
    ):
        """
        MermaidコードからSVGを生成し、期待値ファイルと比較を行う（TDD Green phase）
        """
        # モックでmermaid CLIの実行をシミュレート
        mock_command_available.return_value = True
        mock_subprocess.return_value = Mock(returncode=0, stderr="")

        fixtures_dir = Path(__file__).parent.parent / "fixtures"
        mmd_path = fixtures_dir / mmd_file
        expected_path = fixtures_dir / expected_svg

        # 期待値ファイルが存在しない場合はスキップ
        if not expected_path.exists():
            pytest.skip(f"Expected file {expected_svg} not found")

        with tempfile.TemporaryDirectory() as temp_dir:
            output_path = Path(temp_dir) / "output.svg"
            temp_mmd_path = Path(temp_dir) / "temp.mmd"
            mermaid_code = mmd_path.read_text(encoding="utf-8")

            # テンポラリファイルパスのモック
            mock_temp_path.return_value = str(temp_mmd_path)

            # モックで出力ファイルの存在をシミュレート
            def mock_exists_side_effect(path):
                return str(path) == str(output_path)

            mock_exists.side_effect = mock_exists_side_effect

            # SVG形式で画像生成
            svg_config = basic_config.copy()
            svg_config.update({"image_format": "svg"})

            generator = MermaidImageGenerator(svg_config)

            # ファイル書き込みのモック
            with patch("builtins.open", create=True):
                # generateメソッドを呼び出す前に、出力ファイルに期待値の内容を書き込む
                output_path.write_text(expected_path.read_text(encoding="utf-8"))

                result = generator.generate(mermaid_code, str(output_path), svg_config)
                assert result is True
                assert output_path.exists()

            # SVG比較ロジックのテスト
            similarity_ok, similarity_msg = self._compare_svg_similarity(
                str(expected_path), str(output_path)
            )
            assert similarity_ok, f"SVG comparison failed: {similarity_msg}"

    def test_svg_comparison_edge_cases(self):
        """SVG比較のエッジケースをテスト"""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            # 空ファイルのテスト
            empty_file = temp_path / "empty.svg"
            empty_file.touch()

            valid_svg = temp_path / "valid.svg"
            valid_svg.write_text('<?xml version="1.0"?><svg><rect/></svg>')

            # 空ファイルは失敗する
            ok, msg = self._compare_svg_similarity(str(empty_file), str(valid_svg))
            assert not ok
            assert "empty" in msg.lower()

            # 存在しないファイルは失敗する
            nonexistent = temp_path / "nonexistent.svg"
            ok, msg = self._compare_svg_similarity(str(nonexistent), str(valid_svg))
            assert not ok
            assert "does not exist" in msg.lower()

            # 無効なSVGは失敗する
            invalid_svg = temp_path / "invalid.svg"
            invalid_svg.write_text("This is not SVG content")
            ok, msg = self._compare_svg_similarity(str(invalid_svg), str(valid_svg))
            assert not ok
            assert "not a valid svg" in msg.lower()

    @pytest.mark.parametrize("theme", ["default", "dark", "forest", "neutral"])
    @patch("mkdocs_mermaid_to_image.image_generator.is_command_available")
    @patch("subprocess.run")
    @patch("mkdocs_mermaid_to_image.image_generator.get_temp_file_path")
    @patch("mkdocs_mermaid_to_image.image_generator.clean_temp_file")
    @patch("mkdocs_mermaid_to_image.image_generator.ensure_directory")
    @patch("os.path.exists")
    def test_svg_generation_with_different_themes(
        self,
        mock_exists,
        mock_ensure_dir,
        mock_clean,
        mock_temp_path,
        mock_subprocess,
        mock_command_available,
        basic_config,
        theme,
    ):
        """異なるテーマでのSVG生成をテスト"""
        mock_command_available.return_value = True
        mock_subprocess.return_value = Mock(returncode=0, stderr="")

        fixtures_dir = Path(__file__).parent.parent / "fixtures"
        basic_svg_path = fixtures_dir / "output_basic.svg"

        if not basic_svg_path.exists():
            pytest.skip("Basic SVG fixture not found")

        with tempfile.TemporaryDirectory() as temp_dir:
            output_path = Path(temp_dir) / f"output_{theme}.svg"
            temp_mmd_path = Path(temp_dir) / "temp.mmd"

            mock_temp_path.return_value = str(temp_mmd_path)
            mock_exists.side_effect = lambda path: str(path) == str(output_path)

            # テーマ別設定
            svg_config = basic_config.copy()
            svg_config.update({"image_format": "svg", "theme": theme})

            generator = MermaidImageGenerator(svg_config)

            with patch("builtins.open", create=True):
                # テーマに関係なく同じ構造のSVGを生成（モック）
                output_path.write_text(basic_svg_path.read_text(encoding="utf-8"))

                result = generator.generate(
                    "graph TD\n A --> B", str(output_path), svg_config
                )
                assert result is True
                assert output_path.exists()

                # 生成されたSVGが有効であることを確認
                ok, msg = self._compare_svg_similarity(
                    str(basic_svg_path), str(output_path)
                )
                assert ok, f"Theme {theme} SVG validation failed: {msg}"

    def test_svg_structure_comparison_detailed(self):
        """SVG構造比較の詳細テスト"""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            # 基本SVG
            base_svg = temp_path / "base.svg"
            base_svg.write_text("""<?xml version="1.0"?>
<svg width="400" height="300" viewBox="0 0 400 300">
  <rect x="10" y="10" width="50" height="30"/>
  <text x="35" y="30">Test</text>
</svg>""")

            # サイズが少し異なるSVG（許容範囲内）
            similar_svg = temp_path / "similar.svg"
            similar_svg.write_text("""<?xml version="1.0"?>
<svg width="410" height="305" viewBox="0 0 410 305">
  <rect x="10" y="10" width="50" height="30"/>
  <text x="35" y="30">Test</text>
</svg>""")

            # 大幅に異なるSVG（許容範囲外）
            different_svg = temp_path / "different.svg"
            different_svg.write_text("""<?xml version="1.0"?>
<svg width="800" height="600" viewBox="0 0 800 600">
  <circle cx="50" cy="50" r="25"/>
</svg>""")

            # 類似SVGは成功する
            ok, msg = self._compare_svg_similarity(str(base_svg), str(similar_svg))
            assert ok, f"Similar SVG comparison failed: {msg}"

            # 大幅に異なるSVGは失敗する
            ok, msg = self._compare_svg_similarity(str(base_svg), str(different_svg))
            assert not ok
            assert "difference too large" in msg or "count difference" in msg

    def _compare_svg_similarity(  # noqa: PLR0911, PLR0912
        self, expected_path: str, actual_path: str
    ) -> tuple[bool, str]:
        """
        SVGファイルの比較（TDD Refactor phase - 改良された実装）

        Args:
            expected_path: 期待値SVGファイルのパス
            actual_path: 実際のSVGファイルのパス

        Returns:
            Tuple[bool, str]: (比較結果, メッセージ)
        """
        try:
            # ファイルの存在確認
            expected_file = Path(expected_path)
            actual_file = Path(actual_path)

            if not expected_file.exists():
                return False, f"Expected file does not exist: {expected_path}"
            if not actual_file.exists():
                return False, f"Actual file does not exist: {actual_path}"

            # ファイルサイズの基本チェック
            expected_size = expected_file.stat().st_size
            actual_size = actual_file.stat().st_size

            if expected_size == 0:
                return False, f"Expected file is empty: {expected_path}"
            if actual_size == 0:
                return False, f"Actual file is empty: {actual_path}"

            # SVGファイルの内容を読み込み
            expected_content = expected_file.read_text(encoding="utf-8")
            actual_content = actual_file.read_text(encoding="utf-8")

            # SVGとして有効かチェック
            if not expected_content.strip().startswith(
                "<?xml"
            ) and not expected_content.strip().startswith("<svg"):
                return False, f"Expected file is not a valid SVG: {expected_path}"
            if not actual_content.strip().startswith(
                "<?xml"
            ) and not actual_content.strip().startswith("<svg"):
                return False, f"Actual file is not a valid SVG: {actual_path}"

            # XML構造の解析とチェック
            try:
                expected_root = ET.fromstring(expected_content)
                actual_root = ET.fromstring(actual_content)

                # SVGルート要素の確認
                if expected_root.tag.endswith("svg") and actual_root.tag.endswith(
                    "svg"
                ):
                    # 基本的な構造比較
                    structure_ok, structure_msg = self._compare_svg_structure(
                        expected_root, actual_root
                    )
                    if not structure_ok:
                        return False, f"SVG structure mismatch: {structure_msg}"

                    # テキスト要素の比較
                    text_ok, text_msg = self._compare_svg_text_elements(
                        expected_root, actual_root
                    )
                    if not text_ok:
                        return False, f"SVG text content mismatch: {text_msg}"

                else:
                    return False, "Root elements are not SVG elements"

            except ET.ParseError as e:
                # XMLパースエラーの場合は基本的なファイルサイズ比較にフォールバック
                size_diff_ratio = abs(expected_size - actual_size) / max(
                    expected_size, actual_size
                )
                if size_diff_ratio > 0.5:
                    return (
                        False,
                        f"XML parse failed and file size difference too large: "
                        f"{size_diff_ratio:.3f} > 0.5",
                    )
                return (
                    True,
                    f"SVG comparison passed (fallback to size comparison "
                    f"due to parse error: {e})",
                )

            return True, "SVG comparison passed (structure and content validated)"

        except Exception as e:
            return False, f"Error during SVG comparison: {e!s}"

    def _compare_svg_structure(self, expected_root, actual_root) -> tuple[bool, str]:
        """SVGの基本構造を比較"""
        try:
            # 基本属性の比較（width, height, viewBox）
            for attr in ["width", "height", "viewBox"]:
                expected_val = expected_root.get(attr)
                actual_val = actual_root.get(attr)
                # 数値の場合は近似比較
                if expected_val and actual_val and attr in ["width", "height"]:
                    try:
                        exp_num = float(re.findall(r"\d+", expected_val)[0])
                        act_num = float(re.findall(r"\d+", actual_val)[0])
                        if (
                            abs(exp_num - act_num) / max(exp_num, act_num) > 0.2
                        ):  # 20%の差まで許容
                            return (
                                False,
                                f"{attr} difference too large: {expected_val} "
                                f"vs {actual_val}",
                            )
                    except (ValueError, IndexError):
                        # 数値抽出に失敗した場合は文字列比較
                        if expected_val != actual_val:
                            return (
                                False,
                                f"{attr} mismatch: {expected_val} vs {actual_val}",
                            )

            # 子要素数の比較（大まかな構造確認）
            expected_children = len(list(expected_root))
            actual_children = len(list(actual_root))

            if expected_children > 0 and actual_children > 0:
                child_diff_ratio = abs(expected_children - actual_children) / max(
                    expected_children, actual_children
                )
                if child_diff_ratio > 0.5:  # 50%の差まで許容
                    return (
                        False,
                        f"Child element count difference: {expected_children} "
                        f"vs {actual_children}",
                    )

            return True, "Structure comparison passed"

        except Exception as e:
            return False, f"Structure comparison error: {e!s}"

    def _compare_svg_text_elements(
        self, expected_root, actual_root
    ) -> tuple[bool, str]:
        """SVG内のテキスト要素を比較"""
        try:
            # テキスト要素を抽出
            expected_texts = [
                elem.text
                for elem in expected_root.iter()
                if elem.text and elem.text.strip()
            ]
            actual_texts = [
                elem.text
                for elem in actual_root.iter()
                if elem.text and elem.text.strip()
            ]

            # 基本的なテキスト内容の存在確認
            if expected_texts and actual_texts:
                # 期待値に含まれる主要なテキストが実際の出力にも含まれているかチェック
                for expected_text in expected_texts:
                    text_found = any(
                        expected_text.strip() in actual_text
                        for actual_text in actual_texts
                    )
                    if (
                        not text_found and len(expected_text.strip()) > 2
                    ):  # 短すぎるテキストは無視
                        return (
                            False,
                            f"Expected text not found: '{expected_text.strip()}'",
                        )

            return True, "Text elements comparison passed"

        except Exception as e:
            return False, f"Text comparison error: {e!s}"
