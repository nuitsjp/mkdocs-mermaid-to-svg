# Implementation Plan: Beautiful-Mermaid一括SVG生成

**Branch**: `001-batch-svg-rendering` | **Date**: 2026-01-31 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/001-batch-svg-rendering/spec.md`

## Summary

現在beautiful-mermaidレンダラーはMermaidダイアグラムごとに個別にNode.jsプロセスを起動してSVGを生成している。この機能は、ビルド全体で対象ダイアグラムを収集し、`on_post_build`フェーズで1回のNode.jsプロセスにまとめて処理する2フェーズ構成に改修する。これによりNode.jsの起動オーバーヘッドを排除し、ビルド時間を短縮する。

## Technical Context

**Language/Version**: Python 3.9+ / JavaScript (Node.js ESM)
**Primary Dependencies**: MkDocs, beautiful-mermaid (npm), mermaid-cli (mmdc)
**Storage**: ファイルシステム（SVGファイルをビルド出力ディレクトリに書き出し）
**Testing**: pytest（unit / integration / property）、make test / make check-all
**Target Platform**: クロスプラットフォーム（Windows: `cmd /c`、Linux/macOS: direct）
**Project Type**: single（MkDocsプラグイン）
**Performance Goals**: Node.jsプロセス起動回数を1回に削減、ダイアグラム数に比例する線形増加の排除
**Constraints**: 既存のSVG出力との100%互換性、フォールバック動作の維持
**Scale/Scope**: 通常のドキュメントプロジェクト（数十〜数百ダイアグラム）

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Notes |
|-----------|--------|-------|
| I. コード品質 | ✅ PASS | mypy --strict、ruff、snake_case/CamelCase準拠で実装する |
| II. テスト基準 | ✅ PASS | TDD（Red-Green-Refactor）で実装。unit/integrationテストを追加 |
| III. UX一貫性 | ✅ PASS | serve時はスキップ、build時のみ一括処理。フォールバック維持 |
| IV. パフォーマンス | ✅ PASS | Node.js起動回数を1回に削減。ビルド時間の改善が目的そのもの |
| 品質ゲート | ✅ PASS | make check / make test / make check-security をすべて通過させる |

## Project Structure

### Documentation (this feature)

```text
specs/001-batch-svg-rendering/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
└── tasks.md             # Phase 2 output (/speckit.tasks command)
```

### Source Code (repository root)

```text
src/mkdocs_mermaid_to_svg/
├── plugin.py                    # on_page_markdown / on_post_build の変更
├── processor.py                 # 2フェーズ対応（収集フェーズ・レンダリングフェーズ）
├── image_generator.py           # BatchRenderer追加、BeautifulMermaidRenderer一括対応
├── mermaid_block.py             # 変更なし（既存のまま利用）
├── markdown_processor.py        # 変更なし
├── beautiful_mermaid_runner.mjs # --batch-render モード追加
├── exceptions.py                # BatchRenderingError追加
└── utils.py                     # 変更なし

tests/
├── unit/
│   ├── test_batch_renderer.py   # 一括レンダラーの単体テスト
│   ├── test_plugin.py           # 2フェーズ処理のプラグインテスト
│   └── test_image_generator.py  # 既存テスト拡張
└── integration/
    └── test_batch_integration.py # エンドツーエンドの一括処理テスト
