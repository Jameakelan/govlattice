from typing import Any
from typing import Protocol
from typing import Union
from typing import runtime_checkable


Number = Union[int, float]


@runtime_checkable
class DatasetAdapter(Protocol):
    @property
    def columns(self) -> tuple[str, ...]:
        ...

    @property
    def row_count(self) -> int:
        ...

    def values(self, column: str) -> tuple[Any, ...]:
        ...

    def unique_count(self, columns: tuple[str, ...]) -> int:
        ...

    def filter_between(
        self,
        column: str,
        minimum: Number,
        maximum: Number,
    ) -> "DatasetAdapter":
        ...
