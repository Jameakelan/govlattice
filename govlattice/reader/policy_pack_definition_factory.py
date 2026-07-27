from types import MappingProxyType
from typing import Any
from typing import Mapping

from govlattice.enum import SeverityLevel
from govlattice.model import PolicyDefinition
from govlattice.model import PolicyPackDefinition
from govlattice.model import PolicyPackEntryDefinition
from govlattice.model.immutable import freeze_value


STANDARD_POLICY_PACK_KEYS = frozenset(
    {
        "id",
        "name",
        "version",
        "purpose",
        "enabled",
        "jurisdiction",
        "tags",
        "policies",
    }
)


class PolicyPackDefinitionFactory:
    @classmethod
    def create(
        cls,
        document: Mapping[str, Any],
        loaded_policies: Mapping[str, PolicyDefinition],
    ) -> PolicyPackDefinition:
        pack = document["policy_pack"]
        metadata = {
            key: freeze_value(value)
            for key, value in pack.items()
            if key not in STANDARD_POLICY_PACK_KEYS
        }
        entries = {
            entry["id"]: PolicyPackEntryDefinition(
                id=entry["id"],
                file=entry["file"],
                enabled=entry["enabled"],
                severity=SeverityLevel(entry["severity"]),
                schema_version=entry["schema_version"],
                policy=loaded_policies[entry["id"]],
            )
            for entry in pack["policies"]
        }

        return PolicyPackDefinition(
            pack_schema_version=document["pack_schema_version"],
            id=pack["id"],
            name=pack["name"],
            version=pack["version"],
            purpose=pack.get("purpose"),
            enabled=pack["enabled"],
            jurisdiction=tuple(pack["jurisdiction"]),
            tags=tuple(pack["tags"]),
            metadata=MappingProxyType(metadata),
            policies=MappingProxyType(entries),
        )
