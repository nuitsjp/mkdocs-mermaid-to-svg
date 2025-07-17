# アーキテクチャドキュメント

## 概要

MkDocs Mermaid to Image Pluginは、MkDocsビルドプロセス中にMermaidダイアグラムを静的なSVGイメージに変換する包括的なソリューションです。このプラグインは、Mermaid CLI（`@mermaid-js/mermaid-cli`）を活用してコードブロックを静的画像に変換することで、PDF出力の生成とMermaidダイアグラムを含むドキュメントのオフライン表示を可能にします。

## プロジェクト構成

```
mkdocs-mermaid-to-image/
└── src/
    └── mkdocs_mermaid_to_svg/
        ├── __init__.py             # パッケージ初期化とバージョン情報
        ├── _version.py             # バージョン管理
        ├── plugin.py               # メインMkDocsプラグインクラス (MermaidSvgConverterPlugin)
        ├── processor.py            # ページ処理オーケストレーター (MermaidProcessor)
        ├── markdown_processor.py   # Markdownパースと変換 (MarkdownProcessor)
        ├── image_generator.py      # Mermaid CLI経由での画像生成 (MermaidImageGenerator)
        ├── mermaid_block.py        # Mermaidブロック表現 (MermaidBlock)
        ├── config.py               # 設定スキーマと検証 (ConfigManager)
        ├── types.py                # 型定義とTypedDictクラス
        ├── exceptions.py           # カスタム例外階層
        ├── logging_config.py       # 構造化ログ設定
        └── utils.py                # ユーティリティ関数とヘルパー
```

## コンポーネント依存関係

```mermaid
graph TD
    subgraph "プラグインコア"
        A[plugin.py] --> B[processor.py]
        A --> C[config.py]
        A --> D[exceptions.py]
        A --> E[utils.py]
        A --> F[logging_config.py]
    end

    subgraph "処理パイプライン"
        B --> G[markdown_processor.py]
        B --> H[image_generator.py]
        B --> E
    end

    subgraph "データモデル & ヘルパー"
        G --> I[mermaid_block.py]
        G --> E
        H --> D
        H --> E
        I --> E
    end

    subgraph "外部依存関係"
        MkDocs[MkDocsフレームワーク]
        MermaidCLI["Mermaid CLI (@mermaid-js/mermaid-cli)"]
    end

    A -.->|実装| MkDocs
    H -->|実行| MermaidCLI

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

## クラスアーキテクチャ

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

## 処理フロー

### 1. プラグイン初期化 (`on_config`)

```mermaid
sequenceDiagram
    participant MkDocs
    participant Plugin as MermaidSvgConverterPlugin
    participant CfgMgr as ConfigManager
    participant Proc as MermaidProcessor

    MkDocs->>Plugin: on_config(config)

    Note over Plugin: self.configから設定辞書を抽出
    Plugin->>CfgMgr: validate_config(config_dict)
    CfgMgr-->>Plugin: 検証結果
    alt 検証失敗
        Plugin->>MkDocs: raise MermaidConfigError
    end

    Note over Plugin: 冗長モードに基づいてログレベルを設定
    alt 冗長モード有効
        Plugin->>Plugin: config_dict["log_level"] = "DEBUG"
    else 通常モード
        Plugin->>Plugin: config_dict["log_level"] = "WARNING"
    end

    Plugin->>Plugin: _should_be_enabled(self.config)
    Note over Plugin: enabled_if_env環境変数をチェック
    alt プラグイン無効
        Plugin->>Plugin: logger.info("Plugin is disabled")
        Plugin-->>MkDocs: return config
    end

    Plugin->>Proc: new MermaidProcessor(config_dict)
    Proc->>Proc: MarkdownProcessor(config)を初期化
    Proc->>Proc: MermaidImageGenerator(config)を初期化
    Proc-->>Plugin: プロセッサーインスタンス

    Plugin->>Plugin: logger.info("Plugin initialized successfully")
    Plugin-->>MkDocs: return config
```

### 2. ファイル登録 (`on_files`)

```mermaid
sequenceDiagram
    participant MkDocs
    participant Plugin as MermaidSvgConverterPlugin

    MkDocs->>Plugin: on_files(files, config)

    alt プラグイン無効またはプロセッサーなし
        Plugin-->>MkDocs: return files (処理なし)
    end

    Plugin->>Plugin: self.files = files
    Plugin->>Plugin: self.generated_images = []
    Plugin-->>MkDocs: return files
