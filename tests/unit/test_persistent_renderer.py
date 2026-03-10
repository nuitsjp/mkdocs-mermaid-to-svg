"""PersistentRendererクラスのユニットテスト"""

import json
import os
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock, Mock, patch

import pytest

from mkdocs_mermaid_to_svg.exceptions import MermaidCLIError
from mkdocs_mermaid_to_svg.persistent_renderer import PersistentRenderer


@pytest.fixture
def basic_config() -> dict[str, Any]:
    """テスト用の基本設定"""
    return {
        "renderer": "persistent",
        "theme": "default",
        "css_file": None,
        "puppeteer_config": None,
        "mermaid_config": None,
        "error_on_fail": True,
        "log_level": "INFO",
        "cli_timeout": 90,
    }


@pytest.fixture
def mock_logger() -> Mock:
    """テスト用ロガーモック"""
    return Mock()


class TestBuildStartupConfig:
    """_build_startup_config のテスト"""

    def test_default_puppeteer_config(
        self, basic_config: dict[str, Any], mock_logger: Mock
    ) -> None:
        """デフォルトのPuppeteer設定が正しく構築される"""
        renderer = PersistentRenderer(basic_config, mock_logger)
        config = renderer._build_startup_config()

        assert "puppeteerConfig" in config
        assert "mermaidConfig" in config
        puppeteer = config["puppeteerConfig"]
        assert "--no-sandbox" in puppeteer["args"]
        assert "--disable-setuid-sandbox" in puppeteer["args"]

    def test_default_mermaid_config(
        self, basic_config: dict[str, Any], mock_logger: Mock
    ) -> None:
        """デフォルトのMermaid設定（htmlLabels: false）"""
        renderer = PersistentRenderer(basic_config, mock_logger)
        config = renderer._build_startup_config()

        mermaid = config["mermaidConfig"]
        assert mermaid["htmlLabels"] is False
        assert mermaid["flowchart"]["htmlLabels"] is False

    def test_custom_mermaid_config(
        self, basic_config: dict[str, Any], mock_logger: Mock
    ) -> None:
        """ユーザー指定のMermaid設定が使われる"""
        basic_config["mermaid_config"] = {"theme": "dark", "fontSize": 14}
        renderer = PersistentRenderer(basic_config, mock_logger)
        config = renderer._build_startup_config()

        assert config["mermaidConfig"]["theme"] == "dark"
        assert config["mermaidConfig"]["fontSize"] == 14

    def test_custom_puppeteer_config_file(
        self, basic_config: dict[str, Any], mock_logger: Mock, tmp_path: Path
    ) -> None:
        """puppeteer_configファイル指定時にマージされる"""
        puppeteer_file = tmp_path / "puppeteer.json"
        puppeteer_file.write_text(
            json.dumps(
                {"executablePath": "/usr/bin/chromium", "args": ["--extra-arg"]}
            ),
            encoding="utf-8",
        )
        basic_config["puppeteer_config"] = str(puppeteer_file)

        renderer = PersistentRenderer(basic_config, mock_logger)
        config = renderer._build_startup_config()

        puppeteer = config["puppeteerConfig"]
        assert puppeteer["executablePath"] == "/usr/bin/chromium"
        assert "--extra-arg" in puppeteer["args"]
        assert "--no-sandbox" in puppeteer["args"]

    @patch.dict(os.environ, {"CI": "true"})
    def test_ci_environment_args(
        self, basic_config: dict[str, Any], mock_logger: Mock
    ) -> None:
        """CI環境で追加引数が設定される"""
        renderer = PersistentRenderer(basic_config, mock_logger)
        config = renderer._build_startup_config()

        puppeteer = config["puppeteerConfig"]
        assert "--single-process" in puppeteer["args"]
        assert "--no-zygote" in puppeteer["args"]


