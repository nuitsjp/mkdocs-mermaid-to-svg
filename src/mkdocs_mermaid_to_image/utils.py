"""
MkDocs Mermaid to Image Plugin - ユーティリティ関数ファイル

このファイルは、プラグイン全体で使用される共通のユーティリティ関数を提供します。
主な機能：
- ログ設定とログ出力の管理
- 画像ファイル名の生成
- ディレクトリの作成と管理
- 一時ファイルの操作
- パス操作とファイル操作
- 外部コマンドの可用性チェック

Python学習者へのヒント：
- utilsファイルは、複数のモジュールで共通して使用される小さな関数をまとめる慣例です
- from typing import ...は型ヒントを使用するためのインポートです
- 関数には型ヒント（引数の型と戻り値の型）を付けることで、コードの可読性が向上します
"""

import hashlib  # ハッシュ値計算のための標準ライブラリ（ファイル名生成に使用）
import logging  # ログ出力のための標準ライブラリ
import os  # ファイル・ディレクトリ操作のための標準ライブラリ
import tempfile  # 一時ファイル作成のための標準ライブラリ
from pathlib import Path  # より便利なパス操作のための標準ライブラリ
from shutil import which  # whichコマンド相当の機能


def setup_logger(name: str, log_level: str = "INFO") -> logging.Logger:
    """
    プラグイン用のロガーを設定・取得する関数

    Args:
        name (str): ロガーの名前（通常は__name__を使用）
        log_level (str): ログレベル（'DEBUG', 'INFO', 'WARNING', 'ERROR'）
                        デフォルトは'INFO'

    Returns:
        logging.Logger: 設定されたロガーオブジェクト

    Python学習者へのヒント：
    - loggingは、print()の代わりに使用する本格的なログ出力システムです
    - ログレベルにより、出力される情報の詳細度を制御できます
    - ハンドラー（handler）は、ログの出力先を決定します（コンソール、ファイルなど）
    - フォーマッター（formatter）は、ログメッセージの表示形式を決定します

    使用例:
        logger = setup_logger(__name__, 'DEBUG')
        logger.info("処理を開始します")
        logger.error("エラーが発生しました")
    """
    # 指定された名前のロガーを取得（既存の場合は再利用）
    logger = logging.getLogger(name)

    # ハンドラーが未設定の場合のみ設定（重複設定を防ぐ）
    if not logger.handlers:
        # コンソール出力用のハンドラーを作成
        handler = logging.StreamHandler()

        # ログメッセージのフォーマットを定義
        # %(asctime)s = 日時, %(name)s = ロガー名
        # %(levelname)s = ログレベル, %(message)s = メッセージ
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)

    # ログレベルを設定（getattr関数で文字列から対応する定数を取得）
    logger.setLevel(getattr(logging, log_level.upper()))
    return logger


def generate_image_filename(
    page_file: str, block_index: int, mermaid_code: str, image_format: str
) -> str:
    """
    Mermaid画像用の一意なファイル名を生成する関数

    Args:
        page_file (str): 元のMarkdownファイルのパス
        block_index (int): ページ内でのMermaidブロックの順番（0から開始）
        mermaid_code (str): Mermaidのコード内容
        image_format (str): 画像形式（'png', 'svg'など）

    Returns:
        str: 生成された画像ファイル名

    Python学習者へのヒント：
    - Path(page_file).stemで、ファイル名から拡張子を除いた部分を取得できます
    - hashlib.md5()でMD5ハッシュ値を計算し、同じコードからは同じハッシュが生成されます
    - [:8]でハッシュの最初の8文字のみを使用（ファイル名の短縮のため）
    - f文字列（f"..."）を使用することで、変数を埋め込んだ文字列を簡潔に作成できます

    使用例:
        filename = generate_image_filename('docs/index.md', 0, 'graph TD\nA-->B', 'png')
        # 結果例: 'index_mermaid_0_a1b2c3d4.png'
    """
    # ファイル名から拡張子を除いた部分を取得
    page_name = Path(page_file).stem

    # Mermaidコードのハッシュ値を計算（同じコードなら同じファイル名になる）
    code_hash = hashlib.md5(  # nosec B324
        mermaid_code.encode("utf-8")
    ).hexdigest()[:8]

    # ファイル名を組み立て（ページ名_mermaid_ブロック番号_ハッシュ.拡張子）
    return f"{page_name}_mermaid_{block_index}_{code_hash}.{image_format}"


