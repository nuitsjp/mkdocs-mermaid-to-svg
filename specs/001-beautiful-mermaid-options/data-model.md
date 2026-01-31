# Data Model: beautiful-mermaidレンダリングオプション

**Date**: 2026-01-31 | **Feature**: 001-beautiful-mermaid-options

## エンティティ定義

### BeautifulMermaidOptions（設定値の集合）

プラグイン設定からbeautiful-mermaidへ渡されるレンダリングオプションの論理モデル。

| フィールド名（plugin） | フィールド名（beautiful-mermaid） | 型 | デフォルト | 説明 |
|----------------------|-------------------------------|------|----------|------|
| `bg` | `bg` | str (色コード) | なし（beautiful-mermaid依存: `#FFFFFF`） | 背景色 |
| `fg` | `fg` | str (色コード) | なし（beautiful-mermaid依存: `#27272A`） | 前景色・テキスト色 |
| `line` | `line` | str (色コード) | なし | エッジ・コネクタ色 |
| `accent` | `accent` | str (色コード) | なし | 矢印・ハイライト色 |
| `muted` | `muted` | str (色コード) | なし | セカンダリテキスト・ラベル色 |
| `surface` | `surface` | str (色コード) | なし | ノード・ボックス塗り色 |
| `border` | `border` | str (色コード) | なし | ノード・グループ枠線色 |
| `font` | `font` | str | なし（beautiful-mermaid依存: `Inter`） | フォントファミリー |
| `padding` | `padding` | int | なし（beautiful-mermaid依存: `40`） | キャンバスパディング（px） |
| `node_spacing` | `nodeSpacing` | int | なし（beautiful-mermaid依存: `24`） | ノード間水平間隔（px） |
| `layer_spacing` | `layerSpacing` | int | なし（beautiful-mermaid依存: `40`） | レイヤー間垂直間隔（px） |
| `transparent` | `transparent` | bool | なし（beautiful-mermaid依存: `false`） | 透過背景 |

**備考**: プラグイン側でデフォルト値を持たず、未指定のオプションはペイロードに含めない。beautiful-mermaid側の内部デフォルトに委ねる。

### theme設定の拡張

| 値の種類 | 例 | 対象レンダラー |
|---------|-----|--------------|
| mmdc標準テーマ | `default`, `dark`, `forest`, `neutral` | mmdc |
| beautiful-mermaid名前付きテーマ | `tokyo-night`, `catppuccin-mocha`, `nord`, `dracula`, `github-light`, `github-dark`, `solarized-light`, `solarized-dark`, `one-dark`, `zinc-dark`, `tokyo-night-storm`, `tokyo-night-light`, `catppuccin-latte`, `nord-light` | beautiful-mermaid |

### オプション優先順位

```
beautiful-mermaidデフォルト
  ↓ 上書き
名前付きテーマパレット（theme設定で指定）
  ↓ 上書き
グローバル個別オプション（mkdocs.ymlの各キー）
  ↓ 上書き
ブロック単位属性（```mermaid {key: value}）
```

### BatchRenderItem拡張

既存の`BatchRenderItem`データクラスにオプションフィールドを追加。

| フィールド | 型 | 既存/新規 | 説明 |
|-----------|-----|---------|------|
| `id` | str | 既存 | レンダリングID |
| `code` | str | 既存 | Mermaidコード |
| `theme` | str | 既存 | テーマ名 |
| `output_path` | str | 既存 | SVG出力パス |
| `page_file` | str | 既存 | ページファイルパス |
| `options` | Optional[Dict[str, Any]] | **新規** | マージ済みレンダリングオプション（camelCase変換済み） |

### ペイロードJSON構造

**単一レンダリング（--render）**:
```json
{
  "code": "graph TD; A-->B",
  "theme": "tokyo-night",
  "options": {
    "bg": "#1a1a2e",
    "font": "Noto Sans JP",
    "padding": 50,
    "nodeSpacing": 30
  }
}
```

**バッチレンダリング（--batch-render）**:
```json
[
  {
    "code": "graph TD; A-->B",
    "theme": "default",
    "id": "diagram-1",
    "options": {
      "transparent": true
    }
  },
  {
    "code": "sequenceDiagram; A->>B: hello",
    "theme": "nord",
    "id": "diagram-2",
    "options": {}
  }
]
```

## コンテンツハッシュ拡張

SVGファイル名のMD5ハッシュ入力にオプションを追加:

```
hash_input = mermaid_code + theme + sorted_options_json
```

`sorted_options_json`はオプション辞書をキーでソートしてJSON文字列化したもの。オプションが空の場合は空文字列を使用し、既存のハッシュ結果との後方互換性を維持する。
