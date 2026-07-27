"""Registration and lookup for requirement evaluator implementations."""

from typing import Any
from typing import Optional

from govlattice.evaluator.requirement_evaluation_context import (
    RequirementEvaluationContext,
)
from govlattice.evaluator.requirement_evaluator import (
    RequirementEvaluation,
)
from govlattice.evaluator.requirement_evaluator import (
    RequirementEvaluator,
)
from govlattice.model import RequirementDefinition


class _LegacyEvaluatorAdapter:
    """Adapt the former three-argument evaluator API to the context API."""

    __slots__ = ("requirement_type", "_evaluator")

    def __init__(self, requirement_type: str, evaluator: Any) -> None:
        self.requirement_type = requirement_type
        self._evaluator = evaluator

    def evaluate(
        self,
        requirement: RequirementDefinition,
        context: RequirementEvaluationContext,
    ) -> RequirementEvaluation:
        return self._evaluator.evaluate(
            requirement,
            context.dataset,
            context.metrics,
        )


class EvaluatorRegistry:
    """Map requirement type identifiers to evaluator implementations.

    Duplicate registration is rejected by default so built-in behavior cannot
    be replaced accidentally.
    """

    __slots__ = ("_evaluators",)

    def __init__(self) -> None:
        self._evaluators: dict[str, RequirementEvaluator] = {}

    def register(
        self,
        requirement_type_or_evaluator: Any,
        evaluator: Optional[Any] = None,
        *,
        replace: bool = False,
    ) -> "EvaluatorRegistry":
        """Register an evaluator.

        Args:
            requirement_type_or_evaluator: An evaluator declaring
                ``requirement_type``, or an explicit type string when using
                the legacy two-argument registration form.
            evaluator: Optional legacy or explicitly named evaluator.
            replace: Permit intentional replacement of an existing type.

        Returns:
            This registry for fluent configuration.

        Raises:
            ValueError: If the type is invalid, mismatched, or already used.
            TypeError: If the object does not implement the evaluator
                protocol.
        """
        if evaluator is None:
            candidate = requirement_type_or_evaluator
            requirement_type = getattr(
                candidate,
                "requirement_type",
                None,
            )
            registered_evaluator = candidate
        else:
            requirement_type = requirement_type_or_evaluator
            declared_type = getattr(
                evaluator,
                "requirement_type",
                None,
            )
            if (
                declared_type is not None
                and declared_type != requirement_type
            ):
                raise ValueError(
                    "requirement_type does not match evaluator."
                    "requirement_type"
                )
            registered_evaluator = (
                evaluator
                if declared_type is not None
                else _LegacyEvaluatorAdapter(
                    requirement_type,
                    evaluator,
                )
            )

        if (
            not isinstance(requirement_type, str)
            or not requirement_type.strip()
        ):
            raise ValueError(
                "requirement_type must be a non-empty string"
            )
        requirement_type = requirement_type.strip()
        if not isinstance(registered_evaluator, RequirementEvaluator):
            raise TypeError(
                "evaluator must implement RequirementEvaluator"
            )
        if requirement_type in self._evaluators and not replace:
            raise ValueError(
                f'an evaluator for "{requirement_type}" is '
                "already registered"
            )
        self._evaluators[requirement_type] = registered_evaluator
        return self

    def get(
        self,
        requirement_type: str,
    ) -> Optional[RequirementEvaluator]:
        """Return the evaluator for a requirement type, if registered."""
        return self._evaluators.get(requirement_type)
