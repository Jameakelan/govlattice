from typing import Any

from govlattice.enum import ComparisonOperator


def compare_values(
    observed: Any,
    operator: ComparisonOperator,
    expected: Any,
) -> bool:
    if operator is ComparisonOperator.LT:
        return observed < expected
    if operator is ComparisonOperator.LTE:
        return observed <= expected
    if operator is ComparisonOperator.GT:
        return observed > expected
    if operator is ComparisonOperator.GTE:
        return observed >= expected
    raise ValueError(f"unsupported comparison operator: {operator}")
