from pathlib import Path
import sys


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from govlattice.designer.policy_designer import PolicyDesigner


if __name__ == "__main__":
    policy = (
        PolicyDesigner(policy_name="A10-health-policy")
        .state("dataset")
        .require_columns("id", "name")
        .end()
    )
    
    policy.execute("health_policy.yml")
