"""
MkDocs Mermaid to Image Plugin - パッケージ初期化ファイル

このファイルは、MkDocs用のMermaid図画像変換プラグインのパッケージを初期化します。
主な機能：
- Markdownファイル内のMermaid図をCLIツールを使用して静的画像に変換
- 生成された画像でMermaidコードブロックを置換
- MkDocsのビルド処理に統合されたプリプロセッサとして動作

Python学習者へのヒント：
- __init__.pyファイルはPythonパッケージを定義するための特別なファイルです
- このファイルがあることで、ディレクトリがPythonパッケージとして認識されます
- __version__、__author__などの変数はパッケージのメタデータを定義する慣例です
"""

# パッケージのバージョン情報（セマンティックバージョニング形式）
__version__ = "1.0.0"

# パッケージの作成者情報
__author__ = "Claude Code Assistant"

# パッケージの簡単な説明
__description__ = "MkDocs plugin to preprocess Mermaid diagrams"
