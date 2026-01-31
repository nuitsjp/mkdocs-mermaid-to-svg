# Feature Specification: beautiful-mermaidレンダリングオプションの設定サポート

**Feature Branch**: `001-beautiful-mermaid-options`
**Created**: 2026-01-31
**Status**: Draft
**Input**: User description: "サブモジュールの @beautiful-mermaid で生成できるようにオプションを追加しました。ただ、beautiful-mermaidで利用できるオプションが現在は全く指定できません。オプションを指定できるように設定を追加してください。"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - グローバルレンダリングオプションの設定 (Priority: P1)

ドキュメント作成者として、`mkdocs.yml`でbeautiful-mermaidのレンダリングオプション（背景色、前景色、フォント、パディング、ノード間隔、レイヤー間隔、透過背景）をグローバルに設定し、サイト全体のMermaid図に統一的なスタイルを適用したい。

**Why this priority**: サイト全体で統一されたスタイルを適用することは最も基本的なニーズであり、個別ページでのカスタマイズよりも先に実現すべき機能。

**Independent Test**: `mkdocs.yml`にbeautiful-mermaidオプションを設定し、`mkdocs build`を実行してSVG出力に設定値が反映されることを確認できる。

**Acceptance Scenarios**:

1. **Given** `mkdocs.yml`に`beautiful_mermaid`セクションでオプション（例: `bg: "#1a1a2e"`, `fg: "#e0e0e0"`, `font: "Noto Sans JP"`）を設定している、**When** `mkdocs build`を実行する、**Then** 生成されるSVGにこれらのスタイル設定が反映される
2. **Given** `mkdocs.yml`にbeautiful-mermaidオプションが設定されていない、**When** `mkdocs build`を実行する、**Then** beautiful-mermaidのデフォルト値が使用され、既存の動作と同じ結果になる
3. **Given** `mkdocs.yml`に`beautiful_mermaid`セクションで`transparent: true`を設定している、**When** `mkdocs build`を実行する、**Then** 生成されるSVGの背景が透過になる

---

### User Story 2 - 名前付きテーマパレットの選択 (Priority: P2)

ドキュメント作成者として、beautiful-mermaidが提供する名前付きテーマパレット（例: `tokyo-night`, `catppuccin-mocha`, `nord`など）をグローバル設定で選択し、プリセットされたカラースキームを簡単に適用したい。

**Why this priority**: 名前付きテーマは個別の色設定よりも手軽で、多くのユーザーにとって十分な選択肢を提供する。P1のグローバル設定基盤の上に構築される。

**Independent Test**: `mkdocs.yml`で名前付きテーマ（例: `theme: tokyo-night`）を設定し、ビルドしてテーマの色が正しく反映されることを確認できる。

**Acceptance Scenarios**:

1. **Given** `mkdocs.yml`に`beautiful_mermaid.theme: "tokyo-night"`を設定している、**When** `mkdocs build`を実行する、**Then** tokyo-nightテーマのカラーパレットでSVGが生成される
2. **Given** `mkdocs.yml`に名前付きテーマと個別の色設定（例: `theme: nord`, `bg: "#000000"`）の両方が設定されている、**When** `mkdocs build`を実行する、**Then** 名前付きテーマをベースに個別設定が上書きされる

---

### User Story 3 - コードブロック単位でのオプション上書き (Priority: P3)

ドキュメント作成者として、特定のMermaidコードブロックに対してグローバル設定と異なるレンダリングオプションを指定し、ページごとや図ごとにスタイルをカスタマイズしたい。

**Why this priority**: 個別のカスタマイズは高度な使い方であり、まずグローバル設定が安定してから対応すべき。

**Independent Test**: グローバル設定がある状態で、特定のコードブロックに属性を付与し、そのブロックだけ異なるスタイルで出力されることを確認できる。

**Acceptance Scenarios**:

1. **Given** グローバルに`bg: "#FFFFFF"`が設定されており、特定のMermaidブロックに`{bg: "#000000"}`属性が付与されている、**When** `mkdocs build`を実行する、**Then** そのブロックのSVGは黒背景で生成され、他のブロックは白背景のまま
2. **Given** グローバルに`font: "Inter"`が設定されており、特定のMermaidブロックに`{font: "Noto Sans JP"}`属性が付与されている、**When** `mkdocs build`を実行する、**Then** そのブロックのSVGは"Noto Sans JP"フォントで生成される

---

### Edge Cases

