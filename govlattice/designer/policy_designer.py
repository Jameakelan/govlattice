from pathlib import Path
from typing import Union

from govlattice.builder.expectation_builder import ExpectationBuilder
from govlattice.builder.yaml_builder import YamlBuilder
from govlattice.designer import Designer


class PolicyDesigner(Designer):
    __slots__ = ("_states",)

    def __init__(self, policy_name: str) -> None:
        super().__init__(policy_name)
        self._states: dict[str, ExpectationBuilder] = {}

    def state(self, id: str) -> ExpectationBuilder:
        if not isinstance(id, str):
            raise TypeError("state id must be a string")

        state_id = id.strip()
        if not state_id:
            raise ValueError("state id must not be empty")

        builder = self._states.get(state_id)
        if builder is None:
            builder = ExpectationBuilder(self, state_id)
            self._states[state_id] = builder

        return builder

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

        states = (
            (builder.state_id, builder.requirements)
            for builder in self._states.values()
        )
        return YamlBuilder(self.policy_name, states).write(
            name,
            output_dir=output_dir,
        )