class TestRenderSvg:
    """render_svg のモックテスト"""

    def test_successful_render(
        self,
        basic_config: dict[str, Any],
        mock_logger: Mock,
        tmp_path: Path,
    ) -> None:
        """正常なレンダリングでSVGファイルが出力される"""
        renderer = PersistentRenderer(basic_config, mock_logger)
        output_path = str(tmp_path / "output.svg")

        svg_content = "<svg>test</svg>"
        with (
            patch.object(renderer, "_ensure_process"),
            patch.object(
                renderer,
                "_send_request",
                return_value={"id": "test", "success": True, "svg": svg_content},
            ),
        ):
            result = renderer.render_svg(
                "graph TD\n  A-->B",
                output_path,
                {"theme": "default"},
            )

        assert result is True
        assert Path(output_path).read_text(encoding="utf-8") == svg_content

    def test_failed_render_with_error_on_fail(
        self,
        basic_config: dict[str, Any],
        mock_logger: Mock,
        tmp_path: Path,
    ) -> None:
        """レンダリング失敗時にerror_on_fail=Trueで例外が発生する"""
        renderer = PersistentRenderer(basic_config, mock_logger)
        output_path = str(tmp_path / "output.svg")

        with (
            patch.object(renderer, "_ensure_process"),
            patch.object(
                renderer,
                "_send_request",
                return_value={
                    "id": "test",
                    "success": False,
                    "error": "Syntax error",
                },
            ),
            pytest.raises(MermaidCLIError, match="レンダリングに失敗"),
        ):
            renderer.render_svg(
                "invalid code",
                output_path,
                {"theme": "default"},
            )

    def test_failed_render_without_error_on_fail(
        self,
        basic_config: dict[str, Any],
        mock_logger: Mock,
        tmp_path: Path,
    ) -> None:
        """レンダリング失敗時にerror_on_fail=FalseでFalseを返す"""
        basic_config["error_on_fail"] = False
        renderer = PersistentRenderer(basic_config, mock_logger)
        output_path = str(tmp_path / "output.svg")

        with (
            patch.object(renderer, "_ensure_process"),
            patch.object(
                renderer,
                "_send_request",
                return_value={
                    "id": "test",
                    "success": False,
                    "error": "Syntax error",
                },
            ),
        ):
            result = renderer.render_svg(
                "invalid code",
                output_path,
                {"theme": "default"},
            )

        assert result is False

    def test_render_with_css_file(
        self,
        basic_config: dict[str, Any],
        mock_logger: Mock,
        tmp_path: Path,
    ) -> None:
        """CSSファイルが指定されている場合にリクエストに含まれる"""
        css_file = tmp_path / "custom.css"
        css_file.write_text("body { color: red; }", encoding="utf-8")
        basic_config["css_file"] = str(css_file)

        renderer = PersistentRenderer(basic_config, mock_logger)
        output_path = str(tmp_path / "output.svg")

        captured_request: dict[str, Any] = {}

        def capture_request(req: dict[str, Any]) -> dict[str, Any]:
            captured_request.update(req)
            return {"id": req["id"], "success": True, "svg": "<svg/>"}

        with (
            patch.object(renderer, "_ensure_process"),
            patch.object(renderer, "_send_request", side_effect=capture_request),
        ):
            renderer.render_svg(
                "graph TD\n  A-->B",
                output_path,
                {"theme": "default"},
            )

        assert "css" in captured_request
        assert captured_request["css"] == "body { color: red; }"


class TestClose:
    """close のテスト"""

    def test_close_sends_shutdown(
        self, basic_config: dict[str, Any], mock_logger: Mock
    ) -> None:
        """closeでshutdownコマンドが送信される"""
        renderer = PersistentRenderer(basic_config, mock_logger)

        mock_proc = MagicMock()
        mock_proc.poll.return_value = None
        mock_proc.wait.return_value = None
        renderer._process = mock_proc

        renderer.close()

        mock_proc.stdin.write.assert_called_once()
        written = mock_proc.stdin.write.call_args[0][0]
        assert "shutdown" in written

    def test_close_kills_on_timeout(
        self, basic_config: dict[str, Any], mock_logger: Mock
    ) -> None:
        """shutdown送信後にタイムアウトした場合はkillされる"""
        renderer = PersistentRenderer(basic_config, mock_logger)

        mock_proc = MagicMock()
        mock_proc.poll.return_value = None
        mock_proc.wait.side_effect = [subprocess.TimeoutExpired("cmd", 5), None]
        renderer._process = mock_proc

        renderer.close()

        mock_proc.kill.assert_called_once()

    def test_close_noop_when_no_process(
        self, basic_config: dict[str, Any], mock_logger: Mock
    ) -> None:
        """プロセスがない場合はclose呼び出しが安全にスキップされる"""
        renderer = PersistentRenderer(basic_config, mock_logger)
        renderer.close()  # 例外が発生しないこと

    def test_close_noop_when_already_exited(
        self, basic_config: dict[str, Any], mock_logger: Mock
    ) -> None:
        """既に終了しているプロセスに対してcloseが安全にスキップされる"""
        renderer = PersistentRenderer(basic_config, mock_logger)
        mock_proc = MagicMock()
        mock_proc.poll.return_value = 0
        renderer._process = mock_proc

        renderer.close()

        mock_proc.stdin.write.assert_not_called()


class TestEnsureProcess:
    """_ensure_process のテスト"""

    def test_starts_process_if_none(
        self, basic_config: dict[str, Any], mock_logger: Mock
    ) -> None:
        """プロセスがない場合に起動される"""
        renderer = PersistentRenderer(basic_config, mock_logger)

        with patch.object(renderer, "_start_process") as mock_start:
            renderer._ensure_process()
            mock_start.assert_called_once()

    def test_restarts_if_process_exited(
        self, basic_config: dict[str, Any], mock_logger: Mock
    ) -> None:
        """プロセスが終了している場合に再起動される"""
        renderer = PersistentRenderer(basic_config, mock_logger)
        mock_proc = MagicMock()
        mock_proc.poll.return_value = 1  # 終了済み
        renderer._process = mock_proc

        with patch.object(renderer, "_start_process") as mock_start:
            renderer._ensure_process()
            mock_start.assert_called_once()

    def test_skips_if_process_running(
        self, basic_config: dict[str, Any], mock_logger: Mock
    ) -> None:
        """プロセスが実行中の場合は再起動しない"""
        renderer = PersistentRenderer(basic_config, mock_logger)
        mock_proc = MagicMock()
        mock_proc.poll.return_value = None  # 実行中
        renderer._process = mock_proc

        with patch.object(renderer, "_start_process") as mock_start:
            renderer._ensure_process()
            mock_start.assert_not_called()


