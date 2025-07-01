# コードリファクタリング計画書

## 分析結果サマリー

`similarity-py`による分析結果、以下の主要な重複コードが検出されました：

### 高優先度（即座に対処）
1. **例外クラスの初期化メソッド** - `src/mkdocs_mermaid_to_image/exceptions.py`
   - 類似度: 94.39%〜100.00%
   - 影響範囲: 例外処理全体のコード品質

2. **テストコードの設定検証テスト** - `tests/unit/test_config.py`
   - 類似度: 97.59%〜98.81%
   - 影響範囲: テストコードの保守性

### 中優先度（計画的対処）
3. **ファイルクリーンアップ処理** - `src/mkdocs_mermaid_to_image/utils.py`
   - 類似度: 85.07%〜87.29%
   - 影響範囲: リソース管理とエラーハンドリング

4. **テストモック設定** - 複数のテストファイル
   - 類似度: 81.52%〜90.33%
   - 影響範囲: テストコードの保守性

## 詳細リファクタリング計画

### 1. 【高優先度】例外クラスのリファクタリング

**問題点:**
- 6つの例外クラスの`__init__`メソッドが95%〜100%類似
- 共通のパターン：`details`辞書作成 → `super().__init__(message, details)`呼び出し
- コードの重複により保守性が低下

**解決策:**
```python
# 共通基底クラスの抽出
class MermaidPreprocessorError(Exception):
    def __init__(self, message: str, **context_params) -> None:
        details = {k: v for k, v in context_params.items() if v is not None}

        # mermaid_content/mermaid_codeの切り詰め処理を共通化
        for key in ['mermaid_content', 'mermaid_code']:
            if key in details and isinstance(details[key], str) and len(details[key]) > 200:
                details[key] = details[key][:200] + "..."

        super().__init__(message)
        self.details = details

# 各例外クラスの簡略化
class MermaidCLIError(MermaidPreprocessorError):
    def __init__(self, message: str, command: str | None = None,
                 return_code: int | None = None, stderr: str | None = None) -> None:
        super().__init__(message, command=command, return_code=return_code, stderr=stderr)

class MermaidConfigError(MermaidPreprocessorError):
    def __init__(self, message: str, config_key: str | None = None,
                 config_value: str | int | None = None, suggestion: str | None = None) -> None:
        super().__init__(message, config_key=config_key, config_value=config_value, suggestion=suggestion)
```

**実装手順:**
1. 基底クラス`MermaidPreprocessorError`の`__init__`メソッドを汎用化
2. 各例外クラスを簡潔な実装に変更
3. テストケースの実行で動作確認
4. 型チェック（mypy）でAPI互換性確認

**期待効果:**
- コード行数：150行 → 約80行（約47%削減）
- 保守性：例外処理の変更が1箇所で済む
- 拡張性：新しい例外クラス追加が容易

### 2. 【高優先度】テスト設定検証の共通化

**問題点:**
- `test_config.py`で設定エラーテストが98%類似
- 各テストで同じパターンの`invalid_config`辞書作成
- テストメソッド名以外ほぼ同一

**解決策:**
```python
# パラメータ化テストの導入
@pytest.mark.parametrize("config_override,expected_error,error_message", [
    ({"width": -100}, MermaidConfigError, "Width and height must be positive integers"),
    ({"height": 0}, MermaidConfigError, "Width and height must be positive integers"),
    ({"scale": -1.5}, MermaidConfigError, "Scale must be a positive number"),
    ({"css_file": "/nonexistent/file.css"}, MermaidFileError, "CSS file not found"),
    ({"puppeteer_config": "/nonexistent/config.json"}, MermaidFileError, "Puppeteer config file not found"),
])
def test_validate_config_errors(config_override, expected_error, error_message):
    base_config = {
        "width": 800,
        "height": 600,
        "scale": 1.0,
        "css_file": None,
        "puppeteer_config": None,
    }
    invalid_config = {**base_config, **config_override}

    with pytest.raises(expected_error, match=error_message):
        ConfigManager.validate_config(invalid_config)
```

**実装手順:**
1. パラメータ化テストへの変更
2. 個別テストメソッドの削除
3. テスト実行で同等の検証が可能か確認
4. カバレッジレポートで網羅性確認

**期待効果:**
- コード行数：70行 → 約20行（約71%削減）
- 保守性：新しい設定検証ケース追加が容易
- 可読性：テストケースが一目で把握可能

### 3. 【中優先度】ファイルクリーンアップ処理の統一

**問題点:**
- `clean_temp_file`と`clean_generated_images`で重複したエラーハンドリング
- `PermissionError`と`OSError`の処理パターンが87%類似
- ログ出力の形式も類似

**解決策:**
```python
def clean_file_with_error_handling(file_path: str, logger: logging.Logger | None = None,
                                   operation_type: str = "cleanup") -> bool:
    """ファイル削除の共通処理（エラーハンドリング付き）"""
    if not file_path:
        return False

    file_obj = Path(file_path)

    try:
        if file_obj.exists():
            file_obj.unlink()
            if logger:
                logger.debug(f"Successfully cleaned file: {file_path}")
            return True
        return False
    except (PermissionError, OSError) as e:
        error_type = type(e).__name__
        if logger:
            logger.warning(
                f"{error_type} when cleaning file: {file_path}",
                extra={
                    "context": {
                        "file_path": file_path,
                        "operation_type": operation_type,
                        "error_type": error_type,
                        "error_message": str(e),
                        "suggestion": _get_cleanup_suggestion(error_type),
                    }
                },
            )
        return False

def clean_temp_file(file_path: str) -> None:
    logger = get_logger(__name__)
    clean_file_with_error_handling(file_path, logger, "temp_cleanup")

def clean_generated_images(image_paths: list[str], logger: logging.Logger | None) -> None:
    if not image_paths:
        return

    results = [clean_file_with_error_handling(path, logger, "image_cleanup")
               for path in image_paths if path]

    cleaned_count = sum(results)
    error_count = len(results) - cleaned_count

    if (cleaned_count > 0 or error_count > 0) and logger:
        logger.info(f"Image cleanup: {cleaned_count} cleaned, {error_count} errors")
```

