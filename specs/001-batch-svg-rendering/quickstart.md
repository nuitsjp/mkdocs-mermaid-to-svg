# Quickstart: Beautiful-Mermaid一括SVG生成

**Feature**: 001-batch-svg-rendering
**Date**: 2026-01-31

## 概要

この機能は、beautiful-mermaidレンダラーでのSVG生成をダイアグラムごとの個別処理から、ビルド全体での一括処理に変更する。ユーザーから見た動作は従来と同一（設定変更不要）。

## 変更対象ファイル

### Python側（4ファイル）

1. **`plugin.py`** — `on_files`でBatchRenderRequestを初期化、`on_page_markdown`で収集、`on_post_build`で一括レンダリング実行
2. **`processor.py`** — beautiful-mermaid対応ダイアグラムの収集モードを追加（SVG生成を遅延）
3. **`image_generator.py`** — `BeautifulMermaidRenderer`にバッチレンダリングメソッドを追加
4. **`exceptions.py`** — `BatchRenderingError`を追加（オプション）

### JavaScript側（1ファイル）

5. **`beautiful_mermaid_runner.mjs`** — `--batch-render`モードを追加

## 実装の流れ（開発順序）

### Step 1: Node.jsランナーの一括対応
`beautiful_mermaid_runner.mjs`に`--batch-render`モードを追加する。

```
入力: stdin経由のJSON配列
出力: stdout経由のJSON配列（各要素にid/success/svg/error）
```

### Step 2: Python側のバッチレンダリングメソッド
`BeautifulMermaidRenderer`に`batch_render`メソッドを追加する。

```
入力: list[BatchRenderItem]
処理: 1回のsubprocess.runでNode.js --batch-renderを呼び出し
出力: list[BatchRenderResult]
```

### Step 3: プロセッサの2フェーズ対応
`processor.py`を拡張し、beautiful-mermaid対応ダイアグラムの処理を遅延させる。

```
収集フェーズ: ブロック抽出→対応判別→BatchRenderItemに追加→Markdown書き換え
レンダリングフェーズ: 外部から呼び出して一括処理を実行
```

### Step 4: プラグインの統合
`plugin.py`を変更し、2フェーズ処理を統合する。

```
on_files: BatchRenderRequest初期化
on_page_markdown: 収集フェーズ実行
on_post_build: 一括レンダリング実行→SVGファイル書き出し→フォールバック処理
```

## テストの流れ

各ステップでTDD（Red-Green-Refactor）を実施:

1. **Step 1**: Node.jsランナーのテスト（subprocess呼び出しでJSON入出力を確認）
2. **Step 2**: `batch_render`メソッドのユニットテスト（モックsubprocess）
3. **Step 3**: プロセッサの収集モードテスト
4. **Step 4**: プラグイン統合テスト（E2E）

## 確認コマンド

```bash
make test          # 全テスト実行
make test-unit     # ユニットテストのみ
make check-all     # フォーマット + リント + 型チェック + pre-commit
make build         # MkDocsビルドで動作確認
```
