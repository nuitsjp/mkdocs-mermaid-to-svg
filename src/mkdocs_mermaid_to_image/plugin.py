import os
import shutil
import sys
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


class MermaidToImagePlugin(BasePlugin):  # type: ignore[type-arg,no-untyped-call]
    config_scheme = ConfigManager.get_config_scheme()

    def __init__(self) -> None:
        super().__init__()
        self.processor: Optional[MermaidProcessor] = None
        self.generated_images: list[str] = []
        self.files: Optional[Files] = None

        self.is_serve_mode: bool = "serve" in sys.argv
        self.is_verbose_mode: bool = "--verbose" in sys.argv or "-v" in sys.argv

    def _should_be_enabled(self, config: dict[str, Any]) -> bool:
        """環境変数設定に基づいてプラグインが有効化されるべきかどうかを判定"""
        enabled_if_env = config.get("enabled_if_env")

        if enabled_if_env is not None:
            # enabled_if_envが設定されている場合、環境変数の存在と値をチェック
            env_value = os.environ.get(enabled_if_env)
            return env_value is not None and env_value.strip() != ""

        # enabled_if_envが設定されていない場合は通常のenabled設定に従う
        return bool(config.get("enabled", True))

    def on_config(self, config: Any) -> Any:
        try:
            config_dict = dict(self.config)
            ConfigManager.validate_config(config_dict)

            # verboseモードでない場合は、INFOレベルに設定
            if not self.is_verbose_mode:
                config_dict["log_level"] = "WARNING"  # 下位モジュールは詳細ログを抑制

            logger = get_logger(__name__)

            if not self._should_be_enabled(self.config):
                logger.info("Mermaid preprocessor plugin is disabled")
                return config

            self.processor = MermaidProcessor(config_dict)

            logger.info("Mermaid preprocessor plugin initialized successfully")

        except (MermaidConfigError, MermaidFileError) as e:
            logger = get_logger(__name__)
            logger.error(f"Configuration error: {e!s}")
            raise
        except FileNotFoundError as e:
            logger = get_logger(__name__)
            logger.error(f"Required file not found: {e!s}")
            raise MermaidFileError(
                f"Required file not found during plugin initialization: {e!s}",
                operation="read",
                suggestion="Ensure all required files exist",
            ) from e
        except (OSError, PermissionError) as e:
            logger = get_logger(__name__)
            logger.error(f"File system error: {e!s}")
            raise MermaidFileError(
                f"File system error during plugin initialization: {e!s}",
                operation="access",
                suggestion="Check file permissions and disk space",
            ) from e
        except Exception as e:
            logger = get_logger(__name__)
            logger.error(f"Unexpected error during plugin initialization: {e!s}")
            raise MermaidConfigError(f"Plugin configuration error: {e!s}") from e

        return config

    def on_files(self, files: Any, *, config: Any) -> Any:
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

        from mkdocs.structure.files import File

        for image_path in image_paths:
            image_file_path = Path(image_path)
            if image_file_path.exists():
                # docs_dirからの相対パスを計算
                rel_path = image_file_path.relative_to(docs_dir)
                # ファイルオブジェクトを作成してFilesに追加
                file_obj = File(
                    str(rel_path),
                    str(docs_dir),
                    str(config["site_dir"]),
                    use_directory_urls=config.get("use_directory_urls", True),
                )
                self.files.append(file_obj)

    def _process_mermaid_diagrams(
        self, markdown: str, page: Any, config: Any
    ) -> Optional[str]:
        """Mermaid図の処理を実行"""
        if not self.processor:
            return markdown

        try:
            # ソース側のdocsディレクトリ内に画像を生成
            docs_dir = Path(config["docs_dir"])
            output_dir = docs_dir / self.config["output_dir"]

            modified_content, image_paths = self.processor.process_page(
                page.file.src_path,
                markdown,
                output_dir,
                page_url=page.url,
            )

            self.generated_images.extend(image_paths)

            # 生成された画像をFilesオブジェクトに追加
            self._register_generated_images_to_files(image_paths, docs_dir, config)

            # 画像を生成した場合、常にINFOレベルでログを出力
            if image_paths:
                logger = get_logger(__name__)
                logger.info(
                    f"Generated {len(image_paths)} Mermaid diagrams for "
                    f"{page.file.src_path}"
                )

            return modified_content

        except MermaidPreprocessorError as e:
            logger = get_logger(__name__)
            logger.error(f"Error processing {page.file.src_path}: {e!s}")
            if self.config["error_on_fail"]:
                raise
            return markdown

        except (FileNotFoundError, OSError, PermissionError) as e:
            logger = get_logger(__name__)
            logger.error(f"File system error processing {page.file.src_path}: {e!s}")
            if self.config["error_on_fail"]:
                raise MermaidFileError(
                    f"File system error processing {page.file.src_path}: {e!s}",
                    file_path=page.file.src_path,
                    operation="process",
                    suggestion="Check file permissions and ensure output "
                    "directory exists",
                ) from e
            return markdown
        except ValueError as e:
            logger = get_logger(__name__)
            logger.error(f"Validation error processing {page.file.src_path}: {e!s}")
            if self.config["error_on_fail"]:
                raise MermaidValidationError(
                    f"Validation error processing {page.file.src_path}: {e!s}",
                    validation_type="page_processing",
                    invalid_value=page.file.src_path,
                ) from e
            return markdown
        except Exception as e:
            logger = get_logger(__name__)
            logger.error(f"Unexpected error processing {page.file.src_path}: {e!s}")
            if self.config["error_on_fail"]:
                raise MermaidPreprocessorError(f"Unexpected error: {e!s}") from e
            return markdown

    def on_page_markdown(
        self, markdown: str, *, page: Any, config: Any, files: Any
    ) -> Optional[str]:
        if not self._should_be_enabled(self.config):
            return markdown

        if self.is_serve_mode:
            logger = get_logger(__name__)
            logger.debug(
                f"Skipping Mermaid image generation in serve mode for "
                f"{page.file.src_path}"
            )
            return markdown

        # デバッグログを追加
        logger = get_logger(__name__)
        logger.debug(f"Processing page: {page.file.src_path}")

        return self._process_mermaid_diagrams(markdown, page, config)

    def on_post_build(self, *, config: Any) -> None:
        if not self._should_be_enabled(self.config):
            return

        # 生成した画像の総数をINFOレベルで出力
        if self.generated_images:
            logger = get_logger(__name__)
            logger.info(f"Generated {len(self.generated_images)} Mermaid images total")

        # 生成画像のクリーンアップ
        if self.config.get("cleanup_generated_images", False) and self.generated_images:
            logger = get_logger(__name__)
            clean_generated_images(self.generated_images, logger)

        if not self.config["cache_enabled"]:
            cache_dir = self.config["cache_dir"]
            if Path(cache_dir).exists():
                shutil.rmtree(cache_dir)
                logger = get_logger(__name__)
                logger.debug(f"Cleaned up cache directory: {cache_dir}")

    def on_serve(self, server: Any, *, config: Any, builder: Any) -> Any:
        if not self._should_be_enabled(self.config):
            return server

        if self.config["cache_enabled"]:
            cache_dir = self.config["cache_dir"]
            if Path(cache_dir).exists():
                server.watch(cache_dir)

        return server
