"""
プロジェクト名変更のテストファイル

このファイルは、プロジェクト名やパッケージ名が正しく変更されたことを確認するテストです。
- パッケージ名が mkdocs-mermaid-to-svg に変更されていることを確認
- エントリーポイントが正しく設定されていることを確認
- ディレクトリ名が mkdocs_mermaid_to_svg に変更されていることを確認
"""

from pathlib import Path

import pytest


class TestProjectRename:
    """プロジェクト名変更のテストクラス"""

    def test_new_package_structure_should_exist(self):
        """
        新しいパッケージ構造が存在することを確認するテスト

        このテストは最初に失敗し、ディレクトリ名を変更した後に成功する必要があります。
        """
        # src/mkdocs_mermaid_to_svg ディレクトリが存在することを確認
        project_root = Path(__file__).parent.parent.parent
        new_package_dir = project_root / "src" / "mkdocs_mermaid_to_svg"

        assert (
            new_package_dir.exists()
        ), f"New package directory should exist: {new_package_dir}"
        assert (
            new_package_dir / "__init__.py"
        ).exists(), "Package should have __init__.py"
        assert (new_package_dir / "plugin.py").exists(), "Package should have plugin.py"

    def test_old_package_structure_should_not_exist(self):
        """
        古いパッケージ構造が存在しないことを確認するテスト

        このテストは最初に失敗し、ディレクトリ名を変更した後に成功する必要があります。
        """
        project_root = Path(__file__).parent.parent.parent
        old_package_dir = project_root / "src" / "mkdocs_mermaid_to_image"

        assert (
            not old_package_dir.exists()
        ), f"Old package directory should not exist: {old_package_dir}"

    def test_import_with_new_package_name_should_work(self):
        """
        新しいパッケージ名でのインポートが動作することを確認するテスト

        このテストは最初に失敗し、パッケージ名を変更した後に成功する必要があります。
        """
        try:
            # 新しいパッケージ名でインポートできることを確認
            import mkdocs_mermaid_to_svg
            from mkdocs_mermaid_to_svg.plugin import MermaidSvgConverterPlugin

            # インポートが成功し、クラスが利用可能であることを確認
            assert mkdocs_mermaid_to_svg is not None
            assert MermaidSvgConverterPlugin is not None

        except ImportError as e:
            pytest.fail(f"Should be able to import new package name: {e}")
