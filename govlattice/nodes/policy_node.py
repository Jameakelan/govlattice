from govlattice.nodes.state_node import StateNode


class PolicyNode:
    __slots__ = ("name", "states")

    def __init__(self, name: str) -> None:
        self.name = name
        self.states: dict[str, StateNode] = {}
