from pathlib import Path
from typing import Any

import yaml

from govlattice.error import PolicyPackFileError
from govlattice.error import PolicyPackValidationError
from govlattice.reader.policy_yaml_loader import PathInput
from govlattice.reader.policy_yaml_loader import UniqueKeySafeLoader
from govlattice.reader.policy_yaml_loader import YAML_SUFFIXES


MAX_POLICY_PACK_FILE_BYTES = 1024 * 1024


class PolicyPackYamlLoader:
    MAX_FILE_BYTES = MAX_POLICY_PACK_FILE_BYTES

    @classmethod
    def load(
        cls,
        path: PathInput,
    ) -> tuple[Path, dict[str, Any]]:
        manifest_path = cls._resolve_path(path)
        return manifest_path, cls._load_document(manifest_path)

    @classmethod
    def _resolve_path(cls, path: PathInput) -> Path:
        if not isinstance(path, (str, Path)):
            raise TypeError("manifest path must be a string or Path")
        if isinstance(path, str) and not path.strip():
            raise ValueError("manifest path must not be empty")

        manifest_path = Path(path).expanduser()
        if manifest_path.suffix.lower() not in YAML_SUFFIXES:
            raise PolicyPackFileError(
                "manifest file extension must be .yml or .yaml"
            )
        if not manifest_path.exists():
            raise PolicyPackFileError(
                f'manifest file does not exist: "{manifest_path}"'
            )
        if not manifest_path.is_file():
            raise PolicyPackFileError(
                f'manifest path is not a file: "{manifest_path}"'
            )
        if manifest_path.stat().st_size > cls.MAX_FILE_BYTES:
            raise PolicyPackFileError(
                f"manifest file exceeds {cls.MAX_FILE_BYTES} bytes"
            )
        return manifest_path.resolve()

    @staticmethod
    def _load_document(path: Path) -> dict[str, Any]:
        try:
            content = path.read_text(encoding="utf-8")
        except (OSError, UnicodeError) as error:
            raise PolicyPackFileError(
                f'could not read manifest file: "{path}"'
            ) from error

        try:
            document = yaml.load(
                content,
                Loader=UniqueKeySafeLoader,
            )
        except yaml.YAMLError as error:
            raise PolicyPackValidationError(
                f'invalid pack YAML in "{path}": {error}'
            ) from error

        if not isinstance(document, dict):
            raise PolicyPackValidationError(
                "pack document root must be an object"
            )
        return document
