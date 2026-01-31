# Copilot Instructions

## Primary Directive

- Think in English, interact with the user in Japanese.
- All text, comments, and documentation must be written in Japanese.
- Class names, function names, and other identifiers must be written in English.
- Can execute GitHub CLI/Azure CLI. Will execute and verify them personally
  whenever possible.

## Build, test, lint
- Dev install: `make install-dev` (uv editable install), `make sync` for all extras.
- Docs build: `make build`; PDF build: `make build-pdf` (sets `ENABLE_PDF_EXPORT=1`).
- Serve docs: `make serve`.
- Full tests: `make test`; coverage: `make test-cov`.
- Unit tests: `make test-unit`; integration: `make test-integration`; property tests: `make test-property`.
- Single test: `uv run pytest tests/unit/test_plugin.py::test_name` (pytest nodeid).
- Format: `make format` (ruff format).
- Lint: `make lint` (ruff check --fix).
- Type check: `make typecheck` (mypy --strict).
- Full quality: `make check` or `make check-all` (pre-commit); security: `make check-security`.

## High-level architecture
- `MermaidSvgConverterPlugin` (`src/mkdocs_mermaid_to_svg/plugin.py`) is the MkDocs entry point: validates config, applies `enabled_if_env`/serve gating, and wires the processor.
- `MermaidProcessor` coordinates page processing: `MarkdownProcessor` extracts Mermaid fences into `MermaidBlock` objects, then `MermaidImageGenerator` renders SVG via Mermaid CLI.
- `MermaidImageGenerator` resolves the CLI command (`mmdc` or fallback `npx mmdc`), prepares temp mermaid/puppeteer configs, executes the command, and validates outputs.
- Generated images are registered into MkDocs `Files` and optionally cleaned based on `cleanup_generated_images`; Markdown is rewritten via `MermaidBlock` + `ImagePathResolver`.

## Key conventions
- When changing implementation, follow t-wada TDD: Red (`make test` + `make check-all`), Green (`make test-cov` + `make check-all`), then refactor in small cycles.
- Python is fully typed and checked with `mypy --strict`; keep 4-space indent and 88-char lines, and run `ruff format`/`ruff check`.
- Tests are split into `tests/unit/`, `tests/integration/`, and shared assets in `tests/fixtures/`; use `@pytest.mark.integration` and `@pytest.mark.slow` markers as needed.
- Mermaid conversion happens on `mkdocs build` only; `mkdocs serve` leaves Mermaid fences intact.
- `image_id_enabled` requires the Markdown `attr_list` extension, otherwise config validation fails.
- `enabled_if_env` only activates the plugin when the env var exists and is non-empty.
