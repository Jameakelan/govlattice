from datetime import datetime
import math
from typing import Any
from typing import Mapping
from typing import Optional
from typing import Sequence

from govlattice.nodes.state_node import StateNode


class PolicyNode:
    __slots__ = (
        "name",
        "enabled",
        "tags",
        "created_at",
        "updated_at",
        "metadata",
        "states",
    )

    def __init__(
        self,
        name: str,
        enabled: bool,
        tags: Sequence[str],
        created_at: Optional[str],
        updated_at: Optional[str],
        metadata: Mapping[str, Any],
    ) -> None:
        self.name = name
        self.enabled = self._validate_enabled(enabled)
        self.tags = self._validate_tags(tags)
        self.created_at = self._validate_timestamp(
            "created_at",
            created_at,
        )
        self.updated_at = self._validate_timestamp(
            "updated_at",
            updated_at,
        )
        self._validate_timestamp_order()
        self.metadata = self._validate_metadata(metadata)
        self.states: dict[str, StateNode] = {}

    @staticmethod
    def _validate_enabled(enabled: bool) -> bool:
        if type(enabled) is not bool:
            raise TypeError("enabled must be a boolean")
        return enabled

    @staticmethod
    def _validate_tags(tags: Sequence[str]) -> tuple[str, ...]:
        if isinstance(tags, (str, bytes)) or not isinstance(
            tags,
            (list, tuple),
        ):
            raise TypeError("tags must be a list or tuple of strings")

        normalized: list[str] = []
        seen: set[str] = set()
        for tag in tags:
            if not isinstance(tag, str):
                raise TypeError("tags must contain only strings")
            tag = tag.strip()
            if not tag:
                raise ValueError("tags must not contain empty strings")
            if tag not in seen:
                normalized.append(tag)
                seen.add(tag)
        return tuple(normalized)

    @classmethod
    def _validate_timestamp(
        cls,
        name: str,
        value: Optional[str],
    ) -> Optional[str]:
        if value is None:
            return None
        if not isinstance(value, str):
            raise TypeError(f"{name} must be an ISO 8601 string")

        value = value.strip()
        if not value or "T" not in value:
            raise ValueError(
                f"{name} must be ISO 8601 with a timezone"
            )

        try:
            parsed = cls._parse_timestamp(value)
        except ValueError as error:
            raise ValueError(
                f"{name} must be ISO 8601 with a timezone"
            ) from error
        if parsed.tzinfo is None or parsed.utcoffset() is None:
            raise ValueError(
                f"{name} must be ISO 8601 with a timezone"
            )
        return value

    def _validate_timestamp_order(self) -> None:
        if self.created_at is None or self.updated_at is None:
            return
        if self._parse_timestamp(self.created_at) > self._parse_timestamp(
            self.updated_at
        ):
            raise ValueError("created_at must not be after updated_at")

    @staticmethod
    def _parse_timestamp(value: str) -> datetime:
        normalized = (
            f"{value[:-1]}+00:00"
            if value.endswith(("Z", "z"))
            else value
        )
        return datetime.fromisoformat(normalized)

    @classmethod
    def _validate_metadata(
        cls,
        metadata: Mapping[str, Any],
    ) -> dict[str, Any]:
        reserved = {
            "name",
            "enabled",
            "tags",
            "created_at",
            "updated_at",
            "states",
            "schema_version",
        }
        normalized: dict[str, Any] = {}
        for key, value in metadata.items():
            if key in reserved:
                raise ValueError(
                    f'metadata key "{key}" is reserved'
                )
            normalized[key] = cls._validate_metadata_value(
                value,
                path=key,
            )
        return normalized

    @classmethod
    def _validate_metadata_value(
        cls,
        value: Any,
        path: str,
    ) -> Any:
        if value is None or isinstance(value, (str, bool, int)):
            return value
        if isinstance(value, float):
            if not math.isfinite(value):
                raise ValueError(
                    f'metadata value "{path}" must be finite'
                )
            return value
        if isinstance(value, (list, tuple)):
            return tuple(
                cls._validate_metadata_value(
                    item,
                    path=f"{path}[{index}]",
                )
                for index, item in enumerate(value)
            )
        if isinstance(value, dict):
            normalized: dict[str, Any] = {}
            for key, item in value.items():
                if not isinstance(key, str) or not key:
                    raise TypeError(
                        f'metadata object "{path}" requires string keys'
                    )
                normalized[key] = cls._validate_metadata_value(
                    item,
                    path=f"{path}.{key}",
                )
            return normalized
        raise TypeError(
            f'metadata value "{path}" is not YAML-compatible'
        )
