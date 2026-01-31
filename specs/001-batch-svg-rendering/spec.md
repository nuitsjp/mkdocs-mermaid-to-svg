# Feature Specification: Beautiful-Mermaid一括SVG生成

**Feature Branch**: `001-batch-svg-rendering`
**Created**: 2026-01-31
**Status**: Draft
**Input**: User description: "一括生成することで起動プロセスを1回に減らして処理できるように改修します。"

## Clarifications

### Session 2026-01-31

- Q: 一括処理の収集単位はページ単位かビルド全体か？ → A: ビルド全体で一括処理。`on_page_markdown`でリクエストを収集し、`on_post_build`で1回のNode.jsプロセスにまとめてレンダリングする2フェーズ構成とする。
- Q: Node.jsプロセス全体がクラッシュした場合のフォールバック戦略は？ → A: ビルドをエラーで中断する。可能であればエラー原因となったページやダイアグラムを特定してエラーメッセージに含める（ベストエフォート）。

## User Scenarios & Testing *(mandatory)*

### User Story 1 - ビルド時間の短縮（Priority: P1）

ドキュメント作成者として、複数のMermaidダイアグラムを含むMkDocsプロジェクトをビルドする際、beautiful-mermaidレンダラーが全ダイアグラムをまとめて1回のNode.jsプロセスで処理することで、ビルド時間が大幅に短縮される。処理は2フェーズで行われる：`on_page_markdown`でダイアグラムの収集とMarkdownの書き換えを行い、`on_post_build`で一括レンダリングを実行する。

**Why this priority**: ダイアグラムごとにNode.jsプロセスを起動するオーバーヘッドが現在の主要なボトルネックであり、一括処理による改善がこの機能の核心的価値である。

**Independent Test**: 複数のMermaidダイアグラムを含むMkDocsプロジェクトをビルドし、beautiful-mermaidレンダラーのNode.jsプロセス起動回数が1回であること、および全ダイアグラムのSVGが正しく生成されることを確認する。

**Acceptance Scenarios**:

1. **Given** 5つのMermaidダイアグラムを含むMkDocsプロジェクト, **When** `mkdocs build`を実行する, **Then** beautiful-mermaidレンダラーのNode.jsプロセスは1回のみ起動され、5つすべてのSVGが正しく生成される
2. **Given** 複数ページにまたがるMermaidダイアグラムを含むプロジェクト, **When** ビルドを実行する, **Then** 全ページのダイアグラムが`on_page_markdown`で収集され、`on_post_build`で1回のNode.jsプロセスにまとめて処理される
3. **Given** 異なるテーマ設定を持つ複数のMermaidダイアグラム, **When** ビルドを実行する, **Then** 各ダイアグラムに指定されたテーマが正しく適用されたSVGが生成される

---

### User Story 2 - フォールバック動作の維持（Priority: P2）

ドキュメント作成者として、beautiful-mermaidが対応していないダイアグラム種別（pie、ganttなど）が含まれている場合でも、従来どおりmmdcへのフォールバックが正しく機能し、すべてのダイアグラムが確実にSVGに変換される。

**Why this priority**: 一括処理への移行により、既存のフォールバック機能が壊れないことを保証することは、後方互換性の観点から不可欠である。

**Independent Test**: beautiful-mermaid対応のダイアグラムと非対応のダイアグラムが混在するプロジェクトをビルドし、対応ダイアグラムは一括処理で、非対応ダイアグラムはmmdcフォールバックで処理されることを確認する。

**Acceptance Scenarios**:

1. **Given** flowchartとpieチャートが混在するページ, **When** ビルドを実行する, **Then** flowchartはbeautiful-mermaidで処理され、pieチャートはmmdcで処理され、両方とも正しいSVGが生成される
2. **Given** beautiful-mermaid一括処理中に1つのダイアグラムでエラーが発生する, **When** ビルドを実行する, **Then** エラーが発生したダイアグラムのみmmdcへフォールバックし、他の正常なダイアグラムの結果には影響しない

---

### User Story 3 - 生成結果の同一性（Priority: P2）

ドキュメント作成者として、一括処理モードで生成されたSVGが、従来の1件ずつ処理する方式と同一の出力結果になることで、移行時に見た目の変化が発生しない。

