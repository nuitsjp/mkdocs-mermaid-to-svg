# Tasks: Beautiful-Mermaid一括SVG生成

**Input**: Design documents from `/specs/001-batch-svg-rendering/`
**Prerequisites**: plan.md (required), spec.md (required), research.md, data-model.md, quickstart.md

**Tests**: TDD（t-wada流 Red-Green-Refactor）に従い、各タスクでテストを先行して作成する。ConstitutionのII. テスト基準に準拠。

**Organization**: タスクはユーザーストーリー単位で編成。各ストーリーは独立して実装・テスト可能。

## Format: `[ID] [P?] [Story] Description`

- **[P]**: 並列実行可能（異なるファイル、依存関係なし）
- **[Story]**: 所属するユーザーストーリー（US1, US2, US3）
- ファイルパスは正確に記載

---

## Phase 1: Setup（共通基盤）

**Purpose**: データモデルの定義と例外クラスの追加

- [ ] T001 [P] BatchRenderItem・BatchRenderResultのdataclassを定義する in `src/mkdocs_mermaid_to_svg/image_generator.py`（data-model.mdのエンティティ定義に基づく。id, code, theme, output_path, page_fileフィールドを持つBatchRenderItem。id, success, svg, errorフィールドを持つBatchRenderResult）
- [ ] T002 [P] BatchRenderItem・BatchRenderResultの単体テストを作成する in `tests/unit/test_batch_renderer.py`（フィールドの初期化、バリデーションルールの検証）

**Checkpoint**: データモデルが定義され、テストが通ること。`make test-unit && make check-all` で確認。

---

## Phase 2: Foundational（全ストーリーの前提）

**Purpose**: Node.jsランナーの一括処理対応とPython側のバッチレンダリングメソッド

**⚠️ CRITICAL**: US1〜US3のすべてがこのフェーズに依存する

- [ ] T003 beautiful_mermaid_runner.mjsのテーマ解決ロジックを共通関数`resolveTheme()`に抽出する in `src/mkdocs_mermaid_to_svg/beautiful_mermaid_runner.mjs`（既存の`--render`モードのthemeMap/THEMES/DEFAULTS解決を関数化。既存動作は変更しない）
- [ ] T004 beautiful_mermaid_runner.mjsに`--batch-render`モードを追加する in `src/mkdocs_mermaid_to_svg/beautiful_mermaid_runner.mjs`（stdin経由でJSON配列を受信、各要素を`resolveTheme()`＋`renderMermaid()`で処理、個別try/catchでエラー分離、結果をJSON配列でstdoutに出力。data-model.mdのNode.js Runner Protocolに準拠）
- [ ] T005 `--batch-render`モードの動作テストを作成する in `tests/unit/test_batch_renderer.py`（subprocess経由でNode.jsを呼び出し、JSON配列入出力の正常系・エラー系・空配列・テーマ指定を検証）
- [ ] T006 BeautifulMermaidRendererに`batch_render`メソッドを追加する in `src/mkdocs_mermaid_to_svg/image_generator.py`（`list[BatchRenderItem]`を受け取り、1回のsubprocess.runで`node beautiful_mermaid_runner.mjs --batch-render`を呼び出し、`list[BatchRenderResult]`を返す。プロセスクラッシュ時はMermaidCLIErrorを送出。空リストの場合はNode.jsを起動せず空リストを返す）
- [ ] T007 `batch_render`メソッドの単体テストを作成する in `tests/unit/test_batch_renderer.py`（正常系：複数ダイアグラムの一括処理、異常系：プロセスクラッシュ時のMermaidCLIError、境界：空リストでNode.js未起動、テーマオーバーライドの反映。subprocessをモックして検証）

**Checkpoint**: Node.jsランナーが`--batch-render`で動作し、Python側の`batch_render`メソッドが正しくJSON入出力を処理すること。`make test-unit && make check-all` で確認。

---

## Phase 3: User Story 1 - ビルド時間の短縮（Priority: P1）🎯 MVP

**Goal**: `on_page_markdown`でbeautiful-mermaid対応ダイアグラムを収集し、`on_post_build`で1回のNode.jsプロセスにまとめてレンダリングする2フェーズ処理を実装する

**Independent Test**: 複数のMermaidダイアグラムを含むプロジェクトをビルドし、Node.jsプロセス起動が1回であること、全SVGが正しく生成されることを確認

### Tests for User Story 1

> **NOTE: テストを先に書き、FAILすることを確認してから実装する**

