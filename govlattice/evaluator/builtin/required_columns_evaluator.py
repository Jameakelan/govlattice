"""Evaluator for mandatory dataset columns."""

from govlattice.evaluator.requirement_evaluation_context import (
    RequirementEvaluationContext,
)
from govlattice.evaluator.requirement_evaluator import (
    RequirementEvaluation,
)
from govlattice.evaluator.support import missing_columns
from govlattice.model import RequirementDefinition


class RequiredColumnsEvaluator:
    """Check that every column named by a requirement is available."""

    requirement_type = "require_columns"

    def evaluate(
        self,
        requirement: RequirementDefinition,
        context: RequirementEvaluationContext,
    ) -> RequirementEvaluation:
        """Evaluate a ``require_columns`` requirement."""
        columns = tuple(requirement.parameters["columns"])
        missing = missing_columns(context.dataset, columns)
        result = (
            RequirementEvaluation.passed
            if not missing
            else RequirementEvaluation.failed
        )
        return result(
            expected=requirement.parameters,
            observed={
                "available_columns": context.dataset.columns,
                "missing_columns": missing,
            },
            message=(
                "all required columns are available"
                if not missing
                else f"missing required columns: {', '.join(missing)}"
            ),
        )
