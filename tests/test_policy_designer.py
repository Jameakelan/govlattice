import json
import os
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

import govlattice
from govlattice.designer.policy_designer import PolicyDesigner
from govlattice.verifier.range_overlap_verifier import OverlapRangeError


class PolicyDesignerTests(unittest.TestCase):
    def test_public_versions(self) -> None:
        self.assertEqual(govlattice.__version__, "0.3.0")
        self.assertEqual(govlattice.__schema_version__, "1.2.0")

    def test_json_schema_uses_public_schema_version(self) -> None:
        schema_path = (
            Path(__file__).resolve().parents[1]
            / "schemas"
            / "govlattice-policy.schema.json"
        )
        schema = json.loads(schema_path.read_text(encoding="utf-8"))

        self.assertIn("schema_version", schema["required"])
        self.assertEqual(
            schema["properties"]["schema_version"]["const"],
            govlattice.__schema_version__,
        )

    def test_dev_example_builds_column_requirement(self) -> None:
        policy = (
            PolicyDesigner(policy_name="A10-health-policy")
            .state("dataset")
            .require_columns("id", "name")
        )

        self.assertEqual(policy.state_id, "dataset")
        requirement = policy.requirements[0]
        self.assertEqual(requirement.type, "require_columns")
        self.assertEqual(
            requirement.parameters,
            {"columns": ("id", "name")},
        )

    def test_builder_is_fluent_and_end_returns_designer(self) -> None:
        designer = PolicyDesigner(policy_name="health-policy")
        builder = designer.state("dataset")

        result = builder.require_unique("id")

        self.assertIs(result, builder)
        self.assertIs(builder.end(), designer)

    def test_state_reuses_existing_builder(self) -> None:
        designer = PolicyDesigner(policy_name="health-policy")
        first = designer.state("dataset")
        first.require_columns("id")
        second = designer.state(" dataset ")

        self.assertEqual(second.state_id, "dataset")
        self.assertEqual(len(second.requirements), 1)

    def test_names_are_normalized(self) -> None:
        designer = PolicyDesigner(policy_name=" health-policy ")
        builder = designer.state(" dataset ")

        self.assertEqual(designer.policy_name, "health-policy")
        self.assertEqual(builder.state_id, "dataset")

    def test_invalid_policy_name_is_rejected(self) -> None:
        with self.assertRaises(TypeError):
            PolicyDesigner(policy_name=123)  # type: ignore[arg-type]
        with self.assertRaises(ValueError):
            PolicyDesigner(policy_name=" ")

    def test_invalid_state_id_is_rejected(self) -> None:
        designer = PolicyDesigner(policy_name="health-policy")

        with self.assertRaises(TypeError):
            designer.state(123)  # type: ignore[arg-type]
        with self.assertRaises(ValueError):
            designer.state(" ")

    def test_invalid_columns_are_rejected(self) -> None:
        builder = PolicyDesigner("health-policy").state("dataset")

        with self.assertRaises(ValueError):
            builder.require_columns()
        with self.assertRaises(TypeError):
            builder.require_columns(123)  # type: ignore[arg-type]
        with self.assertRaises(ValueError):
            builder.require_columns(" ")

    def test_instances_do_not_have_dicts(self) -> None:
        designer = PolicyDesigner("health-policy")
        builder = designer.state("dataset")
        segment = builder.segment("adult").when_between("age", 18, 59)

        self.assertFalse(hasattr(designer, "__dict__"))
        self.assertFalse(hasattr(builder, "__dict__"))
        self.assertFalse(hasattr(segment, "__dict__"))

    def test_execute_returns_output_path_and_validates_name(self) -> None:
        designer = PolicyDesigner("health-policy")

        with TemporaryDirectory() as directory:
            output = designer.execute(
                "health_policy.yaml",
                output_dir=directory,
            )

            self.assertEqual(
                output,
                Path(directory).resolve() / "health_policy.yaml",
            )

        with self.assertRaises(TypeError):
            designer.execute(123)  # type: ignore[arg-type]
        with self.assertRaises(ValueError):
            designer.execute(" ")
        with self.assertRaises(ValueError):
            designer.execute("health_policy.json")

    def test_execute_writes_policy_yaml(self) -> None:
        designer = PolicyDesigner("A10-health-policy")
        (
            designer.state("dataset")
            .require_columns("id", "name")
            .require_unique("id")
        )

        with TemporaryDirectory() as directory:
            output = Path(directory) / "health_policy.yaml"

            result = designer.execute(
                output.name,
                output_dir=output.parent,
            )
            self.assertEqual(result, output.resolve())
            self.assertEqual(
                output.read_text(encoding="utf-8"),
                (
                    'schema_version: "1.2.0"\n'
                    "policy:\n"
                    '  name: "A10-health-policy"\n'
                    "  enabled: true\n"
                    "  tags: []\n"
                    "  states:\n"
                    '    "dataset":\n'
                    "      requirements:\n"
                    '        - type: "require_columns"\n'
                    "          columns:\n"
                    '            - "id"\n'
                    '            - "name"\n'
                    '        - type: "require_unique"\n'
                    "          columns:\n"
                    '            - "id"\n'
                ),
            )

    def test_execute_writes_empty_states(self) -> None:
        designer = PolicyDesigner("health-policy")

        with TemporaryDirectory() as directory:
            output = Path(directory) / "health_policy.yml"

            designer.execute(output.name, output_dir=output.parent)
            self.assertEqual(
                output.read_text(encoding="utf-8"),
                (
                    'schema_version: "1.2.0"\n'
                    'policy:\n'
                    '  name: "health-policy"\n'
                    '  enabled: true\n'
                    '  tags: []\n'
                    '  states: {}\n'
                ),
            )

    def test_execute_creates_default_policies_directory(self) -> None:
        designer = PolicyDesigner("health-policy")

        with TemporaryDirectory() as directory:
            previous_directory = Path.cwd()
            try:
                os.chdir(directory)
                output = designer.execute("health_policy.yaml")
            finally:
                os.chdir(previous_directory)

            self.assertEqual(
                output,
                (
                    Path(directory)
                    / "policies"
                    / "health_policy.yaml"
                ).resolve(),
            )
            self.assertTrue(output.is_file())

    def test_execute_creates_custom_nested_output_directory(self) -> None:
        designer = PolicyDesigner("health-policy")

        with TemporaryDirectory() as directory:
            output_directory = Path(directory) / "config" / "policies"
            output = designer.execute(
                "health_policy.yaml",
                output_dir=output_directory,
            )

            self.assertEqual(
                output,
                (output_directory / "health_policy.yaml").resolve(),
            )
            self.assertTrue(output.is_file())

    def test_execute_rejects_paths_as_file_names(self) -> None:
        designer = PolicyDesigner("health-policy")

        with self.assertRaises(ValueError):
            designer.execute("../health_policy.yaml")
        with self.assertRaises(ValueError):
            designer.execute("nested/health_policy.yaml")

    def test_multiple_states_and_segments_are_serialized(self) -> None:
        designer = PolicyDesigner("A10-health-policy")
        (
            designer.state("raw_dataset")
            .require_columns("id", "age", "hba1c")
            .end()
            .state("validated_dataset")
            .segment("adult")
            .when_between("age", minimum=18, maximum=59)
            .require_missing_rate("hba1c", maximum=0.05)
            .require_range("hba1c", minimum=4.0, maximum=14.0)
            .end()
            .segment("senior")
            .when_between("age", minimum=60, maximum=100)
            .require_missing_rate("hba1c", maximum=0.02)
            .end()
            .verify_overlap_range("age")
            .end()
        )

        with TemporaryDirectory() as directory:
            output = designer.execute(
                "health_policy.yml",
                output_dir=directory,
            )
            content = output.read_text(encoding="utf-8")

        self.assertLess(
            content.index('"raw_dataset"'),
            content.index('"validated_dataset"'),
        )
        self.assertLess(
            content.index('"adult"'),
            content.index('"senior"'),
        )
        self.assertIn('type: "between"', content)
        self.assertIn('type: "require_missing_rate"', content)
        self.assertIn('type: "require_range"', content)
        self.assertIn("maximum: 0.05", content)
        self.assertIn("minimum: 4.0", content)

    def test_overlap_verification_is_scoped_to_current_state(self) -> None:
        designer = PolicyDesigner("health-policy")
        first_state = designer.state("first")
        (
            first_state.segment("young")
            .when_between("age", 10, 20)
            .end()
        )
        first_state.verify_overlap_range("age")

        second_state = first_state.end().state("second")
        (
            second_state.segment("adult")
            .when_between("age", 15, 30)
            .end()
        )

        second_state.verify_overlap_range("age")

    def test_overlap_verification_rejects_overlapping_segments(self) -> None:
        state = PolicyDesigner("health-policy").state("dataset")
        state.segment("first").when_between("age", 10, 20).end()
        state.segment("second").when_between("age", 15, 30).end()

        with self.assertRaisesRegex(
            OverlapRangeError,
            'state "dataset".*segment "first".*segment "second"',
        ):
            state.verify_overlap_range("age")

    def test_overlap_verification_treats_boundaries_as_inclusive(self) -> None:
        state = PolicyDesigner("health-policy").state("dataset")
        state.segment("first").when_between("age", 10, 20).end()
        state.segment("second").when_between("age", 20, 30).end()

        with self.assertRaises(OverlapRangeError):
            state.verify_overlap_range("age")

    def test_overlap_verification_groups_ranges_by_column(self) -> None:
        state = PolicyDesigner("health-policy").state("dataset")
        state.segment("age").when_between("age", 10, 20).end()
        state.segment("score").when_between("score", 15, 30).end()

        self.assertIs(state.verify_overlap_range("age"), state)

    def test_overlap_verification_only_checks_selected_column(self) -> None:
        state = PolicyDesigner("health-policy").state("dataset")
        state.segment("age-a").when_between("age", 10, 20).end()
        state.segment("age-b").when_between("age", 21, 30).end()
        state.segment("score-a").when_between("score", 10, 20).end()
        state.segment("score-b").when_between("score", 15, 30).end()

        self.assertIs(state.verify_overlap_range("age"), state)
        with self.assertRaises(OverlapRangeError):
            state.verify_overlap_range("score")

    def test_overlap_verification_rejects_unknown_column(self) -> None:
        state = PolicyDesigner("health-policy").state("dataset")
        state.segment("adult").when_between("age", 18, 59).end()

        with self.assertRaisesRegex(
            ValueError,
            'No between conditions found for column "score"',
        ):
            state.verify_overlap_range("score")

    def test_missing_rate_validation(self) -> None:
        state = PolicyDesigner("health-policy").state("dataset")

        self.assertIs(
            state.require_missing_rate("hba1c", maximum=0.05),
            state,
        )
        with self.assertRaises(TypeError):
            state.require_missing_rate("hba1c", maximum=True)
        with self.assertRaises(ValueError):
            state.require_missing_rate("hba1c", maximum=1.01)

    def test_range_validation(self) -> None:
        state = PolicyDesigner("health-policy").state("dataset")

        self.assertIs(
            state.require_range("age", minimum=18, maximum=100),
            state,
        )
        with self.assertRaises(TypeError):
            state.require_range("age", minimum=False, maximum=100)
        with self.assertRaises(ValueError):
            state.require_range("age", minimum=100, maximum=18)

    def test_segment_requires_a_condition_before_end(self) -> None:
        segment = (
            PolicyDesigner("health-policy")
            .state("dataset")
            .segment("adult")
        )

        with self.assertRaisesRegex(ValueError, "requires a condition"):
            segment.end()

    def test_policy_lifecycle_metadata_is_serialized(self) -> None:
        designer = PolicyDesigner(
            "health-policy",
            enabled=False,
            tags=("health", "testing", "health"),
            created_at="2026-07-01T09:00:00+07:00",
            updated_at="2026-07-27T17:30:00+07:00",
            agile={
                "stage": "testing",
                "sprint": 12,
            },
            reviewers=["alice", "bob"],
            nullable=None,
        )

        with TemporaryDirectory() as directory:
            output = designer.execute(
                "health_policy.yml",
                output_dir=directory,
            )
            content = output.read_text(encoding="utf-8")

        self.assertEqual(
            content,
            (
                'schema_version: "1.2.0"\n'
                "policy:\n"
                '  name: "health-policy"\n'
                "  enabled: false\n"
                "  tags:\n"
                '    - "health"\n'
                '    - "testing"\n'
                '  created_at: "2026-07-01T09:00:00+07:00"\n'
                '  updated_at: "2026-07-27T17:30:00+07:00"\n'
                "  agile:\n"
                '    stage: "testing"\n'
                "    sprint: 12\n"
                "  reviewers:\n"
                '    - "alice"\n'
                '    - "bob"\n'
                "  nullable: null\n"
                "  states: {}\n"
            ),
        )

    def test_policy_lifecycle_metadata_validation(self) -> None:
        with self.assertRaises(TypeError):
            PolicyDesigner("health-policy", enabled=1)
        with self.assertRaises(TypeError):
            PolicyDesigner("health-policy", tags="health")
        with self.assertRaises(ValueError):
            PolicyDesigner("health-policy", tags=(" ",))
        with self.assertRaises(ValueError):
            PolicyDesigner(
                "health-policy",
                created_at="2026-07-01T09:00:00",
            )
        with self.assertRaises(ValueError):
            PolicyDesigner(
                "health-policy",
                created_at="2026-07-28T09:00:00Z",
                updated_at="2026-07-27T09:00:00Z",
            )
        with self.assertRaises(ValueError):
            PolicyDesigner(
                "health-policy",
                **{"states": "invalid"},
            )
        with self.assertRaises(TypeError):
            PolicyDesigner(
                "health-policy",
                custom=object(),
            )
        with self.assertRaises(ValueError):
            PolicyDesigner(
                "health-policy",
                custom=float("nan"),
            )


if __name__ == "__main__":
    unittest.main()
