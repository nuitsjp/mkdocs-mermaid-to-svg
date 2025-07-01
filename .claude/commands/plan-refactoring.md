# リファクタリング計画の作成

`similarity-py .`でコードの意味的な類似が得られます。あなたはこれを実行し、ソースコードの重複を検知して、リファクタリング計画を立てます。細かいオプションは similarity-py -h で確認してください。

以下の観点で分析してください：
1. 最も影響度の高い重複コード（Priority順）
2. 共通化可能なパターンの特定
3. 段階的なリファクタリング手順
4. リスクと対策
5. テスト戦略

## 基本原則

1. **客観的な分析** - ASTベースの構造解析による正確な類似性検出
2. **影響度の評価** - コードサイズと類似度を考慮した優先順位付け
3. **段階的なアプローチ** - 小さく安全なリファクタリングステップに分解
4. **テストドリブン** - 安全性を保証するテスト戦略の策定

## 実行手順

### 2. 類似性検出の実行

**基本的なスキャン**
```bash
# プロジェクト全体をスキャン
similarity-py .

# 特定のディレクトリをスキャン
similarity-py src/

# 閾値を調整して検出精度を変更
similarity-py . --threshold 0.8

# コードを表示して詳細分析
similarity-py . --print
```

**詳細オプション**
```bash
# クロスファイル比較を有効化
similarity-py . --cross-file --threshold 0.75

# 最小行数を調整
similarity-py . --min-lines 5

# テストファイルも含めて分析
similarity-py . --extensions py,test.py
```

### 4. リファクタリング戦略の立案

**優先順位の決定**
- Priority値（行数 × 類似度）の高いものから対処
- ビジネスロジックの重複を最優先
- ユーティリティ関数の共通化

**共通化パターンの分類**
- **関数の抽出**: 同一処理の共通関数化
- **クラスの統合**: 類似クラスの統合またはベースクラス化
- **設定の外部化**: ハードコードされた値の設定ファイル化
- **デザインパターンの適用**: Strategy, Template Methodパターンなど

### 5. 実行例とワークフロー

**Step 1: 全体分析**
```bash
# プロジェクト全体の重複を検出
similarity-py . --threshold 0.8 --min-lines 10 --cross-file
```

**Step 2: 高優先度の詳細分析**
```bash
# 重複コードを実際に表示
similarity-py . --threshold 0.85 --print
```

**Step 3: 特定エリアの深掘り**
```bash
# 特定のモジュールを詳細分析
similarity-py src/core/ --threshold 0.7 --print
similarity-py src/utils/ --threshold 0.75 --print
```

**Step 4: AI分析とプラン作成**
- 検出結果をAIに分析依頼
- リファクタリング計画の策定
- 優先順位付けとリスク評価

### 6. リファクタリング実行時の安全策

**テスト駆動リファクタリング**
```bash
# リファクタリング前にテストを実行
make test-cov

# 各リファクタリングステップ後にテスト
make test              # 動作確認
make check-all         # 型安全性確認, コード品質確認
```

**段階的コミット**
```bash
# 小さな変更ごとにコミット
git add .
git commit -m "refactor: extract common validation logic"

# 大きなリファクタリングは複数コミットに分割
git commit -m "refactor: step 1/3 - extract helper functions"
```

### 7. 分析結果の活用例

**重複検出結果の例**
```
Duplicates in src/utils.py:
────────────────────────────────────────────────────────────
  src/utils.py:10 | L10-25 validate_input
  src/helpers.py:15 | L15-30 check_data_format
  Similarity: 89.50%, Priority: 14.3 (lines: 16)
```

**AI分析後のアクション**
1. **即座に対処**: Priority > 10の重複
2. **計画的対処**: Priority 5-10の重複
3. **長期対処**: Priority < 5の重複

## 実行時の注意事項

1. **パフォーマンス**: 大規模プロジェクトでは時間がかかる場合があります
2. **false positive**: 構造的に似ているが意味が異なるコードに注意
3. **テストコード**: テスト間の重複は許容される場合があります
4. **段階的実行**: 一度にすべてを修正せず、小さくテスト可能な単位で進める

## 継続的改善

```bash
# 定期的な重複チェック（CI/CDに組み込み可能）
similarity-py . --threshold 0.9 > similarity-report.txt

# 進捗確認（リファクタリング前後の比較）
similarity-py . --threshold 0.8 | grep "Priority:" | wc -l
```

このコマンドを使用することで、データ駆動型の効果的なリファクタリング計画を立てることができます。
