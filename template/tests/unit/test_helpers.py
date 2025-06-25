"""Unit tests for utility helper functions."""

import json
from pathlib import Path
from typing import Any

import pytest
from template_package.utils.helpers import (
    chunk_list,
    flatten_dict,
    load_json_file,
    save_json_file,
)


class TestLoadJsonFile:
    """Test load_json_file function."""

    def test_正常系_有効なJSONファイルを読み込める(
        self,
        temp_dir: Path,
    ) -> None:
        """有効なJSONファイルを正常に読み込めることを確認。"""
        test_data = {"name": "test", "value": 123, "nested": {"key": "value"}}
        json_file = temp_dir / "test.json"
        json_file.write_text(json.dumps(test_data), encoding="utf-8")

        result = load_json_file(json_file)

        assert result == test_data
        assert isinstance(result, dict)

    def test_正常系_Path型とstr型の両方を受け付ける(
        self,
        temp_dir: Path,
    ) -> None:
        """Path型とstr型の両方のパスを受け付けることを確認。"""
        test_data = {"test": "data"}
        json_file = temp_dir / "test.json"
        json_file.write_text(json.dumps(test_data), encoding="utf-8")

        # Path型での読み込み
        result_path = load_json_file(json_file)
        # str型での読み込み
        result_str = load_json_file(str(json_file))

        assert result_path == test_data
        assert result_str == test_data

    def test_異常系_ファイルが存在しない場合FileNotFoundError(
        self,
        temp_dir: Path,
    ) -> None:
        """存在しないファイルを読み込もうとするとFileNotFoundErrorが発生。"""
        non_existent_file = temp_dir / "non_existent.json"

        with pytest.raises(FileNotFoundError, match="File not found"):
            load_json_file(non_existent_file)

    def test_異常系_無効なJSONでValueError(
        self,
        temp_dir: Path,
    ) -> None:
        """無効なJSONファイルを読み込もうとするとValueErrorが発生。"""
        invalid_json_file = temp_dir / "invalid.json"
        invalid_json_file.write_text("{invalid json}", encoding="utf-8")

        with pytest.raises(ValueError, match="Invalid JSON"):
            load_json_file(invalid_json_file)

    def test_異常系_JSONが辞書でない場合ValueError(
        self,
        temp_dir: Path,
    ) -> None:
        """JSONが辞書でない場合、ValueErrorが発生。"""
        json_file = temp_dir / "array.json"
        json_file.write_text("[1, 2, 3]", encoding="utf-8")

        with pytest.raises(ValueError, match="Expected JSON object.*got list"):
            load_json_file(json_file)

    def test_エッジケース_空の辞書を読み込める(
        self,
        temp_dir: Path,
    ) -> None:
        """空の辞書を含むJSONファイルを読み込めることを確認。"""
        json_file = temp_dir / "empty.json"
        json_file.write_text("{}", encoding="utf-8")

        result = load_json_file(json_file)

        assert result == {}
        assert isinstance(result, dict)

    def test_正常系_日本語を含むJSONを読み込める(
        self,
        temp_dir: Path,
    ) -> None:
        """日本語を含むJSONファイルを正常に読み込めることを確認。"""
        test_data = {"名前": "テスト", "説明": "これはテストです"}
        json_file = temp_dir / "japanese.json"
        json_file.write_text(
            json.dumps(test_data, ensure_ascii=False), encoding="utf-8"
        )

        result = load_json_file(json_file)

        assert result == test_data


class TestSaveJsonFile:
    """Test save_json_file function."""

    def test_正常系_JSONファイルを保存できる(
        self,
        temp_dir: Path,
    ) -> None:
        """辞書データをJSONファイルとして保存できることを確認。"""
        test_data = {"name": "test", "value": 123, "nested": {"key": "value"}}
        json_file = temp_dir / "output.json"

        save_json_file(test_data, json_file)

        assert json_file.exists()
        loaded_data = json.loads(json_file.read_text(encoding="utf-8"))
        assert loaded_data == test_data

    def test_正常系_親ディレクトリが自動作成される(
        self,
        temp_dir: Path,
    ) -> None:
        """親ディレクトリが存在しない場合、自動的に作成されることを確認。"""
        test_data = {"test": "data"}
        nested_path = temp_dir / "nested" / "dir" / "output.json"

        save_json_file(test_data, nested_path)

        assert nested_path.exists()
        assert nested_path.parent.exists()

    def test_正常系_カスタムインデントで保存できる(
        self,
        temp_dir: Path,
    ) -> None:
        """カスタムインデントレベルでJSONを保存できることを確認。"""
        test_data = {"test": "data", "nested": {"key": "value"}}
        json_file = temp_dir / "indented.json"

        save_json_file(test_data, json_file, indent=4)

        content = json_file.read_text(encoding="utf-8")
        assert "    " in content  # 4スペースのインデント

    def test_正常系_日本語を含むデータを保存できる(
        self,
        temp_dir: Path,
    ) -> None:
        """日本語を含むデータを正しく保存できることを確認。"""
        test_data = {"名前": "テスト", "説明": "これはテストです"}
        json_file = temp_dir / "japanese.json"

        save_json_file(test_data, json_file, ensure_ascii=False)

        content = json_file.read_text(encoding="utf-8")
        assert "名前" in content
        assert "\\u" not in content  # Unicodeエスケープされていない

    def test_正常系_既存ファイルを上書きできる(
        self,
        temp_dir: Path,
    ) -> None:
        """既存のファイルを上書きできることを確認。"""
        json_file = temp_dir / "existing.json"
        json_file.write_text('{"old": "data"}', encoding="utf-8")
        new_data = {"new": "data"}

        save_json_file(new_data, json_file)

        loaded_data = json.loads(json_file.read_text(encoding="utf-8"))
        assert loaded_data == new_data


