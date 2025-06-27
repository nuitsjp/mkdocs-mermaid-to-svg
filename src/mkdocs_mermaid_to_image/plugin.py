"""
MkDocs Mermaid to Image Plugin - メインプラグインクラス

このファイルは、MkDocsプラグインシステムと統合される核となるクラスを定義します。
主な機能：
- MkDocsのビルドプロセスの各段階（フック）に処理を追加
- プラグインの設定管理と初期化
- ページ処理中のMermaid図の画像変換
- ビルド完了後のクリーンアップ処理
- 開発サーバー用の追加機能

Python学習者へのヒント：
- クラス継承（BasePluginを継承）でMkDocsプラグインシステムに統合
- メソッド名がon_で始まるのは、MkDocsのフック（hook）システムです
- super().__init__()で親クラスのコンストラクタを呼び出し
- MkDocsプラグインは、ドキュメント生成の各段階で特定のメソッドが自動実行されます
"""

import shutil
import sys
from pathlib import Path
from typing import Any, Optional

from mkdocs.config import config_options  # 設定オプション

# MkDocsプラグインシステムの基盤となるクラスとモジュール
from mkdocs.plugins import BasePlugin  # プラグインの基底クラス

# 同じパッケージ内のモジュールをインポート（相対インポート）
from .config import ConfigManager, MermaidPluginConfig  # 設定管理クラス
from .exceptions import MermaidConfigError, MermaidPreprocessorError  # カスタム例外
from .processor import MermaidProcessor  # リファクタリング後のメイン処理クラス
from .utils import ensure_directory, setup_logger  # ユーティリティ関数


