import json
import os
import platform
import subprocess  # nosec B404
import tempfile
from pathlib import Path
from typing import Any, ClassVar

from .exceptions import MermaidCLIError, MermaidFileError, MermaidImageError
from .logging_config import get_logger
from .utils import (
    clean_temp_file,
    ensure_directory,
    get_temp_file_path,
    is_command_available,
)


class MermaidImageGenerator:
    # Class-level command cache for performance optimization
    _command_cache: ClassVar[dict[str, str]] = {}

    def __init__(self, config: dict[str, Any]) -> None:
        self.config = config
        self.logger = get_logger(__name__)
        self._resolved_mmdc_command: str | None = None
        self._validate_dependencies()

    @classmethod
    def clear_command_cache(cls) -> None:
        """Clear the command cache (useful for testing)."""
        cls._command_cache.clear()

    @classmethod
    def get_cache_size(cls) -> int:
        """Get the current cache size."""
        return len(cls._command_cache)

    def _validate_dependencies(self) -> None:
        """Validate and resolve the mmdc command with fallback support."""
        primary_command = self.config.get("mmdc_path", "mmdc")

        # Check cache first
        if primary_command in self._command_cache:
            self._resolved_mmdc_command = self._command_cache[primary_command]
            self.logger.debug(
                f"Using cached mmdc command: {self._resolved_mmdc_command} "
                f"(cache size: {len(self._command_cache)})"
            )
            return

        # Try primary command first
        if is_command_available(primary_command):
            self._resolved_mmdc_command = primary_command
            self._command_cache[primary_command] = primary_command
            self.logger.debug(
                f"Using primary mmdc command: {primary_command} (cached for future use)"
            )
            return

        # Determine fallback command
        if primary_command == "mmdc":
            fallback_command = "npx mmdc"
        elif primary_command == "npx mmdc":
            fallback_command = "mmdc"
        else:
            # Custom command, try npx variant
            fallback_command = f"npx {primary_command}"

        # Try fallback command
        if is_command_available(fallback_command):
            self._resolved_mmdc_command = fallback_command
            self._command_cache[primary_command] = fallback_command
            self.logger.info(
                f"Primary command '{primary_command}' not found, "
                f"using fallback: {fallback_command} (cached for future use)"
            )
            return

        # Both failed
        raise MermaidCLIError(
            f"Mermaid CLI not found. Tried '{primary_command}' and "
            f"'{fallback_command}'. Please install it with: "
            f"npm install @mermaid-js/mermaid-cli"
        )

    def generate(
        self,
        mermaid_code: str,
        output_path: str,
        config: dict[str, Any],
        page_file: str | None = None,
    ) -> bool:
        temp_file = None
        puppeteer_config_file = None
        mermaid_config_file = None

        try:
            temp_file = get_temp_file_path(".mmd")

            with Path(temp_file).open("w", encoding="utf-8") as f:
                f.write(mermaid_code)

            ensure_directory(str(Path(output_path).parent))

            cmd, puppeteer_config_file, mermaid_config_file = self._build_mmdc_command(
                temp_file, output_path, config
            )

            result = self._execute_mermaid_command(cmd)

            if result.returncode != 0:
                return self._handle_command_failure(result, cmd)

            if not Path(output_path).exists():
                return self._handle_missing_output(output_path, mermaid_code)

            # MkDocsの標準フォーマットでログ出力
            import logging

            mkdocs_logger = logging.getLogger("mkdocs")
            relative_path = Path(output_path).name
            source_info = f" from {page_file}" if page_file else ""
            mkdocs_logger.info(
                f"Converting Mermaid diagram to SVG: {relative_path}{source_info}"
            )
            return True

        except (MermaidCLIError, MermaidImageError):
            # カスタム例外はそのまま再発生
            raise
        except subprocess.TimeoutExpired:
            return self._handle_timeout_error(cmd)
        except (FileNotFoundError, OSError, PermissionError) as e:
            return self._handle_file_error(e, output_path)
        except Exception as e:
            return self._handle_unexpected_error(e, output_path, mermaid_code)
        finally:
            # テンポラリファイルのクリーンアップ - エラーが発生しても継続
            cleanup_files = [
                ("temp_file", temp_file),
                ("puppeteer_config_file", puppeteer_config_file),
                ("mermaid_config_file", mermaid_config_file),
            ]

            for file_type, file_path in cleanup_files:
                if file_path:
                    try:
                        clean_temp_file(file_path)
                    except Exception as e:
                        self.logger.warning(
                            f"Failed to clean up {file_type} '{file_path}': {e}"
                        )

    def _handle_command_failure(
        self, result: subprocess.CompletedProcess[str], cmd: list[str]
    ) -> bool:
        """mmdcコマンド実行失敗時の処理"""
        error_msg = f"Mermaid CLI failed: {result.stderr}"
        self.logger.error(error_msg)
        self.logger.error(f"Failed command: {' '.join(cmd)}")
        self.logger.error(f"Return code: {result.returncode}")
        self.logger.error(f"Stdout: {result.stdout}")
        self.logger.error(f"Stderr: {result.stderr}")
        if self.config["error_on_fail"]:
            raise MermaidCLIError(
                error_msg,
                command=" ".join(cmd),
                return_code=result.returncode,
                stderr=result.stderr,
            )
        return False

    def _handle_missing_output(self, output_path: str, mermaid_code: str) -> bool:
        """出力ファイルが生成されなかった場合の処理"""
        error_msg = f"Image not created: {output_path}"
        self.logger.error(error_msg)
        if self.config["error_on_fail"]:
            raise MermaidImageError(
                error_msg,
                image_format="svg",
                image_path=output_path,
                mermaid_content=mermaid_code,
                suggestion="Check Mermaid syntax and CLI configuration",
            ) from None
        return False

    def _handle_timeout_error(self, cmd: list[str]) -> bool:
        """タイムアウト時の処理"""
        error_msg = "Mermaid CLI execution timed out"
        self.logger.error(error_msg)
        if self.config["error_on_fail"]:
            raise MermaidCLIError(
                error_msg,
                command=" ".join(cmd),
                stderr="Process timed out after 30 seconds",
            ) from None
        return False

    def _handle_file_error(self, e: Exception, output_path: str) -> bool:
        """ファイルシステムエラー時の処理"""
        error_msg = f"File system error during image generation: {e!s}"
        self.logger.error(error_msg)
        if self.config["error_on_fail"]:
            raise MermaidFileError(
                error_msg,
                file_path=output_path,
                operation="write",
                suggestion="Check file permissions and ensure output directory exists",
            ) from e
        return False

    def _handle_unexpected_error(
        self, e: Exception, output_path: str, mermaid_code: str
    ) -> bool:
        """予期しないエラー時の処理"""
        error_msg = f"Unexpected error generating image: {e!s}"
        self.logger.error(error_msg)
        if self.config["error_on_fail"]:
            raise MermaidImageError(
                error_msg,
                image_format="svg",
                image_path=output_path,
                mermaid_content=mermaid_code,
                suggestion="Check Mermaid diagram syntax and CLI configuration",
            ) from e
        return False

    def _create_mermaid_config_file(self) -> str | None:
        """Create a temporary Mermaid configuration file for PDF compatibility.

        Returns the path to the config file, or None if no config needed.
        """
        mermaid_config = self.config.get("mermaid_config")

        # If mermaid_config is a string (file path), use it directly
        if isinstance(mermaid_config, str):
            return mermaid_config

        # If mermaid_config is a dict, create a temporary file
        if isinstance(mermaid_config, dict):
            config_to_write = mermaid_config
        else:
            # Provide default PDF-compatible configuration
            config_to_write = {
                "htmlLabels": False,
                "flowchart": {"htmlLabels": False},
                "class": {"htmlLabels": False},
            }

        try:
            # Create temporary config file
            config_file = get_temp_file_path(".json")
            with Path(config_file).open("w", encoding="utf-8") as f:
                json.dump(config_to_write, f, indent=2)

            self.logger.debug(f"Created Mermaid config file: {config_file}")
            return config_file
        except Exception as e:
            self.logger.warning(f"Failed to create Mermaid config file: {e}")
            return None

    def _build_mmdc_command(
        self, input_file: str, output_file: str, config: dict[str, Any]
    ) -> tuple[list[str], str | None, str | None]:
        # Use the resolved command from initialization
        if not self._resolved_mmdc_command:
            raise MermaidCLIError("Mermaid CLI command not properly resolved")

        # Handle commands like "npx mmdc" by splitting them
        mmdc_command_parts = self._resolved_mmdc_command.split()

        cmd = [
            *mmdc_command_parts,
            "-i",
            input_file,
            "-o",
            output_file,
            "-e",
            "svg",
        ]

        # Add theme option only if it's not the default
        theme = config.get("theme", self.config["theme"])
        if theme != "default":
            cmd.extend(["-t", theme])

        # Add Mermaid configuration file for PDF compatibility
        mermaid_config_file = self._create_mermaid_config_file()
        if mermaid_config_file:
            cmd.extend(["-c", mermaid_config_file])

        # Add puppeteer config for proper browser handling
        puppeteer_config_file = None

        # Create puppeteer config for better browser compatibility
        puppeteer_config: dict[str, Any] = {
            "args": [
                "--no-sandbox",
                "--disable-setuid-sandbox",
                "--disable-dev-shm-usage",
                "--disable-web-security",
            ]
        }

        # Try to use system Chrome if available
        import shutil

        chrome_path = shutil.which("google-chrome") or shutil.which("chromium-browser")
        if chrome_path:
            puppeteer_config["executablePath"] = chrome_path

        # In CI environments, additional restrictions may be needed
        if os.getenv("CI") or os.getenv("GITHUB_ACTIONS"):
            puppeteer_config["args"].extend(["--single-process", "--no-zygote"])

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(puppeteer_config, f)
            puppeteer_config_file = f.name
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

        return cmd, puppeteer_config_file, mermaid_config_file

    def _execute_mermaid_command(
        self, cmd: list[str]
    ) -> subprocess.CompletedProcess[str]:
        """Execute mermaid command with appropriate shell settings for the platform."""
        # Log command details for debugging CLI issues
        self.logger.debug(f"Executing mermaid CLI command: {' '.join(cmd)}")
        self.logger.debug(f"Command parts: {cmd}")

        # On Windows, use shell=True to handle .ps1 scripts properly
        use_shell = platform.system() == "Windows"

        if use_shell:
            # On Windows, explicitly use cmd.exe to avoid issues with Git Bash
            cmd_str = " ".join(cmd)
            full_cmd = ["cmd", "/c", cmd_str]
            self.logger.debug(f"Windows execution via cmd.exe: {full_cmd}")
            self.logger.debug(f"Joined command string: '{cmd_str}'")
            # Use cmd.exe explicitly to handle npm/node commands properly
            # Input is controlled internally, not from external user input
            return subprocess.run(  # nosec B603,B602,B607
                full_cmd,
                capture_output=True,
                text=True,
                timeout=30,
                check=False,
                shell=False,  # nosec B603
            )
        else:
            # For shell=False, command should be a list
            return subprocess.run(  # nosec B603
                cmd,
                capture_output=True,
                text=True,
                timeout=30,
                check=False,
                shell=False,  # nosec B603
            )
