"""Pytest configuration and fixtures."""

import logging
import os
import tempfile
from collections.abc import Iterator
from pathlib import Path
from typing import Any

import pytest
from template_package.core.example import ExampleClass, ExampleConfig
from template_package.utils.logging_config import set_log_level


@pytest.fixture
def example_config() -> ExampleConfig:
    """Create a test configuration."""
    return ExampleConfig(
        name="test",
        max_items=10,
        enable_validation=True,
    )


@pytest.fixture
def example_instance(example_config: ExampleConfig) -> ExampleClass:
    """Create a test ExampleClass instance."""
    return ExampleClass(example_config)


@pytest.fixture
def sample_data() -> list[dict[str, Any]]:
    """Create sample data for testing."""
    return [
        {"id": 1, "name": "Item 1", "value": 100},
        {"id": 2, "name": "Item 2", "value": 200},
        {"id": 3, "name": "Item 3", "value": 300},
    ]


@pytest.fixture
def temp_dir() -> Iterator[Path]:
    """Create a temporary directory for testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture(autouse=True)
def reset_environment(monkeypatch: pytest.MonkeyPatch) -> None:
    """Reset environment variables for each test."""
    # Remove any test-specific environment variables
    test_env_vars = [var for var in os.environ if var.startswith("TEST_")]
    for var in test_env_vars:
        monkeypatch.delenv(var, raising=False)


@pytest.fixture(scope="session")
def setup_test_logging() -> None:
    """Setup basic logging for test session."""
    # テスト中は標準ライブラリのロギングを使用
    import logging

    log_level = os.environ.get("TEST_LOG_LEVEL", "INFO")
    logging.basicConfig(
        level=getattr(logging, log_level),
        format="[%(levelname)s] %(name)s: %(message)s",
        force=True,
    )


@pytest.fixture
def capture_logs(caplog: pytest.LogCaptureFixture) -> pytest.LogCaptureFixture:
    """Capture logs for testing with proper level."""
    # テスト用にログレベルを設定
    caplog.set_level(logging.DEBUG)
    return caplog


@pytest.fixture
def set_test_log_level():
    """Fixture to dynamically set log level in tests."""

    def _set_level(level: str | int) -> None:
        set_log_level(level)

    return _set_level


# pytestの起動時にロギングを設定
def pytest_configure(config: pytest.Config) -> None:
    """Configure pytest with structured logging setup."""
    # テスト実行時の最小限のログ設定
    log_level = os.environ.get("TEST_LOG_LEVEL", "INFO")  # DEBUGだと詳細すぎる

    # 標準ライブラリのロギングのみを使用（structlogの問題を回避）
    import logging

    logging.basicConfig(
        level=getattr(logging, log_level),
        format="[%(levelname)s] %(name)s: %(message)s",
        force=True,
    )
