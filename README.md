# mkdocs-mermaid-to-svg

[![PyPI - Python Version][python-image]][pypi-link]

An MkDocs plugin to convert Mermaid charts to SVG images.

This plugin finds Mermaid code blocks and replaces them with SVG images. This is useful for formats that don't support JavaScript, like PDF.

- [Documents](https://thankful-beach-0f331f600.1.azurestaticapps.net/)

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

## Options

You can customize the plugin's behavior in `mkdocs.yml`:

```yaml
plugins:
  - mermaid-to-svg:
      mermaid_cli_path: /path/to/your/mmdc
      mermaid_config:
        theme: "default"
        # PDF互換性のための設定（重要！）
        htmlLabels: false
        flowchart:
          htmlLabels: false
        class:
          htmlLabels: false
```

-   `mermaid_cli_path`:
    -   Defaults to `None`.
    -   Path to the `mmdc` executable. If not provided, the plugin will search for it in the system's `PATH`.
-   `image_format`:
    -   Defaults to `svg`.
    -   The output format for the generated images. Can be `svg` or `png`.
-   `mermaid_config`:
    -   Defaults to `None`.
    -   A dictionary of options to pass to Mermaid for rendering. See the [Mermaid documentation](https://mermaid.js.org/config/schema-docs/config.html) for available options.
    -   **Important for PDF generation**: Set `htmlLabels: false` to ensure diagrams display correctly in PDF output.

## PDF Generation

When generating PDFs from your MkDocs site, certain Mermaid diagrams (flowcharts, class diagrams) may not display text correctly due to HTML label rendering. To fix this:

1. **Set `htmlLabels: false`** in your `mermaid_config`:

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

2. **Why this is needed**: Mermaid CLI generates SVG files with `<foreignObject>` elements containing HTML when `htmlLabels` is enabled. PDF generation tools cannot properly render these HTML elements within SVG, causing text to disappear.

3. **Affected diagram types**: Flowcharts, class diagrams, and other diagrams that use text labels.

4. **Not affected**: Sequence diagrams already use standard SVG text elements and work correctly in PDFs.

[pypi-link]: https://pypi.org/project/mkdocs-mermaid-to-svg/
[python-image]: https://img.shields.io/pypi/pyversions/mkdocs-mermaid-to-svg?logo=python&logoColor=aaaaaa&labelColor=333333
