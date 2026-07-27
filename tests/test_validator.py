import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from govlattice.error import SchemaValidationError
from govlattice.validator import JsonSchemaValidator
from govlattice.validator.json_schema_validator import _load_validator


class JsonSchemaValidatorTests(unittest.TestCase):
    def _schema_path(self, directory: str) -> Path:
        path = Path(directory) / "schema.json"
        path.write_text(
            json.dumps(
                {
                    "$schema": (
                        "https://json-schema.org/draft/2020-12/schema"
                    ),
                    "type": "object",
                    "required": ["value"],
                    "properties": {
                        "value": {
                            "type": "number",
                            "minimum": 0,
                        }
                    },
                    "additionalProperties": False,
                }
            ),
            encoding="utf-8",
        )
        return path

    def test_validates_any_document_against_supplied_schema(self) -> None:
        with TemporaryDirectory() as directory:
            validator = JsonSchemaValidator(
                self._schema_path(directory)
            )

            validator.validate({"value": 1})
            with self.assertRaisesRegex(
                SchemaValidationError,
                "value:",
            ):
                validator.validate({"value": -1})

    def test_reuses_cached_validator_for_same_schema_path(self) -> None:
        with TemporaryDirectory() as directory:
            schema_path = self._schema_path(directory)
            first = JsonSchemaValidator(schema_path)
            second = JsonSchemaValidator(schema_path)
            _load_validator.cache_clear()

            first.validate({"value": 1})
            second.validate({"value": 2})

            cache_info = _load_validator.cache_info()
            self.assertEqual(cache_info.misses, 1)
            self.assertEqual(cache_info.hits, 1)

    def test_rejects_invalid_schema_file(self) -> None:
        with TemporaryDirectory() as directory:
            path = Path(directory) / "invalid-schema.json"
            path.write_text("{", encoding="utf-8")
            validator = JsonSchemaValidator(path)

            with self.assertRaisesRegex(
                SchemaValidationError,
                "could not load JSON Schema",
            ):
                validator.validate({})

    def test_validates_constructor_boundaries(self) -> None:
        with self.assertRaises(TypeError):
            JsonSchemaValidator(123)  # type: ignore[arg-type]
        with self.assertRaises(ValueError):
            JsonSchemaValidator(" ")


if __name__ == "__main__":
    unittest.main()
