# Architecture Documentation

## Overview

The MkDocs Mermaid to Image Plugin is a comprehensive solution that converts Mermaid diagrams to static SVG images during the MkDocs build process. This plugin enables PDF output generation and offline viewing of documentation containing Mermaid diagrams by leveraging the Mermaid CLI (`@mermaid-js/mermaid-cli`) to transform code blocks into static images.

## Project Structure

```
mkdocs-mermaid-to-svg/
└── src/
    └── mkdocs_mermaid_to_svg/
        ├── __init__.py             # Package initialization and version information
        ├── _version.py             # Version management
        ├── plugin.py               # Main MkDocs plugin class (MermaidSvgConverterPlugin)
        ├── processor.py            # Page processing orchestrator (MermaidProcessor)
        ├── markdown_processor.py   # Markdown parsing and transformation (MarkdownProcessor)
        ├── image_generator.py      # Image generation via Mermaid CLI (MermaidImageGenerator)
        ├── mermaid_block.py        # Mermaid block representation (MermaidBlock)
        ├── config.py               # Configuration schema and validation (ConfigManager)
        ├── types.py                # Type definitions and TypedDict classes
        ├── exceptions.py           # Custom exception hierarchy
        ├── logging_config.py       # Structured logging configuration
        └── utils.py                # Utility functions and helpers
```

## Component Dependencies

```mermaid
graph TD
    subgraph "Plugin Core"
        A[plugin.py] --> B[processor.py]
        A --> C[config.py]
        A --> D[exceptions.py]
        A --> E[utils.py]
        A --> F[logging_config.py]
    end

    subgraph "Processing Pipeline"
        B --> G[markdown_processor.py]
        B --> H[image_generator.py]
        B --> E
    end

    subgraph "Data Models & Helpers"
        G --> I[mermaid_block.py]
        G --> E
        H --> D
        H --> E
        I --> E
    end

    subgraph "External Dependencies"
        MkDocs[MkDocs Framework]
        MermaidCLI["Mermaid CLI (@mermaid-js/mermaid-cli)"]
    end

    A -.->|implements| MkDocs
    H -->|executes| MermaidCLI

    style A fill:#e1f5fe,stroke:#333,stroke-width:2px
    style B fill:#e8f5e8,stroke:#333,stroke-width:2px
    style G fill:#e0f7fa
    style H fill:#e0f7fa
    style I fill:#f3e5f5
    style C fill:#fff3e0
    style D fill:#fce4ec
    style E fill:#f3e5f5
    style F fill:#f3e5f5
```

## Class Architecture

```mermaid
classDiagram
    direction TB

    class BasePlugin {
        <<interface>>
        +on_config(config)
        +on_files(files, config)
        +on_page_markdown(markdown, page, config, files)
        +on_post_build(config)
        +on_serve(server, config, builder)
    }

    class MermaidSvgConverterPlugin {
        +ConfigManager config_scheme
        +MermaidProcessor processor
        +Logger logger
        +list~str~ generated_images
        +Files files
        +bool is_serve_mode
        +bool is_verbose_mode
        +on_config(config) Any
        +on_files(files, config) Files
        +on_page_markdown(markdown, page, config, files) str
        +on_post_build(config) None
        +on_serve(server, config, builder) Any
        -_should_be_enabled(config) bool
        -_process_mermaid_diagrams(markdown, page, config) str
        -_register_generated_images_to_files(image_paths, docs_dir, config) None
        -_remove_existing_file_by_path(src_path) bool
    }
    MermaidSvgConverterPlugin --|> BasePlugin

    class MermaidProcessor {
        +dict config
        +Logger logger
        +MarkdownProcessor markdown_processor
        +MermaidImageGenerator image_generator
        +process_page(page_file, markdown, output_dir, page_url) tuple~str, list~str~~
    }

    class MarkdownProcessor {
        +dict config
        +Logger logger
        +extract_mermaid_blocks(markdown) List~MermaidBlock~
        +replace_blocks_with_images(markdown, blocks, paths, page_file, page_url) str
        -_parse_attributes(attr_str) dict
    }

    class MermaidImageGenerator {
        +dict config
        +Logger logger
        +str _resolved_mmdc_command
        +ClassVar dict _command_cache
        +generate(code, output_path, config) bool
        +clear_command_cache() None
        +get_cache_size() int
        -_validate_dependencies() None
        -_build_mmdc_command(input_file, output_path, config) tuple
        -_execute_mermaid_command(cmd) CompletedProcess
        -_create_mermaid_config_file() str
        -_handle_command_failure(result, cmd) bool
        -_handle_missing_output(output_path, mermaid_code) bool
        -_handle_timeout_error(cmd) bool
        -_handle_file_error(e, output_path) bool
        -_handle_unexpected_error(e, output_path, mermaid_code) bool
    }

    class MermaidBlock {
        +str code
        +dict attributes
        +int start_pos
        +int end_pos
        +generate_image(output_path, generator, config) bool
        +get_filename(page_file, index, format) str
        +get_image_markdown(image_path, page_file, preserve_original, page_url) str
    }

    class ConfigManager {
        <<static>>
        +get_config_scheme() tuple
        +validate_config(config) bool
    }

    class MermaidPreprocessorError {<<exception>>}
    class MermaidCLIError {<<exception>>}
    class MermaidConfigError {<<exception>>}
    class MermaidParsingError {<<exception>>}
    class MermaidFileError {<<exception>>}
    class MermaidValidationError {<<exception>>}
    class MermaidImageError {<<exception>>}

    MermaidCLIError --|> MermaidPreprocessorError
    MermaidConfigError --|> MermaidPreprocessorError
    MermaidParsingError --|> MermaidPreprocessorError
    MermaidFileError --|> MermaidPreprocessorError
    MermaidValidationError --|> MermaidPreprocessorError
    MermaidImageError --|> MermaidPreprocessorError

    MermaidSvgConverterPlugin o-- MermaidProcessor
    MermaidSvgConverterPlugin ..> ConfigManager : uses
    MermaidProcessor o-- MarkdownProcessor
    MermaidProcessor o-- MermaidImageGenerator
    MarkdownProcessor --> MermaidBlock : creates
    MermaidBlock --> MermaidImageGenerator : uses
    MermaidImageGenerator --> MermaidCLIError : may throw
    MermaidImageGenerator --> MermaidImageError : may throw
```