```

**Structure Decision**: 既存のsrc構造を維持。新ファイルは追加せず、既存ファイルへの拡張で実装する（`beautiful_mermaid_runner.mjs`に`--batch-render`モード追加、`image_generator.py`にバッチ処理ロジック追加）。

## Design（Phase 1成果物）

### 変更概要

```
┌─────────────────────────────────────────────────────────────┐
│ on_files()                                                  │
│   - BatchRenderRequest を初期化（空リスト）                    │
│   - self.generated_images = [] (既存)                       │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│ on_page_markdown() × N ページ                               │
│                                                             │
│  1. extract_mermaid_blocks()                                │
│  2. 各ブロックを分類:                                        │
│     ├─ beautiful-mermaid対応 → BatchRenderItemに追加         │
│     │  Markdownは画像参照に書き換え（SVG未生成）              │
│     └─ mmdc対応 → 従来どおりその場でmmdc実行                  │
│  3. mmdc生成画像をFilesに登録                                │
│  4. 修正済みMarkdownを返す                                   │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│ on_post_build()                                             │
│                                                             │
│  1. BatchRenderRequestが空なら何もしない                      │
│  2. Node.js --batch-render を1回実行                         │
│     stdin: JSON配列 / stdout: JSON配列                      │
│  3. 成功分: SVGをビルド出力ディレクトリに書き出し             │
│  4. 失敗分: 個別にmmdcフォールバック                          │
│  5. プロセスクラッシュ: ビルドエラーで中断                    │
│  6. 画像総数をログ出力                                       │
│  7. クリーンアップ処理（既存）                                │
└─────────────────────────────────────────────────────────────┘
```

### 変更箇所の詳細設計

#### 1. `beautiful_mermaid_runner.mjs` — `--batch-render`モード追加

```javascript
// 新しいモード: --batch-render
// 入力: stdin経由のJSON配列
// 出力: stdout経由のJSON配列
if (mode === '--batch-render') {
  const items = JSON.parse(await readStdin())
  const results = []
  for (const item of items) {
    try {
      const theme = resolveTheme(item.theme)
      const svg = await renderMermaid(item.code, theme)
      results.push({ id: item.id, success: true, svg })
    } catch (err) {
      results.push({ id: item.id, success: false, error: err?.message ?? String(err) })
    }
  }
  process.stdout.write(JSON.stringify(results))
}
```

- 既存の`--render`モード、`--check`モードは変更しない
- テーマ解決ロジックを共通関数`resolveTheme()`に抽出する

#### 2. `image_generator.py` — `BeautifulMermaidRenderer`にバッチメソッド追加

```python
# 新規メソッド
def batch_render(self, items: list[BatchRenderItem]) -> list[BatchRenderResult]:
    """複数ダイアグラムを1回のNode.jsプロセスで一括レンダリング"""
    payload = [
        {"code": item.code, "theme": item.theme, "id": item.id}
        for item in items
    ]
    result = subprocess.run(
        ["node", str(self._runner_path()), "--batch-render"],
        input=json.dumps(payload),
        capture_output=True, text=True, check=False,
        cwd=str(Path.cwd()),
    )
    if result.returncode != 0:
        raise MermaidCLIError(...)

    raw_results = json.loads(result.stdout)
    return [BatchRenderResult(**r) for r in raw_results]
```

#### 3. `processor.py` — 収集モードの追加

```python
def process_page_collect_mode(
    self, page_file, markdown_content, output_dir, page_url, docs_dir,
    batch_items: list[BatchRenderItem],
) -> tuple[str, list[str]]:
    """収集モード: beautiful-mermaid対応ブロックをバッチに追加し、
    mmdc対応ブロックのみその場で処理する"""
    blocks = self.markdown_processor.extract_mermaid_blocks(markdown_content)
    # beautiful対応/非対応を分類
    # beautiful対応 → batch_itemsに追加、Markdown書き換え
    # 非対応 → 従来の_process_single_blockで即時処理
```

#### 4. `plugin.py` — 2フェーズ統合

```python
# on_files に追加
self.batch_items: list[BatchRenderItem] = []

# on_page_markdown を変更
# processor.process_page_collect_mode() を呼び出し、
# beautiful-mermaid対応ブロックはbatch_itemsに収集

# on_post_build に追加
# 1. batch_itemsが空でなければ一括レンダリング
# 2. 成功分をsite/ディレクトリに書き出し
# 3. 失敗分をmmdcフォールバック
```

### 参照ドキュメント

- [research.md](./research.md) — 設計判断の根拠と代替案
- [data-model.md](./data-model.md) — エンティティ定義とプロトコル仕様
- [quickstart.md](./quickstart.md) — 実装手順の概要

## Constitution Check（Phase 1後 再評価）

| Principle | Status | Notes |
|-----------|--------|-------|
| I. コード品質 | ✅ PASS | 既存のコード規約に従った設計。新規クラスはdataclassで最小限 |
| II. テスト基準 | ✅ PASS | TDDで各ステップをテスト。unit/integrationの両レベルで検証 |
| III. UX一貫性 | ✅ PASS | serve時は一切変更なし。build時のみ一括処理。出力SVGは同一 |
| IV. パフォーマンス | ✅ PASS | Node.js起動1回に削減。コンテンツハッシュキャッシュは維持 |
| 品質ゲート | ✅ PASS | make check-all / make test を全工程で実行 |

## Complexity Tracking

該当なし。Constitution違反はない。