class TestSendRequest:
    """_send_request のテスト"""

    def test_raises_on_no_process(
        self, basic_config: dict[str, Any], mock_logger: Mock
    ) -> None:
        """プロセスがない場合に例外が発生する"""
        renderer = PersistentRenderer(basic_config, mock_logger)
        renderer._process = None

        with pytest.raises(MermaidCLIError, match="起動していません"):
            renderer._send_request({"id": "test", "code": "graph TD"})

    def test_raises_on_timeout(
        self, basic_config: dict[str, Any], mock_logger: Mock
    ) -> None:
        """タイムアウト時に例外が発生しプロセスがkillされる"""
        basic_config["cli_timeout"] = 1
        renderer = PersistentRenderer(basic_config, mock_logger, cli_timeout=0.1)

        mock_proc = MagicMock()
        mock_proc.poll.return_value = None
        mock_proc.stderr.read.return_value = ""
        renderer._process = mock_proc

        with (
            patch.object(renderer, "_readline_with_timeout", return_value=None),
            patch.object(renderer, "_kill_process") as mock_kill,
            pytest.raises(MermaidCLIError, match="タイムアウト"),
        ):
            renderer._send_request({"id": "test", "code": "graph TD"})

        mock_kill.assert_called_once()

    def test_raises_on_broken_pipe(
        self, basic_config: dict[str, Any], mock_logger: Mock
    ) -> None:
        """BrokenPipeError時に例外が発生しプロセスがkillされる"""
        renderer = PersistentRenderer(basic_config, mock_logger)

        mock_proc = MagicMock()
        mock_proc.poll.return_value = None
        mock_proc.stdin.write.side_effect = BrokenPipeError("broken")
        renderer._process = mock_proc

        with (
            patch.object(renderer, "_kill_process") as mock_kill,
            pytest.raises(MermaidCLIError, match="リクエスト送信に失敗"),
        ):
            renderer._send_request({"id": "test", "code": "graph TD"})

        mock_kill.assert_called_once()


class TestStartProcess:
    """_start_process のテスト"""

    def test_raises_when_node_not_found(
        self, basic_config: dict[str, Any], mock_logger: Mock
    ) -> None:
        """Node.jsが見つからない場合に例外が発生する"""
        renderer = PersistentRenderer(basic_config, mock_logger)

        with (
            patch("shutil.which", return_value=None),
            pytest.raises(MermaidCLIError, match="Node.jsが見つかりません"),
        ):
            renderer._start_process()


import subprocess  # noqa: E402


class TestConfigRendererChoice:
    """config/image_generatorの統合テスト"""

    def test_persistent_choice_in_config(self) -> None:
        """renderer='persistent'が設定として有効"""
        from mkdocs_mermaid_to_svg.config import ConfigManager

        config = {"renderer": "persistent", "cli_timeout": 90}
        assert ConfigManager.validate_config(config) is True

    def test_invalid_renderer_rejected(self) -> None:
        """無効なrenderer値が拒否される"""
        from mkdocs_mermaid_to_svg.config import ConfigManager
        from mkdocs_mermaid_to_svg.exceptions import MermaidConfigError

        config = {"renderer": "invalid"}
        with pytest.raises(MermaidConfigError):
            ConfigManager.validate_config(config)

    def test_persistent_creates_persistent_renderer(self) -> None:
        """renderer='persistent'でPersistentRendererが生成される"""
        from mkdocs_mermaid_to_svg.image_generator import MermaidImageGenerator

        config = {
            "renderer": "persistent",
            "theme": "default",
            "css_file": None,
            "puppeteer_config": None,
            "mermaid_config": None,
            "error_on_fail": True,
            "log_level": "INFO",
            "mmdc_path": "mmdc",
            "cli_timeout": 90,
        }

        generator = MermaidImageGenerator(config)
        assert isinstance(generator.renderer, PersistentRenderer)

    def test_persistent_does_not_resolve_mmdc(self) -> None:
        """renderer='persistent'ではmmdcコマンドの解決をスキップする"""
        from mkdocs_mermaid_to_svg.image_generator import MermaidImageGenerator

        config = {
            "renderer": "persistent",
            "theme": "default",
            "css_file": None,
            "puppeteer_config": None,
            "mermaid_config": None,
            "error_on_fail": True,
            "log_level": "INFO",
            "mmdc_path": "mmdc",
            "cli_timeout": 90,
        }

        # mmdcが見つからなくてもエラーにならないことを確認
        with patch(
            "mkdocs_mermaid_to_svg.image_generator.is_command_available",
            return_value=False,
        ):
            generator = MermaidImageGenerator(config)
            assert isinstance(generator.renderer, PersistentRenderer)
