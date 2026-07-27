from pathlib import Path
import sys


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from govlattice import ActorProfile
from govlattice import EvaluationContext
from govlattice import ExecutionContext
from govlattice import GovLatticeEngine
from govlattice import PolicyReader
from govlattice import RecordsDatasetAdapter


if __name__ == "__main__":
    policy = PolicyReader.read(
        PROJECT_ROOT / "policies" / "health_policy.yml"
    )
    context = EvaluationContext(
        RecordsDatasetAdapter(
            [
                {
                    "id": 1,
                    "name": "Alice",
                    "age": 30,
                    "hba1c": 5.4,
                },
                {
                    "id": 2,
                    "name": "Bob",
                    "age": 65,
                    "hba1c": 6.1,
                },
            ]
        ),
        metrics={
            "recall": 0.9,
            "precision": 0.85,
            "f1_score": 0.87,
            "false_positive_rate": 0.08,
        },
        execution=ExecutionContext(
            actor=ActorProfile(
                "developer-001",
                display_name="Local developer",
                team="data-quality",
            ),
            environment="development",
            run_id="local-engine-review",
            source="dev_engine_verify.py",
        ),
    )

    result = GovLatticeEngine().verify(
        policy,
        state="validated_dataset",
        context=context,
    )

    print(f"Status: {result.status.value}")
    for finding in result.findings:
        print(
            f"- {finding.requirement_type}: "
            f"{finding.status.value} — {finding.message}"
        )
