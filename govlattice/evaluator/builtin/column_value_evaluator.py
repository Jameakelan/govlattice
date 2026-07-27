from govlattice.evaluator.requirement_evaluation_context import (
    RequirementEvaluationContext,
)
from govlattice.evaluator.requirement_evaluator import (
    RequirementEvaluation,
)
from govlattice.evaluator.support import compare_values
from govlattice.model import RequirementDefinition


class ColumnValueEvaluator:
    requirement_type = "require_column_value"

    def evaluate(
        self,
        requirement: RequirementDefinition,
        context: RequirementEvaluationContext,
    ) -> RequirementEvaluation:
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
        operator = requirement.parameters["operator"]
        expected = requirement.parameters["value"]
        try:
            failed_count = sum(
                not compare_values(value, operator, expected)
                for value in values
            )
        except (TypeError, ValueError) as error:
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
            },
            message=(
                f'all non-missing values in "{column}" pass comparison'
                if passed
                else (
                    f'{failed_count} values in "{column}" '
                    "fail comparison"
                )
            ),
        )
