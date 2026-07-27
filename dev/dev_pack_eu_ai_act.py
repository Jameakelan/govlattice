from pathlib import Path
import sys


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from govlattice import PolicyReference
from govlattice import SeverityLevel
from govlattice.designer.policy_designer import PolicyDesigner
from govlattice.designer.policy_pack_designer import PolicyPackDesigner


EU_AI_ACT_REFERENCE = PolicyReference(
    title="Regulation (EU) 2024/1689 (Artificial Intelligence Act)",
    url="https://eur-lex.europa.eu/eli/reg/2024/1689/oj?locale=en",
)


def define_eu_ai_act_pack() -> PolicyPackDesigner:
    data_governance = (
        PolicyDesigner(
            "data-governance",
            purpose=(
                "Ensure training data meets governance and quality "
                "requirements."
            ),
            severity=SeverityLevel.HIGH,
            tags=("eu-ai-act", "data-quality"),
            lifecycle_stages=("development", "validation"),
            references=(EU_AI_ACT_REFERENCE,),
            owner="data-governance-team",
        )
        .state("training_dataset")
        .require_columns("id", "source", "consent")
        .end()
    )

    human_oversight = (
        PolicyDesigner(
            "human-oversight",
            purpose=(
                "Ensure AI systems provide accountable human "
                "oversight."
            ),
            severity=SeverityLevel.CRITICAL,
            tags=("eu-ai-act", "governance"),
            lifecycle_stages=("deployment", "operation"),
            references=(EU_AI_ACT_REFERENCE,),
            owner="responsible-ai-team",
        )
        .state("ai_system")
        .require_columns("system_id", "oversight_owner")
        .require_metrics(
            ("recall", "precision"),
            (0.8, 0.8),
        )
        .end()
    )

    return (
        PolicyPackDesigner(
            pack_id="eu-ai-act",
            name="EU AI Act",
            version="1.0.0",
            purpose=(
                "Group governance policies supporting EU AI Act "
                "compliance."
            ),
            jurisdiction=("EU",),
            tags=("ai-governance", "regulatory"),
            framework="Regulation (EU) 2024/1689",
        )
        .add_policy(data_governance)
        .add_policy(human_oversight)
        .verify_unique_policy_ids()
        .verify_schema_versions()
        .verify_policy_references()
    )


if __name__ == "__main__":
    define_eu_ai_act_pack().execute("eu-ai-act")
