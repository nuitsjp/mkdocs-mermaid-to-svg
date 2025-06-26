# 開発ガイド

このドキュメントでは、MkDocs Mermaid to Image Pluginの開発環境セットアップと開発手順について説明します。

## 開発環境のセットアップ

### 必要なツール

- **Python**: 3.9以上
- **Node.js**: 18以上（Mermaid CLI用）
- **UV**: 推奨パッケージマネージャー（または pip）
- **Git**: バージョン管理

### 環境構築手順

#### 1. リポジトリのクローン

```bash
git clone https://github.com/nuitsjp/mkdocs-mermaid-to-image.git
cd mkdocs-mermaid-to-image
```

#### 2. Mermaid CLIのインストール

```bash
npm install -g @mermaid-js/mermaid-cli
```

#### 3. Pythonパッケージの開発インストール

**UV使用（推奨）:**
```bash
# 開発依存関係を含めてインストール
uv add --dev --editable .

# 仮想環境が自動作成され、プラグインが開発モードでインストールされます
```

**pipを使用する場合:**
```bash
# 仮想環境を作成
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
# または
.venv\Scripts\activate     # Windows

# 開発依存関係を含めてインストール
pip install -e ".[dev]"
```

#### 4. pre-commitフックの設定

```bash
uv run pre-commit install
```

## 開発用コマンド

### ドキュメント関連

```bash
# 開発版でドキュメントをビルド
uv run mkdocs build

# 開発サーバーを起動（ホットリロード対応）
uv run mkdocs serve

# 特定のポートで起動
uv run mkdocs serve --dev-addr 127.0.0.1:8080
```

### テスト実行

```bash
# 全テスト実行
uv run pytest

# カバレッジ付きテスト
uv run pytest --cov=src/mkdocs_mermaid_to_image

# 特定のテストファイルのみ実行
uv run pytest tests/unit/test_plugin.py

# 詳細出力でテスト実行
uv run pytest -v

# 並列テスト実行（高速化）
uv run pytest -n auto
```

### コード品質チェック

```bash
# 全ての品質チェックを実行
uv run pre-commit run --all-files

# 個別チェック
uv run ruff check src/                    # リント
uv run ruff format src/                   # フォーマット
uv run mypy src/                          # 型チェック
uv run bandit -r src/                     # セキュリティチェック
```

### ベンチマーク・パフォーマンス

```bash
# ベンチマークテスト実行
uv run pytest tests/ -m "not slow"

# パフォーマンステスト実行
uv run pytest tests/ -m "slow"

# プロファイリング
uv run python -m cProfile -o profile.stats scripts/profile_plugin.py
```

## プロジェクト構造

```
mkdocs-mermaid-to-image/
├── src/mkdocs_mermaid_to_image/    # メインソースコード
│   ├── __init__.py                 # パッケージ初期化
│   ├── plugin.py                   # MkDocsプラグインクラス
│   ├── config.py                   # 設定管理とバリデーション
│   ├── processor.py                # メイン処理エンジン
│   ├── markdown_processor.py       # Markdown解析・変換
│   ├── image_generator.py          # 画像生成ロジック
│   ├── mermaid_block.py           # Mermaidブロック表現
│   ├── utils.py                    # ユーティリティ関数
│   └── exceptions.py               # カスタム例外クラス
├── tests/                          # テストコード
│   ├── unit/                       # 単体テスト
│   ├── integration/                # 統合テスト
│   ├── property/                   # プロパティベーステスト
│   ├── fixtures/                   # テスト用データ
│   └── conftest.py                 # pytest設定
├── docs/                           # プロジェクトドキュメント
├── template/                       # 開発テンプレート・参考実装
├── scripts/                        # 開発支援スクリプト
├── pyproject.toml                  # プロジェクト設定
├── mkdocs.yml                      # MkDocs設定（開発環境）
└── CLAUDE.md                       # Claude Code開発ガイド
```

## 開発ワークフロー

### 1. 機能開発の手順

1. **ブランチ作成**
   ```bash
   git checkout -b feature/new-feature
   ```

2. **開発サーバー起動**
   ```bash
   uv run mkdocs serve
   ```

3. **テスト駆動開発**
   ```bash
   # テストを先に書く
   uv run pytest tests/unit/test_new_feature.py -v

   # 実装
   # テストが通るまで繰り返し
   ```

4. **コード品質チェック**
   ```bash
   uv run pre-commit run --all-files
   ```

### 2. テスト戦略

#### 単体テスト
- 各クラス・関数の動作をテスト
- モックを使用した外部依存の分離
- エラーケースの網羅

#### 統合テスト
- プラグイン全体の動作をテスト
- 実際のMermaidファイルでの動作確認
- MkDocsビルドプロセスとの統合

#### プロパティベーステスト
- Hypothesisによる自動テストケース生成
- エッジケースの発見

### 3. デバッグ手順

#### ログレベルの調整
```yaml
# mkdocs.yml
plugins:
  - mermaid-to-image:
      log_level: DEBUG
```

#### プロファイリング
```python
# 性能問題の特定
import cProfile
cProfile.run('your_function()', 'profile.stats')
```

#### ステップデバッグ
```bash
# デバッガー付きでテスト実行
uv run python -m pdb -m pytest tests/unit/test_plugin.py
```

## リリース手順

### 1. バージョン更新

```bash
# pyproject.tomlのversionを更新
# __init__.pyの__version__を更新
```

### 2. 変更ログ更新

```bash
# CHANGELOG.mdに変更内容を記載
```

### 3. テスト・品質チェック

```bash
# 全テスト実行
uv run pytest

# 品質チェック
uv run pre-commit run --all-files

# ドキュメントビルド確認
uv run mkdocs build
```

### 4. タグ作成・リリース

```bash
git tag v1.0.0
git push origin v1.0.0
```

## トラブルシューティング

### よくある開発時の問題

#### 1. プラグインが認識されない
```bash
# プラグインの再インストール
uv add --dev --editable .

# entry pointの確認
uv run python -c "from importlib.metadata import entry_points; print([ep.name for ep in entry_points().select(group='mkdocs.plugins')])"
```

#### 2. テストが失敗する
```bash
# 詳細出力でテスト実行
uv run pytest -vv -s

# 特定のテストのみ実行
uv run pytest tests/unit/test_plugin.py::TestSpecificFunction -v
```

#### 3. Mermaid CLI関連のエラー
```bash
# Mermaid CLIの動作確認
mmdc --version

# パスの確認
which mmdc
```

#### 4. 型エラー
```bash
# mypy設定の確認
uv run mypy --config-file pyproject.toml src/

# 特定ファイルのみチェック
uv run mypy src/mkdocs_mermaid_to_image/plugin.py
```

### パフォーマンス最適化

- キャッシュ機能の効果的な活用
- 並列処理の導入検討
- メモリ使用量の監視

## 貢献ガイドライン

### コーディング規約

- **型ヒント**: 必須（Python 3.9+対応）
- **Docstring**: NumPy形式
- **命名規則**: snake_case（関数・変数）、PascalCase（クラス）
- **行長**: 88文字以内
- **インポート順**: isortに従う

### コミットメッセージ

```
feat: 新機能追加
fix: バグ修正
docs: ドキュメント更新
style: コードスタイル修正
refactor: リファクタリング
test: テスト追加・修正
chore: その他の変更
```

### プルリクエスト

1. 機能ブランチで開発
2. テストを追加・更新
3. ドキュメントを更新
4. pre-commitチェックを通す
5. 詳細な説明を記載

詳細は[CONTRIBUTING.md](contributing.md)を参照してください。
