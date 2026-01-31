from __future__ import annotations

import logging
import os
import sys
from collections.abc import Iterable
from pathlib import Path
from typing import TYPE_CHECKING, Any

from mkdocs.plugins import BasePlugin

if TYPE_CHECKING:
    from mkdocs.structure.files import Files

    from .image_generator import AutoRenderer, BatchRenderItem

from .config import ConfigManager
from .exceptions import (
    MermaidCLIError,
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
        self.processor: MermaidProcessor | None = None
        self.generated_images: list[str] = []
        self.files: Files | None = None
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
        self.batch_items: list[BatchRenderItem] = []

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
    ) -> str | None:
        """Mermaid図の処理を実行"""
        if not self.processor:
            return markdown

        try:
            docs_dir = Path(config["docs_dir"])
            output_dir = docs_dir / self.config["output_dir"]

            # batch_itemsが存在すれば収集モードで処理
            batch_items = getattr(self, "batch_items", None)

            modified_content, image_paths = self.processor.process_page(
                page.file.src_path,
                markdown,
                output_dir,
                page_url=page.url,
                docs_dir=docs_dir,
                batch_items=batch_items,
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
    ) -> str | None:
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

        # beautiful-mermaid対応ダイアグラムの一括レンダリング
        self._execute_batch_render(config)

        # 生成した画像の総数をINFOレベルで出力
        if self.generated_images:
            self.logger.info(
                f"Generated {len(self.generated_images)} Mermaid images total"
            )

        # 生成画像のクリーンアップ
        if self.config.get("cleanup_generated_images", False) and self.generated_images:
            clean_generated_images(self.generated_images, self.logger)

    def _execute_batch_render(self, config: Any) -> None:
        """収集済みbatch_itemsを一括レンダリングし、docs/とsite/に書き出す"""
        batch_items: list[BatchRenderItem] = getattr(self, "batch_items", [])
        if not batch_items or not self.processor:
            return

        from .image_generator import AutoRenderer

        renderer = self.processor.image_generator.renderer
        if not isinstance(renderer, AutoRenderer):
            return

        beautiful_renderer = renderer.beautiful_renderer

        try:
            results = beautiful_renderer.batch_render(batch_items)
        except MermaidCLIError as exc:
            # プロセスクラッシュ時はページ情報を付与してビルド中断
            page_files = {item.page_file for item in batch_items}
            pages_info = ", ".join(sorted(page_files))
            raise MermaidCLIError(
                f"beautiful-mermaid一括レンダリングに失敗 "
                f"(対象ページ: {pages_info}): {exc!s}",
                command="node",
            ) from exc

        # IDからBatchRenderItemへのマッピングを作成
        item_map = {item.id: item for item in batch_items}

        # docs_dirとsite_dirを取得（site/への書き出しに使用）
        docs_dir = self._resolve_docs_dir(config)
        site_dir = Path(config["site_dir"]) if config.get("site_dir") else None

        # 成功結果をdocs/とsite/に書き出す
        failed_items: list[BatchRenderItem] = []
        for result in results:
            item = item_map.get(result.id)
            if item is None:
                continue

            if not result.success or result.svg is None:
                failed_items.append(item)
                continue

            self._write_svg_to_docs_and_site(
                item.output_path, result.svg, docs_dir, site_dir
            )
            self.generated_images.append(item.output_path)
            self._log_batch_svg_generation(item.output_path, item.page_file)

        # 失敗分をmmdcでフォールバック
        if failed_items:
            self._fallback_to_mmdc(failed_items, renderer, docs_dir, site_dir)

    @staticmethod
    def _log_batch_svg_generation(output_path: str, page_file: str) -> None:
        """バッチ生成したSVGのログを既存mmdc形式に合わせて出力する"""
        mkdocs_logger = logging.getLogger("mkdocs")
        filename = Path(output_path).name
        mkdocs_logger.info(
            "Converting Mermaid diagram to SVG: %s from %s",
            filename,
            page_file,
        )

    def _resolve_docs_dir(self, config: Any) -> Path | None:
        """MkDocs設定からdocs_dirを取得する"""
        docs_dir_value = config.get("docs_dir")
        if docs_dir_value is not None:
            return Path(docs_dir_value)
        return None

    def _write_svg_to_docs_and_site(
        self,
        docs_path: str,
        svg_content: str,
        docs_dir: Path | None,
        site_dir: Path | None,
    ) -> None:
        """SVGをdocs/配下に書き出し、site/配下にもコピーする"""
        # docs/配下に書き出す
        output_path = Path(docs_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(svg_content, encoding="utf-8")

        # site/配下にもコピー（on_post_build時点ではMkDocsコピー済みのため）
        if docs_dir is not None and site_dir is not None:
            try:
                rel_path = output_path.relative_to(docs_dir)
                site_path = site_dir / rel_path
                site_path.parent.mkdir(parents=True, exist_ok=True)
                site_path.write_text(svg_content, encoding="utf-8")
            except ValueError:
                # docs_dirからの相対パス解決に失敗した場合はスキップ
                pass

    def _fallback_to_mmdc(
        self,
        failed_items: list[BatchRenderItem],
        renderer: AutoRenderer,
        docs_dir: Path | None,
        site_dir: Path | None,
    ) -> None:
        """batch_renderで失敗したダイアグラムをmmdcで個別に再処理する"""
        mmdc_renderer = renderer.mmdc_renderer
        for item in failed_items:
            try:
                config_for_mmdc = dict(self.config)
                config_for_mmdc["theme"] = item.theme
                success = mmdc_renderer.render_svg(
                    item.code,
                    item.output_path,
                    config_for_mmdc,
                    page_file=item.page_file,
                )
                if success:
                    self.generated_images.append(item.output_path)
                    self._copy_to_site_dir(item.output_path, docs_dir, site_dir)
                    self.logger.info(f"mmdcフォールバックで生成: {item.output_path}")
                else:
                    self.logger.warning(
                        f"mmdcフォールバックも失敗: {item.output_path} "
                        f"(page: {item.page_file})"
                    )
            except Exception as exc:
                self.logger.warning(
                    f"mmdcフォールバック中にエラー: {exc!s} (page: {item.page_file})"
                )

    def _copy_to_site_dir(
        self,
        docs_path: str,
        docs_dir: Path | None,
        site_dir: Path | None,
    ) -> None:
        """docs/配下のファイルをsite/配下にコピーする"""
        if docs_dir is None or site_dir is None:
            return
        try:
            source = Path(docs_path)
            rel_path = source.relative_to(docs_dir)
            dest = site_dir / rel_path
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_bytes(source.read_bytes())
        except (ValueError, OSError):
            pass

    def on_serve(self, server: Any, *, config: Any, builder: Any) -> Any:
        """開発サーバー起動時のフックで追加処理が不要であることを示す"""
        if not self._should_be_enabled(self.config):
            return server

        return server


# 後方互換性のため旧プラグイン名をエイリアスとして公開
# 将来のバージョンで削除予定
MermaidToImagePlugin = MermaidSvgConverterPlugin
