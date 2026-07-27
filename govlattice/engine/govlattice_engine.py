from datetime import datetime
from datetime import timezone
from time import perf_counter
from typing import Optional
from typing import Any

from govlattice.enum import EvaluationStatus
from govlattice.enum import SkipReason
from govlattice.error import UnknownPolicyStateError
from govlattice.evaluator import EvaluatorRegistry
from govlattice.evaluator import RequirementEvaluator
from govlattice.evaluator import RequirementEvaluationContext
from govlattice.evaluator import create_builtin_registry
from govlattice.model import EvaluationContext
from govlattice.model import PolicyDefinition
from govlattice.model import PolicyEvaluationResult
from govlattice.model import RequirementDefinition
from govlattice.model import RequirementFinding


class GovLatticeEngine:
    __slots__ = ("_registry",)

    def __init__(
        self,
        registry: Optional[EvaluatorRegistry] = None,
    ) -> None:
        if registry is not None and not isinstance(
            registry,
            EvaluatorRegistry,
        ):
            raise TypeError("registry must be an EvaluatorRegistry")
        self._registry = registry or create_builtin_registry()

    def register_evaluator(
        self,
        requirement_type_or_evaluator: Any,
        evaluator: Optional[RequirementEvaluator] = None,
        *,
        replace: bool = False,
    ) -> "GovLatticeEngine":
        self._registry.register(
            requirement_type_or_evaluator,
            evaluator,
            replace=replace,
        )
        return self

    def verify(
        self,
        policy: PolicyDefinition,
        *,
        state: str,
        context: EvaluationContext,
    ) -> PolicyEvaluationResult:
        if not isinstance(policy, PolicyDefinition):
            raise TypeError("policy must be a PolicyDefinition")
        if not isinstance(state, str) or not state.strip():
            raise ValueError("state must be a non-empty string")
        if not isinstance(context, EvaluationContext):
            raise TypeError("context must be an EvaluationContext")

        state_id = state.strip()
        if state_id not in policy.states:
            raise UnknownPolicyStateError(
                f'state "{state_id}" does not exist in '
                f'policy "{policy.name}"'
            )

        started_at = self._timestamp()
        started_clock = perf_counter()
        findings: list[RequirementFinding] = []
        result_skip_reason: Optional[SkipReason] = None

        if not policy.enabled:
            status = EvaluationStatus.SKIPPED
            result_skip_reason = SkipReason.POLICY_DISABLED
        elif context.dataset.row_count == 0:
            findings.append(
                RequirementFinding(
                    policy_id=policy.name,
                    state_id=state_id,
                    segment_name=None,
                    requirement_type="state_dataset",
                    status=EvaluationStatus.ERROR,
                    severity=policy.severity,
                    expected={"minimum_rows": 1},
                    observed={"row_count": 0},
                    message="state dataset contains no rows",
                )
            )
            status = EvaluationStatus.ERROR
        else:
            state_definition = policy.states[state_id]
            evaluation_context = RequirementEvaluationContext(
                dataset=context.dataset,
                metrics=context.metrics,
                execution=context.execution,
            )
            findings.extend(
                self._evaluate_requirements(
                    policy=policy,
                    state_id=state_id,
                    segment_name=None,
                    requirements=state_definition.requirements,
                    context=evaluation_context,
                )
            )
            for segment in state_definition.segments.values():
                try:
                    segment_dataset = context.dataset.filter_between(
                        segment.condition.column,
                        segment.condition.minimum,
                        segment.condition.maximum,
                    )
                except Exception as error:
                    findings.append(
                        RequirementFinding(
                            policy_id=policy.name,
                            state_id=state_id,
                            segment_name=segment.name,
                            requirement_type=(
                                f"condition_{segment.condition.type}"
                            ),
                            status=EvaluationStatus.ERROR,
                            severity=policy.severity,
                            expected={
                                "column": segment.condition.column,
                                "minimum": segment.condition.minimum,
                                "maximum": segment.condition.maximum,
                            },
                            observed={},
                            message=(
                                "could not evaluate segment condition: "
                                f"{error}"
                            ),
                        )
                    )
                    continue

                if segment_dataset.row_count == 0:
                    findings.append(
                        RequirementFinding(
                            policy_id=policy.name,
                            state_id=state_id,
                            segment_name=segment.name,
                            requirement_type="segment",
                            status=EvaluationStatus.SKIPPED,
                            severity=policy.severity,
                            expected={
                                "condition": segment.condition.type,
                                "column": segment.condition.column,
                                "minimum": segment.condition.minimum,
                                "maximum": segment.condition.maximum,
                            },
                            observed={"row_count": 0},
                            message="segment matched no rows",
                            skip_reason=SkipReason.SEGMENT_EMPTY,
                        )
                    )
                    continue

                findings.extend(
                    self._evaluate_requirements(
                        policy=policy,
                        state_id=state_id,
                        segment_name=segment.name,
                        requirements=segment.requirements,
                        context=evaluation_context.with_dataset(
                            segment_dataset
                        ),
                    )
                )

            status = self._aggregate_status(findings)

        completed_at = self._timestamp()
        duration_ms = (perf_counter() - started_clock) * 1000
        return PolicyEvaluationResult(
            policy_id=policy.name,
            state_id=state_id,
            status=status,
            findings=tuple(findings),
            execution=context.execution,
            started_at=started_at,
            completed_at=completed_at,
            duration_ms=duration_ms,
            skip_reason=result_skip_reason,
        )

    def _evaluate_requirements(
        self,
        *,
        policy: PolicyDefinition,
        state_id: str,
        segment_name: Optional[str],
        requirements: tuple[RequirementDefinition, ...],
        context: RequirementEvaluationContext,
    ) -> tuple[RequirementFinding, ...]:
        findings: list[RequirementFinding] = []
        for requirement in requirements:
            evaluator = self._registry.get(requirement.type)
            if evaluator is None:
                findings.append(
                    RequirementFinding(
                        policy_id=policy.name,
                        state_id=state_id,
                        segment_name=segment_name,
                        requirement_type=requirement.type,
                        status=EvaluationStatus.ERROR,
                        severity=policy.severity,
                        expected=requirement.parameters,
                        observed={},
                        message=(
                            "no evaluator is registered for "
                            f'"{requirement.type}"'
                        ),
                    )
                )
                continue

            try:
                evaluation = evaluator.evaluate(
                    requirement,
                    context,
                )
                findings.append(
                    RequirementFinding(
                        policy_id=policy.name,
                        state_id=state_id,
                        segment_name=segment_name,
                        requirement_type=requirement.type,
                        status=evaluation.status,
                        severity=policy.severity,
                        expected=evaluation.expected,
                        observed=evaluation.observed,
                        message=evaluation.message,
                    )
                )
            except Exception as error:
                findings.append(
                    RequirementFinding(
                        policy_id=policy.name,
                        state_id=state_id,
                        segment_name=segment_name,
                        requirement_type=requirement.type,
                        status=EvaluationStatus.ERROR,
                        severity=policy.severity,
                        expected=requirement.parameters,
                        observed={},
                        message=f"evaluator failed: {error}",
                    )
                )
        return tuple(findings)

    @staticmethod
    def _aggregate_status(
        findings: list[RequirementFinding],
    ) -> EvaluationStatus:
        statuses = {finding.status for finding in findings}
        if EvaluationStatus.ERROR in statuses:
            return EvaluationStatus.ERROR
        if EvaluationStatus.FAILED in statuses:
            return EvaluationStatus.FAILED
        if EvaluationStatus.PASSED in statuses or not findings:
            return EvaluationStatus.PASSED
        return EvaluationStatus.SKIPPED

    @staticmethod
    def _timestamp() -> str:
        return (
            datetime.now(timezone.utc)
            .isoformat(timespec="milliseconds")
            .replace("+00:00", "Z")
        )
