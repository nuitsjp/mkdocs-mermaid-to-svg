# Research: Beautiful-Mermaid一括SVG生成

**Feature**: 001-batch-svg-rendering
**Date**: 2026-01-31

## R-001: Node.jsランナーの一括処理対応方式

**Decision**: `--batch-render`モードを`beautiful_mermaid_runner.mjs`に追加し、stdin経由でJSON配列を受け取り、各ダイアグラムを順次レンダリングしてJSON配列でstdoutに返す。

**Rationale**:
- 既存の`--render`モードとの後方互換性を維持できる
- stdinからJSON配列を読み、配列の各要素を既存の`renderMermaid`関数で処理するだけなので、実装が最小限
- 各ダイアグラムのレンダリングを`try/catch`で個別に囲むことで、1つの失敗が他に影響しない
- stdout出力もJSON配列にすることで、Python側でのパースが容易

**Alternatives considered**:
- **長時間稼働プロセス（REPL方式）**: Node.jsを常駐させ、各ダイアグラムを逐次送信する。実装が複雑で、プロセスのライフサイクル管理が必要になるため不採用
- **並列ワーカー方式**: Node.jsのworker_threadsで並列処理する。beautiful-mermaidがheadless Chromiumを使うため、並列化による効果が限定的で複雑性が高いため不採用
- **ファイルベース方式**: 入力を一時ファイルに書き出し、結果もファイルから読む。I/Oオーバーヘッドとクリーンアップの手間が増えるため不採用

## R-002: 一括処理のペイロード形式

**Decision**: 入出力ともにJSON形式を使用する。

入力形式（stdin → Node.js）:
```json
[
  {"code": "<mermaid code>", "theme": "default", "id": "page_mermaid_0_abc12345"},
  {"code": "<mermaid code>", "theme": "dark", "id": "page_mermaid_1_def67890"}
]
```

出力形式（Node.js → stdout）:
```json
[
  {"id": "page_mermaid_0_abc12345", "success": true, "svg": "<svg>...</svg>"},
  {"id": "page_mermaid_1_def67890", "success": false, "error": "Syntax error in mermaid code"}
]
```

**Rationale**:
- `id`フィールドでリクエストと結果を1:1で対応付けられる
- `success`フラグで個別の成功/失敗を判定でき、失敗分のみmmdcフォールバック可能
- 既存の単一レンダリングと同じ`code`/`theme`構造を再利用
- JSON配列はstdin/stdoutで自然に扱える

**Alternatives considered**:
- **NDJSON（改行区切りJSON）**: ストリーミング処理には向くが、エラー時の状態管理が複雑になるため不採用
- **MessagePack等のバイナリ形式**: パフォーマンス上の利点はあるが、デバッグ性が低下するため不採用

## R-003: 2フェーズ処理のアーキテクチャ

**Decision**: `on_page_markdown`で収集、`on_post_build`でバッチレンダリング＋ファイル書き出しの2フェーズ構成とする。

**Phase 1（収集フェーズ: `on_page_markdown`）**:
1. Mermaidブロックを抽出
2. beautiful-mermaid対応のダイアグラムを判別
3. 対応ダイアグラム: BatchRequestに追加し、ファイル名を事前決定してMarkdownを書き換え
4. 非対応ダイアグラム（pie、gantt等）: 従来どおりその場でmmdcで処理
5. 修正済みMarkdownを返す（SVGファイルはまだ存在しない）

**Phase 2（レンダリングフェーズ: `on_post_build`）**:
1. 収集したBatchRequestが空なら何もしない
2. 1回のNode.jsプロセスでバッチレンダリング実行
3. 成功した結果をSVGファイルとしてビルド出力ディレクトリに書き出す
4. 失敗したダイアグラムはmmdcフォールバックで再処理
5. プロセス全体のクラッシュ時はビルドエラーとする

**Rationale**:
- MkDocsの`on_page_markdown`はMarkdownの変換前に呼ばれるため、画像参照への書き換えはこの段階で行う必要がある
- `on_post_build`は全ページ処理後に呼ばれるため、全ダイアグラムの収集が完了している
- ファイル名はMD5ハッシュにより決定的に算出できるため、SVGファイルが存在しない時点でもMarkdownの書き換えが可能

**Alternatives considered**:
- **`on_page_markdown`内で全ページ分を待つ**: MkDocsのイベントモデル上不可能
- **`on_env`での処理**: テンプレートレンダリング前だが、Markdownはすでに変換済みのため不適切

## R-004: SVGファイルの書き出し先

**Decision**: `on_post_build`でSVGをビルド出力ディレクトリ（`site/`配下）に直接書き出す。

**Rationale**:
- `on_post_build`時点ではMkDocsのファイルコピーは完了しているため、`docs/`配下に書いてもビルド出力に反映されない
- `on_page_markdown`でMarkdownに埋め込む画像パスは、最終的な`site/`内のパスと一致する必要がある
- 既存の`output_dir`設定（デフォルト: `assets/images`）を基に、`site/{output_dir}/`にSVGを書き出す
- HTMLからの相対パスが正しく解決される

**Alternatives considered**:
- **`docs/`配下に書き出してMkDocsにコピーさせる**: `on_post_build`時点ではコピー済みのため不可
- **`on_page_markdown`で仮ファイルを作成**: ファイルが2回書かれることになり非効率

## R-005: 既存テストとの互換性

**Decision**: 既存のテストスイートを維持しつつ、一括処理に関するテストを追加する。

**Rationale**:
- 既存の個別処理パス（mmdcレンダラー）はそのまま動作するため、既存テストは変更不要
- beautiful-mermaidの一括処理は新しいテストで検証
- SVGゴールデンテスト（`REGENERATE_SVG_GOLDENS=1`）は一括処理でも同一出力を保証するために活用
- integrationテストではビルド全体を通したE2Eテストを追加

**Alternatives considered**: 特になし。テスト追加のみで後方互換性を維持するのが最善。
