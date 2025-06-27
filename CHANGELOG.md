# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- 最小構成でのプラグイン動作サポート - `plugins: [mermaid-to-image]` のみで動作可能
- 全ての設定項目に適切なデフォルト値を設定

### Fixed
- config.py と plugin.py 間の設定項目名の不一致を修正（mermaid_config_file → mermaid_config）
- オプショナル設定項目のデフォルト値を空文字からNoneに統一し一貫性を向上

### Changed
- 設定の空文字デフォルトをNoneに変更してより一貫した動作を実現
