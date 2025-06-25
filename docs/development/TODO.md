# MkDocs Mermaid to Image Plugin - TODO

## 📋 プロジェクト概要

### 🎯 目的
MkDocs環境でMermaidダイアグラムを静的画像として事前レンダリングし、PDF出力に対応させるプラグインの開発・公開。

### 🏗️ 開発背景
- **課題**: 既存のmermaid2プラグインは JavaScript依存でPDF出力時に画像が表示されない
- **解決**: Mermaid CLIを使用した静的画像生成による事前レンダリング
- **利点**: PDFに画像が正常に含まれ、ランタイムJavaScript依存を排除

### 📊 現在の状況
- **開発**: 完了（実験環境で動作確認済み）
- **移行**: 正式リポジトリへの移行完了
- **テスト**: 基本機能テスト済み（3/4通過）
- **ドキュメント**: README・詳細マニュアル完備
- **ライセンス**: MIT（nuitsjp作成者）

## 🚀 Phase 1: 公開準備 (高優先度)

### 📦 PyPI公開
- [ ] **パッケージビルド**
  - [ ] `python -m build` でdist/生成確認
  - [ ] wheel・tar.gz ファイル確認
  - [ ] パッケージメタデータ検証

- [ ] **PyPI テスト公開**
  - [ ] TestPyPIアカウント準備
  - [ ] `twine upload --repository testpypi dist/*`
  - [ ] テストインストール確認

- [ ] **PyPI 本公開**
  - [ ] PyPIアカウント準備・2FA設定
  - [ ] API token生成・保存
  - [ ] `twine upload dist/*` 実行
  - [ ] 公開確認・インストールテスト

### 🔧 品質改善
- [ ] **テスト修正**
  - [ ] Mermaid CLIテストのエラー修正
  - [ ] 4/4テスト全通過確認
  - [ ] テストカバレッジ改善

- [ ] **コード品質**
  - [ ] flake8/black による静的解析
  - [ ] type hints 追加
  - [ ] docstring 改善

### 📚 ドキュメント完善
- [ ] **README 改善**
  - [ ] PyPI badgeの追加
  - [ ] インストール手順の更新
  - [ ] スクリーンショット追加

- [ ] **CHANGELOG 作成**
  - [ ] `CHANGELOG.md` 作成
  - [ ] v1.0.0 リリースノート

## 🛠️ Phase 2: CI/CD構築 (中優先度)

### ⚙️ GitHub Actions
- [ ] **テスト自動化**
  - [ ] `.github/workflows/test.yml` 作成
  - [ ] Python 3.8-3.12 マトリックステスト
  - [ ] Node.js・Mermaid CLI 自動インストール
  - [ ] プルリクエスト時自動テスト

- [ ] **公開自動化**
  - [ ] `.github/workflows/publish.yml` 作成
  - [ ] タグ作成時のPyPI自動公開
  - [ ] GitHub Releases 自動作成

### 🔒 セキュリティ
- [ ] **Secret管理**
  - [ ] PyPI API token の Secrets 設定
  - [ ] Dependabot 有効化
  - [ ] Security advisories 設定

## 📈 Phase 3: 機能拡張 (低優先度)

### 🎨 機能追加
- [ ] **新機能**
  - [ ] SVGフォーマット対応の詳細テスト
  - [ ] カスタムCSS適用機能
  - [ ] バッチ処理の並列化
  - [ ] プログレスバー表示

- [ ] **パフォーマンス**
  - [ ] キャッシュ機能の最適化
  - [ ] 大量ファイル処理の高速化
  - [ ] メモリ使用量の最適化

### 🧪 テスト強化
- [ ] **統合テスト**
  - [ ] 実際のMkDocsプロジェクトでのE2Eテスト
  - [ ] PDF生成の画像品質確認
  - [ ] 各種テーマでの表示確認

- [ ] **エッジケース**
  - [ ] 大量Mermaidブロックのテスト
  - [ ] エラー処理の詳細テスト
  - [ ] 異常な入力に対する堅牢性テスト

## 🌟 Phase 4: コミュニティ構築 (低優先度)

### 📢 プロモーション
- [ ] **発信活動**
  - [ ] ブログ記事・技術記事作成
  - [ ] Twitter/SNS での告知
  - [ ] MkDocsコミュニティでの共有

- [ ] **ドキュメント拡充**
  - [ ] GitHub Pages でのドキュメントサイト
  - [ ] API ドキュメント自動生成
  - [ ] チュートリアル動画作成

### 🤝 コミュニティ
- [ ] **貢献ガイド**
  - [ ] `CONTRIBUTING.md` 作成
  - [ ] Issue/PR テンプレート作成
  - [ ] Code of Conduct 設定

- [ ] **サポート体制**
  - [ ] GitHub Discussions 設定
  - [ ] FAQ ドキュメント作成
  - [ ] バグレポート対応プロセス

## 🎯 Phase 5: 長期メンテナンス (継続)

### 🔄 定期作業
- [ ] **依存関係管理**
  - [ ] 月次依存関係更新確認
  - [ ] セキュリティ脆弱性チェック
  - [ ] Python・Node.js新バージョン対応

- [ ] **機能メンテナンス**
  - [ ] MkDocs新バージョン対応
  - [ ] Mermaid.js新機能対応
  - [ ] ユーザーフィードバック対応

### 📊 品質管理
- [ ] **メトリクス監視**
  - [ ] PyPI ダウンロード数監視
  - [ ] GitHub star/fork 数追跡
  - [ ] Issue/PR 対応時間管理

## ⚡ 緊急度別優先順位

### 🔴 緊急 (今週実施)
1. PyPI テスト公開
2. テスト修正（4/4通過）
3. CHANGELOG.md作成

### 🟡 重要 (今月実施)
1. PyPI本公開
2. GitHub Actions CI設定
3. ドキュメント改善

### 🟢 通常 (来月以降)
1. 機能拡張
2. コミュニティ構築
3. 長期メンテナンス体制

## 📞 次のアクション

### 直近の作業（推奨順序）
1. **パッケージビルド確認** → `python -m build`
2. **TestPyPI公開** → テスト環境での動作確認
3. **テスト修正** → 全テスト通過
4. **PyPI本公開** → 正式リリース
5. **GitHub Actions設定** → 自動化体制構築

### 作業開始コマンド
```bash
# 1. パッケージビルド
cd /path/to/mkdocs-mermaid-to-image
python -m build

# 2. TestPyPI公開
pip install twine
twine upload --repository testpypi dist/*

# 3. テストインストール
pip install --index-url https://test.pypi.org/simple/ mkdocs-mermaid-to-image
```

---

**作成日**: 2024年6月24日
**最終更新**: 2024年6月24日
**作成者**: nuitsjp
**プロジェクト**: mkdocs-mermaid-to-image v1.0.0
