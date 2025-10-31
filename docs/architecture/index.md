# Architecture Documentation

## Overview

The MkDocs Mermaid to SVG plugin turns Mermaid code fences into static SVG images during a MkDocs build so that PDF export and offline browsing work without client-side JavaScript. During `on_config` the plugin validates the configuration, honours the optional `enabled_if_env` gate, and wires up a `MermaidProcessor` instance. When MkDocs renders pages, `on_page_markdown` delegates to the processor (unless we are serving live content) and collects every generated asset so that `on_post_build` can register or clean them via `Files`.

Key runtime traits:

- Configuration is validated and augmented with derived values such as `log_level` based on `--verbose` flags.
- The plugin can be disabled entirely through `enabled_if_env` or by running MkDocs in `serve` mode.
- Generated assets are tracked in-memory so that they can be injected into `Files` and removed when `cleanup_generated_images` is enabled.
- Errors are normalised through `_handle_processing_error`, mapping low-level failures onto the typed exception hierarchy in `exceptions.py`.

## Processing Pipeline

1. **MkDocs hook** – `MermaidSvgConverterPlugin.on_page_markdown` short-circuits for `serve` mode and otherwise invokes `_process_mermaid_diagrams`.
2. **Page processing** – `MermaidProcessor.process_page` extracts all Mermaid blocks, iterates them with a `ProcessingContext`, and collects rewritten Markdown plus image paths.
3. **Markdown extraction** – `MarkdownProcessor` finds both attribute-rich and plain Mermaid fences, parses attributes into dictionaries, and keeps positional information for later replacement.
4. **Image generation** – Each `MermaidBlock.generate_image` call hands the diagram code to `MermaidImageGenerator`, which resolves the CLI command, prepares temp artifacts, executes `mmdc`, and validates outputs.
5. **Markdown rewrite** – Successful blocks replace their source spans with image Markdown that respects the page depth, docs root, and configured `output_dir` via `ImagePathResolver`.

## Sequence Diagram

```mermaid
sequenceDiagram
    participant MkDocs
    participant Plugin as MermaidSvgConverterPlugin
    participant Processor as MermaidProcessor
    participant MD as MarkdownProcessor
    participant Block as MermaidBlock
    participant Generator as MermaidImageGenerator
    participant CLI as Mermaid CLI
    participant Files as MkDocs Files

    MkDocs->>Plugin: on_page_markdown(markdown, page, config)
    Plugin->>Plugin: _should_be_enabled(config)
    alt Disabled or serve mode
        Plugin-->>MkDocs: return original markdown
    else Enabled
        Plugin->>Processor: process_page(page.file.src_path, markdown, output_dir, page_url, docs_dir)
        Processor->>MD: extract_mermaid_blocks(markdown)
        MD-->>Processor: blocks
        loop For each Mermaid block
            Processor->>Block: generate_image(output_path, generator, config, page_file)
            Block->>Generator: generate(code, output_path, runtime_config, page_file)
            Generator->>CLI: run mmdc command
            CLI-->>Generator: CompletedProcess
            alt Command succeeded
                Generator-->>Block: True
            else Command failed
                Generator-->>Block: False or raises error
            end
        end
        Processor->>MD: replace_blocks_with_images(markdown, blocks, image_paths, page_file, page_url, docs_dir, output_dir)
        MD-->>Processor: modified_markdown
        Processor-->>Plugin: modified_markdown, image_paths
        Plugin->>Plugin: _register_generated_images_to_files(image_paths, docs_dir, config)
        Plugin->>Files: append generated File entries
        Plugin-->>MkDocs: modified markdown
    end
```

## Project Structure

```
mkdocs-mermaid-to-svg/
└── src/
    └── mkdocs_mermaid_to_svg/
        ├── __init__.py             # Package init and version exposure
        ├── _version.py             # Version string wiring for mkdocs
        ├── plugin.py               # MermaidSvgConverterPlugin MkDocs entry point and lifecycle hooks
        ├── processor.py            # MermaidProcessor and ProcessingContext coordinating block/image handling
        ├── markdown_processor.py   # MarkdownProcessor + helpers to extract and rewrite Mermaid fences
        ├── image_generator.py      # MermaidImageGenerator plus CLI resolver/executor/artifact manager
        ├── mermaid_block.py        # MermaidBlock & ImagePathResolver for per-block rendering metadata
        ├── config.py               # ConfigManager schema, validation, and file existence checks
        ├── types.py                # LogContext TypedDict shared with logging utilities
        ├── exceptions.py           # Structured exception hierarchy used across the pipeline
        ├── logging_config.py       # Structured logging setup and contextual adapters
        └── utils.py                # Shared helpers (filenames, temp files, CLI detection, cleanup)
```

## Component Dependencies

```mermaid
graph TD
    subgraph "Plugin Core"
        A[plugin.py] --> B[processor.py]
        A --> C[config.py]
        A --> D[exceptions.py]
        A --> F[logging_config.py]
        A --> U[utils.py]
    end

    subgraph "Processing Pipeline"
        B --> G[markdown_processor.py]
        B --> H[image_generator.py]
        B --> U
    end

    subgraph "Markdown Handling"
        G --> I[mermaid_block.py]
        I --> U
    end

    subgraph "Image Generation Internals"
        H --> J[MermaidCommandResolver]
        H --> K[MermaidArtifactManager]
        H --> L[MermaidCLIExecutor]
        H --> U
    end

    subgraph "External Dependencies"
        MkDocs[MkDocs Framework]
        MermaidCLI["@mermaid-js/mermaid-cli"]
    end

    A -.->|implements| MkDocs
    H -->|executes| MermaidCLI
    F --> T[types.py]
```

