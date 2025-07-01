"""
共通テストフィクスチャとユーティリティ

このファイルは、テストファイル間で共有される共通のフィクスチャを定義します。
重複したモック設定を削減し、テストコードの保守性を向上させることが目的です。
"""

from unittest.mock import Mock, patch

import pytest


@pytest.fixture
def mock_mermaid_block():
    """Mermaidブロックのモックを返すフィクスチャ"""
    mock_block = Mock()
    mock_block.get_filename.return_value = "test_0_abc123.png"
    mock_block.generate_image.return_value = True
    mock_block.get_image_markdown.return_value = "![Mermaid](test_0_abc123.png)"
    mock_block.index = 0
    mock_block.mermaid_code = "graph TD\n    A --> B"
    return mock_block


@pytest.fixture
def mock_failed_mermaid_block():
    """画像生成に失敗するMermaidブロックのモック"""
    mock_block = Mock()
    mock_block.get_filename.return_value = "test_0_abc123.png"
    mock_block.generate_image.return_value = False
    mock_block.get_image_markdown.return_value = "![Mermaid](test_0_abc123.png)"
    mock_block.index = 0
    mock_block.mermaid_code = "graph TD\n    A --> B"
    return mock_block


@pytest.fixture
def basic_config():
    """基本的な設定辞書を返すフィクスチャ"""
    return {
        "enabled": True,
        "output_dir": "assets/mermaid",
        "image_format": "png",
        "mmdc_path": "mmdc",
        "theme": "default",
        "background_color": "white",
        "width": 800,
        "height": 600,
        "scale": 1.0,
        "css_file": None,
        "puppeteer_config": None,
        "error_on_fail": False,
        "log_level": "INFO",
    }


@pytest.fixture
def mock_config():
    """MkDocsの設定オブジェクトのモック"""
    config = Mock()
    config.__getitem__ = Mock(
        side_effect=lambda key: {
            "docs_dir": "/tmp/docs",
            "site_dir": "/tmp/site",
        }.get(key)
    )
    return config


@pytest.fixture
def mock_page():
    """MkDocsのPageオブジェクトのモック"""
    page = Mock()
    page.file = Mock()
    page.file.src_path = "test.md"
    page.file.dest_path = "test.html"
    page.title = "Test Page"
    return page


@pytest.fixture
def mock_logger():
    """ロガーオブジェクトのモック"""
    logger = Mock()
    return logger


@pytest.fixture
def mock_command_available():
    """コマンド利用可能性チェックのモック（利用可能）"""
    with patch("mkdocs_mermaid_to_image.image_generator.is_command_available") as mock:
        mock.return_value = True
        yield mock


@pytest.fixture
def mock_command_unavailable():
    """コマンド利用可能性チェックのモック（利用不可）"""
    with patch("mkdocs_mermaid_to_image.image_generator.is_command_available") as mock:
        mock.return_value = False
        yield mock


@pytest.fixture
def mock_subprocess_success():
    """サブプロセス実行成功のモック"""
    with patch("subprocess.run") as mock:
        mock.return_value = Mock(returncode=0, stderr="")
        yield mock


@pytest.fixture
def mock_subprocess_failure():
    """サブプロセス実行失敗のモック"""
    with patch("subprocess.run") as mock:
        mock.return_value = Mock(returncode=1, stderr="Error: Invalid syntax")
        yield mock


@pytest.fixture
def mock_file_operations():
    """ファイル操作のモック（存在するファイル用）"""
    mocks = {}
    with (
        patch("pathlib.Path.exists") as mock_exists,
        patch("pathlib.Path.unlink") as mock_unlink,
    ):
        mock_exists.return_value = True
        mocks["exists"] = mock_exists
        mocks["unlink"] = mock_unlink
        yield mocks


@pytest.fixture
def mock_file_not_exists():
    """ファイル操作のモック（存在しないファイル用）"""
    with patch("pathlib.Path.exists") as mock_exists:
        mock_exists.return_value = False
        yield mock_exists


@pytest.fixture
def mock_temp_file():
    """一時ファイル操作のモック"""
    with (
        patch("mkdocs_mermaid_to_image.utils.get_temp_file_path") as mock_temp_path,
        patch("mkdocs_mermaid_to_image.utils.clean_temp_file") as mock_clean,
    ):
        mock_temp_path.return_value = "/tmp/test.mmd"
        yield {"temp_path": mock_temp_path, "clean": mock_clean}


@pytest.fixture
def mock_processor_with_command(basic_config):
    """コマンド利用可能なプロセッサのモックフィクスチャ"""
    from mkdocs_mermaid_to_image.processor import MermaidProcessor

    with patch(
        "mkdocs_mermaid_to_image.image_generator.is_command_available"
    ) as mock_cmd:
        mock_cmd.return_value = True
        processor = MermaidProcessor(basic_config)
        yield processor, mock_cmd


@pytest.fixture
def mock_processor_without_command(basic_config):
    """コマンド利用不可なプロセッサのモックフィクスチャ"""
    from mkdocs_mermaid_to_image.processor import MermaidProcessor

    with patch(
        "mkdocs_mermaid_to_image.image_generator.is_command_available"
    ) as mock_cmd:
        mock_cmd.return_value = False
        try:
            processor = MermaidProcessor(basic_config)
        except Exception:
            processor = None
        yield processor, mock_cmd


@pytest.fixture
def sample_markdown_content():
    """サンプルMarkdownコンテンツ"""
    return """# Test Document

Some text here.

```mermaid
graph TD
    A[Start] --> B{Decision}
    B -->|Yes| C[End]
    B -->|No| D[Continue]
```

More text here.

```mermaid
sequenceDiagram
    Alice->>Bob: Hello Bob
    Bob-->>Alice: Hello Alice
```

Final text.
"""


@pytest.fixture
def sample_mermaid_code():
    """サンプルMermaidコード"""
    return """graph TD
    A[Start] --> B{Decision}
    B -->|Yes| C[End]
    B -->|No| D[Continue]
"""


@pytest.fixture
def mock_ci_environment():
    """CI環境のモック"""
    with patch("os.getenv") as mock_getenv:
        mock_getenv.side_effect = lambda key: {
            "CI": "true",
            "GITHUB_ACTIONS": "true",
        }.get(key)
        yield mock_getenv


@pytest.fixture
def mock_non_ci_environment():
    """非CI環境のモック"""
    with patch("os.getenv") as mock_getenv:
        mock_getenv.return_value = None
        yield mock_getenv
