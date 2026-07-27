from pathlib import Path
from typing import Any
from typing import Mapping

from govlattice import __schema_version__
from govlattice.error import PolicyValidationError
from govlattice.error import SchemaValidationError
from govlattice.error import UnsupportedPolicySchemaError
from govlattice.validator.json_schema_validator import (
    JsonSchemaValidator,
)


POLICY_SCHEMA_PATH = (
    Path(__file__).resolve().parents[2]
    / "schemas"
    / "govlattice-policy.schema.json"
)


class PolicyValidator:
    _schema_validator = JsonSchemaValidator(POLICY_SCHEMA_PATH)

    @classmethod
    def validate(cls, document: Mapping[str, Any]) -> None:
        if not isinstance(document, Mapping):
            raise TypeError("document must be a mapping")

        version = document.get("schema_version")
        if version != __schema_version__:
            raise UnsupportedPolicySchemaError(
                f"policy schema {version!r} is not supported; "
                f"expected {__schema_version__!r}"
            )

        try:
            cls._schema_validator.validate(document)
        except SchemaValidationError as error:
            raise PolicyValidationError(str(error)) from error
