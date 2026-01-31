# Research: beautiful-mermaidレンダリングオプション

**Date**: 2026-01-31 | **Feature**: 001-beautiful-mermaid-options

## R-001: MkDocs設定スキーマでのネスト辞書サポート

**Decision**: MkDocsの`config_options.Type(dict)`を使用してbeautiful-mermaidオプションを辞書として受け取る。各オプションは`beautiful_mermaid`プレフィックス付きの個別フラットキーとして定義する。

**Rationale**: MkDocsの設定システムは`mkdocs.config.config_options`モジュールの型クラスを使用する。`Type(dict)`はYAMLの辞書構造をそのまま受け取れるが、個別キーの型バリデーションが効かない。一方、個別の`Optional(Type(str))`/`Optional(Type(int))`/`Optional(Type(bool))`として定義すれば、MkDocsの設定バリデーション機構が型チェックを自動で行う。

**Alternatives considered**:
- ネスト辞書（`Type(dict)`1つ）: バリデーションが弱い。却下。
- 個別フラットキー（`beautiful_mermaid_bg`, `beautiful_mermaid_fg`等）: MkDocs標準のバリデーション活用可能だが、キー名が冗長。
- **採用案**: `beautiful_mermaid`プレフィックス付き個別キー。MkDocsの既存パターン（`css_file`, `puppeteer_config`等）と一貫性があり、型安全。

## R-002: 既存theme設定の拡張方法

**Decision**: `theme`設定の`Choice`バリデーションを`OptionallyRequired(Type(str))`に変更し、mmdc用テーマ名とbeautiful-mermaid用テーマ名の両方を自由文字列として受け付ける。バリデーションはランタイムで実施する。

**Rationale**: 現在の`Choice(("default", "dark", "forest", "neutral"))`はmmdc固定のテーマリストのみ許可する。beautiful-mermaidのテーマ名（`tokyo-night`, `catppuccin-mocha`等）を追加すると選択肢が膨大になり、beautiful-mermaid側のテーマ追加のたびにプラグインの更新が必要になる。自由文字列にして、不正なテーマ名はランナー側で`DEFAULTS`にフォールバックする既存の仕組みを活用する。

**Alternatives considered**:
- Choice拡張（全テーマ名をハードコード）: beautiful-mermaid側との同期コスト大。却下。
- 別キー`beautiful_mermaid_theme`: Clarificationで「既存theme拡張」に決定済み。却下。

## R-003: snake_case → camelCaseマッピングの実装方法

**Decision**: image_generator.py内でペイロード構築時に定数マッピング辞書を使用して変換する。

**Rationale**: マッピングが必要なのは`node_spacing` → `nodeSpacing`と`layer_spacing` → `layerSpacing`の2つのみ。他のオプション名（`bg`, `fg`, `font`, `padding`, `transparent`等）はsnake_caseとcamelCaseが同一。定数辞書で明示的にマッピングすることで、将来のオプション追加時にも対応箇所が明確。

**Alternatives considered**:
- 自動変換関数（snake_to_camel）: 汎用的だが、2つの変換のために過剰。却下。
- ランナー側でマッピング: Python側で完結させた方が型安全。却下。

## R-004: ブロック属性とグローバル設定のマージ戦略

**Decision**: グローバル設定をベースにブロック属性で上書きする辞書マージ方式。マージはprocessor.pyの`_collect_for_batch()`内で実施し、`BatchRenderItem`に結合済みオプションとして渡す。

**Rationale**: 既存のtheme上書き（`block.attributes.get("theme", config.get("theme"))`）と同じパターンを拡張する。マージをprocessor層で一元化することで、image_generator層はマージ済みオプションをそのまま使用できる。

**Alternatives considered**:
- image_generator層でマージ: processor層で既にthemeマージしているため一貫性が低い。却下。
- MermaidBlock内でマージ: ブロックがグローバル設定を知る必要があり、結合度が上がる。却下。

## R-005: beautiful_mermaid_runner.mjsでのオプション受け渡し

**Decision**: ペイロードJSONに`options`フィールドを追加し、ランナー内でテーマ解決後にスプレッド演算子でマージして`renderMermaid()`に渡す。

**Rationale**: beautiful-mermaidの`renderMermaid(code, options)`は第2引数に`RenderOptions`オブジェクトを受け取る。テーマ解決（`resolveTheme()`）で得たベースカラーに、ユーザー指定のオプションを上書きマージすれば、テーマ＋個別カスタマイズの両立が実現できる。

**Alternatives considered**:
- コマンドライン引数でオプション渡し: JSON構造の渡しに不向き。却下。
- 別プロセスでオプション処理: 不要な複雑化。却下。

## R-006: コンテンツハッシュとオプションの関係

**Decision**: SVGファイル名のMD5ハッシュ計算にレンダリングオプションも含める。同一Mermaidコードでも異なるオプションが指定された場合は別ファイルとして生成する。

**Rationale**: 現在のハッシュは`mermaid_code + theme`で計算される（`utils.generate_image_filename`）。オプション追加により同一コードでも異なるSVGが生成される可能性があるため、ハッシュにオプションを含めなければキャッシュの不整合が起きる。

**Alternatives considered**:
- ハッシュにオプションを含めない: キャッシュ不整合リスク。却下。
- オプションごとに別ディレクトリ: ファイル管理が複雑化。却下。
