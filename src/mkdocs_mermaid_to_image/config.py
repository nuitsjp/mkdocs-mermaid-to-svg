from pathlib import Path
from typing import Any

from mkdocs.config import config_options


class ConfigManager:
    @staticmethod
    def get_config_scheme() -> tuple[tuple[str, Any], ...]:
        return (
            (
                "enabled",
                config_options.Type(bool, default=True),
            ),
            (
                "enabled_if_env",
                config_options.Optional(config_options.Type(str)),
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
                config_options.Optional(config_options.Type(str)),
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
                config_options.Optional(config_options.Type(str)),
            ),
            (
                "puppeteer_config",
                config_options.Optional(config_options.Type(str)),
            ),
            (
                "temp_dir",
                config_options.Optional(config_options.Type(str)),
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
            (
                "cleanup_generated_images",
                config_options.Type(bool, default=False),
            ),
        )

    @staticmethod
    def validate_config(config: dict[str, Any]) -> bool:
        # 必須パラメータの存在チェック
        required_keys = ["width", "height", "scale"]
        for key in required_keys:
            if key not in config:
                raise ValueError(f"Required configuration key '{key}' is missing")

        if config["width"] <= 0 or config["height"] <= 0:
            raise ValueError("Width and height must be positive integers")

        if config["scale"] <= 0:
            raise ValueError("Scale must be a positive number")

        # オプションパラメータのチェック（存在する場合のみ）
        if (
            "css_file" in config
            and config["css_file"]
            and not Path(config["css_file"]).exists()
        ):
            raise FileNotFoundError(f"CSS file not found: {config['css_file']}")

        if (
            "puppeteer_config" in config
            and config["puppeteer_config"]
            and not Path(config["puppeteer_config"]).exists()
        ):
            raise FileNotFoundError(
                f"Puppeteer config file not found: {config['puppeteer_config']}"
            )

        return True
