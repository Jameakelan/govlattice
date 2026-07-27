from typing import TYPE_CHECKING

from govlattice.builder import Builder
from govlattice.interfaces.expectation_interface import ExpectationInterface

if TYPE_CHECKING:
    from govlattice.designer.policy_designer import PolicyDesigner


class ExpectationBuilder(Builder, ExpectationInterface):
    __slots__ = ("_designer", "_state_id", "_requirements")

    def __init__(self, designer: "PolicyDesigner", state_id: str) -> None:
        self._designer = designer
        self._state_id = state_id
        self._requirements: list[tuple[str, tuple[str, ...]]] = []

    @property
    def state_id(self) -> str:
        return self._state_id

    @property
    def requirements(self) -> tuple[tuple[str, tuple[str, ...]], ...]:
        return tuple(self._requirements)

    def end(self) -> "PolicyDesigner":
        return self._designer

    def require_columns(self, *columns: str) -> "ExpectationBuilder":
        self._requirements.append(
            ("require_columns", self._validate_columns(columns))
        )
        return self

    def require_unique(self, *columns: str) -> "ExpectationBuilder":
        self._requirements.append(
            ("require_unique", self._validate_columns(columns))
        )
        return self

    @staticmethod
    def _validate_columns(columns: tuple[str, ...]) -> tuple[str, ...]:
        if not columns:
            raise ValueError("at least one column is required")

        normalized: list[str] = []
        for column in columns:
            if not isinstance(column, str):
                raise TypeError("column names must be strings")

            column = column.strip()
            if not column:
                raise ValueError("column names must not be empty")
            normalized.append(column)

        return tuple(normalized)
