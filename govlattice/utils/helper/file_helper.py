import os
from pathlib import Path
from tempfile import NamedTemporaryFile
from typing import Collection
from typing import Optional
from typing import Union


PathInput = Union[str, Path]


def resolve_output_path(
    file_name: PathInput,
    output_dir: PathInput,
    allowed_suffixes: Collection[str],
) -> Path:
    """Validate an output file name and resolve its project directory."""
    file_path = _validate_file_name(file_name, allowed_suffixes)
    output_directory = resolve_output_directory(output_dir)
    return output_directory / file_path.name


def write_text_atomically(
    output_path: Path,
    content: str,
    encoding: str = "utf-8",
) -> None:
    """Replace a text file only after its complete content is written."""
    temporary_path: Optional[Path] = None
    try:
        with NamedTemporaryFile(
            mode="w",
            encoding=encoding,
            dir=output_path.parent,
            prefix=f".{output_path.name}.",
            suffix=".tmp",
            delete=False,
        ) as temporary_file:
            temporary_file.write(content)
            temporary_path = Path(temporary_file.name)

        assert temporary_path is not None
        os.chmod(temporary_path, 0o644)
        os.replace(temporary_path, output_path)
    finally:
        if temporary_path is not None and temporary_path.exists():
            temporary_path.unlink()


def _validate_file_name(
    file_name: PathInput,
    allowed_suffixes: Collection[str],
) -> Path:
    if not isinstance(file_name, (str, Path)):
        raise TypeError("file name must be a string or Path")

    file_name_text = str(file_name).strip()
    if not file_name_text:
        raise ValueError("file name must not be empty")
    if "/" in file_name_text or "\\" in file_name_text:
        raise ValueError("file name must not contain a directory")

    file_path = Path(file_name_text)
    if file_path.suffix.lower() not in allowed_suffixes:
        suffixes = ", ".join(sorted(allowed_suffixes))
        raise ValueError(f"file extension must be one of: {suffixes}")

    return file_path


def resolve_output_directory(output_dir: PathInput) -> Path:
    if not isinstance(output_dir, (str, Path)):
        raise TypeError("output_dir must be a string or Path")
    if isinstance(output_dir, str) and not output_dir.strip():
        raise ValueError("output_dir must not be empty")

    output_directory = Path(output_dir).expanduser()
    if not output_directory.is_absolute():
        output_directory = Path.cwd() / output_directory

    output_directory.mkdir(parents=True, exist_ok=True)
    return output_directory.resolve()
