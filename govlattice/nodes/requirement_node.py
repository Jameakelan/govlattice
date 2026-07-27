from numbers import Real
from typing import Any
from typing import Sequence
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
    def metric(
        cls,
        metric: str,
        minimum: Number,
    ) -> "RequirementNode":
        return cls(
            "require_metric",
            {
                "metric": cls._validate_metric(metric),
                "minimum": cls._validate_score(minimum),
            },
        )

    @classmethod
    def metrics(
        cls,
        metrics: Sequence[str],
        minimums: Sequence[Number],
    ) -> "RequirementNode":
        if isinstance(metrics, (str, bytes)) or not isinstance(
            metrics,
            (list, tuple),
        ):
            raise TypeError("metrics must be a list or tuple of strings")
        if isinstance(minimums, (str, bytes)) or not isinstance(
            minimums,
            (list, tuple),
        ):
            raise TypeError(
                "minimums must be a list or tuple of numbers"
            )
        if not metrics:
            raise ValueError("at least one metric is required")
        if len(metrics) != len(minimums):
            raise ValueError(
                "metrics and minimums must have the same length"
            )

        thresholds: dict[str, Number] = {}
        for metric, minimum in zip(metrics, minimums):
            metric = cls._validate_metric(metric)
            if metric in thresholds:
                raise ValueError(f'duplicate metric "{metric}"')
            thresholds[metric] = cls._validate_score(minimum)

        return cls(
            "require_metrics",
            {"metrics": thresholds},
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
    def _validate_metric(metric: str) -> str:
        if not isinstance(metric, str):
            raise TypeError("metric names must be strings")
        metric = metric.strip()
        if not metric:
            raise ValueError("metric names must not be empty")
        return metric

    @classmethod
    def _validate_score(cls, value: Number) -> Number:
        value = cls._validate_number("minimum score", value)
        if value < 0 or value > 1:
            raise ValueError("minimum score must be between 0 and 1")
        return value

    @staticmethod
    def _validate_number(name: str, value: Number) -> Number:
        if isinstance(value, bool) or not isinstance(value, Real):
            raise TypeError(f"{name} must be a number")
        return value
