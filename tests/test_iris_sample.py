import unittest

try:
    import sklearn
except ImportError:
    sklearn = None


@unittest.skipIf(sklearn is None, "scikit-learn is not installed")
class IrisPolicyEngineSampleTests(unittest.TestCase):
    def test_end_to_end_policy_engine_passes(self) -> None:
        from samples.iris.run_policy_engine import run

        dataset_result, model_result, metrics = run()

        self.assertTrue(dataset_result.is_compliant)
        self.assertTrue(model_result.is_compliant)
        self.assertGreaterEqual(metrics["accuracy"], 0.90)
        self.assertGreaterEqual(metrics["macro_precision"], 0.85)
        self.assertGreaterEqual(metrics["macro_recall"], 0.85)
        self.assertGreaterEqual(metrics["macro_f1"], 0.85)


if __name__ == "__main__":
    unittest.main()
