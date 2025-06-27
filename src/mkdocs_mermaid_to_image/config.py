"""
MkDocs Mermaid to Image Plugin - 設定管理ファイル

このファイルは、プラグインの設定スキーマの定義と設定値の検証を担当します。
主な機能：
- MkDocsプラグインの設定スキーマ定義
- 各設定項目のデフォルト値の設定
- 設定値の妥当性検証
- MkDocsの設定システムとの統合

Python学習者へのヒント：
- @staticmethodデコレータは、クラスのインスタンスを作らずに呼び出せる
  メソッドを定義します
- MkDocsのconfig_optionsモジュールを使用して、設定の型と制約を定義します
- タプルで設定項目を定義することで、MkDocsが自動的に設定を処理してくれます
"""

from pathlib import Path  # パス操作のための標準ライブラリ
from typing import Any

from mkdocs.config import config_options  # MkDocs設定システムのライブラリ
from mkdocs.config.base import Config  # MkDocs設定基底クラス


class ConfigManager:
    """
    プラグイン設定の管理を担当するクラス

    このクラスは、MkDocsプラグインの設定スキーマの定義と、
    設定値の検証処理を提供します。

    Python学習者へのヒント：
    - クラス内のメソッドがすべて@staticmethodの場合、
      実際には名前空間として使用されています
    - このパターンは、関連する関数をまとめる際によく使用されます

    使用例:
        # 設定スキーマの取得
        scheme = ConfigManager.get_config_scheme()

        # 設定値の検証
        ConfigManager.validate_config(plugin_config)
    """

    @staticmethod
    def get_config_scheme() -> tuple[tuple[str, Any], ...]:
        """
        プラグインの設定スキーマを定義する関数

        Returns:
            tuple: MkDocs用の設定項目のタプル

        Python学習者へのヒント：
        - タプルは変更不可能なリストのような型です
        - 各設定項目は ('名前', config_options.Type(...)) の形式で定義します
        - config_options.Type()で型とデフォルト値を指定します
        - config_options.Choice()で選択肢を制限できます

        設定項目の説明:
        - enabled: プラグインの有効/無効を制御
        - output_dir: 生成された画像の保存先ディレクトリ
        - image_format: 画像の形式（pngまたはsvg）
        - mermaid_config: Mermaid設定ファイルのパス
        - mmdc_path: Mermaid CLIコマンドのパス
        - theme: Mermaid図のテーマ
        - background_color: 背景色
        - width/height: 画像のサイズ（ピクセル）
        - scale: 画像の拡大率
        - css_file: カスタムCSSファイルのパス
        - puppeteer_config: Puppeteer設定ファイルのパス
        - temp_dir: 一時ファイル用ディレクトリ
        - cache_enabled: キャッシュ機能の有効/無効
        - cache_dir: キャッシュディレクトリ
        - preserve_original: 元のMermaidコードを残すかどうか
        - error_on_fail: エラー時に処理を停止するかどうか
        - log_level: ログの詳細レベル
        """
        return (
            # プラグインの基本制御
            (
                "enabled",
                config_options.Type(bool, default=True),
            ),  # プラグインを有効にするか
            # 出力関連の設定
            (
                "output_dir",
                config_options.Type(str, default="assets/images"),
            ),  # 画像出力ディレクトリ
            (
                "image_format",
                config_options.Choice(["png", "svg"], default="png"),
            ),  # 画像形式（選択肢制限）
            # Mermaid設定
            (
                "mermaid_config",
                config_options.Type(str, default=None),
            ),  # Mermaid設定ファイル（オプション）
            (
                "mmdc_path",
                config_options.Type(str, default="mmdc"),
            ),  # Mermaid CLIのパス
            # 見た目の設定
            (
                "theme",
                config_options.Choice(
                    ["default", "dark", "forest", "neutral"], default="default"
                ),
            ),  # テーマ
            ("background_color", config_options.Type(str, default="white")),  # 背景色
            # 画像サイズ設定
            ("width", config_options.Type(int, default=800)),  # 画像の幅（整数型）
            ("height", config_options.Type(int, default=600)),  # 画像の高さ（整数型）
            (
                "scale",
                config_options.Type(float, default=1.0),
            ),  # 拡大率（浮動小数点型）
            # カスタマイズ設定
            (
                "css_file",
                config_options.Type(str, default=None),
            ),  # カスタムCSSファイル（オプション）
            (
                "puppeteer_config",
                config_options.Type(str, default=None),
            ),  # Puppeteer設定（オプション）
            (
                "temp_dir",
                config_options.Type(str, default=None),
            ),  # 一時ディレクトリ（オプション）
            # キャッシュ設定
            (
                "cache_enabled",
                config_options.Type(bool, default=True),
            ),  # キャッシュを使用するか
            (
                "cache_dir",
                config_options.Type(str, default=".mermaid_cache"),
            ),  # キャッシュディレクトリ
            # 動作制御設定
            (
                "preserve_original",
                config_options.Type(bool, default=False),
            ),  # 元のコードを保持するか
            (
                "error_on_fail",
                config_options.Type(bool, default=False),
            ),  # エラー時に処理を停止するか
            # ログ設定
            (
                "log_level",
                config_options.Choice(
                    ["DEBUG", "INFO", "WARNING", "ERROR"], default="INFO"
                ),
            ),  # ログレベル
        )

    @staticmethod
    def validate_config(config: dict[str, Any]) -> bool:
        """
        プラグイン設定の妥当性を検証する関数

        Args:
            config (dict): 検証する設定の辞書

        Returns:
            bool: 検証に成功した場合True

        Raises:
            ValueError: 設定値が不正な場合
            FileNotFoundError: 指定されたファイルが存在しない場合

        Python学習者へのヒント：
        - 関数が例外を発生させる可能性がある場合、docstringのRaisesセクションに
          記載します
        - and演算子を使用することで、複数の条件を同時にチェックできます
        - f文字列（f"..."）で、変数を含むエラーメッセージを作成できます
        - os.path.exists()でファイルの存在を確認できます

        検証内容:
        - 画像の幅と高さが正の整数であること
        - 拡大率が正の数値であること
        - 指定されたCSSファイルが存在すること（指定されている場合）
        - 指定されたPuppeteer設定ファイルが存在すること（指定されている場合）
        """
        # 画像サイズの検証（幅と高さは正の整数である必要がある）
        if config["width"] <= 0 or config["height"] <= 0:
            raise ValueError("Width and height must be positive integers")

        # 拡大率の検証（正の数値である必要がある）
        if config["scale"] <= 0:
            raise ValueError("Scale must be a positive number")

        # CSSファイルの存在確認（指定されている場合のみ）
        # 「and」演算子により、css_fileがNoneでない場合のみファイル存在をチェック
        if config["css_file"] and not Path(config["css_file"]).exists():
            raise FileNotFoundError(f"CSS file not found: {config['css_file']}")

        # Puppeteer設定ファイルの存在確認（指定されている場合のみ）
        if config["puppeteer_config"] and not Path(config["puppeteer_config"]).exists():
            raise FileNotFoundError(
                f"Puppeteer config file not found: {config['puppeteer_config']}"
            )

        # すべての検証に成功
        return True


