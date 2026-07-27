import os
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from govlattice.designer.policy_designer import PolicyDesigner


class PolicyDesignerTests(unittest.TestCase):
    def test_dev_example_builds_column_requirement(self) -> None:
        policy = (
            PolicyDesigner(policy_name="A10-health-policy")
            .state("dataset")
            .require_columns("id", "name")
        )

        self.assertEqual(policy.state_id, "dataset")
        self.assertEqual(
            policy.requirements,
            (("require_columns", ("id", "name")),),
        )

    def test_builder_is_fluent_and_end_returns_designer(self) -> None:
        designer = PolicyDesigner(policy_name="health-policy")
        builder = designer.state("dataset")

        result = builder.require_unique("id")

        self.assertIs(result, builder)
        self.assertIs(builder.end(), designer)

    def test_state_reuses_existing_builder(self) -> None:
        designer = PolicyDesigner(policy_name="health-policy")

        self.assertIs(designer.state("dataset"), designer.state(" dataset "))

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

        self.assertFalse(hasattr(designer, "__dict__"))
        self.assertFalse(hasattr(builder, "__dict__"))

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
                    "policy:\n"
                    '  name: "A10-health-policy"\n'
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
                    'policy:\n  name: "health-policy"\n  states: {}\n'
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


if __name__ == "__main__":
    unittest.main()
