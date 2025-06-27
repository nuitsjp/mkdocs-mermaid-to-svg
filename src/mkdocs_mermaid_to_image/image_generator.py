"""
MkDocs Mermaid to Image Plugin - 画像生成エンジン

このファイルは、Mermaid CLIを使用した画像生成を専門に扱います。
"""

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
    """
    Mermaid CLIを使用した画像生成を専門に扱うクラス

    単一責任原則に基づき、CLI実行と画像生成のみに責任を持ちます。
    """

    def __init__(self, config: dict[str, Any]) -> None:
        """
        MermaidImageGeneratorのコンストラクタ

        Args:
            config (Dict): 設定情報
        """
        self.config = config
        self.logger = setup_logger(__name__, config.get("log_level", "INFO"))
        self._validate_dependencies()

    def _validate_dependencies(self) -> None:
        """
        必要な依存関係（外部ツール）が利用可能かを検証

        Raises:
            MermaidCLIError: Mermaid CLIが見つからない場合
        """
        if not is_command_available(self.config["mmdc_path"]):
            raise MermaidCLIError(
                f"Mermaid CLI not found at '{self.config['mmdc_path']}'. "
                f"Please install it with: npm install -g @mermaid-js/mermaid-cli"
            )

    def generate(
        self, mermaid_code: str, output_path: str, config: dict[str, Any]
    ) -> bool:
        """
        MermaidコードからMermaid CLIを使用して画像を生成

        Args:
            mermaid_code (str): 画像生成対象のMermaidコード
            output_path (str): 生成する画像ファイルのパス
            config (Dict): 画像生成用の設定（ブロック固有設定含む）

        Returns:
            bool: 画像生成が成功した場合True、失敗した場合False
        """
        temp_file = None

        try:
            # Mermaidコード用の一時ファイルを作成
            temp_file = get_temp_file_path(".mmd")

            # 一時ファイルにMermaidコードを書き込み
            with Path(temp_file).open("w", encoding="utf-8") as f:
                f.write(mermaid_code)

            # 出力ディレクトリが存在することを保証
            ensure_directory(str(Path(output_path).parent))

            # mmdc（Mermaid CLI）コマンドを構築
            cmd = self._build_mmdc_command(temp_file, output_path, config)

            # 実行するコマンドをデバッグログに記録
            self.logger.debug(f"Executing: {' '.join(cmd)}")

            # mmdc コマンドを実行
            result = subprocess.run(  # nosec B603
                cmd, capture_output=True, text=True, timeout=30, check=False
            )

            # コマンドの実行結果をチェック
            if result.returncode != 0:
                error_msg = f"Mermaid CLI failed: {result.stderr}"
                self.logger.error(error_msg)
                if self.config["error_on_fail"]:
                    raise MermaidCLIError(error_msg)
                return False

            # 画像ファイルが実際に作成されたかを確認
            if not Path(output_path).exists():
                error_msg = f"Image not created: {output_path}"
                self.logger.error(error_msg)
                if self.config["error_on_fail"]:
                    raise MermaidCLIError(error_msg) from None
                return False

            # 成功をログに記録
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
            # 一時ファイルのクリーンアップ
            if temp_file:
                clean_temp_file(temp_file)

    def _build_mmdc_command(
        self, input_file: str, output_file: str, config: dict[str, Any]
    ) -> list[str]:
        """
        設定オプションを含むmmdcコマンドを構築

        Args:
            input_file (str): 入力ファイル（Mermaidコード）のパス
            output_file (str): 出力ファイル（画像）のパス
            config (Dict): 画像生成用の設定

        Returns:
            List[str]: 実行するコマンドの配列
        """
        # 基本的なコマンドを構築
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

        # オプション設定を追加（設定されている場合のみ）
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
