import re
from typing import Any

from .exceptions import MermaidParsingError
from .logging_config import get_logger
from .mermaid_block import MermaidBlock


class MarkdownProcessor:
    def __init__(self, config: dict[str, Any]) -> None:
        self.config = config
        self.logger = get_logger(__name__)

    def extract_mermaid_blocks(self, markdown_content: str) -> list[MermaidBlock]:
        blocks = []

        # 属性付きパターンを先に処理
        attr_pattern = r"```mermaid\s*\{([^}]*)\}\s*\n(.*?)\n```"
        for match in re.finditer(attr_pattern, markdown_content, re.DOTALL):
            attributes = self._parse_attributes(match.group(1).strip())
            block = MermaidBlock(
                code=match.group(2).strip(),
                start_pos=match.start(),
                end_pos=match.end(),
                attributes=attributes,
            )
            blocks.append(block)

        # 基本パターンを処理（重複チェック付き）
        basic_pattern = r"```mermaid\s*\n(.*?)\n```"
        for match in re.finditer(basic_pattern, markdown_content, re.DOTALL):
            if not self._overlaps_with_existing_blocks(match, blocks):
                block = MermaidBlock(
                    code=match.group(1).strip(),
                    start_pos=match.start(),
                    end_pos=match.end(),
                )
                blocks.append(block)

        blocks.sort(key=lambda x: x.start_pos)
        self.logger.info(f"Found {len(blocks)} Mermaid blocks")
        return blocks

    def _overlaps_with_existing_blocks(
        self, match: re.Match[str], blocks: list[MermaidBlock]
    ) -> bool:
        """マッチが既存ブロックと重複するかチェック"""
        return any(
            match.start() >= block.start_pos and match.end() <= block.end_pos
            for block in blocks
        )

    def _parse_attributes(self, attr_str: str) -> dict[str, Any]:
        attributes = {}
        if attr_str:
            for attr in attr_str.split(","):
                if ":" in attr:
                    key, value = attr.split(":", 1)
                    key = key.strip()
                    value = value.strip().strip("\"'")
                    attributes[key] = value
        return attributes

    def replace_blocks_with_images(
        self,
        markdown_content: str,
        blocks: list[MermaidBlock],
        image_paths: list[str],
        page_file: str,
        page_url: str = "",
    ) -> str:
        if len(blocks) != len(image_paths):
            raise MermaidParsingError(
                "Number of blocks and image paths must match",
                source_file=page_file,
                mermaid_code=f"Expected {len(blocks)} images, got {len(image_paths)}",
            )

        sorted_blocks = sorted(
            zip(blocks, image_paths), key=lambda x: x[0].start_pos, reverse=True
        )

        result = markdown_content

        for block, image_path in sorted_blocks:
            image_markdown = block.get_image_markdown(
                image_path,
                page_file,
                page_url,
            )

            result = (
                result[: block.start_pos] + image_markdown + result[block.end_pos :]
            )

        return result
