# t-wada流TDDによるテスト作成

CLAUDE.mdの「テスト戦略」セクションで定義されているt-wada流のテスト駆動開発（TDD）に従って、高品質なテストを作成します。

## TDDの基本サイクル

1. 🔴 **Red**: 失敗するテストを書く
2. 🟢 **Green**: テストを通す最小限の実装
3. 🔵 **Refactor**: リファクタリング

## 実行手順

### 1. TODOリストの作成
実装したい機能をリストアップし、最小単位に分解します：
```
[ ] 基本的な機能の動作確認
[ ] エッジケースの処理
[ ] エラーハンドリング
[ ] パフォーマンスが重要な場合はベンチマーク
```

### 2. テストファイルの配置
```
tests/
├── unit/            # 単体テスト
├── property/        # プロパティベーステスト（Hypothesis使用）
├── integration/     # 統合テスト
└── conftest.py      # pytestフィクスチャ
```

### 3. テストの命名規則
日本語で意図を明確に表現します：
```python
def test_正常系_有効なデータで処理成功():
    """chunk_listが正しくチャンク化できることを確認。"""

def test_異常系_不正なサイズでValueError():
    """チャンクサイズが0以下の場合、ValueErrorが発生することを確認。"""

def test_エッジケース_空リストで空結果():
    """空のリストをチャンク化すると空の結果が返されることを確認。"""
```

### 4. templateディレクトリの参考例

**単体テスト** (@template/tests/unit/test_example.py)
- 関数・クラスの基本動作
- 正常系・異常系・エッジケース
- パラメトライズテストの活用

**プロパティベーステスト** (@template/tests/property/test_helpers_property.py)
- Hypothesisによる自動テストケース生成
- 不変条件の検証
- エッジケースの自動発見

**統合テスト** (@template/tests/integration/test_example.py)
- コンポーネント間の連携
- ファイルI/Oやデータ処理パイプライン
- エラーのカスケード処理

## 三角測量の実践例

```python
# Step 1: 最初のテスト（仮実装で通す）
def test_add_正の数():
    assert add(2, 3) == 5

def add(a, b):
    return 5  # 仮実装

# Step 2: 2つ目のテスト（一般化を促す）
def test_add_別の正の数():
    assert add(1, 4) == 5
    assert add(10, 20) == 30  # これで仮実装では通らない

def add(a, b):
    return a + b  # 一般化

# Step 3: エッジケースを追加
def test_add_負の数():
    assert add(-1, -2) == -3
    assert add(-5, 3) == -2
```

## TDD実践時の注意点

1. **テストは1つずつ追加** - 一度に複数のテストを書かない
2. **小さく頻繁にコミット** - Red→Green、Refactor完了でコミット
3. **テストの粒度** - 1つのテストで1つの振る舞いをテスト
4. **リファクタリングの判断** - 重複コード、可読性、設計原則
5. **テストファーストの徹底** - 必ず失敗するテストから書く

## 実行コマンド

```bash
# テストの実行
make test              # 全テスト実行
make test-unit         # 単体テストのみ
make test-property     # プロパティベーステストのみ
make test-cov          # カバレッジ付きテスト

# 特定のテストを実行
uv run pytest tests/unit/test_example.py::TestExampleClass::test_正常系_初期化時は空のリスト -v
```

このコマンドを使用することで、堅牢で保守性の高いテストスイートを構築できます。
