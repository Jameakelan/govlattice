from dataclasses import dataclass
from typing import Any
from typing import Mapping

from govlattice.adapter import DatasetAdapter
from govlattice.model import ExecutionContext
from govlattice.model.immutable import freeze_value


@dataclass(frozen=True, init=False)
class RequirementEvaluationContext:
    __slots__ = ("dataset", "metrics", "execution")

    dataset: DatasetAdapter
    metrics: Mapping[str, Any]
    execution: ExecutionContext

    def __init__(
        self,
        *,
        dataset: DatasetAdapter,
        metrics: Mapping[str, Any],
        execution: ExecutionContext,
    ) -> None:
        if not isinstance(dataset, DatasetAdapter):
            raise TypeError("dataset must implement DatasetAdapter")
        if not isinstance(metrics, Mapping):
            raise TypeError("metrics must be a mapping")
        if not isinstance(execution, ExecutionContext):
            raise TypeError("execution must be an ExecutionContext")
        object.__setattr__(self, "dataset", dataset)
        object.__setattr__(
            self,
            "metrics",
            freeze_value(dict(metrics)),
        )
        object.__setattr__(self, "execution", execution)

    def with_dataset(
        self,
        dataset: DatasetAdapter,
    ) -> "RequirementEvaluationContext":
        return RequirementEvaluationContext(
            dataset=dataset,
            metrics=self.metrics,
            execution=self.execution,
        )
