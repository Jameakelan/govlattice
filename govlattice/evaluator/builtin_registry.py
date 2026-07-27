from govlattice.evaluator.builtin import ColumnValueEvaluator
from govlattice.evaluator.builtin import MetricEvaluator
from govlattice.evaluator.builtin import MetricsEvaluator
from govlattice.evaluator.builtin import MissingRateEvaluator
from govlattice.evaluator.builtin import RangeEvaluator
from govlattice.evaluator.builtin import RequiredColumnsEvaluator
from govlattice.evaluator.builtin import UniqueColumnsEvaluator
from govlattice.evaluator.evaluator_registry import EvaluatorRegistry


BUILTIN_EVALUATORS = (
    RequiredColumnsEvaluator(),
    UniqueColumnsEvaluator(),
    MissingRateEvaluator(),
    RangeEvaluator(),
    MetricEvaluator(),
    MetricsEvaluator(),
    ColumnValueEvaluator(),
)


def create_builtin_registry() -> EvaluatorRegistry:
    registry = EvaluatorRegistry()
    for evaluator in BUILTIN_EVALUATORS:
        registry.register(evaluator)
    return registry