class MermaidPluginConfig(Config):  # type: ignore[no-untyped-call]
    """
    MkDocs Mermaid Plugin用の設定クラス

    MkDocsのConfig基底クラスを継承して、プラグイン固有の設定を定義します。
    各設定項目は、ConfigManagerのget_config_scheme()と同じ項目を定義します。
    """

    enabled = config_options.Type(bool, default=True)
    output_dir = config_options.Type(str, default="assets/images")
    image_format = config_options.Choice(["png", "svg"], default="png")
    mermaid_config = config_options.Optional(config_options.Type(str))
    mmdc_path = config_options.Type(str, default="mmdc")
    theme = config_options.Choice(
        ["default", "dark", "forest", "neutral"], default="default"
    )
    background_color = config_options.Type(str, default="white")
    width = config_options.Type(int, default=800)
    height = config_options.Type(int, default=600)
    scale = config_options.Type(float, default=1.0)
    css_file = config_options.Optional(config_options.Type(str))
    puppeteer_config = config_options.Optional(config_options.Type(str))
    temp_dir = config_options.Optional(config_options.Type(str))
    cache_enabled = config_options.Type(bool, default=True)
    cache_dir = config_options.Type(str, default=".mermaid_cache")
    preserve_original = config_options.Type(bool, default=False)
    error_on_fail = config_options.Type(bool, default=False)
    log_level = config_options.Choice(
        ["DEBUG", "INFO", "WARNING", "ERROR"], default="INFO"
    )