**実装手順:**
1. 共通クリーンアップ関数の実装
2. 既存関数のリファクタリング
3. 単体テストで動作確認
4. 統合テストでエラーハンドリング確認

**期待効果:**
- コード行数：100行 → 約65行（約35%削減）
- エラーハンドリングの一貫性向上
- テスタビリティ向上

### 4. 【中優先度】テストモック設定の共通化

**問題点:**
- テストファイル間でモック設定パターンが類似
- `@patch`デコレータと`Mock`オブジェクト作成が重複
- テストデータの準備処理も類似

**解決策:**
```python
# tests/conftest.py に共通フィクスチャを追加
@pytest.fixture
def mock_mermaid_block():
    """Mermaidブロックのモックを返すフィクスチャ"""
    mock_block = Mock(spec=MermaidBlock)
    mock_block.get_filename.return_value = "test_0_abc123.png"
    mock_block.generate_image.return_value = True
    return mock_block

@pytest.fixture
def mock_processor_with_command(basic_config):
    """コマンド利用可能なプロセッサのモックフィクスチャ"""
    with patch("mkdocs_mermaid_to_image.image_generator.is_command_available") as mock_cmd:
        mock_cmd.return_value = True
        processor = MermaidProcessor(basic_config)
        yield processor, mock_cmd

# テストメソッドの簡略化
def test_process_page_with_blocks(mock_processor_with_command, mock_mermaid_block):
    processor, _ = mock_processor_with_command

    processor.markdown_processor.extract_mermaid_blocks = Mock(return_value=[mock_mermaid_block])
    processor.markdown_processor.replace_blocks_with_images = Mock(return_value="![Mermaid](test.png)")

    result_content, result_paths = processor.process_page("test.md", "```mermaid\ngraph TD\n    A --> B\n```", "/output")

    assert result_content == "![Mermaid](test.png)"
    assert len(result_paths) == 1
```

**実装手順:**
1. 共通フィクスチャの作成
2. テストメソッドの簡略化
3. テスト実行で同等の検証確認
4. 各テストファイル間の一貫性確認

**期待効果:**
- テストコードの重複削減
- テストケース追加時の作業量削減
- フィクスチャの再利用性向上

## 実装スケジュール

### フェーズ1（Week 1）: 高優先度対応
- **Day 1-2**: 例外クラスのリファクタリング
- **Day 3-4**: テスト設定検証の共通化
- **Day 5**: テストケース実行、品質チェック

### フェーズ2（Week 2）: 中優先度対応
- **Day 1-2**: ファイルクリーンアップ処理の統一
- **Day 3-4**: テストモック設定の共通化
- **Day 5**: 統合テスト、パフォーマンス確認

### フェーズ3（Week 3）: 検証・改善
- **Day 1-2**: 全体テストの実行
- **Day 3-4**: ドキュメント更新
- **Day 5**: コードレビューと最終調整

## リスク分析と対策

### 高リスク
1. **例外クラスの変更**
   - **リスク**: 既存コードの例外処理が破綻
   - **対策**: 型チェックとAPIテストの徹底実行
   - **フォールバック**: 段階的移行（deprecation warning）

2. **テストロジックの変更**
   - **リスク**: テストケースの網羅性低下
   - **対策**: カバレッジレポートの比較
   - **フォールバック**: 元のテストケースの並行実行

### 中リスク
3. **ファイル操作の変更**
   - **リスク**: リソースリークやファイルロック
   - **対策**: リソース管理の単体テスト追加
   - **フォールバック**: 元の実装をフォールバック関数として維持

## 期待される効果

### 定量的効果
- **コード行数削減**: 約320行 → 約200行（約37%削減）
- **テストカバレッジ維持**: 90%以上を維持
- **循環的複雑度削減**: 平均15%削減見込み

### 定性的効果
- **保守性向上**: 共通処理の変更が1箇所で済む
- **可読性向上**: 重複コード削減により核心的ロジックが明確化
- **拡張性向上**: 新機能追加時のコード追加量削減
- **テスタビリティ向上**: 共通化により単体テストが容易

## 品質保証戦略

### テスト戦略
1. **リファクタリング前後の動作同等性確認**
   ```bash
   # 全テスト実行（リファクタリング前）
   make test-cov > before_refactor.log

   # リファクタリング実行

   # 全テスト実行（リファクタリング後）
   make test-cov > after_refactor.log

   # 結果比較
   diff before_refactor.log after_refactor.log
   ```

2. **型安全性の確認**
   ```bash
   make typecheck  # mypy strict mode
   ```

3. **統合テストの実行**
   ```bash
   make test-integration  # MkDocsとのE2Eテスト
   ```

### コード品質確認
```bash
# すべての品質チェックを順次実行
make check

# 個別チェック
make lint       # ruff check
make format     # ruff format
make security   # bandit scan
make audit      # 依存脆弱性チェック
```

### パフォーマンス確認
```bash
# 画像生成処理のベンチマーク実行
python -m pytest tests/performance/ -v
```

この計画に基づき、段階的かつ安全にリファクタリングを実行し、コード品質の大幅な向上を図ります。
