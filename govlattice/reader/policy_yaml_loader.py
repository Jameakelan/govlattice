from pathlib import Path
from typing import Any
from typing import Union

import yaml
from yaml.constructor import ConstructorError
from yaml.nodes import MappingNode

from govlattice.error import PolicyFileError
from govlattice.error import PolicySyntaxError
from govlattice.error import PolicyValidationError


PathInput = Union[str, Path]
YAML_SUFFIXES = frozenset({".yaml", ".yml"})
MAX_POLICY_FILE_BYTES = 1024 * 1024


class _UniqueKeySafeLoader(yaml.SafeLoader):
    pass


def _construct_unique_mapping(
    loader: _UniqueKeySafeLoader,
    node: MappingNode,
    deep: bool = False,
) -> dict[Any, Any]:
    mapping: dict[Any, Any] = {}
    for key_node, value_node in node.value:
        key = loader.construct_object(key_node, deep=deep)
        try:
            duplicate = key in mapping
        except TypeError as error:
            raise ConstructorError(
                "while constructing a mapping",
                node.start_mark,
                "found an unhashable key",
                key_node.start_mark,
            ) from error
        if duplicate:
            raise ConstructorError(
                "while constructing a mapping",
                node.start_mark,
                f"found duplicate key {key!r}",
                key_node.start_mark,
            )
        mapping[key] = loader.construct_object(value_node, deep=deep)
    return mapping


_UniqueKeySafeLoader.add_constructor(
    yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG,
    _construct_unique_mapping,
)


class PolicyYamlLoader:
    MAX_FILE_BYTES = MAX_POLICY_FILE_BYTES

    @classmethod
    def load(cls, path: PathInput) -> dict[str, Any]:
        policy_path = cls._resolve_path(path)
        return cls._load_document(policy_path)

    @classmethod
    def _resolve_path(cls, path: PathInput) -> Path:
        if not isinstance(path, (str, Path)):
            raise TypeError("policy path must be a string or Path")
        if isinstance(path, str) and not path.strip():
            raise ValueError("policy path must not be empty")

        policy_path = Path(path).expanduser()
        if policy_path.suffix.lower() not in YAML_SUFFIXES:
            raise PolicyFileError(
                "policy file extension must be .yml or .yaml"
            )
        if not policy_path.exists():
            raise PolicyFileError(
                f'policy file does not exist: "{policy_path}"'
            )
        if not policy_path.is_file():
            raise PolicyFileError(
                f'policy path is not a file: "{policy_path}"'
            )
        if policy_path.stat().st_size > cls.MAX_FILE_BYTES:
            raise PolicyFileError(
                f"policy file exceeds {cls.MAX_FILE_BYTES} bytes"
            )
        return policy_path.resolve()

    @staticmethod
    def _load_document(path: Path) -> dict[str, Any]:
        try:
            content = path.read_text(encoding="utf-8")
        except (OSError, UnicodeError) as error:
            raise PolicyFileError(
                f'could not read policy file: "{path}"'
            ) from error

        try:
            document = yaml.load(content, Loader=_UniqueKeySafeLoader)
        except yaml.YAMLError as error:
            raise PolicySyntaxError(
                f'invalid policy YAML in "{path}": {error}'
            ) from error

        if not isinstance(document, dict):
            raise PolicyValidationError(
                "policy document root must be an object"
            )
        return document
