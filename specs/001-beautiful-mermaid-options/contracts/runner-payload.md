# Contract: beautiful_mermaid_runner.mjs ペイロードスキーマ

**Date**: 2026-01-31 | **Feature**: 001-beautiful-mermaid-options

## 単一レンダリング（--render）

stdin経由で受け取るJSONペイロード。

```json
{
  "code": "<Mermaidコード文字列>",
  "theme": "<テーマ名文字列>",
  "options": {
    "bg": "<色コード>",
    "fg": "<色コード>",
    "line": "<色コード>",
    "accent": "<色コード>",
    "muted": "<色コード>",
    "surface": "<色コード>",
    "border": "<色コード>",
    "font": "<フォントファミリー名>",
    "padding": "<正の整数>",
    "nodeSpacing": "<正の整数>",
    "layerSpacing": "<正の整数>",
    "transparent": "<boolean>"
  }
}
```

- `code`: 必須
- `theme`: 必須（デフォルト: `"default"`）
- `options`: オプション（省略時は空オブジェクトとして扱う）
- `options`内の各キー: すべてオプション（指定されたもののみマージ）

### マージロジック（ランナー内）

```
resolvedTheme = resolveTheme(payload.theme)  // テーマ名 → DiagramColors
mergedOptions = { ...resolvedTheme, ...(payload.options || {}) }
svg = renderMermaid(payload.code, mergedOptions)
```

## バッチレンダリング（--batch-render）

stdin経由で受け取るJSON配列。

```json
[
  {
    "code": "<Mermaidコード文字列>",
    "theme": "<テーマ名文字列>",
    "id": "<一意識別子>",
    "options": { ... }
  }
]
```

- 各アイテムのフィールドは単一レンダリングと同一
- `id`: バッチ内で必須（結果の照合に使用）
- `options`: アイテムごとに異なるオプションを指定可能

### 応答フォーマット（変更なし）

既存の応答フォーマット（stdout JSON）は変更しない。
