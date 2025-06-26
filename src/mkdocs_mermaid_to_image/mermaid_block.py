"""
MkDocs Mermaid to Image Plugin - Mermaidブロック処理

このファイルは、個別のMermaidブロックとその画像生成責任を定義します。
"""

import contextlib
from pathlib import Path
from typing import Any, Optional

from .utils import generate_image_filename


class MermaidBlock:
    """
    Mermaidコードブロックとその画像生成責任を持つクラス

    単一責任原則に基づき、MermaidBlockは自身の画像生成と
    Markdown生成の責任を持ちます。
    """

    def __init__(
        self,
        code: str,
        start_pos: int,
        end_pos: int,
        attributes: Optional[dict[str, Any]] = None,
    ):
        """
        MermaidBlockのコンストラクタ

        Args:
            code (str): Mermaidのコード内容
            start_pos (int): Markdown内での開始位置
            end_pos (int): Markdown内での終了位置
            attributes (Optional[Dict]): ブロック属性
        """
        self.code = code.strip()
        self.start_pos = start_pos
        self.end_pos = end_pos
        self.attributes = attributes or {}

    def __repr__(self) -> str:
        """オブジェクトの文字列表現を返すメソッド"""
        return (
            f"MermaidBlock(code='{self.code[:50]}...', "
            f"start={self.start_pos}, end={self.end_pos})"
        )

    def generate_image(
        self, output_path: str, image_generator: Any, config: dict[str, Any]
    ) -> bool:
        """
        このMermaidブロックから画像を生成

        Args:
            output_path (str): 生成する画像ファイルのパス
            image_generator: 画像生成を行うジェネレータ
            config (Dict): 設定情報

        Returns:
            bool: 画像生成が成功した場合True
        """
        # ブロック固有の属性をマージした設定を作成
        merged_config = config.copy()

        # ブロック属性で設定をオーバーライド
        if "theme" in self.attributes:
            merged_config["theme"] = self.attributes["theme"]
        if "background" in self.attributes:
            merged_config["background_color"] = self.attributes["background"]
        if "width" in self.attributes:
            with contextlib.suppress(ValueError):
                merged_config["width"] = int(self.attributes["width"])
        if "height" in self.attributes:
            with contextlib.suppress(ValueError):
                merged_config["height"] = int(self.attributes["height"])

        result = image_generator.generate(self.code, output_path, merged_config)
        return bool(result)

    def get_image_markdown(
        self, image_path: str, page_file: str, preserve_original: bool = False
    ) -> str:
        """
        このブロックの画像Markdown記法を生成

        Args:
            image_path (str): 画像ファイルのパス
            page_file (str): ページファイルのパス（相対パス計算用）
            preserve_original (bool): 元のコードブロックも保持するか

        Returns:
            str: 画像のMarkdown記法
        """
        # MkDocsでは画像は site/assets/images にコピーされるため、
        # サイトルートからの相対パスを計算する
        image_path_obj = Path(image_path)

        # docs/assets/images/filename.png → assets/images/filename.png
        if "docs" in image_path_obj.parts:
            # docs ディレクトリ以降の部分を取得
            docs_index = image_path_obj.parts.index("docs")
            relative_parts = image_path_obj.parts[docs_index + 1 :]
            image_site_path = str(Path(*relative_parts))
        else:
            # フォールバック: ファイル名のみ使用
            image_site_path = f"assets/images/{image_path_obj.name}"

        # ページファイルからの相対パスを計算
        page_path = Path(page_file)
        page_depth = len(page_path.parent.parts) if page_path.parent != Path() else 0

        # サブディレクトリにいる場合は上位ディレクトリへの相対パスを追加
        if page_depth > 0:
            relative_image_path = "../" * page_depth + image_site_path
        else:
            relative_image_path = image_site_path

        # 画像のMarkdown記法を作成
        image_markdown = f"![Mermaid Diagram]({relative_image_path})"

        # preserve_originalが有効な場合、元のコードも保持
        if preserve_original:
            # 元のブロック内容を再構築
            if self.attributes:
                # 属性付きブロックの場合
                attr_str = ", ".join(f"{k}: {v}" for k, v in self.attributes.items())
                original_block = f"```mermaid {{{attr_str}}}\n{self.code}\n```"
            else:
                # 基本ブロックの場合
                original_block = f"```mermaid\n{self.code}\n```"

            # 画像と元のブロックを両方含める
            image_markdown = f"{image_markdown}\n\n{original_block}"

        return image_markdown

    def get_filename(self, page_file: str, index: int, image_format: str) -> str:
        """
        このブロック用の画像ファイル名を生成

        Args:
            page_file (str): ページファイルのパス
            index (int): ページ内でのブロックインデックス
            image_format (str): 画像形式（png/svg）

        Returns:
            str: 画像ファイル名
        """
        return generate_image_filename(page_file, index, self.code, image_format)
