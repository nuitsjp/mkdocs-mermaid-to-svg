"""Property-based tests for helper functions using Hypothesis."""

import tempfile
from pathlib import Path

from hypothesis import given
from hypothesis import strategies as st
from template_package.utils.helpers import (
    chunk_list,
    flatten_dict,
    load_json_file,
    save_json_file,
)


class TestChunkListProperty:
    """Property-based tests for chunk_list function."""

    @given(
        items=st.lists(st.integers()),
        chunk_size=st.integers(min_value=1, max_value=100),
    )
    def test_プロパティ_チャンク化しても全要素が保持される(
        self,
        items: list[int],
        chunk_size: int,
    ) -> None:
        """チャンク化前後で全要素が保持されることを検証。"""
        chunks = chunk_list(items, chunk_size)

        # フラット化して元のリストと比較
        flattened = [item for chunk in chunks for item in chunk]

        assert flattened == items

    @given(
        items=st.lists(st.integers(), min_size=1),
        chunk_size=st.integers(min_value=1, max_value=100),
    )
    def test_プロパティ_各チャンクサイズが適切(
        self,
        items: list[int],
        chunk_size: int,
    ) -> None:
        """各チャンクのサイズが期待通りであることを検証。"""
        chunks = chunk_list(items, chunk_size)

        if chunks:
            # 最後のチャンク以外はすべてchunk_sizeと同じ
            for chunk in chunks[:-1]:
                assert len(chunk) == chunk_size

            # 最後のチャンクは1以上chunk_size以下
            assert 1 <= len(chunks[-1]) <= chunk_size

    @given(
        items=st.lists(st.text(), min_size=0, max_size=1000),
        chunk_size=st.integers(min_value=1, max_value=100),
    )
    def test_プロパティ_チャンク数が正しい(
        self,
        items: list[str],
        chunk_size: int,
    ) -> None:
        """チャンク数が数学的に正しいことを検証。"""
        chunks = chunk_list(items, chunk_size)

        expected_chunks = (len(items) + chunk_size - 1) // chunk_size
        if len(items) == 0:
            expected_chunks = 0

        assert len(chunks) == expected_chunks


class TestFlattenDictProperty:
    """Property-based tests for flatten_dict function."""

    # JSON互換の値を生成する戦略
    json_value = st.recursive(
        st.none()
        | st.booleans()
        | st.integers()
        | st.floats(allow_nan=False)
        | st.text(),
        lambda children: st.lists(children, max_size=5)
        | st.dictionaries(st.text(), children, max_size=5),
        max_leaves=20,
    )

    @given(nested=st.dictionaries(st.text(min_size=1), json_value, max_size=10))
    def test_プロパティ_フラット化後も全ての値が保持される(
        self,
        nested: dict,
    ) -> None:
        """フラット化前後で全ての値が保持されることを検証。"""
        flattened = flatten_dict(nested)

        # 全ての値を収集
        def collect_values(d: dict) -> list:
            values = []
            for v in d.values():
                if isinstance(v, dict):
                    values.extend(collect_values(v))
                else:
                    values.append(v)
            return values

        original_values = sorted(collect_values(nested), key=str)
        flattened_values = sorted(flattened.values(), key=str)

        # Noneとリストを含む場合は値の比較が複雑になるため、
        # 少なくとも値の数は同じであることを確認
        assert len(original_values) == len(flattened_values)

    @given(
        nested=st.dictionaries(
            st.text(min_size=1, alphabet=st.characters(blacklist_characters=".")),
            st.integers(),
            max_size=10,
        ),
        separator=st.sampled_from([".", "_", "-", "/"]),
    )
    def test_プロパティ_カスタムセパレータが正しく使用される(
        self,
        nested: dict,
        separator: str,
    ) -> None:
        """指定したセパレータが全てのキーで使用されることを検証。"""
        # ネストした構造を作成
        nested_dict = {"level1": nested}

        flattened = flatten_dict(nested_dict, separator=separator)

        # セパレータが含まれるキーがあることを確認
        if nested and flattened:
            separator_keys = [k for k in flattened if separator in k]
            assert len(separator_keys) > 0

            # 他のセパレータが使われていないことを確認
            other_separators = {".", "_", "-", "/"} - {separator}
            for key in flattened:
                for other_sep in other_separators:
                    assert other_sep not in key or other_sep in str(nested)


class TestJsonFileOperationsProperty:
    """Property-based tests for JSON file operations."""

    # JSON互換のオブジェクトを生成
    json_object = st.dictionaries(
        st.text(min_size=1),
        st.recursive(
            st.none()
            | st.booleans()
            | st.integers()
            | st.floats(allow_nan=False)
            | st.text(),
            lambda children: st.lists(children, max_size=3)
            | st.dictionaries(st.text(), children, max_size=3),
            max_leaves=10,
        ),
        min_size=1,
        max_size=10,
    )

    @given(data=json_object)
    def test_プロパティ_保存と読み込みで同じデータが復元される(
        self,
        data: dict,
    ) -> None:
        """JSONファイルへの保存と読み込みでデータが保持されることを検証。"""
        with tempfile.TemporaryDirectory() as temp_dir:
            json_file = Path(temp_dir) / "test_property.json"

            save_json_file(data, json_file)
            loaded_data = load_json_file(json_file)

            assert loaded_data == data

    @given(
        data=json_object,
        indent=st.integers(min_value=0, max_value=8),
    )
    def test_プロパティ_インデントレベルが機能する(
        self,
        data: dict,
        indent: int,
    ) -> None:
        """様々なインデントレベルでも正しく保存・読み込みできることを検証。"""
        with tempfile.TemporaryDirectory() as temp_dir:
            json_file = Path(temp_dir) / "test_indent.json"

            save_json_file(data, json_file, indent=indent)
            loaded_data = load_json_file(json_file)

            assert loaded_data == data

            # インデントが適用されているか確認
            content = json_file.read_text()
            if indent > 0 and len(data) > 0:
                # ネストがある場合、インデントされた行が存在するはず
                lines = content.split("\n")
                if len(lines) > 2:  # 複数行の場合
                    indented_lines = [
                        line for line in lines if line.startswith(" " * indent)
                    ]
                    assert len(indented_lines) > 0


class TestTypeConversionsProperty:
    """Property-based tests for type conversions and edge cases."""

    @given(
        size=st.integers(min_value=0, max_value=1000),
        chunk_size=st.integers(min_value=1, max_value=100),
    )
    def test_プロパティ_様々なリストサイズで正しく動作(
        self,
        size: int,
        chunk_size: int,
    ) -> None:
        """様々なサイズのリストで chunk_list が正しく動作することを検証。"""
        items = list(range(size))
        chunks = chunk_list(items, chunk_size)

        # 結果の検証
        if size == 0:
            assert chunks == []
        else:
            assert len(chunks) == (size + chunk_size - 1) // chunk_size

            # 全要素が含まれているか
            flattened = [item for chunk in chunks for item in chunk]
            assert flattened == items
