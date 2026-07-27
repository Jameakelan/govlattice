"""Optional dataset adapter for pandas DataFrames."""

from typing import Any
from typing import Union


Number = Union[int, float]


class PandasDatasetAdapter:
    """Expose a defensive DataFrame snapshot through ``DatasetAdapter``.

    Pandas is imported only when an adapter is instantiated, so the core
    package remains usable without the optional dependency. Missing pandas
    scalar values, including ``NaN``, ``NaT``, and ``pd.NA``, are normalized
    to ``None`` for consistent requirement semantics.

    Args:
        dataframe: A pandas ``DataFrame`` with unique, non-empty string column
            names.

    Raises:
        ImportError: If pandas is not installed.
        TypeError: If ``dataframe`` is not a pandas ``DataFrame`` or a column
            name is not a non-empty string.
        ValueError: If the DataFrame contains duplicate column names.
    """

    __slots__ = ("_dataframe", "_pandas")

    def __init__(self, dataframe: Any) -> None:
        try:
            import pandas
        except ImportError as error:
            raise ImportError(
                "PandasDatasetAdapter requires pandas; install "
                "requirements-pandas.txt"
            ) from error

        if not isinstance(dataframe, pandas.DataFrame):
            raise TypeError("dataframe must be a pandas DataFrame")

        columns = tuple(dataframe.columns)
        for column in columns:
            if not isinstance(column, str) or not column:
                raise TypeError(
                    "DataFrame columns must be non-empty strings"
                )
        if len(columns) != len(set(columns)):
            raise ValueError("DataFrame columns must be unique")

        self._pandas = pandas
        self._dataframe = dataframe.copy(deep=True)

    @property
    def columns(self) -> tuple[str, ...]:
        """Return DataFrame columns in their existing order."""
        return tuple(self._dataframe.columns)

    @property
    def row_count(self) -> int:
        """Return the number of DataFrame rows."""
        return len(self._dataframe.index)

    def values(self, column: str) -> tuple[Any, ...]:
        """Return normalized values for one DataFrame column."""
        self._require_column(column)
        return tuple(
            self._normalize_value(value)
            for value in self._dataframe[column].tolist()
        )

    def unique_count(self, columns: tuple[str, ...]) -> int:
        """Count unique composite values across selected columns."""
        if not isinstance(columns, tuple) or not columns:
            raise ValueError("columns must be a non-empty tuple")
        for column in columns:
            self._require_column(column)
        return int(
            self._dataframe
            .loc[:, list(columns)]
            .drop_duplicates()
            .shape[0]
        )

    def filter_between(
        self,
        column: str,
        minimum: Number,
        maximum: Number,
    ) -> "PandasDatasetAdapter":
        """Return rows inside an inclusive range, excluding missing values."""
        self._require_column(column)
        series = self._dataframe[column]
        mask = series.ge(minimum) & series.le(maximum)
        mask = mask.fillna(False)
        return PandasDatasetAdapter(self._dataframe.loc[mask])

    def _require_column(self, column: str) -> None:
        """Raise when a requested column is absent from the DataFrame."""
        if column not in self._dataframe.columns:
            raise KeyError(f'column "{column}" does not exist')

    def _normalize_value(self, value: Any) -> Any:
        """Convert pandas missing scalars to ``None``."""
        if value is None:
            return None
        try:
            if bool(self._pandas.isna(value)):
                return None
        except (TypeError, ValueError):
            pass
        return value
