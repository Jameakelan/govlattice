from numbers import Real
from typing import Any
from typing import Union


Number = Union[int, float]


class RequirementNode:
    __slots__ = ("type", "_parameters")

    def __init__(
        self,
        requirement_type: str,
        parameters: dict[str, Any],
    ) -> None:
        self.type = requirement_type
        self._parameters = parameters

    @property
    def parameters(self) -> dict[str, Any]:
        return dict(self._parameters)

    @classmethod
    def columns(
        cls,
        requirement_type: str,
        columns: tuple[str, ...],
    ) -> "RequirementNode":
        return cls(
            requirement_type,
            {"columns": cls._validate_columns(columns)},
        )

    @classmethod
    def missing_rate(
        cls,
        column: str,
        maximum: Number,
    ) -> "RequirementNode":
        column = cls._validate_column(column)
        maximum = cls._validate_number("maximum", maximum)
        if maximum < 0 or maximum > 1:
            raise ValueError("maximum must be between 0 and 1")

        return cls(
            "require_missing_rate",
            {
                "column": column,
                "maximum": maximum,
            },
        )

    @classmethod
    def range(
        cls,
        column: str,
        minimum: Number,
        maximum: Number,
    ) -> "RequirementNode":
        column = cls._validate_column(column)
        minimum = cls._validate_number("minimum", minimum)
        maximum = cls._validate_number("maximum", maximum)
        if minimum > maximum:
            raise ValueError("minimum must not be greater than maximum")

        return cls(
            "require_range",
            {
                "column": column,
                "minimum": minimum,
                "maximum": maximum,
            },
        )

    @classmethod
    def _validate_columns(
        cls,
        columns: tuple[str, ...],
    ) -> tuple[str, ...]:
        if not columns:
            raise ValueError("at least one column is required")
        return tuple(cls._validate_column(column) for column in columns)

    @staticmethod
    def _validate_column(column: str) -> str:
        if not isinstance(column, str):
            raise TypeError("column names must be strings")
        column = column.strip()
        if not column:
            raise ValueError("column names must not be empty")
        return column

    @staticmethod
    def _validate_number(name: str, value: Number) -> Number:
        if isinstance(value, bool) or not isinstance(value, Real):
            raise TypeError(f"{name} must be a number")
        return value
