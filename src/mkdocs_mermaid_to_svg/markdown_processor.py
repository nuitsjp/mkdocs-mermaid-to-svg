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

        fence_pattern = re.compile(
            r"^(?P<indent>[ \t]{0,3})(?P<fence>`{3,}|~{3,})(?P<info>[^\n]*)$",
            re.MULTILINE,
        )

        in_fence = False
        open_fence_char = ""
        open_fence_len = 0
        mermaid_start = 0
        mermaid_content_start = 0
        mermaid_attributes: dict[str, Any] = {}
        in_mermaid = False

        for match in fence_pattern.finditer(markdown_content):
            fence = match.group("fence")
            info = match.group("info") or ""
            info_stripped = info.strip()
            fence_char = fence[0]

            if not in_fence:
                if fence_char == "`" and "`" in info:
                    continue
                attributes = self._parse_mermaid_info(info_stripped)
                in_mermaid = attributes is not None
                in_fence = True
                open_fence_char = fence_char
                open_fence_len = len(fence)
                mermaid_attributes = attributes or {}
                if in_mermaid:
                    mermaid_start = match.start()
                    mermaid_content_start = self._advance_past_newline(
                        markdown_content, match.end()
                    )
                continue

            if self._is_closing_fence(
                fence, info_stripped, open_fence_char, open_fence_len
            ):
                if in_mermaid:
                    code = markdown_content[mermaid_content_start : match.start()]
                    blocks.append(
                        MermaidBlock(
                            code=code,
                            start_pos=mermaid_start,
                            end_pos=match.end(),
                            attributes=mermaid_attributes,
                        )
                    )
                in_fence = False
                in_mermaid = False
                open_fence_char = ""
                open_fence_len = 0
                mermaid_attributes = {}

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

    def _parse_mermaid_info(self, info_str: str) -> dict[str, Any] | None:
        if not info_str.startswith("mermaid"):
            return None

        rest = info_str[len("mermaid") :]
        if rest and not rest[0].isspace() and not rest.startswith("{"):
            return None

        attr_match = re.search(r"\{([^}]*)\}", rest)
        if attr_match:
            return self._parse_attributes(attr_match.group(1).strip())
        return {}

    def _advance_past_newline(self, text: str, pos: int) -> int:
        if text.startswith("\r\n", pos):
            return pos + 2
        if pos < len(text) and text[pos] == "\n":
            return pos + 1
        return pos

    def _is_closing_fence(
        self, fence: str, info_str: str, fence_char: str, fence_len: int
    ) -> bool:
        return fence[0] == fence_char and len(fence) >= fence_len and info_str == ""

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
