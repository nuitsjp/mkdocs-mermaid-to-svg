# MkDocs Mermaid to Image Plugin - アーキテクチャ設計

## 概要

MkDocs Mermaid to Image Pluginは、MkDocsプロジェクト内のMermaid図をビルド時に静的画像（PNG/SVG）に変換するプラグインです。Mermaid CLIを利用してMarkdownファイル内のMermaidコードブロックを画像化し、Markdownの内容を画像参照タグに置き換えます。これにより、PDF出力やオフライン環境での閲覧に対応します。

**参考**: MkDocsプラグインシステムの詳細については [`docs/mkdocs-architecture.md`](docs/mkdocs-architecture.md) を参照してください。

## プロジェクト構造

```
mkdocs-mermaid-to-image/
└── src/
    └── mkdocs_mermaid_to_image/
        ├── __init__.py             # パッケージ初期化
        ├── _version.py             # バージョン情報 (setuptools_scm)
        ├── plugin.py               # MkDocsプラグインメインクラス (MermaidToImagePlugin)
        ├── processor.py            # ページ処理の統括 (MermaidProcessor)
        ├── markdown_processor.py   # Markdown解析 (MarkdownProcessor)
        ├── image_generator.py      # 画像生成 (MermaidImageGenerator)
        ├── mermaid_block.py        # Mermaidブロック表現 (MermaidBlock)
        ├── config.py               # 設定スキーマ (MermaidPluginConfig, ConfigManager)
        ├── exceptions.py           # カスタム例外クラス
        ├── types.py                # 型定義
        ├── utils.py                # ユーティリティ関数
        └── logging_config.py       # ロギング設定
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
        B --> F
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
        +on_config(config)
        +on_page_markdown(markdown, page, config, files)
        +on_post_build(config)
    }
    MermaidToImagePlugin --|> BasePlugin

    class MermaidProcessor {
        +MarkdownProcessor markdown_processor
        +MermaidImageGenerator image_generator
        +process_page(markdown, page_file, output_dir)
    }

    class MarkdownProcessor {
        +extract_mermaid_blocks(markdown) List~MermaidBlock~
        +replace_blocks_with_images(markdown, blocks, paths)
    }

    class MermaidImageGenerator {
        +generate(code, output_path, config) bool
        -_build_mmdc_command()
    }

    class MermaidBlock {
        +str code
        +dict attributes
        +generate_image(generator, config)
        +get_image_markdown(path)
    }

    class MermaidPluginConfig {
        +bool enabled
        +str output_dir
        +str image_format
        +str theme
        ...
    }

    class ConfigManager {
        <<static>>
        +get_config_scheme()
        +validate_config(config)
    }

    class MermaidPreprocessorError {<<exception>>}
    class MermaidCLIError {<<exception>>}
    class MermaidConfigError {<<exception>>}
    class MermaidParsingError {<<exception>>}

    MermaidCLIError --|> MermaidPreprocessorError
    MermaidConfigError --|> MermaidPreprocessorError
    MermaidParsingError --|> MermaidPreprocessorError

    MermaidToImagePlugin o-- MermaidProcessor
    MermaidToImagePlugin o-- MermaidPluginConfig
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
    participant Logger as logging_config

    MkDocs->>Plugin: on_config(config)
    Plugin->>CfgMgr: validate_config(self.config)
    CfgMgr-->>Plugin: 検証結果
    alt 検証失敗
        Plugin->>MkDocs: raise MermaidConfigError
    end

    Plugin->>Logger: setup_logger()
    Logger-->>Plugin: logger

    alt プラグイン無効
        Plugin-->>MkDocs: return config
    end

    Plugin->>Proc: new MermaidProcessor(config)
    Proc-->>Plugin: processorインスタンス

    Plugin->>Plugin: 出力ディレクトリ作成
    Plugin-->>MkDocs: 初期化完了
```

### 2. ページ処理フロー (`on_page_markdown`)

```mermaid
sequenceDiagram
    participant MkDocs
    participant Plugin as MermaidToImagePlugin
    participant Proc as MermaidProcessor
    participant MdProc as MarkdownProcessor
    participant ImgGen as MermaidImageGenerator

    MkDocs->>Plugin: on_page_markdown(markdown, page, ...)
    alt serveモードの場合
        Plugin-->>MkDocs: markdown (スキップ)
    end

    Plugin->>Proc: process_page(markdown, page.file.src_path, output_dir)
    Proc->>MdProc: extract_mermaid_blocks(markdown)
    MdProc-->>Proc: blocks: List[MermaidBlock]

    alt Mermaidブロックなし
        Proc-->>Plugin: (markdown, [])
        Plugin-->>MkDocs: markdown
    end

    loop 各Mermaidブロック
        Proc->>ImgGen: generate(block.code, output_path, config)
        ImgGen-->>Proc: success: bool
    end

    Proc->>MdProc: replace_blocks_with_images(markdown, successful_blocks, image_paths)
    MdProc-->>Proc: modified_markdown

    Proc-->>Plugin: (modified_markdown, image_paths)
    Plugin->>Plugin: 生成画像リストを更新
    Plugin-->>MkDocs: modified_markdown
```

