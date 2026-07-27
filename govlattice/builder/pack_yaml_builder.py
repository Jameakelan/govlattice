import json
from pathlib import Path
import re
from typing import Any
from typing import Union

from govlattice import __pack_schema_version__
from govlattice import __schema_version__
from govlattice.nodes.policy_pack_node import PolicyPackNode
from govlattice.utils.helper.file_helper import write_text_atomically


class PackYamlBuilder:
    __slots__ = ("_pack",)

    def __init__(self, pack: PolicyPackNode) -> None:
        self._pack = pack

    def build(self) -> str:
        lines = [
            "pack_schema_version: "
            f"{self._scalar(__pack_schema_version__)}",
            "policy_pack:",
            f"  id: {self._scalar(self._pack.id)}",
            f"  name: {self._scalar(self._pack.name)}",
            f"  version: {self._scalar(self._pack.version)}",
            f"  enabled: {self._scalar(self._pack.enabled)}",
        ]
        self._append_named_value(
            lines,
            "jurisdiction",
            self._pack.jurisdiction,
            indent=2,
        )
        self._append_named_value(
            lines,
            "tags",
            self._pack.tags,
            indent=2,
        )
        for name, value in self._pack.metadata.items():
            self._append_named_value(lines, name, value, indent=2)

        lines.append("  policies:")
        if not self._pack.policies:
            lines[-1] = "  policies: []"
        else:
            for entry in self._pack.policies:
                lines.extend(
                    [
                        f"    - id: "
                        f"{self._scalar(entry.policy.policy_name)}",
                        f"      file: "
                        f"{self._scalar(f'policies/{entry.file_name}')}",
                        f"      enabled: "
                        f"{self._scalar(entry.policy.enabled)}",
                        f"      severity: "
                        f"{self._scalar(entry.policy.severity.value)}",
                        "      schema_version: "
                        f"{self._scalar(__schema_version__)}",
                    ]
                )
        return "\n".join(lines) + "\n"

    def write(self, pack_directory: Path) -> Path:
        output_path = pack_directory / "manifest.yml"
        write_text_atomically(output_path, self.build())
        return output_path

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
                    indent + 2,
                )
            return
        if isinstance(value, (list, tuple)):
            if not value:
                lines.append(f"{prefix}{key}: []")
                return
            lines.append(f"{prefix}{key}:")
            self._append_sequence(lines, value, indent + 2)
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
                        indent + 2,
                    )
            elif isinstance(value, (list, tuple)):
                lines.append(f"{prefix}-")
                self._append_sequence(lines, value, indent + 2)
            else:
                lines.append(f"{prefix}- {self._scalar(value)}")

    @staticmethod
    def _scalar(value: Any) -> str:
        return json.dumps(value, ensure_ascii=False)

    @staticmethod
    def _key(value: str) -> str:
        if re.fullmatch(r"[A-Za-z_][A-Za-z0-9_-]*", value):
            return value
        return json.dumps(value, ensure_ascii=False)
