"""Column-related helpers shared by dataset requirement evaluators."""

from govlattice.adapter import DatasetAdapter


def missing_columns(
    dataset: DatasetAdapter,
    columns: tuple[str, ...],
) -> tuple[str, ...]:
    """Return requested column names that are absent from a dataset."""
    return tuple(
        column
        for column in columns
        if column not in dataset.columns
    )