def ensure_directory(directory: str) -> None:
    """
    ディレクトリが存在することを保証する関数（存在しない場合は作成）

    Args:
        directory (str): 作成するディレクトリのパス

    Returns:
        None: 戻り値なし

    Python学習者へのヒント：
    - pathlib.Pathを使用することで、OS依存のパス操作を統一的に扱えます
    - mkdir(parents=True)で、中間ディレクトリも含めて作成できます
    - exist_ok=Trueで、既にディレクトリが存在していてもエラーになりません
    - -> Noneは、この関数が値を返さないことを示す型ヒントです

    使用例:
        ensure_directory('assets/images')
        # 'assets'ディレクトリと'images'ディレクトリが作成される
    """
    Path(directory).mkdir(parents=True, exist_ok=True)


def get_temp_file_path(suffix: str = ".mmd") -> str:
    """
    一時ファイルのパスを生成する関数

    Args:
        suffix (str): ファイルの拡張子（デフォルトは'.mmd'）

    Returns:
        str: 生成された一時ファイルのパス

    Python学習者へのヒント：
    - tempfile.mkstemp()は、一意な一時ファイルを作成します
    - 戻り値は(ファイル記述子, パス)のタプルです
    - ファイル記述子は即座にclose()して、パスのみを使用します
    - 一時ファイルは、処理完了後に削除する必要があります

    使用例:
        temp_path = get_temp_file_path('.txt')
        print(f"一時ファイル: {temp_path}")
    """
    # 一時ファイルを作成（ファイル記述子とパスを取得）
    fd, path = tempfile.mkstemp(suffix=suffix)

    # ファイル記述子を即座にclose（パスのみが必要なため）
    os.close(fd)

    return path


def clean_temp_file(file_path: str) -> None:
    """
    一時ファイルを安全に削除する関数

    Args:
        file_path (str): 削除するファイルのパス

    Returns:
        None: 戻り値なし

    Python学習者へのヒント：
    - try-except文を使用することで、エラーが発生しても処理を継続できます
    - os.path.exists()でファイルの存在を確認してから削除します
    - OSErrorは、ファイル操作で発生する可能性のある例外です
    - passは「何もしない」を意味し、例外を無視する場合に使用します

    使用例:
        clean_temp_file('/tmp/temp_file.mmd')
        # ファイルが存在する場合は削除、存在しない場合は何もしない
    """
    try:
        # ファイルが存在する場合のみ削除を実行
        if Path(file_path).exists():
            Path(file_path).unlink()
    except OSError:
        # ファイル削除でエラーが発生しても処理を継続
        # （権限不足、ファイルがロックされている等）
        pass


def get_relative_path(file_path: str, base_path: str) -> str:
    """
    基準パスからファイルパスへの相対パスを計算する関数

    Args:
        file_path (str): 対象ファイルのパス
        base_path (str): 基準となるパス

    Returns:
        str: 相対パス（計算できない場合は元のfile_pathを返す）

    Python学習者へのヒント：
    - os.path.relpath()は、あるパスから別のパスへの相対パスを計算します
    - try-except文で例外処理を行い、計算に失敗した場合は元のパスを返します
    - ValueError例外は、異なるドライブ間（Windows）などで発生する可能性があります

    使用例:
        image_file = '/home/user/project/images/diagram.png'
        base_dir = '/home/user/project/docs'
        rel_path = get_relative_path(image_file, base_dir)
        # 結果: '../images/diagram.png'
    """
    try:
        # 基準パスからファイルパスへの相対パスを計算
        return os.path.relpath(file_path, base_path)
    except ValueError:
        # 相対パス計算に失敗した場合は、元のファイルパスをそのまま返す
        # （異なるドライブ間での計算など）
        return file_path


def is_command_available(command: str) -> bool:
    """
    指定されたコマンドがシステムのPATHで利用可能かチェックする関数

    Args:
        command (str): チェックするコマンド名

    Returns:
        bool: コマンドが利用可能な場合True、そうでない場合False

    Python学習者へのヒント：
    - shutil.which()は、コマンドの実行可能ファイルのパスを検索します
    - コマンドが見つからない場合はNoneを返します
    - 「is not None」で、Noneでない（つまりコマンドが見つかった）かを判定します
    - ファイルのトップレベルでimportしてローカルでも使用する手法です

    使用例:
        if is_command_available('mmdc'):
            print("Mermaid CLIが利用可能です")
        else:
            print("Mermaid CLIがインストールされていません")
    """
    return which(command) is not None  # コマンドが見つかればTrue、見つからなければFalse
