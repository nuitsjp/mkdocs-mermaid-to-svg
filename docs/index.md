# MkDocs Mermaid to Image Plugin

[![Python](https://img.shields.io/badge/python-3.8+-blue.svg)](https://python.org/downloads/)
[![MkDocs](https://img.shields.io/badge/mkdocs-1.4+-green.svg)](https://mkdocs.org/)
[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

**MkDocs環境でMermaidダイアグラムを静的画像として事前レンダリングし、PDF出力に対応させるプラグインです。**

- [Sample PDF](MkDocs-Mermaid-to-Image.pdf)

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
./scripts/setup.sh
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
pip install -e .
```

## 💡 サンプル

このプラグインを使用すると、Mermaidダイアグラムが自動的に静的画像に変換されます：

```mermaid
graph LR
    A[Markdown] --> B[MkDocs Plugin]
    B --> C[Mermaid CLI]
    C --> D[Static Image]
    D --> E[PDF Ready]
```

複雑なフローチャートも対応：

```mermaid
flowchart TD
    Start([開始]) --> Input[Mermaidコード]
    Input --> Process{処理}
    Process -->|成功| Output[PNG/SVG画像]
    Process -->|失敗| Error[エラーログ]
    Output --> Cache[(キャッシュ)]
    Cache --> Build[サイトビルド]
    Build --> End([完了])
    Error --> End
```
