from abc import ABC
from abc import abstractmethod

from govlattice.nodes.state_node import StateNode


class StateVerifier(ABC):
    __slots__ = ()

    @abstractmethod
    def verify(self, state: StateNode) -> None:
        pass
