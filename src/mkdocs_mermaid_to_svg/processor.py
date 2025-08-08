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
    def __init__(self, config: dict[str, Any]) -> None:
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
    ) -> tuple[str, list[str]]:
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

        for i, block in enumerate(blocks):
            self._process_single_block(block, i, context)

        if context.successful_blocks:
            modified_content = self.markdown_processor.replace_blocks_with_images(
                markdown_content,
                context.successful_blocks,
                context.image_paths,
                page_file,
                page_url,
            )
            return modified_content, context.image_paths

        return markdown_content, []

    def _process_single_block(
        self,
        block: Any,
        index: int,
        context: ProcessingContext,
    ) -> None:
        """単一ブロックの処理"""
        try:
            image_filename = block.get_filename(context.page_file, index, "svg")
            image_path = Path(context.output_dir) / image_filename

            success = block.generate_image(
                str(image_path), self.image_generator, self.config, context.page_file
            )

            if success:
                context.image_paths.append(str(image_path))
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
