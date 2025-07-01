# mkdocs-mermaid-to-image

[![PyPI - Python Version][python-image]][pypi-link]

An MkDocs plugin to convert Mermaid charts to images.

This plugin finds Mermaid code blocks and replaces them with images. This is useful for formats that don't support JavaScript, like PDF.

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
pip install mkdocs-mermaid-to-image
```

Activate the plugin in `mkdocs.yml`:

```yaml
plugins:
  - search
  - mermaid-to-image
```

> **Note:** If you have no `plugins` entry in your config file yet, you'll likely also want to add the `search` plugin. MkDocs enables it by default if there is no `plugins` entry set, but now you have to enable it explicitly.

## Options

You can customize the plugin's behavior in `mkdocs.yml`:

```yaml
plugins:
  - mermaid-to-image:
      mermaid_cli_path: /path/to/your/mmdc
      image_format: "svg"
      mermaid_config:
        theme: "default"
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

[pypi-link]: https://pypi.org/project/mkdocs-mermaid-to-image/
[python-image]: https://img.shields.io/pypi/pyversions/mkdocs-mermaid-to-image?logo=python&logoColor=aaaaaa&labelColor=333333