- [ ] T008 [P] [US1] プロセッサの収集モードの単体テストを作成する in `tests/unit/test_processor.py`（beautiful-mermaid対応ブロックがBatchRenderItemとして収集されること、非対応ブロックは従来どおり即時処理されること、Markdownが画像参照に書き換えられること、SVGファイルは生成されないこと）
- [ ] T009 [P] [US1] プラグインの2フェーズ処理の単体テストを作成する in `tests/unit/test_plugin.py`（`on_files`でbatch_itemsが初期化されること、`on_page_markdown`でbatch_itemsに収集されること、`on_post_build`でbatch_renderが呼ばれること、空のbatch_itemsではNode.jsが起動しないこと）

### Implementation for User Story 1

- [ ] T010 [US1] processor.pyにbeautiful-mermaid対応ブロックの判別と収集ロジックを追加する in `src/mkdocs_mermaid_to_svg/processor.py`（`process_page`メソッドを拡張し、`batch_items: list[BatchRenderItem] | None`パラメータを追加。Noneの場合は従来動作。指定時はbeautiful-mermaid対応ブロックをbatch_itemsに追加し、Markdownを画像参照に書き換えるがSVG生成はスキップ。非対応ブロックは従来どおりmmdcで即時処理。`BeautifulMermaidRenderer.is_available()`で対応判別）
- [ ] T011 [US1] plugin.pyのon_filesでbatch_itemsを初期化する in `src/mkdocs_mermaid_to_svg/plugin.py`（`self.batch_items: list[BatchRenderItem] = []`を`on_files`で初期化）
- [ ] T012 [US1] plugin.pyのon_page_markdownで収集モードを使用するよう変更する in `src/mkdocs_mermaid_to_svg/plugin.py`（`_process_mermaid_diagrams`を変更し、`processor.process_page`に`batch_items=self.batch_items`を渡す）
- [ ] T013 [US1] plugin.pyのon_post_buildで一括レンダリングを実行する in `src/mkdocs_mermaid_to_svg/plugin.py`（batch_itemsが空でなければ`BeautifulMermaidRenderer.batch_render()`を呼び出し、成功結果をsite/配下のoutput_pathにSVGファイルとして書き出す。生成画像をgenerated_imagesに追加。ログ出力）

**Checkpoint**: 複数ダイアグラムでNode.js起動が1回に削減され、全SVGが正しく生成されること。`make test && make check-all` で確認。

---

## Phase 4: User Story 2 - フォールバック動作の維持（Priority: P2）

**Goal**: beautiful-mermaid非対応ダイアグラムのmmdcフォールバックと、一括処理中の個別失敗時のフォールバックを実装する

**Independent Test**: beautiful-mermaid対応/非対応が混在するプロジェクトで、全ダイアグラムがSVGに変換されることを確認

### Tests for User Story 2

> **NOTE: テストを先に書き、FAILすることを確認してから実装する**

- [ ] T014 [P] [US2] 個別失敗時のmmdcフォールバックの単体テストを作成する in `tests/unit/test_batch_renderer.py`（batch_renderの結果でsuccess=falseのダイアグラムがmmdcで再処理されること、成功分のSVGは影響を受けないこと）
- [ ] T015 [P] [US2] プロセスクラッシュ時のビルドエラーの単体テストを作成する in `tests/unit/test_batch_renderer.py`（Node.jsプロセス全体がクラッシュした場合にMermaidCLIErrorが送出されビルドが中断すること、エラーメッセージにページ情報が含まれること）

### Implementation for User Story 2

- [ ] T016 [US2] on_post_buildにバッチ結果の失敗分のmmdcフォールバック処理を追加する in `src/mkdocs_mermaid_to_svg/plugin.py`（BatchRenderResultのsuccess=falseの項目を特定し、対応するBatchRenderItemのcode/theme/output_pathを使ってMmdcRendererで個別にSVGを再生成。フォールバック成功時はSVGをsite/配下に書き出す）
- [ ] T017 [US2] on_post_buildにプロセスクラッシュ時のエラーハンドリングを追加する in `src/mkdocs_mermaid_to_svg/plugin.py`（batch_render()がMermaidCLIErrorを送出した場合、エラーメッセージにbatch_itemsのpage_file情報を含めてビルドを中断。ベストエフォートでエラー原因のページを特定）

**Checkpoint**: 対応/非対応混在プロジェクトで全ダイアグラムがSVGに変換され、個別失敗時もフォールバックが動作すること。`make test && make check-all` で確認。

---

