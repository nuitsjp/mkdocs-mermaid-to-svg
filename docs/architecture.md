# アーキテクチャ設計

## 概要

MkDocs Mermaid to Image Pluginは、MkDocsプロジェクト内のMermaid図をビルド時に静的画像（PNG/SVG）に変換するプラグインです。Mermaid CLIを利用してMarkdownファイル内のMermaidコードブロックを画像化し、Markdownの内容を画像参照タグに置き換えます。これにより、PDF出力やオフライン環境での閲覧に対応します。

## プロジェクト構造

```
mkdocs-mermaid-to-image/
└── src/
    └── mkdocs_mermaid_to_image/
        ├── __init__.py             # パッケージ初期化・バージョン情報
        ├── plugin.py               # MkDocsプラグインメインクラス (MermaidToImagePlugin)
        ├── processor.py            # ページ処理の統括 (MermaidProcessor)
        ├── markdown_processor.py   # Markdown解析 (MarkdownProcessor)
        ├── image_generator.py      # 画像生成 (MermaidImageGenerator)
        ├── mermaid_block.py        # Mermaidブロック表現 (MermaidBlock)
        ├── config.py               # 設定スキーマ (MermaidPluginConfig, ConfigManager)
        ├── types.py                # 型定義 (TypedDictなど)
        ├── exceptions.py           # カスタム例外クラス
        ├── logging_config.py       # ロギング設定・構造化フォーマッタ
        └── utils.py                # ユーティリティ関数
```

## ファイル依存関係図