class MermaidToImagePlugin(BasePlugin[MermaidPluginConfig]):  # type: ignore[no-untyped-call]
    """
    MkDocs用のMermaid図画像変換プラグインのメインクラス

    このクラスは、MkDocsのBasePluginを継承し、ドキュメント生成プロセスの
    各段階で必要な処理を実行します。

    主要な責任：
    - プラグイン設定の検証と初期化
    - ファイル処理段階での準備
    - ページのMarkdown処理（Mermaid→画像変換）
    - ビルド完了後のクリーンアップ
    - 開発サーバーモードでの特別な処理

    Python学習者へのヒント：
    - BasePluginクラスを継承することで、MkDocsプラグインとして動作します
    - config_schemeでプラグインの設定スキーマを定義
    - on_で始まるメソッドは、MkDocsの特定のタイミングで自動実行されます

    MkDocsフックの実行順序：
    1. on_config - 設定読み込み・検証時
    2. on_files - ファイル発見時
    3. on_page_markdown - 各ページのMarkdown処理時
    4. on_post_build - ビルド完了後
    5. on_serve - 開発サーバー起動時（開発時のみ）
    """

    config_scheme = (
        ("enabled", config_options.Type(bool, default=True)),
        ("output_dir", config_options.Type(str, default="assets/images")),
        ("image_format", config_options.Choice(["png", "svg"], default="png")),
        ("mermaid_config", config_options.Optional(config_options.Type(str))),
        ("mmdc_path", config_options.Type(str, default="mmdc")),
        (
            "theme",
            config_options.Choice(
                ["default", "dark", "forest", "neutral"], default="default"
            ),
        ),
        ("background_color", config_options.Type(str, default="white")),
        ("width", config_options.Type(int, default=800)),
        ("height", config_options.Type(int, default=600)),
        ("scale", config_options.Type(float, default=1.0)),
        ("css_file", config_options.Optional(config_options.Type(str))),
        ("puppeteer_config", config_options.Optional(config_options.Type(str))),
        ("temp_dir", config_options.Optional(config_options.Type(str))),
        ("cache_enabled", config_options.Type(bool, default=True)),
        ("cache_dir", config_options.Type(str, default=".mermaid_cache")),
        ("preserve_original", config_options.Type(bool, default=False)),
        ("error_on_fail", config_options.Type(bool, default=False)),
        (
            "log_level",
            config_options.Choice(
                ["DEBUG", "INFO", "WARNING", "ERROR"], default="INFO"
            ),
        ),
    )

    def __init__(self) -> None:
        """
        プラグインのコンストラクタ（初期化メソッド）

        Python学習者へのヒント：
        - super().__init__()で親クラス（BasePlugin）のコンストラクタを呼び出し
        - インスタンス変数をNoneや空リストで初期化
        - 実際の設定は後のon_configメソッドで行われます
        """
        super().__init__()  # 親クラス（BasePlugin）の初期化処理を実行
        self.processor: Optional[MermaidProcessor] = (
            None  # MermaidProcessorインスタンス（後で設定）
        )
        self.logger: Optional[Any] = None  # ロガーインスタンス（後で設定）
        self.generated_images: list[str] = []  # 生成された画像のパスを記録するリスト

        # serve モード検出（起動時のコマンドライン引数をチェック）
        self.is_serve_mode: bool = "serve" in sys.argv

    def on_config(self, config: Any) -> Any:
        """
        設定読み込み・検証時に実行されるフックメソッド

        Args:
            config (dict): MkDocsの全体設定辞書

        Returns:
            dict: 更新された設定辞書

        Raises:
            MermaidConfigError: 設定が不正な場合

        Python学習者へのヒント：
        - このメソッドはMkDocsによって自動的に呼び出されます
        - try-except文で例外処理を行い、適切なエラーメッセージを提供
        - self.configでプラグイン固有の設定にアクセスできます
        - 戻り値のconfigは、他のプラグインや処理に渡されます
        """
        try:
            # プラグイン設定の妥当性を検証
            config_dict = dict(self.config)  # MermaidPluginConfig を辞書に変換
            ConfigManager.validate_config(config_dict)

            # ロガーを設定（プラグイン名とログレベルを指定）
            self.logger = setup_logger(__name__, self.config["log_level"])

            # プラグインが無効化されている場合は早期リターン
            if not self.config["enabled"]:
                self.logger.info("Mermaid preprocessor plugin is disabled")
                return config

            # Mermaid処理エンジンを初期化
            self.processor = MermaidProcessor(config_dict)

            # 画像出力ディレクトリが存在することを保証
            # MkDocsのdocs_dirとプラグインのoutput_dirを結合
            output_dir = Path(config["docs_dir"]) / self.config["output_dir"]
            ensure_directory(output_dir)

            # 初期化成功をログに記録
            self.logger.info("Mermaid preprocessor plugin initialized successfully")

        except Exception as e:
            # 予期しない例外をプラグイン固有の例外に変換
            raise MermaidConfigError(f"Plugin configuration error: {e!s}") from e

        # 設定を返す（他のプラグインや処理で使用されるため）
        return config

    def on_files(self, files: Any, *, config: Any) -> Any:
        """
        ファイル発見段階で実行されるフックメソッド

        Args:
            files: MkDocsで発見されたファイルのコレクション
            config (dict): MkDocsの設定辞書（未使用だがインターフェース準拠のため必要）

        Returns:
            files: ファイルコレクション（通常は変更なし）

        Python学習者へのヒント：
        - このメソッドは各ビルド開始時に実行されます
        - プラグインが無効またはプロセッサが未初期化の場合は何もしません
        - ここで前回のビルドで生成した画像リストをクリア
        """
        # プラグインが無効またはプロセッサが未初期化の場合は処理をスキップ
        if not self.config["enabled"] or not self.processor:
            return files

        # 前回のビルドで生成された画像リストをクリア
        # （新しいビルドのために初期化）
        self.generated_images = []

        # ファイルリストはそのまま返す（このプラグインでは変更しない）
        return files

    def on_page_markdown(
        self, markdown: str, *, page: Any, config: Any, files: Any
    ) -> Optional[str]:
        """
        各ページのMarkdown処理時に実行されるフックメソッド（最重要メソッド）

        Args:
            markdown (str): ページの元のMarkdownコンテンツ
            page: MkDocsのページオブジェクト
            config (dict): MkDocsの設定辞書
            files: ファイルコレクション

        Returns:
            str: 処理されたMarkdownコンテンツ（Mermaid→画像に変換済み）

        Python学習者へのヒント：
        - このメソッドが実際のMermaid→画像変換を行う核心部分です
        - 例外処理により、エラーが発生してもビルドを継続できます
        - page.file.src_pathでページファイルのパスを取得
        - list.extend()で複数の要素を一度にリストに追加
        """
        # プラグインが無効またはプロセッサが未初期化の場合は処理をスキップ
        if not self.config["enabled"] or not self.processor:
            return markdown

        # serve モード時は画像化処理をスキップして元のMarkdownを返す
        if self.is_serve_mode:
            if self.logger:
                self.logger.debug(
                    f"Skipping Mermaid image generation in serve mode for "
                    f"{page.file.src_path}"
                )
            return markdown

        try:
            # 画像出力ディレクトリの絶対パスを取得
            output_dir = Path(config["docs_dir"]) / self.config["output_dir"]

            # ページを処理してMermaidブロックを画像に変換
            modified_content, image_paths = self.processor.process_page(
                page.file.src_path,  # ページファイルのパス
                markdown,  # 元のMarkdownコンテンツ
                output_dir,  # 画像出力ディレクトリ
            )

            # 生成された画像パスを記録（統計情報のため）
            self.generated_images.extend(image_paths)

            # 処理結果をログに記録
            if image_paths and self.logger:
                self.logger.info(
                    f"Processed {len(image_paths)} Mermaid diagrams in "
                    f"{page.file.src_path}"
                )

            # 処理されたMarkdownコンテンツを返す
            return modified_content

        except MermaidPreprocessorError as e:
            # プラグイン固有のエラーが発生した場合
            if self.logger:
                self.logger.error(f"Error processing {page.file.src_path}: {e!s}")
            # 設定に応じてエラーで停止するか、元のMarkdownを返すか決定
            if self.config["error_on_fail"]:
                raise  # エラーを再発生（ビルドを停止）
            return markdown  # 元のMarkdownを返す（処理を継続）

        except Exception as e:
            # 予期しない例外が発生した場合
            if self.logger:
                self.logger.error(
                    f"Unexpected error processing {page.file.src_path}: {e!s}"
                )
            if self.config["error_on_fail"]:
                # 予期しない例外をプラグイン例外に変換して発生
                raise MermaidPreprocessorError(f"Unexpected error: {e!s}") from e
            return markdown  # エラーを無視して元のMarkdownを返す

    def on_post_build(self, *, config: Any) -> None:
        """
        ビルド完了後に実行されるフックメソッド

        Args:
            config (dict): MkDocsの設定辞書

        Python学習者へのヒント：
        - ビルド完了後のクリーンアップ処理を行います
        - 統計情報の出力やキャッシュの削除などを実行
        - import文を関数内で行うのは、必要な時にのみモジュールを読み込む手法
        """
        # プラグインが無効の場合は処理をスキップ
        if not self.config["enabled"]:
            return

        # ビルド結果の統計情報をログに出力
        if self.generated_images and self.logger:
            self.logger.info(
                f"Generated {len(self.generated_images)} Mermaid images total"
            )

        # キャッシュが無効化されている場合はキャッシュディレクトリを削除
        if not self.config["cache_enabled"]:
            cache_dir = self.config["cache_dir"]
            if Path(cache_dir).exists():
                shutil.rmtree(cache_dir)  # ディレクトリを再帰的に削除
                if self.logger:
                    self.logger.debug(f"Cleaned up cache directory: {cache_dir}")

    def on_serve(self, server: Any, *, config: Any, builder: Any) -> Any:
        """
        開発サーバー起動時に実行されるフックメソッド

        Args:
            server: MkDocsの開発サーバーオブジェクト
            config (dict): MkDocsの設定辞書
            builder: ビルダーオブジェクト

        Returns:
            server: サーバーオブジェクト（通常は変更なし）

        Python学習者へのヒント：
        - 開発サーバー（mkdocs serve）実行時のみ呼び出されます
        - ファイル変更監視の設定などを行います
        - server.watch()でディレクトリを監視対象に追加
        """
        # プラグインが無効の場合は処理をスキップ
        if not self.config["enabled"]:
            return server

        # キャッシュが有効な場合、キャッシュディレクトリの変更を監視
        # これにより、キャッシュファイルが変更された時に自動でリビルドされます
        if self.config["cache_enabled"]:
            cache_dir = self.config["cache_dir"]
            if Path(cache_dir).exists():
                server.watch(cache_dir)  # キャッシュディレクトリを監視対象に追加

        # サーバーオブジェクトを返す
        return server
