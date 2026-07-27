"""Verify a policy against a pandas DataFrame."""

from tempfile import TemporaryDirectory

import pandas as pd

from govlattice import EvaluationContext
from govlattice import GovLatticeEngine
from govlattice import PandasDatasetAdapter
from govlattice import PolicyDesigner
from govlattice import PolicyReader


def main() -> None:
    """Build a policy and verify a DataFrame with the Pandas adapter."""
    designer = (
        PolicyDesigner("pandas-health-policy")
        .state("dataset")
        .require_columns("patient_id", "age", "hba1c")
        .require_unique("patient_id")
        .require_missing_rate("hba1c", maximum=0.05)
        .require_range("age", minimum=18, maximum=100)
        .end()
    )

    dataframe = pd.DataFrame(
        [
            {"patient_id": 1, "age": 32, "hba1c": 5.4},
            {"patient_id": 2, "age": 68, "hba1c": 6.1},
        ]
    )

    with TemporaryDirectory() as directory:
        policy_path = designer.execute(
            "pandas-health-policy.yml",
            output_dir=directory,
        )
        policy = PolicyReader.read(policy_path)

    result = GovLatticeEngine().verify(
        policy,
        state="dataset",
        context=EvaluationContext(
            PandasDatasetAdapter(dataframe)
        ),
    )

    print(result.status.value)
    for finding in result.findings:
        print(finding.requirement_type, finding.status.value)


if __name__ == "__main__":
    main()
