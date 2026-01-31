# Implementation Plan: beautiful-mermaidレンダリングオプションの設定サポート

**Branch**: `001-beautiful-mermaid-options` | **Date**: 2026-01-31 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/001-beautiful-mermaid-options/spec.md`

## Summary

beautiful-mermaidサブモジュールが対応する全12種類のレンダリングオプション（色、フォント、間隔、透過）を、`mkdocs.yml`のプラグイン設定およびMermaidコードブロック属性から指定可能にする。既存の`theme`設定を拡張してbeautiful-mermaid名前付きテーマも受け付け、設定値をプラグイン→Node.jsランナー→beautiful-mermaidライブラリへ正しく伝搬させる。

## Technical Context

**Language/Version**: Python 3.9+（プラグイン本体）、Node.js（beautiful-mermaidランナー）
**Primary Dependencies**: MkDocs、mkdocs-material（プラグインホスト）、beautiful-mermaid（gitサブモジュール）
**Storage**: N/A（ファイルベースSVG生成）
**Testing**: pytest（unit / integration / property）、make test / make check-all
**Target Platform**: クロスプラットフォーム（Windows / macOS / Linux）
**Project Type**: single（MkDocsプラグイン）
**Performance Goals**: 既存ビルド時間の200%以内（Constitution準拠）
**Constraints**: Python 3.9+互換型アノテーション（`dict[str, Any]`ではなく`Dict[str, Any]`）、mypy --strict通過
**Scale/Scope**: 設定12オプション追加、変更対象ファイル約7ファイル

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| ゲート | ステータス | 備考 |
|--------|----------|------|
| I. コード品質 | ✅ PASS | snake_case命名、mypy --strict対応、ruffフォーマット準拠 |
| II. テスト基準 | ✅ PASS | TDD Red-Green-Refactorで実装予定、unit/integrationテスト追加 |
| III. ユーザー体験の一貫性 | ✅ PASS | serve時はフェンス保持、build時のみSVG変換。後方互換性維持 |
| IV. パフォーマンス要件 | ✅ PASS | オプション伝搬のみで重い処理追加なし。コンテンツハッシュキャッシュ維持 |
| 品質ゲート | ✅ PASS | make check / make test / make check-security すべて通過を確認予定 |

## Project Structure

### Documentation (this feature)

```text
specs/001-beautiful-mermaid-options/
├── spec.md              # 仕様書（作成済み）
├── plan.md              # 本ファイル
├── research.md          # Phase 0: 調査結果
├── data-model.md        # Phase 1: データモデル
├── quickstart.md        # Phase 1: クイックスタートガイド
├── contracts/           # Phase 1: 契約定義
└── tasks.md             # Phase 2: タスク（/speckit.tasksで作成）
```

### Source Code (repository root)

```text
src/mkdocs_mermaid_to_svg/
├── config.py                        # 設定スキーマ（変更対象）
├── plugin.py                        # プラグインエントリポイント（変更対象）
├── processor.py                     # ページ処理・バッチ収集（変更対象）
├── image_generator.py               # レンダラー・ペイロード構築（変更対象）
├── markdown_processor.py            # ブロック属性パース（変更対象）
├── mermaid_block.py                 # MermaidBlockデータクラス（変更対象）
├── beautiful_mermaid_runner.mjs     # Node.jsランナー（変更対象）
├── exceptions.py                    # 例外階層（変更不要）
└── utils.py                         # ユーティリティ（変更不要）

tests/
├── unit/
│   ├── test_config.py               # 設定バリデーションテスト（追加）
│   ├── test_processor.py            # プロセッサテスト（追加）
│   ├── test_image_generator.py      # レンダラーテスト（追加）
│   └── test_markdown_processor.py   # 属性パーステスト（追加）
└── integration/
    └── test_beautiful_mermaid_options.py  # E2Eオプション伝搬テスト（新規）
```

**Structure Decision**: 既存のsingle project構造を維持。新規ファイル作成は不要で、既存ファイルへのオプション追加のみ。

## Constitution Check (Phase 1設計後の再チェック)

| ゲート | ステータス | 備考 |
|--------|----------|------|
| I. コード品質 | ✅ PASS | 新規抽象化なし。既存クラス/関数へのオプション追加のみ。snake_case命名維持。 |
| II. テスト基準 | ✅ PASS | config/processor/image_generator/markdown_processorの各層でunitテスト追加。integrationテスト1件新規。 |
| III. ユーザー体験の一貫性 | ✅ PASS | serve時動作変更なし。AutoRendererフォールバック戦略維持。後方互換性確認済み（オプション未設定時の挙動保証）。 |
| IV. パフォーマンス要件 | ✅ PASS | コンテンツハッシュにオプションを追加（キャッシュ整合性維持）。オプションマージは辞書操作のみで軽量。 |
| 品質ゲート | ✅ PASS | 全品質ゲート通過を実装時に確認。 |

## Complexity Tracking

複雑性違反なし。既存パターンの拡張のみで、新しい抽象化やプロジェクト構造の変更は不要。

## Generated Artifacts

| ファイル | フェーズ | 説明 |
|---------|--------|------|
| [research.md](./research.md) | Phase 0 | 設計判断6件（設定スキーマ、テーマ拡張、命名マッピング、マージ戦略、ランナー連携、ハッシュ拡張） |
| [data-model.md](./data-model.md) | Phase 1 | エンティティ定義、オプション優先順位、BatchRenderItem拡張、ペイロードJSON構造 |
| [contracts/mkdocs-yml-config.md](./contracts/mkdocs-yml-config.md) | Phase 1 | mkdocs.yml設定スキーマ契約（12オプション＋theme拡張） |
| [contracts/runner-payload.md](./contracts/runner-payload.md) | Phase 1 | beautiful_mermaid_runner.mjsペイロードJSON契約（単一・バッチ両対応） |
| [quickstart.md](./quickstart.md) | Phase 1 | ユーザー向けクイックスタートガイド |
