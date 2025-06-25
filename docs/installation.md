# インストールガイド

## 前提条件

### Node.js環境
```bash
# Node.js & npmのバージョン確認
node --version  # v16.0.0+ 必須
npm --version   # v8.0.0+ 必須
```

### Python環境
```bash
# Python環境確認
python3 --version  # 3.8+ 必須
pip3 --version
```

## Mermaid CLIのインストール

!!! warning "重要な依存関係"
    このプラグインはMermaid CLIを必要とします。インストールされていない場合、プラグインは動作しません。

```bash
# グローバルインストール
npm install -g @mermaid-js/mermaid-cli

# インストール確認
mmdc --version
```

!!! info "代替インストール方法"
    プロジェクト固有にインストールしたい場合:
    ```bash
    # package.jsonを使用
    npm install
    # または直接インストール
    npm install @mermaid-js/mermaid-cli
    ```

## Pythonパッケージのインストール

### 基本パッケージ
```bash
# MkDocsとMaterial テーマ
pip install mkdocs mkdocs-material

# PDF生成プラグイン
pip install mkdocs-with-pdf
```

## プラグインのインストール

### 通常インストール（将来のPyPI公開後）
```bash
pip install mkdocs-mermaid-to-image
```

### 開発版インストール
```bash
# プロジェクトルートから
pip install -e .
```

### PATHの設定（必要に応じて）
```bash
export PATH=$HOME/.local/bin:$PATH
```

## 環境構築チェックリスト

- [ ] Node.js (v16.0.0+) インストール済み
- [ ] Python (3.8+) インストール済み
- [ ] Mermaid CLI インストール済み
- [ ] MkDocs & Material インストール済み
- [ ] PDF プラグインインストール済み
- [ ] プラグイン設定完了

## 開発環境セットアップ

開発に参加する場合は、以下の手順で環境をセットアップしてください。

### 1. リポジトリクローン
```bash
git clone https://github.com/nuitsjp/mkdocs-mermaid-to-image
cd mkdocs-mermaid-to-image
```

### 2. 仮想環境作成と有効化
```bash
# 仮想環境作成
python -m venv venv

# 仮想環境有効化
source venv/bin/activate  # Linux/Mac
# venv\Scripts\activate   # Windows
```

### 3. 開発依存関係インストール
```bash
# 開発モードでインストール（依存関係も含む）
pip install -e .[dev]

# または、個別にインストール
pip install -r requirements.txt
pip install pytest pytest-cov black flake8 mypy
```

## よくある問題

### Mermaid CLI not found
```bash
# エラー: mmdc command not found
# 解決: Mermaid CLIをインストール
npm install -g @mermaid-js/mermaid-cli

# パス確認
which mmdc
export PATH=$HOME/.local/bin:$PATH
```

### 権限エラー
```bash
# エラー: Permission denied
# 解決1: 権限確認
chmod +x $(which mmdc)

# 解決2: 一時ディレクトリ作成
mkdir -p /tmp/mermaid
```

### PDF生成失敗
```bash
# エラー: PDF generation failed
# 解決: WeasyPrintの依存関係インストール
pip install weasyprint

# システム依存関係（Ubuntu/Debian）
apt-get install python3-cffi python3-brotli libpango-1.0-0 libpangoft2-1.0-0
```
