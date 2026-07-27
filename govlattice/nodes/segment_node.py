from typing import Optional

from govlattice.nodes.condition_node import ConditionNode
from govlattice.nodes.requirement_node import RequirementNode


class SegmentNode:
    __slots__ = ("name", "condition", "requirements")

    def __init__(self, name: str) -> None:
        self.name = name
        self.condition: Optional[ConditionNode] = None
        self.requirements: list[RequirementNode] = []
