from govlattice.adapter import DatasetAdapter


def missing_columns(
    dataset: DatasetAdapter,
    columns: tuple[str, ...],
) -> tuple[str, ...]:
    return tuple(
        column
        for column in columns
        if column not in dataset.columns
    )
