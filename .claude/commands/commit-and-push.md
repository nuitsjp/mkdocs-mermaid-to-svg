---
mode: agent
description: '変更のコミットとプッシュ'
---

# 変更のコミットとプッシュ

現在の変更をコミットし、リモートリポジトリにプッシュします。CLAUDE.mdの「GitHub操作」セクションの規約に従います。

この手順により、規約に従った一貫性のあるコミットとプッシュが可能になります。

## 実行手順

### 0. 変更後品質の確認
```bash
make check-all
```

必要に応じて修正し、再度確認を実施する。

### 1. 変更内容の確認
```bash
git status && git diff && git log --oneline -10
```

- git statusとgit diffで変更を確認
- 不要なファイルが含まれていないことを確認
- センシティブな情報が含まれていないことを確認
- 変更の種類を判断（feature/fix/refactor/docs/test）

### 2. コミットメッセージの作成
CLAUDE.mdで定義されているフォーマットに従います：
```
<変更の種類>: <変更内容の要約>

詳細な説明（必要に応じて）

🤖 Generated with [GitHub Copilot](https://docs.github.com/ja/copilot)
```

- 変更内容を明確に記述
- なぜ変更したかを説明（whatよりwhy）
- 日本語で記述
