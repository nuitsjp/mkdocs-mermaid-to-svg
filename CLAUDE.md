# CLAUDE.md

このファイルは、Claude Code（claude.ai/code）がこのリポジトリのコードを扱う際のガイダンスを提供します。

## プロジェクト概要

**mkdocs-mermaid-to-image** は、Markdownドキュメント内のMermaid.jsダイアグラムをビルド時に静的画像（PNG/SVG）へ変換するMkDocsプラグインです。これにより、`mkdocs-with-pdf` のようなPDF出力プラグインとの互換性が実現し、オフラインでのダイアグラム閲覧も可能になります。

**主な特徴:**
- ビルド時にMermaidダイアグラムを静的画像へ変換
- すべてのMermaidダイアグラムタイプ（フローチャート、シーケンス、クラス図など）に対応
- MkDocsのPDF生成プラグインと完全互換
- テーマ変更や出力フォーマットのカスタマイズが可能
- 効率的なビルドのためのインテリジェントなキャッシュシステム
- 包括的なエラーハンドリングと優雅なフォールバック

## アーキテクチャ概要

**MkDocsプラグイン統合:**
- MkDocsのライフサイクルフックを持つ `BasePlugin` を実装
- **plugin.py**: メインプラグインクラス（`MermaidToImagePlugin`）と設定管理
- **processor.py**: ダイアグラム変換を統括するコア処理エンジン
- **markdown_processor.py**: Markdownを解析しMermaidブロックを特定
- **image_generator.py**: Mermaid CLIによる画像生成を担当
- **mermaid_block.py**: Mermaidダイアグラム表現用データ構造
- **config.py**: プラグイン設定スキーマとバリデーション
- **utils.py**: ロギング、ファイル操作、ユーティリティ関数
- **exceptions.py**: カスタム例外階層

**処理フロー:**
1. `on_config` フックでプラグイン設定を検証
2. `on_page_markdown` フックで各ページのMarkdownを処理
3. Mermaidブロックを抽出し画像へ変換
4. 元のMermaid構文を画像参照に置換
5. 生成画像をキャッシュし次回ビルドに活用

## 技術スタック

- **言語**: Python 3.9+
- **主要依存**: MkDocs ≥1.4.0, mkdocs-material ≥8.0.0
- **画像処理**: Pillow ≥8.0.0, numpy ≥1.20.0
- **外部依存**: Node.js + `@mermaid-js/mermaid-cli`（mmdcコマンド）
- **パッケージ管理**: uv（最新のPythonパッケージマネージャ）
- **コード品質**: ruff（リント/フォーマット）, mypy（厳格な型チェック）
- **テスト**: pytest + hypothesis（プロパティベーステスト）
- **自動化**: pre-commitフック, GitHub Actions CI/CD

## 開発環境セットアップ

**クイックセットアップ:**
```bash
make setup  # scripts/setup.shによる自動セットアップ
```

**手動セットアップ:**
```bash
# 依存関係インストール
uv sync --all-extras

# pre-commitフックインストール
uv run pre-commit install

# Node.jsとMermaid CLIの確認
node --version
npx mmdc --version
```

## よく使う開発コマンド

**テスト:**
```bash
make test                    # 全テスト実行
make test-unit              # ユニットテストのみ
make test-integration       # 統合テストのみ
make test-cov               # カバレッジ付きテスト
```

**コード品質:**
```bash
make format                 # コードフォーマット（ruff format）
make lint                   # リント＆自動修正（ruff check --fix）
make typecheck              # 型チェック（mypy --strict）
make security               # セキュリティスキャン（bandit）
make audit                  # 依存脆弱性チェック
make check                  # すべての品質チェックを順次実行
```

**開発サーバー:**
```bash
uv run mkdocs serve         # 開発サーバー起動
uv run mkdocs build         # ドキュメントビルド
```

**依存管理:**
```bash
uv add package_name         # ランタイム依存追加
uv add --dev dev_package    # 開発依存追加
uv sync --all-extras        # すべての依存を同期
```

## プラグイン固有の開発上の注意

