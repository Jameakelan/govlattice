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
        return cls(
            status=EvaluationStatus.SKIPPED,
            expected=expected,
            observed=observed,
            message=message,
        )


@runtime_checkable
class RequirementEvaluator(Protocol):
    requirement_type: str

    def evaluate(
        self,
        requirement: RequirementDefinition,
        context: RequirementEvaluationContext,
    ) -> RequirementEvaluation:
        ...
