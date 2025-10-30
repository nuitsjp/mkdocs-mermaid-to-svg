import json
import os
import platform
import subprocess  # nosec B404
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any, ClassVar

from .exceptions import MermaidCLIError, MermaidFileError, MermaidImageError
from .logging_config import get_logger
from .utils import (
    clean_temp_file,
    ensure_directory,
    get_temp_file_path,
    is_command_available,
    split_command,
)


@dataclass
class GenerationArtifacts:
    source_path: str
    puppeteer_config_file: str | None
    mermaid_config_file: str | None
    cleanup_entries: tuple[tuple[str, str], ...]

    def cleanup(self, logger: Any) -> None:
        for label, path in self.cleanup_entries:
            try:
                clean_temp_file(path)
            except Exception as exc:  # pragma: no cover - defensive logging
                logger.warning(f"Failed to clean up {label} '{path}': {exc}")


class MermaidCommandResolver:
    def __init__(
        self,
        config: dict[str, Any],
        logger: Any,
        command_cache: dict[str, tuple[str, ...]],
    ) -> None:
        self.config = config
        self.logger = logger
        self._command_cache = command_cache

    def resolve(self) -> list[str]:
        primary_command = self.config.get("mmdc_path", "mmdc")

        cached_command = self._command_cache.get(primary_command)
        if cached_command:
            self.logger.debug(
                "Using cached mmdc command: %s (cache size: %d)",
                " ".join(cached_command),
                len(self._command_cache),
            )
            return list(cached_command)

        primary_parts = self._attempt_resolve(primary_command)
        if primary_parts:
            self._command_cache[primary_command] = tuple(primary_parts)
            self.logger.debug(
                "Using primary mmdc command: %s (cached for future use)",
                " ".join(primary_parts),
            )
            return primary_parts

        fallback_command = self._determine_fallback(primary_command)
        fallback_parts = self._attempt_resolve(fallback_command)
        if fallback_parts:
            self._command_cache[primary_command] = tuple(fallback_parts)
            self.logger.info(
                "Primary command '%s' not found, using fallback: %s "
                "(cached for future use)",
                primary_command,
                " ".join(fallback_parts),
            )
            return fallback_parts

        raise MermaidCLIError(
            f"Mermaid CLI not found. Tried '{primary_command}' and "
            f"'{fallback_command}'. Please install it with: "
            f"npm install @mermaid-js/mermaid-cli"
        )

    def _attempt_resolve(self, command: str) -> list[str] | None:
        if not is_command_available(command):
            return None

        parts = split_command(command)
        if parts:
            return parts
        return None

    @staticmethod
    def _determine_fallback(primary_command: str) -> str:
        if primary_command == "mmdc":
            return "npx mmdc"
        if primary_command == "npx mmdc":
            return "mmdc"
        return f"npx {primary_command}"


class MermaidCLIExecutor:
    def __init__(self, logger: Any) -> None:
        self.logger = logger

    def run(self, cmd: list[str]) -> subprocess.CompletedProcess[str]:
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

        return subprocess.run(  # nosec B603
            cmd,
            capture_output=True,
            text=True,
            timeout=30,
            check=False,
            shell=False,
        )


class MermaidArtifactManager:
    def __init__(self, config: dict[str, Any], logger: Any) -> None:
        self.config = config
        self.logger = logger

    def prepare(
        self, mermaid_code: str, output_path: str, _runtime_config: dict[str, Any]
    ) -> GenerationArtifacts:
        cleanup_entries: list[tuple[str, str]] = []

        temp_file = get_temp_file_path(".mmd")
        with Path(temp_file).open("w", encoding="utf-8") as file_obj:
            file_obj.write(mermaid_code)
        cleanup_entries.append(("temp_file", temp_file))

        ensure_directory(str(Path(output_path).parent))

        mermaid_config_file, should_cleanup_mermaid = self._resolve_mermaid_config()
        if should_cleanup_mermaid and mermaid_config_file:
            cleanup_entries.append(("mermaid_config_file", mermaid_config_file))

        puppeteer_config_file, should_cleanup_puppeteer = (
            self._resolve_puppeteer_config()
        )
        if should_cleanup_puppeteer and puppeteer_config_file:
            cleanup_entries.append(("puppeteer_config_file", puppeteer_config_file))

        return GenerationArtifacts(
            source_path=temp_file,
            puppeteer_config_file=puppeteer_config_file,
            mermaid_config_file=mermaid_config_file,
            cleanup_entries=tuple(cleanup_entries),
        )

    def _resolve_mermaid_config(self) -> tuple[str | None, bool]:
        mermaid_config = self.config.get("mermaid_config")

        if isinstance(mermaid_config, str):
            return mermaid_config, False

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
            with Path(config_file).open("w", encoding="utf-8") as file_obj:
                json.dump(config_to_write, file_obj, indent=2)

            self.logger.debug(f"Created Mermaid config file: {config_file}")
            return config_file, True
        except Exception as exc:  # pragma: no cover - defensive logging
            self.logger.warning(f"Failed to create Mermaid config file: {exc}")
            return None, False

    def _resolve_puppeteer_config(self) -> tuple[str | None, bool]:
        custom_config = self.config.get("puppeteer_config")

        if custom_config and Path(custom_config).exists():
            return custom_config, False

        if custom_config:
            self.logger.warning(f"Puppeteer config file not found: {custom_config}")

        config_file = self._create_default_puppeteer_config()
        return config_file, True

    def _create_default_puppeteer_config(self) -> str:
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

        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".json", delete=False
        ) as file_obj:
            json.dump(puppeteer_config, file_obj)
            return file_obj.name