**1. 複数ランタイム環境:**
- Python（≥3.9）とNode.js（≥16）の両方が必要
- Mermaid CLI（mmdc）はnpmでグローバルインストール必須
- Windows/Unix両対応のパス処理

**2. MkDocsプラグインライフサイクル:**
- フック実装: `on_config`, `on_page_markdown`
- 設定バリデーションは `config_options` スキーマで
- エラー時もMkDocsビルドを中断しないこと

**3. 画像生成の課題:**
- ヘッドレスブラウザ依存（Mermaid CLI経由のPuppeteer）
- 一時ファイルの管理とクリーンアップ
- キャッシュの無効化戦略
- ダイアグラムタイプ間でのテーマ一貫性

**4. テスト戦略:**
- **ユニットテスト**（`tests/unit/`）: 個別コンポーネントのテスト
- **統合テスト**（`tests/integration/`）: MkDocsとのE2Eテスト
- **プロパティテスト**（`tests/property/`）: hypothesisによる入力検証
- **フィクスチャ**（`tests/fixtures/`）: サンプルMermaidファイルと期待出力

## 設定

**プラグイン設定スキーマ（config.py）:**
```python
# 主な設定項目
image_format: 'png' | 'svg'          # 出力フォーマット
theme: 'default' | 'dark' | 'forest' | 'neutral'
cache_enabled: bool                   # キャッシュ有効化
output_dir: str                       # 画像出力ディレクトリ
```

**MkDocsでのプラグインテスト:**
```yaml
# mkdocs.yml
plugins:
  - mermaid-to-image:
      image_format: 'png'
      theme: 'default'
      cache_enabled: true
```

## コード品質基準

**型チェック:**
- mypyのstrictモード＆完全な型ヒント
- すべての公開APIに型アノテーション必須
- 前方参照には `from __future__ import annotations` を使用

**テスト要件:**
- 最低90%のコードカバレッジ
- テスト命名規則: `test_<scenario>_<expected_result>`
- 入力バリデーションはプロパティベーステスト
- 実際のMkDocsビルドによる統合テスト

**エラーハンドリング:**
- `exceptions.py` にカスタム例外階層
- 画像生成失敗時も優雅にフォールバック
- 解決策付きの詳細なエラーメッセージ
- 適切なレベル（DEBUG, INFO, WARNING, ERROR）でのロギング

## トラブルシューティング

**よくある問題:**

1. **Mermaid CLIが見つからない:**
   ```bash
   npm install -g @mermaid-js/mermaid-cli
   ```

2. **Puppeteer/Chromiumの問題:**
   ```bash
   # Linux: 依存パッケージのインストール
   apt-get install -y libgtk-3-0 libx11-xcb1 libxcomposite1 libxdamage1 libxrandr2 libasound2 libpangocairo-1.0-0 libatk1.0-0
   ```

3. **pre-commitの失敗:**
   ```bash
   uv run pre-commit clean
   uv run pre-commit install
   ```

## GitHub運用

**プルリクエスト作成:**
```bash
make pr TITLE="Feature: Add new theme support" BODY="Description" LABEL="enhancement"
```

**Issue作成:**
```bash
make issue TITLE="Bug: Image generation fails" BODY="Details" LABEL="bug"
```

**ブランチ命名規則:**
- 機能: `feature/theme-support`
- バグ: `fix/image-generation-error`
- ドキュメント: `docs/update-readme`

## パフォーマンス考慮

- 画像生成はCPU負荷が高い（ヘッドレスブラウザレンダリング）
- キャッシュシステムで再生成のオーバーヘッドを削減
- 大きなダイアグラムはタイムアウト値の増加が必要な場合あり
- 複数ダイアグラムの並列処理も検討

## エントリポイント

プラグインはsetuptoolsエントリポイントで登録されます:
```python
# pyproject.toml
[project.entry-points."mkdocs.plugins"]
mermaid-to-image = "mkdocs_mermaid_to_image.plugin:MermaidToImagePlugin"
```

## ドキュメント

- **docs/**: MkDocsドキュメント（プラグイン自体で自己文書化）
- **README.md**: インストールと基本的な使い方
- **docs/development.md**: 詳細な開発ガイド
- **docs/architecture.md**: 技術アーキテクチャ詳細
