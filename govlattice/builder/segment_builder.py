from typing import TYPE_CHECKING
from typing import Sequence

from govlattice.builder import Builder
from govlattice.nodes.condition_node import ConditionNode
from govlattice.nodes.requirement_node import Number
from govlattice.nodes.requirement_node import RequirementNode
from govlattice.nodes.segment_node import SegmentNode

if TYPE_CHECKING:
    from govlattice.builder.state_builder import StateBuilder


class SegmentBuilder(Builder):
    __slots__ = ("_parent", "_node")

    def __init__(
        self,
        parent: "StateBuilder",
        node: SegmentNode,
    ) -> None:
        self._parent = parent
        self._node = node

    @property
    def name(self) -> str:
        return self._node.name

    def when_between(
        self,
        column: str,
        minimum: Number,
        maximum: Number,
    ) -> "SegmentBuilder":
        if self._node.condition is not None:
            raise ValueError(
                f'segment "{self._node.name}" already has a condition'
            )
        self._node.condition = ConditionNode.between(
            column,
            minimum,
            maximum,
        )
        return self

    def require_columns(self, *columns: str) -> "SegmentBuilder":
        self._node.requirements.append(
            RequirementNode.columns("require_columns", columns)
        )
        return self

    def require_unique(self, *columns: str) -> "SegmentBuilder":
        self._node.requirements.append(
            RequirementNode.columns("require_unique", columns)
        )
        return self

    def require_missing_rate(
        self,
        column: str,
        maximum: Number,
    ) -> "SegmentBuilder":
        self._node.requirements.append(
            RequirementNode.missing_rate(column, maximum)
        )
        return self

    def require_range(
        self,
        column: str,
        minimum: Number,
        maximum: Number,
    ) -> "SegmentBuilder":
        self._node.requirements.append(
            RequirementNode.range(column, minimum, maximum)
        )
        return self

    def require_metric(
        self,
        metric: str,
        minimum: Number,
    ) -> "SegmentBuilder":
        self._node.requirements.append(
            RequirementNode.metric(metric, minimum)
        )
        return self

    def require_metrics(
        self,
        metrics: Sequence[str],
        minimums: Sequence[Number],
    ) -> "SegmentBuilder":
        self._node.requirements.append(
            RequirementNode.metrics(metrics, minimums)
        )
        return self

    def end(self) -> "StateBuilder":
        if self._node.condition is None:
            raise ValueError(
                f'segment "{self._node.name}" requires a condition'
            )
        return self._parent
