"""Top-level runtime input supplied to the policy engine."""

from dataclasses import dataclass
from typing import Any
from typing import Mapping
from typing import Optional

from govlattice.adapter.dataset_adapter import DatasetAdapter
from govlattice.model.execution_context import ExecutionContext
from govlattice.model.immutable import freeze_value


@dataclass(frozen=True, init=False)
class EvaluationContext:
    """Bundle dataset inputs, runtime metrics, and execution provenance.

    Metrics are recursively frozen and an empty :class:`ExecutionContext` is
    created when provenance is not supplied.
    """
    __slots__ = ("dataset", "metrics", "execution")

    dataset: DatasetAdapter
    metrics: Mapping[str, Any]
    execution: ExecutionContext

    def __init__(
        self,
        dataset: DatasetAdapter,
        *,
        metrics: Optional[Mapping[str, Any]] = None,
        execution: Optional[ExecutionContext] = None,
    ) -> None:
        if not isinstance(dataset, DatasetAdapter):
            raise TypeError("dataset must implement DatasetAdapter")
        if metrics is not None and not isinstance(metrics, Mapping):
            raise TypeError("metrics must be a mapping")
        if execution is not None and not isinstance(
            execution,
            ExecutionContext,
        ):
            raise TypeError("execution must be an ExecutionContext")

        object.__setattr__(self, "dataset", dataset)
        object.__setattr__(
            self,
            "metrics",
            freeze_value(dict(metrics or {})),
        )
        object.__setattr__(
            self,
            "execution",
            execution or ExecutionContext(),
        )
