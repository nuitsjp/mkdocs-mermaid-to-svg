# 変更のコミットとプッシュ

現在の変更をコミットし、リモートリポジトリにプッシュします。CLAUDE.mdの「GitHub操作」セクションの規約に従います。

## 実行手順

### 1. 変更内容の確認
```bash
git status && git diff && git log --oneline -10
```

### 2. コミットメッセージの作成
CLAUDE.mdで定義されているフォーマットに従います：
```
<変更の種類>: <変更内容の要約>

詳細な説明（必要に応じて）

🤖 Generated with [GitHub Copilot](https://claude.ai/code)
```

### 3. 実行ステップ

1. **変更内容の分析**
   - git statusとgit diffで変更を確認
   - 変更の種類を判断（feature/fix/refactor/docs/test）

2. **ステージングとコミット**
   ```bash
   git add <files>
   git commit -m "$(cat <<'EOF'
   <type>: <summary>

   <detailed description if needed>

   🤖 Generated with [GitHub Copilot](https://claude.ai/code)
   EOF
   )"
   ```

3. **リモートへのプッシュ**
   ```bash
   git push
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

この手順により、規約に従った一貫性のあるコミットとプッシュが可能になります。