```mermaid
graph TD
    subgraph "Plugin Core"
        A[plugin.py] --> B[processor.py]
        A --> C[config.py]
        A --> D[exceptions.py]
        A --> E[utils.py]
        A --> F[logging_config.py]
    end

    subgraph "Processing Logic"
        B --> G[markdown_processor.py]
        B --> H[image_generator.py]
        B --> E
    end

    subgraph "Data & Helpers"
        G --> I[mermaid_block.py]
        G --> E
        H --> D
        H --> E
        I --> E
    end

    subgraph "External Dependencies"
        MkDocs[MkDocs]
        MermaidCLI[Mermaid CLI]
    end

    A --|> MkDocs
    H --> MermaidCLI

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

## クラス図

```mermaid
classDiagram
    direction LR

    class BasePlugin {
        <<interface>>
    }

    class MermaidToImagePlugin {
        +MermaidPluginConfig config
        +MermaidProcessor processor
        +Logger logger
        +list~str~ generated_images
        +Files files
        +bool is_serve_mode
        +bool is_verbose_mode
        +on_config(config)
        +on_files(files, config)
        +on_page_markdown(markdown, page, config, files)
        +on_post_build(config)
        +on_serve(server, config, builder)
        -_should_be_enabled(config) bool
        -_process_mermaid_diagrams(markdown, page, config)
        -_register_generated_images_to_files(image_paths, docs_dir, config)
    }
    MermaidToImagePlugin --|> BasePlugin

    class MermaidProcessor {
        +dict config
        +Logger logger
        +MarkdownProcessor markdown_processor
        +MermaidImageGenerator image_generator
        +process_page(page_file, markdown, output_dir, page_url) tuple
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
        +generate(code, output_path, config) bool
        -_build_mmdc_command(input_file, output_path, config) list
        -_validate_dependencies()
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

    MermaidToImagePlugin o-- MermaidProcessor
    MermaidToImagePlugin ..> ConfigManager
    MermaidProcessor o-- MarkdownProcessor
    MermaidProcessor o-- MermaidImageGenerator
    MarkdownProcessor --> MermaidBlock : creates
    MermaidBlock --> MermaidImageGenerator : uses
    MermaidImageGenerator --> MermaidCLIError : throws
```

## プラグイン処理フロー

### 1. プラグイン初期化フロー (`on_config`)

```mermaid
sequenceDiagram
    participant MkDocs
    participant Plugin as MermaidToImagePlugin
    participant CfgMgr as ConfigManager
    participant Proc as MermaidProcessor

    MkDocs->>Plugin: on_config(config)

    Note over Plugin: config_dict = dict(self.config)
    Plugin->>CfgMgr: validate_config(config_dict)
    CfgMgr-->>Plugin: 検証結果
    alt 検証失敗
        Plugin->>MkDocs: raise MermaidConfigError
    end

    Note over Plugin: verboseモードに応じてログレベルを設定
    alt verboseモード
        Plugin->>Plugin: config_dict["log_level"] = "DEBUG"
    else
        Plugin->>Plugin: config_dict["log_level"] = "WARNING"
    end

    Plugin->>Plugin: _should_be_enabled(self.config)
    Note over Plugin: enabled_if_env環境変数チェック含む
    alt プラグイン無効
        Plugin->>Plugin: logger.info("Plugin is disabled")
        Plugin-->>MkDocs: return config
    end

    Plugin->>Proc: new MermaidProcessor(config_dict)
    Proc->>Proc: MarkdownProcessor(config)
    Proc->>Proc: MermaidImageGenerator(config)
    Proc-->>Plugin: processorインスタンス

    Plugin->>Plugin: logger.info("Plugin initialized successfully")
    Plugin-->>MkDocs: 初期化完了
```

### 2. ファイル処理フロー (`on_files`)

```mermaid
sequenceDiagram
    participant MkDocs
    participant Plugin as MermaidToImagePlugin

    MkDocs->>Plugin: on_files(files, config)

    alt プラグイン無効 or processorなし
        Plugin-->>MkDocs: files (処理なし)
    end

    Plugin->>Plugin: self.files = files
    Plugin->>Plugin: self.generated_images = []
    Plugin-->>MkDocs: files
```

### 3. ページ処理フロー (`on_page_markdown`)

```mermaid
sequenceDiagram
    participant MkDocs
    participant Plugin as MermaidToImagePlugin
    participant Proc as MermaidProcessor
    participant MdProc as MarkdownProcessor
    participant Block as MermaidBlock
    participant ImgGen as MermaidImageGenerator

    MkDocs->>Plugin: on_page_markdown(markdown, page, ...)

    alt プラグイン無効
        Plugin-->>MkDocs: markdown
    end

    alt serveモードの場合
        Plugin-->>MkDocs: markdown (スキップ)
    end

    Plugin->>Proc: process_page(page.file.src_path, markdown, output_dir, page.url)
    Proc->>MdProc: extract_mermaid_blocks(markdown)
    MdProc-->>Proc: blocks: List[MermaidBlock]

    alt Mermaidブロックなし
        Proc-->>Plugin: (markdown, [])
        Plugin-->>MkDocs: markdown
    end

    loop 各Mermaidブロック
        Proc->>Block: generate_image(output_path, image_generator, config)
        Block->>ImgGen: generate(code, output_path, config)
        ImgGen-->>Block: success: bool
        Block-->>Proc: success: bool

        alt 成功
            Proc->>Proc: image_pathsに追加
            Proc->>Proc: successful_blocksに追加
        else 失敗 and error_on_fail=false
            Proc->>Proc: 警告ログ出力、処理継続
        else 失敗 and error_on_fail=true
            Proc->>Proc: 処理継続（エラーは上位でキャッチ）
        end
    end

    alt 成功したブロックあり
        Proc->>MdProc: replace_blocks_with_images(markdown, successful_blocks, image_paths, page_file, page_url)
        MdProc-->>Proc: modified_markdown
        Proc-->>Plugin: (modified_markdown, image_paths)
    else
        Proc-->>Plugin: (markdown, [])
    end

    Plugin->>Plugin: generated_imagesを更新
    Plugin->>Plugin: _register_generated_images_to_files()
    Plugin-->>MkDocs: modified_markdown
```

### 4. 画像生成フロー (`MermaidImageGenerator.generate`)

```mermaid
sequenceDiagram
    participant ImgGen as MermaidImageGenerator
    participant Utils
    participant Subprocess
    participant FileSystem

    ImgGen->>Utils: get_temp_file_path()
    Utils-->>ImgGen: temp_file

    ImgGen->>FileSystem: temp_file.write_text(code)

    ImgGen->>FileSystem: ensure_directory(output_path.parent)

    ImgGen->>ImgGen: _build_mmdc_command(temp_file, output_path, config)
    Note over ImgGen: CI環境の場合、--no-sandbox付きの<br/>一時Puppeteer設定を生成
    ImgGen-->>ImgGen: (cmd: list[str], puppeteer_config_file: str | None)

    ImgGen->>Subprocess: run(cmd)
    Subprocess-->>ImgGen: result

    alt 実行失敗 or 画像ファイルなし
        ImgGen->>ImgGen: _handle_command_failure() or _handle_missing_output()
        alt error_on_fail=true
            ImgGen->>ImgGen: raise MermaidCLIError or MermaidImageError
        end
        ImgGen-->>Block: return False
    end

    ImgGen->>ImgGen: logger.info(...)
    ImgGen-->>Block: return True

    note right of ImgGen: finallyブロックで一時ファイルをクリーンアップ
    ImgGen->>Utils: clean_temp_file(temp_file)
    ImgGen->>Utils: clean_temp_file(puppeteer_config_file)
```

## 環境別処理戦略

このプラグインは、`mkdocs build`（本番ビルド）と`mkdocs serve`（開発サーバー）で動作を切り替えます。

### モード判定

```python
# src/mkdocs_mermaid_to_image/plugin.py
class MermaidToImagePlugin(BasePlugin[MermaidPluginConfig]):
    def __init__(self) -> None:
        # ...
        self.is_serve_mode: bool = "serve" in sys.argv
        self.is_verbose_mode: bool = "--verbose" in sys.argv or "-v" in sys.argv
```

### プラグイン有効化制御

プラグインの有効化は、環境変数設定に基づいて動的に制御できます：

```python
# src/mkdocs_mermaid_to_image/plugin.py
def _should_be_enabled(self, config: MermaidPluginConfig) -> bool:
    enabled_if_env = config.get("enabled_if_env")

    if enabled_if_env is not None:
        # 環境変数の存在と値をチェック
        env_value = os.environ.get(enabled_if_env)
        return env_value is not None and env_value.strip() != ""

    # 通常のenabled設定に従う
    return config.get("enabled", True)
```

### ログレベル制御

verboseモードの有無に応じてログ出力を調整：

```python
# src/mkdocs_mermaid_to_image/plugin.py
# verboseモードに応じてログレベルを動的に設定
config_dict["log_level"] = "DEBUG" if self.is_verbose_mode else "WARNING"
```

## プラグイン設定管理

設定は `mkdocs.yml` で行われ、`src/mkdocs_mermaid_to_image/plugin.py` の `config_scheme` と `src/mkdocs_mermaid_to_image/config.py` の `MermaidPluginConfig` で定義されます。

### 設定スキーマ

```python
# src/mkdocs_mermaid_to_image/plugin.py
class MermaidToImagePlugin(BasePlugin[MermaidPluginConfig]):
    config_scheme = (
        ("enabled", config_options.Type(bool, default=True)),
        ("enabled_if_env", config_options.Optional(config_options.Type(str))),
        ("output_dir", config_options.Type(str, default="assets/images")),
        ("image_format", config_options.Choice(["png", "svg"], default="png")),
        # ... 他の設定項目 ...
        ("cleanup_generated_images", config_options.Type(bool, default=False)),
    )
```

### 設定検証

`ConfigManager.validate_config()` で設定値の整合性を検証します。

## ファイル管理戦略

### 生成画像のFiles登録

生成された画像をMkDocsのFilesオブジェクトに動的に追加し、ビルド対象に含めます。

```python
# src/mkdocs_mermaid_to_image/plugin.py
def _register_generated_images_to_files(self, image_paths: list[str], docs_dir: Path, config: Any) -> None:
    if not (image_paths and self.files):
        return

    from mkdocs.structure.files import File

    for image_path in image_paths:
        image_file_path = Path(image_path)
        if image_file_path.exists():
            rel_path = image_file_path.relative_to(docs_dir)
            file_obj = File(str(rel_path), str(docs_dir), str(config["site_dir"]), ...)
            self.files.append(file_obj)
```

### 画像の配置戦略

- **開発時**: `docs_dir` 内の `output_dir` に画像を生成します。
- **ビルド時**: MkDocsが `_register_generated_images_to_files` で登録された画像を自動的にサイトディレクトリにコピーします。
- **クリーンアップ**: `cleanup_generated_images` 設定でビルド後の自動削除が可能です。

## エラーハンドリング戦略

### 例外階層

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
```

### エラー発生時の処理

- **設定エラー (`MermaidConfigError`, `MermaidFileError`)**: `on_config`で発生し、ビルドプロセスを即座に停止させます。
- **CLI実行エラー (`MermaidCLIError`)**: `image_generator.py`で発生します。
  - `error_on_fail=true`: 例外が送出され、ビルドが停止します。
  - `error_on_fail=false`: エラーログを出力後、処理を継続します（該当図は画像化されません）。
- **画像生成エラー (`MermaidImageError`)**: 画像ファイルが生成されなかった場合に発生します。
- **その他エラー**: 予期せぬエラーは `on_page_markdown` 内でキャッチされ、`error_on_fail` の設定に従って処理されます。

### ログ出力戦略

- **設定レベル**: `log_level` 設定で制御します。
- **Verboseモード**: コマンドライン引数 `--verbose` / `-v` で詳細ログ（`DEBUG`レベル）を有効化します。
- **通常モード**: `WARNING`レベルのログのみ出力されます。
- **条件付きログ**: 画像生成時は常にINFOレベルで結果を出力します。
