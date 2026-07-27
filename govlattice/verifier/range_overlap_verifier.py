from govlattice.nodes.condition_node import ConditionNode
from govlattice.nodes.segment_node import SegmentNode
from govlattice.nodes.state_node import StateNode
from govlattice.verifier.state_verifier import StateVerifier


class OverlapRangeError(ValueError):
    pass


class RangeOverlapVerifier(StateVerifier):
    __slots__ = ("_column",)

    def __init__(self, column: str) -> None:
        if not isinstance(column, str):
            raise TypeError("verification column must be a string")
        column = column.strip()
        if not column:
            raise ValueError("verification column must not be empty")
        self._column = column

    def verify(self, state: StateNode) -> None:
        ranges: list[tuple[SegmentNode, ConditionNode]] = []

        for segment in state.segments.values():
            condition = segment.condition
            if (
                condition is None
                or condition.type != "between"
                or condition.column != self._column
            ):
                continue
            ranges.append((segment, condition))

        if not ranges:
            raise ValueError(
                f'No between conditions found for column "{self._column}" '
                f'in state "{state.name}"'
            )

        self._verify_column(state, self._column, ranges)

    @staticmethod
    def _verify_column(
        state: StateNode,
        column: str,
        ranges: list[tuple[SegmentNode, ConditionNode]],
    ) -> None:
        ordered = sorted(ranges, key=lambda item: item[1].minimum)
        if len(ordered) < 2:
            return

        previous_segment, previous_condition = ordered[0]
        for current_segment, current_condition in ordered[1:]:
            if current_condition.minimum <= previous_condition.maximum:
                raise OverlapRangeError(
                    f'Range overlap in state "{state.name}" '
                    f'for column "{column}": segment '
                    f'"{previous_segment.name}" '
                    f"[{previous_condition.minimum}, "
                    f"{previous_condition.maximum}] overlaps segment "
                    f'"{current_segment.name}" '
                    f"[{current_condition.minimum}, "
                    f"{current_condition.maximum}]"
                )

            if current_condition.maximum > previous_condition.maximum:
                previous_segment = current_segment
                previous_condition = current_condition
