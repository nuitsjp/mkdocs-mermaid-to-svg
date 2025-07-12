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
from mkdocs_mermaid_to_svg.config import ConfigManager
from mkdocs_mermaid_to_svg.exceptions import MermaidFileError


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

        # 期待される設定項目のリスト（PNG関連設定を削除）
        expected_configs = [
            "enabled_if_env",  # 環境変数による有効化
            "output_dir",  # 画像出力ディレクトリ
            "theme",  # テーマ設定
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
        # 有効な設定データを定義（PNG関連設定を削除）
        valid_config = {
            "css_file": None,  # ファイル未指定
            "puppeteer_config": None,  # ファイル未指定
        }

        # 設定検証が成功することを確認
        result = ConfigManager.validate_config(valid_config)
        assert result is True

    @pytest.mark.parametrize(
        "config_override,expected_error,error_message",
        [
            (
                {"css_file": "/nonexistent/file.css"},
                MermaidFileError,
                "CSS file not found",
            ),
            (
                {"puppeteer_config": "/nonexistent/config.json"},
                MermaidFileError,
                "Puppeteer config file not found",
            ),
        ],
    )
    def test_validate_config_errors(
        self, config_override, expected_error, error_message
    ):
        """
        設定検証エラーのパラメータ化テスト

        Python学習者へのヒント：
        - @pytest.mark.parametrizeデコレータで複数のテストケースを一度に実行
        - 各パラメータセットに対して同じテストロジックを適用
        - config_override: 基本設定を上書きする値
        - expected_error: 期待される例外タイプ
        - error_message: 期待されるエラーメッセージ
        """
        base_config = {
            "css_file": None,
            "puppeteer_config": None,
        }
        invalid_config = {**base_config, **config_override}

        with pytest.raises(expected_error, match=error_message):
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
                "css_file": css_file_path,
                "puppeteer_config": puppeteer_file_path,
            }

            result = ConfigManager.validate_config(valid_config)
            assert result is True

        finally:
            # Clean up temporary files
            Path(css_file_path).unlink()
            Path(puppeteer_file_path).unlink()

    def test_config_scheme_includes_enabled_if_env(self):
        """
        設定スキーマにenabled_if_envが含まれることをテスト
        """
        scheme = ConfigManager.get_config_scheme()
        config_names = [item[0] for item in scheme]

        # enabled_if_envが設定スキーマに含まれることを確認
        assert "enabled_if_env" in config_names

    def test_enabled_if_env_is_optional(self):
        """
        enabled_if_envがオプショナル設定であることをテスト
        """
        from mkdocs.config import config_options

        scheme = ConfigManager.get_config_scheme()
        scheme_dict = dict(scheme)

        # enabled_if_envの設定オプションを取得
        enabled_if_env_option = scheme_dict["enabled_if_env"]

        # オプショナル設定であることを確認
        assert isinstance(enabled_if_env_option, config_options.Optional)
