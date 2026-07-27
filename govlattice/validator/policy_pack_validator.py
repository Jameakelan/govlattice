from pathlib import Path
from typing import Any
from typing import Mapping

from govlattice import __pack_schema_version__
from govlattice.error import PolicyPackValidationError
from govlattice.error import SchemaValidationError
from govlattice.error import UnsupportedPolicyPackSchemaError
from govlattice.validator.json_schema_validator import (
    JsonSchemaValidator,
)


POLICY_PACK_SCHEMA_PATH = (
    Path(__file__).resolve().parents[2]
    / "schemas"
    / "govlattice-policy-pack.schema.json"
)


class PolicyPackValidator:
    _schema_validator = JsonSchemaValidator(
        POLICY_PACK_SCHEMA_PATH
    )

    @classmethod
    def validate(cls, document: Mapping[str, Any]) -> None:
        if not isinstance(document, Mapping):
            raise TypeError("document must be a mapping")

        version = document.get("pack_schema_version")
        if version != __pack_schema_version__:
            raise UnsupportedPolicyPackSchemaError(
                f"policy pack schema {version!r} is not supported; "
                f"expected {__pack_schema_version__!r}"
            )

        try:
            cls._schema_validator.validate(document)
        except SchemaValidationError as error:
            raise PolicyPackValidationError(str(error)) from error
