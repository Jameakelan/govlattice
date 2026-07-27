from govlattice.nodes.requirement_node import RequirementNode
from govlattice.nodes.segment_node import SegmentNode


class StateNode:
    __slots__ = ("name", "requirements", "segments")

    def __init__(self, name: str) -> None:
        self.name = name
        self.requirements: list[RequirementNode] = []
        self.segments: dict[str, SegmentNode] = {}
