"""Evaluator for multiple runtime metric minimums."""

from govlattice.evaluator.requirement_evaluation_context import (
    RequirementEvaluationContext,
)
from govlattice.evaluator.requirement_evaluator import (
    RequirementEvaluation,
)
from govlattice.model import RequirementDefinition


class MetricsEvaluator:
    """Check multiple supplied metrics against their minimum thresholds."""

    requirement_type = "require_metrics"

    def evaluate(
        self,
        requirement: RequirementDefinition,
        context: RequirementEvaluationContext,
    ) -> RequirementEvaluation:
        """Evaluate a ``require_metrics`` requirement."""
        thresholds = requirement.parameters["metrics"]
        missing = tuple(
            name for name in thresholds if name not in context.metrics
        )
        if missing:
            return RequirementEvaluation.error(
                expected=requirement.parameters,
                observed={"missing_metrics": missing},
                message=f"metrics were not provided: {', '.join(missing)}",
            )
        try:
            failures = {
                name: {
                    "observed": context.metrics[name],
                    "minimum": minimum,
                }
                for name, minimum in thresholds.items()
                if context.metrics[name] < minimum
            }
        except TypeError as error:
            return RequirementEvaluation.error(
                expected=requirement.parameters,
                observed={
                    "provided_metrics": tuple(context.metrics),
                },
                message=f"metrics cannot be compared: {error}",
            )
        result = (
            RequirementEvaluation.passed
            if not failures
            else RequirementEvaluation.failed
        )
        return result(
            expected=requirement.parameters,
            observed={
                "values": {
                    name: context.metrics[name]
                    for name in thresholds
                },
                "failures": failures,
            },
            message=(
                "all metrics meet their minimum thresholds"
                if not failures
                else (
                    f"{len(failures)} metrics do not meet "
                    "their thresholds"
                )
            ),
        )
