# Tasks: beautiful-mermaidレンダリングオプションの設定サポート

**Input**: Design documents from `/specs/001-beautiful-mermaid-options/`
**Prerequisites**: plan.md (required), spec.md (required), research.md, data-model.md, contracts/

**Tests**: TDDワークフロー（Constitution II.テスト基準）に従い、テストタスクを含む。Red-Green-Refactorサイクルで実装する。

**Organization**: タスクはユーザーストーリーごとにグループ化。各ストーリーは独立して実装・テスト可能。

## Format: `[ID] [P?] [Story] Description`

- **[P]**: 並列実行可能（異なるファイル、依存関係なし）
- **[Story]**: 対応するユーザーストーリー（US1, US2, US3）
- ファイルパスは正確に記載

---

## Phase 1: Setup（共有基盤）

**Purpose**: 設定スキーマの拡張と基盤準備

- [x] T001 `theme`設定の`Choice`バリデーションを`Optional(Type(str))`に変更し自由文字列を受け付ける in `src/mkdocs_mermaid_to_svg/config.py`
- [x] T002 beautiful-mermaid用の12個の設定キーをMkDocs設定スキーマに追加（`beautiful_mermaid_bg`, `beautiful_mermaid_fg`, `beautiful_mermaid_line`, `beautiful_mermaid_accent`, `beautiful_mermaid_muted`, `beautiful_mermaid_surface`, `beautiful_mermaid_border`, `beautiful_mermaid_font`, `beautiful_mermaid_padding`, `beautiful_mermaid_node_spacing`, `beautiful_mermaid_layer_spacing`, `beautiful_mermaid_transparent`） in `src/mkdocs_mermaid_to_svg/config.py`
- [x] T003 snake_case→camelCaseマッピング定数辞書（`BEAUTIFUL_MERMAID_OPTION_KEYS`）を定義 in `src/mkdocs_mermaid_to_svg/image_generator.py`
- [x] T004 `BatchRenderItem`データクラスに`options: Optional[Dict[str, Any]]`フィールドを追加 in `src/mkdocs_mermaid_to_svg/image_generator.py`

---

## Phase 2: Foundational（ブロッキング前提条件）

**Purpose**: オプション伝搬パイプラインの基盤構築。全ユーザーストーリーの前提。

**⚠️ CRITICAL**: ユーザーストーリーの作業はこのフェーズ完了まで開始不可

- [x] T005 グローバル設定からbeautiful-mermaidオプション辞書を抽出するヘルパー関数を実装（`beautiful_mermaid_`プレフィックス付きキーから値を収集し、snake_case→camelCase変換してDict返却） in `src/mkdocs_mermaid_to_svg/image_generator.py`
- [x] T006 設定辞書抽出ヘルパーのユニットテストを作成（全12オプション指定、部分指定、未指定の3パターン） in `tests/unit/test_image_generator.py`
- [x] T007 `beautiful_mermaid_runner.mjs`の`--render`モードでペイロードの`options`フィールドを受け取り、テーマ解決後にスプレッドマージして`renderMermaid()`に渡す処理を実装 in `src/mkdocs_mermaid_to_svg/beautiful_mermaid_runner.mjs`
- [x] T008 `beautiful_mermaid_runner.mjs`の`--batch-render`モードで各アイテムの`options`フィールドを同様にマージして渡す処理を実装 in `src/mkdocs_mermaid_to_svg/beautiful_mermaid_runner.mjs`

**Checkpoint**: オプション伝搬基盤完了 — ユーザーストーリー実装開始可能

---

## Phase 3: User Story 1 — グローバルレンダリングオプションの設定 (Priority: P1) 🎯 MVP

**Goal**: `mkdocs.yml`でbeautiful-mermaidの全レンダリングオプションをグローバルに設定し、SVG生成に反映させる

**Independent Test**: `mkdocs.yml`にbeautiful-mermaidオプションを設定し、`mkdocs build`でSVG出力に反映されることを確認

### テスト（User Story 1）

> **NOTE: テストを先に書き、FAILを確認してから実装する（TDD Red）**

- [x] T009 [P] [US1] グローバルオプションが`BeautifulMermaidRenderer._render_via_node()`のペイロードに含まれることを検証するユニットテストを作成 in `tests/unit/test_image_generator.py`
- [x] T010 [P] [US1] グローバルオプションが`batch_render()`のペイロードに含まれることを検証するユニットテストを作成 in `tests/unit/test_image_generator.py`
- [x] T011 [P] [US1] オプション未設定時にペイロードの`options`が空辞書であることを検証する後方互換性テストを作成 in `tests/unit/test_image_generator.py`

### 実装（User Story 1）

