"""Integration tests for template_package components.

This module demonstrates how to write integration tests that verify
the interaction between multiple components of the template_package.
"""

from pathlib import Path

import pytest
from template_package.core.example import ExampleClass, ExampleConfig, process_data
from template_package.types import ItemDict
from template_package.utils.helpers import chunk_list, load_json_file, save_json_file
from template_package.utils.logging_config import get_logger

# モジュールレベルのロガー
logger = get_logger(__name__)


class SimpleDataProcessor:
    """Simple data processor for testing integration."""

    def process(self, data: list[ItemDict]) -> list[ItemDict]:
        """Process data by adding a processed flag and incrementing values."""
        logger.debug(f"Processing {len(data)} items with SimpleDataProcessor")

        processed_data = []
        for item in data:
            processed_item = item.copy()
            processed_item["value"] = item["value"] * 2  # Double the value
            processed_item["processed"] = True  # Add processed flag
            processed_data.append(processed_item)

        logger.debug(f"Processed {len(processed_data)} items successfully")
        return processed_data


class TestExampleClassIntegration:
    """Integration tests for ExampleClass with other components."""

    def test_正常系_ExampleClassとヘルパー関数の連携(self, temp_dir: Path) -> None:
        """ExampleClassとヘルパー関数が正しく連携することを確認。"""
        logger.debug("Starting ExampleClass and helper function integration test")

        # 1. 設定ファイルをJSONで作成
        config_data = {
            "name": "integration_test",
            "max_items": 5,
            "enable_validation": True,
        }
        config_file = temp_dir / "config.json"
        save_json_file(config_data, config_file)

        # 2. 設定ファイルを読み込んでExampleClassを初期化
        loaded_config_data = load_json_file(config_file)
        config = ExampleConfig(
            name=loaded_config_data["name"],
            max_items=loaded_config_data["max_items"],
            enable_validation=loaded_config_data["enable_validation"],
        )
        example = ExampleClass(config)

        # 3. テストデータを準備してアイテムを追加
        test_items = [
            {"id": 1, "name": "Item 1", "value": 10},
            {"id": 2, "name": "Item 2", "value": 20},
            {"id": 3, "name": "Item 3", "value": 30},
        ]

        for item in test_items:
            example.add_item(item)

        # 4. データを取得してチャンク化
        all_items = example.get_items()
        chunks = chunk_list(all_items, chunk_size=2)

        # 5. 検証
        assert len(all_items) == 3
        assert len(chunks) == 2  # [2, 1]に分割される
        assert len(chunks[0]) == 2
        assert len(chunks[1]) == 1

        logger.info(
            "ExampleClass and helper function integration test completed successfully"
        )

    def test_正常系_データ処理パイプラインの統合(self, temp_dir: Path) -> None:
        """データ処理パイプライン全体の統合テスト。"""
        logger.debug("Starting data processing pipeline integration test")

        # 1. 入力データファイルを作成
        input_data = [
            {"id": 1, "name": "Data 1", "value": 5},
            {"id": 2, "name": "Data 2", "value": 10},
            {"id": 3, "name": "Data 3", "value": 15},
        ]
        input_file = temp_dir / "input.json"
        save_json_file({"items": input_data}, input_file)

        # 2. データファイルを読み込み
        file_data = load_json_file(input_file)
        items_data = file_data["items"]

        # 3. ExampleClassでデータ管理
        config = ExampleConfig(name="pipeline_test", max_items=10)
        example = ExampleClass(config)

        for item in items_data:
            example.add_item(item)

        # 4. データ処理
        processor = SimpleDataProcessor()
        raw_data = example.get_items()
        processed_data = process_data(raw_data, processor)

        # 5. 結果をファイルに保存
        output_file = temp_dir / "output.json"
        save_json_file({"processed_items": processed_data}, output_file)

        # 6. 保存されたファイルを読み込んで検証
        result_data = load_json_file(output_file)
        result_items = result_data["processed_items"]

        # 検証
        assert len(result_items) == 3
        for i, item in enumerate(result_items):
            expected_value = input_data[i]["value"] * 2
            assert item["value"] == expected_value
            assert item["processed"] is True
            assert item["id"] == input_data[i]["id"]
            assert item["name"] == input_data[i]["name"]

        logger.info("Data processing pipeline integration test completed successfully")

    def test_正常系_エラーハンドリングとリカバリー(self, temp_dir: Path) -> None:
        """エラーハンドリングとリカバリーの統合テスト。"""
        logger.debug("Starting error handling and recovery integration test")

        # 1. 不正なデータを含むファイルを作成
        mixed_data = [
            {"id": 1, "name": "Valid Item", "value": 100},  # 正常データ
            {"id": 2, "name": "", "value": 200},  # name が空（バリデーションエラー）
            {"id": 3, "name": "Another Valid", "value": 300},  # 正常データ
        ]

        config = ExampleConfig(name="error_test", max_items=5, enable_validation=True)
        example = ExampleClass(config)

        # 2. データを追加（エラーハンドリング）
        successful_items = []
        failed_items = []

        for item in mixed_data:
            try:
                example.add_item(item)
                successful_items.append(item)
                logger.debug(f"Successfully added item: {item['id']}")
            except ValueError as e:
                failed_items.append(item)
                logger.warning(f"Failed to add item {item['id']}: {e}")

        # 3. 成功したデータのみを処理
        if successful_items:
            valid_data = example.get_items()
            processor = SimpleDataProcessor()
            processed_data = process_data(valid_data, processor)

            # 結果を保存
            output_file = temp_dir / "recovered_output.json"
            save_json_file(
                {
                    "processed_items": processed_data,
                    "failed_items": failed_items,
                    "summary": {
                        "total_input": len(mixed_data),
                        "successful": len(successful_items),
                        "failed": len(failed_items),
                    },
                },
                output_file,
            )

            # 検証
            result = load_json_file(output_file)
            assert len(result["processed_items"]) == 2  # 正常データのみ
            assert len(result["failed_items"]) == 1  # エラーデータ
            assert result["summary"]["total_input"] == 3
            assert result["summary"]["successful"] == 2
            assert result["summary"]["failed"] == 1

            logger.info(
                "Error handling and recovery integration test completed successfully"
            )

    def test_正常系_大量データ処理のパフォーマンス(self, temp_dir: Path) -> None:
        """大量データ処理時のパフォーマンステスト。"""
        logger.debug("Starting large data processing performance test")

        # 1. 大量のテストデータを生成
        large_dataset = [
            {"id": i, "name": f"Item {i}", "value": i * 10}
            for i in range(1, 1001)  # 1000件のデータ
        ]

        # 2. ExampleClassで大量データを管理
        config = ExampleConfig(name="performance_test", max_items=1500)
        example = ExampleClass(config)

        # データをバッチで追加
        batch_size = 100
        batches = chunk_list(large_dataset, batch_size)

        for batch_num, batch in enumerate(batches):
            logger.debug(f"Processing batch {batch_num + 1}/{len(batches)}")
            for item in batch:
                example.add_item(item)

        # 3. 全データを取得して処理
        all_data = example.get_items()
        processor = SimpleDataProcessor()
        processed_data = process_data(all_data, processor)

        # 4. 結果をチャンク化して保存
        output_chunks = chunk_list(processed_data, 200)

        chunk_files = []
        for i, chunk in enumerate(output_chunks):
            chunk_file = temp_dir / f"output_chunk_{i}.json"
            save_json_file({"chunk": i, "data": chunk}, chunk_file)
            chunk_files.append(chunk_file)

        # 5. 検証
        assert len(all_data) == 1000
        assert len(processed_data) == 1000
        assert len(output_chunks) == 5  # 1000 / 200 = 5チャンク

        # 各チャンクファイルの検証
        total_verified = 0
        for chunk_file in chunk_files:
            chunk_data = load_json_file(chunk_file)
            total_verified += len(chunk_data["data"])

        assert total_verified == 1000

        logger.info(
            f"Large data processing test completed: {total_verified} items processed"
        )

    def test_異常系_連鎖エラーハンドリング(self, temp_dir: Path) -> None:
        """複数コンポーネント間でのエラーの連鎖処理テスト。"""
        logger.debug("Starting cascade error handling test")

        # 1. 存在しないファイルの読み込みエラー
        nonexistent_file = temp_dir / "nonexistent.json"

        with pytest.raises(FileNotFoundError):
            load_json_file(nonexistent_file)

        # 2. 不正なJSONファイルの処理
        invalid_json_file = temp_dir / "invalid.json"
        invalid_json_file.write_text("{ invalid json content", encoding="utf-8")

        with pytest.raises(ValueError, match="Invalid JSON"):
            load_json_file(invalid_json_file)

        # 3. 容量制限エラーの処理
        config = ExampleConfig(name="limit_test", max_items=2)
        example = ExampleClass(config)

        # 制限を超えるデータ追加
        items = [
            {"id": 1, "name": "Item 1", "value": 10},
            {"id": 2, "name": "Item 2", "value": 20},
            {"id": 3, "name": "Item 3", "value": 30},  # これでエラーになる
        ]

        # 最初の2つは成功
        example.add_item(items[0])
        example.add_item(items[1])

        # 3つ目でエラー
        with pytest.raises(ValueError, match="max_items limit"):
            example.add_item(items[2])

        # 現在のデータは2件のまま
        assert len(example) == 2

        logger.info("Cascade error handling test completed successfully")


