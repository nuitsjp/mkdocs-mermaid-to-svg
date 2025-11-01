import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Union

from .exceptions import MermaidFileError, MermaidImageError, MermaidPreprocessorError
from .image_generator import MermaidImageGenerator
from .logging_config import get_logger
from .markdown_processor import MarkdownProcessor


@dataclass
class ProcessingContext:
    """ブロック処理のコンテキスト情報"""

    page_file: str
    output_dir: Union[str, Path]
    image_paths: list[str]
    successful_blocks: list[Any]


class MermaidProcessor:
    """Markdown解析と画像生成を統合してページ単位で処理する"""

    def __init__(self, config: dict[str, Any]) -> None:
        """構成要素を初期化し、後続処理で利用するインスタンスを準備する"""
        self.config = config
        self.logger = get_logger(__name__)

        self.markdown_processor = MarkdownProcessor(config)
        self.image_generator = MermaidImageGenerator(config)

    def process_page(
        self,
        page_file: str,
        markdown_content: str,
        output_dir: Union[str, Path],
        page_url: str = "",
        docs_dir: Union[str, Path] | None = None,
    ) -> tuple[str, list[str]]:
        """1ページ分のMarkdownからMermaid図を検出し画像生成・差し替えする"""
        blocks = self.markdown_processor.extract_mermaid_blocks(markdown_content)

        if not blocks:
            return markdown_content, []

        image_paths: list[str] = []
        successful_blocks: list[Any] = []
        context = ProcessingContext(
            page_file=page_file,
            output_dir=output_dir,
            image_paths=image_paths,
            successful_blocks=successful_blocks,
        )

        # 抽出した各ブロックを順に処理し、生成に成功したものだけを記録
        for i, block in enumerate(blocks):
            self._process_single_block(block, i, context)

        if context.successful_blocks:
            docs_dir_str = str(Path(docs_dir)) if docs_dir is not None else None
            modified_content = self.markdown_processor.replace_blocks_with_images(
                markdown_content,
                context.successful_blocks,
                context.image_paths,
                page_file,
                page_url,
                docs_dir=docs_dir_str,
                output_dir=self.config.get("output_dir", "assets/images"),
            )
            return modified_content, context.image_paths

        return markdown_content, []

    def _process_single_block(
        self,
        block: Any,
        index: int,
        context: ProcessingContext,
    ) -> None:
        """単一Mermaidブロックの画像生成と結果記録を行う"""
        try:
            image_filename = block.get_filename(context.page_file, index, "svg")
            image_path = Path(context.output_dir) / image_filename

            success = block.generate_image(
                str(image_path), self.image_generator, self.config, context.page_file
            )

            if success:
                context.image_paths.append(str(image_path))
                if self.config.get("image_id_enabled", False):
                    image_id = self._generate_image_id(block, context.page_file, index)
                    block.set_render_context(image_id=image_id)
                context.successful_blocks.append(block)
            elif not self.config["error_on_fail"]:
                self._handle_generation_failure(
                    index, context.page_file, str(image_path)
                )
            else:
                raise MermaidImageError(
                    f"Image generation failed for block {index} in {context.page_file}",
                    image_path=str(image_path),
                    suggestion="Check Mermaid diagram syntax and CLI availability",
                )

        except MermaidPreprocessorError:
            raise
        except (FileNotFoundError, OSError, PermissionError) as e:
            self._handle_file_system_error(e, index, context.page_file, str(image_path))
        except Exception as e:
            self._handle_unexpected_error(e, index, context.page_file)

    def _handle_generation_failure(
        self, index: int, page_file: str, image_path: str
    ) -> None:
        """画像生成失敗時の処理"""
        self.logger.warning(
            "Image generation failed, keeping original Mermaid block",
            extra={
                "context": {
                    "page_file": page_file,
                    "block_index": index,
                    "image_path": image_path,
                    "suggestion": "Check Mermaid syntax and CLI configuration",
                }
            },
        )

    def _handle_file_system_error(
        self, error: Exception, index: int, page_file: str, image_path: str
    ) -> None:
        """ファイルシステムエラーの処理"""
        error_msg = (
            f"File system error processing block {index} in {page_file}: {error!s}"
        )
        self.logger.error(error_msg)

        if self.config["error_on_fail"]:
            raise MermaidFileError(
                error_msg,
                file_path=image_path,
                operation="image_generation",
                suggestion="Check file permissions and ensure output directory exists",
            ) from error

    def _handle_unexpected_error(
        self, error: Exception, index: int, page_file: str
    ) -> None:
        """予期しないエラーの処理"""
        error_msg = (
            f"Unexpected error processing block {index} in {page_file}: {error!s}"
        )
        self.logger.error(error_msg)

        if self.config["error_on_fail"]:
            raise MermaidPreprocessorError(error_msg) from error

    def _generate_image_id(self, block: Any, page_file: str, index: int) -> str:
        """Mermaid画像に付与する一意なIDを決定する"""
        prefix = self._slugify(
            str(self.config.get("image_id_prefix", "mermaid-diagram"))
        )
        if not prefix:
            prefix = "mermaid-diagram"

        attributes = getattr(block, "attributes", {}) or {}
        override = attributes.get("id")
        if override:
            return self._ensure_valid_start(str(override), prefix)

        page_slug = self._slugify(Path(page_file).stem)
        sequence = index + 1

        if page_slug:
            candidate = f"{prefix}-{page_slug}-{sequence}"
        else:
            candidate = f"{prefix}-{sequence}"

        return self._ensure_valid_start(candidate, prefix)

    @staticmethod
    def _slugify(value: str) -> str:
        """IDとして利用できるよう文字列を正規化する"""
        trimmed = value.strip().lower()
        if not trimmed:
            return ""

        sanitized = re.sub(r"[^a-z0-9_-]+", "-", trimmed)
        sanitized = re.sub(r"-{2,}", "-", sanitized)
        return sanitized.strip("-")

    def _ensure_valid_start(self, identifier: str, prefix: str) -> str:
        """IDが空や数字から始まる場合に接頭辞を付与して補正する"""
        fallback = prefix or "mermaid-diagram"
        sanitized = self._slugify(identifier)

        if not sanitized:
            return fallback

        if sanitized[0].isdigit():
            sanitized = f"{fallback}-{sanitized}"

        return sanitized
