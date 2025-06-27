# 設定オプション

## 最小構成（推奨）

プラグインは適切なデフォルト値を持っているため、最小構成で動作可能です：

```yaml
# mkdocs.yml
plugins:
  - mermaid-to-image  # これだけで動作します！
```

## 基本設定

### プラグイン設定例

```yaml
# mkdocs.yml
plugins:
  - search:
      lang: ja

  # Mermaid前処理プラグイン（カスタマイズ版）
  - mermaid-to-image:
      enabled: true                    # プラグイン有効化（デフォルト: true）
      output_dir: assets/images        # 画像出力ディレクトリ（デフォルト: assets/images）
      image_format: png               # 画像フォーマット（デフォルト: png）
      theme: default                  # Mermaidテーマ（デフォルト: default）
      background_color: white         # 背景色（デフォルト: white）
      width: 800                      # 画像幅（デフォルト: 800）
      height: 600                     # 画像高さ（デフォルト: 600）
      scale: 1.0                      # スケール（デフォルト: 1.0）
      cache_enabled: true             # キャッシュ機能（デフォルト: true）
      preserve_original: false        # 元のコード保持（デフォルト: false）
      error_on_fail: false           # エラー時の動作（デフォルト: false）
      log_level: INFO                 # ログレベル（デフォルト: INFO）

  # PDF生成プラグイン
  - with-pdf:
      author: 作成者名
      copyright: 2024 プロジェクト名
      cover: true                     # 表紙生成
      cover_title: ドキュメントタイトル
      cover_subtitle: サブタイトル
      output_path: document.pdf       # PDF出力パス
```

## 基本設定オプション

| オプション | 型 | デフォルト | 説明 |
|-----------|---|-----------|------|
| `enabled` | bool | `true` | プラグインの有効/無効 |
| `output_dir` | str | `assets/images` | 画像出力ディレクトリ |
| `image_format` | str | `png` | 画像フォーマット（png/svg） |
| `theme` | str | `default` | Mermaidテーマ |
| `width` | int | `800` | 画像幅（px） |
| `height` | int | `600` | 画像高さ（px） |

利用可能なテーマ: default, dark, forest, neutral

## 高度な設定オプション

| オプション | 型 | デフォルト | 説明 |
|-----------|---|-----------|------|
| `mmdc_path` | str | `mmdc` | Mermaid CLIパス |
| `background_color` | str | `white` | 背景色 |
| `scale` | float | `1.0` | スケール倍率 |
| `cache_enabled` | bool | `true` | キャッシュ機能 |
| `preserve_original` | bool | `false` | 元コード保持 |
| `error_on_fail` | bool | `false` | エラー時停止 |
| `log_level` | str | `INFO` | ログレベル |

利用可能なログレベル: DEBUG, INFO, WARNING, ERROR

## オプション設定

以下の設定はオプションで、未指定の場合は無効化されます：

| オプション | 型 | デフォルト | 説明 |
|-----------|---|-----------|------|
| `mermaid_config` | str | `null` | Mermaid設定ファイルのパス |
| `css_file` | str | `null` | カスタムCSSファイルのパス |
| `puppeteer_config` | str | `null` | Puppeteer設定ファイルのパス |
| `temp_dir` | str | `null` | 一時ディレクトリのパス |
| `cache_dir` | str | `.mermaid_cache` | キャッシュディレクトリのパス |

## 詳細設定

### 拡張設定
```yaml
plugins:
  - mermaid-to-image:
      css_file: custom/mermaid.css
      puppeteer_config: config/puppeteer.json
      mermaid_config: config/mermaid.json
      temp_dir: /tmp/mermaid
      cache_dir: .mermaid_cache
```

## カスタムテーマの作成

### Mermaid設定ファイル例（mermaid-config.json）

```json
{
  "theme": "dark",
  "themeVariables": {
    "primaryColor": "#ff6b6b",
    "primaryTextColor": "#ffffff",
    "primaryBorderColor": "#ff6b6b",
    "lineColor": "#ffffff"
  },
  "flowchart": {
    "useMaxWidth": false,
    "htmlLabels": true
  }
}
```

### Puppeteer設定ファイル例（puppeteer-config.json）

```json
{
  "args": [
    "--no-sandbox",
    "--disable-setuid-sandbox",
    "--disable-dev-shm-usage"
  ],
  "headless": true,
  "timeout": 30000
}
```

## 環境変数

以下の環境変数でデフォルト設定を上書きできます：

```bash
export MERMAID_CLI_PATH=/usr/local/bin/mmdc
export MERMAID_THEME=dark
export MERMAID_OUTPUT_DIR=custom/images
```

## 設定の優先順位

設定の適用優先順位は以下の通りです：

1. mkdocs.ymlのプラグイン設定
2. 環境変数
3. デフォルト値

## PDF生成との連携

PDF生成プラグインとの連携設定例：

```yaml
plugins:
  - mermaid-to-image:
      enabled: true
      output_dir: assets/images
      image_format: png

  - with-pdf:
      author: 作成者名
      copyright: 2024 プロジェクト名
      cover: true
      cover_title: ドキュメントタイトル
      output_path: document.pdf
      # 画像パスを正しく解決
      exclude_pages:
        - 'exclude-from-pdf'
```
