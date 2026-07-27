from dataclasses import dataclass
from typing import Any
from typing import Mapping
from typing import Optional

from govlattice.enum import SeverityLevel
from govlattice.model.policy_definition import PolicyDefinition


@dataclass(frozen=True)
class PolicyPackEntryDefinition:
    __slots__ = (
        "id",
        "file",
        "enabled",
        "severity",
        "schema_version",
        "policy",
    )

    id: str
    file: str
    enabled: bool
    severity: SeverityLevel
    schema_version: str
    policy: PolicyDefinition


@dataclass(frozen=True)
class PolicyPackDefinition:
    __slots__ = (
        "pack_schema_version",
        "id",
        "name",
        "version",
        "purpose",
        "enabled",
        "jurisdiction",
        "tags",
        "metadata",
        "policies",
    )

    pack_schema_version: str
    id: str
    name: str
    version: str
    purpose: Optional[str]
    enabled: bool
    jurisdiction: tuple[str, ...]
    tags: tuple[str, ...]
    metadata: Mapping[str, Any]
    policies: Mapping[str, PolicyPackEntryDefinition]