- 無効なオプション名が指定された場合、ビルド時に警告を表示し無視する
- 無効な色コード（例: `bg: "not-a-color"`）が指定された場合、警告を表示しデフォルト値にフォールバックする
- 存在しない名前付きテーマが指定された場合、エラーメッセージを表示しデフォルトテーマを使用する
- renderer設定が`mmdc`の場合、beautiful-mermaid固有のオプションは無視される（`mmdc`はこれらのオプションに対応しない）
- バッチレンダリング時にも各ブロックのオプションが正しく反映される
- beautiful-mermaid専用テーマ（例: `tokyo-night`）が指定された状態でmmdcレンダラーにフォールバックした場合、警告を表示しmmdcのデフォルトテーマを使用する

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: システムは`mkdocs.yml`のプラグイン設定でbeautiful-mermaidのレンダリングオプション（`bg`, `fg`, `font`, `padding`, `node_spacing`, `layer_spacing`, `transparent`）をsnake_case命名でグローバルに指定できなければならない。プラグインはこれらをbeautiful-mermaid側のcamelCase名（`nodeSpacing`, `layerSpacing`）に内部でマッピングする
- **FR-002**: システムは`mkdocs.yml`のプラグイン設定でbeautiful-mermaidのカラーエンリッチメントオプション（`line`, `accent`, `muted`, `surface`, `border`）をグローバルに指定できなければならない
- **FR-003**: システムは既存の`theme`設定を拡張し、mmdc用テーマ（`default`, `dark`, `forest`, `neutral`）に加えてbeautiful-mermaidの名前付きテーマパレット（`tokyo-night`, `catppuccin-mocha`, `nord`など）も同じ`theme`キーで選択できなければならない。使用中のレンダラーに応じて適切なテーマが適用される
- **FR-004**: 名前付きテーマと個別の色設定が同時に指定された場合、システムは名前付きテーマをベースに個別設定で上書きしなければならない
- **FR-005**: システムはMermaidコードブロックの属性（`{key: "value"}`記法）でブロック単位のレンダリングオプション上書きをサポートしなければならない
- **FR-006**: ブロック単位のオプションはグローバル設定より優先されなければならない
- **FR-007**: beautiful-mermaid固有のオプションが指定された状態で`mmdc`レンダラーが使用される場合、システムはこれらのオプションを警告付きで無視しなければならない
- **FR-008**: 無効なオプション値が指定された場合、システムは警告をログに出力しデフォルト値にフォールバックしなければならない
- **FR-009**: beautiful-mermaidオプションが未設定の場合、システムは既存の動作と完全に後方互換でなければならない
- **FR-010**: バッチレンダリング時にも各ブロックのオプションが正しく個別に渡されなければならない

### Key Entities

- **レンダリングオプション**: beautiful-mermaidに渡される設定値の集合（色、フォント、間隔、透過など）
- **名前付きテーマパレット**: beautiful-mermaidが内蔵するプリセットカラーセット（例: tokyo-night, nord）
- **ブロック属性**: 個別のMermaidコードブロックに付与される設定上書き値

## Clarifications

### Session 2026-01-31

- Q: mkdocs.yml設定キーの命名規則（snake_case vs camelCase）はどちらにするか？ → A: snake_case（`node_spacing`, `layer_spacing`）— MkDocs/Python慣例に準拠。beautiful-mermaid側のcamelCase（`nodeSpacing`, `layerSpacing`）へのマッピングはプラグイン内部で行う。
- Q: 既存の`theme`設定とbeautiful-mermaidテーマの共存方法は？ → A: 既存`theme`設定を拡張し、mmdc用テーマもbeautiful-mermaid用テーマも同じ`theme`キーで指定する。レンダラーに応じて適切なテーマが選択される。

## Assumptions

- beautiful-mermaidのRenderOptionsインターフェース（`bg`, `fg`, `line`, `accent`, `muted`, `surface`, `border`, `font`, `padding`, `nodeSpacing`, `layerSpacing`, `transparent`）は安定しており、破壊的変更なく利用可能
- beautiful-mermaid側のテーマパレット名は安定している（テーマの追加はあっても既存テーマの削除・改名はない）
- 既存のMarkdownブロック属性パーサー（`markdown_processor.py`）は新しい属性キーの追加に対応可能
- `mkdocs.yml`のプラグイン設定セクションにネスト構造（`beautiful_mermaid:`以下のオプション）を追加可能

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: ユーザーが`mkdocs.yml`の設定のみで、beautiful-mermaidの全レンダリングオプションを制御でき、設定変更からビルド結果確認まで通常のワークフローで完結する
- **SC-002**: 既存のプロジェクトでbeautiful-mermaidオプションを未設定のまま使用した場合、ビルド結果が変更前と完全に一致する（後方互換性）
- **SC-003**: 名前付きテーマの指定により、個別の色設定なしでサイト全体の図の見た目を一括変更できる
- **SC-004**: 全てのbeautiful-mermaidレンダリングオプション（12種類）がプラグイン設定として公開され、文書化されている
