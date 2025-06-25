"""
MkDocs Mermaid to Image Plugin - カスタム例外クラス定義ファイル

このファイルは、プラグインで使用されるカスタム例外クラスを定義します。
例外処理は、プログラムでエラーが発生した時に適切に対処するための仕組みです。

Python学習者へのヒント：
- Exceptionクラスを継承することで、独自の例外クラスを作成できます
- 例外クラスの階層構造を作ることで、エラーの種類に応じた処理が可能です
- passキーワードは「何もしない」という意味で、クラス定義時によく使われます
"""


class MermaidPreprocessorError(Exception):
    """
    Mermaidプリプロセッサ全体の基底例外クラス

    このクラスは、プラグイン内で発生する全ての例外の親クラスです。

    Python学習者へのヒント：
    - Exceptionクラスから継承することで、独自の例外を作成できます
    - 基底例外クラスを作ることで、プラグイン固有のエラーをまとめて捕捉できます

    使用例:
        try:
            # プラグインの処理
            pass
        except MermaidPreprocessorError as e:
            print(f"プラグインでエラーが発生しました: {e}")
    """

    pass


class MermaidCLIError(MermaidPreprocessorError):
    """
    Mermaid CLIコマンド実行時のエラー

    Mermaid CLIツール（mmdc）を実行した際に失敗した場合に発生します。

    発生する可能性がある状況：
    - Mermaid CLIがシステムにインストールされていない
    - CLIコマンドの実行がタイムアウトした
    - Mermaidコードの文法エラー
    - 画像生成処理での何らかの問題

    Python学習者へのヒント：
    - 外部コマンドを実行する際は、常に失敗の可能性を考慮する必要があります
    """

    pass


class MermaidConfigError(MermaidPreprocessorError):
    """
    プラグイン設定の検証エラー

    MkDocsの設定ファイル（mkdocs.yml）でのプラグイン設定に問題がある場合に発生します。

    発生する可能性がある状況：
    - 画像の幅や高さに負の値が設定されている
    - 指定されたCSSファイルが存在しない
    - 指定されたPuppeteer設定ファイルが存在しない
    - その他の設定値が不正

    Python学習者へのヒント：
    - 設定値の検証は、プログラムの安全性を保つために重要です
    - エラーメッセージは、ユーザーが問題を特定できるよう具体的にします
    """

    pass


class MermaidParsingError(MermaidPreprocessorError):
    """
    Mermaidコードの解析エラー

    Markdownファイル内のMermaidコードブロックを解析する際に問題が発生した場合に発生します。

    発生する可能性がある状況：
    - Mermaidコードブロックの構文が不正
    - 正規表現でのパターンマッチングが失敗
    - ファイルの文字エンコーディングの問題

    Python学習者へのヒント：
    - テキスト解析では、想定外の入力に対する堅牢性が重要です
    - 正規表現は強力ですが、複雑になりがちなので注意が必要です
    """

    pass
