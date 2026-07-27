import unittest

try:
    import pandas as pd
except ImportError:
    pd = None

from govlattice import DatasetAdapter
from govlattice import EvaluationContext
from govlattice import EvaluationStatus
from govlattice import GovLatticeEngine
from govlattice import PandasDatasetAdapter
from govlattice import PolicyDesigner
from govlattice import PolicyReader


@unittest.skipIf(pd is None, "pandas is not installed")
class PandasDatasetAdapterTests(unittest.TestCase):
    def test_implements_dataset_adapter_contract(self) -> None:
        adapter = PandasDatasetAdapter(
            pd.DataFrame([{"id": 1, "age": 20}])
        )

        self.assertIsInstance(adapter, DatasetAdapter)
        self.assertEqual(adapter.columns, ("id", "age"))
        self.assertEqual(adapter.row_count, 1)

    def test_copies_dataframe_input(self) -> None:
        dataframe = pd.DataFrame([{"id": 1}])
        adapter = PandasDatasetAdapter(dataframe)

        dataframe.loc[0, "id"] = 99

        self.assertEqual(adapter.values("id"), (1,))

    def test_normalizes_pandas_missing_values(self) -> None:
        adapter = PandasDatasetAdapter(
            pd.DataFrame(
                {
                    "value": [
                        1.0,
                        float("nan"),
                        pd.NA,
                        pd.NaT,
                    ]
                },
                dtype=object,
            )
        )

        self.assertEqual(
            adapter.values("value"),
            (1.0, None, None, None),
        )

    def test_counts_composite_unique_values(self) -> None:
        adapter = PandasDatasetAdapter(
            pd.DataFrame(
                [
                    {"id": 1, "email": "a@example.com"},
                    {"id": 1, "email": "b@example.com"},
                    {"id": 1, "email": "a@example.com"},
                ]
            )
        )

        self.assertEqual(
            adapter.unique_count(("id", "email")),
            2,
        )

    def test_filters_inclusive_range_and_excludes_missing(
        self,
    ) -> None:
        adapter = PandasDatasetAdapter(
            pd.DataFrame(
                {
                    "age": [17.0, 18.0, 30.0, 60.0, None],
                }
            )
        )

        filtered = adapter.filter_between("age", 18, 60)

        self.assertIsInstance(filtered, PandasDatasetAdapter)
        self.assertEqual(
            filtered.values("age"),
            (18.0, 30.0, 60.0),
        )

    def test_rejects_invalid_dataframe_shapes(self) -> None:
        with self.assertRaises(TypeError):
            PandasDatasetAdapter([{"id": 1}])

        with self.assertRaises(TypeError):
            PandasDatasetAdapter(pd.DataFrame([[1]], columns=[1]))

        with self.assertRaises(ValueError):
            PandasDatasetAdapter(
                pd.DataFrame([[1, 2]], columns=["id", "id"])
            )

    def test_engine_evaluates_pandas_dataset(self) -> None:
        designer = (
            PolicyDesigner("pandas-policy")
            .state("dataset")
            .require_columns("id", "age")
            .require_unique("id")
            .require_missing_rate("age", maximum=0.5)
            .require_range("age", minimum=18, maximum=100)
            .end()
        )
        from tempfile import TemporaryDirectory

        with TemporaryDirectory() as directory:
            path = designer.execute(
                "pandas-policy.yml",
                output_dir=directory,
            )
            policy = PolicyReader.read(path)

        result = GovLatticeEngine().verify(
            policy,
            state="dataset",
            context=EvaluationContext(
                PandasDatasetAdapter(
                    pd.DataFrame(
                        [
                            {"id": 1, "age": 20},
                            {"id": 2, "age": 40},
                        ]
                    )
                )
            ),
        )

        self.assertEqual(result.status, EvaluationStatus.PASSED)


if __name__ == "__main__":
    unittest.main()
