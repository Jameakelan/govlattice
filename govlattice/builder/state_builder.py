from typing import TYPE_CHECKING

from govlattice.builder import Builder
from govlattice.builder.segment_builder import SegmentBuilder
from govlattice.nodes.requirement_node import Number
from govlattice.nodes.requirement_node import RequirementNode
from govlattice.nodes.segment_node import SegmentNode
from govlattice.nodes.state_node import StateNode
from govlattice.verifier.range_overlap_verifier import RangeOverlapVerifier

if TYPE_CHECKING:
    from govlattice.designer.policy_designer import PolicyDesigner


class StateBuilder(Builder):
    __slots__ = ("_designer", "_node")

    def __init__(
        self,
        designer: "PolicyDesigner",
        node: StateNode,
    ) -> None:
        self._designer = designer
        self._node = node

    @property
    def state_id(self) -> str:
        return self._node.name

    @property
    def requirements(self) -> tuple[RequirementNode, ...]:
        return tuple(self._node.requirements)

    def segment(self, name: str) -> SegmentBuilder:
        name = self._validate_name(name)
        node = self._node.segments.get(name)
        if node is None:
            node = SegmentNode(name)
            self._node.segments[name] = node
        return SegmentBuilder(self, node)

    def require_columns(self, *columns: str) -> "StateBuilder":
        self._node.requirements.append(
            RequirementNode.columns("require_columns", columns)
        )
        return self

    def require_unique(self, *columns: str) -> "StateBuilder":
        self._node.requirements.append(
            RequirementNode.columns("require_unique", columns)
        )
        return self

    def require_missing_rate(
        self,
        column: str,
        maximum: Number,
    ) -> "StateBuilder":
        self._node.requirements.append(
            RequirementNode.missing_rate(column, maximum)
        )
        return self

    def require_range(
        self,
        column: str,
        minimum: Number,
        maximum: Number,
    ) -> "StateBuilder":
        self._node.requirements.append(
            RequirementNode.range(column, minimum, maximum)
        )
        return self

    def verify_overlap_range(self, column: str) -> "StateBuilder":
        RangeOverlapVerifier(column).verify(self._node)
        return self

    def end(self) -> "PolicyDesigner":
        return self._designer

    @staticmethod
    def _validate_name(name: str) -> str:
        if not isinstance(name, str):
            raise TypeError("segment name must be a string")
        name = name.strip()
        if not name:
            raise ValueError("segment name must not be empty")
        return name
