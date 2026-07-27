
from abc import ABC
from abc import abstractmethod


class Builder(ABC):
    __slots__ = ()

    @abstractmethod
    def end(self) -> object:
        pass
