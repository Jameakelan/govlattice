from pathlib import Path
import sys


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from govlattice import PolicyPackReader


if __name__ == "__main__":
    pack = PolicyPackReader.read(
        PROJECT_ROOT
        / "policies"
        / "eu-ai-act"
        / "manifest.yml"
    )
    print(f"Pack: {pack.name} ({pack.version})")
    print(f"Purpose: {pack.purpose}")
    print(f"Policies: {', '.join(pack.policies)}")
