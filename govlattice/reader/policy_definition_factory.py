from types import MappingProxyType
from typing import Any
from typing import Mapping

from govlattice.enum import ComparisonOperator
from govlattice.enum import SeverityLevel
from govlattice.model import ConditionDefinition
from govlattice.model import PolicyDefinition
from govlattice.model import ReferenceDefinition
from govlattice.model import RequirementDefinition
from govlattice.model import SegmentDefinition
from govlattice.model import StateDefinition
from govlattice.model.immutable import freeze_value


STANDARD_POLICY_KEYS = frozenset(
    {
        "name",
        "purpose",
        "enabled",
        "severity",
        "tags",
        "lifecycle_stages",
        "references",
        "created_at",
        "updated_at",
        "states",
    }
)


class PolicyDefinitionFactory:
    @classmethod
    def create(
        cls,
        document: Mapping[str, Any],
    ) -> PolicyDefinition:
        policy = document["policy"]
        metadata = {
            key: freeze_value(value)
            for key, value in policy.items()
            if key not in STANDARD_POLICY_KEYS
        }
        states = {
            state_id: cls._build_state(state_id, state)
            for state_id, state in policy["states"].items()
        }
        references = tuple(
            ReferenceDefinition(
                title=reference["title"],
                url=reference["url"],
            )
            for reference in policy["references"]
        )

        return PolicyDefinition(
            schema_version=document["schema_version"],
            name=policy["name"],
            purpose=policy.get("purpose"),
            enabled=policy["enabled"],
            severity=SeverityLevel(policy["severity"]),
            tags=tuple(policy["tags"]),
            lifecycle_stages=tuple(policy["lifecycle_stages"]),
            references=references,
            created_at=policy.get("created_at"),
            updated_at=policy.get("updated_at"),
            metadata=MappingProxyType(metadata),
            states=MappingProxyType(states),
        )

    @classmethod
    def _build_state(
        cls,
        state_id: str,
        state: Mapping[str, Any],
    ) -> StateDefinition:
        segments = {
            name: cls._build_segment(name, segment)
            for name, segment in state.get("segments", {}).items()
        }
        return StateDefinition(
            id=state_id,
            requirements=cls._build_requirements(
                state["requirements"]
            ),
            segments=MappingProxyType(segments),
        )

    @classmethod
    def _build_segment(
        cls,
        name: str,
        segment: Mapping[str, Any],
    ) -> SegmentDefinition:
        condition = segment["when"]
        return SegmentDefinition(
            name=name,
            condition=ConditionDefinition(
                type=condition["type"],
                column=condition["column"],
                minimum=condition["minimum"],
                maximum=condition["maximum"],
            ),
            requirements=cls._build_requirements(
                segment["requirements"]
            ),
        )

    @classmethod
    def _build_requirements(
        cls,
        requirements: list[Mapping[str, Any]],
    ) -> tuple[RequirementDefinition, ...]:
        definitions: list[RequirementDefinition] = []
        for requirement in requirements:
            parameters = {
                key: (
                    ComparisonOperator(value)
                    if key == "operator"
                    else freeze_value(value)
                )
                for key, value in requirement.items()
                if key != "type"
            }
            definitions.append(
                RequirementDefinition(
                    type=requirement["type"],
                    parameters=MappingProxyType(parameters),
                )
            )
        return tuple(definitions)
