import os
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


class MermaidSvgConverterPlugin(BasePlugin):  # type: ignore[type-arg,no-untyped-call]
    config_scheme = ConfigManager.get_config_scheme()

    def __init__(self) -> None:
        super().__init__()
        self.processor: Optional[MermaidProcessor] = None
        self.generated_images: list[str] = []
        self.files: Optional[Files] = None
        self.logger = get_logger(__name__)

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
        config_dict = dict(self.config)
        ConfigManager.validate_config(config_dict)

        config_dict["log_level"] = "DEBUG" if self.is_verbose_mode else "WARNING"

        if not self._should_be_enabled(self.config):
            self.logger.info("Mermaid preprocessor plugin is disabled")
            return config

        try:
            self.processor = MermaidProcessor(config_dict)
            self.logger.info("Mermaid preprocessor plugin initialized successfully")
        except Exception as e:
            self.logger.error(f"Plugin initialization failed: {e!s}")
            self._handle_init_error(e)

        return config

    def _handle_init_error(self, error: Exception) -> None:
        """Initialize error handling with appropriate exception types."""
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
                page.file.src_path, markdown, output_dir, page_url=page.url
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
            return self._handle_processing_error(
                page.file.src_path, "preprocessor", None, markdown
            )
        except (FileNotFoundError, OSError, PermissionError) as e:
            return self._handle_processing_error(
                page.file.src_path, "file_system", e, markdown
            )
        except ValueError as e:
            return self._handle_processing_error(
                page.file.src_path, "validation", e, markdown
            )
        except Exception as e:
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

    def on_page_markdown(
        self, markdown: str, *, page: Any, config: Any, files: Any
    ) -> Optional[str]:
        if not self._should_be_enabled(self.config):
            return markdown

        if self.is_serve_mode:
            return markdown

        return self._process_mermaid_diagrams(markdown, page, config)

    def on_post_build(self, *, config: Any) -> None:
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
        if not self._should_be_enabled(self.config):
            return server

        return server


# Backward compatibility: alias for the old name
# This will be removed in a future version
MermaidToImagePlugin = MermaidSvgConverterPlugin
