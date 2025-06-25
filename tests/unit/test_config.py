"""
MkDocs Mermaid to Image Plugin - ConfigManagerクラスのテスト

このファイルは、ConfigManagerクラスの動作を検証するテストケースを定義します。
テストの目的：
- 設定スキーマが正しく定義されていることを確認
- 設定検証機能が適切に動作することを確認
- 有効な設定と無効な設定の両方をテスト
- エラーケースで適切な例外が発生することを確認

Python学習者へのヒント：
- pytestフレームワークを使用してテストを記述
- classでテストを組織化（関連するテストをまとめる）
- assert文でテスト条件を検証
- tempfileモジュールで一時ファイルを作成してテスト
- pytest.raisesで例外発生をテスト
"""

import tempfile  # 一時ファイル作成用（ファイル存在テスト用）
from pathlib import Path

import pytest  # Pythonのテストフレームワーク

# テスト対象のConfigManagerクラスをインポート
from mkdocs_mermaid_to_image.config import ConfigManager


class TestConfigManager:
    """
    ConfigManagerクラスのテストケースを含むクラス

    Python学習者へのヒント：
    - クラス名はTestで始まる慣例があります
    - 関連するテストメソッドをクラス内にまとめることで整理しやすくなります
    - 各メソッドはtest_で始まる名前にします
    """

    def test_get_config_scheme(self):
        """
        設定スキーマが正しく定義されているかをテストするメソッド

        Python学習者へのヒント：
        - isinstance()関数で型チェックを行います
        - リスト内包表記 [item[0] for item in scheme] で要素を抽出
        - forループで期待される設定項目が含まれているかを確認
        """
        # ConfigManagerから設定スキーマを取得
        scheme = ConfigManager.get_config_scheme()

        # スキーマがタプル型で、要素が存在することを確認
        assert isinstance(scheme, tuple)  # タプル型であることを確認
        assert len(scheme) > 0  # 要素が存在することを確認

        # 設定項目名の一覧を抽出（各項目の最初の要素が名前）
        config_names = [item[0] for item in scheme]

        # 期待される設定項目のリスト
        expected_configs = [
            "enabled",  # プラグインの有効/無効
            "output_dir",  # 画像出力ディレクトリ
            "image_format",  # 画像形式
            "mmdc_path",  # Mermaid CLIのパス
            "theme",  # テーマ設定
            "background_color",  # 背景色
            "width",  # 画像の幅
            "height",  # 画像の高さ
            "scale",  # 拡大率
            "error_on_fail",  # エラー時の動作
            "log_level",  # ログレベル
        ]

        # すべての期待される設定項目が含まれているかを確認
        for expected in expected_configs:
            assert expected in config_names

    def test_validate_config_success(self):
        """
        有効な設定が正しく検証されることをテストするメソッド

        Python学習者へのヒント：
        - 辞書型で設定データを定義
        - Noneは「設定されていない」ことを表します
        - assertで戻り値がTrueであることを確認
        """
        # 有効な設定データを定義
        valid_config = {
            "width": 800,  # 正の整数
            "height": 600,  # 正の整数
            "scale": 1.0,  # 正の浮動小数点数
            "css_file": None,  # ファイル未指定
            "puppeteer_config": None,  # ファイル未指定
        }

        # 設定検証が成功することを確認
        result = ConfigManager.validate_config(valid_config)
        assert result is True

    def test_validate_config_invalid_width(self):
        invalid_config = {
            "width": -100,
            "height": 600,
            "scale": 1.0,
            "css_file": None,
            "puppeteer_config": None,
        }

        with pytest.raises(
            ValueError, match="Width and height must be positive integers"
        ):
            ConfigManager.validate_config(invalid_config)

    def test_validate_config_invalid_height(self):
        invalid_config = {
            "width": 800,
            "height": 0,
            "scale": 1.0,
            "css_file": None,
            "puppeteer_config": None,
        }

        with pytest.raises(
            ValueError, match="Width and height must be positive integers"
        ):
            ConfigManager.validate_config(invalid_config)

    def test_validate_config_invalid_scale(self):
        invalid_config = {
            "width": 800,
            "height": 600,
            "scale": -1.5,
            "css_file": None,
            "puppeteer_config": None,
        }

        with pytest.raises(ValueError, match="Scale must be a positive number"):
            ConfigManager.validate_config(invalid_config)

    def test_validate_config_missing_css_file(self):
        invalid_config = {
            "width": 800,
            "height": 600,
            "scale": 1.0,
            "css_file": "/nonexistent/file.css",
            "puppeteer_config": None,
        }

        with pytest.raises(FileNotFoundError, match="CSS file not found"):
            ConfigManager.validate_config(invalid_config)

    def test_validate_config_missing_puppeteer_config(self):
        invalid_config = {
            "width": 800,
            "height": 600,
            "scale": 1.0,
            "css_file": None,
            "puppeteer_config": "/nonexistent/config.json",
        }

        with pytest.raises(FileNotFoundError, match="Puppeteer config file not found"):
            ConfigManager.validate_config(invalid_config)

    def test_validate_config_with_existing_files(self):
        with tempfile.NamedTemporaryFile(suffix=".css", delete=False) as css_file:
            css_file.write(b"body { background: white; }")
            css_file_path = css_file.name

        with tempfile.NamedTemporaryFile(
            suffix=".json", delete=False
        ) as puppeteer_file:
            puppeteer_file.write(b'{"headless": true}')
            puppeteer_file_path = puppeteer_file.name

        try:
            valid_config = {
                "width": 800,
                "height": 600,
                "scale": 1.0,
                "css_file": css_file_path,
                "puppeteer_config": puppeteer_file_path,
            }

            result = ConfigManager.validate_config(valid_config)
            assert result is True

        finally:
            # Clean up temporary files
            Path(css_file_path).unlink()
            Path(puppeteer_file_path).unlink()
