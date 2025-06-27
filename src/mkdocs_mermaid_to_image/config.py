from pathlib import Path
from typing import Any

from mkdocs.config import config_options
from mkdocs.config.base import Config


class ConfigManager:
    @staticmethod
    def get_config_scheme() -> tuple[tuple[str, Any], ...]:
        return (
            (
                "enabled",
                config_options.Type(bool, default=True),
            ),
            (
                "output_dir",
                config_options.Type(str, default="assets/images"),
            ),
            (
                "image_format",
                config_options.Choice(["png", "svg"], default="png"),
            ),
            (
                "mermaid_config",
                config_options.Type(str, default=None),
            ),
            (
                "mmdc_path",
                config_options.Type(str, default="mmdc"),
            ),
            (
                "theme",
                config_options.Choice(
                    ["default", "dark", "forest", "neutral"], default="default"
                ),
            ),
            ("background_color", config_options.Type(str, default="white")),
            ("width", config_options.Type(int, default=800)),
            ("height", config_options.Type(int, default=600)),
            (
                "scale",
                config_options.Type(float, default=1.0),
            ),
            (
                "css_file",
                config_options.Type(str, default=None),
            ),
            (
                "puppeteer_config",
                config_options.Type(str, default=None),
            ),
            (
                "temp_dir",
                config_options.Type(str, default=None),
            ),
            (
                "cache_enabled",
                config_options.Type(bool, default=True),
            ),
            (
                "cache_dir",
                config_options.Type(str, default=".mermaid_cache"),
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
        )

    @staticmethod
    def validate_config(config: dict[str, Any]) -> bool:
        if config["width"] <= 0 or config["height"] <= 0:
            raise ValueError("Width and height must be positive integers")

        if config["scale"] <= 0:
            raise ValueError("Scale must be a positive number")

        if config["css_file"] and not Path(config["css_file"]).exists():
            raise FileNotFoundError(f"CSS file not found: {config['css_file']}")

        if config["puppeteer_config"] and not Path(config["puppeteer_config"]).exists():
            raise FileNotFoundError(
                f"Puppeteer config file not found: {config['puppeteer_config']}"
            )

        return True


class MermaidPluginConfig(Config):  # type: ignore[no-untyped-call]
    enabled = config_options.Type(bool, default=True)
    output_dir = config_options.Type(str, default="assets/images")
    image_format = config_options.Choice(["png", "svg"], default="png")
    mermaid_config = config_options.Optional(config_options.Type(str))
    mmdc_path = config_options.Type(str, default="mmdc")
    theme = config_options.Choice(
        ["default", "dark", "forest", "neutral"], default="default"
    )
    background_color = config_options.Type(str, default="white")
    width = config_options.Type(int, default=800)
    height = config_options.Type(int, default=600)
    scale = config_options.Type(float, default=1.0)
    css_file = config_options.Optional(config_options.Type(str))
    puppeteer_config = config_options.Optional(config_options.Type(str))
    temp_dir = config_options.Optional(config_options.Type(str))
    cache_enabled = config_options.Type(bool, default=True)
    cache_dir = config_options.Type(str, default=".mermaid_cache")
    preserve_original = config_options.Type(bool, default=False)
    error_on_fail = config_options.Type(bool, default=False)
    log_level = config_options.Choice(
        ["DEBUG", "INFO", "WARNING", "ERROR"], default="INFO"
    )
