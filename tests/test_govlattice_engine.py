from dataclasses import replace
from pathlib import Path
from tempfile import TemporaryDirectory
from types import MappingProxyType
import unittest

from govlattice import ActorProfile
from govlattice import ActorType
from govlattice import ComparisonOperator
from govlattice import EvaluationContext
from govlattice import EvaluationStatus
from govlattice import ExecutionContext
from govlattice import GovLatticeEngine
from govlattice import PolicyDesigner
from govlattice import PolicyEnforcementError
from govlattice import PolicyReader
from govlattice import RecordsDatasetAdapter
from govlattice import RequirementDefinition
from govlattice import RequirementEvaluation
from govlattice import SeverityLevel
from govlattice import SkipReason
from govlattice import StateDefinition
from govlattice import UnknownPolicyStateError


class _AlwaysPassEvaluator:
    def evaluate(self, requirement, dataset, metrics):
        return RequirementEvaluation(
            status=EvaluationStatus.PASSED,
            expected=requirement.parameters,
            observed={"row_count": dataset.row_count},
            message="custom requirement passed",
        )


class _ContextAwareEvaluator:
    requirement_type = "require_context"

    def evaluate(self, requirement, context):
        return RequirementEvaluation.passed(
            expected=requirement.parameters,
            observed={
                "row_count": context.dataset.row_count,
                "run_id": context.execution.run_id,
            },
            message="context-aware requirement passed",
        )


class _ReplacementEvaluator:
    requirement_type = "require_context"

    def evaluate(self, requirement, context):
        return RequirementEvaluation.failed(
            expected=requirement.parameters,
            observed={},
            message="replacement evaluator failed",
        )


class _CountingFailEvaluator:
    requirement_type = "require_counting"

    def __init__(self):
        self.call_count = 0

    def evaluate(self, requirement, context):
        self.call_count += 1
        return RequirementEvaluation.failed(
            expected=requirement.parameters,
            observed={"row_count": context.dataset.row_count},
            message="counting requirement failed",
        )


