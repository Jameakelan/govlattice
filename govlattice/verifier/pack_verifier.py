from abc import ABC
from abc import abstractmethod

from govlattice.nodes.policy_pack_node import PolicyPackNode


class PackVerifier(ABC):
    __slots__ = ()

    @abstractmethod
    def verify(self, pack: PolicyPackNode) -> None:
        pass
