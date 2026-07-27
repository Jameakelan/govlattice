from dataclasses import is_dataclass
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from govlattice import PolicyDesigner
from govlattice import PolicyPackConsistencyError
from govlattice import PolicyPackDesigner
from govlattice import PolicyPackFileError
from govlattice import PolicyPackReadError
from govlattice import PolicyPackReader
from govlattice import PolicyPackValidationError
from govlattice import SeverityLevel
from govlattice import UnsupportedPolicyPackSchemaError


class PolicyPackReaderTests(unittest.TestCase):
    def _create_pack(self, directory: str) -> Path:
        data_policy = (
            PolicyDesigner(
                "data-governance",
                purpose="Ensure governed training data.",
                severity=SeverityLevel.HIGH,
            )
            .state("training_dataset")
            .require_columns("id", "source")
            .end()
        )
        oversight_policy = (
            PolicyDesigner(
                "human-oversight",
                severity=SeverityLevel.CRITICAL,
            )
            .state("ai_system")
            .require_columns("system_id", "owner")
            .end()
        )
        pack = (
            PolicyPackDesigner(
                "eu-ai-act",
                "EU AI Act",
                "1.0.0",
                purpose="Group EU AI Act policies.",
                jurisdiction=("EU",),
                framework="Regulation (EU) 2024/1689",
            )
            .add_policy(data_policy)
            .add_policy(oversight_policy)
        )
        return pack.execute("eu-ai-act", output_dir=directory)

    def test_reads_pack_and_all_policies_eagerly(self) -> None:
        with TemporaryDirectory() as directory:
            manifest = self._create_pack(directory)
            pack = PolicyPackReader.read(manifest)

        self.assertTrue(is_dataclass(pack))
        self.assertFalse(hasattr(pack, "__dict__"))
        self.assertEqual(pack.pack_schema_version, "1.2.0")
        self.assertEqual(pack.id, "eu-ai-act")
        self.assertEqual(pack.purpose, "Group EU AI Act policies.")
        self.assertEqual(pack.jurisdiction, ("EU",))
        self.assertEqual(
            pack.metadata["framework"],
            "Regulation (EU) 2024/1689",
        )
        self.assertEqual(
            tuple(pack.policies),
            ("data-governance", "human-oversight"),
        )

        entry = pack.policies["data-governance"]
        self.assertTrue(is_dataclass(entry))
        self.assertEqual(entry.severity, SeverityLevel.HIGH)
        self.assertEqual(entry.policy.name, entry.id)
        self.assertIn("training_dataset", entry.policy.states)

        with self.assertRaises(TypeError):
            pack.policies["new"] = entry  # type: ignore[index]

    def test_rejects_missing_policy_file(self) -> None:
        with TemporaryDirectory() as directory:
            manifest = self._create_pack(directory)
            (
                manifest.parent
                / "policies"
                / "data-governance.yml"
            ).unlink()

            with self.assertRaisesRegex(
                PolicyPackReadError,
                'could not load policy "data-governance"',
            ):
                PolicyPackReader.read(manifest)

    def test_rejects_duplicate_policy_ids(self) -> None:
        with TemporaryDirectory() as directory:
            manifest = self._create_pack(directory)
            content = manifest.read_text(encoding="utf-8")
            content = content.replace(
                '    - id: "human-oversight"',
                '    - id: "data-governance"',
            )
            manifest.write_text(content, encoding="utf-8")

            with self.assertRaisesRegex(
                PolicyPackConsistencyError,
                "duplicate policy id",
            ):
                PolicyPackReader.read(manifest)

    def test_rejects_duplicate_policy_file_references(self) -> None:
        with TemporaryDirectory() as directory:
            manifest = self._create_pack(directory)
            content = manifest.read_text(encoding="utf-8")
            content = content.replace(
                '"policies/human-oversight.yml"',
                '"policies/data-governance.yml"',
            )
            manifest.write_text(content, encoding="utf-8")

            with self.assertRaisesRegex(
                PolicyPackConsistencyError,
                "referenced more than once",
            ):
                PolicyPackReader.read(manifest)

    def test_rejects_manifest_policy_mismatch(self) -> None:
        with TemporaryDirectory() as directory:
            manifest = self._create_pack(directory)
            content = manifest.read_text(encoding="utf-8")
            content = content.replace(
                '      severity: "high"',
                '      severity: "low"',
                1,
            )
            manifest.write_text(content, encoding="utf-8")

            with self.assertRaisesRegex(
                PolicyPackConsistencyError,
                "severity.*manifest declares",
            ):
                PolicyPackReader.read(manifest)

    def test_rejects_path_traversal_in_manifest(self) -> None:
        with TemporaryDirectory() as directory:
            manifest = self._create_pack(directory)
            content = manifest.read_text(encoding="utf-8")
            content = content.replace(
                '"policies/data-governance.yml"',
                '"../data-governance.yml"',
            )
            manifest.write_text(content, encoding="utf-8")

            with self.assertRaises(PolicyPackValidationError):
                PolicyPackReader.read(manifest)

    def test_rejects_symlink_escape(self) -> None:
        with TemporaryDirectory() as directory:
            manifest = self._create_pack(directory)
            policy_path = (
                manifest.parent
                / "policies"
                / "data-governance.yml"
            )
            outside_path = Path(directory) / "outside-policy.yml"
            outside_path.write_text(
                policy_path.read_text(encoding="utf-8"),
                encoding="utf-8",
            )
            policy_path.unlink()
            policy_path.symlink_to(outside_path)

            with self.assertRaisesRegex(
                PolicyPackFileError,
                "resolves outside",
            ):
                PolicyPackReader.read(manifest)

    def test_rejects_unsupported_pack_schema(self) -> None:
        with TemporaryDirectory() as directory:
            manifest = self._create_pack(directory)
            content = manifest.read_text(encoding="utf-8")
            content = content.replace(
                'pack_schema_version: "1.2.0"',
                'pack_schema_version: "1.1.0"',
            )
            manifest.write_text(content, encoding="utf-8")

            with self.assertRaisesRegex(
                UnsupportedPolicyPackSchemaError,
                "expected '1.2.0'",
            ):
                PolicyPackReader.read(manifest)

    def test_validates_manifest_file_boundary(self) -> None:
        with self.assertRaises(TypeError):
            PolicyPackReader.read(123)  # type: ignore[arg-type]
        with self.assertRaises(ValueError):
            PolicyPackReader.read(" ")
        with self.assertRaises(PolicyPackFileError):
            PolicyPackReader.read("missing-manifest.yml")


if __name__ == "__main__":
    unittest.main()
