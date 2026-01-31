"""一括レンダリング機能の単体テスト"""

from __future__ import annotations

import json
import subprocess
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock, patch

import pytest

from mkdocs_mermaid_to_svg.exceptions import MermaidCLIError
from mkdocs_mermaid_to_svg.image_generator import (
    BatchRenderItem,
    BatchRenderResult,
    BeautifulMermaidRenderer,
    MermaidImageGenerator,
)


class TestBatchRenderItem:
    """BatchRenderItemのdataclassテスト"""

    def test_フィールドの初期化(self) -> None:
        item = BatchRenderItem(
            id="index_mermaid_0_abc12345",
            code="graph TD\n  A-->B",
            theme="default",
            output_path="/site/assets/images/index_mermaid_0_abc12345.svg",
            page_file="index.md",
        )
        assert item.id == "index_mermaid_0_abc12345"
        assert item.code == "graph TD\n  A-->B"
        assert item.theme == "default"
        assert item.output_path == "/site/assets/images/index_mermaid_0_abc12345.svg"
        assert item.page_file == "index.md"

    def test_frozenでイミュータブル(self) -> None:
        item = BatchRenderItem(
            id="test_id",
            code="graph TD",
            theme="default",
            output_path="/tmp/test.svg",
            page_file="test.md",
        )
        with pytest.raises(AttributeError):
            item.id = "new_id"  # type: ignore[misc]


class TestBatchRenderResult:
    """BatchRenderResultのdataclassテスト"""

    def test_成功時のフィールド(self) -> None:
        result = BatchRenderResult(
            id="index_mermaid_0_abc12345",
            success=True,
            svg="<svg>test</svg>",
        )
        assert result.id == "index_mermaid_0_abc12345"
        assert result.success is True
        assert result.svg == "<svg>test</svg>"
        assert result.error is None

    def test_失敗時のフィールド(self) -> None:
        result = BatchRenderResult(
            id="index_mermaid_0_abc12345",
            success=False,
            error="Parse error in mermaid code",
        )
        assert result.id == "index_mermaid_0_abc12345"
        assert result.success is False
        assert result.svg is None
        assert result.error == "Parse error in mermaid code"

    def test_デフォルト値(self) -> None:
        result = BatchRenderResult(
            id="test_id",
            success=True,
        )
        assert result.svg is None
        assert result.error is None

    def test_frozenでイミュータブル(self) -> None:
        result = BatchRenderResult(
            id="test_id",
            success=True,
            svg="<svg></svg>",
        )
        with pytest.raises(AttributeError):
            result.success = False  # type: ignore[misc]


# ---------------------------------------------------------------------------
# T005: --batch-render モードの動作テスト（subprocess経由でNode.jsを呼び出し）
# ---------------------------------------------------------------------------

RUNNER_PATH = (
    Path(__file__).resolve().parents[2]
    / "src"
    / "mkdocs_mermaid_to_svg"
    / "beautiful_mermaid_runner.mjs"
)

# beautiful-mermaid npmパッケージが利用可能か判定
_NODE_MODULES = (
    Path(__file__).resolve().parents[2] / "node_modules" / "beautiful-mermaid"
)
_BEAUTIFUL_MERMAID_AVAILABLE = _NODE_MODULES.exists()
_SKIP_REASON = "beautiful-mermaid npmパッケージが未インストール"


def _run_batch_render(
    payload: list[dict[str, Any]],
) -> subprocess.CompletedProcess[str]:
    """テスト用ヘルパー: --batch-renderモードを実行する"""
    return subprocess.run(
        ["node", str(RUNNER_PATH), "--batch-render"],
        input=json.dumps(payload),
        capture_output=True,
        text=True,
        check=False,
        cwd=str(Path.cwd()),
        encoding="utf-8",
    )


