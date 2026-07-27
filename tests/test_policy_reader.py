from dataclasses import is_dataclass
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from govlattice import ComparisonOperator
from govlattice import PolicyDesigner
from govlattice import PolicyFileError
from govlattice import PolicyReader
from govlattice import PolicySyntaxError
from govlattice import PolicyValidationError
from govlattice import SeverityLevel
from govlattice import UnsupportedPolicySchemaError


class PolicyReaderTests(unittest.TestCase):
    def _write(self, directory: str, content: str) -> Path:
        path = Path(directory) / "policy.yml"
        path.write_text(content, encoding="utf-8")
        return path

    def test_reads_generated_policy_as_immutable_definition(self) -> None:
        designer = (
            PolicyDesigner(
                "health-policy",
                purpose="Ensure reliable health data.",
                severity=SeverityLevel.HIGH,
                tags=("health",),
                lifecycle_stages=("validation",),
                owner={
                    "team": "data-quality",
                    "reviewers": ["alice", "bob"],
                },
            )
            .state("dataset")
            .require_metric(
                "false_positive_rate",
                0.1,
                operator=ComparisonOperator.LTE,
            )
            .segment("adult")
            .when_between("age", 18, 59)
            .require_column_value(
                "age",
                18,
                operator=ComparisonOperator.GTE,
            )
            .end()
            .end()
        )

        with TemporaryDirectory() as directory:
            path = designer.execute(
                "health_policy.yml",
                output_dir=directory,
            )
            policy = PolicyReader.read(path)

        self.assertEqual(policy.schema_version, "1.6.0")
        self.assertTrue(is_dataclass(policy))
        self.assertFalse(hasattr(policy, "__dict__"))
        self.assertEqual(policy.name, "health-policy")
        self.assertEqual(
            policy.purpose,
            "Ensure reliable health data.",
        )
        self.assertEqual(policy.severity, SeverityLevel.HIGH)
        self.assertEqual(policy.tags, ("health",))
        self.assertEqual(
            policy.metadata["owner"]["reviewers"],
            ("alice", "bob"),
        )

        state = policy.states["dataset"]
        self.assertEqual(state.id, "dataset")
        self.assertEqual(
            state.requirements[0].parameters["operator"],
            ComparisonOperator.LTE,
        )
        segment = state.segments["adult"]
        self.assertEqual(segment.condition.column, "age")
        self.assertEqual(
            segment.requirements[0].parameters["operator"],
            ComparisonOperator.GTE,
        )

        with self.assertRaises(AttributeError):
            policy.name = "changed"  # type: ignore[misc]
        with self.assertRaises(TypeError):
            policy.states["changed"] = state  # type: ignore[index]
        with self.assertRaises(TypeError):
            policy.metadata["owner"]["team"] = "changed"  # type: ignore[index]

    def test_rejects_duplicate_yaml_keys(self) -> None:
        content = (
            'schema_version: "1.6.0"\n'
            'schema_version: "1.6.0"\n'
            "policy: {}\n"
        )

        with TemporaryDirectory() as directory:
            path = self._write(directory, content)
            with self.assertRaisesRegex(
                PolicySyntaxError,
                "duplicate key",
            ):
                PolicyReader.read(path)

    def test_rejects_unsafe_yaml_tags(self) -> None:
        content = (
            'schema_version: "1.6.0"\n'
            "policy: !!python/object/apply:os.system\n"
            '  - "echo unsafe"\n'
        )

        with TemporaryDirectory() as directory:
            path = self._write(directory, content)
            with self.assertRaises(PolicySyntaxError):
                PolicyReader.read(path)

    def test_rejects_unsupported_schema_version(self) -> None:
        content = (
            'schema_version: "1.5.0"\n'
            "policy: {}\n"
        )

        with TemporaryDirectory() as directory:
            path = self._write(directory, content)
            with self.assertRaisesRegex(
                UnsupportedPolicySchemaError,
                "expected '1.6.0'",
            ):
                PolicyReader.read(path)

    def test_rejects_schema_invalid_policy(self) -> None:
        content = (
            'schema_version: "1.6.0"\n'
            "policy:\n"
            '  name: "incomplete-policy"\n'
        )

        with TemporaryDirectory() as directory:
            path = self._write(directory, content)
            with self.assertRaises(PolicyValidationError):
                PolicyReader.read(path)

    def test_rejects_non_object_document(self) -> None:
        with TemporaryDirectory() as directory:
            path = self._write(directory, "- one\n- two\n")
            with self.assertRaisesRegex(
                PolicyValidationError,
                "root must be an object",
            ):
                PolicyReader.read(path)

    def test_validates_file_boundary(self) -> None:
        with self.assertRaises(TypeError):
            PolicyReader.read(123)  # type: ignore[arg-type]
        with self.assertRaises(ValueError):
            PolicyReader.read(" ")
        with self.assertRaises(PolicyFileError):
            PolicyReader.read("missing.yml")

        with TemporaryDirectory() as directory:
            invalid_suffix = Path(directory) / "policy.json"
            invalid_suffix.write_text("{}", encoding="utf-8")
            with self.assertRaises(PolicyFileError):
                PolicyReader.read(invalid_suffix)

            directory_path = Path(directory) / "directory.yml"
            directory_path.mkdir()
            with self.assertRaises(PolicyFileError):
                PolicyReader.read(directory_path)

    def test_rejects_oversized_policy_file(self) -> None:
        with TemporaryDirectory() as directory:
            path = Path(directory) / "large.yml"
            path.write_bytes(b"x" * (PolicyReader.MAX_FILE_BYTES + 1))

            with self.assertRaisesRegex(
                PolicyFileError,
                "exceeds",
            ):
                PolicyReader.read(path)


if __name__ == "__main__":
    unittest.main()