class GovLatticeEngineTests(unittest.TestCase):
    def _read_policy(self, designer: PolicyDesigner):
        with TemporaryDirectory() as directory:
            path = designer.execute(
                "policy.yml",
                output_dir=directory,
            )
            return PolicyReader.read(path)

    def _quality_policy(self):
        designer = (
            PolicyDesigner(
                "quality-policy",
                severity=SeverityLevel.HIGH,
            )
            .state("validated_dataset")
            .require_columns("id", "email", "age", "hba1c")
            .require_unique("id", "email")
            .require_missing_rate("hba1c", maximum=0.5)
            .require_range("age", minimum=18, maximum=100)
            .require_metric("recall", 0.8)
            .require_metrics(
                ("precision", "f1_score"),
                (0.75, 0.8),
            )
            .require_column_value(
                "age",
                18,
                operator=ComparisonOperator.GTE,
            )
            .segment("adult")
            .when_between("age", 18, 59)
            .require_missing_rate("hba1c", maximum=0.5)
            .end()
            .segment("senior")
            .when_between("age", 60, 100)
            .require_missing_rate("hba1c", maximum=0.5)
            .end()
            .end()
        )
        return self._read_policy(designer)

    def test_verify_passes_all_builtin_requirements(self) -> None:
        policy = self._quality_policy()
        actor = ActorProfile(
            "user-1842",
            actor_type=ActorType.HUMAN,
            display_name="Logan",
            team="data-quality",
            roles=("reviewer",),
        )
        context = EvaluationContext(
            RecordsDatasetAdapter(
                [
                    {
                        "id": 1,
                        "email": "a@example.com",
                        "age": 30,
                        "hba1c": 5.2,
                    },
                    {
                        "id": 1,
                        "email": "b@example.com",
                        "age": 70,
                        "hba1c": 6.0,
                    },
                ]
            ),
            metrics={
                "recall": 0.9,
                "precision": 0.8,
                "f1_score": 0.85,
            },
            execution=ExecutionContext(
                actor=actor,
                environment="staging",
                run_id="run-001",
                source="unit-test",
            ),
        )

        result = GovLatticeEngine().verify(
            policy,
            state="validated_dataset",
            context=context,
        )

        self.assertEqual(result.status, EvaluationStatus.PASSED)
        self.assertTrue(result.is_compliant)
        self.assertEqual(result.failed_count, 0)
        self.assertGreater(result.passed_count, 7)
        self.assertEqual(
            result.execution.actor.subject_id,
            "user-1842",
        )
        self.assertEqual(result.execution.run_id, "run-001")
        self.assertGreaterEqual(result.duration_ms, 0)
        self.assertTrue(result.started_at.endswith("Z"))

    def test_composite_uniqueness_uses_the_combined_key(self) -> None:
        policy = self._read_policy(
            PolicyDesigner("unique-policy")
            .state("dataset")
            .require_unique("id", "email")
            .end()
        )
        engine = GovLatticeEngine()

        passing = engine.verify(
            policy,
            state="dataset",
            context=EvaluationContext(
                RecordsDatasetAdapter(
                    [
                        {"id": 1, "email": "a@example.com"},
                        {"id": 1, "email": "b@example.com"},
                    ]
                )
            ),
        )
        failing = engine.verify(
            policy,
            state="dataset",
            context=EvaluationContext(
                RecordsDatasetAdapter(
                    [
                        {"id": 1, "email": "a@example.com"},
                        {"id": 1, "email": "a@example.com"},
                    ]
                )
            ),
        )

        self.assertEqual(passing.status, EvaluationStatus.PASSED)
        self.assertEqual(failing.status, EvaluationStatus.FAILED)
        self.assertEqual(
            failing.findings[0].observed["duplicate_count"],
            1,
        )

    def test_verify_reports_failure_without_raising(self) -> None:
        policy = self._read_policy(
            PolicyDesigner("metric-policy")
            .state("evaluation")
            .require_metric("recall", 0.8)
            .end()
        )

        result = GovLatticeEngine().verify(
            policy,
            state="evaluation",
            context=EvaluationContext(
                RecordsDatasetAdapter([{"id": 1}]),
                metrics={"recall": 0.7},
            ),
        )

        self.assertEqual(result.status, EvaluationStatus.FAILED)
        self.assertFalse(result.is_compliant)
        self.assertEqual(result.failed_count, 1)

    def test_missing_metric_and_column_are_errors(self) -> None:
        policy = self._read_policy(
            PolicyDesigner("context-policy")
            .state("evaluation")
            .require_range("age", 18, 100)
            .require_metric("recall", 0.8)
            .end()
        )

        result = GovLatticeEngine().verify(
            policy,
            state="evaluation",
            context=EvaluationContext(
                RecordsDatasetAdapter([{"id": 1}])
            ),
        )

        self.assertEqual(result.status, EvaluationStatus.ERROR)
        self.assertEqual(result.error_count, 2)

    def test_disabled_policy_skips_without_actor(self) -> None:
        policy = self._read_policy(
            PolicyDesigner("disabled-policy", enabled=False)
            .state("dataset")
            .require_columns("id")
            .end()
        )

        result = GovLatticeEngine().verify(
            policy,
            state="dataset",
            context=EvaluationContext(
                RecordsDatasetAdapter([{"id": 1}])
            ),
        )

        self.assertEqual(result.status, EvaluationStatus.SKIPPED)
        self.assertEqual(
            result.skip_reason,
            SkipReason.POLICY_DISABLED,
        )
        self.assertIsNone(result.execution.actor)
        self.assertEqual(result.findings, ())

    def test_empty_state_is_error_and_empty_segment_is_skipped(self) -> None:
        empty_state_policy = self._read_policy(
            PolicyDesigner("empty-state")
            .state("dataset")
            .require_columns("id")
            .end()
        )
        empty_state = GovLatticeEngine().verify(
            empty_state_policy,
            state="dataset",
            context=EvaluationContext(RecordsDatasetAdapter([])),
        )
        self.assertEqual(empty_state.status, EvaluationStatus.ERROR)

        segment_policy = self._read_policy(
            PolicyDesigner("segment-policy")
            .state("dataset")
            .require_columns("age")
            .segment("senior")
            .when_between("age", 60, 100)
            .require_columns("age")
            .end()
            .end()
        )
        segment_result = GovLatticeEngine().verify(
            segment_policy,
            state="dataset",
            context=EvaluationContext(
                RecordsDatasetAdapter([{"age": 30}])
            ),
        )

        self.assertEqual(
            segment_result.status,
            EvaluationStatus.PASSED,
        )
        self.assertEqual(segment_result.skipped_count, 1)
        self.assertEqual(
            segment_result.findings[-1].skip_reason,
            SkipReason.SEGMENT_EMPTY,
        )

    def test_unknown_state_raises_usage_error(self) -> None:
        policy = self._read_policy(
            PolicyDesigner("state-policy").state("dataset").end()
        )

        with self.assertRaises(UnknownPolicyStateError):
            GovLatticeEngine().verify(
                policy,
                state="unknown",
                context=EvaluationContext(
                    RecordsDatasetAdapter([{"id": 1}])
                ),
            )

    def test_custom_evaluator_can_be_registered(self) -> None:
        policy = self._read_policy(
            PolicyDesigner("custom-policy").state("dataset").end()
        )
        custom_requirement = RequirementDefinition(
            type="require_custom",
            parameters=MappingProxyType({"enabled": True}),
        )
        custom_state = StateDefinition(
            id="dataset",
            requirements=(custom_requirement,),
            segments=MappingProxyType({}),
        )
        policy = replace(
            policy,
            states=MappingProxyType({"dataset": custom_state}),
        )
        engine = GovLatticeEngine().register_evaluator(
            "require_custom",
            _AlwaysPassEvaluator(),
        )

        result = engine.verify(
            policy,
            state="dataset",
            context=EvaluationContext(
                RecordsDatasetAdapter([{"id": 1}])
            ),
        )

        self.assertEqual(result.status, EvaluationStatus.PASSED)
        self.assertEqual(
            result.findings[0].message,
            "custom requirement passed",
        )

    def test_context_aware_evaluator_can_be_registered(self) -> None:
        policy = self._read_policy(
            PolicyDesigner("custom-policy").state("dataset").end()
        )
        custom_requirement = RequirementDefinition(
            type="require_context",
            parameters=MappingProxyType({}),
        )
        policy = replace(
            policy,
            states=MappingProxyType(
                {
                    "dataset": StateDefinition(
                        id="dataset",
                        requirements=(custom_requirement,),
                        segments=MappingProxyType({}),
                    )
                }
            ),
        )
        engine = GovLatticeEngine().register_evaluator(
            _ContextAwareEvaluator()
        )

        result = engine.verify(
            policy,
            state="dataset",
            context=EvaluationContext(
                RecordsDatasetAdapter([{"id": 1}]),
                execution=ExecutionContext(run_id="run-context"),
            ),
        )

        self.assertEqual(result.status, EvaluationStatus.PASSED)
        self.assertEqual(
            result.findings[0].observed["run_id"],
            "run-context",
        )

    def test_duplicate_evaluator_requires_explicit_replace(
        self,
    ) -> None:
        engine = GovLatticeEngine().register_evaluator(
            _ContextAwareEvaluator()
        )

        with self.assertRaises(ValueError):
            engine.register_evaluator(_ReplacementEvaluator())

        self.assertIs(
            engine.register_evaluator(
                _ReplacementEvaluator(),
                replace=True,
            ),
            engine,
        )

    def test_declared_requirement_type_must_match_registration(
        self,
    ) -> None:
        with self.assertRaises(ValueError):
            GovLatticeEngine().register_evaluator(
                "require_other",
                _ContextAwareEvaluator(),
            )

    def test_enforce_returns_result_when_policy_passes(self) -> None:
        policy = self._read_policy(
            PolicyDesigner("passing-policy")
            .state("dataset")
            .require_columns("id")
            .end()
        )

        result = GovLatticeEngine().enforce(
            policy,
            state="dataset",
            context=EvaluationContext(
                RecordsDatasetAdapter([{"id": 1}]),
                execution=ExecutionContext(run_id="run-enforce"),
            ),
        )

        self.assertEqual(result.status, EvaluationStatus.PASSED)
        self.assertEqual(result.execution.run_id, "run-enforce")

    def test_enforce_blocks_failed_policy_with_complete_result(
        self,
    ) -> None:
        policy = self._read_policy(
            PolicyDesigner("failing-policy")
            .state("dataset")
            .require_columns("id", "email")
            .end()
        )

        with self.assertRaises(PolicyEnforcementError) as raised:
            GovLatticeEngine().enforce(
                policy,
                state="dataset",
                context=EvaluationContext(
                    RecordsDatasetAdapter([{"id": 1}])
                ),
            )

        error = raised.exception
        self.assertEqual(
            error.result.status,
            EvaluationStatus.FAILED,
        )
        self.assertEqual(error.result.failed_count, 1)
        self.assertEqual(len(error.result.findings), 1)
        self.assertIn("failing-policy", str(error))

    def test_enforce_fails_closed_when_verification_errors(
        self,
    ) -> None:
        policy = self._read_policy(
            PolicyDesigner("error-policy")
            .state("evaluation")
            .require_metric("recall", 0.8)
            .end()
        )

        with self.assertRaises(PolicyEnforcementError) as raised:
            GovLatticeEngine().enforce(
                policy,
                state="evaluation",
                context=EvaluationContext(
                    RecordsDatasetAdapter([{"id": 1}])
                ),
            )

        self.assertEqual(
            raised.exception.result.status,
            EvaluationStatus.ERROR,
        )
        self.assertEqual(raised.exception.result.error_count, 1)

    def test_enforce_allows_disabled_policy_to_skip(self) -> None:
        policy = self._read_policy(
            PolicyDesigner("disabled-policy", enabled=False)
            .state("dataset")
            .require_columns("id")
            .end()
        )

        result = GovLatticeEngine().enforce(
            policy,
            state="dataset",
            context=EvaluationContext(
                RecordsDatasetAdapter([{"id": 1}])
            ),
        )

        self.assertEqual(result.status, EvaluationStatus.SKIPPED)
        self.assertEqual(
            result.skip_reason,
            SkipReason.POLICY_DISABLED,
        )

    def test_enforce_evaluates_each_requirement_once(self) -> None:
        policy = self._read_policy(
            PolicyDesigner("counting-policy").state("dataset").end()
        )
        custom_requirement = RequirementDefinition(
            type="require_counting",
            parameters=MappingProxyType({}),
        )
        policy = replace(
            policy,
            states=MappingProxyType(
                {
                    "dataset": StateDefinition(
                        id="dataset",
                        requirements=(custom_requirement,),
                        segments=MappingProxyType({}),
                    )
                }
            ),
        )
        evaluator = _CountingFailEvaluator()
        engine = GovLatticeEngine().register_evaluator(evaluator)

        with self.assertRaises(PolicyEnforcementError):
            engine.enforce(
                policy,
                state="dataset",
                context=EvaluationContext(
                    RecordsDatasetAdapter([{"id": 1}])
                ),
            )

        self.assertEqual(evaluator.call_count, 1)

    def test_enforce_preserves_unknown_state_usage_error(
        self,
    ) -> None:
        policy = self._read_policy(
            PolicyDesigner("state-policy").state("dataset").end()
        )

        with self.assertRaises(UnknownPolicyStateError):
            GovLatticeEngine().enforce(
                policy,
                state="unknown",
                context=EvaluationContext(
                    RecordsDatasetAdapter([{"id": 1}])
                ),
            )


if __name__ == "__main__":
    unittest.main()