## Processing Flow

### 1. Plugin Initialization (`on_config`)

```mermaid
sequenceDiagram
    participant MkDocs
    participant Plugin as MermaidSvgConverterPlugin
    participant CfgMgr as ConfigManager
    participant Proc as MermaidProcessor

    MkDocs->>Plugin: on_config(config)

    Note over Plugin: Extract config dictionary from self.config
    Plugin->>CfgMgr: validate_config(config_dict)
    CfgMgr-->>Plugin: validation result
    alt Validation fails
        Plugin->>MkDocs: raise MermaidConfigError
    end

    Note over Plugin: Set log level based on verbose mode
    alt Verbose mode enabled
        Plugin->>Plugin: config_dict["log_level"] = "DEBUG"
    else Normal mode
        Plugin->>Plugin: config_dict["log_level"] = "WARNING"
    end

    Plugin->>Plugin: _should_be_enabled(self.config)
    Note over Plugin: Check enabled_if_env environment variable
    alt Plugin disabled
        Plugin->>Plugin: logger.info("Plugin is disabled")
        Plugin-->>MkDocs: return config
    end

    Plugin->>Proc: new MermaidProcessor(config_dict)
    Proc->>Proc: Initialize MarkdownProcessor(config)
    Proc->>Proc: Initialize MermaidImageGenerator(config)
    Proc-->>Plugin: processor instance

    Plugin->>Plugin: logger.info("Plugin initialized successfully")
    Plugin-->>MkDocs: return config
```

### 2. File Registration (`on_files`)

```mermaid
sequenceDiagram
    participant MkDocs
    participant Plugin as MermaidSvgConverterPlugin

    MkDocs->>Plugin: on_files(files, config)

    alt Plugin disabled or no processor
        Plugin-->>MkDocs: return files (no processing)
    end

    Plugin->>Plugin: self.files = files
    Plugin->>Plugin: self.generated_images = []
    Plugin-->>MkDocs: return files
```

### 3. Page Processing (`on_page_markdown`)