### 3. 画像生成フロー (`image_generator.py`)

```mermaid
sequenceDiagram
    participant Proc as MermaidProcessor
    participant ImgGen as MermaidImageGenerator
    participant Utils
    participant Subprocess
    participant FileSystem

    Proc->>ImgGen: generate(code, output_path, config)
    ImgGen->>Utils: get_temp_file_path()
    Utils-->>ImgGen: temp_file

    ImgGen->>FileSystem: write(temp_file, mermaid_code)

    ImgGen->>ImgGen: _build_mmdc_command(temp_file, output_path, config)
    ImgGen-->>ImgGen: cmd: list[str]

    ImgGen->>Subprocess: run(cmd)
    Subprocess-->>ImgGen: result

    alt 実行失敗
        ImgGen->>ImgGen: logger.error(...)
        ImgGen-->>Proc: return False
    end

    ImgGen->>FileSystem: Path(output_path).exists()
    alt 画像ファイルなし
        ImgGen->>ImgGen: logger.error(...)
        ImgGen-->>Proc: return False
    end

    ImgGen-->>Proc: return True

    finally
        ImgGen->>Utils: clean_temp_file(temp_file)
    end
```

## 開発・本番環境での処理分岐戦略

このプラグインは、`mkdocs build`（本番ビルド）と`mkdocs serve`（開発サーバー）で動作を切り替えます。`serve`モードでは、高速なリロードを実現するため、画像の生成処理をスキップします。

この判定は、プラグインの初期化時に `sys.argv` をチェックすることで行われます。

```python
# src/mkdocs_mermaid_to_image/plugin.py
class MermaidToImagePlugin(BasePlugin[MermaidPluginConfig]):
    def __init__(self) -> None:
        # ...
        self.is_serve_mode: bool = "serve" in sys.argv

    def on_page_markdown(self, markdown: str, ...) -> Optional[str]:
        # ...
        if self.is_serve_mode:
            # serveモードでは画像生成をスキップ
            return markdown
        # ... buildモードの処理 ...
```

このシンプルなアプローチにより、`on_startup` フック（MkDocs 1.4+）への依存をなくし、幅広いMkDocsバージョンとの互換性を維持しています。

## プラグイン設定管理

設定は `src/mkdocs_mermaid_to_image/config.py` で一元管理されます。

- **`MermaidPluginConfig`**: `mkdocs.config.base.Config` を継承したクラスで、`mkdocs.yml` で利用可能なすべての設定項目とその型、デフォルト値を定義します。
- **`ConfigManager`**: 設定の検証ロジック（ファイルパスの存在確認など）を提供する静的クラス。`on_config`フック内で呼び出されます。

```python
# src/mkdocs_mermaid_to_image/config.py

class MermaidPluginConfig(Config):
    enabled = config_options.Type(bool, default=True)
    output_dir = config_options.Type(str, default="assets/images")
    # ... 他の設定項目 ...

class ConfigManager:
    @staticmethod
    def validate_config(config: dict[str, Any]) -> bool:
        # ... バリデーションロジック ...
        return True
```

## エラーハンドリング戦略

`src/mkdocs_mermaid_to_image/exceptions.py` で定義されたカスタム例外階層を用いて、エラーの種類に応じた詳細な情報を提供します。

### 例外階層

```mermaid
graph TD
    A[MermaidPreprocessorError]
    B[MermaidCLIError] --> A
    C[MermaidConfigError] --> A
    D[MermaidParsingError] --> A

    style A fill:#fce4ec,stroke:#c51162,stroke-width:2px
```

- **`MermaidPreprocessorError`**: プラグイン内で発生するすべてのカスタム例外の基底クラス。
- **`MermaidCLIError`**: Mermaid CLIの実行に失敗した場合に送出。コマンド、リターンコード、標準エラー出力などの詳細情報を含みます。
- **`MermaidConfigError`**: 設定 (`mkdocs.yml`) に問題がある場合に送出。
- **`MermaidParsingError`**: Markdown内のMermaidブロックの解析に失敗した場合に送出（現在は未使用、将来の拡張用）。

### エラー発生時の処理

- **設定エラー (`MermaidConfigError`)**: `on_config`で発生。ビルドプロセスを即座に停止させます。
- **CLI実行エラー (`MermaidCLIError`)**: `image_generator.py`で発生。`error_on_fail` 設定が `true` の場合はビルドを停止させ、`false` の場合はエラーをログに出力して処理を続行します（該当の図は画像化されません）。
