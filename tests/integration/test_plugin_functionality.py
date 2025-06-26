"""
MkDocs Mermaid to Image Plugin - 統合機能テストスクリプト
"""

import sys
from unittest.mock import Mock, patch

from mkdocs_mermaid_to_image.config import ConfigManager
from mkdocs_mermaid_to_image.plugin import MermaidToImagePlugin
from mkdocs_mermaid_to_image.processor import MermaidProcessor
from mkdocs_mermaid_to_image.utils import (
    generate_image_filename,
    is_command_available,
    setup_logger,
)


def test_plugin_initialization():
    """プラグインの初期化テスト"""
    plugin = MermaidToImagePlugin()
    assert plugin is not None


def test_processor_functionality():
    """Mermaidプロセッサの機能テスト"""
    config = {
        "mmdc_path": "mmdc",
        "output_dir": "assets/images",
        "image_format": "png",
        "theme": "default",
        "background_color": "white",
        "width": 800,
        "height": 600,
        "scale": 1.0,
        "css_file": None,
        "puppeteer_config": None,
        "mermaid_config": None,
        "cache_enabled": True,
        "cache_dir": ".mermaid_cache",
        "preserve_original": False,
        "error_on_fail": False,
        "log_level": "INFO",
    }
    processor = MermaidProcessor(config)
    markdown_content = """# Test

```mermaid
graph TD
    A --> B
```

Some text.

```mermaid {theme: dark}
sequenceDiagram
    Alice->>Bob: Hello
```
"""
    blocks = processor.markdown_processor.extract_mermaid_blocks(markdown_content)
    assert len(blocks) == 2
    assert "graph TD" in blocks[0].code
    assert "sequenceDiagram" in blocks[1].code


def test_config_validation():
    """設定検証機能のテスト"""
    valid_config = {
        "width": 800,
        "height": 600,
        "scale": 1.0,
        "css_file": None,
        "puppeteer_config": None,
    }
    assert ConfigManager.validate_config(valid_config) is True


def test_utils():
    """ユーティリティ関数のテスト"""
    filename = generate_image_filename("test.md", 0, "graph TD\n A --> B", "png")
    assert filename.endswith(".png")
    assert "test_mermaid_0_" in filename

    logger = setup_logger("test", "INFO")
    assert logger is not None

    result = is_command_available("python3")
    assert result is True


def test_serve_mode_integration():
    """serve モード統合テスト - 実際のワークフローを模擬"""

    # Test 1: serve モードでの完全なワークフロー
    with patch.object(sys, "argv", ["mkdocs", "serve"]):
        # プラグイン初期化
        plugin = MermaidToImagePlugin()
        assert plugin.is_serve_mode is True

        # 設定を模擬
        plugin.config = {
            "enabled": True,
            "output_dir": "assets/images",
            "image_format": "png",
            "mmdc_path": "mmdc",
            "theme": "default",
            "background_color": "white",
            "width": 800,
            "height": 600,
            "scale": 1.0,
            "css_file": None,
            "puppeteer_config": None,
            "mermaid_config": None,
            "cache_enabled": True,
            "cache_dir": ".mermaid_cache",
            "preserve_original": False,
            "error_on_fail": False,
            "log_level": "INFO",
        }

        # プロセッサを模擬（実際には初期化されない想定）
        plugin.processor = Mock()
        plugin.logger = Mock()

        # Mockページとconfig
        mock_page = Mock()
        mock_page.file.src_path = "example.md"
        mock_config = {"docs_dir": "/docs"}

        # 複数のMermaidブロックを含むMarkdown
        test_markdown = """
# サンプルページ

## フローチャート

```mermaid
graph TD
    A[開始] --> B{条件分岐}
    B -->|Yes| C[処理A]
    B -->|No| D[処理B]
    C --> E[終了]
    D --> E
```

## シーケンス図

```mermaid
sequenceDiagram
    participant A as Alice
    participant B as Bob
    A->>B: Hello Bob
    B-->>A: Hello Alice
```

通常のテキストコンテンツ
"""

        # ページ処理実行
        result = plugin.on_page_markdown(
            test_markdown, page=mock_page, config=mock_config, files=[]
        )

        # 検証
        assert result == test_markdown  # 元のMarkdownがそのまま返される
        plugin.processor.process_page.assert_not_called()  # プロセッサが呼ばれない
        plugin.logger.debug.assert_called_once()  # デバッグログが記録される
        assert len(plugin.generated_images) == 0  # 画像は生成されない