```mermaid
sequenceDiagram
    participant MkDocs
    participant Plugin as MermaidSvgConverterPlugin
    participant Proc as MermaidProcessor
    participant MdProc as MarkdownProcessor
    participant Block as MermaidBlock
    participant ImgGen as MermaidImageGenerator

    MkDocs->>Plugin: on_page_markdown(markdown, page, config, files)

    alt Plugin disabled
        Plugin-->>MkDocs: return markdown (unchanged)
    end

    alt Serve mode detected
        Plugin-->>MkDocs: return markdown (skip processing)
    end

    Plugin->>Proc: process_page(page.file.src_path, markdown, output_dir, page.url)
    Proc->>MdProc: extract_mermaid_blocks(markdown)
    MdProc-->>Proc: blocks: List[MermaidBlock]

    alt No Mermaid blocks found
        Proc-->>Plugin: (markdown, [])
        Plugin-->>MkDocs: return markdown
    end

    loop For each Mermaid block
        Proc->>Block: generate_image(output_path, image_generator, config)
        Block->>ImgGen: generate(code, output_path, merged_config)
        ImgGen-->>Block: success: bool
        Block-->>Proc: success: bool

        alt Image generation successful
            Proc->>Proc: Add to image_paths list
            Proc->>Proc: Add to successful_blocks list
        else Failed and error_on_fail=false
            Proc->>Proc: Log warning, continue processing
        else Failed and error_on_fail=true
            Proc->>Proc: Continue (error handled upstream)
        end
    end

    alt Successful blocks exist
        Proc->>MdProc: replace_blocks_with_images(markdown, successful_blocks, image_paths, page_file, page_url)
        MdProc-->>Proc: modified_markdown
        Proc-->>Plugin: (modified_markdown, image_paths)
    else No successful blocks
        Proc-->>Plugin: (markdown, [])
    end

    Plugin->>Plugin: Update generated_images list
    Plugin->>Plugin: _register_generated_images_to_files()
    Plugin-->>MkDocs: return modified_markdown
```

### 4. Image Generation (`MermaidImageGenerator.generate`)

```mermaid
sequenceDiagram
    participant ImgGen as MermaidImageGenerator
    participant Utils
    participant Subprocess
    participant FileSystem

    ImgGen->>Utils: get_temp_file_path(".mmd")
    Utils-->>ImgGen: temp_file_path

    ImgGen->>FileSystem: write mermaid_code to temp_file
    ImgGen->>FileSystem: ensure_directory(output_path.parent)

    ImgGen->>ImgGen: _build_mmdc_command(temp_file, output_path, config)
    Note over ImgGen: Create Puppeteer config for CI environments<br/>with --no-sandbox and browser settings
    ImgGen-->>ImgGen: (cmd: list[str], puppeteer_config_file: str, mermaid_config_file: str)

    ImgGen->>Subprocess: run(cmd) with 30s timeout
    Subprocess-->>ImgGen: result: CompletedProcess

    alt Command execution failed
        ImgGen->>ImgGen: _handle_command_failure()
        alt error_on_fail=true
            ImgGen->>ImgGen: raise MermaidCLIError
        end
        ImgGen-->>Block: return False
    end

    alt Output file not created
        ImgGen->>ImgGen: _handle_missing_output()
        alt error_on_fail=true
            ImgGen->>ImgGen: raise MermaidImageError
        end
        ImgGen-->>Block: return False
    end

    ImgGen->>ImgGen: logger.info("Generated image: ...")
    ImgGen-->>Block: return True

    note over ImgGen: Finally block: Clean up temporary files
    ImgGen->>Utils: clean_temp_file(temp_file)
    ImgGen->>Utils: clean_temp_file(puppeteer_config_file)
    ImgGen->>Utils: clean_temp_file(mermaid_config_file)
```

## Configuration Management

The plugin configuration is managed through `mkdocs.yml` and validated using the `ConfigManager` class.

### Configuration Schema

```python
# Available configuration options in mkdocs.yml
plugins:
  - mkdocs-mermaid-to-svg:
      enabled_if_env: "ENABLE_MERMAID"        # Environment variable for conditional activation
      output_dir: "assets/images"             # Directory for generated images
      mermaid_config: {...}                   # Mermaid configuration object or file path
      theme: "default"                        # Mermaid theme: default, dark, forest, neutral
      css_file: "path/to/custom.css"          # Optional CSS file for styling
      puppeteer_config: "path/to/config.json" # Optional Puppeteer configuration
      temp_dir: "/tmp"                        # Temporary directory for processing
      preserve_original: false                # Keep original Mermaid blocks alongside images
      error_on_fail: false                    # Stop build on image generation failure
      log_level: "INFO"                       # Logging level
      cleanup_generated_images: false         # Clean up generated images after build
```

### Validation Logic

The `ConfigManager.validate_config()` method ensures:
- File paths (CSS, Puppeteer config) exist when specified
- Configuration consistency across all options

## Environment-Specific Behavior

### Mode Detection

The plugin automatically detects the execution environment:

