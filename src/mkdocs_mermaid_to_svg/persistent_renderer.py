"""Puppeteer常駐プロセスを利用したMermaidレンダラー"""

from __future__ import annotations

import atexit
import base64
import json
import os
import shutil
import subprocess  # nosec B404
import threading
import uuid
from pathlib import Path
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    import logging

from .exceptions import MermaidCLIError
from .utils import ensure_directory


class PersistentRenderer:
    """Node.js+Puppeteer常駐プロセスでMermaidダイアグラムをSVGに変換する

    ブラウザを1回だけ起動し、NDJSONプロトコルで複数リクエストを処理する。
    ``Renderer`` プロトコル（image_generator.py）を実装する。
    """

    def __init__(
        self,
        config: dict[str, Any],
        logger: logging.Logger,
        *,
        cli_timeout: float = 90.0,
    ) -> None:
        self.config = config
        self.logger = logger
        self._cli_timeout = cli_timeout
        self._process: subprocess.Popen[str] | None = None
        self._lock = threading.Lock()
        self._closed = False

    # ------------------------------------------------------------------
    # Renderer プロトコル
    # ------------------------------------------------------------------

    def render_svg(
        self,
        mermaid_code: str,
        output_path: str,
        config: dict[str, Any],
        page_file: str | None = None,
    ) -> bool:
        """MermaidコードをSVGファイルとしてレンダリングする"""
        self._ensure_process()

        request_id = uuid.uuid4().hex[:12]
        request: dict[str, Any] = {
            "id": request_id,
            "code": mermaid_code,
            "theme": config.get("theme", self.config.get("theme", "default")),
        }

        css_file = self.config.get("css_file")
        if css_file and Path(css_file).exists():
            request["css"] = Path(css_file).read_text(encoding="utf-8")

        response = self._send_request(request)

        if not response.get("success"):
            error_msg = response.get("error", "不明なエラー")
            self.logger.error(
                "Mermaidレンダリングに失敗 (id=%s): %s", request_id, error_msg
            )
            if self.config.get("error_on_fail", True):
                raise MermaidCLIError(
                    f"Persistent rendererでのレンダリングに失敗: {error_msg}",
                    command="node persistent_mermaid_renderer.mjs",
                )
            return False

        svg_content = response.get("svg", "")
        ensure_directory(str(Path(output_path).parent))
        Path(output_path).write_text(svg_content, encoding="utf-8")
        return True

    def close(self) -> None:
        """常駐プロセスを安全にシャットダウンする"""
        with self._lock:
            self._closed = True
            proc = self._process
            self._process = None

        if proc is None or proc.poll() is not None:
            return

        try:
            shutdown_cmd = json.dumps({"command": "shutdown"}) + "\n"
            proc.stdin.write(shutdown_cmd)  # type: ignore[union-attr]
            proc.stdin.flush()  # type: ignore[union-attr]
            proc.wait(timeout=5.0)
            self.logger.debug("常駐プロセスを正常にシャットダウンしました")
        except Exception:
            self.logger.warning("常駐プロセスのシャットダウンに失敗、強制終了します")
            proc.kill()
            proc.wait(timeout=5.0)

    # ------------------------------------------------------------------
    # 内部メソッド
    # ------------------------------------------------------------------

    def _ensure_process(self) -> None:
        """常駐プロセスが起動していなければ起動する（遅延初期化）"""
        with self._lock:
            if self._closed:
                # close後に再利用された場合はフラグをリセット
                self._closed = False

            if self._process is not None and self._process.poll() is None:
                return

            self._start_process()

    def _start_process(self) -> None:
        """Node.js常駐プロセスを起動し、readyメッセージを待つ"""
        node_path = shutil.which("node")
        if node_path is None:
            raise MermaidCLIError(
                "Node.jsが見つかりません。インストールしてください。",
                command="node",
            )

        script_path = str(Path(__file__).with_name("persistent_mermaid_renderer.mjs"))

        startup_config = self._build_startup_config()
        config_b64 = base64.b64encode(
            json.dumps(startup_config).encode("utf-8")
        ).decode("ascii")

        cmd = [node_path, script_path, config_b64]
        self.logger.debug("常駐プロセスを起動: %s", " ".join(cmd))

        self._process = subprocess.Popen(  # nosec B603
            cmd,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding="utf-8",
            bufsize=1,
        )

        atexit.register(self.close)

        # readyメッセージを待つ
        ready_response = self._readline_with_timeout(timeout=30.0)
        if ready_response is None:
            stderr_output = self._read_stderr()
            self._kill_process()
            raise MermaidCLIError(
                f"常駐プロセスの起動に失敗しました: {stderr_output}",
                command=" ".join(cmd),
                stderr=stderr_output,
            )

        try:
            ready_data = json.loads(ready_response)
        except json.JSONDecodeError as exc:
            stderr_output = self._read_stderr()
            self._kill_process()
            raise MermaidCLIError(
                f"常駐プロセスからの応答をパースできません: {ready_response}",
                command=" ".join(cmd),
                stderr=stderr_output,
            ) from exc

        if not ready_data.get("ready"):
            self._kill_process()
            raise MermaidCLIError(
                "常駐プロセスがready状態になりませんでした",
                command=" ".join(cmd),
            )

        self.logger.debug("常駐プロセスが起動しました (pid=%s)", self._process.pid)

    def _build_startup_config(self) -> dict[str, Any]:
        """起動設定を構築する（MermaidArtifactManagerと同等のpuppeteer引数）"""
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

        # ユーザー指定のpuppeteer_configファイルがあればマージ
        custom_config_path = self.config.get("puppeteer_config")
        if custom_config_path and Path(custom_config_path).exists():
            try:
                with Path(custom_config_path).open(encoding="utf-8") as f:
                    custom_config = json.load(f)
                if isinstance(custom_config, dict):
                    # argsはマージ、他のキーは上書き
                    custom_args = custom_config.pop("args", [])
                    puppeteer_config.update(custom_config)
                    if custom_args:
                        existing_args = set(puppeteer_config.get("args", []))
                        for arg in custom_args:
                            if arg not in existing_args:
                                puppeteer_config["args"].append(arg)
            except (json.JSONDecodeError, OSError) as exc:
                self.logger.warning("puppeteer_config読み込みに失敗: %s", exc)

        # mermaid設定
        mermaid_config_raw = self.config.get("mermaid_config")
        if isinstance(mermaid_config_raw, dict):
            mermaid_config = mermaid_config_raw
        else:
            mermaid_config = {
                "htmlLabels": False,
                "flowchart": {"htmlLabels": False},
                "class": {"htmlLabels": False},
            }

        return {
            "puppeteerConfig": puppeteer_config,
            "mermaidConfig": mermaid_config,
        }

    def _send_request(self, request: dict[str, Any]) -> dict[str, Any]:
        """リクエストを送信し、レスポンスを受け取る"""
        proc = self._process
        if proc is None or proc.poll() is not None:
            raise MermaidCLIError("常駐プロセスが起動していません")

        request_line = json.dumps(request, ensure_ascii=False) + "\n"
        try:
            proc.stdin.write(request_line)  # type: ignore[union-attr]
            proc.stdin.flush()  # type: ignore[union-attr]
        except (BrokenPipeError, OSError) as exc:
            self._kill_process()
            raise MermaidCLIError(
                f"常駐プロセスへのリクエスト送信に失敗: {exc}"
            ) from exc

        response_line = self._readline_with_timeout(timeout=self._cli_timeout)
        if response_line is None:
            stderr_output = self._read_stderr()
            self._kill_process()
            raise MermaidCLIError(
                f"常駐プロセスからの応答がタイムアウトしました "
                f"(timeout={self._cli_timeout}s): {stderr_output}",
                stderr=stderr_output,
            )

        try:
            return json.loads(response_line)  # type: ignore[no-any-return]
        except json.JSONDecodeError as exc:
            raise MermaidCLIError(
                f"常駐プロセスからの応答をパースできません: {response_line}"
            ) from exc

    def _readline_with_timeout(self, *, timeout: float) -> str | None:
        """stdoutから1行読み取る（タイムアウト付き）

        WindowsのselectがpipeをサポートしないためThreadベースで実装。
        """
        result: list[str | None] = [None]

        def _read() -> None:
            try:
                proc = self._process
                if proc and proc.stdout:
                    line = proc.stdout.readline()
                    if line:
                        result[0] = line.rstrip("\n").rstrip("\r")
            except Exception:
                pass

        thread = threading.Thread(target=_read, daemon=True)
        thread.start()
        thread.join(timeout=timeout)

        if thread.is_alive():
            return None

        return result[0]

    def _read_stderr(self) -> str:
        """stderrから利用可能な内容を読み取る（ノンブロッキング）"""
        proc = self._process
        if proc is None or proc.stderr is None:
            return ""
        try:
            # stderrの残りを読むためにプロセスが終了している場合のみ
            if proc.poll() is not None:
                return proc.stderr.read() or ""
        except Exception:
            pass
        return ""

    def _kill_process(self) -> None:
        """常駐プロセスを強制終了する"""
        proc = self._process
        self._process = None
        if proc is not None:
            try:
                proc.kill()
                proc.wait(timeout=5.0)
            except Exception:
                pass
