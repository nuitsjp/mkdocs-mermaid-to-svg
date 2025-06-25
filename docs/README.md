# MkDocs Mermaid to Image Plugin

[![Python](https://img.shields.io/badge/python-3.8+-blue.svg)](https://python.org/downloads/)
[![MkDocs](https://img.shields.io/badge/mkdocs-1.4+-green.svg)](https://mkdocs.org/)
[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

**MkDocs環境でMermaidダイアグラムを静的画像として事前レンダリングし、PDF出力に対応させるプラグインです。**

## ✨ 特徴

- MermaidダイアグラムをPNG/SVG画像として事前レンダリング
- PDF出力対応
- 標準テーマサポート
- キャッシュ機能による高速ビルド

## 🚀 クイックスタート

### 自動セットアップ（推奨）

```bash
git clone https://github.com/nuitsjp/mkdocs-mermaid-to-image
cd mkdocs-mermaid-to-image
./setup.sh
```

### 手動インストール

#### 1. 依存関係のインストール
```bash
# Node.js環境（Mermaid CLI用）
npm install -g @mermaid-js/mermaid-cli

# Python環境
pip install mkdocs mkdocs-material
```

#### 2. プラグインのインストール
```bash
git clone https://github.com/nuitsjp/mkdocs-mermaid-to-image
cd mkdocs-mermaid-to-image
pip install -e .
```

### 基本設定

```yaml
plugins:
  - mermaid-to-image:
      enabled: true
      output_dir: assets/images
  - with-pdf:
      output_path: document.pdf
```

## 📖 ドキュメント

詳細なドキュメントは[こちら](https://nuitsjp.github.io/mkdocs-mermaid-to-image/)をご覧ください。

- [インストールガイド](https://nuitsjp.github.io/mkdocs-mermaid-to-image/installation/)
- [設定オプション](https://nuitsjp.github.io/mkdocs-mermaid-to-image/configuration/)
- [使用方法](https://nuitsjp.github.io/mkdocs-mermaid-to-image/usage/)
- [トラブルシューティング](https://nuitsjp.github.io/mkdocs-mermaid-to-image/troubleshooting/)

## 🤝 コントリビューション

コントリビューションを歓迎します！詳細は[コントリビューションガイド](https://nuitsjp.github.io/mkdocs-mermaid-to-image/contributing/)をご覧ください。

## 📄 ライセンス

このプロジェクトはMITライセンスの下で公開されています。詳細は [LICENSE](LICENSE) ファイルを参照してください。

---

**Made with ❤️ by nuitsjp**
