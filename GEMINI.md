# GEMINI.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**mkdocs-mermaid-to-image** is a MkDocs plugin that converts Mermaid.js diagrams in Markdown documents into static images (PNG/SVG) during the build process. This enables compatibility with PDF output plugins like `mkdocs-with-pdf` and provides offline diagram viewing capabilities.

**Key Features:**
- Converts Mermaid diagrams to static images at build time
- Supports all Mermaid diagram types (flowcharts, sequence, class diagrams, etc.)
- Full PDF export compatibility with MkDocs PDF generators
- Themeable diagrams with customizable output formats
- Intelligent caching system for efficient builds
- Comprehensive error handling with graceful degradation

## Architecture Overview

**MkDocs Plugin Integration:**
- Implements `BasePlugin` with MkDocs lifecycle hooks
- **plugin.py**: Main plugin class (`MermaidToImagePlugin`) with configuration management
- **processor.py**: Core processing engine that orchestrates diagram conversion
- **markdown_processor.py**: Parses Markdown and identifies Mermaid blocks
- **image_generator.py**: Handles image generation via Mermaid CLI
- **mermaid_block.py**: Data structures for Mermaid diagram representation
- **config.py**: Plugin configuration schema and validation
- **utils.py**: Logging, file operations, and utility functions
- **exceptions.py**: Custom exception hierarchy

**Processing Flow:**
1. `on_config` hook validates plugin configuration
2. `on_page_markdown` hook processes each page's Markdown content
3. Mermaid blocks are extracted and converted to images
4. Original Mermaid syntax is replaced with image references
5. Generated images are cached for subsequent builds

## Technology Stack

- **Language**: Python 3.9+
- **Core Dependencies**: MkDocs ≥1.4.0, mkdocs-material ≥8.0.0
- **Image Processing**: Pillow ≥8.0.0, numpy ≥1.20.0
- **External Dependency**: Node.js with `@mermaid-js/mermaid-cli` (mmdc command)
- **Package Management**: uv (modern Python package manager)
- **Code Quality**: ruff (linting/formatting), mypy (strict type checking)
- **Testing**: pytest with hypothesis for property-based testing
- **Automation**: pre-commit hooks, GitHub Actions CI/CD

## Development Environment Setup

**Quick Setup:**
```bash
make setup  # Automated setup via scripts/setup.sh
```

**Manual Setup:**
```bash
# Install dependencies
uv sync --all-extras

# Install pre-commit hooks
uv run pre-commit install

# Verify Node.js and Mermaid CLI
node --version
npx mmdc --version
```

## Common Development Commands

**Testing:**
```bash
make test                    # Run all tests
make test-unit              # Unit tests only
make test-integration       # Integration tests only
make test-cov               # With coverage report
```

**Code Quality:**
```bash
make format                 # Format code (ruff format)
make lint                   # Lint and auto-fix (ruff check --fix)
make typecheck              # Type checking (mypy --strict)
make security               # Security scan (bandit)
make audit                  # Dependency vulnerability check
make check                  # Run all quality checks sequentially
```

**Development Server:**
```bash
uv run mkdocs serve         # Start development server
uv run mkdocs build         # Build documentation
```

**Dependencies:**
```bash
uv add package_name         # Add runtime dependency
uv add --dev dev_package    # Add development dependency
uv sync --all-extras        # Sync all dependencies
```

## Plugin-Specific Development Considerations

**1. Multi-Runtime Environment:**
- Requires both Python (≥3.9) and Node.js (≥16) environments
- Mermaid CLI (`mmdc`) must be globally available via npm
- Cross-platform compatibility for Windows/Unix paths

**2. MkDocs Plugin Lifecycle:**
- Hook implementation: `on_config`, `on_page_markdown`
- Configuration validation via `config_options` schema
- Error handling must not break MkDocs build process

**3. Image Generation Challenges:**
- Headless browser dependencies (Puppeteer via Mermaid CLI)
- Temporary file management and cleanup
- Cache invalidation strategies
- Theme consistency across diagram types

**4. Testing Strategy:**
- **Unit Tests** (`tests/unit/`): Individual component testing
- **Integration Tests** (`tests/integration/`): End-to-end MkDocs integration
- **Property Tests** (`tests/property/`): Hypothesis-generated test cases
- **Fixtures** (`tests/fixtures/`): Sample Mermaid files and expected outputs

## Configuration

**Plugin Configuration Schema (config.py):**
```python
# Key configuration options
image_format: 'png' | 'svg'          # Output format
theme: 'default' | 'dark' | 'forest' | 'neutral'
cache_enabled: bool                   # Enable/disable caching
output_dir: str                       # Image output directory
```

**Testing Plugin with MkDocs:**
```yaml
# mkdocs.yml
plugins:
  - mermaid-to-image:
      image_format: 'png'
      theme: 'default'
      cache_enabled: true
```

## Code Quality Standards

**Type Checking:**
- mypy in strict mode with comprehensive type hints
- All public APIs must have complete type annotations
- Use `from __future__ import annotations` for forward references

**Testing Requirements:**
- Minimum 90% code coverage
- Test naming convention: `test_<scenario>_<expected_result>`
- Property-based testing for input validation
- Integration tests with real MkDocs builds

**Error Handling:**
- Custom exception hierarchy in `exceptions.py`
- Graceful degradation when image generation fails
- Detailed error messages with resolution suggestions
- Logging at appropriate levels (DEBUG, INFO, WARNING, ERROR)

## Troubleshooting

**Common Issues:**

1. **Mermaid CLI not found:**
   ```bash
   npm install -g @mermaid-js/mermaid-cli
   ```

2. **Puppeteer/Chromium issues:**
   ```bash
   # Linux: Install dependencies
   apt-get install -y libgtk-3-0 libx11-xcb1 libxcomposite1 libxdamage1 libxrandr2 libasound2 libpangocairo-1.0-0 libatk1.0-0
   ```

3. **Pre-commit failures:**
   ```bash
   uv run pre-commit clean
   uv run pre-commit install
   ```

## GitHub Operations

**Pull Request Creation:**
```bash
make pr TITLE="Feature: Add new theme support" BODY="Description" LABEL="enhancement"
```

**Issue Creation:**
```bash
make issue TITLE="Bug: Image generation fails" BODY="Details" LABEL="bug"
```

**Branch Naming:**
- Features: `feature/theme-support`
- Bugs: `fix/image-generation-error`
- Docs: `docs/update-readme`

## Performance Considerations

- Image generation is CPU-intensive (headless browser rendering)
- Caching system reduces repeated generation overhead
- Large diagrams may require increased timeout values
- Consider parallel processing for multiple diagrams

## Entry Point

The plugin is registered via setuptools entry point:
```python
# pyproject.toml
[project.entry-points."mkdocs.plugins"]
mermaid-to-image = "mkdocs_mermaid_to_image.plugin:MermaidToImagePlugin"
```

## Documentation

- **docs/**: MkDocs documentation (self-documenting via the plugin)
- **README.md**: Installation and basic usage
- **docs/development.md**: Detailed development guide
- **docs/architecture.md**: Technical architecture details
