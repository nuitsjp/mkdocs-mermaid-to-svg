"""
MermaidImageGeneratorクラスのテスト
このファイルでは、MermaidImageGeneratorクラスの動作を検証します。

Python未経験者へのヒント：
- pytestを使ってテストを書いています。
- patchやMockで外部依存を疑似的に置き換えています。
- assert文で「期待する結果」かどうかを検証します。
"""

import subprocess
import tempfile
from pathlib import Path
from typing import Tuple
from unittest.mock import Mock, patch

import pytest

try:
    import numpy as np
    from PIL import Image

    PILLOW_AVAILABLE = True
except ImportError:
    PILLOW_AVAILABLE = False

from mkdocs_mermaid_to_image.exceptions import MermaidCLIError
from mkdocs_mermaid_to_image.image_generator import MermaidImageGenerator


class TestMermaidImageGenerator:
    """MermaidImageGeneratorクラスのテストクラス"""

    @pytest.fixture
    def basic_config(self):
        """テスト用の基本設定を返すfixture"""
        return {
            "mmdc_path": "mmdc",
            "theme": "default",
            "background_color": "white",
            "width": 800,
            "height": 600,
            "scale": 1.0,
            "css_file": None,
            "puppeteer_config": None,
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
            mock_clean.assert_called_once_with("/tmp/test.mmd")

    @patch("mkdocs_mermaid_to_image.image_generator.is_command_available")
    @patch("subprocess.run")
    @patch("os.path.exists")
    @patch("mkdocs_mermaid_to_image.image_generator.get_temp_file_path")
    @patch("mkdocs_mermaid_to_image.image_generator.clean_temp_file")
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
            mock_clean.assert_called_once_with("/tmp/test.mmd")

    @patch("mkdocs_mermaid_to_image.image_generator.is_command_available")
    @patch("subprocess.run")
    @patch("mkdocs_mermaid_to_image.image_generator.get_temp_file_path")
    @patch("mkdocs_mermaid_to_image.image_generator.clean_temp_file")
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
            mock_clean.assert_called_once_with("/tmp/test.mmd")

    @patch("mkdocs_mermaid_to_image.image_generator.is_command_available")
    def test_build_mmdc_command_basic(self, mock_command_available, basic_config):
        """mmdcコマンド生成の基本テスト"""
        mock_command_available.return_value = True
        generator = MermaidImageGenerator(basic_config)

        cmd = generator._build_mmdc_command("input.mmd", "output.png", basic_config)

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

        cmd = generator._build_mmdc_command("input.mmd", "output.png", override_config)

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
        self, mock_command_available, basic_config
    ):
        """CSSやpuppeteer等のファイル指定時のコマンド生成テスト"""
        mock_command_available.return_value = True
        basic_config.update(
            {
                "css_file": "/path/to/custom.css",
                "puppeteer_config": "/path/to/puppeteer.json",
                "mermaid_config": "/path/to/mermaid.json",
            }
        )
        generator = MermaidImageGenerator(basic_config)

        cmd = generator._build_mmdc_command("input.mmd", "output.png", basic_config)

        assert "-C" in cmd
        assert "/path/to/custom.css" in cmd
        assert "-p" in cmd
        assert "/path/to/puppeteer.json" in cmd
        assert "-c" in cmd
        assert "/path/to/mermaid.json" in cmd

    @patch("mkdocs_mermaid_to_image.image_generator.is_command_available")
    def test_generate_with_error_on_fail_true(
        self, mock_command_available, basic_config
    ):
        """error_on_fail=True時に例外が発生するかテスト"""
        basic_config["error_on_fail"] = True
        mock_command_available.return_value = True

        generator = MermaidImageGenerator(basic_config)

        with patch("subprocess.run") as mock_subprocess:
            mock_subprocess.return_value = Mock(returncode=1, stderr="Error message")

            with patch("builtins.open", create=True), patch(
                "mkdocs_mermaid_to_image.image_generator.get_temp_file_path"
            ), patch("mkdocs_mermaid_to_image.image_generator.ensure_directory"), patch(
                "mkdocs_mermaid_to_image.image_generator.clean_temp_file"
            ), pytest.raises(MermaidCLIError):
                generator.generate("invalid", "/tmp/output.png", basic_config)

    @pytest.mark.parametrize(
        "mmd_file, expected_png",
        [
            ("sample_basic.mmd", "output_basic.png"),
            ("sample_sequence.mmd", "output_sequence.png"),
        ],
    )
    def test_generate_mermaid_image_and_compare(
        self, basic_config, mmd_file, expected_png
    ):
        """
        Mermaidコードから画像を生成し、類似度比較を行う
        """
        fixtures_dir = Path(__file__).parent.parent / "fixtures"
        mmd_path = fixtures_dir / mmd_file
        expected_path = fixtures_dir / expected_png

        # 期待値ファイルが存在しない場合はスキップ
        if not expected_path.exists():
            pytest.skip(f"Expected file {expected_png} not found")

        with tempfile.TemporaryDirectory() as temp_dir:
            output_path = Path(temp_dir) / "output.png"
            mermaid_code = mmd_path.read_text(encoding="utf-8")
            generator = MermaidImageGenerator(basic_config)
            result = generator.generate(mermaid_code, str(output_path), basic_config)
            assert result is True
            assert output_path.exists()

            # 類似度比較
            similarity_ok, similarity_msg = self._compare_images_similarity(
                str(expected_path), str(output_path), threshold=0.95
            )
            assert similarity_ok, f"Similarity comparison failed: {similarity_msg}"

    def _compare_images_similarity(  # noqa: PLR0911
        self, expected_path: str, actual_path: str, threshold: float = 0.95
    ) -> Tuple[bool, str]:
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
            with Image.open(expected_path) as expected_img, Image.open(
                actual_path
            ) as actual_img:
                # 基本的な妥当性チェック
                if not os.path.exists(expected_path):
                    return False, f"Expected file does not exist: {expected_path}"
                if not os.path.exists(actual_path):
                    return False, f"Actual file does not exist: {actual_path}"

                expected_size = os.path.getsize(expected_path)
                actual_size = os.path.getsize(actual_path)

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