@pytest.mark.skipif(not _BEAUTIFUL_MERMAID_AVAILABLE, reason=_SKIP_REASON)
class TestBatchRenderNodeRunner:
    """--batch-renderモードの動作テスト（T005）"""

    @pytest.mark.integration
    def test_正常系_複数ダイアグラムの一括処理(self) -> None:
        payload = [
            {"id": "item_1", "code": "graph TD\n  A-->B", "theme": "default"},
            {
                "id": "item_2",
                "code": "sequenceDiagram\n  Alice->>Bob: Hello",
                "theme": "default",
            },
        ]
        result = _run_batch_render(payload)
        assert result.returncode == 0, f"stderr: {result.stderr}"
        results = json.loads(result.stdout)
        assert len(results) == 2
        assert results[0]["id"] == "item_1"
        assert results[0]["success"] is True
        assert "<svg" in results[0]["svg"]
        assert results[1]["id"] == "item_2"
        assert results[1]["success"] is True
        assert "<svg" in results[1]["svg"]

    @pytest.mark.integration
    def test_空配列の入力(self) -> None:
        result = _run_batch_render([])
        assert result.returncode == 0
        results = json.loads(result.stdout)
        assert results == []

    @pytest.mark.integration
    def test_エラー分離_個別ダイアグラムの失敗が他に影響しない(self) -> None:
        payload = [
            {"id": "good", "code": "graph TD\n  A-->B", "theme": "default"},
            {"id": "bad", "code": "", "theme": "default"},
        ]
        result = _run_batch_render(payload)
        assert result.returncode == 0
        results = json.loads(result.stdout)
        assert len(results) == 2
        # 正常な方は成功
        assert results[0]["id"] == "good"
        assert results[0]["success"] is True
        assert "<svg" in results[0]["svg"]
        # 空コードの方はエラー
        assert results[1]["id"] == "bad"
        assert results[1]["success"] is False
        assert results[1]["error"] is not None

    @pytest.mark.integration
    def test_テーマ指定の反映(self) -> None:
        payload = [
            {"id": "themed", "code": "graph TD\n  A-->B", "theme": "dark"},
        ]
        result = _run_batch_render(payload)
        assert result.returncode == 0
        results = json.loads(result.stdout)
        assert len(results) == 1
        assert results[0]["success"] is True
        assert "<svg" in results[0]["svg"]


# ---------------------------------------------------------------------------
# T007: batch_render メソッドの単体テスト（subprocess をモック）
# ---------------------------------------------------------------------------


def _make_renderer() -> BeautifulMermaidRenderer:
    """テスト用ヘルパー: BeautifulMermaidRendererを生成する"""
    generator = MagicMock(spec=MermaidImageGenerator)
    logger = MagicMock()
    return BeautifulMermaidRenderer(generator, logger)


def _make_items(count: int = 2) -> list[BatchRenderItem]:
    """テスト用ヘルパー: BatchRenderItemリストを生成する"""
    return [
        BatchRenderItem(
            id=f"item_{i}",
            code=f"graph TD\n  A{i}-->B{i}",
            theme="default",
            output_path=f"/site/images/item_{i}.svg",
            page_file=f"page_{i}.md",
        )
        for i in range(count)
    ]


