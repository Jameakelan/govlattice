from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from govlattice import EvaluationContext
from govlattice import EvaluationStatus
from govlattice import ExecutionContext
from govlattice import GovLatticeEngine
from govlattice import PolicyDesigner
from govlattice import PolicyReader
from govlattice import RecordsDatasetAdapter


class HtmlReportTests(unittest.TestCase):
    def _result(self):
        with TemporaryDirectory() as directory:
            policy_path = (
                PolicyDesigner("html-report-policy")
                .state("dataset")
                .require_columns("id", "email")
                .end()
                .execute("policy.yml", output_dir=directory)
            )
            policy = PolicyReader.read(policy_path)

        return GovLatticeEngine().verify(
            policy,
            state="dataset",
            context=EvaluationContext(
                RecordsDatasetAdapter([{"id": 1}]),
                execution=ExecutionContext(
                    environment="test",
                    run_id="report-001",
                    source="<script>alert(1)</script>",
                ),
            ),
        )

    def test_to_html_renders_summary_and_escapes_content(self) -> None:
        result = self._result()

        html = result.to_html()

        self.assertIn("<!doctype html>", html)
        self.assertIn("html-report-policy", html)
        self.assertIn("require_columns", html)
        self.assertIn("report-001", html)
        self.assertIn("missing required columns: email", html)
        self.assertIn(
            "&lt;script&gt;alert(1)&lt;/script&gt;",
            html,
        )
        self.assertNotIn("<script>alert(1)</script>", html)
        self.assertEqual(result.status, EvaluationStatus.FAILED)

    def test_write_html_creates_nested_directory(self) -> None:
        result = self._result()

        with TemporaryDirectory() as directory:
            output = Path(directory) / "output" / "report.html"
            written = result.write_html(output)

            self.assertEqual(written, output.resolve())
            self.assertTrue(written.is_file())
            self.assertEqual(
                written.read_text(encoding="utf-8"),
                result.to_html(),
            )

    def test_write_html_validates_output_path(self) -> None:
        result = self._result()

        with self.assertRaises(TypeError):
            result.write_html(123)
        with self.assertRaises(ValueError):
            result.write_html("")
        with self.assertRaises(ValueError):
            result.write_html("report.txt")


if __name__ == "__main__":
    unittest.main()