class TestChunkList:
    """Test chunk_list function."""

    def test_正常系_リストを指定サイズに分割できる(self) -> None:
        """リストを指定サイズのチャンクに分割できることを確認。"""
        items = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]

        chunks = chunk_list(items, 3)

        assert chunks == [[1, 2, 3], [4, 5, 6], [7, 8, 9], [10]]

    def test_正常系_ちょうど割り切れるサイズで分割できる(self) -> None:
        """リストがチャンクサイズで割り切れる場合の動作を確認。"""
        items = [1, 2, 3, 4, 5, 6]

        chunks = chunk_list(items, 2)

        assert chunks == [[1, 2], [3, 4], [5, 6]]

    def test_正常系_チャンクサイズがリストより大きい場合(self) -> None:
        """チャンクサイズがリストサイズより大きい場合の動作を確認。"""
        items = [1, 2, 3]

        chunks = chunk_list(items, 10)

        assert chunks == [[1, 2, 3]]

    def test_正常系_空のリストを処理できる(self) -> None:
        """空のリストを処理できることを確認。"""
        items: list[int] = []

        chunks = chunk_list(items, 5)

        assert chunks == []

    def test_正常系_異なる型のリストを処理できる(self) -> None:
        """文字列リストなど異なる型でも動作することを確認。"""
        items = ["a", "b", "c", "d", "e"]

        chunks = chunk_list(items, 2)

        assert chunks == [["a", "b"], ["c", "d"], ["e"]]

    def test_異常系_チャンクサイズが0以下でValueError(self) -> None:
        """チャンクサイズが0以下の場合、ValueErrorが発生。"""
        items = [1, 2, 3]

        with pytest.raises(ValueError, match="chunk_size must be positive"):
            chunk_list(items, 0)

        with pytest.raises(ValueError, match="chunk_size must be positive"):
            chunk_list(items, -1)

    @pytest.mark.parametrize(
        "input_size,chunk_size,expected_chunks",
        [
            (10, 1, 10),  # 1要素ずつ
            (10, 5, 2),  # 半分ずつ
            (10, 10, 1),  # 全体で1チャンク
            (10, 15, 1),  # チャンクサイズが大きい
            (0, 5, 0),  # 空リスト
        ],
    )
    def test_パラメトライズ_様々なサイズで正しくチャンク数が計算される(
        self,
        input_size: int,
        chunk_size: int,
        expected_chunks: int,
    ) -> None:
        """様々なサイズの組み合わせで正しいチャンク数になることを確認。"""
        items = list(range(input_size))

        chunks = chunk_list(items, chunk_size)

        assert len(chunks) == expected_chunks


class TestFlattenDict:
    """Test flatten_dict function."""

    def test_正常系_ネストした辞書をフラット化できる(self) -> None:
        """ネストした辞書を正しくフラット化できることを確認。"""
        nested = {
            "a": 1,
            "b": {
                "c": 2,
                "d": {
                    "e": 3,
                },
            },
        }

        flattened = flatten_dict(nested)

        assert flattened == {
            "a": 1,
            "b.c": 2,
            "b.d.e": 3,
        }

    def test_正常系_カスタムセパレータを使用できる(self) -> None:
        """カスタムセパレータでフラット化できることを確認。"""
        nested = {
            "a": {
                "b": 1,
                "c": 2,
            },
        }

        flattened = flatten_dict(nested, separator="/")

        assert flattened == {
            "a/b": 1,
            "a/c": 2,
        }

    def test_正常系_プレフィックスを追加できる(self) -> None:
        """プレフィックスを追加してフラット化できることを確認。"""
        nested = {
            "a": 1,
            "b": {
                "c": 2,
            },
        }

        flattened = flatten_dict(nested, prefix="root")

        assert flattened == {
            "root.a": 1,
            "root.b.c": 2,
        }

    def test_正常系_空の辞書を処理できる(self) -> None:
        """空の辞書を処理できることを確認。"""
        flattened = flatten_dict({})

        assert flattened == {}

    def test_正常系_フラットな辞書はそのまま返される(self) -> None:
        """既にフラットな辞書はそのまま返されることを確認。"""
        flat_dict = {"a": 1, "b": 2, "c": 3}

        flattened = flatten_dict(flat_dict)

        assert flattened == flat_dict

    def test_正常系_混在した型を含む辞書を処理できる(self) -> None:
        """様々な型の値を含む辞書を処理できることを確認。"""
        nested: dict[str, Any] = {
            "string": "value",
            "number": 123,
            "float": 3.14,
            "bool": True,
            "none": None,
            "list": [1, 2, 3],
            "nested": {
                "key": "value",
            },
        }

        flattened = flatten_dict(nested)

        assert flattened == {
            "string": "value",
            "number": 123,
            "float": 3.14,
            "bool": True,
            "none": None,
            "list": [1, 2, 3],
            "nested.key": "value",
        }

    def test_正常系_深いネストを処理できる(self) -> None:
        """深くネストした辞書を処理できることを確認。"""
        nested = {
            "level1": {
                "level2": {
                    "level3": {
                        "level4": {
                            "value": "deep",
                        },
                    },
                },
            },
        }

        flattened = flatten_dict(nested)

        assert flattened == {
            "level1.level2.level3.level4.value": "deep",
        }

    def test_正常系_同じキーが異なるレベルに存在する場合(self) -> None:
        """同じキー名が異なるネストレベルに存在する場合の動作を確認。"""
        nested = {
            "data": 1,
            "group": {
                "data": 2,
                "subgroup": {
                    "data": 3,
                },
            },
        }

        flattened = flatten_dict(nested)

        assert flattened == {
            "data": 1,
            "group.data": 2,
            "group.subgroup.data": 3,
        }
