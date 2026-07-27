from pathlib import Path
from typing import Any
from typing import Mapping

from govlattice.error import PolicyPackConsistencyError
from govlattice.error import PolicyPackFileError
from govlattice.error import PolicyPackReadError
from govlattice.error import PolicyReadError
from govlattice.model import PolicyDefinition
from govlattice.model import PolicyPackDefinition
from govlattice.reader.policy_pack_definition_factory import (
    PolicyPackDefinitionFactory,
)
from govlattice.reader.policy_pack_yaml_loader import (
    MAX_POLICY_PACK_FILE_BYTES,
)
from govlattice.reader.policy_pack_yaml_loader import (
    PolicyPackYamlLoader,
)
from govlattice.reader.policy_reader import PolicyReader
from govlattice.reader.policy_yaml_loader import PathInput
from govlattice.validator import PolicyPackValidator


class PolicyPackReader:
    MAX_FILE_BYTES = MAX_POLICY_PACK_FILE_BYTES

    @classmethod
    def read(cls, path: PathInput) -> PolicyPackDefinition:
        manifest_path, document = PolicyPackYamlLoader.load(path)
        PolicyPackValidator.validate(document)
        policies = cls._load_policies(manifest_path, document)
        return PolicyPackDefinitionFactory.create(
            document,
            policies,
        )

    @classmethod
    def _load_policies(
        cls,
        manifest_path: Path,
        document: Mapping[str, Any],
    ) -> Mapping[str, PolicyDefinition]:
        loaded: dict[str, PolicyDefinition] = {}
        resolved_paths: set[Path] = set()

        for entry in document["policy_pack"]["policies"]:
            policy_id = entry["id"]
            if policy_id in loaded:
                raise PolicyPackConsistencyError(
                    f'duplicate policy id "{policy_id}"'
                )

            policy_path = cls._resolve_policy_path(
                manifest_path,
                entry["file"],
            )
            if policy_path in resolved_paths:
                raise PolicyPackConsistencyError(
                    f'policy file "{entry["file"]}" is referenced '
                    "more than once"
                )
            resolved_paths.add(policy_path)

            try:
                policy = PolicyReader.read(policy_path)
            except PolicyReadError as error:
                raise PolicyPackReadError(
                    f'could not load policy "{policy_id}" from '
                    f'"{entry["file"]}": {error}'
                ) from error

            cls._validate_consistency(entry, policy)
            loaded[policy_id] = policy

        return loaded

    @staticmethod
    def _resolve_policy_path(
        manifest_path: Path,
        file_name: str,
    ) -> Path:
        relative_path = Path(file_name)
        if relative_path.is_absolute() or ".." in relative_path.parts:
            raise PolicyPackFileError(
                f'policy file path is unsafe: "{file_name}"'
            )
        if (
            not relative_path.parts
            or relative_path.parts[0] != "policies"
        ):
            raise PolicyPackFileError(
                f'policy file must be inside "policies/": '
                f'"{file_name}"'
            )

        pack_directory = manifest_path.parent.resolve()
        policy_path = (pack_directory / relative_path).resolve()
        try:
            policy_path.relative_to(pack_directory)
        except ValueError as error:
            raise PolicyPackFileError(
                f'policy file resolves outside the pack: "{file_name}"'
            ) from error

        if policy_path == manifest_path:
            raise PolicyPackFileError(
                "policy file must not reference the manifest"
            )
        return policy_path

    @staticmethod
    def _validate_consistency(
        entry: Mapping[str, Any],
        policy: PolicyDefinition,
    ) -> None:
        expected = {
            "id": policy.name,
            "enabled": policy.enabled,
            "severity": policy.severity.value,
            "schema_version": policy.schema_version,
        }
        for field, actual in expected.items():
            declared = entry[field]
            if declared != actual:
                raise PolicyPackConsistencyError(
                    f'policy "{entry["id"]}" {field} is '
                    f"{actual!r}, but the manifest declares "
                    f"{declared!r}"
                )
