"""
MkDocs Mermaid to Image Plugin - Markdown処理

このファイルは、Markdownの解析と置換処理を専門に扱います。
"""

import re
from typing import Any

from .mermaid_block import MermaidBlock
from .utils import setup_logger


class MarkdownProcessor:
    """
    Markdownの解析と変換を専門に扱うクラス

    単一責任原則に基づき、Markdown操作のみに責任を持ちます。
    """

    def __init__(self, config: dict[str, Any]) -> None:
        """
        MarkdownProcessorのコンストラクタ

        Args:
            config (dict): 設定情報
        """
        self.config = config
        self.logger = setup_logger(__name__, config.get("log_level", "INFO"))

    def extract_mermaid_blocks(self, markdown_content: str) -> list[MermaidBlock]:
        """
        MarkdownコンテンツからすべてのMermaidコードブロックを抽出

        Args:
            markdown_content (str): 処理対象のMarkdownテキスト

        Returns:
            List[MermaidBlock]: 見つかったMermaidブロックのリスト
        """
        blocks = []

        # 基本的なmermaidブロックのパターン（属性なし）
        basic_pattern = r"```mermaid\s*\n(.*?)\n```"

        # 属性付きmermaidブロックのパターン
        attr_pattern = r"```mermaid\s*\{([^}]*)\}\s*\n(.*?)\n```"

        # まず属性付きブロックを検索（より具体的なパターンを先に処理）
        for match in re.finditer(attr_pattern, markdown_content, re.DOTALL):
            attr_str = match.group(1).strip()
            code = match.group(2).strip()

            # 属性文字列を解析して辞書に変換
            attributes = self._parse_attributes(attr_str)

            # MermaidBlockオブジェクトを作成してリストに追加
            block = MermaidBlock(
                code=code,
                start_pos=match.start(),
                end_pos=match.end(),
                attributes=attributes,
            )
            blocks.append(block)

        # 次に基本的なブロック（属性なし）を検索
        for match in re.finditer(basic_pattern, markdown_content, re.DOTALL):
            # 既に属性付きブロックとして見つかっている場合はスキップ
            overlaps = any(
                match.start() >= block.start_pos and match.end() <= block.end_pos
                for block in blocks
            )
            if not overlaps:
                code = match.group(1).strip()
                block = MermaidBlock(
                    code=code, start_pos=match.start(), end_pos=match.end()
                )
                blocks.append(block)

        # ブロックを出現位置順にソート
        blocks.sort(key=lambda x: x.start_pos)

        self.logger.info(f"Found {len(blocks)} Mermaid blocks")
        return blocks

    def _parse_attributes(self, attr_str: str) -> dict[str, Any]:
        """
        属性文字列を解析して辞書に変換

        Args:
            attr_str (str): 属性文字列（例: "theme: dark, background: black"）

        Returns:
            dict: 属性辞書
        """
        attributes = {}
        if attr_str:
            # カンマで分割して各属性を処理
            for attr in attr_str.split(","):
                if ":" in attr:
                    key, value = attr.split(":", 1)
                    # 前後の空白と引用符を除去
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
    ) -> str:
        """
        Markdownコンテンツ内のMermaidブロックを画像参照に置換

        Args:
            markdown_content (str): 元のMarkdownコンテンツ
            blocks (List[MermaidBlock]): 置換対象のMermaidブロック
            image_paths (List[str]): 対応する画像ファイルのパス
            page_file (str): ページファイルのパス（相対パス計算用）

        Returns:
            str: Mermaidブロックが画像参照に置換されたMarkdown

        Raises:
            ValueError: ブロック数と画像パス数が一致しない場合
        """
        if len(blocks) != len(image_paths):
            raise ValueError("Number of blocks and image paths must match")

        # ブロックを位置の逆順でソート（後ろから処理して位置のずれを防ぐ）
        sorted_blocks = sorted(
            zip(blocks, image_paths), key=lambda x: x[0].start_pos, reverse=True
        )

        result = markdown_content

        # 各ブロックを画像参照に置換
        for block, image_path in sorted_blocks:
            # ブロックが画像Markdown記法を生成
            image_markdown = block.get_image_markdown(
                image_path, page_file, self.config.get("preserve_original", False)
            )

            # ブロックを置換（文字列の切り貼り）
            result = (
                result[: block.start_pos] + image_markdown + result[block.end_pos :]
            )

        return result
