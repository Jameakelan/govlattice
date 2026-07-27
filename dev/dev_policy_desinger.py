from pathlib import Path
import sys


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from govlattice.designer.policy_designer import PolicyDesigner


def define_single_policy() -> None:
    policy = (
        PolicyDesigner(policy_name="A10-health-policy")
        .state("dataset")
        .require_columns("id", "name")
        .end()
    )
    
    policy.execute("health_policy.yml")

def define_multiple_states_in_policy() -> None:
    policy = (
        PolicyDesigner(
            policy_name="A10-health-policy",
            enabled=True,
            tags=("health", "integration-test"),
            created_at="2026-07-01T09:00:00+07:00",
            updated_at="2026-07-27T17:30:00+07:00",
            agile_stage="testing",
            sprint="sprint-12",
            owner="data-quality-team",
        )
        .state("raw_dataset")
            .require_columns("id", "name", "age", "hba1c")
        .end()
        .state("validated_dataset")
            .segment("adult")
                .when_between("age", minimum=18, maximum=59)
                .require_missing_rate("hba1c", maximum=0.05)
                .require_range("hba1c", minimum=4.0, maximum=14.0)
                .require_metric("recall", 0.8)
                .require_metrics(
                    ("precision", "f1_score"),
                    (0.75, 0.8),
                )
            .end()
            .segment("senior")
                .when_between("age", minimum=60, maximum=100)
                .require_missing_rate("hba1c", maximum=0.02)
                .require_range("hba1c", minimum=4.0, maximum=12.0)
            .end()
            .verify_overlap_range("age")
        .end()
    )
    
    policy.execute("health_policy.yml")

if __name__ == "__main__":
    define_multiple_states_in_policy()
