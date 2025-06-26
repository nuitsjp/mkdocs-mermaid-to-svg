---
title: GEMINI.md
created_at: 2025-06-27
updated_at: 2025-06-27
# このプロパティは、Gemini Codeが関連するドキュメントの更新を検知するために必要です。消去しないでください。
---

このファイルは、[Gemini Code](https://deepmind.google/technologies/gemini/) がこのリポジトリのコードを扱う際のガイダンスを提供します。

## プロジェクト概要

このプロジェクトは、MkDocsのプラグイン「mkdocs-mermaid-to-image」です。MkDocsで作成されたドキュメント内のMermaid.jsダイアグラムを、ビルド時に静的な画像（PNGまたはSVG）に変換する機能を提供します。これにより、`mkdocs-with-pdf`のようなPDF出力プラグインを使用した場合でも、ダイアグラムが正しく表示されるようになります。

## 技術スタック

- **言語**: Python 3.9+
- **主要ライブラリ**: MkDocs, Pillow, numpy
- **外部依存**: Node.js, `@mermaid-js/mermaid-cli` (Mermaidダイアグラムのレンダリングに必要)
- **パッケージ管理**: uv, npm
- **リンター/フォーマッター**: Ruff
- **型チェッカー**: mypy (strict mode)
- **テストフレームワーク**: pytest
- **自動化**: pre-commit, GitHub Actions

## プロジェクト全体の構造(デフォルト。必要に応じて更新してください)

```
project-root/
├── .github/                     # GitHub Actionsの設定ファイル
│   ├── workflows/               # CI/CD + ベンチマークワークフロー
│   │   ├── ci.yml               # メインCI（テスト・リント・型チェック）
│   │   └── benchmark.yml        # パフォーマンスベンチマーク
│   ├── dependabot.yml           # Dependabotの設定
│   ├── ISSUE_TEMPLATE/          # Issueテンプレート
│   └── PULL_REQUEST_TEMPLATE.md # Pull Requestテンプレート
├── template/                    # **重要**: Claude Codeのベストプラクティス・モデルコード
│   ├── src/
│   │   └── template_package/    # モデルパッケージの完全な実装例
│   │       ├── __init__.py      # パッケージエクスポートの例
│   │       ├── py.typed         # 型情報マーカーの例
│   │       ├── types.py         # 型定義のベストプラクティス
│   │       ├── core/
│   │       │   └── example.py   # クラス・関数実装の模範例
│   │       └── utils/
│   │           ├── helpers.py   # ユーティリティ関数の実装例
│   │           ├── logging_config.py # ロギング設定の実装例
│   │           └── profiling.py # パフォーマンス測定の実装例
│   └── tests/                   # テストコードの完全な実装例
│       ├── unit/                # 単体テスト
│       ├── property/            # プロパティベーステスト
│       ├── integration/         # 結合テスト
│       └── conftest.py          # pytestフィクスチャ
├── src/                         # 実際の開発用ディレクトリ
│       └── project_name/    # モデルパッケージの完全な実装例
│           └── （プロジェクト固有のパッケージを配置）
├── tests/                       # 実際のテスト用ディレクトリ
│   ├── unit/                    # 単体テスト
│   ├── property/                # プロパティベーステスト
│   ├── integration/             # 統合テスト
│   └── conftest.py              # pytest設定
├── docs/                        # ドキュメント
├── scripts/                     # ユーティリティスクリプト
├── pyproject.toml               # uv/ruff/mypyの設定ファイル
├── .gitignore                   # バージョン管理除外ファイル
├── .pre-commit-config.yaml      # pre-commitの設定ファイル
├── README.md                    # 人間向けのプロジェクトの説明
└── CLAUDE.md                    # このファイル
```

## 実装時の必須要件

**重要**: コードを書く際は、必ず以下のすべてを遵守してください：

### 0. 開発環境を確認して活用する

- 開発環境はuvで管理されています。すべてのPythonコマンドに `uv run` を前置し、新しい依存関係は `uv add` で追加してください。
- GitHub CLIがインストールされています。GitHub操作は `make pr` や `make issue` 、または `gh` コマンドを使用してください。
- pre-commitフックが設定されているほか、mypyやruff、pytestなどの厳格なガードレールが整備されています。こまめにmakeコマンドにあるチェックやフォーマットを実行し、コード品質を保証してください。
- 「よく使うコマンド」セクションにあるmakeコマンドとしたコマンド集は、この開発環境での開発を支援するためのコマンドが揃っています。積極的に活用してください。

### 1. コード品質を保証する

**コード品質保証のベストプラクティスは「コーディング規約」セクションを参照してください。**

コーディング後は必ず適切なmakeコマンドを実行してください。例えば、コーディング品質を保証するためのmakeコマンドは以下の通りです。

- `make format`: コードフォーマット
- `make lint`: リントチェック
- `make typecheck`: 型チェック（strict mode）
- `make test`: 全テスト実行
- まとめて実行: `make check-all`（format → lint → typecheck → test）

### 2. テストを実装する

**テスト実装のベストプラクティスは「テスト戦略」セクションを参照してください。**

新機能には必ず対応するテストを作成してください。

### 3. 適切なロギングを行う

**ロギングのベストプラクティスは「ロギング戦略」セクションを参照してください。**

このプロジェクトでは、すべてのコードに実行時のロギングを実装することを必須とします。これにより、開発・デバッグ時の問題追跡が容易になります。

### 4. パフォーマンスを測定する

**パフォーマンス測定のベストプラクティスは「パフォーマンス測定とベンチマーク」セクションを参照してください。**

重い処理を含む関数には適宜プロファイリングを実装し、パフォーマンスを測定することで実装のボトルネックが発見しやすいようにしてください。

### 5. 段階的実装アプローチを行う

- **インターフェース設計**: まずProtocolやABCでインターフェースを定義
- **テストファースト**: 実装前にテストを作成
- **段階的実装**: 最小限の実装→リファクタリング→最適化の順序

## `template/`ディレクトリにあるモデルケースの参照

@template/ ディレクトリには、Python開発のベストプラクティスを示すモデルコードが含まれています。実装時の参考として積極的に活用してください。

### モデルコード参照の推奨場面

1. **新しいクラスや関数を実装する際**
   - @template/src/project_name/core/example.py で適切な型ヒント、docstring、エラーハンドリングを確認
   - @template/src/project_name/types.py で型定義のパターンを確認

2. **ユーティリティ関数を作成する際**
   - @template/src/project_name/utils/helpers.py で関数の構造、エラー処理、ロギングを確認

3. **テストを書く際**
   - @template/tests/unit/ で単体テストの書き方を確認
   - @template/tests/property/ でプロパティベーステストの例を確認
   - @template/tests/conftest.py でフィクスチャの実装例を確認

4. **ロギングを実装する際**
   - @template/src/project_name/utils/logging_config.py で設定例を確認
   - 各モジュールでのロガー使用例を確認

新しいコードを書く際は、まず`template/`内の類似例を確認し、パターンを踏襲し、プロジェクト固有の要件に合わせて調整してください。
`template/`は削除せず、常に参照可能な状態を維持します。

## よく使うコマンド

### 基本的な開発コマンド（Makefile使用）

```bash
# 開発環境のセットアップ
make setup                  # 依存関係インストール + pre-commitフック設定など

# テスト実行
make test                   # 全テスト実行（単体・プロパティベース・統合）
make test-cov               # カバレッジ付きテスト実行
make test-unit              # 単体テストのみ実行
make test-property          # プロパティベーステストのみ実行

# コード品質チェック
make format                 # コードフォーマット
make lint                   # リントチェック（自動修正付き）
make typecheck              # 型チェック（strict mode）
make security               # セキュリティチェック（bandit）
make audit                  # 依存関係の脆弱性チェック（pip-audit）

# パフォーマンス測定
make benchmark              # ローカルベンチマーク実行
make profile                # プロファイリング実行

# 統合チェック
make check                  # format, lint, typecheck, testを順番に実行
make check-all              # pre-commitで全ファイルをチェック

# パフォーマンス測定
make benchmark              # ローカルベンチマーク実行
make profile                # プロファイリング実行

# GitHub操作
make pr TITLE="タイトル" BODY="本文" [LABEL="ラベル"]      # PR作成
make issue TITLE="タイトル" BODY="本文" [LABEL="ラベル"]   # イシュー作成

# その他
make clean                  # キャッシュファイルの削除
make help                   # 利用可能なコマンド一覧

# 依存関係の追加
make sync                         # 全依存関係を同期
uv add package_name                # ランタイム依存関係
uv add --dev dev_package_name      # 開発依存関係
uv lock --upgrade                  # 依存関係を更新
```

## コーディング規約

### ディレクトリ構成

パッケージとテストは @template/ 内の構造を踏襲します。コアロジックは必ず `src/project_name` 内に配置してください。

```
src/
├── project_name/
│   ├── core/
│   ├── utils/
│   ├── __init__.py
│   └── ...
├── tests/
│   ├── unit/
│   ├── property/
│   ├── integration/
│   └── conftest.py
├── docs/
...
```

### Python コーディングスタイル

- **型ヒント**: Python 3.12+ の型ヒントを必ず使用（mypy strict mode + PEP 695準拠）
- **Docstring**: NumPy形式のDocstringを使用
- **命名規則**:
  - クラス: PascalCase
  - 関数/変数: snake_case
  - 定数: UPPER_SNAKE_CASE
  - プライベート: 先頭に `_`
- **インポート順序**: 標準ライブラリ → サードパーティ → ローカル（ruffが自動整理）

### 型ヒントのベストプラクティス

@template/src/template_package/types.py を参照してください。

### エラーメッセージの原則

#### 1. 具体的で実用的
```python
# Bad
raise ValueError("Invalid input")

# Good
raise ValueError(
    f"Expected positive integer for 'count', got {count}. "
    f"Please provide a value greater than 0."
)
```

#### 2. コンテキストを提供
```python
try:
    result = process_data(data)
except ProcessingError as e:
    raise ProcessingError(
        f"Failed to process data from {source_file}: {e}"
    ) from e
```

#### 3. 解決策を提示
```python
if not config_file.exists():
    raise FileNotFoundError(
        f"Configuration file not found at {config_file}. "
        f"Create one by running: python -m {__package__}.init_config"
    )
```

### アンカーコメント

疑問点や改善点がある場合は、アンカーコメントを活用してください。

```python
# AIDEV-NOTE: このクラスは外部APIとの統合専用
# AIDEV-TODO: パフォーマンス最適化が必要（レスポンス時間>500ms）
# AIDEV-QUESTION: この実装でメモリリークの可能性は？
```

## テスト戦略

**t-wada流のテスト駆動開発（TDD）を徹底してください。**

### TDD TODOリスト（t-wada流）

#### 基本方針

- 🔴 Red: 失敗するテストを書く
- 🟢 Green: テストを通す最小限の実装
- 🔵 Refactor: リファクタリング
- 小さなステップで進める
- 仮実装（ベタ書き）から始める
- 三角測量で一般化する
- 明白な実装が分かる場合は直接実装してもOK
- テストリストを常に更新する
- 不安なところからテストを書く

#### TDDの実施手順

1. **TODOリストの作成**
   ```
   [ ] 実装したい機能をリストアップ
   [ ] 不安な部分、エッジケースも追加
   [ ] 最小単位に分解
   ```

2. **Red フェーズ**
   ```python
   # 1. 失敗するテストを書く
   def test_新機能が期待通り動作する():
       result = new_function(input_data)
       assert result == expected_output  # まだ実装していないので失敗
   ```

3. **Green フェーズ**
   ```python
   # 2. テストを通す最小限の実装
   def new_function(input_data):
       return expected_output  # 仮実装（ベタ書き）
   ```

4. **Refactor フェーズ**
   ```python
   # 3. リファクタリング（テストが通ることを確認しながら）
   def new_function(input_data):
       # 実際のロジックに置き換える
       processed = process_data(input_data)
       return format_output(processed)
   ```

#### 三角測量の例

```python
# Step 1: 最初のテスト（ベタ書きで通す）
def test_add_正の数():
    assert add(2, 3) == 5

def add(a, b):
    return 5  # 仮実装

# Step 2: 2つ目のテスト（一般化を促す）
def test_add_別の正の数():
    assert add(1, 4) == 5
    assert add(10, 20) == 30  # これで仮実装では通らない

def add(a, b):
    return a + b  # 一般化

# Step 3: エッジケースを追加
def test_add_負の数():
    assert add(-1, -2) == -3
    assert add(-5, 3) == -2
```

#### TDD実践時の注意点

1. **テストは1つずつ追加**
   - 一度に複数のテストを書かない
   - 各テストが失敗することを確認してから実装

2. **コミットのタイミング**
   - Red → Green: テストが通ったらコミット
   - Refactor: リファクタリング完了でコミット
   - 小さく頻繁にコミットする

3. **テストの粒度**
   - 最小単位でテストを書く
   - 1つのテストで1つの振る舞いをテスト
   - テスト名は日本語で意図を明確に

4. **リファクタリングの判断**
   - 重複コードがある
   - 可読性が低い
   - 設計原則（SOLID等）に違反
   - パフォーマンスの問題（測定してから）

5. **テストファーストの実践**
   - 必ず失敗するテストから書く
   - `make test`で失敗を確認
   - 最小限の実装でテストを通す

6. **段階的な実装**
   - TODOリストを1つずつ消化
   - 各ステップでテストが通ることを確認
   - リファクタリング時もテストを実行

### TDDサイクルの記録

実装時は以下のフォーマットでTDDサイクルを記録してください：

```markdown
## 機能: ユーザー認証システム

### TODOリスト
- [x] ユーザー名とパスワードで認証できる
- [x] 不正な認証情報でエラーを返す
- [ ] パスワードのハッシュ化
- [ ] セッション管理
- [ ] ログアウト機能

### サイクル1: 基本的な認証
🔴 Red: test_正常系_有効な認証情報でTrue()
🟢 Green: return True（仮実装）
🔵 Refactor: 実際の認証ロジックを実装

### サイクル2: エラーハンドリング
🔴 Red: test_異常系_無効な認証情報でFalse()
🟢 Green: if文で条件分岐
🔵 Refactor: エラーメッセージの改善
```

詳細は @template/tests/ にある実装を適宜参照してください。

### テストの種類

1. **単体テスト** ( @template/tests/unit/test_example.py などを参照 )
   - 関数・クラスの基本動作をテスト
   - 正常系・異常系・エッジケースもカバーする

2. **プロパティベーステスト** ( @template/tests/property/test_helpers_property.py などを参照 )
   - Hypothesisで様々な入力パターンを自動生成してテスト

3. **統合テスト** ( @template/tests/integration/test_example.py などを参照 )
   - コンポーネント間の連携

### テスト命名規約

```python
# 日本語で意図を明確に
def test_正常系_有効なデータで処理成功():
    """chunk_listが正しくチャンク化できることを確認。"""

 def test_異常系_不正なサイズでValueError():
    """チャンクサイズが0以下の場合、ValueErrorが発生することを確認。"""

def test_エッジケース_空リストで空結果():
    """空のリストをチャンク化すると空の結果が返されることを確認。"""
```

## ロギング戦略

### ロギング実装の必須要件

**TL;DR**

1. **各モジュールの冒頭で必ずロガーを実装**
2. **関数・メソッドの開始と終了時にログを出力**
3. **エラー処理時にログを出力し、exc_info=Trueを付けることでエラーの原因を追跡できるようにする**
4. **ログレベルの使い分け**
    - **DEBUG**: 詳細な実行フロー、引数、戻り値
    - **INFO**: 重要な処理の完了、状態変更
    - **WARNING**: 異常ではないが注意が必要な状況
    - **ERROR**: エラー発生時（必ずexc_info=Trueを付ける）

詳細は @template/src/template_package/utils/logging_config.py や @template/src/template_package にある実装を適宜参照してください。

### 開発時のロギング設定

```python
# コード実装時は必ずINFOモード、デバッグ時はDEBUGモードで開発
from project_name import setup_logging
setup_logging(level="INFO")

# または環境変数で設定
export LOG_LEVEL=INFO
```

### テスト時の設定

```python
# テスト実行時のログレベル制御
export TEST_LOG_LEVEL=INFO  # デフォルトはDEBUG

# 個別のテストでログレベルを変更
def test_with_custom_log_level(set_test_log_level):
    set_test_log_level("WARNING")
    # テスト実行
```

## パフォーマンス測定とベンチマーク

### プロファイリングツールの使用

```python
# template/src/template_package/utils/profiling.py を参照
from project_name.utils.profiling import profile, timeit, Timer, profile_context

# 関数デコレーター
@profile
def heavy_computation():
    return sum(i**2 for i in range(10000))

@timeit
def quick_function():
    return [i for i in range(1000)]

# コンテキストマネージャー
with Timer("Custom operation") as timer:
    result = process_large_dataset()
print(f"Took {timer.elapsed:.4f} seconds")

# 詳細プロファイリング
with profile_context(sort_by="cumulative", limit=10) as prof:
    complex_operation()
```

### ベンチマーク自動化

GitHub Actionsで自動ベンチマークが実行されます：
- PR作成時にパフォーマンス比較
- 10%以上の性能低下でアラート
- ベンチマーク結果をPRコメントに自動投稿

## GitHub操作

Claude Codeは `gh` コマンドを使用してGitHub操作を行うことができます。

### プルリクエスト作成

#### ブランチ名の命名規則

- 機能追加: `feature/...`
- バグ修正: `fix/...`
- リファクタリング: `refactor/...`
- ドキュメント更新: `docs/...`
- テスト: `test/...`

#### ラベル名の命名規則

- 機能追加: `enhancement`
- バグ修正: `bug`
- リファクタリング: `refactor`
- ドキュメント更新: `documentation`
- テスト: `test`

#### コマンドの例

```bash
# Makefileコマンドを使用したPR作成
make pr TITLE="機能追加" BODY="新しい機能を実装しました" LABEL="enhancement"
make pr TITLE="認証エラー修正" BODY="ログイン時の500エラーを修正" LABEL="bug"
make pr TITLE="ドキュメント更新" BODY="READMEを更新しました" LABEL="documentation"

# ラベルなしでPR作成
make pr TITLE="リファクタリング" BODY="コードの可読性を向上させました"

# 直接gh CLIを使用する場合
gh pr create --title "Feature: Add new functionality" --body "Description of changes"

# ドラフトPRの作成
gh pr create --draft --title "WIP: Working on feature" --body "Description of changes"
```

### イシュー管理

```bash
# Makefileコマンドを使用したイシューの作成
make issue TITLE="認証の不具合" BODY="ログイン時にエラーが発生します" LABEL="bug"
make issue TITLE="新機能の提案" BODY="〜の機能があると便利です" LABEL="enhancement"
make issue TITLE="Claude Code改善" BODY="〜の部分で改善が必要です" LABEL="documentation"
make issue TITLE="質問" BODY="〜について教えてください" LABEL="question"

# ラベルなしでイシュー作成
make issue TITLE="一般的な改善提案" BODY="〜を改善してはどうでしょうか"

# 直接gh CLIを使用する場合
gh issue create --title "Bug: Fix authentication" --body "Description"

# イシューの一覧表示
gh issue list

# イシューの詳細表示
gh issue view 123
```

## CLAUDE.md自動更新トリガー

**重要**: 以下の状況でCLAUDE.mdの更新を検討してください：

### 変更ベースのトリガー
- 仕様の追加・変更があった場合
- 新しい依存関係の追加時
- プロジェクト構造の変更
- コーディング規約の更新

### 頻度ベースのトリガー

- **同じ質問が2回以上発生** → 即座にFAQとして追加
- **新しいエラーパターンを2回以上確認** → トラブルシューティングに追加

## トラブルシューティング

### pre-commitが失敗する場合

```bash
# キャッシュをクリア
uv run pre-commit clean
uv run pre-commit gc

# 再インストール
uv run pre-commit uninstall
uv run pre-commit install
```

### ...随時追記してください...

## FAQ

### ...随時追記してください...

## 詳細ガイドの参照

以下の専用ガイドを必要に応じてインポートしてください。

#### 機械学習プロジェクト

機械学習プロジェクトの場合、@docs/ml-project-guide.md をインポートしてください。

このガイドには以下が含まれます：
- PyTorch, numpy, pandas の設定
- Weights & Biases (wandb) の統合手順
- Hydra による設定管理
- GPU環境の最適化
- 実験管理のベストプラクティス
- データバージョニング戦略

#### バックエンドAPI プロジェクト

FastAPI を使用したバックエンドプロジェクトの場合、@docs/backend-project-guide.md をインポートしてください。

このガイドには以下が含まれます：
- FastAPI + Pydantic の設定
- SQLAlchemy による非同期データベース操作
- JWT認証とセキュリティ設定
- API設計のベストプラクティス
- Docker開発環境
- プロダクション考慮事項

### カスタムガイドの追加

プロジェクト固有の要件に応じて、追加のガイドを`docs/` ディレクトリに作成できます。
例: フロントエンドプロジェクトのガイド(`docs/frontend-project-guide.md`), チーム固有のルール(`docs/team-specific-guide.md`)など

## TDD TODOリスト（t-wada流）

### 基本方針

- 🔴 Red: 失敗するテストを書く
- 🟢 Green: テストを通す最小限の実装
- 🔵 Refactor: リファクタリング
- 小さなステップで進める
- 仮実装（ベタ書き）から始める
- 三角測量で一般化する
- 明白な実装が分かる場合は直接実装してもOK
- テストリストを常に更新する
- 不安なところからテストを書く
