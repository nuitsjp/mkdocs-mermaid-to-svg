# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Development Commands

### Testing
```bash
# Run tests with short traceback format
make test

# Run tests with coverage report
make test-cov

# Run specific test types
make test-unit           # Unit tests only
make test-integration    # Integration tests only
make test-property       # Property-based tests only

```

### Code Quality
```bash
# Format code
make format

# Lint and fix issues
make lint

# Type checking
make typecheck

# Security check
make security

# Dependency vulnerability audit
make audit

# Run all quality checks in sequence
make check
```

### Development Server
```bash
# Start MkDocs development server with hot reload
uv run mkdocs serve

# Build documentation site
uv run mkdocs build
```

## Project Architecture

This is a MkDocs plugin that converts Mermaid diagrams to static images (PNG/SVG) during the build process, enabling PDF output and offline viewing.

### Core Components

- **`plugin.py`** - Main MkDocs plugin class (`MermaidToImagePlugin`)
  - Handles MkDocs lifecycle hooks (`on_config`, `on_files`, `on_page_markdown`, `on_post_build`)
  - Manages plugin state and mode detection (serve vs build)
  - Integrates with MkDocs file system

- **`processor.py`** - Page processing orchestrator (`MermaidProcessor`)
  - Coordinates markdown processing and image generation
  - Handles batch processing of Mermaid blocks per page

- **`markdown_processor.py`** - Markdown parsing and transformation (`MarkdownProcessor`)
  - Extracts Mermaid code blocks using regex patterns
  - Replaces Mermaid blocks with image tags
  - Preserves attributes and handles relative paths

- **`image_generator.py`** - Image generation via Mermaid CLI (`MermaidImageGenerator`)
  - Executes `@mermaid-js/mermaid-cli` (mmdc) subprocess
  - Handles CI environment configuration (puppeteer sandboxing)
  - Manages temporary files and cleanup

- **`config.py`** - Configuration schema and validation (`MermaidPluginConfig`, `ConfigManager`)
  - Validates plugin settings from `mkdocs.yml`
  - Provides type-safe configuration access

### Processing Flow

1. **Plugin Initialization** (`on_config`):
   - Validates configuration via `ConfigManager`
   - Sets up logging based on verbose mode
   - Checks `enabled_if_env` environment variable for conditional activation
   - Creates `MermaidProcessor` instance

2. **Page Processing** (`on_page_markdown`):
   - Skips processing in serve mode (development)
   - Extracts Mermaid blocks from markdown
   - Generates images for each block via Mermaid CLI
   - Replaces blocks with image references
   - Registers generated images with MkDocs file system

3. **Image Generation**:
   - Creates temporary `.mmd` files with Mermaid code
   - Builds `mmdc` command with configuration options
   - Handles CI environments with puppeteer `--no-sandbox`
   - Cleans up temporary files

### Key Configuration Options

- **`enabled_if_env`** - Enable plugin only when environment variable is set (useful for PDF builds)
- **`output_dir`** - Directory for generated images (default: `assets/images`)
- **`image_format`** - Output format: `png` or `svg`
- **`theme`** - Mermaid theme: `default`, `dark`, `forest`, `neutral`
- **`error_on_fail`** - Whether to stop build on image generation failure
- **`cache_enabled`** - Enable image caching for performance

### Error Handling

The plugin uses a structured exception hierarchy:
- **`MermaidConfigError`** - Configuration validation errors (stops build)
- **`MermaidCLIError`** - Mermaid CLI execution errors
- **`MermaidImageError`** - Image file generation/validation errors
- **`MermaidFileError`** - File system operation errors

Error behavior is controlled by `error_on_fail` setting:
- `true` - Stop build on any error
- `false` - Log errors and continue (skip failed diagrams)

### Development Notes

- Plugin automatically detects serve mode (`mkdocs serve`) and skips image processing for faster development
- Use `--verbose` flag for detailed debug logging
- CI environments are detected and handled with appropriate puppeteer configuration
- Generated images are dynamically registered with MkDocs file system for proper copying to site directory
- Pre-commit hooks ensure code quality (ruff, mypy, bandit)

### Testing Strategy

- **Unit tests** (`tests/unit/`) - Test individual components in isolation
- **Integration tests** (`tests/integration/`) - Test plugin with actual MkDocs builds
- **Property tests** - Use Hypothesis for property-based testing
- **Fixtures** (`tests/fixtures/`) - Sample Mermaid files and expected outputs
- **Test coverage** - Maintained with pytest-cov, reports in `htmlcov/`
- **Fixtures** (`tests/fixtures/`) - Sample Mermaid files and expected outputs
- **Test coverage** - Maintained with pytest-cov, reports in `htmlcov/`
