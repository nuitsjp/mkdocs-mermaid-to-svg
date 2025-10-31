import re
from pathlib import Path
from typing import Any

from .exceptions import MermaidParsingError
from .logging_config import get_logger
from .mermaid_block import MermaidBlock


class MarkdownProcessor:
    """Markdown内のMermaid記法ブロック抽出と差し替えを担当するコンポーネント"""

    def __init__(self, config: dict[str, Any]) -> None:
        """設定値とロガーを保持し後続処理で参照できるようにする"""
        self.config = config
        self.logger = get_logger(__name__)

    def extract_mermaid_blocks(self, markdown_content: str) -> list[MermaidBlock]:
        """Markdown本文からMermaidブロックを検出してメタ情報付きで返す"""
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
        """Mermaidコードブロックに付与された属性文字列を辞書へ変換する"""
        attributes: dict[str, Any] = {}
        if not attr_str:
            return attributes

        parsed_items = self._split_attribute_string(attr_str)

        for attr in parsed_items:
            if ":" not in attr:
                continue

            key, value = attr.split(":", 1)
            key = key.strip()
            value = value.strip()

            if not key:
                continue

            if len(value) >= 2 and value[0] == value[-1] and value[0] in {'"', "'"}:
                quote = value[0]
                inner = value[1:-1]
                value = inner.replace(f"\\{quote}", quote)

            attributes[key] = value

        return attributes

    @staticmethod
    def _split_attribute_string(attr_str: str) -> list[str]:
        """カンマ区切りの属性リストを引用符の有無を考慮して分割する"""
        parts: list[str] = []
        buf: list[str] = []
        in_quote: str | None = None
        escape_next = False

        for ch in attr_str:
            if escape_next:
                buf.append(ch)
                escape_next = False
                continue

            if ch == "\\":
                escape_next = True
                continue

            if ch in {'"', "'"}:
                if in_quote == ch:
                    in_quote = None
                elif in_quote is None:
                    in_quote = ch
                buf.append(ch)
                continue

            if ch == "," and in_quote is None:
                parts.append("".join(buf).strip())
                buf = []
                continue

            buf.append(ch)

        if buf:
            parts.append("".join(buf).strip())

        return parts

    def replace_blocks_with_images(  # noqa: PLR0913
        self,
        markdown_content: str,
        blocks: list[MermaidBlock],
        image_paths: list[str],
        page_file: str,
        page_url: str = "",
        *,
        docs_dir: Path | str | None = None,
        output_dir: str | None = None,
    ) -> str:
        """抽出済みMermaidブロックを生成済み画像の参照Markdownに差し替える"""
        if len(blocks) != len(image_paths):
            raise MermaidParsingError(
                "Number of blocks and image paths must match",
                source_file=page_file,
                mermaid_code=f"Expected {len(blocks)} images, got {len(image_paths)}",
            )

        # 末尾から置換するためブロック開始位置の降順に並べ替える
        sorted_blocks = sorted(
            zip(blocks, image_paths), key=lambda x: x[0].start_pos, reverse=True
        )

        result = markdown_content

        for block, image_path in sorted_blocks:
            image_markdown = block.get_image_markdown(
                image_path,
                page_file,
                page_url=page_url,
                output_dir=self.config.get("output_dir", "assets/images")
                if output_dir is None
                else output_dir,
                docs_dir=docs_dir,
            )

            # 末尾位置から順に置換し、先頭ブロックのインデックスがずれないようにする
            result = (
                result[: block.start_pos] + image_markdown + result[block.end_pos :]
            )

        return result
