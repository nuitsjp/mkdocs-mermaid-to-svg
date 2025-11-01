import os
import sys
from collections.abc import Iterable
from pathlib import Path
from typing import TYPE_CHECKING, Any, Optional

from mkdocs.plugins import BasePlugin

if TYPE_CHECKING:
    from mkdocs.structure.files import Files

from .config import ConfigManager
from .exceptions import (
    MermaidConfigError,
    MermaidFileError,
    MermaidPreprocessorError,
    MermaidValidationError,
)
from .logging_config import get_logger
from .processor import MermaidProcessor
from .utils import clean_generated_images


class MermaidSvgConverterPlugin(BasePlugin):  # type: ignore[type-arg,no-untyped-call]
    """Mermaid記法ブロックをSVG画像へ変換するMkDocsプラグイン"""

    config_scheme = ConfigManager.get_config_scheme()

    def __init__(self) -> None:
        """Markdown処理の前段で必要となる状態とロガーを初期化する"""
        super().__init__()
        # プロセッサや生成物を初期化して、Markdown処理中の状態管理に備える
        self.processor: Optional[MermaidProcessor] = None
        self.generated_images: list[str] = []
        self.files: Optional[Files] = None
        self.logger = get_logger(__name__)

        # CLI引数からserveモードや詳細ログ出力モードかどうかを判定
        self.is_serve_mode: bool = "serve" in sys.argv
        self.is_verbose_mode: bool = "--verbose" in sys.argv or "-v" in sys.argv

    def _should_be_enabled(self, config: dict[str, Any]) -> bool:
        """環境変数設定に基づいてプラグインが有効化されるべきかどうかを判定"""
        enabled_if_env = config.get("enabled_if_env")

        if enabled_if_env is not None:
            # enabled_if_envが設定されている場合、環境変数の存在と値をチェック
            env_value = os.environ.get(enabled_if_env)
            return env_value is not None and env_value.strip() != ""

        # enabled_if_envが設定されていない場合はプラグインを有効化
        return True

    def on_config(self, config: Any) -> Any:
        """MkDocs設定を取り込みプラグインを有効化する準備を整える"""
        # mkdocs.ymlから受け取った設定を検証し、プラグイン用設定に整形
        config_dict = dict(self.config)
        ConfigManager.validate_config(config_dict)

        config_dict["log_level"] = "DEBUG" if self.is_verbose_mode else "WARNING"

        if not self._should_be_enabled(self.config):
            self.logger.info("Mermaid preprocessor plugin is disabled")
            return config

        if config_dict.get("image_id_enabled", False):
            self._ensure_attr_list_extension_enabled(config)

        try:
            # MermaidProcessorを生成し、後続のMarkdown処理を引き受けさせる
            self.processor = MermaidProcessor(config_dict)
            self.logger.info("Mermaid preprocessor plugin initialized successfully")
        except Exception as e:
            self.logger.error(f"Plugin initialization failed: {e!s}")
            self._handle_init_error(e)

        return config

    def _handle_init_error(self, error: Exception) -> None:
        """初期化時の例外を分類し利用者向けの例外へ変換して再送出する"""
        if isinstance(error, (MermaidConfigError, MermaidFileError)):
            raise error
        elif isinstance(error, FileNotFoundError):
            raise MermaidFileError(
                f"Required file not found during plugin initialization: {error!s}",
                operation="read",
                suggestion="Ensure all required files exist",
            ) from error
        elif isinstance(error, (OSError, PermissionError)):
            raise MermaidFileError(
                f"File system error during plugin initialization: {error!s}",
                operation="access",
                suggestion="Check file permissions and disk space",
            ) from error
        else:
            raise MermaidConfigError(
                f"Plugin configuration error: {error!s}"
            ) from error

    def on_files(self, files: Any, *, config: Any) -> Any:
        """ビルド対象ファイル一覧から生成物の追跡を開始する"""
        if not self._should_be_enabled(self.config) or not self.processor:
            return files

        # Filesオブジェクトを保存
        self.files = files
        self.generated_images = []

        return files

    def _register_generated_images_to_files(
        self, image_paths: list[str], docs_dir: Path, config: Any
    ) -> None:
        """生成された画像をFilesオブジェクトに追加"""
        if not (image_paths and self.files):
            return

        for image_path in image_paths:
            # 生成済み画像をMkDocsのビルド対象として登録
            self._add_image_file_to_files(image_path, docs_dir, config)

    def _add_image_file_to_files(
        self, image_path: str, docs_dir: Path, config: Any
    ) -> None:
        """単一の画像ファイルをFilesオブジェクトに追加"""
        image_file_path = Path(image_path)
        if not image_file_path.exists():
            self.logger.warning(f"Generated image file does not exist: {image_path}")
            return

        try:
            from mkdocs.structure.files import File

            rel_path = image_file_path.relative_to(docs_dir)
            rel_path_str = str(rel_path).replace("\\", "/")

            # 既に同じパスのファイルが登録されていれば置き換え
            self._remove_existing_file_by_path(rel_path_str)

            file_obj = File(
                rel_path_str,
                str(docs_dir),
                str(config["site_dir"]),
                use_directory_urls=config.get("use_directory_urls", True),
            )
            file_obj.src_path = file_obj.src_path.replace("\\", "/")
            if self.files is not None:
                self.files.append(file_obj)

        except ValueError as e:
            self.logger.error(f"Error processing image path {image_path}: {e}")

    def _remove_existing_file_by_path(self, src_path: str) -> bool:
        """指定されたsrc_pathを持つファイルを削除する"""
        if not self.files:
            return False

        normalized_src_path = src_path.replace("\\", "/")

        # 既存Filesリストから一致するエントリを探し出し除去
        for file_obj in self.files:
            if file_obj.src_path.replace("\\", "/") == normalized_src_path:
                self.files.remove(file_obj)
                return True
        return False

    def _process_mermaid_diagrams(
        self, markdown: str, page: Any, config: Any
    ) -> Optional[str]:
        """Mermaid図の処理を実行"""
        if not self.processor:
            return markdown

        try:
            docs_dir = Path(config["docs_dir"])
            output_dir = docs_dir / self.config["output_dir"]

            modified_content, image_paths = self.processor.process_page(
                page.file.src_path,
                markdown,
                output_dir,
                page_url=page.url,
                docs_dir=docs_dir,
            )

            self.generated_images.extend(image_paths)
            self._register_generated_images_to_files(image_paths, docs_dir, config)

            if image_paths:
                self.logger.info(
                    f"Generated {len(image_paths)} Mermaid diagrams for "
                    f"{page.file.src_path}"
                )

            return modified_content

        except MermaidPreprocessorError:
            # Mermaid変換で失敗した場合は設定に応じて例外を投げるか元Markdownを返す
            return self._handle_processing_error(
                page.file.src_path, "preprocessor", None, markdown
            )
        except (FileNotFoundError, OSError, PermissionError) as e:
            # ファイルI/O周りの失敗は利用者にリカバリー策を提示
            return self._handle_processing_error(
                page.file.src_path, "file_system", e, markdown
            )
        except ValueError as e:
            # Mermaid入力の検証エラーを拾い、必要なら例外を伝播させる
            return self._handle_processing_error(
                page.file.src_path, "validation", e, markdown
            )
        except Exception as e:
            # 予期しない例外は最後の手段としてまとめて処理
            return self._handle_processing_error(
                page.file.src_path, "unexpected", e, markdown
            )

    def _handle_processing_error(
        self,
        page_path: str,
        error_type: str,
        error: Exception | None,
        fallback_content: str,
    ) -> str:
        """統一されたエラー処理ハンドラー"""
        if error_type == "preprocessor":
            self.logger.error(f"Error processing {page_path}")
            if self.config["error_on_fail"]:
                if error:
                    raise error
                else:
                    raise MermaidPreprocessorError(f"Error processing {page_path}")
        elif error_type == "file_system":
            self.logger.error(f"File system error processing {page_path}: {error!s}")
            if self.config["error_on_fail"]:
                raise MermaidFileError(
                    f"File system error processing {page_path}: {error!s}",
                    file_path=page_path,
                    operation="process",
                    suggestion=(
                        "Check file permissions and ensure output directory exists"
                    ),
                ) from error
        elif error_type == "validation":
            self.logger.error(f"Validation error processing {page_path}: {error!s}")
            if self.config["error_on_fail"]:
                raise MermaidValidationError(
                    f"Validation error processing {page_path}: {error!s}",
                    validation_type="page_processing",
                    invalid_value=page_path,
                ) from error
        else:  # unexpected
            self.logger.error(f"Unexpected error processing {page_path}: {error!s}")
            if self.config["error_on_fail"]:
                raise MermaidPreprocessorError(
                    f"Unexpected error: {error!s}"
                ) from error

        return fallback_content

    def _ensure_attr_list_extension_enabled(self, mkdocs_config: Any) -> None:
        """attr_list拡張が有効でない場合に利用者へ明示的に通知する"""
        extensions = self._extract_markdown_extensions(mkdocs_config)

        if self._has_attr_list_extension(extensions):
            return

        raise MermaidConfigError(
            "image_id_enabled requires that the attr_list extension must be enabled.",
            config_key="markdown_extensions",
            suggestion=(
                "Add 'attr_list' to markdown_extensions in mkdocs.yml or disable "
                "image_id_enabled."
            ),
        )

    @staticmethod
    def _extract_markdown_extensions(config: Any) -> list[Any]:
        """MkDocs設定からmarkdown_extensionsのリストを取得する"""
        extensions_value: Any = None
        try:
            extensions_value = config["markdown_extensions"]
        except (KeyError, TypeError):
            if hasattr(config, "get"):
                extensions_value = config.get("markdown_extensions", None)

        return MermaidSvgConverterPlugin._normalize_extensions(extensions_value)

    @staticmethod
    def _normalize_extensions(value: Any) -> list[Any]:
        """markdown_extensions設定をリストへ正規化する"""
        if value is None:
            return []

        if isinstance(value, list):
            return value

        if isinstance(value, Iterable) and not isinstance(value, (str, bytes)):
            return list(value)

        return []

    @staticmethod
    def _has_attr_list_extension(extensions: list[Any]) -> bool:
        """attr_list拡張が有効かどうかを判定する"""
        attr_identifiers = {"attr_list", "markdown.extensions.attr_list"}

        for extension in extensions:
            if isinstance(extension, str):
                normalized = extension.split(":")[0].lower()
                if normalized in attr_identifiers or normalized.endswith("attr_list"):
                    return True
            elif isinstance(extension, dict):
                for key in extension:
                    normalized = str(key).split(":")[0].lower()
                    if normalized in attr_identifiers or normalized.endswith(
                        "attr_list"
                    ):
                        return True
        return False

    def on_page_markdown(
        self, markdown: str, *, page: Any, config: Any, files: Any
    ) -> Optional[str]:
        """ビルド対象MarkdownからMermaidブロックを検出し変換する"""
        if not self._should_be_enabled(self.config):
            return markdown

        if self.is_serve_mode:
            return markdown

        return self._process_mermaid_diagrams(markdown, page, config)

    def on_post_build(self, *, config: Any) -> None:
        """静的サイト出力後に生成画像の記録やクリーンアップを行う"""
        if not self._should_be_enabled(self.config):
            return

        # 生成した画像の総数をINFOレベルで出力
        if self.generated_images:
            self.logger.info(
                f"Generated {len(self.generated_images)} Mermaid images total"
            )

        # 生成画像のクリーンアップ
        if self.config.get("cleanup_generated_images", False) and self.generated_images:
            clean_generated_images(self.generated_images, self.logger)

    def on_serve(self, server: Any, *, config: Any, builder: Any) -> Any:
        """開発サーバー起動時のフックで追加処理が不要であることを示す"""
        if not self._should_be_enabled(self.config):
            return server

        return server


# 後方互換性のため旧プラグイン名をエイリアスとして公開
# 将来のバージョンで削除予定
MermaidToImagePlugin = MermaidSvgConverterPlugin
