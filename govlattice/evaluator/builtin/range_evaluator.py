"""Evaluator for inclusive numeric column ranges."""

from govlattice.evaluator.requirement_evaluation_context import (
    RequirementEvaluationContext,
)
from govlattice.evaluator.requirement_evaluator import (
    RequirementEvaluation,
)
from govlattice.model import RequirementDefinition


class RangeEvaluator:
    """Check all non-missing column values against an inclusive range."""

    requirement_type = "require_range"

    def evaluate(
        self,
        requirement: RequirementDefinition,
        context: RequirementEvaluationContext,
    ) -> RequirementEvaluation:
        """Evaluate a ``require_range`` requirement."""
        column = requirement.parameters["column"]
        if column not in context.dataset.columns:
            return RequirementEvaluation.error(
                expected=requirement.parameters,
                observed={"missing_column": column},
                message=f'column "{column}" does not exist',
            )
        values = tuple(
            value
            for value in context.dataset.values(column)
            if value is not None
        )
        if not values:
            return RequirementEvaluation.error(
                expected=requirement.parameters,
                observed={"evaluated_count": 0},
                message=f'column "{column}" has no non-missing values',
            )
        minimum = requirement.parameters["minimum"]
        maximum = requirement.parameters["maximum"]
        try:
            failed_count = sum(
                not minimum <= value <= maximum
                for value in values
            )
            observed_minimum = min(values)
            observed_maximum = max(values)
        except TypeError as error:
            return RequirementEvaluation.error(
                expected=requirement.parameters,
                observed={"evaluated_count": len(values)},
                message=f'column "{column}" cannot be compared: {error}',
            )
        passed = failed_count == 0
        result = (
            RequirementEvaluation.passed
            if passed
            else RequirementEvaluation.failed
        )
        return result(
            expected=requirement.parameters,
            observed={
                "evaluated_count": len(values),
                "failed_count": failed_count,
                "minimum": observed_minimum,
                "maximum": observed_maximum,
            },
            message=(
                f'all non-missing values in "{column}" are in range'
                if passed
                else f'{failed_count} values in "{column}" are out of range'
            ),
        )
