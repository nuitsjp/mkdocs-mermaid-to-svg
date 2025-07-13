from pathlib import Path
from typing import Any

from .utils import generate_image_filename


def _calculate_relative_path_prefix(page_file: str) -> str:
    """ページファイルパスから適切な相対パスプレフィックスを計算する

    Args:
        page_file: ページファイルのパス（例: "appendix/mkdocs-architecture.md"）

    Returns:
        相対パスプレフィックス（例: "../" or "../../../"）
    """
    if not page_file:
        return ""

    page_path = Path(page_file)
    # ディレクトリの深さを計算（ファイル名を除く）
    depth = len(page_path.parent.parts)

    # ルートレベル（深さ0）の場合は相対パス不要
    if depth == 0:
        return ""
    else:
        # 各階層に対して "../" を追加
        return "../" * depth


class MermaidBlock:
    def __init__(
        self,
        code: str,
        start_pos: int,
        end_pos: int,
        attributes: dict[str, Any] | None = None,
    ):
        self.code = code.strip()
        self.start_pos = start_pos
        self.end_pos = end_pos
        self.attributes = attributes or {}

    def __repr__(self) -> str:
        return (
            f"MermaidBlock(code='{self.code[:50]}...', "
            f"start={self.start_pos}, end={self.end_pos})"
        )

    def generate_image(
        self,
        output_path: str,
        image_generator: Any,
        config: dict[str, Any],
        page_file: str | None = None,
    ) -> bool:
        merged_config = config.copy()

        if "theme" in self.attributes:
            merged_config["theme"] = self.attributes["theme"]

        result = image_generator.generate(
            self.code, output_path, merged_config, page_file
        )
        return bool(result)

    def get_image_markdown(
        self,
        image_path: str,
        page_file: str,
        page_url: str = "",
    ) -> str:
        image_path_obj = Path(image_path)

        # 相対パスプレフィックスを計算
        relative_prefix = _calculate_relative_path_prefix(page_file)

        # 相対パス付きで画像パスを構築
        relative_image_path = f"{relative_prefix}assets/images/{image_path_obj.name}"

        image_markdown = f"![Mermaid Diagram]({relative_image_path})"

        return image_markdown

    def get_filename(self, page_file: str, index: int, image_format: str) -> str:
        return generate_image_filename(page_file, index, self.code, image_format)