## Class Architecture

```mermaid
classDiagram
    direction TB

    class MermaidSvgConverterPlugin {
        -MermaidProcessor~None~ processor
        -list~str~ generated_images
        -Files~None~ files
        -Logger logger
        -bool is_serve_mode
        -bool is_verbose_mode
        +on_config(config) Any
        +on_files(files, config) Files
        +on_page_markdown(markdown, page, config, files) str
        +on_post_build(config) None
        +on_serve(server, config, builder) Any
        -_should_be_enabled(config) bool
        -_process_mermaid_diagrams(markdown, page, config) str
        -_register_generated_images_to_files(image_paths, docs_dir, config) None
        -_add_image_file_to_files(image_path, docs_dir, config) None
        -_remove_existing_file_by_path(src_path) bool
        -_handle_init_error(error) None
        -_handle_processing_error(page_path, error_type, error, fallback) str
    }

    class MermaidProcessor {
        +dict config
        +Logger logger
        +MarkdownProcessor markdown_processor
        +MermaidImageGenerator image_generator
        +process_page(page_file, markdown, output_dir, page_url, docs_dir) tuple~str, list~str~~
        -_process_single_block(block, index, context) None
        -_handle_generation_failure(index, page_file, image_path) None
        -_handle_file_system_error(error, index, page_file, image_path) None
        -_handle_unexpected_error(error, index, page_file) None
    }

    class ProcessingContext {
        +str page_file
        +str|Path output_dir
        +list~str~ image_paths
        +list~Any~ successful_blocks
    }

    class MarkdownProcessor {
        +dict config
        +Logger logger
        +extract_mermaid_blocks(markdown) list~MermaidBlock~
        +replace_blocks_with_images(markdown, blocks, paths, page_file, page_url, docs_dir, output_dir) str
        -_parse_attributes(attr_str) dict
        -_split_attribute_string(attr_str) list~str~
        -_overlaps_with_existing_blocks(match, blocks) bool
    }

    class MermaidBlock {
        +str code
        +dict attributes
        +int start_pos
        +int end_pos
        +generate_image(output_path, generator, config, page_file) bool
        +get_filename(page_file, index, format) str
        +get_image_markdown(image_path, page_file, page_url, output_dir, docs_dir) str
    }

    class ImagePathResolver {
        +to_markdown_path(image_path, page_file, output_dir, docs_dir) str
        -_resolve_relative_path(image_path, output_dir, docs_dir) str
        -_normalize_output_dir(output_dir) str
    }

    MermaidSvgConverterPlugin --> MermaidProcessor
    MermaidProcessor --> ProcessingContext
    MermaidProcessor --> MarkdownProcessor
    MermaidProcessor --> MermaidImageGenerator
    MarkdownProcessor --> MermaidBlock
    MermaidBlock --> ImagePathResolver
```

```mermaid
classDiagram
    direction TB

    class MermaidImageGenerator {
        +dict config
        +Logger logger
        +generate(mermaid_code, output_path, runtime_config, page_file) bool
        +clear_command_cache() None
        +get_cache_size() int
        -_validate_dependencies() None
        -_validate_generation_result(result, output_path, mermaid_code) bool
        -_log_successful_generation(output_path, page_file) None
        -_build_mmdc_command(input_file, output_file, runtime_config, puppeteer_config_file, mermaid_config_file) tuple
        -_execute_mermaid_command(cmd) CompletedProcess
        -_handle_command_failure(result, cmd) bool
        -_handle_missing_output(output_path, mermaid_code) bool
        -_handle_timeout_error(cmd) bool
        -_handle_file_error(error, output_path) bool
        -_handle_unexpected_error(error, output_path, mermaid_code) bool
    }

    class MermaidCommandResolver {
        +resolve() list~str~
        -_attempt_resolve(command) list~str~?
        -_determine_fallback(primary_command) str
    }

    class MermaidArtifactManager {
        +prepare(mermaid_code, output_path, runtime_config) GenerationArtifacts
        -_resolve_mermaid_config() tuple~str|None, bool~
        -_resolve_puppeteer_config() tuple~str|None, bool~
        -_create_default_puppeteer_config() str
    }

    class MermaidCLIExecutor {
        +run(cmd) CompletedProcess
    }

    class GenerationArtifacts {
        +str source_path
        +str? puppeteer_config_file
        +str? mermaid_config_file
        +tuple cleanup_entries
        +cleanup(logger) None
    }

    MermaidImageGenerator --> MermaidCommandResolver
    MermaidImageGenerator --> MermaidArtifactManager
    MermaidImageGenerator --> MermaidCLIExecutor
    MermaidArtifactManager --> GenerationArtifacts
```

## Configuration Highlights

- `enabled_if_env` toggles the plugin unless a non-empty environment variable is present.
- `output_dir` controls where SVGs are written relative to `docs_dir` and feeds directly into Markdown rewriting logic.
- `theme`, `css_file`, and `mermaid_config` influence Mermaid CLI rendering; dictionary Mermaid configs are serialised to a temp file.
- `puppeteer_config` can point at an existing file; otherwise the artifact manager writes a Chrome-friendly default and tears it down afterward.
- `mmdc_path` (and its fallback logic) is resolved through `MermaidCommandResolver`, with results cached across generations.
- `cleanup_generated_images` toggles post-build removal using `utils.clean_generated_images`.
- `log_level` is derived from CLI verbosity or `MKDOCS_MERMAID_LOG_LEVEL` and applied through `logging_config.setup_plugin_logging`.
- `error_on_fail` guards whether failures raise typed exceptions (`MermaidFileError`, `MermaidImageError`, etc.) or silently preserve the original Markdown block.