class TestMultiComponentIntegration:
    """複数コンポーネントの統合テスト。"""

    def test_正常系_ファイルIO_データ処理_チャンク化の統合(
        self, temp_dir: Path
    ) -> None:
        """ファイルIO、データ処理、チャンク化の完全な統合テスト。"""
        logger.debug("Starting comprehensive integration test")

        # 1. 複数のデータファイルを作成
        datasets = {
            "users": [
                {"id": 1, "name": "Alice", "value": 100},
                {"id": 2, "name": "Bob", "value": 150},
            ],
            "products": [
                {"id": 3, "name": "Product A", "value": 200},
                {"id": 4, "name": "Product B", "value": 250},
                {"id": 5, "name": "Product C", "value": 300},
            ],
        }

        data_files = {}
        for category, data in datasets.items():
            file_path = temp_dir / f"{category}.json"
            save_json_file({"items": data}, file_path)
            data_files[category] = file_path

        # 2. 各ファイルからデータを読み込み、統合
        all_items = []
        for category, file_path in data_files.items():
            file_data = load_json_file(file_path)
            items = file_data["items"]
            logger.debug(f"Loaded {len(items)} items from {category}")
            all_items.extend(items)

        # 3. ExampleClassで統合データを管理
        config = ExampleConfig(name="multi_component_test", max_items=10)
        example = ExampleClass(config)

        for item in all_items:
            example.add_item(item)

        # 4. データを処理
        processor = SimpleDataProcessor()
        managed_data = example.get_items()
        processed_data = process_data(managed_data, processor)

        # 5. 結果をカテゴリ別にチャンク化
        user_results = [item for item in processed_data if item["id"] <= 2]
        product_results = [item for item in processed_data if item["id"] > 2]

        # 6. チャンク化して保存
        user_chunks = chunk_list(user_results, 1)  # 1つずつ分割
        product_chunks = chunk_list(product_results, 2)  # 2つずつ分割

        # 結果を保存
        results_file = temp_dir / "integration_results.json"
        save_json_file(
            {
                "user_chunks": len(user_chunks),
                "product_chunks": len(product_chunks),
                "total_processed": len(processed_data),
                "user_results": user_results,
                "product_results": product_results,
            },
            results_file,
        )

        # 7. 検証
        results = load_json_file(results_file)

        assert results["total_processed"] == 5
        assert results["user_chunks"] == 2  # 2ユーザー、1つずつ
        assert results["product_chunks"] == 2  # 3商品、2つずつで2チャンク
        assert len(results["user_results"]) == 2
        assert len(results["product_results"]) == 3

        # 処理結果の値が正しく倍になっているか確認
        for result in results["user_results"]:
            original_value = next(
                item["value"]
                for dataset in datasets.values()
                for item in dataset
                if item["id"] == result["id"]
            )
            assert result["value"] == original_value * 2
            assert result["processed"] is True

        logger.info(
            "Comprehensive multi-component integration test completed successfully"
        )
