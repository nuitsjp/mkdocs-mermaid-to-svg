from pathlib import Path
from typing import Any

from .image_generator import MermaidImageGenerator
from .markdown_processor import MarkdownProcessor
from .logging_config import get_logger


class MermaidProcessor:
    def __init__(self, config: dict[str, Any]) -> None:
        self.config = config
        self.logger = get_logger(__name__)

        self.markdown_processor = MarkdownProcessor(config)
        self.image_generator = MermaidImageGenerator(config)

    def process_page(
        self, page_file: str, markdown_content: str, output_dir: str, page_url: str = ""
    ) -> tuple[str, list[str]]:
        blocks = self.markdown_processor.extract_mermaid_blocks(markdown_content)

        if not blocks:
            return markdown_content, []

        image_paths = []
        successful_blocks = []

        for i, block in enumerate(blocks):
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
                    "Keeping original Mermaid block due to generation failure"
                )
                continue
            else:
                pass

        if successful_blocks:
            modified_content = self.markdown_processor.replace_blocks_with_images(
                markdown_content, successful_blocks, image_paths, page_file, page_url
            )
            return modified_content, image_paths

        return markdown_content, []
