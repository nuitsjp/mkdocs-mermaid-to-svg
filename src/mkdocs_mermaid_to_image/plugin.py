import os
import shutil
import sys
from pathlib import Path
from typing import Any, Optional

from mkdocs.config import config_options
from mkdocs.plugins import BasePlugin

from .config import ConfigManager, MermaidPluginConfig
from .exceptions import MermaidConfigError, MermaidPreprocessorError
from .processor import MermaidProcessor
from .utils import ensure_directory, setup_logger


class MermaidToImagePlugin(BasePlugin[MermaidPluginConfig]):  # type: ignore[no-untyped-call]
    config_scheme = (
        ("enabled", config_options.Type(bool, default=True)),
        ("enabled_if_env", config_options.Optional(config_options.Type(str))),
        ("output_dir", config_options.Type(str, default="assets/images")),
        ("image_format", config_options.Choice(["png", "svg"], default="png")),
        ("mermaid_config", config_options.Optional(config_options.Type(str))),
        ("mmdc_path", config_options.Type(str, default="mmdc")),
        (
            "theme",
            config_options.Choice(
                ["default", "dark", "forest", "neutral"], default="default"
            ),
        ),
        ("background_color", config_options.Type(str, default="white")),
        ("width", config_options.Type(int, default=800)),
        ("height", config_options.Type(int, default=600)),
        ("scale", config_options.Type(float, default=1.0)),
        ("css_file", config_options.Optional(config_options.Type(str))),
        ("puppeteer_config", config_options.Optional(config_options.Type(str))),
        ("temp_dir", config_options.Optional(config_options.Type(str))),
        ("cache_enabled", config_options.Type(bool, default=True)),
        ("cache_dir", config_options.Type(str, default=".mermaid_cache")),
        ("preserve_original", config_options.Type(bool, default=False)),
        ("error_on_fail", config_options.Type(bool, default=False)),
        (
            "log_level",
            config_options.Choice(
                ["DEBUG", "INFO", "WARNING", "ERROR"], default="INFO"
            ),
        ),
    )

    def __init__(self) -> None:
        super().__init__()
        self.processor: Optional[MermaidProcessor] = None
        self.logger: Optional[Any] = None
        self.generated_images: list[str] = []

        self.is_serve_mode: bool = "serve" in sys.argv

    def _should_be_enabled(self, config: MermaidPluginConfig) -> bool:
        """環境変数設定に基づいてプラグインが有効化されるべきかどうかを判定"""
        enabled_if_env = config.get("enabled_if_env")

        if enabled_if_env is not None:
            # enabled_if_envが設定されている場合、環境変数の存在と値をチェック
            env_value = os.environ.get(enabled_if_env)
            return env_value is not None and env_value.strip() != ""

        # enabled_if_envが設定されていない場合は通常のenabled設定に従う
        return config.get("enabled", True)

    def on_config(self, config: Any) -> Any:
        try:
            config_dict = dict(self.config)
            ConfigManager.validate_config(config_dict)

            self.logger = setup_logger(__name__, self.config["log_level"])

            if not self._should_be_enabled(self.config):
                self.logger.info("Mermaid preprocessor plugin is disabled")
                return config

            self.processor = MermaidProcessor(config_dict)

            output_dir = Path(config["site_dir"]) / self.config["output_dir"]
            ensure_directory(output_dir)

            self.logger.info("Mermaid preprocessor plugin initialized successfully")

        except Exception as e:
            raise MermaidConfigError(f"Plugin configuration error: {e!s}") from e

        return config

    def on_files(self, files: Any, *, config: Any) -> Any:
        if not self._should_be_enabled(self.config) or not self.processor:
            return files

        self.generated_images = []

        return files

    def on_page_markdown(
        self, markdown: str, *, page: Any, config: Any, files: Any
    ) -> Optional[str]:
        if not self._should_be_enabled(self.config) or not self.processor:
            return markdown

        if self.is_serve_mode:
            if self.logger:
                self.logger.debug(
                    f"Skipping Mermaid image generation in serve mode for "
                    f"{page.file.src_path}"
                )
            return markdown

        try:
            output_dir = Path(config["site_dir"]) / self.config["output_dir"]

            modified_content, image_paths = self.processor.process_page(
                page.file.src_path,
                markdown,
                output_dir,
                page_url=page.url,
            )

            self.generated_images.extend(image_paths)

            if image_paths and self.logger:
                self.logger.info(
                    f"Processed {len(image_paths)} Mermaid diagrams in "
                    f"{page.file.src_path}"
                )

            return modified_content

        except MermaidPreprocessorError as e:
            if self.logger:
                self.logger.error(f"Error processing {page.file.src_path}: {e!s}")
            if self.config["error_on_fail"]:
                raise
            return markdown

        except Exception as e:
            if self.logger:
                self.logger.error(
                    f"Unexpected error processing {page.file.src_path}: {e!s}"
                )
            if self.config["error_on_fail"]:
                raise MermaidPreprocessorError(f"Unexpected error: {e!s}") from e
            return markdown

    def on_post_build(self, *, config: Any) -> None:
        if not self._should_be_enabled(self.config):
            return

        if self.generated_images and self.logger:
            self.logger.info(
                f"Generated {len(self.generated_images)} Mermaid images total"
            )

        if not self.config["cache_enabled"]:
            cache_dir = self.config["cache_dir"]
            if Path(cache_dir).exists():
                shutil.rmtree(cache_dir)
                if self.logger:
                    self.logger.debug(f"Cleaned up cache directory: {cache_dir}")

    def on_serve(self, server: Any, *, config: Any, builder: Any) -> Any:
        if not self._should_be_enabled(self.config):
            return server

        if self.config["cache_enabled"]:
            cache_dir = self.config["cache_dir"]
            if Path(cache_dir).exists():
                server.watch(cache_dir)

        return server
