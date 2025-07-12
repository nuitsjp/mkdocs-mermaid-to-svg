from pathlib import Path
from typing import Any

from mkdocs.config import config_options

from .exceptions import MermaidFileError


class ConfigManager:
    @staticmethod
    def get_config_scheme() -> tuple[tuple[str, Any], ...]:
        return (
            (
                "enabled_if_env",
                config_options.Optional(config_options.Type(str)),
            ),
            (
                "output_dir",
                config_options.Type(str, default="assets/images"),
            ),
            (
                "mermaid_config",
                config_options.Optional(config_options.Type(dict)),
            ),
            (
                "theme",
                config_options.Choice(
                    ["default", "dark", "forest", "neutral"], default="default"
                ),
            ),
            (
                "css_file",
                config_options.Optional(config_options.Type(str)),
            ),
            (
                "puppeteer_config",
                config_options.Optional(config_options.Type(str)),
            ),
            (
                "preserve_original",
                config_options.Type(bool, default=False),
            ),
            (
                "error_on_fail",
                config_options.Type(bool, default=False),
            ),
            (
                "log_level",
                config_options.Choice(
                    ["DEBUG", "INFO", "WARNING", "ERROR"], default="INFO"
                ),
            ),
            (
                "cleanup_generated_images",
                config_options.Type(bool, default=False),
            ),
            (
                "mmdc_path",
                config_options.Type(str, default="mmdc"),
            ),
        )

    @staticmethod
    def validate_config(config: dict[str, Any]) -> bool:
        # オプションパラメータのチェック（存在する場合のみ）
        if (
            "css_file" in config
            and config["css_file"]
            and not Path(config["css_file"]).exists()
        ):
            raise MermaidFileError(
                f"CSS file not found: {config['css_file']}",
                file_path=config["css_file"],
                operation="read",
                suggestion="Ensure the CSS file exists or remove the "
                "css_file configuration",
            )

        if (
            "puppeteer_config" in config
            and config["puppeteer_config"]
            and not Path(config["puppeteer_config"]).exists()
        ):
            raise MermaidFileError(
                f"Puppeteer config file not found: {config['puppeteer_config']}",
                file_path=config["puppeteer_config"],
                operation="read",
                suggestion="Ensure the Puppeteer config file exists or "
                "remove the puppeteer_config configuration",
            )

        return True
