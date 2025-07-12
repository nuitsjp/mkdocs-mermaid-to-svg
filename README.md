# mkdocs-mermaid-to-svg

[![PyPI - Python Version][python-image]][pypi-link]

An MkDocs plugin to convert Mermaid charts to SVG images.

This plugin finds Mermaid code blocks and replaces them with SVG images. This is especially useful for formats that don't support JavaScript, like PDF generation.

- [Documents](https://thankful-beach-0f331f600.1.azurestaticapps.net/)

## Features

- **SVG-only output**: Generates high-quality SVG images from Mermaid diagrams
- **PDF compatible**: SVG images work perfectly in PDF exports
- **Automatic conversion**: Finds and converts all Mermaid code blocks
- **Configurable**: Supports Mermaid themes and custom configurations
- **Environment-aware**: Can be conditionally enabled via environment variables

## Requirements

This plugin requires a Mermaid execution engine. Please install one of the following:

-   [Mermaid CLI](https://github.com/mermaid-js/mermaid-cli)
-   [Node.js](https://nodejs.org/) with [Puppeteer](https://pptr.dev/)

For Mermaid CLI to work properly, you also need to install a browser for Puppeteer:

```bash
npx puppeteer browsers install chrome-headless-shell
```

## Setup

Install the plugin using pip:

```bash
pip install mkdocs-mermaid-to-svg
```

Activate the plugin in `mkdocs.yml`:

```yaml
plugins:
  - search
  - mermaid-to-svg
```

> **Note:** If you have no `plugins` entry in your config file yet, you'll likely also want to add the `search` plugin. MkDocs enables it by default if there is no `plugins` entry set, but now you have to enable it explicitly.

## Configuration

You can customize the plugin's behavior in `mkdocs.yml`. All options are optional:

### Basic Configuration

```yaml
plugins:
  - mermaid-to-svg:
      output_dir: "assets/images"  # Where to store generated SVG files
      theme: "default"             # Mermaid theme (default, dark, forest, neutral)
      background_color: "white"    # Background color for diagrams
      width: 800                   # Image width in pixels
      height: 600                  # Image height in pixels
      scale: 1.0                   # Scale factor for the diagram
```

### PDF-Compatible Configuration

For PDF generation, use this configuration to ensure text displays correctly:

```yaml
plugins:
  - mermaid-to-svg:
      mermaid_config:
        # Essential for PDF compatibility
        htmlLabels: false
        flowchart:
          htmlLabels: false
        class:
          htmlLabels: false
        theme: "default"
```

### Conditional Activation

Enable the plugin only when generating PDFs:

```yaml
plugins:
  - mermaid-to-svg:
      enabled_if_env: "ENABLE_MERMAID_SVG"  # Only enable if this env var is set
```

Then run:
```bash
ENABLE_MERMAID_SVG=1 mkdocs build
```

### Advanced Options

```yaml
plugins:
  - mermaid-to-svg:
      mmdc_path: "/path/to/mmdc"           # Custom path to Mermaid CLI
      temp_dir: "/tmp/mermaid"             # Custom temporary directory
      css_file: "custom-mermaid.css"      # Custom CSS file
      puppeteer_config: "puppeteer.json"  # Custom Puppeteer configuration
      preserve_original: true             # Keep original Mermaid code in output
      error_on_fail: false                # Continue on diagram generation errors
      log_level: "INFO"                   # Logging level (DEBUG, INFO, WARNING, ERROR)
      cleanup_generated_images: false     # Clean up generated images after build
```

## Available Options

| Option | Default | Description |
|--------|---------|-------------|
| `enabled_if_env` | `None` | Environment variable name to conditionally enable plugin |
| `output_dir` | `"assets/images"` | Directory to store generated SVG files |
| `theme` | `"default"` | Mermaid theme (default, dark, forest, neutral) |
| `background_color` | `"white"` | Background color for diagrams |
| `width` | `800` | Image width in pixels |
| `height` | `600` | Image height in pixels |
| `scale` | `1.0` | Scale factor for the diagram |
| `mmdc_path` | `None` | Path to `mmdc` executable (auto-detected if not set) |
| `mermaid_config` | `None` | Mermaid configuration dictionary |
| `css_file` | `None` | Path to custom CSS file |
| `puppeteer_config` | `None` | Path to Puppeteer configuration file |
| `temp_dir` | `None` | Custom temporary directory |
| `preserve_original` | `false` | Keep original Mermaid code in output |
| `error_on_fail` | `false` | Stop build on diagram generation errors |
| `log_level` | `"INFO"` | Logging level |
| `cleanup_generated_images` | `false` | Clean up generated images after build |

## PDF Generation

This plugin is specifically designed for PDF generation compatibility:

### Why SVG?

- **Vector graphics**: SVG images scale perfectly at any resolution
- **Text preservation**: SVG text remains selectable and searchable in PDFs
- **No JavaScript**: Works in PDF generators that don't support JavaScript

### PDF-Specific Issues and Solutions

1. **HTML Labels Problem**: Mermaid CLI generates SVG files with `<foreignObject>` elements containing HTML when `htmlLabels` is enabled. PDF generation tools cannot properly render these HTML elements, causing text to disappear.

   **Solution**: Set `htmlLabels: false` in your `mermaid_config`:
   ```yaml
   plugins:
     - mermaid-to-svg:
         mermaid_config:
           htmlLabels: false
           flowchart:
             htmlLabels: false
           class:
             htmlLabels: false
   ```

2. **Affected Diagram Types**: Flowcharts, class diagrams, and other diagrams that use text labels.

3. **Not Affected**: Sequence diagrams already use standard SVG text elements and work correctly in PDFs.

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
