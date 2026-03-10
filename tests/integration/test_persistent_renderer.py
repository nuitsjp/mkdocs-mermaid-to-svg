"""PersistentRendererの統合テスト

実際のNode.jsプロセスを起動してMermaid SVGレンダリングを検証する。
"""

import shutil
from pathlib import Path
from typing import Any
from unittest.mock import Mock

import pytest

from mkdocs_mermaid_to_svg.exceptions import MermaidCLIError
from mkdocs_mermaid_to_svg.persistent_renderer import PersistentRenderer

# Node.jsとmermaid-cliが利用可能かチェック
_NODE_AVAILABLE = shutil.which("node") is not None


def _check_mermaid_available() -> bool:
    """mermaidパッケージがnode_modulesにインストールされているか確認"""
    if not _NODE_AVAILABLE:
        return False
    try:
        import subprocess

        result = subprocess.run(  # nosec B603 B607
            ["node", "-e", "require.resolve('mermaid')"],
            capture_output=True,
            text=True,
            check=False,
            timeout=10,
        )
        return result.returncode == 0
    except Exception:
        return False


def _check_puppeteer_available() -> bool:
    """puppeteerパッケージがnode_modulesにインストールされているか確認"""
    if not _NODE_AVAILABLE:
        return False
    try:
        import subprocess

        result = subprocess.run(  # nosec B603 B607
            ["node", "-e", "require.resolve('puppeteer')"],
            capture_output=True,
            text=True,
            check=False,
            timeout=10,
        )
        return result.returncode == 0
    except Exception:
        return False


_MERMAID_AVAILABLE = _check_mermaid_available()
_PUPPETEER_AVAILABLE = _check_puppeteer_available()

pytestmark = [
    pytest.mark.integration,
    pytest.mark.skipif(not _NODE_AVAILABLE, reason="Node.jsが利用できません"),
    pytest.mark.skipif(
        not _MERMAID_AVAILABLE, reason="mermaidパッケージが利用できません"
    ),
    pytest.mark.skipif(
        not _PUPPETEER_AVAILABLE, reason="puppeteerパッケージが利用できません"
    ),
]


@pytest.fixture
def persistent_config() -> dict[str, Any]:
    """テスト用の設定"""
    import os

    puppeteer_config = None
    if os.getenv("CI") or os.getenv("GITHUB_ACTIONS"):
        config_path = (
            Path(__file__).parent.parent.parent / ".github" / "puppeteer.config.json"
        )
        if config_path.exists():
            puppeteer_config = str(config_path)

    return {
        "renderer": "persistent",
        "theme": "default",
        "css_file": None,
        "puppeteer_config": puppeteer_config,
        "mermaid_config": None,
        "error_on_fail": True,
        "log_level": "INFO",
        "cli_timeout": 90,
    }


@pytest.fixture
def renderer(persistent_config: dict[str, Any]) -> PersistentRenderer:
    """PersistentRendererインスタンスを作成し、テスト後にクリーンアップ"""
    logger = Mock()
    r = PersistentRenderer(persistent_config, logger, cli_timeout=90.0)
    yield r  # type: ignore[misc]
    r.close()


