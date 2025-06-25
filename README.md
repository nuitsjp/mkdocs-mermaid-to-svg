# Claude Code向けPythonテンプレート

[![Python 3.12+](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/downloads/)
[![uv](https://img.shields.io/badge/uv-latest-green.svg)](https://github.com/astral-sh/uv)
[![Ruff](https://img.shields.io/badge/code%20style-ruff-000000.svg)](https://github.com/astral-sh/ruff)
[![Checked with mypy](https://www.mypy-lang.org/static/mypy_badge.svg)](https://mypy-lang.org/)
[![CI](https://github.com/discus0434/python-template-for-claude-code/actions/workflows/ci.yml/badge.svg)](https://github.com/discus0434/python-template-for-claude-code/actions/workflows/ci.yml)

このリポジトリは、[Claude Code](https://www.anthropic.com/claude-code) との協働に最適化された、本番環境に対応可能なPythonプロジェクトテンプレートです。厳格な型チェック、Claude Codeのパフォーマンスを引き出すための包括的なドキュメントやテンプレート、便利なカスタムスラッシュコマンドなどを備えています。

## 🚀 クイックスタート

### テンプレートの使用方法

1.  GitHubで「Use this template」ボタンをクリックして、新しいリポジトリを作成
2.  新しいリポジトリをクローン
3.  セットアップスクリプトを実行
4.  Claude CodeとGemini CLIを初回起動して認証
5.  Claude Codeの対話モードで`/initialize-project` コマンドを実行して、プロジェクトを初期化

```bash
# 新しいリポジトリをクローン
git clone https://github.com/yourusername/mkdocs-mermaid-to-image.git
cd mkdocs-mermaid-to-image

# セットアップ
make setup
claude
gemini

# プロジェクトの初期化
claude  # /initialize-projectを実行
```

セットアップスクリプトは、以下の処理を自動的に実行します。
- プロジェクト内のすべての `mkdocs_mermaid_to_image` を、指定したプロジェクト名に置換
- `uv` を使用してPythonの仮想環境を構築
- Claude Codeをインストール
- Gemini CLIをインストール
- GitHub CLI (`gh`) をインストール（途中でログインを求められることがあります）
- すべての依存関係をインストール
- pre-commitフックを設定
- 初期テストを実行

## 🔗 主要ドキュメント

- **[CLAUDE.md](./CLAUDE.md)**: Claude Code向けの技術仕様と実装ガイド
- **[template/](./template/)**: ベストプラクティスを反映したサンプルコード集

## 📋 Claude Code チートシート

#### 基本的なCLIコマンド
```bash
# 対話モードを開始
claude

# プロンプトを指定して対話モードを開始
claude "質問内容"

# SDKモードで質問を実行
claude -p "質問内容"

# 最新の会話を続ける
claude -c

# 対話的にセッションを選択して再開
claude -r

# アップデートとシステム管理
claude update                    # Claude Codeを最新版に更新します
claude --version                # バージョン情報を確認します
claude --help                   # ヘルプを表示します
claude mcp                      # Model Context Protocol (MCP) を設定します
```

#### CLIフラグとオプション
```bash
# モデル設定
claude --model sonnet           # Sonnetモデルを使用します
claude --model opus             # Opusモデルを使用します

# セッション管理
claude --list-sessions          # セッションの一覧を表示します
claude --delete-session "<id>"  # 指定したセッションを削除します

# ディレクトリと作業環境
claude --add-dir /path/to/dir   # 作業ディレクトリを追加します
claude --add-dir dir1 --add-dir dir2  # 複数のディレクトリを追加します

# 出力とフォーマット制御
claude --output-format text     # テキスト形式で出力します
claude --output-format json     # JSON形式で出力します
claude --output-format stream-json  # ストリーミングJSON形式で出力します
claude --verbose               # 詳細なログを表示します
claude --quiet                 # 最小限の出力に抑制します

# 実行制御と権限管理
claude --max-turns 5           # 最大ターン数を制限します
claude --timeout 30            # タイムアウトを秒単位で設定します
claude --tool-permissions restricted  # ツールの権限を制限します
claude --allowedTools "Read,Write,Bash"  # 許可するツールを指定します
claude --disallowedTools "WebFetch"      # 禁止するツールを指定します

# セッションと履歴の管理
claude --list-sessions         # セッションの一覧を表示します
claude --delete-session "<id>" # 指定したセッションを削除します
claude --session-id "<id>"     # 特定のセッションで開始します
claude --no-history           # 履歴を保存しません
```

#### パイプとストリーム操作
```bash
# パイプからの入力
echo "コードをレビューしてください" | claude
cat file.py | claude "このコードを説明してください"

# ファイルの内容を直接入力
claude < input.txt

# 環境変数による設定
export ANTHROPIC_MODEL=claude-3-5-sonnet-20241022
export ANTHROPIC_API_KEY=your_api_key
```

#### REPLモードのスラッシュコマンド
Claude Codeの対話モード（REPL）中に使用できるコマンドです。

```bash
# 基本コマンド
/help                          # ヘルプと利用可能なコマンド一覧を表示します
/clear                         # 画面をクリアし、履歴をリセットします
/resume                        # 対話的にセッションを選択して再開します
/continue                      # 直前のセッションに戻ります
/exit                          # Claude Codeを終了します
/quit                          # Claude Codeを終了します（/exitのエイリアス）

# モデルと設定の管理
/model                         # 現在のモデルを表示・変更します
/model sonnet                  # Claude 3.5 Sonnetに変更します
/model opus                    # Claude 3 Opusに変更します
/model haiku                   # Claude 3 Haikuに変更します
/settings                      # 現在の設定を表示・変更します
/permissions                   # 現在のツール権限を表示します

# メモリと記憶の管理
/memory                        # メモリ管理とプロジェクトの記憶（ナレッジ）を表示・編集します
/memory clear                  # メモリをクリアします
/memory show                   # 現在のメモリ内容を表示します
/memory edit                   # メモリを編集します
#                              # CLAUDE.mdへのクイックアクセス（行頭で#）

# セッション管理
/save                          # 現在のセッションを保存します
/save <name>                   # セッションに名前を付けて保存します
/load <session-id>             # 指定したセッションを読み込みます
/sessions                      # セッションの一覧を表示します
/list-sessions                 # セッションの一覧を表示します（/sessionsのエイリアス）
/delete-session <id>           # 指定したセッションを削除します

# ファイルとプロジェクトの操作
/add-dir <path>                # 作業ディレクトリを追加します
/remove-dir <path>             # 作業ディレクトリを削除します
/list-dirs                     # 現在の作業ディレクトリ一覧を表示します
/cwd                           # 現在の作業ディレクトリを表示します
/pwd                           # 現在の作業ディレクトリを表示します（/cwdのエイリアス）

# モードと表示の切り替え
/terminal-setup                # 複数行入力モードを設定します
/vim-mode                      # Vimキーバインドを有効化します
/emacs-mode                    # Emacsキーバインドを有効化します

# デバッグ、診断、ユーティリティ
/debug                         # デバッグ情報を表示します
/status                        # システムの状態と接続状況を表示します
/version                       # Claude Codeのバージョン情報を表示します
/whoami                        # 現在のユーザー情報を表示します
/tokens                        # トークン使用量の統計を表示します
/feedback                      # フィードバックを送信します
/reset                         # 設定をデフォルトにリセットします
```

#### カスタムスラッシュコマンド

このプロジェクトには、開発効率を向上させるための独自のスラッシュコマンドが含まれています。これらは`.claude/commands/`ディレクトリに定義されています。

##### /gemini-documentation
Gemini AIを使用してドキュメントの作成や校正を行います。Geminiは文章作成に優れているため、技術文書の品質向上に活用できます。

使用例：
- /gemini-documentation README.mdを校正
- /gemini-documentation APIドキュメントを作成
- /gemini-documentation ユーザーガイドを更新

##### /gemini-search
Gemini AIを使用してWeb検索を実行します。最新の技術情報や解決策を検索する際に便利です。

使用例：
- /gemini-search Python 3.13の新機能
- /gemini-search FastAPIのベストプラクティス
- /gemini-search 型ヒントの高度な使い方

##### /initialize-project
テンプレートリポジトリから新しいプロジェクトを初期化する際の設定作業を自動化します。プロジェクト固有の情報でCLAUDE.mdやpyproject.tomlを更新します。

使用例：
- /initialize-project

このコマンドは対話的に実行され、プロジェクトの概要やタイプに応じて適切な設定を行います。

##### /ensure-quality
`make check-all`が成功するまで自動的にコードを修正し、コード品質を保証します。フォーマット、リント、型チェック、テストを順番に実行し、エラーを自動修正します。

使用例：
- /ensure-quality

このコマンドは、プロジェクトのコード品質を一貫して高いレベルに保つために使用します。

##### /write-tests
CLAUDE.mdで定義されているt-wada流のTDD（テスト駆動開発）に従って、高品質なテストを作成します。template/tests/ディレクトリのサンプルコードを参考にします。

使用例：
- /write-tests

Red-Green-Refactorサイクルに従い、単体テスト、プロパティベーステスト、統合テストを作成します。

##### /commit-and-pr
現在の変更をコミットし、適切なブランチを作成してプルリクエストを作成します。CLAUDE.mdのGitHub操作規約に従い、適切なブランチ名とコミットメッセージ形式を使用します。

使用例：
- /commit-and-pr

変更の種類に応じて自動的にfeature/、fix/、refactor/などのブランチを作成し、PRを生成します。

##### /safe-refactor
テストカバレッジを維持しながら、コードを安全にリファクタリングします。template/ディレクトリの実装パターンを参考に、型安全性、エラーハンドリング、パフォーマンスを改善します。

使用例：
- /safe-refactor

小さなステップで進め、各変更後にテストを実行して動作を確認します。

---

#### キーボードショートカットと対話操作

```bash
# 基本操作
Ctrl+J                         # 改行
Esc x 2                        # 前のメッセージに戻る
Ctrl+C                         # 現在の入力や生成をキャンセル
Ctrl+D                         # Claude Codeセッションを終了
Ctrl+L                         # ターミナル画面をクリア
Ctrl+R                         # コマンド履歴を逆方向に検索（対応端末のみ）
Up/Down arrows                 # コマンド履歴を移動
Tab                            # オートコンプリート（利用可能な場合）
Shift + Tab                    # Planモードの切り替え

# 複数行入力（環境によって異なります）
\<Enter>                       # クイックエスケープ（すべての端末で対応）
Option+Enter                   # macOS標準
Shift+Enter                    # /terminal-setup後に有効
Alt+Enter                      # Linux/Windows（一部の端末）

# 特殊入力
Esc Esc                        # 前のメッセージを編集
#<Enter>                       # CLAUDE.mdへのクイックアクセス
/<tab>                         # スラッシュコマンドの補完
```

#### 高度な使用例と統合

```bash
# 複数のオプションを組み合わせる
claude --model opus --verbose --add-dir ./src --add-dir ./tests "プロジェクト全体をレビューしてください"

# 特定の形式で出力を制御する
claude --output-format json -p "このコードの問題点をJSON形式で教えてください" < code.py

# タイムアウト付きで実行する
claude --timeout 60 --max-turns 3 "複雑な最適化を提案してください"

# 制限されたツール権限で実行する
claude --tool-permissions restricted "安全にコードを分析してください"

# セッション管理を活用する
claude --save-session "code-review-2024" --model sonnet
claude --load-session "code-review-2024" --continue

# スクリプトの自動化で活用する
claude --output-format json --quiet -p "テストを実行してエラー数を返してください" | jq '.error_count'

# CI/CDでの活用例
cat test_results.txt | claude --output-format text -p "テスト結果を分析してサマリーを作成してください"

# 設定ファイルと連携する
export ANTHROPIC_MODEL=claude-3-5-sonnet-20241022
export CLAUDE_CONFIG_FILE="./claude-config.json"
claude --config-file ./claude-config.json
```

#### Model Context Protocol (MCP) 統合

```bash
# MCPサーバーの設定と管理
claude mcp                     # MCP設定画面を開きます
claude mcp list                # 利用可能なMCPサーバーの一覧を表示します
claude mcp enable <server>     # MCPサーバーを有効化します
claude mcp disable <server>    # MCPサーバーを無効化します
claude mcp status              # MCPの接続状況を確認します

# MCPサーバーの例（設定後に利用可能）
# - ファイルシステム操作
# - データベース接続
# - Git操作
# - Docker管理
# - クラウドサービス統合
```

#### 環境変数と設定の活用

```bash
# 基本設定
export ANTHROPIC_API_KEY="your_api_key"
export ANTHROPIC_MODEL="claude-3-5-sonnet-20241022"
export CLAUDE_CONFIG_DIR="~/.config/claude-code"

# 高度な設定
export CLAUDE_MAX_TURNS=10           # デフォルトの最大ターン数を設定します
export CLAUDE_DEFAULT_TIMEOUT=120    # デフォルトのタイムアウトを設定します
export CLAUDE_HISTORY_SIZE=1000      # 履歴の保存数を設定します
export CLAUDE_AUTO_SAVE=true         # セッションの自動保存を有効化します

# プロジェクト固有の設定
export CLAUDE_PROJECT_DIRS="./src:./tests:./docs"
export CLAUDE_ALLOWED_TOOLS="Read,Write,Bash,Edit"
export CLAUDE_DISALLOWED_TOOLS="WebFetch,WebSearch"

# デバッグと開発設定
export CLAUDE_DEBUG=true             # デバッグモードを有効化します
export CLAUDE_LOG_LEVEL=INFO         # ログレベルを設定します
export CLAUDE_VERBOSE=true           # 詳細な出力を有効化します
```

## ✨ 主な特徴

### 🛠️ 開発ツール
- **[uv](https://github.com/astral-sh/uv)** - 高速なPythonパッケージマネージャー
- **[Ruff](https://github.com/astral-sh/ruff)** - 超高速なPythonリンター＆フォーマッター
- **[mypy](https://mypy-lang.org/)** - `strict`モードとPEP 695の型構文に対応した静的型チェッカー
- **[pytest](https://pytest.org/)** - カバレッジ計測機能付きのテストフレームワーク
- **[hypothesis](https://hypothesis.readthedocs.io/)** - プロパティベーステストのフレームワーク
- **[pytest-benchmark](https://pytest-benchmark.readthedocs.io/)** - パフォーマンスの自動テスト
- **[bandit](https://github.com/PyCQA/bandit)** - セキュリティスキャンツール
- **[pip-audit](https://github.com/pypa/pip-audit)** - 依存関係の脆弱性チェック
- **[pre-commit](https://pre-commit.com/)** - コード品質を維持するためのGitフック

### 🔍 コード品質と型安全
- ✅ PEP 695の新しい型パラメーター構文 (`type` 文) に対応
- ✅ `TypedDict`, `Literal`, `Protocol` を活用した堅牢な型システム
- ✅ JSON操作を型安全に行うためのユーティリティを提供
- ✅ プロパティベーステストによるエッジケースの検証
- ✅ ヘルパー関数を網羅したテストスイート
- ✅ セキュリティと脆弱性の自動チェック

### ⚡ パフォーマンスとプロファイリング
- ✅ `@profile` や `@timeit` デコレータによる手軽なパフォーマンス測定
- ✅ CIによる自動ベンチマーク（Pull Request時にパフォーマンスの比較レポートを生成）
- ✅ コンテキストマネージャー型のプロファイラー
- ✅ パフォーマンスリグレッションの検出システム
- ✅ メモリと実行時間の詳細な監視

### 🔄 CI/CDと自動化
- ✅ 並列実行に対応した高速なCIパイプライン
- ✅ 自動パフォーマンスベンチマーク（Pull Request時にレポートを生成）
- ✅ Dependabotによる依存関係の自動更新
- ✅ GitHub CLIによるワンコマンドでのPull Request・Issue作成
- ✅ キャッシュを最適化した実行環境

### 📚 包括的なドキュメント
- ✅ **CLAUDE.md** - プロジェクトの基本情報
- ✅ **専門ガイド** - 機械学習やバックエンド開発に対応
- ✅ **協働戦略ガイド** - 人間とClaude Codeが効果的に連携するための方法
- ✅ **メモリ更新プロトコル** - ドキュメントの品質を管理するフレームワーク

## 📁 プロジェクト構造

```
project-root/
├── .github/                     # GitHub Actionsの設定ファイル
│   ├── workflows/               # CI/CD + ベンチマークのワークフロー
│   │   ├── ci.yml              # メインCI（テスト、リント、型チェック）
│   │   └── benchmark.yml       # パフォーマンスベンチマーク
│   ├── dependabot.yml           # Dependabotの設定
│   ├── ISSUE_TEMPLATE/          # Issueテンプレート
│   └── PULL_REQUEST_TEMPLATE.md # Pull Requestテンプレート
├── src/
│   └── mkdocs_mermaid_to_image/            # メインパッケージ（`uv sync` でインストール可能）
│       ├── __init__.py
│       ├── py.typed             # PEP 561に準拠した型情報マーカー
│       ├── types.py             # プロジェクト共通の型定義
│       ├── core/                # コアロジック
│       └── utils/               # ユーティリティ
├── tests/                       # テストコード
│   ├── unit/                    # 単体テスト
│   ├── property/                # プロパティベーステスト
│   ├── integration/             # 結合テスト
│   └── conftest.py              # pytestの設定
├── docs/                        # ドキュメント
├── scripts/                     # セットアップ用スクリプト
├── pyproject.toml               # 依存関係とツールの設定
├── .pre-commit-config.yaml      # pre-commitの設定
├── README.md                    # プロジェクトの説明
└── CLAUDE.md                    # Claude Code用ガイド
```

## 📚 ドキュメント階層

### 🎯 主要ドキュメント
- **[CLAUDE.md](CLAUDE.md)** - プロジェクト全体の包括的なガイド
  - プロジェクト概要とコーディング規約
  - よく使うコマンドとGitHub操作
  - 型ヒント、テスト戦略、セキュリティ

### 🤝 戦略ガイド

### 🎨 プロジェクト種別ごとのガイド
- **[ml-project-guide.md](docs/ml-project-guide.md)** - 機械学習プロジェクト向け
  - PyTorch, Hydra, wandb の統合設定
  - 実験管理とデータバージョニング
  - GPUの最適化とモデル管理

- **[backend-project-guide.md](docs/backend-project-guide.md)** - FastAPIバックエンドプロジェクト向け
  - 非同期データベース操作とJWT認証
  - API設計とセキュリティ設定
  - Docker開発環境と本番環境に関する考慮事項

## ✅ 新規プロジェクト設定チェックリスト

### 🔧 基本的なプロジェクト設定
- [ ] **作者情報の更新**: `pyproject.toml` の `authors` セクションを更新します。
- [ ] **ライセンスの選択**: `LICENSE` ファイルを適切なライセンスに変更します。
- [ ] **README.mdの更新**: プロジェクト固有の説明、機能、使用方法を記述します。
- [ ] **CLAUDE.mdのカスタマイズ**: プロジェクトの概要を適宜更新します。
- [ ] **専門ガイドの追加**: 必要に応じて `docs/` 内に詳細なガイドを追加します。

### ⚙️ 開発環境と品質設定
- [ ] **依存関係の調整**: プロジェクトに必要な追加パッケージを導入します。
- [ ] **リントルールの調整**: プロジェクトに合わせて `ruff` の設定をカスタマイズします。
- [ ] **テストカバレッジの調整**: `pytest` のカバレッジ要件を調整します。
- [ ] **プロファイリング設定**: パフォーマンス要件に応じてベンチマークを設定します。

### 🔐 GitHubリポジトリとセキュリティ設定
- [ ] **ブランチ保護**: `main` ブランチの保護ルールを有効化します。
- [ ] **Pull Requestの必須レビュー**: Pull Request作成時のレビュー要求を設定します。
- [ ] **ステータスチェック**: CI、型チェック、テストの成功を必須条件にします。
- [ ] **Dependabot**: 依存関係の自動更新を有効化します。
- [ ] **Issues/Projects**: 必要に応じてプロジェクト管理機能を有効化します。

## 🔧 カスタマイズ

### 型チェックの厳格度を調整する

`mypy` の `strict` モードが厳しすぎる場合は、`pyproject.toml` で以下のように設定を緩和できます。

```toml
# pyproject.toml - 基本設定から開始
[tool.mypy]
python_version = "3.12"
warn_return_any = true
warn_unused_configs = true

# 段階的により厳格な設定を有効化
[[tool.mypy.overrides]]
module = ["mkdocs_mermaid_to_image.core.*"]
strict = true  # まずはコアモジュールに `strict` モードを適用します
```

### リントルールを変更する

```toml
# pyproject.toml
[tool.ruff.lint]
# 必要に応じてルールコードを追加・削除
select = ["E", "F", "I"]  # 基本的なルールから開始
ignore = ["E501"]  # 行の長さはフォーマッターが処理するため無視します
```

### テストカバレッジの要件を変更する

```toml
# pyproject.toml
[tool.pytest.ini_options]
addopts = [
    "--cov-fail-under=60",  # 初期要件を低めに設定
]
```

## 🔗 外部リソース

### 🛠️ 開発ツールの公式ドキュメント
- **[uv Documentation](https://docs.astral.sh/uv/)** - Pythonパッケージ管理
- **[Ruff Documentation](https://docs.astral.sh/ruff/)** - リント＆フォーマッター
- **[mypy Documentation](https://mypy.readthedocs.io/)** - 型チェッカー
- **[pytest Documentation](https://docs.pytest.org/en/stable/)** - テストフレームワーク
- **[Hypothesis Documentation](https://hypothesis.readthedocs.io/)** - プロパティベーステスト

### 🤖 Claude Code関連リソース
- **[Claude Code Official Site](https://www.anthropic.com/claude-code)** - 基本情報とインストール
- **[Claude Code Documentation](https://docs.anthropic.com/en/docs/claude-code)** - 使用方法とベストプラクティス

### 🐍 Pythonと型ヒント関連リソース
- **[PEP 695 - Type Parameter Syntax](https://peps.python.org/pep-0695/)** - 新しい型パラメーター構文の仕様
- **[TypedDict Guide](https://docs.python.org/3/library/typing.html#typing.TypedDict)** - 型安全な辞書
- **[Python 3.12 Release Notes](https://docs.python.org/3/whatsnew/3.12.html)** - 新機能一覧

---

## 📄 ライセンス

このテンプレートはMITライセンスの下で公開されています。詳細は `LICENSE` ファイルをご覧ください。
