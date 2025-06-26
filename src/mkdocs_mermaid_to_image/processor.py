"""
MkDocs Mermaid to Image Plugin - メインプロセッサー

このファイルは、リファクタリング後のメインプロセッサーです。
各コンポーネントを統合して、ページ全体の処理を管理します。
"""

from pathlib import Path
from typing import Any

from .image_generator import MermaidImageGenerator
from .markdown_processor import MarkdownProcessor
from .utils import setup_logger


class MermaidProcessor:
    """
    Mermaid図の処理を統合管理するメインクラス

    リファクタリング後は、各専門クラスを組み合わせて
    ページ全体の処理フローを管理する責任のみを持ちます。
    """

    def __init__(self, config: dict[str, Any]) -> None:
        """
        MermaidProcessorのコンストラクタ

        Args:
            config (dict): プラグインの設定情報
        """
        self.config = config
        self.logger = setup_logger(__name__, config.get("log_level", "INFO"))

        # 各専門クラスを初期化
        self.markdown_processor = MarkdownProcessor(config)
        self.image_generator = MermaidImageGenerator(config)

    def process_page(
        self, page_file: str, markdown_content: str, output_dir: str
    ) -> tuple[str, list[str]]:
        """
        単一ページを処理し、変更されたコンテンツと生成された画像パスを返す

        Args:
            page_file (str): 処理対象のページファイルパス
            markdown_content (str): ページのMarkdownコンテンツ
            output_dir (str): 画像の出力ディレクトリ

        Returns:
            Tuple[str, List[str]]: (変更されたMarkdown, 生成された画像パスのリスト)
        """
        # 1. Markdownからmermaidブロックを抽出
        blocks = self.markdown_processor.extract_mermaid_blocks(markdown_content)

        # ブロックが見つからない場合は何もしない
        if not blocks:
            return markdown_content, []

        # 2. 各ブロックに対して画像を生成
        image_paths = []
        successful_blocks = []

        for i, block in enumerate(blocks):
            # 画像ファイル名を生成
            image_filename = block.get_filename(
                page_file, i, self.config["image_format"]
            )
            image_path = Path(output_dir) / image_filename

            # ブロック自身に画像生成を依頼
            success = block.generate_image(
                str(image_path), self.image_generator, self.config
            )

            if success:
                image_paths.append(str(image_path))
                successful_blocks.append(block)
            elif not self.config["error_on_fail"]:
                self.logger.warning(
                    "Keeping original Mermaid block due to generation failure"
                )
                # 失敗したブロックは処理対象から除外
                continue
            else:
                # error_on_failがTrueの場合は例外が既に発生している
                pass

        # 3. 成功したブロックがある場合のみ置換処理を実行
        if successful_blocks:
            modified_content = self.markdown_processor.replace_blocks_with_images(
                markdown_content, successful_blocks, image_paths, page_file
            )
            return modified_content, image_paths

        # すべてのブロックで画像生成に失敗した場合は元のコンテンツを返す
        return markdown_content, []


# 後方互換性のために旧クラスもエクスポート
# 新しい構造では実際にはmermaid_block.pyにあります