```

### 3. ページ処理 (`on_page_markdown`)

```mermaid
sequenceDiagram
    participant MkDocs
    participant Plugin as MermaidSvgConverterPlugin
    participant Proc as MermaidProcessor
    participant MdProc as MarkdownProcessor
    participant Block as MermaidBlock
    participant ImgGen as MermaidImageGenerator

    MkDocs->>Plugin: on_page_markdown(markdown, page, config, files)

    alt プラグイン無効
        Plugin-->>MkDocs: return markdown (変更なし)
    end

    alt サーブモード検出
        Plugin-->>MkDocs: return markdown (処理をスキップ)
    end

    Plugin->>Proc: process_page(page.file.src_path, markdown, output_dir, page.url)
    Proc->>MdProc: extract_mermaid_blocks(markdown)
    MdProc-->>Proc: blocks: List[MermaidBlock]

    alt Mermaidブロックが見つからない
        Proc-->>Plugin: (markdown, [])
        Plugin-->>MkDocs: return markdown
    end

    loop 各Mermaidブロック
        Proc->>Block: generate_image(output_path, image_generator, config)
        Block->>ImgGen: generate(code, output_path, merged_config)
        ImgGen-->>Block: success: bool
        Block-->>Proc: success: bool

        alt 画像生成成功
            Proc->>Proc: image_pathsリストに追加
            Proc->>Proc: successful_blocksリストに追加
        else 失敗 かつ error_on_fail=false
            Proc->>Proc: 警告をログ、処理続行
        else 失敗 かつ error_on_fail=true
            Proc->>Proc: 続行（エラーは上位で処理）
        end
    end

    alt 成功したブロックが存在
        Proc->>MdProc: replace_blocks_with_images(markdown, successful_blocks, image_paths, page_file, page_url)
        MdProc-->>Proc: modified_markdown
        Proc-->>Plugin: (modified_markdown, image_paths)
    else 成功したブロックなし
        Proc-->>Plugin: (markdown, [])
    end

    Plugin->>Plugin: generated_imagesリストを更新
    Plugin->>Plugin: _register_generated_images_to_files()
    Plugin-->>MkDocs: return modified_markdown
```

### 4. 画像生成 (`MermaidImageGenerator.generate`)

```mermaid
sequenceDiagram
    participant ImgGen as MermaidImageGenerator
    participant Utils
    participant Subprocess
    participant FileSystem

    ImgGen->>Utils: get_temp_file_path(".mmd")
    Utils-->>ImgGen: temp_file_path

    ImgGen->>FileSystem: temp_fileにmermaid_codeを書き込み
    ImgGen->>FileSystem: ensure_directory(output_path.parent)

    ImgGen->>ImgGen: _build_mmdc_command(temp_file, output_path, config)
    Note over ImgGen: CI環境用Puppeteer設定を作成<br/>--no-sandboxとブラウザ設定で
    ImgGen-->>ImgGen: (cmd: list[str], puppeteer_config_file: str, mermaid_config_file: str)

    ImgGen->>Subprocess: run(cmd) 30秒タイムアウト
    Subprocess-->>ImgGen: result: CompletedProcess

    alt コマンド実行失敗
        ImgGen->>ImgGen: _handle_command_failure()
        alt error_on_fail=true
            ImgGen->>ImgGen: raise MermaidCLIError
        end
        ImgGen-->>Block: return False
    end

    alt 出力ファイルが作成されない
        ImgGen->>ImgGen: _handle_missing_output()
        alt error_on_fail=true
            ImgGen->>ImgGen: raise MermaidImageError
        end
        ImgGen-->>Block: return False
    end

    ImgGen->>ImgGen: logger.info("Generated image: ...")
    ImgGen-->>Block: return True

    note over ImgGen: finallyブロック: 一時ファイルをクリーンアップ
    ImgGen->>Utils: clean_temp_file(temp_file)
    ImgGen->>Utils: clean_temp_file(puppeteer_config_file)
    ImgGen->>Utils: clean_temp_file(mermaid_config_file)
```

## 設定管理

プラグインの設定は`mkdocs.yml`を通じて管理され、`ConfigManager`クラスを使用して検証されます。

### 設定スキーマ

```python
# mkdocs.yml で利用可能な設定オプション
plugins:
  - mkdocs-mermaid-to-image:
      enabled_if_env: "ENABLE_MERMAID"        # 条件付き有効化のための環境変数
      output_dir: "assets/images"             # 生成画像のディレクトリ
      mermaid_config: {...}                   # Mermaid設定オブジェクトまたはファイルパス
      theme: "default"                        # Mermaidテーマ: default, dark, forest, neutral
      css_file: "path/to/custom.css"          # スタイリング用オプショナルCSSファイル
      puppeteer_config: "path/to/config.json" # オプショナルPuppeteer設定
      temp_dir: "/tmp"                        # 処理用一時ディレクトリ
      preserve_original: false                # 元のMermaidブロックを画像と並行して保持
      error_on_fail: false                    # 画像生成失敗時にビルドを停止
      log_level: "INFO"                       # ログレベル
      cleanup_generated_images: false         # ビルド後に生成画像をクリーンアップ
