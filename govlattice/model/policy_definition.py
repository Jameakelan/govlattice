from dataclasses import dataclass
from typing import Any
from typing import Mapping
from typing import Optional
from typing import Union

from govlattice.enum import SeverityLevel


@dataclass(frozen=True)
class ReferenceDefinition:
    __slots__ = ("title", "url")

    title: str
    url: str


@dataclass(frozen=True)
class RequirementDefinition:
    __slots__ = ("type", "parameters")

    type: str
    parameters: Mapping[str, Any]


@dataclass(frozen=True)
class ConditionDefinition:
    __slots__ = ("type", "column", "minimum", "maximum")

    type: str
    column: str
    minimum: Union[int, float]
    maximum: Union[int, float]


@dataclass(frozen=True)
class SegmentDefinition:
    __slots__ = ("name", "condition", "requirements")

    name: str
    condition: ConditionDefinition
    requirements: tuple[RequirementDefinition, ...]


@dataclass(frozen=True)
class StateDefinition:
    __slots__ = ("id", "requirements", "segments")

    id: str
    requirements: tuple[RequirementDefinition, ...]
    segments: Mapping[str, SegmentDefinition]


@dataclass(frozen=True)
class PolicyDefinition:
    __slots__ = (
        "schema_version",
        "name",
        "purpose",
        "enabled",
        "severity",
        "tags",
        "lifecycle_stages",
        "references",
        "created_at",
        "updated_at",
        "metadata",
        "states",
    )

    schema_version: str
    name: str
    purpose: Optional[str]
    enabled: bool
    severity: SeverityLevel
    tags: tuple[str, ...]
    lifecycle_stages: tuple[str, ...]
    references: tuple[ReferenceDefinition, ...]
    created_at: Optional[str]
    updated_at: Optional[str]
    metadata: Mapping[str, Any]
    states: Mapping[str, StateDefinition]