## Phase 5: User Story 3 - 生成結果の同一性（Priority: P2）

**Goal**: 一括処理で生成されたSVGが従来の個別処理と同一の内容であることを保証する

**Independent Test**: 同一ダイアグラムを一括方式と個別方式で処理し、SVG出力が一致することを確認

### Tests for User Story 3

> **NOTE: テストを先に書き、FAILすることを確認してから実装する**

- [ ] T018 [US3] 一括処理と個別処理のSVG出力同一性テストを作成する in `tests/unit/test_batch_renderer.py`（同じMermaidコード・テーマで、`_render_via_node`（個別）と`batch_render`（一括）の出力SVGが完全一致すること。flowchart、sequence、class、er、stateの各ダイアグラム種別で確認）

### Implementation for User Story 3

- [ ] T019 [US3] 一括処理のテーマ解決が個別処理と同一であることを検証・修正する in `src/mkdocs_mermaid_to_svg/beautiful_mermaid_runner.mjs`（`--batch-render`の各要素で`resolveTheme()`が`--render`と同じテーマ解決結果を返すことを確認。差異があれば修正）

**Checkpoint**: 一括処理と個別処理のSVG出力が100%一致すること。`make test && make check-all` で確認。

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: 全ストーリーを横断する改善とエッジケースの対応

- [ ] T020 [P] エッジケーステストを追加する in `tests/unit/test_batch_renderer.py`（0件ダイアグラムでNode.js未起動、大規模ダイアグラム（数千行）の処理、serve時の非実行）
- [ ] T021 [P] 統合テストを作成する in `tests/integration/test_batch_integration.py`（複数ページにまたがるMermaidダイアグラムの一括処理E2Eテスト。`@pytest.mark.integration`マーカー付与）
- [ ] T022 既存テストの回帰確認と品質チェックを実行する（`make test && make check-all && make check-security`。既存テストがすべて通ること、型チェック・リント・セキュリティ検査に問題がないこと）

---

## Dependencies & Execution Order

### Phase Dependencies

- **Phase 1（Setup）**: 依存なし — 即時開始可能
- **Phase 2（Foundational）**: Phase 1に依存 — データモデルが定義されている必要あり
- **Phase 3（US1）**: Phase 2に依存 — Node.jsランナーとbatch_renderメソッドが必要
- **Phase 4（US2）**: Phase 3に依存 — 2フェーズ処理の基本動作が前提
- **Phase 5（US3）**: Phase 2に依存 — batch_renderが存在すれば検証可能（US1と並列可能だがUS1後が望ましい）
- **Phase 6（Polish）**: Phase 3〜5に依存

### User Story Dependencies

- **US1（P1）**: Phase 2完了後に開始可能。他ストーリーに依存しない
- **US2（P2）**: US1のon_post_build処理に依存（フォールバック追加のため）
- **US3（P2）**: Phase 2完了後に検証可能。US1の実装は不要だが、統合後の確認が望ましい

### Within Each User Story

- テストを先に書きFAILを確認 → 実装 → テスト通過 → リファクタリング
- processor.py → plugin.py の順（収集ロジック → 統合）
- 各タスク完了後に`make test && make check-all`

### Parallel Opportunities

- T001, T002: 並列実行可能（dataclass定義とテスト）
- T008, T009: 並列実行可能（異なるテストファイル）
- T014, T015: 並列実行可能（同一ファイル内の独立テスト）
- T020, T021: 並列実行可能（異なるテストファイル）

---

## Implementation Strategy

### MVP First（User Story 1のみ）

1. Phase 1: Setup → dataclass定義
2. Phase 2: Foundational → Node.jsランナー + batch_renderメソッド
3. Phase 3: US1 → 2フェーズ処理の実装
4. **STOP and VALIDATE**: 複数ダイアグラムでNode.js起動が1回であることを確認
5. `make build` で実プロジェクトの動作確認

### Incremental Delivery

1. Setup + Foundational → 基盤完成
2. US1実装 → 一括処理の基本動作確認（MVP）
3. US2実装 → フォールバック動作の完全性確認
4. US3実装 → 出力同一性の保証
5. Polish → エッジケース・統合テスト・品質チェック

---

## Notes

- [P]タスク = 異なるファイル、依存関係なし
- [Story]ラベル = 所属ユーザーストーリーのトレーサビリティ
- 各ユーザーストーリーは独立して完成・テスト可能
- テストはFAILを確認してから実装（TDD）
- 各タスクまたは論理グループ完了後にコミット
- チェックポイントで`make test && make check-all`を実行
