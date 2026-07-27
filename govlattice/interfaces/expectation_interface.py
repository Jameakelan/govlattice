from abc import ABC
from abc import abstractmethod


class ExpectationInterface(ABC):
    __slots__ = ()

    @abstractmethod
    def require_columns(self, *columns: str) -> "ExpectationInterface":
        pass

    @abstractmethod
    def require_unique(self, *columns: str) -> "ExpectationInterface":
        pass
