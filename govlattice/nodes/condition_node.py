from numbers import Real
from typing import Union


Number = Union[int, float]


class ConditionNode:
    __slots__ = ("type", "column", "minimum", "maximum")

    def __init__(
        self,
        condition_type: str,
        column: str,
        minimum: Number,
        maximum: Number,
    ) -> None:
        self.type = condition_type
        self.column = column
        self.minimum = minimum
        self.maximum = maximum

    @classmethod
    def between(
        cls,
        column: str,
        minimum: Number,
        maximum: Number,
    ) -> "ConditionNode":
        column = cls._validate_column(column)
        minimum = cls._validate_number("minimum", minimum)
        maximum = cls._validate_number("maximum", maximum)
        if minimum > maximum:
            raise ValueError("minimum must not be greater than maximum")

        return cls("between", column, minimum, maximum)

    @staticmethod
    def _validate_column(column: str) -> str:
        if not isinstance(column, str):
            raise TypeError("column must be a string")
        column = column.strip()
        if not column:
            raise ValueError("column must not be empty")
        return column

    @staticmethod
    def _validate_number(name: str, value: Number) -> Number:
        if isinstance(value, bool) or not isinstance(value, Real):
            raise TypeError(f"{name} must be a number")
        return value
