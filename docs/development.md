# 開発ガイド

このドキュメントは `mkdocs-mermaid-to-image` プラグインの開発に参加するための総合的なガイドです。

## はじめに

このプラグインは、MkDocsドキュメント内のMermaidダイアグラムを静的画像（PNG/SVG）に変換し、PDF出力やオフライン表示を可能にすることを目的としています。

開発に参加したい方は、このガイドに従って環境をセットアップし、開発フローを理解してください。

## 開発環境のセットアップ

### 1. 前提条件

開発を始める前に、以下のツールがインストールされていることを確認してください。

- **Python**: 3.9以上
- **Node.js**: 16以上（Mermaid CLIの実行に必要）
- **uv**: 高速なPythonパッケージインストーラ（推奨）
- **Git**: バージョン管理システム

### 2. クイックスタート

```bash
# 1. リポジトリをクローン
git clone https://github.com/nuitsjp/mkdocs-mermaid-to-image.git
cd mkdocs-mermaid-to-image

# 2. Mermaid CLIをグローバルインストール
npm install -g @mermaid-js/mermaid-cli

# 3. 開発環境をセットアップ（uvを使用）
# これにより、編集可能モードでプラグインがインストールされ、
# 開発用の依存関係もすべて導入されます。
uv sync --all-extras

# 4. pre-commitフックをインストール
# これにより、コミット時に自動でコード品質チェックが実行されます。
uv run pre-commit install
```

### 3. 開発サーバーの起動

開発中は、MkDocsの組み込みサーバーを使用すると、変更をリアルタイムで確認できます。

```bash
# 開発サーバーを起動（ホットリロード対応）
uv run mkdocs serve
```

ブラウザで `http://127.0.0.1:8000` を開くと、ドキュメントサイトが表示されます。