```

### 検証ロジック

`ConfigManager.validate_config()`メソッドは以下を保証します：
- 指定されたファイルパス（CSS、Puppeteer設定）が存在する
- 全オプション間の設定の整合性

## 環境固有の動作

### モード検出

プラグインは実行環境を自動的に検出します：

```python
# src/mkdocs_mermaid_to_svg/plugin.py
class MermaidSvgConverterPlugin(BasePlugin):
    def __init__(self) -> None:
        self.is_serve_mode: bool = "serve" in sys.argv
        self.is_verbose_mode: bool = "--verbose" in sys.argv or "-v" in sys.argv
```

### 条件付き有効化

プラグインの有効化は環境変数で制御できます：

```python
def _should_be_enabled(self, config: dict[str, Any]) -> bool:
    enabled_if_env = config.get("enabled_if_env")

    if enabled_if_env is not None:
        # 環境変数が存在し、空でない値を持つかチェック
        env_value = os.environ.get(enabled_if_env)
        return env_value is not None and env_value.strip() != ""

    # デフォルト: 条件付き環境変数が設定されていない場合は常に有効
    return True
```

### ログ戦略

ログレベルは冗長モードに基づいて動的に調整されます：

```python
# 冗長モードに基づいてログレベルを調整
config_dict["log_level"] = "DEBUG" if self.is_verbose_mode else "WARNING"
```

## ファイル管理戦略

### 生成画像の登録

生成された画像は、サイトディレクトリへの適切なコピーを確保するため、MkDocsのファイルシステムに動的に登録されます：

```python
def _register_generated_images_to_files(self, image_paths: list[str], docs_dir: Path, config: Any) -> None:
    from mkdocs.structure.files import File

    for image_path in image_paths:
        image_file_path = Path(image_path)
        if image_file_path.exists():
            rel_path = image_file_path.relative_to(docs_dir)
            # クロスプラットフォーム互換性のためのパス正規化
            rel_path_str = str(rel_path).replace("\\", "/")

            # 重複を避けるため既存ファイルを削除
            self._remove_existing_file_by_path(rel_path_str)

            # 新しいFileオブジェクトを作成し登録
            file_obj = File(rel_path_str, str(docs_dir), str(config["site_dir"]), ...)
            self.files.append(file_obj)
```

### 画像配置戦略

- **開発モード**: 即座に表示するため`docs_dir/output_dir`に画像を生成
- **ビルドモード**: MkDocsが登録された画像を自動的にサイトディレクトリにコピー
- **クリーンアップ**: `cleanup_generated_images`によるビルド完了後のオプション自動クリーンアップ

## エラーハンドリングアーキテクチャ

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
    style B fill:#e3f2fd,stroke:#1976d2,stroke-width:1px
    style C fill:#e3f2fd,stroke:#1976d2,stroke-width:1px
    style D fill:#e3f2fd,stroke:#1976d2,stroke-width:1px
    style E fill:#e3f2fd,stroke:#1976d2,stroke-width:1px
    style F fill:#e3f2fd,stroke:#1976d2,stroke-width:1px
    style G fill:#e3f2fd,stroke:#1976d2,stroke-width:1px
```

### エラーハンドリング戦略

1. **設定エラー**: `on_config`中に検出され、即座にビルドプロセスを停止
2. **CLI実行エラー**: `error_on_fail`設定に基づいて処理：
   - `true`: ビルドを停止し例外を発生
   - `false`: エラーをログし継続（失敗したダイアグラムをスキップ）
3. **ファイルシステムエラー**: 詳細なエラーコンテキストと提案を含む包括的な処理
4. **検証エラー**: 特定のエラーメッセージと修正ガイダンスを含む入力検証

### エラーコンテキストとログ

すべてのカスタム例外にはデバッグ用のコンテキスト情報が含まれます：

```python
class MermaidCLIError(MermaidPreprocessorError):
    def __init__(self, message: str, command: str = None, return_code: int = None, stderr: str = None):
        super().__init__(message, command=command, return_code=return_code, stderr=stderr)
```

この包括的なエラーハンドリングは、異なる環境での堅牢な動作を保証し、問題のトラブルシューティングのための明確なガイダンスを提供します。

## パフォーマンス最適化

### コマンドキャッシング

`MermaidImageGenerator`は、繰り返しのCLI検出を避けるためにクラスレベルのコマンドキャッシングを実装しています：

```python
class MermaidImageGenerator:
    _command_cache: ClassVar[dict[str, str]] = {}

    def _validate_dependencies(self) -> None:
        # mmdcコマンドの解決を試みる前にまずキャッシュをチェック
        if primary_command in self._command_cache:
            self._resolved_mmdc_command = self._command_cache[primary_command]
            return
```

### バッチ処理

プラグインは、I/Oオーバーヘッドを最小限に抑え、同じドキュメント内のダイアグラム間の整合性を維持するために、ページ内のすべてのMermaidブロックをバッチ操作として処理します。

### 一時ファイル管理

自動クリーンアップ機能を持つ効率的な一時ファイル処理により、ビルドプロセス中の最小限のディスク使用量を確保し、リソースリークを防ぎます。