**Why this priority**: 既存ユーザーの成果物に影響を与えないことは、安心して更新を適用するために重要である。

**Independent Test**: 同一のMermaidダイアグラム群を従来方式と一括方式の両方で処理し、生成されたSVGの内容が一致することを確認する。

**Acceptance Scenarios**:

1. **Given** 既存のMermaidダイアグラム群, **When** 一括処理モードでSVGを生成する, **Then** 従来の個別処理モードと同一のSVG出力が得られる

---

### Edge Cases

- 一括処理に渡すダイアグラムが0件の場合、Node.jsプロセスを起動しないこと
- 一括処理中にNode.jsプロセスがクラッシュした場合、ビルドをエラーで中断し、可能であれば原因となったページやダイアグラムをエラーメッセージに含めること
- 非常に大きなダイアグラム（数千行）が含まれている場合でも処理が完了すること
- 一括処理のペイロードがプロセス間通信の制限を超える場合の動作
- `mkdocs serve`時には一括処理が実行されず、従来どおりMermaid fenceがそのまま残ること

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: beautiful-mermaidレンダラーは、ビルド全体で生成対象となるすべてのMermaidダイアグラムを`on_page_markdown`フェーズで収集し、`on_post_build`フェーズで1回のNode.jsプロセス起動にまとめて処理しなければならない
- **FR-002**: 一括処理のリクエストには、各ダイアグラムのMermaidコード、テーマ設定、および出力先情報が含まれなければならない
- **FR-003**: 一括処理の結果は、各ダイアグラムごとに成功/失敗を個別に判定できなければならない
- **FR-004**: 一括処理中に失敗したダイアグラムは、個別にmmdcフォールバックで再処理されなければならない
- **FR-005**: beautiful-mermaidが対応していないダイアグラム種別は、一括処理の対象から除外し、従来どおりmmdcで処理しなければならない
- **FR-006**: 一括処理で生成されるSVGは、従来の個別処理と同一の内容でなければならない
- **FR-007**: 処理対象のbeautiful-mermaidダイアグラムが0件の場合、Node.jsプロセスを起動してはならない
- **FR-008**: `on_page_markdown`フェーズではMarkdownの書き換え（画像参照への置換）とレンダリングリクエストの収集のみを行い、SVGの生成は行わない
- **FR-009**: Node.jsプロセス全体がクラッシュした場合、ビルドをエラーで中断しなければならない。エラーメッセージには可能な限りエラー原因となったページやダイアグラムの情報を含める（ベストエフォート）

### Key Entities

- **BatchRequest**: 一括処理のリクエスト。複数のダイアグラム情報（Mermaidコード、テーマ、識別子、出力先パス、ソースページ情報）を保持する
- **BatchResult**: 一括処理の結果。各ダイアグラムごとの成功/失敗ステータスと生成されたSVGデータを保持する

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: 10個のMermaidダイアグラムを含むプロジェクトのビルドにおいて、beautiful-mermaidのNode.jsプロセス起動回数が1回に削減される
- **SC-002**: 複数ダイアグラムを含むプロジェクトのビルド時間が、ダイアグラム数に比例して線形に増加しなくなる（プロセス起動オーバーヘッド分の改善）
- **SC-003**: 一括処理で生成されたSVGが、従来方式で生成されたSVGと100%同一の内容である
- **SC-004**: 一括処理中に一部のダイアグラムが失敗しても、他のダイアグラムの処理結果に影響がない

## Assumptions

- beautiful-mermaidのNode.jsランナー（`beautiful_mermaid_runner.mjs`）は、一括処理に対応するよう拡張可能である
- プロセス間通信（stdin/stdout）で複数ダイアグラムのペイロードを十分に扱える（通常のドキュメントプロジェクトで数百KB〜数MB程度を想定）
- 一括処理のペイロード形式はJSON配列で、各要素が従来の単一リクエストと同じ構造を持つ
- mmdcレンダラーは従来どおり個別処理のまま変更しない（一括化はbeautiful-mermaidのみ対象）
- `on_post_build`で生成したSVGファイルはビルド出力ディレクトリに直接書き出す
