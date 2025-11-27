from pathlib import Path
from typing import Any

from mkdocs.config import config_options

from .exceptions import MermaidConfigError, MermaidFileError


class ConfigManager:
    """MkDocsプラグイン設定の定義と検証を担う"""

    @staticmethod
    def get_config_scheme() -> tuple[tuple[str, Any], ...]:
        """MkDocsに渡す設定スキーマを定義する"""
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
                "image_id_enabled",
                config_options.Type(bool, default=False),
            ),
            (
                "image_id_prefix",
                config_options.Type(str, default="mermaid-diagram"),
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
                "error_on_fail",
                config_options.Type(bool, default=True),
            ),
            (
                "log_level",
                config_options.Choice(
                    ["DEBUG", "INFO", "WARNING", "ERROR"], default="INFO"
                ),
            ),
            (
                "cleanup_generated_images",
                config_options.Type(bool, default=True),
            ),
            (
                "mmdc_path",
                config_options.Type(str, default="mmdc"),
            ),
            (
                "cli_timeout",
                config_options.Type(int, default=90),
            ),
        )

    @staticmethod
    def validate_config(config: dict[str, Any]) -> bool:
        """設定ファイルで指定されたパス類を検証し存在しない場合は例外を投げる"""
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

        cli_timeout = config.get("cli_timeout")
        if cli_timeout is not None and cli_timeout <= 0:
            raise MermaidConfigError(
                "cli_timeout must be a positive number of seconds",
                config_key="cli_timeout",
                config_value=cli_timeout,
                suggestion="Set cli_timeout to a positive integer such as 60",
            )

        return True
