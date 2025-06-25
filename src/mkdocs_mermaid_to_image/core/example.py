"""Example module with basic functionality."""

from dataclasses import dataclass
from typing import Any, Protocol

from ..utils.logging_config import get_logger

logger = get_logger(__name__)


@dataclass
class ExampleConfig:
    """Configuration for example functionality."""

    name: str
    max_items: int = 100
    enable_validation: bool = True

    def __post_init__(self) -> None:
        """Validate configuration after initialization."""
        if self.max_items <= 0:
            raise ValueError("max_items must be positive")


class DataProcessor(Protocol):
    """Protocol for data processors."""

    def process(self, data: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Process data and return processed result."""
        ...


class ExampleClass:
    """Example class demonstrating the project structure."""

    def __init__(self, config: ExampleConfig) -> None:
        """Initialize with configuration."""
        self.config = config
        self._items: list[dict[str, Any]] = []
        logger.info(
            "ExampleClass initialized",
            config_name=config.name,
            max_items=config.max_items,
        )

    def add_item(self, item: dict[str, Any]) -> None:
        """Add an item to the collection."""
        logger.debug("Adding item", item_id=item.get("id"), item_name=item.get("name"))

        if len(self._items) >= self.config.max_items:
            raise ValueError("max_items limit exceeded")

        if self.config.enable_validation:
            required_fields = {"id", "name", "value"}
            if not all(field in item for field in required_fields):
                raise ValueError("Missing required fields: id, name, value")
            if not item.get("name"):
                raise ValueError("name cannot be empty")

        self._items.append(item)
        logger.debug(
            "Item added successfully",
            total_items=len(self._items),
            max_items=self.config.max_items,
        )

    def get_items(
        self,
        filter_key: str | None = None,
        filter_value: Any = None,
    ) -> list[dict[str, Any]]:
        """Get items with optional filtering."""
        logger.debug(
            "Getting items",
            filter_key=filter_key,
            filter_value=filter_value,
            total_items=len(self._items),
        )

        if filter_key is None:
            return self._items.copy()

        filtered = [
            item for item in self._items if item.get(filter_key) == filter_value
        ]
        logger.debug(
            "Items filtered",
            original_count=len(self._items),
            filtered_count=len(filtered),
            filter_key=filter_key,
        )
        return filtered

    def __len__(self) -> int:
        """Return number of items."""
        return len(self._items)

    def __repr__(self) -> str:
        """Return string representation."""
        return (
            f"ExampleClass(name='{self.config.name}', "
            f"items={len(self._items)}/{self.config.max_items})"
        )


def process_data(
    data: list[dict[str, Any]],
    processor: DataProcessor,
    validate: bool = True,
) -> list[dict[str, Any]]:
    """Process data using the provided processor."""
    logger.info("Processing data", item_count=len(data), validation_enabled=validate)

    if validate and not data:
        raise ValueError("Data cannot be empty when validation is enabled")

    result = processor.process(data)
    logger.info("Processing completed", input_count=len(data), output_count=len(result))
    return result