class TestBatchRenderMethod:
    """batch_renderメソッドの単体テスト（T007）"""

    @patch("mkdocs_mermaid_to_svg.image_generator.subprocess.run")
    def test_正常系_複数ダイアグラムの一括処理(self, mock_run: MagicMock) -> None:
        mock_run.return_value = subprocess.CompletedProcess(
            args=[],
            returncode=0,
            stdout=json.dumps(
                [
                    {"id": "item_0", "success": True, "svg": "<svg>0</svg>"},
                    {"id": "item_1", "success": True, "svg": "<svg>1</svg>"},
                ]
            ),
            stderr="",
        )
        renderer = _make_renderer()
        items = _make_items(2)
        results = renderer.batch_render(items)

        assert len(results) == 2
        assert results[0].id == "item_0"
        assert results[0].success is True
        assert results[0].svg == "<svg>0</svg>"
        assert results[1].id == "item_1"
        assert results[1].success is True
        assert results[1].svg == "<svg>1</svg>"

        # subprocessの呼び出しを確認
        mock_run.assert_called_once()
        call_args = mock_run.call_args
        assert "--batch-render" in call_args[0][0]
        # 入力JSONの検証
        input_payload = json.loads(call_args[1]["input"])
        assert len(input_payload) == 2
        assert input_payload[0]["id"] == "item_0"
        assert input_payload[1]["id"] == "item_1"

    @patch("mkdocs_mermaid_to_svg.image_generator.subprocess.run")
    def test_プロセスクラッシュ時にMermaidCLIError(self, mock_run: MagicMock) -> None:
        mock_run.return_value = subprocess.CompletedProcess(
            args=[],
            returncode=1,
            stdout="",
            stderr="Segmentation fault",
        )
        renderer = _make_renderer()
        items = _make_items(1)

        with pytest.raises(MermaidCLIError, match="一括レンダリングに失敗"):
            renderer.batch_render(items)

    @patch("mkdocs_mermaid_to_svg.image_generator.subprocess.run")
    def test_空リストではNodejsを起動しない(self, mock_run: MagicMock) -> None:
        renderer = _make_renderer()
        results = renderer.batch_render([])

        assert results == []
        mock_run.assert_not_called()

    @patch("mkdocs_mermaid_to_svg.image_generator.subprocess.run")
    def test_テーマオーバーライドがペイロードに反映される(
        self, mock_run: MagicMock
    ) -> None:
        mock_run.return_value = subprocess.CompletedProcess(
            args=[],
            returncode=0,
            stdout=json.dumps(
                [
                    {"id": "dark_item", "success": True, "svg": "<svg>dark</svg>"},
                ]
            ),
            stderr="",
        )
        renderer = _make_renderer()
        items = [
            BatchRenderItem(
                id="dark_item",
                code="graph TD\n  A-->B",
                theme="dark",
                output_path="/site/images/dark.svg",
                page_file="page.md",
            )
        ]
        results = renderer.batch_render(items)

        assert len(results) == 1
        assert results[0].success is True
        # ペイロードにテーマが正しく設定されていることを確認
        input_payload = json.loads(mock_run.call_args[1]["input"])
        assert input_payload[0]["theme"] == "dark"

    @patch("mkdocs_mermaid_to_svg.image_generator.subprocess.run")
    def test_不正なJSON出力でMermaidCLIError(self, mock_run: MagicMock) -> None:
        mock_run.return_value = subprocess.CompletedProcess(
            args=[],
            returncode=0,
            stdout="not valid json",
            stderr="",
        )
        renderer = _make_renderer()
        items = _make_items(1)

        with pytest.raises(MermaidCLIError, match="パースできません"):
            renderer.batch_render(items)

    @patch("mkdocs_mermaid_to_svg.image_generator.subprocess.run")
    def test_OSError時にMermaidCLIError(self, mock_run: MagicMock) -> None:
        mock_run.side_effect = OSError("No such file or directory")
        renderer = _make_renderer()
        items = _make_items(1)

        with pytest.raises(MermaidCLIError, match="Node.jsの実行に失敗"):
            renderer.batch_render(items)

    @patch("mkdocs_mermaid_to_svg.image_generator.subprocess.run")
    def test_部分的な失敗結果を正しくパースする(self, mock_run: MagicMock) -> None:
        mock_run.return_value = subprocess.CompletedProcess(
            args=[],
            returncode=0,
            stdout=json.dumps(
                [
                    {"id": "ok", "success": True, "svg": "<svg>ok</svg>"},
                    {"id": "ng", "success": False, "error": "Parse error"},
                ]
            ),
            stderr="",
        )
        renderer = _make_renderer()
        items = _make_items(2)
        results = renderer.batch_render(items)

        assert len(results) == 2
        assert results[0].success is True
        assert results[0].svg == "<svg>ok</svg>"
        assert results[0].error is None
        assert results[1].success is False
        assert results[1].svg is None
        assert results[1].error == "Parse error"


# ---------------------------------------------------------------------------
# T018: 一括処理と個別処理のSVG出力同一性テスト
# ---------------------------------------------------------------------------


def _run_single_render(code: str, theme: str = "default") -> str:
    """テスト用ヘルパー: --renderモード（個別処理）を実行してSVGを返す"""
    payload = {"code": code, "theme": theme}
    result = subprocess.run(
        ["node", str(RUNNER_PATH), "--render"],
        input=json.dumps(payload),
        capture_output=True,
        text=True,
        check=False,
        cwd=str(Path.cwd()),
        encoding="utf-8",
    )
    assert result.returncode == 0, f"--render失敗: {result.stderr}"
    return result.stdout


