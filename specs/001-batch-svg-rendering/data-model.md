# Data Model: Beautiful-Mermaid一括SVG生成

**Feature**: 001-batch-svg-rendering
**Date**: 2026-01-31

## Entities

### BatchRenderItem

一括処理の個別リクエスト項目。`on_page_markdown`フェーズで収集される。

| Field | Type | Description |
|-------|------|-------------|
| `id` | `str` | ダイアグラムの一意識別子（ファイル名から導出、例: `page_mermaid_0_abc12345`） |
| `code` | `str` | Mermaidダイアグラムのソースコード |
| `theme` | `str` | テーマ名（`default`, `dark`等）。ブロック属性によるオーバーライドを反映済み |
| `output_path` | `str` | SVGファイルの書き出し先パス（ビルド出力ディレクトリ内の絶対パス） |
| `page_file` | `str` | ソースページのファイルパス（`docs/`からの相対パス。エラー報告用） |

**Validation rules**:
- `id`は空文字不可
- `code`は空文字不可（空のMermaidコードは収集段階で除外済み）
- `output_path`は絶対パスであること

### BatchRenderResult

一括処理の個別結果。Node.jsランナーから返される。

| Field | Type | Description |
|-------|------|-------------|
| `id` | `str` | リクエストの`id`と対応する識別子 |
| `success` | `bool` | レンダリング成功/失敗 |
| `svg` | `str \| None` | 成功時のSVGコンテンツ。失敗時は`None` |
| `error` | `str \| None` | 失敗時のエラーメッセージ。成功時は`None` |

**Validation rules**:
- `success=True`の場合、`svg`は非空文字列であること
- `success=False`の場合、`error`は非空文字列であること
- `id`はリクエストの`id`と1:1で対応すること

### BatchRenderRequest（集約）

一括処理全体のリクエスト。プラグインレベルで管理される。

| Field | Type | Description |
|-------|------|-------------|
| `items` | `list[BatchRenderItem]` | 処理対象のダイアグラム一覧 |

**State transitions**:
```
Empty → Collecting（on_page_markdown中）→ Ready（全ページ処理完了）→ Rendered（on_post_build完了）
```

**Lifecycle**:
1. `on_files`: 空のリクエストを初期化
2. `on_page_markdown`: beautiful-mermaid対応ダイアグラムを`items`に追加
3. `on_post_build`: 全`items`を一括レンダリング、結果をファイルに書き出し

## Relationships

```
Plugin (1) ──manages──> BatchRenderRequest (1)
BatchRenderRequest (1) ──contains──> BatchRenderItem (0..N)
BatchRenderItem (1) ──produces──> BatchRenderResult (1)
BatchRenderResult (success=false) ──triggers──> mmdc fallback (individual)
```

## Node.js Runner Protocol

### Input（stdin）
```json
[
  {"code": "graph TD\n  A-->B", "theme": "default", "id": "index_mermaid_0_abc12345"},
  {"code": "sequenceDiagram\n  A->>B: msg", "theme": "dark", "id": "guide_mermaid_0_def67890"}
]
```

### Output（stdout）
```json
[
  {"id": "index_mermaid_0_abc12345", "success": true, "svg": "<svg>...</svg>"},
  {"id": "guide_mermaid_0_def67890", "success": true, "svg": "<svg>...</svg>"}
]
```

### Error case（個別失敗）
```json
[
  {"id": "index_mermaid_0_abc12345", "success": true, "svg": "<svg>...</svg>"},
  {"id": "guide_mermaid_0_def67890", "success": false, "error": "Parse error in mermaid code"}
]
```

### Error case（プロセスクラッシュ）
- exit code ≠ 0 かつ stdout が有効なJSON配列でない場合
- Python側は `MermaidCLIError` を送出し、ビルドを中断する
