## コメント付与タスク指針
- 目的: `src/mkdocs_mermaid_to_svg/` 配下の主要モジュールに、Python未経験でも意図が追えるような簡潔なブロック単位のコメントを追加する。
- コメント粒度: 1関数1コメントより細かく、処理のまとまりごとに1〜2行で要点を記述する。言語仕様の解説は不要で、制御フローの理由やデータの流れに焦点を当てる。既存コメントとの重複は避ける。
- コメント言語: すべて日本語で記載する。専門用語は必要に応じて英単語併記可。
- 文体: 平易な日本語または簡潔な英語を許容。冗長さを避け、読み手がコード全体の意図と責務分担を素早く把握できるようにする。
- 作業手順: 対象ファイルごとに差分を確認しながらコメント候補を洗い出し → TDD指針に則り最小単位で編集 → `make check-all` でフォーマット・lint・テストを確認。

## ファイル別チェックリスト
- [x] `src/mkdocs_mermaid_to_svg/plugin.py`: MkDocsプラグインエントリ全体のデータフローと設定反映箇所を説明。
- [ ] `src/mkdocs_mermaid_to_svg/markdown_processor.py`: Markdown解析フロー、Mermaidブロック検出ロジックをブロック単位で解説。
- [ ] `src/mkdocs_mermaid_to_svg/image_generator.py`: Mermaid CLI呼び出しとSVG生成過程、キャッシュや外部コマンド失敗時の扱いを整理。
- [ ] `src/mkdocs_mermaid_to_svg/processor.py`: Processorクラスの責務分担、他コンポーネントとの連携ポイントをコメント化。
- [ ] `src/mkdocs_mermaid_to_svg/mermaid_block.py`: MermaidBlockデータ構造の役割と主要メソッドの意図を明文化。
- [ ] `src/mkdocs_mermaid_to_svg/config.py`: 設定値の読み込み・検証ロジックの要点を記述。
- [ ] `src/mkdocs_mermaid_to_svg/logging_config.py`: ロギング初期化処理の流れとログレベル制御箇所を説明。
- [ ] `src/mkdocs_mermaid_to_svg/utils.py`: 共通ユーティリティの用途と注意点を要約。
- [ ] `src/mkdocs_mermaid_to_svg/types.py`: 型エイリアス・プロトコルの役割を説明。
- [ ] `src/mkdocs_mermaid_to_svg/exceptions.py`: 例外クラスの使用シナリオをコメントで補足。
- [ ] `src/mkdocs_mermaid_to_svg/_version.py`: バージョン情報の管理方針を明記（変更が必要な場合のみ）。
- [ ] `src/mkdocs_mermaid_to_svg/__init__.py`: 公開APIの意図を簡潔に記載（必要なら）。

このTODOを起点に、セッションが変わっても同じ手順でコメント追加作業を継続する。