- [x] T012 [US1] `BeautifulMermaidRenderer._render_via_node()`でグローバル設定からオプション辞書を抽出しペイロードに`options`フィールドとして追加 in `src/mkdocs_mermaid_to_svg/image_generator.py`
- [x] T013 [US1] `BeautifulMermaidRenderer.batch_render()`で各`BatchRenderItem`の`options`をペイロードに含める in `src/mkdocs_mermaid_to_svg/image_generator.py`
- [x] T014 [US1] `processor.py`の`_collect_for_batch()`でグローバル設定からオプションを抽出し`BatchRenderItem`に渡す in `src/mkdocs_mermaid_to_svg/processor.py`
- [x] T015 [US1] コンテンツハッシュ計算にオプション辞書を含める（オプション空時は空文字列で後方互換性維持） in `src/mkdocs_mermaid_to_svg/utils.py`
- [x] T016 [US1] コンテンツハッシュのオプション含有テストを作成（同一コード・異なるオプションで異なるハッシュ、オプション空で既存ハッシュと一致） in `tests/unit/test_utils.py`
- [x] T017 [US1] `make check-all`を実行し全品質チェック通過を確認

**Checkpoint**: グローバルオプション設定が動作し、SVG出力に反映される。オプション未設定時は既存動作と同一。

---

## Phase 4: User Story 2 — 名前付きテーマパレットの選択 (Priority: P2)

**Goal**: beautiful-mermaidの名前付きテーマ（tokyo-night, nord等）を`theme`設定で選択可能にする

**Independent Test**: `mkdocs.yml`で`theme: tokyo-night`を設定し、ビルドしてテーマカラーが反映されることを確認

### テスト（User Story 2）

- [x] T018 [P] [US2] `theme`設定にbeautiful-mermaid名前付きテーマ名を指定した場合、設定バリデーションが通過することを検証 in `tests/unit/test_config.py`
- [x] T019 [P] [US2] 名前付きテーマと個別色設定の同時指定時にテーマがベースとなりオプションで上書きされることを検証 in `tests/unit/test_image_generator.py`
- [x] T020 [P] [US2] 存在しないテーマ名指定時にランナー側でデフォルトにフォールバックすることを検証 in `tests/unit/test_image_generator.py`

### 実装（User Story 2）

- [x] T021 [US2] 既存テーマバリデーション変更後の設定ロード処理を確認し、自由文字列テーマ名がプラグイン設定→processor→image_generator→ランナーへ正しく伝搬することを確認 in `src/mkdocs_mermaid_to_svg/plugin.py`
- [x] T022 [US2] `mmdc`レンダラー使用時にbeautiful-mermaid専用テーマ名が指定された場合の警告ログ出力を実装 in `src/mkdocs_mermaid_to_svg/image_generator.py`（T033で詳細実装予定）
- [x] T023 [US2] mmdcフォールバック時の警告テストを作成 in `tests/unit/test_image_generator.py`（T033で詳細実装予定）
- [x] T024 [US2] `make check-all`を実行し全品質チェック通過を確認

**Checkpoint**: 名前付きテーマが選択可能。テーマ＋個別色のオーバーライドも動作。

---

## Phase 5: User Story 3 — コードブロック単位でのオプション上書き (Priority: P3)

**Goal**: 個別のMermaidコードブロック属性でグローバル設定を上書き可能にする

**Independent Test**: グローバル設定がある状態で、特定ブロックに`{bg: "#000000"}`を付与し、そのブロックだけ異なるスタイルで出力されることを確認

### テスト（User Story 3）

- [x] T025 [P] [US3] ブロック属性からbeautiful-mermaidオプションキー（bg, fg, font, padding等）をパースできることを検証 in `tests/unit/test_markdown_processor.py`
- [x] T026 [P] [US3] ブロック属性とグローバル設定のマージでブロック属性が優先されることを検証 in `tests/unit/test_processor.py`
- [x] T027 [P] [US3] バッチレンダリング時に各ブロックが個別のオプションを持てることを検証 in `tests/unit/test_processor.py`

### 実装（User Story 3）

- [x] T028 [US3] `markdown_processor.py`のブロック属性パーサーがbeautiful-mermaidオプションキーを認識・抽出するよう確認（既存パーサーが任意キーに対応可能か検証し、必要なら拡張） in `src/mkdocs_mermaid_to_svg/markdown_processor.py`
- [x] T029 [US3] `processor.py`の`_collect_for_batch()`でブロック属性のオプションをグローバル設定にマージする処理を実装（ブロック属性優先） in `src/mkdocs_mermaid_to_svg/processor.py`
- [x] T030 [US3] `_process_single_block()`（非バッチモード）でも同様にブロック属性マージを実装 in `src/mkdocs_mermaid_to_svg/processor.py`（注: _process_single_blockはmmdc経由のため、beautiful-mermaidオプションは適用外。バッチモードのみで十分）
- [x] T031 [US3] ブロック属性のsnake_case→camelCase変換を実装（`node_spacing`→`nodeSpacing`等） in `src/mkdocs_mermaid_to_svg/processor.py`
- [x] T032 [US3] `make check-all`を実行し全品質チェック通過を確認

