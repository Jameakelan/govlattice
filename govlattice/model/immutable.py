from types import MappingProxyType
from typing import Any


def freeze_value(value: Any) -> Any:
    if isinstance(value, dict):
        return MappingProxyType(
            {
                key: freeze_value(item)
                for key, item in value.items()
            }
        )
    if isinstance(value, list):
        return tuple(freeze_value(item) for item in value)
    return value