class TestPersistentRendererIntegration:
    """実際のNode.jsプロセスを使った統合テスト"""

    @pytest.mark.slow
    def test_render_flowchart(
        self, renderer: PersistentRenderer, tmp_path: Path
    ) -> None:
        """フローチャートのSVG生成"""
        output_path = str(tmp_path / "flowchart.svg")
        result = renderer.render_svg(
            "graph TD\n  A[Start] --> B[End]",
            output_path,
            {"theme": "default"},
        )

        assert result is True
        svg_content = Path(output_path).read_text(encoding="utf-8")
        assert "<svg" in svg_content
        assert "Start" in svg_content

    @pytest.mark.slow
    def test_render_sequence_diagram(
        self, renderer: PersistentRenderer, tmp_path: Path
    ) -> None:
        """シーケンス図のSVG生成"""
        output_path = str(tmp_path / "sequence.svg")
        result = renderer.render_svg(
            "sequenceDiagram\n  Alice->>Bob: Hello\n  Bob-->>Alice: Hi",
            output_path,
            {"theme": "default"},
        )

        assert result is True
        svg_content = Path(output_path).read_text(encoding="utf-8")
        assert "<svg" in svg_content

    @pytest.mark.slow
    def test_multiple_renders_same_process(
        self, renderer: PersistentRenderer, tmp_path: Path
    ) -> None:
        """同一プロセスで複数ダイアグラムを連続レンダリング"""
        diagrams = [
            ("graph TD\n  A-->B", "diagram1.svg"),
            ("graph LR\n  C-->D", "diagram2.svg"),
            ("graph TD\n  E-->F-->G", "diagram3.svg"),
        ]

        for code, filename in diagrams:
            output_path = str(tmp_path / filename)
            result = renderer.render_svg(code, output_path, {"theme": "default"})
            assert result is True
            assert "<svg" in Path(output_path).read_text(encoding="utf-8")

    @pytest.mark.slow
    def test_render_with_theme(
        self, renderer: PersistentRenderer, tmp_path: Path
    ) -> None:
        """テーマ指定付きレンダリング"""
        output_path = str(tmp_path / "dark.svg")
        result = renderer.render_svg(
            "graph TD\n  A-->B",
            output_path,
            {"theme": "dark"},
        )

        assert result is True
        assert Path(output_path).exists()

    @pytest.mark.slow
    def test_invalid_code_error(
        self, renderer: PersistentRenderer, tmp_path: Path
    ) -> None:
        """不正なMermaidコードでエラーが返る"""
        output_path = str(tmp_path / "invalid.svg")
        with pytest.raises(MermaidCLIError):
            renderer.render_svg(
                "this is not valid mermaid code !!!@@@###",
                output_path,
                {"theme": "default"},
            )

    @pytest.mark.slow
    def test_close_and_rerender(
        self, persistent_config: dict[str, Any], tmp_path: Path
    ) -> None:
        """close後に再度renderするとプロセスが再起動される"""
        logger = Mock()
        renderer = PersistentRenderer(persistent_config, logger, cli_timeout=90.0)

        try:
            # 初回レンダリング
            output1 = str(tmp_path / "first.svg")
            result1 = renderer.render_svg(
                "graph TD\n  A-->B", output1, {"theme": "default"}
            )
            assert result1 is True

            # closeしてプロセスを終了
            renderer.close()
            assert renderer._process is None

            # 再度レンダリング（プロセスが自動再起動）
            output2 = str(tmp_path / "second.svg")
            result2 = renderer.render_svg(
                "graph LR\n  C-->D", output2, {"theme": "default"}
            )
            assert result2 is True
            assert "<svg" in Path(output2).read_text(encoding="utf-8")
        finally:
            renderer.close()


class TestPluginCloseIntegration:
    """plugin.pyのon_post_buildでcloseが呼ばれることのテスト"""

    def test_on_post_build_calls_close(self) -> None:
        """on_post_buildでrendererのcloseが呼ばれる"""
        from unittest.mock import MagicMock, patch

        from mkdocs_mermaid_to_svg.plugin import MermaidSvgConverterPlugin

        plugin = MermaidSvgConverterPlugin()

        # processorモックを設定
        mock_renderer = MagicMock()
        mock_renderer.close = MagicMock()
        mock_image_generator = MagicMock()
        mock_image_generator.renderer = mock_renderer
        mock_processor = MagicMock()
        mock_processor.image_generator = mock_image_generator

        plugin.processor = mock_processor
        plugin.generated_images = []

        # _should_be_enabledをTrueに
        with patch.object(plugin, "_should_be_enabled", return_value=True):
            plugin.on_post_build(config=MagicMock())

        mock_renderer.close.assert_called_once()
