import json
from pathlib import Path
from typing import Iterable
from typing import Union

from govlattice.builder.file_helper import resolve_output_path
from govlattice.builder.file_helper import write_text_atomically


Requirement = tuple[str, tuple[str, ...]]
State = tuple[str, tuple[Requirement, ...]]
YAML_SUFFIXES = frozenset({".yaml", ".yml"})


class YamlBuilder:
    """Serialize a policy definition as deterministic YAML."""

    __slots__ = ("_policy_name", "_states")

    def __init__(self, policy_name: str, states: Iterable[State]) -> None:
        self._policy_name = policy_name
        self._states = tuple(states)

    def build(self) -> str:
        lines = [
            "policy:",
            f"  name: {self._scalar(self._policy_name)}",
            "  states:",
        ]

        if not self._states:
            lines[-1] = "  states: {}"
            return "\n".join(lines) + "\n"

        for state_id, requirements in self._states:
            lines.append(f"    {self._scalar(state_id)}:")
            if not requirements:
                lines.append("      requirements: []")
                continue

            lines.append("      requirements:")
            for requirement_type, columns in requirements:
                lines.append(
                    f"        - type: {self._scalar(requirement_type)}"
                )
                lines.append("          columns:")
                for column in columns:
                    lines.append(f"            - {self._scalar(column)}")

        return "\n".join(lines) + "\n"

    def write(
        self,
        file_name: Union[str, Path],
        output_dir: Union[str, Path] = "policies",
    ) -> Path:
        output_path = resolve_output_path(
            file_name,
            output_dir,
            allowed_suffixes=YAML_SUFFIXES,
        )
        write_text_atomically(output_path, self.build())
        return output_path

    @staticmethod
    def _scalar(value: str) -> str:
        # JSON strings are valid YAML 1.2 scalars and safely preserve special
        # characters without requiring an external YAML dependency.
        return json.dumps(value, ensure_ascii=False)
