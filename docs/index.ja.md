# mkdocs-mermaid-to-svg

[![PyPI - Python Version][python-image]][pypi-link]
[![Linux Support][linux-image]](#requirements)
[![Windows Support][windows-image]](#requirements)

MermaidチャートをSVGイメージに変換するMkDocsプラグイン。

このプラグインはMermaidコードブロックを検出し、SVGイメージに置き換えます。これはPDF出力のようにJavaScriptをサポートしないフォーマットで特に有用です。

- [ドキュメント](https://thankful-beach-0f331f600.1.azurestaticapps.net/)

## 機能

- **SVG出力**: MermaidダイアグラムからSVGイメージを生成
- **PDF対応**: SVGイメージはPDFエクスポートで完璧に動作
- **自動変換**: すべてのMermaidコードブロックを自動的に検出し変換
- **設定可能**: Mermaidテーマとカスタム設定をサポート
- **環境制御**: 環境変数により条件付きで有効化可能

## 要件

このプラグインは事前に[Node.js](https://nodejs.org/)がインストールされている必要があります。

### Mermaid CLI

```bash
# Mermaid CLIをグローバルにインストール
npm install -g @mermaid-js/mermaid-cli

# またはプロジェクトごとにインストール
npm install @mermaid-js/mermaid-cli
```

### Puppeteer

```bash
# Puppeteerをインストール
npm install puppeteer

# Puppeteer用ブラウザをインストール（必須）
npx puppeteer browsers install chrome-headless-shell
```

## セットアップ

pipを使用してプラグインをインストール：

```bash
pip install mkdocs-mermaid-to-svg
```

`mkdocs.yml`でプラグインを有効化（PDF生成の推奨設定）：

```yaml
plugins:
  - mermaid-to-svg:
      # PDF互換性のためhtmlLabelsを無効化
      mermaid_config:
        htmlLabels: false
        flowchart:
          htmlLabels: false
        class:
          htmlLabels: false
  - to-pdf:  # PDF生成プラグインと組み合わせる場合
      enabled_if_env: ENABLE_PDF_EXPORT
```

### PDF互換性

`htmlLabels`が有効の場合、Mermaid CLIは`<foreignObject>`要素を含むHTMLを含むSVGファイルを生成します。PDF生成ツールはこれらのHTML要素を適切にレンダリングできず、テキストが消えてしまいます。

- **影響を受けるダイアグラム**: フローチャート、クラス図、テキストラベルを使用するその他のダイアグラム
- **影響を受けないダイアグラム**: シーケンス図は標準のSVGテキスト要素を使用し、PDFで正しく動作

## 設定

`mkdocs.yml`でプラグインの動作をカスタマイズできます。すべてのオプションは任意です：

### 条件付き有効化

PDF生成時のみプラグインを有効にするには、to-pdfプラグインと同じ環境変数を使用します：

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

実行方法：
```bash
ENABLE_PDF_EXPORT=1 mkdocs build
```

### 高度なオプション

```yaml
plugins:
  - mermaid-to-svg:
      mmdc_path: "mmdc"                   # Mermaid CLIのパス
      css_file: "custom-mermaid.css"      # カスタムCSSファイル
      puppeteer_config: "puppeteer.json"  # カスタムPuppeteer設定
      error_on_fail: false                # ダイアグラム生成エラー時も継続
      log_level: "INFO"                   # ログレベル (DEBUG, INFO, WARNING, ERROR)
      cleanup_generated_images: true      # ビルド後に生成イメージをクリーンアップ
```

## 設定オプション

| オプション | デフォルト | 説明 |
|-----------|----------|------|
| `enabled_if_env` | `None` | プラグインを条件付きで有効化する環境変数名 |
| `output_dir` | `"assets/images"` | 生成されるSVGファイルを保存するディレクトリ |
| `theme` | `"default"` | Mermaidテーマ (default, dark, forest, neutral) |
| `mmdc_path` | `"mmdc"` | `mmdc`実行ファイルのパス |
| `mermaid_config` | `None` | Mermaid設定辞書 |
| `css_file` | `None` | カスタムCSSファイルのパス |
| `puppeteer_config` | `None` | Puppeteer設定ファイルのパス |
| `error_on_fail` | `true` | ダイアグラム生成エラー時にビルドを停止 |
| `log_level` | `"INFO"` | ログレベル |
| `cleanup_generated_images` | `true` | ビルド後に生成イメージをクリーンアップ |

## PDF生成

このプラグインはPDF生成互換性を考慮して設計されています：

### なぜSVG？

- **ベクターフォーマット**: SVGイメージはあらゆる解像度で美しくスケール
- **テキスト保持**: SVGテキストはPDFで選択可能で検索可能
- **JS不要**: JavaScriptをサポートしないPDF生成ツールで動作

## 使用例

1. MarkdownにMermaidダイアグラムを書く：

   ````markdown
   ```mermaid
   graph TD
       A[開始] --> B{決定}
       B -->|はい| C[アクション1]
       B -->|いいえ| D[アクション2]
   ```
   ````

2. プラグインがビルド時に自動的にSVGイメージに変換：

   ```html
   <p><img alt="Mermaid Diagram" src="assets/images/diagram_123abc.svg" /></p>
   ```

3. PDFエクスポートでは、選択可能なテキストを含む鮮明でスケーラブルなダイアグラムが表示されます。

[pypi-link]: https://pypi.org/project/mkdocs-mermaid-to-svg/
[python-image]: https://img.shields.io/pypi/pyversions/mkdocs-mermaid-to-svg?logo=python&logoColor=aaaaaa&labelColor=333333
[linux-image]: https://img.shields.io/badge/Linux-supported-success?logo=linux&logoColor=white&labelColor=333333
[windows-image]: https://img.shields.io/badge/Windows-supported-success?logo=windows&logoColor=white&labelColor=333333
