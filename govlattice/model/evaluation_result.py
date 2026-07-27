from dataclasses import dataclass
from typing import Any
from typing import Mapping
from typing import Optional

from govlattice.enum import EvaluationStatus
from govlattice.enum import SeverityLevel
from govlattice.enum import SkipReason
from govlattice.model.execution_context import ExecutionContext
from govlattice.model.immutable import freeze_value


@dataclass(frozen=True, init=False)
class RequirementFinding:
    __slots__ = (
        "policy_id",
        "state_id",
        "segment_name",
        "requirement_type",
        "status",
        "severity",
        "expected",
        "observed",
        "message",
        "skip_reason",
    )

    policy_id: str
    state_id: str
    segment_name: Optional[str]
    requirement_type: str
    status: EvaluationStatus
    severity: SeverityLevel
    expected: Mapping[str, Any]
    observed: Mapping[str, Any]
    message: str
    skip_reason: Optional[SkipReason]

    def __init__(
        self,
        *,
        policy_id: str,
        state_id: str,
        segment_name: Optional[str],
        requirement_type: str,
        status: EvaluationStatus,
        severity: SeverityLevel,
        expected: Mapping[str, Any],
        observed: Mapping[str, Any],
        message: str,
        skip_reason: Optional[SkipReason] = None,
    ) -> None:
        object.__setattr__(self, "policy_id", policy_id)
        object.__setattr__(self, "state_id", state_id)
        object.__setattr__(self, "segment_name", segment_name)
        object.__setattr__(
            self,
            "requirement_type",
            requirement_type,
        )
        object.__setattr__(self, "status", status)
        object.__setattr__(self, "severity", severity)
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
        object.__setattr__(self, "skip_reason", skip_reason)


@dataclass(frozen=True)
class PolicyEvaluationResult:
    __slots__ = (
        "policy_id",
        "state_id",
        "status",
        "findings",
        "execution",
        "started_at",
        "completed_at",
        "duration_ms",
        "skip_reason",
    )

    policy_id: str
    state_id: str
    status: EvaluationStatus
    findings: tuple[RequirementFinding, ...]
    execution: ExecutionContext
    started_at: str
    completed_at: str
    duration_ms: float
    skip_reason: Optional[SkipReason]

    @property
    def passed_count(self) -> int:
        return self._count(EvaluationStatus.PASSED)

    @property
    def failed_count(self) -> int:
        return self._count(EvaluationStatus.FAILED)

    @property
    def skipped_count(self) -> int:
        return self._count(EvaluationStatus.SKIPPED)

    @property
    def error_count(self) -> int:
        return self._count(EvaluationStatus.ERROR)

    @property
    def is_compliant(self) -> bool:
        return self.status in {
            EvaluationStatus.PASSED,
            EvaluationStatus.SKIPPED,
        }

    def _count(self, status: EvaluationStatus) -> int:
        return sum(
            finding.status is status
            for finding in self.findings
        )