@pytest.mark.skipif(not _BEAUTIFUL_MERMAID_AVAILABLE, reason=_SKIP_REASON)
class TestBatchVsSingleOutputIdentity:
    """一括処理と個別処理のSVG出力同一性テスト（T018/T019）"""

    @pytest.mark.integration
    @pytest.mark.parametrize(
        "code,label",
        [
            ("graph TD\n  A-->B\n  B-->C", "flowchart"),
            ("sequenceDiagram\n  Alice->>Bob: Hello\n  Bob-->>Alice: Hi", "sequence"),
            ("classDiagram\n  Animal <|-- Duck\n  Animal : +int age", "class"),
            ("erDiagram\n  CUSTOMER ||--o{ ORDER : places", "er"),
            ("stateDiagram-v2\n  [*] --> Active\n  Active --> [*]", "state"),
        ],
    )
    def test_一括処理と個別処理のSVG出力が一致する(self, code: str, label: str) -> None:
        """同じMermaidコード・テーマで個別処理と一括処理のSVGが完全一致すること"""
        # 個別処理
        single_svg = _run_single_render(code)

        # 一括処理
        batch_payload = [{"id": f"test_{label}", "code": code, "theme": "default"}]
        batch_result = _run_batch_render(batch_payload)
        assert (
            batch_result.returncode == 0
        ), f"--batch-render失敗: {batch_result.stderr}"
        batch_results = json.loads(batch_result.stdout)
        assert len(batch_results) == 1
        assert batch_results[0]["success"] is True
        batch_svg = batch_results[0]["svg"]

        # 完全一致を確認
        assert single_svg == batch_svg, (
            f"{label}ダイアグラムで一括処理と個別処理のSVGが不一致\n"
            f"個別: {single_svg[:100]}...\n"
            f"一括: {batch_svg[:100]}..."
        )


# ---------------------------------------------------------------------------
# T020: エッジケーステスト
# ---------------------------------------------------------------------------


class TestBatchRenderEdgeCases:
    """一括処理のエッジケーステスト（T020）"""

    @patch("mkdocs_mermaid_to_svg.image_generator.subprocess.run")
    def test_大規模ダイアグラムの処理(self, mock_run: MagicMock) -> None:
        """数千行規模のダイアグラムでも正常に処理されること"""
        # 1000ノードのフローチャートを生成
        lines = ["graph TD"]
        for i in range(1000):
            lines.append(f"  N{i}-->N{i + 1}")
        large_code = "\n".join(lines)

        mock_run.return_value = subprocess.CompletedProcess(
            args=[],
            returncode=0,
            stdout=json.dumps(
                [
                    {"id": "large", "success": True, "svg": "<svg>large</svg>"},
                ]
            ),
            stderr="",
        )
        renderer = _make_renderer()
        items = [
            BatchRenderItem(
                id="large",
                code=large_code,
                theme="default",
                output_path="/site/images/large.svg",
                page_file="page.md",
            )
        ]
        results = renderer.batch_render(items)

        assert len(results) == 1
        assert results[0].success is True
        # 入力ペイロードにフルコードが渡されていることを確認
        input_payload = json.loads(mock_run.call_args[1]["input"])
        assert len(input_payload[0]["code"].split("\n")) == 1001

    @patch("mkdocs_mermaid_to_svg.image_generator.subprocess.run")
    def test_多数のダイアグラムの一括処理(self, mock_run: MagicMock) -> None:
        """50件のダイアグラムを1回のプロセスで処理できること"""
        count = 50
        mock_results = [
            {"id": f"item_{i}", "success": True, "svg": f"<svg>{i}</svg>"}
            for i in range(count)
        ]
        mock_run.return_value = subprocess.CompletedProcess(
            args=[],
            returncode=0,
            stdout=json.dumps(mock_results),
            stderr="",
        )
        renderer = _make_renderer()
        items = _make_items(count)
        results = renderer.batch_render(items)

        assert len(results) == count
        assert all(r.success for r in results)
        # subprocessは1回だけ呼ばれること
        mock_run.assert_called_once()
