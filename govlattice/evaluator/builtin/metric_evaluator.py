from govlattice.evaluator.requirement_evaluation_context import (
    RequirementEvaluationContext,
)
from govlattice.evaluator.requirement_evaluator import (
    RequirementEvaluation,
)
from govlattice.evaluator.support import compare_values
from govlattice.model import RequirementDefinition


class MetricEvaluator:
    requirement_type = "require_metric"

    def evaluate(
        self,
        requirement: RequirementDefinition,
        context: RequirementEvaluationContext,
    ) -> RequirementEvaluation:
        metric = requirement.parameters["metric"]
        if metric not in context.metrics:
            return RequirementEvaluation.error(
                expected=requirement.parameters,
                observed={"missing_metric": metric},
                message=f'metric "{metric}" was not provided',
            )
        observed = context.metrics[metric]
        operator = requirement.parameters["operator"]
        expected = requirement.parameters["value"]
        try:
            passed = compare_values(observed, operator, expected)
        except (TypeError, ValueError) as error:
            return RequirementEvaluation.error(
                expected=requirement.parameters,
                observed={"value": observed},
                message=f'metric "{metric}" cannot be compared: {error}',
            )
        result = (
            RequirementEvaluation.passed
            if passed
            else RequirementEvaluation.failed
        )
        return result(
            expected=requirement.parameters,
            observed={"metric": metric, "value": observed},
            message=(
                f'metric "{metric}" meets its threshold'
                if passed
                else f'metric "{metric}" does not meet its threshold'
            ),
        )
