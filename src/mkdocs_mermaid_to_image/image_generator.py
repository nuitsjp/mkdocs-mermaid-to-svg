import subprocess  # nosec B404
from pathlib import Path
from typing import Any

from .exceptions import MermaidCLIError
from .utils import (
    clean_temp_file,
    ensure_directory,
    get_temp_file_path,
    is_command_available,
    setup_logger,
)


class MermaidImageGenerator:
    def __init__(self, config: dict[str, Any]) -> None:
        self.config = config
        self.logger = setup_logger(__name__, config.get("log_level", "INFO"))
        self._validate_dependencies()

    def _validate_dependencies(self) -> None:
        if not is_command_available(self.config["mmdc_path"]):
            raise MermaidCLIError(
                f"Mermaid CLI not found at '{self.config['mmdc_path']}'. "
                f"Please install it with: npm install -g @mermaid-js/mermaid-cli"
            )

    def generate(
        self, mermaid_code: str, output_path: str, config: dict[str, Any]
    ) -> bool:
        temp_file = None

        try:
            temp_file = get_temp_file_path(".mmd")

            with Path(temp_file).open("w", encoding="utf-8") as f:
                f.write(mermaid_code)

            ensure_directory(str(Path(output_path).parent))

            cmd = self._build_mmdc_command(temp_file, output_path, config)

            self.logger.debug(f"Executing: {' '.join(cmd)}")

            result = subprocess.run(  # nosec B603
                cmd, capture_output=True, text=True, timeout=30, check=False
            )

            if result.returncode != 0:
                error_msg = f"Mermaid CLI failed: {result.stderr}"
                self.logger.error(error_msg)
                if self.config["error_on_fail"]:
                    raise MermaidCLIError(error_msg)
                return False

            if not Path(output_path).exists():
                error_msg = f"Image not created: {output_path}"
                self.logger.error(error_msg)
                if self.config["error_on_fail"]:
                    raise MermaidCLIError(error_msg) from None
                return False

            self.logger.info(f"Generated image: {output_path}")
            return True

        except subprocess.TimeoutExpired:
            error_msg = "Mermaid CLI execution timed out"
            self.logger.error(error_msg)
            if self.config["error_on_fail"]:
                raise MermaidCLIError(error_msg) from None
            return False

        except Exception as e:
            error_msg = f"Error generating image: {e!s}"
            self.logger.error(error_msg)
            if self.config["error_on_fail"]:
                raise MermaidCLIError(error_msg) from e
            return False

        finally:
            if temp_file:
                clean_temp_file(temp_file)

    def _build_mmdc_command(
        self, input_file: str, output_file: str, config: dict[str, Any]
    ) -> list[str]:
        cmd = [
            self.config["mmdc_path"],
            "-i",
            input_file,
            "-o",
            output_file,
            "-t",
            config.get("theme", self.config["theme"]),
            "-b",
            config.get("background_color", self.config["background_color"]),
            "-w",
            str(config.get("width", self.config["width"])),
            "-H",
            str(config.get("height", self.config["height"])),
            "-s",
            str(config.get("scale", self.config["scale"])),
        ]

        # Add --no-sandbox for CI environments via puppeteer config
        import json
        import os
        import tempfile

        if os.getenv("CI") or os.getenv("GITHUB_ACTIONS"):
            # Create temporary puppeteer config with --no-sandbox
            puppeteer_config = {"args": ["--no-sandbox"]}
            with tempfile.NamedTemporaryFile(
                mode="w", suffix=".json", delete=False
            ) as f:
                json.dump(puppeteer_config, f)
                cmd.extend(["-p", f.name])

        if self.config.get("css_file"):
            cmd.extend(["-C", self.config["css_file"]])

        if self.config.get("puppeteer_config"):
            puppeteer_config_path = Path(self.config["puppeteer_config"])
            if puppeteer_config_path.exists():
                cmd.extend(["-p", self.config["puppeteer_config"]])
            else:
                self.logger.warning(
                    f"Puppeteer config file not found: "
                    f"{self.config['puppeteer_config']}"
                )

        if self.config.get("mermaid_config"):
            cmd.extend(["-c", self.config["mermaid_config"]])

        return cmd
