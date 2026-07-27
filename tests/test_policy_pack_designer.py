import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

import govlattice
from govlattice import PolicyReference
from govlattice import SeverityLevel
from govlattice.designer.policy_designer import PolicyDesigner
from govlattice.designer.policy_pack_designer import PolicyPackDesigner
from govlattice.verifier.unique_policy_ids_verifier import (
    DuplicatePolicyIdError,
)


class PolicyPackDesignerTests(unittest.TestCase):
    def _policy(
        self,
        name: str,
        severity: SeverityLevel = SeverityLevel.MEDIUM,
    ) -> PolicyDesigner:
        return (
            PolicyDesigner(
                name,
                severity=severity,
                lifecycle_stages=("validation",),
                references=(
                    PolicyReference(
                        "Official reference",
                        "https://example.com/regulation",
                    ),
                ),
            )
            .state("dataset")
            .require_columns("id")
            .end()
        )

    def test_pack_exports_manifest_and_policy_files(self) -> None:
        pack = (
            PolicyPackDesigner(
                pack_id="eu-ai-act",
                name="EU AI Act",
                version="1.0.0",
                jurisdiction=("EU",),
                tags=("regulatory",),
                framework="Regulation (EU) 2024/1689",
            )
            .add_policy(
                self._policy(
                    "data-governance",
                    SeverityLevel.HIGH,
                )
            )
            .add_policy(
                self._policy(
                    "human-oversight",
                    SeverityLevel.CRITICAL,
                )
            )
            .verify_unique_policy_ids()
            .verify_schema_versions()
            .verify_policy_references()
        )

        with TemporaryDirectory() as directory:
            manifest = pack.execute(
                "eu-ai-act",
                output_dir=directory,
            )
            pack_directory = Path(directory).resolve() / "eu-ai-act"
            content = manifest.read_text(encoding="utf-8")

            self.assertEqual(
                manifest,
                pack_directory / "manifest.yml",
            )
            self.assertTrue(
                (
                    pack_directory
                    / "policies"
                    / "data-governance.yml"
                ).is_file()
            )
            self.assertTrue(
                (
                    pack_directory
                    / "policies"
                    / "human-oversight.yml"
                ).is_file()
            )

        self.assertIn('pack_schema_version: "1.0.0"', content)
        self.assertIn('id: "eu-ai-act"', content)
        self.assertIn('framework: "Regulation (EU) 2024/1689"', content)
        self.assertIn('file: "policies/data-governance.yml"', content)
        self.assertIn('severity: "critical"', content)
        self.assertIn('schema_version: "1.4.0"', content)

    def test_pack_rejects_duplicate_policy_ids(self) -> None:
        policy = self._policy("data-governance")
        pack = (
            PolicyPackDesigner(
                "eu-ai-act",
                "EU AI Act",
                "1.0.0",
            )
            .add_policy(policy)
            .add_policy(policy)
        )

        with self.assertRaises(DuplicatePolicyIdError):
            pack.verify_unique_policy_ids()

    def test_pack_rejects_non_file_safe_policy_name(self) -> None:
        policy = self._policy("data governance")
        pack = PolicyPackDesigner(
            "eu-ai-act",
            "EU AI Act",
            "1.0.0",
        )

        with self.assertRaises(ValueError):
            pack.add_policy(policy)

    def test_pack_schema_versions_match_public_constants(self) -> None:
        schema_path = (
            Path(__file__).resolve().parents[1]
            / "schemas"
            / "govlattice-policy-pack.schema.json"
        )
        schema = json.loads(schema_path.read_text(encoding="utf-8"))

        self.assertEqual(
            schema["properties"]["pack_schema_version"]["const"],
            govlattice.__pack_schema_version__,
        )
        self.assertEqual(
            schema["$defs"]["policy_entry"]["properties"][
                "schema_version"
            ]["const"],
            govlattice.__schema_version__,
        )


if __name__ == "__main__":
    unittest.main()