class MermaidImageGenerator:
    # Class-level command cache for performance optimization
    _command_cache: ClassVar[dict[str, tuple[str, ...]]] = {}

    def __init__(
        self,
        config: dict[str, Any],
        *,
        command_resolver: MermaidCommandResolver | None = None,
        artifact_manager: MermaidArtifactManager | None = None,
        cli_executor: MermaidCLIExecutor | None = None,
    ) -> None:
        self.config = config
        self.logger = get_logger(__name__)
        self.command_resolver = command_resolver or MermaidCommandResolver(
            config, self.logger, self._command_cache
        )
        self.artifact_manager = artifact_manager or MermaidArtifactManager(
            config, self.logger
        )
        self.cli_executor = cli_executor or MermaidCLIExecutor(self.logger)
        self._resolved_mmdc_command: list[str] | None = None
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
        """Resolve and cache the Mermaid CLI command."""
        self._resolved_mmdc_command = self.command_resolver.resolve()

    def generate(
        self,
        mermaid_code: str,
        output_path: str,
        config: dict[str, Any],
        page_file: str | None = None,
    ) -> bool:
        artifacts: GenerationArtifacts | None = None
        cmd: list[str] = []

        try:
            artifacts = self.artifact_manager.prepare(mermaid_code, output_path, config)
            cmd, _, _ = self._build_mmdc_command(
                artifacts.source_path,
                output_path,
                config,
                puppeteer_config_file=artifacts.puppeteer_config_file,
                mermaid_config_file=artifacts.mermaid_config_file,
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
            if artifacts:
                artifacts.cleanup(self.logger)

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

    def _build_mmdc_command(
        self,
        input_file: str,
        output_file: str,
        config: dict[str, Any],
        *,
        puppeteer_config_file: str | None = None,
        mermaid_config_file: str | None = None,
    ) -> tuple[list[str], str | None, str | None]:
        if not self._resolved_mmdc_command:
            raise MermaidCLIError("Mermaid CLI command not properly resolved")

        mmdc_command_parts = list(self._resolved_mmdc_command)

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

        fallback_manager = (
            self.artifact_manager
            if hasattr(self.artifact_manager, "_resolve_mermaid_config")
            else MermaidArtifactManager(self.config, self.logger)
        )

        used_mermaid_config = mermaid_config_file
        returned_mermaid_config = mermaid_config_file
        if used_mermaid_config is None:
            used_mermaid_config, should_cleanup_mermaid = (
                fallback_manager._resolve_mermaid_config()
            )
            if should_cleanup_mermaid:
                returned_mermaid_config = used_mermaid_config

        if used_mermaid_config:
            cmd.extend(["-c", used_mermaid_config])

        if self.config.get("css_file"):
            cmd.extend(["-C", self.config["css_file"]])

        custom_puppeteer_config = self.config.get("puppeteer_config")
        returned_puppeteer_config: str | None = None
        if custom_puppeteer_config and Path(custom_puppeteer_config).exists():
            cmd.extend(["-p", custom_puppeteer_config])
        else:
            fallback_used_config = puppeteer_config_file
            if fallback_used_config is None:
                fallback_used_config, should_cleanup_puppeteer = (
                    fallback_manager._resolve_puppeteer_config()
                )
                if should_cleanup_puppeteer:
                    returned_puppeteer_config = fallback_used_config
            else:
                returned_puppeteer_config = puppeteer_config_file

            if fallback_used_config:
                cmd.extend(["-p", fallback_used_config])

        return cmd, returned_puppeteer_config, returned_mermaid_config

    def _execute_mermaid_command(
        self, cmd: list[str]
    ) -> subprocess.CompletedProcess[str]:
        """Execute the Mermaid CLI command via the configured executor."""
        return self.cli_executor.run(cmd)
