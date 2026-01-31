# mkdocs-mermaid-to-svg

[![PyPI - Python Version][python-image]][pypi-link]
[![Linux Support][linux-image]](#requirements)
[![Windows Support][windows-image]](#requirements)

[Japanese](./README.ja.md) | **English**

An MkDocs plugin to convert Mermaid charts to SVG images.

This plugin detects Mermaid code blocks and replaces them with SVG images. This is especially useful for formats that don't support JavaScript, like PDF output.

- [Documentation](https://kind-ground-03224aa00.3.azurestaticapps.net/)
- [DeepWiki](https://deepwiki.com/nuitsjp/mkdocs-mermaid-to-svg)

## Features

- **SVG output**: Generates high-quality SVG images from Mermaid diagrams
- **Automatic conversion**: Automatically detects and converts all Mermaid code blocks
- **Configurable**: Supports Mermaid themes and custom configurations
- **beautiful-mermaid rendering**: Fine-grained control over colors, fonts, spacing via [beautiful-mermaid](https://github.com/nuitsjp/beautiful-mermaid) options
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
      image_id_enabled: true
      image_id_prefix: mermaid-diagram
      # Disable HTML labels for PDF compatibility
      mermaid_config:
        htmlLabels: false
        flowchart:
          htmlLabels: false
        class:
          htmlLabels: false
  - to-pdf:  # When used with PDF generation plugins
      enabled_if_env: ENABLE_PDF_EXPORT

> **Note**
> If `mermaid_config` is omitted, the plugin automatically writes a temporary config that disables `htmlLabels` (including `flowchart` and `class` diagrams). The PDF-safe defaults are always applied; specify `mermaid_config` only when you need custom Mermaid settings.
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
      renderer: "auto"                 # auto: beautiful-mermaid優先, mmdc: 従来CLI固定
      mmdc_path: "mmdc"                   # Path to Mermaid CLI
      css_file: "custom-mermaid.css"      # Custom CSS file
      puppeteer_config: "puppeteer.json"  # Custom Puppeteer configuration
      error_on_fail: false                # Continue on diagram generation errors
      log_level: "WARNING"                # Currently derived from mkdocs CLI flags (see note below)
      cleanup_generated_images: true      # Clean up generated images after build
      image_id_enabled: true              # Emit unique ids on rendered <img> tags
      image_id_prefix: "mermaid-diagram"  # Override id prefix (requires attr_list)
```

### beautiful-mermaid Rendering Options

When using `renderer: "auto"`, you can customize [beautiful-mermaid](https://github.com/nuitsjp/beautiful-mermaid) rendering options globally in `mkdocs.yml`:

```yaml
plugins:
  - mermaid-to-svg:
      renderer: "auto"
      theme: "tokyo-night"                # Named theme (tokyo-night, nord, etc.)
      beautiful_mermaid_bg: "#1a1b26"     # Background color
      beautiful_mermaid_fg: "#c0caf5"     # Foreground (text) color
      beautiful_mermaid_line: "#565f89"   # Line/edge color
      beautiful_mermaid_accent: "#7aa2f7" # Accent color
      beautiful_mermaid_font: "Inter"     # Font family
      beautiful_mermaid_padding: 20       # Diagram padding (px)
      beautiful_mermaid_node_spacing: 80  # Node spacing (px)
      beautiful_mermaid_transparent: true # Transparent background
```

Available options:

| Option | Type | Description |
|--------|------|-------------|
| `beautiful_mermaid_bg` | `str` | Background color |
| `beautiful_mermaid_fg` | `str` | Foreground (text) color |
| `beautiful_mermaid_line` | `str` | Line/edge color |
| `beautiful_mermaid_accent` | `str` | Accent color |
| `beautiful_mermaid_muted` | `str` | Muted color |
| `beautiful_mermaid_surface` | `str` | Surface color |
| `beautiful_mermaid_border` | `str` | Border color |
| `beautiful_mermaid_font` | `str` | Font family |
| `beautiful_mermaid_padding` | `int` | Diagram padding (px) |
| `beautiful_mermaid_node_spacing` | `int` | Node spacing (px) |
| `beautiful_mermaid_layer_spacing` | `int` | Layer spacing (px) |
| `beautiful_mermaid_transparent` | `bool` | Transparent background |

#### Per-block overrides

You can override global options on individual code blocks using fence attributes:

````markdown
```mermaid {bg: "#000000", font: "Fira Code"}
graph TD
    A --> B
```
````

Block attributes take precedence over global `mkdocs.yml` settings. The `theme` attribute can also be overridden per block:

````markdown
```mermaid {theme: "nord", accent: "#88c0d0"}
sequenceDiagram
    Alice->>Bob: Hello
```
````

> **Note**: beautiful-mermaid options only apply when `renderer: "auto"` is set and the diagram type is supported (flowchart, sequence, class, ER, state). Unsupported types (pie, gantt, etc.) fall back to mmdc, where these options are ignored.

> **Mermaid image IDs**
> Set `image_id_enabled: true` to add deterministic IDs (e.g. `mermaid-diagram-guide-1`) to every generated image. This allows per-diagram CSS targeting and PDF sizing tweaks.
>
> - Enable the Markdown [`attr_list`](https://python-markdown.github.io/extensions/attr_list/) extension, otherwise MkDocs will treat `{#...}` literally.
> - Override the prefix with `image_id_prefix`. Custom IDs can also be supplied per code fence using `{id: "custom-id"}` attributes.

Example configuration:

```yaml
markdown_extensions:
  - attr_list

plugins:
  - mermaid-to-svg:
      image_id_enabled: true
      image_id_prefix: "diagram"
```

## Configuration Options

| Option | Default | Description |
|--------|---------|-------------|
| `enabled_if_env` | `None` | Environment variable name to conditionally enable plugin |
| `output_dir` | `"assets/images"` | Directory to store generated SVG files |
| `theme` | `"default"` | Mermaid theme — mmdc built-ins (default, dark, forest, neutral) or beautiful-mermaid named themes (tokyo-night, nord, etc.) |
| `renderer` | `"mmdc"` | `auto`=beautiful-mermaid優先（未導入/未対応時はmmdcへ）, `mmdc`=従来CLI固定 |
| `mmdc_path` | `"mmdc"` | Path to `mmdc` executable |
| `cli_timeout` | `90` | Timeout (seconds) for Mermaid CLI; adjust if your diagrams are very small/very heavy |
| `mermaid_config` | `None` | Mermaid configuration dictionary |
| `css_file` | `None` | Path to custom CSS file |
| `puppeteer_config` | `None` | Path to Puppeteer configuration file |
| `error_on_fail` | `true` | Stop build on diagram generation errors |
| `log_level` | `auto` | Ignored in `mkdocs.yml`; resolves to `DEBUG` with `mkdocs build --verbose/-v`, otherwise `WARNING` |
| `cleanup_generated_images` | `true` | Clean up generated images after build |
| `image_id_enabled` | `false` | Attach `{#id}` suffixes to generated image Markdown (requires `attr_list`) |
| `image_id_prefix` | `"mermaid-diagram"` | Prefix used for generated IDs when `image_id_enabled` is true |
| `beautiful_mermaid_*` | `None` | beautiful-mermaid rendering options (see [beautiful-mermaid Rendering Options](#beautiful-mermaid-rendering-options)) |

> **Log level behaviour**
> The plugin currently overrides `log_level` based on the MkDocs CLI flags: `mkdocs build --verbose` or `-v` forces `DEBUG`, and omitting them forces `WARNING`. Values specified in `mkdocs.yml` are ignored for now.

### Runtime Notes

- `mkdocs serve` leaves Mermaid fences untouched; conversion runs during `mkdocs build`.
- `enabled_if_env` must be set to a non-empty environment variable to activate the plugin; missing or empty values keep it disabled.
- If the configured `mmdc_path` is not available, the plugin falls back to `npx mmdc`.
- When `puppeteer_config` is omitted or the file is missing, a temporary headless-friendly config is generated and cleaned up after use.
- `renderer: auto` requires `node` and `beautiful-mermaid` to be installed in the MkDocs project (e.g. `npm install beautiful-mermaid`).
- `renderer: auto` falls back to mmdc when the diagram type is unsupported (e.g. pie/gantt) or the renderer fails.

### SVG Golden Tests

Golden SVG comparison tests run by default and can be skipped with:

```bash
SKIP_SVG_GOLDEN=1 uv run pytest tests/integration/test_svg_golden.py
```

To regenerate expected SVG files:

```bash
REGENERATE_SVG_GOLDENS=1 uv run pytest tests/integration/test_svg_golden.py
```

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
