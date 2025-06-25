"""Example module demonstrating best practices."""

from dataclasses import dataclass
from typing import Any, Protocol

from ..types import ItemDict


# ロガーを遅延初期化で循環インポートを回避
def _get_logger() -> Any:
    try:
        from ..utils.logging_config import get_logger

        return get_logger(__name__, module="example")
    except ImportError:
        import logging

        return logging.getLogger(__name__)


logger: Any = _get_logger()


class DataProcessor(Protocol):
    """Protocol for data processors."""

    def process(self, data: list[ItemDict]) -> list[ItemDict]:
        """Process a list of data items."""
        ...


@dataclass
class ExampleConfig:
    """Configuration for ExampleClass."""

    name: str
    max_items: int = 100
    enable_validation: bool = True

    def __post_init__(self) -> None:
        """Validate configuration after initialization."""
        logger.debug(
            "Initializing ExampleConfig",
            name=self.name,
            max_items=self.max_items,
        )
        if self.max_items <= 0:
            logger.error(
                "Invalid max_items value",
                max_items=self.max_items,
                error="max_items must be positive",
            )
            raise ValueError(f"max_items must be positive, got {self.max_items}")
        logger.debug("ExampleConfig validation completed", status="success")


class ExampleClass:
    """Example class demonstrating type hints and documentation.

    This class shows how to properly structure a Python class with:
    - Type hints for all methods
    - Comprehensive docstrings
    - Proper error handling

    Attributes
    ----------
    config : ExampleConfig
        Configuration for this instance
    data : list[dict[str, Any]]
        Internal data storage

    Examples
    --------
    >>> config = ExampleConfig(name="test", max_items=50)
    >>> example = ExampleClass(config)
    >>> example.add_item({"id": 1, "value": "test"})
    >>> len(example)
    1
    """

    def __init__(self, config: ExampleConfig) -> None:
        """Initialize ExampleClass with configuration.

        Parameters
        ----------
        config : ExampleConfig
            Configuration object
        """
        logger.debug(
            "Creating ExampleClass instance",
            config_name=config.name,
            max_items=config.max_items,
            validation_enabled=config.enable_validation,
        )
        self.config = config
        self.data: list[ItemDict] = []
        logger.info(
            "ExampleClass initialized",
            name=config.name,
            max_items=config.max_items,
            instance_id=id(self),
        )

    def add_item(self, item: ItemDict) -> None:
        """Add an item to the internal storage.

        Parameters
        ----------
        item : dict[str, Any]
            Item to add

        Raises
        ------
        ValueError
            If max_items limit is reached or validation fails
        """
        logger.debug(
            "Adding item",
            item_id=item.get("id"),
            item_name=item.get("name"),
            current_count=len(self.data),
        )

        if len(self.data) >= self.config.max_items:
            logger.warning(
                "Cannot add item: max_items limit reached",
                max_items=self.config.max_items,
                current_count=len(self.data),
                item_id=item.get("id"),
            )
            raise ValueError(
                f"Cannot add item: max_items limit ({self.config.max_items}) reached"
            )

        if self.config.enable_validation:
            logger.debug("Validating item", validation_enabled=True)
            self._validate_item(item)

        self.data.append(item)
        logger.debug(
            "Item added successfully",
            item_id=item.get("id"),
            total_items=len(self.data),
            capacity_used_percent=round(
                (len(self.data) / self.config.max_items) * 100, 1
            ),
        )

    def _validate_item(self, item: ItemDict) -> None:
        """Validate an item before adding.

        Parameters
        ----------
        item : dict[str, Any]
            Item to validate

        Raises
        ------
        ValueError
            If item is invalid
        """
        logger.debug(
            "Validating item",
            item_keys=list(item.keys()),
            has_id="id" in item,
            has_name="name" in item,
            has_value="value" in item,
        )

        # Validate required fields
        required_fields = {"id", "name", "value"}
        missing_fields = required_fields - set(item.keys())
        if missing_fields:
            logger.error(
                "Missing required fields",
                missing_fields=list(missing_fields),
                provided_fields=list(item.keys()),
                required_fields=list(required_fields),
            )
            raise ValueError(f"Missing required fields: {missing_fields}")

        # Check if all required fields have truthy values (not None or empty)
        invalid_fields = [field for field in required_fields if not item.get(field)]
        if invalid_fields:
            logger.error(
                "Required fields have empty or None values",
                item_id=item.get("id"),
                invalid_fields=invalid_fields,
                field_values={field: item.get(field) for field in invalid_fields},
            )
            raise ValueError(
                f"Required fields cannot be None or empty: {invalid_fields}"
            )

        logger.debug("Item validation passed", status="valid")

    def get_items(
        self,
        *,
        filter_key: str | None = None,
        filter_value: Any | None = None,
    ) -> list[ItemDict]:
        """Get items with optional filtering.

        Parameters
        ----------
        filter_key : str | None
            Key to filter by
        filter_value : Any | None
            Value to filter by

        Returns
        -------
        list[dict[str, Any]]
            Filtered items
        """
        logger.debug(
            "Getting items",
            filter_key=filter_key,
            filter_value=filter_value,
            total_items=len(self.data),
        )

        if filter_key is None or filter_value is None:
            logger.debug(
                "No filter applied",
                returning_all=True,
                item_count=len(self.data),
            )
            return self.data.copy()

        filtered = [item for item in self.data if item.get(filter_key) == filter_value]
        logger.debug(
            "Filter applied",
            filter_key=filter_key,
            filter_value=filter_value,
            matched_count=len(filtered),
            total_count=len(self.data),
            match_rate_percent=round(
                (len(filtered) / len(self.data) * 100) if self.data else 0, 1
            ),
        )
        return filtered

    def __len__(self) -> int:
        """Return the number of items."""
        return len(self.data)

    def __repr__(self) -> str:
        """Return string representation."""
        return (
            f"ExampleClass(name={self.config.name!r}, "
            f"items={len(self)}/{self.config.max_items})"
        )


def process_data(
    data: list[ItemDict],
    processor: DataProcessor,
    *,
    validate: bool = True,
) -> list[ItemDict]:
    """Process data using a processor.

    Parameters
    ----------
    data : list[dict[str, Any]]
        Data to process
    processor : DataProcessor
        Processor to use
    validate : bool
        Whether to validate data before processing

    Returns
    -------
    list[dict[str, Any]]
        Processed data

    Raises
    ------
    ValueError
        If validation fails
    """
    logger.debug(
        "Processing data",
        item_count=len(data),
        validation_enabled=validate,
        processor_type=processor.__class__.__name__,
    )

    if validate and not data:
        logger.error(
            "Data validation failed",
            reason="empty data",
            validation_enabled=True,
        )
        raise ValueError("Data cannot be empty")

    logger.debug(
        "Calling processor",
        processor_class=processor.__class__.__name__,
        input_count=len(data),
    )
    result = processor.process(data)
    logger.info(
        "Data processing completed",
        input_count=len(data),
        output_count=len(result),
        items_modified=len(result) - len(data) if len(result) != len(data) else 0,
        processing_status="success",
    )

    return result
