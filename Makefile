.PHONY: help test test-cov test-unit test-property test-integration format lint typecheck security audit check check-all check-security benchmark profile setup pr issue clean install-dev serve build build-pdf mmdc-version mmdc-version-npx

# デフォルトターゲット
help:
	@echo "Usage: make [target]"
	@echo ""
	@echo "Available targets:"
	@echo "  setup        - セットアップ（依存関係インストール、pre-commit設定）"
	@echo "  install-dev  - 開発用に編集可能モードでパッケージをインストール"
	@echo "  sync         - 全依存関係を同期"
	@echo "  test         - 全テスト実行（単体・プロパティ・統合）"
	@echo "  test-cov     - カバレッジ付きテスト実行"
	@echo "  test-unit    - 単体テストのみ実行"
	@echo "  test-property - プロパティベーステストのみ実行"
	@echo "  test-integration - 統合テストのみ実行"
	@echo "  format       - コードフォーマット（ruff format）"
	@echo "  lint         - リントチェック（ruff check --fix）"
	@echo "  typecheck    - 型チェック（mypy）"
	@echo "  security     - セキュリティチェック（bandit）"
	@echo "  audit        - 依存関係の脆弱性チェック（pip-audit）"
	@echo "  benchmark    - パフォーマンスベンチマーク実行"
	@echo "  check        - 品質チェック（format + lint + typecheck）"
	@echo "  check-security - セキュリティチェック（security + audit）"
	@echo "  check-all    - 完全チェック（pre-commitフック全実行）"
	@echo "  serve        - MkDocs開発サーバー起動"
	@echo "  build        - MkDocsドキュメントビルド"
	@echo "  build-pdf    - PDF生成付きMkDocsビルド"
	@echo "  mmdc-version - Mermaid CLIバージョン確認"
	@echo "  mmdc-version-npx - npx経由でMermaid CLIバージョン確認"
	@echo "  pr           - PR作成 (TITLE=\"タイトル\" BODY=\"本文\" [LABEL=\"ラベル\"])"
	@echo "  issue        - イシュー作成 (TITLE=\"タイトル\" BODY=\"本文\" [LABEL=\"ラベル\"])"
	@echo "  clean        - キャッシュファイルの削除"

# セットアップ
setup:
	chmod +x scripts/setup.sh && ./scripts/setup.sh

install-dev:
	uv pip install -e .

sync:
	uv sync --all-extras

# テスト関連
test:
	uv run pytest

test-cov:
	uv run pytest --cov=src --cov-report=html --cov-report=term

test-unit:
	uv run pytest tests/unit/ -v

test-property:
	uv run pytest tests/property/ -v

test-integration:
	uv run pytest tests/integration/ -v

# コード品質チェック
format:
	uv run ruff format . --config=pyproject.toml

lint:
	uv run ruff check . --fix --config=pyproject.toml

typecheck:
	uv run mypy src/ --strict

security:
	uv run bandit -r src/

audit:
	uv run pip-audit

# パフォーマンス測定
benchmark:
	@echo "Running performance benchmarks..."
	@if [ -f benchmark_suite.py ]; then \
		uv run pytest benchmark_suite.py --benchmark-only --benchmark-autosave; \
	else \
		echo "Creating benchmark suite..."; \
		echo 'import pytest\nfrom project_name.utils.helpers import chunk_list\n\ndef test_chunk_list_benchmark(benchmark):\n    data = list(range(1000))\n    result = benchmark(chunk_list, data, 10)\n    assert len(result) == 100' > benchmark_suite.py; \
		uv add --dev pytest-benchmark; \
		uv run pytest benchmark_suite.py --benchmark-only --benchmark-autosave; \
	fi

# 統合チェック
check: format lint typecheck
	@echo "Quality checks completed"

check-all:
	uv run pre-commit run --all-files

check-security: security audit
	@echo "Security checks completed"

# GitHub操作
pr:
	@if [ -z "$(TITLE)" ]; then \
		echo "Error: TITLE is required. Usage: make pr TITLE=\"タイトル\" BODY=\"本文\" [LABEL=\"ラベル\"]"; \
		exit 1; \
	fi
	@if [ -z "$(BODY)" ]; then \
		echo "Error: BODY is required. Usage: make pr TITLE=\"タイトル\" BODY=\"本文\" [LABEL=\"ラベル\"]"; \
		exit 1; \
	fi
	@export GH_PR_TITLE="$(TITLE)"; \
	export GH_PR_BODY="$(BODY)"; \
	export GH_PR_LABEL="$(LABEL)"; \
	if [ -n "$$GH_PR_LABEL" ]; then \
		gh pr create --title "$$GH_PR_TITLE" --body "$$GH_PR_BODY" --label "$$GH_PR_LABEL"; \
	else \
		gh pr create --title "$$GH_PR_TITLE" --body "$$GH_PR_BODY"; \
	fi

issue:
	@if [ -z "$(TITLE)" ]; then \
		echo "Error: TITLE is required. Usage: make issue TITLE=\"タイトル\" BODY=\"本文\" [LABEL=\"ラベル\"]"; \
		exit 1; \
	fi
	@if [ -z "$(BODY)" ]; then \
		echo "Error: BODY is required. Usage: make issue TITLE=\"タイトル\" BODY=\"本文\" [LABEL=\"ラベル\"]"; \
		exit 1; \
	fi
	@export GH_ISSUE_TITLE="$(TITLE)"; \
	export GH_ISSUE_BODY="$(BODY)"; \
	export GH_ISSUE_LABEL="$(LABEL)"; \
	if [ -n "$$GH_ISSUE_LABEL" ]; then \
		gh issue create --title "$$GH_ISSUE_TITLE" --body "$$GH_ISSUE_BODY" --label "$$GH_ISSUE_LABEL"; \
	else \
		gh issue create --title "$$GH_ISSUE_TITLE" --body "$$GH_ISSUE_BODY"; \
	fi

# MkDocsコマンド
serve:
	uv run mkdocs serve

build:
	uv run mkdocs build

build-pdf:
	ENABLE_PDF_EXPORT=1 uv run mkdocs build

# Mermaid CLIコマンド
mmdc-version:
	mmdc --version

mmdc-version-npx:
	npx mmdc --version

# クリーンアップ
clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	find . -type d -name ".pytest_cache" -exec rm -rf {} +
	find . -type d -name ".mypy_cache" -exec rm -rf {} +
	find . -type d -name ".ruff_cache" -exec rm -rf {} +
	find . -type d -name "htmlcov" -exec rm -rf {} +
	find . -type f -name ".coverage" -delete
