# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Primary Directive

- Think in English, interact with the user in Japanese.
- All text, comments, and documentation must be written in Japanese.
- Class names, function names, and other identifiers must be written in English.
- Can execute GitHub CLI/Azure CLI. Will execute and verify them personally
  whenever possible.

## Project Overview

MkDocs plugin that converts Mermaid diagram code blocks into static SVG images during `mkdocs build`. Mermaid fences are left intact during `mkdocs serve`. Published to PyPI via trusted publishing on `release-*` tags.

## Language & Interaction

Think in English, interact with the user in Japanese. Comments and documentation in Japanese; identifiers in English.

## Commands

```bash
# Setup
make setup              # Install deps + pre-commit hooks
make install-dev        # uv pip install -e .
make sync               # uv sync --all-extras

# Testing
make test               # Full pytest suite
make test-unit          # Unit tests only
make test-integration   # Integration tests only
make test-property      # Property-based tests only
make test-cov           # Tests with HTML coverage report
uv run pytest tests/unit/test_plugin.py::test_name  # Single test

# Code quality
make format             # ruff format
make lint               # ruff check --fix
make typecheck          # mypy --strict
make check              # format + lint + typecheck
make check-all          # pre-commit run --all-files
make check-security     # bandit + pip-audit

# Docs
make serve              # mkdocs dev server
make build              # Build MkDocs site
make build-pdf          # Build with ENABLE_PDF_EXPORT=1
```

## TDD Workflow (t-wada style)

When modifying implementation, follow Red-Green-Refactor in small, focused cycles:

1. **Red**: Write a failing test → `make test` + `make check-all`
2. **Green**: Write simplest code to pass → `make test-cov` + `make check-all`
3. **Refactor**: Clean up → verify all checks still pass

## Architecture

**Entry point**: `MermaidSvgConverterPlugin` in `src/mkdocs_mermaid_to_svg/plugin.py` — MkDocs plugin that hooks into `on_config`, `on_files`, `on_page_markdown`, and `on_post_build`.

**Processing pipeline** (on each page during build):
1. `MermaidProcessor` (`processor.py`) coordinates page-level work
2. `MarkdownProcessor` (`markdown_processor.py`) extracts Mermaid fences into `MermaidBlock` objects via regex, parsing block attributes (theme, id)
3. `MermaidImageGenerator` (`image_generator.py`) renders SVGs using a strategy pattern:
   - `AutoRenderer`: tries `BeautifulMermaidRenderer` (Node.js, via `beautiful-mermaid` submodule) first, falls back to `mmdc` for unsupported diagram types (pie, gantt)
   - `MermaidCLIExecutor`: platform-aware subprocess execution (Windows uses `cmd /c`)
   - `MermaidCommandResolver`: finds `mmdc` or falls back to `npx mmdc`, caches result
4. Generated SVGs are registered into MkDocs `Files`; Markdown is rewritten with image references via `ImagePathResolver`
5. `on_post_build` optionally cleans up generated images (`cleanup_generated_images`)

**Key behaviors**:
- `enabled_if_env` activates plugin only when the named env var is set and non-empty
- `image_id_enabled` requires the `attr_list` Markdown extension; config validation enforces this
- Filenames are deterministic via MD5 content hashing (`utils.generate_image_filename`)
- `beautiful-mermaid` is a git submodule at repo root; its runner is `beautiful_mermaid_runner.mjs`

## Coding Conventions

- Python 3.9+, fully typed with `mypy --strict`, 4-space indent, 88-char lines
- `snake_case` for functions/variables, `CamelCase` for classes
- Structured exception hierarchy in `exceptions.py` (all inherit `MermaidPreprocessorError`)
- Tests mirror source layout: `tests/unit/`, `tests/integration/`, `tests/fixtures/`
- Use `@pytest.mark.integration` and `@pytest.mark.slow` markers appropriately
- SVG golden tests: regenerate with `REGENERATE_SVG_GOLDENS=1`

## Commit Style

Conventional commits: `feat:`, `fix:`, `refactor:`, `docs:` — subject under 72 chars. Reference related issues in body/PR description.
