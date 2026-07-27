from types import MappingProxyType
from typing import Any
from typing import Mapping
from typing import Sequence
from typing import Union


Number = Union[int, float]


class RecordsDatasetAdapter:
    __slots__ = ("_records", "_columns")

    def __init__(
        self,
        records: Sequence[Mapping[str, Any]],
    ) -> None:
        if isinstance(records, (str, bytes)) or not isinstance(
            records,
            (list, tuple),
        ):
            raise TypeError(
                "records must be a list or tuple of mappings"
            )

        normalized: list[Mapping[str, Any]] = []
        columns: list[str] = []
        for record in records:
            if not isinstance(record, Mapping):
                raise TypeError("each record must be a mapping")
            copied: dict[str, Any] = {}
            for key, value in record.items():
                if not isinstance(key, str) or not key:
                    raise TypeError(
                        "record keys must be non-empty strings"
                    )
                copied[key] = value
                if key not in columns:
                    columns.append(key)
            normalized.append(MappingProxyType(copied))

        self._records = tuple(normalized)
        self._columns = tuple(columns)

    @property
    def columns(self) -> tuple[str, ...]:
        return self._columns

    @property
    def row_count(self) -> int:
        return len(self._records)

    def values(self, column: str) -> tuple[Any, ...]:
        self._require_column(column)
        return tuple(record.get(column) for record in self._records)

    def unique_count(self, columns: tuple[str, ...]) -> int:
        for column in columns:
            self._require_column(column)

        keys = {
            tuple(record.get(column) for column in columns)
            for record in self._records
        }
        return len(keys)

    def filter_between(
        self,
        column: str,
        minimum: Number,
        maximum: Number,
    ) -> "RecordsDatasetAdapter":
        self._require_column(column)
        records = []
        for record in self._records:
            value = record.get(column)
            if value is None:
                continue
            if minimum <= value <= maximum:
                records.append(dict(record))
        return RecordsDatasetAdapter(records)

    def _require_column(self, column: str) -> None:
        if column not in self._columns:
            raise KeyError(f'column "{column}" does not exist')
