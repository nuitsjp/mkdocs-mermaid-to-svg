## コメント付与タスク指針
- 目的: `src/mkdocs_mermaid_to_svg/` 配下の主要モジュールに、Python未経験でも意図が追えるような簡潔なブロック単位のコメントを追加する。
- コメント粒度: 1関数1コメントより細かく、処理のまとまりごとに1〜2行で要点を記述する。言語仕様の解説は不要で、制御フローの理由やデータの流れに焦点を当てる。既存コメントとの重複は避ける。
- コメント言語: すべて日本語で記載する。専門用語は必要に応じて英単語併記可。
- docstring: 不足している箇所は追加し、関数やクラスの責務を端的に説明する。
- 既存コメント: 英語表記があれば日本語へ置き換え、内容の正確性を再確認した上で必要に応じて訂正する。
- 文体: 平易な日本語または簡潔な英語を許容。冗長さを避け、読み手がコード全体の意図と責務分担を素早く把握できるようにする。
- 作業手順: 対象ファイルごとに差分を確認しながらコメント候補を洗い出し → TDD指針に則り最小単位で編集 → `make check-all` でフォーマット・lint・テストを確認。

## ファイル別チェックリスト
- [x] `src/mkdocs_mermaid_to_svg/plugin.py`: コメント・docstring でエントリ処理と設定反映箇所を説明済み。
- [x] `src/mkdocs_mermaid_to_svg/markdown_processor.py`: コメント・docstringで抽出と置換の流れを説明済み。
- [x] `src/mkdocs_mermaid_to_svg/image_generator.py`: コメント・docstringで生成フローと失敗時処理を整理済み。
- [x] `src/mkdocs_mermaid_to_svg/processor.py`: コメント・docstringで連携フローを整理済み。
- [x] `src/mkdocs_mermaid_to_svg/mermaid_block.py`: コメント・docstringでデータ構造と役割を明文化済み。
- [x] `src/mkdocs_mermaid_to_svg/config.py`: docstringで設定スキーマと検証の役割を明文化済み。
- [x] `src/mkdocs_mermaid_to_svg/logging_config.py`: コメント・docstringでロギング初期化の流れを説明済み。
- [x] `src/mkdocs_mermaid_to_svg/utils.py`: コメント・docstringでユーティリティの用途を説明済み。
- [x] `src/mkdocs_mermaid_to_svg/types.py`: docstringでログ用TypedDictの役割を説明済み。
- [x] `src/mkdocs_mermaid_to_svg/exceptions.py`: docstringで例外クラスの役割と文脈を説明済み。
- [x] `src/mkdocs_mermaid_to_svg/_version.py`: 自動生成ファイルである旨を日本語コメントで明記済み。
- [x] `src/mkdocs_mermaid_to_svg/__init__.py`: モジュールdocstringで公開情報の意図を明記済み。

このTODOを起点に、セッションが変わっても同じ手順でコメント追加作業を継続する。
