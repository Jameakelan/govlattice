"""Demonstrate workflow-blocking policy enforcement."""

from pathlib import Path
import sys
from tempfile import TemporaryDirectory


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from govlattice import ActorProfile
from govlattice import EvaluationContext
from govlattice import ExecutionContext
from govlattice import GovLatticeEngine
from govlattice import PolicyDesigner
from govlattice import PolicyEnforcementError
from govlattice import PolicyEvaluationResult
from govlattice import PolicyReader
from govlattice import RecordsDatasetAdapter


def create_context(
    records: list[dict[str, object]],
    *,
    recall: float,
    run_id: str,
) -> EvaluationContext:
    """Create one auditable evaluation context for the example."""
    return EvaluationContext(
        RecordsDatasetAdapter(records),
        metrics={"recall": recall},
        execution=ExecutionContext(
            actor=ActorProfile(
                "developer-001",
                display_name="Local developer",
                team="data-quality",
            ),
            environment="development",
            run_id=run_id,
            source="dev_engine_enforce.py",
        ),
    )


def print_result(
    label: str,
    result: PolicyEvaluationResult,
) -> None:
    """Print an evaluation result and all requirement findings."""
    print(f"{label}: {result.status.value}")
    for finding in result.findings:
        print(
            f"- {finding.requirement_type}: "
            f"{finding.status.value} — {finding.message}"
        )


def main() -> None:
    """Run one allowed workflow and one blocked workflow."""
    designer = (
        PolicyDesigner("engine-enforcement-policy")
        .state("validated_dataset")
        .require_columns("id", "age")
        .require_unique("id")
        .require_range("age", minimum=18, maximum=100)
        .require_metric("recall", 0.8)
        .end()
    )

    with TemporaryDirectory() as directory:
        policy_path = designer.execute(
            "engine-enforcement-policy.yml",
            output_dir=directory,
        )
        policy = PolicyReader.read(policy_path)

    engine = GovLatticeEngine()
    passing_context = create_context(
        [
            {"id": 1, "age": 30},
            {"id": 2, "age": 65},
        ],
        recall=0.9,
        run_id="enforce-passing-run",
    )
    passing_result = engine.enforce(
        policy,
        state="validated_dataset",
        context=passing_context,
    )
    print_result("Workflow allowed", passing_result)

    failing_context = create_context(
        [
            {"id": 1, "age": 17},
            {"id": 1, "age": 65},
        ],
        recall=0.7,
        run_id="enforce-blocked-run",
    )
    try:
        engine.enforce(
            policy,
            state="validated_dataset",
            context=failing_context,
        )
    except PolicyEnforcementError as error:
        print_result("Workflow blocked", error.result)


if __name__ == "__main__":
    main()
