"""Train an Iris classifier and enforce its data and model policies."""

from pathlib import Path
import sys
from typing import Mapping


SAMPLE_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SAMPLE_DIR.parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import pandas as pd
from sklearn.datasets import load_iris
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score
from sklearn.metrics import f1_score
from sklearn.metrics import precision_score
from sklearn.metrics import recall_score
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

from govlattice import ActorProfile
from govlattice import EvaluationContext
from govlattice import ExecutionContext
from govlattice import GovLatticeEngine
from govlattice import PandasDatasetAdapter
from govlattice import PolicyEnforcementError
from govlattice import PolicyEvaluationResult
from govlattice import PolicyReader


FEATURE_COLUMNS = (
    "sepal_length",
    "sepal_width",
    "petal_length",
    "petal_width",
)
DATASET_POLICY_PATH = SAMPLE_DIR / "iris-dataset-quality.yml"
MODEL_POLICY_PATH = SAMPLE_DIR / "iris-model-quality.yml"


def load_dataset() -> pd.DataFrame:
    """Load sklearn Iris data with policy-compatible column names."""
    bunch = load_iris(as_frame=True)
    dataframe = bunch.data.copy()
    dataframe.columns = list(FEATURE_COLUMNS)
    species_by_target = {
        target: species
        for target, species in enumerate(bunch.target_names)
    }
    dataframe["species"] = bunch.target.map(species_by_target)
    return dataframe


def create_execution_context(run_id: str) -> ExecutionContext:
    """Create consistent provenance for one sample engine execution."""
    return ExecutionContext(
        actor=ActorProfile(
            "iris-sample",
            display_name="Iris sklearn sample",
            team="model-quality",
        ),
        environment="sample",
        run_id=run_id,
        source="samples/iris/run_policy_engine.py",
    )


def train_and_measure(
    dataframe: pd.DataFrame,
) -> tuple[pd.DataFrame, Mapping[str, float]]:
    """Train a deterministic classifier and return test data and metrics."""
    features = dataframe.loc[:, list(FEATURE_COLUMNS)]
    target = dataframe["species"]
    train_features, test_features, train_target, test_target = (
        train_test_split(
            features,
            target,
            test_size=0.2,
            random_state=42,
            stratify=target,
        )
    )
    model = Pipeline(
        [
            ("scale", StandardScaler()),
            (
                "classifier",
                LogisticRegression(
                    max_iter=500,
                    random_state=42,
                ),
            ),
        ]
    )
    model.fit(train_features, train_target)
    predictions = model.predict(test_features)

    metrics = {
        "accuracy": float(
            accuracy_score(test_target, predictions)
        ),
        "macro_precision": float(
            precision_score(
                test_target,
                predictions,
                average="macro",
                zero_division=0,
            )
        ),
        "macro_recall": float(
            recall_score(
                test_target,
                predictions,
                average="macro",
                zero_division=0,
            )
        ),
        "macro_f1": float(
            f1_score(
                test_target,
                predictions,
                average="macro",
                zero_division=0,
            )
        ),
    }
    evaluated_data = test_features.copy()
    evaluated_data["species"] = test_target
    return evaluated_data, metrics


def run() -> tuple[
    PolicyEvaluationResult,
    PolicyEvaluationResult,
    Mapping[str, float],
]:
    """Enforce the Iris dataset policy, train, then enforce model quality."""
    dataframe = load_dataset()
    engine = GovLatticeEngine()

    dataset_policy = PolicyReader.read(DATASET_POLICY_PATH)
    dataset_result = engine.enforce(
        dataset_policy,
        state="validated_dataset",
        context=EvaluationContext(
            PandasDatasetAdapter(dataframe),
            execution=create_execution_context(
                "iris-dataset-validation"
            ),
        ),
    )

    evaluated_data, metrics = train_and_measure(dataframe)
    model_policy = PolicyReader.read(MODEL_POLICY_PATH)
    model_result = engine.enforce(
        model_policy,
        state="model_evaluation",
        context=EvaluationContext(
            PandasDatasetAdapter(evaluated_data),
            metrics=metrics,
            execution=create_execution_context(
                "iris-model-validation"
            ),
        ),
    )
    return dataset_result, model_result, metrics


def print_result(
    label: str,
    result: PolicyEvaluationResult,
) -> None:
    """Print one policy result and all findings."""
    print(f"{label}: {result.status.value}")
    for finding in result.findings:
        print(
            f"- {finding.requirement_type}: "
            f"{finding.status.value} — {finding.message}"
        )


def main() -> None:
    """Run the end-to-end sample and display enforcement evidence."""
    try:
        dataset_result, model_result, metrics = run()
    except PolicyEnforcementError as error:
        print_result("Workflow blocked", error.result)
        raise

    print_result("Dataset policy", dataset_result)
    print("Model metrics:")
    for name, value in metrics.items():
        print(f"- {name}: {value:.4f}")
    print_result("Model policy", model_result)
    print("Workflow allowed: all active policies passed")


if __name__ == "__main__":
    main()
