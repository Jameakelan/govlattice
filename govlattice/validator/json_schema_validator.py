import json
from functools import lru_cache
from pathlib import Path
from typing import Any
from typing import Mapping
from typing import Union

from jsonschema import Draft202012Validator
from jsonschema import FormatChecker
from jsonschema.exceptions import SchemaError

from govlattice.error import SchemaValidationError


PathInput = Union[str, Path]


@lru_cache(maxsize=None)
def _load_validator(schema_path: Path) -> Draft202012Validator:
    try:
        schema = json.loads(schema_path.read_text(encoding="utf-8"))
        Draft202012Validator.check_schema(schema)
    except (
        OSError,
        UnicodeError,
        json.JSONDecodeError,
        SchemaError,
    ) as error:
        raise SchemaValidationError(
            f'could not load JSON Schema: "{schema_path}"'
        ) from error

    return Draft202012Validator(
        schema,
        format_checker=FormatChecker(),
    )


class JsonSchemaValidator:
    __slots__ = ("_schema_path",)

    def __init__(self, schema_path: PathInput) -> None:
        if not isinstance(schema_path, (str, Path)):
            raise TypeError("schema_path must be a string or Path")
        if isinstance(schema_path, str) and not schema_path.strip():
            raise ValueError("schema_path must not be empty")
        self._schema_path = Path(schema_path).expanduser().resolve()

    def validate(self, document: Mapping[str, Any]) -> None:
        if not isinstance(document, Mapping):
            raise TypeError("document must be a mapping")

        validator = _load_validator(self._schema_path)
        errors = sorted(
            validator.iter_errors(document),
            key=lambda error: tuple(str(part) for part in error.path),
        )
        if not errors:
            return

        error = errors[0]
        location = ".".join(str(part) for part in error.absolute_path)
        prefix = f"{location}: " if location else ""
        raise SchemaValidationError(f"{prefix}{error.message}")
