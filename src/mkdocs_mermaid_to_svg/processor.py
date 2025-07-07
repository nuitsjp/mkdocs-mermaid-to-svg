from pathlib import Path
from typing import Any, Union

from .exceptions import MermaidFileError, MermaidImageError, MermaidPreprocessorError
from .image_generator import MermaidImageGenerator
from .logging_config import get_logger
from .markdown_processor import MarkdownProcessor


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

        image_paths = []
        successful_blocks = []

        for i, block in enumerate(blocks):
            try:
                image_filename = block.get_filename(
                    page_file, i, self.config["image_format"]
                )
                image_path = Path(output_dir) / image_filename

                success = block.generate_image(
                    str(image_path), self.image_generator, self.config
                )

                if success:
                    image_paths.append(str(image_path))
                    successful_blocks.append(block)
                elif not self.config["error_on_fail"]:
                    self.logger.warning(
                        "Image generation failed, keeping original Mermaid block",
                        extra={
                            "context": {
                                "page_file": page_file,
                                "block_index": i,
                                "image_path": str(image_path),
                                "suggestion": "Check Mermaid syntax and CLI "
                                "configuration",
                            }
                        },
                    )
                    continue
                else:
                    raise MermaidImageError(
                        f"Image generation failed for block {i} in {page_file}",
                        image_path=str(image_path),
                        suggestion="Check Mermaid diagram syntax and CLI availability",
                    )

            except MermaidPreprocessorError:
                # カスタム例外はそのまま再発生
                raise
            except (FileNotFoundError, OSError, PermissionError) as e:
                error_msg = (
                    f"File system error processing block {i} in {page_file}: {e!s}"
                )
                self.logger.error(error_msg)
                if self.config["error_on_fail"]:
                    raise MermaidFileError(
                        error_msg,
                        file_path=str(image_path),
                        operation="image_generation",
                        suggestion="Check file permissions and ensure output "
                        "directory exists",
                    ) from e
                continue
            except Exception as e:
                error_msg = (
                    f"Unexpected error processing block {i} in {page_file}: {e!s}"
                )
                self.logger.error(error_msg)
                if self.config["error_on_fail"]:
                    raise MermaidPreprocessorError(error_msg) from e
                continue

        if successful_blocks:
            modified_content = self.markdown_processor.replace_blocks_with_images(
                markdown_content, successful_blocks, image_paths, page_file, page_url
            )
            return modified_content, image_paths

        return markdown_content, []
