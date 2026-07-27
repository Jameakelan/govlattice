from pathlib import Path
import sys


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from govlattice import PolicyReader


if __name__ == "__main__":
    policy = PolicyReader.read(
        PROJECT_ROOT / "policies" / "health_policy.yml"
    )
    print(f"Policy: {policy.name}")
    print(f"Purpose: {policy.purpose}")
    print(f"States: {', '.join(policy.states)}")
