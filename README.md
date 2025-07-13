# mkdocs-mermaid-to-svg

[![PyPI - Python Version][python-image]][pypi-link]
[![Linux Support][linux-image]](#requirements)
[![Windows Support][windows-image]](#requirements)

An MkDocs plugin to convert Mermaid charts to SVG images.

This plugin detects Mermaid code blocks and replaces them with SVG images. This is especially useful for formats that don't support JavaScript, like PDF output.

- [Documentation](https://thankful-beach-0f331f600.1.azurestaticapps.net/)

## Features

- **SVG output**: Generates high-quality SVG images from Mermaid diagrams
- **PDF compatible**: SVG images work perfectly in PDF exports
- **Automatic conversion**: Automatically detects and converts all Mermaid code blocks
- **Configurable**: Supports Mermaid themes and custom configurations
- **Environment control**: Can be conditionally enabled via environment variables

## Requirements

This plugin requires [Node.js](https://nodejs.org/) to be installed beforehand.

### Mermaid CLI

```bash
# Install Mermaid CLI globally
npm install -g @mermaid-js/mermaid-cli

# Or install per project
npm install @mermaid-js/mermaid-cli
```

### Puppeteer

```bash
# Install Puppeteer
npm install puppeteer

# Install browser for Puppeteer (required)
npx puppeteer browsers install chrome-headless-shell
```

## Setup

Install the plugin using pip:

```bash
pip install mkdocs-mermaid-to-svg
```

Activate the plugin in `mkdocs.yml` (recommended configuration for PDF generation):

```yaml
plugins:
  - mermaid-to-svg:
      # Disable HTML labels for PDF compatibility
      mermaid_config:
        htmlLabels: false
        flowchart:
          htmlLabels: false
        class:
          htmlLabels: false
  - to-pdf:  # When used with PDF generation plugins
      enabled_if_env: ENABLE_PDF_EXPORT
```

### PDF Compatibility

When `htmlLabels` is enabled, Mermaid CLI generates SVG files with `<foreignObject>` elements containing HTML. PDF generation tools cannot properly render these HTML elements, causing text to disappear.

- **Affected diagrams**: Flowcharts, class diagrams, and other diagrams that use text labels
- **Not affected**: Sequence diagrams use standard SVG text elements and work correctly in PDFs

## Configuration

You can customize the plugin's behavior in `mkdocs.yml`. All options are optional:

### Conditional Activation

To enable the plugin only during PDF generation, use the same environment variable as the to-pdf plugin:

```yaml
plugins:
  - mermaid-to-svg:
      enabled_if_env: "ENABLE_PDF_EXPORT"  # Use same env var as to-pdf plugin
      mermaid_config:
        htmlLabels: false
        flowchart:
          htmlLabels: false
        class:
          htmlLabels: false
  - to-pdf:
      enabled_if_env: ENABLE_PDF_EXPORT
```

Run with:
```bash
ENABLE_PDF_EXPORT=1 mkdocs build
```

### Advanced Options

```yaml
plugins:
  - mermaid-to-svg:
      mmdc_path: "mmdc"                   # Path to Mermaid CLI
      css_file: "custom-mermaid.css"      # Custom CSS file
      puppeteer_config: "puppeteer.json"  # Custom Puppeteer configuration
      error_on_fail: false                # Continue on diagram generation errors
      log_level: "INFO"                   # Log level (DEBUG, INFO, WARNING, ERROR)
      cleanup_generated_images: true      # Clean up generated images after build
```

## Configuration Options

| Option | Default | Description |
|--------|---------|-------------|
| `enabled_if_env` | `None` | Environment variable name to conditionally enable plugin |
| `output_dir` | `"assets/images"` | Directory to store generated SVG files |
| `theme` | `"default"` | Mermaid theme (default, dark, forest, neutral) |
| `mmdc_path` | `"mmdc"` | Path to `mmdc` executable |
| `mermaid_config` | `None` | Mermaid configuration dictionary |
| `css_file` | `None` | Path to custom CSS file |
| `puppeteer_config` | `None` | Path to Puppeteer configuration file |
| `error_on_fail` | `true` | Stop build on diagram generation errors |
| `log_level` | `"INFO"` | Log level |
| `cleanup_generated_images` | `true` | Clean up generated images after build |

## PDF Generation

This plugin is designed with PDF generation compatibility in mind:

### Why SVG?

- **Vector format**: SVG images scale beautifully at any resolution
- **Text preservation**: SVG text remains selectable and searchable in PDFs
- **No JS required**: Works with PDF generation tools that don't support JavaScript

## Usage Example

1. Write Mermaid diagrams in your Markdown:

   ````markdown
   ```mermaid
   graph TD
       A[Start] --> B{Decision}
       B -->|Yes| C[Action 1]
       B -->|No| D[Action 2]
   ```
   ````

2. The plugin automatically converts them to SVG images during build:

   ```html
   <p><img alt="Mermaid Diagram" src="assets/images/diagram_123abc.svg" /></p>
   ```

3. Your PDF exports will display crisp, scalable diagrams with selectable text.

[pypi-link]: https://pypi.org/project/mkdocs-mermaid-to-svg/
[python-image]: https://img.shields.io/pypi/pyversions/mkdocs-mermaid-to-svg?logo=python&logoColor=aaaaaa&labelColor=333333
[linux-image]: https://img.shields.io/badge/Linux-supported-success?logo=linux&logoColor=white&labelColor=333333
[windows-image]: https://img.shields.io/badge/Windows-supported-success?logo=windows&logoColor=white&labelColor=333333
