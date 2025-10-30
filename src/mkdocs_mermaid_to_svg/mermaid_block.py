import os
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
    depth = len(page_path.parent.parts)

    if depth == 0:
        return ""
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
        *,
        output_dir: str | None = None,
        docs_dir: str | Path | None = None,
    ) -> str:
        relative_prefix = _calculate_relative_path_prefix(page_file)

        relative_path = self._compute_relative_path(
            image_path=image_path,
            page_file=page_file,
            output_dir=output_dir,
            docs_dir=docs_dir,
        )

        if relative_prefix:
            image_path_for_markdown = f"{relative_prefix}{relative_path}"
        else:
            image_path_for_markdown = relative_path

        return f"![Mermaid Diagram]({image_path_for_markdown})"

    def _compute_relative_path(
        self,
        *,
        image_path: str,
        page_file: str,
        output_dir: str | None,
        docs_dir: str | Path | None,
    ) -> str:
        image_path_obj = Path(image_path)
        docs_dir_path = Path(docs_dir).resolve() if docs_dir else None

        if docs_dir_path:
            try:
                rel_to_docs = os.path.relpath(
                    image_path_obj.resolve(strict=False), docs_dir_path
                )
                rel_to_docs = rel_to_docs.replace("\\", "/")
                if rel_to_docs.startswith("./"):
                    rel_to_docs = rel_to_docs[2:]
                return rel_to_docs
            except ValueError:
                pass

        normalized_output_dir = self._normalize_output_dir(output_dir)

        if normalized_output_dir:
            return f"{normalized_output_dir}/{image_path_obj.name}".replace("//", "/")

        return image_path_obj.name

    @staticmethod
    def _normalize_output_dir(output_dir: str | None) -> str:
        default_dir = "assets/images"

        if not output_dir:
            return default_dir

        normalized = Path(output_dir).as_posix().strip("/")

        if normalized in {"", "."}:
            return ""

        return normalized

    def get_filename(self, page_file: str, index: int, image_format: str) -> str:
        return generate_image_filename(page_file, index, self.code, image_format)
