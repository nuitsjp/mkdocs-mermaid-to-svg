import os
from pathlib import Path
from typing import Any

from .utils import generate_image_filename


def _calculate_relative_path_prefix(page_file: str) -> str:
    """ページファイルの深さに応じた相対パスの接頭辞を計算する"""
    if not page_file:
        return ""

    page_path = Path(page_file)
    depth = len(page_path.parent.parts)

    if depth == 0:
        return ""

    return "../" * depth


class ImagePathResolver:
    """生成された画像ファイルをMarkdownから参照しやすいパスに変換する"""

    def __init__(self, default_output_dir: str = "assets/images") -> None:
        self.default_output_dir = default_output_dir

    def to_markdown_path(
        self,
        *,
        image_path: str | Path,
        page_file: str,
        output_dir: str | None,
        docs_dir: str | Path | None,
    ) -> str:
        """ページ位置を考慮してMarkdown内で使用する相対パスを返す"""
        relative_prefix = _calculate_relative_path_prefix(page_file)
        relative_path = self._resolve_relative_path(
            image_path=image_path,
            output_dir=output_dir,
            docs_dir=docs_dir,
        )

        # ページ深度がある場合は適切なプレフィックスを付与
        if relative_prefix:
            return f"{relative_prefix}{relative_path}"
        return relative_path

    def _resolve_relative_path(
        self,
        *,
        image_path: str | Path,
        output_dir: str | None,
        docs_dir: str | Path | None,
    ) -> str:
        """docs_dirや出力設定を踏まえた相対パスを計算する"""
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
                if not rel_to_docs.startswith("../") and rel_to_docs != "..":
                    return rel_to_docs
            except ValueError:
                pass

        normalized_output_dir = self._normalize_output_dir(output_dir)

        if normalized_output_dir:
            return f"{normalized_output_dir}/{image_path_obj.name}".replace("//", "/")

        return image_path_obj.name

    def _normalize_output_dir(self, output_dir: str | None) -> str:
        """output_dir設定をスラッシュ区切りへ正規化する"""
        if not output_dir:
            return self.default_output_dir

        normalized = Path(output_dir).as_posix().strip("/")

        if normalized in {"", "."}:
            return ""

        return normalized


class MermaidBlock:
    """Markdown内のMermaidコードブロックを表し画像生成を仲介する"""

    _default_path_resolver = ImagePathResolver()

    def __init__(
        self,
        code: str,
        start_pos: int,
        end_pos: int,
        attributes: dict[str, Any] | None = None,
    ):
        """ブロックのコードと位置情報、任意属性を保持する"""
        self.code = code.strip()
        self.start_pos = start_pos
        self.end_pos = end_pos
        self.attributes = attributes or {}
        self._path_resolver = self._default_path_resolver

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
        """Mermaid CLI用の設定を整え画像生成処理を呼び出す"""
        merged_config = config.copy()

        # ブロックごとにテーマ指定があれば優先する
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
        """生成済み画像をMarkdownリンクとして利用できる形式に整形する"""
        markdown_path = self._path_resolver.to_markdown_path(
            image_path=image_path,
            page_file=page_file,
            output_dir=output_dir,
            docs_dir=docs_dir,
        )

        return f"![Mermaid Diagram]({markdown_path})"

    def get_filename(self, page_file: str, index: int, image_format: str) -> str:
        """ブロック内容に基づく安定したファイル名を生成する"""
        return generate_image_filename(page_file, index, self.code, image_format)
