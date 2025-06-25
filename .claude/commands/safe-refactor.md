# 安全なリファクタリング

テストカバレッジを維持しながら、コードを安全にリファクタリングします。template/ディレクトリの実装パターンを参考にして、コードの品質と保守性を向上させます。

## 基本原則

1. **テストが通ることを確認** - リファクタリング前後でテストが通ることを保証
2. **小さなステップで進める** - 一度に大きな変更を加えない
3. **パターンの参照** - template/ディレクトリの実装例を参考にする
4. **コミットの頻度** - 各リファクタリングステップでコミット

## リファクタリングの種類と手順

### 1. 型安全性の向上
**参考**: @template/src/template_package/types.py

```python
# Before: 辞書をそのまま使用
def process_item(item: dict) -> dict:
    return {"id": item["id"], "processed": True}

# After: TypedDictを使用
from typing import TypedDict

class ItemDict(TypedDict):
    id: int
    name: str
    value: int

class ProcessedItemDict(ItemDict):
    processed: bool

def process_item(item: ItemDict) -> ProcessedItemDict:
    return {**item, "processed": True}
```

### 2. エラーハンドリングの改善
**参考**: @template/src/template_package/core/example.py

```python
# Before: 単純なエラー
if not data:
    raise ValueError("Invalid data")

# After: 具体的で実用的なエラー
if not data:
    raise ValueError(
        f"Data cannot be empty when validation is enabled. "
        f"Either provide valid data or set validate=False."
    )
```

### 3. ロギングの追加
**参考**: @template/src/template_package/utils/logging_config.py

```python
from project_name.utils.logging_config import get_logger

logger = get_logger(__name__)

def process_data(data: list) -> list:
    logger.debug(f"Processing {len(data)} items")

    try:
        result = [transform(item) for item in data]
        logger.info(f"Successfully processed {len(result)} items")
        return result
    except Exception as e:
        logger.error(f"Failed to process data: {e}", exc_info=True)
        raise
```

### 4. テストの追加・改善
**参考**: @template/tests/

- 単体テスト: 正常系・異常系・エッジケース
- プロパティベーステスト: Hypothesisを使用した自動テスト
- 統合テスト: コンポーネント間の連携

### 5. パフォーマンスの最適化
**参考**: @template/src/template_package/utils/profiling.py

```python
from project_name.utils.profiling import profile, timeit

@timeit
def optimized_function(data: list) -> list:
    # リスト内包表記を使用
    return [item * 2 for item in data if item > 0]

@profile
def heavy_computation():
    # プロファイリング対象の処理
    pass
```

## 実行ステップ

1. **現状の確認**
   ```bash
   make test              # テストが通ることを確認
   make test-cov          # カバレッジを記録
   ```

2. **リファクタリング対象の特定**
   - 複雑度の高い関数
   - 重複コード
   - 型安全性が低い箇所
   - エラーハンドリングが不十分な箇所

3. **段階的なリファクタリング**
   - 一つの改善点に集中
   - テストを実行して動作確認
   - コミット（リファクタリング内容を明記）

4. **品質チェック**
   ```bash
   make check-all         # 全体的な品質チェック
   make test-cov          # カバレッジが維持されているか確認
   make benchmark         # パフォーマンスの確認（必要に応じて）
   ```

## リファクタリングのチェックリスト

- [ ] 関数は単一責任の原則に従っているか
- [ ] 適切な型ヒントが付けられているか
- [ ] エラーメッセージは具体的で実用的か
- [ ] 適切なロギングが実装されているか
- [ ] テストカバレッジは維持/向上しているか
- [ ] template/の実装パターンに準拠しているか
- [ ] ドキュメント（docstring）は更新されているか

## 注意事項

1. **動作の変更は避ける** - リファクタリングは内部構造の改善であり、外部動作は変えない
2. **テストファースト** - テストがない場合は先にテストを書く
3. **段階的コミット** - 大きな変更は小さなコミットに分割
4. **レビューの準備** - 変更理由を明確に説明できるようにする

このコマンドを使用することで、コードベースを継続的に改善し、長期的な保守性を確保できます。
