import json
import re

from pathlib import Path
import shutil
from typing import Any

from web_novel_scraper.logger_manager import create_logger
from web_novel_scraper.exceptions import (
    InvalidPathError,
    FileNotFoundCustomError,
    InvalidFileTypeError,
    OSCustomError,
    JsonParseError,
    InvalidJsonTypeError,
    EmptyDirError,
    EmptyFileError,
)

# Logger
logger = create_logger(__name__)

## FILE OPERATIONS HELPER


class IOUtils:
    """Static helper for disc operations."""

    ## HELPERS

    @staticmethod
    def _normalize_path(path: Path | str) -> Path:
        """Convert string path to Path object or raise InvalidPathError."""

        if not path:
            raise InvalidPathError("Path cannot be empty.")

        try:
            normalized = Path(path)

        except TypeError as e:
            raise InvalidPathError(f"Invalid path type: {type(path)}") from e

        return normalized

    @staticmethod
    def _validate_file_exists(path: Path) -> None:
        """Raise FileNotFoundCustomError if file does not exist."""

        if not path.exists():
            raise FileNotFoundCustomError(f"File does not exist: {path}")

    @staticmethod
    def _validate_is_file(path: Path) -> None:
        """Raise InvalidPathError if path is not a file."""

        if not path.is_file():
            raise InvalidPathError(f"Path is not a file: {path}")

    @staticmethod
    def _validate_is_dir(path: Path) -> None:
        """Raise InvalidPathError if path is not a directory."""

        if not path.is_dir():
            raise InvalidPathError(f"Path is not a directory: {path}")

    @staticmethod
    def _validate_extension(path: Path, expected_extension: str) -> None:
        """Raise InvalidFileTypeError if extension does not match."""

        if path.suffix.lower() != expected_extension.lower():
            raise InvalidFileTypeError(
                f"Expected File to have '{expected_extension}' Extension, got '{path.suffix}'"
            )

    @staticmethod
    def _read_text_file_content(path: Path, encoding: str = "utf-8") -> str:
        """Read text content from file with specified encoding."""

        try:
            return path.read_text(encoding=encoding)

        except UnicodeDecodeError as e:
            raise InvalidFileTypeError(
                f"Failed to decode file as UTF-8: '{path}'"
            ) from e

        except OSError as e:
            raise OSCustomError(f"Failed to read file: {path}") from e

    @staticmethod
    def _read_binary_file_content(path: Path) -> bytes:
        """Read binary content from file."""

        try:
            return path.read_bytes()

        except OSError as e:
            raise OSCustomError(f"Failed to read file: {path}") from e

    @staticmethod
    def _save_text_file_content(path: Path, data: str, encoding: str = "utf-8") -> None:
        """Write text content to file with specified encoding."""

        try:
            path.write_text(data=data, encoding=encoding)

        except OSError as e:
            raise OSCustomError(f"Failed to Write Content to file: {path}") from e

    @staticmethod
    def _save_binary_file_content(path: Path, data: bytes) -> None:
        """Write binary content to file."""

        try:
            path.write_bytes(data=data)

        except OSError as e:
            raise OSCustomError(f"Failed to Write Bytes Content to file: {path}") from e

    @staticmethod
    def _validate_json_data_type(
        json_data: Any, expected_type: type | tuple[type, type]
    ) -> None:
        """Raise InvalidJsonTypeError if json data type does not match expected type."""

        if not isinstance(json_data, expected_type):
            raise InvalidJsonTypeError(
                f"Expected {str(expected_type)}, got {type(json_data).__name__}"
            )

    @staticmethod
    def _parse_json(
        content: str, expected_type: type | tuple[type, type]
    ) -> dict[str, Any] | list[dict[str, Any]]:
        """Parse JSON content and validate its type."""

        try:
            parsed = json.loads(content)

        except json.JSONDecodeError as e:
            raise JsonParseError("File is an invalid JSON.") from e

        IOUtils._validate_json_data_type(parsed, expected_type)

        return parsed

    ## DIRECTORY OPERATIONS

    @staticmethod
    def dir_exists(path: Path | str) -> bool:
        """Validates if *path* is a valid directory and exists."""
        normalized_path = IOUtils._normalize_path(path)

        if normalized_path.exists():
            IOUtils._validate_is_dir(normalized_path)
        return normalized_path.exists()

    @staticmethod
    def ensure_dir(path: Path | str) -> None:
        """Create directory and all parent directories if they don't exist."""

        normalized_path = IOUtils._normalize_path(path)
        dir_exists = IOUtils.dir_exists(normalized_path)

        if not dir_exists:
            logger.debug(
                f"{normalized_path} does not exist. Creating new directory and parents."
            )
            try:
                normalized_path.mkdir(parents=True, exist_ok=True)
            except OSError as e:
                raise OSCustomError(
                    f"Failed to create directory and parents: {path}"
                ) from e

    @staticmethod
    def get_path_in_dir(directory: Path | str, file_or_dir: str) -> Path:
        """Returns Path object for a file or directory inside a directory."""
        normalized_path = IOUtils._normalize_path(directory)
        if normalized_path.exists():
            IOUtils._validate_is_dir(normalized_path)

        return normalized_path / file_or_dir

    @staticmethod
    def sanitize_dirname(name: str) -> str:
        """Replace invalid directory name characters with underscores, preserving spaces."""
        # Collapse multiple spaces into a single space (optional; comment out if not desired)
        name = re.sub(r"\s+", " ", name.strip())

        # Replace any char that is *not* letter, digit, underscore, hyphen, or space.
        return re.sub(r"[^\w\-\s]", "_", name)

    @staticmethod
    def list_files_from_dir(dir: Path | str, glob: str = "*") -> list[Path]:
        normalized_path = IOUtils._normalize_path(dir)
        IOUtils._validate_is_dir(normalized_path)
        try:
            paths = [p for p in normalized_path.glob(glob) if p.is_file()]
        except OSError as e:
            raise OSCustomError(f"Failed to list files in directory: {dir}") from e

        if paths == []:
            raise EmptyDirError(f"No files found in directory: {dir} with glob: {glob}")

        return paths

    ## READ OPERATIONS

    @staticmethod
    def read_json_file(
        path: Path | str, type: type
    ) -> dict[str, Any] | list[dict[str, Any]]:
        """Read and parse JSON file, validating it matches expected type."""

        normalized_path = IOUtils._normalize_path(path)

        IOUtils._validate_extension(normalized_path, ".json")

        IOUtils._validate_file_exists(normalized_path)

        IOUtils._validate_is_file(normalized_path)
        content = IOUtils._read_text_file_content(normalized_path)
        json_content = IOUtils._parse_json(content, type)
        if json_content == {} or json_content == []:
            raise EmptyFileError(f"JSON File is empty: {normalized_path}")
        return json_content

    @staticmethod
    def read_text_file(path: Path | str) -> str:
        """Read and return UTF-8 text content from file."""
        normalized_path = IOUtils._normalize_path(path)
        IOUtils._validate_file_exists(normalized_path)

        IOUtils._validate_is_file(normalized_path)
        content = IOUtils._read_text_file_content(normalized_path)
        if content == "":
            raise EmptyFileError(f"File is empty: {normalized_path}")

        return content

    @staticmethod
    def read_binary_file(path: Path | str) -> bytes:
        """Read and return binary content from file."""
        normalized_path = IOUtils._normalize_path(path)
        IOUtils._validate_file_exists(normalized_path)

        IOUtils._validate_is_file(normalized_path)
        binary_content = IOUtils._read_binary_file_content(normalized_path)
        if binary_content == b"":
            raise EmptyFileError(f"File is empty: {normalized_path}")

        return binary_content

    ## WRITE OPERATION

    @staticmethod
    def save_json_file(path: Path | str, data: dict | list) -> None:
        """Write data to JSON file with pretty formatting."""

        normalized_path = IOUtils._normalize_path(path)

        IOUtils._validate_extension(normalized_path, ".json")
        if normalized_path.exists():
            IOUtils._validate_is_file(normalized_path)

        IOUtils._validate_json_data_type(data, (dict, list))

        IOUtils._save_text_file_content(
            path=normalized_path,
            data=json.dumps(data, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    @staticmethod
    def save_text_file(path: Path | str, text: str) -> None:
        """Write UTF-8 text content to file."""

        normalized_path = IOUtils._normalize_path(path)

        if normalized_path.exists():
            IOUtils._validate_is_file(normalized_path)

        IOUtils._save_text_file_content(
            path=normalized_path,
            data=text,
            encoding="utf-8",
        )

    @staticmethod
    def save_binary_file(path: Path | str, data: bytes) -> None:
        """Write binary content to file."""
        normalized_path = IOUtils._normalize_path(path)

        if normalized_path.exists():
            IOUtils._validate_is_file(normalized_path)

        IOUtils._save_binary_file_content(path=normalized_path, data=data)

    ## DELETE/COPY OPERATIONS

    @staticmethod
    def delete_file(path: Path | str) -> None:
        """Delete file if it exists, otherwise do nothing."""
        normalized_path = IOUtils._normalize_path(path)

        if not normalized_path.exists():
            logger.debug(
                f"Tried to delete file '{normalized_path}' but it does not exist."
            )
            return

        IOUtils._validate_is_file(normalized_path)

        try:
            normalized_path.unlink()

        except OSError as e:
            raise OSCustomError(f"Failed to Delete file: {normalized_path}") from e

    @staticmethod
    def delete_dir(path: Path | str) -> None:
        """Delete empty directory if it exists, otherwise do nothing."""
        normalized_path = IOUtils._normalize_path(path)

        if not normalized_path.exists():
            logger.debug(
                f"Tried to delete file '{normalized_path}' but it does not exist."
            )
            return

        IOUtils._validate_is_dir(normalized_path)

        try:
            normalized_path.rmdir()

        except OSError as e:
            raise OSCustomError(f"Failed to Delete directory: {normalized_path}") from e

    @staticmethod
    def copy_file(src_path: Path | str, dst_path: Path | str) -> None:
        """Copy source file to destination file."""
        if src_path == dst_path:
            raise InvalidPathError("Source and destination paths cannot be the same.")

        normalized_src_path = IOUtils._normalize_path(src_path)
        normalized_dst_path = IOUtils._normalize_path(dst_path)

        IOUtils._validate_file_exists(normalized_src_path)
        IOUtils._validate_is_file(normalized_src_path)

        if normalized_dst_path.exists():
            IOUtils._validate_is_file(normalized_dst_path)
            logger.debug(
                f"Destination file '{normalized_dst_path}' already exists and will be overwritten with '{normalized_src_path}' contents."
            )

        try:
            normalized_dst_path.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy(normalized_src_path,normalized_dst_path)
        except OSError as e:
            raise OSCustomError(
                f"Failed to copy file from '{normalized_src_path}' to '{normalized_dst_path}'"
            ) from e
