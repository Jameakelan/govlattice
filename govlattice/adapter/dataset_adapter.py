"""Dataset abstraction consumed by the policy engine."""

from typing import Any
from typing import Protocol
from typing import Union
from typing import runtime_checkable


Number = Union[int, float]


@runtime_checkable
class DatasetAdapter(Protocol):
    """Minimal dataset operations required by built-in evaluators.

    Third-party adapters for dataframe, database, or distributed systems can
    implement this protocol without modifying the engine.
    """

    @property
    def columns(self) -> tuple[str, ...]:
        """Return available column names in deterministic order."""
        ...

    @property
    def row_count(self) -> int:
        """Return the number of rows in this dataset scope."""
        ...

    def values(self, column: str) -> tuple[Any, ...]:
        """Return all values for one column in row order."""
        ...

    def unique_count(self, columns: tuple[str, ...]) -> int:
        """Return the number of unique composite keys for ``columns``."""
        ...

    def filter_between(
        self,
        column: str,
        minimum: Number,
        maximum: Number,
    ) -> "DatasetAdapter":
        """Return rows whose non-missing column value is within the range."""
        ...
