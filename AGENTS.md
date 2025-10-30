# Repository Guidelines

## Primary Directive

- Think in English, interact with the user in Japanese.
- When modifying the implementation, strictly adhere to the t-wada style of Test-Driven Development (TDD).
  - **t-wada TDD Concept**:
    1. 1st Issue
        1. First, write a failing test (Red).
            - make test
            - make check-all
        2. Then, write the simplest code to make it pass (Green).
            - make test-cov
            - make check-all
        3. Finally, refactor the code (Refactor).
    2. 2nd Issue
        1. First, write a failing test (Red).
            - make test
            - make check-all
        2. Then, write the simplest code to make it pass (Green).
            - make test-cov
            - make check-all
        3. Finally, refactor the code (Refactor).
  - Each cycle should be small and focused on a single purpose.

## Project Structure & Module Organization
- Core plugin code lives in `src/mkdocs_mermaid_to_svg/`. Start with `plugin.py` for the MkDocs entry point, then follow the flow through `markdown_processor.py` and `image_generator.py` for Mermaid block detection and SVG rendering.
- Shared utilities and configuration helpers are split across `config.py`, `logging_config.py`, and `utils.py` to keep plugin logic clean.
- Tests mirror the runtime layout: unit suites in `tests/unit/`, integration checks in `tests/integration/`, and reusable diagrams or assets in `tests/fixtures/`. MkDocs content for previews lives in `docs/`.

## Build, Test, and Development Commands
- `make install-dev` installs the package in editable mode via `uv`.
- `make test` runs the full pytest suite; use `make test-unit` or `make test-integration` to scope failures.
- `make serve` starts `uv run mkdocs serve` for live documentation previews with the plugin enabled.
- `make build` produces a static MkDocs site; `ENABLE_PDF_EXPORT=1 make build` mimics the PDF flow.

## Coding Style & Naming Conventions
- Python files use 4-space indentation, 88-character lines, and type hints everywhere (`mypy --strict` is enforced).
- Run `make format` before reviews to apply `ruff format`, and `make lint` to keep imports and bugbear checks clean.
- Prefer `snake_case` for functions and variables, `CamelCase` for classes, and descriptive module names matching their responsibility (e.g., `markdown_processor.py` handles Markdown traversal).

## Testing Guidelines
- All tests run through `pytest` with coverage on `src/mkdocs_mermaid_to_svg`. Expect reports in `.tmp/` and `htmlcov/`.
- Use the `@pytest.mark.integration` marker for end-to-end MkDocs runs; flag heavier Mermaid scenarios with `@pytest.mark.slow`.
- Store fixtures in `tests/fixtures/` and name new files `test_<feature>.py` to match discovery rules (`test_*.py`, `*_test.py`).

## Commit & Pull Request Guidelines
- Follow the conventional style used in history (`feat:`, `fix:`, `refactor:`, `docs:`) and keep the subject concise (72 characters or fewer).
- Reference related issues in the commit body or PR description, and explain the impact on SVG output or MkDocs behavior.
- PRs should include: a short summary, screenshots or artifact paths for new diagrams when relevant, test commands executed (e.g., `make test`), and notes on any environment variables or Mermaid CLI expectations.
- Before sending a PR, run at least `make check` to cover formatting, linting, and type checks; add `make check-security` when dependencies or CLI integrations change.
