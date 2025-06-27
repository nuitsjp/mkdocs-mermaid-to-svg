import contextlib
from pathlib import Path
from typing import Any, Optional

from .utils import generate_image_filename


class MermaidBlock:
    def __init__(
        self,
        code: str,
        start_pos: int,
        end_pos: int,
        attributes: Optional[dict[str, Any]] = None,
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
        self, output_path: str, image_generator: Any, config: dict[str, Any]
    ) -> bool:
        merged_config = config.copy()

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
        self,
        image_path: str,
        page_file: str,
        preserve_original: bool = False,
        page_url: str = "",
    ) -> str:
        image_path_obj = Path(image_path)

        # Use image filename for the assets/images path
        image_site_path = f"assets/images/{image_path_obj.name}"

        # Calculate depth based on page URL, not file path
        if page_url:
            # Remove leading/trailing slashes and count directory levels
            url_parts = page_url.strip("/").split("/")
            # Remove index.html or similar if present, count actual directory depth
            if url_parts == [""] or (len(url_parts) == 1 and url_parts[0] == ""):
                page_depth = 0  # Root page
            else:
                # Count directory levels (exclude page filename if present)
                page_depth = len(
                    [part for part in url_parts if part and not part.endswith(".html")]
                )
        else:
            # Fallback to old method if page_url is not provided
            page_path = Path(page_file)
            page_depth = (
                len(page_path.parent.parts) if page_path.parent != Path() else 0
            )

        if page_depth > 0:
            relative_image_path = "../" * page_depth + image_site_path
        else:
            relative_image_path = image_site_path

        image_markdown = f"![Mermaid Diagram]({relative_image_path})"

        if preserve_original:
            if self.attributes:
                attr_str = ", ".join(f"{k}: {v}" for k, v in self.attributes.items())
                original_block = f"```mermaid {{{attr_str}}}\n{self.code}\n```"
            else:
                original_block = f"```mermaid\n{self.code}\n```"

            image_markdown = f"{image_markdown}\n\n{original_block}"

        return image_markdown

    def get_filename(self, page_file: str, index: int, image_format: str) -> str:
        return generate_image_filename(page_file, index, self.code, image_format)
