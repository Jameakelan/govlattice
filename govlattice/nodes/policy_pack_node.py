import re
from typing import Any
from typing import Mapping
from typing import Sequence

from govlattice.nodes.policy_node import PolicyNode
from govlattice.nodes.policy_pack_entry_node import PolicyPackEntryNode


class PolicyPackNode:
    __slots__ = (
        "id",
        "name",
        "version",
        "enabled",
        "jurisdiction",
        "tags",
        "metadata",
        "policies",
    )

    def __init__(
        self,
        pack_id: str,
        name: str,
        version: str,
        enabled: bool,
        jurisdiction: Sequence[str],
        tags: Sequence[str],
        metadata: Mapping[str, Any],
    ) -> None:
        self.id = self._validate_id(pack_id)
        self.name = self._validate_text("pack name", name)
        self.version = self._validate_text("pack version", version)
        self.enabled = PolicyNode._validate_enabled(enabled)
        self.jurisdiction = PolicyNode._validate_string_sequence(
            "jurisdiction",
            jurisdiction,
        )
        self.tags = PolicyNode._validate_string_sequence("tags", tags)
        self.metadata = self._validate_metadata(metadata)
        self.policies: list[PolicyPackEntryNode] = []

    @staticmethod
    def _validate_id(pack_id: str) -> str:
        pack_id = PolicyPackNode._validate_text("pack_id", pack_id)
        if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]*", pack_id):
            raise ValueError(
                "pack_id may contain only letters, digits, dots, "
                "underscores, and hyphens"
            )
        return pack_id

    @staticmethod
    def _validate_text(name: str, value: str) -> str:
        if not isinstance(value, str):
            raise TypeError(f"{name} must be a string")
        value = value.strip()
        if not value:
            raise ValueError(f"{name} must not be empty")
        return value

    @staticmethod
    def _validate_metadata(
        metadata: Mapping[str, Any],
    ) -> dict[str, Any]:
        reserved = {
            "id",
            "name",
            "version",
            "enabled",
            "jurisdiction",
            "tags",
            "policies",
            "pack_schema_version",
        }
        normalized: dict[str, Any] = {}
        for key, value in metadata.items():
            if key in reserved:
                raise ValueError(
                    f'pack metadata key "{key}" is reserved'
                )
            normalized[key] = PolicyNode._validate_metadata_value(
                value,
                path=key,
            )
        return normalized
