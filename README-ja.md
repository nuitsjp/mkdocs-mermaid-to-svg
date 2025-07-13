# mkdocs-mermaid-to-svg

[![PyPI - Python Version][python-image]][pypi-link]
[![Linux Support][linux-image]](#requirements)
[![Windows Support][windows-image]](#requirements)

MermaidチャートをSVG画像に変換するMkDocsプラグインです。

このプラグインはMermaidコードブロックを検出してSVG画像に置き換えます。JavaScriptをサポートしないPDF出力などの形式で特に有効です。

- [ドキュメント](https://thankful-beach-0f331f600.1.azurestaticapps.net/)

## 特徴

- **SVG出力**: Mermaid図表から高品質なSVG画像を生成
- **PDF対応**: SVG画像はPDFエクスポートで完全に動作
- **自動変換**: すべてのMermaidコードブロックを自動検出・変換
- **設定可能**: Mermaidテーマとカスタム設定に対応
- **環境制御**: 環境変数による条件付き有効化が可能

## 要件

このプラグインには[Node.js](https://nodejs.org/)が事前にインストールされている必要があります。

### Mermaid CLI

```bash
# Mermaid CLIをグローバルインストール
npm install -g @mermaid-js/mermaid-cli

# または、プロジェクトごとにインストール
npm install @mermaid-js/mermaid-cli
```

### Puppeteer

```bash
# Puppeteerをインストール
npm install puppeteer

# Puppeteer用ブラウザもインストール（必須）
npx puppeteer browsers install chrome-headless-shell
```

## セットアップ

pipでプラグインをインストール：

```bash
pip install mkdocs-mermaid-to-svg
```

`mkdocs.yml`でプラグインを有効化（PDF生成を考慮した推奨設定）：

```yaml
plugins:
  - mermaid-to-svg:
      # PDF生成時の互換性のためHTMLラベルを無効化
      mermaid_config:
        htmlLabels: false
        flowchart:
          htmlLabels: false
        class:
          htmlLabels: false
  - to-pdf:  # PDF生成プラグインと併用する場合
      enabled_if_env: ENABLE_PDF_EXPORT
```

### PDF互換性について

`htmlLabels`が有効な場合、Mermaid CLIはHTMLを含む`<foreignObject>`要素を持つSVGファイルを生成します。PDF生成ツールはこれらのHTML要素を正しくレンダリングできないため、テキストが表示されません。

- **影響を受ける図表**: フローチャート、クラス図など、テキストラベルを使用する図表
- **影響を受けない図表**: シーケンス図は標準のSVGテキスト要素を使用するため、PDFでも正常に動作

## 設定

`mkdocs.yml`でプラグインの動作をカスタマイズできます。すべてのオプションは任意です：

### 条件付き有効化

PDF生成時のみプラグインを有効化したい場合は、to-pdfプラグインと同じ環境変数を使用：

```yaml
plugins:
  - mermaid-to-svg:
      enabled_if_env: "ENABLE_PDF_EXPORT"  # to-pdfプラグインと同じ環境変数を使用
      mermaid_config:
        htmlLabels: false
        flowchart:
          htmlLabels: false
        class:
          htmlLabels: false
  - to-pdf:
      enabled_if_env: ENABLE_PDF_EXPORT
```

実行時：
```bash
ENABLE_PDF_EXPORT=1 mkdocs build
```

### 高度なオプション

```yaml
plugins:
  - mermaid-to-svg:
      mmdc_path: "mmdc"                   # Mermaid CLIへのパス
      css_file: "custom-mermaid.css"      # カスタムCSSファイル
      puppeteer_config: "puppeteer.json"  # カスタムPuppeteer設定
      error_on_fail: false                # 図表生成エラー時も継続
      log_level: "INFO"                   # ログレベル (DEBUG, INFO, WARNING, ERROR)
      cleanup_generated_images: true      # ビルド後に生成された画像をクリーンアップ
```

## 設定オプション

| オプション | デフォルト | 説明 |
|--------|---------|-------------|
| `enabled_if_env` | `None` | プラグインを条件付きで有効にする環境変数名 |
| `output_dir` | `"assets/images"` | 生成されたSVGファイルを保存するディレクトリ |
| `theme` | `"default"` | Mermaidテーマ (default, dark, forest, neutral) |
| `mmdc_path` | `"mmdc"` | `mmdc`実行ファイルへのパス |
| `mermaid_config` | `None` | Mermaid設定辞書 |
| `css_file` | `None` | カスタムCSSファイルへのパス |
| `puppeteer_config` | `None` | Puppeteer設定ファイルへのパス |
| `error_on_fail` | `true` | 図表生成エラー時にビルドを停止 |
| `log_level` | `"INFO"` | ログレベル |
| `cleanup_generated_images` | `true` | ビルド後に生成された画像をクリーンアップ |

## PDF生成

このプラグインはPDF生成との互換性を重視して設計されています：

### なぜSVG？

- **ベクター形式**: SVG画像はあらゆる解像度で美しくスケーリング
- **テキスト保持**: SVGテキストはPDF内で選択・検索が可能
- **JS不要**: JavaScriptをサポートしないPDF生成ツールでも動作

## 使用例

1. MarkdownでMermaid図表を記述：

   ````markdown
   ```mermaid
   graph TD
       A[開始] --> B{判定}
       B -->|はい| C[アクション1]
       B -->|いいえ| D[アクション2]
   ```
   ````

2. ビルド時にプラグインが自動的にSVG画像に変換：

   ```html
   <p><img alt="Mermaid Diagram" src="assets/images/diagram_123abc.svg" /></p>
   ```

3. PDFエクスポート時に、選択可能なテキストを持つ高解像度でスケーラブルな図表が出力されます。

[pypi-link]: https://pypi.org/project/mkdocs-mermaid-to-svg/
[python-image]: https://img.shields.io/pypi/pyversions/mkdocs-mermaid-to-svg?logo=python&logoColor=aaaaaa&labelColor=333333
[linux-image]: https://img.shields.io/badge/Linux-supported-success?logo=linux&logoColor=white&labelColor=333333
[windows-image]: https://img.shields.io/badge/Windows-supported-success?logo=windows&logoColor=white&labelColor=333333
