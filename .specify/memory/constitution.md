<!--
  Sync Impact Report
  ==================
  Version change: (new) → 1.0.0
  Modified principles: N/A (initial creation)
  Added sections:
    - Core Principles (4 principles)
    - 開発制約 (Development Constraints)
    - 品質ゲート (Quality Gates)
    - Governance
  Removed sections: N/A
  Templates requiring updates:
    - .specify/templates/plan-template.md — ✅ 変更不要（Constitution Check が汎用的に定義済み）
    - .specify/templates/spec-template.md — ✅ 変更不要（Success Criteria が汎用的に定義済み）
    - .specify/templates/tasks-template.md — ✅ 変更不要（テスト優先の構造が既に反映済み）
    - .specify/templates/checklist-template.md — ✅ 変更不要
    - .specify/templates/agent-file-template.md — ✅ 変更不要
  Follow-up TODOs: None
-->

# mkdocs-mermaid-to-svg Constitution

## Core Principles

### I. コード品質 (Code Quality)

- すべてのPythonコードは `mypy --strict` を通過しなければならない（MUST）。
- `ruff` によるフォーマット（88文字行制限）およびリント検査を義務付ける。
- `snake_case`（関数・変数）、`CamelCase`（クラス）の命名規約に従わなければならない（MUST）。
- 構造化された例外階層（`exceptions.py` の `MermaidPreprocessorError` 継承）を維持する。
- 不要なコード、未使用のインポート、後方互換性ハックは即座に削除する。
- 新しい抽象化は、具体的な重複が3箇所以上存在する場合にのみ導入する。
- セキュリティ検査（`bandit` + `pip-audit`）を `make check-security` で実施できる状態を維持する。

**根拠**: 静的型検査と一貫したスタイルにより、レビューコストを削減し、
ランタイムエラーを未然に防ぐ。

### II. テスト基準 (Testing Standards)

- TDDワークフロー（t-wada流 Red-Green-Refactor）を厳守する（MUST）。
  1. **Red**: 失敗するテストを書く → `make test` + `make check-all`
  2. **Green**: テストを通す最小限のコードを書く → `make test-cov` + `make check-all`
  3. **Refactor**: クリーンアップ → すべてのチェックが通ることを確認
- テストは `tests/unit/`、`tests/integration/`、`tests/fixtures/` のミラー構造に配置する（MUST）。
- インテグレーションテストには `@pytest.mark.integration` マーカーを付与する（MUST）。
- 低速テストには `@pytest.mark.slow` マーカーを付与する（MUST）。
- SVGゴールデンテストは `REGENERATE_SVG_GOLDENS=1` で再生成可能な状態を維持する。
- プロパティベーステスト（`make test-property`）を活用し、境界条件を網羅する。
- カバレッジレポート（`make test-cov`）を定期的に確認し、未テストのパスを把握する。

**根拠**: テストファーストにより設計品質が向上し、リグレッションを早期検出できる。
小さなサイクルで回すことで、問題の特定と修正が容易になる。

### III. ユーザー体験の一貫性 (User Experience Consistency)

- `mkdocs serve` 時はMermaidフェンスをそのまま残し、ライブプレビューを妨げない（MUST）。
- `mkdocs build` 時はMermaidコードブロックを静的SVGに確実に変換する（MUST）。
- `enabled_if_env` による環境変数制御で、プラグインの有効/無効を明示的に切り替えられる（MUST）。
- 生成されるファイル名はMD5コンテンツハッシュによる決定的命名を使用する（MUST）。
- エラーメッセージは `MermaidPreprocessorError` 階層で構造化し、
  ユーザーが原因を特定できる情報を含める（MUST）。
- `AutoRenderer` のフォールバック戦略（`BeautifulMermaidRenderer` → `mmdc`）を維持し、
  サポート外のダイアグラムタイプでもビルドが失敗しないようにする（MUST）。

**根拠**: MkDocsユーザーは「開発時はインタラクティブ、ビルド時は静的」という
一貫した体験を期待する。予測可能な動作がプラグインの信頼性を担保する。

### IV. パフォーマンス要件 (Performance Requirements)

- SVGレンダリング結果はコンテンツハッシュベースのキャッシュにより、
  同一内容のダイアグラムを再レンダリングしない（MUST）。
- `MermaidCommandResolver` は `mmdc` / `npx mmdc` の解決結果をキャッシュし、
  ページごとの繰り返し検索を回避する（MUST）。
- サブプロセス実行（`MermaidCLIExecutor`）はプラットフォーム固有の最適化
  （Windows: `cmd /c`）を適用する（MUST）。
- `on_post_build` でのクリーンアップ処理は、ビルド完了後に一括で実行し、
  ビルド中のI/Oオーバーヘッドを最小化する（MUST）。
- 新機能追加時にビルド時間の著しい増加（既存ベンチマーク比200%超）が
  発生する場合、最適化を義務付ける（MUST）。

**根拠**: MkDocsビルドはCI/CDパイプラインで頻繁に実行されるため、
不要な再計算やI/Oの削減がワークフロー全体の効率に直結する。

## 開発制約 (Development Constraints)

- Python 3.9+ を最低サポートバージョンとする。
- `beautiful-mermaid` はgitサブモジュールとして管理し、
  ランナーは `beautiful_mermaid_runner.mjs` を使用する。
- `image_id_enabled` 使用時は `attr_list` Markdown拡張を必須とし、
  設定バリデーションで強制する。
- コミットメッセージは Conventional Commits 形式
  （`feat:`, `fix:`, `refactor:`, `docs:`）に従い、件名は72文字以内とする。
- PyPIへの公開は `release-*` タグによる trusted publishing で実施する。

## 品質ゲート (Quality Gates)

すべてのPR/マージは以下のゲートを通過しなければならない（MUST）:

1. `make check`（format + lint + typecheck）が成功すること
2. `make test`（全テストスイート）が成功すること
3. `make check-security`（bandit + pip-audit）で既知の脆弱性がないこと
4. 新規コードに対応するテストが存在すること（TDDワークフローに従うこと）
5. `make check-all`（pre-commit フック全体）が成功すること

## Governance

- この Constitution はプロジェクトのすべての開発プラクティスに優先する。
- 修正には以下を必要とする:
  1. 変更内容の文書化（Sync Impact Report の更新）
  2. 影響を受けるテンプレートの同期確認
  3. バージョン番号の適切な更新（セマンティックバージョニングに従う）
- すべてのPR/レビューは Constitution への準拠を検証しなければならない（MUST）。
- 複雑性の追加は明示的な正当化を必要とする。
- ランタイム開発ガイダンスは `CLAUDE.md` を参照すること。

**Version**: 1.0.0 | **Ratified**: 2026-01-31 | **Last Amended**: 2026-01-31
