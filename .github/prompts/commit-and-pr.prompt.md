# 変更のコミットとPR作成

現在の変更をコミットし、適切なブランチを作成してプルリクエストを作成します。CLAUDE.mdの「GitHub操作」セクションの規約に従います。

## 実行手順

### 1. 変更内容の確認
```bash
git status              # 変更ファイルの確認
git diff                # 変更内容の確認
git log --oneline -10   # 最近のコミット履歴を確認
```

### 2. コミットメッセージの作成
CLAUDE.mdで定義されているフォーマットに従います：
```
<変更の種類>: <変更内容の要約>

詳細な説明（必要に応じて）

🤖 Generated with [Claude Code](https://claude.ai/code)

Co-Authored-By: Claude <noreply@anthropic.com>
```

### 3. ブランチ名の命名規則
変更の種類に応じて適切なプレフィックスを使用：
- `feature/` - 機能追加
- `fix/` - バグ修正
- `refactor/` - リファクタリング
- `docs/` - ドキュメント更新
- `test/` - テスト追加・修正

### 4. ラベルの命名規則
PRに付けるラベル：
- `enhancement` - 機能追加
- `bug` - バグ修正
- `refactor` - リファクタリング
- `documentation` - ドキュメント
- `test` - テスト

### 5. 実行ステップ

1. **変更内容の分析**
   - git statusとgit diffで変更を確認
   - 変更の種類を判断（feature/fix/refactor/docs/test）

2. **ブランチの作成**
   ```bash
   git checkout -b <branch-type>/<descriptive-name>
   ```

3. **ステージングとコミット**
   ```bash
   git add <files>
   git commit -m "$(cat <<'EOF'
   <type>: <summary>

   <detailed description if needed>

   🤖 Generated with [Claude Code](https://claude.ai/code)

   Co-Authored-By: Claude <noreply@anthropic.com>
   EOF
   )"
   ```

4. **リモートへのプッシュ**
   ```bash
   git push -u origin <branch-name>
   ```

5. **PRの作成**
   ```bash
   make pr TITLE="<PR title>" BODY="<PR description>" LABEL="<label>"
   # または
   gh pr create --title "<title>" --body "$(cat <<'EOF'
   ## Summary
   - <変更点1>
   - <変更点2>

   ## Test plan
   - [ ] make check-allが成功することを確認
   - [ ] 関連するテストが追加されていることを確認
   - [ ] ドキュメントが更新されていることを確認

   🤖 Generated with [Claude Code](https://claude.ai/code)
   EOF
   )"
   ```

## 注意事項

1. **コミット前の確認**
   - `make check-all`が成功することを確認
   - 不要なファイルが含まれていないことを確認
   - センシティブな情報が含まれていないことを確認

2. **コミットメッセージ**
   - 変更内容を明確に記述
   - なぜ変更したかを説明（whatよりwhy）
   - 日本語での記述も可

3. **PR作成時**
   - テストプランを必ず含める
   - レビュアーが理解しやすい説明を心がける
   - 関連するIssueがあればリンクする

## 使用例

```bash
# 機能追加のPR
make pr TITLE="feat: ユーザー認証機能を追加" BODY="JWTトークンベースの認証システムを実装しました" LABEL="enhancement"

# バグ修正のPR
make pr TITLE="fix: ログイン時の500エラーを修正" BODY="認証トークンの検証ロジックを修正しました" LABEL="bug"

# ドキュメント更新のPR
make pr TITLE="docs: APIドキュメントを更新" BODY="新しいエンドポイントの説明を追加しました" LABEL="documentation"
```

このコマンドにより、規約に従った一貫性のあるコミットとPR作成が可能になります。
