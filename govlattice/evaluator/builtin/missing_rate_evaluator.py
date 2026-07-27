"""Evaluator for maximum column missing-rate requirements."""

from govlattice.evaluator.requirement_evaluation_context import (
    RequirementEvaluationContext,
)
from govlattice.evaluator.requirement_evaluator import (
    RequirementEvaluation,
)
from govlattice.model import RequirementDefinition


class MissingRateEvaluator:
    """Check that a column's missing-value rate is within its maximum."""

    requirement_type = "require_missing_rate"

    def evaluate(
        self,
        requirement: RequirementDefinition,
        context: RequirementEvaluationContext,
    ) -> RequirementEvaluation:
        """Evaluate a ``require_missing_rate`` requirement."""
        column = requirement.parameters["column"]
        if column not in context.dataset.columns:
            return RequirementEvaluation.error(
                expected=requirement.parameters,
                observed={"missing_column": column},
                message=f'column "{column}" does not exist',
            )
        values = context.dataset.values(column)
        missing_count = sum(value is None for value in values)
        rate = missing_count / context.dataset.row_count
        maximum = requirement.parameters["maximum"]
        passed = rate <= maximum
        result = (
            RequirementEvaluation.passed
            if passed
            else RequirementEvaluation.failed
        )
        return result(
            expected=requirement.parameters,
            observed={
                "missing_count": missing_count,
                "row_count": context.dataset.row_count,
                "missing_rate": rate,
            },
            message=(
                f'missing rate for "{column}" is within the maximum'
                if passed
                else (
                    f'missing rate for "{column}" exceeds the maximum'
                )
            ),
        )
