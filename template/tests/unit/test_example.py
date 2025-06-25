"""Unit tests for example module."""

from typing import Any

import pytest
from template_package.core.example import (
    ExampleClass,
    ExampleConfig,
    process_data,
)


class TestExampleConfig:
    """Test ExampleConfig class."""

    def test_正常系_デフォルト値で初期化される(self) -> None:
        """デフォルト値でConfigが作成されることを確認。"""
        config = ExampleConfig(name="test")

        assert config.name == "test"
        assert config.max_items == 100
        assert config.enable_validation is True

    def test_正常系_カスタム値で初期化される(self) -> None:
        """カスタム値でConfigが作成されることを確認。"""
        config = ExampleConfig(
            name="custom",
            max_items=50,
            enable_validation=False,
        )

        assert config.name == "custom"
        assert config.max_items == 50
        assert config.enable_validation is False

    def test_異常系_max_itemsが負の値でValueError(self) -> None:
        """max_itemsが負の値の場合、ValueErrorが発生することを確認。"""
        with pytest.raises(ValueError, match="max_items must be positive"):
            ExampleConfig(name="test", max_items=-1)

    def test_異常系_max_itemsがゼロでValueError(self) -> None:
        """max_itemsが0の場合、ValueErrorが発生することを確認。"""
        with pytest.raises(ValueError, match="max_items must be positive"):
            ExampleConfig(name="test", max_items=0)


class TestExampleClass:
    """Test ExampleClass."""

    def test_正常系_初期化時は空のリスト(
        self,
        example_instance: ExampleClass,
    ) -> None:
        """初期化時にデータが空であることを確認。"""
        assert len(example_instance) == 0
        assert example_instance.get_items() == []

    def test_正常系_アイテムを追加できる(
        self,
        example_instance: ExampleClass,
    ) -> None:
        """アイテムを正常に追加できることを確認。"""
        item = {"id": 1, "name": "test_item", "value": 42}
        example_instance.add_item(item)

        assert len(example_instance) == 1
        assert example_instance.get_items() == [item]

    def test_正常系_複数のアイテムを追加できる(
        self,
        example_instance: ExampleClass,
        sample_data: list[dict[str, Any]],
    ) -> None:
        """複数のアイテムを追加できることを確認。"""
        for item in sample_data:
            example_instance.add_item(item)

        assert len(example_instance) == len(sample_data)
        assert example_instance.get_items() == sample_data

    def test_正常系_フィルタリングが機能する(
        self,
        example_instance: ExampleClass,
        sample_data: list[dict[str, Any]],
    ) -> None:
        """フィルタリングが正しく機能することを確認。"""
        for item in sample_data:
            example_instance.add_item(item)

        filtered = example_instance.get_items(
            filter_key="value",
            filter_value=200,
        )

        assert len(filtered) == 1
        assert filtered[0]["id"] == 2

    def test_異常系_最大数を超えるとValueError(
        self,
        example_config: ExampleConfig,
    ) -> None:
        """最大数を超えてアイテムを追加しようとするとエラーになることを確認。"""
        example_config.max_items = 2
        instance = ExampleClass(example_config)

        instance.add_item({"id": 1, "name": "item1", "value": 10})
        instance.add_item({"id": 2, "name": "item2", "value": 20})

        with pytest.raises(ValueError, match="max_items limit"):
            instance.add_item({"id": 3, "name": "item3", "value": 30})

    def test_異常系_空の辞書でValueError(
        self,
        example_instance: ExampleClass,
    ) -> None:
        """空の辞書を追加しようとするとエラーになることを確認。"""
        with pytest.raises(ValueError, match="Missing required fields"):
            example_instance.add_item({})

    def test_異常系_辞書以外を追加しようとするとTypeError(
        self,
        example_instance: ExampleClass,
    ) -> None:
        """辞書以外を追加しようとするとエラーになることを確認。"""
        # mypyによる型チェックがあるため、実行時には型エラーとして扱われる
        # ここでは実際に文字列が渡された場合の動作をテスト
        with pytest.raises((TypeError, AttributeError)):
            example_instance.add_item("not a dict")  # type: ignore

    def test_正常系_バリデーション無効時は空の辞書も追加できる(
        self,
        example_config: ExampleConfig,
    ) -> None:
        """バリデーション無効時は制約がないことを確認。"""
        example_config.enable_validation = False
        instance = ExampleClass(example_config)

        # バリデーション無効時は空の辞書も追加可能
        instance.add_item({})
        assert len(instance) == 1

    def test_正常系_repr表現が正しい(
        self,
        example_instance: ExampleClass,
        sample_data: list[dict[str, Any]],
    ) -> None:
        """repr表現が期待通りであることを確認。"""
        for item in sample_data[:2]:
            example_instance.add_item(item)

        repr_str = repr(example_instance)
        assert "ExampleClass" in repr_str
        assert "name='test'" in repr_str
        assert "items=2/10" in repr_str


class MockProcessor:
    """Mock implementation of DataProcessor protocol."""

    def process(self, data: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Simply return the data with 'processed' flag."""
        return [{**item, "processed": True} for item in data]


class TestProcessData:
    """Test process_data function."""

    def test_正常系_データが処理される(
        self,
        sample_data: list[dict[str, Any]],
    ) -> None:
        """データが正しく処理されることを確認。"""
        processor = MockProcessor()
        result = process_data(sample_data, processor)

        assert len(result) == len(sample_data)
        assert all(item["processed"] is True for item in result)

    def test_異常系_バリデーション有効で空データはエラー(self) -> None:
        """バリデーション有効時、空データでエラーになることを確認。"""
        processor = MockProcessor()

        with pytest.raises(ValueError, match="Data cannot be empty"):
            process_data([], processor, validate=True)

    def test_正常系_バリデーション無効で空データも処理できる(self) -> None:
        """バリデーション無効時、空データも処理できることを確認。"""
        processor = MockProcessor()
        result = process_data([], processor, validate=False)

        assert result == []

    @pytest.mark.parametrize(
        "input_data,expected_length",
        [
            ([{"id": 1}], 1),
            ([{"id": 1}, {"id": 2}], 2),
            ([{"id": i} for i in range(10)], 10),
        ],
    )
    def test_パラメトライズ_様々なサイズのデータを処理できる(
        self,
        input_data: list[dict[str, Any]],
        expected_length: int,
    ) -> None:
        """様々なサイズのデータを処理できることを確認。"""
        processor = MockProcessor()
        result = process_data(input_data, processor)

        assert len(result) == expected_length