```python
# src/mkdocs_mermaid_to_svg/plugin.py
class MermaidSvgConverterPlugin(BasePlugin):
    def __init__(self) -> None:
        self.is_serve_mode: bool = "serve" in sys.argv
        self.is_verbose_mode: bool = "--verbose" in sys.argv or "-v" in sys.argv
```

### Conditional Activation

Plugin activation can be controlled via environment variables:

```python
def _should_be_enabled(self, config: dict[str, Any]) -> bool:
    enabled_if_env = config.get("enabled_if_env")

    if enabled_if_env is not None:
        # Check if environment variable exists and has non-empty value
        env_value = os.environ.get(enabled_if_env)
        return env_value is not None and env_value.strip() != ""

    # Default: always enabled if no conditional environment variable set
    return True
```

### Logging Strategy

Log levels are dynamically adjusted based on verbose mode:

```python
# Adjust log level based on verbose mode
config_dict["log_level"] = "DEBUG" if self.is_verbose_mode else "WARNING"
```

## File Management Strategy

### Generated Image Registration

Generated images are dynamically registered with MkDocs' file system to ensure proper copying to the site directory:

```python
def _register_generated_images_to_files(self, image_paths: list[str], docs_dir: Path, config: Any) -> None:
    from mkdocs.structure.files import File

    for image_path in image_paths:
        image_file_path = Path(image_path)
        if image_file_path.exists():
            rel_path = image_file_path.relative_to(docs_dir)
            # Normalize path for cross-platform compatibility
            rel_path_str = str(rel_path).replace("\\", "/")

            # Remove existing file to avoid duplicates
            self._remove_existing_file_by_path(rel_path_str)

            # Create and register new File object
            file_obj = File(rel_path_str, str(docs_dir), str(config["site_dir"]), ...)
            self.files.append(file_obj)
```

### Image Placement Strategy

- **Development Mode**: Images are generated in `docs_dir/output_dir` for immediate viewing
- **Build Mode**: MkDocs automatically copies registered images to the site directory
- **Cleanup**: Optional automatic cleanup after build completion via `cleanup_generated_images`

## Error Handling Architecture

### Exception Hierarchy

```mermaid
graph TD
    A[MermaidPreprocessorError]
    B[MermaidCLIError] --> A
    C[MermaidConfigError] --> A
    D[MermaidParsingError] --> A
    E[MermaidFileError] --> A
    F[MermaidValidationError] --> A
    G[MermaidImageError] --> A

    style A fill:#fce4ec,stroke:#c51162,stroke-width:2px
    style B fill:#e3f2fd,stroke:#1976d2,stroke-width:1px
    style C fill:#e3f2fd,stroke:#1976d2,stroke-width:1px
    style D fill:#e3f2fd,stroke:#1976d2,stroke-width:1px
    style E fill:#e3f2fd,stroke:#1976d2,stroke-width:1px
    style F fill:#e3f2fd,stroke:#1976d2,stroke-width:1px
    style G fill:#e3f2fd,stroke:#1976d2,stroke-width:1px
```

### Error Handling Strategy

1. **Configuration Errors**: Detected during `on_config` and immediately stop the build process
2. **CLI Execution Errors**: Handled based on `error_on_fail` configuration:
   - `true`: Stop build and raise exception
   - `false`: Log error and continue (skip failed diagrams)
3. **File System Errors**: Comprehensive handling with detailed error context and suggestions
4. **Validation Errors**: Input validation with specific error messages and remediation guidance

### Error Context and Logging

All custom exceptions include contextual information for debugging:

```python
class MermaidCLIError(MermaidPreprocessorError):
    def __init__(self, message: str, command: str = None, return_code: int = None, stderr: str = None):
        super().__init__(message, command=command, return_code=return_code, stderr=stderr)
```

This comprehensive error handling ensures robust operation across different environments and provides clear guidance for troubleshooting issues.

## Performance Optimizations

### Command Caching

The `MermaidImageGenerator` implements class-level command caching to avoid repeated CLI detection:

```python
class MermaidImageGenerator:
    _command_cache: ClassVar[dict[str, str]] = {}

    def _validate_dependencies(self) -> None:
        # Check cache first before trying to resolve mmdc command
        if primary_command in self._command_cache:
            self._resolved_mmdc_command = self._command_cache[primary_command]
            return
```

### Batch Processing

The plugin processes all Mermaid blocks in a page as a batch operation, minimizing I/O overhead and maintaining consistency across diagrams within the same document.

### Temporary File Management

Efficient temporary file handling with automatic cleanup ensures minimal disk usage and prevents resource leaks during the build process.
