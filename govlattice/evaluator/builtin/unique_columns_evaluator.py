from govlattice.evaluator.requirement_evaluation_context import (
    RequirementEvaluationContext,
)
from govlattice.evaluator.requirement_evaluator import (
    RequirementEvaluation,
)
from govlattice.evaluator.support import missing_columns
from govlattice.model import RequirementDefinition


class UniqueColumnsEvaluator:
    requirement_type = "require_unique"

    def evaluate(
        self,
        requirement: RequirementDefinition,
        context: RequirementEvaluationContext,
    ) -> RequirementEvaluation:
        columns = tuple(requirement.parameters["columns"])
        missing = missing_columns(context.dataset, columns)
        if missing:
            return RequirementEvaluation.error(
                expected=requirement.parameters,
                observed={"missing_columns": missing},
                message=(
                    "cannot check uniqueness; missing columns: "
                    f"{', '.join(missing)}"
                ),
            )
        try:
            unique_count = context.dataset.unique_count(columns)
        except (TypeError, ValueError) as error:
            return RequirementEvaluation.error(
                expected=requirement.parameters,
                observed={"columns": columns},
                message=(
                    "could not evaluate composite uniqueness: "
                    f"{error}"
                ),
            )
        duplicate_count = context.dataset.row_count - unique_count
        result = (
            RequirementEvaluation.passed
            if duplicate_count == 0
            else RequirementEvaluation.failed
        )
        return result(
            expected=requirement.parameters,
            observed={
                "row_count": context.dataset.row_count,
                "unique_count": unique_count,
                "duplicate_count": duplicate_count,
                "composite_columns": columns,
            },
            message=(
                "composite values are unique"
                if duplicate_count == 0
                else (
                    f"found {duplicate_count} duplicate "
                    "composite values"
                )
            ),
        )
