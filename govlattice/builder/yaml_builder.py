import json
from pathlib import Path
import re
from typing import Any
from typing import Union

from govlattice import __schema_version__
from govlattice.nodes.policy_node import PolicyNode
from govlattice.nodes.requirement_node import RequirementNode
from govlattice.nodes.segment_node import SegmentNode
from govlattice.nodes.state_node import StateNode
from govlattice.utils.helper.file_helper import resolve_output_path
from govlattice.utils.helper.file_helper import write_text_atomically


YAML_SUFFIXES = frozenset({".yaml", ".yml"})


class YamlBuilder:
    """Serialize a policy definition as deterministic YAML."""

    __slots__ = ("_policy",)

    def __init__(self, policy: PolicyNode) -> None:
        self._policy = policy

    def build(self) -> str:
        lines = [
            f"schema_version: {self._scalar(__schema_version__)}",
            "policy:",
            f"  name: {self._scalar(self._policy.name)}",
        ]
        self._append_named_value(
            lines,
            "enabled",
            self._policy.enabled,
            indent=2,
        )
        self._append_named_value(
            lines,
            "tags",
            self._policy.tags,
            indent=2,
        )
        if self._policy.created_at is not None:
            self._append_named_value(
                lines,
                "created_at",
                self._policy.created_at,
                indent=2,
            )
        if self._policy.updated_at is not None:
            self._append_named_value(
                lines,
                "updated_at",
                self._policy.updated_at,
                indent=2,
            )
        for name, value in self._policy.metadata.items():
            self._append_named_value(lines, name, value, indent=2)
        lines.append("  states:")

        if not self._policy.states:
            lines[-1] = "  states: {}"
            return "\n".join(lines) + "\n"

        for state in self._policy.states.values():
            self._append_state(lines, state)

        return "\n".join(lines) + "\n"

    def _append_state(self, lines: list[str], state: StateNode) -> None:
        lines.append(f"    {self._scalar(state.name)}:")
        self._append_requirements(lines, state.requirements, indent=6)
        if state.segments:
            lines.append("      segments:")
            for segment in state.segments.values():
                self._append_segment(lines, segment)

    def _append_segment(
        self,
        lines: list[str],
        segment: SegmentNode,
    ) -> None:
        lines.append(f"        {self._scalar(segment.name)}:")
        if segment.condition is not None:
            lines.append("          when:")
            lines.append(
                "            type: "
                f"{self._scalar(segment.condition.type)}"
            )
            lines.append(
                "            column: "
                f"{self._scalar(segment.condition.column)}"
            )
            lines.append(
                "            minimum: "
                f"{self._scalar(segment.condition.minimum)}"
            )
            lines.append(
                "            maximum: "
                f"{self._scalar(segment.condition.maximum)}"
            )
        self._append_requirements(
            lines,
            segment.requirements,
            indent=10,
        )

    def _append_requirements(
        self,
        lines: list[str],
        requirements: list[RequirementNode],
        indent: int,
    ) -> None:
        prefix = " " * indent
        if not requirements:
            lines.append(f"{prefix}requirements: []")
            return

        lines.append(f"{prefix}requirements:")
        item_prefix = " " * (indent + 2)
        value_prefix = " " * (indent + 4)
        list_prefix = " " * (indent + 6)
        for requirement in requirements:
            lines.append(
                f"{item_prefix}- type: "
                f"{self._scalar(requirement.type)}"
            )
            for name, value in requirement.parameters.items():
                if isinstance(value, tuple):
                    lines.append(f"{value_prefix}{name}:")
                    for item in value:
                        lines.append(
                            f"{list_prefix}- {self._scalar(item)}"
                        )
                else:
                    lines.append(
                        f"{value_prefix}{name}: {self._scalar(value)}"
                    )

    def _append_named_value(
        self,
        lines: list[str],
        name: str,
        value: Any,
        indent: int,
    ) -> None:
        prefix = " " * indent
        key = self._key(name)
        if isinstance(value, dict):
            if not value:
                lines.append(f"{prefix}{key}: {{}}")
                return
            lines.append(f"{prefix}{key}:")
            for child_name, child_value in value.items():
                self._append_named_value(
                    lines,
                    child_name,
                    child_value,
                    indent=indent + 2,
                )
            return
        if isinstance(value, (list, tuple)):
            if not value:
                lines.append(f"{prefix}{key}: []")
                return
            lines.append(f"{prefix}{key}:")
            self._append_sequence(lines, value, indent=indent + 2)
            return
        lines.append(f"{prefix}{key}: {self._scalar(value)}")

    def _append_sequence(
        self,
        lines: list[str],
        values: Union[list[Any], tuple[Any, ...]],
        indent: int,
    ) -> None:
        prefix = " " * indent
        for value in values:
            if isinstance(value, dict):
                lines.append(f"{prefix}-")
                for name, child_value in value.items():
                    self._append_named_value(
                        lines,
                        name,
                        child_value,
                        indent=indent + 2,
                    )
            elif isinstance(value, (list, tuple)):
                lines.append(f"{prefix}-")
                self._append_sequence(
                    lines,
                    value,
                    indent=indent + 2,
                )
            else:
                lines.append(f"{prefix}- {self._scalar(value)}")

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
    def _scalar(value: Any) -> str:
        # JSON strings are valid YAML 1.2 scalars and safely preserve special
        # characters without requiring an external YAML dependency.
        return json.dumps(value, ensure_ascii=False)

    @staticmethod
    def _key(value: str) -> str:
        if re.fullmatch(r"[A-Za-z_][A-Za-z0-9_-]*", value):
            return value
        return json.dumps(value, ensure_ascii=False)