def test_build_mode_integration():
    """build モード統合テスト - 実際のワークフローを模擬"""

    # Test 2: build モードでの完全なワークフロー
    with patch.object(sys, "argv", ["mkdocs", "build"]):
        # プラグイン初期化
        plugin = MermaidToImagePlugin()
        assert plugin.is_serve_mode is False

        # 設定を模擬
        plugin.config = {
            "enabled": True,
            "output_dir": "assets/images",
            "error_on_fail": False,
        }

        # プロセッサを模擬して成功ケースを再現
        mock_processor = Mock()
        mock_processor.process_page.return_value = (
            """
# サンプルページ

## フローチャート

<img alt="Mermaid Diagram" src="assets/images/example_mermaid_0_abc123.png" />

## シーケンス図

<img alt="Mermaid Diagram" src="assets/images/example_mermaid_1_def456.png" />

通常のテキストコンテンツ
""".strip(),
            [
                "assets/images/example_mermaid_0_abc123.png",
                "assets/images/example_mermaid_1_def456.png",
            ],
        )
        plugin.processor = mock_processor
        plugin.logger = Mock()

        # Mockページとconfig
        mock_page = Mock()
        mock_page.file.src_path = "example.md"
        mock_config = {"docs_dir": "/docs"}

        # 複数のMermaidブロックを含むMarkdown
        test_markdown = """
# サンプルページ

## フローチャート

```mermaid
graph TD
    A[開始] --> B{条件分岐}
    B -->|Yes| C[処理A]
    B -->|No| D[処理B]
    C --> E[終了]
    D --> E
```

## シーケンス図

```mermaid
sequenceDiagram
    participant A as Alice
    participant B as Bob
    A->>B: Hello Bob
    B-->>A: Hello Alice
```

通常のテキストコンテンツ
"""

        # ページ処理実行
        result = plugin.on_page_markdown(
            test_markdown, page=mock_page, config=mock_config, files=[]
        )

        # 検証
        assert "assets/images/example_mermaid_0_abc123.png" in result
        assert "assets/images/example_mermaid_1_def456.png" in result
        plugin.processor.process_page.assert_called_once()  # プロセッサが呼ばれる
        assert len(plugin.generated_images) == 2  # 2つの画像が記録される
        plugin.logger.info.assert_called_once()  # 情報ログが記録される


def test_mixed_command_scenarios():
    """様々なコマンドシナリオでのserve検出テスト"""

    # gh-deploy コマンド
    with patch.object(sys, "argv", ["mkdocs", "gh-deploy", "--force"]):
        plugin = MermaidToImagePlugin()
        assert plugin.is_serve_mode is False

    # serve コマンド（詳細オプション付き）
    with patch.object(
        sys, "argv", ["mkdocs", "serve", "--dev-addr", "0.0.0.0:8000", "--livereload"]
    ):
        plugin = MermaidToImagePlugin()
        assert plugin.is_serve_mode is True

    # build コマンド（クリーンオプション付き）
    with patch.object(sys, "argv", ["mkdocs", "build", "--clean"]):
        plugin = MermaidToImagePlugin()
        assert plugin.is_serve_mode is False


def test_serve_mode_performance_optimization():
    """serve モードでのパフォーマンス最適化効果の検証"""

    with patch.object(sys, "argv", ["mkdocs", "serve"]):
        plugin = MermaidToImagePlugin()
        plugin.config = {"enabled": True}
        plugin.processor = Mock()
        plugin.logger = Mock()

        # 大量のMermaidブロックを含むMarkdown（パフォーマンステスト用）
        large_markdown = "# Test Page\n\n"
        for i in range(10):  # 10個のMermaidブロック
            large_markdown += f"""
## Diagram {i}
```mermaid
graph TD
    A{i} --> B{i}
    B{i} --> C{i}
```
"""

        mock_page = Mock()
        mock_page.file.src_path = "large_page.md"
        mock_config = {"docs_dir": "/docs"}

        # ページ処理実行
        result = plugin.on_page_markdown(
            large_markdown, page=mock_page, config=mock_config, files=[]
        )

        # パフォーマンス最適化の検証
        assert result == large_markdown  # 元のMarkdownがそのまま返される
        # 重い画像生成処理がスキップされる
        plugin.processor.process_page.assert_not_called()
        assert len(plugin.generated_images) == 0  # 画像生成なし
