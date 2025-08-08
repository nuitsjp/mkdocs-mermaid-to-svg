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
        temp_files = self._TempFileManager()

        try:
            temp_files.temp_file = get_temp_file_path(".mmd")

            with Path(temp_files.temp_file).open("w", encoding="utf-8") as f:
                f.write(mermaid_code)

            ensure_directory(str(Path(output_path).parent))

            cmd, temp_files.puppeteer_config_file, temp_files.mermaid_config_file = (
                self._build_mmdc_command(temp_files.temp_file, output_path, config)
            )

            result = self._execute_mermaid_command(cmd)

            if not self._validate_generation_result(result, output_path, mermaid_code):
                return False

            self._log_successful_generation(output_path, page_file)
            return True

        except (MermaidCLIError, MermaidImageError):
            raise
        except subprocess.TimeoutExpired:
            return self._handle_timeout_error(cmd)
        except (FileNotFoundError, OSError, PermissionError) as e:
            return self._handle_file_error(e, output_path)
        except Exception as e:
            return self._handle_unexpected_error(e, output_path, mermaid_code)
        finally:
            temp_files.cleanup_all(self.logger)

    class _TempFileManager:
        """一時ファイル管理のヘルパークラス"""

        def __init__(self) -> None:
            self.temp_file: str | None = None
            self.puppeteer_config_file: str | None = None
            self.mermaid_config_file: str | None = None

        def cleanup_all(self, logger: Any) -> None:
            """全ての一時ファイルをクリーンアップ"""
            cleanup_files = [
                ("temp_file", self.temp_file),
                ("puppeteer_config_file", self.puppeteer_config_file),
                ("mermaid_config_file", self.mermaid_config_file),
            ]

            for file_type, file_path in cleanup_files:
                if file_path:
                    try:
                        clean_temp_file(file_path)
                    except Exception as e:
                        logger.warning(
                            f"Failed to clean up {file_type} '{file_path}': {e}"
                        )

    def _validate_generation_result(
        self,
        result: subprocess.CompletedProcess[str],
        output_path: str,
        mermaid_code: str,
    ) -> bool:
        """画像生成結果を検証"""
        if result.returncode != 0:
            return self._handle_command_failure(result, [])

        if not Path(output_path).exists():
            return self._handle_missing_output(output_path, mermaid_code)

        return True

    def _log_successful_generation(
        self, output_path: str, page_file: str | None
    ) -> None:
        """成功時のログ出力"""
        import logging

        mkdocs_logger = logging.getLogger("mkdocs")
        relative_path = Path(output_path).name
        source_info = f" from {page_file}" if page_file else ""
        mkdocs_logger.info(
            f"Converting Mermaid diagram to SVG: {relative_path}{source_info}"
        )

    def _handle_command_failure(
        self, result: subprocess.CompletedProcess[str], cmd: list[str]
    ) -> bool:
        """mmdcコマンド実行失敗時の処理"""
        error_msg = f"Mermaid CLI failed: {result.stderr}"
        self.logger.error(error_msg)
        self.logger.error(f"Return code: {result.returncode}")

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
            )
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
            )
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
        """Create a temporary Mermaid configuration file for PDF compatibility."""
        mermaid_config = self.config.get("mermaid_config")

        if isinstance(mermaid_config, str):
            return mermaid_config

        config_to_write = (
            mermaid_config
            if isinstance(mermaid_config, dict)
            else {
                "htmlLabels": False,
                "flowchart": {"htmlLabels": False},
                "class": {"htmlLabels": False},
            }
        )

        try:
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
        if not self._resolved_mmdc_command:
            raise MermaidCLIError("Mermaid CLI command not properly resolved")

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

        theme = config.get("theme", self.config["theme"])
        if theme != "default":
            cmd.extend(["-t", theme])

        mermaid_config_file = self._create_mermaid_config_file()
        if mermaid_config_file:
            cmd.extend(["-c", mermaid_config_file])

        puppeteer_config_file = self._create_puppeteer_config()
        cmd.extend(["-p", puppeteer_config_file])

        if self.config.get("css_file"):
            cmd.extend(["-C", self.config["css_file"]])

        custom_puppeteer_config = self.config.get("puppeteer_config")
        if custom_puppeteer_config and Path(custom_puppeteer_config).exists():
            cmd.extend(["-p", custom_puppeteer_config])
        elif custom_puppeteer_config:
            self.logger.warning(
                f"Puppeteer config file not found: {custom_puppeteer_config}"
            )

        return cmd, puppeteer_config_file, mermaid_config_file

    def _create_puppeteer_config(self) -> str:
        """Create puppeteer config for better browser compatibility."""
        import shutil

        puppeteer_config: dict[str, Any] = {
            "args": [
                "--no-sandbox",
                "--disable-setuid-sandbox",
                "--disable-dev-shm-usage",
                "--disable-web-security",
            ]
        }

        chrome_path = shutil.which("google-chrome") or shutil.which("chromium-browser")
        if chrome_path:
            puppeteer_config["executablePath"] = chrome_path

        if os.getenv("CI") or os.getenv("GITHUB_ACTIONS"):
            puppeteer_config["args"].extend(["--single-process", "--no-zygote"])

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(puppeteer_config, f)
            return f.name

    def _execute_mermaid_command(
        self, cmd: list[str]
    ) -> subprocess.CompletedProcess[str]:
        """Execute mermaid command with appropriate shell settings for the platform."""
        self.logger.debug(f"Executing mermaid CLI command: {' '.join(cmd)}")

        use_shell = platform.system() == "Windows"

        if use_shell:
            cmd_str = " ".join(cmd)
            full_cmd = ["cmd", "/c", cmd_str]
            return subprocess.run(  # nosec B603,B602,B607
                full_cmd,
                capture_output=True,
                text=True,
                timeout=30,
                check=False,
                shell=False,  # nosec B603
            )
        else:
            return subprocess.run(  # nosec B603
                cmd,
                capture_output=True,
                text=True,
                timeout=30,
                check=False,
                shell=False,
            )
