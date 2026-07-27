"""Generate the policy files used by the Iris examples."""

from pathlib import Path
import sys


SAMPLE_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SAMPLE_DIR.parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from govlattice import PolicyDesigner
from govlattice import SeverityLevel


def define_dataset_policy() -> PolicyDesigner:
    """Define validation rules for Iris feature and label data."""
    return (
        PolicyDesigner(
            "iris-dataset-quality",
            purpose=(
                "Validate Iris feature data before model training "
                "or inference."
            ),
            severity=SeverityLevel.HIGH,
            tags=("iris", "dataset", "quality"),
            lifecycle_stages=("data-validation",),
            owner="data-quality-team",
        )
        .state("validated_dataset")
        .require_columns(
            "sepal_length",
            "sepal_width",
            "petal_length",
            "petal_width",
            "species",
        )
        .require_missing_rate("sepal_length", maximum=0.0)
        .require_missing_rate("sepal_width", maximum=0.0)
        .require_missing_rate("petal_length", maximum=0.0)
        .require_missing_rate("petal_width", maximum=0.0)
        .require_missing_rate("species", maximum=0.0)
        .require_range("sepal_length", minimum=4.0, maximum=9.0)
        .require_range("sepal_width", minimum=1.5, maximum=5.0)
        .require_range("petal_length", minimum=0.5, maximum=7.5)
        .require_range("petal_width", minimum=0.0, maximum=3.0)
        .end()
    )


def define_model_policy() -> PolicyDesigner:
    """Define minimum classification metrics for an Iris model."""
    return (
        PolicyDesigner(
            "iris-model-quality",
            purpose=(
                "Define minimum classification quality for an "
                "Iris model."
            ),
            severity=SeverityLevel.HIGH,
            tags=("iris", "model", "classification"),
            lifecycle_stages=("model-validation",),
            owner="model-quality-team",
        )
        .state("model_evaluation")
        .require_metric("accuracy", 0.90)
        .require_metric("macro_precision", 0.85)
        .require_metric("macro_recall", 0.85)
        .require_metric("macro_f1", 0.85)
        .end()
    )


def generate_policies() -> tuple[Path, Path]:
    """Generate both Iris policies in the sample directory."""
    dataset_path = define_dataset_policy().execute(
        "iris-dataset-quality.yml",
        output_dir=SAMPLE_DIR,
    )
    model_path = define_model_policy().execute(
        "iris-model-quality.yml",
        output_dir=SAMPLE_DIR,
    )
    return dataset_path, model_path


def main() -> None:
    """Generate policies and print their resolved output paths."""
    for path in generate_policies():
        print(path)


if __name__ == "__main__":
    main()
