from pathlib import Path
from typing import Any
from typing import Optional
from typing import Sequence
from typing import Union

from govlattice.builder.state_builder import StateBuilder
from govlattice.builder.yaml_builder import YamlBuilder
from govlattice.designer import Designer
from govlattice.nodes.policy_node import PolicyNode
from govlattice.nodes.policy_reference_node import PolicyReference
from govlattice.nodes.state_node import StateNode
from govlattice.severity import SeverityLevel


class PolicyDesigner(Designer):
    __slots__ = ("_policy",)

    def __init__(
        self,
        policy_name: str,
        *,
        purpose: Optional[str] = None,
        enabled: bool = True,
        severity: SeverityLevel = SeverityLevel.MEDIUM,
        tags: Sequence[str] = (),
        lifecycle_stages: Sequence[str] = (),
        references: Sequence[PolicyReference] = (),
        created_at: Optional[str] = None,
        updated_at: Optional[str] = None,
        **metadata: Any,
    ) -> None:
        super().__init__(policy_name)
        self._policy = PolicyNode(
            name=self.policy_name,
            purpose=purpose,
            enabled=enabled,
            severity=severity,
            tags=tags,
            lifecycle_stages=lifecycle_stages,
            references=references,
            created_at=created_at,
            updated_at=updated_at,
            metadata=metadata,
        )

    def state(self, id: str) -> StateBuilder:
        if not isinstance(id, str):
            raise TypeError("state id must be a string")

        state_id = id.strip()
        if not state_id:
            raise ValueError("state id must not be empty")

        node = self._policy.states.get(state_id)
        if node is None:
            node = StateNode(state_id)
            self._policy.states[state_id] = node
        return StateBuilder(self, node)

    @property
    def enabled(self) -> bool:
        return self._policy.enabled

    @property
    def purpose(self) -> Optional[str]:
        return self._policy.purpose

    @property
    def severity(self) -> SeverityLevel:
        return self._policy.severity

    @property
    def references(self) -> tuple[PolicyReference, ...]:
        return self._policy.references

    def execute(
        self,
        name: str,
        output_dir: Union[str, Path] = "policies",
    ) -> Path:
        if not isinstance(name, str):
            raise TypeError("execution name must be a string")
        name = name.strip()
        if not name:
            raise ValueError("execution name must not be empty")

        return YamlBuilder(self._policy).write(
            name,
            output_dir=output_dir,
        )