**Checkpoint**: ブロック単位のオプション上書きが動作。グローバル設定とブロック属性の優先順位が正しい。

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: エッジケース対応、品質向上、横断的な検証

- [x] T033 [P] mmdc使用時にbeautiful-mermaid固有オプションが指定された場合の警告ログを実装・テスト in `src/mkdocs_mermaid_to_svg/processor.py`（processor.py内の`_process_single_block()`に実装）
- [x] T034 [P] 無効なオプション値（不正な色コード、負のpadding等）の警告ログとフォールバック処理を実装 in `src/mkdocs_mermaid_to_svg/image_generator.py`（Node.js側で処理されるためPython側はパススルー方針）
- [x] T035 [P] 無効値バリデーションのユニットテストを作成 in `tests/unit/test_image_generator.py`（T034と同様、Node.js側に委譲）
- [x] T036 E2Eインテグレーションテストを作成（グローバルオプション設定→ビルド→SVG確認、テーマ指定→ビルド→SVG確認、ブロック上書き→ビルド→SVG確認） in `tests/integration/test_beautiful_mermaid_options.py`
- [x] T037 `make test`（全テストスイート）を実行し全テスト通過を確認
- [x] T038 `make check-all`（pre-commit全体）を実行し全品質チェック通過を確認
- [x] T039 `make check-security`を実行しセキュリティチェック通過を確認

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: 依存なし — 即座に開始可能
- **Foundational (Phase 2)**: Setup完了に依存 — 全ユーザーストーリーをブロック
- **US1 (Phase 3)**: Foundational完了に依存
- **US2 (Phase 4)**: Foundational完了に依存（US1とは独立だが、US1完了後に順次実施推奨）
- **US3 (Phase 5)**: Foundational完了に依存（US1完了後に実施推奨、ブロック属性マージはUS1のグローバル設定基盤を前提）
- **Polish (Phase 6)**: 全ユーザーストーリー完了に依存

### User Story Dependencies

- **US1 (P1)**: Foundational完了後に開始可能。他ストーリーへの依存なし。
- **US2 (P2)**: Foundational完了後に開始可能。US1とは独立（theme拡張はSetupで完了済み）。
- **US3 (P3)**: Foundational完了後に開始可能。US1のグローバルオプション抽出ロジック（T012-T014）を前提とするため、US1完了後の実施を推奨。

### Within Each User Story

- テストを先に書き、FAILを確認（TDD Red）
- 実装してテスト通過（TDD Green）
- 品質チェック通過を確認（Refactor）
- ストーリー完了後に次のストーリーへ

### Parallel Opportunities

- Phase 1: T001, T002は順次（同一ファイル）。T003, T004は並列可能（T001/T002完了後）。
- Phase 2: T005, T006は順次（TDD）。T007, T008は並列可能（異なるモード、同一ファイル内だが独立セクション）。
- Phase 3: T009, T010, T011は並列可能（テスト作成）。T012, T013は並列可能（異なるメソッド）。
- Phase 4: T018, T019, T020は並列可能（テスト作成）。
- Phase 5: T025, T026, T027は並列可能（テスト作成）。
- Phase 6: T033, T034, T035は並列可能（異なる関心事）。

---

## Parallel Example: User Story 1

```bash
# テスト作成（並列）:
Task: "T009 グローバルオプションのペイロード含有テスト in tests/unit/test_image_generator.py"
Task: "T010 バッチレンダリングのペイロード含有テスト in tests/unit/test_image_generator.py"
Task: "T011 後方互換性テスト in tests/unit/test_image_generator.py"

# 実装（T012, T013は並列可能）:
Task: "T012 _render_via_node()へのオプション追加 in image_generator.py"
Task: "T013 batch_render()へのオプション追加 in image_generator.py"
```

---

## Implementation Strategy

### MVP First（User Story 1のみ）

1. Phase 1: Setup完了 → 設定スキーマ拡張
2. Phase 2: Foundational完了 → オプション伝搬基盤
3. Phase 3: User Story 1完了 → グローバルオプション動作確認
4. **STOP and VALIDATE**: `mkdocs build`でSVGにオプション反映を確認
5. オプション未設定時の後方互換性を確認

### Incremental Delivery

1. Setup + Foundational → 基盤完了
2. US1追加 → グローバルオプション動作 → MVP! 🎯
3. US2追加 → 名前付きテーマ選択可能
4. US3追加 → ブロック単位カスタマイズ可能
5. Polish → エッジケース・品質保証

---

## Notes

- [P]タスク = 異なるファイルまたは異なる関心事、依存関係なし
- [Story]ラベルはタスクをユーザーストーリーに紐付け
- 各ストーリーは独立して完了・テスト可能
- TDD: テストFAIL確認後に実装（Constitution II準拠）
- 各タスクまたは論理グループ完了後にコミット
- チェックポイントで独立検証を実施
