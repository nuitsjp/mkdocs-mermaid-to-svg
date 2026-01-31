# Contract: mkdocs.yml プラグイン設定スキーマ

**Date**: 2026-01-31 | **Feature**: 001-beautiful-mermaid-options

## 設定インターフェース

ユーザーが`mkdocs.yml`で指定する設定の契約定義。

### 設定例

```yaml
plugins:
  - mermaid_to_svg:
      renderer: auto
      theme: tokyo-night              # 既存設定を拡張（mmdc + beautiful-mermaid テーマ名）
      # beautiful-mermaid レンダリングオプション（すべてオプション）
      beautiful_mermaid_bg: "#1a1a2e"
      beautiful_mermaid_fg: "#e0e0e0"
      beautiful_mermaid_line: "#4a9eff"
      beautiful_mermaid_accent: "#ff6b6b"
      beautiful_mermaid_muted: "#888888"
      beautiful_mermaid_surface: "#2a2a3e"
      beautiful_mermaid_border: "#3a3a4e"
      beautiful_mermaid_font: "Noto Sans JP"
      beautiful_mermaid_padding: 50
      beautiful_mermaid_node_spacing: 30
      beautiful_mermaid_layer_spacing: 50
      beautiful_mermaid_transparent: false
```

### 設定キー定義

| キー名 | 型 | 必須 | デフォルト | バリデーション |
|--------|-----|------|----------|--------------|
| `theme` | string | いいえ | `"default"` | 自由文字列（不正値はランタイムフォールバック） |
| `beautiful_mermaid_bg` | string | いいえ | なし | CSS色コード形式（省略時はbeautiful-mermaidデフォルト） |
| `beautiful_mermaid_fg` | string | いいえ | なし | CSS色コード形式 |
| `beautiful_mermaid_line` | string | いいえ | なし | CSS色コード形式 |
| `beautiful_mermaid_accent` | string | いいえ | なし | CSS色コード形式 |
| `beautiful_mermaid_muted` | string | いいえ | なし | CSS色コード形式 |
| `beautiful_mermaid_surface` | string | いいえ | なし | CSS色コード形式 |
| `beautiful_mermaid_border` | string | いいえ | なし | CSS色コード形式 |
| `beautiful_mermaid_font` | string | いいえ | なし | フォントファミリー名 |
| `beautiful_mermaid_padding` | integer | いいえ | なし | 正の整数（px） |
| `beautiful_mermaid_node_spacing` | integer | いいえ | なし | 正の整数（px） |
| `beautiful_mermaid_layer_spacing` | integer | いいえ | なし | 正の整数（px） |
| `beautiful_mermaid_transparent` | boolean | いいえ | なし | true/false |

### 後方互換性

- 上記キーがすべて未設定の場合、動作は変更前と同一
- 既存の`theme`設定値（`default`, `dark`, `forest`, `neutral`）は引き続き動作する
- `renderer: mmdc`の場合、`beautiful_mermaid_*`キーは警告付きで無視される
