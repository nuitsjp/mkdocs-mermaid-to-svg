"""
MkDocs Mermaid to Image Plugin - 統合機能テストスクリプト
"""

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
