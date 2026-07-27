"""Contracts and immutable outcomes for requirement evaluation."""

from dataclasses import dataclass
from typing import Any
from typing import Mapping
from typing import Protocol
from typing import runtime_checkable

from govlattice.enum import EvaluationStatus
from govlattice.evaluator.requirement_evaluation_context import (
    RequirementEvaluationContext,
)
from govlattice.model import RequirementDefinition
from govlattice.model.immutable import freeze_value


@dataclass(frozen=True, init=False)
class RequirementEvaluation:
    """Describe the outcome produced by one requirement evaluator.

    ``expected`` and ``observed`` are recursively frozen to prevent an audit
    result from changing after evaluation.
    """

    __slots__ = ("status", "expected", "observed", "message")

    status: EvaluationStatus
    expected: Mapping[str, Any]
    observed: Mapping[str, Any]
    message: str

    def __init__(
        self,
        *,
        status: EvaluationStatus,
        expected: Mapping[str, Any],
        observed: Mapping[str, Any],
        message: str,
    ) -> None:
        object.__setattr__(self, "status", status)
        object.__setattr__(
            self,
            "expected",
            freeze_value(dict(expected)),
        )
        object.__setattr__(
            self,
            "observed",
            freeze_value(dict(observed)),
        )
        object.__setattr__(self, "message", message)

    @classmethod
    def passed(
        cls,
        *,
        expected: Mapping[str, Any],
        observed: Mapping[str, Any],
        message: str,
    ) -> "RequirementEvaluation":
        """Create a successful requirement evaluation."""
        return cls(
            status=EvaluationStatus.PASSED,
            expected=expected,
            observed=observed,
            message=message,
        )

    @classmethod
    def failed(
        cls,
        *,
        expected: Mapping[str, Any],
        observed: Mapping[str, Any],
        message: str,
    ) -> "RequirementEvaluation":
        """Create a valid evaluation that did not meet the requirement."""
        return cls(
            status=EvaluationStatus.FAILED,
            expected=expected,
            observed=observed,
            message=message,
        )

    @classmethod
    def error(
        cls,
        *,
        expected: Mapping[str, Any],
        observed: Mapping[str, Any],
        message: str,
    ) -> "RequirementEvaluation":
        """Create an evaluation that could not establish compliance."""
        return cls(
            status=EvaluationStatus.ERROR,
            expected=expected,
            observed=observed,
            message=message,
        )

    @classmethod
    def skipped(
        cls,
        *,
        expected: Mapping[str, Any],
        observed: Mapping[str, Any],
        message: str,
    ) -> "RequirementEvaluation":
        """Create an evaluation intentionally excluded from execution."""
        return cls(
            status=EvaluationStatus.SKIPPED,
            expected=expected,
            observed=observed,
            message=message,
        )


@runtime_checkable
class RequirementEvaluator(Protocol):
    """Protocol implemented by built-in and custom requirement evaluators.

    Implementations declare a unique ``requirement_type`` and must return a
    :class:`RequirementEvaluation` without mutating the supplied context.
    """

    requirement_type: str

    def evaluate(
        self,
        requirement: RequirementDefinition,
        context: RequirementEvaluationContext,
    ) -> RequirementEvaluation:
        """Evaluate one requirement against its scoped runtime context."""
        ...
